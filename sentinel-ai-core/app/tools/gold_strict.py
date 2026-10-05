"""Strict Gold mode (REQ-0039, REQ-0052).

With ``SENTINEL_GOLD_REQUIRED`` on, the service refuses to start when Gold
is missing or older than ``SENTINEL_GOLD_MAX_AGE_HOURS`` (default 24). Off
by default: the service falls back to the labelled mock, and ``/health``
names ``gold_source`` mock. The public link keeps it off on purpose: it
serves the mock (decision 019).
"""

from __future__ import annotations

import logging
import os
import time

log = logging.getLogger("sentinel.gold")

REQUIRED_ENV = "SENTINEL_GOLD_REQUIRED"
MAX_AGE_ENV = "SENTINEL_GOLD_MAX_AGE_HOURS"
DEFAULT_MAX_AGE_H = 24.0


def strict_enabled() -> bool:
    return os.environ.get(REQUIRED_ENV, "").strip().lower() in ("1", "true", "on", "yes")


def max_age_h() -> float:
    try:
        return float(os.environ.get(MAX_AGE_ENV, "") or DEFAULT_MAX_AGE_H)
    except ValueError:
        return DEFAULT_MAX_AGE_H


def gold_files_mtime() -> float | None:
    """Newest modification time of the Gold files, or None when absent."""
    from app.services import gold_service

    db_file = gold_service.gold_duckdb_path()
    if db_file is not None:
        return db_file.stat().st_mtime
    gold_dir = gold_service._gold_path()
    if not gold_dir.is_dir():
        return None
    mtimes = [path.stat().st_mtime for path in gold_dir.rglob("*") if path.is_file()]
    return max(mtimes) if mtimes else None


def check(source: str, mtime: float | None, now: float, limit_h: float) -> None:
    """Raise when strict mode must refuse to start; pass silently otherwise."""
    if source == "mock":
        raise RuntimeError(
            f"{REQUIRED_ENV} is on but Gold resolved to the labelled mock: "
            "point SENTINEL_GOLD_DUCKDB or SENTINEL_GOLD_DIR at fresh Gold"
        )
    if mtime is None:
        raise RuntimeError(f"{REQUIRED_ENV} is on but no Gold file is readable")
    age_h = (now - mtime) / 3600.0
    if age_h > limit_h:
        raise RuntimeError(
            f"{REQUIRED_ENV} is on but Gold is {age_h:.1f}h old "
            f"(limit {limit_h:.1f}h from {MAX_AGE_ENV})"
        )


def enforce_strict_gold(source: str) -> None:
    """Refuse to start under strict mode with missing or stale Gold."""
    if not strict_enabled():
        return
    check(source, gold_files_mtime(), time.time(), max_age_h())
    log.info("strict Gold mode: source=%s is fresh", source)
