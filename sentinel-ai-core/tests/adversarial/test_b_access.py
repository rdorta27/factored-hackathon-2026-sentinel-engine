"""B. Unauthorized access.

Already covered elsewhere and **not duplicated here** (listed in the summary):
`test_chat.py::test_foreign_reference_does_not_disclose` (B1),
`test_transactions.py::test_customer_identifier_is_rejected` (B2),
`test_chat.py::test_extra_field_is_422` (B5).

This module adds the shapes that had no test: a forged cookie, a malformed
reference, and the documented behaviour of a replayed bearer cookie.
"""

from fastapi.testclient import TestClient

from app.session.router import SESSION_COOKIE

from .conftest import CUSTOMER, OTHER_CUSTOMER, facts_travel_nowhere

# --- blocked (verified) ---


def test_forged_session_token_is_rejected(api) -> None:
    """B3. An invented token has no server-side session behind it."""
    api.cookies.set(SESSION_COOKIE, "forged-token-value")
    assert api.get("/transactions").status_code == 401
    assert api.post("/chat", json={"message": "hola"}).status_code == 401


def test_reference_with_path_shapes_is_rejected(logged_in) -> None:
    """B6. The selection pattern is format-neutral but bounded."""
    for payload in ("../../etc/passwd", "TXN 1001", "x" * 65, ""):
        response = logged_in.post("/chat", json={"selected_reference": payload})
        assert response.status_code == 422, payload


def test_selection_cannot_name_another_customers_row(logged_in) -> None:
    """B1 variant: the same attempt through the session-scoped lookup.

    blocked (verified): even if the id were guessable, `gold.get(...)` is
    scoped to the session customer and returns nothing.
    """
    response = logged_in.post("/chat", json={"selected_reference": "TXN-9001"})
    assert response.status_code == 200
    assert facts_travel_nowhere(response.json())


def test_foreign_rows_are_absent_from_the_listing(logged_in) -> None:
    listing = logged_in.get("/transactions").json()["transactions"]
    ids = {row["reference"] for row in listing}
    assert "TXN-9001" not in ids
    assert "TXN-2001" not in ids
    assert "TXN-3001" not in ids


# --- documented behaviour, not a block: bearer cookie replay ---------------


def test_replayed_bearer_cookie_still_works_by_design(api) -> None:
    """B4. Expected behaviour, **not** a blocked attack.

    The session token is a bearer credential: possession is the proof, so a
    copied cookie from the same session is indistinguishable from the original
    and must work. This is a design limitation, and these tests assert the
    documented behaviour rather than pretending to block it.

    What mitigates the risk instead of blocking it:
      * `HttpOnly` — the token is not readable from JavaScript, so XSS cannot
        copy it (asserted below and in `test_session.py`).
      * `SameSite` — a cross-site form post does not carry the cookie.
      * Short TTL — the window in which a stolen token is useful is small.
    """
    api.post("/session/login", json={"login": CUSTOMER, "password": "Testpass-001"})
    copied = api.cookies.get(SESSION_COOKIE)
    assert copied, "the session cookie must exist to replay it"

    attacker = type(api)(api.app)
    attacker.cookies.set(SESSION_COOKIE, copied)
    assert attacker.get("/transactions").status_code == 200, (
        "a copied bearer cookie is expected to work; this is the limitation"
    )

    # The mitigation that does hold: the cookie is not script-accessible.
    set_cookie = api.app.state and None  # keep flake8 quiet about unused names
    response = api.post("/session/login", json={"login": CUSTOMER, "password": "Testpass-001"})
    assert "HttpOnly" in response.headers.get("set-cookie", "")


def test_logout_does_not_invalidate_other_customers_sessions(api) -> None:
    """Isolation of the revocation, not of the credential.

    Two live sessions in the same process; logging out one must not kill the
    other. Each assertion uses a fresh client carrying an explicit token, so the
    original client's cookie jar cannot mask which session is being checked.
    """
    first_client = TestClient(api.app)
    first_client.post("/session/login", json={"login": CUSTOMER, "password": "Testpass-001"})
    first = first_client.cookies.get(SESSION_COOKIE)

    second_client = TestClient(api.app)
    second_client.post("/session/login", json={"login": "CUST-0002", "password": "Testpass-001"})
    second = second_client.cookies.get(SESSION_COOKIE)
    assert first != second

    first_client.post("/session/logout")

    revoked = TestClient(api.app)
    revoked.cookies.set(SESSION_COOKIE, first)
    assert revoked.get("/transactions").status_code == 401, "the logged-out session is dead"

    survivor = TestClient(api.app)
    survivor.cookies.set(SESSION_COOKIE, second)
    assert survivor.get("/transactions").status_code == 200, "the other session survives"
