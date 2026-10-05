"""The served app picks router_v2 from the environment and falls back per turn."""

import json

import pytest
from fastapi.testclient import TestClient

from app.ai import serving
from app.ai.demo import DemoModel
from app.ai.llm import PromptedLLMRouter
from app.ai.serving import FallbackModel, model_from_env
from app.ai.transport import InvalidReply, LLMResponse, ModelUnavailable
from app.main import create_app

KEY = "fw_test_secret_key_123"
# Example ids recorded in evidence/evaluation-runs/2024Q4-eval-v7 (examples_v2).
EVAL_V7_EXAMPLE_IDS = (
    "dv-b01-es-MX", "dv-b03-pt-BR", "dv-b10-pt-BR", "dv-b14-es-CO",
    "dv-b17-pt-BR", "dv-b20-es-MX", "dv-b24-es-CO", "dv-b27-es-AR",
)
MODEL = "accounts/fireworks/models/glm-5p3-flash"


class ScriptedTransport:
    def __init__(self, reply: str | Exception) -> None:
        self.reply = reply
        self.calls: list[dict] = []

    def complete(self, *, model, messages, temperature=0.0):  # type: ignore[no-untyped-def]
        self.calls.append({"model": model, "messages": messages, "temperature": temperature})
        if isinstance(self.reply, Exception):
            raise self.reply
        return LLMResponse(content=self.reply, tokens_in=10, tokens_out=5, cost_usd=0.0001)


@pytest.fixture
def llm_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_LLM_BASE_URL", "https://llm.example/v1")
    monkeypatch.setenv("SENTINEL_LLM_API_KEY", KEY)
    for name in ("CHEAP", "STRONG", "DEFAULT"):
        monkeypatch.setenv(f"SENTINEL_LLM_{name}_MODEL", MODEL)
    monkeypatch.setenv("SENTINEL_LLM_PROMPT_VERSION", "v2")


