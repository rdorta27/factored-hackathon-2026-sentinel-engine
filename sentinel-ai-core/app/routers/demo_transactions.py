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
from app.policy.engine import _expired, decision_snapshot
from app.policy.load import load_country
from app.schemas.chat import CandidateTransaction, OwnCase, ProductView, TransactionList
from app.session.models import Session
from app.session.router import require_customer
from app.state.cases import OPEN
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
    window: dict[str, object] = {}
    if key == "candidateOutOfWindow" and policy is not None:
        # The same figures the "why" card reads, from the same policy function.
        snapshot = decision_snapshot("window.expired", candidate, today, policy)
        window = {
            "window_days": snapshot.get("window_days"),
            "last_eligible_date": snapshot.get("last_eligible_date"),
        }
    return CandidateTransaction(
        **window,
        reference=candidate.candidate_id,
        amount=candidate.amount,
        currency=candidate.currency,
        merchant=candidate.merchant,
        date=candidate.date,
        status=candidate.status.value,
        eligible=key is None,
        ineligibleKey=key,
    )


_STATE_BY_KEY = {
    "candidateOutOfWindow": "outside_window",
    "candidateDisputed": "already_disputed",
}


def case_state(view: CandidateTransaction, in_review: set[str], with_advisor: set[str]) -> str:
    """State of one charge for the recent-charges panel, from the case store and the policy.

    A dispute opened here wins, then a handoff ticket. The policy result decides the rest.
    """
    if view.reference in in_review:
        return "in_review"
    if view.reference in with_advisor:
        return "with_advisor"
    if view.ineligibleKey is None:
        return "eligible"
    return _STATE_BY_KEY.get(view.ineligibleKey, "not_disputable")


def _with_state(
    view: CandidateTransaction,
    in_review: set[str],
    with_advisor: set[str],
    case_ids: dict[str, str],
) -> CandidateTransaction:
    state = case_state(view, in_review, with_advisor)
    update: dict[str, object] = {"case_state": state}
    if state in ("in_review", "with_advisor") and view.reference in case_ids:
        update["case_id"] = case_ids[view.reference]
    if state == "in_review":
        # A dispute opened here closes the charge to a second dispute.
        update.update(eligible=False, ineligibleKey="candidateDisputed")
    elif state == "with_advisor":
        # An advisor already has the charge: a tap must not file a second ticket.
        update.update(eligible=False, ineligibleKey="candidateWithAdvisor")
    return view.model_copy(update=update)


@router.get("/transactions")
def list_transactions(
    request: Request,
    session: Session = Depends(require_customer),
) -> TransactionList:
    if "customer_id" in request.query_params:
        raise HTTPException(status_code=422, detail="customer_id is not an accepted parameter")

    gold = request.app.state.gold
    ref_date = request.app.state.reference_date
    rows = gold.list_for_customer(session.customer_id)
    cases = request.app.state.cases.for_customer(session.customer_id)
    in_review = {c.transaction_id for c in cases if c.kind == "dispute" and c.status == OPEN and c.transaction_id}
    with_advisor = {c.transaction_id for c in cases if c.kind == "handoff" and c.transaction_id}
    # The case that holds each charge: an open dispute wins over a handoff ticket.
    case_ids = {c.transaction_id: c.case_id for c in cases if c.kind == "handoff" and c.transaction_id}
    case_ids.update(
        {c.transaction_id: c.case_id for c in cases if c.kind == "dispute" and c.status == OPEN and c.transaction_id}
    )
    views = [candidate_view(to_candidate(row), session.country, ref_date) for row in rows]
    # Only a Gold source that holds product data gives a product. Never invent digits.
    lookup = getattr(gold, "product_for", None)
    info = lookup(session.customer_id) if lookup else None
    summaries = [
        OwnCase(
            case_id=c.case_id,
            case_state="in_review" if c.kind == "dispute" else "with_advisor",
            merchant=c.merchant,
            amount=c.amount,
            currency=c.currency,
            date=c.transaction_date,
        )
        for c in cases
        if (c.kind == "dispute" and c.status == OPEN) or c.kind == "handoff"
    ]
    return TransactionList(
        cases=summaries,
        product=ProductView(kind=info.kind, last4=info.last4) if info else None,
        as_of=ref_date.isoformat(),
        # Raw Gold vocabulary never reaches the API: rows go through the candidate adapter.
        transactions=[_with_state(view, in_review, with_advisor, case_ids) for view in views],
    )
