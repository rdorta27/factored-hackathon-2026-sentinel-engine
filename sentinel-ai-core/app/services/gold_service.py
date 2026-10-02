"""
Gold layer DuckDB connector (PII-free).

Reads exclusively from ``v_service_dispute_eligible_transactions`` – the
PII-free projection mandated by ADR 008.  All DuckDB calls are offloaded
via ``asyncio.to_thread()`` so the FastAPI event loop is never blocked.

Source priority for local development:
  1. ``data/gold_bank.duckdb``  – single-file DuckDB written by the Medallion pipeline.
  2. ``data/gold/``             – Delta Lake directory (``SENTINEL_GOLD_DIR``).
  3. Mock data                  – when neither source is present.
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

# Candidate paths probed in order when SENTINEL_GOLD_DUCKDB is not set.
# Each entry is relative to the current working directory at runtime so the
# service resolves correctly whether launched from the monorepo root, from
# inside sentinel-ai-core/, or from sentinel-data-engine/.
_DUCKDB_CANDIDATES: tuple[Path, ...] = (
    Path("data/gold_bank.duckdb"),
    Path("sentinel-data-engine/data/gold_bank.duckdb"),
    Path("../sentinel-data-engine/data/gold_bank.duckdb"),
    Path("../data/gold_bank.duckdb"),
)


def _gold_path() -> Path:
    return _GOLD_DIR.resolve()


def gold_duckdb_path() -> Path | None:
    """Return the first resolvable path to ``gold_bank.duckdb``, or None.

    Resolution order:
      1. ``SENTINEL_GOLD_DUCKDB`` env var (must point to an existing file).
      2. Candidate paths in ``_DUCKDB_CANDIDATES`` (first existing file wins).
    """
    env_val = os.getenv("SENTINEL_GOLD_DUCKDB", "").strip()
    if env_val:
        p = Path(env_val).resolve()
        if p.is_file():
            return p

    for candidate in _DUCKDB_CANDIDATES:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved

    return None


# ---------------------------------------------------------------------------
# Priority 1: single-file DuckDB helpers
# ---------------------------------------------------------------------------


def _sync_fetch_transactions_duckdb(customer_id: str, db_path: str) -> list[dict[str, Any]]:
    """Query ``v_service_dispute_eligible_transactions`` from the local .duckdb file."""
    con = duckdb.connect(database=db_path, read_only=True)
    try:
        rows = con.execute(
            f"""
            SELECT *
            FROM {_VIEW_TABLE}
            WHERE customer_id = ?
            ORDER BY transaction_date DESC
            """,
            [customer_id],
        ).fetchall()
        col_names = [d[0] for d in con.execute(f"DESCRIBE {_VIEW_TABLE}").fetchall()]
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


def _sync_fetch_transaction_duckdb(customer_id: str, transaction_id: str, db_path: str) -> dict[str, Any] | None:
    """Return a single transaction from the local .duckdb file, or None."""
    con = duckdb.connect(database=db_path, read_only=True)
    try:
        rows = con.execute(
            f"""
            SELECT *
            FROM {_VIEW_TABLE}
            WHERE customer_id = ?
              AND transaction_id = ?
            LIMIT 1
            """,
            [customer_id, transaction_id],
        ).fetchall()
        if not rows:
            return None
        col_names = [d[0] for d in con.execute(f"DESCRIBE {_VIEW_TABLE}").fetchall()]
        record = dict(zip(col_names, rows[0]))
        candidate = to_candidate(record.get("transaction_status", ""))
        record["canonical_status"] = candidate.status.value
        record["status_i18n_key"] = candidate.i18n_key
        return record
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Priority 2: Delta Lake helpers
# ---------------------------------------------------------------------------


def _sync_fetch_transactions(customer_id: str) -> list[dict[str, Any]]:
    """
    Query the PII-free Gold view for a single customer's eligible transactions.

    Dispatches to the local DuckDB file (Priority 1) when present; otherwise
    reads from the Delta Lake directory (Priority 2).

    Returns a list of row dicts with a ``candidate_status`` field appended.
    """
    db_file = gold_duckdb_path()
    if db_file is not None:
        return _sync_fetch_transactions_duckdb(customer_id, str(db_file))
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
    """Return a single transaction row for ``customer_id`` + ``transaction_id``, or None.

    Dispatches to the local DuckDB file (Priority 1) when present; otherwise
    reads from the Delta Lake directory (Priority 2).
    """
    db_file = gold_duckdb_path()
    if db_file is not None:
        return _sync_fetch_transaction_duckdb(customer_id, transaction_id, str(db_file))
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
