"""Grounding tests: exact match, ambiguity, no match, contradiction."""

from app.chat.grounding import (
    StatedFacts,
    extract_facts,
    ground,
    normalize_amount,
    normalize_text,
)
from app.gold.store import GoldRow

YEAR = 2026
MERCHANTS = ["ACME Store", "Cafe Central"]


def row(reference: str, amount: str, merchant: str, day: str) -> GoldRow:
    return GoldRow(reference, "CUST-0001", amount, "MXN", merchant, day, "Approved", as_of="2026-06-17")


ROWS = [
    row("TXN-1001", "1000.00", "ACME Store", "2026-06-10"),
    row("TXN-1002", "1000.00", "ACME Store", "2026-05-20"),
    row("TXN-1003", "250.50", "Cafe Central", "2026-06-05"),
]


def test_exact_match_selects_one() -> None:
    facts = StatedFacts("2026-06-10", "1000.00", "ACME Store")
    result = ground(facts, ROWS, YEAR)
    assert result.outcome == "matched"
    assert result.match is not None and result.match.reference == "TXN-1001"


def test_same_amount_two_dates_is_ambiguous() -> None:
    facts = StatedFacts(None, "1000.00", "ACME Store")
    result = ground(facts, ROWS, YEAR)
    assert result.outcome == "ambiguous"
    assert {r.reference for r in result.candidates} == {"TXN-1001", "TXN-1002"}
    assert result.match is None


def test_wrong_date_matches_nothing() -> None:
    facts = StatedFacts("2026-09-20", "1000.00", "ACME Store")
    result = ground(facts, ROWS, YEAR)
    assert result.outcome == "none"


def test_contradictory_merchant_matches_nothing() -> None:
    facts = StatedFacts("2026-06-10", "1000.00", "Other Shop")
    result = ground(facts, ROWS, YEAR)
    assert result.outcome == "none"


def test_nothing_stated_is_none() -> None:
    assert ground(StatedFacts(None, None, None), ROWS, YEAR).outcome == "none"


def test_amount_and_merchant_only() -> None:
    facts = StatedFacts(None, "250.50", "Cafe Central")
    result = ground(facts, ROWS, YEAR)
    assert result.outcome == "matched"
    assert result.match is not None and result.match.reference == "TXN-1003"


def test_normalize_amount_handles_both_conventions() -> None:
    assert normalize_amount("1.000,00") == "1000.00"
    assert normalize_amount("1,000.00") == "1000.00"
    assert normalize_amount("1000") == "1000.00"
    assert normalize_amount("250,50") == "250.50"


def test_normalize_text_strips_accents_and_case() -> None:
    assert normalize_text("  Café   CENTRAL ") == "cafe central"


def test_extract_facts_reads_message() -> None:
    facts = extract_facts("cargo de $1,000.00 en ACME Store del 10 de junio", YEAR, MERCHANTS)
    assert facts.amount == "1000.00"
    assert facts.merchant == "ACME Store"
    assert facts.date_iso == "2026-06-10"
