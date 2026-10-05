"""Advisor side: /api/v1/handoffs, role enforcement, and the demo login flag (decision 009)."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.chat import AdvisorTicket, AdvisorTrace

CUSTOMER_PASSWORD = "Testpass-001"
ADVISOR_PASSWORD = "Advisor-001"


def login(api: TestClient, name: str, password: str) -> int:
    return api.post("/api/v1/auth/login", json={"login": name, "password": password}).status_code


@pytest.fixture
def demo_auth(monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_DEMO_AUTH", "1")


def escalate(api: TestClient, customer: str = "CUST-0001") -> dict:
    assert login(api, customer, CUSTOMER_PASSWORD) == 200
    if customer == "CUST-0001":
        api.post("/api/v1/chat", json={"selected_reference": "TXN-1003"})
    api.post("/api/v1/chat", json={"message": "quiero una persona"})
    handoff = api.post("/api/v1/chat", json={"message": "quiero una persona"}).json()
    assert handoff["kind"] == "handoff"
    api.post("/api/v1/auth/logout")
    return handoff


def test_advisor_does_not_exist_without_the_flag() -> None:
    api = TestClient(create_app())
    assert login(api, "ADV-0001", ADVISOR_PASSWORD) == 401
    assert login(api, "CUST-0001", CUSTOMER_PASSWORD) == 200


def test_password_is_required_even_with_the_flag(demo_auth) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    assert login(api, "ADV-0001", "wrong") == 401
    assert api.post("/api/v1/auth/login", json={"login": "ADV-0001"}).status_code == 422
    assert api.post("/api/v1/auth/login", json={"customer_id": "CUST-0001", "password": CUSTOMER_PASSWORD}).status_code == 422


def test_advisor_reads_the_full_ticket(demo_auth) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    handoff = escalate(api)
    response = api.post("/api/v1/auth/login", json={"login": "ADV-0001", "password": ADVISOR_PASSWORD})
    assert response.json()["role"] == "advisor"

    tickets = [AdvisorTicket.model_validate(item) for item in api.get("/api/v1/handoffs").json()]
    assert [t.case_id for t in tickets] == [handoff["reference"]]
    ticket = tickets[0]
    assert (ticket.customer_id, ticket.country, ticket.status, ticket.reason_key) == (
        "CUST-0001", "MX", "Escalated", "handoff.person",
    )
    assert ticket.package.model_dump(mode="json", exclude={"actions_taken", "evidence"}) == {
        key: value for key, value in handoff["package"].items() if key not in ("actions_taken", "evidence")
    }
    assert ticket.package.evidence["policy_rule"] == "person.insist"
    assert "policy_rule" not in handoff["package"]["evidence"]
    assert any("policy_rule" in item for item in ticket.package.model_dump(mode="json")["actions_taken"])
    assert all("policy_rule" not in item and "tool" not in item for item in handoff["package"]["actions_taken"])
    assert ticket.package.summary.startswith("3 turns.")
    assert ticket.package.verified_facts is not None and ticket.package.verified_facts.merchant == "ACME Store"
    assert api.get(f"/api/v1/handoffs/{ticket.case_id}").json()["case_id"] == ticket.case_id


def test_advisor_sees_every_customers_ticket_newest_first(demo_auth) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    first = escalate(api, "CUST-0001")
    second = escalate(api, "CUST-0002")
    login(api, "ADV-0001", ADVISOR_PASSWORD)
    ids = [item["case_id"] for item in api.get("/api/v1/handoffs").json()]
    assert ids == [second["reference"], first["reference"]]


def test_a_dispute_is_not_a_ticket(demo_auth) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    login(api, "CUST-0001", CUSTOMER_PASSWORD)
    api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"})
    case_id = api.post("/api/v1/chat", json={"selected_reference": "TXN-1006"}).json()["case_id"]
    api.post("/api/v1/auth/logout")
    login(api, "ADV-0001", ADVISOR_PASSWORD)
    assert api.get(f"/api/v1/handoffs/{case_id}").status_code == 404
    assert api.get("/api/v1/handoffs/HO-missing").status_code == 404


def test_customer_is_forbidden_and_audited(demo_auth) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    login(api, "CUST-0001", CUSTOMER_PASSWORD)
    assert api.get("/api/v1/handoffs").status_code == 403
    assert api.get("/api/v1/handoffs/HO-anything").status_code == 403
    assert api.app.state.audit.records[-1].event == "access_denied"


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("post", "/api/v1/chat", {"message": "hola"}),
        ("get", "/api/v1/transactions", None),
        ("post", "/api/v1/disputes/preview", {"reference": "TXN-1006"}),
        ("get", "/api/v1/disputes", None),
    ],
)
def test_advisor_cannot_use_customer_endpoints(demo_auth, method, path, body) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    login(api, "ADV-0001", ADVISOR_PASSWORD)
    response = api.post(path, json=body) if method == "post" else api.get(path)
    assert response.status_code == 403


def test_handoffs_need_a_session() -> None:
    assert TestClient(create_app()).get("/api/v1/handoffs").status_code == 401


def test_a_customer_cannot_read_a_trace(demo_auth) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    handoff = escalate(api)
    login(api, "CUST-0001", CUSTOMER_PASSWORD)
    assert api.get(f"/api/v1/handoffs/{handoff['reference']}/trace").status_code == 403
    assert api.app.state.audit.records[-1].event == "access_denied"


def test_advisor_sees_the_trace_steps_without_text_or_identifier(demo_auth) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    handoff = escalate(api)
    login(api, "ADV-0001", ADVISOR_PASSWORD)
    trace = AdvisorTrace.model_validate(
        api.get(f"/api/v1/handoffs/{handoff['reference']}/trace").json()
    )
    assert trace.available is True and trace.trace_id
    assert trace.steps, "the escalating turn recorded steps"
    assert any(step.step == "escalate" for step in trace.steps)
    assert all(step.latency_ms >= 0 and step.model and step.prompt_version for step in trace.steps)
    raw = json.dumps(trace.model_dump(mode="json"))
    assert "CUST-" not in raw
    assert "quiero una persona" not in raw
    assert "session_ref" not in raw


def test_trace_of_a_missing_ticket_is_404(demo_auth) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    login(api, "ADV-0001", ADVISOR_PASSWORD)
    assert api.get("/api/v1/handoffs/HO-missing/trace").status_code == 404


def test_trace_reports_unavailable_when_the_row_has_none(demo_auth) -> None:  # type: ignore[no-untyped-def]
    from datetime import datetime, timezone

    from app.state.cases import CaseRow

    api = TestClient(create_app())
    api.app.state.cases.add(
        CaseRow(
            case_id="HO-old",
            customer_id="CUST-0001",
            kind="handoff",
            status="Escalated",
            created_at=datetime.now(timezone.utc),
            package={"request": "dispute", "language": "es-419", "country": "MX"},
        )
    )
    login(api, "ADV-0001", ADVISOR_PASSWORD)
    body = api.get("/api/v1/handoffs/HO-old/trace").json()
    assert body["available"] is False and body["steps"] == []


def test_a_charge_with_an_advisor_files_one_ticket_across_sessions(demo_auth) -> None:  # type: ignore[no-untyped-def]
    """Regression: a new session forgot the ticket, so the same charge filed a second one."""
    api = TestClient(create_app())
    first = escalate(api)
    second = escalate(api)
    assert second["reference"] == first["reference"]
    assert login(api, "ADV-0001", ADVISOR_PASSWORD) == 200
    tickets = [t for t in api.get("/api/v1/handoffs").json() if t["package"]["verified_facts"]]
    refs = [t["package"]["verified_facts"]["transaction_id"] for t in tickets]
    assert refs.count("TXN-1003") == 1


def test_a_charge_with_an_advisor_is_not_selectable(demo_auth) -> None:  # type: ignore[no-untyped-def]
    api = TestClient(create_app())
    escalate(api)
    assert login(api, "CUST-0001", CUSTOMER_PASSWORD) == 200
    rows = {row["reference"]: row for row in api.get("/api/v1/transactions").json()["transactions"]}
    assert rows["TXN-1003"]["case_state"] == "with_advisor"
    assert rows["TXN-1003"]["eligible"] is False
    assert rows["TXN-1003"]["ineligibleKey"] == "candidateWithAdvisor"
