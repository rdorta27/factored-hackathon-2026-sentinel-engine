from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

STATIC = Path(__file__).parent.parent / "app" / "static"
APP_JS = (STATIC / "app.js").read_text(encoding="utf-8")
INDEX = (STATIC / "index.html").read_text(encoding="utf-8")
PASSWORD = "Testpass-001"


def test_page_uses_confirm_box_and_hides_the_identifier() -> None:
    assert "chat-confirm" in APP_JS
    assert "selected_reference" in APP_JS
    assert "textContent" in APP_JS
    assert "innerHTML" not in APP_JS
    assert "/branding/brand.css" in INDEX
    assert "/branding/chat.css" in INDEX
    api = TestClient(create_app())
    page = api.get("/ui/")
    assert page.status_code == 200
    assert "chat-confirm" not in page.text or "class=\"chat-confirm\"" not in page.text
    assert api.get("/branding/chat.css").status_code == 200


def test_agent_control_is_two_step_and_session_is_not_stored() -> None:
    assert "localStorage" not in APP_JS
    assert "sessionStorage" not in APP_JS
    assert 't("agentMessage")' in APP_JS
    assert "quiero una persona" not in APP_JS
    assert "function clearThread()" in APP_JS
    start = APP_JS.index('getElementById("logout").addEventListener')
    assert 'clearThread();\n  show("view-login")' in APP_JS[start:start + 220]
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code == 200
    first = api.post("/api/v1/chat", json={"message": "quiero una persona"})
    second = api.post("/api/v1/chat", json={"message": "quiero una persona"})
    assert first.json()["kind"] == "text"
    assert second.json()["kind"] == "handoff"


def test_mask_keeps_only_the_last_four() -> None:
    assert "****" in APP_JS
    assert "slice(-4)" in APP_JS


def test_transactions_panel_marks_ineligible_and_paints_http_errors() -> None:
    """E2E: the panel only offers eligible charges, and a failed call is not
    rendered as a bot reply (it used to paint the JSON error body as text)."""
    assert "!tx.eligible" in APP_JS
    assert "ineligibleKey" in APP_JS
    assert "renderError" in APP_JS
    assert "!response.ok" in APP_JS
    assert "tooManyRequests" in APP_JS


def test_handoff_card_shows_the_reference() -> None:
    assert 't("field_reference")' in APP_JS
    assert "body.reference" in APP_JS


def test_explanation_renders_verified_values_not_prose() -> None:
    assert 'body.kind === "explanation"' in APP_JS
    assert "explanationText" in APP_JS
    assert "fillTemplate" in APP_JS
    assert "body.values" in APP_JS
    assert "explanation.demo" in APP_JS
    assert "innerHTML" not in APP_JS


def test_demo_entry_has_banner_personas_and_named_languages() -> None:
    assert 'data-testid="demo-banner"' in INDEX
    assert 'data-testid="demo-personas"' in INDEX
    assert INDEX.count('data-testid="demo-persona"') == 4
    assert "CUST-" not in INDEX
    assert 'id="password-login"' in INDEX
    for name in (
        "Español · Latinoamérica",
        "Español · México",
        "Español · Colombia",
        "Español · Argentina",
        "Português · Brasil",
    ):
        assert name in INDEX, f"named language missing: {name}"
    for code in (">es-419<", ">es-MX<", ">es-CO<", ">es-AR<", ">pt-BR<"):
        assert code not in INDEX, f"locale code shown as a label: {code}"
    assert 'data-testid="locale-button"' in INDEX
    assert "locale-group" in APP_JS
    assert "/api/v1/auth/demo" in APP_JS


def test_the_why_followup_returns_an_explanation_over_http() -> None:
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code == 200
    api.post("/api/v1/chat", json={"message": "Hay un cobro de 2500 MXN en ACME Store"})
    body = api.post("/api/v1/chat", json={"message": "¿de dónde salen los 90 días?"}).json()
    assert body["kind"] == "explanation"
    assert body["message_key"] == "explanation.window.expired"
    assert body["values"]["window_days"] == 90
    assert body["values"]["synthetic"] is True

