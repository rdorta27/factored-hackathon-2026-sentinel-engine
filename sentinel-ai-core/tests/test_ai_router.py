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
        api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": "Testpass-001"}).status_code
        == 200
    )
    response = api.post("/api/v1/chat", json={"message": "no reconozco este cargo"})
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


def _router(content: str, **overrides):  # type: ignore[no-untyped-def]
    from app.ai.llm import PromptedLLMRouter, RouterConfig

    config = RouterConfig(
        cheap_model=overrides.get("cheap_model", "cheap-test"),
        strong_model=overrides.get("strong_model", "strong-test"),
        default_model=overrides.get("default_model", "default-test"),
        prompt_version=overrides.get("prompt_version", "v1"),
    )
    return PromptedLLMRouter(StubTransport(content), config)


def test_router_understands_charge_missing_out_of_scope_and_person() -> None:
    cases = [
        ('{"intent": "charge", "language": "es-419"}', "charge", "es-419"),
        ('{"intent": "missing", "language": "es-419"}', "missing", "es-419"),
        ('{"intent": "out_of_scope", "language": "es-419"}', "out_of_scope", "es-419"),
        ('{"intent": "person", "language": "es-419"}', "person", "es-419"),
    ]
    for content, intent, _lang in cases:
        result = _router(content).understand("hola", [])
        assert result.kind.value == intent
        assert result.tokens_in == 12
        assert result.cost_usd > 0


def test_router_detects_portuguese_and_selects_strong_route() -> None:
    router = _router('{"intent": "charge", "language": "pt-BR"}')
    result = router.understand("não reconheço esta cobrança", [])
    assert result.language.value == "pt-BR"
    assert router.describe().route == "strong"
    assert router.describe().model == "strong-test"


def test_router_falls_back_to_default_model() -> None:
    router = _router('{"intent": "charge", "language": "es-419"}', cheap_model="", strong_model="")
    result = router.understand("hola", [])
    assert result.kind.value == "charge"
    assert router.describe().model == "default-test"


def test_router_request_carries_no_identifiers_and_numeric_amount() -> None:
    from app.ai.llm import build_messages

    messages = build_messages(
        "no reconozco un cargo",
        [],
        {"transaction_id": "TXN-1", "amount": 1000.0},
    )
    blob = str(messages)
    assert "CUST-" not in blob
    assert "customer_id" not in blob
    assert "first_name" not in blob
    assert "credit_score" not in blob


def test_router_rejects_forbidden_keys() -> None:
    import pytest

    from app.ai.llm import build_messages

    with pytest.raises(ValueError, match="not allowed|forbidden"):
        build_messages("hola", [], {"customer_id": "CUST-0001"})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="not allowed"):
        build_messages("hola", [], {"customer_first_name": "Ana"})  # type: ignore[dict-item]


def test_router_guard_greps_pii_columns() -> None:
    """Structured PII columns never leave the process (adversarial A9 covers free text).

    A9 stays no_defense_yet because raw free-text ids still travel inside the
    message string; this guard covers the structured charge and request keys.
    See evidence/adversarial/20260930T214744Z/summary.json.
    """
    from app.ai.llm import build_messages

    pii_columns = ("customer_first_name", "customer_last_name", "customer_credit_score")
    for column in pii_columns:
        try:
            build_messages("hola", [], {column: "x"})  # type: ignore[dict-item]
        except ValueError:
            continue
        raise AssertionError(f"column {column} must be rejected")


def test_router_served_turn_records_real_identity() -> None:
    from app.observability import Recorder
    from app.orchestrator.step import Ports
    from app.orchestrator.types import ConversationState, Language, TextInput
    from app.tools.fake import InMemoryTools

    router = _router('{"intent": "missing", "language": "es-419"}')
    recorder = Recorder(path=None, salt="test-salt")
    from app.observability import TurnObserver

    observer = TurnObserver(
        recorder=recorder, trace_id="a" * 16, session_ref="b" * 16, country="MX"
    )
    ports = Ports(
        idempotency_scope="test",
        tools=InMemoryTools(),
        model=router,  # type: ignore[arg-type]
        country="MX",
        observer=observer,
    )
    from app.orchestrator.step import step

    step(TextInput("hay un problema"), ConversationState(language=Language.ES_419), ports)
    records = [r for r in recorder.records if r.step == "understand"]
    assert records
    assert records[0].model == "cheap-test"
    assert records[0].prompt_version == "v1"
    assert isinstance(records[0].cost_usd, float)


def test_model_unavailable_falls_back_to_handoff() -> None:
    from app.ai.transport import ModelUnavailable
    from app.orchestrator.step import Ports
    from app.orchestrator.types import ConversationState, Language, OutcomeKind, TextInput
    from app.tools.fake import InMemoryTools

    class FailingModel:
        def understand(self, message: str, turns: list[str], context: dict | None = None):  # type: ignore[no-untyped-def]
            raise ModelUnavailable("down")

        def classify(self, message: str) -> str:
            return "Cargo no reconocido"

        def describe(self):  # type: ignore[no-untyped-def]
            from app.ai.port import ModelInfo

            return ModelInfo(model="failing", route="test", prompt_version="v1")

    ports = Ports(idempotency_scope="t", tools=InMemoryTools(), model=FailingModel())  # type: ignore[arg-type]
    from app.orchestrator.step import step

    output = step(TextInput("hola"), ConversationState(language=Language.ES_419), ports)
    assert output.kind is OutcomeKind.HANDOFF
    assert output.reason == "model_unavailable"
    assert output.case_number is None


