from datetime import date
from decimal import Decimal

from app.orchestrator.types import Candidate, TransactionStatus
from app.policy.engine import (
    CountryPolicy,
    HitOutcome,
    Intent,
    PolicyRequest,
    Threshold,
    evaluate,
)


def _policy(**overrides: object) -> CountryPolicy:
    base = CountryPolicy(
        country="MX",
        currency="MXN",
        demo_today=date(2024, 12, 30),
        window_days=90,
        disputable={
            "Approved": True,
            "Pending": False,
            "Reversed": False,
            "Declined": False,
        },
        fraud_score=Threshold(None, True, 25),
        high_amount=Threshold(None, True, 26),
        staleness_days=Threshold(None, True, 27),
    )
    return CountryPolicy(**{**base.__dict__, **overrides})


def _charge(status: TransactionStatus, when: str = "2024-10-01", amount: str = "10") -> Candidate:
    return Candidate(
        "c1",
        status,
        amount,
        "MXN",
        "ACME",
        when,
        "2024-10-02",
    )


def _request(**kwargs: object) -> PolicyRequest:
    policy = kwargs.pop("policy", _policy())
    return PolicyRequest(
        intent=kwargs.pop("intent", Intent.CHARGE),
        country=kwargs.pop("country", "MX"),
        today=kwargs.pop("today", date(2024, 12, 30)),
        policy=policy,
        **kwargs,
    )


def test_insist_beats_reversed_status() -> None:
    hit = evaluate(
        _request(
            intent=Intent.PERSON,
            person_asks=2,
            candidate=_charge(TransactionStatus.REVERSED),
        )
    )
    assert hit.rule_id == "person.insist"
    assert hit.outcome is HitOutcome.HANDOFF


def test_day_90_does_not_expire() -> None:
    hit = evaluate(
        _request(
            today=date(2024, 12, 30),
            candidate=_charge(TransactionStatus.APPROVED, "2024-10-01"),
        )
    )
    assert hit.rule_id != "window.expired"
    assert hit.outcome is HitOutcome.ALLOW


def test_day_91_expires() -> None:
    hit = evaluate(
        _request(
            today=date(2024, 12, 31),
            candidate=_charge(TransactionStatus.APPROVED, "2024-10-01"),
        )
    )
    assert hit.rule_id == "window.expired"
    assert hit.outcome is HitOutcome.EXPLAIN


def test_null_threshold_does_not_fire() -> None:
    hit = evaluate(
        _request(candidate=_charge(TransactionStatus.APPROVED, amount="999999"))
    )
    assert hit.rule_id != "amount.high"
    assert hit.outcome is HitOutcome.ALLOW


def test_amount_equal_to_threshold_does_not_fire() -> None:
    policy = _policy(high_amount=Threshold("100", True, 26))
    hit = evaluate(
        _request(policy=policy, candidate=_charge(TransactionStatus.APPROVED, amount="100"))
    )
    assert hit.rule_id != "amount.high"


def test_unknown_country_is_not_allow() -> None:
    hit = evaluate(_request(country="PE", policy=None))
    assert hit.outcome is not HitOutcome.ALLOW
    assert hit.rule_id == "country.unknown"


def test_gold_hint_loses() -> None:
    charge = _charge(TransactionStatus.APPROVED, "2024-10-01")
    charge = Candidate(
        charge.candidate_id,
        charge.status,
        charge.amount,
        charge.currency,
        charge.merchant,
        charge.date,
        charge.as_of,
        gold_eligible=True,
    )
    hit = evaluate(_request(today=date(2024, 12, 31), candidate=charge))
    assert hit.rule_id == "window.expired"
    assert Decimal("91") > 90


def _priced(currency: str, amount: str = "10", score: float | None = None) -> Candidate:
    return Candidate("c1", TransactionStatus.APPROVED, amount, currency, "ACME", "2024-12-01", "2024-12-02", score)


def _per_currency(**limits: str) -> Threshold:
    return Threshold(None, True, 26, values=tuple(sorted(limits.items())), source="evidence/evaluation/2024Q4-v2/summary.json")


def test_usd_charge_on_mexican_account_uses_usd_limit() -> None:
    policy = _policy(high_amount=_per_currency(MXN="100000", USD="5000"))
    hit = evaluate(_request(policy=policy, candidate=_priced("USD", amount="6000")))
    assert hit.rule_id == "amount.high"
    assert hit.outcome is HitOutcome.HANDOFF


def test_fraud_score_is_compared_per_currency() -> None:
    policy = _policy(fraud_score=Threshold(None, True, 25, values=(("MXN", "40"), ("USD", "28.5"))))
    assert evaluate(_request(policy=policy, candidate=_priced("USD", score=30.0))).rule_id == "fraud.score"
    assert evaluate(_request(policy=policy, candidate=_priced("MXN", score=30.0))).rule_id != "fraud.score"


def test_currency_without_a_value_does_not_fire() -> None:
    policy = _policy(
        fraud_score=Threshold(None, True, 25, values=(("USD", "28.5"),)),
        high_amount=_per_currency(USD="5000"),
    )
    hit = evaluate(_request(policy=policy, candidate=_priced("MXN", amount="999999", score=99.0)))
    assert hit.rule_id not in ("fraud.score", "amount.high")
    assert hit.outcome is HitOutcome.ALLOW


def test_per_currency_value_equal_does_not_fire() -> None:
    policy = _policy(high_amount=_per_currency(USD="5000"), fraud_score=Threshold(None, True, 25, values=(("USD", "28.5"),)))
    hit = evaluate(_request(policy=policy, candidate=_priced("USD", amount="5000", score=28.5)))
    assert hit.outcome is HitOutcome.ALLOW


def test_loader_reads_per_currency_values(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.policy.load import CONFIG_DIR, load_country

    text = (CONFIG_DIR / "mx.yaml").read_text(encoding="utf-8").replace(
        "  high_amount:\n    value: null\n",
        '  high_amount:\n    values:\n      USD: "5000"\n      MXN: null\n    source: "Bank policy X v3"\n',
    )
    (tmp_path / "mx.yaml").write_text(text, encoding="utf-8")
    policy = load_country("MX", tmp_path)
    assert policy is not None
    assert policy.high_amount.values == (("USD", "5000"),)
    assert policy.high_amount.source == "Bank policy X v3"
    assert policy.high_amount.limit_for("USD", "MXN") == "5000"
    assert policy.high_amount.limit_for("MXN", "MXN") is None
