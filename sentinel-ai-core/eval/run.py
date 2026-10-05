"""Selection on development and the single held-out measurement.

Usage from ``sentinel-ai-core/`` (load ``.env`` first, see README)::

    python3 -m eval.run select 2024Q4-select-v1 [--record]
    python3 -m eval.run measure 2024Q4-eval-v7 [--record]
    python3 -m eval.run verify 2024Q4-eval-v7
    python3 -m eval.run train 2024Q4-train-v1

``select`` reads the development split only and fails on a held-out case.
``measure`` checks the seal hash and ``measured.json``, runs the baseline and
both router versions on the sealed cases, freezes the run and appends the hash.
``verify`` recomputes a frozen measurement from the recordings, offline, and
compares it with the frozen summary. Without ``--record`` no live call is made.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

from app.ai.demo import DemoModel
from app.ai.llm import ROUTE_RULES, SYSTEM_PROMPT_V3, PromptedLLMRouter, RouterConfig
from app.ai.prices import PRICE_SOURCE, PRICES
from app.ai.recording import RecordingTransport
from app.ai.transport import HttpTransport, InvalidReply, ModelUnavailable
from eval import metrics
from eval.budget import DEFAULT_CAP_USD, CappedTransport, assert_freezable
from eval.cases import Case, check_splits, load_cases, load_dir
from eval.examples import PROMPT_VERSION_WITH_EXAMPLES, build_examples
from eval.intervals import accuracy_block
from eval.paired import paired, paired_flags
from eval.report import EVAL_VERSION, freeze_run, render_resolution, validate_has_n
from eval.runner import run_system
from eval.seal import (
    MEASURED_PATH,
    SEAL_PATH,
    SEALED_DIR,
    assert_not_measured,
    blocks,
    record_measured,
    verify_seal,
)
from eval.versions import Version, run_version, run_versions

HERE = Path(__file__).parent
REPO_ROOT = HERE.parent.parent
CASES_DIR = HERE / "cases"
RECORDINGS_DIR = HERE.parent / "app" / "ai" / "fixtures"
EXAMPLES_PATH = HERE / "examples_v2.json"
# The resolution set and its own recordings, kept out of the app image (design §5).
RESOLUTION_PATH = CASES_DIR / "resolution.jsonl"
RESOLUTION_RECORDINGS_DIR = HERE / "recordings" / "resolution-v1"
# Fresh recordings: the selection ones carry no log-probabilities, so the
# calibration records the same inputs again, now with the label alternatives.
CALIBRATION_RECORDINGS_DIR = HERE / "recordings" / "calibration-v1"

# Choice rule of the 018 amendment, fixed before the calibration was run.
T_ACT_MIN_ACCURACY = 0.9321  # eval-v7 v2 held-out accuracy (0.9821) minus 5 points
T_ABSTAIN_MAX_ACCURACY = 0.5
CONFIDENCE_BANDS = (
    ("0.00-0.50", 0.0, 0.5),
    ("0.50-0.60", 0.5, 0.6),
    ("0.60-0.70", 0.6, 0.7),
    ("0.70-0.80", 0.7, 0.8),
    ("0.80-0.90", 0.8, 0.9),
    ("0.90-0.95", 0.9, 0.95),
    ("0.95-1.00", 0.95, 1.0000001),
)

CHEAP_CANDIDATES = ("accounts/fireworks/models/gpt-oss-120b", "accounts/fireworks/models/glm-5p3-flash")
STRONG_CANDIDATES = ("accounts/fireworks/models/deepseek-v4p1-flash",)
STABILITY_BASES = 25
END_TO_END_CASES = 30
SIMULATION_NOTE = "Team-written simulation cases, never dataset rows (decision 007)."


class SelectionReadsHeldOut(ValueError):
    """A selection run was given a held-out case."""


def _mix(cases: list[Case]) -> dict:
    return {
        "n": len(cases),
        "by_variant": dict(sorted(Counter(c.variant or c.locale for c in cases).items())),
        "by_intent": dict(sorted(Counter(c.expected_intent for c in cases).items())),
        "by_split": dict(sorted(Counter(c.split for c in cases).items())),
    }


def live_transport(record: bool, cap_usd: float) -> tuple[CappedTransport | None, str]:
    """One capped live transport per run, shared by every recorder; None when replaying."""
    api_key = os.environ.get("SENTINEL_LLM_API_KEY", "")
    if not record:
        return None, api_key
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
        max_tokens=int(os.environ.get("SENTINEL_LLM_MAX_TOKENS", "200") or 200),
        reasoning_effort=os.environ.get("SENTINEL_LLM_REASONING_EFFORT") or None,
    )
    return CappedTransport(http, cap_usd=cap_usd), api_key


def recorder(prompt_version: str, live: CappedTransport | None, api_key: str, record: bool) -> RecordingTransport:
    return RecordingTransport(RECORDINGS_DIR, prompt_version, live, record=record, api_key=api_key)


def _spend(live: CappedTransport | None) -> dict:
    return live.report() if live is not None else {"n": 0, "cap_usd": None, "spent_usd": 0.0, "capped": False}


def _pt_loss(cases: list[Case], predicted: list[str]) -> dict:
    """Bases where pt-BR is wrong and es-MX right, minus the opposite (016 amendment, D2)."""
    by_base: dict[str, dict[str, bool]] = {}
    for case, p in zip(cases, predicted):
        if case.base_id and case.variant in ("es-MX", "pt-BR"):
            by_base.setdefault(case.base_id, {})[case.variant] = p == case.expected_intent
    shared = {b: row for b, row in by_base.items() if len(row) == 2}
    lost = sorted(b for b, row in shared.items() if row["es-MX"] and not row["pt-BR"])
    won = sorted(b for b, row in shared.items() if row["pt-BR"] and not row["es-MX"])
    return {"n": len(shared), "lost_bases": lost, "won_bases": won, "net_loss": len(lost) - len(won)}


def _route_simulation(cases: list[Case], single: dict[str, dict]) -> dict:
    """D1 to D3 without extra calls: combine single-model predictions under each route rule."""
    out = {}
    for rule_name, rule in sorted(ROUTE_RULES.items()):
        routes = [rule(case.message) for case in cases]
        strong_share = sum(1 for r in routes if r == "strong") / len(cases) if cases else 0.0
        combos = {}
        for cheap in CHEAP_CANDIDATES:
            for strong in STRONG_CANDIDATES:
                if cheap not in single or strong not in single:
                    continue
                preds = [
                    single[strong]["predicted"][i] if routes[i] == "strong" else single[cheap]["predicted"][i]
                    for i in range(len(cases))
                ]
                correct = [p == c.expected_intent for p, c in zip(preds, cases)]
                combos[f"{cheap} + {strong}"] = accuracy_block(cases, correct)
        per_route = {}
        for model, block in single.items():
            for route in ("cheap", "strong"):
                idx = [i for i, r in enumerate(routes) if r == route]
                per_route.setdefault(model, {})[route] = accuracy_block(
                    [cases[i] for i in idx], [block["predicted"][i] == cases[i].expected_intent for i in idx]
                )
        out[rule_name] = {
            "n": len(cases),
            "strong_share": round(strong_share, 4),
            "combined": combos,
            "per_route_accuracy": per_route,
        }
    return out


def select(
    run_id: str,
    record: bool = False,
    cap_usd: float = DEFAULT_CAP_USD,
    freeze: bool = True,
    extra_strong: tuple[str, ...] = (),
) -> dict:
    """``extra_strong`` adds the larger strong models 016 measures only when the strong candidate fails."""
    global STRONG_CANDIDATES
    STRONG_CANDIDATES = tuple(dict.fromkeys(STRONG_CANDIDATES + extra_strong))
    loaded = load_dir(CASES_DIR)
    held = sorted(c.id for c in loaded if c.split == "held_out")
    if held:
        raise SelectionReadsHeldOut(f"selection reads development only; held-out ids given: {held}")
    check_splits(loaded)
    # The validation split is carved from development for the cut-off calibration
    # (018 amendment); model selection keeps reading development only.
    cases = [c for c in loaded if c.split == "development"]
    live, api_key = live_transport(record, cap_usd)
    rec = recorder("v1", live, api_key, record)
    single = {}
    for model in CHEAP_CANDIDATES + STRONG_CANDIDATES:
        config = RouterConfig(cheap_model=model, strong_model=model, default_model=model, route_rule="strong")
        block = run_version(cases, Version(PromptedLLMRouter(rec, config), rec))
        block["pt_loss"] = _pt_loss(cases, block["predicted"])
        single[model] = block
    baseline = run_version(cases, Version(DemoModel()))
    spend = _spend(live)
    summary = {
        "run_id": run_id,
        "kind": "selection",
        "eval_version": EVAL_VERSION,
        "n": len(cases),
        "case_mix": _mix(cases),
        "split": "development",
        "candidates": single,
        "baseline": baseline,
        "routes": _route_simulation(cases, single),
        "spend": spend,
        "prices": PRICE_SOURCE,
        "notes": [SIMULATION_NOTE, "Selection run on the development split only (016 amendment)."],
    }
    validate_has_n(summary)
    if freeze:
        assert_freezable(spend)
        freeze_run(REPO_ROOT, run_id, summary, _selection_report(summary))
    return summary


def _router(rec: RecordingTransport, prompt_version: str, examples=(), system_prompt: str | None = None) -> PromptedLLMRouter:  # type: ignore[no-untyped-def]
    cheap = os.environ.get("SENTINEL_LLM_CHEAP_MODEL", "")
    strong = os.environ.get("SENTINEL_LLM_STRONG_MODEL", "")
    if not cheap or not strong:
        raise SystemExit("set SENTINEL_LLM_CHEAP_MODEL and SENTINEL_LLM_STRONG_MODEL to the models chosen in 016")
    config = RouterConfig(
        cheap_model=cheap,
        strong_model=strong,
        default_model=os.environ.get("SENTINEL_LLM_DEFAULT_MODEL", "") or cheap,
        prompt_version=prompt_version,
        examples=examples,
        route_rule=os.environ.get("SENTINEL_LLM_ROUTE_RULE", "heuristic") or "heuristic",
    )
    if system_prompt is not None:
        config.system_prompt = system_prompt
    return PromptedLLMRouter(rec, config)


def _band_of(confidence: float) -> str:
    for label, low, high in CONFIDENCE_BANDS:
        if low <= confidence < high:
            return label
    return CONFIDENCE_BANDS[-1][0]


def _confidence_rows(cases: list[Case], router: PromptedLLMRouter) -> list[dict]:
    """One row per case: expected label, predicted label and confidence."""
    rows = []
    for case in cases:
        try:
            result = router.understand(case.message, list(case.turns))
        except (InvalidReply, ModelUnavailable):
            predicted, confidence = "unavailable", None
        else:
            predicted, confidence = result.kind.value, result.confidence
        rows.append(
            {
                "id": case.id,
                "base_id": case.base_id,
                "split": case.split,
                "expected": case.expected_intent,
                "predicted": predicted,
                "confidence": confidence,
            }
        )
    return rows


def _accuracy(rows: list[dict]) -> float | None:
    if not rows:
        return None
    return round(sum(row["predicted"] == row["expected"] for row in rows) / len(rows), 4)


def _split_report(rows: list[dict], t_act: float, t_abstain: float) -> dict:
    bands: dict[str, dict] = {}
    for row in rows:
        confidence = row["confidence"]
        if confidence is None:
            continue
        bucket = bands.setdefault(_band_of(confidence), {"n": 0, "correct": 0})
        bucket["n"] += 1
        bucket["correct"] += row["predicted"] == row["expected"]
    acted = clarified = abstained = 0
    for row in rows:
        confidence = row["confidence"]
        if confidence is None or confidence < t_abstain:
            abstained += 1
        elif confidence >= t_act:
            acted += 1
        else:
            clarified += 1
    n = len(rows)
    return {
        "n": n,
        "with_confidence": sum(1 for row in rows if row["confidence"] is not None),
        "accuracy": _accuracy(rows),
        "bands": {
            label: {"n": bucket["n"], "accuracy": round(bucket["correct"] / bucket["n"], 4)}
            for label, bucket in sorted(bands.items())
        },
        "actions": {
            "acted": {"n": acted, "share": round(acted / n, 4) if n else 0.0},
            "clarified": {"n": clarified, "share": round(clarified / n, 4) if n else 0.0},
            "abstained": {"n": abstained, "share": round(abstained / n, 4) if n else 0.0},
        },
    }


def _choose_cutoffs(rows: list[dict]) -> dict:
    """The 018 amendment rule, applied to the validation split only."""
    scored = [row for row in rows if row["confidence"] is not None]
    thresholds = sorted({row["confidence"] for row in scored})
    t_act = 1.0
    for threshold in thresholds:
        acted = [row for row in scored if row["confidence"] >= threshold]
        accuracy = _accuracy(acted)
        if accuracy is not None and accuracy >= T_ACT_MIN_ACCURACY:
            t_act = threshold
            break
    t_abstain = 0.0
    for threshold in thresholds:
        abstained = [row for row in scored if row["confidence"] < threshold]
        accuracy = _accuracy(abstained)
        if accuracy is not None and accuracy < T_ABSTAIN_MAX_ACCURACY:
            t_abstain = threshold
    t_abstain = min(t_abstain, t_act)
    return {
        "t_act": round(t_act, 2),
        "t_abstain": round(t_abstain, 2),
        "chosen_on": "validation",
        "rule": {
            "t_act_min_accuracy": T_ACT_MIN_ACCURACY,
            "t_abstain_max_accuracy": T_ABSTAIN_MAX_ACCURACY,
            "note": "lowest cut-off acting at the eval-v7 v2 accuracy minus the 018 tolerance; highest cut-off abstaining under one half",
        },
        "n": len(scored),
    }


def calibrate(
    run_id: str,
    record: bool = False,
    cap_usd: float = DEFAULT_CAP_USD,
    freeze: bool = True,
    prompt: str = PROMPT_VERSION_WITH_EXAMPLES,
) -> dict:
    """Fit confidences on development, choose the cut-offs on validation.

    ``prompt`` is "v2" or "v3": same code and rule, versioned examples and
    recordings. The v2 path is unchanged.
    """
    from eval.examples import build_examples_v3

    cases = load_dir(CASES_DIR)
    check_splits(cases)
    development = [c for c in cases if c.split == "development"]
    validation = [c for c in cases if c.split == "validation"]
    if not validation:
        raise SystemExit("no validation cases; run the split carve first (018 amendment)")
    if prompt == "v3":
        spec = json.loads((HERE / "examples_v3.json").read_text(encoding="utf-8"))
        examples = build_examples_v3(development, spec["ids"], spec.get("drafts"))
        recordings = HERE / "recordings" / "calibration-v3"
        system_prompt: str | None = SYSTEM_PROMPT_V3
    else:
        if not EXAMPLES_PATH.is_file():
            raise SystemExit(f"write the development example ids for v2 to {EXAMPLES_PATH} before calibrating")
        examples = build_examples(development, json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))["ids"])
        recordings = CALIBRATION_RECORDINGS_DIR
        system_prompt = None
    live, api_key = live_transport(record, cap_usd)
    max_tokens = int(os.environ.get("SENTINEL_LLM_MAX_TOKENS", "200") or 200)
    rec = RecordingTransport(recordings, prompt, live, record=record, api_key=api_key)
    router = _router(rec, prompt, examples, system_prompt)
    rows = _confidence_rows(development + validation, router)
    dev_rows = [row for row in rows if row["split"] == "development"]
    val_rows = [row for row in rows if row["split"] == "validation"]
    cutoffs = _choose_cutoffs(val_rows)
    spend = _spend(live)
    summary = {
        "run_id": run_id,
        "kind": "calibration",
        "eval_version": EVAL_VERSION,
        "prompt_version": prompt,
        "max_tokens": max_tokens,
        "n": len(rows),
        "case_mix": _mix(development + validation),
        "splits": {
            "development": _split_report(dev_rows, cutoffs["t_act"], cutoffs["t_abstain"]),
            "validation": _split_report(val_rows, cutoffs["t_act"], cutoffs["t_abstain"]),
        },
        "cutoffs": cutoffs,
        "spend": spend,
        "prices": PRICE_SOURCE,
        "notes": [
            SIMULATION_NOTE,
            "Confidences recorded once with log-probabilities; cut-offs chosen on the validation split (018 amendment).",
            "Validation is descriptive: development was read by model selection and the prompt examples; eval-v8 remains the clean measurement.",
        ],
    }
    validate_has_n(summary)
    if freeze:
        assert_freezable(spend)
        freeze_run(REPO_ROOT, run_id, summary, _calibration_report(summary))
    return summary


def _calibration_report(summary: dict) -> str:
    cut = summary["cutoffs"]
    lines = [
        f"# Calibration run {summary['run_id']}",
        "",
        f"Development + validation, n={summary['n']}. Cut-offs chosen on validation: "
        f"`t_act` = {cut['t_act']}, `t_abstain` = {cut['t_abstain']} (n={cut['n']} labels with confidence).",
        "",
    ]
    for split in ("development", "validation"):
        block = summary["splits"][split]
        lines += [
            f"## {split.capitalize()} (n={block['n']}, accuracy {block['accuracy']})",
            "",
            "| Confidence band | n | Accuracy |",
            "|---|---|---|",
        ]
        for label, band in block["bands"].items():
            lines.append(f"| {label} | {band['n']} | {band['accuracy']} |")
        actions = block["actions"]
        lines += [
            "",
            f"Act {actions['acted']['share']} · Clarify {actions['clarified']['share']} · "
            f"Abstain {actions['abstained']['share']}",
            "",
        ]
    spend = summary["spend"]
    lines += [f"Spend: USD {spend['spent_usd']} over {spend['n']} live calls (cap {spend['cap_usd']}).", "", "## Notes"]
    lines += [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


def _held_out_summary(run_id: str, record: bool, cap_usd: float, seal_record: dict) -> dict:
    sealed = load_dir(SEALED_DIR)
    development = load_dir(CASES_DIR)
    check_splits(sealed + development)
    not_held = sorted(c.id for c in sealed if c.split != "held_out")
    if not_held:
        raise SystemExit(f"sealed files may hold only held-out cases: {not_held}")
    if not EXAMPLES_PATH.is_file():
        raise SystemExit(f"write the development example ids for v2 to {EXAMPLES_PATH} before measuring")
    examples = build_examples(development, json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))["ids"])
    parts = blocks(sealed)
    main = parts["main"]
    live, api_key = live_transport(record, cap_usd)
    rec_v1 = recorder("v1", live, api_key, record)
    rec_v2 = recorder(PROMPT_VERSION_WITH_EXAMPLES, live, api_key, record)
    stability_bases = sorted({c.base_id for c in main if c.base_id})[:STABILITY_BASES]
    repeat_ids = frozenset(c.id for c in main if c.base_id in stability_bases)

    def versions(repeat: bool) -> dict:
        return {
            "baseline": Version(DemoModel()),
            "router_v1": Version(_router(rec_v1, "v1"), rec_v1),
            "router_v2": Version(
                _router(rec_v2, PROMPT_VERSION_WITH_EXAMPLES, examples),
                rec_v2,
                repetitions=3 if repeat else 1,
                repeat_ids=repeat_ids if repeat else frozenset(),
            ),
        }

    component = run_versions(main, versions(repeat=True))
    noisy_block = {}
    if parts["noisy"]:
        twins = {(c.base_id, c.variant): c for c in main}
        noisy_cases = [c for c in parts["noisy"] if (c.base_id, c.variant) in twins]
        twin_cases = [twins[(c.base_id, c.variant)] for c in noisy_cases]
        noisy_run = run_versions(noisy_cases, versions(repeat=False))
        twin_index = {case.id: i for i, case in enumerate(main)}
        degradation = {}
        for name, block in noisy_run["versions"].items():
            twin_pred = [component["versions"][name]["predicted"][twin_index[c.id]] for c in twin_cases]
            # Same labels on both sides: a "broken" case is one the noise made wrong.
            relabelled = [Case(**{**c.__dict__, "id": n.id}) for c, n in zip(twin_cases, noisy_cases)]
            degradation[name] = paired(relabelled, twin_pred, block["predicted"])
        noisy_block = {
            "n": len(noisy_cases),
            "by_perturbation": dict(sorted(Counter(c.perturbation for c in noisy_cases).items())),
            "versions": noisy_run["versions"],
            "degradation_vs_twin": degradation,
            "descriptive": True,
        }
    attacks = parts["attacks"]
    code_decided = [c for c in attacks if (c.fault or "none") != "none"]
    model_facing = [c for c in attacks if (c.fault or "none") == "none"]
    e2e = [c for c in sorted(main, key=lambda c: (c.base_id or "", c.variant or ""))][:END_TO_END_CASES]
    system = {"baseline": metrics.system_metrics(run_system(code_decided + model_facing + e2e, RECORDINGS_DIR, DemoModel))}
    for name, rec, version, ex in (
        ("router_v1", rec_v1, "v1", ()),
        ("router_v2", rec_v2, PROMPT_VERSION_WITH_EXAMPLES, examples),
    ):
        turns = run_system(model_facing + e2e, RECORDINGS_DIR, lambda r=rec, v=version, e=ex: _router(r, v, e))
        system[name] = metrics.system_metrics(turns)
    spend = _spend(live)
    return {
        "run_id": run_id,
        "kind": "held_out_measurement",
        "eval_version": EVAL_VERSION,
        "n": len(sealed),
        "seal": seal_record,
        "case_mix": {"main": _mix(main), "noisy": _mix(parts["noisy"]), "attacks": _mix(attacks)},
        "component": component,
        "noisy": noisy_block,
        "attacks": {
            "n": len(attacks),
            "code_decided": {"n": len(code_decided), "ids": sorted(c.id for c in code_decided)},
            "model_facing": {"n": len(model_facing), "ids": sorted(c.id for c in model_facing)},
        },
        "end_to_end": {"n": len(e2e), "ids": [c.id for c in e2e]},
        "system": system,
        "spend": spend,
        "prices": PRICE_SOURCE,
        "examples_v2": {"n": len(examples), "ids": [e.case_id for e in examples]},
        "notes": [
            SIMULATION_NOTE,
            "Held-out set sealed by hash before measuring and measured once (decision 018).",
            "Component latency comes from the recorded live calls; system latency is replay time.",
            f"Stability: router_v2 recorded three times on {len(stability_bases)} bases.",
        ],
    }


def measure(run_id: str, record: bool = False, cap_usd: float = DEFAULT_CAP_USD) -> dict:
    seal_record = verify_seal(SEALED_DIR, SEAL_PATH)
    assert_not_measured(seal_record["hash"], MEASURED_PATH)
    summary = _held_out_summary(run_id, record, cap_usd, seal_record)
    validate_has_n(summary)
    assert_freezable(summary["spend"])
    freeze_run(REPO_ROOT, run_id, summary, _measurement_report(summary))
    record_measured(seal_record["hash"], run_id, MEASURED_PATH)
    return summary


def _head_commit() -> str:
    """The commit the loop was measured at, so a replay knows what it reproduces."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - a missing git must not fail the run
        return "unknown"


