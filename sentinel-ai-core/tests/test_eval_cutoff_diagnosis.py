"""Cut-off diagnosis: replay only, no live call (evidence-hardening task 4.4)."""

import pytest

from eval import cutoff_diagnosis


def _row(confidence, correct: bool, index: int) -> dict:
    return {
        "id": f"r-{index}",
        "split": "validation",
        "expected": "charge",
        "predicted": "charge" if correct else "missing",
        "confidence": confidence,
    }


def test_lowest_acting_threshold_returns_the_raw_value() -> None:
    rows = [
        _row(0.50, False, 1),
        _row(0.99998, True, 2),
        _row(0.99999, True, 3),
        _row(1.0, True, 4),
    ]
    # The rule needs accuracy >= 0.9321; the first acting threshold is 0.99998.
    assert cutoff_diagnosis.lowest_acting_threshold(rows) == 0.99998


def test_lowest_acting_threshold_none_when_no_threshold_meets_the_rule() -> None:
    rows = [_row(0.9, False, 1), _row(0.8, False, 2)]
    assert cutoff_diagnosis.lowest_acting_threshold(rows) is None


def test_diagnosis_replays_the_committed_recordings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_LLM_CHEAP_MODEL", "accounts/fireworks/models/glm-5p3-flash")
    monkeypatch.setenv("SENTINEL_LLM_STRONG_MODEL", "accounts/fireworks/models/glm-5p3-flash")
    monkeypatch.setenv("SENTINEL_LLM_DEFAULT_MODEL", "accounts/fireworks/models/glm-5p3-flash")
    summary = cutoff_diagnosis.diagnose("test-cutoff", freeze=False)
    validation = summary["validation"]
    assert validation["n"] == 26
    assert validation["with_confidence"] == 24
    assert validation["without_confidence"] == 2
    assert validation["lowest_threshold_raw"] == pytest.approx(0.99998456, abs=1e-7)
    assert validation["lowest_threshold_rounded"] == 1.0
    kind = summary["kind_accuracy"]
    assert kind["no_cutoffs"]["kind_accuracy"] == 0.9899
    assert kind["t_act_1_0"]["kind_accuracy"] == 0.5404
    assert kind["t_act_unrounded"]["kind_accuracy"] == 0.7778
    assert "0.9999845600455524" in cutoff_diagnosis.render(summary)
