"""
Incremental batch processing, schema evolution, deduplication, and Gold layer
idempotency tests for REQ-0018.

Test scenarios
--------------
test_batch1_baseline_counts
    Verifies initial Silver and Gold row counts after the first ingestion batch.

test_batch2_deduplication
    Verifies that an exact duplicate transaction_id inserted in Batch 2 is
    purged by the Silver DISTINCT step; Silver row count increases by exactly
    2 (late-arrival + new record), not 3.

test_batch2_schema_evolution_tolerance
    Verifies that adding device_fingerprint to bronze_transactions does not
    raise an error in Silver or Gold transformations.

test_batch2_late_arrival_eligibility
    Verifies that a transaction dated 10 days before the 2026-06-17 cutoff
    (transaction_date = '2026-06-07') is processed into Gold and flagged
    is_eligible_for_dispute = TRUE (days_since_transaction = 10 ≤ 90).

test_batch2_country_normalisation
    Verifies that a transaction with transaction_country = 'Mexico' is stored
    as 'México' in silver_transactions (REQ-0015).

test_pii_free_view_columns
    Verifies that v_service_dispute_eligible_transactions exists after Gold is
    built and contains none of the PII columns dropped by ADR 008
    (customer_first_name, customer_last_name, customer_credit_score).

test_gold_idempotency
    Verifies that running the Gold transformation twice (DROP + CREATE) produces
    the same row count and the same set of is_eligible_for_dispute values.
"""

from __future__ import annotations

from typing import Any

import duckdb
import pytest

