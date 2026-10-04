"""
Gold layer DuckDB connector (PII-free).

Reads exclusively from ``v_service_dispute_eligible_transactions`` – the
PII-free projection mandated by ADR 008.  All DuckDB calls are offloaded
via ``asyncio.to_thread()`` so the FastAPI event loop is never blocked.

Source priority for local development:
  1. ``SENTINEL_GOLD_DUCKDB``, or one path fixed relative to the repository.
  2. ``data/gold/``             – Delta Lake directory (``SENTINEL_GOLD_DIR``).
  3. Mock data                  – when neither source is present, or when
     ``SENTINEL_GOLD_SOURCE`` is ``mock`` (no file is opened).
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
_DATE_PREDICATE = "CAST(transaction_date AS DATE) <= CAST(? AS DATE)"


def repo_root() -> Path:
    """Repository root, from this file, never from the process working directory."""
    return Path(__file__).resolve().parents[3]


def default_gold_duckdb_path() -> Path:
    """The one DuckDB file the app looks for when ``SENTINEL_GOLD_DUCKDB`` is unset."""
    return repo_root() / "sentinel-data-engine" / "data" / "gold_bank.duckdb"


def _gold_path() -> Path:
    return _GOLD_DIR.resolve()


def gold_duckdb_path() -> Path | None:
    """Return the DuckDB Gold file, or None.

    ``SENTINEL_GOLD_DUCKDB`` when set (absolute, or relative to the repository).
    Otherwise ``sentinel-data-engine/data/gold_bank.duckdb`` next to this package.
    A relative value is never resolved from the folder the process was started from.
    A set value that is not a file does not fall through to another path.
    """
    env_val = os.getenv("SENTINEL_GOLD_DUCKDB", "").strip()
    if env_val:
        candidate = Path(env_val)
        if not candidate.is_absolute():
            candidate = repo_root() / candidate
        resolved = candidate.resolve()
        return resolved if resolved.is_file() else None
    candidate = default_gold_duckdb_path()
    return candidate if candidate.is_file() else None


# ---------------------------------------------------------------------------
# Priority 1: single-file DuckDB helpers
# ---------------------------------------------------------------------------


def _sync_fetch_transactions_duckdb(customer_id: str, db_path: str, as_of: str) -> list[dict[str, Any]]:
    """Query ``v_service_dispute_eligible_transactions`` from the local .duckdb file."""
    con = duckdb.connect(database=db_path, read_only=True)
    try:
        rows = con.execute(
            f"""
            SELECT *
            FROM {_VIEW_TABLE}
            WHERE customer_id = ?
              AND {_DATE_PREDICATE}
            ORDER BY transaction_date DESC
            """,
            [customer_id, as_of],
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


def _sync_fetch_transaction_duckdb(
    customer_id: str, transaction_id: str, db_path: str, as_of: str
) -> dict[str, Any] | None:
    """Return a single transaction from the local .duckdb file, or None."""
    con = duckdb.connect(database=db_path, read_only=True)
    try:
        rows = con.execute(
            f"""
            SELECT *
            FROM {_VIEW_TABLE}
            WHERE customer_id = ?
              AND transaction_id = ?
              AND {_DATE_PREDICATE}
            LIMIT 1
            """,
            [customer_id, transaction_id, as_of],
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


def _sync_fetch_transactions(customer_id: str, as_of: str) -> list[dict[str, Any]]:
    """
    Query the PII-free Gold view for a single customer's eligible transactions.

    Dispatches to the local DuckDB file (Priority 1) when present; otherwise
    reads from the Delta Lake directory (Priority 2).

    Returns a list of row dicts with a ``candidate_status`` field appended.
    """
    db_file = gold_duckdb_path()
    if db_file is not None:
        return _sync_fetch_transactions_duckdb(customer_id, str(db_file), as_of)
    table_path = str(_gold_path() / _VIEW_TABLE)
    con = duckdb.connect(database=":memory:", read_only=False)
    try:
        con.execute("INSTALL delta; LOAD delta;")
        rows = con.execute(
            f"""
            SELECT *
            FROM delta_scan('{table_path}')
            WHERE customer_id = ?
              AND {_DATE_PREDICATE}
            ORDER BY transaction_date DESC
            """,
            [customer_id, as_of],
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


def _sync_fetch_transaction(customer_id: str, transaction_id: str, as_of: str) -> dict[str, Any] | None:
    """Return a single transaction row for ``customer_id`` + ``transaction_id``, or None.

    Dispatches to the local DuckDB file (Priority 1) when present; otherwise
    reads from the Delta Lake directory (Priority 2).
    """
    db_file = gold_duckdb_path()
    if db_file is not None:
        return _sync_fetch_transaction_duckdb(customer_id, transaction_id, str(db_file), as_of)
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
              AND {_DATE_PREDICATE}
            LIMIT 1
            """,
            [customer_id, transaction_id, as_of],
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


async def fetch_transactions_for_customer(customer_id: str, as_of: str) -> list[dict[str, Any]]:
    """
    Async wrapper: fetch all PII-free transactions for *customer_id*.

    Offloads the DuckDB read to a thread pool so the event loop stays free.
    Rows dated after *as_of* are excluded in the query.
    """
    return await asyncio.to_thread(_sync_fetch_transactions, customer_id, as_of)


async def fetch_transaction(
    customer_id: str, transaction_id: str, as_of: str
) -> dict[str, Any] | None:
    """
    Async wrapper: fetch a single transaction scoped to *customer_id*.

    Returns None when the transaction does not exist or belongs to a
    different customer (session isolation enforced at the SQL layer).
    """
    return await asyncio.to_thread(_sync_fetch_transaction, customer_id, transaction_id, as_of)
