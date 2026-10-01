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
router = APIRouter(prefix="/api/v1/session", tags=["session"])

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
    tid = getattr(request.state, "trace_id", None)
    if tid and len(tid) == 16:
        return tid
    import secrets
    return secrets.token_hex(8)


def get_service(request: Request) -> SessionService:
    return request.app.state.session_service


def require_session(request: Request) -> Session:
    token = request.cookies.get(SESSION_COOKIE)
    trace_id = _trace(request)
    ip = _ip(request)
    if token is None:
        request.app.state.audit.emit("access_denied", trace_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        return get_service(request).validate(token, trace_id, ip)
    except SessionExpired:
        # Retention: the conversation (customer turns included) dies with the session.
        request.app.state.conversation_store.delete(token)
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
    token = request.cookies.get(SESSION_COOKIE)
    get_service(request).logout(token, _trace(request), _ip(request))
    if token is not None:
        request.app.state.conversation_store.delete(token)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "Logged out"})


@router.get("/me")
def me(session: Session = Depends(require_session)) -> dict[str, str]:
    # The browser never needs the customer identifier; identity stays server-side.
    return {"role": session.role, "country": session.country}