from sentinel_data.transforms import (
    DATASET_CUTOFF_DATE,
    DISPUTE_ELIGIBILITY_DAYS,
    gold_eligible_transactions_sql,
    gold_service_eligible_transactions_sql,
    silver_transactions_sql,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CUTOFF = DATASET_CUTOFF_DATE          # "2026-06-17"
_LATE_ARRIVAL_DATE = "2026-06-07"      # 10 days before cutoff — must be eligible
_OLD_DATE = "2025-09-01"               # > 90 days before cutoff — not eligible

# transaction_id shared between Batch 1 and the Batch 2 duplicate row
_DUPLICATE_TXN_ID = "TXN-B1-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fetchdicts(con: duckdb.DuckDBPyConnection, sql: str) -> list[dict[str, Any]]:
    """Execute *sql* and return results as a list of row dicts (no pandas needed)."""
    result = con.execute(sql)
    cols = [desc[0] for desc in result.description]
    return [dict(zip(cols, row)) for row in result.fetchall()]


def _scalar(con: duckdb.DuckDBPyConnection, sql: str) -> Any:
    return con.execute(sql).fetchone()[0]


# ---------------------------------------------------------------------------
# Fixture: fresh in-memory connection with supporting Silver tables
# ---------------------------------------------------------------------------


def _minimal_silver_support(con: duckdb.DuckDBPyConnection) -> None:
    """Create the minimal Silver tables that Gold queries join against.

    Only customers and complaints are needed because gold_eligible_transactions_sql
    joins silver_transactions → silver_customers (LEFT) and silver_complaints (LEFT).
    """
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS silver_customers AS
        SELECT * FROM (VALUES
            ('C001', 'Ana',  'Lopez',  'CO', 'PREMIUM', 750),
            ('C002', 'Luis', 'Gomez',  'MX', 'BASIC',   580),
            ('C003', 'Sara', 'Torres', 'AR', 'STANDARD', 620)
        ) t(customer_id, first_name, last_name, country, segment, credit_score)
        """
    )
    con.execute(
        f"""
        CREATE TABLE IF NOT EXISTS silver_complaints AS
        SELECT * FROM (VALUES
            ('COMP001', 'C002', 'PROD-B', 'OPEN', '{_CUTOFF}', NULL)
        ) t(complaint_id, customer_id, product_id, status, creation_date, resolution_date)
        """
    )


# ---------------------------------------------------------------------------
# State shared between batch steps via a module-level connection.
# Each test function uses the @pytest.fixture below to get an isolated
# connection so tests remain independent.
# ---------------------------------------------------------------------------


@pytest.fixture()
def con() -> duckdb.DuckDBPyConnection:
    """Return a fresh in-memory DuckDB connection for one test."""
    c = duckdb.connect(":memory:")
    yield c
    c.close()


# ---------------------------------------------------------------------------
# Internal setup helpers
# ---------------------------------------------------------------------------


def _create_bronze_batch1(con: duckdb.DuckDBPyConnection) -> None:
    """Create bronze_transactions and load Batch 1 (2 valid records)."""
    con.execute(
        f"""
        CREATE TABLE bronze_transactions (
            transaction_id       VARCHAR,
            transaction_date     VARCHAR,
            process_date         VARCHAR,
            customer_id          VARCHAR,
            product_id           VARCHAR,
            amount               DOUBLE,
            currency             VARCHAR,
            channel              VARCHAR,
            transaction_country  VARCHAR,
            transaction_status   VARCHAR,
            is_fraud             BOOLEAN,
            merchant_name        VARCHAR,
            transaction_type     VARCHAR,
            fraud_score          DOUBLE,
            merchant_category    VARCHAR
        )
        """
    )
    con.execute(
        f"""
        INSERT INTO bronze_transactions VALUES
            ('{_DUPLICATE_TXN_ID}', '{_CUTOFF}',        '{_CUTOFF}',        'C001', 'PROD-A', 150.0, 'MXN', 'APP',    'Colombia', 'COMPLETED', FALSE, 'MerchX', 'PURCHASE', 0.1, 'RETAIL'),
            ('TXN-B1-002',          '{_LATE_ARRIVAL_DATE}', '{_CUTOFF}',    'C003', 'PROD-C', 300.0, 'COP', 'ONLINE', 'Argentina','COMPLETED', FALSE, 'MerchY', 'PURCHASE', 0.0, 'FOOD')
        """
    )


def _build_silver(con: duckdb.DuckDBPyConnection) -> None:
    """Rebuild silver_transactions from bronze_transactions using the canonical SQL."""
    con.execute("DROP TABLE IF EXISTS silver_transactions")
    sql = silver_transactions_sql("bronze_transactions")
    con.execute(f"CREATE TABLE silver_transactions AS {sql}")


def _build_gold(con: duckdb.DuckDBPyConnection) -> None:
    """Rebuild Gold eligible transactions table and PII-free view."""
    con.execute("DROP TABLE IF EXISTS gold_dispute_eligible_transactions")
    con.execute("DROP VIEW  IF EXISTS v_service_dispute_eligible_transactions")

    gold_sql = gold_eligible_transactions_sql(silver_prefix="silver_", engine="duckdb")
    con.execute(f"CREATE TABLE gold_dispute_eligible_transactions AS {gold_sql}")

    view_sql = gold_service_eligible_transactions_sql("gold_dispute_eligible_transactions")
    con.execute(f"CREATE VIEW v_service_dispute_eligible_transactions AS {view_sql}")


def _run_batch1(con: duckdb.DuckDBPyConnection) -> None:
    """Full Batch 1 pipeline: Bronze → Silver → Gold."""
    _minimal_silver_support(con)
    _create_bronze_batch1(con)
    _build_silver(con)
    _build_gold(con)


def _append_batch2(con: duckdb.DuckDBPyConnection) -> None:
    """Schema-evolve bronze and append Batch 2 rows."""
    # Schema evolution: add optional column to simulate upstream change.
    con.execute("ALTER TABLE bronze_transactions ADD COLUMN device_fingerprint VARCHAR")

    con.execute(
        f"""
        INSERT INTO bronze_transactions VALUES
            -- Late-arriving valid record (transaction_date 10 days before cutoff).
            -- Uses C003/PROD-C which has no open complaint, so is_eligible = TRUE.
            ('TXN-B2-LATE', '{_LATE_ARRIVAL_DATE}', '{_CUTOFF}', 'C003', 'PROD-C', 99.0,  'MXN', 'ATM',    'México',   'COMPLETED', FALSE, 'MerchZ', 'PURCHASE', 0.0, 'RETAIL',  NULL),
            -- Duplicate: same transaction_id as Batch 1 row 1
            ('{_DUPLICATE_TXN_ID}', '{_CUTOFF}',    '{_CUTOFF}', 'C001', 'PROD-A', 150.0, 'MXN', 'APP',    'Colombia', 'COMPLETED', FALSE, 'MerchX', 'PURCHASE', 0.1, 'RETAIL',  NULL),
            -- New valid record with device_fingerprint populated (schema evolution)
            ('TXN-B2-NEW',  '{_CUTOFF}',            '{_CUTOFF}', 'C001', 'PROD-A', 500.0, 'USD', 'ONLINE', 'Mexico',   'COMPLETED', FALSE, 'MerchW', 'TRANSFER', 0.0, 'DIGITAL', 'fp-abc123')
        """
    )


def _run_batch2(con: duckdb.DuckDBPyConnection) -> None:
    """Append Batch 2 rows and re-run Silver → Gold."""
    _append_batch2(con)
    _build_silver(con)
    _build_gold(con)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_batch1_baseline_counts(con: duckdb.DuckDBPyConnection) -> None:
    """Batch 1 should produce 2 Silver rows and 2 Gold rows."""
    _run_batch1(con)

    silver_count = _scalar(con, "SELECT COUNT(*) FROM silver_transactions")
    gold_count = _scalar(con, "SELECT COUNT(*) FROM gold_dispute_eligible_transactions")

    assert silver_count == 2, (
        f"Expected 2 Silver rows after Batch 1; got {silver_count}"
    )
    assert gold_count == 2, (
        f"Expected 2 Gold rows after Batch 1; got {gold_count}"
    )


def test_batch2_deduplication(con: duckdb.DuckDBPyConnection) -> None:
    """Silver must deduplicate by transaction_id; Batch 2 adds 2 net-new rows (not 3).

    Batch 1: 2 distinct IDs.
    Batch 2 appends: 1 late-arrival (new ID), 1 duplicate (existing ID), 1 new valid.
    Expected Silver total: 4 (2 + 2 net-new).
    """
    _run_batch1(con)
    _run_batch2(con)

    silver_count = _scalar(con, "SELECT COUNT(*) FROM silver_transactions")
    duplicate_occurrences = _scalar(
        con,
        f"SELECT COUNT(*) FROM silver_transactions WHERE transaction_id = '{_DUPLICATE_TXN_ID}'"
    )

    assert duplicate_occurrences == 1, (
        f"Duplicate transaction_id '{_DUPLICATE_TXN_ID}' must appear exactly once in Silver; "
        f"found {duplicate_occurrences} occurrence(s)"
    )
    assert silver_count == 4, (
        f"Expected 4 distinct Silver rows after Batch 2; got {silver_count}. "
        f"DISTINCT deduplication may not be working correctly."
    )


def test_batch2_schema_evolution_tolerance(con: duckdb.DuckDBPyConnection) -> None:
    """Adding device_fingerprint to bronze_transactions must not break Silver or Gold.

    silver_transactions_sql uses a fixed SELECT column list and does not
    reference device_fingerprint, so the extra column must be silently ignored.
    """
    _run_batch1(con)

    # This call internally does ALTER TABLE + INSERT with device_fingerprint values
    # then rebuilds Silver and Gold.  If schema evolution breaks anything, it raises.
    try:
        _run_batch2(con)
    except Exception as exc:
        pytest.fail(
            f"Schema evolution (adding device_fingerprint) broke the pipeline: {exc}"
        )

    silver_cols = {
        row["column_name"]
        for row in _fetchdicts(
            con, "SELECT column_name FROM information_schema.columns WHERE table_name = 'silver_transactions'"
        )
    }
    assert "device_fingerprint" not in silver_cols, (
        "device_fingerprint must not be propagated into silver_transactions"
    )

    gold_cols = {
        row["column_name"]
        for row in _fetchdicts(
            con,
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'gold_dispute_eligible_transactions'"
        )
    }
    assert "device_fingerprint" not in gold_cols, (
        "device_fingerprint must not be propagated into gold_dispute_eligible_transactions"
    )


def test_batch2_late_arrival_eligibility(con: duckdb.DuckDBPyConnection) -> None:
    """A transaction dated 10 days before the cutoff must be eligible for dispute.

    transaction_date = '2026-06-07' → days_since_transaction = 10 ≤ 90
    transaction_status = 'COMPLETED' (not Reversed/Refunded)
    No open complaint references this customer+product pair in Batch 2.
    Expected: is_eligible_for_dispute = TRUE.
    """
    _run_batch1(con)
    _run_batch2(con)

    rows = _fetchdicts(
        con,
        "SELECT transaction_id, days_since_transaction, is_eligible_for_dispute "
        "FROM gold_dispute_eligible_transactions "
        "WHERE transaction_id = 'TXN-B2-LATE'"
    )

    assert len(rows) == 1, (
        "Late-arriving transaction 'TXN-B2-LATE' not found in gold_dispute_eligible_transactions"
    )
    row = rows[0]
    assert row["days_since_transaction"] == 10, (
        f"Expected days_since_transaction = 10 for late-arrival record; "
        f"got {row['days_since_transaction']}"
    )
    assert row["is_eligible_for_dispute"] is True, (
        f"Late-arriving transaction within {DISPUTE_ELIGIBILITY_DAYS}-day window must be "
        f"is_eligible_for_dispute = TRUE; got {row['is_eligible_for_dispute']}"
    )


def test_batch2_country_normalisation(con: duckdb.DuckDBPyConnection) -> None:
    """'Mexico' in transaction_country must be stored as 'México' in Silver (REQ-0015)."""
    _run_batch1(con)
    _run_batch2(con)

    raw_mexico_count = _scalar(
        con,
        "SELECT COUNT(*) FROM silver_transactions WHERE transaction_country = 'Mexico'"
    )
    normalised_count = _scalar(
        con,
        "SELECT COUNT(*) FROM silver_transactions WHERE transaction_country = 'México'"
    )

    assert raw_mexico_count == 0, (
        f"Found {raw_mexico_count} row(s) with un-normalised 'Mexico' in silver_transactions; "
        "country_norm_expr must canonicalise all occurrences to 'México' (REQ-0015)"
    )
    assert normalised_count >= 1, (
        "Expected at least one row with normalised 'México' in silver_transactions after Batch 2; "
        f"found {normalised_count}"
    )


def test_pii_free_view_columns(con: duckdb.DuckDBPyConnection) -> None:
    """v_service_dispute_eligible_transactions must not expose PII columns (ADR 008).

    Dropped columns: customer_first_name, customer_last_name, customer_credit_score.
    The view must exist and be queryable after Gold is built.
    """
    _run_batch1(con)
    _run_batch2(con)

    # Verify the view is reachable
    try:
        view_rows = _scalar(con, "SELECT COUNT(*) FROM v_service_dispute_eligible_transactions")
    except Exception as exc:
        pytest.fail(f"v_service_dispute_eligible_transactions is not queryable: {exc}")

    assert view_rows >= 0, "View returned a negative count — something is wrong."

    # Inspect view column names via a zero-row query
    result = con.execute(
        "SELECT * FROM v_service_dispute_eligible_transactions LIMIT 0"
    )
    view_cols = {desc[0] for desc in result.description}

    pii_columns = {"customer_first_name", "customer_last_name", "customer_credit_score"}
    exposed_pii = pii_columns & view_cols

    assert not exposed_pii, (
        f"PII column(s) {exposed_pii} are present in v_service_dispute_eligible_transactions. "
        "ADR 008 requires these to be stripped before the service layer."
    )


def test_gold_idempotency(con: duckdb.DuckDBPyConnection) -> None:
    """Running the Gold transformation twice must produce identical results.

    Idempotency is ensured by the DROP + CREATE pattern in _build_gold.
    Re-running on the same Silver state must not change the row count or
    alter the set of eligible transaction IDs.
    """
    _run_batch1(con)
    _run_batch2(con)

    count_first = _scalar(
        con, "SELECT COUNT(*) FROM gold_dispute_eligible_transactions"
    )
    eligible_ids_first = {
        row["transaction_id"]
        for row in _fetchdicts(
            con,
            "SELECT transaction_id FROM gold_dispute_eligible_transactions "
            "WHERE is_eligible_for_dispute = TRUE"
        )
    }

    # Run Gold a second time on the same Silver data
    _build_gold(con)

    count_second = _scalar(
        con, "SELECT COUNT(*) FROM gold_dispute_eligible_transactions"
    )
    eligible_ids_second = {
        row["transaction_id"]
        for row in _fetchdicts(
            con,
            "SELECT transaction_id FROM gold_dispute_eligible_transactions "
            "WHERE is_eligible_for_dispute = TRUE"
        )
    }

    assert count_first == count_second, (
        f"Gold row count changed between runs: first={count_first}, second={count_second}. "
        "Gold transformation is not idempotent."
    )
    assert eligible_ids_first == eligible_ids_second, (
        f"Eligible transaction IDs differ between runs.\n"
        f"  First run:  {sorted(eligible_ids_first)}\n"
        f"  Second run: {sorted(eligible_ids_second)}\n"
        "Gold transformation is not idempotent."
    )
