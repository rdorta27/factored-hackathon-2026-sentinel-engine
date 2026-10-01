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
    """One rule's limit. ``values`` maps a charge currency to its limit.

    A currency missing from ``values`` has no limit, so the rule does not fire
    for it. ``value`` is a single limit that applies to the file's own currency
    (used by staleness, which has no currency). ``source`` names where the
    numbers come from: an evidence run or a bank policy reference.
    """

    value: str | None
    provisional: bool
    decision: int | None = None
    values: tuple[tuple[str, str], ...] = ()
    source: str | None = None

    def limit_for(self, currency: str, file_currency: str) -> str | None:
        for code, limit in self.values:
            if code == currency:
                return limit
        if self.value is not None and currency == file_currency:
            return self.value
        return None


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
    candidate = request.candidate
    if request.states_not_theirs and threshold.value is not None:
        return PolicyHit(HitOutcome.HANDOFF, "fraud.score", threshold.provisional)
    if candidate is None or candidate.fraud_score is None:
        return None
    limit = threshold.limit_for(candidate.currency, policy.currency)
    if limit is not None and candidate.fraud_score > float(limit):
        return PolicyHit(HitOutcome.HANDOFF, "fraud.score", threshold.provisional)
    return None


def _amount(request: PolicyRequest, policy: CountryPolicy) -> PolicyHit | None:
    candidate = request.candidate
    if candidate is None:
        return None
    limit = policy.high_amount.limit_for(candidate.currency, policy.currency)
    if limit is not None and Decimal(candidate.amount) > Decimal(limit):
        return PolicyHit(HitOutcome.HANDOFF, "amount.high", policy.high_amount.provisional)
    return None


def _expired(candidate: Candidate, today: date, window_days: int) -> bool:
    age = (today - date.fromisoformat(candidate.date)).days
    return age > window_days
