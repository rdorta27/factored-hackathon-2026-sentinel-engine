"""
Operational SQLite database: sessions, conversation state and cases.

Synchronous SQLAlchemy 2.x over the stdlib ``sqlite3`` driver: the routes are
sync and run in FastAPI's threadpool, so no call blocks the event loop.
The same declarative models run on Postgres by changing the URL.

Path: ``SENTINEL_DB_PATH``, default ``var/sentinel.db`` next to the package
(gitignored). One file serves one instance; a deployment needs persistent
storage for it.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase

from app.observability.writer import var_dir

DB_PATH_ENV = "SENTINEL_DB_PATH"


class Base(DeclarativeBase):
    pass


def db_path() -> Path:
    override = os.environ.get(DB_PATH_ENV)
    return Path(override) if override else var_dir() / "sentinel.db"


def make_engine(path: Path | str | None = None) -> Engine:
    """Create the engine and every table (idempotent)."""
    target = Path(path) if path is not None else db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{target}",
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _pragmas(connection, _record):  # type: ignore[no-untyped-def]
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Import models so Base.metadata is populated before create_all.
    from app.models import conversation, dispute_case, session_state  # noqa: F401

    Base.metadata.create_all(engine)
    return engine
