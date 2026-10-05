"""Why the paired difference in safe resolution is 0 (evidence-hardening task 1.1).

Usage from ``sentinel-ai-core/`` (load ``.env`` first, see README)::

    python3 -m eval.resolution_gap 2024Q4-resolution-gap-v1

Replays the baseline and ``router_v2`` on the resolution set from the
committed recordings of ``2024Q4-resolution-v2``. It makes no live call.
Each case gets one label: both resolve, both fail, or different. The
summary reports the ceiling of safe resolution (cases that policy lets
resolve) and the cases where the two systems read a different intent, so
the cause of a 0 difference is stated from data.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from app.ai.demo import DemoModel
from app.ai.recording import RecordingTransport
from eval import metrics
from eval.cases import load_cases, load_dir
from eval.examples import PROMPT_VERSION_WITH_EXAMPLES, build_examples
from eval.report import EVAL_VERSION, freeze_run, validate_has_n
from eval.run import (
    CASES_DIR,
    EXAMPLES_PATH,
    REPO_ROOT,
    RESOLUTION_PATH,
    RESOLUTION_RECORDINGS_DIR,
    SIMULATION_NOTE,
    _head_commit,
    _resolved,
    _router,
)
from eval.runner import run_system

SOURCE_RUN = "2024Q4-resolution-v2"
BOTH_RESOLVE, BOTH_FAIL, DIFFERENT = "both_resolve", "both_fail", "different"
CAUSE_CEILING = "ceiling"
CAUSE_NO_SEPARATION = "set_cannot_separate"
CAUSE_SYSTEMS_DIFFER = "systems_differ"


def case_label(baseline_resolved: bool, router_resolved: bool) -> str:
    if baseline_resolved and router_resolved:
        return BOTH_RESOLVE
    if not baseline_resolved and not router_resolved:
        return BOTH_FAIL
    return DIFFERENT


def _cause(ceilings: dict, outcome_differs: int) -> str:
    """Ceiling when both systems resolve every resolvable case; otherwise the set or the systems."""
    if outcome_differs:
        return CAUSE_SYSTEMS_DIFFER
    if all(block["gap"] == 0 for block in ceilings.values()):
        return CAUSE_CEILING
    return CAUSE_NO_SEPARATION


def gap_summary(run_id: str, cases: list, baseline_turns: list[dict], router_turns: list[dict]) -> dict:
    """The per-case labels, the ceiling per system and the stated cause, from turns only."""
    if not (len(cases) == len(baseline_turns) == len(router_turns)):
        raise ValueError("the gap needs one turn per case for both systems")
    rows = []
    for case, b, r in zip(cases, baseline_turns, router_turns):
        rows.append({
            "id": case.id,
            "situation": case.base_id or case.id,
            "expected_outcome": case.expected_outcome,
            "may_resolve": not case.requires_handoff and not case.must_not_pass,
            "baseline_outcome": b.get("outcome"),
            "router_outcome": r.get("outcome"),
            "baseline_label": b.get("label"),
            "router_label": r.get("label"),
            "label": case_label(_resolved(b), _resolved(r)),
        })
    by_label = Counter(row["label"] for row in rows)
    ceilings = {
        "baseline": metrics.resolution_ceiling(baseline_turns),
        "router_v2": metrics.resolution_ceiling(router_turns),
    }
    outcome_differs = [row["id"] for row in rows if row["baseline_outcome"] != row["router_outcome"]]
    label_differs = [row["id"] for row in rows if row["baseline_label"] != row["router_label"]]
    expected = {c.id: c.expected_intent for c in cases}
    n = len(rows)
    summary = {
        "run_id": run_id,
        "kind": "resolution_gap",
        "eval_version": EVAL_VERSION,
        "source_run": SOURCE_RUN,
        "n": n,
        "labels": {
            "n": n,
            BOTH_RESOLVE: by_label.get(BOTH_RESOLVE, 0),
            BOTH_FAIL: by_label.get(BOTH_FAIL, 0),
            DIFFERENT: by_label.get(DIFFERENT, 0),
        },
        "ceiling": ceilings,
        "outcome_differs": {"n": n, "count": len(outcome_differs), "cases": sorted(outcome_differs)},
        "intent_differs": {"n": n, "count": len(label_differs), "cases": sorted(label_differs)},
        "intent_correct": {
            name: {"n": n, "correct": sum(1 for row in rows if row[f"{name}_label"] == expected[row["id"]])}
            for name in ("baseline", "router")
        },
        "expected_intent_mix": dict(sorted(Counter(c.expected_intent for c in cases).items())),
        "cause": _cause(ceilings, len(outcome_differs)),
        "cases": rows,
        "measured_commit": _head_commit(),
        "notes": [
            SIMULATION_NOTE,
            "Simulation over a mock store, replay of committed recordings: no live call (decision 022).",
            "Resolvable means no handoff is required and the case may pass; policy sets this, not the router.",
            "Cause ceiling: both systems resolve every resolvable case, so no system can resolve more on this set.",
        ],
    }
    validate_has_n(summary)
    return summary


def render(summary: dict) -> str:
    """Readable view; every number comes from ``summary``."""
    labels = summary["labels"]
    lines = [
        f"# Resolution gap {summary['run_id']}",
        "",
        f"Replay of {summary['source_run']} · simulation over a mock store · n={summary['n']} · "
        f"commit {summary['measured_commit'][:12]}.",
        "",
        "## Case labels",
        "",
        f"- both resolve: {labels[BOTH_RESOLVE]} of {labels['n']}",
        f"- both fail: {labels[BOTH_FAIL]} of {labels['n']}",
        f"- different: {labels[DIFFERENT]} of {labels['n']}",
        "",
        "## Ceiling of safe resolution",
        "",
        "| Version | Attempted | Resolvable | Resolved | Ceiling share | Achieved share | Gap |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, block in summary["ceiling"].items():
        lines.append(
            f"| {name} | {block['attempted']} | {block['resolvable']} | {block['resolved']} | "
            f"{block['ceiling_share']} | {block['achieved_share']} | {block['gap']} |"
        )
    intent = summary["intent_differs"]
    correct = summary["intent_correct"]
    lines += [
        "",
        "## Where the systems differ",
        "",
        f"- outcome differs: {summary['outcome_differs']['count']} of {summary['outcome_differs']['n']}",
        f"- intent label differs: {intent['count']} of {intent['n']}",
        f"- intent correct: baseline {correct['baseline']['correct']} of {correct['baseline']['n']}, "
        f"router {correct['router']['correct']} of {correct['router']['n']}",
        f"- expected intent mix: {summary['expected_intent_mix']}",
        "",
        f"## Cause: {summary['cause']}",
        "",
        "## Cases",
        "",
        "| Case | May resolve | Baseline | Router | Label |",
        "|---|---|---|---|---|",
    ]
    for row in summary["cases"]:
        lines.append(
            f"| {row['id']} | {row['may_resolve']} | {row['baseline_outcome']} ({row['baseline_label']}) | "
            f"{row['router_outcome']} ({row['router_label']}) | {row['label']} |"
        )
    lines += ["", "## Notes"] + [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


def run(
    run_id: str,
    freeze: bool = True,
    router_factory=None,  # type: ignore[no-untyped-def]
    recordings_dir: Path | str | None = None,
) -> dict:
    """Replay both systems offline and build the gap summary; ``router_factory`` is for tests."""
    cases = load_cases(RESOLUTION_PATH)
    rec_dir = Path(recordings_dir) if recordings_dir is not None else RESOLUTION_RECORDINGS_DIR
    if router_factory is None:
        examples = build_examples(
            load_dir(CASES_DIR), json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))["ids"]
        )
        rec = RecordingTransport(rec_dir, PROMPT_VERSION_WITH_EXAMPLES, None, record=False)
        router_factory = lambda: _router(rec, PROMPT_VERSION_WITH_EXAMPLES, examples)  # noqa: E731
    baseline_turns = run_system(cases, rec_dir, DemoModel)
    router_turns = run_system(cases, rec_dir, router_factory)
    summary = gap_summary(run_id, cases, baseline_turns, router_turns)
    if freeze:
        freeze_run(REPO_ROOT, run_id, summary, render(summary))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    args = parser.parse_args(argv)
    summary = run(args.run_id)
    print(f"[resolution_gap] froze {args.run_id}: {summary['labels']} cause={summary['cause']}")


if __name__ == "__main__":
    main()


__all__ = ["case_label", "gap_summary", "render", "run"]
