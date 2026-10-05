import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from urllib.parse import urlsplit

from app.session.models import Session
from app.session.service import (
    InvalidCredentials,
    LockedOut,
    SessionExpired,
    SessionService,
    UnknownSession,
)

SESSION_COOKIE = "sentinel_session"
router = APIRouter(prefix="/api/v1/auth", tags=["session"])

_GENERIC = {"detail": "Invalid credentials"}
_LOCKED = {"detail": "Too many failed attempts. Try again later."}
_CSRF = {"detail": "CSRF check failed"}

# The session cookie lifetime mirrors the server-side TTL (service.SESSION_TTL).
SESSION_MAX_AGE = 30 * 60

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    login: str = Field(min_length=4, max_length=32, pattern=r"^[A-Za-z0-9\-]+$")
    password: str = Field(min_length=1, max_length=128)


def _secure() -> bool:
    # Secure by default (production is HTTPS); local HTTP dev sets
    # SENTINEL_SECURE_COOKIES=false explicitly. Tests do the same in conftest.
    return os.environ.get("SENTINEL_SECURE_COOKIES", "true").lower() != "false"


def _host_of(value: str) -> str:
    try:
        return (urlsplit(value).hostname or "").lower()
    except ValueError:
        return ""


def _csrf_ok(request: Request) -> bool:
    """Reject cross-site state-changing requests carrying the session cookie.

    Browsers always attach Origin (fetch/POST) or Referer on cross-site
    requests, while non-browser clients (tests, curl, smoke scripts) send
    neither and stay unaffected. Same-origin requests pass; anything else 403s.
    """
    if request.method in _SAFE_METHODS:
        return True
    if request.cookies.get(SESSION_COOKIE) is None:
        return True
    host = (request.headers.get("host") or "").split(":")[0].lower()
    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    if origin is None and referer is None:
        return True
    if origin is not None and _host_of(origin) != host:
        return False
    if referer is not None and _host_of(referer) != host:
        return False
    return True


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
    if not _csrf_ok(request):
        request.app.state.audit.emit("access_denied", trace_id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF check failed")
    try:
        return get_service(request).validate(token, trace_id, ip)
    except SessionExpired:
        # Retention: the conversation (customer turns included) dies with the session.
        request.app.state.conversation_store.delete(token)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    except UnknownSession:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


def require_role(role: str):  # type: ignore[no-untyped-def]
    """Dependency: a live session whose stored role is ``role``; otherwise 403 and ``access_denied``."""

    def dependency(request: Request, session: Session = Depends(require_session)) -> Session:
        if session.role != role:
            request.app.state.audit.emit("access_denied", _trace(request))
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return session

    return dependency


require_customer = require_role("customer")
require_advisor = require_role("advisor")


# One-click demo personas: fixture login plus the interface locale the
# evaluator sees. The ambiguous persona is CUST-0001 in pt-BR (decision 017:
# a pt-BR writer holds an MX, CO or AR account). No customer id reaches the
# browser: the persona id is the only thing the page sends.
_PERSONAS = {
    "normal": {"login": "CUST-0001", "locale": "es-MX"},
    "ambiguous": {"login": "CUST-0001", "locale": "pt-BR"},
    "high-amount": {"login": "CUST-0002", "locale": "es-CO"},
    "not-me": {"login": "CUST-0003", "locale": "es-AR"},
}


def _demo_enabled() -> bool:
    return os.environ.get("SENTINEL_DEMO_AUTH", "0") == "1"


def _personas_enabled() -> bool:
    """One-click personas. ``SENTINEL_DEMO_PERSONAS`` overrides the demo flag.

    Unset follows ``SENTINEL_DEMO_AUTH``, so local runs and tests do not change.
    The public link sets it to ``0`` and keeps the advisor role.
    """
    flag = os.environ.get("SENTINEL_DEMO_PERSONAS")
    if flag is None:
        return _demo_enabled()
    return flag == "1"


def _demo_cookie(response: JSONResponse, session: Session) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        session.token,
        httponly=True,
        samesite="lax",
        secure=_secure(),
        max_age=SESSION_MAX_AGE,
        path="/",
    )


@router.get("/demo")
def demo_personas() -> JSONResponse:
    """List the demo personas. 404 unless the persona flag is on."""
    if not _personas_enabled():
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "personas": [
                {"id": persona, "locale": spec["locale"]} for persona, spec in _PERSONAS.items()
            ]
        },
    )


@router.post("/demo/{persona}")
def demo_login(persona: str, request: Request) -> JSONResponse:
    """Sign in as a demo persona with one click: no password, customers only."""
    if not _personas_enabled():
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"})
    spec = _PERSONAS.get(persona)
    if spec is None:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Not found"})
    service = get_service(request)
    trace_id = _trace(request)
    try:
        session = service.login_demo(spec["login"], _ip(request), trace_id)
    except InvalidCredentials:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=_GENERIC,
            headers={"WWW-Authenticate": "Cookie"},
        )
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"detail": "Logged in", "role": session.role, "locale": spec["locale"]},
    )
    _demo_cookie(response, session)
    return response


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
        max_age=SESSION_MAX_AGE,
        path="/",
    )
    return response


@router.post("/logout")
def logout(request: Request) -> JSONResponse:
    token = request.cookies.get(SESSION_COOKIE)
    get_service(request).logout(token, _trace(request), _ip(request))
    if token is not None:
        request.app.state.conversation_store.delete(token)
    response = JSONResponse(status_code=status.HTTP_200_OK, content={"detail": "Logged out"})
    # The endpoint returns its own JSONResponse, so the cookie must be cleared
    # on it: the injected Response's headers would be discarded.
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=_secure())
    return response


@router.get("/me")
def me(session: Session = Depends(require_session)) -> dict[str, str]:
    # The browser never needs the customer identifier; identity stays server-side.
    return {"role": session.role, "country": session.country}
