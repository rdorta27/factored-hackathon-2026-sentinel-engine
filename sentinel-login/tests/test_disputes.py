"""Dispute endpoint tests: creation, refusals, replay, receipt, isolation."""

from fastapi.testclient import TestClient

from app.main import create_app

CUSTOMER = ("CUST-0001", "Testpass-001")


def make_client() -> TestClient:
    client = TestClient(create_app())
    assert (
        client.post(
            "/auth/login",
            json={"customer_id": CUSTOMER[0], "password": CUSTOMER[1]},
        ).status_code
        == 200
    )
    return client


def create(client: TestClient, ref: str, key: str = "key-1"):
    return client.post(
        "/api/v1/disputes/create",
        json={"transaction_ref": ref},
        headers={"Idempotency-Key": key},
    )


def test_eligible_creates_case_with_proof() -> None:
    response = create(make_client(), "TXN-1001")
    assert response.status_code == 201
    body = response.json()
    assert body["case_id"].startswith("CASE-")
    assert body["verified"] is True
    assert "temporarily held (simulated)" in body["hold"]
    assert "90-day" in body["rule"] and "Art. 4" in body["rule"]
    assert body["sla_deadline"].startswith("2026-06-21")
    assert body["receipt_ref"] == f"RCPT-{body['case_id']}"
    assert "Queued" in body["queue_status"]
    assert body["source"] == "mock"


def test_stale_refused_with_reason() -> None:
    response = create(make_client(), "TXN-1002")
    assert response.status_code == 422
    assert "90-day" in response.json()["reason"]


def test_refunded_refused() -> None:
    response = create(make_client(), "TXN-1003")
    assert response.status_code == 422
    assert "refunded" in response.json()["reason"]


def test_prior_dispute_refused() -> None:
    response = create(make_client(), "TXN-1004")
    assert response.status_code == 422
    assert "already" in response.json()["reason"]


def test_unknown_reference_refused() -> None:
    response = create(make_client(), "TXN-0000")
    assert response.status_code == 422


def test_duplicate_key_replays_without_new_case() -> None:
    client = make_client()
    first = create(client, "TXN-1001", key="dup-1")
    second = create(client, "TXN-1001", key="dup-1")
    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json()["case_id"] == first.json()["case_id"]
    assert len(client.app.state.cases._cases) == 1


def test_refusal_creates_no_case() -> None:
    client = make_client()
    create(client, "TXN-1002", key="r-1")
    assert client.app.state.cases._cases == {}


def test_receipt_download() -> None:
    client = make_client()
    case_id = create(client, "TXN-1001").json()["case_id"]
    response = client.get(f"/api/v1/disputes/{case_id}/receipt")
    assert response.status_code == 200
    assert "DISPUTE RECEIPT" in response.text
    assert case_id in response.text
    assert "simulated" in response.text


def test_receipt_unknown_404() -> None:
    client = make_client()
    assert client.get("/api/v1/disputes/CASE-9999/receipt").status_code == 404


def test_create_without_session_401() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/disputes/create", json={"transaction_ref": "TXN-1001"}
    )
    assert response.status_code == 401


def test_create_extra_field_422() -> None:
    client = make_client()
    response = client.post(
        "/api/v1/disputes/create",
        json={"transaction_ref": "TXN-1001", "amount": "99999"},
    )
    assert response.status_code == 422


def test_advisor_cannot_create_403() -> None:
    client = TestClient(create_app())
    client.post("/auth/login", json={"customer_id": "ADV-0001", "password": "Advisor-001"})
    response = client.post(
        "/api/v1/disputes/create", json={"transaction_ref": "TXN-1001"}
    )
    assert response.status_code == 403
