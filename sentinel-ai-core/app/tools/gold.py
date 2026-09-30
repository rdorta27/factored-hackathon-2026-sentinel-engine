from dataclasses import dataclass
from typing import Protocol

from app.orchestrator.types import Candidate, TransactionStatus


@dataclass(frozen=True)
class GoldRow:
    reference: str
    customer_id: str
    amount: str
    currency: str
    merchant: str
    date: str
    status: str
    as_of: str
    refunded: bool = False
    prior_dispute: bool = False


class GoldTransactions(Protocol):
    def get(self, reference: str, customer_id: str) -> GoldRow | None: ...

    def list_for_customer(self, customer_id: str) -> list[GoldRow]: ...


class MockGoldStore:
    def __init__(self, as_of: str) -> None:
        rows = [
            GoldRow("TXN-1001", "CUST-0001", "1000.00", "MXN", "ACME Store", "2026-06-10", "Approved", as_of),
            GoldRow("TXN-1002", "CUST-0001", "2500.00", "MXN", "ACME Store", "2026-01-15", "Approved", as_of),
            GoldRow("TXN-1003", "CUST-0001", "500.00", "MXN", "ACME Store", "2026-06-05", "Refunded", as_of, refunded=True),
            GoldRow("TXN-1004", "CUST-0001", "750.00", "MXN", "ACME Store", "2026-06-08", "Approved", as_of, prior_dispute=True),
            GoldRow("TXN-1006", "CUST-0001", "320.00", "MXN", "Cafe Central", "2026-06-12", "Approved", as_of),
            GoldRow("TXN-2001", "CUST-0002", "250000.00", "COP", "Almacen Andino", "2026-06-11", "Approved", as_of),
            GoldRow("TXN-3001", "CUST-0003", "45000.00", "ARS", "Tienda del Sur", "2026-06-09", "Approved", as_of),
            GoldRow("TXN-9001", "CUST-9999", "100.00", "MXN", "ACME Store", "2026-06-10", "Approved", as_of),
        ]
        self._rows = {(row.reference, row.customer_id): row for row in rows}

    def get(self, reference: str, customer_id: str) -> GoldRow | None:
        return self._rows.get((reference, customer_id))

    def list_for_customer(self, customer_id: str) -> list[GoldRow]:
        rows = [row for row in self._rows.values() if row.customer_id == customer_id]
        return sorted(rows, key=lambda row: row.date, reverse=True)


def to_candidate(row: GoldRow) -> Candidate:
    status = row.status
    if row.refunded or status == "Refunded":
        mapped = TransactionStatus.REVERSED
    else:
        mapped = TransactionStatus(status)
    return Candidate(
        candidate_id=row.reference,
        status=mapped,
        amount=row.amount,
        currency=row.currency,
        merchant=row.merchant,
        date=row.date,
        as_of=row.as_of,
        is_disputed=row.prior_dispute,
    )
