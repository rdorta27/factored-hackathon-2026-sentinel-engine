"""Breakdowns with 95% intervals that resample base situations.

The four variants of a base share intent, amount and merchant, so they are
not independent cases. Intervals therefore resample bases (cluster
bootstrap); a case without a base is its own cluster. A breakdown whose
interval is wider than ±10 points is labelled descriptive (decision 018).
"""

from __future__ import annotations

import random
from collections import defaultdict

from eval.cases import Case

BOOTSTRAP_RESAMPLES = 2000
BOOTSTRAP_SEED = 20261001
DESCRIPTIVE_HALF_WIDTH = 0.10


def cluster_of(case: Case) -> str:
    return case.base_id or case.id


def bootstrap_interval(
    clusters: dict[str, list[float]],
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float] | None:
    """95% percentile interval of the pooled mean over resampled clusters."""
    keys = sorted(clusters)
    if not keys:
        return None
    rng = random.Random(seed)
    values = []
    for _ in range(resamples):
        total, count = 0.0, 0
        for _ in keys:
            items = clusters[rng.choice(keys)]
            total += sum(items)
            count += len(items)
        values.append(total / count if count else 0.0)
    values.sort()
    low = values[int(0.025 * (resamples - 1))]
    high = values[int(0.975 * (resamples - 1))]
    return round(low, 4), round(high, 4)


def accuracy_block(cases: list[Case], correct: list[bool]) -> dict:
    clusters: dict[str, list[float]] = defaultdict(list)
    for case, ok in zip(cases, correct):
        clusters[cluster_of(case)].append(1.0 if ok else 0.0)
    n = len(cases)
    hits = sum(1 for ok in correct if ok)
    interval = bootstrap_interval(clusters)
    descriptive = interval is None or (interval[1] - interval[0]) / 2 > DESCRIPTIVE_HALF_WIDTH
    return {
        "n": n,
        "clusters": len(clusters),
        "accuracy": round(hits / n, 4) if n else 0.0,
        "interval_95": list(interval) if interval else None,
        "descriptive": descriptive,
    }


def breakdown(cases: list[Case], predicted: list[str]) -> dict:
    """Overall, per-variant and per-intent accuracy, each with n and a base-level interval."""
    correct = [p == c.expected_intent for c, p in zip(cases, predicted)]

    def by(key) -> dict:  # type: ignore[no-untyped-def]
        groups: dict[str, list[int]] = defaultdict(list)
        for index, case in enumerate(cases):
            value = key(case)
            if value is not None:
                groups[value].append(index)
        return {
            name: accuracy_block([cases[i] for i in idx], [correct[i] for i in idx])
            for name, idx in sorted(groups.items())
        }

    return {
        "overall": accuracy_block(cases, correct),
        "by_variant": by(lambda c: c.variant),
        "by_intent": by(lambda c: c.expected_intent),
        "method": f"cluster bootstrap over bases, {BOOTSTRAP_RESAMPLES} resamples, seed {BOOTSTRAP_SEED}",
    }


__all__ = [
    "BOOTSTRAP_RESAMPLES",
    "BOOTSTRAP_SEED",
    "DESCRIPTIVE_HALF_WIDTH",
    "accuracy_block",
    "bootstrap_interval",
    "breakdown",
    "cluster_of",
]
