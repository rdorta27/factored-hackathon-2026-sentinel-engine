from datetime import date

from app.orchestrator.types import Candidate, TransactionStatus
from app.policy.engine import (
    CountryPolicy,
    HitOutcome,
    Intent,
    PolicyRequest,
    Threshold,
    evaluate,
)


def _policy() -> CountryPolicy:
    return CountryPolicy(
        country="MX",
        currency="MXN",
        demo_today=date(2024, 12, 1),
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


def _charge(status: TransactionStatus) -> Candidate:
    return Candidate("c1", status, "10", "MXN", "ACME", "2024-11-01", "2024-11-02")


def test_reversed_blocks_dispute() -> None:
    hit = evaluate(
        PolicyRequest(
            Intent.CHARGE,
            "MX",
            date(2024, 12, 1),
            _charge(TransactionStatus.REVERSED),
            policy=_policy(),
        )
    )
    assert hit.outcome is HitOutcome.EXPLAIN
    assert hit.rule_id == "status.reversed"


def test_person_request_hands_off_on_repeat() -> None:
    hit = evaluate(
        PolicyRequest(
            Intent.PERSON,
            "MX",
            date(2024, 12, 1),
            _charge(TransactionStatus.APPROVED),
            person_asks=2,
            policy=_policy(),
        )
    )
    assert hit.outcome is HitOutcome.HANDOFF


def test_missing_amount_threshold_is_not_a_rule() -> None:
    hit = evaluate(
        PolicyRequest(
            Intent.CHARGE,
            "MX",
            date(2024, 12, 1),
            Candidate("c1", TransactionStatus.APPROVED, "999999", "MXN", "ACME", "2024-11-01", "2024-11-02"),
            policy=_policy(),
        )
    )
    assert hit.outcome is HitOutcome.ALLOW
