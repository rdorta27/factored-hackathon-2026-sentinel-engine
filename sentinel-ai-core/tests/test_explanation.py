"""Why follow-ups: deterministic recognition and explanation from the stored
decision (spec `decision-explanation`). The model, the lookup tool and the
policy engine are never called to answer one."""

from datetime import date

import pytest

from app.ai.port import UnderstandKind, UnderstandResult
from app.orchestrator.explanation import (
    asks_why,
    explanation_for,
    is_why_followup,
    names_a_charge,
)
from app.orchestrator.step import Ports, step
from app.orchestrator.types import (
    ConversationState,
    Language,
    LastDecision,
    OutcomeKind,
    TextInput,
)
from app.tools.fake import InMemoryTools

TODAY = date(2026, 6, 17)
WINDOW = LastDecision(
    rule_id="window.expired",
    candidate_id="TXN-1002",
    policy_version="v1",
    values={
        "window_days": 90,
        "charge_date": "2026-01-15",
        "last_eligible_date": "2026-04-15",
        "age_days": 153,
        "synthetic": True,
    },
)


class SpyModel:
    def __init__(self) -> None:
        self.understand_calls = 0
        self.classify_calls = 0

    def understand(self, message, turns, context=None):  # type: ignore[no-untyped-def]
        self.understand_calls += 1
        return UnderstandResult(UnderstandKind.CHARGE, Language.ES_419)

    def classify(self, message):  # type: ignore[no-untyped-def]
        self.classify_calls += 1
        return "Cargo no reconocido"


class SpyTools(InMemoryTools):
    def __init__(self) -> None:
        super().__init__([])
        self.lookup_calls = 0

    def lookup_transactions(self):  # type: ignore[no-untyped-def]
        self.lookup_calls += 1
        return super().lookup_transactions()


def _ports(model, tools) -> Ports:  # type: ignore[no-untyped-def]
    return Ports("s1", tools, model, today=TODAY)  # type: ignore[arg-type]


WHY_ES = [
    "¿por qué?",
    "y eso por qué",
    "en qué te basas para decirme eso",
    "de dónde salen los 90 días",
    "de dónde viene eso",
    "¿a qué se debe?",
    "¿por qué motivo?",
    "¿con qué criterio?",
    "¿cómo lo sabes?",
]
WHY_PT = [
    "por que?",
    "por quê?",
    "com base em que",
    "de onde vem isso",
    "de onde saem esses números",
    "por qual motivo",
    "por qual razão",
    "com que critério",
    "como você sabe?",
]


@pytest.mark.parametrize("message", WHY_ES + WHY_PT)
def test_why_phrasings_are_recognised(message: str) -> None:
    assert asks_why(message)
    assert is_why_followup(message, [], TODAY.year)


@pytest.mark.parametrize(
    "message",
    [
        "no sé cómo explicarlo",
        "quiero que me expliquen un cargo de 890",
        "gracias",
        "no reconozco un cargo",
    ],
)
def test_non_why_messages_are_not_recognised(message: str) -> None:
    assert not asks_why(message)


def test_a_why_question_that_names_a_charge_is_a_new_request() -> None:
    assert asks_why("¿por qué me cobraron 2500 en ACME Store?")
    assert not is_why_followup("¿por qué me cobraron 2500 en ACME Store?", [], TODAY.year)
    assert not is_why_followup(
        "¿por qué rechazaste el cargo de Cafe Central?", ["Cafe Central"], TODAY.year
    )


def test_the_window_quoted_is_not_a_charge() -> None:
    assert not names_a_charge("¿de dónde salen los 90 días?", [], TODAY.year)


def test_window_rule_explains_its_values() -> None:
    result = explanation_for(WINDOW)
    assert result.kind == "rule"
    assert result.message_key == "explanation.window.expired"
    assert result.rule_id == "window.expired"
    assert result.values["window_days"] == 90
    assert result.values["last_eligible_date"] == "2026-04-15"


@pytest.mark.parametrize(
    "rule",
    ["status.pending", "status.reversed", "status.declined", "already.disputed"],
)
def test_status_rules_explain_their_rule(rule: str) -> None:
    result = explanation_for(LastDecision(rule_id=rule, candidate_id="c1"))
    assert result.kind == "rule"
    assert result.message_key == f"explanation.{rule}"
    assert result.rule_id == rule


@pytest.mark.parametrize("rule", ["amount.high", "fraud.score", "fraud.claim"])
def test_safety_rules_share_one_fixed_sentence(rule: str) -> None:
    result = explanation_for(LastDecision(rule_id=rule, candidate_id="c1"))
    assert result.kind == "withheld"
    assert result.message_key == "explanation.safety"
    assert result.rule_id == "advisor.review", "the reply must not say which rule fired"
    assert result.values == {}


def test_the_three_safety_replies_are_identical() -> None:
    replies = [
        explanation_for(LastDecision(rule_id=rule, candidate_id="c1"))
        for rule in ("amount.high", "fraud.score", "fraud.claim")
    ]
    signature = {(item.kind, item.message_key, item.rule_id, tuple(item.values.items())) for item in replies}
    assert len(signature) == 1


def test_no_decision_offers_what_the_service_can_do() -> None:
    result = explanation_for(None)
    assert result.kind == "none"
    assert result.message_key == "explanation.none"
    assert result.rule_id is None


def test_step_answers_a_why_followup_without_calling_anything(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    import app.orchestrator.step as step_module

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("the policy engine must not run for an explanation")

    monkeypatch.setattr(step_module, "evaluate", _forbidden)
    model = SpyModel()
    tools = SpyTools()
    state = ConversationState(language=Language.ES_419, last_decision=WINDOW)
    output = step(TextInput("¿en qué te basas, de dónde salen los 90 días?"), state, _ports(model, tools))
    assert output.kind is OutcomeKind.EXPLANATION
    assert output.explanation_key == "explanation.window.expired"
    assert output.explanation_values["window_days"] == 90
    assert model.understand_calls == 0
    assert model.classify_calls == 0
    assert tools.lookup_calls == 0


def test_step_keeps_the_charge_path_when_a_charge_is_named() -> None:
    model = SpyModel()
    tools = SpyTools()
    state = ConversationState(language=Language.ES_419, last_decision=WINDOW)
    step(TextInput("¿por qué me cobraron 2500 en ACME Store?"), state, _ports(model, tools))
    assert model.understand_calls == 1, "a new request goes through the model"


def test_step_with_no_decision_states_no_rule() -> None:
    model = SpyModel()
    tools = SpyTools()
    state = ConversationState(language=Language.ES_419)
    output = step(TextInput("¿por qué?"), state, _ports(model, tools))
    assert output.kind is OutcomeKind.EXPLANATION
    assert output.explanation_key == "explanation.none"
    assert output.reason is None
    assert model.understand_calls == 0
    assert tools.lookup_calls == 0
