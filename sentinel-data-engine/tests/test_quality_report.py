"""Tests for the fully generated data quality report (quality-report change).

Covers Task 1 (all sections generated from collectors) and Task 2 (verify mode).

Strategy: build a tiny raw CSV fixture, run LocalPipelineRunner end to end
into a temp DuckDB file, and assert the report keeps every required section
on rerun. A second test tampers with a figure and expects verify to fail.
"""

from __future__ import annotations

import csv
from pathlib import Path

from sentinel_data.local_runner import LocalPipelineRunner


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _minimal_fixture(raw_dir: Path) -> None:
    """Create small CSVs covering all Silver tables plus quarantine/orphan/late/null cases."""
    _write_csv(
        raw_dir / "customers.csv",
        [
            {
                "customer_id": "C001", "first_name": "Ana", "last_name": "Lopez",
                "document_type": "DNI", "document_number": "1", "date_of_birth": "1990-01-01",
                "gender": "F", "city": "CDMX", "state": "CDMX", "country": "Mexico",
                "segment": "BASIC", "customer_status": "ACTIVE", "detected_accent": "es-MX",
                "registration_date": "2024-01-01", "registration_branch_id": "B1",
                "last_updated": "2026-01-01", "accepts_marketing": "true",
                "credit_score": "700", "estimated_monthly_income": "1000",
            },
            {
                "customer_id": "C002", "first_name": "Luis", "last_name": "Gomez",
                "document_type": "DNI", "document_number": "2", "date_of_birth": "1991-02-02",
                "gender": "M", "city": "Bogota", "state": "DC", "country": "Colombia",
                "segment": "BASIC", "customer_status": "ACTIVE", "detected_accent": "es-CO",
                "registration_date": "2024-01-02", "registration_branch_id": "B1",
                "last_updated": "2026-01-02", "accepts_marketing": "false",
                "credit_score": "650", "estimated_monthly_income": "900",
            },
        ],
    )
    _write_csv(
        raw_dir / "products.csv",
        [
            {
                "product_id": "P001", "customer_id": "C001", "product_type": "CHECKING",
                "product_number": "N1", "product_status": "ACTIVE", "currency": "MXN",
                "current_balance": "100", "credit_limit": "1000", "interest_rate": "0.1",
                "opening_date": "2024-01-01", "expiration_date": "2030-01-01",
                "opening_branch_id": "B1", "opening_channel": "APP",
                "has_linked_app": "true", "days_past_due": "0", "last_updated": "2026-01-01",
            },
        ],
    )
    _write_csv(
        raw_dir / "transactions.csv",
        [
            # Valid row, late arrival (process_date > transaction_date).
            {
                "transaction_id": "T001", "transaction_date": "2026-06-07",
                "process_date": "2026-06-10", "product_id": "P001", "customer_id": "C001",
                "transaction_type": "PURCHASE", "transaction_category": "Food",
                "amount": "100", "currency": "MXN", "amount_usd": "5",
                "channel": "APP", "branch_id": "B1", "transaction_country": "Mexico",
                "transaction_status": "COMPLETED", "is_fraud": "false",
                "fraud_score": "1.0", "merchant_name": "MerchX", "merchant_category": "RETAIL",
            },
            # Duplicate of T001 (dedup check: Bronze 4 rows, Silver fewer).
            {
                "transaction_id": "T001", "transaction_date": "2026-06-07",
                "process_date": "2026-06-10", "product_id": "P001", "customer_id": "C001",
                "transaction_type": "PURCHASE", "transaction_category": "Food",
                "amount": "100", "currency": "MXN", "amount_usd": "5",
                "channel": "APP", "branch_id": "B1", "transaction_country": "Mexico",
                "transaction_status": "COMPLETED", "is_fraud": "false",
                "fraud_score": "1.0", "merchant_name": "MerchX", "merchant_category": "RETAIL",
            },
            # Orphan (unknown customer) + invalid amount (quarantine).
            {
                "transaction_id": "T002", "transaction_date": "2026-06-08",
                "process_date": "2026-06-08", "product_id": "P001", "customer_id": "C999",
                "transaction_type": "PURCHASE", "transaction_category": "",
                "amount": "", "currency": "MXN", "amount_usd": "",
                "channel": "APP", "branch_id": "B1", "transaction_country": "México",
                "transaction_status": "COMPLETED", "is_fraud": "false",
                "fraud_score": "", "merchant_name": "", "merchant_category": "",
            },
            # Null optional merchant_name (null-visibility check).
            {
                "transaction_id": "T003", "transaction_date": "2026-06-08",
                "process_date": "2026-06-08", "product_id": "P001", "customer_id": "C001",
                "transaction_type": "PURCHASE", "transaction_category": "Food",
                "amount": "50", "currency": "MXN", "amount_usd": "2.5",
                "channel": "APP", "branch_id": "B1", "transaction_country": "México",
                "transaction_status": "COMPLETED", "is_fraud": "false",
                "fraud_score": "0.5", "merchant_name": "", "merchant_category": "RETAIL",
            },
        ],
    )
    _write_csv(
        raw_dir / "complaints.csv",
        [
            {
                "complaint_id": "K001", "process_date": "2026-06-09",
                "customer_id": "C001", "affected_product_id": "P001",
                "assigned_agent_id": "A001", "origin_interaction_id": "I001",
                "creation_date": "2026-06-08", "resolution_date": "",
                "closing_date": "", "case_type": "DISPUTE", "category": "CHARGE",
                "subcategory": "DUP", "reception_channel": "APP",
                "description": "dup charge", "priority": "HIGH", "status": "OPEN",
                "sla_breached": "false", "resolution": "",
                "claimed_amount": "100", "currency": "MXN",
                "compensation_granted": "false", "is_repeat_complainer": "false",
            },
        ],
    )
    _write_csv(
        raw_dir / "service_agents.csv",
        [
            {
                "agent_id": "A001", "first_name": "Maria", "last_name": "Ruiz",
                "agent_type": "SPECIALIST", "experience_level": "SENIOR",
                "languages": "es", "native_accent": "es-MX",
                "country_of_origin": "Mexico", "agent_status": "ACTIVE",
                "work_shift": "DAY", "hire_date": "2023-01-01", "avg_csat": "4.5",
                "employee_code": "E001", "email": "m@example.com",
            },
        ],
    )
    _write_csv(
        raw_dir / "call_center_interactions.csv",
        [
            {
                "interaction_id": "I001", "process_date": "2026-06-09",
                "customer_id": "C001", "agent_id": "A001",
                "interaction_date": "2026-06-08", "interaction_type": "CALL",
                "channel": "PHONE", "contact_reason": "charge",
                "reason_category": "DISPUTE", "duration_seconds": "120",
                "wait_time_seconds": "10", "sentiment_score": "0.2",
                "was_escalated": "false", "was_resolved": "true",
                "requires_followup": "false", "has_transcript": "false",
                "has_recording": "true", "detected_sentiment": "NEUTRAL",
            },
            # Second row with missing optional duration (null-visibility).
            {
                "interaction_id": "I002", "process_date": "2026-06-09",
                "customer_id": "C002", "agent_id": "A001",
                "interaction_date": "2026-06-09", "interaction_type": "CALL",
                "channel": "PHONE", "contact_reason": "info",
                "reason_category": "INFO", "duration_seconds": "",
                "wait_time_seconds": "", "sentiment_score": "",
                "was_escalated": "false", "was_resolved": "true",
                "requires_followup": "false", "has_transcript": "false",
                "has_recording": "false", "detected_sentiment": "NEUTRAL",
            },
        ],
    )
    _write_csv(
        raw_dir / "satisfaction_surveys.csv",
        [
            {
                "survey_id": "S001", "process_date": "2026-06-10",
                "customer_id": "C001", "interaction_id": "I001", "agent_id": "A001",
                "survey_date": "2026-06-09", "survey_type": "CSAT",
                "send_channel": "APP", "main_score": "8",
                "open_comments": "ok", "nps_category": "PASSIVE",
            },
        ],
    )


