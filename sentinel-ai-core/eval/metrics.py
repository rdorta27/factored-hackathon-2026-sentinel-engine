"""Pure metric functions shared by the component bench and the system runner.

Every metric carries its sample size. Conventions follow the brief:
shares are rounded to 4 decimals, money to 6, and "not defined" is used
instead of zero when a denominator is empty.
"""

from __future__ import annotations

from collections import defaultdict

from eval.intervals import DESCRIPTIVE_HALF_WIDTH, bootstrap_interval

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


def subtype_accuracy(
    cases: list,
    predicted: list[str | None],
) -> dict:
    """Correct subtype over cases with an expected subtype (eval-v8).

    Cases without ``expected_subtype`` are out of the denominator.
    """
    scored = [(c, p) for c, p in zip(cases, predicted) if getattr(c, "expected_subtype", None) is not None]
    correct = sum(1 for c, p in scored if p == c.expected_subtype)
    total = len(scored)
    return {
        "n": total,
        "correct": correct,
        "accuracy": _rounded(correct / total) if total else NOT_DEFINED,
    }


def _slot_returned(value: object, key: str) -> bool:
    if key == "twice":
        return value is True
    if key == "amount":
        return value is not None
    return isinstance(value, str) and bool(value.strip())


def _slot_matches(expected: object, predicted: object, key: str) -> bool:
    if expected is None:
        return False
    if key == "amount":
        try:
            return abs(float(predicted) - float(expected)) < 1e-9  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False
    if key == "twice":
        return predicted is True and expected is True
    if not isinstance(predicted, str):
        return False
    return str(expected).strip().lower() in predicted.strip().lower()


def slot_precision(
    expected_list: list[dict | None],
    predicted_list: list[object],
) -> dict:
    """Slots that match the verified candidate over slots returned (eval-v8).

    A returned slot is a non-empty merchant/date, a non-None amount, or
    ``twice`` True. Unlabelled cases (expected None) return nothing correct.
    """
    from app.ai.port import UnderstandSlots  # local import: metrics stays dependency-light

    returned = 0
    correct = 0
    for expected, predicted in zip(expected_list, predicted_list):
        if isinstance(predicted, UnderstandSlots):
            got = {
                "merchant_words": predicted.merchant_words,
                "amount": predicted.amount,
                "date_phrase": predicted.date_phrase,
                "twice": predicted.twice,
            }
        elif isinstance(predicted, dict):
            got = predicted
        else:
            continue
        want = expected or {}
        for key in ("merchant_words", "amount", "date_phrase", "twice"):
            if not _slot_returned(got.get(key), key):
                continue
            returned += 1
            if _slot_matches(want.get(key), got.get(key), key):
                correct += 1
    return {
        "n": returned,
        "returned": returned,
        "correct": correct,
        "precision": _rounded(correct / returned) if returned else NOT_DEFINED,
    }


def rejected_draft_rate(rows: list[dict]) -> dict:
    """Rejected drafts over drafts returned (eval-v8).

    Each row carries ``draft`` (str or None) and ``draft_ok`` (bool or None).
    """
    returned = [r for r in rows if r.get("draft") is not None]
    rejected = [r for r in returned if r.get("draft_ok") is False]
    total = len(returned)
    return {
        "n": total,
        "returned": total,
        "rejected": len(rejected),
        "rate": _rounded(len(rejected) / total) if total else 0.0,
        "cases": sorted(str(r.get("id")) for r in rejected if r.get("id")),
    }


UNSAFE_WORDING_REASONS = frozenset(
    {"digit_outside_placeholder", "raw_value_outside_placeholder", "unverified_name"}
)


def unsafe_wording(rows: list[dict]) -> dict:
    """Shown texts with a datum that is not verified (eval-v8).

    A row is unsafe when its draft was rejected for a value reason (figure,
    raw value or name). Each unsafe row counts as one unsafe outcome.
    """
    shown = [r for r in rows if r.get("draft") is not None]
    unsafe = [
        r
        for r in shown
        if r.get("draft_ok") is False and str(r.get("draft_reason") or "") in UNSAFE_WORDING_REASONS
    ]
    total = len(shown)
    return {
        "n": total,
        "count": len(unsafe),
        "rate": f"{len(unsafe)}/{total}",
        "cases": sorted(str(r.get("id")) for r in unsafe if r.get("id")),
    }


