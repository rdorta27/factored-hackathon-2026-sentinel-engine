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
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from time import perf_counter

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.observability import Recorder, TurnObserver
from app.orchestrator.step import Ports, step
from app.privacy import mask
from app.orchestrator.types import (
    Candidate,
    CandidateIdInput,
    ConversationState,
    Language,
    OutcomeKind,
    Phase,
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
    ConversationTurn,
    ErrorReply,
    Explanation,
    ExplanationValues,
    Handoff,
    HandoffAction,
    HandoffPackage,
    MessageKeys,
    TextReply,
    TransactionFacts,
    VerifiedFacts,
)
from app.session.models import Session
from app.session.router import SESSION_COOKIE, require_customer
from app.state.cases import ESCALATED, CaseRow, CaseTools
from app.state.conversation import StoredConversation
from app.tools.bound import SessionBoundLookup

router = APIRouter(prefix="/api/v1", tags=["chat"])

# Policy rule or orchestrator reason → translation key shown to the customer.
_TEXT_KEYS = {
    "person.ask": "person.ask",
    "out_of_scope.ask": "out_of_scope.ask",
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
    "fraud.claim": "handoff.review",
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
    "fraud.claim": "customer_states_not_theirs",
    "amount.high": "amount_above_threshold",
    "out_of_scope": "request_outside_scope",
    "model_unavailable": "intent_not_understood",
}
_ACTION_STEPS = {"decide", "act", "verify", "escalate"}
# Per-session retention bound: oldest entries are discarded with an overflow
# mark once exceeded (REQ-0001, REQ-0027).
MAX_HISTORY = 50
MAX_ACTIONS = 200

# Reply kind → derived conversation phase carried on the turn record.
_REPLY_PHASES = {
    "clarification": Phase.CLARIFYING.value,
    "confirm_box": Phase.AWAITING_CONFIRMATION.value,
    "case_confirmation": Phase.RESOLVED.value,
    "handoff": Phase.HANDED_OFF.value,
}


# Response language of the interface. The five locales are the ones the selector
# offers; the orchestrator knows two, so the regional nuance stays in the
# frontend dictionary and only the base language crosses this boundary.
_LOCALE_TO_LANGUAGE = {
    "es-419": Language.ES_419,
    "es-MX": Language.ES_419,
    "es-CO": Language.ES_419,
    "es-AR": Language.ES_419,
    "pt-BR": Language.PT_BR,
}


def _as_language(locale: str | None) -> Language | None:
    """Map a selector locale to the language the service answers in."""
    if locale is None:
        return None
    return _LOCALE_TO_LANGUAGE.get(locale)


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
        phase=Phase.HANDED_OFF.value,
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
        if state.pending_confirmation is not None:
            # A message that is not a person request does not confirm, but the
            # box is still open: show it again instead of a confusing "which
            # charge", so the customer can press the button (REQ-0006).
            pending = next(
                (
                    item
                    for item in state.candidates
                    if item.candidate_id == state.pending_confirmation.candidate_id
                ),
                None,
            )
            if pending is not None:
                return ConfirmBox(
                    message_key="confirmCharge",
                    candidate=candidate_view(pending, session.country, ref_date),
                )
        if not state.candidates:
            # Nothing shown yet: offer the customer's own charges as chips.
            state.candidates = bound.lookup_transactions()
        shown = [
            item for item in state.candidates if item.candidate_id not in state.rejected_ids
        ][:4]
        return Clarification(
            message_key="clarifyWhichCharge",
            missing="transaction",
            candidates=[
                candidate_view(item, session.country, ref_date) for item in shown
            ],
        )
    if kind in (OutcomeKind.EXPLAIN, OutcomeKind.OFFER):
        return TextReply(message_key=_TEXT_KEYS.get(output.reason or "", "greetingHelp"))
    if kind is OutcomeKind.EXPLANATION:
        return Explanation(
            message_key=output.explanation_key or "explanation.none",
            rule_id=output.reason,
            values=ExplanationValues(**output.explanation_values),
        )
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
    # Language the interface asked for, and what the model detected. Kept apart
    # so the turn record can report both without lying.
    selected_language: Language | None = None
    detected_language: Language | None = None

    @property
    def state(self) -> ConversationState:
        return self.stored.state


