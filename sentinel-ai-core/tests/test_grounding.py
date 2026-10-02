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
    def understand(self, message: str, turns: list[str], context: dict | None = None) -> UnderstandResult:
        language = Language.PT_BR if "cobran" in message else Language.ES_419
        return UnderstandResult(UnderstandKind.CHARGE, language)

    def classify(self, message: str) -> str:
        return "Cargo no reconocido"


def _row(status: TransactionStatus = TransactionStatus.APPROVED, candidate_id: str = "c1") -> Candidate:
    return Candidate(
        candidate_id=candidate_id,
        status=status,
        amount="1000.00",
        currency="MXN",
        merchant="ACME Store",
        date="2026-06-10",
        as_of="2026-06-17",
    )


def test_spanish_and_portuguese_match_the_same_charge() -> None:
    spanish = "cargo del 10 de junio en ACME Store por 1.000,00"
    portuguese = "cobrança de 10 de junho na ACME Store por R$ 1.000,00"
    for message in (spanish, portuguese):
        tools = InMemoryTools([_row(), _row(candidate_id="c2")])
        tools.candidates[1] = Candidate(
            candidate_id="c2",
            status=TransactionStatus.APPROVED,
            amount="320.00",
            currency="MXN",
            merchant="Cafe Central",
            date="2026-06-12",
            as_of="2026-06-17",
        )
        ports = Ports(
            idempotency_scope="s1",
            tools=tools,
            model=ChargeModel(),
            today=date(2026, 6, 17),
        )
        result = step(TextInput(message), ConversationState(language=Language.ES_419), ports)
        assert result.kind is OutcomeKind.CONFIRM_BOX
        assert result.candidate is not None
        assert result.candidate.candidate_id == "c1"
        assert tools.open_calls == 0


def test_portuguese_ambiguity_does_not_select_one() -> None:
    tools = InMemoryTools([_row(), _row(candidate_id="c2")])
    ports = Ports(idempotency_scope="s1", tools=tools, model=ChargeModel(), today=date(2026, 6, 17))
    result = step(
        TextInput("cobrança na ACME Store"),
        ConversationState(language=Language.PT_BR),
        ports,
    )
    assert result.kind is OutcomeKind.QUESTION
    assert tools.open_calls == 0


def test_reversed_match_explains_and_skips_the_box() -> None:
    tools = InMemoryTools([_row(TransactionStatus.REVERSED)])
    ports = Ports(idempotency_scope="s1", tools=tools, model=ChargeModel(), today=date(2026, 6, 17))
    result = step(
        TextInput("cargo del 10 de junio en ACME Store por 1.000,00"),
        ConversationState(language=Language.ES_419),
        ports,
    )
    assert result.kind is OutcomeKind.EXPLAIN
    assert result.reason == "status.reversed"
    assert tools.open_calls == 0


def test_written_yes_does_not_open() -> None:
    tools = InMemoryTools([_row()])
    state = ConversationState(language=Language.ES_419)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ChargeModel(), today=date(2026, 6, 17))
    shown = step(
        TextInput("cargo del 10 de junio en ACME Store por 1.000,00"),
        state,
        ports,
    )
    answer = step(TextInput("sí"), state, ports)
    assert shown.kind is OutcomeKind.CONFIRM_BOX
    assert answer.kind is OutcomeKind.QUESTION
    assert tools.open_calls == 0


def test_structured_id_without_a_box_does_not_open() -> None:
    tools = InMemoryTools([_row()])
    state = ConversationState(language=Language.ES_419, candidates=tools.candidates)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ChargeModel(), today=date(2026, 6, 17))
    result = step(CandidateIdInput("c1"), state, ports)
    assert result.kind is OutcomeKind.CONFIRM_BOX
    assert tools.open_calls == 0
