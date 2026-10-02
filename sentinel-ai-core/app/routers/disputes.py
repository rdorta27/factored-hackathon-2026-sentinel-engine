"""
/api/v1/disputes — the dispute workflow outside the chat, on the same engine.

  POST /api/v1/disputes/preview   step 1: policy decision on one own charge, no write
  POST /api/v1/disputes           step 2: open the previewed dispute, verified by read-back
  GET  /api/v1/disputes           the customer's cases (disputes and handoff tickets)
  GET  /api/v1/disputes/{case_id} one of them

Both POSTs run the orchestrator ``step()`` on the session's conversation state
through the chat's turn cycle, so the confirm box, the policy, idempotency,
read-back and the turn record are the chat's own: this is a second client of
the same executor, not a second business path. Identity comes from the cookie.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.orchestrator.types import CandidateIdInput, OutcomeKind
from app.routers.demo_chat import (
    finish_turn,
    open_turn,
    rate_limited,
    run_turn,
    select_charge,
    unknown_charge,
)
from app.schemas.chat import (
    CaseConfirmation,
    CaseSummary,
    ConfirmationDisplay,
    DisputeCreateInput,
    DisputePreviewInput,
    MessageKeys,
    TransactionFacts,
)
from app.session.models import Session
from app.session.router import require_customer
from app.state.cases import OPEN, CaseRow

router = APIRouter(prefix="/api/v1/disputes", tags=["disputes"])


def _facts(row: CaseRow) -> TransactionFacts | None:
    if not (row.amount and row.currency and row.merchant and row.transaction_date):
        return None
    return TransactionFacts(
        amount=row.amount, currency=row.currency, merchant=row.merchant, date=row.transaction_date
    )


def _summary(row: CaseRow) -> CaseSummary:
    return CaseSummary(
        case_id=row.case_id,
        kind="handoff" if row.kind == "handoff" else "dispute",
        status=row.status,
        transaction=_facts(row),
        reason_key=row.reason_key,
        created_at=row.created_at,
    )


def _open_case(request: Request, session: Session, reference: str) -> CaseRow | None:
    rows = request.app.state.cases.for_customer(session.customer_id)
    return next(
        (row for row in rows if row.kind == "dispute" and row.status == OPEN and row.transaction_id == reference),
        None,
    )


def _confirmation_from(row: CaseRow, reference_date: str) -> CaseConfirmation:
    facts = _facts(row)
    assert facts is not None
    return CaseConfirmation(
        case_id=row.case_id,
        transaction=facts,
        verified_at=datetime.now(timezone.utc),
        display=ConfirmationDisplay(
            amount=facts.amount, currency=facts.currency, merchant=facts.merchant, referenceDate=reference_date
        ),
        messages=MessageKeys(nextStep="nextStepReview", rule="ruleEligible", noFunds="noFundsHeld"),
        attempt=1,
    )


@router.post("/preview")
def preview(body: DisputePreviewInput, request: Request, session: Session = Depends(require_customer)) -> JSONResponse:
    blocked = rate_limited(request, session)
    if blocked is not None:
        return blocked
    turn = open_turn(request, session)
    turn_input = CandidateIdInput(candidate_id=body.reference)
    if select_charge(turn, body.reference) is None:
        return finish_turn(request, turn, unknown_charge(turn), policy_rule="unknownCharge", turn_input=turn_input)
    # A preview never confirms: a box already pending for this charge is recomputed, not consumed.
    pending = turn.state.pending_confirmation
    if pending is not None and pending.candidate_id == body.reference:
        turn.state.pending_confirmation = None
    output, reply = run_turn(turn, turn_input)
    pending = turn.state.pending_confirmation
    turn.stored.pending_reason = body.reason if pending is not None and pending.candidate_id == body.reference else None
    return finish_turn(request, turn, reply, output, turn_input=turn_input)


@router.post("")
def create(body: DisputeCreateInput, request: Request, session: Session = Depends(require_customer)) -> JSONResponse:
    blocked = rate_limited(request, session)
    if blocked is not None:
        return blocked
    turn = open_turn(request, session)
    turn_input = CandidateIdInput(candidate_id=body.reference)
    pending = turn.state.pending_confirmation
    if pending is None or pending.candidate_id != body.reference:
        existing = _open_case(request, session, body.reference)
        if existing is not None and _facts(existing) is not None:
            # Read back from the store: the case exists, the call is answered, nothing is written.
            confirmation = _confirmation_from(existing, turn.ref_date.isoformat())
            return finish_turn(request, turn, confirmation, policy_rule="already.open", turn_input=turn_input)
        raise HTTPException(status_code=409, detail="preview_required")
    if select_charge(turn, body.reference) is None:
        return finish_turn(request, turn, unknown_charge(turn), policy_rule="unknownCharge", turn_input=turn_input)
    output, reply = run_turn(turn, turn_input)
    created = output is not None and output.kind is OutcomeKind.CASE_NUMBER and isinstance(reply, CaseConfirmation)
    if created and turn.stored.pending_reason:
        request.app.state.cases.set_reason(reply.case_id, turn.stored.pending_reason)
    turn.stored.pending_reason = None
    return finish_turn(request, turn, reply, output, status_code=201 if created else 200, turn_input=turn_input)


@router.get("")
def list_cases(request: Request, session: Session = Depends(require_customer)) -> list[CaseSummary]:
    if "customer_id" in request.query_params:
        raise HTTPException(status_code=422, detail="customer_id is not an accepted parameter")
    return [_summary(row) for row in request.app.state.cases.for_customer(session.customer_id)]


@router.get("/{case_id}")
def get_case(case_id: str, request: Request, session: Session = Depends(require_customer)) -> CaseSummary:
    row = request.app.state.cases.get(case_id)
    if row is None or row.customer_id != session.customer_id:
        # Another customer's case is indistinguishable from a missing one.
        raise HTTPException(status_code=404, detail="Case not found")
    return _summary(row)
