from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.orchestrator.types import TransactionStatus


class PolicyOutcome(StrEnum):
    EXPLAIN_STATUS = "explain_status"
    HANDOFF = "handoff"
    ALLOW = "allow"


@dataclass(frozen=True)
class PolicyFacts:
    status: TransactionStatus
    asks_for_person: bool = False
    fraud_threshold: float | None = None
    fraud_score: float | None = None
    states_not_theirs: bool = False
    amount: str | None = None
    amount_threshold: str | None = None


def evaluate(facts: PolicyFacts) -> PolicyOutcome:
    if facts.status in (
        TransactionStatus.PENDING,
        TransactionStatus.REVERSED,
        TransactionStatus.DECLINED,
    ):
        return PolicyOutcome.EXPLAIN_STATUS
    if facts.asks_for_person:
        return PolicyOutcome.HANDOFF
    if facts.fraud_threshold is not None and (
        facts.states_not_theirs
        or (
            facts.fraud_score is not None
            and facts.fraud_score > facts.fraud_threshold
        )
    ):
        return PolicyOutcome.HANDOFF
    if (
        facts.amount_threshold is not None
        and facts.amount is not None
        and Decimal(facts.amount) > Decimal(facts.amount_threshold)
    ):
        return PolicyOutcome.HANDOFF
    if facts.status is TransactionStatus.APPROVED:
        return PolicyOutcome.ALLOW
    return PolicyOutcome.EXPLAIN_STATUS
