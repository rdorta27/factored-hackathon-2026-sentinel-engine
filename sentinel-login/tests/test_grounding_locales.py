"""Bilingual grounding: Spanish and Portuguese messages about the same charge."""

from app.chat.grounding import extract_facts, ground
from app.gold.store import GoldRow

YEAR = 2026
MERCHANTS = ["ACME Store", "Cafe Central"]

ROWS = [
    GoldRow("TXN-1001", "CUST-0001", "1000.00", "MXN", "ACME Store", "2026-06-10", "Approved", as_of="2026-06-17"),
    GoldRow("TXN-1002", "CUST-0001", "1000.00", "MXN", "ACME Store", "2026-05-20", "Approved", as_of="2026-06-17"),
    GoldRow("TXN-2001", "CUST-0002", "1000.00", "BRL", "Loja ACME", "2026-06-10", "Approved", as_of="2026-06-17"),
]

SPANISH = "disputo el cargo de $1.000,00 en ACME Store del 10 de junio"
PORTUGUESE = "quero disputar a cobrança de R$ 1.000,00 na Loja ACME do dia 10 de junho"


def test_spanish_message_grounds_to_the_charge() -> None:
    facts = extract_facts(SPANISH, YEAR, MERCHANTS)
    assert facts.amount == "1000.00"
    assert facts.date_iso == "2026-06-10"
    result = ground(facts, ROWS[:2], YEAR)
    assert result.outcome == "matched"
    assert result.match is not None and result.match.reference == "TXN-1001"


def test_portuguese_message_grounds_to_the_charge() -> None:
    facts = extract_facts(PORTUGUESE, YEAR, MERCHANTS + ["Loja ACME"])
    assert facts.amount == "1000.00"
    assert facts.date_iso == "2026-06-10"
    result = ground(facts, [ROWS[2]], YEAR)
    assert result.outcome == "matched"
    assert result.match is not None and result.match.reference == "TXN-2001"


def test_both_languages_reach_the_same_verdict() -> None:
    # Same charge, same facts: each language matches its own country's row.
    spanish = ground(extract_facts(SPANISH, YEAR, MERCHANTS), ROWS[:2], YEAR)
    portuguese = ground(
        extract_facts(PORTUGUESE, YEAR, MERCHANTS + ["Loja ACME"]), [ROWS[2]], YEAR
    )
    assert spanish.outcome == portuguese.outcome == "matched"
    assert spanish.match is not None and portuguese.match is not None
    assert spanish.match.date == portuguese.match.date
    assert spanish.match.amount == portuguese.match.amount


def test_portuguese_amount_with_dot_thousands() -> None:
    facts = extract_facts("cobrança de R$ 1.000,00 na Loja ACME", YEAR, ["Loja ACME"])
    assert facts.amount == "1000.00"


def test_portuguese_ambiguous_message_clarifies() -> None:
    # Two charges at the same merchant, no date stated: the system must ask.
    same_merchant = [
        GoldRow("TXN-2001", "CUST-0002", "1000.00", "BRL", "Loja ACME", "2026-06-10", "Approved"),
        GoldRow("TXN-2002", "CUST-0002", "1000.00", "BRL", "Loja ACME", "2026-05-10", "Approved"),
    ]
    facts = extract_facts("não reconheço a cobrança de R$ 1.000,00 na Loja ACME", YEAR, ["Loja ACME"])
    result = ground(facts, same_merchant, YEAR)
    assert result.outcome == "ambiguous"
    assert {r.reference for r in result.candidates} == {"TXN-2001", "TXN-2002"}
    assert result.match is None


def test_portuguese_months_not_confused_with_spanish() -> None:
    janeiro = extract_facts("cobrança de R$ 500,00 em 15 de janeiro", YEAR, [])
    junho = extract_facts("cobrança de R$ 500,00 em 15 de junho", YEAR, [])
    assert janeiro.date_iso == "2026-01-15"
    assert junho.date_iso == "2026-06-15"


def test_portuguese_without_ambiguity_marker_is_exact() -> None:
    facts = extract_facts(
        "a cobrança de R$ 1.000,00 na Loja ACME do dia 10 de junho", YEAR, ["Loja ACME"]
    )
    assert facts.date_iso == "2026-06-10"
    assert facts.amount == "1000.00"
