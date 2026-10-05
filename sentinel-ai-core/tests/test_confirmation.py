from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date
from time import time

from app.ai.port import UnderstandKind, UnderstandResult
from app.db.session import make_engine
from app.orchestrator.step import CONFIRM_TTL_S, Ports, step
from app.orchestrator.types import (
    Candidate,
    CandidateIdInput,
    ConversationState,
    Language,
    OutcomeKind,
    TextInput,
    TransactionStatus,
)
from app.state.cases import CaseTools, InMemoryCaseRepository, SqliteCaseRepository
from app.tools.fake import InMemoryTools
from app.tools.gold import MockGoldStore
from app.tools.ports import ToolStatus


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


def test_late_confirmation_never_writes_and_asks_again() -> None:
    tools = InMemoryTools([_candidate()])
    state = ConversationState(language=Language.ES_419)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ScriptModel(), today=date(2024, 12, 1))
    step(TextInput("no reconozco este cargo Exito 85.000 2024-10-01"), state, ports)
    assert state.pending_confirmation is not None
    state.pending_confirmation = replace(
        state.pending_confirmation, created_at=time() - CONFIRM_TTL_S - 60.0
    )
    result = step(CandidateIdInput("c1"), state, ports)
    assert result.kind is OutcomeKind.CONFIRM_BOX
    assert result.case_number is None
    assert tools.open_calls == 0
    assert state.pending_confirmation is not None
    assert state.pending_confirmation.created_at > time() - CONFIRM_TTL_S


def test_fresh_confirmation_still_opens() -> None:
    tools = InMemoryTools([_candidate()])
    state = ConversationState(language=Language.ES_419)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ScriptModel(), today=date(2024, 12, 1))
    step(TextInput("no reconozco este cargo Exito 85.000 2024-10-01"), state, ports)
    assert state.pending_confirmation is not None
    state.pending_confirmation = replace(state.pending_confirmation, created_at=time())
    result = step(CandidateIdInput("c1"), state, ports)
    assert result.kind is OutcomeKind.CASE_NUMBER
    assert tools.open_calls == 1


def _parallel_opens_same_case(tools: CaseTools) -> None:
    key = "s1:c1:open_dispute"

    def confirm(n: int) -> str | None:
        opened = tools.open_dispute("c1", f"token-{n}", "Cargo duplicado", "", key)
        assert opened.status is ToolStatus.OK
        assert opened.record is not None
        return opened.record.dispute_id

    with ThreadPoolExecutor(max_workers=8) as pool:
        dispute_ids = list(pool.map(confirm, range(8)))
    assert len(set(dispute_ids)) == 1, "parallel confirmations share one case"
    assert len(tools.disputes()) == 1


def test_parallel_confirmations_open_one_case_in_memory() -> None:
    tools = CaseTools(InMemoryCaseRepository(), "CUST-0001", MockGoldStore(as_of="2024-12-01"))
    _parallel_opens_same_case(tools)


def test_parallel_confirmations_open_one_case_in_sqlite(tmp_path) -> None:  # type: ignore[no-untyped-def]
    repo = SqliteCaseRepository(make_engine(tmp_path / "cases.db"))
    tools = CaseTools(repo, "CUST-0001", MockGoldStore(as_of="2024-12-01"))
    _parallel_opens_same_case(tools)
