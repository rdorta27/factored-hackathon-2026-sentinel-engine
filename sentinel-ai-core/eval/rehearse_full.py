"""Full rehearsal and prompt ablation on development data (eval-v8 tasks 3.1, 3.2).

Usage from ``sentinel-ai-core/`` (load ``.env`` first)::

    python3 -m eval.rehearse_full rehearse 2024Q4-rehearsal-v8 [--cap 0.45]
    python3 -m eval.rehearse_full ablate 2024Q4-ablation-v8 [--cap 1.0]

Both read the development split only and refuse a held-out case. Both use
fresh recording directories per run, so every router call is a new live call
under one shared spend cap. ``rehearse`` runs every candidate (keyword
baseline, trained baseline, v2, v2 with cut-offs, v3, v3 with cut-offs)
through the v8 component metrics with three high-risk repeats, then freezes
the run. ``ablate`` runs prompt v3 with 0, 4, 8 and 32 examples on the same
cases and freezes one run with all four configs. Neither judges: the gates of
the 018 amendment decide on the sealed set only.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent
CASES_DIR = HERE / "cases"
EXAMPLES_V2_PATH = HERE / "examples_v2.json"
EXAMPLES_V3_PATH = HERE / "examples_v3.json"
sys.path.insert(0, str(HERE.parent))

from app.ai.demo import DemoModel  # noqa: E402
from app.ai.llm import SYSTEM_PROMPT_V3, Cutoffs, PromptedLLMRouter, RouterConfig  # noqa: E402
from app.ai.prices import PRICE_SOURCE, PRICES  # noqa: E402
from app.ai.recording import RecordingTransport  # noqa: E402
from app.ai.transport import HttpTransport  # noqa: E402
from eval.budget import CappedTransport, assert_freezable  # noqa: E402
from eval.cases import check_splits, load_dir  # noqa: E402
from eval.examples import build_examples, build_examples_v3  # noqa: E402
from eval.report import EVAL_VERSION, freeze_run, validate_has_n  # noqa: E402
from eval.trained import load_frozen as load_trained  # noqa: E402
from eval.versions import Version, run_version, run_versions, with_high_risk_repeats  # noqa: E402

SIMULATION_NOTE = "Team-written simulation cases, never dataset rows (decision 007)."

# Calibrated cut-offs (018 amendment): v2 from 2024Q4-calibration-v1, v3 from 2024Q4-calibration-v3.
CUTOFFS_V2 = Cutoffs(t_act=0.86, t_abstain=0.0, calibration_run="2024Q4-calibration-v1")
CUTOFFS_V3 = Cutoffs(t_act=1.0, t_abstain=0.0, calibration_run="2024Q4-calibration-v3")


class DevelopmentReadsHeldOut(ValueError):
    """A rehearsal run was given a held-out case."""


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _env() -> dict:
    base_url = os.environ.get("SENTINEL_LLM_BASE_URL", "")
    api_key = os.environ.get("SENTINEL_LLM_API_KEY", "")
    if not base_url or not api_key:
        raise SystemExit("live calls need SENTINEL_LLM_BASE_URL and SENTINEL_LLM_API_KEY in the environment")
    cheap = os.environ.get("SENTINEL_LLM_CHEAP_MODEL", "")
    strong = os.environ.get("SENTINEL_LLM_STRONG_MODEL", "")
    if not cheap or not strong:
        raise SystemExit("set SENTINEL_LLM_CHEAP_MODEL and SENTINEL_LLM_STRONG_MODEL to the models chosen in 016")
    return {
        "base_url": base_url,
        "api_key": api_key,
        "cheap": cheap,
        "strong": strong,
        "default": os.environ.get("SENTINEL_LLM_DEFAULT_MODEL", "") or cheap,
        "route_rule": os.environ.get("SENTINEL_LLM_ROUTE_RULE", "heuristic") or "heuristic",
        "max_tokens": int(os.environ.get("SENTINEL_LLM_MAX_TOKENS", "400") or 400),
    }


def _live(env: dict, cap_usd: float) -> CappedTransport:
    http = HttpTransport(
        base_url=env["base_url"],
        api_key=env["api_key"],
        timeout_s=float(os.environ.get("SENTINEL_LLM_TIMEOUT_S", "10") or 10),
        max_retries=int(os.environ.get("SENTINEL_LLM_MAX_RETRIES", "2") or 2),
        prices=PRICES,
        require_price=True,
        max_tokens=env["max_tokens"],
        reasoning_effort=os.environ.get("SENTINEL_LLM_REASONING_EFFORT", "low") or "low",
    )
    return CappedTransport(http, cap_usd=cap_usd)


def _dev_cases() -> list:
    loaded = load_dir(CASES_DIR)
    held = sorted(c.id for c in loaded if c.split == "held_out")
    if held:
        raise DevelopmentReadsHeldOut(f"rehearsal reads development only; held-out ids given: {held}")
    check_splits(loaded)
    return [c for c in loaded if c.split == "development"]


def _slim(block: dict) -> dict:
    """The v8 component fields a rehearsal reports (every number carries n)."""
    return {
        "n": block["n"],
        "intent": block["intent"],
        "breakdown_overall": block["breakdown"]["overall"],
        "subtype": block["subtype"],
        "slots": block["slots"],
        "drafts": block["drafts"],
        "unsafe_wording": block["unsafe_wording"],
        "json_failures": block["json_failures"],
        "stability": block["stability"],
        "latency_ms": block["latency_ms"],
        "cost_usd": block["cost_usd"],
        "prompt_version": block["prompt_version"],
        "example_ids": block["example_ids"],
    }


def rehearse(run_id: str, cap_usd: float = 0.45, freeze: bool = True) -> dict:
    started = time.perf_counter()
    cases = _dev_cases()
    env = _env()
    live = _live(env, cap_usd)
    rec_v2 = RecordingTransport(HERE / "recordings" / run_id / "v2", "v2", live, record=True, api_key=env["api_key"])
    rec_v3 = RecordingTransport(HERE / "recordings" / run_id / "v3", "v3", live, record=True, api_key=env["api_key"])
    development = load_dir(CASES_DIR)
    examples_v2 = build_examples(development, json.loads(EXAMPLES_V2_PATH.read_text(encoding="utf-8"))["ids"])
    spec = json.loads(EXAMPLES_V3_PATH.read_text(encoding="utf-8"))
    examples_v3 = build_examples_v3(development, spec["ids"], spec.get("drafts"))

    def _router(rec: RecordingTransport, prompt: str, examples=(), cutoffs=None, system_prompt=None) -> PromptedLLMRouter:
        config = RouterConfig(
            cheap_model=env["cheap"], strong_model=env["strong"], default_model=env["default"],
            prompt_version=prompt, examples=examples, route_rule=env["route_rule"], cutoffs=cutoffs,
        )
        if system_prompt is not None:
            config.system_prompt = system_prompt
        return PromptedLLMRouter(rec, config)

    versions = with_high_risk_repeats(
        {
            "baseline": Version(DemoModel()),
            "trained_baseline": Version(load_trained()),
            "router_v2": Version(_router(rec_v2, "v2", examples_v2)),
            "router_v2_cutoffs": Version(_router(rec_v2, "v2", examples_v2, CUTOFFS_V2)),
            "router_v3": Version(_router(rec_v3, "v3", examples_v3, None, SYSTEM_PROMPT_V3)),
            "router_v3_cutoffs": Version(_router(rec_v3, "v3", examples_v3, CUTOFFS_V3, SYSTEM_PROMPT_V3)),
        },
        cases,
    )
    component = run_versions(cases, versions)
    spend = live.report()
    summary = {
        "run_id": run_id,
        "kind": "rehearsal",
        "eval_version": EVAL_VERSION,
        "commit": _git_commit(),
        "n": len(cases),
        "split": "development",
        "candidates": {name: _slim(block) for name, block in component["versions"].items()},
        "paired": component["paired"],
        "cutoffs": {
            "v2": {"t_act": CUTOFFS_V2.t_act, "t_abstain": CUTOFFS_V2.t_abstain, "n": 0, "run": CUTOFFS_V2.calibration_run},
            "v3": {"t_act": CUTOFFS_V3.t_act, "t_abstain": CUTOFFS_V3.t_abstain, "n": 0, "run": CUTOFFS_V3.calibration_run},
        },
        "spend": spend,
        "prices": PRICE_SOURCE,
        "elapsed_s": round(time.perf_counter() - started, 1),
        "notes": [SIMULATION_NOTE, "Full rehearsal on development with every candidate, the v8 metrics and the spend cap. No sealed case read. Proves the pipeline; judges nothing."],
    }
    validate_has_n(summary)
    lines = [f"# Rehearsal {run_id} (development, every candidate)", "",
             f"Cases: {len(cases)} development. No sealed case read.", ""]
    for name, block in summary["candidates"].items():
        lines.append(
            f"- {name}: kind {block['intent']['accuracy']} (n={block['intent']['n']}); "
            f"subtype {block['subtype']['accuracy']}; slots {block['slots']['precision']}; "
            f"rejected {block['drafts']['rejected']}/{block['drafts']['returned']}; "
            f"unsafe wording {block['unsafe_wording']['rate']}; cost USD {block['cost_usd']['total']}."
        )
    lines += ["", f"Spend: USD {spend['spent_usd']} over {spend['n']} live calls (cap {spend['cap_usd']}). "
                  f"Time {summary['elapsed_s']} s."]
    if freeze:
        assert_freezable(spend)
        freeze_run(REPO_ROOT, run_id, summary, "\n".join(lines) + "\n")
    return summary


def ablate(run_id: str, cap_usd: float = 1.0, freeze: bool = True) -> dict:
    """Prompt ablation: v3 with 0, 4, 8 and 32 examples on the same dev cases."""
    started = time.perf_counter()
    cases = _dev_cases()
    env = _env()
    live = _live(env, cap_usd)
    development = load_dir(CASES_DIR)
    spec = json.loads(EXAMPLES_V3_PATH.read_text(encoding="utf-8"))
    full_ids = spec["ids"]
    configs = {"v3_no_examples": [], "v3_4_examples": full_ids[:4], "v3_8_examples": full_ids[:8], "v3_32_examples": full_ids}
    blocks = {}
    for name, ids in configs.items():
        rec = RecordingTransport(HERE / "recordings" / run_id / name, "v3", live, record=True, api_key=env["api_key"])
        examples = build_examples_v3(development, ids, spec.get("drafts")) if ids else ()
        config = RouterConfig(
            cheap_model=env["cheap"], strong_model=env["strong"], default_model=env["default"],
            prompt_version="v3", examples=examples, route_rule=env["route_rule"],
        )
        config.system_prompt = SYSTEM_PROMPT_V3
        block = run_version(cases, Version(PromptedLLMRouter(rec, config)))
        blocks[name] = {
            "n": block["n"],
            "example_ids": [e.case_id for e in examples],
            "kind_accuracy": block["intent"]["accuracy"],
            "by_intent": {label: stats["accuracy"] for label, stats in block["breakdown"]["by_intent"].items()},
            "subtype_accuracy": block["subtype"]["accuracy"],
            "slot_precision": block["slots"]["precision"],
            "rejected_drafts": block["drafts"]["rejected"],
            "drafts_returned": block["drafts"]["returned"],
            "unsafe_wording": block["unsafe_wording"],
            "cost_usd": block["cost_usd"],
            "latency_ms": block["latency_ms"],
        }
    spend = live.report()
    summary = {
        "run_id": run_id,
        "kind": "ablation",
        "eval_version": EVAL_VERSION,
        "commit": _git_commit(),
        "n": len(cases),
        "split": "development",
        "configs": blocks,
        "spend": spend,
        "prices": PRICE_SOURCE,
        "elapsed_s": round(time.perf_counter() - started, 1),
        "notes": [SIMULATION_NOTE, "Prompt ablation on the same development cases: the ablation picks nothing; the gates of the 018 amendment decide on the sealed set."],
    }
    validate_has_n(summary)
    lines = [f"# Ablation {run_id} (prompt v3 examples on development)", "",
             f"Cases: {len(cases)} development, same cases for every config. No sealed case read.", ""]
    for name, block in blocks.items():
        lines.append(
            f"- {name} ({len(block['example_ids'])} examples): kind {block['kind_accuracy']}; "
            f"subtype {block['subtype_accuracy']}; cost USD {block['cost_usd']['total']} "
            f"(n={block['cost_usd']['n']}); latency p50/p95 ms {block['latency_ms']['p50']}/{block['latency_ms']['p95']}."
        )
    lines += ["", f"Spend: USD {spend['spent_usd']} over {spend['n']} live calls (cap {spend['cap_usd']}). "
                  f"Time {summary['elapsed_s']} s."]
    if freeze:
        assert_freezable(spend)
        freeze_run(REPO_ROOT, run_id, summary, "\n".join(lines) + "\n")
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Full rehearsal and prompt ablation on development.")
    parser.add_argument("command", choices=("rehearse", "ablate"))
    parser.add_argument("run_id")
    parser.add_argument("--cap", type=float, default=None, help="spend cap in USD (rehearse 0.45, ablate 1.0)")
    args = parser.parse_args(argv)
    if args.command == "rehearse":
        summary = rehearse(args.run_id, cap_usd=args.cap or 0.45)
        print(f"[rehearse] {summary['n']} cases, spend USD {summary['spend']['spent_usd']}, {summary['elapsed_s']} s")
    else:
        summary = ablate(args.run_id, cap_usd=args.cap or 1.0)
        print(f"[ablate] {summary['n']} cases x4 configs, spend USD {summary['spend']['spent_usd']}, {summary['elapsed_s']} s")


if __name__ == "__main__":
    main()
