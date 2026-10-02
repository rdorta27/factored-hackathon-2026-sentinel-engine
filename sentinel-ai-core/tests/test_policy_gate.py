from datetime import date

from app.ai.port import UnderstandKind, UnderstandResult
from app.orchestrator.step import Ports, step
from app.orchestrator.types import (
    Candidate,
    CandidateIdInput,
    ConversationState,
    Language,
    OutcomeKind,
    TextInput,
    TransactionStatus,
)
from app.tools.fake import InMemoryTools


class ChargeModel:
    def __init__(self) -> None:
        self.classify_calls = 0

    def understand(self, message: str, turns: list[str], context: dict | None = None) -> UnderstandResult:
        return UnderstandResult(UnderstandKind.CHARGE, Language.ES_419)

    def classify(self, message: str) -> str:
        self.classify_calls += 1
        return "Cargo no reconocido"


def test_reversed_charge_rejects_open_and_skips_classify() -> None:
    model = ChargeModel()
    tools = InMemoryTools(
        [
            Candidate(
                "c1",
                TransactionStatus.REVERSED,
                "10",
                "MXN",
                "ACME",
                "2024-11-01",
                "2024-11-02",
            )
        ]
    )
    ports = Ports("s1", tools, model, today=date(2024, 12, 1))
    state = ConversationState(language=Language.ES_419)
    result = step(TextInput("no reconozco este cargo ACME 10.00 2024-11-01"), state, ports)
    assert result.kind is OutcomeKind.EXPLAIN
    assert result.reason == "status.reversed"
    assert model.classify_calls == 0
    assert tools.open_calls == 0


def test_window_expired_before_confirm_does_not_open() -> None:
    model = ChargeModel()
    tools = InMemoryTools(
        [
            Candidate(
                "c1",
                TransactionStatus.APPROVED,
                "10",
                "MXN",
                "ACME",
                "2024-10-01",
                "2024-10-02",
            )
        ]
    )
    shown = Ports("s1", tools, model, today=date(2024, 12, 1))
    state = ConversationState(language=Language.ES_419)
    box = step(TextInput("no reconozco este cargo ACME 10.00 2024-10-01"), state, shown)
    assert box.kind is OutcomeKind.CONFIRM_BOX
    expired = Ports("s1", tools, model, today=date(2025, 1, 15))
    result = step(CandidateIdInput("c1"), state, expired)
    assert result.kind is OutcomeKind.EXPLAIN
    assert result.reason == "window.expired"
    assert tools.open_calls == 0