def _resolution_mix(cases: list[Case]) -> dict:
    return {
        "n": len(cases),
        "by_country": dict(sorted(Counter(c.country for c in cases).items())),
        "by_locale": dict(sorted(Counter(c.locale for c in cases).items())),
        "by_variant": dict(sorted(Counter(c.variant or c.locale for c in cases).items())),
        "by_outcome": dict(sorted(Counter(c.expected_outcome for c in cases).items())),
        "by_situation": dict(sorted(Counter(c.base_id or c.id for c in cases).items())),
    }


def _resolved(turn: dict) -> bool:
    """A safe resolution: a case number on a must-not-pass case would not count."""
    return turn.get("outcome") == "case_confirmation" and not turn.get("must_not_pass")


def resolution(
    run_id: str,
    record: bool = False,
    cap_usd: float = DEFAULT_CAP_USD,
    freeze: bool = True,
    router_factory=None,  # type: ignore[no-untyped-def]
    recordings_dir: Path | str | None = None,
    live_mode: bool = False,
) -> dict:
    """Measure safe resolution over the multi-turn resolution set (decision 022).

    Baseline and ``router_v2`` replay the same cases, session, store and reference
    date. The router's answers are recorded once under the spend cap and replayed
    offline afterwards; ``router_factory`` is for tests only.

    ``live_mode`` is the live timing mode (evidence-hardening 2.1): every router
    call is a new live call under the spend cap, recorded in a fresh folder for
    this run. The summary labels the latency and the cost as live. Without it the
    run replays committed recordings and labels the numbers as replay.
    """
    cases = load_cases(RESOLUTION_PATH)
    check_splits(cases)
    development = load_dir(CASES_DIR)
    if not EXAMPLES_PATH.is_file():
        raise SystemExit(f"write the development example ids for v2 to {EXAMPLES_PATH} before running")
    examples = build_examples(development, json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))["ids"])
    if live_mode:
        record = True
    live, api_key = live_transport(record, cap_usd)
    if live_mode:
        rec_dir = HERE / "recordings" / run_id
    else:
        rec_dir = Path(recordings_dir) if recordings_dir is not None else RESOLUTION_RECORDINGS_DIR
    rec = RecordingTransport(
        rec_dir,
        PROMPT_VERSION_WITH_EXAMPLES,
        live,
        record=record,
        api_key=api_key,
        force_live=live_mode,
    )
    if router_factory is None:
        router_factory = lambda: _router(rec, PROMPT_VERSION_WITH_EXAMPLES, examples)  # noqa: E731
    timing = "live" if live_mode else "replay"
    baseline_turns = run_system(cases, rec_dir, DemoModel, timing=timing)
    router_turns = run_system(cases, rec_dir, router_factory, timing=timing)
    system = {
        "baseline": metrics.system_metrics(baseline_turns),
        "router_v2": metrics.system_metrics(router_turns),
    }
    paired_block = paired_flags(
        cases,
        [_resolved(t) for t in baseline_turns],
        [_resolved(t) for t in router_turns],
    )
    situations = sorted({c.base_id for c in cases if c.base_id})
    summary = {
        "run_id": run_id,
        "kind": "resolution",
        "eval_version": EVAL_VERSION,
        "n": len(cases),
        "bases": len(situations),
        "situations": {"n": len(situations), "ids": situations},
        "case_mix": _resolution_mix(cases),
        "system": system,
        "paired_resolution": paired_block,
        "spend": _spend(live),
        "prices": PRICE_SOURCE,
        "timing": {
            "mode": timing,
            "latency_source": timing,
            "cost_source": timing,
            "end_to_end": live_mode,
            "per_call": metrics.timing_metrics(router_turns)["per_call"],
            "per_conversation": metrics.timing_metrics(router_turns)["per_conversation"],
            "cost": {
                "per_attempted": system["router_v2"]["cost_usd"]["per_attempted"],
                "per_resolution": system["router_v2"]["cost_usd"]["per_resolution"],
            },
        },
        "measured_commit": _head_commit(),
        "notes": [
            SIMULATION_NOTE,
            "Simulation over a mock store: not a field resolution rate (decision 022).",
            "Baseline and router_v2 on the same cases, session, store and reference date; intervals resample situations.",
            "The system block replays the loop at measured_commit; a later loop change means a new run (task 1.1).",
        ],
    }
    validate_has_n(summary)
    if freeze:
        assert_freezable(summary["spend"])
        freeze_run(REPO_ROOT, run_id, summary, render_resolution(summary))
    return summary


