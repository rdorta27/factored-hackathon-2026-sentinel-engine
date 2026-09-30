from app.orchestrator.types import TransactionStatus
from app.policy.engine import PolicyFacts, PolicyOutcome, evaluate


def test_reversed_blocks_dispute() -> None:
    outcome = evaluate(PolicyFacts(status=TransactionStatus.REVERSED))
    assert outcome is PolicyOutcome.EXPLAIN_STATUS


def test_person_request_hands_off() -> None:
    outcome = evaluate(
        PolicyFacts(status=TransactionStatus.APPROVED, asks_for_person=True)
    )
    assert outcome is PolicyOutcome.HANDOFF


def test_missing_amount_threshold_is_not_a_rule() -> None:
    outcome = evaluate(
        PolicyFacts(
            status=TransactionStatus.APPROVED,
            amount="999999",
            amount_threshold=None,
        )
    )
    assert outcome is PolicyOutcome.ALLOW
