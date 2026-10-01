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
    assert api.post("/api/v1/session/logout").status_code == 200

    replayed = TestClient(api.app)
    replayed.cookies.set(SESSION_COOKIE, token)
    assert replayed.post("/api/v1/chat", json={"message": "hola"}).status_code == 401
    assert replayed.get("/api/v1/transactions").status_code == 401


@pytest.mark.attack("C4", "blocked_verified")
def test_conversation_state_does_not_leak_between_customers(api) -> None:
    """C4. A second customer must not inherit the first customer's thread.

    State is keyed by the session token (`app/routers/chat.py::_bundle`), not
    by the customer id, so the second session starts its own conversation and
    its candidates come from its own Gold rows. A second session for the *same*
    customer would also get a fresh thread — see the FINDING below.
    """
    login_as(api, CUSTOMER)
    api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    # FINDING: conversation state is keyed by the session token, not by the
    # customer id. Two sessions for the same customer would not share a thread.
    assert len(api.app.state.conversations) == 1, "one live session, one thread"

    api.post("/api/v1/session/logout")
    login_as(api, "CUST-0002")
    reply = api.post("/api/v1/chat", json={"message": "no reconozco un cargo"}).json()

    assert len(api.app.state.conversations) == 2, "a second session opens its own thread"
    # The first customer's rows never appear in the second customer's reply.
    assert "1000.00" not in str(reply)


@pytest.mark.attack("C5", "blocked_verified")
def test_unknown_session_cookie_shape_is_rejected(api) -> None:
    """A structurally odd but well-formed token is still just unknown."""
    for token in ("", "a", "0" * 43):
        api.cookies.set(SESSION_COOKIE, token)
        assert api.get("/api/v1/transactions").status_code == 401, token
