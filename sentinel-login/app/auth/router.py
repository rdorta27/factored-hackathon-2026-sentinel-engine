"""Auth endpoints. Identity always comes from the session, never the body."""

import os

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import JSONResponse

from app.audit.logger import AuditLogger
from app.auth.models import Session
from app.auth.schemas import LoginRequest, MeResponse
from app.auth.service import (
    AuthService,
    InvalidCredentials,
    LockedOut,
    SessionExpired,
    UnknownSession,
)

SESSION_COOKIE = "sentinel_session"

router = APIRouter(prefix="/auth", tags=["auth"])

_GENERIC_LOGIN_ERROR = {"detail": "Invalid credentials"}
_LOCKED_ERROR = {"detail": "Too many failed attempts. Try again later."}


def _cookie_secure() -> bool:
    return os.environ.get("SENTINEL_SECURE_COOKIES", "false").lower() == "true"


def _client_ip(request: Request) -> str:
    # request.client.host may be the platform proxy; the trusted source is
    # defined at deploy time. Never trust X-Forwarded-For by default.
    return request.client.host if request.client else "unknown"


def _trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", "unknown")


def get_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_audit(request: Request) -> AuditLogger:
    return request.app.state.audit


def require_session(request: Request) -> Session:
    """Resolve the customer from the session cookie. Reusable by later routes."""
    from fastapi import HTTPException

    token = request.cookies.get(SESSION_COOKIE)
    service = get_service(request)
    trace_id = _trace_id(request)
    ip = _client_ip(request)
    if token is None:
        get_audit(request).emit("access_denied", None, trace_id, ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    try:
        return service.validate(token, trace_id, ip)
    except SessionExpired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired"
        )
    except UnknownSession:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )


@router.post("/login")
def login(body: LoginRequest, request: Request) -> JSONResponse:
    service = get_service(request)
    trace_id = _trace_id(request)
    ip = _client_ip(request)
    try:
        session = service.login(body.customer_id, body.password, ip, trace_id)
    except LockedOut:
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=_LOCKED_ERROR)
    except InvalidCredentials:
        headers = {"WWW-Authenticate": "Cookie"}
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=_GENERIC_LOGIN_ERROR,
            headers=headers,
        )
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"detail": "Logged in", "role": session.role},
    )
    response.set_cookie(
        SESSION_COOKIE,
        session.token,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
        path="/",
    )
    return response


@router.post("/logout")
def logout(request: Request, response: Response) -> JSONResponse:
    service = get_service(request)
    service.logout(
        request.cookies.get(SESSION_COOKIE), _trace_id(request), _client_ip(request)
    )
    response.delete_cookie(SESSION_COOKIE, path="/")
    return JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "Logged out"})


@router.get("/me", response_model=MeResponse)
def me(session: Session = Depends(require_session)) -> MeResponse:
    return MeResponse(customer_id=session.customer_id)
