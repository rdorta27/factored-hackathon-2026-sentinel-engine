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


__all__ = ["EVAL_VERSION", "build_summary", "freeze_run", "render_report", "validate_has_n"]
