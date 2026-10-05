"""Chat-start behaviour (openspec change `chat-start`).

One test per requirement of the change: openers, charge status, out-of-scope
subtypes, slot grounding, why for a named charge, and validated model words.
The fake router returns contract v3 results; the same cases run with v2-style
results for the code fallbacks.
"""

from datetime import date

import pytest

from app.ai.port import ModelInfo, UnderstandKind, UnderstandResult, UnderstandSlots
from app.ai.transport import ModelUnavailable
from app.observability import Recorder, TurnObserver
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

TODAY = date(2026, 6, 17)


def _row(
    candidate_id: str,
    merchant: str,
    amount: str,
    day: str,
    status: TransactionStatus = TransactionStatus.APPROVED,
) -> Candidate:
    return Candidate(candidate_id, status, amount, "MXN", merchant, day, "2026-06-17")


def _tools() -> InMemoryTools:
    return InMemoryTools(
        [
            _row("c0", "Cafe Central", "800.00", "2026-01-15"),
            _row("c1", "Cafe Central", "320.00", "2026-06-12"),
            _row("c2", "ACME Store", "1000.00", "2026-06-10"),
            _row("c3", "Tienda del Sur", "500.00", "2026-06-05", TransactionStatus.PENDING),
        ]
    )


class Router:
    """A fake contract v3 router, keyed by the exact message."""

    def __init__(self, results: dict[str, UnderstandResult] | None = None,
                 default: UnderstandResult | None = None) -> None:
        self.results = results or {}
        self.default = default

    def describe(self) -> ModelInfo:
        return ModelInfo("fake-v3", "mock", "v3")

    def classify(self, message: str) -> str:
        return "Cargo no reconocido"

    def understand(self, message: str, turns: list[str], context: dict | None = None) -> UnderstandResult:
        if message in self.results:
            return self.results[message]
        if self.default is not None:
            return self.default
        raise ModelUnavailable(message)


def _ports(model, tools=None, observer=None) -> Ports:
    return Ports(
        idempotency_scope="s1",
        tools=tools or _tools(),
        model=model,  # type: ignore[arg-type]
        today=TODAY,
        observer=observer,
    )


def _say(router, text: str, state=None, tools=None, observer=None):  # type: ignore[no-untyped-def]
    state = state or ConversationState(language=Language.ES_419)
    return step(TextInput(text), state, _ports(router, tools, observer))


# --- 2.1 openers -----------------------------------------------------------


@pytest.mark.parametrize(
    ("subtype", "message"),
    [
        ("greeting", "hola"),
        ("thanks", "muchas gracias"),
        ("goodbye", "adiós"),
        ("identity", "¿eres un bot?"),
        ("help", "¿en qué puedes ayudar?"),
    ],
)
def test_opener_subtype_gets_a_friendly_reply_and_no_handoff(subtype: str, message: str) -> None:
    router = Router({message: UnderstandResult(UnderstandKind.MISSING, Language.ES_419, subtype=subtype)})
    output = _say(router, message)
    assert output.kind is OutcomeKind.EXPLAIN
    assert output.reason == f"opener.{subtype}"
    assert output.message_key == f"opener.{subtype}"


def test_opener_fallback_on_a_v2_missing_result() -> None:
    router = Router({"hola": UnderstandResult(UnderstandKind.MISSING, Language.ES_419)})
    output = _say(router, "hola")
    assert output.kind is OutcomeKind.EXPLAIN
    assert output.reason == "opener.greeting"


def test_greeting_with_a_request_keeps_the_request() -> None:
    router = Router(
        {
            "hola, no reconozco un cargo de Cafe Central": UnderstandResult(
                UnderstandKind.MISSING, Language.ES_419, subtype="greeting"
            )
        }
    )
    output = _say(router, "hola, no reconozco un cargo de Cafe Central")
    assert output.reason != "opener.greeting", "a request must not become small talk"
    assert output.kind in (OutcomeKind.QUESTION, OutcomeKind.CONFIRM_BOX)


