"""Application factory: trace ids, shared services, and auth routes."""

import secrets
from pathlib import Path

from fastapi import FastAPI, Request

from app.audit.logger import AuditLogger
from app.auth import router as auth_router
from app.auth.ratelimit import AttemptTracker
from app.auth.repositories import InMemorySessionStore, JsonUserRepository
from app.auth.router import SESSION_COOKIE
from app.auth.service import AuthService
from app.admin.router import router as admin_router
from app.advisor.router import router as advisor_router
from app.chat import router as chat_router
from app.chat.orchestrator import MockOrchestrator
from app.chat.stores import InMemoryCaseStore
from app.disputes import router as disputes_router
from app.disputes.policy import DEMO_TODAY, DisputePolicy
from app.disputes.service import DisputeService
from app.gold.store import MockGoldStore
from app.ui.router import mount_ui

FIXTURE_PATH = Path(__file__).parent / "auth" / "mocks" / "users.json"


def create_app() -> FastAPI:
    app = FastAPI(title="Sentinel Login (test skeleton)")
    app.state.audit = AuditLogger()
    app.state.cases = InMemoryCaseStore()
    app.state.gold = MockGoldStore(as_of=DEMO_TODAY.isoformat())
    app.state.policy = DisputePolicy()
    app.state.disputes = DisputeService(
        app.state.gold, app.state.cases, app.state.policy, app.state.audit
    )
    app.state.orchestrator = MockOrchestrator(app.state.cases)
    app.state.auth_service = AuthService(
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

    app.include_router(auth_router.router)
    app.include_router(chat_router.router)
    app.include_router(advisor_router)
    app.include_router(admin_router)
    app.include_router(disputes_router.router)
    mount_ui(app)
    return app


app = create_app()

__all__ = ["SESSION_COOKIE", "app", "create_app"]