def _strip(node):  # type: ignore[no-untyped-def]
    if isinstance(node, dict):
        # per_intent and bases were added after 2024Q4-eval-v7 (covered by unit
        # tests), so frozen runs without them still verify.
        return {k: _strip(v) for k, v in node.items() if k not in ("latency_ms", "per_intent", "bases")}
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def _comparable(summary: dict) -> dict:
    """Everything a replay must reproduce: spend, wall-clock latency and the commit
    are left out, since a replay makes no live call and records where it ran.
    The per-variant/per-country breakdown is a view over the same turns (added
    after 2024Q4-resolution-v1, covered by unit tests), so it is left out too
    and frozen runs without it still verify."""
    body = json.loads(json.dumps(summary, sort_keys=True))
    body.pop("spend", None)
    body.pop("measured_commit", None)
    body.pop("timing", None)
    system = body.get("system")
    if isinstance(system, dict):
        for block in system.values():
            if isinstance(block, dict):
                block.pop("by_variant", None)
                block.pop("by_country", None)
    return _strip(body)


def verify(run_id: str) -> bool:
    """Recompute a frozen run from recordings, offline, and compare."""
    frozen_path = REPO_ROOT / "evidence" / "evaluation-runs" / run_id / "summary.json"
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    if frozen.get("kind") == "training":
        from eval import train as training

        return training.verify(run_id)
    if frozen.get("kind") == "resolution":
        replayed = resolution(run_id, record=False, freeze=False)
        return _comparable(replayed) == _comparable(frozen)
    if frozen.get("kind") == "calibration":
        replayed = calibrate(run_id, record=False, freeze=False)
        return _comparable(replayed) == _comparable(frozen)
    seal_record = verify_seal(SEALED_DIR, SEAL_PATH)
    if frozen.get("seal", {}).get("hash") != seal_record["hash"]:
        raise SystemExit("the sealed set differs from the one this run measured")
    replayed = _held_out_summary(run_id, record=False, cap_usd=DEFAULT_CAP_USD, seal_record=seal_record)
    return _comparable(replayed) == _comparable(frozen)