def rate_limited(request: Request, session: Session) -> JSONResponse | None:
    """429 when the session exhausted its write budget, else None.

    Shared by ``POST /api/v1/chat`` and ``POST /api/v1/disputes``: every
    authenticated write costs one unit, so a script cannot burn unbounded
    model calls or fill the case store from one session.
    """
    limiter = getattr(request.app.state, "write_limiter", None)
    if limiter is None or limiter.allow(f"write:{session.token}"):
        return None
    trace_id: str = getattr(request.state, "trace_id", None) or secrets.token_hex(8)
    request.app.state.audit.emit("rate_limited", trace_id)
    return JSONResponse(status_code=429, content={"detail": "Too many requests"})


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
    """Run the orchestrator once and project its output onto the reply contract.

    Two languages are kept apart on purpose:

    * **understanding** — what the model detected from the text. It stays as the
      model reported it, so the turn record and the logs do not lie about what
      was understood.
    * **response** — what the customer picked in the interface. It decides the
      language of everything the service generates afterwards: the reply, the
      handoff ticket and the stored state.

    The selector wins over detection for the *response* only. Without a selector,
    both are the detected language, which is the behaviour before this change.
    """
    try:
        output = step(turn_input, turn.state, turn.ports)
    except Exception:
        # Gold or orchestrator failure: degrade gracefully without leaking internals.
        return None, ErrorReply(message_key="errorGeneric", trace_id=turn.trace_id)

    detected = output.language
    turn.detected_language = detected
    if turn.selected_language is not None:
        # Response language: applied after the loop, before anything is rendered,
        # ticketed or stored.
        turn.state.language = turn.selected_language
        output = replace(output, language=turn.selected_language)

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


_CUSTOMER_PHRASES = {
    "described_charge": "described a charge",
    "unclear_charge": "described a charge the system could not single out",
    "selected_charge": "selected a charge",
    "selected_unknown_charge": "selected a charge not in their account",
    "asked_for_person": "asked for a person",
    "asked_why": "asked why a decision was made",
    "out_of_scope": "asked for something outside disputes",
    "not_understood": "sent a message the system could not understand",
}


def _turn_entry(
    number: int,
    turn_input: TextInput | CandidateIdInput | None,
    reply: ChatReply,
    output: TurnOutput | None,
    policy_rule: str | None,
) -> ConversationTurn:
    """What happened in one turn, as codes and references (REQ-0008: no raw transcript)."""
    reason = policy_rule or (output.reason if output is not None else None)
    charge: str | None = None
    if isinstance(turn_input, CandidateIdInput):
        # An unverified reference (possibly another customer's) never enters the ticket.
        known = reason not in ("unknownCharge", "unknown_candidate")
        charge = turn_input.candidate_id if known else None
        customer = "selected_charge" if known else "selected_unknown_charge"
    elif reason and reason.startswith("person."):
        customer = "asked_for_person"
    elif reason == "out_of_scope":
        customer = "out_of_scope"
    elif reason == "model_unavailable":
        customer = "not_understood"
    elif isinstance(reply, Explanation):
        customer = "asked_why"
    elif isinstance(reply, Clarification):
        customer = "unclear_charge"
    else:
        customer = "described_charge"
    if charge is None and output is not None and output.candidate is not None:
        charge = output.candidate.candidate_id
    if isinstance(reply, (TextReply, Clarification, ConfirmBox, ErrorReply, Explanation)):
        rule = reason or reply.message_key
    elif isinstance(reply, Handoff):
        rule = reason or reply.reason_key
    else:
        rule = reason
    return ConversationTurn(
        turn=number,
        customer=customer,
        charge=charge,
        system=reply.kind,
        rule=rule,
        phase=_REPLY_PHASES.get(reply.kind, Phase.COLLECTING.value),
    )


def _system_phrase(entry: ConversationTurn) -> str:
    if entry.rule == "person.ask":
        return "offered help once (person.ask)"
    rule = f" ({entry.rule})" if entry.rule else ""
    return {
        "text": f"explained{rule}",
        "explanation": f"explained the decision{rule}",
        "clarification": "asked which charge",
        "confirm_box": "showed the confirm box",
        "case_confirmation": "opened and verified a case",
        "handoff": f"handed off{rule}",
        "error": "failed with a generic error",
    }.get(entry.system, entry.system)


