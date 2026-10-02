"""System runner: replay cases against POST /chat and read the turn records.

Each case gets a fresh app (test session CUST-0001) with the fixture-backed
router. Faults are injected through app state before the replay, reusing the
adversarial patterns. The turn is joined by the X-Trace-Id header through
``Recorder.records_for``; metrics come from the recovered records plus the
response body, never from a second instrumentation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app.ai.fixtures import FixtureTransport
from app.ai.llm import PromptedLLMRouter, RouterConfig
from app.main import create_app
from app.orchestrator.types import ConversationState, Language
from app.session.router import SESSION_COOKIE
from app.tools.fake import InMemoryTools
from eval.cases import Case

PASSWORD = "Testpass-001"
CUSTOMER = "CUST-0001"
# Two-turn cases log in as the demo customer of their country (local + USD accounts).
CUSTOMERS = {"MX": "CUST-0001", "CO": "CUST-0002", "AR": "CUST-0003"}

SAFE_FAULT_OUTCOMES = ("handoff", "offer", "error")


class RaisingGold:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def get(self, reference: str, customer_id: str):  # type: ignore[no-untyped-def]
        raise self._error

    def list_for_customer(self, customer_id: str):  # type: ignore[no-untyped-def]
        raise self._error


def build_client(fixtures_dir: Path | str, model=None) -> TestClient:  # type: ignore[no-untyped-def]
    """A fresh app per case; ``model`` replaces the fixture-backed router when given."""
    config = RouterConfig(
        cheap_model="cheap-eval",
        strong_model="strong-eval",
        default_model="default-eval",
        prompt_version="v1",
    )
    router = model if model is not None else PromptedLLMRouter(FixtureTransport(fixtures_dir), config)
    # Each case on its own in-memory state: cases never share sessions or cases.
    return TestClient(create_app(model=router, state_backend="memory"))


def login(client: TestClient, customer: str = CUSTOMER) -> None:
    response = client.post("/api/v1/auth/login", json={"login": customer, "password": PASSWORD})
    assert response.status_code == 200, "test login must succeed"


def inject_fault(client: TestClient, fault: str) -> None:
    if fault == "gold_unavailable":
        client.app.state.gold = RaisingGold(ConnectionError("gold down"))
    elif fault == "tool_failure":
        client.app.state.gold = RaisingGold(TimeoutError("tool timeout"))
    elif fault == "expired_session":
        token = client.cookies.get(SESSION_COOKIE)
        store = client.app.state.session_service._sessions
        session = store._sessions[token]
        store._sessions[token] = session.__class__(
            **{**session.__dict__, "expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)}
        )


def seed_failing_tools(client: TestClient) -> None:
    """Pre-seed per-session tools so the first turn already sees failures."""
    token = client.cookies.get(SESSION_COOKIE)
    client.app.state.conversations[token] = ConversationState(language=Language.ES_419)
    client.app.state.memories[token] = InMemoryTools(lookup_failures=99)


def match_outcome(case: Case, kind: str | None, status_code: int, policy_rules: list[str] | None = None) -> bool:
    if case.expected_rule is not None:
        rule_ok = case.expected_rule in (policy_rules or [])
        if case.expected_outcome == "handoff":
            return kind == "handoff" and rule_ok
        return kind == case.expected_outcome and rule_ok and not any(
            rule in (policy_rules or []) for rule in ("amount.high", "fraud.score", "fraud.claim")
        )
    if (case.fault or "none") != "none":
        if kind == "case_confirmation":
            return False
        return kind in SAFE_FAULT_OUTCOMES or status_code == 401
    if kind == case.expected_outcome:
        return True
    if case.requires_handoff and kind in ("handoff", "offer"):
        return True
    if case.requires_handoff and kind == "text" and any(
        rule.startswith("person") for rule in (policy_rules or [])
    ):
        # First person ask is an offer rendered as text (message_key person.ask);
        # only a second insist escalates. The decide record proves the path.
        return True
    return False


def run_case(client: TestClient, case: Case) -> dict:
    login(client, CUSTOMERS[case.country] if case.selected_reference else CUSTOMER)
    inject_fault(client, case.fault or "none")
    response = client.post("/api/v1/chat", json={"message": case.message})
    earlier: list = []
    if case.selected_reference and response.status_code == 200:
        first_trace = response.headers.get("X-Trace-Id", "unknown")
        earlier = client.app.state.recorder.records_for(first_trace) if first_trace != "unknown" else []
        response = client.post("/api/v1/chat", json={"selected_reference": case.selected_reference})
    body = response.json() if response.status_code == 200 else {}
    kind = body.get("kind")
    trace_id = response.headers.get("X-Trace-Id", "unknown")
    records = earlier + (client.app.state.recorder.records_for(trace_id) if trace_id != "unknown" else [])
    understand = next((r for r in records if r.step == "understand"), None)
    closing = next((r for r in reversed(records) if r.step == "turn"), None)
    policy_rules = sorted({r.policy_rule for r in records if r.policy_rule})
    return {
        "id": case.id,
        "locale": case.locale,
        "country": case.country,
        "expected_intent": case.expected_intent,
        "expected_outcome": case.expected_outcome,
        "outcome": kind,
        "matched": match_outcome(case, kind, response.status_code, policy_rules),
        "requires_handoff": case.requires_handoff,
        "must_not_pass": case.must_not_pass,
        "fault": case.fault or "none",
        "adversarial": "adversarial" in case.tags,
        "latency_ms": closing.latency_ms if closing else 0.0,
        "cost_usd": understand.cost_usd if understand else 0.0,
        "model": understand.model if understand else "unknown",
        "route": understand.route if understand else "unknown",
        "prompt_version": understand.prompt_version if understand else "unknown",
        "trace_id": trace_id,
    }


def run_system(cases: list[Case], fixtures_dir: Path | str, model_factory=None) -> list[dict]:  # type: ignore[no-untyped-def]
    turns = []
    for case in cases:
        model = model_factory() if model_factory is not None else None
        turns.append(run_case(build_client(fixtures_dir, model), case))
    return turns


__all__ = [
    "SAFE_FAULT_OUTCOMES",
    "build_client",
    "inject_fault",
    "login",
    "match_outcome",
    "run_case",
    "run_system",
    "seed_failing_tools",
]
