"""Report validation and write-once freeze."""

import pytest

from eval.report import build_summary, freeze_run, validate_has_n


def _summary(**overrides):  # type: ignore[no-untyped-def]
    base = {
        "run_id": "test-v1",
        "eval_version": "test",
        "created_at": "2026-09-30T00:00:00+00:00",
        "labels": {"n": 1, "run_id": "2024Q4-v1", "summary_sha16": "abc"},
        "case_mix": {"n": 2},
        "component": {"n": 2},
        "system": {"n": 2},
        "safety": {"n": 1},
        "automation": {"n": 2},
        "failures": [],
        "n": 2,
        "notes": [],
    }
    base.update(overrides)
    return base


def test_metric_without_n_is_rejected() -> None:
    with pytest.raises(ValueError, match="without n"):
        validate_has_n({"accuracy": 0.9})
    validate_has_n(_summary())


def test_second_freeze_refuses_overwrite(tmp_path) -> None:  # type: ignore[no-untyped-def]
    summary = _summary()
    first = freeze_run(tmp_path, "run-v1", summary, "# report\n")
    assert (first / "summary.json").is_file()
    assert (first / "report.md").is_file()
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        freeze_run(tmp_path, "run-v1", summary, "# report\n")
    second = freeze_run(tmp_path, "run-v2", summary, "# report\n")
    assert second.is_dir()
