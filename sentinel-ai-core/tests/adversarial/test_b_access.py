"""B. Unauthorized access.

Already covered elsewhere and **not duplicated here** (listed in the summary):
`test_chat.py::test_foreign_reference_does_not_disclose` (B1),
`test_transactions.py::test_customer_identifier_is_rejected` (B2),
`test_chat.py::test_extra_field_is_422` (B5).

This module adds the shapes that had no test: a forged cookie, a malformed
reference, and the documented behaviour of a replayed bearer cookie.
"""

import pytest
from fastapi.testclient import TestClient

from app.session.router import SESSION_COOKIE

from .conftest import CUSTOMER, facts_travel_nowhere, login_as

# --- blocked (verified) ---


@pytest.mark.attack("B3", "blocked_verified")
def test_forged_session_token_is_rejected(api) -> None:
    """B3. An invented token has no server-side session behind it."""
    api.cookies.set(SESSION_COOKIE, "forged-token-value")
    assert api.get("/api/v1/transactions").status_code == 401
    assert api.post("/api/v1/chat", json={"message": "hola"}).status_code == 401


@pytest.mark.attack("B6", "blocked_verified")
def test_reference_with_path_shapes_is_rejected(logged_in) -> None:
    """B6. The selection pattern is format-neutral but bounded."""
    for payload in ("../../etc/passwd", "TXN 1001", "x" * 65, ""):
        response = logged_in.post("/api/v1/chat", json={"selected_reference": payload})
        assert response.status_code == 422, payload


@pytest.mark.attack("B1v", "blocked_verified")
def test_selection_cannot_name_another_customers_row(logged_in) -> None:
    """B1 variant: the same attempt through the session-scoped lookup.

    blocked (verified): even if the id were guessable, `gold.get(...)` is
    scoped to the session customer and returns nothing.
    """
    response = logged_in.post("/api/v1/chat", json={"selected_reference": "TXN-9001"})
    assert response.status_code == 200
    assert facts_travel_nowhere(response.json())


@pytest.mark.attack("B7", "blocked_verified")
def test_foreign_rows_are_absent_from_the_listing(logged_in) -> None:
    listing = logged_in.get("/api/v1/transactions").json()["transactions"]
    ids = {row["reference"] for row in listing}
    assert "TXN-9001" not in ids
    assert "TXN-2001" not in ids
    assert "TXN-3001" not in ids


# --- documented behaviour, not a block: bearer cookie replay ---------------


@pytest.mark.attack("B4", "documented")
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
    api.post("/api/v1/auth/login", json={"login": CUSTOMER, "password": "Testpass-001"})
    copied = api.cookies.get(SESSION_COOKIE)
    assert copied, "the session cookie must exist to replay it"

    attacker = type(api)(api.app)
    attacker.cookies.set(SESSION_COOKIE, copied)
    assert attacker.get("/api/v1/transactions").status_code == 200, (
        "a copied bearer cookie is expected to work; this is the limitation"
    )

    # The mitigation that does hold: the cookie is not script-accessible.
    response = api.post("/api/v1/auth/login", json={"login": CUSTOMER, "password": "Testpass-001"})
    assert "HttpOnly" in response.headers.get("set-cookie", "")


@pytest.mark.attack("B8", "blocked_verified")
def test_logout_does_not_invalidate_other_customers_sessions(api) -> None:
    """Isolation of the revocation, not of the credential.

    Two live sessions in the same process; logging out one must not kill the
    other. Each assertion uses a fresh client carrying an explicit token, so the
    original client's cookie jar cannot mask which session is being checked.
    """
    first_client = TestClient(api.app)
    first_client.post("/api/v1/auth/login", json={"login": CUSTOMER, "password": "Testpass-001"})
    first = first_client.cookies.get(SESSION_COOKIE)

    second_client = TestClient(api.app)
    second_client.post("/api/v1/auth/login", json={"login": "CUST-0002", "password": "Testpass-001"})
    second = second_client.cookies.get(SESSION_COOKIE)
    assert first != second

    first_client.post("/api/v1/auth/logout")

    revoked = TestClient(api.app)
    revoked.cookies.set(SESSION_COOKIE, first)
    assert revoked.get("/api/v1/transactions").status_code == 401, "the logged-out session is dead"

    survivor = TestClient(api.app)
    survivor.cookies.set(SESSION_COOKIE, second)
    assert survivor.get("/api/v1/transactions").status_code == 200, "the other session survives"


