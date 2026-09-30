from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from app.orchestrator.types import Candidate, TransactionStatus


class HitOutcome(StrEnum):
    EXPLAIN = "explain"
    HANDOFF = "handoff"
    ALLOW = "allow"
    OFFER = "offer"


class Intent(StrEnum):
    CHARGE = "charge"
    DISPUTE = "dispute"
    OUT_OF_SCOPE = "out_of_scope"
    PERSON = "person"
    MISSING = "missing"


@dataclass(frozen=True)
class Threshold:
    value: str | None
    provisional: bool
    decision: int | None = None


@dataclass(frozen=True)
class CountryPolicy:
    country: str
    currency: str
    demo_today: date
    window_days: int
    disputable: dict[str, bool]
    fraud_score: Threshold
    high_amount: Threshold
    staleness_days: Threshold
    mandatory_fields: tuple[str, ...] = ()
    synthetic: bool = True


@dataclass(frozen=True)
class PolicyRequest:
    intent: Intent
    country: str
    today: date
    candidate: Candidate | None = None
    clarification_count: int = 0
    person_asks: int = 0
    states_not_theirs: bool = False
    policy: CountryPolicy | None = None


@dataclass(frozen=True)
class PolicyHit:
    outcome: HitOutcome
    rule_id: str
    provisional: bool = False


def evaluate(request: PolicyRequest) -> PolicyHit:
    if request.policy is None or request.policy.country != request.country:
        return PolicyHit(HitOutcome.HANDOFF, "country.unknown")
    policy = request.policy
    if request.person_asks >= 2 or (
        request.intent is Intent.PERSON and request.person_asks >= 2
    ):
        return PolicyHit(HitOutcome.HANDOFF, "person.insist")
    if request.intent is Intent.PERSON and request.person_asks >= 2:
        return PolicyHit(HitOutcome.HANDOFF, "person.insist")
    fraud = _fraud(request, policy)
    if fraud is not None:
        return fraud
    amount = _amount(request, policy)
    if amount is not None:
        return amount
    candidate = request.candidate
    if candidate is not None and not policy.disputable.get(candidate.status.value, False):
        return PolicyHit(HitOutcome.EXPLAIN, f"status.{candidate.status.value.lower()}")
    if candidate is not None and _expired(candidate, request.today, policy.window_days):
        return PolicyHit(HitOutcome.EXPLAIN, "window.expired")
    if candidate is not None and candidate.is_disputed:
        return PolicyHit(HitOutcome.EXPLAIN, "already.disputed")
    if request.clarification_count > 0 and policy.mandatory_fields:
        return PolicyHit(HitOutcome.HANDOFF, "fields.missing")
    if request.person_asks == 1 or request.intent is Intent.PERSON:
        return PolicyHit(HitOutcome.OFFER, "person.ask")
    if candidate is not None and candidate.status is TransactionStatus.APPROVED:
        return PolicyHit(HitOutcome.ALLOW, "status.approved")
    return PolicyHit(HitOutcome.EXPLAIN, "no.candidate")


def _fraud(request: PolicyRequest, policy: CountryPolicy) -> PolicyHit | None:
    threshold = policy.fraud_score
    if threshold.value is None:
        return None
    score = None if request.candidate is None else request.candidate.fraud_score
    if request.states_not_theirs or (score is not None and score > float(threshold.value)):
        return PolicyHit(HitOutcome.HANDOFF, "fraud.score", threshold.provisional)
    return None


def _amount(request: PolicyRequest, policy: CountryPolicy) -> PolicyHit | None:
    threshold = policy.high_amount
    candidate = request.candidate
    if threshold.value is None or candidate is None:
        return None
    if candidate.currency != policy.currency:
        return None
    if Decimal(candidate.amount) > Decimal(threshold.value):
        return PolicyHit(HitOutcome.HANDOFF, "amount.high", threshold.provisional)
    return None


def _expired(candidate: Candidate, today: date, window_days: int) -> bool:
    age = (today - date.fromisoformat(candidate.date)).days
    return age > window_days
