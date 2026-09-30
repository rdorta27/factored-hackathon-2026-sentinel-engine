"""i18n tests: fallback, completeness of every rendered key, storage hygiene."""

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

I18N_DIR = Path(__file__).parent.parent / "app" / "ui" / "i18n"
STATIC_DIR = Path(__file__).parent.parent / "app" / "ui" / "static"
LOCALES = ("es-419", "es-MX", "es-CO", "es-AR", "pt-BR")
BASE = "es-419"


def base_strings() -> dict:
    return json.loads((I18N_DIR / f"{BASE}.json").read_text(encoding="utf-8"))


def test_regional_fallback_to_base() -> None:
    client = TestClient(create_app())
    base = client.get("/i18n/es-419").json()
    regional = client.get("/i18n/es-AR").json()
    assert regional["txWord"] == "consumo"  # overridden
    assert regional["loginTitle"] == base["loginTitle"]  # fell back
    assert set(base) <= set(regional)


def test_mexican_override_and_fallback() -> None:
    client = TestClient(create_app())
    strings = client.get("/i18n/es-MX").json()
    assert strings["agentButton"] == "Hablar con un asesor"
    assert strings["txWord"] == "cargo"  # inherited from es-419


def test_portuguese_is_complete() -> None:
    client = TestClient(create_app())
    base = client.get("/i18n/es-419").json()
    pt = client.get("/i18n/pt-BR").json()
    assert set(base) <= set(pt)
    assert pt["agentButton"] == "Falar com um atendente"


def test_unknown_locale_404() -> None:
    client = TestClient(create_app())
    assert client.get("/i18n/fr-FR").status_code == 404
    assert client.get("/i18n/xx").status_code == 404


def test_every_rendered_key_exists_in_every_locale() -> None:
    """Every key the UI renders must exist in all five locales.

    Keys are discovered from the render code and the HTML, so a new string
    added without a translation fails here instead of reaching the screen.
    """
    source = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    markup = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    rendered: set[str] = set(re.findall(r't\(\s*"([A-Za-z0-9_]+)"', source))
    rendered |= set(re.findall(r"data-i18n(?:-ph)?=\"([A-Za-z0-9_]+)\"", markup))
    rendered = {key for key in rendered if key != "a"}
    # Metric labels are built as `m_<event>`; collect the event names too.
    rendered |= {
        f"m_{event}"
        for event in (
            "login_success", "login_failed", "login_locked", "logout",
            "session_expired", "access_denied", "case_opened",
            "handoff_created", "case_claimed", "case_state_changed",
        )
    }
    timeline_keys = re.search(r"\[([^\]]*step_[^\]]*)\]", source)
    if timeline_keys:
        rendered |= set(re.findall(r'"(step_[a-z_]+)"', timeline_keys.group(1)))
    # Server-selected keys the client renders indirectly.
    rendered |= {
        "nextStepAdvisorReview", "ruleEligible", "queueInReview", "noFundsHeld",
        "handoffUnverified", "errorGeneric", "reasonAgentButton",
        "reasonCustomerAsked", "reasonHighRisk", "candidateOutOfWindow",
    }

    assert rendered, "expected to discover rendered keys"

    missing = {}
    client = TestClient(create_app())
    for locale in LOCALES:
        path = I18N_DIR / f"{locale}.json"
        assert path.exists(), f"locale file missing: {locale}"
        # Regionals override only; completeness is a property of the merge,
        # because that merged dictionary is what the interface renders.
        strings = client.get(f"/i18n/{locale}").json()
        absent = sorted(key for key in rendered if key not in strings)
        if absent:
            missing[locale] = absent
    assert not missing, f"untranslated keys per locale: {missing}"


def test_no_raw_keys_or_iso_dates_in_render_code() -> None:
    """No fabricated label literals and no raw ISO date rendering."""
    source = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    for raw_key in ('"hold"', '"rule"', '"ref"', 't("field_hold")'):
        assert raw_key not in source, f"raw key rendered: {raw_key}"
    assert "formatDate(display.slaDate)" in source, "SLA must be formatted"
    assert "sla_deadline" not in source, "raw ISO field must be gone"


def test_frontend_served_under_ui_prefix() -> None:
    client = TestClient(create_app())
    page = client.get("/ui/")
    assert page.status_code == 200
    for real_id in ('id="view-login"', 'id="thread"', 'id="transactions"'):
        assert real_id in page.text, f"app markup missing {real_id}"


def test_index_references_app_assets() -> None:
    markup = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    assert 'src="/ui/app.js"' in markup
    assert 'href="/ui/styles.css"' in markup
    client = TestClient(create_app())
    assert client.get("/ui/app.js").status_code == 200
    assert client.get("/ui/styles.css").status_code == 200


def test_ui_assets_load_without_404() -> None:
    client = TestClient(create_app())
    css = client.get("/ui/styles.css")
    js = client.get("/ui/app.js")
    assert css.status_code == 200
    assert js.status_code == 200
    assert ":root" in css.text
    assert "THEME_KEY" in js.text


def test_api_routes_still_reachable_under_ui_mount() -> None:
    client = TestClient(create_app())
    # The static mount on /ui must not shadow API paths.
    assert client.get("/i18n/es-419").status_code == 200
    assert client.get("/docs").status_code == 200
    assert client.post("/auth/login", json={}).status_code == 422


def test_root_redirects_to_ui() -> None:
    client = TestClient(create_app())
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 308)
    assert response.headers["location"].endswith("/ui/")


def test_only_theme_key_in_browser_storage() -> None:
    source = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
    assert "sentinel-theme" in source
    assert "localStorage.setItem" in source
    assert source.count("localStorage.setItem") == 1
    assert "innerHTML" not in source


def test_i18n_files_are_valid_json() -> None:
    for path in sorted(I18N_DIR.glob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))
