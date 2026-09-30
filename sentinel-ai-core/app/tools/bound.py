from app.orchestrator.types import Candidate
from app.tools.fake import InMemoryTools
from app.tools.gold import GoldTransactions, to_candidate
from app.tools.ports import OpenResult


class SessionBoundLookup:
    def __init__(self, gold: GoldTransactions, customer_id: str, memory: InMemoryTools) -> None:
        self._gold = gold
        self._customer_id = customer_id
        self._memory = memory

    def lookup_transactions(self) -> list[Candidate]:
        return [to_candidate(row) for row in self._gold.list_for_customer(self._customer_id)]

    def open_dispute(
        self,
        candidate_id: str,
        token: str | None,
        category: str,
        statement: str,
        idempotency_key: str,
    ) -> OpenResult:
        return self._memory.open_dispute(candidate_id, token, category, statement, idempotency_key)

    def lookup_dispute(self, dispute_id: str):
        return self._memory.lookup_dispute(dispute_id)
