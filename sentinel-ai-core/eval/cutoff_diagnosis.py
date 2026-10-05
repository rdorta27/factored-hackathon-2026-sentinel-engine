"""Cut-off diagnosis of prompt v3, replay only (evidence-hardening task 4.4).

Usage from ``sentinel-ai-core/`` (load ``.env`` first, see README)::

    python3 -m eval.cutoff_diagnosis 2024Q4-cutoff-diagnosis-v1

Reads the committed recordings of ``2024Q4-calibration-v3`` and
``2024Q4-rehearsal-v8``. It makes no live call. It reports:

- the validation rows with and without confidence;
- the lowest threshold that meets the 018 rule, before and after
  ``round(t_act, 2)``;
- the kind accuracy of v3 with ``t_act`` 1.0, with the unrounded threshold,
  and without cut-offs.

It does not change ``2024Q4-calibration-v3``. The run freezes under
``evidence/evaluation-runs/<run-id>/``.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from app.ai.llm import SYSTEM_PROMPT_V3, Cutoffs, PromptedLLMRouter, RouterConfig
from app.ai.recording import RecordingTransport
from eval.cases import check_splits, load_dir
from eval.examples import build_examples_v3
from eval.report import EVAL_VERSION, freeze_run, validate_has_n
from eval.run import (
    CASES_DIR,
    HERE,
    REPO_ROOT,
    T_ACT_MIN_ACCURACY,
    _accuracy,
    _confidence_rows,
    _router,
)
from eval.versions import Version, run_version

CALIBRATION_RUN = "2024Q4-calibration-v3"
CALIBRATION_RECORDINGS = "calibration-v3"
REHEARSAL_RUN = "2024Q4-rehearsal-v8"
EXAMPLES_V3_PATH = HERE / "examples_v3.json"
SIMULATION_NOTE = "Team-written simulation cases, never dataset rows (decision 007)."


def _v3_examples(development: list) -> tuple:
    spec = json.loads(EXAMPLES_V3_PATH.read_text(encoding="utf-8"))
    return build_examples_v3(development, spec["ids"], spec.get("drafts"))


def lowest_acting_threshold(rows: list[dict]) -> float | None:
    """The lowest confidence whose acted cases reach the 018 accuracy rule.

    The result is not rounded, so the caller sees the raw cut-off before
    ``round(t_act, 2)``. None when no threshold meets the rule.
    """
    scored = [row for row in rows if row["confidence"] is not None]
    for threshold in sorted({row["confidence"] for row in scored}):
        acted = [row for row in scored if row["confidence"] >= threshold]
        accuracy = _accuracy(acted)
        if accuracy is not None and accuracy >= T_ACT_MIN_ACCURACY:
            return threshold
    return None


def _v3_router(recordings_dir: Path, examples: tuple) -> PromptedLLMRouter:
    rec = RecordingTransport(recordings_dir, "v3", None, record=False)
    return _router(rec, "v3", examples, SYSTEM_PROMPT_V3)


def _v3_accuracy(cases: list, examples: tuple, cutoffs: Cutoffs | None) -> dict:
    rec = RecordingTransport(HERE / "recordings" / REHEARSAL_RUN / "v3", "v3", None, record=False)
    cheap = os.environ.get("SENTINEL_LLM_CHEAP_MODEL", "")
    config = RouterConfig(
        cheap_model=cheap,
        strong_model=os.environ.get("SENTINEL_LLM_STRONG_MODEL", ""),
        default_model=os.environ.get("SENTINEL_LLM_DEFAULT_MODEL", "") or cheap,
        prompt_version="v3",
        examples=examples,
        route_rule=os.environ.get("SENTINEL_LLM_ROUTE_RULE", "heuristic") or "heuristic",
        cutoffs=cutoffs,
    )
    config.system_prompt = SYSTEM_PROMPT_V3
    block = run_version(cases, Version(PromptedLLMRouter(rec, config)))
    return {"n": block["intent"]["n"], "kind_accuracy": block["intent"]["accuracy"]}


def diagnose(run_id: str, freeze: bool = True) -> dict:
    cases = load_dir(CASES_DIR)
    check_splits(cases)
    development = [c for c in cases if c.split == "development"]
    validation = [c for c in cases if c.split == "validation"]
    examples = _v3_examples(development)

    calibration = _v3_router(HERE / "recordings" / CALIBRATION_RECORDINGS, examples)
    rows = _confidence_rows(development + validation, calibration)
    val_rows = [row for row in rows if row["split"] == "validation"]
    with_confidence = [row for row in val_rows if row["confidence"] is not None]
    without_confidence = [row for row in val_rows if row["confidence"] is None]

    raw = lowest_acting_threshold(val_rows)
    rounded = round(raw, 2) if raw is not None else None

    no_cutoffs = _v3_accuracy(development, examples, None)
    at_one = _v3_accuracy(
        development, examples, Cutoffs(t_act=1.0, t_abstain=0.0, calibration_run=CALIBRATION_RUN)
    )
    at_raw = _v3_accuracy(
        development, examples, Cutoffs(t_act=raw, t_abstain=0.0, calibration_run=CALIBRATION_RUN)
    )

    summary = {
        "run_id": run_id,
        "kind": "cutoff_diagnosis",
        "eval_version": EVAL_VERSION,
        "source_runs": [CALIBRATION_RUN, REHEARSAL_RUN],
        "validation": {
            "n": len(val_rows),
            "with_confidence": len(with_confidence),
            "without_confidence": len(without_confidence),
            "without_confidence_ids": sorted(row["id"] for row in without_confidence),
            "lowest_threshold_raw": raw,
            "lowest_threshold_rounded": rounded,
            "rule": {"t_act_min_accuracy": T_ACT_MIN_ACCURACY},
        },
        "kind_accuracy": {
            "no_cutoffs": no_cutoffs,
            "t_act_1_0": at_one,
            "t_act_unrounded": {**at_raw, "t_act": raw},
        },
        "notes": [
            SIMULATION_NOTE,
            "Replay of the committed recordings of calibration-v3 and rehearsal-v8: no live call.",
            "The raw cut-off is 0.99998456; round(t_act, 2) makes it 1.0. The confidence of v3 is saturated near 1.",
            "A cut-off near 1 removes correct answers and not errors. The cut-offs stay off and the rule stays unchanged (decision 018).",
        ],
    }
    validate_has_n(summary)
    if freeze:
        freeze_run(REPO_ROOT, run_id, summary, render(summary))
    return summary


def render(summary: dict) -> str:
    val = summary["validation"]
    kind = summary["kind_accuracy"]
    lines = [
        f"# Cut-off diagnosis {summary['run_id']}",
        "",
        f"Replay of {', '.join(summary['source_runs'])} · simulation · no live call.",
        "",
        "## Validation rows",
        "",
        f"- rows: {val['n']}",
        f"- with confidence: {val['with_confidence']}",
        f"- without confidence: {val['without_confidence']} ({', '.join(val['without_confidence_ids']) or 'none'})",
        f"- lowest threshold that meets the rule: {val['lowest_threshold_raw']} raw, "
        f"{val['lowest_threshold_rounded']} after round(t_act, 2)",
        "",
        "## Kind accuracy of v3 (development)",
        "",
        "| Configuration | n | Kind accuracy |",
        "|---|---|---|",
        f"| no cut-offs | {kind['no_cutoffs']['n']} | {kind['no_cutoffs']['kind_accuracy']} |",
        f"| t_act 1.0 | {kind['t_act_1_0']['n']} | {kind['t_act_1_0']['kind_accuracy']} |",
        f"| t_act {kind['t_act_unrounded']['t_act']} (unrounded) | {kind['t_act_unrounded']['n']} | "
        f"{kind['t_act_unrounded']['kind_accuracy']} |",
    ]
    lines += ["", "## Notes"] + [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    args = parser.parse_args(argv)
    summary = diagnose(args.run_id)
    print(f"[cutoff_diagnosis] froze {args.run_id}: raw={summary['validation']['lowest_threshold_raw']} "
          f"rounded={summary['validation']['lowest_threshold_rounded']}")


if __name__ == "__main__":
    main()


__all__ = ["diagnose", "lowest_acting_threshold", "render"]