def summarize(turns: list[ConversationTurn]) -> str:
    """Deterministic advisor summary built only from the structured turns."""
    parts = []
    for entry in turns:
        charge = f" {entry.charge}" if entry.charge else ""
        parts.append(
            f"Turn {entry.turn}: customer {_CUSTOMER_PHRASES.get(entry.customer, entry.customer)}{charge}; "
            f"system {_system_phrase(entry)}."
        )
    count = len(turns)
    return f"{count} turn{'s' if count != 1 else ''}. " + " ".join(parts)


def finish_turn(
    request: Request,
    turn: TurnContext,
    reply: ChatReply,
    output: TurnOutput | None = None,
    *,
    policy_rule: str | None = None,
    status_code: int = 200,
    turn_input: TextInput | CandidateIdInput | None = None,
) -> JSONResponse:
    """Record the turn in the history, complete a handoff package with the whole
    conversation, persist, file the ticket, close the turn record, reply."""
    stored = turn.stored
    number = len(stored.history) + 1
    stored.history.append(_turn_entry(number, turn_input, reply, output, policy_rule).model_dump(mode="json"))
    stored.actions.extend(
        HandoffAction(
            turn=number,
            step=record.step,
            tool=record.tool,
            outcome=record.outcome,
            attempt=record.attempt,
            policy_rule=record.policy_rule,
        ).model_dump(mode="json")
        for record in turn.recorder.records_for(turn.trace_id)
        if record.step in _ACTION_STEPS
    )
    if len(stored.history) > MAX_HISTORY:
        del stored.history[: len(stored.history) - MAX_HISTORY]
        stored.overflow = True
    if len(stored.actions) > MAX_ACTIONS:
        del stored.actions[: len(stored.actions) - MAX_ACTIONS]
        stored.overflow = True
    if isinstance(reply, Handoff):
        conversation = [ConversationTurn.model_validate(item) for item in stored.history]
        update: dict = {
            "summary": summarize(conversation),
            "conversation": conversation,
            "actions_taken": [HandoffAction.model_validate(item) for item in stored.actions],
        }
        if reply.package.verified_facts is None:
            # The escalating turn named no charge (e.g. "a person, please"): hand over
            # the last charge verified earlier in the session, if any.
            last = next((entry.charge for entry in reversed(conversation) if entry.charge), None)
            candidate = next((item for item in turn.state.candidates if item.candidate_id == last), None)
            if candidate is not None:
                update["verified_facts"] = _verified_facts(candidate, turn.session.country, turn.ref_date)
        reply = reply.model_copy(update={"package": reply.package.model_copy(update=update)})
    new_ticket = False
    if isinstance(reply, Handoff):
        if turn.state.handoff_reference is None:
            turn.state.handoff_reference = reply.reference
            new_ticket = True
        else:
            # Already handed off: the advisor has the case, so repeated turns do
            # not file another ticket and keep pointing at the first one.
            reply = reply.model_copy(update={"reference": turn.state.handoff_reference})
    request.app.state.conversation_store.save(turn.token, stored)
    if new_ticket:
        _save_ticket(request, turn, reply)  # type: ignore[arg-type]
    if isinstance(reply, ErrorReply):
        outcome = "failed"
    elif output is None:
        outcome = "ok"
    else:
        outcome = _turn_outcome(output)
    turn.observer.emit(
        step="turn",
        language=turn.state.language.value,
        detected_language=(
            turn.detected_language.value
            if turn.detected_language is not None
            else turn.state.language.value
        ),
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
    session: Session = Depends(require_customer),
) -> JSONResponse:
    blocked = rate_limited(request, session)
    if blocked is not None:
        return blocked
    turn = open_turn(request, session)
    # Response language from the interface. `None` keeps the previous behaviour:
    # the language the model detects from the message decides.
    turn.selected_language = _as_language(body.language)

    if body.selected_reference is not None:
        turn_input: TextInput | CandidateIdInput = CandidateIdInput(candidate_id=body.selected_reference)
        if select_charge(turn, body.selected_reference) is None:
            return finish_turn(
                request, turn, unknown_charge(turn), policy_rule="unknownCharge", turn_input=turn_input
            )
    else:
        # REQ-0047: this is the single place free customer text enters the
        # system. It is masked here, at the boundary, so the orchestrator, the
        # model and the conversation state never hold a raw identifier.
        # `tests/privacy/test_masking.py` fails if another TextInput is built
        # without going through `mask`.
        turn_input = TextInput(text=mask(body.message or ""))

    output, reply = run_turn(turn, turn_input)
    return finish_turn(request, turn, reply, output, turn_input=turn_input)
