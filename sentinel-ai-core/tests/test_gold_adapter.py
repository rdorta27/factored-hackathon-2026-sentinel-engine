from app.orchestrator.types import TransactionStatus
from app.tools.bound import SessionBoundLookup
from app.tools.fake import InMemoryTools
from app.tools.gold import MockGoldStore

AS_OF = "2026-06-17"


def test_lookup_is_bound_and_hides_foreign_rows() -> None:
    gold = MockGoldStore(as_of=AS_OF)
    bound = SessionBoundLookup(gold, "CUST-0001", InMemoryTools())
    rows = bound.lookup_transactions()
    ids = {row.candidate_id for row in rows}
    assert "TXN-9001" not in ids
    assert "TXN-2001" not in ids
    assert all(row.as_of == AS_OF for row in rows)


def test_refunded_maps_to_reversed() -> None:
    gold = MockGoldStore(as_of=AS_OF)
    bound = SessionBoundLookup(gold, "CUST-0001", InMemoryTools())
    refunded = next(row for row in bound.lookup_transactions() if row.candidate_id == "TXN-1003")
    assert refunded.status is TransactionStatus.REVERSED


def test_lookup_transactions_takes_no_customer_argument() -> None:
    bound = SessionBoundLookup(MockGoldStore(as_of=AS_OF), "CUST-0001", InMemoryTools())
    assert bound.lookup_transactions.__code__.co_argcount == 1
