"""Advisor side: /api/v1/handoffs, role enforcement, and the demo login flag (decision 009)."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.chat import AdvisorTicket

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
    assert ticket.package.model_dump(mode="json") == handoff["package"]
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
