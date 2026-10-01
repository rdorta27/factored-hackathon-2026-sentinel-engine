from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.orchestrator.types import Language


class UnderstandKind(StrEnum):
    CHARGE = "charge"
    MISSING = "missing"
    OUT_OF_SCOPE = "out_of_scope"
    PERSON = "person"


@dataclass(frozen=True)
class ModelInfo:
    model: str
    route: str
    prompt_version: str


@dataclass(frozen=True)
class UnderstandResult:
    kind: UnderstandKind
    language: Language
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0
    # The customer explicitly says the charge was not theirs. Reported, never decided here.
    not_mine: bool = False


class ModelPort(Protocol):
    def understand(self, message: str, turns: list[str]) -> UnderstandResult: ...

    def classify(self, message: str) -> str: ...

    def describe(self) -> ModelInfo: ...
