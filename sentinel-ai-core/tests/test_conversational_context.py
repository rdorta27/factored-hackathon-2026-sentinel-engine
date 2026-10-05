"""Conversational context acceptance (REQ-0001): turns reach the model, denial
memory, repair re-anchoring, language persistence, bounded history, phase."""

from datetime import date

from fastapi.testclient import TestClient

from app.ai.port import ModelInfo, UnderstandKind, UnderstandResult
from app.main import create_app
from app.orchestrator.step import Ports, step
from app.orchestrator.types import (
    Candidate,
    ConversationState,
    Language,
    OutcomeKind,
    Phase,
    TextInput,
    TransactionStatus,
    TurnOutput,
    phase_of,
)
from app.session.router import SESSION_COOKIE
from app.tools.fake import InMemoryTools

PASSWORD = "Testpass-001"
TODAY = date(2026, 6, 17)


def _row(candidate_id: str, merchant: str, amount: str, day: str) -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        status=TransactionStatus.APPROVED,
        amount=amount,
        currency="MXN",
        merchant=merchant,
        date=f"2026-06-{day}",
        as_of="2026-06-17",
    )


def _tools() -> InMemoryTools:
    return InMemoryTools(
        [
            _row("c1", "ACME Store", "1000.00", "10"),
            _row("c2", "Cafe Central", "320.00", "12"),
            _row("c3", "ACME Store", "500.00", "11"),
        ]
    )


class _Base:
    def describe(self) -> ModelInfo:
        return ModelInfo(model="test", route="test", prompt_version="v1")

    def classify(self, message: str) -> str:
        return "Cargo no reconocido"


class RecordingModel(_Base):
    """Captures what the loop hands to the model."""

    def __init__(self) -> None:
        self.seen: dict = {}

    def understand(
        self, message: str, turns: list[str], context: dict | None = None
    ) -> UnderstandResult:
        self.seen = {"turns": list(turns), "context": context}
        language = Language.PT_BR if "cobran" in message else Language.ES_419
        return UnderstandResult(UnderstandKind.CHARGE, language)


class VagueModel(_Base):
    def understand(
        self, message: str, turns: list[str], context: dict | None = None
    ) -> UnderstandResult:
        language = Language.PT_BR if "cobran" in message else Language.ES_419
        return UnderstandResult(UnderstandKind.MISSING, language)


class DenyModel(_Base):
    def understand(
        self, message: str, turns: list[str], context: dict | None = None
    ) -> UnderstandResult:
        return UnderstandResult(UnderstandKind.CHARGE, Language.ES_419, not_mine=True)


def _ports(model: _Base) -> Ports:
    return Ports(idempotency_scope="s1", tools=_tools(), model=model, today=TODAY)  # type: ignore[arg-type]


def test_model_receives_prior_turns_and_digest() -> None:
    model = RecordingModel()
    state = ConversationState(language=Language.ES_419)
    ports = _ports(model)
    step(TextInput("primero"), state, ports)
    step(TextInput("segundo"), state, ports)
    assert model.seen["turns"] == ["primero", "segundo"], "no turn is dropped"
    assert model.seen["context"] == {
        "sys_questions": ["which_charge"],
        "shown_ids": [item.candidate_id for item in state.candidates[:4]],
    }


def test_third_clarification_hands_off() -> None:
    state = ConversationState(language=Language.ES_419)
    ports = _ports(VagueModel())
    # A greeting is now an opener (`chat-start`), so vague turns stay vague.
    assert step(TextInput("mmm"), state, ports).kind is OutcomeKind.QUESTION
    assert step(TextInput("no se"), state, ports).kind is OutcomeKind.QUESTION
    third = step(TextInput("que hago"), state, ports)
    assert third.kind is OutcomeKind.HANDOFF
    assert third.reason == "fields.missing"
    assert state.clarification_count == 2


def test_denied_charge_never_reappears() -> None:
    state = ConversationState(language=Language.ES_419)
    ports = _ports(DenyModel())
    first = step(TextInput("hola"), state, ports)
    assert first.kind is OutcomeKind.QUESTION
    shown = [item.candidate_id for item in state.candidates]
    assert shown, "something was shown to deny"
    second = step(TextInput("no fui yo"), state, ports)
    assert second.kind is OutcomeKind.QUESTION
    assert state.rejected_ids == shown
    assert all(item.candidate_id not in shown for item in state.candidates)


def test_correction_reanchors_to_the_repaired_candidate() -> None:
    state = ConversationState(language=Language.ES_419)
    ports = _ports(RecordingModel())
    first = step(TextInput("cargo en ACME Store"), state, ports)
    assert first.kind is OutcomeKind.QUESTION
    old = [item.candidate_id for item in state.candidates]
    assert len(old) > 1
    repaired = step(TextInput("no, el del 10 de junio por 1.000,00"), state, ports)
    assert repaired.kind is OutcomeKind.CONFIRM_BOX
    assert repaired.candidate is not None and repaired.candidate.candidate_id == "c1"
    assert "c1" not in state.rejected_ids
    assert all(item in state.rejected_ids for item in old if item != "c1")


def test_language_persists_across_turns_and_switch() -> None:
    state = ConversationState(language=Language.ES_419)
    ports = _ports(VagueModel())
    step(TextInput("hola"), state, ports)
    assert state.language is Language.ES_419
    step(TextInput("sigues ahi"), state, ports)
    assert state.language is Language.ES_419
    step(TextInput("tem uma cobrança"), state, ports)
    assert state.language is Language.PT_BR
    step(TextInput("outra cobrança"), state, ports)
    assert state.language is Language.PT_BR


def test_phase_is_derived_and_reported() -> None:
    assert phase_of(ConversationState(language=Language.ES_419)) is Phase.COLLECTING
    state = ConversationState(language=Language.ES_419)
    ports = _ports(VagueModel())
    output = step(TextInput("no se"), state, ports)
    assert phase_of(state, output) is Phase.CLARIFYING
    assert phase_of(
        state,
        TurnOutput(kind=OutcomeKind.HANDOFF, language=Language.ES_419, reason="fields.missing"),
    ) is Phase.HANDED_OFF

    api = TestClient(create_app())
    assert (
        api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code
        == 200
    )
    api.post("/api/v1/chat", json={"message": "HOLA"})
    api.post("/api/v1/chat", json={"message": "HOLA OTRA VEZ"})
    body = api.post("/api/v1/chat", json={"message": "HOLA DE NUEVO"}).json()
    assert body["kind"] == "handoff"
    assert [entry["phase"] for entry in body["package"]["conversation"]] == [
        "clarifying",
        "clarifying",
        "handed_off",
    ]


def test_history_is_bounded_with_an_overflow_mark() -> None:
    api = TestClient(create_app())
    assert (
        api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code
        == 200
    )
    for number in range(55):
        assert api.post("/api/v1/chat", json={"message": f"hola {number}"}).status_code == 200
    token = api.cookies.get(SESSION_COOKIE)
    assert token is not None
    stored = api.app.state.conversation_store.get(token)
    assert stored is not None
    assert len(stored.history) == 50
    assert stored.overflow is True
    assert stored.history[0]["turn"] == 6, "oldest entries are discarded first"
    assert len(stored.state.turns) == 50, "the stored turn window is bounded too"
