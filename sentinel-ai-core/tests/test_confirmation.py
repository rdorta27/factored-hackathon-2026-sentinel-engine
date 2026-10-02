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


class ScriptModel:
    def __init__(self, kind: UnderstandKind = UnderstandKind.CHARGE) -> None:
        self.kind = kind
        self.classify_calls = 0

    def understand(self, message: str, turns: list[str], context: dict | None = None) -> UnderstandResult:
        return UnderstandResult(kind=self.kind, language=Language.ES_419)

    def classify(self, message: str) -> str:
        self.classify_calls += 1
        return "Cargo duplicado"


def _candidate(status: TransactionStatus = TransactionStatus.APPROVED) -> Candidate:
    return Candidate(
        candidate_id="c1",
        status=status,
        amount="85.000",
        currency="COP",
        merchant="Exito",
        date="2024-10-01",
        as_of="2024-10-02",
    )


def test_written_yes_does_not_open() -> None:
    tools = InMemoryTools([_candidate()])
    state = ConversationState(language=Language.ES_419)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ScriptModel(), today=date(2024, 12, 1))
    first = step(TextInput("no reconozco este cargo Exito 85.000 2024-10-01"), state, ports)
    assert first.kind is OutcomeKind.CONFIRM_BOX
    second = step(TextInput("sí"), state, ports)
    assert second.kind is OutcomeKind.QUESTION
    assert state.pending_confirmation is not None
    assert tools.open_calls == 0


def test_unknown_candidate_does_not_open() -> None:
    tools = InMemoryTools([_candidate()])
    state = ConversationState(language=Language.ES_419)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ScriptModel(), today=date(2024, 12, 1))
    step(TextInput("no reconozco este cargo Exito 85.000 2024-10-01"), state, ports)
    result = step(CandidateIdInput("other"), state, ports)
    assert result.kind is OutcomeKind.FAILURE
    assert tools.open_calls == 0


def test_confirm_returns_case_number_once() -> None:
    tools = InMemoryTools([_candidate()])
    state = ConversationState(language=Language.ES_419)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ScriptModel(), today=date(2024, 12, 1))
    step(TextInput("no reconozco este cargo Exito 85.000 2024-10-01"), state, ports)
    opened = step(CandidateIdInput("c1"), state, ports)
    again = step(CandidateIdInput("c1"), state, ports)
    assert opened.kind is OutcomeKind.CASE_NUMBER
    assert opened.case_number == "D-1"
    assert again.kind is OutcomeKind.CONFIRM_BOX
    assert tools.open_calls == 1


def test_three_failed_lookups_hand_off_without_case_number() -> None:
    tools = InMemoryTools([_candidate()], lookup_failures=3)
    state = ConversationState(language=Language.ES_419)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ScriptModel(), today=date(2024, 12, 1))
    step(TextInput("no reconozco este cargo Exito 85.000 2024-10-01"), state, ports)
    result = step(CandidateIdInput("c1"), state, ports)
    assert result.kind is OutcomeKind.HANDOFF
    assert result.case_number is None
    assert result.attempt == 3
    assert len(tools.by_key) == 1
