from datetime import date

from app.ai.fake import FakeModel
from app.orchestrator.step import Ports, step
from app.orchestrator.types import (
    Candidate,
    ConversationState,
    Language,
    OutcomeKind,
    TextInput,
    TransactionStatus,
)
from app.tools.fake import InMemoryTools


def test_first_ask_offers_and_second_hands_off_without_classify() -> None:
    model = FakeModel()
    tools = InMemoryTools(
        [
            Candidate(
                "c1",
                TransactionStatus.APPROVED,
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
    first = step(TextInput("quiero una persona"), state, ports)
    second = step(TextInput("quiero una persona"), state, ports)
    assert first.kind is OutcomeKind.OFFER
    assert second.kind is OutcomeKind.HANDOFF
    assert second.reason == "person.insist"
    assert model.classify_calls == 0
    assert tools.open_calls == 0
    assert state.person_asks == 2
