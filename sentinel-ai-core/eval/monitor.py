"""Country monitoring over the turn log: aggregates only, frozen write-once.

Usage from ``sentinel-ai-core/``::

    python3 -m eval.monitor <turns.jsonl> <run-id> [--simulated]

Reads step records (one JSON object per line, as written by
``app.observability.writer.Recorder`` to ``var/turns.jsonl``) and freezes
per-country, per-language aggregates under
``evidence/monitoring/<run-id>/summary.json``. The output holds counts,
percentiles and money only: no trace id, session reference or text ever
leaves the log. A replayed workload is labelled simulated with
``--simulated``. An existing run id is refused, never overwritten.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from eval.metrics import percentile
from eval.report import validate_has_n

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent

KNOWN_COUNTRIES = ("MX", "CO", "AR")
FAILED_OUTCOMES = ("failed", "timeout")


def _group_key(record: dict) -> tuple[str, str]:
    country = record.get("country")
    country = country if country in KNOWN_COUNTRIES else "other"
    language = record.get("language") or "unknown"
    return str(country), str(language)


def summarize(records: list[dict], *, source: str, simulated: bool) -> dict:
    """Aggregate step records per country and language.

    ``records`` are raw JSON objects, so a log line from outside the current
    validation (for example an unknown country) is reported apart instead of
    rejected. Trace ids are used only to join a fallback answer to its turn
    and never appear in the output.
    """
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for record in records:
        if not isinstance(record, dict):
            continue
        buckets[_group_key(record)].append(record)
    turn_closes = [r for r in records if isinstance(r, dict) and r.get("step") == "turn"]
    stamps = sorted(
        str(r.get("ts")) for r in records if isinstance(r, dict) and r.get("ts")
    )
    groups: dict[str, dict] = {}
    for (country, language), rows in sorted(buckets.items()):
        closes = [r for r in rows if r.get("step") == "turn"]
        latencies = [float(r.get("latency_ms", 0.0) or 0.0) for r in closes]
        failed = [r for r in rows if r.get("outcome") in FAILED_OUTCOMES]
        fallback_traces = {
            str(r.get("trace_id"))
            for r in rows
            if r.get("step") == "understand" and r.get("route") == "fallback"
        }
        groups.setdefault(country, {})[language] = {
            "n": len(closes),
            "turn_latency_ms": {
                "n": len(closes),
                "p50": percentile(latencies, 50),
                "p95": percentile(latencies, 95),
            },
            "failed_or_timed_out_steps": {"n": len(failed)},
            "escalations": {"n": sum(1 for r in rows if r.get("step") == "escalate")},
            "handoffs": {"n": sum(1 for r in closes if r.get("handoff"))},
            "fallback_turns": {"n": len(fallback_traces)},
            "cost_usd": {
                "n": len(rows),
                "total": round(
                    sum(float(r.get("cost_usd", 0.0) or 0.0) for r in rows), 6
                ),
            },
        }
    summary = {
        "workload": {
            "n": len(turn_closes),
            "source": source,
            "records": len(records),
            "turns": len(turn_closes),
            "period": {
                "first": stamps[0] if stamps else None,
                "last": stamps[-1] if stamps else None,
            },
            "simulated": simulated,
        },
        "groups": groups,
        "notes": [
            "Aggregates only: no trace id, session reference or text.",
            "A country outside MX, CO and AR is reported apart under other.",
            "Understand records carry the session language before detection, "
            "so model cost lands under the pre-detection language group.",
        ]
        + (
            ["Replayed workload, labelled simulated: not field behaviour."]
            if simulated
            else []
        ),
    }
    validate_has_n(summary)
    return summary


def render_report(summary: dict) -> str:
    workload = summary["workload"]
    lines = [
        f"# Country monitoring {workload['source']}",
        "",
        f"Workload: {workload['turns']} turns in {workload['records']} records, "
        f"{workload['period']['first']} to {workload['period']['last']} "
        f"({'simulated' if workload['simulated'] else 'field'}).",
        "",
        "| Country | Language | Turns | Latency p50/p95 ms | Failed/timed-out steps | "
        "Escalations | Handoffs | Fallback turns | Cost USD |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for country, languages in summary["groups"].items():
        for language, block in languages.items():
            latency = block["turn_latency_ms"]
            lines.append(
                f"| {country} | {language} | {block['n']} | "
                f"{latency['p50']}/{latency['p95']} | "
                f"{block['failed_or_timed_out_steps']['n']} | "
                f"{block['escalations']['n']} | {block['handoffs']['n']} | "
                f"{block['fallback_turns']['n']} | {block['cost_usd']['total']} |"
            )
    lines += ["", "## Notes"] + [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


def freeze_monitoring(repo_root: Path | str, run_id: str, summary: dict, report_md: str) -> Path:
    folder = Path(repo_root) / "evidence" / "monitoring" / run_id
    if folder.exists():
        raise SystemExit(f"refusing to overwrite committed run {folder}; use a new run id")
    folder.mkdir(parents=True)
    (folder / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (folder / "report.md").write_text(report_md, encoding="utf-8")
    return folder


def monitor(
    log_path: Path | str,
    run_id: str,
    *,
    simulated: bool = False,
    freeze: bool = True,
) -> dict:
    path = Path(log_path)
    records = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    summary = summarize(records, source=str(path), simulated=simulated)
    if freeze:
        freeze_monitoring(REPO_ROOT, run_id, summary, render_report(summary))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Aggregate the turn log per country and language.")
    parser.add_argument("log", help="turn log as JSON lines (e.g. var/turns.jsonl)")
    parser.add_argument("run_id", help="monitoring run id, frozen write-once")
    parser.add_argument(
        "--simulated",
        action="store_true",
        help="label a replayed workload as simulated",
    )
    args = parser.parse_args(argv)
    summary = monitor(args.log, args.run_id, simulated=args.simulated)
    workload = summary["workload"]
    print(f"[monitor] froze {args.run_id}: {workload['turns']} turns, {workload['records']} records")


if __name__ == "__main__":
    main()


__all__ = ["freeze_monitoring", "main", "monitor", "render_report", "summarize"]