def test_without_llm_variables_the_baseline_is_served(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SENTINEL_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("SENTINEL_LLM_API_KEY", raising=False)
    assert isinstance(model_from_env(), DemoModel)
    body = TestClient(create_app()).get("/api/v1/health").json()
    assert (body["model"], body["route"]) == ("keyword-baseline", "baseline")


def test_a_missing_key_keeps_the_baseline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_LLM_BASE_URL", "https://llm.example/v1")
    monkeypatch.setenv("SENTINEL_LLM_API_KEY", "")
    assert isinstance(model_from_env(), DemoModel)


def test_router_v2_is_served_with_the_measured_examples(llm_env: None) -> None:
    transport = ScriptedTransport('{"intent": "person", "language": "es-419", "amount": null, "not_mine": false}')
    model = model_from_env(transport)
    assert isinstance(model, FallbackModel)
    model.understand("quiero hablar con un asesor", [])
    messages = transport.calls[0]["messages"]
    examples = [json.loads(m["content"])["message"] for m in messages[1:-1] if m["role"] == "user"]
    assert len(examples) == len(EVAL_V7_EXAMPLE_IDS)
    config = serving.router_config()
    assert config.example_ids == EVAL_V7_EXAMPLE_IDS
    assert model.describe().prompt_version == "v2"
    assert model.describe().model == MODEL


def test_v2_without_loadable_examples_fails_at_startup(llm_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(serving, "EXAMPLES_PATH", tmp_path / "missing.json")
    with pytest.raises(RuntimeError, match="development examples"):
        create_app()


def test_cutoffs_are_off_unless_the_setting_is_on(llm_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SENTINEL_LLM_CUTOFFS", raising=False)
    assert serving.router_config().cutoffs is None
    monkeypatch.setenv("SENTINEL_LLM_CUTOFFS", "1")
    cutoffs = serving.router_config().cutoffs
    assert cutoffs is not None
    assert (cutoffs.t_act, cutoffs.t_abstain) == (0.86, 0.0)
    assert cutoffs.calibration_run == "2024Q4-calibration-v1"


def test_cutoffs_enabled_without_a_config_fail_at_startup(
    llm_env: None, monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_LLM_CUTOFFS", "1")
    monkeypatch.setattr(serving, "CUTOFFS_PATH", tmp_path / "missing.json")
    with pytest.raises(RuntimeError, match="router configuration"):
        serving.router_config()


@pytest.mark.parametrize("failure", [ModelUnavailable("down"), InvalidReply("bad json")])
def test_a_model_failure_is_answered_by_the_baseline(failure: Exception) -> None:
    model = FallbackModel(PromptedLLMRouter(ScriptedTransport(failure), serving.RouterConfig()), DemoModel())
    result = model.understand("quiero hablar con un asesor", [])
    assert result.kind.value == "person"
    info = model.describe()
    assert (info.route, info.model) == ("fallback", "keyword-baseline")


def test_the_next_turn_goes_back_to_the_model() -> None:
    transport = ScriptedTransport(ModelUnavailable("down"))
    model = FallbackModel(PromptedLLMRouter(transport, serving.RouterConfig()), DemoModel())
    model.understand("hola", [])
    transport.reply = '{"intent": "charge", "language": "es-419", "amount": null, "not_mine": false}'
    model.understand("hola", [])
    assert model.describe().route != "fallback"


def test_an_outage_still_answers_the_customer_and_never_leaks_the_key(llm_env: None, monkeypatch: pytest.MonkeyPatch, caplog) -> None:  # type: ignore[no-untyped-def]
    transport = ScriptedTransport(ModelUnavailable("model endpoint 503"))
    monkeypatch.setattr(serving, "model_from_env", lambda: model_from_env(transport))
    api = TestClient(create_app())
    assert api.post("/api/v1/auth/login", json={"login": "CUST-0001", "password": "Testpass-001"}).status_code == 200
    with caplog.at_level("INFO"):
        response = api.post("/api/v1/chat", json={"message": "no reconozco un cargo"})
    assert response.status_code == 200
    assert response.json()["kind"] != "error"
    health = api.get("/api/v1/health")
    # Health reports the configured model; who answered a turn is in the turn log.
    assert health.json()["model"] == MODEL
    understood = [r for r in api.app.state.recorder.records if r.step == "understand"]
    assert understood and understood[-1].route == "fallback"
    assert KEY not in health.text + response.text + caplog.text


def test_who_answered_is_kept_per_thread() -> None:
    import threading

    transport = ScriptedTransport(ModelUnavailable("down"))
    model = FallbackModel(PromptedLLMRouter(transport, serving.RouterConfig()), DemoModel())
    failed, answered, seen = threading.Event(), threading.Event(), {}

    def failing() -> None:
        model.understand("hola", [])
        failed.set()
        answered.wait(5)
        seen["failing"] = model.describe().route

    def succeeding() -> None:
        failed.wait(5)
        ok = ScriptedTransport('{"intent": "charge", "language": "es-419", "amount": null, "not_mine": false}')
        other = FallbackModel(PromptedLLMRouter(ok, serving.RouterConfig()), DemoModel())
        model._primary = other._primary  # same shared model object, now answering
        model.understand("hola", [])
        answered.set()
        seen["succeeding"] = model.describe().route

    threads = [threading.Thread(target=failing), threading.Thread(target=succeeding)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert seen == {"failing": "fallback", "succeeding": "cheap"}


def test_the_served_examples_equal_what_the_eval_loader_builds() -> None:
    """The image carries a copy of the examples; the eval loader stays the source."""
    from eval.cases import load_dir
    from eval.examples import build_examples

    ids = json.loads(serving.EXAMPLES_PATH.with_name("examples_v2.json").read_text(encoding="utf-8"))
    eval_ids = json.loads((serving.EXAMPLES_PATH.parents[2] / "eval" / "examples_v2.json").read_text(encoding="utf-8"))["ids"]
    expected = build_examples(load_dir(serving.EXAMPLES_PATH.parents[2] / "eval" / "cases"), eval_ids)
    assert serving.load_examples() == expected
    assert [row["case_id"] for row in ids["examples"]] == list(EVAL_V7_EXAMPLE_IDS)


EVAL_V3_EXAMPLE_IDS = (
    "v3-greet-es-MX", "v3-greet-es-CO", "v3-greet-es-AR", "v3-greet-pt-BR",
    "v3-thanks-es-MX", "v3-thanks-es-CO", "v3-thanks-es-AR", "v3-thanks-pt-BR",
    "v3-identity-es-MX", "v3-identity-es-CO", "v3-identity-es-AR", "v3-identity-pt-BR",
    "v3-unclear-es-MX", "v3-unclear-es-CO", "v3-unclear-es-AR", "v3-unclear-pt-BR",
    "v3-status-es-MX", "v3-status-es-CO", "v3-status-es-AR", "v3-status-pt-BR",
    "v3-loan-es-MX", "v3-loan-es-CO", "v3-loan-es-AR", "v3-loan-pt-BR",
    "v3-balance-es-MX", "v3-balance-es-CO", "v3-balance-es-AR", "v3-balance-pt-BR",
    "v3-amount-es-MX", "v3-amount-es-CO", "v3-amount-es-AR", "v3-amount-pt-BR",
)


def test_the_v3_served_examples_equal_what_the_eval_loader_builds() -> None:
    """The v3 image copy matches the v3 eval loader; both stay development."""
    from eval.cases import load_dir
    from eval.examples import build_examples_v3

    rows = json.loads(serving.EXAMPLES_V3_PATH.read_text(encoding="utf-8"))["examples"]
    spec = json.loads((serving.EXAMPLES_V3_PATH.parents[2] / "eval" / "examples_v3.json").read_text(encoding="utf-8"))
    expected = build_examples_v3(
        load_dir(serving.EXAMPLES_V3_PATH.parents[2] / "eval" / "cases"), spec["ids"], spec.get("drafts")
    )
    assert serving.load_examples_v3() == expected
    assert [row["case_id"] for row in rows] == list(EVAL_V3_EXAMPLE_IDS)


def test_prompt_v3_is_served_only_behind_the_v3_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.ai.llm import SYSTEM_PROMPT, SYSTEM_PROMPT_V3

    monkeypatch.setenv("SENTINEL_LLM_BASE_URL", "https://llm.example/v1")
    monkeypatch.setenv("SENTINEL_LLM_API_KEY", KEY)
    for name in ("CHEAP", "STRONG", "DEFAULT"):
        monkeypatch.setenv(f"SENTINEL_LLM_{name}_MODEL", MODEL)
    monkeypatch.setenv("SENTINEL_LLM_PROMPT_VERSION", "v3")
    config = serving.router_config()
    assert config.example_ids == EVAL_V3_EXAMPLE_IDS
    assert config.system_prompt == SYSTEM_PROMPT_V3
    assert config.system_prompt != SYSTEM_PROMPT
    monkeypatch.setenv("SENTINEL_LLM_PROMPT_VERSION", "v2")
    assert serving.router_config().system_prompt == SYSTEM_PROMPT
