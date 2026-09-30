from dataclasses import dataclass
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
from app.policy.engine import PolicyFacts, PolicyOutcome, evaluate
from app.tools.ports import ToolStatus, TransactionLookup

MAX_ATTEMPTS = 3
OPEN_ACTION = "open_dispute"


@dataclass
class Ports:
    session_ref: str
    tools: TransactionLookup
    model: ModelPort


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
        return TurnOutput(kind=OutcomeKind.HANDOFF, language=state.language, reason="person")
    candidates = ports.tools.lookup_transactions()
    state.candidates = candidates
    if not candidates:
        state.clarification_count += 1
        return TurnOutput(kind=OutcomeKind.QUESTION, language=state.language)
    selected = candidates[0]
    outcome = evaluate(PolicyFacts(status=selected.status))
    if outcome is PolicyOutcome.EXPLAIN_STATUS:
        return TurnOutput(
            kind=OutcomeKind.EXPLAIN,
            language=state.language,
            candidate=selected,
            reason=selected.status.value,
        )
    if outcome is PolicyOutcome.HANDOFF:
        return TurnOutput(kind=OutcomeKind.HANDOFF, language=state.language, reason="policy")
    category = ports.model.classify(turn.text)
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
    )


def _confirm(
    turn: CandidateIdInput, state: ConversationState, ports: Ports
) -> TurnOutput:
    pending = state.pending_confirmation
    shown = {item.candidate_id for item in state.candidates}
    if pending is None or turn.candidate_id != pending.candidate_id or turn.candidate_id not in shown:
        return TurnOutput(kind=OutcomeKind.FAILURE, language=state.language, reason="unknown_candidate")
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


def shown_candidate(state: ConversationState, candidate_id: str) -> Candidate | None:
    for item in state.candidates:
        if item.candidate_id == candidate_id:
            return item
    return None
