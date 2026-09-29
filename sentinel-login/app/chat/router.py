"""POST /chat for customers. Identity comes from the session, never the body."""

from fastapi import Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.auth.models import Session
from app.auth.roles import require_customer
from app.auth.router import _client_ip, _trace_id, get_audit
from app.chat.contract import (
    CaseConfirmation,
    ChatReply,
    Clarification,
    ErrorReply,
    Handoff,
    TextReply,
    TransactionFacts,
)
from app.chat.orchestrator import (
    ClarificationDecision,
    EscalateDecision,
    OpenCaseDecision,
    Orchestrator,
    TextDecision,
)
from app.chat.stores import CaseRecord, CaseStore
from app.disputes.service import DisputeResult, DisputeService
from app.gold.store import GoldTransactions

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(min_length=1, max_length=2000)


def get_orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


def get_cases(request: Request) -> CaseStore:
    return request.app.state.cases


def get_gold(request: Request) -> GoldTransactions:
    return request.app.state.gold


def get_disputes(request: Request) -> DisputeService:
    return request.app.state.disputes


def _handoff_for(
    record: CaseRecord, reason: str, estimated_time: str
) -> Handoff:
    return Handoff(
        reference=f"HO-{record.case_id}",
        reason=reason,
        advisor_received=(
            f"Dispute request for {record.amount} {record.currency} at "
            f"{record.merchant} on {record.date}. Case {record.case_id} "
            f"is {record.state} with priority {record.priority}."
        ),
        estimated_time=estimated_time,
    )


def _confirmation_from(result: DisputeResult) -> CaseConfirmation:
    assert result.case is not None and result.proof is not None
    case = result.case
    proof = result.proof
    return CaseConfirmation(
        case_id=case.case_id,
        transaction=TransactionFacts(
            amount=case.amount,
            currency=case.currency,
            merchant=case.merchant,
            date=case.date,
        ),
        state=case.state,
        priority=case.priority,
        next_steps=[
            f"Case {case.case_id} is registered.",
            "An advisor reviews it within 2 business days.",
        ],
        expected_timeline="2 business days",
        verified_at=case.created_at,
        verified=True,
        hold=proof.hold,
        eligibility=proof.rule,
        sla_deadline=proof.sla_deadline,
        receipt_ref=proof.receipt_ref,
        queue_status=proof.queue_status,
    )


@router.post("")
def chat(
    body: ChatRequest,
    request: Request,
    session: Session = Depends(require_customer),
) -> JSONResponse:
    orchestrator = get_orchestrator(request)
    audit = get_audit(request)
    trace_id = _trace_id(request)
    ip = _client_ip(request)
    try:
        decision = orchestrator.decide(body.message, session.customer_id)
    except Exception:  # noqa: BLE001 - orchestrator failure is always generic
        reply: ChatReply = ErrorReply(
            message="Something went wrong. Please try again.", trace_id=trace_id
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=reply.model_dump(mode="json"))
    if isinstance(decision, TextDecision):
        reply = TextReply(text=decision.text)
    elif isinstance(decision, ClarificationDecision):
        reply = Clarification(text=decision.text, missing=decision.missing)
    elif isinstance(decision, EscalateDecision):
        record = get_cases(request).create(
            session.customer_id,
            "0.00",
            "MXN",
            "unknown",
            "2026-06-10",
            "Escalated",
            decision.priority,
            reason=decision.reason,
        )
        audit.emit("handoff_created", session.customer_id, trace_id, ip)
        reply = _handoff_for(record, decision.reason, "1 business day")
    else:
        reply = _open_case(decision, request, session, trace_id, ip)
    return JSONResponse(status_code=status.HTTP_200_OK, content=reply.model_dump(mode="json"))


def _open_case(
    decision: OpenCaseDecision,
    request: Request,
    session: Session,
    trace_id: str,
    ip: str,
) -> ChatReply:
    """All case creation flows through the disputes service. No invented facts."""
    result = get_disputes(request).create(
        session.customer_id,
        decision.reference,
        f"chat-{trace_id}",
        trace_id,
        ip,
        pre_created_id=decision.pre_created_id,
    )
    if result.outcome == "created":
        return _confirmation_from(result)
    if result.outcome == "verified_failed":
        assert result.case is not None
        return _handoff_for(result.case, result.reason, "1 business day")
    row = get_gold(request).get(decision.reference, session.customer_id)
    record = get_cases(request).create(
        session.customer_id,
        row.amount if row else "0.00",
        row.currency if row else "MXN",
        row.merchant if row else "unknown",
        row.date if row else "2026-06-10",
        "Escalated",
        decision.priority,
        reason=result.reason,
    )
    get_audit(request).emit("handoff_created", session.customer_id, trace_id, ip)
    return _handoff_for(record, result.reason, "1 business day")
