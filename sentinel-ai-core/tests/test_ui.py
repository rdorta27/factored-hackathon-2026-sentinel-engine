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
    assert "quiero una persona" in APP_JS
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code == 200
    first = api.post("/api/v1/chat", json={"message": "quiero una persona"})
    second = api.post("/api/v1/chat", json={"message": "quiero una persona"})
    assert first.json()["kind"] == "text"
    assert second.json()["kind"] == "handoff"


def test_mask_keeps_only_the_last_four() -> None:
    assert "****" in APP_JS
    assert "slice(-4)" in APP_JS
