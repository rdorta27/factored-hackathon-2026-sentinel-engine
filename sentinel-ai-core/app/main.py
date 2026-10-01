"""
Sentinel AI Core – FastAPI application entry point.

One app, one API under ``/api/v1``: auth, transactions, chat, disputes,
handoffs (advisor) and health, plus the page at ``/ui/`` (customer chat and
advisor view). The business path is always orchestrator →
policy → session-bound tools; only the adapters behind the ports change:

  - Gold: DuckDB view when readable, in-memory mock otherwise
    (``SENTINEL_GOLD_SOURCE``, see ``app.tools.gold_duckdb``).
  - Model: keyword baseline by default, any ``ModelPort`` via ``create_app(model=...)``.
  - Users: test fixture, or ``SENTINEL_USERS_PATH`` (keep real-Gold users under
    the gitignored ``data/``).
  - State (sessions, conversation, cases): SQLite at ``SENTINEL_DB_PATH`` or in
    memory (``SENTINEL_STATE_BACKEND`` = ``sqlite`` default | ``memory``).

Exports:
  - ``app``: the served instance (``uvicorn app.main:app``).
  - ``create_app()``: factory for isolated instances (tests, eval runner).
  - ``SESSION_COOKIE``: the cookie name used by the session layer.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

from fastapi import APIRouter, FastAPI, Request

from app.ai.port import ModelPort
from app.session.router import SESSION_COOKIE  # re-exported for test imports

__all__ = ["app", "create_app", "SESSION_COOKIE"]

_FIXTURE_PATH = Path(__file__).parent / "session" / "fixtures" / "users.json"


def create_app(model: ModelPort | None = None, state_backend: str | None = None) -> FastAPI:
    """
    Create a fully wired application instance.

    Each call returns an independent FastAPI app with its own in-memory state,
    so test cases can spin up isolated instances. The model is selectable per
    app (keyword baseline by default) without editing code. ``state_backend``
    overrides ``SENTINEL_STATE_BACKEND`` (the offline eval replays each case on
    ``memory`` so cases never share a database).
    """
    from app.ai.demo import DemoModel
    from app.observability import Recorder
    from app.routers.demo_chat import router as chat_router
    from app.routers.disputes import router as disputes_router
    from app.routers.handoffs import router as handoffs_router
    from app.routers.demo_transactions import router as txn_router
    from app.routers.ui import mount_ui
    from app.session.audit import AuditLogger
    from app.session.clock import reference_date as get_reference_date
    from app.session.limits import AttemptTracker
    from app.session.router import router as session_router
    from app.session.service import SessionService
    from app.session.store import InMemorySessionStore, JsonUserRepository, SqliteSessionStore
    from app.state.cases import InMemoryCaseRepository, SqliteCaseRepository
    from app.state.conversation import InMemoryConversationStore, SqliteConversationStore
    from app.tools.gold_duckdb import select_gold

    application = FastAPI(title="Sentinel AI Core", version="0.1.0")

    @application.middleware("http")
    async def trace_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.trace_id = secrets.token_hex(8)
        response = await call_next(request)
        response.headers["X-Trace-Id"] = request.state.trace_id
        return response

    recorder = Recorder()
    ref_date = get_reference_date()
    audit = AuditLogger(recorder)
    demo_auth = os.environ.get("SENTINEL_DEMO_AUTH", "0") == "1"
    users = JsonUserRepository(Path(os.environ.get("SENTINEL_USERS_PATH") or _FIXTURE_PATH), demo_roles=demo_auth)
    state_backend = (state_backend or os.environ.get("SENTINEL_STATE_BACKEND", "sqlite")).lower()
    if state_backend == "memory":
        sessions = InMemorySessionStore()
        conversation_store = InMemoryConversationStore()
        cases = InMemoryCaseRepository()
    else:
        from app.db.session import make_engine

        state_backend = "sqlite"
        engine = make_engine()
        sessions = SqliteSessionStore(engine, ref_date)
        conversation_store = SqliteConversationStore(engine)
        cases = SqliteCaseRepository(engine)
    # Login attempts stay in memory: per process, documented limit with several workers.
    attempts = AttemptTracker()
    service = SessionService(users, sessions, attempts, audit)
    gold, gold_source = select_gold(as_of=ref_date.isoformat())

    application.state.recorder = recorder
    application.state.audit = audit
    application.state.model = model if model is not None else DemoModel()
    application.state.session_service = service
    application.state.gold = gold
    application.state.gold_source = gold_source
    application.state.reference_date = ref_date
    application.state.state_backend = state_backend
    application.state.conversation_store = conversation_store
    application.state.cases = cases
    # In memory, the live conversations dict (tests count threads through it).
    application.state.conversations = getattr(conversation_store, "items", {})
    # One CaseTools per customer (opaque key): write side of the tool port.
    application.state.memories = {}

    ops = APIRouter(prefix="/api/v1", tags=["ops"])

    @ops.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "gold_source": gold_source,
            "state_backend": state_backend,
            "reference_date": ref_date.isoformat(),
        }

    application.include_router(session_router)
    application.include_router(txn_router)
    application.include_router(chat_router)
    application.include_router(disputes_router)
    application.include_router(handoffs_router)
    application.include_router(ops)
    mount_ui(application)

    return application


app = create_app()
