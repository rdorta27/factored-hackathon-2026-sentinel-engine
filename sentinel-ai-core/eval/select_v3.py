"""Selection runs for prompt v3 on the development split only.

Usage from ``sentinel-ai-core/`` (load ``.env`` first)::

    python3 -m eval.select_v3 2024Q4-select-v3 [--record] [--cap 0.45]

Without ``--record`` the run replays existing recordings and makes no live
call. With ``--record`` it calls the live endpoint through the spend cap and
freezes the run under ``evidence/evaluation-runs/<run-id>/``. Each run reads
development cases only and refuses a held-out case. No v3 call touches the
sealed set.
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
EXAMPLES_V3_PATH = HERE / "examples_v3.json"
sys.path.insert(0, str(HERE.parent))

from app.ai.drafts import DraftFacts, validate_draft  # noqa: E402
from app.ai.llm import SYSTEM_PROMPT_V3, PromptedLLMRouter, RouterConfig  # noqa: E402
from app.ai.prices import PRICE_SOURCE, PRICES  # noqa: E402
from app.ai.recording import RecordingTransport  # noqa: E402
from app.ai.transport import HttpTransport, InvalidReply, ModelUnavailable  # noqa: E402
from eval.budget import DEFAULT_CAP_USD, CappedTransport, assert_freezable  # noqa: E402
from eval.cases import check_splits, load_dir  # noqa: E402
from eval.examples import build_examples_v3  # noqa: E402
from eval.report import EVAL_VERSION, freeze_run, validate_has_n  # noqa: E402

MODEL = "accounts/fireworks/models/glm-5p3-flash"
SIMULATION_NOTE = "Team-written simulation cases, never dataset rows (decision 007)."


class SelectionReadsHeldOut(ValueError):
    """A selection run was given a held-out case."""


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _slot_match(expected: dict | None, got: object) -> dict:
    from app.ai.port import UnderstandSlots

    assert isinstance(got, UnderstandSlots)
    expected = expected or {}
    out = {}
    for key in ("merchant_words", "amount", "date_phrase", "twice"):
        want = expected.get(key)
        have = getattr(got, key)
        if want is None:
            out[key] = {"expected": None, "match": have in (None, False) if key == "twice" else have is None}
        elif key == "amount":
            out[key] = {"expected": want, "match": have is not None and abs(float(have) - float(want)) < 1e-9}
        elif key == "twice":
            out[key] = {"expected": want, "match": have is bool(want) and have}
        else:
            out[key] = {"expected": want, "match": have is not None and want.strip().lower() in have.strip().lower()}
    return out


def select_v3(run_id: str, record: bool = False, cap_usd: float = DEFAULT_CAP_USD, freeze: bool = False) -> dict:
    loaded = load_dir(CASES_DIR)
    held = sorted(c.id for c in loaded if c.split == "held_out")
    if held:
        raise SelectionReadsHeldOut(f"selection reads development only; held-out ids given: {held}")
    check_splits(loaded)
    cases = [c for c in loaded if c.split == "development"]
    spec = json.loads(EXAMPLES_V3_PATH.read_text(encoding="utf-8"))
    example_ids = spec["ids"]
    examples = build_examples_v3(loaded, example_ids, spec.get("drafts"))

    api_key = os.environ.get("SENTINEL_LLM_API_KEY", "")
    live: CappedTransport | None = None
    if record:
        base_url = os.environ.get("SENTINEL_LLM_BASE_URL", "")
        if not base_url or not api_key:
            raise SystemExit("recording needs SENTINEL_LLM_BASE_URL and SENTINEL_LLM_API_KEY in the environment")
        http = HttpTransport(
            base_url=base_url,
            api_key=api_key,
            timeout_s=float(os.environ.get("SENTINEL_LLM_TIMEOUT_S", "10") or 10),
            max_retries=int(os.environ.get("SENTINEL_LLM_MAX_RETRIES", "2") or 2),
            prices=PRICES,
            require_price=True,
            max_tokens=int(os.environ.get("SENTINEL_LLM_MAX_TOKENS", "400") or 400),
            reasoning_effort=os.environ.get("SENTINEL_LLM_REASONING_EFFORT", "low") or "low",
        )
        live = CappedTransport(http, cap_usd=cap_usd)
    recordings = HERE / "recordings" / run_id
    transport = RecordingTransport(recordings, "v3", live, record=record, api_key=api_key)
    config = RouterConfig(
        cheap_model=os.environ.get("SENTINEL_LLM_CHEAP_MODEL", "") or MODEL,
        strong_model=os.environ.get("SENTINEL_LLM_STRONG_MODEL", "") or MODEL,
        default_model=os.environ.get("SENTINEL_LLM_DEFAULT_MODEL", "") or MODEL,
        prompt_version="v3",
        system_prompt=SYSTEM_PROMPT_V3,
        examples=examples,
        route_rule=os.environ.get("SENTINEL_LLM_ROUTE_RULE", "heuristic") or "heuristic",
    )
    router = PromptedLLMRouter(transport, config)

    rows = []
    for case in cases:
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
                "not_mine": result.not_mine,
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
    summary = {
        "run_id": run_id,
        "kind": "selection",
        "eval_version": EVAL_VERSION,
        "commit": _git_commit(),
        "prompt_version": "v3",
        "example_ids": example_ids,
        "n": len(cases),
        "split": "development",
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
        "spend": live.report() if live is not None else {"n": 0, "cap_usd": None, "spent_usd": 0.0, "capped": False},
        "prices": PRICE_SOURCE,
        "notes": [SIMULATION_NOTE, "Selection run for prompt v3 on the development split only."],
        "rows": rows,
    }
    validate_has_n(summary)
    lines = [
        f"# Selection {run_id} (prompt v3)",
        "",
        f"Cases: {len(cases)} development. Kind accuracy: {summary['kind_accuracy']:.4f}.",
        f"Subtype accuracy: {summary['subtype_accuracy']}. Slot match: {summary['slot_match']}.",
        f"Drafts: {summary['drafts']['n']} returned, {summary['drafts']['rejected']} rejected {summary['drafts']['reasons']}.",
        f"Invalid: {summary['invalid']}. Unavailable: {summary['unavailable']}.",
        f"Spend: {summary['spend']}. Cost total USD {summary['cost_usd']['total']}.",
    ]
    if record or freeze:
        assert_freezable(summary["spend"])
        freeze_run(REPO_ROOT, run_id, summary, "\n".join(lines) + "\n")
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Selection runs for prompt v3.")
    parser.add_argument("run_id")
    parser.add_argument("--record", action="store_true", help="call the live endpoint on a missing recording")
    parser.add_argument("--freeze", action="store_true", help="freeze an offline replay without live calls")
    parser.add_argument("--cap", type=float, default=DEFAULT_CAP_USD, help="spend cap in USD for live calls")
    args = parser.parse_args(argv)
    summary = select_v3(args.run_id, record=args.record, cap_usd=args.cap, freeze=args.freeze)
    print(f"[select_v3] {summary['n']} cases, kind accuracy {summary['kind_accuracy']:.4f}, spend {summary['spend']}")


if __name__ == "__main__":
    main()
