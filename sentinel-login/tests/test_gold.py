"""Gold seam tests: matrix rows, freshness, per-customer isolation."""

from app.gold.store import MockGoldStore

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
