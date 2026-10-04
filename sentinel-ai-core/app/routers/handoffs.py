"""
GET /api/v1/handoffs            escalated tickets, newest first (role advisor)
GET /api/v1/handoffs/{id}       one ticket (role advisor)
GET /api/v1/handoffs/{id}/trace trace of the turn that filed it (role advisor)

The advisor side of the handoff (decision 009, REQ-0008): the full package the
chat produced — summary, per-turn conversation, verified facts, actions
attempted, evidence, open questions — plus the customer id and country. Any
other role gets 403 and an ``access_denied`` audit record.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.schemas.chat import AdvisorTicket, AdvisorTrace, HandoffPackage, TraceStep
from app.session.models import Session
from app.session.router import require_advisor
from app.state.cases import CaseRow

router = APIRouter(prefix="/api/v1/handoffs", tags=["advisor"])


def _ticket(row: CaseRow) -> AdvisorTicket:
    package = HandoffPackage.model_validate(row.package or {"request": "unknown", "language": "es-419", "country": ""})
    return AdvisorTicket(
        case_id=row.case_id,
        status=row.status,
        created_at=row.created_at,
        customer_id=row.customer_id,
        country=package.country,
        reason_key=row.reason_key,
        package=package,
    )


@router.get("")
def list_handoffs(request: Request, session: Session = Depends(require_advisor)) -> list[AdvisorTicket]:
    return [_ticket(row) for row in request.app.state.cases.handoffs()]


@router.get("/{case_id}")
def get_handoff(case_id: str, request: Request, session: Session = Depends(require_advisor)) -> AdvisorTicket:
    row = request.app.state.cases.get(case_id)
    if row is None or row.kind != "handoff":
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _ticket(row)


@router.get("/{case_id}/trace")
def get_trace(case_id: str, request: Request, session: Session = Depends(require_advisor)) -> AdvisorTrace:
    """The escalating turn's records: steps, outcome, latency, model, cost.

    Falls back to the JSONL log when the turn is no longer in memory (a
    restart); if neither holds it, the trace is reported unavailable instead
    of failing. Never carries customer text or an identifier.
    """
    row = request.app.state.cases.get(case_id)
    if row is None or row.kind != "handoff":
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not row.trace_id:
        return AdvisorTrace(case_id=case_id, trace_id=None, available=False)
    recorder = request.app.state.recorder
    records = recorder.records_for(row.trace_id) or recorder.persisted_for(row.trace_id)
    steps = [
        TraceStep(
            step=record.step,
            tool=record.tool,
            outcome=record.outcome,
            attempt=record.attempt,
            latency_ms=record.latency_ms,
            model=record.model,
            route=record.route,
            prompt_version=record.prompt_version,
            cost_usd=record.cost_usd,
            policy_version=record.policy_version,
            ts=record.ts,
        )
        for record in records
    ]
    return AdvisorTrace(case_id=case_id, trace_id=row.trace_id, available=bool(records), steps=steps)
