import hashlib
import json
import secrets
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DbSession

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


class SqliteSessionStore:
    """Sessions in the operational database. Rows are keyed by a hash of the token."""

    def __init__(self, engine, reference_date: date) -> None:  # type: ignore[no-untyped-def]
        self._engine = engine
        self._reference_date = reference_date

    @staticmethod
    def _key(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create(self, user: UserRecord, ttl: timedelta) -> Session:
        from app.models.conversation import ConversationRecord
        from app.models.session_state import SessionState

        now = datetime.now(timezone.utc)
        session = Session(
            token=secrets.token_urlsafe(32),
            customer_id=user.customer_id,
            country=user.country,
            created_at=now,
            expires_at=now + ttl,
            role=user.role,
        )
        with DbSession(self._engine) as db, db.begin():
            # Purge sessions that expired more than a day ago and were never revisited,
            # and every conversation whose session is gone (same token hash as key).
            db.execute(delete(SessionState).where(SessionState.expires_at < now - timedelta(days=1)))
            db.execute(
                delete(ConversationRecord).where(
                    ConversationRecord.session_id.not_in(select(SessionState.session_id))
                )
            )
            db.add(
                SessionState(
                    session_id=self._key(session.token),
                    customer_id=session.customer_id,
                    country=session.country,
                    role=session.role,
                    reference_date=self._reference_date,
                    expires_at=session.expires_at,
                    created_at=now,
                )
            )
        return session

    def get(self, token: str) -> Session | None:
        from app.models.session_state import SessionState

        with DbSession(self._engine) as db, db.begin():
            row = db.get(SessionState, self._key(token))
            if row is None or row.expired:
                return None
            expires_at = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) >= expires_at:
                row.expired = True
                return None
            created_at = row.created_at if row.created_at.tzinfo else row.created_at.replace(tzinfo=timezone.utc)
            return Session(
                token=token,
                customer_id=row.customer_id,
                country=row.country,
                created_at=created_at,
                expires_at=expires_at,
                role=row.role,
            )

    def revoke(self, token: str) -> None:
        from app.models.session_state import SessionState

        with DbSession(self._engine) as db, db.begin():
            db.execute(delete(SessionState).where(SessionState.session_id == self._key(token)))

    def consume_expired(self, token: str) -> bool:
        from app.models.session_state import SessionState

        with DbSession(self._engine) as db, db.begin():
            row = db.get(SessionState, self._key(token))
            if row is None or not row.expired:
                return False
            db.delete(row)
            return True