def _run_fixture(tmp_path: Path) -> tuple[Path, Path]:
    raw_dir = tmp_path / "raw"
    duckdb_path = tmp_path / "gold.duckdb"
    report_path = tmp_path / "report.md"
    _minimal_fixture(raw_dir)
    LocalPipelineRunner(
        raw_dir=raw_dir, duckdb_path=duckdb_path, report_path=report_path
    ).run()
    return duckdb_path, report_path


def test_full_report_keeps_all_sections_on_rerun(tmp_path: Path) -> None:
    """Default-path rerun must keep every generated section (no hand text)."""
    raw_dir = tmp_path / "raw"
    duckdb_path = tmp_path / "gold.duckdb"
    report_path = tmp_path / "report.md"
    _minimal_fixture(raw_dir)

    runner = LocalPipelineRunner(
        raw_dir=raw_dir, duckdb_path=duckdb_path, report_path=report_path
    )
    runner.run()
    first = report_path.read_text(encoding="utf-8")

    # Rerun with the default report path keeps all sections.
    runner.run()
    second = report_path.read_text(encoding="utf-8")

    for section in [
        "## 1. Volume Summary",
        "### Drop breakdown",
        "Quarantine per rule",
        "## 2. Orphans & Late Arrivals",
        "### Late arrivals per partitioned table",
        "## 3. Nulls & Country Normalisation",
        "### Null counts and rates",
        "## 4. PII Compliance Verification",
        "```json figures",
    ]:
        assert section in first, f"Missing section in first run: {section}"
        assert section in second, f"Section lost on rerun: {section}"


def test_collectors_cover_quarantine_orphans_late_and_nulls(tmp_path: Path) -> None:
    """Quarantine, orphans, late arrivals and optional nulls are visible."""
    _, report_path = _run_fixture(tmp_path)
    text = report_path.read_text(encoding="utf-8")

    # Quarantine per rule names at least one failed catalog rule.
    assert "Quarantine per rule" in text
    # Orphan check for the C999 transaction.
    assert "transactions_missing_customer" in text
    # Late arrival for T001 (process 06-10 > event 06-07).
    assert "Late arrivals" in text
    # Optional nulls visible (merchant_name has empty values).
    assert "merchant_name" in text


def test_verify_passes_then_fails_on_changed_figure(tmp_path: Path) -> None:
    """Verify recomputes figures and fails naming the differing figure."""
    duckdb_path, report_path = _run_fixture(tmp_path)
    runner = LocalPipelineRunner(
        raw_dir=tmp_path / "raw", duckdb_path=duckdb_path, report_path=report_path
    )
    assert runner.verify() == {}

    # Tamper with one figure in the committed report.
    text = report_path.read_text(encoding="utf-8")
    tampered = text.replace('"quarantine.total":', '"quarantine.totalX":', 1)
    assert tampered != text
    report_path.write_text(tampered, encoding="utf-8")

    mismatches = runner.verify()
    assert mismatches, "Expected verify to fail after tampering with a figure"
