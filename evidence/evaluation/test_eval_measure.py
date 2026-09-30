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
