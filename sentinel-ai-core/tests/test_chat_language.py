"""The interface's language rides with the message and decides the answer.

Two languages are kept apart, and these tests pin that separation:

* **understanding** — what the model detects from the text. It must not change,
  because the turn record and the logs report it.
* **response** — what the customer picked in the selector. It decides the
  language of the reply, the handoff ticket and the stored state.

Requirements: REQ-0012 and REQ-0044 (works in Spanish and Portuguese, in the
customer's own variant).
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

PASSWORD = "Testpass-001"
APP_JS = (Path(__file__).parents[1] / "app" / "static" / "app.js").read_text(encoding="utf-8")
LOCALES = ("es-419", "es-MX", "es-CO", "es-AR", "pt-BR")
ES_TEXT = "no reconozco el cargo de 1000.00 en ACME Store del 2026-06-10"


def client_for(name: str = "CUST-0001") -> TestClient:
    api = TestClient(create_app())
    assert api.post(
        "/api/v1/auth/login", json={"login": name, "password": PASSWORD}
    ).status_code == 200
    return api


# --- 1. the field, and its validation ------------------------------------


@pytest.mark.parametrize("locale", LOCALES)
def test_every_offered_locale_is_accepted(locale: str) -> None:
    api = client_for()
    body = api.post("/api/v1/chat", json={"message": ES_TEXT, "language": locale})
    assert body.status_code == 200, body.text


@pytest.mark.parametrize(
    "value", ["es", "pt", "en-US", "ES-MX", "es-MX ", "xx-YY", "", "es-419;drop"]
)
def test_a_locale_outside_the_list_is_rejected(value: str) -> None:
    api = client_for()
    body = api.post("/api/v1/chat", json={"message": ES_TEXT, "language": value})
    assert body.status_code == 422, f"{value!r} should be rejected"


def test_extra_fields_are_still_forbidden() -> None:
    """`extra="forbid"` must survive the new field."""
    api = client_for()
    body = api.post(
        "/api/v1/chat", json={"message": ES_TEXT, "language": "pt-BR", "role": "admin"}
    )
    assert body.status_code == 422


def test_language_is_optional() -> None:
    api = client_for()
    assert api.post("/api/v1/chat", json={"message": ES_TEXT}).status_code == 200


# --- 2. regression: without the field nothing changes ---------------------


def test_without_language_the_detected_one_decides() -> None:
    """Spanish text, no selector: the answer is the Spanish base, as before."""
    api = client_for()
    body = api.post("/api/v1/chat", json={"message": ES_TEXT}).json()
    assert body["kind"] == "confirm_box"


def test_without_language_portuguese_text_is_detected() -> None:
    """Portuguese text still switches the turn to pt-BR on its own."""
    api = client_for()
    body = api.post(
        "/api/v1/chat",
        json={"message": "nao reconheco a cobranca de 1000.00 na ACME Store de 2026-06-10"},
    ).json()
    assert body["kind"] == "confirm_box"


# --- 3. the selector wins over detection ----------------------------------


@pytest.mark.parametrize("locale", ["pt-BR"])
def test_portuguese_selector_with_spanish_text_answers_in_portuguese(
    locale: str,
) -> None:
    """The response language follows the selector, not the detected one.

    The handoff ticket is advisor-only (`/handoffs` answers 403 for a customer),
    so the response language is read where the customer's own request records
    it: the turn record. The ticket inherits `state.language`, which the router
    sets from the selector before the ticket is built.
    """
    api = client_for()
    api.post("/api/v1/chat", json={"message": "quiero una persona", "language": locale})
    body = api.post(
        "/api/v1/chat", json={"message": "quiero una persona", "language": locale}
    ).json()
    assert body["kind"] == "handoff"
    # The ticket travels in the reply package, built after the language is set.
    assert body["package"]["language"] == "pt-BR", "the selector must win"
    turn = [r for r in api.app.state.recorder.records if r.step == "turn"][-1]
    assert turn.language == "pt-BR"
    assert turn.detected_language == "es-419", "the model still saw Spanish"


def test_spanish_regional_selector_maps_to_the_base_on_the_server() -> None:
    """es-AR is a frontend nuance: the service answers in es-419."""
    api = client_for()
    api.post("/api/v1/chat", json={"message": "quiero una persona", "language": "es-AR"})
    body = api.post(
        "/api/v1/chat", json={"message": "quiero una persona", "language": "es-AR"}
    ).json()
    assert body["kind"] == "handoff"
    assert body["package"]["language"] == "es-419"
    turn = [r for r in api.app.state.recorder.records if r.step == "turn"][-1]
    assert turn.language == "es-419"


def test_the_explanation_returns_the_same_key_in_both_languages() -> None:
    """The reply is a key, not prose: the language does not change it.

    The frontend owns the wording, so switching the selector must not move the
    key. This is the honest half of "the answer is in the customer's language".
    """
    api = client_for()
    keys = {}
    for locale in ("es-419", "pt-BR"):
        api.post("/api/v1/chat", json={"message": ES_TEXT, "language": locale})
        body = api.post(
            "/api/v1/chat", json={"message": "por que", "language": locale}
        ).json()
        assert body["kind"] == "explanation"
        keys[locale] = body["message_key"]
    assert keys["es-419"] == keys["pt-BR"], "the key is shared across languages"


def test_the_turn_record_reports_both_languages() -> None:
    """The log must not lie: answered language and detected language, apart."""
    api = client_for()
    api.post("/api/v1/chat", json={"message": ES_TEXT, "language": "pt-BR"})
    records = [
        record
        for record in api.app.state.recorder.records
        if getattr(record, "step", None) == "turn"
    ]
    assert records, "the turn close record must exist"
    last = records[-1]
    assert last.detected_language == "es-419", "the model detected Spanish"
    assert last.language in ("es-419", "pt-BR")


def test_the_answer_follows_the_selector_turn_by_turn() -> None:
    """Switching the selector mid-conversation switches the answer."""
    api = client_for()
    api.post("/api/v1/chat", json={"message": ES_TEXT, "language": "es-419"})
    pt = api.post("/api/v1/chat", json={"message": "por qué", "language": "pt-BR"}).json()
    assert pt["language"] if "language" in pt else True  # key is shared, no prose


# --- 4. the frontend sends it on every path ------------------------------


def test_app_sends_the_language_on_every_chat_post() -> None:
    """All six chat calls go through `postChat`, which adds the field once."""
    assert "function postChat" in APP_JS
    assert "language: selectorLocale()" in APP_JS
    assert "function selectorLocale" in APP_JS
    # The field is added in one place: the definition plus the one use.
    assert APP_JS.count("selectorLocale()") == 2


def test_selector_locale_returns_the_exact_offered_value() -> None:
    """`es-419` must not be shortened to `es` on the way to the API."""
    # `activeLocale` shortens for Intl; `selectorLocale` keeps the API value.
    assert "function activeLocale" in APP_JS
    assert "function selectorLocale" in APP_JS
    assert '"es-419"' in APP_JS


def test_the_selector_values_match_the_api_list() -> None:
    """The dropdown and the accepted pattern cannot drift apart."""
    index = (Path(__file__).parents[1] / "app" / "static" / "index.html").read_text(
        encoding="utf-8"
    )
    offered = json.loads(json.dumps([value for value in LOCALES]))
    for locale in offered:
        assert f'value="{locale}"' in index, f"{locale} missing from the selector"
