"""
Sentinel AI Core – FastAPI application entry point.

One app, one API under ``/api/v1``: auth, transactions, chat, disputes,
handoffs (advisor) and health, plus the page at ``/ui/`` (customer chat and
advisor view). The business path is always orchestrator →
policy → session-bound tools; only the adapters behind the ports change:

  - Gold: DuckDB view when readable, in-memory mock otherwise
    (``SENTINEL_GOLD_SOURCE``, see ``app.tools.gold_duckdb``).
  - Model: router_v2 with baseline fallback when ``SENTINEL_LLM_BASE_URL`` and
    ``SENTINEL_LLM_API_KEY`` are set (``app.ai.serving``), keyword baseline
    otherwise; any ``ModelPort`` via ``create_app(model=...)``.
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

from fastapi import APIRouter, FastAPI, Request, Response
from sqlalchemy import text

from app.ai.port import ModelPort
from app.session.router import SESSION_COOKIE  # re-exported for test imports

__all__ = ["app", "create_app", "SESSION_COOKIE"]

_FIXTURE_PATH = Path(__file__).parent / "session" / "fixtures" / "users.json"


def create_app(model: ModelPort | None = None, state_backend: str | None = None) -> FastAPI:
    """
    Create a fully wired application instance.

    Each call returns an independent FastAPI app with its own in-memory state,
    so test cases can spin up isolated instances. The model is selectable per
    app (see ``app.ai.serving``) without editing code. ``state_backend``
    overrides ``SENTINEL_STATE_BACKEND`` (the offline eval replays each case on
    ``memory`` so cases never share a database).
    """
    from app.ai.serving import model_from_env
    from app.observability import Recorder
    from app.routers.demo_chat import router as chat_router
    from app.routers.disputes import router as disputes_router
    from app.routers.handoffs import router as handoffs_router
    from app.routers.demo_transactions import router as txn_router
    from app.routers.ui import mount_ui
    from app.session.audit import AuditLogger
    from app.session.clock import reference_date as get_reference_date
    from app.session.limits import AttemptTracker, RateLimiter
    from app.session.router import router as session_router
    from app.session.service import SessionService
    from app.session.store import InMemorySessionStore, JsonUserRepository, SqliteSessionStore
    from app.state.cases import InMemoryCaseRepository, SqliteCaseRepository
    from app.state.conversation import InMemoryConversationStore, SqliteConversationStore
    from app.tools.faults import apply_gold_fault, apply_model_fault, apply_store_fault
    from app.tools.gold_duckdb import select_gold
    from app.tools.gold_strict import enforce_strict_gold, strict_enabled

    application = FastAPI(title="Sentinel AI Core", version="0.1.0")

    @application.middleware("http")
    async def trace_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.trace_id = secrets.token_hex(8)
        response = await call_next(request)
        response.headers["X-Trace-Id"] = request.state.trace_id
        # Transport hardening: clickjacking, MIME sniffing and referrer leaks
        # are mitigated for every response, including the served page.
        # HSTS is only honored on HTTPS; on local HTTP it is ignored.
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'deny'; "
            "base-uri 'self'; form-action 'self'"
        )
        return response

    recorder = Recorder()
    ref_date = get_reference_date()
    audit = AuditLogger(recorder)
    demo_auth = os.environ.get("SENTINEL_DEMO_AUTH", "0") == "1"
    users = JsonUserRepository(Path(os.environ.get("SENTINEL_USERS_PATH") or _FIXTURE_PATH), demo_roles=demo_auth)
    engine = None
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
    # Write budget for chat/disputes, also per process (same documented limit).
    write_limiter = RateLimiter()
    service = SessionService(users, sessions, attempts, audit)
    gold, gold_source = select_gold(as_of=ref_date.isoformat())
    # Strict mode refuses to start on missing or stale Gold (off by default).
    enforce_strict_gold(gold_source)
    # Fault injection for the frozen robustness run (SENTINEL_FAULT_*):
    # off by default, so production serves the real adapters.
    gold = apply_gold_fault(gold)

    application.state.recorder = recorder
    application.state.audit = audit
    application.state.model = apply_model_fault(model if model is not None else model_from_env())
    application.state.session_service = service
    application.state.write_limiter = write_limiter
    application.state.gold = gold
    application.state.gold_source = gold_source
    application.state.reference_date = ref_date
    application.state.state_backend = state_backend
    application.state.engine = engine
    application.state.conversation_store = conversation_store
    application.state.cases = apply_store_fault(cases)
    # In memory, the live conversations dict (tests count threads through it).
    application.state.conversations = getattr(conversation_store, "items", {})
    # One CaseTools per customer (opaque key): write side of the tool port.
    application.state.memories = {}

    ops = APIRouter(prefix="/api/v1", tags=["ops"])

    @ops.get("/health")
    def health(response: Response) -> dict[str, str]:
        # Strong health: the state store must answer, not only the process.
        # A probe that only sees "ok" would keep routing traffic to an
        # instance whose database file is gone or unwritable.
        status = "ok"
        if application.state.engine is not None:
            try:
                with application.state.engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
            except Exception:  # noqa: BLE001 - any store failure means not ready
                status = "unavailable"
                response.status_code = 503
        info = application.state.model.describe()
        return {
            "status": status,
            "model": info.model,
            "route": info.route,
            "prompt_version": info.prompt_version,
            "gold_source": gold_source,
            "gold_required": "on" if strict_enabled() else "off",
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
