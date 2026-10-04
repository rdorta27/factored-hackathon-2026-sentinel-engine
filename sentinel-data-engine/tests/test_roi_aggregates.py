"""ROI aggregates: source switch, aggregates only, write-once freeze."""

import importlib.util
import json
import sys
from pathlib import Path

import duckdb
import pytest

_REPO = Path(__file__).resolve().parent.parent.parent
_SPEC = importlib.util.spec_from_file_location("roi_aggregates", _REPO / "scripts" / "roi_aggregates.py")
roi = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = roi
_SPEC.loader.exec_module(roi)


def _write_calls(path: Path, *, silver_has_duration: bool) -> None:
    con = duckdb.connect(str(path))
    con.execute(
        """
        CREATE TABLE bronze_call_center_interactions (
            interaction_id INTEGER, interaction_date DATE, contact_reason VARCHAR,
            duration_seconds INTEGER, was_resolved BOOLEAN, was_escalated BOOLEAN
        )
        """
    )
    # Two transactional calls (one resolved, one escalated), one without a
    # duration, one complaint call, one technical call.
    con.execute(
        "INSERT INTO bronze_call_center_interactions VALUES"
        " (1, '2026-01-01', 'Transaccional', 180, TRUE, FALSE),"
        " (2, '2026-01-02', 'Transaccional', 300, FALSE, TRUE),"
        " (3, '2026-01-03', 'Transaccional', NULL, TRUE, FALSE),"
        " (4, '2026-01-04', 'Queja', 600, FALSE, FALSE),"
        " (5, '2026-01-05', 'Técnico', 60, TRUE, FALSE)"
    )
    columns = "interaction_id INTEGER, interaction_date DATE, contact_reason VARCHAR"
    if silver_has_duration:
        columns += ", duration_seconds INTEGER, was_resolved BOOLEAN, was_escalated BOOLEAN"
        silver_rows = "SELECT interaction_id, interaction_date, contact_reason, duration_seconds, was_resolved, was_escalated FROM bronze_call_center_interactions"
    else:
        # Silver before the restored columns: no durations there.
        columns += ", was_resolved BOOLEAN, was_escalated BOOLEAN"
        silver_rows = "SELECT interaction_id, interaction_date, contact_reason, was_resolved, was_escalated FROM bronze_call_center_interactions"
    con.execute(f"CREATE TABLE silver_call_center_interactions ({columns})")
    con.execute(f"INSERT INTO silver_call_center_interactions {silver_rows}")
    con.close()


def test_reads_silver_when_it_kept_the_durations(tmp_path: Path) -> None:
    db = tmp_path / "gold_bank.duckdb"
    _write_calls(db, silver_has_duration=True)
    summary = roi.summarize(db)
    assert summary["source"]["table"] == "silver_call_center_interactions"
    assert summary["total_calls"]["n"] == 5
    assert summary["transactional_calls"]["n"] == 3
    transactional = summary["transactional"]
    assert transactional["handle_time"]["n_with_duration"] == 2
    assert transactional["handle_time"]["missing_duration"] == 1
    assert transactional["handle_time"]["mean_minutes"] == 4.0  # (180 + 300) / 2 / 60
    assert transactional["first_contact_resolution"]["share"] == 0.6667
    assert transactional["escalation"]["share"] == 0.3333
    assert summary["complaint_calls"]["handle_time"]["mean_minutes"] == 10.0


def test_falls_back_to_bronze_when_silver_drops_the_durations(tmp_path: Path) -> None:
    db = tmp_path / "gold_bank.duckdb"
    _write_calls(db, silver_has_duration=False)
    summary = roi.summarize(db)
    assert summary["source"]["table"] == "bronze_call_center_interactions"
    assert summary["source"]["reason"] == "silver drops duration_seconds, bronze has it"
    assert summary["transactional"]["handle_time"]["mean_minutes"] == 4.0
    assert summary["total_calls"]["missing_duration"] == 1


def test_freeze_is_write_once_and_holds_no_identifier(tmp_path: Path) -> None:
    db = tmp_path / "gold_bank.duckdb"
    _write_calls(db, silver_has_duration=True)
    summary = roi.summarize(db)
    original = roi.EVIDENCE_DIR
    roi.EVIDENCE_DIR = tmp_path
    try:
        folder = roi.freeze("roi-v1", summary)
        assert (folder / "summary.json").is_file()
        with pytest.raises(SystemExit, match="refusing to overwrite"):
            roi.freeze("roi-v1", summary)
    finally:
        roi.EVIDENCE_DIR = original
    dumped = json.dumps(summary, sort_keys=True)
    for banned in ("interaction_id", "CUST-", '"1"', "customer_id"):
        assert banned not in dumped, banned
    report = roi.render_report(summary)
    assert "does not separate dispute calls" in report
    assert "advisor-hour cost is assumed" in report
