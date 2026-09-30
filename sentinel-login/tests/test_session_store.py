"""Unit tests for the session store contract: create, validate, expire, revoke."""

from datetime import timedelta

from app.auth.repositories import InMemorySessionStore


def test_create_returns_session_for_customer() -> None:
    store = InMemorySessionStore()
    session = store.create("CUST-0001", timedelta(minutes=30))
    assert session.customer_id == "CUST-0001"
    assert session.token
    assert session.expires_at > session.created_at


def test_get_returns_live_session() -> None:
    store = InMemorySessionStore()
    session = store.create("CUST-0001", timedelta(minutes=30))
    assert store.get(session.token) == session


def test_get_unknown_token_returns_none() -> None:
    store = InMemorySessionStore()
    assert store.get("not-a-real-token") is None


def test_expired_session_is_removed_and_returns_none() -> None:
    store = InMemorySessionStore()
    session = store.create("CUST-0001", timedelta(seconds=-1))
    assert store.get(session.token) is None


def test_consume_expired_reports_expired_token_once() -> None:
    store = InMemorySessionStore()
    session = store.create("CUST-0001", timedelta(seconds=-1))
    assert store.get(session.token) is None
    assert store.consume_expired(session.token) is True
    assert store.consume_expired(session.token) is False


def test_consume_expired_false_for_unknown_token() -> None:
    store = InMemorySessionStore()
    assert store.consume_expired("not-a-real-token") is False


def test_revoke_removes_session() -> None:
    store = InMemorySessionStore()
    session = store.create("CUST-0001", timedelta(minutes=30))
    store.revoke(session.token)
    assert store.get(session.token) is None


def test_revoke_unknown_token_is_noop() -> None:
    store = InMemorySessionStore()
    store.revoke("not-a-real-token")
