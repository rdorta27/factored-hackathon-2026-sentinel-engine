"""White label: the bank name and the accent come from the environment (change bank-ui)."""

import logging

import pytest
from fastapi.testclient import TestClient

from app.branding import DEFAULT_ACCENT, DEFAULT_NAME, accent_passes, contrast, load_brand
from app.main import create_app


def _client(monkeypatch: pytest.MonkeyPatch, name: str | None, accent: str | None) -> TestClient:
    for key, value in (("SENTINEL_BRAND_NAME", name), ("SENTINEL_BRAND_ACCENT", accent)):
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    return TestClient(create_app())


def test_defaults_are_sentinel_and_the_bank_blue(monkeypatch: pytest.MonkeyPatch) -> None:
    api = _client(monkeypatch, None, None)
    assert api.get("/ui/brand.json").json() == {"name": DEFAULT_NAME, "accent": DEFAULT_ACCENT, "customized": False}
    assert "--accent" not in api.get("/ui/brand.css").text


def test_another_bank_gets_its_name_and_accent(monkeypatch: pytest.MonkeyPatch) -> None:
    api = _client(monkeypatch, "Banco Aurora", "#0b6e4f")
    assert api.get("/ui/brand.json").json() == {"name": "Banco Aurora", "accent": "#0b6e4f", "customized": True}
    css = api.get("/ui/brand.css")
    assert css.headers["content-type"].startswith("text/css")
    assert "--accent: #0b6e4f" in css.text
    assert '[data-theme="dark"]' in css.text


def test_accent_that_fails_contrast_falls_back_and_is_logged(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="app.branding"):
        api = _client(monkeypatch, "Banco Claro", "#ffd54a")
    assert api.get("/ui/brand.json").json()["accent"] == DEFAULT_ACCENT
    assert "contrast" in caplog.text
    assert api.get("/ui/brand.json").json()["name"] == "Banco Claro"


def test_accent_that_is_not_a_color_falls_back(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.WARNING, logger="app.branding"):
        api = _client(monkeypatch, None, "red; } body { display:none")
    assert api.get("/ui/brand.json").json()["accent"] == DEFAULT_ACCENT
    assert "display" not in api.get("/ui/brand.css").text


def test_dark_text_variant_reads_on_the_dark_card(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_BRAND_ACCENT", "#7a1fa2")
    brand = load_brand()
    assert accent_passes(brand.accent)
    assert contrast(brand.accent_text_dark, "#162033") >= 4.5


def test_name_is_trimmed_and_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_BRAND_NAME", "  " + "B" * 80 + "  ")
    assert len(load_brand().name) == 40


def test_tints_follow_the_accent_and_read_at_aa(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.branding import tints

    for accent in ("#0b6e4f", "#7a1fa2", "#b3261e", DEFAULT_ACCENT):
        for theme, tone in tints(accent).items():
            assert contrast(tone["text"], tone["fill"]) >= 4.5, (accent, theme)
    api = _client(monkeypatch, None, "#0b6e4f")
    css = api.get("/ui/brand.css").text
    assert "--pill-info-bg" in css and "--callout-bg" in css
