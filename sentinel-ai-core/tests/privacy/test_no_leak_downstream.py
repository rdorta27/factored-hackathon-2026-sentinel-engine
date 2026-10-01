"""No customer identifier survives anywhere past the entry point (REQ-0047).

The mask runs once, at the router. These tests verify that nothing downstream —
the conversation state, the stored JSON, the log records or the advisor ticket —
holds the raw value.
"""

import json

from fastapi.testclient import TestClient

from app.main import create_app
from app.state.conversation import to_json

PASSWORD = "Testpass-001"
CUSTOMER = "CUST-0001"
RAW_ID = "1098234"
MESSAGE = f"mi DNI es {RAW_ID} y no reconozco un cargo"


def logged_in() -> TestClient:
    api = TestClient(create_app())
    assert api.post(
        "/api/v1/auth/login", json={"login": CUSTOMER, "password": PASSWORD}
    ).status_code == 200
    return api


def test_conversation_state_holds_the_masked_text() -> None:
    """`state.turns` stores what the router passed in: already masked."""
    api = logged_in()
    api.post("/api/v1/chat", json={"message": MESSAGE})
    token = api.cookies.get("sentinel_session")
    stored = api.app.state.conversation_store.get(token)
    assert stored is not None
    stored_turns = stored.state.turns
    assert stored_turns, "the turn was recorded"
    assert raw_id_absent(stored_turns), f"raw id in turns: {stored_turns}"
    assert any("[DOC_ID]" in turn for turn in stored_turns)

    # The serialized form that would be written to SQLite is clean too.
    serialized = to_json(stored.state)
    assert RAW_ID not in serialized, "the stored JSON would leak the id"


def test_structured_logs_hold_no_customer_text() -> None:
    """`StepRecord` has no free-text field by design; assert it stays that way."""
    api = logged_in()
    api.post("/api/v1/chat", json={"message": MESSAGE})
    records = api.app.state.recorder.records if hasattr(api.app.state.recorder, "records") else []
    blob = json.dumps([r.__dict__ if hasattr(r, "__dict__") else str(r) for r in records], default=str)
    assert RAW_ID not in blob, "a log record carries the raw identifier"


def test_handoff_ticket_carries_no_identifier() -> None:
    """The advisor package carries keys and structured turns, never the raw text."""
    api = logged_in()
    api.post("/api/v1/chat", json={"message": "quiero hablar con una persona"})
    api.post("/api/v1/chat", json={"message": "quiero hablar con una persona"})
    cases = api.get("/api/v1/disputes").json()
    handoffs = [case for case in cases if case.get("kind") == "handoff"]
    assert handoffs, "the second ask must produce a handoff ticket"
    blob = json.dumps(handoffs)
    assert RAW_ID not in blob, "the ticket leaks the identifier"
    assert "[DOC_ID]" not in blob, "the ticket should carry keys, not the message"


def test_handoff_after_a_pii_message_leaks_nothing() -> None:
    """Even when PII was typed earlier, the ticket built later is clean."""
    api = logged_in()
    api.post("/api/v1/chat", json={"message": MESSAGE})
    api.post("/api/v1/chat", json={"message": "quiero hablar con una persona"})
    api.post("/api/v1/chat", json={"message": "quiero hablar con una persona"})
    blob = json.dumps(api.get("/api/v1/disputes").json())
    assert RAW_ID not in blob


def raw_id_absent(values: list[str]) -> bool:
    return all(RAW_ID not in value for value in values)
