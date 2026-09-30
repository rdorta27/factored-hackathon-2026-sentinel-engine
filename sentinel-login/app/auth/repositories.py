"""Storage contracts and their first adapters.

The service layer depends only on the protocols below, so a real database
can replace the mock adapters without changing any contract.
"""

import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from app.auth.models import Session, UserRecord


class UserRepository(Protocol):
    """Lookup for test customers by id."""

    def get_by_customer_id(self, customer_id: str) -> UserRecord | None:
        ...


class SessionStore(Protocol):
    """Server-side session storage with expiry and revocation."""

    def create(self, customer_id: str, ttl: timedelta, role: str = "customer") -> Session:
        ...

    def get(self, token: str) -> Session | None:
        ...

    def revoke(self, token: str) -> None:
        ...

    def consume_expired(self, token: str) -> bool:
        """Return True once if the token existed but passed its expiry."""
        ...


class JsonUserRepository:
    """Mock adapter reading invented test users from a JSON fixture."""

    def __init__(self, fixture_path: str | Path) -> None:
        raw = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        self._users = {
            entry["customer_id"]: UserRecord(
                customer_id=entry["customer_id"],
                kdf=entry["kdf"],
                salt_hex=entry["salt_hex"],
                hash_hex=entry["hash_hex"],
                role=entry.get("role", "customer"),
            )
            for entry in raw["users"]
        }

    def get_by_customer_id(self, customer_id: str) -> UserRecord | None:
        return self._users.get(customer_id)


class InMemorySessionStore:
    """Single-process session store. Not shared across workers or restarts."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._expired_tokens: set[str] = set()

    def create(self, customer_id: str, ttl: timedelta, role: str = "customer") -> Session:
        now = datetime.now(timezone.utc)
        session = Session(
            token=secrets.token_urlsafe(32),
            customer_id=customer_id,
            created_at=now,
            expires_at=now + ttl,
            role=role,
        )
        self._sessions[session.token] = session
        return session

    def get(self, token: str) -> Session | None:
        session = self._sessions.get(token)
        if session is None:
            return None
        if datetime.now(timezone.utc) >= session.expires_at:
            self._sessions.pop(token, None)
            self._expired_tokens.add(token)
            return None
        return session

    def revoke(self, token: str) -> None:
        self._sessions.pop(token, None)
        self._expired_tokens.discard(token)

    def consume_expired(self, token: str) -> bool:
        if token in self._expired_tokens:
            self._expired_tokens.discard(token)
            return True
        return False