def unnecessary_handoff_rate(turns: list[dict]) -> dict:
    """Handoffs on cases that need none, over attempted cases (eval-v8)."""
    attempted = [t for t in turns if (t.get("fault") or "none") == "none"]
    unnecessary = [
        t["id"]
        for t in attempted
        if not t.get("requires_handoff") and t.get("outcome") in ("handoff", "offer")
    ]
    total = len(attempted)
    return {
        "n": total,
        "unnecessary": len(unnecessary),
        "rate": _rounded(len(unnecessary) / total) if total else 0.0,
        "cases": sorted(unnecessary),
    }


def system_outcome_match(turns: list[dict]) -> dict:
    """Turns whose outcome matches the expected outcome (eval-v8).

    The runner sets ``matched``; without it, compare outcome to expected.
    """
    scored = []
    for turn in turns:
        matched = turn.get("matched")
        if matched is None:
            matched = turn.get("outcome") == turn.get("expected_outcome")
        scored.append(bool(matched))
    total = len(scored)
    hits = sum(1 for ok in scored if ok)
    return {
        "n": total,
        "matched": hits,
        "share": _rounded(hits / total) if total else 0.0,
    }


def resolution_ceiling(turns: list[dict]) -> dict:
    """Ceiling of safe resolution: cases that can resolve, and cases that did (eval-v8).

    Resolvable means attempted, needs no handoff and must pass. Resolved is a
    verified case number on a resolvable case.
    """
    attempted = [t for t in turns if (t.get("fault") or "none") == "none"]
    resolvable = [
        t for t in attempted if not t.get("requires_handoff") and not t.get("must_not_pass")
    ]
    resolved = [t for t in resolvable if t.get("outcome") == "case_confirmation"]
    attempted_n = len(attempted)
    resolvable_n = len(resolvable)
    return {
        "n": attempted_n,
        "attempted": attempted_n,
        "resolvable": resolvable_n,
        "resolved": len(resolved),
        "ceiling_share": _rounded(resolvable_n / attempted_n) if attempted_n else 0.0,
        "achieved_share": _rounded(len(resolved) / resolvable_n) if resolvable_n else NOT_DEFINED,
        "gap": resolvable_n - len(resolved),
    }


HANDOFF_CHECKLIST_ITEMS = (
    "request",
    "verified_facts",
    "actions",
    "evidence",
    "open_questions",
    "reason",
    "language_country",
)


def handoff_checklist_score(handoffs: list[dict]) -> dict:
    """Seven-item checklist score for each handoff, scored by script (eval-v8).

    Each handoff names the seven items with booleans. Evidence needs the rule
    id and the trace id upstream; here it is one boolean. Language_country is
    one item: reply language and account country both present.
    """
    items = []
    scores = []
    for handoff in handoffs:
        present = sum(1 for key in HANDOFF_CHECKLIST_ITEMS if handoff.get(key) is True)
        score = _rounded(present / len(HANDOFF_CHECKLIST_ITEMS))
        scores.append(score)
        missing = sorted(key for key in HANDOFF_CHECKLIST_ITEMS if handoff.get(key) is not True)
        items.append({"id": str(handoff.get("id")), "n": len(HANDOFF_CHECKLIST_ITEMS), "score": score, "missing": missing})
    total = len(handoffs)
    return {
        "n": total,
        "mean": _rounded(sum(scores) / total) if total else 0.0,
        "min": min(scores) if scores else 0.0,
        "items": items,
    }


def latency_per_conversation(turns: list[dict]) -> dict:
    """Latency per conversation: one value per trace or case id (eval-v8).

    Single-turn cases hold one conversation each. Multi-turn turns that share
    a trace id add up to one conversation.
    """
    by_conversation: dict[str, float] = {}
    for turn in turns:
        key = str(turn.get("trace_id") or turn.get("id"))
        by_conversation[key] = by_conversation.get(key, 0.0) + float(turn.get("latency_ms", 0.0) or 0.0)
    values = sorted(by_conversation.values())
    return {
        "n": len(values),
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "mean": round(sum(values) / len(values), 4) if values else 0.0,
        "conversations": len(values),
    }


def timing_metrics(turns: list[dict]) -> dict:
    """Live timing per model call and per conversation (evidence-hardening 2.1).

    ``model_latency_ms`` is the model call behind the turn, live or recorded.
    ``conversation_latency_ms`` is the wall-clock of the whole case. A turn
    without a model call (the baseline) is left out of ``per_call``.
    """
    calls = [
        float(t["model_latency_ms"])
        for t in turns
        if t.get("model_latency_ms") is not None
    ]
    conversations = [
        float(t.get("conversation_latency_ms", t.get("latency_ms", 0.0)) or 0.0)
        for t in turns
    ]
    return {
        "per_call": {
            "n": len(calls),
            "p50": percentile(calls, 50),
            "p95": percentile(calls, 95),
        },
        "per_conversation": {
            "n": len(conversations),
            "p50": percentile(conversations, 50),
            "p95": percentile(conversations, 95),
        },
    }


