"""Write budget: one session cannot burn unbounded turns or fill the store.

The budget covers every authenticated write that can reach the model or the
case store (chat and both dispute POSTs) and counts per session, so one
script session cannot hammer the API while other sessions stay unaffected.
"""

from fastapi.testclient import TestClient

from app.main import create_app
from app.session.limits import RateLimiter

LOGIN = "CUST-0001"
PASSWORD = "Testpass-001"


def login(api: TestClient) -> None:
    assert api.post("/api/v1/auth/login", json={"login": LOGIN, "password": PASSWORD}).status_code == 200


def test_chat_is_throttled_after_the_write_budget_is_spent() -> None:
    api = TestClient(create_app())
    login(api)
    codes = set()
    for _ in range(61):
        codes.add(api.post("/api/v1/chat", json={"message": "hola"}).status_code)
    assert codes == {200, 429}, "the 61st write in the window must be throttled"
    blocked = api.post("/api/v1/chat", json={"message": "hola"})
    assert blocked.status_code == 429
    body = blocked.json()
    assert body["detail"] == "Too many requests"
    # The body carries the trace id, so the error bubble can show the reference.
    assert body["trace_id"] == blocked.headers["X-Trace-Id"]
    # The throttle is auditable without naming the customer.
    events = [record.event for record in api.app.state.audit.records]
    assert "rate_limited" in events


def test_disputes_share_the_chat_budget() -> None:
    api = TestClient(create_app())
    login(api)
    for _ in range(61):
        api.post("/api/v1/chat", json={"message": "hola"})
    preview = api.post("/api/v1/disputes/preview", json={"reference": "TXN-1001"})
    assert preview.status_code == 429
    create = api.post("/api/v1/disputes", json={"reference": "TXN-1001"})
    assert create.status_code == 429


def test_a_fresh_session_is_not_affected() -> None:
    blocked = TestClient(create_app())
    login(blocked)
    for _ in range(61):
        blocked.post("/api/v1/chat", json={"message": "hola"})
    other = TestClient(create_app())
    login(other)
    assert other.post("/api/v1/chat", json={"message": "hola"}).status_code == 200


def test_limiter_window_expires() -> None:
    from datetime import datetime, timedelta, timezone

    limiter = RateLimiter(max_events=2, window=timedelta(seconds=60))
    assert limiter.allow("k")
    assert limiter.allow("k")
    assert not limiter.allow("k")
    # Entries older than the window stop counting.
    aged = datetime.now(timezone.utc) - timedelta(seconds=61)
    limiter._events["k"] = [aged, aged]
    assert limiter.allow("k")
