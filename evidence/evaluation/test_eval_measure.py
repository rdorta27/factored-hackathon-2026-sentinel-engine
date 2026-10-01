"""Unit checks for the evaluation evidence script (synthetic data only)."""

import csv
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import eval_measure as m

COMPLAINT_FIELDS = [
    "complaint_id", "creation_date", "process_date", "customer_id", "case_type",
    "category", "subcategory", "reception_channel", "description",
    "claimed_amount", "currency", "priority", "status",
]
INTERACTION_FIELDS = [
    "interaction_id", "interaction_date", "process_date", "contact_reason",
    "was_escalated", "was_resolved", "requires_followup",
]
TRANSACTION_FIELDS = [
    "transaction_id", "transaction_date", "process_date", "amount",
    "currency", "transaction_country", "fraud_score",
]


def _write(base: str, rel: str, fields: list, rows: list) -> None:
    path = os.path.join(base, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def data_dir() -> str:
    tmp = tempfile.mkdtemp()
    _write(tmp, "complaints/year=2024/month=10/day=01/a.csv", COMPLAINT_FIELDS, [
        {"complaint_id": "C1", "creation_date": "2024-10-05", "process_date": "2024-10-05",
         "customer_id": "X", "case_type": "Claim", "category": "Cargo no reconocido",
         "subcategory": "Cargo no reconocido", "reception_channel": "Web",
         "description": "cargo no reconocido en tarjeta", "claimed_amount": "1000.00",
         "currency": "MXN", "priority": "High", "status": "Open"},
    ])
    _write(tmp, "complaints/year=2024/month=11/day=01/a.csv", COMPLAINT_FIELDS, [
        {"complaint_id": "C2", "creation_date": "2024-11-05", "process_date": "2024-11-05",
         "customer_id": "X", "case_type": "Claim", "category": "Cargo duplicado",
         "subcategory": "", "reception_channel": "App", "description": "duplicado",
         "claimed_amount": "2500.00", "currency": "MXN", "priority": "Low", "status": "Closed"},
    ])
    _write(tmp, "complaints/year=2024/month=12/day=01/a.csv", COMPLAINT_FIELDS, [
        {"complaint_id": "C3", "creation_date": "2024-12-05", "process_date": "2024-12-05",
         "customer_id": "X", "case_type": "Complaint", "category": "Atencion",
         "subcategory": "Demora", "reception_channel": "Email", "description": "demora atencion",
         "claimed_amount": "", "currency": "", "priority": "Medium", "status": "Open"},
    ])
    _write(tmp, "call_center_interactions/year=2024/month=10/day=01/a.csv", INTERACTION_FIELDS, [
        {"interaction_id": "I1", "interaction_date": "2024-10-06", "process_date": "2024-10-06",
         "contact_reason": "Transaccional", "was_escalated": "True",
         "was_resolved": "True", "requires_followup": "False"},
    ])
    _write(tmp, "call_center_interactions/year=2024/month=11/day=01/a.csv", INTERACTION_FIELDS, [
        {"interaction_id": "I2", "interaction_date": "2024-11-06", "process_date": "2024-11-06",
         "contact_reason": "Reclamo", "was_escalated": "False",
         "was_resolved": "False", "requires_followup": "True"},
    ])
    _write(tmp, "transactions/year=2024/month=10/day=01/a.csv", TRANSACTION_FIELDS, [
        {"transaction_id": "T1", "transaction_date": "2024-10-07", "process_date": "2024-10-07",
         "amount": "100.00", "currency": "MXN", "transaction_country": "MX", "fraud_score": "12"},
    ])
    _write(tmp, "transactions/year=2024/month=11/day=01/a.csv", TRANSACTION_FIELDS, [
        {"transaction_id": "T2", "transaction_date": "2024-11-07", "process_date": "2024-11-07",
         "amount": "200.00", "currency": "MXN", "transaction_country": "MX", "fraud_score": "80"},
    ])
    return tmp


def test_full_counter_and_mix_present(data_dir: str) -> None:
    summary = m.compute_summary(data_dir, "2024Q4")
    assert len(summary["labels"]["claim"]) == 2
    assert summary["labels"]["claim_n"] == 2
    assert summary["label_quality"]["null_subcategory"] == 1
    assert set(summary["mix"]) == {"by_month", "by_country", "by_channel", "by_priority", "by_status"}
    assert set(summary["intent_mix"]["contact_reason"]) == {"Transaccional", "Reclamo"}
    assert summary["intent_mix"]["was_escalated"]["denominator"] == 2
    assert "MX" in summary["thresholds"]
    assert summary["thresholds"]["MX"]["currency"] == "MXN"


def test_planted_identifier_fails_guard(data_dir: str) -> None:
    summary = m.compute_summary(data_dir, "2024Q4")
    m.guard_summary(summary)
    bad = json.loads(json.dumps(summary))
    bad["mix"]["by_channel"]["CUST-0001"] = 1
    with pytest.raises(SystemExit, match="guard"):
        m.guard_summary(bad)


def test_verify_names_mismatched_field(data_dir: str, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(m, "BASE", str(tmp_path))
    monkeypatch.setattr(m, "find_data", lambda: data_dir)
    m.do_run("2024Q4-v9", "2024Q4")
    summary_path = tmp_path / "2024Q4-v9" / "summary.json"
    body = json.loads(summary_path.read_text(encoding="utf-8"))
    body["mix"]["by_month"]["2099-01"] = 1
    summary_path.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(SystemExit, match="verify failed"):
        m.do_verify("2024Q4-v9")


def test_derive_records_provenance(data_dir: str, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(m, "BASE", str(tmp_path))
    monkeypatch.setattr(m, "find_data", lambda: data_dir)
    m.do_run("2024Q4-v9", "2024Q4")
    m.do_verify("2024Q4-v9")
    m.do_derive("2024Q4-v9")
    labels_path = os.path.join(
        os.path.dirname(os.path.dirname(str(tmp_path))), "sentinel-ai-core", "eval", "labels.json"
    )
    assert os.path.isfile(labels_path)
    body = json.loads(open(labels_path, encoding="utf-8").read())
    assert body["run_id"] == "2024Q4-v9"
    assert body["summary_sha16"]


def _silver_db(path: str) -> None:
    duckdb = pytest.importorskip("duckdb")
    con = duckdb.connect(path)
    con.execute("CREATE TABLE silver_customers (customer_id VARCHAR, country VARCHAR)")
    con.execute("INSERT INTO silver_customers VALUES ('A', 'México'), ('B', 'Mexico'), ('C', 'Colombia')")
    con.execute(
        "CREATE TABLE silver_transactions (customer_id VARCHAR, transaction_date TIMESTAMP, "
        "amount DOUBLE, currency VARCHAR, fraud_score DOUBLE, amount_usd DOUBLE, transaction_country VARCHAR)"
    )
    rows = []
    for i in range(120):
        rows.append(("A", "2024-10-10", 100.0 + i, "USD", 10.0 + i / 10, None, "Brazil"))
        rows.append(("C", "2024-11-10", 1000.0 + i, "COP", 20.0, 1.0, "Colombia"))
    rows += [("A", "2024-11-11", 5.0, "MXN", 1.0, None, "México"), ("B", "2024-12-01", 7.0, "USD", 2.0, 7.0, "México")]
    rows.append(("C", "2025-07-02", 999999.0, "COP", 99.0, None, "Colombia"))  # held-out, excluded
    con.executemany("INSERT INTO silver_transactions VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    con.execute("CREATE TABLE silver_products (customer_id VARCHAR, currency VARCHAR)")
    con.execute("INSERT INTO silver_products VALUES ('A', 'USD'), ('A', 'MXN'), ('C', 'COP')")
    con.close()


def test_account_thresholds_split_currencies(tmp_path) -> None:  # type: ignore[no-untyped-def]
    db = str(tmp_path / "gold_bank.duckdb")
    _silver_db(db)
    out = m.account_thresholds(db, "2024-10-01", "2025-01-01")
    mx = out["groups"]["México"]
    assert set(mx) == {"USD", "MXN"}
    assert mx["USD"]["n"] == 121 and mx["USD"]["amount"]["p95"] is not None
    assert mx["MXN"]["below_minimum"] is True and mx["MXN"]["amount"] is None
    assert out["country_normalized"] == 1
    assert out["groups"]["Colombia"]["COP"]["n"] == 120
    assert "Brazil" not in out["groups"]
    assert out["product_currency"]["México"]["by_currency"] == {"USD": 1, "MXN": 1}
    m.guard_summary(out)


def test_run_includes_account_thresholds_and_verifies(data_dir: str, tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    db = str(tmp_path / "gold_bank.duckdb")
    _silver_db(db)
    monkeypatch.setenv(m.DUCKDB_ENV, db)
    monkeypatch.setattr(m, "BASE", str(tmp_path))
    monkeypatch.setattr(m, "find_data", lambda: data_dir)
    m.do_run("2024Q4-v9", "2024Q4")
    body = json.loads((tmp_path / "2024Q4-v9" / "summary.json").read_text(encoding="utf-8"))
    assert "México" in body["account_thresholds"]["groups"]
    m.do_verify("2024Q4-v9")
