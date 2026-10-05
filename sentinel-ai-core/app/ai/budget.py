"""Daily model spend guard (REQ-0026, REQ-0055).

``SENTINEL_LLM_DAILY_BUDGET_USD`` caps model spend per process per day. When
the spend of the day reaches the cap, the keyword baseline answers the next
turns and the turn log records ``budget`` as the route. The running total
lives in the state database file, so a restart keeps it. Unset, blank or
non-positive means off: the public link serves the model with no cap.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from datetime import date
from pathlib import Path

log = logging.getLogger("sentinel.model")

BUDGET_ENV = "SENTINEL_LLM_DAILY_BUDGET_USD"
BUDGET_ROUTE = "budget"


def budget_from_env() -> float | None:
    """The daily cap in USD, or None when the guard is off."""
    raw = os.environ.get(BUDGET_ENV, "").strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        log.warning("%s is not a number (%r); the spend guard stays off", BUDGET_ENV, raw)
        return None
    if value <= 0:
        return None
    return value


class BudgetGuard:
    """Per-process, per-day spend totals in the state database file."""

    def __init__(self, budget_usd: float | None, path: Path | str | None = None, day: str | None = None) -> None:
        self._budget_usd = budget_usd
        self._path = Path(path) if path is not None else None
        self._day = day or date.today().isoformat()

    @property
    def enabled(self) -> bool:
        return self._budget_usd is not None and self._budget_usd > 0

    def _connect(self) -> sqlite3.Connection:
        from app.db.session import db_path

        target = self._path or db_path()
        connection = sqlite3.connect(target)
        connection.execute(
            "CREATE TABLE IF NOT EXISTS daily_model_spend (day TEXT PRIMARY KEY, total_usd REAL NOT NULL)"
        )
        return connection

    def spent_usd(self) -> float:
        """Spend recorded for the day, 0 when the guard is off or nothing ran."""
        if not self.enabled:
            return 0.0
        with self._connect() as connection:
            row = connection.execute(
                "SELECT total_usd FROM daily_model_spend WHERE day = ?", (self._day,)
            ).fetchone()
        return float(row[0]) if row else 0.0

    def exhausted(self) -> bool:
        spent = self.spent_usd()
        if self.enabled and spent >= (self._budget_usd or 0.0):
            log.warning("daily model budget reached (%.4f USD); the baseline answers", spent)
            return True
        return False

    def record(self, cost_usd: float) -> None:
        """Add one model call cost to the day total. No-op when off."""
        if not self.enabled or cost_usd <= 0:
            return
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO daily_model_spend (day, total_usd) VALUES (?, ?) "
                "ON CONFLICT(day) DO UPDATE SET total_usd = total_usd + excluded.total_usd",
                (self._day, cost_usd),
            )
