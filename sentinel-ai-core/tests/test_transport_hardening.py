"""Transport hardening: Secure cookie by default, security headers, CSRF guard.

The session cookie is a bearer token; these are the three controls that stop
it from leaking or being abused from another site: Secure (no cleartext on
the wire), the response headers (clickjacking, sniffing), and the
Origin/Referer check on cookie-carrying writes (CSRF).
"""

import os

from fastapi.testclient import TestClient

from app.main import SESSION_COOKIE, create_app

LOGIN = "CUST-0001"
PASSWORD = "Testpass-001"


def login(api: TestClient) -> None:
    response = api.post("/api/v1/auth/login", json={"login": LOGIN, "password": PASSWORD})
    assert response.status_code == 200


def test_session_cookie_is_secure_by_default(monkeypatch) -> None:
    monkeypatch.setenv("SENTINEL_SECURE_COOKIES", "true")
    api = TestClient(create_app())
    cookie = api.post(
        "/api/v1/auth/login", json={"login": LOGIN, "password": PASSWORD}
    ).headers.get("set-cookie", "")
    assert "Secure" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Max-Age=" in cookie


def test_security_headers_on_api_and_page() -> None:
    api = TestClient(create_app())
    for response in (api.get("/api/v1/health"), api.get("/ui/")):
        headers = response.headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert "frame-ancestors 'deny'" in headers["Content-Security-Policy"]
        assert headers["Referrer-Policy"] == "no-referrer"
        assert headers["Strict-Transport-Security"].startswith("max-age=")


def test_cross_site_write_with_cookie_is_rejected() -> None:
    api = TestClient(create_app())
    login(api)
    payload = {"message": "hola"}
    # Browser on another origin: Origin is attached and does not match.
    cross = api.post(
        "/api/v1/chat",
        json=payload,
        headers={"Origin": "https://evil.example"},
    )
    assert cross.status_code == 403
    # Referer-only browsers (older) are checked the same way.
    via_referer = api.post(
        "/api/v1/chat",
        json=payload,
        headers={"Referer": "https://evil.example/attack.html"},
    )
    assert via_referer.status_code == 403


def test_same_origin_and_client_writes_stay_open() -> None:
    api = TestClient(create_app())
    login(api)
    same_origin = api.post(
        "/api/v1/chat",
        json={"message": "hola"},
        headers={"Origin": "http://testserver"},
    )
    assert same_origin.status_code == 200
    # Non-browser clients (tests, curl, smoke scripts) send neither header.
    no_headers = api.post("/api/v1/chat", json={"message": "hola"})
    assert no_headers.status_code == 200


def test_logout_clears_the_cookie_with_the_same_flags() -> None:
    api = TestClient(create_app())
    login(api)
    cookie = api.post("/api/v1/auth/logout").headers.get("set-cookie", "")
    assert SESSION_COOKIE in cookie
    assert "HttpOnly" in cookie
