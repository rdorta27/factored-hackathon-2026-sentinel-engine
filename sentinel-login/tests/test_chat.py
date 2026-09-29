"""Chat tests: one contract per scenario, auth shapes, verified-only confirmations."""

from fastapi.testclient import TestClient

from app.main import create_app

CUSTOMER = ("CUST-0001", "Testpass-001")


def make_customer_client() -> TestClient:
    client = TestClient(create_app())
    assert (
        client.post(
            "/auth/login",
            json={"customer_id": CUSTOMER[0], "password": CUSTOMER[1]},
        ).status_code
        == 200
    )
    return client


def test_normal_case_returns_verified_confirmation() -> None:
    client = make_customer_client()
    response = client.post("/chat", json={"message": "I dispute the charge of 1000 at ACME"})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "case_confirmation"
    assert body["verified"] is True
    assert body["case_id"].startswith("CASE-")
    assert body["transaction"] == {
        "amount": "1000.00",
        "currency": "MXN",
        "merchant": "ACME Store",
        "date": "2026-06-10",
    }
    assert "verified_at" in body
    assert body["source"] == "mock"
    assert "temporarily held (simulated)" in body["hold"]
    assert "Art. 4" in body["eligibility"]
    assert body["receipt_ref"] == f"RCPT-{body['case_id']}"


def test_chat_confirmation_matches_disputes_service() -> None:
    client = make_customer_client()
    endpoint = client.post(
        "/api/v1/disputes/create",
        json={"transaction_ref": "TXN-1001"},
        headers={"Idempotency-Key": "chat-parity-1"},
    ).json()
    chat = client.post(
        "/chat", json={"message": "I dispute the charge of 1000 at ACME"}
    ).json()
    assert chat["hold"] == endpoint["hold"]
    assert chat["eligibility"] == endpoint["rule"]
    from datetime import datetime

    assert datetime.fromisoformat(chat["sla_deadline"]) == datetime.fromisoformat(
        endpoint["sla_deadline"]
    )
    assert chat["queue_status"] == endpoint["queue_status"]


def test_stale_charge_chat_returns_handoff() -> None:
    client = make_customer_client()
    response = client.post("/chat", json={"message": "dispute the old charge from january"})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "handoff"
    assert "90-day" in body["reason"]


def test_refunded_charge_chat_returns_handoff() -> None:
    client = make_customer_client()
    response = client.post("/chat", json={"message": "dispute the refunded charge"})
    assert response.status_code == 200
    assert response.json()["kind"] == "handoff"


def test_ambiguous_message_returns_clarification() -> None:
    client = make_customer_client()
    response = client.post("/chat", json={"message": "help with charge"})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "clarification"
    assert body["missing"] == "transaction"


def test_high_risk_message_returns_handoff() -> None:
    client = make_customer_client()
    response = client.post("/chat", json={"message": "my card was stolen, fraud!"})
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "handoff"
    assert body["reference"].startswith("HO-CASE-")
    assert "advisor_received" in body


def test_broken_store_returns_handoff_never_confirmation() -> None:
    client = make_customer_client()
    response = client.post("/chat", json={"message": "broken dispute flow error test"})
    assert response.status_code == 200
    assert response.json()["kind"] == "handoff"


def test_agent_request_escalates_on_insistence() -> None:
    client = make_customer_client()
    first = client.post("/chat", json={"message": "I want a human agent"})
    assert first.json()["kind"] == "text"
    second = client.post("/chat", json={"message": "agent please"})
    assert second.json()["kind"] == "handoff"


def test_chat_without_session_401() -> None:
    client = TestClient(create_app())
    response = client.post("/chat", json={"message": "dispute charge 1000"})
    assert response.status_code == 401


def test_chat_extra_field_422() -> None:
    client = make_customer_client()
    response = client.post(
        "/chat", json={"message": "dispute charge", "customer_id": "CUST-9999"}
    )
    assert response.status_code == 422


def test_chat_rejects_non_customer_role_403() -> None:
    client = TestClient(create_app())
    assert (
        client.post(
            "/auth/login", json={"customer_id": "ADV-0001", "password": "Advisor-001"}
        ).status_code
        == 200
    )
    response = client.post("/chat", json={"message": "dispute charge 1000"})
    assert response.status_code == 403
