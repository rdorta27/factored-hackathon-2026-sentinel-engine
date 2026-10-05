"""Cases: disputes opened after confirmation, and handoff tickets.

``CaseRepository`` stores full rows (memory or SQLite). ``CaseTools`` binds it
to one customer and implements the write side of the tool port
(``open_dispute``, ``lookup_dispute``) with the same semantics as
``app.tools.fake.InMemoryTools``: one record per idempotency key, a
confirmation token required for a new record, and read-back by id.
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Protocol

from sqlalchemy import Engine, select, update
from sqlalchemy.orm import Session as DbSession

from app.models.dispute_case import DisputeCase
from app.tools.gold import GoldTransactions
from app.tools.ports import DisputeRecord, OpenResult, ToolStatus

OPEN = "Open"
ESCALATED = "Escalated"


@dataclass(frozen=True)
class CaseRow:
    case_id: str
    customer_id: str
    kind: str  # "dispute" | "handoff"
    status: str  # dataset complaints vocabulary
    created_at: datetime
    transaction_id: str | None = None
    amount: str | None = None
    currency: str | None = None
    merchant: str | None = None
    transaction_date: str | None = None
    category: str | None = None
    idempotency_key: str | None = None
    reason: str | None = None
    reason_key: str | None = None
    package: dict[str, Any] | None = None
    trace_id: str | None = None


def new_case_id() -> str:
    return f"D-{secrets.token_hex(4).upper()}"


class CaseRepository(Protocol):
    def add(self, row: CaseRow) -> None: ...

    def by_key(self, key: str) -> CaseRow | None: ...

    def get(self, case_id: str) -> CaseRow | None: ...

    def for_customer(self, customer_id: str) -> list[CaseRow]: ...

    def set_reason(self, case_id: str, reason: str) -> None: ...

    def handoffs(self) -> list[CaseRow]: ...


class InMemoryCaseRepository:
    def __init__(self) -> None:
        self._rows: dict[str, CaseRow] = {}

    def add(self, row: CaseRow) -> None:
        self._rows[row.case_id] = row

    def by_key(self, key: str) -> CaseRow | None:
        return next((row for row in self._rows.values() if row.idempotency_key == key), None)

    def get(self, case_id: str) -> CaseRow | None:
        return self._rows.get(case_id)

    def for_customer(self, customer_id: str) -> list[CaseRow]:
        rows = [row for row in self._rows.values() if row.customer_id == customer_id]
        return sorted(rows, key=lambda row: row.created_at, reverse=True)

    def set_reason(self, case_id: str, reason: str) -> None:
        row = self._rows.get(case_id)
        if row is not None:
            self._rows[case_id] = replace(row, reason=reason)

    def handoffs(self) -> list[CaseRow]:
        rows = [row for row in self._rows.values() if row.kind == "handoff"]
        return sorted(rows, key=lambda row: row.created_at, reverse=True)


def _to_row(record: DisputeCase) -> CaseRow:
    created = record.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return CaseRow(
        case_id=record.dispute_id,
        customer_id=record.customer_id,
        kind=record.kind,
        status=record.status,
        created_at=created,
        transaction_id=record.transaction_id,
        amount=None if record.amount is None else f"{record.amount:.2f}",
        currency=record.currency,
        merchant=record.merchant,
        transaction_date=record.transaction_date,
        category=record.category,
        idempotency_key=record.idempotency_key,
        reason=record.reason,
        reason_key=record.escalation_reason,
        package=json.loads(record.package) if record.package else None,
        trace_id=record.trace_id,
    )


class SqliteCaseRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, row: CaseRow) -> None:
        with DbSession(self._engine) as db, db.begin():
            db.add(
                DisputeCase(
                    dispute_id=row.case_id,
                    customer_id=row.customer_id,
                    kind=row.kind,
                    status=row.status,
                    created_at=row.created_at,
                    transaction_id=row.transaction_id,
                    amount=None if row.amount is None else float(row.amount),
                    currency=row.currency,
                    merchant=row.merchant,
                    transaction_date=row.transaction_date,
                    category=row.category,
                    idempotency_key=row.idempotency_key,
                    reason=row.reason,
                    escalation_reason=row.reason_key,
                    package=json.dumps(row.package) if row.package is not None else None,
                    trace_id=row.trace_id,
                )
            )

    def by_key(self, key: str) -> CaseRow | None:
        with DbSession(self._engine) as db:
            record = db.scalars(select(DisputeCase).where(DisputeCase.idempotency_key == key)).first()
            return None if record is None else _to_row(record)

    def get(self, case_id: str) -> CaseRow | None:
        with DbSession(self._engine) as db:
            record = db.get(DisputeCase, case_id)
            return None if record is None else _to_row(record)

    def for_customer(self, customer_id: str) -> list[CaseRow]:
        with DbSession(self._engine) as db:
            records = db.scalars(
                select(DisputeCase)
                .where(DisputeCase.customer_id == customer_id)
                .order_by(DisputeCase.created_at.desc())
            ).all()
            return [_to_row(record) for record in records]

    def set_reason(self, case_id: str, reason: str) -> None:
        with DbSession(self._engine) as db, db.begin():
            db.execute(update(DisputeCase).where(DisputeCase.dispute_id == case_id).values(reason=reason))

    def handoffs(self) -> list[CaseRow]:
        with DbSession(self._engine) as db:
            records = db.scalars(
                select(DisputeCase).where(DisputeCase.kind == "handoff").order_by(DisputeCase.created_at.desc())
            ).all()
            return [_to_row(record) for record in records]


class CaseTools:
    """Write side of the tool port for one customer, over a ``CaseRepository``.

    ``open_calls`` and ``lookup_failures_left`` mirror ``InMemoryTools`` so the
    same fault injection works on both backends.
    """

    def __init__(self, repo: CaseRepository, customer_id: str, gold: GoldTransactions) -> None:
        self._repo = repo
        self._customer_id = customer_id
        self._gold = gold
        self.used_tokens: set[str] = set()
        self.open_calls = 0
        self.lookup_failures_left = 0

    @property
    def by_key(self) -> dict[str, CaseRow]:
        return {
            row.idempotency_key: row
            for row in self._repo.for_customer(self._customer_id)
            if row.kind == "dispute" and row.idempotency_key
        }

    def disputed_refs(self) -> set[str]:
        """Charges with an open dispute in this system, whatever session opened it."""
        return {
            row.transaction_id
            for row in self._repo.for_customer(self._customer_id)
            if row.kind == "dispute" and row.status == OPEN and row.transaction_id
        }

    def disputes(self) -> list[CaseRow]:
        """The customer's disputes, newest first, for a status question."""
        return [
            row
            for row in self._repo.for_customer(self._customer_id)
            if row.kind == "dispute"
        ]

    def open_dispute(
        self,
        candidate_id: str,
        token: str | None,
        category: str,
        statement: str,
        idempotency_key: str,
    ) -> OpenResult:
        self.open_calls += 1
        existing = self._repo.by_key(idempotency_key)
        if existing is not None:
            return OpenResult(status=ToolStatus.OK, record=_record(existing))
        if not token or not token.strip() or token in self.used_tokens:
            return OpenResult(status=ToolStatus.REJECTED)
        self.used_tokens.add(token)
        gold_row = self._gold.get(candidate_id, self._customer_id)
        row = CaseRow(
            case_id=new_case_id(),
            customer_id=self._customer_id,
            kind="dispute",
            status=OPEN,
            created_at=datetime.now(timezone.utc),
            transaction_id=candidate_id,
            amount=gold_row.amount if gold_row else None,
            currency=gold_row.currency if gold_row else None,
            merchant=gold_row.merchant if gold_row else None,
            transaction_date=gold_row.date if gold_row else None,
            category=category,
            idempotency_key=idempotency_key,
            reason=statement or None,
        )
        self._repo.add(row)
        return OpenResult(status=ToolStatus.OK, record=_record(row))

    def lookup_dispute(self, dispute_id: str) -> DisputeRecord | None:
        if self.lookup_failures_left > 0:
            self.lookup_failures_left -= 1
            return None
        row = self._repo.get(dispute_id)
        if row is None or row.customer_id != self._customer_id or row.kind != "dispute":
            return None
        return _record(row)


def _record(row: CaseRow) -> DisputeRecord:
    return DisputeRecord(
        dispute_id=row.case_id,
        candidate_id=row.transaction_id or "",
        category=row.category or "",
        idempotency_key=row.idempotency_key or "",
    )
