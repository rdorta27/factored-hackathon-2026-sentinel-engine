from fastapi.testclient import TestClient

from app.main import create_app

PASSWORD = "Testpass-001"


def login(api: TestClient, name: str = "CUST-0001") -> None:
    assert api.post("/session/login", json={"login": name, "password": PASSWORD}).status_code == 200


def test_listing_is_session_scoped_and_ordered() -> None:
    api = TestClient(create_app())
    login(api)
    response = api.get("/transactions")
    assert response.status_code == 200
    body = response.json()
    assert body["as_of"] == "2026-06-17"
    ids = [row["reference"] for row in body["transactions"]]
    dates = [row["date"] for row in body["transactions"]]
    assert "TXN-9001" not in ids
    assert "TXN-2001" not in ids
    assert dates == sorted(dates, reverse=True)
    assert body["transactions"][0]["currency"] == "MXN"


def test_customer_identifier_is_rejected() -> None:
    api = TestClient(create_app())
    login(api)
    response = api.get("/transactions", params={"customer_id": "CUST-9999"})
    assert response.status_code == 422


def test_listing_requires_a_session() -> None:
    api = TestClient(create_app())
    assert api.get("/transactions").status_code == 401
