"""Read-only observability. No conversation contents, only counts and audit."""

from collections import Counter

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.auth.models import Session
from app.auth.roles import require_role
from app.audit.logger import AuditLogger

router = APIRouter(prefix="/admin", tags=["admin"])

COUNTED_EVENTS = (
    "login_success",
    "login_failed",
    "login_locked",
    "logout",
    "session_expired",
    "access_denied",
    "case_opened",
    "handoff_created",
    "case_claimed",
    "case_state_changed",
)


def get_audit(request: Request) -> AuditLogger:
    return request.app.state.audit


@router.get("/audit")
def read_audit(
    request: Request, session: Session = Depends(require_role("admin"))
) -> JSONResponse:
    # Audit records never carry message text; only event metadata.
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"records": get_audit(request).records},
    )


@router.get("/metrics")
def read_metrics(
    request: Request, session: Session = Depends(require_role("admin"))
) -> JSONResponse:
    counts = Counter(r["event"] for r in get_audit(request).records)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"metrics": {event: counts.get(event, 0) for event in COUNTED_EVENTS}},
    )
