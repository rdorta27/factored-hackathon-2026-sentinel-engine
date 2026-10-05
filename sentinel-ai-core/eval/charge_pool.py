"""The charges that the service lists for one example, as `Candidate` rows.

The merchant text stays as Gold gives it ("UNSPECIFIED" for no name), so the
selector and the rules see what the service sees.
"""

from __future__ import annotations

from app.orchestrator.types import Candidate, TransactionStatus
from eval import charge_examples as gen


def to_candidate(row: gen.Row, as_of: str) -> Candidate:
    known = {status.value for status in TransactionStatus}
    return Candidate(
        candidate_id=row.transaction_id,
        status=TransactionStatus(row.status) if row.status in known else TransactionStatus.PENDING,
        amount=f"{row.amount:.2f}",
        currency=row.currency,
        merchant=row.merchant,
        date=row.date,
        as_of=as_of,
    )


def pool_candidates(example: gen.Example, rows: dict[str, list[gen.Row]]) -> list[Candidate]:
    """Newest first, as `lookup_transactions` lists them."""
    return [to_candidate(row, example.today) for row in gen.pool_of(example, rows)]
