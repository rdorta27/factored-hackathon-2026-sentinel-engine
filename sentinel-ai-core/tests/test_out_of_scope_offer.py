"""Out of scope explains and offers an advisor first (decision 008); a second turn hands off."""

from datetime import date

from app.ai.demo import DemoModel
from app.orchestrator.step import Ports, step
from app.orchestrator.types import (
    Candidate,
    ConversationState,
    Language,
    OutcomeKind,
    TextInput,
    TransactionStatus,
)
from app.state.conversation import from_json
from app.tools.fake import InMemoryTools
from dataclasses import asdict
import json


def _ports() -> tuple[InMemoryTools, Ports]:
    tools = InMemoryTools(
        [Candidate("c1", TransactionStatus.APPROVED, "85.000", "COP", "Exito", "2024-10-01", "2024-10-02")]
    )
    return tools, Ports("s1", tools, DemoModel(), today=date(2024, 12, 1), country="MX")


def _say(state: ConversationState, ports: Ports, text: str):  # type: ignore[no-untyped-def]
    return step(TextInput(text), state, ports)


def test_two_out_of_scope_turns_get_the_offer_and_the_third_hands_off() -> None:
    _, ports = _ports()
    state = ConversationState(language=Language.ES_419)
    first = _say(state, ports, "cuál es mi saldo")
    second = _say(state, ports, "quiero ver mi saldo")
    third = _say(state, ports, "dime mi saldo")
    assert [(o.kind, o.reason) for o in (first, second)] == [(OutcomeKind.OFFER, "out_of_scope.ask")] * 2
    assert (third.kind, third.reason) == (OutcomeKind.HANDOFF, "out_of_scope")


def test_a_charge_turn_in_between_resets_the_offer() -> None:
    _, ports = _ports()
    state = ConversationState(language=Language.ES_419)
    _say(state, ports, "cuál es mi saldo")
    assert state.scope_asks == 1
    _say(state, ports, "no reconozco un cargo")
    assert state.scope_asks == 0
    again = _say(state, ports, "cuál es mi saldo")
    assert again.kind is OutcomeKind.OFFER


def test_asking_for_an_advisor_after_the_offer_hands_off() -> None:
    _, ports = _ports()
    state = ConversationState(language=Language.ES_419)
    assert _say(state, ports, "cuál es mi saldo").kind is OutcomeKind.OFFER
    answer = _say(state, ports, "quiero una persona")
    assert (answer.kind, answer.reason) == (OutcomeKind.HANDOFF, "person.insist")


def test_a_person_ask_without_the_offer_still_offers_first() -> None:
    _, ports = _ports()
    state = ConversationState(language=Language.ES_419)
    assert _say(state, ports, "quiero una persona").kind is OutcomeKind.OFFER


def test_the_offer_count_survives_a_stored_conversation() -> None:
    _, ports = _ports()
    state = ConversationState(language=Language.PT_BR)
    _say(state, ports, "qual é o meu saldo")
    restored = from_json(json.dumps(asdict(state)))
    assert restored.scope_asks == 1
    assert _say(restored, ports, "qual é o meu saldo").kind is OutcomeKind.OFFER
    assert _say(restored, ports, "qual é o meu saldo").kind is OutcomeKind.HANDOFF
