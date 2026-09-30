"""Router tests: baseline identity, transports, fixtures, prompted router, PII guard."""

import pytest

from app.ai.demo import DemoModel
from app.ai.fake import FakeModel
from app.ai.transport import HttpTransport, LLMResponse, ModelUnavailable


def test_baseline_describe_is_non_empty() -> None:
    for model in (DemoModel(), FakeModel()):
        info = model.describe()
        assert info.model.strip()
        assert info.route.strip()
        assert info.prompt_version.strip()


def test_baseline_understand_carries_zero_cost() -> None:
    result = DemoModel().understand("no reconozco este cargo", [])
    assert result.tokens_in == 0
    assert result.tokens_out == 0
    assert result.cost_usd == 0.0


def test_create_app_injects_fake_model() -> None:
    from fastapi.testclient import TestClient

    from app.main import create_app

    api = TestClient(create_app(model=FakeModel()))
    assert api.app.state.model.describe().model == "fake"
    assert (
        api.post("/session/login", json={"login": "CUST-0001", "password": "Testpass-001"}).status_code
        == 200
    )
    response = api.post("/chat", json={"message": "no reconozco este cargo"})
    assert response.status_code == 200
    assert response.json()["kind"] in ("clarification", "confirm_box", "handoff", "text")


class StubTransport:
    def __init__(self, content: str = '{"intent": "charge", "language": "es-419"}') -> None:
        self.calls: list[dict] = []
        self._content = content

    def complete(self, *, model: str, messages: list[dict], temperature: float = 0.0) -> LLMResponse:
        self.calls.append({"model": model, "messages": messages, "temperature": temperature})
        return LLMResponse(content=self._content, tokens_in=12, tokens_out=8, cost_usd=0.0001)


def test_http_transport_raises_typed_error_on_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def _boom(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise httpx.ConnectTimeout("down")

    monkeypatch.setattr("httpx.Client.post", _boom)
    transport = HttpTransport(base_url="http://127.0.0.1:9", max_retries=1)
    with pytest.raises(ModelUnavailable):
        transport.complete(model="test-model", messages=[{"role": "user", "content": "hi"}])


def test_stub_transport_records_calls() -> None:
    stub = StubTransport()
    response = stub.complete(model="cheap", messages=[{"role": "user", "content": "hola"}])
    assert response.tokens_in == 12
    assert stub.calls[0]["model"] == "cheap"


def test_fixture_replay_returns_recorded_result_without_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json
    from pathlib import Path

    import httpx

    from app.ai.fixtures import FixtureTransport

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("no HTTP connection may be opened during replay")

    monkeypatch.setattr("httpx.Client.post", _forbidden)
    fixtures = Path(__file__).parent.parent / "app" / "ai" / "fixtures"
    transport = FixtureTransport(fixtures, prompt_version="v1")
    response = transport.complete(
        model="any", messages=[{"role": "user", "content": "no reconozco este cargo"}]
    )
    body = json.loads(response.content)
    assert body == {"intent": "charge", "language": "es-419"}
    assert response.tokens_in == 42
    assert response.cost_usd == 0.0001


def test_fixtures_carry_provenance_and_no_personal_data() -> None:
    import json
    from pathlib import Path

    fixtures = Path(__file__).parent.parent / "app" / "ai" / "fixtures"
    files = sorted(fixtures.glob("v1-*.json"))
    assert files, "initial fixtures must be committed"
    forbidden = ("CUST-", "customer_id", "first_name", "last_name", "credit_score", "document")
    for path in files:
        body = json.loads(path.read_text(encoding="utf-8"))
        assert body["prompt_version"] == "v1"
        assert body["input_hash"] in path.name
        blob = json.dumps(body, ensure_ascii=False).lower()
        assert all(token.lower() not in blob for token in forbidden)
