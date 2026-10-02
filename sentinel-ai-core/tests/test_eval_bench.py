"""Component benchmark over the identical case set, offline."""

from pathlib import Path

import pytest

from eval.bench_router import run_bench
from eval.cases import load_dir

CASES_DIR = Path(__file__).parent.parent / "eval" / "cases"
FIXTURES = Path(__file__).parent.parent / "app" / "ai" / "fixtures"


def test_both_models_ran_the_identical_set() -> None:
    cases = [c for c in load_dir(CASES_DIR) if c.split == "development" and c.fault == "none"]
    result = run_bench(cases, repetitions=2, fixtures_dir=FIXTURES)
    assert result["identical_set"] is True
    assert result["router"]["n"] == result["baseline"]["n"] == len(cases)
    assert set(result["router"]["intent"]["per_class"]) == {"charge", "missing", "out_of_scope", "person"}
    assert set(result["router"]["by_locale"]) == {"es-419", "pt-BR"}


def test_repeated_case_reports_agreement_and_variability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import httpx

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("no HTTP connection may be opened during the bench")

    monkeypatch.setattr("httpx.Client.post", _forbidden)
    cases = load_dir(CASES_DIR)[:4]
    result = run_bench(cases, repetitions=3, fixtures_dir=FIXTURES)
    stability = result["router"]["stability"]
    assert stability["runs"] == 3
    assert 0.0 <= stability["agreement"] <= 1.0
    assert result["router"]["latency_ms"]["n"] == 4 * 3
    assert result["router"]["cost_usd"]["n"] == 4 * 3


def test_invalid_reply_is_counted_as_json_failure() -> None:
    from app.ai.llm import PromptedLLMRouter, RouterConfig
    from app.ai.transport import LLMResponse
    from eval.bench_router import INVALID, predict, run_bench
    from eval.cases import Case

    class Broken:
        def complete(self, *, model, messages, temperature=0.0):  # type: ignore[no-untyped-def]
            return LLMResponse(content="sure! here is the intent: charge")

    router = PromptedLLMRouter(Broken(), RouterConfig(cheap_model="m"))
    case = Case(
        id="t-1", locale="es-419", country="MX", turns=("no reconozco este cargo",),
        expected_intent="charge", expected_category=None, expected_outcome="clarification",
        requires_handoff=False,
    )
    assert predict(router, case)[0] == INVALID
    result = run_bench([case], router=router, repetitions=2)
    assert result["router"]["json_failures"] == {"n": 2, "count": 2}
    assert result["router"]["intent"]["accuracy"] == 0.0


def _case(case_id: str, split: str, intent: str = "charge"):  # type: ignore[no-untyped-def]
    from eval.cases import Case

    return Case(
        id=case_id, locale="es-419", country="MX", turns=(f"texto {case_id}",),
        expected_intent=intent, expected_category=None, expected_outcome="clarification",
        requires_handoff=False, split=split,
    )


def test_examples_come_only_from_development() -> None:
    import pytest

    from eval.examples import HeldOutExample, build_examples

    cases = [_case("dev-1", "development"), _case("ho-1", "held_out")]
    assert [e.case_id for e in build_examples(cases, ["dev-1"])] == ["dev-1"]
    with pytest.raises(HeldOutExample):
        build_examples(cases, ["dev-1", "ho-1"])


def test_v2_prompt_places_examples_before_the_turn_and_records_ids() -> None:
    from app.ai.llm import PromptedLLMRouter, RouterConfig
    from eval.examples import build_examples

    class Spy:
        messages: list = []

        def complete(self, *, model, messages, temperature=0.0):  # type: ignore[no-untyped-def]
            from app.ai.transport import LLMResponse

            Spy.messages = messages
            return LLMResponse(content='{"intent": "missing", "language": "es-419"}')

    examples = build_examples([_case("dev-7", "development", "missing")], ["dev-7"])
    config = RouterConfig(cheap_model="m", prompt_version="v2", examples=examples)
    PromptedLLMRouter(Spy(), config).understand("no veo mi cargo", [])
    roles = [m["role"] for m in Spy.messages]
    assert roles == ["system", "user", "assistant", "user"]
    assert "texto dev-7" in Spy.messages[1]["content"]
    assert "no veo mi cargo" in Spy.messages[-1]["content"]
    assert config.example_ids == ("dev-7",)