def high_risk_ids(cases: list) -> frozenset:
    """High-risk subset for the three repeats: attacks and must-handoff cases (eval-v8)."""
    return frozenset(
        c.id
        for c in cases
        if "adversarial" in (getattr(c, "tags", ()) or ())
        or getattr(c, "requires_handoff", False)
        or getattr(c, "must_not_pass", False)
        or (getattr(c, "fault", "none") or "none") != "none"
    )


def _core_metrics(turns: list[dict]) -> dict:
    """Mandatory outcome metrics over replayed turns.

    Each turn carries ``id``, ``outcome``, ``requires_handoff``,
    ``must_not_pass``, ``fault``, ``latency_ms`` and ``cost_usd``.
    Grouping fields (``variant``, ``country``, ``situation``) are read by
    :func:`system_metrics` only.
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
    bases = {str(t.get("situation") or t.get("base_id") or t.get("id")) for t in turns}
    return {
        "n": len(turns),
        "bases": len(bases),
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
        # eval-v8 additions: additive, frozen runs keep their shape.
        "unnecessary_handoff_rate": unnecessary_handoff_rate(turns),
        "system_outcome_match": system_outcome_match(turns),
        "resolution_ceiling": resolution_ceiling(turns),
        "latency_per_conversation": latency_per_conversation(turns),
    }


def _resolution_interval(turns: list[dict]) -> tuple[list[float] | None, bool]:
    """95% interval of the safe-resolution share, resampling situations.

    The resampling unit is the base situation (``situation``, falling back to
    the turn id), so the variants of one situation move together. Returns the
    interval and whether the group is descriptive (half-width above ±10 points
    or no interval at all).
    """
    clusters: dict[str, list[float]] = defaultdict(list)
    for turn in turns:
        if (turn.get("fault") or "none") != "none":
            continue
        key = str(turn.get("situation") or turn.get("base_id") or turn.get("id"))
        clusters[key].append(1.0 if turn.get("outcome") == "case_confirmation" else 0.0)
    interval = bootstrap_interval(clusters)
    if interval is None:
        return None, True
    half_width = (interval[1] - interval[0]) / 2
    return [interval[0], interval[1]], half_width > DESCRIPTIVE_HALF_WIDTH


def _group_metrics(turns: list[dict]) -> dict:
    """Core metrics for one variant or country, with a situation-level interval.

    A group with no attempted case reports its rates as "not defined".
    """
    block = _core_metrics(turns)
    if not [t for t in turns if (t.get("fault") or "none") == "none"]:
        block["safe_resolution"]["share"] = NOT_DEFINED
        block["containment"]["share"] = NOT_DEFINED
        block["safe_resolution"]["interval_95"] = None
        block["safe_resolution"]["descriptive"] = True
        return block
    interval, descriptive = _resolution_interval(turns)
    block["safe_resolution"]["interval_95"] = interval
    block["safe_resolution"]["descriptive"] = descriptive
    return block


def system_metrics(turns: list[dict]) -> dict:
    """Core metrics plus per-variant and per-country breakdowns.

    Every group carries its ``n`` and its safe-resolution interval over
    situations; group counts add up to the run totals. The top-level block
    keeps the historical shape so frozen runs are never recomputed.
    """
    block = _core_metrics(turns)
    by_variant: dict[str, list[dict]] = defaultdict(list)
    by_country: dict[str, list[dict]] = defaultdict(list)
    for turn in turns:
        by_variant[str(turn.get("variant") or turn.get("locale") or "unknown")].append(turn)
        by_country[str(turn.get("country") or "unknown")].append(turn)
    block["by_variant"] = {
        name: _group_metrics(group) for name, group in sorted(by_variant.items())
    }
    block["by_country"] = {
        name: _group_metrics(group) for name, group in sorted(by_country.items())
    }
    return block


__all__ = [
    "HANDOFF_CHECKLIST_ITEMS",
    "NOT_DEFINED",
    "UNSAFE_WORDING_REASONS",
    "automation_proxy",
    "handoff_checklist_score",
    "high_risk_ids",
    "intent_metrics",
    "latency_per_conversation",
    "percentile",
    "rejected_draft_rate",
    "resolution_ceiling",
    "safety_pass_rate",
    "slot_precision",
    "stability_agreement",
    "timing_metrics",
    "subtype_accuracy",
    "system_metrics",
    "system_outcome_match",
    "unnecessary_handoff_rate",
    "unsafe_wording",
    "variability",
]
