import os

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.session.models import Session
from app.session.service import (
    InvalidCredentials,
    LockedOut,
    SessionExpired,
    SessionService,
    UnknownSession,
)

SESSION_COOKIE = "sentinel_session"
router = APIRouter(prefix="/session", tags=["session"])

_GENERIC = {"detail": "Invalid credentials"}
_LOCKED = {"detail": "Too many failed attempts. Try again later."}


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    login: str = Field(min_length=4, max_length=32, pattern=r"^[A-Za-z0-9\-]+$")
    password: str = Field(min_length=1, max_length=128)


def _secure() -> bool:
    return os.environ.get("SENTINEL_SECURE_COOKIES", "false").lower() == "true"


def _ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _trace(request: Request) -> str:
    return getattr(request.state, "trace_id", "unknown")


def get_service(request: Request) -> SessionService:
    return request.app.state.session_service


def require_session(request: Request) -> Session:
    token = request.cookies.get(SESSION_COOKIE)
    trace_id = _trace(request)
    ip = _ip(request)
    if token is None:
        request.app.state.audit.emit("access_denied", None, trace_id, ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return get_service(request).validate(token, trace_id, ip)
    except SessionExpired:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    except UnknownSession:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


@router.post("/login")
def login(body: LoginRequest, request: Request) -> JSONResponse:
    service = get_service(request)
    trace_id = _trace(request)
    ip = _ip(request)
    try:
        session = service.login(body.login, body.password, ip, trace_id)
    except LockedOut:
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=_LOCKED)
    except InvalidCredentials:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=_GENERIC,
            headers={"WWW-Authenticate": "Cookie"},
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
        secure=_secure(),
        path="/",
    )
    return response


@router.post("/logout")
def logout(request: Request, response: Response) -> JSONResponse:
    get_service(request).logout(request.cookies.get(SESSION_COOKIE), _trace(request), _ip(request))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "Logged out"})


@router.get("/me")
def me(session: Session = Depends(require_session)) -> dict[str, str]:
    return {"customer_id": session.customer_id, "country": session.country}
