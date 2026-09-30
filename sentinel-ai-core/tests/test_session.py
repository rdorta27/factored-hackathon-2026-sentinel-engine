import json
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import SESSION_COOKIE, create_app
from app.session.clock import DEFAULT_REFERENCE_DATE

PASSWORD = "Testpass-001"
LOGIN = "CUST-0001"


def client() -> TestClient:
    return TestClient(create_app())


def login(api: TestClient, name: str = LOGIN, password: str = PASSWORD):
    return api.post("/session/login", json={"login": name, "password": password})


def test_login_sets_cookie_and_me_returns_customer_and_country() -> None:
    api = client()
    response = login(api)
    assert response.status_code == 200
    cookie = response.headers.get("set-cookie", "")
    assert SESSION_COOKIE in cookie
    assert "HttpOnly" in cookie
    me = api.get("/session/me")
    assert me.status_code == 200
    assert me.json() == {"customer_id": "CUST-0001", "country": "MX"}


def test_wrong_password_and_unknown_user_are_identical() -> None:
    api = client()
    wrong = login(api, password="wrong-password")
    unknown = login(api, name="CUST-9999")
    assert wrong.status_code == 401
    assert unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Invalid credentials"}
    events = [row.event for row in api.app.state.audit.records]
    assert events.count("login_failed") == 2


def test_customer_id_in_login_body_is_rejected() -> None:
    api = client()
    response = api.post(
        "/session/login",
        json={"login": LOGIN, "password": PASSWORD, "customer_id": "CUST-9999"},
    )
    assert response.status_code == 422
    assert api.app.state.audit.records == []


def test_expired_session_is_cleared() -> None:
    api = client()
    assert login(api).status_code == 200
    token = api.cookies.get(SESSION_COOKIE)
    store = api.app.state.session_service._sessions
    session = store._sessions[token]
    store._sessions[token] = session.__class__(
        **{**session.__dict__, "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)}
    )
    response = api.get("/session/me")
    assert response.status_code == 401
    assert api.app.state.audit.records[-1].event == "session_expired"
    assert token not in store._sessions


def test_logout_revokes_the_token() -> None:
    api = client()
    login(api)
    assert api.post("/session/logout").status_code == 200
    assert api.get("/session/me").status_code == 401
    assert api.app.state.audit.records[-1].event == "access_denied"


def test_lockout_after_five_failures() -> None:
    api = client()
    for _ in range(5):
        assert login(api, password="wrong").status_code == 401
    blocked = login(api, password="wrong")
    assert blocked.status_code == 429
    assert api.app.state.audit.records[-1].event == "login_locked"


def test_audit_has_no_password_or_token() -> None:
    api = client()
    login(api)
    token = api.cookies.get(SESSION_COOKIE)
    dumped = "\n".join(row.to_json() for row in api.app.state.audit.records)
    assert PASSWORD not in dumped
    assert token not in dumped
    assert LOGIN not in dumped
    assert api.app.state.audit.records[-1].trace_id


def test_audit_session_ref_is_a_hash_not_the_customer() -> None:
    api = client()
    login(api)
    record = api.app.state.audit.records[-1]
    assert record.event == "login_success"
    assert record.step == "session"
    assert record.session_ref != LOGIN
    assert len(record.session_ref) == 16


def test_reference_date_defaults_and_override(monkeypatch) -> None:
    monkeypatch.delenv("SENTINEL_REFERENCE_DATE", raising=False)
    assert create_app().state.reference_date.isoformat() == DEFAULT_REFERENCE_DATE
    monkeypatch.setenv("SENTINEL_REFERENCE_DATE", "2026-03-01")
    assert create_app().state.reference_date.isoformat() == "2026-03-01"
    monkeypatch.setenv("SENTINEL_REFERENCE_DATE", "not-a-date")
    assert create_app().state.reference_date.isoformat() == DEFAULT_REFERENCE_DATE
