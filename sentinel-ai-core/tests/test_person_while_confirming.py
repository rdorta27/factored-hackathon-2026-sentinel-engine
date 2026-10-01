"""A person request while the confirm box is open (REQ-0040).

The confirm box swallows every message except one: a request for a person. This
module pins that, and pins that everything else keeps today's behaviour.

Behaviour under test, identical with the box open or closed:

* first ask -> OFFER, the box stays open;
* insisting -> HANDOFF, the box closes, and no case is ever opened.

The check for "no case" is always `tools.open_calls == 0`, which measures the
write itself rather than looking for its consequences.
"""

from datetime import date

import pytest

from app.ai.demo import DemoModel
from app.ai.port import UnderstandKind, UnderstandResult
from app.ai.transport import ModelUnavailable
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

PERSON_ES = "quiero hablar con una persona"
PERSON_PT = "quero falar com um atendente"
TODAY = date(2026, 6, 17)


def candidate(reference: str, currency: str = "MXN", amount: str = "1000.00") -> Candidate:
    return Candidate(
        candidate_id=reference,
        status=TransactionStatus.APPROVED,
        amount=amount,
        currency=currency,
        merchant="ACME Store",
        date="2026-06-10",
        as_of="2026-06-17",
    )


def opened_box(
    currency: str = "MXN", reference: str = "TXN-1001", language: Language = Language.ES_419
) -> tuple[ConversationState, Ports, InMemoryTools]:
    """Drive one turn until the confirm box is open."""
    tools = InMemoryTools([candidate(reference, currency)])
    ports = Ports("s1", tools, DemoModel(), country="MX", today=TODAY)
    state = ConversationState(language=language)
    step(TextInput("no reconozco el cargo de 1000.00 en ACME Store del 2026-06-10"), state, ports)
    assert state.pending_confirmation is not None, "the box must be open for these tests"
    return state, ports, tools


# --- the fix: a person request reaches the shared rule -------------------


def test_first_ask_with_the_box_open_offers_and_keeps_the_box() -> None:
    state, ports, tools = opened_box()
    output = step(TextInput(PERSON_ES), state, ports)
    assert output.kind is OutcomeKind.OFFER
    assert state.person_asks == 1
    assert state.pending_confirmation is not None, "the box stays open after an offer"
    assert tools.open_calls == 0


def test_second_ask_with_the_box_open_hands_off_and_closes_the_box() -> None:
    state, ports, tools = opened_box()
    step(TextInput(PERSON_ES), state, ports)
    output = step(TextInput(PERSON_ES), state, ports)
    assert output.kind is OutcomeKind.HANDOFF
    assert output.reason == "person.insist"
    assert state.person_asks == 2
    assert state.pending_confirmation is None, "the box closes so no case can be opened"
    assert tools.open_calls == 0, "a handoff never opens a case"


def test_portuguese_person_request_behaves_the_same() -> None:
    """The rule does not depend on the language: the same two steps apply.

    The stand-in `DemoModel` always reports `es-419`, so the state language is
    whatever the model returned on the first turn; what this test pins is that a
    Portuguese request still traverses OFFER then HANDOFF.
    """
    state, ports, tools = opened_box(language=Language.PT_BR)
    first = step(TextInput(PERSON_PT), state, ports)
    second = step(TextInput(PERSON_PT), state, ports)
    assert first.kind is OutcomeKind.OFFER
    assert second.kind is OutcomeKind.HANDOFF
    assert second.reason == "person.insist"
    assert tools.open_calls == 0


@pytest.mark.parametrize(
    ("reference", "currency"),
    [("TXN-1001", "MXN"), ("TXN-2001", "COP"), ("TXN-3001", "ARS")],
)
def test_every_country_customer_escalates_without_opening_a_case(
    reference: str, currency: str
) -> None:
    state, ports, tools = opened_box(currency=currency, reference=reference)
    step(TextInput(PERSON_ES), state, ports)
    output = step(TextInput(PERSON_ES), state, ports)
    assert output.kind is OutcomeKind.HANDOFF
    assert tools.open_calls == 0
    assert state.pending_confirmation is None


# --- everything else keeps today's behaviour -----------------------------


@pytest.mark.parametrize("message", ["sí", "si", "no", "mejor luego", "1234"])
def test_other_text_with_the_box_open_is_unchanged(message: str) -> None:
    """Any non-person message still returns the same QUESTION as before."""
    state, ports, tools = opened_box()
    before = state.pending_confirmation
    output = step(TextInput(message), state, ports)
    assert output.kind is OutcomeKind.QUESTION
    assert output.text == message
    assert state.pending_confirmation is before, "the box is untouched"
    assert state.person_asks == 0, "no person ask was recorded"
    assert tools.open_calls == 0


def test_model_failure_with_the_box_open_does_not_escalate() -> None:
    """`model_unavailable` must not become a handoff while the box is open."""

    class UnavailableModel:
        def understand(self, message: str, turns: list[str]):  # type: ignore[no-untyped-def]
            raise ModelUnavailable("down")

        def classify(self, message: str) -> str:
            return "Cargo duplicado"

        def describe(self):  # type: ignore[no-untyped-def]
            from app.ai.port import ModelInfo

            return ModelInfo(model="down", route="test", prompt_version="v1")

    state, _ports, tools = opened_box()
    ports = Ports("s1", tools, UnavailableModel(), country="MX", today=TODAY)
    output = step(TextInput("quiero hablar con una persona"), state, ports)
    assert output.kind is OutcomeKind.QUESTION, "a model failure is not a person request"
    assert state.pending_confirmation is not None, "the box stays open"
    assert state.person_asks == 0
    assert tools.open_calls == 0


def test_offer_then_confirm_still_opens_the_case() -> None:
    """Asking once must not poison the confirmation path.

    The offer does not touch the box; the button then runs the normal flow and
    the case is opened and read back.
    """
    state, ports, tools = opened_box()
    offer = step(TextInput(PERSON_ES), state, ports)
    assert offer.kind is OutcomeKind.OFFER
    assert state.pending_confirmation is not None

    output = step(CandidateIdInput("TXN-1001"), state, ports)
    assert output.kind is OutcomeKind.CASE_NUMBER
    assert output.case_number is not None
    assert tools.open_calls >= 1, "the customer still got their case"


# --- the shared rule, exercised without a box ---------------------------


def test_the_same_rule_without_a_box_still_offers_then_hands_off() -> None:
    """Regression guard for the extraction: the helper is used by both paths."""
    tools = InMemoryTools([candidate("TXN-1001")])
    ports = Ports("s1", tools, DemoModel(), country="MX", today=TODAY)
    state = ConversationState(language=Language.ES_419)

    first = step(TextInput(PERSON_ES), state, ports)
    second = step(TextInput(PERSON_ES), state, ports)
    assert first.kind is OutcomeKind.OFFER
    assert second.kind is OutcomeKind.HANDOFF
    assert second.reason == "person.insist"
    assert tools.open_calls == 0
