"""Advisor queue: escalated cases as summaries, claim and state change."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.auth.models import Session
from app.auth.roles import require_role
from app.auth.router import _client_ip, _trace_id, get_audit
from app.chat.stores import CaseRecord, CaseStore

router = APIRouter(prefix="/advisor", tags=["advisor"])

ALLOWED_STATES = ("InReview", "Resolved", "Closed")


class StateChange(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    state: str = Field(pattern="^(InReview|Resolved|Closed)$")


def get_cases(request: Request) -> CaseStore:
    return request.app.state.cases


def _summary(record: CaseRecord) -> dict:
    # Minimum privilege: case-necessary fields only, no transcript, no profile.
    return {
        "reference": f"HO-{record.case_id}",
        "case_id": record.case_id,
        "customer_id": record.customer_id,
        "transaction": {
            "amount": record.amount,
            "currency": record.currency,
            "merchant": record.merchant,
            "date": record.date,
        },
        "state": record.state,
        "priority": record.priority,
        "reason": record.reason,
        "owner": record.owner,
        "created_at": record.created_at.isoformat(),
    }


@router.get("/cases")
def list_cases(
    request: Request, session: Session = Depends(require_role("advisor"))
) -> JSONResponse:
    records = get_cases(request).list_escalated()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"cases": [_summary(r) for r in records]},
    )


@router.post("/cases/{case_id}/claim")
def claim_case(
    case_id: str, request: Request, session: Session = Depends(require_role("advisor"))
) -> JSONResponse:
    cases = get_cases(request)
    current = cases.get(case_id)
    if current is None or current.state != "Escalated":
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Case not found"}
        )
    record = cases.update(case_id, "InReview", owner=session.customer_id)
    assert record is not None
    get_audit(request).emit("case_claimed", session.customer_id, _trace_id(request), _client_ip(request))
    return JSONResponse(status_code=status.HTTP_200_OK, content=_summary(record))


@router.post("/cases/{case_id}/state")
def change_state(
    case_id: str,
    body: StateChange,
    request: Request,
    session: Session = Depends(require_role("advisor")),
) -> JSONResponse:
    record = get_cases(request).update(case_id, body.state)
    if record is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Case not found"}
        )
    get_audit(request).emit(
        "case_state_changed", session.customer_id, _trace_id(request), _client_ip(request)
    )
    return JSONResponse(status_code=status.HTTP_200_OK, content=_summary(record))
