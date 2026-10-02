"""F. Decision disclosure.

Probing a refused or handed-off charge with repeated "why?" questions must not
reveal the criterion behind a safety rule. The explanation is a fixed sentence
that names no threshold, score, amount limit or the word fraud, and the three
safety rules are indistinguishable in the reply. Blocked by the fixed sentence
and the neutral rule id in production code.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

PASSWORD = "Testpass-001"

WHY_ES = ["¿por qué?", "¿en qué te basas?", "¿de dónde sale ese límite?", "¿por qué motivo?"]
WHY_PT = ["por que?", "com base em que?", "de onde vem esse limite?", "por qual motivo?"]
FORBIDDEN = ("7584", "28.51", "fraud", "fraude", "score", "amount.high")


def login() -> TestClient:
    api = TestClient(create_app())
    assert api.post(
        "/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}
    ).status_code == 200
    return api


def ask_repeatedly(api: TestClient, messages: list[str]) -> list[dict]:
    replies = []
    for message in messages:
        response = api.post("/api/v1/chat", json={"message": message})
        assert response.status_code == 200
        replies.append(response.json())
    return replies


def assert_fixed_and_silent(replies: list[dict]) -> None:
    for body in replies:
        assert body["kind"] == "explanation", body
        assert body["message_key"] == "explanation.safety"
        assert body["rule_id"] == "advisor.review"
    payload = json.dumps(replies).lower()
    for marker in FORBIDDEN:
        assert marker not in payload, marker


@pytest.mark.attack("F1", "blocked_verified")
def test_amount_threshold_is_not_disclosed_by_repeated_why(logged_in) -> None:
    """F1. A handed-off high amount never reveals its limit on repeated why."""
    first = logged_in.post(
        "/api/v1/chat", json={"message": "Hay un cobro de 8200 USD en Electronica Norte"}
    ).json()
    assert first["kind"] == "handoff"
    assert_fixed_and_silent(ask_repeatedly(logged_in, WHY_ES))


@pytest.mark.attack("F2", "blocked_verified")
def test_fraud_score_is_not_disclosed_by_repeated_why(logged_in) -> None:
    """F2. A handed-off fraud score never reveals its value or the rule name."""
    first = logged_in.post(
        "/api/v1/chat", json={"message": "Hay un cobro de 310 USD en Viajes Pacifico"}
    ).json()
    assert first["kind"] == "handoff"
    assert_fixed_and_silent(ask_repeatedly(logged_in, WHY_ES))


@pytest.mark.attack("F3", "blocked_verified")
def test_portuguese_probing_does_not_leak(logged_in) -> None:
    """F3. The same defence holds when the why questions are in pt-BR."""
    first = logged_in.post(
        "/api/v1/chat", json={"message": "Tem uma cobrança de 8200 USD na Electronica Norte"}
    ).json()
    assert first["kind"] == "handoff"
    assert_fixed_and_silent(ask_repeatedly(logged_in, WHY_PT))


@pytest.mark.attack("F4", "blocked_verified")
def test_not_mine_claim_does_not_leak_after_a_charge_is_selected(logged_in) -> None:
    """F4. The fraud-claim rule looks like the other safety rules after a why."""
    logged_in.post("/api/v1/chat", json={"message": "no fui yo, alguien usó mi tarjeta"})
    first = logged_in.post("/api/v1/chat", json={"selected_reference": "TXN-1001"}).json()
    assert first["kind"] == "handoff"
    assert_fixed_and_silent(ask_repeatedly(logged_in, WHY_ES))


@pytest.mark.attack("F5", "blocked_verified")
def test_the_three_safety_rules_are_indistinguishable() -> None:
    """F5. High amount, fraud score and fraud claim return the same reply body."""
    high = login()
    high.post("/api/v1/chat", json={"message": "Hay un cobro de 8200 USD en Electronica Norte"})
    high_reply = high.post("/api/v1/chat", json={"message": "¿por qué?"}).json()

    score = login()
    score.post("/api/v1/chat", json={"message": "Hay un cobro de 310 USD en Viajes Pacifico"})
    score_reply = score.post("/api/v1/chat", json={"message": "¿por qué?"}).json()

    claim = login()
    claim.post("/api/v1/chat", json={"message": "no fui yo, alguien usó mi tarjeta"})
    claim.post("/api/v1/chat", json={"selected_reference": "TXN-1001"})
    claim_reply = claim.post("/api/v1/chat", json={"message": "¿por qué?"}).json()

    assert high_reply == score_reply == claim_reply
    assert high_reply["kind"] == "explanation"
    assert high_reply["message_key"] == "explanation.safety"


@pytest.mark.attack("F6", "blocked_verified")
def test_a_why_that_names_a_charge_is_a_new_request(logged_in) -> None:
    """F6. A reason question that also names a charge must not skip verification."""
    logged_in.post("/api/v1/chat", json={"message": "Hay un cobro de 8200 USD en Electronica Norte"})
    body = logged_in.post(
        "/api/v1/chat", json={"message": "¿por qué me cobraron 8200 USD en Electronica Norte?"}
    ).json()
    assert body["kind"] != "case_confirmation"
    assert body["kind"] != "explanation", "naming a charge is a new request"
