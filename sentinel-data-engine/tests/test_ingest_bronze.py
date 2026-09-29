"""
Unit tests for BronzeIngestor (local / DuckDB mode).

All tests run without Spark, S3 credentials, or network access beyond the
one-time DuckDB delta extension download.

Test matrix
-----------
    test_bronze_local_ingestion_creates_delta_table   – table is created, row count correct
    test_bronze_local_ingestion_adds_metadata_columns – audit columns present and non-null
    test_idempotency_no_duplicates_on_second_run      – running twice yields the same row count
    test_idempotency_skips_already_ingested_files     – second run appends 0 new rows
    test_new_file_added_between_runs_is_ingested      – a new file after first run IS picked up
    test_config_defaults_are_sane                     – config model defaults are correct

Run with:
    pytest tests/test_ingest_bronze.py -v
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import duckdb
import pytest

from sentinel_data.bronze.ingest_bronze import BronzeIngestorConfig, BronzeIngestor, RunMode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SKIP_DELTA = pytest.mark.skipif(
    os.getenv("SKIP_DELTA_TESTS", "0") == "1",
    reason="Delta extension unavailable in this environment (set SKIP_DELTA_TESTS=0 to enable)",
)

_SAMPLE_ROWS = [
    {"transaction_id": "T001", "account_id": "A1", "amount": "100.00", "currency": "USD"},
    {"transaction_id": "T002", "account_id": "A2", "amount": "250.50", "currency": "EUR"},
    {"transaction_id": "T003", "account_id": "A1", "amount": "75.00",  "currency": "USD"},
]


def _write_csv(path: Path, rows: list[dict]) -> None:
    """Write *rows* to *path* as a CSV with a header row."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _row_count(bronze_path: Path) -> int:
    """Return the total number of rows in the Delta table at *bronze_path*."""
    con = duckdb.connect()
    con.execute("INSTALL delta; LOAD delta;")
    count: int = con.execute(
        f"SELECT COUNT(*) FROM delta_scan('{bronze_path.resolve()}')"
    ).fetchone()[0]  # type: ignore[index]
    con.close()
    return count


