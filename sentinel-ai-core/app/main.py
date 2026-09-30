import secrets
from pathlib import Path

from fastapi import FastAPI, Request

from app.observability import Recorder
from app.routers.chat import router as chat_router
from app.routers.ui import mount_ui
from app.routers.transactions import router as transactions_router
from app.session.audit import AuditLogger
from app.session.clock import reference_date
from app.session.limits import AttemptTracker
from app.session.router import SESSION_COOKIE, router as session_router
from app.session.service import SessionService
from app.session.store import InMemorySessionStore, JsonUserRepository
from app.tools.gold import MockGoldStore

FIXTURE_PATH = Path(__file__).parent / "session" / "fixtures" / "users.json"


def create_app() -> FastAPI:
    app = FastAPI(title="Sentinel Engine")
    app.state.recorder = Recorder()
    app.state.audit = AuditLogger(app.state.recorder)
    app.state.reference_date = reference_date()
    app.state.gold = MockGoldStore(as_of=app.state.reference_date.isoformat())
    app.state.conversations = {}
    app.state.memories = {}
    app.state.session_service = SessionService(
        JsonUserRepository(FIXTURE_PATH),
        InMemorySessionStore(),
        AttemptTracker(),
        app.state.audit,
    )

    @app.middleware("http")
    async def trace_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.trace_id = secrets.token_hex(8)
        response = await call_next(request)
        response.headers["X-Trace-Id"] = request.state.trace_id
        return response

    app.include_router(session_router)
    app.include_router(transactions_router)
    app.include_router(chat_router)
    mount_ui(app)
    return app


app = create_app()

__all__ = ["SESSION_COOKIE", "app", "create_app"]
