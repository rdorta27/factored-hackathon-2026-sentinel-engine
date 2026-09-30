"""
Sentinel AI Core – FastAPI application entry point.

Exports two public symbols used by the test suite:
  - ``create_app()``: factory that wires the full demo/session-based application
    (cookie auth, in-memory Gold store, orchestrator-driven chat).
  - ``SESSION_COOKIE``: the cookie name used by the session layer.

The module-level ``app`` instance uses the DuckDB Gold layer and the real
Anthropic LLM; it is the production-mode entry point.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI

from app.db.session import init_db
from app.routers import chat, disputes, transactions
from app.session.router import SESSION_COOKIE  # re-exported for test imports

__all__ = ["app", "create_app", "SESSION_COOKIE"]

_FIXTURE_PATH = Path(__file__).parent / "session" / "fixtures" / "users.json"


# ---------------------------------------------------------------------------
# Production app (DuckDB Gold layer + real Anthropic LLM)
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield


app = FastAPI(
    title="Sentinel AI Core",
    version="0.1.0",
    description="Dispute intake backend connecting FastAPI, DuckDB Gold layer, and Anthropic LLM.",
    lifespan=lifespan,
)

app.include_router(transactions.router)
app.include_router(disputes.router)
app.include_router(chat.router)


@app.get("/health", tags=["ops"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Demo / test factory (in-memory Gold store + DemoModel, no external services)
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """
    Create a fully wired demo application instance.

    Each call returns an independent FastAPI app with its own in-memory state,
    so test cases can spin up isolated instances.
    """
    from app.routers.auth_compat import api_v1_auth_router, auth_router
    from app.routers.demo_chat import router as chat_router
    from app.routers.demo_transactions import router as txn_router
    from app.routers.ui import mount_ui
    from app.session.audit import AuditLogger
    from app.session.clock import reference_date as get_reference_date
    from app.session.limits import AttemptTracker
    from app.session.router import router as session_router
    from app.session.service import SessionService
    from app.session.store import InMemorySessionStore, JsonUserRepository
    from app.tools.gold import MockGoldStore

    demo = FastAPI(title="Sentinel AI Core (demo)", version="0.1.0")

    ref_date = get_reference_date()
    audit = AuditLogger()
    users = JsonUserRepository(_FIXTURE_PATH)
    sessions = InMemorySessionStore()
    attempts = AttemptTracker()
    service = SessionService(users, sessions, attempts, audit)
    gold = MockGoldStore(as_of=ref_date.isoformat())

    demo.state.audit = audit
    demo.state.session_service = service
    demo.state.gold = gold
    demo.state.reference_date = ref_date
    # Per-session dicts keyed by cookie token.
    demo.state.memories = {}        # token → InMemoryTools
    demo.state.conversations = {}   # token → ConversationState

    demo.include_router(session_router)
    demo.include_router(auth_router)          # POST /auth/login alias
    demo.include_router(api_v1_auth_router)   # POST /api/v1/auth/login alias
    demo.include_router(txn_router)
    demo.include_router(chat_router)
    mount_ui(demo)

    return demo
