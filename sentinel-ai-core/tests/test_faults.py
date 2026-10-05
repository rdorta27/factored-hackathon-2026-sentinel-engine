"""Fault adapters: every injected fault ends in a safe reply (REQ-0021, REQ-0026).

A safe reply is HTTP 200 with a known reply kind and no internals in the
body. No turn may raise, leak, or invent a case number.
"""

import pytest
from fastapi.testclient import TestClient

from app.ai.demo import DemoModel
from app.ai.serving import FallbackModel
from app.main import create_app
from app.tools.faults import FailingCaseStore, FailingGold, FaultModel, SlowGold

PASSWORD = "Testpass-001"
SAFE_KINDS = frozenset(
    {
        "text",
        "clarification",
        "confirm_box",
        "explanation",
        "case_confirmation",
        "handoff",
        "error",
    }
)


def _logged(api: TestClient) -> TestClient:
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": PASSWORD}).status_code == 200
    return api


def _assert_safe(response) -> dict:  # type: ignore[no-untyped-def]
    assert response.status_code == 200
    body = response.json()
    assert body["kind"] in SAFE_KINDS, body
    assert "Traceback" not in response.text
    assert "fault injection" not in response.text
    return body


@pytest.mark.parametrize("fault", ["timeout", "error_5xx", "invalid_json"])
def test_model_faults_are_answered_by_the_baseline(fault: str) -> None:
    model = FallbackModel(FaultModel(DemoModel(), fault), DemoModel())
    api = _logged(TestClient(create_app(model=model)))
    body = _assert_safe(api.post("/api/v1/chat", json={"message": "no reconozco un cargo"}))
    assert body["kind"] != "error"
    understood = [record for record in api.app.state.recorder.records if record.step == "understand"]
    assert understood and understood[-1].route == "fallback"


def test_slow_gold_hands_off_without_a_case(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_GOLD_TIMEOUT_S", "0.05")
    app = create_app()
    app.state.gold = SlowGold(app.state.gold, delay_s=0.5)
    api = _logged(TestClient(app))
    body = _assert_safe(api.post("/api/v1/chat", json={"message": "no reconozco un cargo"}))
    assert body["kind"] in ("handoff", "error")
    assert "case_id" not in body


def test_gold_error_never_leaks_internals() -> None:
    app = create_app()
    app.state.gold = FailingGold()
    api = _logged(TestClient(app))
    body = _assert_safe(api.post("/api/v1/chat", json={"message": "no reconozco un cargo"}))
    assert body["kind"] in ("error", "handoff", "clarification", "text")


def test_store_error_on_confirm_never_becomes_a_case() -> None:
    app = create_app()
    app.state.cases = FailingCaseStore(app.state.cases)
    api = _logged(TestClient(app))
    first = api.post("/api/v1/chat", json={"selected_reference": "TXN-1001"})
    assert first.status_code == 200
    assert first.json()["kind"] == "confirm_box"
    body = _assert_safe(api.post("/api/v1/chat", json={"selected_reference": "TXN-1001"}))
    assert body["kind"] == "error"
    assert "case_id" not in body
