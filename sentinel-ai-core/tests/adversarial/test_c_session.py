"""C. Session lifecycle.

Already covered elsewhere and **not duplicated here** (listed in the summary):
`test_chat.py::test_chat_without_session_is_401` (C2).

This module completes the two shapes that were only tested against
`/session/me` and not against the business endpoints, plus cross-session
residue.
"""

import pytest
from fastapi.testclient import TestClient

from app.session.router import SESSION_COOKIE

from .conftest import CUSTOMER, expire_session, login_as

# --- blocked (verified) ---


@pytest.mark.attack("C1", "blocked_verified")
def test_expired_session_cannot_use_chat_or_transactions(logged_in) -> None:
    """C1. Expiry is enforced on the business routes, not only on /session/me."""
    expire_session(logged_in)
    assert logged_in.post("/api/v1/chat", json={"message": "hola"}).status_code == 401
    assert logged_in.get("/api/v1/transactions").status_code == 401


@pytest.mark.attack("C1b", "blocked_verified")
def test_expired_session_is_audited_as_denied(logged_in) -> None:
    """The expiry is audited as `session_expired`, which is the accurate event.

    Not `access_denied`: the session existed and expired, which is a different
    signal from a missing or forged credential. Asserting the specific event
    keeps the audit honest.
    """
    expire_session(logged_in)
    logged_in.get("/api/v1/transactions")
    events = [record.event for record in logged_in.app.state.audit.records]
    assert "session_expired" in events


@pytest.mark.attack("C3", "blocked_verified")
def test_revoked_token_cannot_be_replayed_in_chat(api) -> None:
    """C3. Logout must kill the token for every route, not only /session/me."""
    login_as(api, CUSTOMER)
    token = api.cookies.get(SESSION_COOKIE)
    assert api.post("/api/v1/auth/logout").status_code == 200

    replayed = TestClient(api.app)
    replayed.cookies.set(SESSION_COOKIE, token)
    assert replayed.post("/api/v1/chat", json={"message": "hola"}).status_code == 401
    assert replayed.get("/api/v1/transactions").status_code == 401


@pytest.mark.attack("C4", "blocked_verified")
def test_conversation_state_does_not_leak_between_customers(api) -> None:
    """C4. A second customer must not inherit the first customer's thread.

    Conversation state is keyed by a hash of the session token
    (`app/state/conversation.py`), not by the customer id, and it is deleted
    on logout (retention), so the second session starts its own conversation
    and its candidates come from its own Gold rows.
    """
    login_as(api, CUSTOMER)
    api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    assert len(api.app.state.conversations) == 1, "one live session, one thread"

    api.post("/api/v1/auth/logout")
    assert len(api.app.state.conversations) == 0, "logout deletes the thread"
    login_as(api, "CUST-0002")
    reply = api.post("/api/v1/chat", json={"message": "no reconozco un cargo"}).json()

    assert len(api.app.state.conversations) == 1, "the second session opens its own thread"
    # The first customer's rows never appear in the second customer's reply.
    assert "1000.00" not in str(reply)


@pytest.mark.attack("C5", "blocked_verified")
def test_unknown_session_cookie_shape_is_rejected(api) -> None:
    """A structurally odd but well-formed token is still just unknown."""
    for token in ("", "a", "0" * 43):
        api.cookies.set(SESSION_COOKIE, token)
        assert api.get("/api/v1/transactions").status_code == 401, token


@pytest.mark.attack("C6", "blocked_verified")
def test_disputes_api_without_or_after_session_writes_nothing(api) -> None:
    """C6. The disputes API needs a live session for every step, reads included."""
    assert api.post("/api/v1/disputes/preview", json={"reference": "TXN-1006"}).status_code == 401
    assert api.post("/api/v1/disputes", json={"reference": "TXN-1006"}).status_code == 401
    assert api.get("/api/v1/disputes").status_code == 401

    login_as(api, CUSTOMER)
    api.post("/api/v1/disputes/preview", json={"reference": "TXN-1006"})
    expire_session(api)
    assert api.post("/api/v1/disputes", json={"reference": "TXN-1006"}).status_code == 401
    login_as(api, CUSTOMER)
    assert api.get("/api/v1/disputes").json() == [], "the expired session's preview opened nothing"