def test_an_unclear_missing_result_still_asks() -> None:
    router = Router({"algo raro": UnderstandResult(UnderstandKind.MISSING, Language.ES_419, subtype="unclear")})
    output = _say(router, "algo raro")
    assert output.kind is OutcomeKind.QUESTION


# --- 2.2 charge status ------------------------------------------------------


def test_charge_status_is_answered_without_a_box() -> None:
    router = Router(
        {
            "quiero ver el estado de mi último cargo": UnderstandResult(
                UnderstandKind.STATUS, Language.ES_419
            )
        }
    )
    output = _say(router, "quiero ver el estado de mi último cargo")
    assert output.kind is OutcomeKind.EXPLANATION
    assert output.kind is not OutcomeKind.CONFIRM_BOX
    assert output.explanation_key.startswith("charge.status")
    assert output.explanation_values["merchant"] == "Cafe Central"
    assert output.explanation_values["status"] == "Approved"
    assert output.explanation_values["eligible"] is True


def test_status_of_a_named_charge_uses_the_slot() -> None:
    router = Router(
        {
            "estado del cargo de mil pesos": UnderstandResult(
                UnderstandKind.STATUS,
                Language.ES_419,
                slots=UnderstandSlots(amount=1000),
            )
        }
    )
    output = _say(router, "estado del cargo de mil pesos")
    assert output.kind is OutcomeKind.EXPLANATION
    assert output.explanation_values["merchant"] == "ACME Store"


# --- 2.3 out-of-scope subtypes ---------------------------------------------


@pytest.mark.parametrize("subtype", ["balance", "loan", "card", "address", "transfer", "other"])
def test_out_of_scope_reply_names_the_subtype(subtype: str) -> None:
    message = "ayuda"
    router = Router(
        {message: UnderstandResult(UnderstandKind.OUT_OF_SCOPE, Language.ES_419, subtype=subtype)}
    )
    output = _say(router, message)
    assert output.kind is OutcomeKind.OFFER
    assert output.reason == f"out_of_scope.{subtype}"
    assert output.message_key == f"out_of_scope.{subtype}"


# --- 2.4 slot grounding -----------------------------------------------------


def test_mil_pesos_slot_grounds_the_charge() -> None:
    message = "un cobro de mil pesos"
    router = Router(
        {message: UnderstandResult(UnderstandKind.CHARGE, Language.ES_419, slots=UnderstandSlots(amount=1000))}
    )
    output = _say(router, message)
    assert output.kind is OutcomeKind.CONFIRM_BOX
    assert output.candidate is not None and output.candidate.candidate_id == "c2"


def test_mil_pesos_code_fallback_with_a_v2_result() -> None:
    message = "un cobro de mil pesos"
    router = Router({message: UnderstandResult(UnderstandKind.CHARGE, Language.ES_419)})
    output = _say(router, message)
    assert output.kind is OutcomeKind.CONFIRM_BOX
    assert output.candidate is not None and output.candidate.candidate_id == "c2"


def test_a_slot_with_no_match_says_what_was_searched() -> None:
    message = "un cobro de 9999 pesos"
    router = Router(
        {message: UnderstandResult(UnderstandKind.CHARGE, Language.ES_419, slots=UnderstandSlots(amount=9999))}
    )
    output = _say(router, message)
    assert output.kind is OutcomeKind.QUESTION
    assert output.reason == "charge.not_found"


# --- 2.5 why for a named charge --------------------------------------------


def test_why_for_a_named_charge_answers_from_the_rule() -> None:
    message = "¿por qué no puedo reclamar el de enero?"
    router = Router({message: UnderstandResult(UnderstandKind.CHARGE, Language.ES_419)})
    output = _say(router, message)
    assert output.kind is OutcomeKind.EXPLANATION
    assert output.reason == "window.expired"
    assert output.explanation_values["window_days"] == 90
    assert output.explanation_values["charge_date"] == "2026-01-15"
    assert output.explanation_values["last_eligible_date"] == "2026-04-15"


