"""One policy gate for dispute creation, shared by chat and the HTTP endpoint."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Literal

from app.audit.logger import AuditLogger
from app.chat.stores import CaseRecord, CaseStore
from app.disputes.policy import DisputePolicy, check_eligibility, reference_date
from app.disputes.sla import add_business_days
from app.gold.store import GoldRow, GoldTransactions

VERIFY_ATTEMPTS = 3
SLA_BUSINESS_DAYS = 2


def sla_deadline() -> datetime:
    """Deadline as business days after the reference date, never wall clock."""
    deadline = add_business_days(reference_date(), SLA_BUSINESS_DAYS)
    return datetime.combine(deadline, time.min, tzinfo=timezone.utc)


@dataclass(frozen=True)
class ProofOfWork:
    """The five trust elements proving the case was opened and verified.

    Every string here is locale-neutral on purpose: the interface formats and
    translates. Only keys and raw values travel over the wire.
    """

    case_id: str
    amount: str
    currency: str
    merchant: str
    transaction_date: str
    reference_date: str
    sla_date: str
    rule_key: str = "ruleEligible"
    queue_key: str = "queueInReview"
    no_funds_key: str = "noFundsHeld"


@dataclass
class DisputeResult:
    """Outcome of one creation attempt. Stored verbatim for idempotent replay."""

    outcome: Literal["created", "refused", "verified_failed"]
    case: CaseRecord | None
    reason_key: str
    reason_detail: str | None = None
    proof: ProofOfWork | None = None
    replayed: bool = False


class DisputeService:
    """Deterministic gate: policy check, create, re-read, prove. No LLM inside."""

    def __init__(
        self,
        gold: GoldTransactions,
        cases: CaseStore,
        policy: DisputePolicy,
        audit: AuditLogger,
    ) -> None:
        self._gold = gold
        self._cases = cases
        self._policy = policy
        self._audit = audit
        self._keys: dict[str, DisputeResult] = {}

    def create(
        self,
        customer_id: str,
        reference: str,
        idempotency_key: str,
        trace_id: str,
        ip: str,
        pre_created_id: str | None = None,
    ) -> DisputeResult:
        if idempotency_key in self._keys:
            stored = self._keys[idempotency_key]
            return DisputeResult(
                outcome=stored.outcome,
                case=stored.case,
                reason_key=stored.reason_key,
                reason_detail=stored.reason_detail,
                proof=stored.proof,
                replayed=True,
            )
        if pre_created_id is not None:
            # Mock chaos path: the staged write was lost; policy is skipped
            # and only the verification loop runs, using Gold facts if known.
            facts = self._gold.get(reference, customer_id)
            result = self._verify_only(
                customer_id, pre_created_id, facts, trace_id, ip
            )
        else:
            row = self._gold.get(reference, customer_id)
            if row is None:
                result = self._refuse(
                    customer_id, "refusedNotFound", None, trace_id, ip
                )
            else:
                ok, reason = check_eligibility(row, self._policy)
                if not ok:
                    result = self._refuse(
                        customer_id, "refusedIneligible", reason, trace_id, ip
                    )
                else:
                    record = self._cases.create(
                        customer_id,
                        row.amount,
                        row.currency,
                        row.merchant,
                        row.date,
                        "Open",
                        "High",
                        reason="customer dispute",
                    )
                    result = self._verify_only(
                        customer_id, record.case_id, row, trace_id, ip
                    )
        self._keys[idempotency_key] = result
        return result

    def _refuse(
        self,
        customer_id: str,
        reason_key: str,
        reason_detail: str | None,
        trace_id: str,
        ip: str,
    ) -> DisputeResult:
        self._audit.emit("dispute_refused", customer_id, trace_id, ip)
        return DisputeResult("refused", None, reason_key, reason_detail)

    def _verify_only(
        self,
        customer_id: str,
        case_id: str,
        row: GoldRow | None,
        trace_id: str,
        ip: str,
    ) -> DisputeResult:
        verified: CaseRecord | None = None
        for _ in range(VERIFY_ATTEMPTS):
            candidate = self._cases.get(case_id)
            if candidate is not None and candidate.customer_id == customer_id:
                verified = candidate
                break
        if verified is None:
            placeholder = self._cases.create(
                customer_id,
                row.amount if row else "0.00",
                row.currency if row else "MXN",
                row.merchant if row else "unknown",
                row.date if row else reference_date().isoformat(),
                "Escalated",
                "High",
                reason="Verification of the created case failed",
            )
            self._audit.emit("handoff_created", customer_id, trace_id, ip)
            return DisputeResult(
                outcome="verified_failed",
                case=placeholder,
                reason_key="handoffUnverified",
            )
        self._audit.emit("case_opened", customer_id, trace_id, ip)
        proof = ProofOfWork(
            case_id=verified.case_id,
            amount=verified.amount,
            currency=verified.currency,
            merchant=verified.merchant,
            transaction_date=verified.date,
            reference_date=reference_date().isoformat(),
            sla_date=add_business_days(reference_date(), SLA_BUSINESS_DAYS).isoformat(),
        )
        return DisputeResult("created", verified, "", None, proof)

    def build_receipt(self, case: CaseRecord) -> str:
        """Plain-text downloadable receipt. ASCII-only, locale-neutral."""
        deadline = add_business_days(reference_date(), SLA_BUSINESS_DAYS).isoformat()
        return "\n".join(
            [
                "SENTINEL ENGINE - DISPUTE RECEIPT (demo, simulated)",
                f"Case: {case.case_id}",
                f"Customer: {case.customer_id}",
                f"Transaction: {case.amount} {case.currency} at "
                f"{case.merchant} on {case.date}",
                f"State: {case.state} | Priority: {case.priority}",
                "Hold: none. No funds were held or moved (simulated case only).",
                f"Rule: eligible within the {self._policy.window_days}-day "
                f"dispute window ({self._policy.article}).",
                f"Reference date: {reference_date().isoformat()}",
                f"Expected resolution (business days): {deadline}",
                "Queue: with an advisor for review.",
                f"Opened: {case.created_at.isoformat()}",
            ]
        )
