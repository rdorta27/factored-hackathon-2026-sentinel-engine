"""Login attempt limiting per customer id and per source IP."""

from datetime import datetime, timedelta, timezone

MAX_FAILURES = 5
LOCKOUT_DURATION = timedelta(minutes=15)


class AttemptTracker:
    """Counts consecutive failures; locks out after too many."""

    def __init__(self) -> None:
        self._failures: dict[str, list[datetime]] = {}

    def _prune(self, key: str, now: datetime) -> list[datetime]:
        recent = [t for t in self._failures.get(key, []) if now - t < LOCKOUT_DURATION]
        self._failures[key] = recent
        return recent

    def is_locked(self, *keys: str) -> bool:
        now = datetime.now(timezone.utc)
        return any(len(self._prune(key, now)) >= MAX_FAILURES for key in keys)

    def record_failure(self, *keys: str) -> None:
        now = datetime.now(timezone.utc)
        for key in keys:
            self._failures.setdefault(key, []).append(now)

    def reset(self, *keys: str) -> None:
        for key in keys:
            self._failures.pop(key, None)
