"""
Operational SQLite database setup.

Uses SQLAlchemy 2.x with aiosqlite for async I/O.  All synchronous
CPU/DB-bound calls are offloaded via asyncio.to_thread() where needed
outside this module to keep the FastAPI event loop unblocked.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

_DB_PATH = Path(os.getenv("SENTINEL_DB_PATH", "sentinel_operational.db"))
_DATABASE_URL = f"sqlite+aiosqlite:///{_DB_PATH}"

engine = create_async_engine(_DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    """Create all tables defined by ORM models (idempotent)."""
    # Import models so Base.metadata is populated before create_all
    from app.models import dispute_case, session_state  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:  # type: ignore[return]
    """FastAPI dependency that yields a managed AsyncSession."""
    async with AsyncSessionLocal() as session:
        yield session
