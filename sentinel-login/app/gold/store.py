"""Gold read seam. Phase 2 swaps the mock for DuckDB or Delta Lake adapters."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GoldRow:
    """One denormalized transaction row with eligibility flags and freshness."""

    reference: str
    customer_id: str
    amount: str
    currency: str
    merchant: str
    date: str
    status: str
    refunded: bool = False
    prior_dispute: bool = False
    as_of: str = ""


class GoldTransactions(Protocol):
    """Read-only eligibility rows, always filtered by session customer."""

    def get(self, reference: str, customer_id: str) -> GoldRow | None:
        ...


class MockGoldStore:
    """Invented rows for the demo matrix. Labeled mock, never dataset data."""

    def __init__(self, as_of: str) -> None:
        rows = [
            GoldRow("TXN-1001", "CUST-0001", "1000.00", "MXN", "ACME Store",
                    "2026-06-10", "Approved", as_of=as_of),
            GoldRow("TXN-1002", "CUST-0001", "2500.00", "MXN", "ACME Store",
                    "2026-01-15", "Approved", as_of=as_of),
            GoldRow("TXN-1003", "CUST-0001", "500.00", "MXN", "ACME Store",
                    "2026-06-05", "Refunded", refunded=True, as_of=as_of),
            GoldRow("TXN-1004", "CUST-0001", "750.00", "MXN", "ACME Store",
                    "2026-06-08", "Approved", prior_dispute=True, as_of=as_of),
            GoldRow("TXN-9001", "CUST-9999", "100.00", "MXN", "ACME Store",
                    "2026-06-10", "Approved", as_of=as_of),
        ]
        self._rows = {(r.reference, r.customer_id): r for r in rows}

    def get(self, reference: str, customer_id: str) -> GoldRow | None:
        return self._rows.get((reference, customer_id))