def _make_config(tmp_path: Path) -> BronzeIngestorConfig:
    return BronzeIngestorConfig(
        table_name="transactions",
        run_mode=RunMode.LOCAL,
        local_raw_dir=tmp_path / "raw",
        local_bronze_dir=tmp_path / "bronze",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def raw_dir_with_one_csv(tmp_path: Path) -> Path:
    """Create a single CSV file under raw/transactions/ and return tmp_path."""
    _write_csv(
        tmp_path / "raw" / "transactions" / "part_0001.csv",
        _SAMPLE_ROWS,
    )
    return tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@SKIP_DELTA
def test_bronze_local_ingestion_creates_delta_table(
    raw_dir_with_one_csv: Path,
) -> None:
    """After a local run the Bronze Delta table must exist and contain all source rows."""
    cfg = _make_config(raw_dir_with_one_csv)
    BronzeIngestor(cfg).run()

    bronze_path = cfg.local_bronze_dir / cfg.table_name
    assert bronze_path.exists(), "Bronze directory was not created"
    assert _row_count(bronze_path) == len(_SAMPLE_ROWS), (
        f"Expected {len(_SAMPLE_ROWS)} rows, got {_row_count(bronze_path)}"
    )


@SKIP_DELTA
def test_bronze_local_ingestion_adds_metadata_columns(
    raw_dir_with_one_csv: Path,
) -> None:
    """All four audit columns must be present and non-null in every Bronze row."""
    cfg = _make_config(raw_dir_with_one_csv)
    BronzeIngestor(cfg).run()

    bronze_path = cfg.local_bronze_dir / cfg.table_name
    con = duckdb.connect()
    con.execute("INSTALL delta; LOAD delta;")

    column_names = [
        row[0]
        for row in con.execute(
            f"DESCRIBE SELECT * FROM delta_scan('{bronze_path.resolve()}')"
        ).fetchall()
    ]
    for audit_col in ("_source_system", "_source_file", "_ingested_at", "_batch_id"):
        assert audit_col in column_names, f"Audit column '{audit_col}' is missing"

    rows = con.execute(
        f"""
        SELECT _ingested_at, _source_file, _batch_id, _source_system
        FROM delta_scan('{bronze_path.resolve()}')
        """
    ).fetchall()

    for ingested_at, source_file, batch_id, source_system in rows:
        assert ingested_at is not None, "_ingested_at must not be NULL"
        assert source_file and str(source_file).endswith(".csv"), (
            f"_source_file should point to a CSV, got: {source_file}"
        )
        assert batch_id, "_batch_id must not be empty"
        assert source_system, "_source_system must not be empty"

    con.close()


@SKIP_DELTA
def test_idempotency_no_duplicates_on_second_run(
    raw_dir_with_one_csv: Path,
) -> None:
    """
    Running BronzeIngestor twice over the same raw directory must yield the
    same row count as a single run – no duplicate records may be appended.

    This is the core idempotency contract: the ingestor reads the set of
    ``_source_file`` values already present in the Bronze table and skips any
    file whose resolved path is already recorded there.
    """
    cfg = _make_config(raw_dir_with_one_csv)
    bronze_path = cfg.local_bronze_dir / cfg.table_name

    # First run – baseline ingestion
    BronzeIngestor(cfg).run()
    count_after_first_run = _row_count(bronze_path)

    # Second run – must not append any rows
    BronzeIngestor(cfg).run()
    count_after_second_run = _row_count(bronze_path)

    assert count_after_first_run == count_after_second_run, (
        f"Duplicate rows detected: count went from {count_after_first_run} "
        f"to {count_after_second_run} after a second run over the same files."
    )


@SKIP_DELTA
def test_idempotency_skips_already_ingested_files(
    raw_dir_with_one_csv: Path,
) -> None:
    """
    After the first run, the ingestor must report the existing file as skipped
    and append exactly 0 new rows on the second run.
    """
    cfg = _make_config(raw_dir_with_one_csv)
    bronze_path = cfg.local_bronze_dir / cfg.table_name

    BronzeIngestor(cfg).run()
    rows_before = _row_count(bronze_path)

    BronzeIngestor(cfg).run()
    rows_after = _row_count(bronze_path)

    assert rows_after - rows_before == 0, (
        f"Expected 0 new rows on second run, got {rows_after - rows_before}."
    )


@SKIP_DELTA
def test_new_file_added_between_runs_is_ingested(
    raw_dir_with_one_csv: Path,
) -> None:
    """
    A CSV file added to the raw directory *after* the first run must be picked
    up by the second run while the original file is still skipped.
    """
    cfg = _make_config(raw_dir_with_one_csv)
    bronze_path = cfg.local_bronze_dir / cfg.table_name

    # First run – ingests part_0001.csv
    BronzeIngestor(cfg).run()
    rows_after_first = _row_count(bronze_path)

    # Add a new file with 2 fresh rows
    new_rows = [
        {"transaction_id": "T004", "account_id": "A3", "amount": "10.00", "currency": "GBP"},
        {"transaction_id": "T005", "account_id": "A3", "amount": "20.00", "currency": "GBP"},
    ]
    _write_csv(
        raw_dir_with_one_csv / "raw" / "transactions" / "part_0002.csv",
        new_rows,
    )

    # Second run – must ingest only the new file
    BronzeIngestor(cfg).run()
    rows_after_second = _row_count(bronze_path)

    assert rows_after_second == rows_after_first + len(new_rows), (
        f"Expected {rows_after_first + len(new_rows)} total rows after second run, "
        f"got {rows_after_second}."
    )


def test_config_defaults_are_sane() -> None:
    """BronzeIngestorConfig must instantiate with only a table_name argument."""
    cfg = BronzeIngestorConfig(table_name="digital_events")
    assert cfg.run_mode == RunMode.LOCAL
    assert cfg.local_raw_dir == Path("data/raw")
    assert cfg.local_bronze_dir == Path("data/bronze")
    assert cfg.source_system == "s3"
