"""
POST /api/v1/chat

Cookie-session-scoped conversational dispute-intake endpoint. Drives the
orchestrator step function with the Gold store on ``app.state.gold`` and the
model from ``app.state.model`` (keyword baseline by default).

This module is the HTTP adapter only: the orchestrator and the policy engine
decide; here each ``TurnOutput`` is projected onto the canonical reply
contract in ``app.schemas.chat``. A handoff carries the advisor package
(REQ-0008), which is also written to the closing turn record.

Per-session state is stored in app.state.memories (InMemoryTools) and
app.state.conversations (ConversationState), both keyed by the session token.
"""

from __future__ import annotations

import secrets
from datetime import date, datetime, timedelta, timezone
from time import perf_counter

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.observability import Recorder, TurnObserver
from app.orchestrator.step import Ports, step
from app.orchestrator.types import (
    Candidate,
    CandidateIdInput,
    ConversationState,
    Language,
    OutcomeKind,
    TextInput,
    TurnOutput,
)
from app.routers.demo_transactions import candidate_view
from app.schemas.chat import (
    CaseConfirmation,
    ChatInput,
    ChatReply,
    Clarification,
    ConfirmationDisplay,
    ConfirmBox,
    ErrorReply,
    Handoff,
    HandoffAction,
    HandoffPackage,
    MessageKeys,
    TextReply,
    TransactionFacts,
    VerifiedFacts,
)
from app.session.models import Session
from app.session.router import SESSION_COOKIE, require_session
from app.tools.bound import SessionBoundLookup
from app.tools.fake import InMemoryTools
from app.tools.gold import to_candidate

router = APIRouter(prefix="/api/v1", tags=["chat"])

# Policy rule or orchestrator reason → translation key shown to the customer.
_TEXT_KEYS = {
    "person.ask": "person.ask",
    "status.reversed": "status.reversed",
    "status.declined": "status.declined",
    "status.pending": "status.pending",
    "window.expired": "window.expired",
    "already.disputed": "already.disputed",
    "no.candidate": "no.candidate",
}
_HANDOFF_KEYS = {
    "person.insist": "handoff.person",
    "unverified": "handoffUnverified",
    "unknown_candidate": "unknownCharge",
    "unknownCharge": "unknownCharge",
    "fields.missing": "fields.missing",
    "fraud.score": "handoff.review",
    "amount.high": "handoff.amountHigh",
    "out_of_scope": "handoff.outOfScope",
    "model_unavailable": "handoff.modelUnavailable",
}
# Reason → what the advisor still has to resolve (keys, not prose).
_OPEN_QUESTIONS = {
    "person.insist": "customer_requested_person",
    "unverified": "case_not_verified",
    "unknown_candidate": "charge_not_found",
    "unknownCharge": "charge_not_found",
    "fields.missing": "mandatory_fields_missing",
    "fraud.score": "possible_fraud",
    "amount.high": "amount_above_threshold",
    "out_of_scope": "request_outside_scope",
    "model_unavailable": "intent_not_understood",
}
_ACTION_STEPS = {"decide", "act", "verify", "escalate"}


def _sla_date(ref_date: date) -> str:
    """Return a 5-calendar-day estimate from the reference date."""
    return (ref_date + timedelta(days=5)).isoformat()


def _request_of(reason: str | None) -> str:
    if reason and reason.startswith("person."):
        return "person"
    if reason == "out_of_scope":
        return "out_of_scope"
    return "dispute"


def _verified_facts(candidate: Candidate, country: str, ref_date: date) -> VerifiedFacts:
    view = candidate_view(candidate, country, ref_date)
    return VerifiedFacts(
        transaction_id=candidate.candidate_id,
        amount=float(candidate.amount),
        currency=candidate.currency,
        merchant=candidate.merchant,
        transaction_date=candidate.date,
        days_since_transaction=(ref_date - date.fromisoformat(candidate.date)).days,
        is_eligible_for_dispute=view.eligible,
    )


def _handoff(
    reason: str | None,
    candidate: Candidate | None,
    attempt: int | None,
    *,
    language: str,
    country: str,
    trace_id: str,
    ref_date: date,
    recorder: Recorder,
) -> Handoff:
    actions = [
        HandoffAction(
            step=record.step,
            tool=record.tool,
            outcome=record.outcome,
            attempt=record.attempt,
            policy_rule=record.policy_rule,
        )
        for record in recorder.records_for(trace_id)
        if record.step in _ACTION_STEPS
    ]
    evidence = {"trace_id": trace_id, "reference_date": ref_date.isoformat()}
    if reason:
        evidence["policy_rule"] = reason
    if candidate is not None:
        evidence["as_of"] = candidate.as_of
    package = HandoffPackage(
        request=_request_of(reason),
        verified_facts=_verified_facts(candidate, country, ref_date) if candidate else None,
        actions_taken=actions,
        evidence=evidence,
        open_questions=[_OPEN_QUESTIONS.get(reason or "", "review_required")],
        language=language,
        country=country,
    )
    return Handoff(
        reference=f"HO-{trace_id[:8]}",
        reason_key=_HANDOFF_KEYS.get(reason or "", "handoff.review"),
        estimated_date=_sla_date(ref_date),
        attempt=attempt,
        package=package,
    )


