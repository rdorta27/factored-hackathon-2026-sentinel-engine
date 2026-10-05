"""Offline rehearsal for eval-v8 on development data only (task 3.1, partial).

Reads the development split only and refuses a held-out case. Runs the
available offline candidates (keyword baseline plus the fixture-backed v1
and v2 routers) through the v8 component metrics with three high-risk
repeats, and the system metrics over a fixture replay. Makes no live call,
reads no sealed case, spends USD 0. Trained baseline, live v3 and cut-off
variants wait for their merges and keys; the full rehearsal repeats this
with every candidate before the freeze.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.demo import DemoModel  # noqa: E402
from eval import metrics  # noqa: E402
from eval.bench_router import default_router  # noqa: E402
from eval.cases import check_splits, load_dir  # noqa: E402
from eval.report import validate_has_n  # noqa: E402
from eval.runner import run_system  # noqa: E402
from eval.versions import Version, run_versions, with_high_risk_repeats  # noqa: E402

HERE = Path(__file__).parent
CASES_DIR = HERE / "cases"
FIXTURES_DIR = HERE.parent / "app" / "ai" / "fixtures"


def rehearse() -> dict:
    started = time.perf_counter()
    loaded = load_dir(CASES_DIR)
    held = sorted(c.id for c in loaded if c.split == "held_out")
    if held:
        raise SystemExit(f"rehearsal reads development only; held-out ids given: {held}")
    check_splits(loaded)
    cases = [c for c in loaded if c.split == "development"]
    versions = with_high_risk_repeats(
        {
            "baseline": Version(DemoModel()),
            "router_v1": Version(default_router(str(FIXTURES_DIR), "v1")),
            "router_v2": Version(default_router(str(FIXTURES_DIR), "v2")),
        },
        cases,
    )
    # Fixture routers carry no recorded repetitions; repeats collapse to one pass.
    component = run_versions(cases, versions)
    sample = [c for c in cases if c.fault == "none"][:40]
    turns = run_system(sample, str(FIXTURES_DIR), DemoModel)
    system = metrics.system_metrics(turns)
    summary = {
        "run_id": "rehearsal-v8-offline",
        "n": len(cases),
        "component": {
            name: {
                "n": block["n"],
                "intent": block["intent"],
                "subtype": block["subtype"],
                "slots": block["slots"],
                "drafts": block["drafts"],
                "unsafe_wording": block["unsafe_wording"],
                "stability": block["stability"],
            }
            for name, block in component["versions"].items()
        },
        "system_sample": {
            "n": system["n"],
            "unnecessary_handoff_rate": system["unnecessary_handoff_rate"],
            "system_outcome_match": system["system_outcome_match"],
            "resolution_ceiling": system["resolution_ceiling"],
            "latency_per_conversation": system["latency_per_conversation"],
        },
        "spend": {"n": 0, "cap_usd": 0.45, "spent_usd": 0.0, "capped": False},
        "elapsed_s": round(time.perf_counter() - started, 1),
    }
    validate_has_n(summary)
    return summary


def render_note(summary: dict) -> str:
    lines = [
        "---",
        "language: en",
        "style: ASD-STE100",
        "last_reviewed: 2026-10-05",
        "---",
        "",
        "# Rehearsal v8 (offline, development only)",
        "",
        f"- Cases: {summary['n']} development. No sealed case read. No live call.",
        f"- Spend: USD {summary['spend']['spent_usd']} over {summary['spend']['n']} live calls "
        f"(cap {summary['spend']['cap_usd']}). Time {summary['elapsed_s']} s.",
        "",
        "## Component (offline fixtures)",
        "",
    ]
    for name, block in summary["component"].items():
        lines.append(
            f"- {name}: kind {block['intent']['accuracy']} (n={block['intent']['n']}); "
            f"subtype {block['subtype']['accuracy']} ({block['subtype']['correct']}/{block['subtype']['n']}); "
            f"slots {block['slots']['precision']} ({block['slots']['correct']}/{block['slots']['returned']}); "
            f"rejected {block['drafts']['rejected']}/{block['drafts']['returned']}; "
            f"unsafe wording {block['unsafe_wording']['rate']}."
        )
    sample = summary["system_sample"]
    ceiling = sample["resolution_ceiling"]
    conv = sample["latency_per_conversation"]
    lines += [
        "",
        "## System sample (baseline fixture replay, 40 cases)",
        "",
        f"- Unnecessary handoffs: {sample['unnecessary_handoff_rate']['unnecessary']}/"
        f"{sample['unnecessary_handoff_rate']['n']}.",
        f"- Outcome match: {sample['system_outcome_match']['matched']}/{sample['system_outcome_match']['n']}.",
        f"- Ceiling: {ceiling['resolved']} of {ceiling['resolvable']} resolvable "
        f"of {ceiling['attempted']} (gap {ceiling['gap']}).",
        f"- Latency per conversation p50/p95 ms: {conv['p50']}/{conv['p95']}.",
        "",
        "## Limits",
        "",
        "- Offline fixtures only: trained baseline, live v3 and cut-off variants are missing.",
        "- Fixture scores check the pipeline only. They do not rank the models.",
        "- The full rehearsal runs every candidate with the spend cap before the freeze.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    summary = rehearse()
    out = HERE / "review" / "rehearsal-v8.md"
    out.write_text(render_note(summary), encoding="utf-8")
    print(f"[rehearse] {summary['n']} dev cases, USD 0.0, {summary['elapsed_s']} s -> {out}")


if __name__ == "__main__":
    main()
