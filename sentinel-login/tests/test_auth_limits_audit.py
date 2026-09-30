"""Tests for attempt limiting and the JSON audit log."""

from datetime import timedelta

from fastapi.testclient import TestClient

from app.main import SESSION_COOKIE, create_app

PASSWORD = "Testpass-001"
CUSTOMER = "CUST-0001"


def test_lockout_after_five_failures() -> None:
    client = TestClient(create_app())
    for _ in range(5):
        response = client.post(
            "/auth/login", json={"customer_id": CUSTOMER, "password": "wrong"}
        )
        assert response.status_code == 401
    blocked = client.post(
        "/auth/login", json={"customer_id": CUSTOMER, "password": "wrong"}
    )
    assert blocked.status_code == 429
    assert blocked.json() == {"detail": "Too many failed attempts. Try again later."}
    audit = client.app.state.audit
    assert [r["event"] for r in audit.records].count("login_failed") == 5
    assert audit.records[-1]["event"] == "login_locked"


def test_success_resets_failure_counter() -> None:
    client = TestClient(create_app())
    for _ in range(4):
        client.post("/auth/login", json={"customer_id": CUSTOMER, "password": "wrong"})
    assert (
        client.post(
            "/auth/login", json={"customer_id": CUSTOMER, "password": PASSWORD}
        ).status_code
        == 200
    )
    for _ in range(4):
        client.post("/auth/login", json={"customer_id": CUSTOMER, "password": "wrong"})
    # 8 failures total but split by a success: no lockout yet.
    response = client.post(
        "/auth/login", json={"customer_id": CUSTOMER, "password": "wrong"}
    )
    assert response.status_code == 401


def test_audit_record_shape_and_no_secrets() -> None:
    client = TestClient(create_app())
    client.post("/auth/login", json={"customer_id": CUSTOMER, "password": PASSWORD})
    client.get("/auth/me")
    client.get("/auth/me", headers={"Cookie": f"{SESSION_COOKIE}=forged"})
    records = client.app.state.audit.records
    assert records, "expected audit records"
    for record in records:
        assert {"ts", "event", "customer_id", "trace_id", "ip"} <= set(record)
        assert len(record["trace_id"]) == 16
    blob = " ".join(str(v) for r in records for v in r.values())
    assert PASSWORD not in blob
    forged_events = [r["event"] for r in records if r["event"] == "access_denied"]
    assert forged_events


def test_expired_session_audited_as_session_expired() -> None:
    import app.auth.service as service_module

    service_module.SESSION_TTL = timedelta(seconds=-1)
    try:
        client = TestClient(create_app())
        assert (
            client.post(
                "/auth/login", json={"customer_id": CUSTOMER, "password": PASSWORD}
            ).status_code
            == 200
        )
        response = client.get("/auth/me")
        assert response.status_code == 401
        assert response.json() == {"detail": "Session expired"}
        events = [r["event"] for r in client.app.state.audit.records]
        assert "session_expired" in events
    finally:
        service_module.SESSION_TTL = timedelta(minutes=30)
