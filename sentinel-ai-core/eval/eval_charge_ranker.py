"""Compare the charge-selection configurations on one held-out set (decision 025).

Configurations, all on the same examples:
- `rules_fixed`: the parsers and the narrowing before `chat-start` (a frozen copy, `grounding_before_chat_start.py`).
- `rules_tuned`: `narrow` of `app/ai/grounding.py` after `chat-start`, with the switch off.
- `learned`: the same `narrow`, with the selector of the frozen run train-v1. This is the served path.
- `LLM`: the model reads the description into slots. Code then narrows the charges with them. Sample only.

This module never imports the training module. It reads the weights file through
`load_ranker`, which checks the recorded hash.

    python -m eval.eval_charge_ranker --split validation                 # check, writes nothing
    python -m eval.eval_charge_ranker --split test --run test-v1         # frozen, write-once
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import date
from pathlib import Path
from typing import Callable

from app.ai import charge_ranker as ranker
from app.ai.grounding import (
    SoftFacts,
    StatedFacts,
    narrow,
    narrow_candidates,
    relative_dates,
    stated_merchant_tokens,
)
from app.orchestrator.types import Candidate
from eval import charge_examples as gen
from eval import grounding_before_chat_start as before
from eval.charge_pool import pool_candidates

ROOT = Path(__file__).resolve().parents[2] / "evidence" / "charge-ranker"
SHOWN = 3
BOOTSTRAP = 1000
METRICS = ("right_first", "right_in_top3", "wrong_automatic", "asks")

_OFF = None  # `narrow` reads the switch when no selector is given; main() checks that it is off.
Outcome = dict[str, bool]
Reader = Callable[[str, date, list[Candidate]], "tuple[list[Candidate], Candidate | None]"]


def _score(ordered: list[Candidate], pick: Candidate | None, target: str) -> Outcome:
    return {
        "right_first": bool(ordered) and ordered[0].candidate_id == target,
        "right_in_top3": any(row.candidate_id == target for row in ordered[:SHOWN]),
        "wrong_automatic": pick is not None and pick.candidate_id != target,
        "asks": pick is None,
    }


def _rest(first: list[Candidate], pool: list[Candidate]) -> list[Candidate]:
    seen = {row.candidate_id for row in first}
    return first + [row for row in pool if row.candidate_id not in seen]


def rules_fixed(text: str, today: date, pool: list[Candidate]) -> tuple[list[Candidate], Candidate | None]:
    """What the loop does now: one exact match is picked; otherwise the short list asks."""
    merchants = [row.merchant for row in pool]
    facts = before.extract_facts(text, today.year, merchants)
    grounded = before.ground(facts, pool)
    if grounded.outcome == "matched" and grounded.match is not None:
        return _rest([grounded.match], pool), grounded.match
    soft = before.extract_soft(text, today, merchants)
    narrowed = before.narrow_candidates(facts, soft, pool, today)
    ranked = narrowed.candidates if narrowed.stated else before.rank_candidates(facts, grounded.candidates or pool, today)
    return _rest(list(ranked), pool), None


def _from_narrow(result) -> tuple[list[Candidate], Candidate | None]:  # type: ignore[no-untyped-def]
    return result.candidates, result.match


def rules_tuned(text: str, today: date, pool: list[Candidate]) -> tuple[list[Candidate], Candidate | None]:
    """The loop after chat-start, with the selector off."""
    ordered, pick = _from_narrow(narrow(text, None, pool, today, selector=_OFF))
    return _rest(list(ordered), pool), pick


def learned(model: ranker.ChargeRanker) -> Reader:
    def read(text: str, today: date, pool: list[Candidate]) -> tuple[list[Candidate], Candidate | None]:
        ordered, pick = _from_narrow(narrow(text, None, pool, today, selector=model))
        return _rest(list(ordered), pool), pick

    return read


def _slot_dates(phrase: str, today: date) -> frozenset[str]:
    found = set(relative_dates(phrase, today))
    absolute = ranker._absolute_date(ranker.normalize_text(phrase), today)
    if absolute:
        found.add(absolute)
    return frozenset(found)


def llm_reader(understand: Callable[[str], object]) -> Reader:
    """Slots from the model, then the same narrowing as the rules. The model never sees the rows."""

    def read(text: str, today: date, pool: list[Candidate]) -> tuple[list[Candidate], Candidate | None]:
        slots = getattr(understand(text), "slots", None)
        merchants = [row.merchant for row in pool]
        amount = f"{slots.amount:.2f}" if slots is not None and slots.amount else None
        tokens = stated_merchant_tokens(slots.merchant_words, merchants) if slots is not None and slots.merchant_words else ()
        dates = _slot_dates(slots.date_phrase, today) if slots is not None and slots.date_phrase else frozenset()
        facts = StatedFacts(None, amount, None)
        soft = SoftFacts(tokens, dates, bool(slots is not None and slots.twice))
        narrowed = narrow_candidates(facts, soft, pool, today)
        pick = narrowed.candidates[0] if narrowed.stated and not narrowed.not_found and len(narrowed.candidates) == 1 else None
        return _rest(list(narrowed.candidates) if narrowed.stated else [], pool), pick

    return read


def _rate(items: list[Outcome], key: str) -> float:
    return sum(item[key] for item in items) / len(items) if items else 0.0


def _interval(groups: dict[str, list[Outcome]], key: str, seed: int) -> list[float]:
    """95% range, resampling customers (two examples of one customer are not independent)."""
    names = sorted(groups)
    counts = {name: (sum(item[key] for item in groups[name]), len(groups[name])) for name in names}
    rng = random.Random(seed)
    values = []
    for _ in range(BOOTSTRAP):
        hit = total = 0
        for name in rng.choices(names, k=len(names)):
            hit += counts[name][0]
            total += counts[name][1]
        values.append(hit / total if total else 0.0)
    values.sort()
    return [round(values[int(0.025 * BOOTSTRAP)], 4), round(values[int(0.975 * BOOTSTRAP) - 1], 4)]


def block(rows: list[tuple[gen.Example, Outcome]]) -> dict:
    """Counts, rates and 95% ranges for one group of examples."""
    outcomes = [outcome for _, outcome in rows]
    by_customer: dict[str, list[Outcome]] = {}
    for example, outcome in rows:
        by_customer.setdefault(example.customer_id, []).append(outcome)
    out: dict = {"n": len(rows)}
    for index, key in enumerate(METRICS):
        out[key] = {
            "count": sum(item[key] for item in outcomes),
            "rate": round(_rate(outcomes, key), 4),
            "range_95": _interval(by_customer, key, gen.SEED + index),
        }
    return out


def breakdowns(rows: list[tuple[gen.Example, Outcome]]) -> dict:
    cuts = {
        "locale": lambda e: e.locale,
        "mentions_merchant": lambda e: "yes" if e.has_merchant else "no",
        "family": lambda e: e.family,
        "amount_in_words": lambda e: "yes" if e.amount_in_words else "no",
    }
    return {
        cut: {
            value: block([pair for pair in rows if key(pair[0]) == value])
            for value in sorted({key(example) for example, _ in rows})
        }
        for cut, key in cuts.items()
    }


def run(
    examples: list[gen.Example],
    rows: dict[str, list[gen.Row]],
    readers: dict[str, Reader],
    llm_ids: set[str] | None = None,
) -> dict:
    results: dict = {}
    for name, reader in readers.items():
        subset = [e for e in examples if llm_ids is None or name != "LLM" or e.example_id in llm_ids]
        scored = []
        for example in subset:
            pool = pool_candidates(example, rows)
            ordered, pick = reader(example.text, date.fromisoformat(example.today), pool)
            scored.append((example, _score(ordered, pick, example.target_id)))
        results[name] = {"all": block(scored), "breakdowns": breakdowns(scored)}
    return results


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("validation", "test"), required=True)
    parser.add_argument("--run", help="write-once run folder name under evidence/charge-ranker/")
    parser.add_argument("--llm-sample", type=int, default=0, help="examples for the LLM configuration")
    args = parser.parse_args(argv)
    if args.split == "test" and not args.run:
        raise SystemExit("The test split is measured once. Give --run with a new folder name.")
    target = ROOT / args.run if args.run else None
    if target is not None and target.exists():
        raise SystemExit(f"{target} exists. A run is write-once.")

    train = json.loads((ROOT / "train-v1" / "summary.json").read_text(encoding="utf-8"))
    data = json.loads((ROOT / "data-v1" / "summary.json").read_text(encoding="utf-8"))
    model = ranker.load_ranker(ROOT / "train-v1" / "model.json", train["model_sha256"])
    examples, rows = gen.build_dataset(gen.gold_path())
    if gen.digest_of(examples) != data["examples_hash"]:
        raise SystemExit("The rebuilt examples differ from the frozen run data-v1.")
    chosen = [e for e in examples if e.split == args.split]

    if ranker.enabled():
        raise SystemExit(f"Unset {ranker.SWITCH}: the rules configurations must run with the switch off.")
    readers: dict[str, Reader] = {
        "rules_fixed": rules_fixed, "rules_tuned": rules_tuned, "learned": learned(model),
    }
    notes = []
    llm_ids: set[str] | None = None
    if args.llm_sample:
        from app.ai.serving import model_from_env
        from app.ai.demo import DemoModel

        live = model_from_env()
        if isinstance(live, DemoModel):
            notes.append("LLM is not measured: no model key is set.")
        else:
            sample = random.Random(gen.SEED).sample(chosen, min(args.llm_sample, len(chosen)))
            llm_ids = {e.example_id for e in sample}
            readers["LLM"] = llm_reader(lambda text: live.understand(text, []))
    results = run(chosen, rows, readers, llm_ids)
    summary = {
        "run": f"charge-ranker/{args.run}" if args.run else "check",
        "data_type": "Simulation: team-generated descriptions of real Gold transactions.",
        "split": args.split,
        "data_run": data["run"],
        "examples_hash": data["examples_hash"],
        "model_sha256": train["model_sha256"],
        "threshold": train["threshold"],
        "seed": gen.SEED,
        "shown_for_top_k": SHOWN,
        "llm_sample": len(llm_ids) if llm_ids else 0,
        "notes": notes,
        "code_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "configurations": results,
    }
    text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if target is None:
        print(json.dumps({k: v["all"] for k, v in results.items()}, indent=1), file=sys.stderr)
        return
    target.mkdir(parents=True)
    (target / "summary.json").write_text(text, encoding="utf-8")
    print(json.dumps({k: v["all"] for k, v in results.items()}, indent=1), file=sys.stderr)


if __name__ == "__main__":
    main()
