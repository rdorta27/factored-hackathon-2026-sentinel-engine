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
class UnderstandResult:
    kind: UnderstandKind
    language: Language


class ModelPort(Protocol):
    def understand(self, message: str, turns: list[str]) -> UnderstandResult: ...

    def classify(self, message: str) -> str: ...
