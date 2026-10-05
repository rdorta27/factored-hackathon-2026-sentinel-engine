"""Descriptive post hoc analysis of the frozen v8 measurement (M1, M2, M4).

Usage from ``sentinel-ai-core/``::

    python3 -m eval.analysis_v8

The command reads the frozen run ``2024Q4-eval-v8``, its recordings and the
trained baseline of ``2024Q4-train-v1``. It makes no live model call. It
freezes one descriptive run under
``evidence/evaluation-runs/2024Q4-analysis-v8/``.

- M1: error analysis. The confusion matrix of router_v2, router_v3 and the
  trained baseline by intent, language and country, and the failure
  categories of router_v3 with the case ids.
- M2: the highest-weighted character n-grams per intent of the trained
  baseline. It shows what the model learns.
- M4: the complementarity of the router and the trained baseline from the
  ``paired`` fields of the frozen run. This is post hoc and descriptive.
  The TF-IDF to LLM cascade is a projection, not a measurement.

The script also reports a post hoc sensitivity of router_v3 without the rows
that the frozen summary labels ``unavailable``. It is descriptive. It is not
the measurement.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent
RECORDINGS_DIR = HERE / "recordings" / "2024Q4-eval-v8"
SOURCE_RUN = "2024Q4-eval-v8"
ANALYSIS_RUN = "2024Q4-analysis-v8"
TRAIN_RUN = "2024Q4-train-v1"
SEALED_V8_DIR = HERE / "cases" / "sealed_v8"
SEALED_V8B_DIR = HERE / "cases" / "sealed_v8b"
EXAMPLES_V2_PATH = HERE / "examples_v2.json"
EXAMPLES_V3_PATH = HERE / "examples_v3.json"
CASES_DIR = HERE / "cases"

sys.path.insert(0, str(HERE.parent))

from eval.cases import Case, load_dir  # noqa: E402
from eval.examples import build_examples, build_examples_v3  # noqa: E402
from eval.report import EVAL_VERSION, freeze_run, validate_has_n  # noqa: E402
from eval.trained import load_frozen  # noqa: E402
from eval.versions import Version, run_version  # noqa: E402

ANALYSIS_CANDIDATES = ("trained_baseline", "router_v2", "router_v3")
TOP_NGRAMS = 12
NOTES = [
    "Team-written simulation cases, never dataset rows (decision 007).",
    "Post hoc and descriptive: the analysis reads the frozen 2024Q4-eval-v8 run and its recordings. It makes no live call and changes no gate.",
    "The case text stays in the sealed set. This page names cases by id only.",
    "The replay turns the rows that the frozen summary labels unavailable into predictions. The sensitivity section keeps the frozen view.",
]


def _frozen_summary(run_id: str = SOURCE_RUN) -> dict:
    path = REPO_ROOT / "evidence" / "evaluation-runs" / run_id / "summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _diagonal(confusion: dict) -> int:
    return sum(row.get(expected, 0) for expected, row in confusion.items() if expected != "unavailable")


def _unavailable(confusion: dict) -> int:
    return sum(row.get("unavailable", 0) for expected, row in confusion.items() if expected != "unavailable")


def _build_versions(cases: list[Case]) -> dict[str, Version]:
    """The replay candidates of M1. One pass each, no repeats, no live call."""
    from app.ai.llm import SYSTEM_PROMPT_V3, PromptedLLMRouter, RouterConfig
    from app.ai.recording import RecordingTransport
    from eval.measure_v8 import _env

    env = _env()
    development = load_dir(CASES_DIR)
    v2_ids = json.loads(EXAMPLES_V2_PATH.read_text(encoding="utf-8"))["ids"]
    spec = json.loads(EXAMPLES_V3_PATH.read_text(encoding="utf-8"))
    examples_v2 = build_examples(development, v2_ids)
    examples_v3 = build_examples_v3(development, spec["ids"], spec.get("drafts"))
    rec_v2 = RecordingTransport(RECORDINGS_DIR / "v2", "v2", None, record=False)
    rec_v3 = RecordingTransport(RECORDINGS_DIR / "v3", "v3", None, record=False)

    def router(rec, prompt, examples, system_prompt=None):  # type: ignore[no-untyped-def]
        config = RouterConfig(
            cheap_model=env["cheap"], strong_model=env["strong"], default_model=env["default"],
            prompt_version=prompt, examples=examples, route_rule=env["route_rule"],
        )
        if system_prompt is not None:
            config.system_prompt = system_prompt
        return PromptedLLMRouter(rec, config)

    return {
        "trained_baseline": Version(load_frozen()),
        "router_v2": Version(router(rec_v2, "v2", examples_v2), rec_v2),
        "router_v3": Version(router(rec_v3, "v3", examples_v3, SYSTEM_PROMPT_V3), rec_v3),
    }


def _m1(cases: list[Case]) -> dict:
    """Confusion by intent, language and country, and the v3 failure categories."""
    by_id = {c.id: c for c in cases}
    versions = _build_versions(cases)
    out: dict = {"n": len(cases), "candidates": {}}
    for name, version in versions.items():
        block = run_version(cases, version)
        predicted = block["predicted"]
        confusion = block["intent"]["confusion"]
        failures: dict[str, list[str]] = defaultdict(list)
        by_locale: dict[str, dict] = defaultdict(lambda: {"n": 0, "correct": 0})
        by_country: dict[str, dict] = defaultdict(lambda: {"n": 0, "correct": 0})
        for case, p in zip(cases, predicted):
            ok = p == case.expected_intent
            by_locale[case.locale]["n"] += 1
            by_locale[case.locale]["correct"] += ok
            by_country[case.country]["n"] += 1
            by_country[case.country]["correct"] += ok
            if not ok:
                failures[f"{case.expected_intent}->{p}"].append(case.id)
        out["candidates"][name] = {
            "n": block["n"],
            "confusion": confusion,
            "by_locale": {
                k: {"n": v["n"], "accuracy": round(v["correct"] / v["n"], 4) if v["n"] else None}
                for k, v in sorted(by_locale.items())
            },
            "by_country": {
                k: {"n": v["n"], "accuracy": round(v["correct"] / v["n"], 4) if v["n"] else None}
                for k, v in sorted(by_country.items())
            },
            "failures": {k: sorted(ids) for k, ids in sorted(failures.items())},
            "failure_count": sum(len(ids) for ids in failures.values()),
        }
    return out


def _m2() -> dict:
    """The highest-weighted character n-grams per intent of the trained baseline."""
    model = load_frozen()
    body = model.body
    vocabulary = list(body["vocabulary"])
    coef = body["coef"]
    labels = list(body["labels"])
    out = {"n": len(vocabulary), "labels": {}}
    for index, label in enumerate(labels):
        row = coef[index]
        ranked = sorted(range(len(vocabulary)), key=lambda i: row[i], reverse=True)[:TOP_NGRAMS]
        out["labels"][label] = [
            {"term": vocabulary[i].replace(" ", "·"), "weight": round(float(row[i]), 4)} for i in ranked
        ]
    return out


def _m4(frozen: dict) -> dict:
    """Complementarity of the router and the trained baseline from the paired fields."""
    out: dict = {"n": frozen["candidates"]["trained_baseline"]["n"], "pairs": {}}
    for after in ("router_v2", "router_v3"):
        block = frozen["paired"][f"{after}_vs_trained_baseline"]
        n = block["n"]
        fixed, broken = len(block["fixed"]), len(block["broken"])
        correct_before = _diagonal(frozen["candidates"]["trained_baseline"]["intent"]["confusion"])
        correct_after = _diagonal(frozen["candidates"][after]["intent"]["confusion"])
        both_right = correct_before - broken
        both_wrong = n - correct_after - broken
        out["pairs"][f"{after}_vs_trained_baseline"] = {
            "n": n,
            "both_right": both_right,
            "both_wrong": both_wrong,
            "only_router": fixed,
            "only_trained_baseline": broken,
            "net": block["net"],
            "interval_95": block["interval_95"],
            "above_zero": block["above_zero"],
            "only_router_ids": block["fixed"],
            "only_trained_baseline_ids": block["broken"],
        }
    return out


def _sensitivity(frozen: dict) -> dict:
    """Router_v3 accuracy without the rows the frozen summary labels unavailable."""
    out = {"n": 0, "blocks": {}}
    for block_name in ("candidates", "noisy", "attacks", "topup"):
        block = frozen[block_name]["router_v3"] if block_name == "candidates" else frozen[block_name]["candidates"]["router_v3"]
        confusion = block["intent"]["confusion"]
        n = block["n"]
        unavailable = _unavailable(confusion)
        correct = _diagonal(confusion)
        subtype = block["subtype"]
        unavailable_subtype = sum(
            row.get("unavailable", 0) for expected, row in confusion.items() if expected in ("missing", "out_of_scope")
        )
        denom = subtype["n"] - unavailable_subtype
        subtype_all = subtype["accuracy"]
        subtype_without = round(subtype["correct"] / denom, 4) if denom > 0 else None
        out["blocks"][block_name] = {
            "n": n,
            "unavailable": unavailable,
            "kind_accuracy_all": block["intent"]["accuracy"],
            "kind_accuracy_without_unavailable": round(correct / (n - unavailable), 4) if n - unavailable else None,
            "subtype_n": subtype["n"],
            "subtype_unavailable": unavailable_subtype,
            "subtype_accuracy_all": subtype_all,
            "subtype_accuracy_without_unavailable": subtype_without,
        }
    return out


def _render(summary: dict) -> str:
    m1 = summary["M1_errors"]
    m4 = summary["M4_complementarity"]
    lines = [
        f"# Analysis of {summary['source_run']} (post hoc, descriptive)",
        "",
        f"Cases: main {m1['n']}. No live call. The case text stays in the sealed set.",
        "",
        "## M1 · Failure categories by intent, language and country",
        "",
    ]
    for name, block in m1["candidates"].items():
        lines.append(f"### {name}: {block['failure_count']} wrong of {block['n']}")
        for category, ids in block["failures"].items():
            lines.append(f"- {category}: {len(ids)} ({', '.join(ids)})")
        lines.append("")
    lines += ["## M2 · Trained baseline, highest-weight n-grams per intent", ""]
    for label, terms in summary["M2_ngrams"]["labels"].items():
        lines.append(f"- {label}: " + ", ".join(f"`{t['term']}` {t['weight']}" for t in terms))
    lines += [
        "",
        "The model reads character n-grams of three to five characters, not words. A dot is a space.",
        "The weights show the substrings that push each intent: `cobr` (cobro) for charge, `algo` and `blema` (problema) for missing,",
        "`sald` (saldo) for out of scope, `ende` (entiende) and `huma` (humano) for person, `ultim` and `estad` (estado) for status.",
        "",
    ]
    lines += ["", "## M4 · Complementarity (post hoc, descriptive)", ""]
    for pair, block in m4["pairs"].items():
        lines.append(
            f"- {pair}: both right {block['both_right']}, both wrong {block['both_wrong']}, "
            f"only router {block['only_router']}, only trained {block['only_trained_baseline']}, "
            f"net {block['net']} {block['interval_95']} of {block['n']}"
        )
    lines += ["", "The TF-IDF to LLM cascade is a projection, not a measurement.", ""]
    lines += ["## Post hoc sensitivity of router_v3", ""]
    for block_name, block in summary["sensitivity"]["blocks"].items():
        lines.append(
            f"- {block_name}: unavailable {block['unavailable']} of {block['n']}; "
            f"kind {block['kind_accuracy_all']} all, {block['kind_accuracy_without_unavailable']} without; "
            f"subtype {block['subtype_accuracy_all']} all, {block['subtype_accuracy_without_unavailable']} without"
        )
    lines += ["", "Not the measurement. It changes no gate and no verdict.", ""]
    lines += ["## Notes"] + [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


def analyze(run_id: str = ANALYSIS_RUN, freeze: bool = True) -> dict:
    started = time.perf_counter()
    frozen = _frozen_summary()
    cases = [c for c in load_dir(SEALED_V8_DIR) if "noisy" not in c.tags and "adversarial" not in c.tags]
    summary = {
        "run_id": run_id,
        "kind": "analysis",
        "eval_version": EVAL_VERSION,
        "source_run": SOURCE_RUN,
        "measured_commit": frozen.get("measured_commit"),
        "n": len(cases),
        "M1_errors": _m1(cases),
        "M2_ngrams": _m2(),
        "M4_complementarity": _m4(frozen),
        "sensitivity": _sensitivity(frozen),
        "elapsed_s": round(time.perf_counter() - started, 1),
        "notes": NOTES,
    }
    validate_has_n(summary)
    if freeze:
        freeze_run(REPO_ROOT, run_id, summary, _render(summary))
    return summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Post hoc descriptive analysis of the frozen v8 run.")
    parser.add_argument("run_id", nargs="?", default=ANALYSIS_RUN)
    args = parser.parse_args(argv)
    summary = analyze(args.run_id)
    print(f"[analysis] froze {args.run_id}: {summary['n']} cases, {summary['elapsed_s']} s, no live call")


if __name__ == "__main__":
    main()


__all__ = ["analyze", "main"]
