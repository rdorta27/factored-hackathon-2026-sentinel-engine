"""Regression tests for the flow defects that Felix found on 2026-10-04.

One test per defect of ``openspec/changes/flow-fixes``. They fail on the code
before the fix, so a change that hides a defect breaks a test here.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

PASSWORD = "Testpass-001"
CUSTOMER = "CUST-0001"


def logged_in() -> TestClient:
    api = TestClient(create_app())
    response = api.post("/api/v1/auth/login", json={"login": CUSTOMER, "password": PASSWORD})
    assert response.status_code == 200
    return api


def chat(api: TestClient, **body: str) -> dict:
    return api.post("/api/v1/chat", json=body).json()


def open_dispute(api: TestClient, reference: str) -> str:
    """Show the box for one charge and confirm it. Return the case reference."""
    assert chat(api, selected_reference=reference)["kind"] == "confirm_box"
    confirmed = chat(api, selected_reference=reference)
    assert confirmed["kind"] == "case_confirmation"
    return confirmed["case_id"]


def test_another_charge_after_a_handoff_continues() -> None:
    """F1: a handoff does not block a new request about another charge."""
    api = logged_in()
    assert chat(api, message="quiero una persona")["kind"] == "text"
    filed = chat(api, message="quiero una persona")
    assert filed["kind"] == "handoff"

    reply = chat(api, message="no reconozco el cargo de Cafe Central")
    assert reply["kind"] == "confirm_box", "a new charge must continue the flow"
    assert reply["candidate"]["reference"] == "TXN-1006"


def test_the_same_charge_after_a_handoff_keeps_its_ticket() -> None:
    """F1: a message about the filed charge answers with its ticket."""
    api = logged_in()
    filed = chat(api, selected_reference="TXN-1101")
    assert filed["kind"] == "handoff"
    assert filed["reason_key"] == "handoff.amountHigh"

    again = chat(api, selected_reference="TXN-1101")
    assert again["kind"] == "handoff"
    assert again["reference"] == filed["reference"]
    assert again["reason_key"] == "handoff.amountHigh"


def test_a_filed_ticket_reason_does_not_change() -> None:
    """F1: a later turn reuses the reference and the reason of the filed ticket."""
    api = logged_in()
    chat(api, message="quiero una persona")
    filed = chat(api, message="quiero una persona")
    assert filed["kind"] == "handoff"
    assert filed["reason_key"] == "handoff.person"

    chat(api, message="HOLA")
    chat(api, message="HOLA")
    later = chat(api, message="HOLA")
    assert later["kind"] == "handoff"
    assert later["reference"] == filed["reference"]
    assert later["reason_key"] == "handoff.person", "the filed reason is fixed"


@pytest.mark.parametrize(
    "question",
    [
        "ya abrí una disputa, ¿en qué va?",
        "já abri uma contestação, qual é o status?",
    ],
)
def test_dispute_status_question_never_opens_a_case(question: str) -> None:
    """F2: a dispute-status question answers from the case store and never opens a case."""
    api = logged_in()
    case_id = open_dispute(api, "TXN-1006")
    before = len(api.app.state.cases.for_customer(CUSTOMER))

    reply = chat(api, message=question)
    assert reply["kind"] == "explanation", "a status question is not a new dispute"
    assert case_id in json.dumps(reply), "the reply names the existing case"
    assert len(api.app.state.cases.for_customer(CUSTOMER)) == before


def test_a_correction_replaces_the_confirm_box() -> None:
    """F3: with the box open, a correction grounds the new charge."""
    api = logged_in()
    box = chat(api, selected_reference="TXN-1001")
    assert box["kind"] == "confirm_box"
    assert box["candidate"]["reference"] == "TXN-1001"

    corrected = chat(api, message="no, perdón, el de 320")
    assert corrected["kind"] == "confirm_box"
    assert corrected["candidate"]["reference"] == "TXN-1006"


def test_an_already_disputed_charge_does_not_open_a_box() -> None:
    """F4: the case store is checked before the box opens."""
    api = logged_in()
    open_dispute(api, "TXN-1006")
    before = len(api.app.state.cases.for_customer(CUSTOMER))

    reply = chat(api, selected_reference="TXN-1006")
    assert reply["kind"] == "text"
    assert reply["message_key"] == "already.disputed"
    assert len(api.app.state.cases.for_customer(CUSTOMER)) == before


def test_a_date_with_no_match_names_the_searched_date() -> None:
    """F5: when no charge matches a date, the reply names the date that it searched."""
    api = logged_in()
    reply = chat(api, message="algo raro ayer")
    assert reply["kind"] == "clarification"
    rendered = json.dumps(reply)
    assert any(
        marker in rendered for marker in ("2026-06-16", "16 jun", "16 de junio", "16/06")
    ), "the reply names the searched date"


def test_a_message_over_two_thousand_characters_is_422() -> None:
    """F6: the server keeps the 2000-character limit on the message."""
    api = logged_in()
    assert api.post("/api/v1/chat", json={"message": "a" * 2000}).status_code == 200
    assert api.post("/api/v1/chat", json={"message": "a" * 2001}).status_code == 422


def test_rate_limit_body_carries_the_trace_id() -> None:
    """F7: the 429 body carries the trace id so the error bubble shows the reference."""
    api = logged_in()
    response = None
    for _ in range(61):
        response = api.post("/api/v1/chat", json={"message": "hola"})
    assert response is not None and response.status_code == 429
    body = response.json()
    assert "trace_id" in body
    assert body["trace_id"] == response.headers["X-Trace-Id"]
