"""Report writer: summary.json plus a readable report.md, frozen write-once.

Every metric carries its sample size; a metric without ``n`` is rejected
instead of reported. Runs live under ``evidence/evaluation-runs/<run-id>/``
and an existing run is never overwritten.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

EVAL_VERSION = "2026-09-30+runner-v1"


METRIC_KEYS = frozenset(
    {"accuracy", "share", "rate", "precision", "recall", "f1", "agreement", "mean",
     "count", "resolved", "passed", "automated", "contained", "total",
     "correct", "returned", "rejected", "matched", "resolvable", "attempted",
     "ceiling_share", "achieved_share", "gap", "unnecessary", "conversations",
     "score"}
)


def validate_has_n(node, path: str = "$") -> None:  # type: ignore[no-untyped-def]
    """Reject any metric mapping that reports numbers without a sample size.

    Plain count distributions (``{"es-419": 20}``) are skipped: they carry no
    derived metric and their parent holds ``n``.
    """
    if isinstance(node, dict):
        if (set(node) & METRIC_KEYS) and "n" not in node and "denominator" not in node:
            raise ValueError(f"metric at {path} reports numbers without n")
        for key, value in node.items():
            validate_has_n(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            validate_has_n(item, f"{path}[{index}]")


def build_summary(
    *,
    run_id: str,
    comparison: dict,
    turns: list[dict],
    system: dict,
    labels: dict,
    case_mix: dict,
    failures: list[dict],
    safety: dict,
    automation: dict,
    notes: list[str] | None = None,
) -> dict:
    summary = {
        "run_id": run_id,
        "eval_version": EVAL_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "labels": labels,
        "case_mix": case_mix,
        "component": comparison,
        "system": system,
        "safety": safety,
        "automation": automation,
        "failures": failures,
        "n": system.get("n", len(turns)),
        "bases": system.get("bases", 0),
        "notes": notes or [],
    }
    validate_has_n(summary)
    return summary


def render_report(summary: dict) -> str:
    lines = [
        f"# Evaluation run {summary['run_id']}",
        "",
        f"Eval {summary['eval_version']} · labels {summary['labels'].get('run_id')} "
        f"({summary['labels'].get('summary_sha16')}) · n={summary['n']} · bases={summary.get('bases')}",
        "",
        "## Component (router vs baseline)",
    ]
    for name in ("router", "baseline"):
        block = summary["component"].get(name, {})
        intent = block.get("intent", {})
        lines.append(f"### {name}: accuracy {intent.get('accuracy')} (n={block.get('n')})")
        for label, stats in (intent.get("per_class") or {}).items():
            lines.append(
                f"- {label}: P {stats.get('precision')} R {stats.get('recall')} "
                f"F1 {stats.get('f1')} (support {stats.get('support')})"
            )
        for locale, loc in (block.get("by_locale") or {}).items():
            lines.append(f"- {locale}: accuracy {loc.get('accuracy')} (n={loc.get('n')})")
        stability = block.get("stability", {})
        lines.append(
            f"- stability: agreement {stability.get('agreement')} over "
            f"{stability.get('runs')} runs (n={stability.get('n')})"
        )
    system = summary.get("system", {})
    lines += [
        "",
        "## System",
        f"- safe resolution: {system.get('safe_resolution', {}).get('resolved')}/"
        f"{system.get('safe_resolution', {}).get('n')}",
        f"- containment share: {system.get('containment', {}).get('share')}",
        f"- unsafe outcomes: {system.get('unsafe_outcomes', {}).get('rate')}",
        f"- latency p50/p95 ms: {system.get('latency_ms', {}).get('p50')}/"
        f"{system.get('latency_ms', {}).get('p95')}",
        f"- cost per attempted/resolution USD: "
        f"{system.get('cost_usd', {}).get('per_attempted')}/"
        f"{system.get('cost_usd', {}).get('per_resolution')}",
        "",
        "## Failures",
    ]
    if summary.get("failures"):
        for failure in summary["failures"]:
            lines.append(f"- {failure.get('id')}: {failure.get('reason')}")
    else:
        lines.append("- none")
    if summary.get("notes"):
        lines += ["", "## Notes"] + [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


def render_resolution(summary: dict) -> str:
    """Readable view of a resolution run; every number comes from ``summary``."""
    system = summary["system"]
    timing = summary.get("timing", {})
    mode = timing.get("mode", "replay")
    live = mode == "live"
    latency_note = (
        "The latency and the cost come from live model calls under the spend cap. "
        "The numbers are end-to-end."
        if live
        else "The latency and the cost come from a replay of committed recordings. "
        "The times are replay times, not end-to-end latency."
    )
    lines = [
        f"# Resolution measurement {summary['run_id']}",
        "",
        f"Eval {summary['eval_version']} · simulation over a mock store · "
        f"n={summary['n']} cases in {summary['situations']['n']} situations · "
        f"commit {str(summary['measured_commit'])[:12]}.",
        "",
        "> Simulation over a mock store, not a field resolution rate (decision 022).",
        f"> Timing: {mode}. {latency_note}",
        "",
        "## Safe resolution by version",
        "",
        "| Version | Safe resolutions | Share | Containment | Missed | Unnecessary | Unsafe outcomes | Cost per attempted | Cost per resolution |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for name, block in system.items():
        resolution_block = block["safe_resolution"]
        escalation = block["escalation_quality"]
        unsafe = block["unsafe_outcomes"]
        cost = block["cost_usd"]
        lines.append(
            f"| {name} | {resolution_block['resolved']} of {resolution_block['n']} | "
            f"{resolution_block['share']} | {block['containment']['share']} | "
            f"{len(escalation['missed_transfers'])} | {len(escalation['unnecessary_transfers'])} | "
            f"{unsafe['count']} ({unsafe['rate']}) | "
            f"{cost['per_attempted']} | {cost['per_resolution']} |"
        )
    if timing:
        call = timing.get("per_call", {})
        conversation = timing.get("per_conversation", {})
        cost = timing.get("cost", {})
        lines += [
            "",
            "## Timing (router_v2)",
            "",
            f"- Mode: {mode}.",
            f"- Per model call p50/p95 ms: {call.get('p50')}/{call.get('p95')} (n={call.get('n')})",
            f"- Per conversation p50/p95 ms: {conversation.get('p50')}/{conversation.get('p95')} "
            f"(n={conversation.get('n')})",
            f"- Cost per attempted case / per resolution USD: "
            f"{cost.get('per_attempted')} / {cost.get('per_resolution')}",
            f"- {latency_note}",
        ]
    paired = summary["paired_resolution"]
    router = system["router_v2"]
    baseline = system["baseline"]
    safe = all(block["unsafe_outcomes"]["count"] == 0 for block in system.values())
    transferred = all(len(block["escalation_quality"]["missed_transfers"]) == 0 for block in system.values())
    lines += [
        "",
        "## Paired resolution (router_v2 vs baseline)",
        "",
        f"- fixed {len(paired['fixed'])}, broken {len(paired['broken'])}, net {paired['net']} of "
        f"{paired['n']} ({paired['net_share']}), interval {paired['interval_95']}, above zero: {paired['above_zero']}",
        "",
        "## Breakdown by language variant (safe resolution, situations as clusters)",
        "",
        "| Group | Version | Resolved | Share | 95% interval |",
        "|---|---|---|---|---|",
    ]
    for group in sorted({g for block in system.values() for g in block.get("by_variant", {})}):
        for name in ("baseline", "router_v2"):
            cell = system[name].get("by_variant", {}).get(group, {})
            safe_block = cell.get("safe_resolution", {})
            lines.append(
                f"| {group} | {name} | {safe_block.get('resolved')} of {safe_block.get('n')} | "
                f"{safe_block.get('share')} | {_interval(safe_block)} |"
            )
    lines += [
        "",
        "## Breakdown by account country (safe resolution, situations as clusters)",
        "",
        "| Group | Version | Resolved | Share | 95% interval |",
        "|---|---|---|---|---|",
    ]
    for group in sorted({g for block in system.values() for g in block.get("by_country", {})}):
        for name in ("baseline", "router_v2"):
            cell = system[name].get("by_country", {}).get(group, {})
            safe_block = cell.get("safe_resolution", {})
            lines.append(
                f"| {group} | {name} | {safe_block.get('resolved')} of {safe_block.get('n')} | "
                f"{safe_block.get('share')} | {_interval(safe_block)} |"
            )
    lines += [
        "",
        "Groups with an interval wider than ±10 points are descriptive; "
        "per-country groups of this size are descriptive by construction.",
        "System outcomes are not broken down by customer segment: cases carry "
        "no customer record, so there is nothing to group by.",
        "",
        "## Acceptance rules (decision 022)",
        "",
        f"- R1 safe: {'PASS' if safe else 'FAIL'} — "
        + "; ".join(f"{name} {block['unsafe_outcomes']['rate']}" for name, block in system.items()),
        f"- R2 no missed transfers: {'PASS' if transferred else 'FAIL'} — "
        + "; ".join(f"{name} {len(block['escalation_quality']['missed_transfers'])}" for name, block in system.items()),
        f"- R3 router resolves more (interval above zero): {'PASS' if paired['above_zero'] else 'not above zero'}",
        f"- R4 router unsafe outcomes: {'PASS' if router['unsafe_outcomes']['count'] == 0 else 'FAIL'}"
        + (f"; baseline {baseline['unsafe_outcomes']['count']}" if baseline["unsafe_outcomes"]["count"] else ""),
        "",
        f"Spend: USD {summary['spend']['spent_usd']} over {summary['spend']['n']} live calls "
        f"(cap {summary['spend']['cap_usd']}). Prices: {summary['prices']}.",
    ]
    if summary.get("notes"):
        lines += ["", "## Notes"] + [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


def freeze_run(repo_root: Path | str, run_id: str, summary: dict, report_md: str) -> Path:
    folder = Path(repo_root) / "evidence" / "evaluation-runs" / run_id
    if folder.exists():
        raise SystemExit(f"refusing to overwrite committed run {folder}; use a new run id")
    folder.mkdir(parents=True)
    (folder / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (folder / "report.md").write_text(report_md, encoding="utf-8")
    return folder


def _interval(block: dict) -> str:
    interval = block.get("interval_95")
    text = f"[{interval[0]}, {interval[1]}]" if interval else "n/a"
    return text + (" (descriptive)" if block.get("descriptive") else "")


def render_measurement(summary: dict) -> str:
    """Readable view of a held-out measurement; every number comes from ``summary``."""
    seal = summary["seal"]
    component = summary["component"]
    versions = component["versions"]
    lines = [
        f"# Held-out measurement {summary['run_id']}",
        "",
        f"Eval {summary['eval_version']} · seal {seal['hash'][:16]} · n={summary['n']} cases "
        f"from {summary.get('bases')} bases · main block n={component['n']}, same case ids for every version.",
        "",
        "## Accuracy by version",
        "",
        "| Version | n | Bases | Accuracy | 95% interval | JSON failures | Cost USD (total) | Latency p50/p95 ms |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, block in versions.items():
        overall = block["breakdown"]["overall"]
        lines.append(
            f"| {name} | {overall['n']} | {overall.get('bases')} | {overall['accuracy']} | {_interval(overall)} | "
            f"{block['json_failures']['count']}/{block['json_failures']['n']} | {block['cost_usd']['total']} | "
            f"{block['latency_ms']['p50']}/{block['latency_ms']['p95']} |"
        )
    lines += ["", "## Paired comparisons", ""]
    for name, block in component["paired"].items():
        lines.append(
            f"- {name}: fixed {len(block['fixed'])}, broken {len(block['broken'])}, net {block['net']} "
            f"of {block['n']} ({block['net_share']}), interval {block['interval_95']}, "
            f"above zero: {block['above_zero']}"
        )
        if block["broken"]:
            lines.append(f"  - broken: {', '.join(block['broken'])}")
    lines += ["", "## By variant", ""]
    for name, block in versions.items():
        losses = block["variant_losses"]
        lines.append(f"### {name} (best variant: {losses.get('best')})")
        for variant, stats in block["breakdown"]["by_variant"].items():
            loss = losses["by_variant"].get(variant, {})
            lost = ", ".join(loss.get("lost_bases", [])) or "none"
            lines.append(
                f"- {variant}: accuracy {stats['accuracy']} {_interval(stats)} "
                f"(n={stats['n']}, bases={stats.get('bases')}); "
                f"net loss {loss.get('net_loss')} of {loss.get('n')} shared bases; lost: {lost}"
            )
    lines += ["", "## By intent", ""]
    for name, block in versions.items():
        parts = [
            f"{intent} {stats['accuracy']} {_interval(stats)} (n={stats['n']}, bases={stats.get('bases')})"
            for intent, stats in block["breakdown"]["by_intent"].items()
        ]
        lines.append(f"- {name}: " + "; ".join(parts))
    lines += ["", "## v8 metrics by version", ""]
    for name, block in versions.items():
        subtype = block.get("subtype", {})
        slots = block.get("slots", {})
        drafts = block.get("drafts", {})
        wording = block.get("unsafe_wording", {})
        lines.append(
            f"- {name}: subtype accuracy {subtype.get('accuracy')} "
            f"({subtype.get('correct')}/{subtype.get('n')}); "
            f"slot precision {slots.get('precision')} "
            f"({slots.get('correct')}/{slots.get('returned')}); "
            f"rejected drafts {drafts.get('rejected')}/{drafts.get('returned')} "
            f"(rate {drafts.get('rate')}); "
            f"unsafe wording {wording.get('rate')}"
            + (f" ({', '.join(wording.get('cases', []))})" if wording.get("cases") else "")
        )
    lines += ["", "## By language and country (kind accuracy)", ""]
    for name, block in versions.items():
        breakdown = block.get("breakdown", {})
        locales = breakdown.get("by_locale", {})
        countries = breakdown.get("by_country", {})
        if locales:
            parts = [f"{loc} {stats['accuracy']} (n={stats['n']})" for loc, stats in sorted(locales.items())]
            lines.append(f"- {name} by language: " + "; ".join(parts))
        if countries:
            parts = [f"{cty} {stats['accuracy']} (n={stats['n']})" for cty, stats in sorted(countries.items())]
            lines.append(f"- {name} by country: " + "; ".join(parts))
    lines += ["", "## Stability", ""]
    for name, block in versions.items():
        stability = block["stability"]
        lines.append(
            f"- {name}: agreement {stability['agreement']} over {stability.get('recorded_repetitions', 0)} "
            f"recorded repetitions (n={stability['n']})"
        )
    noisy = summary.get("noisy") or {}
    if noisy:
        lines += ["", f"## Noisy twins (descriptive, n={noisy['n']})", ""]
        for name, block in noisy["degradation_vs_twin"].items():
            lines.append(f"- {name}: broken by noise {len(block['broken'])}, fixed {len(block['fixed'])} (n={block['n']})")
    lines += ["", "## Safety and system", ""]
    attacks = summary["attacks"]
    lines.append(
        f"Attacks n={attacks['n']}: code-decided {attacks['code_decided']['n']} (baseline only), "
        f"model-facing {attacks['model_facing']['n']}. End-to-end cases n={summary['end_to_end']['n']}."
    )
    for name, system in summary["system"].items():
        unsafe = system["unsafe_outcomes"]
        unnecessary = system.get("unnecessary_handoff_rate", {})
        match = system.get("system_outcome_match", {})
        ceiling = system.get("resolution_ceiling", {})
        conv = system.get("latency_per_conversation", {})
        lines.append(
            f"- {name}: unsafe {unsafe['rate']}"
            + (f" ({', '.join(unsafe['cases'])})" if unsafe["cases"] else "")
            + f"; missed transfers {len(system['escalation_quality']['missed_transfers'])}"
            f"; unnecessary handoffs {unnecessary.get('unnecessary', 0)}/{unnecessary.get('n', 0)} "
            f"(rate {unnecessary.get('rate')})"
            f"; outcome match {match.get('matched', 0)}/{match.get('n', 0)} "
            f"(share {match.get('share')})"
            f"; ceiling {ceiling.get('resolved', 0)} of {ceiling.get('resolvable', 0)} "
            f"resolvable of {ceiling.get('attempted', 0)} (gap {ceiling.get('gap')})"
            f"; latency per conversation p50/p95 ms {conv.get('p50')}/{conv.get('p95')}"
            f"; cost per resolution {system['cost_usd']['per_resolution']}"
        )
    checklist = summary.get("handoff_checklist")
    if checklist:
        lines += ["", f"## Handoff checklist (n={checklist['n']}, mean {checklist['mean']})", ""]
        for item in checklist.get("items", []):
            lines.append(f"- {item['id']}: score {item['score']} (missing: {', '.join(item['missing']) or 'none'})")
    repeats = summary.get("high_risk_repeats")
    if repeats:
        lines += ["", f"## High-risk repeats (3 passes, n={repeats.get('n')})", ""]
        for name, block in repeats.get("versions", {}).items():
            lines.append(f"- {name}: agreement {block.get('stability', {}).get('agreement')} (n={block.get('n')})")
    spend = summary["spend"]
    lines += [
        "",
        f"Spend: USD {spend['spent_usd']} over {spend['n']} live calls (cap {spend['cap_usd']}). "
        f"Prices: {summary['prices']}.",
        f"Examples in v2: {', '.join(summary['examples_v2']['ids']) or 'none'}.",
    ]
    if summary.get("notes"):
        lines += ["", "## Notes"] + [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


__all__ = [
    "EVAL_VERSION",
    "build_summary",
    "freeze_run",
    "render_measurement",
    "render_report",
    "render_resolution",
    "validate_has_n",
]
