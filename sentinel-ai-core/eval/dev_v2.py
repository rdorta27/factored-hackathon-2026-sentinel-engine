"""Development numbers for baseline and router_v2 (eval-v8 task 1.1).

Usage from ``sentinel-ai-core/`` (load ``.env`` first)::

    python3 -m eval.dev_v2 2024Q4-dev-v8-v2 [--cap 1.0]

Reads the development split only and refuses a held-out case. The baseline
is free. Router_v2 (prompt v2 with the development examples, routed
cheap/strong per the environment) records into a fresh directory per run,
so every router call is a new live call under the spend cap (default
USD 1). The run freezes under ``evidence/evaluation-runs/<run-id>/``.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent
CASES_DIR = HERE / "cases"
EXAMPLES_V2_PATH = HERE / "examples_v2.json"
sys.path.insert(0, str(HERE.parent))

from app.ai.demo import DemoModel  # noqa: E402
from app.ai.drafts import DraftFacts, validate_draft  # noqa: E402
from app.ai.llm import PromptedLLMRouter, RouterConfig  # noqa: E402
from app.ai.prices import PRICE_SOURCE, PRICES  # noqa: E402
from app.ai.recording import RecordingTransport  # noqa: E402
from app.ai.transport import HttpTransport, InvalidReply, ModelUnavailable  # noqa: E402
from eval.budget import DEFAULT_CAP_USD, CappedTransport, assert_freezable  # noqa: E402
from eval.cases import check_splits, load_dir  # noqa: E402
from eval.examples import build_examples  # noqa: E402
from eval.paired import paired  # noqa: E402
from eval.report import EVAL_VERSION, freeze_run, validate_has_n  # noqa: E402
from eval.select_v3 import _slot_match  # noqa: E402

SIMULATION_NOTE = "Team-written simulation cases, never dataset rows (decision 007)."


class DevelopmentReadsHeldOut(ValueError):
    """A development run was given a held-out case."""


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def dev_numbers(run_id: str, cap_usd: float = 1.0, freeze: bool = True) -> dict:
    loaded = load_dir(CASES_DIR)
    held = sorted(c.id for c in loaded if c.split == "held_out")
    if held:
        raise DevelopmentReadsHeldOut(f"development reads development only; held-out ids given: {held}")
    check_splits(loaded)
    cases = [c for c in loaded if c.split == "development"]
    examples = build_examples(loaded, json.loads(EXAMPLES_V2_PATH.read_text(encoding="utf-8"))["ids"])

    base_url = os.environ.get("SENTINEL_LLM_BASE_URL", "")
    api_key = os.environ.get("SENTINEL_LLM_API_KEY", "")
    if not base_url or not api_key:
        raise SystemExit("live calls need SENTINEL_LLM_BASE_URL and SENTINEL_LLM_API_KEY in the environment")
    cheap = os.environ.get("SENTINEL_LLM_CHEAP_MODEL", "")
    strong = os.environ.get("SENTINEL_LLM_STRONG_MODEL", "")
    if not cheap or not strong:
        raise SystemExit("set SENTINEL_LLM_CHEAP_MODEL and SENTINEL_LLM_STRONG_MODEL to the models chosen in 016")
    max_tokens = int(os.environ.get("SENTINEL_LLM_MAX_TOKENS", "400") or 400)
    http = HttpTransport(
        base_url=base_url,
        api_key=api_key,
        timeout_s=float(os.environ.get("SENTINEL_LLM_TIMEOUT_S", "10") or 10),
        max_retries=int(os.environ.get("SENTINEL_LLM_MAX_RETRIES", "2") or 2),
        prices=PRICES,
        require_price=True,
        max_tokens=max_tokens,
        reasoning_effort=os.environ.get("SENTINEL_LLM_REASONING_EFFORT", "low") or "low",
    )
    live = CappedTransport(http, cap_usd=cap_usd)
    recordings = HERE / "recordings" / run_id
    transport = RecordingTransport(recordings, "v2", live, record=True, api_key=api_key)
    config = RouterConfig(
        cheap_model=cheap,
        strong_model=strong,
        default_model=os.environ.get("SENTINEL_LLM_DEFAULT_MODEL", "") or cheap,
        prompt_version="v2",
        examples=examples,
        route_rule=os.environ.get("SENTINEL_LLM_ROUTE_RULE", "heuristic") or "heuristic",
    )
    router = PromptedLLMRouter(transport, config)
    baseline = DemoModel()

    base_ok, rows = [], []
    for case in cases:
        try:
            base_kind = baseline.understand(case.message, list(case.turns)).kind.value
        except (InvalidReply, ModelUnavailable):
            base_kind = "unavailable"
        base_ok.append(base_kind == case.expected_intent)
        try:
            result = router.understand(case.message, list(case.turns))
        except InvalidReply:
            rows.append({"id": case.id, "status": "invalid"})
            continue
        except ModelUnavailable:
            rows.append({"id": case.id, "status": "unavailable"})
            continue
        slot_scores = _slot_match(case.expected_slots, result.slots)
        draft_ok: bool | None = None
        draft_reason: str | None = None
        if result.reply_draft is not None:
            facts = DraftFacts(
                merchant=(case.expected_slots or {}).get("merchant_words"),
                amount=str((case.expected_slots or {}).get("amount"))
                if (case.expected_slots or {}).get("amount") is not None
                else None,
                date=(case.expected_slots or {}).get("date_phrase"),
            )
            draft_ok, draft_reason = validate_draft(result.reply_draft, facts, case.locale)
        rows.append(
            {
                "id": case.id,
                "status": "ok",
                "kind": result.kind.value,
                "kind_ok": result.kind.value == case.expected_intent,
                "subtype": result.subtype,
                "subtype_ok": True if case.expected_subtype is None else result.subtype == case.expected_subtype,
                "slots": slot_scores,
                "draft": result.reply_draft,
                "draft_ok": draft_ok,
                "draft_reason": draft_reason,
                "confidence": result.confidence,
                "cost_usd": result.cost_usd,
            }
        )
    ok = [r for r in rows if r["status"] == "ok"]
    intent_of = {c.id: c.expected_intent for c in cases}
    subtype_of = {c.id: c.expected_subtype for c in cases}
    sub = [r for r in ok if subtype_of[r["id"]] is not None]
    by_intent = {}
    for intent in sorted(set(intent_of.values())):
        group = [r for r in ok if intent_of[r["id"]] == intent]
        by_intent[intent] = sum(r["kind_ok"] for r in group) / len(group) if group else None
    spend = live.report()
    summary = {
        "run_id": run_id,
        "kind": "development",
        "eval_version": EVAL_VERSION,
        "commit": _git_commit(),
        "prompt_version": "v2",
        "example_ids": [e.case_id for e in examples],
        "models": {"cheap": cheap, "strong": strong, "route_rule": config.route_rule},
        "max_tokens": max_tokens,
        "n": len(cases),
        "split": "development",
        "baseline": {
            "n": len(cases),
            "kind_accuracy": round(sum(base_ok) / len(base_ok), 4) if base_ok else 0.0,
        },
        "router_v2": {
            "n": len(cases),
            "kind_accuracy": sum(r["kind_ok"] for r in ok) / len(ok) if ok else 0.0,
            "by_intent": by_intent,
            "subtype_accuracy": sum(r["subtype_ok"] for r in sub) / len(sub) if sub else None,
            "slot_match": {
                key: sum(r["slots"][key]["match"] for r in ok) / len(ok) if ok else None
                for key in ("merchant_words", "amount", "date_phrase", "twice")
            },
            "drafts": {
                "n": sum(1 for r in ok if r["draft"] is not None),
                "rejected": sum(1 for r in ok if r["draft_ok"] is False),
                "reasons": dict(sorted(Counter(r["draft_reason"] for r in ok if r["draft_ok"] is False).items())),
            },
            "invalid": sum(1 for r in rows if r["status"] == "invalid"),
            "unavailable": sum(1 for r in rows if r["status"] == "unavailable"),
            "cost_usd": {"total": round(sum(r.get("cost_usd", 0.0) for r in ok), 6), "n": len(ok)},
        },
        "paired_router_v2_vs_baseline": paired(
            cases,
            [c.expected_intent if hit else "other" for c, hit in zip(cases, base_ok)],
            [r["kind"] if r["status"] == "ok" else "other" for r in rows],
        ),
        "spend": spend,
        "prices": PRICE_SOURCE,
        "notes": [SIMULATION_NOTE, "Development numbers for baseline and router_v2 on the router-v3 development split (018 amendment)."],
        "rows": rows,
    }
    validate_has_n(summary)
    lines = [
        f"# Development {run_id} (baseline vs router v2)",
        "",
        f"Cases: {len(cases)} development. No sealed case read.",
        f"Baseline kind accuracy: {summary['baseline']['kind_accuracy']:.4f}.",
        f"Router v2 kind accuracy: {summary['router_v2']['kind_accuracy']:.4f}.",
        f"Subtype accuracy: {summary['router_v2']['subtype_accuracy']}. "
        f"Slot match: {summary['router_v2']['slot_match']}.",
        f"Drafts: {summary['router_v2']['drafts']['n']} returned, "
        f"{summary['router_v2']['drafts']['rejected']} rejected {summary['router_v2']['drafts']['reasons']}.",
        f"Paired net: {summary['paired_router_v2_vs_baseline']['net']} of {summary['paired_router_v2_vs_baseline']['n']} "
        f"({summary['paired_router_v2_vs_baseline']['net_share']}).",
        f"Spend: USD {spend['spent_usd']} over {spend['n']} live calls (cap {spend['cap_usd']}).",
    ]
    if freeze:
        assert_freezable(spend)
        freeze_run(REPO_ROOT, run_id, summary, "\n".join(lines) + "\n")
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Development numbers for baseline and router_v2.")
    parser.add_argument("run_id")
    parser.add_argument("--cap", type=float, default=1.0, help="spend cap in USD for live calls")
    args = parser.parse_args(argv)
    summary = dev_numbers(args.run_id, cap_usd=args.cap)
    print(f"[dev_v2] {summary['n']} cases, baseline {summary['baseline']['kind_accuracy']:.4f}, "
          f"v2 {summary['router_v2']['kind_accuracy']:.4f}, spend {summary['spend']}")


if __name__ == "__main__":
    main()
