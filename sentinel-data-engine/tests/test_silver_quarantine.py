"""
Unit tests for SilverTransformer – quarantine split and Silver promotion.

Strategy
--------
All tests run in LOCAL mode using DuckDB + the delta extension.
No Spark session, no S3 credentials, no network calls beyond the one-time
DuckDB extension download.

Fixture layout (uses tmp_path to avoid cross-test pollution)
------------------------------------------------------------
    tmp_path/
        bronze/transactions/   – Bronze Delta table (written by fixture)
        silver/transactions/   – Silver Delta table (created by transformer)
        silver/rejected_records/ – Quarantine Delta table (created by transformer)

Test matrix
-----------
    test_valid_rows_reach_silver          – all-valid input → silver table has rows
    test_invalid_rows_routed_to_quarantine – null id → rejected_records has rows
    test_rejection_reason_content         – rejection_reason names the failed rules
    test_mixed_input_split_correctly      – 2 valid + 1 invalid → split verified
    test_deduplication_keeps_latest_row   – same id twice → only latest survives in silver
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import duckdb
import pytest

from sentinel_data.silver.transform_silver import (
    QualityRule,
    RunMode,
    SilverTransformerConfig,
    SilverTransformer,
)


# ---------------------------------------------------------------------------
# Skip guard – requires the delta DuckDB extension (network access on first run)
# ---------------------------------------------------------------------------

SKIP_DELTA = pytest.mark.skipif(
    os.getenv("SKIP_DELTA_TESTS", "0") == "1",
    reason="Delta extension unavailable in this environment (set SKIP_DELTA_TESTS=0 to enable)",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_bronze_delta(
    tmp_path: Path,
    rows: list[dict],
    table_name: str = "transactions",
) -> Path:
    """
    Create a Bronze Delta table from a list of dicts.

    Mandatory Bronze audit columns (_ingested_at, _source_file, _batch_id,
    _source_system) are injected automatically so tests only need to supply
    the business columns.
    """
    bronze_dir = tmp_path / "bronze" / table_name
    bronze_dir.mkdir(parents=True, exist_ok=True)

    # Write a temporary CSV then import into Delta via DuckDB
    csv_path = tmp_path / f"{table_name}_fixture.csv"
    if rows:
        fieldnames = list(rows[0].keys()) + [
            "_ingested_at",
            "_source_file",
            "_batch_id",
            "_source_system",
        ]
        with csv_path.open("w", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for i, row in enumerate(rows):
                writer.writerow(
                    {
                        **row,
                        "_ingested_at": f"2026-01-01T00:0{i}:00Z",
                        "_source_file": f"/data/raw/{table_name}/part_{i:04d}.csv",
                        "_batch_id": "test-batch-001",
                        "_source_system": "local",
                    }
                )

    con = duckdb.connect()
    con.execute("INSTALL delta; LOAD delta;")
    con.execute(
        f"""
        COPY (SELECT * FROM read_csv_auto('{csv_path}', header = true))
        TO 'delta://{bronze_dir.resolve()}'
        (FORMAT delta);
        """
    )
    con.close()
    return bronze_dir


def _read_delta(path: Path) -> list[dict]:
    """Return all rows from a Delta table as a list of dicts."""
    con = duckdb.connect()
    con.execute("INSTALL delta; LOAD delta;")
    rows = con.execute(
        f"SELECT * FROM delta_scan('{path.resolve()}')"
    ).df().to_dict(orient="records")
    con.close()
    return rows


def _make_config(tmp_path: Path, rules: list[QualityRule] | None = None) -> SilverTransformerConfig:
    return SilverTransformerConfig(
        table_name="transactions",
        primary_key="id",
        run_mode=RunMode.LOCAL,
        quality_rules=rules or SilverTransformerConfig.__fields__["quality_rules"].default_factory(),
        local_bronze_dir=tmp_path / "bronze",
        local_silver_dir=tmp_path / "silver",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@SKIP_DELTA
def test_valid_rows_reach_silver(tmp_path: Path) -> None:
    """All rows with non-null, positive id must appear in the Silver table."""
    rows = [
        {"id": "1", "amount": "100.00"},
        {"id": "2", "amount": "250.50"},
    ]
    _write_bronze_delta(tmp_path, rows)

    cfg = _make_config(tmp_path)
    SilverTransformer(cfg).run()

    silver_path = tmp_path / "silver" / "transactions"
    assert silver_path.exists(), "Silver directory was not created"

    silver_rows = _read_delta(silver_path)
    assert len(silver_rows) == 2, f"Expected 2 silver rows, got {len(silver_rows)}"


@SKIP_DELTA
def test_invalid_rows_routed_to_quarantine(tmp_path: Path) -> None:
    """A row with a null id must not enter Silver and must appear in rejected_records."""
    rows = [
        {"id": None, "amount": "999.00"},
    ]
    _write_bronze_delta(tmp_path, rows)

    cfg = _make_config(tmp_path)
    SilverTransformer(cfg).run()

    silver_path = tmp_path / "silver" / "transactions"
    quarantine_path = tmp_path / "silver" / "rejected_records"

    # Silver table may not exist at all (no clean rows written)
    silver_rows = _read_delta(silver_path) if silver_path.exists() else []
    assert len(silver_rows) == 0, "Null-id row must not reach Silver"

    assert quarantine_path.exists(), "Quarantine directory was not created"
    quarantine_rows = _read_delta(quarantine_path)
    assert len(quarantine_rows) == 1, f"Expected 1 quarantine row, got {len(quarantine_rows)}"


@SKIP_DELTA
def test_rejection_reason_content(tmp_path: Path) -> None:
    """The rejection_reason field must name every failed rule, separated by ';'."""
    rows = [
        {"id": None, "amount": "50.00"},   # fails id_not_null AND id_positive
    ]
    _write_bronze_delta(tmp_path, rows)

    cfg = _make_config(tmp_path)
    SilverTransformer(cfg).run()

    quarantine_path = tmp_path / "silver" / "rejected_records"
    quarantine_rows = _read_delta(quarantine_path)
    assert quarantine_rows, "No quarantine rows found"

    reason: str = quarantine_rows[0]["rejection_reason"]
    assert "id_not_null" in reason, f"Expected 'id_not_null' in rejection_reason, got: {reason}"
    assert "id_positive" in reason, f"Expected 'id_positive' in rejection_reason, got: {reason}"


@SKIP_DELTA
def test_mixed_input_split_correctly(tmp_path: Path) -> None:
    """2 valid rows + 1 invalid row must produce 2 Silver rows and 1 quarantine row."""
    rows = [
        {"id": "1",  "amount": "10.00"},
        {"id": "2",  "amount": "20.00"},
        {"id": None, "amount": "30.00"},
    ]
    _write_bronze_delta(tmp_path, rows)

    cfg = _make_config(tmp_path)
    SilverTransformer(cfg).run()

    silver_rows = _read_delta(tmp_path / "silver" / "transactions")
    quarantine_rows = _read_delta(tmp_path / "silver" / "rejected_records")

    assert len(silver_rows) == 2, f"Expected 2 silver rows, got {len(silver_rows)}"
    assert len(quarantine_rows) == 1, f"Expected 1 quarantine row, got {len(quarantine_rows)}"


@SKIP_DELTA
def test_deduplication_keeps_latest_row(tmp_path: Path) -> None:
    """
    Two Bronze records sharing the same id must produce exactly one Silver row,
    and it must be the one with the later _ingested_at timestamp.
    """
    # Both rows have id=1 but different amounts and timestamps.
    # The fixture assigns _ingested_at as 2026-01-01T00:00:00Z and 2026-01-01T00:01:00Z.
    rows = [
        {"id": "1", "amount": "OLD_100"},
        {"id": "1", "amount": "NEW_200"},
    ]
    _write_bronze_delta(tmp_path, rows)

    cfg = _make_config(tmp_path)
    SilverTransformer(cfg).run()

    silver_rows = _read_delta(tmp_path / "silver" / "transactions")
    assert len(silver_rows) == 1, f"Expected 1 deduplicated row, got {len(silver_rows)}"
    assert silver_rows[0]["amount"] == "NEW_200", (
        f"Expected the later row to survive deduplication, got amount={silver_rows[0]['amount']}"
    )


@SKIP_DELTA
def test_quarantine_schema_has_required_columns(tmp_path: Path) -> None:
    """Quarantine records must expose raw_record, rejection_reason, rejected_at, source_file."""
    rows = [{"id": None, "amount": "0"}]
    _write_bronze_delta(tmp_path, rows)

    cfg = _make_config(tmp_path)
    SilverTransformer(cfg).run()

    quarantine_rows = _read_delta(tmp_path / "silver" / "rejected_records")
    assert quarantine_rows, "No quarantine rows produced"
    record = quarantine_rows[0]

    for required_col in ("raw_record", "rejection_reason", "rejected_at", "source_file"):
        assert required_col in record, f"Missing required quarantine column: {required_col}"
    assert record["raw_record"], "raw_record must not be empty"
    assert record["rejected_at"] is not None, "rejected_at must not be null"