def _to_reply(
    output: TurnOutput,
    state: ConversationState,
    bound: SessionBoundLookup,
    *,
    session: Session,
    trace_id: str,
    ref_date: date,
    recorder: Recorder,
) -> ChatReply:
    kind = output.kind
    if kind is OutcomeKind.QUESTION:
        if not state.candidates:
            # Nothing shown yet: offer the customer's own charges as chips.
            state.candidates = bound.lookup_transactions()
        return Clarification(
            message_key="clarifyWhichCharge",
            missing="transaction",
            candidates=[
                candidate_view(item, session.country, ref_date) for item in state.candidates[:4]
            ],
        )
    if kind in (OutcomeKind.EXPLAIN, OutcomeKind.OFFER):
        return TextReply(message_key=_TEXT_KEYS.get(output.reason or "", "greetingHelp"))
    if kind is OutcomeKind.CONFIRM_BOX and output.candidate is not None:
        return ConfirmBox(
            message_key="confirmCharge",
            candidate=candidate_view(output.candidate, session.country, ref_date),
        )
    if kind is OutcomeKind.CASE_NUMBER and output.candidate is not None and output.case_number:
        item = output.candidate
        return CaseConfirmation(
            case_id=output.case_number,
            transaction=TransactionFacts(
                amount=item.amount, currency=item.currency, merchant=item.merchant, date=item.date
            ),
            verified_at=datetime.now(timezone.utc),
            display=ConfirmationDisplay(
                amount=item.amount,
                currency=item.currency,
                merchant=item.merchant,
                referenceDate=ref_date.isoformat(),
            ),
            messages=MessageKeys(nextStep="nextStepReview", rule="ruleEligible", noFunds="noFundsHeld"),
            attempt=output.attempt or 1,
        )
    # HANDOFF, FAILURE, or an output missing the data its kind needs.
    return _handoff(
        output.reason,
        output.candidate,
        output.attempt,
        language=state.language.value,
        country=session.country,
        trace_id=trace_id,
        ref_date=ref_date,
        recorder=recorder,
    )


def _turn_outcome(output: TurnOutput | None) -> str:
    if output is None:
        return "failed"
    if output.kind is OutcomeKind.FAILURE:
        return "rejected" if output.reason == "unknown_candidate" else "failed"
    return "ok"


def _reply(reply: ChatReply, trace_id: str) -> JSONResponse:
    return JSONResponse(content=reply.model_dump(mode="json"), headers={"X-Trace-Id": trace_id})


@router.post("/chat")
def chat(
    body: ChatInput,
    request: Request,
    session: Session = Depends(require_session),
) -> JSONResponse:
    token: str = request.cookies.get(SESSION_COOKIE, "")
    trace_id: str = getattr(request.state, "trace_id", None) or secrets.token_hex(8)

    memories: dict[str, InMemoryTools] = request.app.state.memories
    conversations: dict[str, ConversationState] = request.app.state.conversations

    if token not in memories:
        memories[token] = InMemoryTools()
    if token not in conversations:
        conversations[token] = ConversationState(language=Language.ES_419)

    memory = memories[token]
    state = conversations[token]
    gold = request.app.state.gold
    ref_date = request.app.state.reference_date
    recorder: Recorder = request.app.state.recorder

    observer = TurnObserver(
        recorder=recorder,
        trace_id=trace_id,
        session_ref=recorder.session_ref(token),
        country=session.country,
    )

    bound = SessionBoundLookup(gold, session.customer_id, memory)
    ports = Ports(
        idempotency_scope=token[:12],
        tools=bound,
        model=request.app.state.model,
        country=session.country,
        today=ref_date,
        trace_id=trace_id,
        observer=observer,
    )

    started = perf_counter()

    if body.selected_reference is not None:
        # Check if this reference belongs to the customer at all.
        row = gold.get(body.selected_reference, session.customer_id)
        if row is None:
            reply = _handoff(
                "unknownCharge",
                None,
                None,
                language=state.language.value,
                country=session.country,
                trace_id=trace_id,
                ref_date=ref_date,
                recorder=recorder,
            )
            observer.emit(
                step="turn",
                language=state.language.value,
                outcome="ok",
                attempt=1,
                policy_rule="unknownCharge",
                latency_ms=(perf_counter() - started) * 1000,
                handoff=reply.package.model_dump(mode="json"),
            )
            return _reply(reply, trace_id)
        # The transactions panel shows every own charge, so a tapped charge
        # counts as shown even when the last clarification listed others.
        if all(item.candidate_id != row.reference for item in state.candidates):
            state.candidates = [*state.candidates, to_candidate(row)]
        turn = CandidateIdInput(candidate_id=body.selected_reference)
    else:
        turn = TextInput(text=body.message or "")

    try:
        output = step(turn, state, ports)
    except Exception:
        # Gold or orchestrator failure: degrade gracefully without leaking internals.
        observer.emit(
            step="turn",
            language=state.language.value,
            outcome="failed",
            attempt=1,
            latency_ms=(perf_counter() - started) * 1000,
        )
        return _reply(ErrorReply(message_key="errorGeneric", trace_id=trace_id), trace_id)

    # For FAILURE (unknown/foreign reference), strip candidate details to avoid
    # disclosing data from another customer's transaction.
    if output.kind is OutcomeKind.FAILURE:
        output = TurnOutput(kind=OutcomeKind.FAILURE, language=output.language, reason=output.reason)

    reply = _to_reply(
        output,
        state,
        bound,
        session=session,
        trace_id=trace_id,
        ref_date=ref_date,
        recorder=recorder,
    )

    observer.emit(
        step="turn",
        language=state.language.value,
        outcome=_turn_outcome(output),
        attempt=output.attempt if output.attempt is not None else 1,
        policy_rule=output.reason,
        latency_ms=(perf_counter() - started) * 1000,
        handoff=reply.package.model_dump(mode="json") if isinstance(reply, Handoff) else None,
    )

    return _reply(reply, trace_id)
