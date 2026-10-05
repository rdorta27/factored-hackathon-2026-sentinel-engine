#!/usr/bin/env python3
"""Write site/numbers.json from the frozen summary.json runs.

Every number on the site comes from here. Each entry keeps its source run,
its field path, its denominator and its data type (what-is-real labels).

    python3 scripts/site_numbers.py          # write site/numbers.json
    python3 scripts/site_numbers.py --check  # exit 1 if the file is stale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
OUT = ROOT / "site" / "numbers.json"

ADV = "adversarial/20261005T014816Z"
EVAL = "evaluation-runs/2024Q4-eval-v7"
RES = "evaluation-runs/2024Q4-resolution-v2"
PROBLEM = "problem/dev-v1"
GAP = "evaluation-runs/2024Q4-resolution-gap-v1"

# id -> (run, field path, format, type label, denominator path or None, text)
# Formats: int, pct (0..1 to percent), pct_raw (already percent), str, float2.
METRICS: dict[str, tuple] = {
    "adv_attempted": (ADV, "totals.attempted", "int", "Test suite", None,
                      "attacks tried"),
    "adv_rate": (ADV, "totals.unsafe_outcome_rate", "str", "Test suite", None,
                 "attacks with an unsafe outcome"),
    "adv_blocked": (ADV, "totals.blocked_verified", "int", "Test suite",
                    "totals.attempted", "blocked by production code"),
    "adv_mock": (ADV, "totals.passes_on_mock", "int", "Test suite",
                 "totals.attempted", "safe only with the mock model"),
    "intent_baseline": (EVAL, "component.versions.baseline.breakdown.overall.accuracy",
                        "pct", "Simulation",
                        "component.versions.baseline.breakdown.overall.n",
                        "intent accuracy of the keyword baseline"),
    "intent_router": (EVAL, "component.versions.router_v2.breakdown.overall.accuracy",
                      "pct", "Simulation",
                      "component.versions.router_v2.breakdown.overall.n",
                      "intent accuracy of the LLM router"),
    "intent_n": (EVAL, "component.n", "int", "Simulation", None,
                 "held-out turns in the intent test"),
    "res_resolved": (RES, "system.router_v2.safe_resolution.resolved", "int",
                     "Simulation", "system.router_v2.safe_resolution.n",
                     "cases resolved safely"),
    "res_n": (RES, "system.router_v2.safe_resolution.n", "int", "Simulation",
              None, "resolution cases"),
    "res_unsafe": (RES, "system.router_v2.unsafe_outcomes.rate", "str",
                   "Simulation", None, "unsafe outcomes in the resolution run"),
    "res_net": (RES, "paired_resolution.net", "int", "Simulation",
                "paired_resolution.n",
                "net cases gained by the router over the baseline"),
    "ceil_resolvable": (GAP, "ceiling.router_v2.resolvable", "int", "Simulation",
                        "ceiling.router_v2.n", "cases that the policy lets the system resolve"),
    "ceil_resolved": (GAP, "ceiling.router_v2.resolved", "int", "Simulation",
                      "ceiling.router_v2.resolvable", "of the resolvable cases resolved"),
    "problem_calls": (PROBLEM, "totals.calls", "int", "Synthetic", None,
                      "calls in the development window"),
    "problem_dispute_calls": (PROBLEM, "demand.transaction_dispute.calls", "int",
                              "Synthetic", "totals.calls",
                              "calls about a transaction dispute"),
    "problem_dispute_hours": (PROBLEM, "hours.transaction_dispute.hours_per_month",
                              "float1", "Synthetic", None,
                              "agent hours per month on disputes"),
    "problem_dispute_resolved": (PROBLEM, "reasons.Queja.share_pct", "pct_raw",
                                 "Synthetic", "reasons.Queja.n",
                                 "of dispute calls end resolved"),
}


# Series for the evidence explorer. Each row reads one field of a frozen run.
# kind: rate (0..1 with n), count (value of denominator) or scale (value with unit).
SERIES: list[dict] = [
    {
        "id": "intent", "title": "Intent accuracy", "type": "Simulation", "run": EVAL, "kind": "rate",
        "about": "The intent router against the keyword baseline on the same sealed held-out turns. The cases are team-written, not production traffic.",
        "rows": [
            ("Keyword baseline", "component.versions.baseline.breakdown.overall.accuracy", "component.versions.baseline.breakdown.overall.n"),
            ("LLM router, first version", "component.versions.router_v1.breakdown.overall.accuracy", "component.versions.router_v1.breakdown.overall.n"),
            ("LLM router, final version", "component.versions.router_v2.breakdown.overall.accuracy", "component.versions.router_v2.breakdown.overall.n"),
        ],
    },
    {
        "id": "resolution", "title": "Resolution ceiling", "type": "Simulation", "run": GAP, "kind": "count",
        "about": "The policy sets a ceiling on how many simulated cases may resolve. Both systems resolve every case under the ceiling, so the two systems do not differ. The set cannot separate the two systems on resolution.",
        "rows": [
            ("Cases the policy lets resolve", "ceiling.router_v2.resolvable", "ceiling.router_v2.n"),
            ("Resolved by the baseline", "ceiling.baseline.resolved", "ceiling.baseline.n"),
            ("Resolved by the LLM router", "ceiling.router_v2.resolved", "ceiling.router_v2.n"),
        ],
    },
    {
        "id": "attacks", "title": "Attacks", "type": "Test suite", "run": ADV, "kind": "count",
        "about": "Each bar shows the attacks that production code stops. The other attacks pass only with the mock model, or are documented limits. No attack has an unsafe outcome.",
        "rows": [
            ("Prompt injection", "categories.A_prompt_injection.blocked_verified", "categories.A_prompt_injection.attempted"),
            ("Unauthorized access", "categories.B_unauthorized_access.blocked_verified", "categories.B_unauthorized_access.attempted"),
            ("Session", "categories.C_session.blocked_verified", "categories.C_session.attempted"),
            ("Tool failures", "categories.D_tool_failures.blocked_verified", "categories.D_tool_failures.attempted"),
            ("Multilingual ambiguity", "categories.E_multilingual_ambiguity.blocked_verified", "categories.E_multilingual_ambiguity.attempted"),
            ("Decision disclosure", "categories.F_decision_disclosure.blocked_verified", "categories.F_decision_disclosure.attempted"),
            ("All attacks", "totals.blocked_verified", "totals.attempted"),
        ],
        "extra": [("Unsafe outcomes, all attacks", "totals.unsafe_outcome_rate")],
    },
    {
        "id": "latency", "title": "Latency", "type": "Simulation", "run": EVAL, "kind": "scale", "unit": "ms",
        "mode": "Live model calls on simulation cases",
        "about": "Time of one routed turn with the LLM router, in milliseconds. The calls are live. The cases are team-written.",
        "rows": [
            ("Median (p50)", "component.versions.router_v2.latency_ms.p50", "component.versions.router_v2.latency_ms.n"),
            ("Slow turn (p95)", "component.versions.router_v2.latency_ms.p95", "component.versions.router_v2.latency_ms.n"),
        ],
    },
    {
        "id": "replay", "title": "Latency of a replay", "type": "Simulation", "run": RES, "kind": "scale", "unit": "ms",
        "mode": "Replay of recorded model answers, no live call",
        "about": "The resolution run replays recorded answers. It measures the code, not the model. Do not compare it with the live latency.",
        "rows": [
            ("Median (p50)", "system.router_v2.latency_ms.p50", "system.router_v2.latency_ms.n"),
            ("Slow turn (p95)", "system.router_v2.latency_ms.p95", "system.router_v2.latency_ms.n"),
        ],
    },
    {
        "id": "cost", "title": "Cost", "type": "Simulation", "run": EVAL, "kind": "scale", "unit": "USD",
        "mode": "Live model calls on simulation cases",
        "about": "Total price of the live calls of each router on the same turns. The prices come from the Fireworks model library, as the router models decision records.",
        "rows": [
            ("LLM router, first version", "component.versions.router_v1.cost_usd.total", "component.versions.router_v1.cost_usd.n"),
            ("LLM router, final version", "component.versions.router_v2.cost_usd.total", "component.versions.router_v2.cost_usd.n"),
        ],
    },
]


def build_series(runs_cache: dict, evidence: Path) -> list[dict]:
    out = []
    for sdef in SERIES:
        run = sdef["run"]
        if run not in runs_cache:
            runs_cache[run] = json.loads((evidence / run / "summary.json").read_text())
        data = runs_cache[run]
        rows = []
        for label, vpath, dpath in sdef["rows"]:
            rows.append({"label": label, "value": dig(data, vpath), "n": dig(data, dpath), "field": vpath, "n_field": dpath})
        entry = {k: sdef[k] for k in ("id", "title", "type", "kind", "about") if k in sdef}
        entry.update({"source": f"evidence/{run}/summary.json", "rows": rows})
        for k in ("unit", "mode"):
            if k in sdef:
                entry[k] = sdef[k]
        if "extra" in sdef:
            entry["extra"] = [{"label": lb, "value": dig(data, pth), "field": pth} for lb, pth in sdef["extra"]]
        out.append(entry)
    return out


def dig(obj, path: str):
    for part in path.split("."):
        obj = obj[part]
    return obj


def fmt(value, kind: str) -> str:
    if kind == "int":
        return f"{int(value):,}"
    if kind == "pct":
        return f"{value * 100:.1f}%"
    if kind == "pct_raw":
        return f"{value:.1f}%"
    if kind == "float1":
        return f"{value:,.1f}"
    return str(value)


def build(evidence: Path = EVIDENCE) -> dict:
    runs: dict[str, dict] = {}
    numbers: dict[str, dict] = {}
    for key, (run, path, kind, label, denom, text) in METRICS.items():
        if run not in runs:
            runs[run] = json.loads((evidence / run / "summary.json").read_text())
        value = dig(runs[run], path)
        entry = {
            "text": fmt(value, kind),
            "value": value,
            "type": label,
            "label": text,
            "source": f"evidence/{run}/summary.json",
            "field": path,
        }
        if denom:
            entry["denominator"] = dig(runs[run], denom)
            entry["denominator_field"] = denom
        numbers[key] = entry
    return {
        "note": "Generated by scripts/site_numbers.py from frozen summary.json runs. Do not edit.",
        "numbers": numbers,
        "series": build_series(runs, evidence),
    }


def render(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


# <span data-num="id">, data-num-type="id" and data-num-den="id" hold no
# nested tags. The script writes their text from numbers.json.
SLOT = re.compile(
    r'(<(\w+)[^>]*?\bdata-(num|num-type|num-den)="(\w+)"[^>]*>)(.*?)(</\2>)',
    re.S,
)


# Markdown pages use <!--n:key-->text<!--/n--> (invisible when rendered).
MD_SLOT = re.compile(r"(<!--n:(\w+)-->)(.*?)(<!--/n-->)", re.S)
MD_FILES = [ROOT / "docs" / "build" / "video-script.md"]


def sync_markdown(numbers: dict, check: bool = False) -> list[Path]:
    changed = []
    for page in MD_FILES:
        if not page.exists():
            continue
        old = page.read_text()
        new = MD_SLOT.sub(lambda m: m.group(1) + numbers[m.group(2)]["text"] + m.group(4), old)
        if new != old:
            changed.append(page)
            if not check:
                page.write_text(new)
    return changed


def slot_text(numbers: dict, kind: str, key: str) -> str:
    entry = numbers[key]
    if kind == "num":
        return entry["text"]
    if kind == "num-type":
        return entry["type"]
    return f"{int(entry['denominator']):,}"


def sync_pages(data: dict, site: Path = OUT.parent) -> list[Path]:
    """Rewrite the text of each number slot. Return the pages that changed."""
    changed = []
    for page in sorted(site.rglob("*.html")):
        old = page.read_text()
        new = SLOT.sub(
            lambda m: m.group(1) + slot_text(data["numbers"], m.group(3), m.group(4)) + m.group(6),
            old,
        )
        if new != old:
            page.write_text(new)
            changed.append(page)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = build()
    text = render(data)
    if args.check:
        stale = not OUT.exists() or OUT.read_text() != text
        for page in OUT.parent.rglob("*.html"):
            if SLOT.sub(lambda m: m.group(1) + slot_text(data["numbers"], m.group(3), m.group(4)) + m.group(6),
                        page.read_text()) != page.read_text():
                print(f"stale number in {page.relative_to(ROOT)}")
                stale = True
        for page in sync_markdown(data["numbers"], check=True):
            print(f"stale number in {page.relative_to(ROOT)}")
            stale = True
        if stale:
            print("The site is stale. Run scripts/site_numbers.py.")
            return 1
        print("The site numbers are current.")
        return 0
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(text)
    pages = sync_pages(data) + sync_markdown(data["numbers"])
    print(f"wrote {OUT.relative_to(ROOT)} ({len(METRICS)} numbers), updated {len(pages)} page(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
