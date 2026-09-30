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
