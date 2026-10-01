from app.policy.engine import HitOutcome, Intent, PolicyRequest
from app.policy.load import load_country
from datetime import date


def test_loads_mx_and_missing_file_is_not_allow() -> None:
    mx = load_country("MX")
    assert mx is not None
    assert mx.currency == "MXN"
    assert mx.mandatory_fields == ()
    assert mx.high_amount.value is None
    assert mx.high_amount.provisional is True
    assert load_country("BR") is None
    hit = PolicyRequest(Intent.CHARGE, "BR", date(2026, 6, 17), policy=None)
    from app.policy.engine import evaluate

    assert evaluate(hit).outcome is not HitOutcome.ALLOW


def test_threshold_values_match_their_evidence() -> None:
    import json
    import re
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    countries = {"MX": "México", "CO": "Colombia", "AR": "Argentina"}
    rules = (("fraud_score", "fraud_score"), ("high_amount", "amount"))
    for code, name in countries.items():
        policy = load_country(code)
        assert policy is not None
        for attr, metric in rules:
            threshold = getattr(policy, attr)
            assert threshold.values, f"{code} {attr} has no values"
            source = threshold.source or ""
            if source.startswith("evidence/"):
                groups = json.loads((repo / source).read_text(encoding="utf-8"))["account_thresholds"]["groups"][name]
                for currency, limit in threshold.values:
                    assert groups[currency]["below_minimum"] is False
                    assert float(limit) == groups[currency][metric]["p95"], (code, attr, currency)
            else:  # a bank policy reference: format only
                for currency, limit in threshold.values:
                    assert re.fullmatch(r"[A-Z]{3}", currency) and float(limit) > 0


def test_mexican_mxn_has_no_threshold() -> None:
    mx = load_country("MX")
    assert mx is not None
    assert mx.fraud_score.limit_for("MXN", mx.currency) is None
    assert mx.high_amount.limit_for("MXN", mx.currency) is None
    assert mx.high_amount.limit_for("USD", mx.currency) is not None


def test_every_configured_threshold_has_a_demo_row_above_it() -> None:
    from app.tools.gold import MockGoldStore

    rows = MockGoldStore("2026-06-17")._rows.values()
    customers = {"MX": "CUST-0001", "CO": "CUST-0002", "AR": "CUST-0003"}
    for code, customer in customers.items():
        policy = load_country(code)
        assert policy is not None
        own = [row for row in rows if row.customer_id == customer]
        for currency, limit in policy.high_amount.values:
            assert any(r.currency == currency and float(r.amount) > float(limit) for r in own), (code, currency)
        for currency, limit in policy.fraud_score.values:
            assert any(
                r.currency == currency and r.fraud_score is not None and r.fraud_score > float(limit) for r in own
            ), (code, currency)
        assert {r.currency for r in own} == {policy.currency, "USD"}
