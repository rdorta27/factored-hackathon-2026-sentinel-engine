"""Tool ports: the action-executor boundary of the loop.

Every tool behind these ports runs synchronously in the request threadpool
(the routes are sync ``def``; see ``app/db/session.py``). Async code must
never call a tool directly: it enters through ``asyncio.to_thread``, as the
Gold readers in ``app/services/gold_service.py`` do. ``tests/test_event_loop.py``
fails if a new async function blocks on one of these calls.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.orchestrator.types import Candidate


class ToolStatus(StrEnum):
    OK = "ok"
    REJECTED = "rejected"
    FAILED = "failed"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class DisputeRecord:
    dispute_id: str
    candidate_id: str
    category: str
    idempotency_key: str


@dataclass(frozen=True)
class OpenResult:
    status: ToolStatus
    record: DisputeRecord | None = None


class TransactionLookup(Protocol):
    def lookup_transactions(self) -> list[Candidate]: ...

    def open_dispute(
        self,
        candidate_id: str,
        token: str | None,
        category: str,
        statement: str,
        idempotency_key: str,
    ) -> OpenResult: ...

    def lookup_dispute(self, dispute_id: str) -> DisputeRecord | None: ...
