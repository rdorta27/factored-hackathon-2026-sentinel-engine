from pathlib import Path
import re

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


def test_resolution_panel_renders_the_closed_steps() -> None:
    assert "renderSteps" in APP_JS
    assert 'data-testid", "steps-panel"' in APP_JS
    assert 'data-i18n="stepsTitle"' in INDEX
    assert "body.steps" in APP_JS
    assert "innerHTML" not in APP_JS
    strings = (STATIC / "i18n" / "es-419.json").read_text(encoding="utf-8")
    for key in (
        "stepsTitle",
        "step.understood",
        "step.lookedUp",
        "step.checkedPolicy",
        "step.caseOpened",
        "step.noCase",
        "step.handedOff",
        "step.refused",
    ):
        assert f'"{key}"' in strings, f"{key} missing from the locale"


def test_transaction_status_label_is_neutral() -> None:
    assert "statusLabel" in APP_JS
    assert "txStatusApproved" in APP_JS
    assert "tx-status" in APP_JS
    code = re.sub(r"/\*.*?\*/", "", APP_JS, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code).lower()
    for signal in ("fraud", "fraude", "score", "threshold", "umbral"):
        assert signal not in code, f"a fraud signal leaked into the page: {signal}"


def test_advisor_view_lists_tickets_and_opens_a_read_only_detail() -> None:
    assert 'data-testid="queue-detail"' in INDEX
    assert "queue-row" in APP_JS
    assert "openTicket" in APP_JS
    assert "/trace" in APP_JS and "traceBlock" in APP_JS
    assert "packageBlock" in APP_JS
    for key in ("q_language", "q_country", "q_reason", "q_created"):
        assert f't("{key}")' in APP_JS, f"the list must show {key}"
    # Read-only: the advisor block only issues GETs, never a write.
    start = APP_JS.index("function ticketRow")
    end = APP_JS.index('document.getElementById("login-form")')
    block = APP_JS[start:end]
    for method in ('method: "POST"', 'method: "PUT"', 'method: "PATCH"', 'method: "DELETE"'):
        assert method not in block, f"the advisor view issues a write: {method}"


def test_product_screens_are_captured() -> None:
    screens = Path(__file__).resolve().parents[2] / "docs" / "build" / "screenshots" / "ui-product"
    for locale in ("es-MX", "pt-BR"):
        for size in ("desktop", "phone"):
            for name in ("entry", "chat", "advisor-list", "advisor-detail"):
                path = screens / f"{name}-{locale}-{size}.png"
                assert path.is_file() and path.stat().st_size > 1000, path


def test_the_why_followup_returns_an_explanation_over_http() -> None:
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code == 200
    api.post("/api/v1/chat", json={"message": "Hay un cobro de 2500 MXN en ACME Store"})
    body = api.post("/api/v1/chat", json={"message": "¿de dónde salen los 90 días?"}).json()
    assert body["kind"] == "explanation"
    assert body["message_key"] == "explanation.window.expired"
    assert body["values"]["window_days"] == 90
    assert body["values"]["synthetic"] is True



def test_bank_shell_has_session_line_data_date_and_three_columns() -> None:
    for marker in ('id="session-context"', 'id="reference-date"', 'id="steps-col"', 'id="charges-col"', 'id="agent"'):
        assert marker in INDEX, marker
    # No balance anywhere in the shell or the script.
    for word in ("saldo", "balance", "saldo disponible"):
        assert word not in INDEX.lower() and word not in APP_JS.lower()
    # The product is shown only when the API sends one.
    assert "payload.product" in APP_JS
    assert "innerHTML" not in APP_JS


def test_charge_pill_reads_the_server_state_and_does_not_compute_it() -> None:
    assert "tx.case_state" in APP_JS
    for state in ("eligible", "in_review", "with_advisor", "already_disputed", "outside_window"):
        strings = (STATIC / "i18n" / "es-419.json").read_text(encoding="utf-8")
        assert f'"state.{state}"' in strings
    # The page never re-derives the window or the status rule.
    assert "window_days" not in APP_JS and "Date.now" not in APP_JS and "new Date()" not in APP_JS


def test_new_locale_keys_exist_in_both_languages() -> None:
    import json

    es = json.loads((STATIC / "i18n" / "es-419.json").read_text(encoding="utf-8"))
    pt = json.loads((STATIC / "i18n" / "pt-BR.json").read_text(encoding="utf-8"))
    used = set(re.findall(r'data-i18n="([^"]+)"', INDEX))
    assert used <= set(es) and used <= set(pt), sorted(used - set(es) | used - set(pt))
    assert set(es) == set(pt), sorted(set(es) ^ set(pt))
