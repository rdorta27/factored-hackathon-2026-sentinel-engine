"""One-click demo personas behind SENTINEL_DEMO_AUTH (change ui-product 1.2)."""

from fastapi.testclient import TestClient

from app.main import create_app

PERSONAS = {
    "normal": "es-MX",
    "ambiguous": "pt-BR",
    "high-amount": "es-CO",
    "not-me": "es-AR",
}


def test_demo_route_does_not_exist_without_the_flag() -> None:
    api = TestClient(create_app())
    assert api.get("/api/v1/auth/demo").status_code == 404
    assert api.post("/api/v1/auth/demo/normal").status_code == 404


def test_personas_flag_zero_disables_the_route(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_DEMO_AUTH", "1")
    monkeypatch.setenv("SENTINEL_DEMO_PERSONAS", "0")
    api = TestClient(create_app())
    assert api.get("/api/v1/auth/demo").status_code == 404
    assert api.post("/api/v1/auth/demo/normal").status_code == 404


def test_personas_flag_unset_follows_demo_auth(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_DEMO_AUTH", "1")
    monkeypatch.delenv("SENTINEL_DEMO_PERSONAS", raising=False)
    api = TestClient(create_app())
    assert api.get("/api/v1/auth/demo").status_code == 200
    assert api.post("/api/v1/auth/demo/normal").status_code == 200


def test_advisor_still_needs_a_password_with_personas_off(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_DEMO_AUTH", "1")
    monkeypatch.setenv("SENTINEL_DEMO_PERSONAS", "0")
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/login", json={"login": "ADV-0001", "password": "wrong"}).status_code == 401
    assert api.post("/api/v1/auth/login", json={"login": "ADV-0001", "password": "Advisor-001"}).status_code == 200


def test_unknown_persona_is_404_with_the_flag(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_DEMO_AUTH", "1")
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/demo/someone").status_code == 404


def test_personas_list_matches_the_four_cases(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_DEMO_AUTH", "1")
    api = TestClient(create_app())
    body = api.get("/api/v1/auth/demo").json()
    assert {item["id"]: item["locale"] for item in body["personas"]} == PERSONAS
    assert "CUST-" not in api.get("/api/v1/auth/demo").text


def test_each_persona_signs_in_without_a_password(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_DEMO_AUTH", "1")
    for persona, locale in PERSONAS.items():
        api = TestClient(create_app())
        response = api.post(f"/api/v1/auth/demo/{persona}")
        assert response.status_code == 200, persona
        assert response.json()["role"] == "customer"
        assert response.json()["locale"] == locale
        me = api.get("/api/v1/auth/me").json()
        assert me["role"] == "customer"
        chat = api.post("/api/v1/chat", json={"message": "hola"})
        assert chat.status_code == 200
