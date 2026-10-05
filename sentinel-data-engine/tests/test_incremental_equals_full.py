"""An incremental load gives the same rows as a full load, row by row.

Both paths build the same Bronze row multiset and run the canonical Silver
and Gold SQL. The incremental path ingests in two batches and rebuilds
after each; the full path ingests once. Silver, Gold and the PII-free view
must match exactly, so a late or reprocessed batch never changes history.
"""

from __future__ import annotations

import json
from typing import Any

import duckdb
import pytest

from test_incremental_fixture import (
    _build_gold,
    _build_silver,
    _fetchdicts,
    _minimal_silver_support,
)

BRONZE_COLUMNS = (
    "transaction_id, transaction_date, process_date, customer_id, product_id,"
    " amount, currency, channel, transaction_country, transaction_status,"
    " is_fraud, merchant_name, transaction_type, fraud_score,"
    " merchant_category, transaction_category, amount_usd, branch_id,"
    " device_fingerprint"
)

BATCH1 = (
    "('TXN-B1-001', '2026-06-17', '2026-06-17', 'C001', 'PROD-A', 150.0, 'MXN', 'APP',"
    " 'Colombia', 'COMPLETED', FALSE, 'MerchX', 'PURCHASE', 0.1, 'RETAIL', 'Food', 12.50, NULL, NULL)",
    "('TXN-B1-002', '2026-06-07', '2026-06-17', 'C003', 'PROD-C', 300.0, 'COP', 'ONLINE',"
    " 'Argentina', 'COMPLETED', FALSE, 'MerchY', 'PURCHASE', 0.0, 'FOOD', 'Transport', 18.00, NULL, NULL)",
)

BATCH2 = (
    "('TXN-B2-LATE', '2026-06-07', '2026-06-17', 'C003', 'PROD-C', 99.0, 'MXN', 'ATM',"
    " 'México', 'COMPLETED', FALSE, 'MerchZ', 'PURCHASE', 0.0, 'RETAIL', 'Health', 7.10, NULL, NULL)",
    "('TXN-B1-001', '2026-06-17', '2026-06-17', 'C001', 'PROD-A', 150.0, 'MXN', 'APP',"
    " 'Colombia', 'COMPLETED', FALSE, 'MerchX', 'PURCHASE', 0.1, 'RETAIL', 'Food', 12.50, NULL, NULL)",
    "('TXN-B2-NEW', '2026-06-17', '2026-06-17', 'C001', 'PROD-A', 500.0, 'USD', 'ONLINE',"
    " 'Mexico', 'COMPLETED', FALSE, 'MerchW', 'TRANSFER', 0.0, 'DIGITAL', NULL, 500.0, 'BR-001', 'fp-abc123')",
)

TABLES = (
    "silver_transactions",
    "gold_dispute_eligible_transactions",
    "v_service_dispute_eligible_transactions",
)


@pytest.fixture()
def con() -> duckdb.DuckDBPyConnection:
    connection = duckdb.connect(":memory:")
    yield connection
    connection.close()


def _create_bronze(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE bronze_transactions (
            transaction_id        VARCHAR,
            transaction_date      VARCHAR,
            process_date          VARCHAR,
            customer_id           VARCHAR,
            product_id            VARCHAR,
            amount                DOUBLE,
            currency              VARCHAR,
            channel               VARCHAR,
            transaction_country   VARCHAR,
            transaction_status    VARCHAR,
            is_fraud              BOOLEAN,
            merchant_name         VARCHAR,
            transaction_type      VARCHAR,
            fraud_score           DOUBLE,
            merchant_category     VARCHAR,
            transaction_category  VARCHAR,
            amount_usd            DOUBLE,
            branch_id             VARCHAR,
            device_fingerprint    VARCHAR
        )
        """
    )


def _insert(con: duckdb.DuckDBPyConnection, rows: tuple[str, ...]) -> None:
    con.execute(f"INSERT INTO bronze_transactions ({BRONZE_COLUMNS}) VALUES {','.join(rows)}")


def _rebuild(con: duckdb.DuckDBPyConnection) -> None:
    _build_silver(con)
    _build_gold(con)


def _snapshot(con: duckdb.DuckDBPyConnection) -> dict[str, list[str]]:
    """Every compared table as sorted canonical row strings."""
    snap: dict[str, list[str]] = {}
    for table in TABLES:
        rows = _fetchdicts(con, f"SELECT * FROM {table}")
        snap[table] = sorted(json.dumps(row, sort_keys=True, default=str) for row in rows)
    return snap


def _snapshot_columns(con: duckdb.DuckDBPyConnection) -> dict[str, list[str]]:
    return {
        table: [desc[0] for desc in con.execute(f"SELECT * FROM {table} LIMIT 0").description]
        for table in TABLES
    }


def test_incremental_load_equals_full_load_row_by_row(con: duckdb.DuckDBPyConnection) -> None:
    full = duckdb.connect(":memory:")
    try:
        _minimal_silver_support(full)
        _create_bronze(full)
        _insert(full, BATCH1 + BATCH2)
        _rebuild(full)
        expected = _snapshot(full)
        expected_columns = _snapshot_columns(full)
    finally:
        full.close()

    _minimal_silver_support(con)
    _create_bronze(con)
    _insert(con, BATCH1)
    _rebuild(con)
    _insert(con, BATCH2)
    _rebuild(con)

    assert _snapshot_columns(con) == expected_columns
    assert _snapshot(con) == expected


def test_comparison_is_not_vacuous(con: duckdb.DuckDBPyConnection) -> None:
    """The compared tables hold rows and the duplicate collapsed to one."""
    _minimal_silver_support(con)
    _create_bronze(con)
    _insert(con, BATCH1 + BATCH2)
    _rebuild(con)
    snap = _snapshot(con)
    assert len(snap["silver_transactions"]) == 4
    assert len(snap["gold_dispute_eligible_transactions"]) > 0
    assert len(snap["v_service_dispute_eligible_transactions"]) > 0
