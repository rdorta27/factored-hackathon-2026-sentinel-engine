"""Locality guarantees: raw values over the wire, one formatter in the UI.

These tests read the frontend source, because the guarantees are about which
code path renders what: a second formatter or a translated datum is the bug.
"""

import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app

STATIC_DIR = Path(__file__).parent.parent / "app" / "ui" / "static"
APP_JS = (STATIC_DIR / "app.js").read_text(encoding="utf-8")
INDEX = (STATIC_DIR / "index.html").read_text(encoding="utf-8")


def customer_client() -> TestClient:
    client = TestClient(create_app())
    client.post(
        "/auth/login", json={"customer_id": "CUST-0001", "password": "Testpass-001"}
    )
    return client


def test_only_one_amount_formatter_and_one_date_formatter() -> None:
    assert APP_JS.count("Intl.NumberFormat") == 1
    assert APP_JS.count("Intl.DateTimeFormat") == 1
    assert APP_JS.count("function formatAmount") == 1
    assert APP_JS.count("function formatDate") == 1


def test_currency_code_is_always_shown() -> None:
    assert 'CURRENCY_DISPLAY = "code"' in APP_JS
    assert "currencyDisplay: CURRENCY_DISPLAY" in APP_JS


def test_every_amount_site_uses_the_shared_formatter() -> None:
    # The panel, the chips and the card all go through formatAmount.
    assert APP_JS.count("formatAmount(") >= 4
    # No template may interpolate a raw amount next to a raw currency.
    assert not re.search(r"\$\{[^}]*\.amount\}\s*\$\{[^}]*\.currency", APP_JS)


def test_dates_are_never_rendered_raw() -> None:
    assert APP_JS.count("formatDate(") >= 4
    # Every `.date` interpolation must be wrapped in the formatter.
    raw = re.findall(r"\$\{[^}]*\.date\}", APP_JS)
    assert raw == [], f"dates rendered without formatting: {raw}"


def test_merchant_never_passes_through_i18n() -> None:
    assert "function merchantLabel" in APP_JS
    # The merchant is always rendered through merchantLabel, never t(...).
    assert not re.search(r"t\(\s*[a-zA-Z_]*merchant[a-zA-Z_]*\s*\)", APP_JS)
    assert APP_JS.count("merchantLabel(") >= 2


def test_ui_never_renders_internal_transaction_ids() -> None:
    # The candidate reference travels in the request body, never in the text.
    assert "selected_reference" in APP_JS
    assert "candidate.reference}" not in APP_JS
    assert "tx.reference" not in APP_JS


def test_confirmation_payload_is_locale_neutral() -> None:
    client = customer_client()
    body = client.post(
        "/api/v1/disputes/create",
        json={"transaction_ref": "TXN-1001"},
        headers={"Idempotency-Key": "locale-1"},
    ).json()
    assert body["display"] == {
        "amount": "1000.00",
        "currency": "MXN",
        "merchant": "ACME Store",
        "referenceDate": "2026-06-17",
        "slaDate": "2026-06-19",
    }
    # Keys, not prose: nothing the client must translate is pre-written.
    assert set(body["messages"]) == {"nextStep", "rule", "queue", "noFunds"}
    for value in body["messages"].values():
        assert re.fullmatch(r"[A-Za-z]+", value), value


def test_no_server_authored_english_in_replies() -> None:
    """Any sentence-like string in a reply would arrive untranslated."""
    client = customer_client()
    chat = client.post(
        "/chat", json={"message": "help with charge"}
    ).json()
    assert "message_key" in chat
    assert "text" not in chat
    handoff = client.post("/chat", json={"message": "stolen card fraud"}).json()
    assert "reason_key" in handoff
    assert "reason" not in handoff
    assert "advisor_received" not in handoff


def test_chips_show_readable_text_not_the_id() -> None:
    client = customer_client()
    body = client.post(
        "/chat",
        json={"message": "I dispute the charge of 1000.00 at ACME Store on 2026-09-20"},
    ).json()
    assert body["candidates"]
    for candidate in body["candidates"]:
        assert candidate["merchant"] and candidate["amount"] and candidate["currency"]
        # The reference is data for the client, not a label the user reads.
        assert candidate["reference"].startswith("TXN-")


def test_index_loads_assets_under_the_ui_prefix() -> None:
    assert 'src="/ui/app.js"' in INDEX
    assert 'href="/ui/styles.css"' in INDEX
