"""SQLite backend: state survives a restart; retention deletes the conversation."""

import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session as DbSession

from app.main import create_app
from app.models.session_state import SessionState
from app.session.router import SESSION_COOKIE

PASSWORD = "Testpass-001"


@pytest.fixture
def sqlite_env(monkeypatch, tmp_path):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_STATE_BACKEND", "sqlite")
    monkeypatch.setenv("SENTINEL_DB_PATH", str(tmp_path / "state.db"))
    return tmp_path


def login(api: TestClient) -> None:
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code == 200


def restarted(api: TestClient) -> TestClient:
    """A new process on the same database, carrying the browser cookie."""
    fresh = TestClient(create_app())
    fresh.cookies.set(SESSION_COOKIE, api.cookies.get(SESSION_COOKIE))
    return fresh


def test_health_reports_sqlite(sqlite_env) -> None:  # type: ignore[no-untyped-def]
    assert TestClient(create_app()).get("/api/v1/health").json()["state_backend"] == "sqlite"


def test_health_fails_when_the_state_store_is_unreachable(sqlite_env) -> None:  # type: ignore[no-untyped-def]
    app = create_app()
    api = TestClient(app)
    assert api.get("/api/v1/health").status_code == 200

    class Broken:
        def connect(self):  # type: ignore[no-untyped-def]
            raise RuntimeError("database is gone")

    app.state.engine = Broken()
    response = api.get("/api/v1/health")
    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"


def test_a_conversation_files_one_handoff_ticket(sqlite_env) -> None:  # type: ignore[no-untyped-def]
    app = create_app()
    api = TestClient(app)
    login(api)
    references = set()
    for _ in range(6):
        body = api.post("/api/v1/chat", json={"message": "quiero hablar con una persona"}).json()
        if body["kind"] == "handoff":
            references.add(body["reference"])
    assert len(references) == 1, "every handoff reply points at the same ticket"
    assert len(app.state.cases.handoffs()) == 1


def test_session_conversation_and_case_survive_a_restart(sqlite_env) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    login(api)
    assert api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"}).json()["kind"] == "confirm_box"

    # The pending confirm box lives in the database, so another process can confirm it.
    second = restarted(api)
    case = second.post("/api/v1/chat", json={"selected_reference": "TXN-1006"}).json()
    assert case["kind"] == "case_confirmation"

    third = restarted(second)
    listing = third.get("/api/v1/disputes").json()
    assert [row["case_id"] for row in listing] == [case["case_id"]]
    assert third.post("/api/v1/chat", json={"selected_reference": "TXN-1006"}).json()["message_key"] == "already.disputed"


def test_session_token_is_not_stored_in_clear(sqlite_env) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    login(api)
    api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    raw = (sqlite_env / "state.db").read_bytes()
    assert api.cookies.get(SESSION_COOKIE).encode() not in raw


def test_logout_deletes_the_conversation(sqlite_env) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    login(api)
    api.post("/api/v1/chat", json={"message": "no reconozco un cargo de Cafe Central"})
    store = api.app.state.conversation_store
    assert store.count() == 1
    api.post("/api/v1/auth/logout")
    assert store.count() == 0


def test_database_file_is_owner_only(sqlite_env) -> None:  # type: ignore[no-untyped-def]
    import os
    import stat

    os.chmod(sqlite_env, 0o755)
    api = TestClient(create_app())
    login(api)
    for suffix in ("", "-wal", "-shm"):
        path = sqlite_env / f"state.db{suffix}"
        if path.exists():
            assert stat.S_IMODE(os.stat(path).st_mode) == 0o600, path.name
    assert stat.S_IMODE(os.stat(sqlite_env).st_mode) == 0o755, "an existing folder is left as is"


def test_database_folder_created_owner_only(tmp_path) -> None:  # type: ignore[no-untyped-def]
    import os
    import stat

    from app.db.session import make_engine

    folder = tmp_path / "fresh"
    make_engine(folder / "state.db").dispose()
    assert stat.S_IMODE(os.stat(folder).st_mode) == 0o700


def test_a_conversation_stored_without_the_field_loads(sqlite_env) -> None:  # type: ignore[no-untyped-def]
    from app.state.conversation import from_json

    state = from_json(json.dumps({"language": "es-419", "turns": ["hola"]}))
    assert state.last_decision is None


def test_last_decision_survives_a_sqlite_round_trip(sqlite_env) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    login(api)
    api.post("/api/v1/chat", json={"message": "Hay un cobro de 2500 MXN en ACME Store"})
    token = api.cookies.get(SESSION_COOKIE)
    assert token is not None
    stored = api.app.state.conversation_store.get(token)
    assert stored is not None and stored.state.last_decision is not None
    assert stored.state.last_decision.rule_id == "window.expired"
    assert stored.state.last_decision.values["window_days"] == 90

    second = restarted(api)
    reloaded = second.app.state.conversation_store.get(token)
    assert reloaded is not None and reloaded.state.last_decision is not None
    assert reloaded.state.last_decision.rule_id == "window.expired"
    assert reloaded.state.last_decision.values["age_days"] == 153


def test_expiry_deletes_the_conversation(sqlite_env) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    login(api)
    api.post("/api/v1/chat", json={"message": "no reconozco un cargo de Cafe Central"})
    engine = api.app.state.conversation_store._engine
    with DbSession(engine) as db, db.begin():
        db.execute(update(SessionState).values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)))
    assert api.post("/api/v1/chat", json={"message": "hola"}).status_code == 401
    assert api.app.state.conversation_store.count() == 0
