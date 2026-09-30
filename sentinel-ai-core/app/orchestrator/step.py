from dataclasses import dataclass
from datetime import date
from uuid import uuid4

from app.ai.port import ModelPort, UnderstandKind
from app.orchestrator.types import (
    Candidate,
    CandidateIdInput,
    ConversationState,
    OutcomeKind,
    PendingConfirmation,
    TextInput,
    TurnInput,
    TurnOutput,
)
from app.policy.engine import HitOutcome, Intent, PolicyHit, PolicyRequest, evaluate
from app.policy.load import load_country
from app.tools.ports import ToolStatus, TransactionLookup

MAX_ATTEMPTS = 3
OPEN_ACTION = "open_dispute"


@dataclass
class Ports:
    session_ref: str
    tools: TransactionLookup
    model: ModelPort
    country: str = "MX"
    today: date | None = None


def step(turn: TurnInput, state: ConversationState, ports: Ports) -> TurnOutput:
    if isinstance(turn, CandidateIdInput):
        return _confirm(turn, state, ports)
    return _on_text(turn, state, ports)


def _on_text(turn: TextInput, state: ConversationState, ports: Ports) -> TurnOutput:
    state.turns.append(turn.text)
    if state.pending_confirmation is not None:
        return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language, text=turn.text)
    understood = ports.model.understand(turn.text, state.turns)
    state.language = understood.language
    if understood.kind is UnderstandKind.MISSING:
        state.clarification_count += 1
        return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language)
    if understood.kind is UnderstandKind.OUT_OF_SCOPE:
        return TurnOutput(
            kind=OutcomeKind.HANDOFF,
            language=state.language,
            reason="out_of_scope",
        )
    if understood.kind is UnderstandKind.PERSON:
        state.person_asks += 1
        hit = _hit(state, ports, Intent.PERSON, None)
        return _from_hit(hit, state, None)
    candidates = ports.tools.lookup_transactions()
    state.candidates = candidates
    if not candidates:
        state.clarification_count += 1
        return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language)
    selected = candidates[0]
    return _after_policy(state, ports, Intent.CHARGE, selected, turn.text)


def _confirm(
    turn: CandidateIdInput, state: ConversationState, ports: Ports
) -> TurnOutput:
    pending = state.pending_confirmation
    shown = {item.candidate_id for item in state.candidates}
    if pending is None or turn.candidate_id != pending.candidate_id or turn.candidate_id not in shown:
        return TurnOutput(kind=OutcomeKind.FAILURE, language=state.language, reason="unknown_candidate")
    selected = shown_candidate(state, turn.candidate_id)
    hit = _hit(state, ports, Intent.DISPUTE, selected)
    if hit.outcome is not HitOutcome.ALLOW:
        return _from_hit(hit, state, selected)
    token = uuid4().hex
    key = f"{ports.session_ref}:{pending.candidate_id}:{pending.action}"
    opened = ports.tools.open_dispute(
        pending.candidate_id,
        token,
        pending.category,
        "",
        key,
    )
    if opened.status is not ToolStatus.OK or opened.record is None:
        return _unverified(state, 1)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        found = ports.tools.lookup_dispute(opened.record.dispute_id)
        if found is not None:
            state.pending_confirmation = None
            return TurnOutput(
                kind=OutcomeKind.CASE_NUMBER,
                language=state.language,
                case_number=found.dispute_id,
                attempt=attempt,
                category=found.category,
            )
        if attempt < MAX_ATTEMPTS:
            ports.tools.open_dispute(
                pending.candidate_id,
                None,
                pending.category,
                "",
                key,
            )
    return _unverified(state, MAX_ATTEMPTS)


def _unverified(state: ConversationState, attempt: int) -> TurnOutput:
    state.pending_confirmation = None
    return TurnOutput(
        kind=OutcomeKind.HANDOFF,
        language=state.language,
        reason="unverified",
        attempt=attempt,
    )


def _hit(
    state: ConversationState,
    ports: Ports,
    intent: Intent,
    candidate: Candidate | None,
) -> PolicyHit:
    policy = load_country(ports.country)
    today = ports.today or (policy.demo_today if policy else date(2026, 6, 17))
    return evaluate(
        PolicyRequest(
            intent=intent,
            country=ports.country,
            today=today,
            candidate=candidate,
            clarification_count=state.clarification_count,
            person_asks=state.person_asks,
            policy=policy,
        )
    )


def _after_policy(
    state: ConversationState,
    ports: Ports,
    intent: Intent,
    selected: Candidate,
    message: str,
) -> TurnOutput:
    hit = _hit(state, ports, intent, selected)
    if hit.outcome is not HitOutcome.ALLOW:
        return _from_hit(hit, state, selected)
    category = ports.model.classify(message)
    state.pending_confirmation = PendingConfirmation(
        candidate_id=selected.candidate_id,
        action=OPEN_ACTION,
        category=category,
    )
    return TurnOutput(
        kind=OutcomeKind.CONFIRM_BOX,
        language=state.language,
        candidate=selected,
        category=category,
        reason=hit.rule_id,
    )


def _from_hit(
    hit: PolicyHit, state: ConversationState, candidate: Candidate | None
) -> TurnOutput:
    kind = {
        HitOutcome.EXPLAIN: OutcomeKind.EXPLAIN,
        HitOutcome.HANDOFF: OutcomeKind.HANDOFF,
        HitOutcome.OFFER: OutcomeKind.OFFER,
        HitOutcome.ALLOW: OutcomeKind.CONFIRM_BOX,
    }[hit.outcome]
    return TurnOutput(
        kind=kind,
        language=state.language,
        candidate=candidate,
        reason=hit.rule_id,
    )


def shown_candidate(state: ConversationState, candidate_id: str) -> Candidate | None:
    for item in state.candidates:
        if item.candidate_id == candidate_id:
            return item
    return None
