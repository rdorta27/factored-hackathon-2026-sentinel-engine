"""An explicit "it was not me" claim hands off as suspected fraud; not recognizing a charge does not."""

import json

import pytest
from fastapi.testclient import TestClient

from app.ai.demo import DemoModel
from app.ai.llm import parse_content
from app.main import create_app
from app.schemas.chat import Handoff


@pytest.mark.parametrize(
    "message",
    ["no fui yo, alguien usó mi tarjeta", "me clonaron la tarjeta", "não fui eu", "clonaram meu cartão"],
)
def test_baseline_reports_the_claim(message: str) -> None:
    understood = DemoModel().understand(message, [])
    assert understood.not_mine is True
    assert understood.kind.value == "charge"


@pytest.mark.parametrize("message", ["no reconozco este cargo", "não reconheço esta cobrança"])
def test_not_recognizing_is_not_a_claim(message: str) -> None:
    assert DemoModel().understand(message, []).not_mine is False


def test_router_reports_the_claim_only_when_true() -> None:
    assert parse_content(json.dumps({"intent": "charge", "language": "es-419", "not_mine": True}))[2] is True
    assert parse_content(json.dumps({"intent": "charge", "language": "pt-BR"}))[2] is False
    assert parse_content(json.dumps({"intent": "charge", "language": "es-419", "not_mine": "yes"}))[2] is False


def _logged_in() -> TestClient:
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": "Testpass-001"}).status_code == 200
    return api


def test_claim_hands_off_with_its_own_rule() -> None:
    api = _logged_in()
    api.post("/api/v1/chat", json={"message": "no fui yo, alguien usó mi tarjeta"})
    raw = api.post("/api/v1/chat", json={"selected_reference": "TXN-1001"}).json()
    assert raw["kind"] == "handoff"
    package = Handoff.model_validate(raw).package
    assert package.conversation[-1].rule == "fraud.claim"
    assert "customer_states_not_theirs" in package.open_questions
    assert raw["reason_key"] == "handoff.review"
    assert "fraud" not in json.dumps({k: v for k, v in raw.items() if k != "package"}).lower()


def test_unrecognized_charge_keeps_the_dispute_path() -> None:
    api = _logged_in()
    api.post("/api/v1/chat", json={"message": "no reconozco este cargo"})
    raw = api.post("/api/v1/chat", json={"selected_reference": "TXN-1001"}).json()
    assert raw["kind"] != "handoff"


@pytest.mark.parametrize(
    ("login", "reference", "rule"),
    [
        ("CUST-0001", "TXN-1101", "amount.high"),
        ("CUST-0001", "TXN-1102", "fraud.score"),
        ("CUST-0002", "TXN-2002", "amount.high"),
        ("CUST-0002", "TXN-2102", "fraud.score"),
        ("CUST-0003", "TXN-3101", "amount.high"),
        ("CUST-0003", "TXN-3003", "fraud.score"),
    ],
)
def test_demo_rows_hand_off_with_their_rule(login: str, reference: str, rule: str) -> None:
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/login", json={"login": login, "password": "Testpass-001"}).status_code == 200
    api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    raw = api.post("/api/v1/chat", json={"selected_reference": reference}).json()
    assert raw["kind"] == "handoff"
    assert Handoff.model_validate(raw).package.conversation[-1].rule == rule


def test_mexican_mxn_charge_is_not_escalated_by_amount() -> None:
    api = _logged_in()
    api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    raw = api.post("/api/v1/chat", json={"selected_reference": "TXN-1001"}).json()
    assert raw["kind"] != "handoff"
