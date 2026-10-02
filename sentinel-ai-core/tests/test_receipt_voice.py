"""The receipt speaks in the bank's voice, not the customer's words.

The customer's bubble keeps whatever they typed. The card below it must state
the charge itself, so the two never read as an echo.
"""

import json
import re
from pathlib import Path

import pytest

APP_JS = (Path(__file__).parents[1] / "app" / "static" / "app.js").read_text(encoding="utf-8")
I18N_DIR = Path(__file__).parents[1] / "app" / "static" / "i18n"
LOCALES = ("es-419", "es-MX", "es-CO", "es-AR", "pt-BR")


def merged_strings(locale: str) -> dict:
    base = json.loads((I18N_DIR / "es-419.json").read_text(encoding="utf-8"))
    override = json.loads((I18N_DIR / f"{locale}.json").read_text(encoding="utf-8"))
    return {**base, **override}


def receipt_block() -> str:
    """The `case_confirmation` branch of the renderer."""
    start = APP_JS.index('body.kind === "case_confirmation"')
    end = APP_JS.index('body.kind === "explanation"')
    return APP_JS[start:end]


# --- the card does not echo the customer ---------------------------------


def test_card_does_not_use_the_customer_phrase() -> None:
    """`humanStatement` is the customer's voice: it must not appear in the card."""
    block = receipt_block()
    assert "humanStatement" not in block, "the receipt echoes the customer's sentence"
    assert "referToCharge" not in block, "the receipt uses the customer's wording"
    assert "receiptCharge" in block, "the receipt states the charge in the bank's voice"


def test_customer_bubble_keeps_its_own_wording() -> None:
    """Only the card changed: the bubble the customer sees is untouched."""
    assert 't("referToCharge")' in APP_JS
    assert "function humanStatement" in APP_JS
    # The bubble path still uses it.
    assert "addBubble(humanStatement(" in APP_JS


# --- the new line is translated in every locale --------------------------


@pytest.mark.parametrize("locale", LOCALES)
def test_receipt_charge_exists_in_every_locale(locale: str) -> None:
    strings = merged_strings(locale)
    assert "receiptCharge" in strings, f"{locale} missing receiptCharge"


@pytest.mark.parametrize("locale", LOCALES)
def test_receipt_charge_has_the_three_placeholders(locale: str) -> None:
    template = merged_strings(locale)["receiptCharge"]
    for placeholder in ("{merchant}", "{amount}", "{date}"):
        assert placeholder in template, f"{locale}: {placeholder} missing"


def test_receipt_charge_reads_as_the_bank_not_the_customer() -> None:
    """It states a fact; it does not say "I mean the charge"."""
    for locale in LOCALES:
        template = merged_strings(locale)["receiptCharge"].lower()
        assert not template.startswith("me refiro"), locale
        assert not template.startswith("refiro-me"), locale
        assert not template.startswith("me refiero"), locale


def test_regional_wording_differs_where_the_word_differs() -> None:
    """Argentina says "consumo", Brazil says "cobrança"."""
    assert merged_strings("es-AR")["receiptCharge"].startswith("Consumo")
    assert merged_strings("pt-BR")["receiptCharge"].startswith("Cobrança")
    assert merged_strings("es-419")["receiptCharge"].startswith("Cargo")


# --- same formatting as everywhere else ----------------------------------


def test_receipt_uses_the_shared_formatters() -> None:
    """Amount and date go through the same locale-aware helpers."""
    start = APP_JS.index("function receiptCharge")
    end = APP_JS.index("\n}", start)
    body = APP_JS[start:end]
    assert "formatAmount(" in body
    assert "formatDate(" in body
    assert "fill(" in body


def test_receipt_shows_the_transaction_currency() -> None:
    """The amount comes from the charge, currency included."""
    block = receipt_block()
    assert "body.transaction" in block
    helper = APP_JS[APP_JS.index("function receiptCharge") :]
    assert "tx.currency" in helper.split("\n}")[0]
