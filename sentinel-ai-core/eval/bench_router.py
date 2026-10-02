"""Component benchmark: router vs keyword baseline over the same intent cases.

Both models implement ``ModelPort`` and see the identical case list; the
result records the case ids to prove it. Offline: the router is served by
``FixtureTransport`` with committed fixtures, so no connection is opened.
"""

from __future__ import annotations

from time import perf_counter

from app.ai.demo import DemoModel
from app.ai.fixtures import FixtureTransport
from app.ai.llm import PromptedLLMRouter, RouterConfig
from app.ai.transport import InvalidReply
from eval import metrics
from eval.cases import Case


INVALID = "invalid"


def predict(model, case: Case) -> tuple[str, str, float, float]:
    """One understanding call; a reply that is not the expected JSON predicts ``invalid``."""
    started = perf_counter()
    try:
        result = model.understand(case.message, list(case.turns))
    except InvalidReply:
        return INVALID, INVALID, (perf_counter() - started) * 1000, 0.0
    latency_ms = (perf_counter() - started) * 1000
    return result.kind.value, result.language.value, latency_ms, float(result.cost_usd)


def default_router(fixtures_dir, prompt_version: str = "v1") -> PromptedLLMRouter:
    config = RouterConfig(
        cheap_model="cheap-eval",
        strong_model="strong-eval",
        default_model="default-eval",
        prompt_version=prompt_version,
    )
    return PromptedLLMRouter(FixtureTransport(fixtures_dir, prompt_version), config)


def run_bench(
    cases: list[Case],
    router=None,
    baseline=None,
    repetitions: int = 3,
    fixtures_dir=None,
) -> dict:
    router = router if router is not None else default_router(fixtures_dir or "app/ai/fixtures")
    baseline = baseline if baseline is not None else DemoModel()
    case_ids = [c.id for c in cases]
    models = {"router": router, "baseline": baseline}
    comparison = {"case_ids": case_ids, "n": len(cases), "repetitions": repetitions}
    for name, model in models.items():
        rep_intents: list[list[str]] = []
        rep_locales: list[list[str]] = []
        latencies: list[float] = []
        costs: list[float] = []
        first_pairs: list[tuple[str, str]] = []
        for _ in range(max(1, repetitions)):
            intents, locales = [], []
            for case in cases:
                intent, language, latency_ms, cost = predict(model, case)
                intents.append(intent)
                locales.append(language)
                latencies.append(latency_ms)
                costs.append(cost)
            rep_intents.append(intents)
            rep_locales.append(locales)
        for case, intent in zip(cases, rep_intents[0]):
            first_pairs.append((case.expected_intent, intent))
        by_locale = {}
        for locale in sorted({c.locale for c in cases}):
            subset = [(e, p) for (e, p), c in zip(first_pairs, cases) if c.locale == locale]
            by_locale[locale] = metrics.intent_metrics(subset)
        # Component safety: injected instructions must not divert understanding.
        # A must-not-pass case passes when the predicted intent still matches
        # the label; a diversion is recorded as a failure by name.
        safety_items = [
            {"id": c.id, "must_not_pass": c.must_not_pass,
             "outcome": "clarification" if p == c.expected_intent else "case_confirmation"}
            for c, p in zip(cases, rep_intents[0])
        ]
        comparison[name] = {
            "n": len(cases),
            "intent": metrics.intent_metrics(first_pairs),
            "by_locale": by_locale,
            "safety": metrics.safety_pass_rate(safety_items),
            "stability": metrics.stability_agreement(rep_intents),
            "json_failures": {
                "n": sum(len(rep) for rep in rep_intents),
                "count": sum(rep.count(INVALID) for rep in rep_intents),
            },
            "latency_ms": metrics.variability(latencies),
            "cost_usd": metrics.variability(costs),
            "model": model.describe().model,
            "route": model.describe().route,
            "prompt_version": model.describe().prompt_version,
        }
    comparison["identical_set"] = comparison["case_ids"] == case_ids
    return comparison


__all__ = ["INVALID", "default_router", "predict", "run_bench"]
