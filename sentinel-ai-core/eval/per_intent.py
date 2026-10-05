"""Precision, recall and F1 per intent, with intervals that resample base situations.

The point values equal ``metrics.intent_metrics``. The interval is the 95%
percentile interval of a cluster bootstrap over bases, like the accuracy
intervals of ``eval.intervals`` (decision 018). An interval wider than
+-10 points is labelled descriptive. An undefined ratio is 0.0, as in
``metrics.intent_metrics``.
"""

from __future__ import annotations

import random
from collections import defaultdict

from eval.cases import INTENTS, Case
from eval.intervals import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    DESCRIPTIVE_HALF_WIDTH,
    cluster_of,
)

SCORES = ("precision", "recall", "f1")


def _scores(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def per_intent_intervals(
    cases: list[Case],
    predicted: list[str],
    labels: tuple[str, ...] = INTENTS,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict:
    """``{label: {n, precision, recall, f1}}``; each score has ``value``, ``interval_95`` and ``descriptive``."""
    clusters: dict[str, dict[str, list[int]]] = defaultdict(lambda: {label: [0, 0, 0] for label in labels})
    for case, guess in zip(cases, predicted):
        counts = clusters[cluster_of(case)]
        for label in labels:
            if case.expected_intent == label and guess == label:
                counts[label][0] += 1
            elif guess == label:
                counts[label][1] += 1
            elif case.expected_intent == label:
                counts[label][2] += 1
    keys = sorted(clusters)
    totals = {label: [sum(clusters[k][label][i] for k in keys) for i in range(3)] for label in labels}
    rng = random.Random(seed)
    draws: dict[str, list[list[float]]] = {label: [[], [], []] for label in labels}
    for _ in range(resamples if keys else 0):
        sums = {label: [0, 0, 0] for label in labels}
        for _ in keys:
            picked = clusters[rng.choice(keys)]
            for label in labels:
                for i in range(3):
                    sums[label][i] += picked[label][i]
        for label in labels:
            for i, value in enumerate(_scores(*sums[label])):
                draws[label][i].append(value)
    block = {}
    for label in labels:
        row: dict = {"n": totals[label][0] + totals[label][2]}
        for i, name in enumerate(SCORES):
            values = sorted(draws[label][i])
            interval = None
            if values:
                interval = [
                    round(values[int(0.025 * (len(values) - 1))], 4),
                    round(values[int(0.975 * (len(values) - 1))], 4),
                ]
            descriptive = interval is None or (interval[1] - interval[0]) / 2 > DESCRIPTIVE_HALF_WIDTH
            row[name] = {
                "value": round(_scores(*totals[label])[i], 4),
                "interval_95": interval,
                "descriptive": descriptive,
            }
        block[label] = row
    return block


__all__ = ["SCORES", "per_intent_intervals"]
