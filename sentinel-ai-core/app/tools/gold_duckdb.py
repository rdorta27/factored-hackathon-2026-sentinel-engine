"""DuckDB Gold store behind the ``GoldTransactions`` seam.

Reads the PII-free view ``v_service_dispute_eligible_transactions`` through
``app.services.gold_service`` and maps each row onto ``GoldRow``, so the
orchestrator, the listing and the chat run unchanged on real Gold.
``select_gold`` falls back to the in-memory mock when the view is not
readable (no local ``data/``, no ``delta`` extension, any DuckDB error).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from app.services import gold_service
from app.tools.gold import GoldRow, GoldTransactions, MockGoldStore

logger = logging.getLogger("sentinel.gold")

# Dataset vocabulary (data dictionary: Approved, Declined, Pending, Reversed).
_STATUSES = {"approved": "Approved", "declined": "Declined", "pending": "Pending", "reversed": "Reversed"}


def to_gold_row(record: dict[str, Any], as_of: str) -> GoldRow:
    """Map one view row onto the seam. Unknown statuses become Pending (not disputable)."""
    raw = str(record.get("transaction_status") or "").strip().lower()
    refunded = raw in ("refunded", "reversed")
    return GoldRow(
        reference=str(record["transaction_id"]),
        customer_id=str(record["customer_id"]),
        amount=f"{float(record.get('amount') or 0):.2f}",
        currency=str(record.get("currency") or ""),
        merchant=str(record.get("merchant_name") or ""),
        date=str(record.get("transaction_date") or "")[:10],
        status=_STATUSES.get(raw, "Reversed" if refunded else "Pending"),
        as_of=as_of,
        refunded=refunded,
        prior_dispute=bool(record.get("is_disputed", False)),
        fraud_score=_score(record.get("fraud_score")),
    )


def _score(raw: Any) -> float | None:
    try:
        return None if raw is None or str(raw).strip() == "" else float(raw)
    except (TypeError, ValueError):
        return None


class DuckDbGoldStore:
    """Real Gold read; same contract as ``MockGoldStore``."""

    def __init__(self, as_of: str) -> None:
        self._as_of = as_of

    def get(self, reference: str, customer_id: str) -> GoldRow | None:
        record = gold_service._sync_fetch_transaction(customer_id, reference, self._as_of)
        return None if record is None else to_gold_row(record, self._as_of)

    def list_for_customer(self, customer_id: str) -> list[GoldRow]:
        rows = [
            to_gold_row(record, self._as_of)
            for record in gold_service._sync_fetch_transactions(customer_id, self._as_of)
        ]
        return sorted(rows, key=lambda row: row.date, reverse=True)


def select_gold(as_of: str) -> tuple[GoldTransactions, str]:
    """Return the DuckDB store when the view answers a probe, else the mock.

    ``SENTINEL_GOLD_SOURCE`` = ``auto`` (default) | ``mock`` | ``duckdb``.
    ``duckdb`` still falls back to the mock, with a warning, if the probe fails.

    Source priority (``auto`` mode):
      1. ``SENTINEL_GOLD_DUCKDB``, or the repository-relative DuckDB file.
      2. ``SENTINEL_GOLD_DIR``      – Delta Lake directory.
      3. Mock data                  – when neither source is present or readable.

    ``mock`` returns before any file is opened.
    """
    if os.environ.get("SENTINEL_GOLD_SOURCE", "auto").lower() == "mock":
        return MockGoldStore(as_of=as_of), "mock"

    # Priority 1: single-file DuckDB (multi-path resolution)
    db_file = gold_service.gold_duckdb_path()
    if db_file is not None:
        store = DuckDbGoldStore(as_of)
        try:
            store.list_for_customer("__probe__")
        except Exception as error:  # noqa: BLE001
            logger.warning("gold_bank.duckdb at %s not readable (%s); trying Delta Lake", db_file, type(error).__name__)
        else:
            logger.info("Gold source: duckdb file (%s)", db_file)
            return store, "duckdb"

    # Priority 2: Delta Lake directory
    view = gold_service._gold_path() / gold_service._VIEW_TABLE
    if view.is_dir():
        store = DuckDbGoldStore(as_of)
        try:
            store.list_for_customer("__probe__")
        except Exception as error:  # noqa: BLE001
            logger.warning("Gold view at %s not readable (%s); using the mock", view, type(error).__name__)
        else:
            logger.info("Gold source: delta lake (%s)", view)
            return store, "duckdb"
    else:
        logger.info("Gold view not found at %s; using the mock", view)

    # Priority 3: mock fallback
    return MockGoldStore(as_of=as_of), "mock"
