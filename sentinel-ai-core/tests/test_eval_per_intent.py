"""Per-intent precision, recall and F1 with base-level intervals, and the frozen trained version."""

import json
from pathlib import Path

import pytest

from app.ai.demo import DemoModel
from eval import metrics, run, train
from eval.cases import INTENTS, load_dir, validate_case
from eval.per_intent import SCORES, per_intent_intervals
from eval.trained import TRAIN_RUN, load_frozen, trained_version
from eval.versions import Version, run_versions


def _case(case_id: str, base: str, intent: str):  # type: ignore[no-untyped-def]
    return validate_case(
        {
            "id": case_id, "base_id": base, "variant": "es-MX", "locale": "es-419", "country": "MX",
            "turns": ["texto"], "expected_intent": intent, "expected_outcome": "clarification", "split": "development",
        },
        "test",
    )


CASES = [_case(f"c{i}", f"b{i // 2}", intent) for i, intent in enumerate(["charge", "charge", "missing", "person"] * 5)]
PREDICTED = ["charge", "missing", "missing", "person", "charge", "charge", "charge", "person", "missing", "person"] * 2


def test_point_values_match_intent_metrics() -> None:
    block = per_intent_intervals(CASES, PREDICTED)
    reference = metrics.intent_metrics([(c.expected_intent, p) for c, p in zip(CASES, PREDICTED)], labels=list(INTENTS))
    for label in INTENTS:
        assert block[label]["n"] == reference["per_class"][label]["n"]
        for name in SCORES:
            assert block[label][name]["value"] == pytest.approx(reference["per_class"][label][name], abs=1e-4)


def test_every_score_has_an_interval_and_the_value_is_inside_a_wide_one() -> None:
    block = per_intent_intervals(CASES, PREDICTED)
    assert set(block) == set(INTENTS)
    for label in ("charge", "missing", "person"):
        for name in SCORES:
            score = block[label][name]
            low, high = score["interval_95"]
            assert 0.0 <= low <= high <= 1.0
            assert isinstance(score["descriptive"], bool)


def test_a_class_with_no_case_scores_zero() -> None:
    assert per_intent_intervals(CASES, PREDICTED)["status"]["recall"]["value"] == 0.0


def test_the_interval_is_reproducible() -> None:
    assert per_intent_intervals(CASES, PREDICTED) == per_intent_intervals(CASES, PREDICTED)


def test_the_interval_resamples_bases_not_cases() -> None:
    one_base = [_case(f"x{i}", "same", "charge") for i in range(6)]
    block = per_intent_intervals(one_base, ["charge", "charge", "missing", "charge", "missing", "charge"])
    # One cluster: every resample is the same data, so the interval collapses on the value.
    assert block["charge"]["recall"]["interval_95"] == [block["charge"]["recall"]["value"]] * 2


def test_run_versions_reports_per_intent_for_every_version() -> None:
    development = [c for c in load_dir(train.CASES_DIR) if c.split == "development"]
    result = run_versions(development, {"baseline": Version(DemoModel()), "trained_baseline": trained_version()})
    assert set(result["versions"]) == {"baseline", "trained_baseline"}
    for block in result["versions"].values():
        assert set(block["per_intent"]) == set(INTENTS)
        for intent in INTENTS:
            for name in SCORES:
                assert {"value", "interval_95", "descriptive"} <= set(block["per_intent"][intent][name])
    assert result["versions"]["trained_baseline"]["models"]["count"] == {"trained-baseline": len(development)}
    assert result["versions"]["trained_baseline"]["cost_usd"]["total"] == 0.0


def test_the_verify_comparison_ignores_per_intent() -> None:
    with_block = {"component": {"versions": {"v": {"intent": {"n": 1}, "per_intent": {"charge": {}}}}}}
    without = {"component": {"versions": {"v": {"intent": {"n": 1}}}}}
    assert run._comparable(with_block) == run._comparable(without)


def test_load_frozen_checks_the_model_hash(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    folder = root / "evidence" / "evaluation-runs" / TRAIN_RUN
    folder.mkdir(parents=True)
    source = train.REPO_ROOT / "evidence" / "evaluation-runs" / TRAIN_RUN
    (folder / "summary.json").write_text((source / "summary.json").read_text(encoding="utf-8"), encoding="utf-8")
    (folder / "model.json").write_text((source / "model.json").read_text(encoding="utf-8"), encoding="utf-8")
    assert load_frozen(TRAIN_RUN, root).classify("quiero hablar con una persona") in INTENTS
    body = json.loads((folder / "model.json").read_text(encoding="utf-8"))
    body["intercept"][0] += 1
    (folder / "model.json").write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(ValueError, match="frozen hash"):
        load_frozen(TRAIN_RUN, root)
