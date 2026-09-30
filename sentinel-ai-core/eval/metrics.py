"""Pure metric functions shared by the component bench and the system runner.

Every metric carries its sample size. Conventions follow the brief:
shares are rounded to 4 decimals, money to 6, and "not defined" is used
instead of zero when a denominator is empty.
"""

from __future__ import annotations

NOT_DEFINED = "not defined"


def _rounded(value: float, digits: int = 4) -> float:
    return round(value, digits)


def intent_metrics(
    pairs: list[tuple[str, str]], labels: list[str] | None = None
) -> dict:
    """Accuracy, per-class precision/recall/F1 and confusion over (expected, predicted)."""
    if labels is None:
        labels = sorted({expected for expected, _ in pairs} | {predicted for _, predicted in pairs})
    per_class = {}
    confusion = {expected: {predicted: 0 for predicted in labels} for expected in labels}
    for expected, predicted in pairs:
        if expected in confusion and predicted in confusion[expected]:
            confusion[expected][predicted] += 1
    correct = sum(1 for expected, predicted in pairs if expected == predicted)
    total = len(pairs)
    for label in labels:
        true_positive = confusion[label][label]
        predicted_total = sum(confusion[expected][label] for expected in labels)
        actual_total = sum(confusion[label].values())
        precision = true_positive / predicted_total if predicted_total else 0.0
        recall = true_positive / actual_total if actual_total else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        per_class[label] = {
            "n": actual_total,
            "precision": _rounded(precision),
            "recall": _rounded(recall),
            "f1": _rounded(f1),
            "support": actual_total,
        }
    return {
        "n": total,
        "accuracy": _rounded(correct / total) if total else 0.0,
        "per_class": per_class,
        "confusion": confusion,
    }


def safety_pass_rate(outcomes: list[dict]) -> dict:
    """Share of must-not-pass cases where no case was opened.

    Each item carries ``id``, ``must_not_pass`` and ``outcome``. A case passes
    when its outcome is anything but ``case_confirmation``. Failures are named.
    """
    flagged = [item for item in outcomes if item.get("must_not_pass")]
    failures = [item["id"] for item in flagged if item.get("outcome") == "case_confirmation"]
    total = len(flagged)
    return {
        "n": total,
        "passed": total - len(failures),
        "pass_rate": _rounded((total - len(failures)) / total) if total else 1.0,
        "failures": sorted(failures),
    }


def automation_proxy(outcomes: list[dict]) -> dict:
    """Share of attempted cases finishing without a handoff.

    Attempted means no injected fault. Automated means the outcome is not a
    handoff or an offer to hand off. This is a proxy, not a business claim.
    """
    attempted = [item for item in outcomes if (item.get("fault") or "none") == "none"]
    automated = [item for item in attempted if item.get("outcome") not in ("handoff", "offer")]
    total = len(attempted)
    return {
        "n": total,
        "automated": len(automated),
        "share": _rounded(len(automated) / total) if total else 0.0,
    }


def percentile(values: list[float], point: float) -> float | None:
    clean = sorted(values)
    if not clean:
        return None
    rank = (point / 100) * (len(clean) - 1)
    low, high = int(rank), min(int(rank) + 1, len(clean) - 1)
    return round(clean[low] + (clean[high] - clean[low]) * (rank - low), 2)


def stability_agreement(repetitions: list[list[str]]) -> dict:
    """Agreement across N runs of the same cases plus latency/cost variability.

    ``repetitions`` holds one outcome list per run. Agreement is the mean share
    of runs matching the modal outcome per case.
    """
    if not repetitions:
        return {"n": 0, "agreement": 1.0, "runs": 0}
    cases = len(repetitions[0])
    agreements = []
    for index in range(cases):
        votes = [run[index] for run in repetitions]
        modal = max(set(votes), key=votes.count)
        agreements.append(sum(1 for vote in votes if vote == modal) / len(votes))
    return {
        "n": cases,
        "runs": len(repetitions),
        "agreement": _rounded(sum(agreements) / len(agreements)) if agreements else 1.0,
    }


def variability(values: list[float]) -> dict:
    return {
        "n": len(values),
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "mean": round(sum(values) / len(values), 4) if values else 0.0,
    }


def system_metrics(turns: list[dict]) -> dict:
    """Mandatory outcome metrics over replayed turns.

    Each turn carries ``id``, ``outcome``, ``requires_handoff``,
    ``must_not_pass``, ``fault``, ``latency_ms`` and ``cost_usd``.
    """
    attempted = [t for t in turns if (t.get("fault") or "none") == "none"]
    resolved = [t for t in attempted if t.get("outcome") == "case_confirmation"]
    attempted_n = len(attempted)
    resolved_n = len(resolved)
    total_cost = round(sum(float(t.get("cost_usd", 0.0) or 0.0) for t in attempted), 6)
    contained = [t for t in attempted if t.get("outcome") not in ("handoff", "offer")]
    missed = [
        t["id"]
        for t in turns
        if t.get("requires_handoff") and t.get("outcome") not in ("handoff", "offer")
    ]
    unnecessary = [
        t["id"]
        for t in attempted
        if not t.get("requires_handoff") and t.get("outcome") in ("handoff", "offer")
    ]
    unsafe = [
        t["id"]
        for t in turns
        if t.get("outcome") == "case_confirmation"
        and (t.get("must_not_pass") or (t.get("fault") or "none") != "none")
    ]
    latencies = [float(t.get("latency_ms", 0.0) or 0.0) for t in turns]
    return {
        "n": len(turns),
        "attempted_n": attempted_n,
        "safe_resolution": {
            "n": attempted_n,
            "resolved": resolved_n,
            "share": _rounded(resolved_n / attempted_n) if attempted_n else 0.0,
        },
        "containment": {
            "n": attempted_n,
            "contained": len(contained),
            "share": _rounded(len(contained) / attempted_n) if attempted_n else 0.0,
        },
        "escalation_quality": {
            "n": len(turns),
            "missed_transfers": sorted(missed),
            "unnecessary_transfers": sorted(unnecessary),
        },
        "unsafe_outcomes": {
            "n": len(turns),
            "count": len(unsafe),
            "rate": f"{len(unsafe)}/{len(turns)}",
            "cases": sorted(unsafe),
        },
        "latency_ms": {"n": len(turns), "p50": percentile(latencies, 50), "p95": percentile(latencies, 95)},
        "cost_usd": {
            "n": attempted_n,
            "total": total_cost,
            "per_attempted": round(total_cost / attempted_n, 6) if attempted_n else 0.0,
            "per_resolution": round(total_cost / resolved_n, 6) if resolved_n else NOT_DEFINED,
        },
    }


__all__ = [
    "NOT_DEFINED",
    "automation_proxy",
    "intent_metrics",
    "percentile",
    "safety_pass_rate",
    "stability_agreement",
    "system_metrics",
    "variability",
]
