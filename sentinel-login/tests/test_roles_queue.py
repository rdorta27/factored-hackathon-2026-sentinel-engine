"""Privilege-escalation matrix and the advisor queue flow."""

from fastapi.testclient import TestClient

from app.main import create_app

CUSTOMER = ("CUST-0001", "Testpass-001")
ADVISOR = ("ADV-0001", "Advisor-001")
ADMIN = ("ADM-0001", "Admin-001")


def login_as(client: TestClient, creds: tuple[str, str]) -> None:
    assert (
        client.post(
            "/auth/login",
            json={"customer_id": creds[0], "password": creds[1]},
        ).status_code
        == 200
    )


def test_customer_cannot_list_queue_403() -> None:
    client = TestClient(create_app())
    login_as(client, CUSTOMER)
    response = client.get("/advisor/cases")
    assert response.status_code == 403
    assert response.json() == {"detail": "Access denied"}


def test_unauthenticated_queue_access_401() -> None:
    client = TestClient(create_app())
    assert client.get("/advisor/cases").status_code == 401


def test_handoff_appears_in_queue_with_summary_only() -> None:
    client = TestClient(create_app())
    login_as(client, CUSTOMER)
    assert client.post("/chat", json={"message": "stolen card fraud"}).status_code == 200
    login_as(client, ADVISOR)
    response = client.get("/advisor/cases")
    assert response.status_code == 200
    cases = response.json()["cases"]
    assert len(cases) == 1
    case = cases[0]
    assert case["reference"].startswith("HO-CASE-")
    assert "transcript" not in case
    assert "profile" not in case
    assert case["state"] == "Escalated"


def test_advisor_claims_and_advances_case() -> None:
    client = TestClient(create_app())
    login_as(client, CUSTOMER)
    client.post("/chat", json={"message": "stolen card fraud"})
    client.post("/auth/login", json={"customer_id": ADVISOR[0], "password": ADVISOR[1]})
    cases = client.get("/advisor/cases").json()["cases"]
    case_id = cases[0]["case_id"]
    claimed = client.post(f"/advisor/cases/{case_id}/claim")
    assert claimed.status_code == 200
    assert claimed.json()["owner"] == "ADV-0001"
    assert claimed.json()["state"] == "InReview"
    moved = client.post(f"/advisor/cases/{case_id}/state", json={"state": "Resolved"})
    assert moved.status_code == 200
    assert moved.json()["state"] == "Resolved"
    assert client.get("/advisor/cases").json()["cases"] == []


def test_claim_non_escalated_case_404() -> None:
    client = TestClient(create_app())
    login_as(client, ADVISOR)
    assert client.post("/advisor/cases/CASE-9999/claim").status_code == 404


def test_denied_access_is_audited() -> None:
    client = TestClient(create_app())
    login_as(client, CUSTOMER)
    client.get("/advisor/cases")
    events = [r["event"] for r in client.app.state.audit.records]
    assert "access_denied" in events
