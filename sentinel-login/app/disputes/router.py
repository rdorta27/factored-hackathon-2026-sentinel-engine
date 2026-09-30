"""Dispute creation endpoint: thin HTTP skin over the deterministic service."""

import uuid

from fastapi import Depends, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.routing import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.auth.models import Session
from app.auth.roles import require_customer
from app.auth.router import _client_ip, _trace_id
from app.chat.stores import CaseStore
from app.disputes.service import DisputeService

router = APIRouter(prefix="/api/v1/disputes", tags=["disputes"])


class DisputeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    transaction_ref: str = Field(pattern=r"^TXN-[0-9]{4}$")


def get_disputes(request: Request) -> DisputeService:
    return request.app.state.disputes


def get_cases(request: Request) -> CaseStore:
    return request.app.state.cases


@router.post("/create")
def create_dispute(
    body: DisputeCreateRequest,
    request: Request,
    session: Session = Depends(require_customer),
) -> JSONResponse:
    key = request.headers.get("Idempotency-Key") or f"single-{uuid.uuid4().hex}"
    result = get_disputes(request).create(
        session.customer_id,
        body.transaction_ref,
        key,
        _trace_id(request),
        _client_ip(request),
    )
    if result.outcome == "created":
        assert result.case is not None and result.proof is not None
        proof = result.proof
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "case_id": result.case.case_id,
                "state": result.case.state,
                # Raw values and keys only: the interface formats and translates.
                "display": {
                    "amount": proof.amount,
                    "currency": proof.currency,
                    "merchant": proof.merchant,
                    "referenceDate": proof.reference_date,
                    "slaDate": proof.sla_date,
                },
                "messages": {
                    "nextStep": "nextStepAdvisorReview",
                    "rule": proof.rule_key,
                    "queue": proof.queue_key,
                    "noFunds": proof.no_funds_key,
                },
                "verified": True,
                "source": "mock",
            },
        )
    if result.outcome == "refused":
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "reason_key": result.reason_key,
                "reason_detail": result.reason_detail,
            },
        )
    handoff_case = result.case
    assert handoff_case is not None
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "reason_key": result.reason_key,
            "handoff": {"reference": f"HO-{handoff_case.case_id}"},
        },
    )


@router.get("/{case_id}/receipt")
def get_receipt(
    case_id: str, request: Request, session: Session = Depends(require_customer)
) -> PlainTextResponse:
    record = get_cases(request).get(case_id)
    if record is None or record.customer_id != session.customer_id:
        return PlainTextResponse(
            status_code=status.HTTP_404_NOT_FOUND, content="Receipt not found"
        )
    text = get_disputes(request).build_receipt(record)
    return PlainTextResponse(status_code=status.HTTP_200_OK, content=text)
