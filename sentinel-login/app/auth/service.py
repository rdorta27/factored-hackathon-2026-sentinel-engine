"""Authentication service: credentials, sessions, limits, and audit."""

from datetime import timedelta

from app.audit.logger import AuditLogger, token_fingerprint
from app.auth import security
from app.auth.models import Session
from app.auth.ratelimit import AttemptTracker
from app.auth.repositories import SessionStore, UserRepository
from app.auth.security import DUMMY_HASH_HEX, DUMMY_SALT_HEX

SESSION_TTL = timedelta(minutes=30)


class InvalidCredentials(Exception):
    """Wrong password or unknown user. Always surfaced as one generic error."""


class LockedOut(Exception):
    """Too many recent failures for this id or IP."""


class SessionExpired(Exception):
    """The token existed but passed its expiry."""


class UnknownSession(Exception):
    """No session exists for this token."""


class AuthService:
    """Coordinates login, logout, and session validation with audit."""

    def __init__(
        self,
        users: UserRepository,
        sessions: SessionStore,
        attempts: AttemptTracker,
        audit: AuditLogger,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._attempts = attempts
        self._audit = audit

    def _keys(self, customer_id: str, ip: str) -> tuple[str, str]:
        return f"id:{customer_id}", f"ip:{ip}"

    def login(
        self, customer_id: str, password: str, ip: str, trace_id: str
    ) -> Session:
        keys = self._keys(customer_id, ip)
        if self._attempts.is_locked(*keys):
            self._audit.emit("login_locked", customer_id, trace_id, ip)
            raise LockedOut
        user = self._users.get_by_customer_id(customer_id)
        if user is None:
            # Same KDF work as a real check: no timing or message oracle.
            security.verify_password(password, DUMMY_SALT_HEX, DUMMY_HASH_HEX)
            ok = False
        else:
            ok = security.verify_password(password, user.salt_hex, user.hash_hex)
        if not ok:
            self._attempts.record_failure(*keys)
            self._audit.emit("login_failed", customer_id, trace_id, ip)
            raise InvalidCredentials
        self._attempts.reset(*keys)
        session = self._sessions.create(customer_id, SESSION_TTL, role=user.role)
        self._audit.emit("login_success", customer_id, trace_id, ip)
        return session

    def logout(self, token: str | None, trace_id: str, ip: str) -> None:
        """Idempotent: revoking an unknown or missing token still succeeds."""
        customer_id: str | None = None
        if token is not None:
            session = self._sessions.get(token)
            if session is not None:
                customer_id = session.customer_id
            self._sessions.revoke(token)
            self._audit.emit(
                "logout", customer_id, trace_id, ip,
            )
        else:
            self._audit.emit("logout", None, trace_id, ip)

    def validate(self, token: str, trace_id: str, ip: str) -> Session:
        """Resolve a session token, auditing expired and unknown tokens."""
        session = self._sessions.get(token)
        if session is not None:
            return session
        if self._sessions.consume_expired(token):
            self._audit.emit("session_expired", None, trace_id, ip)
            raise SessionExpired
        self._audit.emit("access_denied", None, trace_id, ip)
        raise UnknownSession

    def token_fingerprint(self, token: str) -> str:
        return token_fingerprint(token)
