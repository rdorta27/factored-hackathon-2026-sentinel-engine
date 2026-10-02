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
     "count", "resolved", "passed", "automated", "contained", "total"}
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
        "notes": notes or [],
    }
    validate_has_n(summary)
    return summary


def render_report(summary: dict) -> str:
    lines = [
        f"# Evaluation run {summary['run_id']}",
        "",
        f"Eval {summary['eval_version']} · labels {summary['labels'].get('run_id')} "
        f"({summary['labels'].get('summary_sha16')}) · n={summary['n']}",
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
        f"Eval {summary['eval_version']} · seal {seal['hash'][:16]} · n={summary['n']} · "
        f"main block n={component['n']}, same case ids for every version.",
        "",
        "## Accuracy by version",
        "",
        "| Version | Accuracy | 95% interval | JSON failures | Cost USD (total) | Latency p50/p95 ms |",
        "|---|---|---|---|---|---|",
    ]
    for name, block in versions.items():
        overall = block["breakdown"]["overall"]
        lines.append(
            f"| {name} | {overall['accuracy']} | {_interval(overall)} | "
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
                f"- {variant}: accuracy {stats['accuracy']} {_interval(stats)} (n={stats['n']}); "
                f"net loss {loss.get('net_loss')} of {loss.get('n')} shared bases; lost: {lost}"
            )
    lines += ["", "## By intent", ""]
    for name, block in versions.items():
        parts = [
            f"{intent} {stats['accuracy']} {_interval(stats)} (n={stats['n']})"
            for intent, stats in block["breakdown"]["by_intent"].items()
        ]
        lines.append(f"- {name}: " + "; ".join(parts))
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
        lines.append(
            f"- {name}: unsafe {unsafe['rate']}"
            + (f" ({', '.join(unsafe['cases'])})" if unsafe["cases"] else "")
            + f"; missed transfers {len(system['escalation_quality']['missed_transfers'])}"
            f"; cost per resolution {system['cost_usd']['per_resolution']}"
        )
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


__all__ = ["EVAL_VERSION", "build_summary", "freeze_run", "render_measurement", "render_report", "validate_has_n"]
