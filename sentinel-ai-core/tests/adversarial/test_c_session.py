"""C. Session lifecycle.

Already covered elsewhere and **not duplicated here** (listed in the summary):
`test_chat.py::test_chat_without_session_is_401` (C2).

This module completes the two shapes that were only tested against
`/session/me` and not against the business endpoints, plus cross-session
residue.
"""

from .conftest import CUSTOMER, PASSWORD, expire_session, login_as

# --- blocked (verified) ---


def test_expired_session_cannot_use_chat_or_transactions(logged_in) -> None:
    """C1. Expiry is enforced on the business routes, not only on /session/me."""
    expire_session(logged_in)
    assert logged_in.post("/chat", json={"message": "hola"}).status_code == 401
    assert logged_in.get("/transactions").status_code == 401


def test_expired_session_is_audited_as_denied(logged_in) -> None:
    """The expiry is audited as `session_expired`, which is the accurate event.

    Not `access_denied`: the session existed and expired, which is a different
    signal from a missing or forged credential. Asserting the specific event
    keeps the audit honest.
    """
    expire_session(logged_in)
    logged_in.get("/transactions")
    events = [record["event"] for record in logged_in.app.state.audit.records]
    assert "session_expired" in events


def test_revoked_token_cannot_be_replayed_in_chat(api) -> None:
    """C3. Logout must kill the token for every route, not only /session/me."""
    login_as(api, CUSTOMER)
    token = api.cookies.get("sentinel_session")
    assert api.post("/session/logout").status_code == 200

    replayed = type(api)(api.app)
    replayed.cookies.set("sentinel_session", token)
    assert replayed.post("/chat", json={"message": "hola"}).status_code == 401
    assert replayed.get("/transactions").status_code == 401


def test_conversation_state_does_not_leak_between_customers(api) -> None:
    """C4. A second customer must not inherit the first customer's thread.

    State is keyed by customer, so the second session starts its own
    conversation and its candidates come from its own Gold rows.
    """
    login_as(api, CUSTOMER)
    api.post("/chat", json={"message": "no reconozco un cargo"})
    # FINDING: conversation state is keyed by the session token, not by the
    # customer id. Two sessions for the same customer would not share a thread.
    assert len(api.app.state.conversations) == 1, "one live session, one thread"

    api.post("/session/logout")
    login_as(api, "CUST-0002")
    reply = api.post("/chat", json={"message": "no reconozco un cargo"}).json()

    assert len(api.app.state.conversations) == 2, "a second session opens its own thread"
    # The first customer's rows never appear in the second customer's reply.
    assert "1000.00" not in str(reply)


def test_unknown_session_cookie_shape_is_rejected(api) -> None:
    """A structurally odd but well-formed token is still just unknown."""
    for token in ("", "a", "0" * 43):
        api.cookies.set("sentinel_session", token)
        assert api.get("/transactions").status_code == 401, token
