import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from dataclasses import replace

from app.orchestrator.types import Candidate
from app.tools.gold import GoldTransactions, to_candidate
from app.tools.ports import OpenResult

# Well above the measured 0.28 s cold DuckDB read. Tests set a smaller value.
DEFAULT_GOLD_TIMEOUT_S = 2.0
_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="gold-read")


class GoldTimeout(Exception):
    """A Gold read exceeded SENTINEL_GOLD_TIMEOUT_S."""


def gold_timeout_s() -> float:
    raw = os.environ.get("SENTINEL_GOLD_TIMEOUT_S", "").strip()
    if not raw:
        return DEFAULT_GOLD_TIMEOUT_S
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_GOLD_TIMEOUT_S
    return value if value > 0 else DEFAULT_GOLD_TIMEOUT_S


def _bounded(fn, *args):  # type: ignore[no-untyped-def]
    future = _POOL.submit(fn, *args)
    try:
        return future.result(timeout=gold_timeout_s())
    except FuturesTimeout as exc:
        raise GoldTimeout() from exc


class SessionBoundLookup:
    """Tool port bound to the session customer.

    ``memory`` is the write side (``InMemoryTools`` or ``CaseTools``). When it
    knows which charges already have an open dispute (``disputed_refs``), those
    candidates are marked ``is_disputed`` so the policy refuses a second case
    from any later session, not only from the one that opened it.
    """

    def __init__(self, gold: GoldTransactions, customer_id: str, memory) -> None:  # type: ignore[no-untyped-def]
        self._gold = gold
        self._customer_id = customer_id
        self._memory = memory

    def _mark(self, candidates: list[Candidate]) -> list[Candidate]:
        disputed_refs = getattr(self._memory, "disputed_refs", None)
        if disputed_refs is None:
            return candidates
        disputed = disputed_refs()
        return [
            replace(item, is_disputed=True) if item.candidate_id in disputed else item
            for item in candidates
        ]

    def lookup_transactions(self) -> list[Candidate]:
        rows = _bounded(self._gold.list_for_customer, self._customer_id)
        return self._mark([to_candidate(row) for row in rows])

    def candidate(self, reference: str) -> Candidate | None:
        """One of the customer's charges, marked like the listing; None if not theirs."""
        row = _bounded(self._gold.get, reference, self._customer_id)
        return None if row is None else self._mark([to_candidate(row)])[0]

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
