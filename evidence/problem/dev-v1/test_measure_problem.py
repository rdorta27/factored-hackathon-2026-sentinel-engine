"""Unit checks for the problem-evidence script (synthetic fixture only)."""

import csv
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

import measure_problem as m

FIELDS = [
    "interaction_id", "interaction_date", "process_date", "contact_reason",
    "reason_category", "duration_seconds", "was_resolved",
]


def _write(base, rel, rows):
    path = os.path.join(base, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def data_dir(tmp_path):
    root = str(tmp_path)
    _write(root, "call_center_interactions/year=2023/month=06/day=17/a.csv", [
        {"interaction_id": "I1", "interaction_date": "2023-06-17 10:00:00",
         "process_date": "2023-06-17", "contact_reason": "Transaccional",
         "reason_category": "Transaccional", "duration_seconds": "120", "was_resolved": "True"},
        {"interaction_id": "I2", "interaction_date": "2023-06-17 11:00:00",
         "process_date": "2023-06-17", "contact_reason": "Transaccional",
         "reason_category": "Transaccional", "duration_seconds": "60", "was_resolved": "False"},
    ])
    _write(root, "call_center_interactions/year=2023/month=06/day=18/a.csv", [
        {"interaction_id": "I3", "interaction_date": "2023-06-18 09:00:00",
         "process_date": "2023-06-18", "contact_reason": "Queja",
         "reason_category": "Queja", "duration_seconds": "300", "was_resolved": "True"},
        {"interaction_id": "I4", "interaction_date": "2023-06-18 09:30:00",
         "process_date": "2023-06-18", "contact_reason": "Producto",
         "reason_category": "Producto", "duration_seconds": "", "was_resolved": "True"},
        {"interaction_id": "I5", "interaction_date": "2023-06-18 10:00:00",
         "process_date": "2023-06-18", "contact_reason": "Técnico",
         "reason_category": "Técnico", "duration_seconds": "180", "was_resolved": "False"},
    ])
    # A held-out row sits in a development partition (the one-day offset).
    _write(root, "call_center_interactions/year=2025/month=06/day=30/a.csv", [
        {"interaction_id": "I6", "interaction_date": "2025-07-01 10:00:00",
         "process_date": "2025-06-30", "contact_reason": "Transaccional",
         "reason_category": "Transaccional", "duration_seconds": "100", "was_resolved": "True"},
    ])
    return root


def test_workflow_of_maps_known_and_unknown():
    assert m.workflow_of("Transaccional") == "account_or_payment_inquiry"
    assert m.workflow_of("Queja") == "transaction_dispute"
    assert m.workflow_of("Producto") == "card_support"
    assert m.workflow_of("Técnico") == "other"
    assert m.workflow_of("unknown") == "other"
    assert m.workflow_of(None) == "other"


def test_wilson_bounds_and_edges():
    lo, hi = m.wilson(50, 100)
    assert 40 < lo < 50 < hi < 60
    assert m.wilson(0, 0) == [None, None]
    lo0, hi0 = m.wilson(0, 10)
    assert lo0 == 0.0 and 0 < hi0 < 100


def test_percentile_and_bootstrap_are_deterministic():
    values = list(range(1, 101))
    assert m.percentile(values, 95) == 95
    assert m.percentile([], 95) is None
    first = m.bootstrap_ci(values, 95, n_boot=100)
    second = m.bootstrap_ci(values, 95, n_boot=100)
    assert first == second
    assert first[0] <= first[1]


def test_compute_summary_on_fixture(data_dir, monkeypatch):
    monkeypatch.setattr(m, "BOOTSTRAP", 50)
    out = m.compute_summary(data_dir)
    assert out["totals"]["calls"] == 5
    assert out["totals"]["excluded_heldout"] == 1
    assert out["reasons"]["Transaccional"]["n"] == 2
    assert out["reasons"]["Transaccional"]["resolved"] == 1
    assert out["reasons"]["Transaccional"]["share_pct"] == 50.0
    assert out["reasons"]["Transaccional"]["workflow"] == "account_or_payment_inquiry"
    assert out["demand"]["account_or_payment_inquiry"]["calls"] == 2
    assert out["demand"]["transaction_dispute"]["calls"] == 1
    assert out["demand"]["credit_information"]["calls"] == 0
    assert out["demand"]["account_or_payment_inquiry"]["highest_day"] == 2
    assert out["hours"]["account_or_payment_inquiry"]["mean_minutes"] == 1.5
    assert out["hours"]["card_support"]["missing_duration"] == 1
    assert out["hours"]["transaction_dispute"]["rank"] == 1
    assert out["hours"]["account_or_payment_inquiry"]["rank"] == 2
    assert out["hours"]["other"]["rank"] is None
    assert out["missing"]["duration_seconds"]["missing"] == 1
    assert out["missing"]["contact_reason"]["missing"] == 0
    assert set(out["mapping"]) == {"Transaccional", "Producto", "Queja",
                                   "Técnico", "Comercial", "Retención"}
