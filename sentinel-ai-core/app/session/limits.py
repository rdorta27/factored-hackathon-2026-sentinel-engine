from datetime import datetime, timedelta, timezone

MAX_FAILURES = 5
LOCKOUT_DURATION = timedelta(minutes=15)

# Write budget for the authenticated business routes (chat, disputes): a
# human session never sends this many turns a minute, a script does. Login
# keeps its own failure lockout above; this counts successful writes.
MAX_WRITES_PER_WINDOW = 60
WRITE_WINDOW = timedelta(seconds=60)
_MAX_KEYS = 10_000


class AttemptTracker:
    def __init__(self) -> None:
        self._failures: dict[str, list[datetime]] = {}

    def _prune(self, key: str, now: datetime) -> list[datetime]:
        recent = [stamp for stamp in self._failures.get(key, []) if now - stamp < LOCKOUT_DURATION]
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


class RateLimiter:
    """Fixed-window counter per key (session token), one shared instance per app."""

    def __init__(self, max_events: int = MAX_WRITES_PER_WINDOW, window: timedelta = WRITE_WINDOW) -> None:
        self._max = max_events
        self._window = window
        self._events: dict[str, list[datetime]] = {}

    def allow(self, key: str) -> bool:
        now = datetime.now(timezone.utc)
        if len(self._events) > _MAX_KEYS:
            self._prune_all(now)
        recent = [stamp for stamp in self._events.get(key, []) if now - stamp < self._window]
        if len(recent) >= self._max:
            self._events[key] = recent
            return False
        recent.append(now)
        self._events[key] = recent
        return True

    def _prune_all(self, now: datetime) -> None:
        self._events = {
            key: [stamp for stamp in stamps if now - stamp < self._window]
            for key, stamps in self._events.items()
        }
        self._events = {key: stamps for key, stamps in self._events.items() if stamps}