def _selection_report(summary: dict) -> str:
    lines = [f"# Selection run {summary['run_id']}", "", f"Development split, n={summary['n']}.", ""]
    lines.append("| Model | Accuracy | 95% interval | JSON failures | pt-BR net loss | Cost USD |")
    lines.append("|---|---|---|---|---|---|")
    for model, block in summary["candidates"].items():
        overall = block["breakdown"]["overall"]
        lines.append(
            f"| `{model}` | {overall['accuracy']} | {overall['interval_95']} | "
            f"{block['json_failures']['count']}/{block['json_failures']['n']} | "
            f"{block['pt_loss']['net_loss']} of {block['pt_loss']['n']} | {block['cost_usd']['total']} |"
        )
    base = summary["baseline"]["breakdown"]["overall"]
    lines += ["", f"Keyword baseline: accuracy {base['accuracy']} (n={base['n']}).", "", "## Route rules", ""]
    for rule, block in summary["routes"].items():
        lines.append(f"### {rule}: {block['strong_share']} of turns to strong")
        for combo, acc in block["combined"].items():
            lines.append(f"- {combo}: accuracy {acc['accuracy']} {acc['interval_95']} (n={acc['n']})")
    spend = summary["spend"]
    lines += ["", f"Spend: USD {spend['spent_usd']} over {spend['n']} live calls (cap {spend['cap_usd']})."]
    lines += ["", "## Notes"] + [f"- {note}" for note in summary["notes"]]
    return "\n".join(lines) + "\n"


