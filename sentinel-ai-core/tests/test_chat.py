from fastapi.testclient import TestClient

from app.main import create_app

PASSWORD = "Testpass-001"


def client() -> TestClient:
    return TestClient(create_app())


def login(api: TestClient, name: str = "CUST-0001") -> None:
    assert api.post("/api/v1/session/login", json={"login": name, "password": PASSWORD}).status_code == 200


def test_chat_without_session_is_401() -> None:
    api = client()
    response = api.post("/api/v1/chat", json={"message": "hola"})
    assert response.status_code == 401
    assert api.app.state.audit.records[-1].event == "access_denied"


def test_extra_field_is_422() -> None:
    api = client()
    login(api)
    response = api.post("/api/v1/chat", json={"message": "hola", "customer_id": "CUST-0001"})
    assert response.status_code == 422


def test_clarification_then_selection_shows_the_box() -> None:
    api = client()
    login(api)
    asked = api.post("/api/v1/chat", json={"message": "HOLA"})
    assert asked.json()["kind"] == "clarification"
    chosen = api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"})
    body = chosen.json()
    assert body["kind"] == "confirm_box"
    assert "fields.missing" not in str(body)


def test_selection_does_not_open() -> None:
    api = client()
    login(api)
    response = api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "confirm_box"
    assert "confirmation_token" not in body
    assert body["candidate"]["merchant"] == "Cafe Central"
    token = next(iter(api.app.state.memories))
    assert api.app.state.memories[token].open_calls == 0


def test_foreign_reference_does_not_disclose() -> None:
    api = client()
    login(api)
    response = api.post("/api/v1/chat", json={"selected_reference": "TXN-9001"})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "handoff"
    assert "ACME Store" not in str(body)
    assert "100.00" not in str(body)


def test_confirmation_hides_the_token_and_skips_receipt() -> None:
    api = client()
    login(api)
    shown = api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"})
    assert shown.json()["kind"] == "confirm_box"
    opened = api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"})
    body = opened.json()
    assert body["kind"] == "case_confirmation"
    assert body["verified"] is True
    assert body["source"] == "mock"
    assert "confirmation_token" not in body
    assert "receipt" not in body
    assert api.get(f"/api/v1/disputes/{body['case_id']}/receipt").status_code == 404


def test_unverified_write_is_handoff_without_case_number() -> None:
    api = client()
    login(api)
    api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"})
    memory = next(iter(api.app.state.memories.values()))
    memory.lookup_failures_left = 3
    response = api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"})
    body = response.json()
    assert body["kind"] == "handoff"
    assert "case_id" not in body
    assert body["attempt"] == 3
