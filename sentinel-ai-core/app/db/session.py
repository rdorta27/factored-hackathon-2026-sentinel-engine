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
    """Create the engine and every table (idempotent).

    The operational database holds sessions and conversation state, so the
    file is owner-only (``0600``, inherited by its WAL sidecars) and a folder
    created here is ``0700``; an existing folder is left as is (REQ-0027).
    """
    target = Path(path) if path is not None else db_path()
    if not target.parent.exists():
        target.parent.mkdir(parents=True, mode=0o700)
    # Created owner-only before SQLite opens it; SQLite gives the WAL and SHM
    # sidecars the same mode as the database file.
    os.close(os.open(target, os.O_CREAT | os.O_RDWR, 0o600))
    os.chmod(target, 0o600)
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
    _ensure_columns(engine)
    return engine


def _ensure_columns(engine: Engine) -> None:
    """Add columns that predate the current model, idempotently.

    ``create_all`` never alters an existing table, so a database created
    before ``dispute_cases.trace_id`` would miss it. The advisor trace route
    treats the missing value as "unavailable"; this keeps an old file usable.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "dispute_cases" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("dispute_cases")}
    if "trace_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE dispute_cases ADD COLUMN trace_id VARCHAR(64)"))
