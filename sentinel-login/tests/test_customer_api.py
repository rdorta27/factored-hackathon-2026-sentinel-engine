"""Customer read endpoints that feed the interface panel and locale default."""

from fastapi.testclient import TestClient

from app.main import create_app

CREDENTIALS = {
    "CUST-0001": ("Testpass-001", "MXN", "es-MX"),
    "CUST-0002": ("Testpass-001", "COP", "es-CO"),
    "CUST-0003": ("Testpass-001", "ARS", "es-AR"),
}


def login(client: TestClient, customer_id: str) -> None:
    password = CREDENTIALS[customer_id][0]
    assert (
        client.post(
            "/auth/login", json={"customer_id": customer_id, "password": password}
        ).status_code
        == 200
    )


def test_each_country_lists_its_own_currency() -> None:
    for customer_id, (_, currency, _locale) in CREDENTIALS.items():
        client = TestClient(create_app())
        login(client, customer_id)
        body = client.get("/api/v1/transactions").json()
        assert body["transactions"], customer_id
        assert {tx["currency"] for tx in body["transactions"]} == {currency}


def test_listing_carries_the_reference_date() -> None:
    client = TestClient(create_app())
    login(client, "CUST-0001")
    assert client.get("/api/v1/transactions").json()["referenceDate"] == "2026-06-17"


def test_listing_never_leaks_another_customer() -> None:
    client = TestClient(create_app())
    login(client, "CUST-0001")
    references = {tx["reference"] for tx in client.get("/api/v1/transactions").json()["transactions"]}
    assert "TXN-9001" not in references
    assert all(ref.startswith("TXN-1") for ref in references)


def test_transactions_require_a_session() -> None:
    client = TestClient(create_app())
    assert client.get("/api/v1/transactions").status_code == 401


def test_advisor_cannot_list_customer_transactions() -> None:
    client = TestClient(create_app())
    client.post("/auth/login", json={"customer_id": "ADV-0001", "password": "Advisor-001"})
    assert client.get("/api/v1/transactions").status_code == 403


def test_session_context_defaults_language_by_country() -> None:
    for customer_id, (_, _currency, locale) in CREDENTIALS.items():
        client = TestClient(create_app())
        login(client, customer_id)
        context = client.get("/api/v1/session/context").json()
        assert context["defaultLocale"] == locale
        assert context["referenceDate"] == "2026-06-17"


def test_session_context_masks_nothing_sensitive() -> None:
    client = TestClient(create_app())
    login(client, "CUST-0001")
    context = client.get("/api/v1/session/context").json()
    assert set(context) == {"displayName", "country", "defaultLocale", "referenceDate"}
    assert "customer_id" not in context
    assert "password" not in str(context).lower()
