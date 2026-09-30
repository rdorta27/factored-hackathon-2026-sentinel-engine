"""
Gold layer DuckDB connector (PII-free).

Reads exclusively from ``v_service_dispute_eligible_transactions`` – the
PII-free projection mandated by ADR 008.  All DuckDB calls are offloaded
via ``asyncio.to_thread()`` so the FastAPI event loop is never blocked.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import duckdb

from app.schemas.status import StatusCandidate, to_candidate

_GOLD_DIR = Path(os.getenv("SENTINEL_GOLD_DIR", "data/gold"))
_VIEW_TABLE = "v_service_dispute_eligible_transactions"


def _gold_path() -> Path:
    return _GOLD_DIR.resolve()


# ---------------------------------------------------------------------------
# Synchronous helpers (run inside asyncio.to_thread)
# ---------------------------------------------------------------------------


def _sync_fetch_transactions(customer_id: str) -> list[dict[str, Any]]:
    """
    Query the PII-free Gold view for a single customer's eligible transactions.

    Returns a list of row dicts with a ``candidate_status`` field appended.
    """
    table_path = str(_gold_path() / _VIEW_TABLE)
    con = duckdb.connect(database=":memory:", read_only=False)
    try:
        con.execute("INSTALL delta; LOAD delta;")
        rows = con.execute(
            f"""
            SELECT *
            FROM delta_scan('{table_path}')
            WHERE customer_id = ?
            ORDER BY transaction_date DESC
            """,
            [customer_id],
        ).fetchall()
        col_names = [
            d[0]
            for d in con.execute(
                f"DESCRIBE SELECT * FROM delta_scan('{table_path}') LIMIT 0"
            ).fetchall()
        ]
        result: list[dict[str, Any]] = []
        for row in rows:
            record = dict(zip(col_names, row))
            raw_status: str = record.get("transaction_status", "")
            candidate: StatusCandidate = to_candidate(raw_status)
            record["canonical_status"] = candidate.status.value
            record["status_i18n_key"] = candidate.i18n_key
            result.append(record)
        return result
    finally:
        con.close()


def _sync_fetch_transaction(customer_id: str, transaction_id: str) -> dict[str, Any] | None:
    """Return a single transaction row for ``customer_id`` + ``transaction_id``, or None."""
    table_path = str(_gold_path() / _VIEW_TABLE)
    con = duckdb.connect(database=":memory:", read_only=False)
    try:
        con.execute("INSTALL delta; LOAD delta;")
        rows = con.execute(
            f"""
            SELECT *
            FROM delta_scan('{table_path}')
            WHERE customer_id = ?
              AND transaction_id = ?
            LIMIT 1
            """,
            [customer_id, transaction_id],
        ).fetchall()
        if not rows:
            return None
        col_names = [
            d[0]
            for d in con.execute(
                f"DESCRIBE SELECT * FROM delta_scan('{table_path}') LIMIT 0"
            ).fetchall()
        ]
        record = dict(zip(col_names, rows[0]))
        candidate = to_candidate(record.get("transaction_status", ""))
        record["canonical_status"] = candidate.status.value
        record["status_i18n_key"] = candidate.i18n_key
        return record
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Async public API
# ---------------------------------------------------------------------------


async def fetch_transactions_for_customer(customer_id: str) -> list[dict[str, Any]]:
    """
    Async wrapper: fetch all PII-free transactions for *customer_id*.

    Offloads the DuckDB read to a thread pool so the event loop stays free.
    """
    return await asyncio.to_thread(_sync_fetch_transactions, customer_id)


async def fetch_transaction(
    customer_id: str, transaction_id: str
) -> dict[str, Any] | None:
    """
    Async wrapper: fetch a single transaction scoped to *customer_id*.

    Returns None when the transaction does not exist or belongs to a
    different customer (session isolation enforced at the SQL layer).
    """
    return await asyncio.to_thread(_sync_fetch_transaction, customer_id, transaction_id)
