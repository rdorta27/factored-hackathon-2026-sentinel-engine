"""Case storage seam. Phase 2 replaces the in-memory adapter with Gold reads."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


@dataclass
class CaseRecord:
    """One dispute case. Only case-necessary fields; never a full profile."""

    case_id: str
    customer_id: str
    amount: str
    currency: str
    merchant: str
    date: str
    state: str
    priority: str
    reason: str = ""
    owner: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CaseStore(Protocol):
    """Persistence contract for cases. `delete` exists for mocks and tests."""

    def create(
        self,
        customer_id: str,
        amount: str,
        currency: str,
        merchant: str,
        date: str,
        state: str,
        priority: str,
        reason: str = "",
    ) -> CaseRecord:
        ...

    def get(self, case_id: str) -> CaseRecord | None:
        ...

    def update(self, case_id: str, state: str, owner: str | None = None) -> CaseRecord | None:
        ...

    def list_escalated(self) -> list[CaseRecord]:
        ...

    def delete(self, case_id: str) -> None:
        ...


class InMemoryCaseStore:
    """Single-process case store. Demo only; vanishes on restart."""

    def __init__(self) -> None:
        self._cases: dict[str, CaseRecord] = {}
        self._counter = 0

    def create(
        self,
        customer_id: str,
        amount: str,
        currency: str,
        merchant: str,
        date: str,
        state: str,
        priority: str,
        reason: str = "",
    ) -> CaseRecord:
        self._counter += 1
        record = CaseRecord(
            case_id=f"CASE-{self._counter:04d}",
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            merchant=merchant,
            date=date,
            state=state,
            priority=priority,
            reason=reason,
        )
        self._cases[record.case_id] = record
        return record

    def get(self, case_id: str) -> CaseRecord | None:
        return self._cases.get(case_id)

    def update(
        self, case_id: str, state: str, owner: str | None = None
    ) -> CaseRecord | None:
        record = self._cases.get(case_id)
        if record is None:
            return None
        record.state = state
        if owner is not None:
            record.owner = owner
        return record

    def list_escalated(self) -> list[CaseRecord]:
        return [c for c in self._cases.values() if c.state == "Escalated"]

    def delete(self, case_id: str) -> None:
        self._cases.pop(case_id, None)
