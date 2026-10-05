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


def _draft_rows(cases: list[Case], drafts: list) -> list[dict]:  # type: ignore[no-untyped-def]
    """Draft plus its validation against the verified slots (eval-v8)."""
    from app.ai.drafts import DraftFacts, validate_draft

    rows = []
    for case, draft in zip(cases, drafts):
        if draft is None:
            rows.append({"id": case.id, "draft": None, "draft_ok": None, "draft_reason": None})
            continue
        slots = case.expected_slots or {}
        facts = DraftFacts(
            merchant=slots.get("merchant_words"),
            amount=str(slots.get("amount")) if slots.get("amount") is not None else None,
            date=slots.get("date_phrase"),
        )
        ok, reason = validate_draft(draft, facts, case.locale)
        rows.append({"id": case.id, "draft": draft, "draft_ok": ok, "draft_reason": reason})
    return rows


@dataclass
class Version:
    model: object
    # Transport whose ``repetition`` selects the recorded pass; None for the baseline.
    transport: object | None = None
    repetitions: int = 1
    repeat_ids: frozenset[str] = field(default_factory=frozenset)


def _call(model, case: Case, transport=None) -> tuple:  # type: ignore[no-untyped-def]
    """One understanding call plus the v3 fields (subtype, slots, draft)."""
    started = perf_counter()
    try:
        result = model.understand(case.message, list(case.turns))
    except InvalidReply:
        intent, cost, subtype, slots, draft = INVALID, 0.0, None, None, None
    except ModelUnavailable:
        intent, cost, subtype, slots, draft = UNAVAILABLE, 0.0, None, None, None
    else:
        intent, cost = result.kind.value, float(result.cost_usd)
        subtype, slots, draft = result.subtype, result.slots, result.reply_draft
    info = model.describe()
    latency_ms = (perf_counter() - started) * 1000
    recorded = getattr(transport, "last_latency_ms", None)
    if recorded:
        latency_ms = recorded
    return intent, latency_ms, cost, info.model, info.route, subtype, slots, draft


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
    predicted_subtypes = [row[5] for row in first]
    predicted_slots = [row[6] for row in first]
    predicted_drafts = [row[7] for row in first]
    draft_rows = _draft_rows(cases, predicted_drafts)
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
        # eval-v8 additions: subtype, slots, drafts and unsafe wording.
        "subtype": metrics.subtype_accuracy(cases, predicted_subtypes),
        "slots": metrics.slot_precision(
            [c.expected_slots for c in cases], predicted_slots
        ),
        "drafts": metrics.rejected_draft_rate(draft_rows),
        "unsafe_wording": metrics.unsafe_wording(draft_rows),
    }


def with_high_risk_repeats(
    versions: dict[str, Version], cases: list[Case], repetitions: int = 3
) -> dict[str, Version]:
    """Three recorded passes over the high-risk subset (eval-v8).

    Attacks and must-handoff cases get ``repetitions`` passes. The baseline
    keeps one pass: it has no recorded repetitions.
    """
    risky = metrics.high_risk_ids(cases)
    out = {}
    for name, version in versions.items():
        if name == "baseline":
            out[name] = version
            continue
        out[name] = Version(
            model=version.model,
            transport=version.transport,
            repetitions=repetitions,
            repeat_ids=frozenset(version.repeat_ids | risky) if version.repeat_ids else risky,
        )
    return out


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


__all__ = ["UNAVAILABLE", "Version", "run_version", "run_versions", "with_high_risk_repeats"]