def _measurement_report(summary: dict) -> str:
    from eval.report import render_measurement

    return render_measurement(summary)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Router evaluation: select on development, measure once.")
    parser.add_argument("command", choices=("select", "measure", "verify", "resolution", "calibrate", "train"))
    parser.add_argument("run_id")
    parser.add_argument("--record", action="store_true", help="call the live endpoint on a missing recording")
    parser.add_argument("--live", action="store_true", help="resolution only: live timing mode, every call is live")
    parser.add_argument("--cap", type=float, default=DEFAULT_CAP_USD, help="spend cap in USD for live calls")
    parser.add_argument("--strong", action="append", default=[], help="extra strong candidate (select only)")
    parser.add_argument("--prompt", default="v2", help="prompt version for calibrate (v2 or v3)")
    args = parser.parse_args(argv)
    if args.command == "select":
        summary = select(args.run_id, args.record, args.cap, extra_strong=tuple(args.strong))
        print(f"[select] froze {args.run_id}, spend USD {summary['spend']['spent_usd']}")
    elif args.command == "measure":
        summary = measure(args.run_id, args.record, args.cap)
        print(f"[measure] froze {args.run_id}, spend USD {summary['spend']['spent_usd']}")
    elif args.command == "resolution":
        summary = resolution(args.run_id, args.record, args.cap, live_mode=args.live)
        print(f"[resolution] froze {args.run_id}, spend USD {summary['spend']['spent_usd']}")
    elif args.command == "train":
        from eval import train as training

        summary = training.train(args.run_id)
        print(f"[train] froze {args.run_id}, validation accuracy {summary['validation']['selected']['accuracy']}")
    elif args.command == "calibrate":
        summary = calibrate(args.run_id, args.record, args.cap, prompt=args.prompt)
        print(f"[calibrate] froze {args.run_id}, spend USD {summary['spend']['spent_usd']}")
    else:
        same = verify(args.run_id)
        print(f"[verify] {args.run_id}: {'matches' if same else 'DIFFERS from'} the frozen summary")
        sys.exit(0 if same else 1)


if __name__ == "__main__":
    main()


__all__ = ["SelectionReadsHeldOut", "calibrate", "main", "measure", "resolution", "select", "verify"]
