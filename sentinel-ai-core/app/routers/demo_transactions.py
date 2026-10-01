"""
GET /api/v1/transactions

Cookie-session-scoped listing of the customer's transactions from the Gold
store on ``app.state.gold`` (DuckDB view or in-memory mock, same contract).

Each row is a ``CandidateTransaction``: the same object the chat uses for
clarification chips and the confirm box, so the interface renders one shape.
``eligible`` and ``ineligibleKey`` come from the country policy, never from
the client.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request

from app.orchestrator.types import Candidate
from app.policy.engine import _expired
from app.policy.load import load_country
from app.schemas.chat import CandidateTransaction, TransactionList
from app.session.models import Session
from app.session.router import require_session
from app.tools.gold import to_candidate

router = APIRouter(prefix="/api/v1", tags=["transactions"])

_STATUS_KEYS = {
    "Reversed": "candidateReversed",
    "Declined": "candidateDeclined",
    "Pending": "candidatePending",
}


def candidate_view(candidate: Candidate, country: str, today: date) -> CandidateTransaction:
    """Project an orchestrator candidate onto the interface contract."""
    policy = load_country(country)
    key: str | None = None
    if policy is None:
        key = "candidateOutOfWindow"
    elif not policy.disputable.get(candidate.status.value, False):
        key = _STATUS_KEYS.get(candidate.status.value, "candidatePending")
    elif _expired(candidate, today, policy.window_days):
        key = "candidateOutOfWindow"
    elif candidate.is_disputed:
        key = "candidateDisputed"
    return CandidateTransaction(
        reference=candidate.candidate_id,
        amount=candidate.amount,
        currency=candidate.currency,
        merchant=candidate.merchant,
        date=candidate.date,
        status=candidate.status.value,
        eligible=key is None,
        ineligibleKey=key,
    )


@router.get("/transactions")
def list_transactions(
    request: Request,
    session: Session = Depends(require_session),
) -> TransactionList:
    if "customer_id" in request.query_params:
        raise HTTPException(status_code=422, detail="customer_id is not an accepted parameter")

    gold = request.app.state.gold
    ref_date = request.app.state.reference_date
    rows = gold.list_for_customer(session.customer_id)
    return TransactionList(
        as_of=ref_date.isoformat(),
        # Raw Gold vocabulary never reaches the API: rows go through the candidate adapter.
        transactions=[candidate_view(to_candidate(row), session.country, ref_date) for row in rows],
    )
