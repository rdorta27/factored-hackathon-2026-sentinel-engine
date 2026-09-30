"""Endpoint tests: login, logout, session identity, and attack shapes."""

from fastapi.testclient import TestClient

from app.main import SESSION_COOKIE, create_app

PASSWORD = "Testpass-001"
CUSTOMER = "CUST-0001"


def make_client() -> TestClient:
    return TestClient(create_app())


def login(client: TestClient, customer: str = CUSTOMER, password: str = PASSWORD):
    return client.post("/auth/login", json={"customer_id": customer, "password": password})


def test_login_success_sets_http_only_cookie() -> None:
    client = make_client()
    response = login(client)
    assert response.status_code == 200
    cookie = response.headers.get("set-cookie", "")
    assert SESSION_COOKIE in cookie
    assert "HttpOnly" in cookie
    assert "X-Trace-Id" in response.headers


def test_login_wrong_password_generic_401() -> None:
    client = make_client()
    response = login(client, password="Wrongpass-999")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
    assert "WWW-Authenticate" in response.headers


def test_login_unknown_user_same_generic_401() -> None:
    client = make_client()
    response = login(client, customer="CUST-9999")
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_login_missing_field_422() -> None:
    client = make_client()
    response = client.post("/auth/login", json={"customer_id": CUSTOMER})
    assert response.status_code == 422


def test_smuggled_customer_id_rejected_with_422() -> None:
    # Belt 2 of session-derived identity: the body cannot carry customer_id
    # anywhere except the declared credential field.
    client = make_client()
    response = client.post(
        "/auth/login",
        json={"customer_id": CUSTOMER, "password": PASSWORD, "role": "admin"},
    )
    assert response.status_code == 422


def test_me_returns_session_customer() -> None:
    client = make_client()
    assert login(client).status_code == 200
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json() == {"customer_id": CUSTOMER}


def test_me_without_cookie_401() -> None:
    client = make_client()
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_me_with_forged_token_401() -> None:
    client = make_client()
    client.cookies.set(SESSION_COOKIE, "forged-token-value")
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout_revokes_token() -> None:
    client = make_client()
    assert login(client).status_code == 200
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_logout_without_session_is_idempotent() -> None:
    client = make_client()
    assert client.post("/auth/logout").status_code == 200
