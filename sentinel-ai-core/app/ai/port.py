from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from app.orchestrator.types import Language


class UnderstandKind(StrEnum):
    CHARGE = "charge"
    STATUS = "status"
    MISSING = "missing"
    OUT_OF_SCOPE = "out_of_scope"
    PERSON = "person"


# Subtypes for contract v3: openers stay ``missing`` with a subtype, so the
# intent block of eval-v7 stays comparable. New fields stay optional.
SUBTYPE_MISSING = frozenset({"greeting", "thanks", "goodbye", "identity", "help", "unclear"})
SUBTYPE_OUT_OF_SCOPE = frozenset({"balance", "loan", "card", "address", "transfer", "other"})


@dataclass(frozen=True)
class ModelInfo:
    model: str
    route: str
    prompt_version: str


@dataclass(frozen=True)
class UnderstandSlots:
    """Hints from the customer words, never facts. Code matches each slot
    against verified candidates; a slot that matches nothing is dropped."""

    merchant_words: str | None = None
    amount: float | None = None
    date_phrase: str | None = None
    twice: bool = False


@dataclass(frozen=True)
class UnderstandResult:
    kind: UnderstandKind
    language: Language
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    # The customer explicitly says the charge was not theirs. Reported, never decided here.
    not_mine: bool = False
    # The router's confidence in its label, 0 to 1, when the provider returned
    # log-probabilities; None otherwise. Reported, never decided here.
    confidence: float | None = None
    # Contract v3, all optional so v1, v2 and the baseline still fit.
    subtype: str | None = None
    slots: UnderstandSlots = field(default_factory=UnderstandSlots)
    # Draft wording with placeholders only, for turns that do not decide.
    reply_draft: str | None = None


class ModelPort(Protocol):
    def understand(
        self, message: str, turns: list[str], context: dict | None = None
    ) -> UnderstandResult: ...

    def classify(self, message: str) -> str: ...

    def describe(self) -> ModelInfo: ...
