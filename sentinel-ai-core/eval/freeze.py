"""Freeze one offline evaluation run: bench + system replay + report.

Usage from ``sentinel-ai-core/``::

    python3 -m eval.freeze 2024Q4-eval-v1

Runs the fixture-backed router and the keyword baseline over the identical
case set, replays every case through POST /chat, and freezes ``summary.json``
plus ``report.md`` write-once under ``evidence/evaluation-runs/<run-id>/``.
No connection is opened: the only model transport is ``FixtureTransport``.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from eval import metrics
from eval.bench_router import run_bench
from eval.cases import check_splits, load_dir, load_labels
from eval.report import build_summary, freeze_run, render_report
from eval.runner import run_system

HERE = Path(__file__).parent
CASES_DIR = HERE / "cases"
FIXTURES_DIR = HERE.parent / "app" / "ai" / "fixtures"
LABELS_PATH = HERE / "labels.json"


def case_mix(cases: list) -> dict:  # type: ignore[no-untyped-def]
    mix = {
        "n": len(cases),
        "by_locale": dict(sorted(Counter(c.locale for c in cases).items())),
        "by_country": dict(sorted(Counter(c.country for c in cases).items())),
        "by_intent": dict(sorted(Counter(c.expected_intent for c in cases).items())),
        "by_split": dict(sorted(Counter(c.split for c in cases).items())),
    }
    return mix


def main(run_id: str) -> Path:
    cases = load_dir(CASES_DIR)
    check_splits(cases)
    provenance = load_labels(LABELS_PATH)
    measurable = [c for c in cases if c.fault == "none"]
    comparison = run_bench(measurable, repetitions=3, fixtures_dir=FIXTURES_DIR)
    turns = run_system(cases, FIXTURES_DIR)
    system = metrics.system_metrics(turns)
    safety = metrics.safety_pass_rate(turns)
    automation = metrics.automation_proxy(turns)
    failures = [
        {"id": t["id"], "reason": f"expected {t['expected_outcome']}, got {t['outcome']}"}
        for t in turns
        if not t["matched"]
    ]
    failures += [
        {"id": t["id"], "reason": "must-not-pass case opened a case"}
        for t in turns
        if t["must_not_pass"] and t["outcome"] == "case_confirmation"
    ]
    summary = build_summary(
        run_id=run_id,
        comparison=comparison,
        turns=turns,
        system=system,
        labels={
            "n": len(provenance.claim_labels),
            "run_id": provenance.run_id,
            "summary_sha16": provenance.summary_sha16,
        },
        case_mix=case_mix(cases),
        failures=failures,
        safety=safety,
        automation=automation,
        notes=[
            "Team-written simulation cases, never dataset rows (decision 007).",
            "Router served by baseline-mirrored fixtures (no live model configured); "
            "router-vs-baseline delta is zero by construction.",
            "Small-sample limits apply per locale and class; held_out measured once in this run.",
        ],
    )
    repo_root = HERE.parent.parent
    return freeze_run(repo_root, run_id, summary, render_report(summary))


if __name__ == "__main__":
    run_id = sys.argv[1] if len(sys.argv) > 1 else "2024Q4-eval-v1"
    folder = main(run_id)
    print(f"[freeze] wrote {folder}/summary.json")
