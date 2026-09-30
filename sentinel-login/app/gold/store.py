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


@dataclass(frozen=True)
class CustomerProfile:
    """Demo customer: country drives the default language, not the currency."""

    customer_id: str
    country: str
    default_locale: str
    display_name: str


class GoldTransactions(Protocol):
    """Read-only eligibility rows, always filtered by session customer."""

    def get(self, reference: str, customer_id: str) -> GoldRow | None:
        ...

    def list_for_customer(self, customer_id: str) -> list[GoldRow]:
        ...


# Invented demo customers. Currencies come from the country; the reference date
# for the seeded rows is the dataset end, so the window behaves like a demo.
CUSTOMER_PROFILES = {
    "CUST-0001": CustomerProfile("CUST-0001", "MX", "es-MX", "Ana M. R."),
    "CUST-0002": CustomerProfile("CUST-0002", "CO", "es-CO", "Carla G. P."),
    "CUST-0003": CustomerProfile("CUST-0003", "AR", "es-AR", "Diego S. L."),
}

_STAFF_PROFILES = {
    "ADV-0001": CustomerProfile("ADV-0001", "MX", "es-MX", "Asesor Uno"),
    "ADM-0001": CustomerProfile("ADM-0001", "MX", "es-MX", "Administrador"),
}


def profile_for(customer_id: str) -> CustomerProfile:
    """Profile for a session customer; staff fall back to a neutral demo one."""
    return CUSTOMER_PROFILES.get(customer_id) or _STAFF_PROFILES.get(
        customer_id, CustomerProfile(customer_id, "MX", "es-MX", "Cliente Demo")
    )


class MockGoldStore:
    """Invented rows for the demo matrix. Labeled mock, never dataset data."""

    def __init__(self, as_of: str) -> None:
        rows = [
            # Mexico, MXN
            GoldRow("TXN-1001", "CUST-0001", "1000.00", "MXN", "ACME Store",
                    "2026-06-10", "Approved", as_of=as_of),
            GoldRow("TXN-1002", "CUST-0001", "2500.00", "MXN", "ACME Store",
                    "2026-01-15", "Approved", as_of=as_of),
            GoldRow("TXN-1003", "CUST-0001", "500.00", "MXN", "ACME Store",
                    "2026-06-05", "Refunded", refunded=True, as_of=as_of),
            GoldRow("TXN-1004", "CUST-0001", "750.00", "MXN", "ACME Store",
                    "2026-06-08", "Approved", prior_dispute=True, as_of=as_of),
            GoldRow("TXN-1005", "CUST-0001", "1000.00", "MXN", "ACME Store",
                    "2026-05-20", "Approved", as_of=as_of),
            GoldRow("TXN-1006", "CUST-0001", "320.00", "MXN", "Cafe Central",
                    "2026-06-12", "Approved", as_of=as_of),
            # Colombia, COP
            GoldRow("TXN-2001", "CUST-0002", "250000.00", "COP", "Almacen Andino",
                    "2026-06-11", "Approved", as_of=as_of),
            GoldRow("TXN-2002", "CUST-0002", "89000.00", "COP", "Cafe Bogota",
                    "2026-06-14", "Approved", as_of=as_of),
            # Argentina, ARS
            GoldRow("TXN-3001", "CUST-0003", "45000.00", "ARS", "Tienda del Sur",
                    "2026-06-09", "Approved", as_of=as_of),
            GoldRow("TXN-3002", "CUST-0003", "12500.00", "ARS", "Panaderia Norte",
                    "2026-06-15", "Approved", as_of=as_of),
            # Another customer's row, used to prove isolation.
            GoldRow("TXN-9001", "CUST-9999", "100.00", "MXN", "ACME Store",
                    "2026-06-10", "Approved", as_of=as_of),
        ]
        self._rows = {(r.reference, r.customer_id): r for r in rows}

    def get(self, reference: str, customer_id: str) -> GoldRow | None:
        return self._rows.get((reference, customer_id))

    def list_for_customer(self, customer_id: str) -> list[GoldRow]:
        """Every row of one customer, newest first. Isolation lives here."""
        rows = [r for r in self._rows.values() if r.customer_id == customer_id]
        return sorted(rows, key=lambda r: r.date, reverse=True)
