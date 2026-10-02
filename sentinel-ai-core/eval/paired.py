"""Case-by-case comparisons on the same cases (decision 018, D4 to D6).

Two versions are compared on identical cases: the ids each one fixes and
breaks, the net difference and its 95% interval, resampling bases. Variants
are compared inside each base: a base counts as a loss for a variant when
that variant is wrong and the best variant is right.
"""

from __future__ import annotations

from collections import defaultdict

from eval.cases import VARIANTS, Case
from eval.intervals import bootstrap_interval, cluster_of


def paired(cases: list[Case], before: list[str], after: list[str]) -> dict:
    """What ``after`` fixes and breaks relative to ``before`` on the same cases."""
    if not (len(cases) == len(before) == len(after)):
        raise ValueError("paired comparison needs one prediction per case for both versions")
    fixed, broken = [], []
    clusters: dict[str, list[float]] = defaultdict(list)
    for case, b, a in zip(cases, before, after):
        was, now = b == case.expected_intent, a == case.expected_intent
        if now and not was:
            fixed.append(case.id)
        elif was and not now:
            broken.append(case.id)
        clusters[cluster_of(case)].append(float(now) - float(was))
    n = len(cases)
    net = len(fixed) - len(broken)
    interval = bootstrap_interval(clusters)
    return {
        "n": n,
        "fixed": sorted(fixed),
        "broken": sorted(broken),
        "net": net,
        "net_share": round(net / n, 4) if n else 0.0,
        "interval_95": list(interval) if interval else None,
        "above_zero": bool(interval and interval[0] > 0),
    }


def variant_losses(cases: list[Case], predicted: list[str]) -> dict:
    """Per variant, the net loss against the best variant over bases that have both."""
    correct: dict[str, dict[str, bool]] = defaultdict(dict)
    for case, p in zip(cases, predicted):
        if case.base_id and case.variant:
            correct[case.base_id][case.variant] = p == case.expected_intent
    accuracy = {}
    for variant in VARIANTS:
        seen = [row[variant] for row in correct.values() if variant in row]
        if seen:
            accuracy[variant] = sum(seen) / len(seen)
    if not accuracy:
        return {"n": 0, "best": None, "by_variant": {}}
    best = max(sorted(accuracy), key=lambda v: accuracy[v])
    result = {}
    for variant in sorted(accuracy):
        shared = [base for base, row in correct.items() if variant in row and best in row]
        lost = sorted(base for base in shared if not correct[base][variant] and correct[base][best])
        won = sorted(base for base in shared if correct[base][variant] and not correct[base][best])
        result[variant] = {
            "n": len(shared),
            "accuracy": round(accuracy[variant], 4),
            "lost_bases": lost,
            "won_bases": won,
            "net_loss": len(lost) - len(won),
        }
    return {"n": len(correct), "best": best, "by_variant": result}


__all__ = ["paired", "variant_losses"]
