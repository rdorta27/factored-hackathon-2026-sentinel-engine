"""Probe prompt v3 with the real model over the v3 development cases.

Usage from ``sentinel-ai-core/`` (load ``.env`` first)::

    SENTINEL_LLM_PROMPT_VERSION=v3 python3 -m eval.probe_v3 [--out eval/review/probe-v3.md]

Reads the served v3 configuration (same examples and system prompt as the
app), calls the live endpoint through the spend cap, and writes a markdown
report: kind, subtype and slots against expected, raw and filled draft,
rejection reason, language and cost. Not a frozen measurement: G2 reads it.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

os.environ.setdefault("SENTINEL_LLM_PROMPT_VERSION", "v3")

from app.ai.drafts import DraftFacts, fill_draft, validate_draft  # noqa: E402
from app.ai.serving import model_from_env  # noqa: E402
from app.ai.transport import InvalidReply, ModelUnavailable  # noqa: E402
from eval.budget import DEFAULT_CAP_USD  # noqa: E402
from eval.cases import load_dir  # noqa: E402

FELIX = {"v3-loan-es-MX": "Felix 4", "v3-amount-es-MX": "Felix 8"}


def _slot_text(case, result) -> str:
    want = case.expected_slots or {}
    parts = []
    for key in ("merchant_words", "amount", "date_phrase", "twice"):
        if key not in want:
            continue
        have = getattr(result.slots, key)
        parts.append(f"{key}={have!r}" + ("" if _match(key, want[key], have) else " MISS"))
    return "; ".join(parts) or "-"


def _match(key: str, want, have) -> bool:
    if key == "amount":
        return have is not None and abs(float(have) - float(want)) < 1e-9
    if key == "twice":
        return have is True
    return have is not None and str(want).strip().lower() in str(have).strip().lower()


def probe() -> tuple[list[dict], float]:
    cases = [c for c in load_dir(HERE / "cases") if c.id.startswith("v3-")]
    model = model_from_env()
    info = model.describe()
    print(f"[probe_v3] model={info.model} prompt={info.prompt_version}")
    rows = []
    for case in sorted(cases, key=lambda c: c.id):
        try:
            result = model.understand(case.message, list(case.turns))
        except (InvalidReply, ModelUnavailable) as exc:
            rows.append({"case": case, "error": f"{type(exc).__name__}"})
            continue
        facts = DraftFacts(
            merchant=(case.expected_slots or {}).get("merchant_words"),
            amount=str((case.expected_slots or {}).get("amount"))
            if (case.expected_slots or {}).get("amount") is not None
            else None,
            date=(case.expected_slots or {}).get("date_phrase"),
        )
        draft_ok, reason, filled = None, None, None
        if result.reply_draft is not None:
            draft_ok, reason = validate_draft(result.reply_draft, facts, result.language.value)
            filled = fill_draft(result.reply_draft, facts) if draft_ok else None
        rows.append({"case": case, "result": result, "facts": facts, "draft_ok": draft_ok, "reason": reason, "filled": filled})
    spent = sum(r["result"].cost_usd for r in rows if "result" in r)
    return rows, spent


def report(rows: list[dict], spent: float) -> str:
    ok = [r for r in rows if "result" in r]
    kind_ok = sum(r["result"].kind.value == r["case"].expected_intent for r in ok)
    sub_cases = [r for r in ok if r["case"].expected_subtype is not None]
    sub_ok = sum(r["result"].subtype == r["case"].expected_subtype for r in sub_cases)
    lines = [
        "# Probe v3: development cases through the served prompt",
        "",
        f"Rows: {len(rows)}. Kind match: {kind_ok}/{len(ok)}. Subtype match: {sub_ok}/{len(sub_cases)}.",
        f"Drafts returned: {sum(1 for r in ok if r['result'].reply_draft is not None)}. "
        f"Rejected: {sum(1 for r in ok if r['draft_ok'] is False)}. Live spend: USD {spent:.6f} (cap {DEFAULT_CAP_USD}).",
        "",
        "Felix spotlight: `v3-loan-es-MX` (point 4, loan stays out of scope) and "
        "`v3-amount-es-MX` (point 8, amount slot 1000). Both rows are marked below.",
        "",
        "| Case | Message | Kind (want) | Subtype (want) | Slots | Draft raw | Draft shown | Reject | Lang |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        case = row["case"]
        mark = f" **[{FELIX[case.id]}]**" if case.id in FELIX else ""
        if "error" in row:
            lines.append(f"| {case.id}{mark} | {case.message} | {row['error']} | - | - | - | - | - | {case.locale} |")
            continue
        result = row["result"]
        want_sub = case.expected_subtype or "-"
        got_sub = result.subtype or "-"
        sub = f"{got_sub} ({want_sub})"
        if case.expected_subtype is not None and result.subtype != case.expected_subtype:
            sub += " MISS"
        kind = f"{result.kind.value} ({case.expected_intent})"
        if result.kind.value != case.expected_intent:
            kind += " MISS"
        draft = (result.reply_draft or "-").replace("|", "/")
        shown = (row["filled"] or "-").replace("|", "/") if row["draft_ok"] else "-"
        lines.append(
            f"| {case.id}{mark} | {case.message} | {kind} | {sub} | {_slot_text(case, result)} "
            f"| {draft} | {shown} | {row['reason'] or '-'} | {result.language.value} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Probe prompt v3 with the real model.")
    parser.add_argument("--out", default="eval/review/probe-v3.md")
    args = parser.parse_args(argv)
    rows, spent = probe()
    text = report(rows, spent)
    out = Path(args.out)
    if not out.is_absolute:
        out = HERE.parent / args.out
    out.write_text(text, encoding="utf-8")
    print(f"[probe_v3] wrote {out}, spend USD {spent:.6f}")
    if spent > DEFAULT_CAP_USD:
        raise SystemExit(f"probe spend USD {spent:.6f} passed the cap {DEFAULT_CAP_USD}")


if __name__ == "__main__":
    main()
