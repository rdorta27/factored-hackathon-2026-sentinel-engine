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
