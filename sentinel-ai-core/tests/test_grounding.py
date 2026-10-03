from datetime import date

from app.ai.grounding import (
    StatedFacts,
    extract_soft,
    is_repeated_charge,
    narrow_candidates,
    relative_dates,
    stated_merchant_tokens,
    token_matches_merchant,
)
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


MOCK_MERCHANTS = (
    "ACME Store",
    "Cafe Central",
    "Electronica Norte",
    "Viajes Pacifico",
    "Almacen Andino",
    "Motores Bogota",
    "Farmacia Central",
    "Tech Import",
    "Streaming Plus",
    "Tienda del Sur",
    "Autos Rosario",
    "Libreria Austral",
    "Hotel Patagonia",
    "Musica Online",
)
# A token that belongs to that merchant and not to the others, except where
# the name itself is shared ("central").
_DISTINCT = {
    "ACME Store": "acme",
    "Cafe Central": "cafe",
    "Electronica Norte": "electronica",
    "Viajes Pacifico": "pacifico",
    "Almacen Andino": "andino",
    "Motores Bogota": "bogota",
    "Farmacia Central": "farmacia",
    "Tech Import": "import",
    "Streaming Plus": "streaming",
    "Tienda del Sur": "sur",
    "Autos Rosario": "rosario",
    "Libreria Austral": "austral",
    "Hotel Patagonia": "patagonia",
    "Musica Online": "musica",
}
REFERENCE = date(2026, 6, 17)


def test_cafeteria_matches_cafe_central_and_not_the_others() -> None:
    hits = [name for name in MOCK_MERCHANTS if token_matches_merchant("cafeteria", name)]
    assert hits == ["Cafe Central"]
    assert "cafeteria" in stated_merchant_tokens("me cobraron en la cafetería", list(MOCK_MERCHANTS))


def test_every_mock_merchant_matches_its_own_token() -> None:
    for merchant, token in _DISTINCT.items():
        hits = [name for name in MOCK_MERCHANTS if token_matches_merchant(token, name)]
        assert merchant in hits, token
        if token != "central":
            assert hits == [merchant], (token, hits)


def test_relative_dates_at_the_reference_date() -> None:
    expected = {
        "hoy": {"2026-06-17"},
        "hoje": {"2026-06-17"},
        "ayer": {"2026-06-16"},
        "ontem": {"2026-06-16"},
        "anteayer": {"2026-06-15"},
        "anteontem": {"2026-06-15"},
        "el lunes": {"2026-06-15"},
        "el martes": {"2026-06-16"},
        "el miércoles": {"2026-06-17"},
        "el jueves": {"2026-06-11"},
        "el viernes": {"2026-06-12"},
        "el sábado": {"2026-06-13"},
        "el domingo": {"2026-06-14"},
        "na segunda": {"2026-06-15"},
        "na terça": {"2026-06-16"},
        "na quarta": {"2026-06-17"},
        "na quinta": {"2026-06-11"},
        "na sexta": {"2026-06-12"},
        "semana pasada": {f"2026-06-{day:02d}" for day in range(10, 17)},
        "semana passada": {f"2026-06-{day:02d}" for day in range(10, 17)},
        "hace 3 días": {"2026-06-14"},
        "há 2 dias": {"2026-06-15"},
    }
    for phrase, dates in expected.items():
        assert relative_dates(phrase, REFERENCE) == frozenset(dates), phrase


def test_repeated_phrase_keeps_the_duplicated_pair() -> None:
    assert is_repeated_charge("me cobraron dos veces")
    assert is_repeated_charge("cobraram duas vezes")
    pair = (
        _row(candidate_id="a"),
        Candidate(
            candidate_id="b",
            status=TransactionStatus.APPROVED,
            amount="1000.00",
            currency="MXN",
            merchant="ACME Store",
            date="2026-06-11",
            as_of="2026-06-17",
        ),
        Candidate(
            candidate_id="c",
            status=TransactionStatus.APPROVED,
            amount="320.00",
            currency="MXN",
            merchant="Cafe Central",
            date="2026-06-12",
            as_of="2026-06-17",
        ),
    )
    soft = extract_soft("me cobraron dos veces", REFERENCE, ["ACME Store", "Cafe Central"])
    narrowed = narrow_candidates(StatedFacts(None, None, None), soft, list(pair), REFERENCE)
    assert {item.candidate_id for item in narrowed.candidates} == {"a", "b"}
    assert narrowed.not_found is False


def test_one_soft_match_is_a_clarification_never_a_confirm_box() -> None:
    cafe = Candidate(
        candidate_id="cafe",
        status=TransactionStatus.APPROVED,
        amount="320.00",
        currency="MXN",
        merchant="Cafe Central",
        date="2026-06-12",
        as_of="2026-06-17",
    )
    other = Candidate(
        candidate_id="other",
        status=TransactionStatus.APPROVED,
        amount="8200.00",
        currency="USD",
        merchant="Electronica Norte",
        date="2026-06-13",
        as_of="2026-06-17",
    )
    tools = InMemoryTools([cafe, other])
    state = ConversationState(language=Language.ES_419)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ChargeModel(), today=REFERENCE)
    result = step(TextInput("me cobraron en la cafetería"), state, ports)
    assert result.kind is OutcomeKind.QUESTION
    assert result.kind is not OutcomeKind.CONFIRM_BOX
    assert [item.candidate_id for item in state.candidates] == ["cafe"]
    assert tools.open_calls == 0


def test_unknown_merchant_gets_the_not_found_text() -> None:
    tools = InMemoryTools([
        _row(candidate_id="old"),
        Candidate(
            candidate_id="new",
            status=TransactionStatus.APPROVED,
            amount="320.00",
            currency="MXN",
            merchant="Cafe Central",
            date="2026-06-16",
            as_of="2026-06-17",
        ),
    ])
    state = ConversationState(language=Language.ES_419)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ChargeModel(), today=REFERENCE)
    result = step(TextInput("me cobraron en Tienda Lumbre"), state, ports)
    assert result.kind is OutcomeKind.QUESTION
    assert result.reason == "charge.not_found"
    assert [item.candidate_id for item in state.candidates] == ["new", "old"]
    from pathlib import Path
    import json

    root = Path(__file__).parents[1] / "app" / "static" / "i18n"
    for locale in ("es-419", "pt-BR"):
        text = json.loads((root / f"{locale}.json").read_text(encoding="utf-8"))["charge.not_found"]
        assert "datos" in text or "dados" in text


def test_no_detail_keeps_the_current_question() -> None:
    tools = InMemoryTools([_row()])
    ports = Ports(idempotency_scope="s1", tools=tools, model=ChargeModel(), today=REFERENCE)
    result = step(
        TextInput("no reconozco un cargo"),
        ConversationState(language=Language.ES_419),
        ports,
    )
    assert result.kind is OutcomeKind.QUESTION
    assert result.reason is None


def test_structured_id_without_a_box_does_not_open() -> None:
    tools = InMemoryTools([_row()])
    state = ConversationState(language=Language.ES_419, candidates=tools.candidates)
    ports = Ports(idempotency_scope="s1", tools=tools, model=ChargeModel(), today=date(2026, 6, 17))
    result = step(CandidateIdInput("c1"), state, ports)
    assert result.kind is OutcomeKind.CONFIRM_BOX
    assert tools.open_calls == 0
