"""POST /chat for customers. Identity comes from the session, never the body."""

from fastapi import Depends, Request, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.auth.models import Session
from app.auth.roles import require_customer
from app.auth.router import _client_ip, _trace_id, get_audit
from app.chat.contract import (
    CandidateTransaction,
    CaseConfirmation,
    ChatReply,
    Clarification,
    ConfirmationDisplay,
    ErrorReply,
    Handoff,
    MessageKeys,
    TextReply,
    TransactionFacts,
)
from app.chat.grounding import StatedFacts, extract_facts, ground, rank_candidates
from app.chat.orchestrator import (
    ChooseTransactionDecision,
    ClarificationDecision,
    EscalateDecision,
    OpenCaseDecision,
    Orchestrator,
    TextDecision,
)
from app.chat.stores import CaseRecord, CaseStore
from app.disputes.policy import check_eligibility, reference_date
from app.disputes.service import DisputeResult, DisputeService
from app.gold.store import GoldRow, GoldTransactions

router = APIRouter(prefix="/chat", tags=["chat"])

MAX_CANDIDATES = 4


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    message: str = Field(default="", max_length=2000)
    # Format-neutral on purpose: Phase 2 dataset ids are VARCHAR(30) and will
    # not look like the mock's TXN-1234. Authorization comes from looking the
    # reference up inside the session customer's rows, not from this pattern.
    selected_reference: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$",
    )


def get_orchestrator(request: Request) -> Orchestrator:
    return request.app.state.orchestrator


def get_cases(request: Request) -> CaseStore:
    return request.app.state.cases


def get_gold(request: Request) -> GoldTransactions:
    return request.app.state.gold


def get_disputes(request: Request) -> DisputeService:
    return request.app.state.disputes


def get_reference_date(request: Request):  # type: ignore[no-untyped-def]
    """Effective reference date, read from app state (env-backed at startup)."""
    value = getattr(request.app.state, "reference_date", None)
    if value is not None:
        return value
    return reference_date()


def _handoff_for(
    record: CaseRecord, reason_key: str, reason_detail: str | None = None
) -> Handoff:
    return Handoff(
        reference=f"HO-{record.case_id}",
        reason_key=reason_key,
        reason_detail=reason_detail,
        source="mock",
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
        verified_at=case.created_at,
        verified=True,
        display=ConfirmationDisplay(
            amount=case.amount,
            currency=case.currency,
            merchant=case.merchant,
            referenceDate=proof.reference_date,
            slaDate=proof.sla_date,
        ),
        messages=MessageKeys(
            nextStep="nextStepAdvisorReview",
            rule="ruleEligible",
            queue="queueInReview",
            noFunds="noFundsHeld",
        ),
    )


@router.post("")
def chat(
    body: ChatRequest,
    request: Request,
    session: Session = Depends(require_customer),
) -> JSONResponse:
    audit = get_audit(request)
    trace_id = _trace_id(request)
    ip = _client_ip(request)

    # An explicit structured selection bypasses the mock entirely: the client
    # already grounded the transaction by tapping it.
    if body.selected_reference:
        return _respond(
            _open_reference(body.selected_reference, request, session, trace_id, ip)
        )

    orchestrator = get_orchestrator(request)
    try:
        decision = orchestrator.decide(body.message, session.customer_id)
    except Exception:  # noqa: BLE001 - orchestrator failure is always generic
        reply: ChatReply = ErrorReply(message_key="errorGeneric", trace_id=trace_id)
        return _respond(reply)
    if isinstance(decision, TextDecision):
        reply = TextReply(message_key=decision.message_key)
    elif isinstance(decision, ClarificationDecision):
        reply = _clarify(request, session, decision.message_key, decision.missing)
    elif isinstance(decision, EscalateDecision):
        record = get_cases(request).create(
            session.customer_id,
            "0.00",
            "MXN",
            "unknown",
            get_reference_date(request).isoformat(),
            "Escalated",
            decision.priority,
            reason="escalated to advisor",
        )
        audit.emit("handoff_created", session.customer_id, trace_id, ip)
        reply = _handoff_for(record, decision.reason_key)
    else:
        reply = _resolve_and_open(decision, request, session, trace_id, ip)
    return _respond(reply)


def _respond(reply: ChatReply) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK, content=reply.model_dump(mode="json")
    )


def _candidate(row: GoldRow, policy, today) -> CandidateTransaction:  # type: ignore[no-untyped-def]
    eligible, reason = check_eligibility(row, policy, today)
    return CandidateTransaction(
        reference=row.reference,
        amount=row.amount,
        currency=row.currency,
        merchant=row.merchant,
        date=row.date,
        eligible=eligible,
        ineligibleKey=None if eligible else "candidateOutOfWindow",
    )


def _clarify(
    request: Request,
    session: Session,
    message_key: str,
    missing: str = "transaction",
    rows: list[GoldRow] | None = None,
    facts: StatedFacts | None = None,
) -> Clarification:
    policy = getattr(request.app.state, "policy", None)
    today = get_reference_date(request)
    available = rows if rows is not None else get_gold(request).list_for_customer(
        session.customer_id
    )
    ordered = rank_candidates(facts, available) if facts is not None else available
    return Clarification(
        message_key=message_key,
        missing=missing,
        candidates=[
            _candidate(row, policy, today) for row in ordered[:MAX_CANDIDATES]
        ],
    )


def _resolve_and_open(
    decision: OpenCaseDecision,
    request: Request,
    session: Session,
    trace_id: str,
    ip: str,
) -> ChatReply:
    """Ground the statement before creating anything. Never guess a transaction."""
    gold = get_gold(request)
    rows = gold.list_for_customer(session.customer_id)
    reference_year = get_reference_date(request).year

    if decision.pre_created_id is not None:
        return _open_reference(
            "", request, session, trace_id, ip, pre_created_id=decision.pre_created_id
        )

    merchants = [row.merchant for row in rows]
    facts = extract_facts(decision.statement, reference_year, merchants)
    result = ground(facts, rows, reference_year)
    if result.outcome != "matched" or result.match is None:
        key = (
            "clarifyAmbiguous"
            if result.outcome == "ambiguous"
            else "clarifyNotFound"
        )
        get_audit(request).emit(
            "grounding_ambiguous" if result.outcome == "ambiguous" else "grounding_none",
            session.customer_id,
            trace_id,
            ip,
        )
        return _clarify(
            request,
            session,
            key,
            rows=result.candidates if result.candidates else rows,
            facts=facts,
        )
    return _open_reference(
        result.match.reference, request, session, trace_id, ip
    )


def _open_reference(
    reference: str,
    request: Request,
    session: Session,
    trace_id: str,
    ip: str,
    pre_created_id: str | None = None,
) -> ChatReply:
    result = get_disputes(request).create(
        session.customer_id,
        reference,
        f"chat-{trace_id}",
        trace_id,
        ip,
        pre_created_id=pre_created_id,
    )
    if result.outcome == "created":
        return _confirmation_from(result)
    if result.outcome == "verified_failed":
        assert result.case is not None
        return _handoff_for(result.case, "handoffUnverified")
    row = get_gold(request).get(reference, session.customer_id)
    record = get_cases(request).create(
        session.customer_id,
        row.amount if row else "0.00",
        row.currency if row else "MXN",
        row.merchant if row else "unknown",
        row.date if row else get_reference_date(request).isoformat(),
        "Escalated",
        "High",
        reason=result.reason_key,
    )
    get_audit(request).emit("handoff_created", session.customer_id, trace_id, ip)
    return _handoff_for(record, result.reason_key, result.reason_detail)
