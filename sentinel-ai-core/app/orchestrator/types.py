from dataclasses import dataclass, field
from enum import StrEnum
from time import time
from typing import Any, Union


class Language(StrEnum):
    ES_419 = "es-419"
    PT_BR = "pt-BR"


class TransactionStatus(StrEnum):
    APPROVED = "Approved"
    DECLINED = "Declined"
    PENDING = "Pending"
    REVERSED = "Reversed"


class OutcomeKind(StrEnum):
    QUESTION = "question"
    EXPLAIN = "explain"
    EXPLANATION = "explanation"
    CONFIRM_BOX = "confirm_box"
    CASE_NUMBER = "case_number"
    HANDOFF = "handoff"
    OFFER = "offer"
    FAILURE = "failure"


class Phase(StrEnum):
    """Named conversation phase, derived from state plus turn outcome (REQ-0001).

    Never stored as separate mutable state: ``phase_of`` computes it, and only
    the handoff package and the turn record carry the value.
    """

    COLLECTING = "collecting"
    CLARIFYING = "clarifying"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    RESOLVED = "resolved"
    HANDED_OFF = "handed_off"


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    status: TransactionStatus
    amount: str
    currency: str
    merchant: str
    date: str
    as_of: str
    fraud_score: float | None = None
    is_disputed: bool = False
    gold_eligible: bool | None = None

    def __post_init__(self) -> None:
        if not self.currency.strip():
            raise ValueError("currency is required")


@dataclass(frozen=True)
class PendingConfirmation:
    candidate_id: str
    action: str
    category: str
    # Epoch seconds when the box opened. A confirmation older than
    # CONFIRM_TTL_S (step.py) never writes; the loop asks again.
    created_at: float = field(default_factory=time)


@dataclass
class LastDecision:
    """The last policy decision shown to the customer (REQ-0033).

    A snapshot, never recomputed: ``values`` holds only verified values read
    from the country file and the verified candidate at decision time. Only
    rules that have an explanation are recorded.
    """

    rule_id: str
    candidate_id: str | None = None
    policy_version: str | None = None
    values: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationState:
    language: Language
    turns: list[str] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    pending_confirmation: PendingConfirmation | None = None
    clarification_count: int = 0
    person_asks: int = 0
    # Consecutive out-of-scope turns: the first explains and offers, the second hands off.
    scope_asks: int = 0
    states_not_theirs: bool = False
    # Denied or superseded candidate ids: never shown again (REQ-0001).
    rejected_ids: list[str] = field(default_factory=list)
    # Last system question codes (e.g. "missing", "which_charge"), newest last,
    # capped at two: the system-side half of the model digest (REQ-0001).
    sys_questions: list[str] = field(default_factory=list)
    # Reference of the ticket filed for this conversation. A conversation files
    # at most one: later turns that hand off again point at the same ticket.
    handoff_reference: str | None = None
    # Last explainable policy decision, kept for a "why" follow-up (REQ-0033).
    last_decision: LastDecision | None = None


@dataclass(frozen=True)
class TextInput:
    text: str


@dataclass(frozen=True)
class CandidateIdInput:
    candidate_id: str


TurnInput = Union[TextInput, CandidateIdInput]


@dataclass(frozen=True)
class TurnOutput:
    kind: OutcomeKind
    language: Language
    text: str = ""
    candidate: Candidate | None = None
    case_number: str | None = None
    reason: str | None = None
    attempt: int | None = None
    category: str | None = None
    # Explanation reply: a translation key plus verified values, no prose.
    explanation_key: str | None = None
    explanation_values: dict[str, Any] = field(default_factory=dict)
    # Text reply: the reviewed template variant chosen for this turn.
    message_key: str | None = None


def phase_of(state: ConversationState, output: TurnOutput | None = None) -> Phase:
    """Derive the named phase from state plus, when given, the turn outcome."""
    if output is not None:
        if output.kind is OutcomeKind.HANDOFF:
            return Phase.HANDED_OFF
        if output.kind is OutcomeKind.CASE_NUMBER:
            return Phase.RESOLVED
        if output.kind is OutcomeKind.CONFIRM_BOX:
            return Phase.AWAITING_CONFIRMATION
        if output.kind is OutcomeKind.QUESTION:
            return Phase.CLARIFYING if state.clarification_count > 0 else Phase.COLLECTING
        return Phase.COLLECTING
    if state.pending_confirmation is not None:
        return Phase.AWAITING_CONFIRMATION
    if state.clarification_count > 0:
        return Phase.CLARIFYING
    return Phase.COLLECTING
