"""Server-side role checks. Frontend gating alone never grants access."""

from collections.abc import Callable

from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException

from app.auth.models import Session
from app.auth.router import _client_ip, _trace_id, get_audit, require_session

ROLE_LEVELS = {"customer": 1, "advisor": 2, "admin": 3}


def require_customer(
    request: Request, session: Session = Depends(require_session)
) -> Session:
    """Customer-only endpoints (chat, disputes). Anything else gets 403."""
    if session.role != "customer":
        get_audit(request).emit(
            "access_denied", session.customer_id, _trace_id(request), _client_ip(request)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Customers only"
        )
    return session


def require_role(minimum: str) -> Callable[[Request], Session]:
    """Dependency factory: session role must reach at least `minimum`."""

    def check(request: Request, session: Session = Depends(require_session)) -> Session:
        if ROLE_LEVELS.get(session.role, 0) < ROLE_LEVELS[minimum]:
            get_audit(request).emit(
                "access_denied", session.customer_id, _trace_id(request), _client_ip(request)
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
        return session

    return check
