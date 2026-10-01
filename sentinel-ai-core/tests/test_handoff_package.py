"""The handoff package carries the whole conversation: a summary and every action attempted."""

import json

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.chat import Handoff
from app.session.router import SESSION_COOKIE

PASSWORD = "Testpass-001"


def logged_in(api: TestClient | None = None) -> TestClient:
    api = api or TestClient(create_app())
    assert api.post("/api/v1/session/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code == 200
    return api


def chat(api: TestClient, **body: str) -> dict:
    return api.post("/api/v1/chat", json=body).json()


def test_summary_and_conversation_cover_every_turn() -> None:
    api = logged_in()
    chat(api, message="hola, tengo una duda")
    chat(api, selected_reference="TXN-1003")
    chat(api, message="quiero una persona")
    raw = chat(api, message="quiero una persona")
    package = Handoff.model_validate(raw).package

    assert [(t.turn, t.customer, t.charge, t.system, t.rule) for t in package.conversation] == [
        (1, "unclear_charge", None, "clarification", "clarifyWhichCharge"),
        (2, "selected_charge", "TXN-1003", "text", "status.reversed"),
        (3, "asked_for_person", None, "text", "person.ask"),
        (4, "asked_for_person", None, "handoff", "person.insist"),
    ]
    assert package.summary.startswith("4 turns. Turn 1: customer described a charge the system could not single out")
    assert "Turn 2: customer selected a charge TXN-1003; system explained (status.reversed)." in package.summary
    assert "Turn 3: customer asked for a person; system offered help once (person.ask)." in package.summary
    assert package.summary.endswith("Turn 4: customer asked for a person; system handed off (person.insist).")
    text = json.dumps(raw)
    assert "hola, tengo una duda" not in text and "quiero una persona" not in text, "no raw transcript"


def test_actions_include_earlier_turns_and_failed_attempts() -> None:
    api = logged_in()
    chat(api, selected_reference="TXN-1006")
    next(iter(api.app.state.memories.values())).lookup_failures_left = 99
    package = Handoff.model_validate(chat(api, selected_reference="TXN-1006")).package

    actions = [(a.turn, a.step, a.tool, a.outcome, a.attempt) for a in package.actions_taken]
    assert (1, "decide", None, "ok", 1) in actions, "the turn-1 policy decision travels with the ticket"
    assert (2, "act", "open_dispute", "ok", 1) in actions
    failed_reads = [a for a in actions if a[2] == "lookup_dispute"]
    assert [(a[3], a[4]) for a in failed_reads] == [("failed", 1), ("failed", 2), ("failed", 3)]
    assert package.conversation[-1].system == "handoff" and package.conversation[-1].rule == "unverified"


def test_unknown_reference_never_enters_the_ticket() -> None:
    api = logged_in()
    chat(api, selected_reference="TXN-9001")
    chat(api, message="quiero una persona")
    package = chat(api, message="quiero una persona")["package"]
    assert package["conversation"][0] == {
        "turn": 1, "customer": "selected_unknown_charge", "charge": None, "system": "handoff", "rule": "unknownCharge",
    }
    assert "TXN-9001" not in json.dumps(package)


def test_the_ticket_and_the_log_keep_the_full_package() -> None:
    api = logged_in()
    chat(api, message="quiero una persona")
    response = api.post("/api/v1/chat", json={"message": "quiero una persona"})
    package = response.json()["package"]
    assert api.app.state.cases.get(response.json()["reference"]).package == package
    turn = [r for r in api.app.state.recorder.records_for(response.headers["X-Trace-Id"]) if r.step == "turn"][-1]
    assert turn.handoff == package and len(package["conversation"]) == 2


def test_history_survives_a_restart_and_dies_with_the_session(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_STATE_BACKEND", "sqlite")
    monkeypatch.setenv("SENTINEL_DB_PATH", str(tmp_path / "state.db"))
    first = logged_in()
    chat(first, message="quiero una persona")

    second = TestClient(create_app())
    second.cookies.set(SESSION_COOKIE, first.cookies.get(SESSION_COOKIE))
    package = chat(second, message="quiero una persona")["package"]
    assert [t["turn"] for t in package["conversation"]] == [1, 2]

    second.post("/api/v1/session/logout")
    assert second.app.state.conversation_store.count() == 0
