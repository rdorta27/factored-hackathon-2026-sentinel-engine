from dataclasses import dataclass, field
from enum import StrEnum
from typing import Union


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
    CONFIRM_BOX = "confirm_box"
    CASE_NUMBER = "case_number"
    HANDOFF = "handoff"
    OFFER = "offer"
    FAILURE = "failure"


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


@dataclass
class ConversationState:
    language: Language
    turns: list[str] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    pending_confirmation: PendingConfirmation | None = None
    clarification_count: int = 0
    person_asks: int = 0
    states_not_theirs: bool = False


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