def test_why_for_a_named_charge_wins_when_the_model_says_status() -> None:
    message = "¿por qué no puedo reclamar el de enero?"
    router = Router({message: UnderstandResult(UnderstandKind.STATUS, Language.ES_419)})
    output = _say(router, message)
    assert output.kind is OutcomeKind.EXPLANATION
    assert output.reason == "window.expired"


# --- 2.6 validated model words ---------------------------------------------


def test_an_accepted_draft_is_shown() -> None:
    message = "hola"
    draft = "Hola, puedo revisar tu cargo y abrir un reclamo."
    router = Router(
        {message: UnderstandResult(UnderstandKind.MISSING, Language.ES_419, subtype="greeting", reply_draft=draft)}
    )
    output = _say(router, message)
    assert output.text == draft


def test_a_rejected_draft_falls_back_to_the_template_and_names_the_reason() -> None:
    message = "hola"
    router = Router(
        {
            message: UnderstandResult(
                UnderstandKind.MISSING,
                Language.ES_419,
                subtype="greeting",
                reply_draft="Te devolveremos 500 pesos hoy.",
            )
        }
    )
    recorder = Recorder(path=None, salt="test-salt")
    observer = TurnObserver(recorder=recorder, trace_id="a" * 16, session_ref="b" * 16, country="MX")
    output = _say(router, message, observer=observer)
    assert output.text == ""
    assert output.message_key == "opener.greeting"
    events = [record.event for record in recorder.records if record.event]
    assert any(event.startswith("draft_rejected:") for event in events)


def test_a_decision_turn_ignores_the_draft() -> None:
    message = "no reconozco el cargo de 1000.00 en ACME Store"
    router = Router(
        {
            message: UnderstandResult(
                UnderstandKind.CHARGE, Language.ES_419, reply_draft="Puedo ayudarte con eso."
            )
        }
    )
    output = _say(router, message)
    assert output.kind is OutcomeKind.CONFIRM_BOX
    assert output.text == "", "a confirm box never carries model words"


def test_a_status_draft_fills_verified_values() -> None:
    message = "estado de mi cargo"
    router = Router(
        {
            message: UnderstandResult(
                UnderstandKind.STATUS,
                Language.ES_419,
                reply_draft="Tu cargo en {merchant} está {status}.",
            )
        }
    )
    output = _say(router, message)
    assert output.kind is OutcomeKind.EXPLANATION
    assert "Cafe Central" in output.text
    assert "{" not in output.text


def test_the_page_shows_the_model_text_when_present() -> None:
    from pathlib import Path

    app_js = (Path(__file__).parents[1] / "app" / "static" / "app.js").read_text(encoding="utf-8")
    assert "body.text ?" in app_js, "the page must prefer the model words"


def test_the_words_table_separates_draft_from_template() -> None:
    from app.orchestrator.step import DRAFT_ALLOWED_KINDS, TEMPLATE_ONLY_KINDS

    assert DRAFT_ALLOWED_KINDS.isdisjoint(TEMPLATE_ONLY_KINDS)
    for kind in (OutcomeKind.CONFIRM_BOX, OutcomeKind.CASE_NUMBER, OutcomeKind.HANDOFF, OutcomeKind.FAILURE):
        assert kind in TEMPLATE_ONLY_KINDS
    for kind in (OutcomeKind.EXPLAIN, OutcomeKind.OFFER, OutcomeKind.QUESTION):
        assert kind in DRAFT_ALLOWED_KINDS


# --- 2.7 one narrowing seam -------------------------------------------------


def test_the_loop_calls_only_narrow(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    import app.orchestrator.step as step_module

    real = step_module.narrow

    def spy(message, understood, rows, today):  # type: ignore[no-untyped-def]
        calls.append(message)
        return real(message, understood, rows, today)

    monkeypatch.setattr(step_module, "narrow", spy)
    router = Router(default=UnderstandResult(UnderstandKind.CHARGE, Language.ES_419))
    _say(router, "no reconozco un cargo")
    assert calls == ["no reconozco un cargo"]
