"""/api/v1/disputes: two-step write on the chat's engine, read-only listing, isolation."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.chat import CaseConfirmation, CaseSummary, ConfirmBox, Handoff, TextReply

PASSWORD = "Testpass-001"


def logged_in(api: TestClient | None = None, name: str = "CUST-0001") -> TestClient:
    api = api or TestClient(create_app())
    assert api.post("/api/v1/session/login", json={"login": name, "password": PASSWORD}).status_code == 200
    return api


def test_requires_a_session() -> None:
    api = TestClient(create_app())
    assert api.post("/api/v1/disputes/preview", json={"reference": "TXN-1006"}).status_code == 401
    assert api.post("/api/v1/disputes", json={"reference": "TXN-1006"}).status_code == 401
    assert api.get("/api/v1/disputes").status_code == 401


def test_preview_then_create_opens_one_verified_case() -> None:
    api = logged_in()
    box = ConfirmBox.model_validate(api.post("/api/v1/disputes/preview", json={"reference": "TXN-1006", "reason": "no la hice"}).json())
    assert box.candidate.merchant == "Cafe Central"
    assert api.get("/api/v1/disputes").json() == [], "a preview never writes"

    created = api.post("/api/v1/disputes", json={"reference": "TXN-1006"})
    assert created.status_code == 201
    case = CaseConfirmation.model_validate(created.json())
    listing = [CaseSummary.model_validate(row) for row in api.get("/api/v1/disputes").json()]
    assert [(row.case_id, row.kind, row.status) for row in listing] == [(case.case_id, "dispute", "Open")]
    assert api.app.state.cases.get(case.case_id).reason == "no la hice"
    assert "no la hice" not in json.dumps(api.get(f"/api/v1/disputes/{case.case_id}").json()), "reason stays server-side"
    assert all("no la hice" not in record.to_json() for record in api.app.state.recorder.records), "never logged"


def test_create_without_preview_is_409_and_writes_nothing() -> None:
    api = logged_in()
    response = api.post("/api/v1/disputes", json={"reference": "TXN-1006"})
    assert response.status_code == 409
    assert api.get("/api/v1/disputes").json() == []


def test_preview_runs_the_policy() -> None:
    api = logged_in()
    reply = TextReply.model_validate(api.post("/api/v1/disputes/preview", json={"reference": "TXN-1003"}).json())
    assert reply.message_key == "status.reversed"
    assert api.post("/api/v1/disputes", json={"reference": "TXN-1003"}).status_code == 409


def test_previewing_twice_never_opens() -> None:
    api = logged_in()
    api.post("/api/v1/disputes/preview", json={"reference": "TXN-1006"})
    second = api.post("/api/v1/disputes/preview", json={"reference": "TXN-1006"}).json()
    assert second["kind"] == "confirm_box"
    assert api.get("/api/v1/disputes").json() == []


def test_foreign_reference_is_a_handoff_without_disclosure() -> None:
    api = logged_in()
    raw = api.post("/api/v1/disputes/preview", json={"reference": "TXN-9001"}).json()
    handoff = Handoff.model_validate(raw)
    assert handoff.reason_key == "unknownCharge"
    assert "ACME Store" not in json.dumps(raw)
    assert api.post("/api/v1/disputes", json={"reference": "TXN-9001"}).status_code == 409


@pytest.mark.parametrize(
    "body",
    [
        {"reference": "TXN-1006", "customer_id": "CUST-9999"},
        {"reference": "TXN-1006", "confirmation_token": "x"},
        {"reference": "TXN 1006"},
    ],
)
def test_bad_bodies_are_422(body: dict) -> None:
    api = logged_in()
    assert api.post("/api/v1/disputes/preview", json=body).status_code == 422


def test_cases_are_isolated_per_customer() -> None:
    api = logged_in()
    api.post("/api/v1/disputes/preview", json={"reference": "TXN-1006"})
    case_id = api.post("/api/v1/disputes", json={"reference": "TXN-1006"}).json()["case_id"]
    api.post("/api/v1/session/logout")
    logged_in(api, "CUST-0002")
    assert api.get("/api/v1/disputes").json() == []
    assert api.get(f"/api/v1/disputes/{case_id}").status_code == 404
    assert api.get("/api/v1/disputes", params={"customer_id": "CUST-0001"}).status_code == 422


def test_second_session_cannot_dispute_the_same_charge_again() -> None:
    api = logged_in()
    api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"})
    first = api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"}).json()
    assert first["kind"] == "case_confirmation"
    api.post("/api/v1/session/logout")

    logged_in(api)
    again = api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"}).json()
    assert again == {"kind": "text", "message_key": "already.disputed"}
    existing = api.post("/api/v1/disputes", json={"reference": "TXN-1006"})
    assert existing.status_code == 200 and existing.json()["case_id"] == first["case_id"]
    assert len([row for row in api.get("/api/v1/disputes").json() if row["kind"] == "dispute"]) == 1


def test_handoff_is_filed_as_a_ticket() -> None:
    api = logged_in()
    api.post("/api/v1/chat", json={"message": "quiero una persona"})
    handoff = api.post("/api/v1/chat", json={"message": "quiero una persona"}).json()
    tickets = [CaseSummary.model_validate(row) for row in api.get("/api/v1/disputes").json()]
    assert [(t.case_id, t.kind, t.status, t.reason_key) for t in tickets] == [
        (handoff["reference"], "handoff", "Escalated", "handoff.person")
    ]
    stored = api.app.state.cases.get(handoff["reference"])
    assert stored.package == handoff["package"], "the advisor ticket keeps the whole package"
