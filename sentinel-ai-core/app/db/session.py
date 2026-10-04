"""
Operational SQLite database: sessions, conversation state and cases.

Synchronous SQLAlchemy 2.x over the stdlib ``sqlite3`` driver: the routes are
sync and run in FastAPI's threadpool, so no call blocks the event loop.
The same declarative models run on Postgres by changing the URL.

Path: ``SENTINEL_DB_PATH``, default ``var/sentinel.db`` next to the package
(gitignored). One file serves one instance. ``SENTINEL_SQLITE_JOURNAL``
selects the journal mode (``WAL`` by default, ``DELETE`` on a file share).
Startup fails if the directory is not writable.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase

from app.observability.writer import require_writable, var_dir

DB_PATH_ENV = "SENTINEL_DB_PATH"
JOURNAL_ENV = "SENTINEL_SQLITE_JOURNAL"
_JOURNAL_MODES = frozenset({"DELETE", "WAL"})


class Base(DeclarativeBase):
    pass


def db_path() -> Path:
    override = os.environ.get(DB_PATH_ENV)
    return Path(override) if override else var_dir() / "sentinel.db"


def journal_mode() -> str:
    """``WAL`` unless ``SENTINEL_SQLITE_JOURNAL`` names ``DELETE`` or ``WAL``."""
    raw = os.environ.get(JOURNAL_ENV, "WAL").strip().upper()
    if raw not in _JOURNAL_MODES:
        raise ValueError(f"{JOURNAL_ENV} must be DELETE or WAL, got {raw!r}")
    return raw


def make_engine(path: Path | str | None = None) -> Engine:
    """Create the engine and every table (idempotent).

    The operational database holds sessions and conversation state, so the
    file is owner-only (``0600``, inherited by its WAL sidecars) and a folder
    created here is ``0700``; an existing folder is left as is (REQ-0027).
    """
    target = Path(path) if path is not None else db_path()
    require_writable(target.parent)
    mode = journal_mode()
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
        cursor.execute(f"PRAGMA journal_mode={mode}")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Import models so Base.metadata is populated before create_all.
    from app.models import conversation, dispute_case, session_state  # noqa: F401

    Base.metadata.create_all(engine)
    return engine
