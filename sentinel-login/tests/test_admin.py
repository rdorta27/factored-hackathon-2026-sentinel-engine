"""Admin tests: counts match audit events, no conversation content leaks."""

from fastapi.testclient import TestClient

from app.main import create_app

CUSTOMER = ("CUST-0001", "Testpass-001")
ADVISOR = ("ADV-0001", "Advisor-001")
ADMIN = ("ADM-0001", "Admin-001")


def test_advisor_cannot_reach_admin_403() -> None:
    client = TestClient(create_app())
    client.post("/auth/login", json={"customer_id": ADVISOR[0], "password": ADVISOR[1]})
    assert client.get("/admin/metrics").status_code == 403
    assert client.get("/admin/audit").status_code == 403


def test_customer_cannot_reach_admin_403() -> None:
    client = TestClient(create_app())
    client.post(
        "/auth/login", json={"customer_id": CUSTOMER[0], "password": CUSTOMER[1]}
    )
    assert client.get("/admin/metrics").status_code == 403


def test_metrics_match_audit_events() -> None:
    client = TestClient(create_app())
    client.post("/auth/login", json={"customer_id": CUSTOMER[0], "password": CUSTOMER[1]})
    client.post("/chat", json={"message": "stolen card fraud"})
    client.post("/chat", json={"message": "help with charge"})
    client.post("/auth/login", json={"customer_id": ADMIN[0], "password": ADMIN[1]})
    metrics = client.get("/admin/metrics").json()["metrics"]
    records = client.get("/admin/audit").json()["records"]
    assert metrics["login_success"] == 2
    assert metrics["handoff_created"] == 1
    assert metrics["login_failed"] == 0
    assert sum(1 for r in records if r["event"] == "handoff_created") == 1


def test_no_message_text_in_audit() -> None:
    client = TestClient(create_app())
    secret = "my secret charge xyzzy-999"
    client.post("/auth/login", json={"customer_id": CUSTOMER[0], "password": CUSTOMER[1]})
    client.post("/chat", json={"message": secret})
    client.post("/auth/login", json={"customer_id": ADMIN[0], "password": ADMIN[1]})
    blob = client.get("/admin/audit").json()
    assert "xyzzy-999" not in str(blob)