def test_router_request_never_carries_the_fraud_score() -> None:
    import pytest

    from app.ai.llm import SYSTEM_PROMPT, build_messages

    with pytest.raises(ValueError, match="not allowed"):
        build_messages("no reconozco un cargo", [], {"transaction_id": "TXN-1", "amount": 1.0, "fraud_score": 29.0})
    assert "fraud" not in SYSTEM_PROMPT


def _record(tmp_path, model: str, repetition: int, intent: str, message: str = "no reconozco este cargo"):  # type: ignore[no-untyped-def]
    from app.ai.llm import build_messages
    from app.ai.recording import RecordedTransport, write_recording

    messages = build_messages(message, [message])
    replay = RecordedTransport(tmp_path, "v1", repetition=repetition)
    path, digest = replay.path_for(model, messages)
    write_recording(
        path,
        model=model,
        prompt_version="v1",
        digest=digest,
        repetition=repetition,
        messages=messages,
        response=LLMResponse(content=f'{{"intent": "{intent}", "language": "es-419"}}', tokens_in=10, tokens_out=5),
    )
    return path, messages


def test_two_models_do_not_share_a_recording(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.ai.recording import RecordedTransport

    path_a, messages = _record(tmp_path, "cheap-model", 0, "charge")
    path_b, _ = _record(tmp_path, "strong-model", 0, "missing")
    assert path_a != path_b
    replay = RecordedTransport(tmp_path, "v1")
    assert '"charge"' in replay.complete(model="cheap-model", messages=messages).content
    assert '"missing"' in replay.complete(model="strong-model", messages=messages).content


def test_two_repetitions_do_not_share_a_recording(tmp_path) -> None:  # type: ignore[no-untyped-def]
    import json

    from app.ai.recording import RecordedTransport

    path_0, messages = _record(tmp_path, "cheap-model", 0, "charge")
    path_1, _ = _record(tmp_path, "cheap-model", 1, "person")
    assert path_0 != path_1
    body = json.loads(path_1.read_text(encoding="utf-8"))
    assert (body["model"], body["prompt_version"], body["repetition"]) == ("cheap-model", "v1", 1)
    assert '"person"' in RecordedTransport(tmp_path, "v1", repetition=1).complete(
        model="cheap-model", messages=messages
    ).content
    with pytest.raises(ModelUnavailable):
        RecordedTransport(tmp_path, "v1", repetition=2).complete(model="cheap-model", messages=messages)


class _FakeHttpResponse:
    def __init__(self, body: dict, status_code: int = 200) -> None:
        self._body = body
        self.status_code = status_code

    def json(self) -> dict:
        return self._body


def _serve(monkeypatch: pytest.MonkeyPatch, body: dict, sent: list | None = None) -> None:
    def _post(self, url, json=None, headers=None):  # type: ignore[no-untyped-def]
        if sent is not None:
            sent.append({"url": url, "json": json, "headers": headers})
        return _FakeHttpResponse(body)

    monkeypatch.setattr("httpx.Client.post", _post)


_USAGE_BODY = {
    "choices": [{"message": {"content": '{"intent": "charge", "language": "es-419"}'}}],
    "usage": {"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000},
}


def test_cost_follows_the_serving_model(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.ai.prices import PRICES

    _serve(monkeypatch, _USAGE_BODY)
    transport = HttpTransport(base_url="http://fake", prices=PRICES, require_price=True)
    cheap = transport.complete(model="accounts/fireworks/models/gpt-oss-120b", messages=[])
    strong = transport.complete(model="accounts/fireworks/models/deepseek-v4p1-flash", messages=[])
    assert cheap.cost_usd == pytest.approx(0.15 + 0.60)
    assert strong.cost_usd == pytest.approx(0.30 + 1.20)


def test_cached_input_uses_the_cached_price(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.ai.prices import PRICES

    body = {**_USAGE_BODY, "usage": {**_USAGE_BODY["usage"], "prompt_tokens_details": {"cached_tokens": 1_000_000}}}
    _serve(monkeypatch, body)
    transport = HttpTransport(base_url="http://fake", prices=PRICES, require_price=True)
    reply = transport.complete(model="accounts/fireworks/models/deepseek-v4p1-flash", messages=[])
    assert reply.cost_usd == pytest.approx(0.006 + 1.20)


def test_unpriced_model_is_refused_before_the_call(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.ai.prices import PRICES, UnknownPrice

    sent: list = []
    _serve(monkeypatch, _USAGE_BODY, sent)
    transport = HttpTransport(base_url="http://fake", prices=PRICES, require_price=True)
    with pytest.raises(UnknownPrice, match="accounts/fireworks/models/unknown"):
        transport.complete(model="accounts/fireworks/models/unknown", messages=[])
    assert sent == []


def test_request_asks_for_bounded_json(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list = []
    _serve(monkeypatch, _USAGE_BODY, sent)
    HttpTransport(base_url="http://fake", max_tokens=200, reasoning_effort="low").complete(
        model="m", messages=[{"role": "user", "content": "hola"}]
    )
    body = sent[0]["json"]
    assert body["max_tokens"] == 200
    assert body["response_format"] == {"type": "json_object"}
    assert body["reasoning_effort"] == "low"


def test_invalid_reply_is_a_json_failure_and_still_unavailable() -> None:
    from app.ai.llm import PromptedLLMRouter, RouterConfig
    from app.ai.transport import InvalidReply

    for content in ("not json", "[1, 2]", '{"intent": "refund", "language": "es-419"}'):
        router = PromptedLLMRouter(StubTransport(content), RouterConfig(cheap_model="m"))
        with pytest.raises(InvalidReply):
            router.understand("no reconozco este cargo", [])
        assert issubclass(InvalidReply, ModelUnavailable)


class _CountingLive:
    def __init__(self, content: str = '{"intent": "charge", "language": "es-419"}') -> None:
        self.calls = 0
        self.content = content

    def complete(self, *, model: str, messages: list[dict], temperature: float = 0.0) -> LLMResponse:
        self.calls += 1
        return LLMResponse(content=self.content, tokens_in=10, tokens_out=5, cost_usd=0.001)


def _messages(text: str = "no reconozco este cargo") -> list[dict]:
    from app.ai.llm import build_messages

    return build_messages(text, [text])


def test_recording_hit_makes_no_live_call(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.ai.recording import RecordingTransport

    live = _CountingLive()
    recorder = RecordingTransport(tmp_path, "v1", live, record=True)
    first = recorder.complete(model="m", messages=_messages())
    second = recorder.complete(model="m", messages=_messages())
    assert live.calls == 1
    assert first.content == second.content
    assert recorder.spent_usd == pytest.approx(0.001)


def test_recording_miss_outside_recording_mode_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.ai.recording import RecordingTransport

    live = _CountingLive()
    with pytest.raises(ModelUnavailable, match="not recording"):
        RecordingTransport(tmp_path, "v1", live, record=False).complete(model="m", messages=_messages())
    assert live.calls == 0


def test_recording_refuses_to_write_a_secret(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.ai.recording import RecordingTransport, SecretInRecording

    key = "fw_test_not_a_real_key_123"
    for content in (f'{{"intent": "charge", "note": "{key}"}}', '{"intent": "charge", "h": "Authorization: x"}'):
        recorder = RecordingTransport(tmp_path, "v1", _CountingLive(content), record=True, api_key=key)
        with pytest.raises(SecretInRecording):
            recorder.complete(model="m", messages=_messages())
    assert list(tmp_path.iterdir()) == []


def test_model_port_accepts_optional_digest_and_two_arg_calls() -> None:
    """Contract: understand(message, turns, context=None); old two-arg calls keep working."""
    from app.ai.llm import PromptedLLMRouter, RouterConfig

    digest = {"sys_questions": ["missing"], "shown_ids": ["TXN-1006"]}
    assert DemoModel().understand("hola", [], digest).kind.value == "charge"
    assert FakeModel().understand("hay un problema", [], digest).kind.value == "missing"
    assert DemoModel().understand("hola", []).kind.value == "charge"

    stub = StubTransport('{"intent": "missing", "language": "es-419"}')
    router = PromptedLLMRouter(stub, RouterConfig(cheap_model="c", prompt_version="v1"))
    assert router.understand("hola", ["hola"], digest).kind.value == "missing"
    assert router.understand("hola", []).kind.value == "missing"


def test_digest_travels_in_the_router_request() -> None:
    import json

    from app.ai.llm import PromptedLLMRouter, RouterConfig

    stub = StubTransport('{"intent": "charge", "language": "es-419"}')
    router = PromptedLLMRouter(stub, RouterConfig(cheap_model="c", prompt_version="v1"))
    digest = {"sys_questions": ["missing", "which_charge"], "shown_ids": ["TXN-1", "TXN-2"]}
    router.understand("hola de nuevo", ["hola"], digest)
    user_body = json.loads(stub.calls[0]["messages"][-1]["content"])
    assert user_body["digest"] == digest
    assert user_body["turns"] == ["hola"]


def test_digest_rejects_unknown_fields_and_personal_data() -> None:
    import pytest

    from app.ai.llm import build_messages

    with pytest.raises(ValueError, match="not allowed"):
        build_messages("hola", [], None, context={"cot": "I think..."})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="must be a list"):
        build_messages("hola", [], None, context={"sys_questions": "missing"})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="forbidden"):
        build_messages("hola", [], None, context={"sys_questions": [], "customer_id": "CUST-1"})  # type: ignore[dict-item]
