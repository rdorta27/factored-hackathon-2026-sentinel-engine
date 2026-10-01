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
    # Dataset fraud score; read by the policy engine only, never shown or sent to the model.
    fraud_score: float | None = None


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
            # USD product of the Mexican customer. The dataset holds Mexican accounts in USD only;
            # the MXN rows above are an invented local account with no threshold (decision 6).
            GoldRow("TXN-1101", "CUST-0001", "8200.00", "USD", "Electronica Norte", "2026-06-13", "Approved", as_of),
            GoldRow("TXN-1102", "CUST-0001", "310.00", "USD", "Viajes Pacifico", "2026-06-14", "Approved", as_of, fraud_score=29.6),
            GoldRow("TXN-2001", "CUST-0002", "250000.00", "COP", "Almacen Andino", "2026-06-11", "Approved", as_of),
            GoldRow("TXN-2002", "CUST-0002", "32000000.00", "COP", "Motores Bogota", "2026-06-12", "Approved", as_of),
            GoldRow("TXN-2003", "CUST-0002", "180000.00", "COP", "Farmacia Central", "2026-06-13", "Approved", as_of, fraud_score=29.4),
            GoldRow("TXN-2101", "CUST-0002", "7900.00", "USD", "Tech Import", "2026-06-14", "Approved", as_of),
            GoldRow("TXN-2102", "CUST-0002", "95.00", "USD", "Streaming Plus", "2026-06-15", "Approved", as_of, fraud_score=29.1),
            GoldRow("TXN-3001", "CUST-0003", "45000.00", "ARS", "Tienda del Sur", "2026-06-09", "Approved", as_of),
            GoldRow("TXN-3002", "CUST-0003", "2900000.00", "ARS", "Autos Rosario", "2026-06-10", "Approved", as_of),
            GoldRow("TXN-3003", "CUST-0003", "38000.00", "ARS", "Libreria Austral", "2026-06-11", "Approved", as_of, fraud_score=29.3),
            GoldRow("TXN-3101", "CUST-0003", "7800.00", "USD", "Hotel Patagonia", "2026-06-12", "Approved", as_of),
            GoldRow("TXN-3102", "CUST-0003", "120.00", "USD", "Musica Online", "2026-06-13", "Approved", as_of, fraud_score=29.2),
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
        fraud_score=row.fraud_score,
        is_disputed=row.prior_dispute,
    )
