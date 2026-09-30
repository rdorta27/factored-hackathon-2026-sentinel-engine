from datetime import date

import pytest

from app.ai.fake import FakeModel
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


def _candidate() -> Candidate:
    return Candidate(
        candidate_id="c1",
        status=TransactionStatus.APPROVED,
        amount="85.000",
        currency="COP",
        merchant="Exito",
        date="2024-10-01",
        as_of="2024-10-02",
    )


def _ports(model: FakeModel) -> tuple[InMemoryTools, Ports]:
    tools = InMemoryTools([_candidate()])
    return tools, Ports(idempotency_scope="s1", tools=tools, model=model, today=date(2024, 12, 1))


@pytest.mark.parametrize(
    ("text", "language", "category"),
    [
        ("no reconozco este cargo Exito 85.000 2024-10-01", Language.ES_419, "Cargo no reconocido"),
        ("não reconheço esta cobrança Exito 85.000 2024-10-01", Language.PT_BR, "Cargo no reconocido"),
    ],
)
def test_normal_case_confirms_then_returns_case_number(
    text: str, language: Language, category: str
) -> None:
    model = FakeModel()
    tools, ports = _ports(model)
    state = ConversationState(language=language)
    shown = step(TextInput(text), state, ports)
    opened = step(CandidateIdInput("c1"), state, ports)
    assert shown.kind is OutcomeKind.CONFIRM_BOX
    assert shown.case_number is None
    assert shown.language is language
    assert opened.kind is OutcomeKind.CASE_NUMBER
    assert opened.case_number == "D-1"
    assert opened.category == category
    assert tools.open_calls == 1


def test_duplicate_charge_is_the_normal_case_with_another_category() -> None:
    model = FakeModel()
    tools, ports = _ports(model)
    state = ConversationState(language=Language.ES_419)
    shown = step(TextInput("me cobraron dos veces Exito 85.000 2024-10-01"), state, ports)
    opened = step(CandidateIdInput("c1"), state, ports)
    assert shown.kind is OutcomeKind.CONFIRM_BOX
    assert opened.category == "Cargo duplicado"
    assert tools.open_calls == 1


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("hay un problema", Language.ES_419),
        ("tem um problema", Language.PT_BR),
    ],
)
def test_ambiguous_case_asks_and_does_not_open(text: str, language: Language) -> None:
    model = FakeModel()
    tools, ports = _ports(model)
    state = ConversationState(language=language)
    result = step(TextInput(text), state, ports)
    assert result.kind is OutcomeKind.QUESTION
    assert result.language is language
    assert tools.open_calls == 0
    assert model.classify_calls == 0


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("cuál es mi saldo", Language.ES_419),
        ("qual é o meu saldo", Language.PT_BR),
    ],
)
def test_unsupported_case_offers_handoff(text: str, language: Language) -> None:
    model = FakeModel()
    tools, ports = _ports(model)
    state = ConversationState(language=language)
    result = step(TextInput(text), state, ports)
    assert result.kind is OutcomeKind.HANDOFF
    assert result.reason == "out_of_scope"
    assert result.case_number is None
    assert tools.open_calls == 0


@pytest.mark.parametrize(
    ("text", "language"),
    [
        ("quiero una persona", Language.ES_419),
        ("quero uma pessoa", Language.PT_BR),
    ],
)
def test_human_case_hands_off_without_token(text: str, language: Language) -> None:
    model = FakeModel()
    tools, ports = _ports(model)
    state = ConversationState(language=language)
    first = step(TextInput(text), state, ports)
    result = step(TextInput(text), state, ports)
    assert first.kind is OutcomeKind.OFFER
    assert result.kind is OutcomeKind.HANDOFF
    assert result.reason == "person.insist"
    assert result.case_number is None
    assert tools.open_calls == 0
    assert model.classify_calls == 0
    assert state.pending_confirmation is None
