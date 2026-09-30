import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from app.session.models import Session, UserRecord


class UserRepository(Protocol):
    def get_by_login(self, login: str) -> UserRecord | None: ...


class SessionStore(Protocol):
    def create(self, user: UserRecord, ttl: timedelta) -> Session: ...

    def get(self, token: str) -> Session | None: ...

    def revoke(self, token: str) -> None: ...

    def consume_expired(self, token: str) -> bool: ...


class JsonUserRepository:
    def __init__(self, fixture_path: str | Path) -> None:
        raw = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        self._users = {
            entry["login"]: UserRecord(
                customer_id=entry["customer_id"],
                country=entry["country"],
                kdf=entry["kdf"],
                salt_hex=entry["salt_hex"],
                hash_hex=entry["hash_hex"],
                role=entry.get("role", "customer"),
            )
            for entry in raw["users"]
        }

    def get_by_login(self, login: str) -> UserRecord | None:
        return self._users.get(login)


class InMemorySessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._expired_tokens: set[str] = set()

    def create(self, user: UserRecord, ttl: timedelta) -> Session:
        now = datetime.now(timezone.utc)
        session = Session(
            token=secrets.token_urlsafe(32),
            customer_id=user.customer_id,
            country=user.country,
            created_at=now,
            expires_at=now + ttl,
            role=user.role,
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