# --- disputes API: a second entry point, same isolation ---


@pytest.mark.attack("B9", "blocked_verified")
def test_disputes_api_never_reaches_another_customers_charge_or_case(logged_in) -> None:
    """B9. Another customer's charge or case through `/api/v1/disputes` is unknown.

    blocked (verified): the preview resolves the reference inside the session
    customer's Gold rows (handoff, no facts), and a case id from another
    customer is a 404 indistinguishable from a missing case.
    """
    preview = logged_in.post("/api/v1/disputes/preview", json={"reference": "TXN-9001"})
    assert preview.json()["kind"] == "handoff"
    assert facts_travel_nowhere(preview.json())
    assert "ACME Store" not in preview.text and "100.00" not in preview.text
    assert logged_in.post("/api/v1/disputes", json={"reference": "TXN-9001"}).status_code == 409

    logged_in.post("/api/v1/disputes/preview", json={"reference": "TXN-1006"})
    case_id = logged_in.post("/api/v1/disputes", json={"reference": "TXN-1006"}).json()["case_id"]
    logged_in.post("/api/v1/auth/logout")
    login_as(logged_in, "CUST-0002")
    assert logged_in.get(f"/api/v1/disputes/{case_id}").status_code == 404
    assert logged_in.get("/api/v1/disputes").json() == []


@pytest.mark.attack("B10", "blocked_verified")
def test_disputes_api_rejects_a_client_supplied_identity(logged_in) -> None:
    """B10. A `customer_id` in the body or the query never selects whose data is used."""
    body = {"reference": "TXN-1006", "customer_id": "CUST-0002"}
    assert logged_in.post("/api/v1/disputes/preview", json=body).status_code == 422
    assert logged_in.post("/api/v1/disputes", json=body).status_code == 422
    assert logged_in.get("/api/v1/disputes", params={"customer_id": "CUST-0002"}).status_code == 422


# --- advisor endpoint: the most sensitive read, every customer's tickets ---


@pytest.mark.attack("B11", "blocked_verified")
def test_customer_cannot_read_the_advisor_tickets(logged_in) -> None:
    """B11. A customer session asking for `/api/v1/handoffs` gets 403, never tickets.

    blocked (verified): the role stored on the server-side session is checked
    in code (`require_advisor`); the denial is audited as `access_denied`.
    Another customer's escalation exists, so a leak would be visible.
    """
    logged_in.post("/api/v1/auth/logout")
    login_as(logged_in, "CUST-0002")
    logged_in.post("/api/v1/chat", json={"message": "quiero una persona"})
    logged_in.post("/api/v1/chat", json={"message": "quiero una persona"})
    logged_in.post("/api/v1/auth/logout")

    login_as(logged_in, CUSTOMER)
    for path in ("/api/v1/handoffs", "/api/v1/handoffs/HO-00000000"):
        response = logged_in.get(path)
        assert response.status_code == 403
        assert "CUST-0002" not in response.text and "package" not in response.text
    assert logged_in.app.state.audit.records[-1].event == "access_denied"


@pytest.mark.attack("B12", "blocked_verified")
def test_advisor_login_does_not_exist_outside_demo_auth(api, monkeypatch) -> None:
    """B12. Without `SENTINEL_DEMO_AUTH=1` the advisor credential is an unknown user.

    blocked (verified): non-customer fixture users load only under the flag,
    and the failure is the same generic 401 as any unknown login.
    """
    monkeypatch.delenv("SENTINEL_DEMO_AUTH", raising=False)
    from app.main import create_app

    fresh = TestClient(create_app())
    response = fresh.post("/api/v1/auth/login", json={"login": "ADV-0001", "password": "Advisor-001"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
    assert fresh.get("/api/v1/handoffs").status_code == 401
