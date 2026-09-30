"""Gold seam tests: matrix rows, freshness, per-customer isolation."""

from app.gold.store import MockGoldStore, profile_for

AS_OF = "2026-06-20"


def test_eligible_row_reads_with_as_of() -> None:
    row = MockGoldStore(AS_OF).get("TXN-1001", "CUST-0001")
    assert row is not None
    assert row.amount == "1000.00"
    assert row.as_of == AS_OF


def test_unknown_reference_reads_absent() -> None:
    assert MockGoldStore(AS_OF).get("TXN-0000", "CUST-0001") is None


def test_cross_customer_reference_reads_absent() -> None:
    assert MockGoldStore(AS_OF).get("TXN-9001", "CUST-0001") is None
    assert MockGoldStore(AS_OF).get("TXN-1001", "CUST-9999") is None


def test_matrix_flags_present() -> None:
    store = MockGoldStore(AS_OF)
    stale = store.get("TXN-1002", "CUST-0001")
    assert stale is not None and stale.date == "2026-01-15"
    refunded = store.get("TXN-1003", "CUST-0001")
    assert refunded is not None and refunded.refunded
    disputed = store.get("TXN-1004", "CUST-0001")
    assert disputed is not None and disputed.prior_dispute


def test_each_country_reads_its_own_currency() -> None:
    store = MockGoldStore(AS_OF)
    assert {r.currency for r in store.list_for_customer("CUST-0001")} == {"MXN"}
    assert {r.currency for r in store.list_for_customer("CUST-0002")} == {"COP"}
    assert {r.currency for r in store.list_for_customer("CUST-0003")} == {"ARS"}


def test_listing_is_ordered_and_isolated() -> None:
    store = MockGoldStore(AS_OF)
    rows = store.list_for_customer("CUST-0001")
    assert rows == sorted(rows, key=lambda r: r.date, reverse=True)
    assert all(row.customer_id == "CUST-0001" for row in rows)
    assert all(r.reference != "TXN-9001" for r in rows)


def test_profile_for_known_and_unknown_customers() -> None:
    assert profile_for("CUST-0002").default_locale == "es-CO"
    assert profile_for("ADV-0001").country == "MX"
    assert profile_for("WHO-0001").customer_id == "WHO-0001"
