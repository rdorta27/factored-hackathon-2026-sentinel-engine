from app.orchestrator.types import Candidate
from app.tools.ports import DisputeRecord, OpenResult, ToolStatus


class InMemoryTools:
    def __init__(
        self,
        candidates: list[Candidate] | None = None,
        lookup_failures: int = 0,
    ) -> None:
        self.candidates = list(candidates or [])
        self.lookup_failures_left = lookup_failures
        self.by_key: dict[str, DisputeRecord] = {}
        self.used_tokens: set[str] = set()
        self.open_calls = 0

    def lookup_transactions(self) -> list[Candidate]:
        return list(self.candidates)

    def open_dispute(
        self,
        candidate_id: str,
        token: str | None,
        category: str,
        statement: str,
        idempotency_key: str,
    ) -> OpenResult:
        self.open_calls += 1
        existing = self.by_key.get(idempotency_key)
        if existing is not None:
            return OpenResult(status=ToolStatus.OK, record=existing)
        if not token or not token.strip() or token in self.used_tokens:
            return OpenResult(status=ToolStatus.REJECTED)
        self.used_tokens.add(token)
        record = DisputeRecord(
            dispute_id=f"D-{len(self.by_key) + 1}",
            candidate_id=candidate_id,
            category=category,
            idempotency_key=idempotency_key,
        )
        self.by_key[idempotency_key] = record
        return OpenResult(status=ToolStatus.OK, record=record)

    def lookup_dispute(self, dispute_id: str) -> DisputeRecord | None:
        if self.lookup_failures_left > 0:
            self.lookup_failures_left -= 1
            return None
        for record in self.by_key.values():
            if record.dispute_id == dispute_id:
                return record
        return None
