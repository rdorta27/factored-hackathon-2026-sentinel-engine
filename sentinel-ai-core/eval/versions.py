"""Run the baseline and both router versions over the identical cases.

Stability comes only from separately recorded repetitions: a repetition is
served by setting the transport's ``repetition`` before the pass, and a case
with no recording for that repetition is left out of the stability n rather
than replayed from repetition 0 (evaluation-runner spec).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from time import perf_counter

from app.ai.transport import InvalidReply, ModelUnavailable
from eval import metrics
from eval.bench_router import INVALID
from eval.cases import Case
from eval.intervals import breakdown
from eval.paired import paired, variant_losses
from eval.per_intent import per_intent_intervals

UNAVAILABLE = "unavailable"


@dataclass
class Version:
    model: object
    # Transport whose ``repetition`` selects the recorded pass; None for the baseline.
    transport: object | None = None
    repetitions: int = 1
    repeat_ids: frozenset[str] = field(default_factory=frozenset)


def _call(model, case: Case, transport=None) -> tuple[str, float, float, str, str]:  # type: ignore[no-untyped-def]
    started = perf_counter()
    try:
        result = model.understand(case.message, list(case.turns))
    except InvalidReply:
        intent, cost = INVALID, 0.0
    except ModelUnavailable:
        intent, cost = UNAVAILABLE, 0.0
    else:
        intent, cost = result.kind.value, float(result.cost_usd)
    info = model.describe()
    latency_ms = (perf_counter() - started) * 1000
    recorded = getattr(transport, "last_latency_ms", None)
    if recorded:
        latency_ms = recorded
    return intent, latency_ms, cost, info.model, info.route


def run_version(cases: list[Case], version: Version) -> dict:
    if version.transport is not None:
        version.transport.repetition = 0
    first = [_call(version.model, case, version.transport) for case in cases]
    predicted = [row[0] for row in first]
    passes: dict[str, list[str]] = {case.id: [row[0]] for case, row in zip(cases, first)}
    for repetition in range(1, max(1, version.repetitions)):
        if version.transport is None:
            break
        version.transport.repetition = repetition
        for case in cases:
            if case.id not in version.repeat_ids:
                continue
            intent = _call(version.model, case)[0]
            if intent != UNAVAILABLE:
                passes[case.id].append(intent)
    if version.transport is not None:
        version.transport.repetition = 0
    repeated = [votes for votes in passes.values() if len(votes) >= 2]
    runs = min((len(v) for v in repeated), default=0)
    stability = metrics.stability_agreement([[votes[r] for votes in repeated] for r in range(runs)])
    stability["recorded_repetitions"] = runs
    pairs = [(case.expected_intent, p) for case, p in zip(cases, predicted)]
    info = version.model.describe()
    config = getattr(version.model, "_config", None)
    return {
        "n": len(cases),
        "predicted": predicted,
        "intent": metrics.intent_metrics(pairs),
        "per_intent": per_intent_intervals(cases, predicted),
        "breakdown": breakdown(cases, predicted),
        "variant_losses": variant_losses(cases, predicted),
        "json_failures": {"n": len(cases), "count": predicted.count(INVALID)},
        "unavailable": {"n": len(cases), "count": predicted.count(UNAVAILABLE)},
        "stability": stability,
        "latency_ms": metrics.variability([row[1] for row in first]),
        "cost_usd": {**metrics.variability([row[2] for row in first]), "total": round(sum(r[2] for r in first), 6)},
        "routes": {"n": len(cases), "count": dict(sorted(Counter(row[4] for row in first).items()))},
        "models": {"n": len(cases), "count": dict(sorted(Counter(row[3] for row in first).items()))},
        "prompt_version": info.prompt_version,
        "example_ids": list(getattr(config, "example_ids", ()) or ()),
    }


def run_versions(cases: list[Case], versions: dict[str, Version], reference: str = "baseline") -> dict:
    """Every version over the same case ids, plus paired comparisons against ``reference``."""
    case_ids = [case.id for case in cases]
    results = {name: run_version(cases, version) for name, version in versions.items()}
    comparisons = {}
    names = list(versions)
    for i, before in enumerate(names):
        for after in names[i + 1 :]:
            comparisons[f"{after}_vs_{before}"] = paired(
                cases, results[before]["predicted"], results[after]["predicted"]
            )
    return {
        "n": len(cases),
        "case_ids": case_ids,
        "identical_set": True,
        "reference": reference,
        "versions": results,
        "paired": comparisons,
    }


__all__ = ["UNAVAILABLE", "Version", "run_version", "run_versions"]
