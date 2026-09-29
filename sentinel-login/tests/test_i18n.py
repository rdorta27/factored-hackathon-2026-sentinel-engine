"""i18n tests: fallback, completeness, and storage hygiene."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

I18N_DIR = Path(__file__).parent.parent / "app" / "ui" / "i18n"


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


def test_frontend_served_at_root() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "sentinel" in response.text.lower()


def test_only_theme_key_in_browser_storage() -> None:
    source = (Path(__file__).parent.parent / "app" / "ui" / "static" / "app.js").read_text(
        encoding="utf-8"
    )
    assert "sentinel-theme" in source
    assert "localStorage.setItem" in source
    assert source.count("localStorage.setItem") == 1
    assert "innerHTML" not in source


def test_i18n_files_are_valid_json() -> None:
    for path in sorted(I18N_DIR.glob("*.json")):
        json.loads(path.read_text(encoding="utf-8"))
