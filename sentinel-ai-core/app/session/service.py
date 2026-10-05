from datetime import timedelta

from app.session import security
from app.session.audit import AuditLogger
from app.session.limits import AttemptTracker
from app.session.models import Session
from app.session.security import DUMMY_HASH_HEX, DUMMY_SALT_HEX
from app.session.store import SessionStore, UserRepository

SESSION_TTL = timedelta(minutes=30)


class InvalidCredentials(Exception):
    pass


class LockedOut(Exception):
    pass


class SessionExpired(Exception):
    pass


class UnknownSession(Exception):
    pass


class SessionService:
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

    def login(self, login: str, password: str, ip: str, trace_id: str) -> Session:
        keys = (f"id:{login}", f"ip:{ip}")
        if self._attempts.is_locked(*keys):
            self._audit.emit("login_locked", trace_id)
            raise LockedOut
        user = self._users.get_by_login(login)
        if user is None:
            security.verify_password(password, DUMMY_SALT_HEX, DUMMY_HASH_HEX)
            ok = False
        else:
            ok = security.verify_password(password, user.salt_hex, user.hash_hex)
        if not ok:
            self._attempts.record_failure(*keys)
            self._audit.emit("login_failed", trace_id)
            raise InvalidCredentials
        self._attempts.reset(*keys)
        session = self._sessions.create(user, SESSION_TTL)
        self._audit.emit("login_success", trace_id, session.token, country=user.country)
        return session

    def login_demo(self, login: str, ip: str, trace_id: str) -> Session:
        """One-click demo sign-in: no password, customers only.

        The router gates this behind ``SENTINEL_DEMO_PERSONAS`` (unset follows
        ``SENTINEL_DEMO_AUTH``) and a visible banner; an id alone proves nothing
        about identity (README limitation).
        """
        user = self._users.get_by_login(login)
        if user is None or user.role != "customer":
            self._audit.emit("login_failed", trace_id)
            raise InvalidCredentials
        session = self._sessions.create(user, SESSION_TTL)
        self._audit.emit("login_success", trace_id, session.token, country=user.country)
        return session

    def logout(self, token: str | None, trace_id: str, ip: str) -> None:
        session_id = None
        country = "MX"
        if token is not None:
            session = self._sessions.get(token)
            if session is not None:
                session_id = session.token
                country = session.country
            self._sessions.revoke(token)
        self._audit.emit("logout", trace_id, session_id, country=country)

    def validate(self, token: str, trace_id: str, ip: str) -> Session:
        session = self._sessions.get(token)
        if session is not None:
            return session
        if self._sessions.consume_expired(token):
            self._audit.emit("session_expired", trace_id)
            raise SessionExpired
        self._audit.emit("access_denied", trace_id)
        raise UnknownSession
