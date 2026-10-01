"""
POST /api/v1/chat

Cookie-session-scoped conversational dispute-intake endpoint. Drives the
orchestrator step function with the Gold store on ``app.state.gold`` and the
model from ``app.state.model`` (keyword baseline by default).

This module is the HTTP adapter only: the orchestrator and the policy engine
decide; here each ``TurnOutput`` is projected onto the canonical reply
contract in ``app.schemas.chat``. A handoff carries the advisor package
(REQ-0008), which is also written to the closing turn record.

Conversation state lives in ``app.state.conversation_store`` (memory or
SQLite, keyed by a hash of the session token). Cases live in
``app.state.cases``; ``app.state.memories`` caches one ``CaseTools`` per
customer (keyed by an opaque salted hash), so a charge disputed in one session
is "already disputed" in the next. The turn cycle (``open_turn`` →
``run_turn`` → ``finish_turn``) is shared with ``/api/v1/disputes``.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
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
from app.state.cases import ESCALATED, CaseRow, CaseTools
from app.state.conversation import StoredConversation
from app.tools.bound import SessionBoundLookup

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


@dataclass
class TurnContext:
    """Everything one request needs to run a turn for the session customer."""

    session: Session
    token: str
    trace_id: str
    stored: StoredConversation
    bound: SessionBoundLookup
    tools: CaseTools
    ports: Ports
    observer: TurnObserver
    recorder: Recorder
    ref_date: date
    started: float

    @property
    def state(self) -> ConversationState:
        return self.stored.state


def open_turn(request: Request, session: Session) -> TurnContext:
    app_state = request.app.state
    token: str = request.cookies.get(SESSION_COOKIE, "")
    trace_id: str = getattr(request.state, "trace_id", None) or secrets.token_hex(8)
    recorder: Recorder = app_state.recorder
    ref_date: date = app_state.reference_date

    stored = app_state.conversation_store.get(token) or StoredConversation(
        ConversationState(language=Language.ES_419)
    )
    # Opaque, stable per customer: idempotency and case tools survive new sessions,
    # and the orchestrator never sees the customer identifier.
    customer_ref = recorder.session_ref(f"customer:{session.customer_id}")
    memories: dict[str, CaseTools] = app_state.memories
    if customer_ref not in memories:
        memories[customer_ref] = CaseTools(app_state.cases, session.customer_id, app_state.gold)
    tools = memories[customer_ref]

    observer = TurnObserver(
        recorder=recorder,
        trace_id=trace_id,
        session_ref=recorder.session_ref(token),
        country=session.country,
    )
    bound = SessionBoundLookup(app_state.gold, session.customer_id, tools)
    ports = Ports(
        idempotency_scope=customer_ref,
        tools=bound,
        model=app_state.model,
        country=session.country,
        today=ref_date,
        trace_id=trace_id,
        observer=observer,
    )
    return TurnContext(
        session=session,
        token=token,
        trace_id=trace_id,
        stored=stored,
        bound=bound,
        tools=tools,
        ports=ports,
        observer=observer,
        recorder=recorder,
        ref_date=ref_date,
        started=perf_counter(),
    )


def select_charge(turn: TurnContext, reference: str) -> Candidate | None:
    """Make an own charge selectable; None when the reference is not the customer's.

    The transactions panel shows every own charge, so a tapped charge counts as
    shown even when the last clarification listed others. The fresh candidate
    replaces a stale one, so "already disputed" is current.
    """
    candidate = turn.bound.candidate(reference)
    if candidate is None:
        return None
    state = turn.state
    if any(item.candidate_id == reference for item in state.candidates):
        state.candidates = [candidate if item.candidate_id == reference else item for item in state.candidates]
    else:
        state.candidates = [*state.candidates, candidate]
    return candidate


def unknown_charge(turn: TurnContext) -> Handoff:
    return _handoff(
        "unknownCharge",
        None,
        None,
        language=turn.state.language.value,
        country=turn.session.country,
        trace_id=turn.trace_id,
        ref_date=turn.ref_date,
        recorder=turn.recorder,
    )


def run_turn(turn: TurnContext, turn_input: TextInput | CandidateIdInput) -> tuple[TurnOutput | None, ChatReply]:
    """Run the orchestrator once and project its output onto the reply contract."""
    try:
        output = step(turn_input, turn.state, turn.ports)
    except Exception:
        # Gold or orchestrator failure: degrade gracefully without leaking internals.
        return None, ErrorReply(message_key="errorGeneric", trace_id=turn.trace_id)

    # For FAILURE (unknown/foreign reference), strip candidate details to avoid
    # disclosing data from another customer's transaction.
    if output.kind is OutcomeKind.FAILURE:
        output = TurnOutput(kind=OutcomeKind.FAILURE, language=output.language, reason=output.reason)

    reply = _to_reply(
        output,
        turn.state,
        turn.bound,
        session=turn.session,
        trace_id=turn.trace_id,
        ref_date=turn.ref_date,
        recorder=turn.recorder,
    )
    return output, reply


def _save_ticket(request: Request, turn: TurnContext, reply: Handoff) -> None:
    facts = reply.package.verified_facts
    request.app.state.cases.add(
        CaseRow(
            case_id=reply.reference,
            customer_id=turn.session.customer_id,
            kind="handoff",
            status=ESCALATED,
            created_at=datetime.now(timezone.utc),
            transaction_id=facts.transaction_id if facts else None,
            amount=f"{facts.amount:.2f}" if facts else None,
            currency=facts.currency if facts else None,
            merchant=facts.merchant if facts else None,
            transaction_date=facts.transaction_date if facts else None,
            reason_key=reply.reason_key,
            package=reply.package.model_dump(mode="json"),
        )
    )


def finish_turn(
    request: Request,
    turn: TurnContext,
    reply: ChatReply,
    output: TurnOutput | None = None,
    *,
    policy_rule: str | None = None,
    status_code: int = 200,
) -> JSONResponse:
    """Persist the conversation, file a handoff ticket, close the turn record, reply."""
    request.app.state.conversation_store.save(turn.token, turn.stored)
    if isinstance(reply, Handoff):
        _save_ticket(request, turn, reply)
    if isinstance(reply, ErrorReply):
        outcome = "failed"
    elif output is None:
        outcome = "ok"
    else:
        outcome = _turn_outcome(output)
    turn.observer.emit(
        step="turn",
        language=turn.state.language.value,
        outcome=outcome,
        attempt=output.attempt if output is not None and output.attempt is not None else 1,
        policy_rule=policy_rule if policy_rule is not None else (output.reason if output else None),
        latency_ms=(perf_counter() - turn.started) * 1000,
        handoff=reply.package.model_dump(mode="json") if isinstance(reply, Handoff) else None,
    )
    return JSONResponse(
        status_code=status_code,
        content=reply.model_dump(mode="json"),
        headers={"X-Trace-Id": turn.trace_id},
    )


@router.post("/chat")
def chat(
    body: ChatInput,
    request: Request,
    session: Session = Depends(require_session),
) -> JSONResponse:
    turn = open_turn(request, session)

    if body.selected_reference is not None:
        if select_charge(turn, body.selected_reference) is None:
            return finish_turn(request, turn, unknown_charge(turn), policy_rule="unknownCharge")
        turn_input: TextInput | CandidateIdInput = CandidateIdInput(candidate_id=body.selected_reference)
    else:
        turn_input = TextInput(text=body.message or "")

    output, reply = run_turn(turn, turn_input)
    return finish_turn(request, turn, reply, output)
