"""Report validation and write-once freeze."""

import pytest

from eval.metrics import system_metrics
from eval.report import build_summary, freeze_run, render_resolution, validate_has_n


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


def test_resolution_report_carries_the_breakdown() -> None:
    def _turn(turn_id: str, variant: str, country: str, outcome: str):  # type: ignore[no-untyped-def]
        return {
            "id": turn_id, "locale": "es-419", "country": country, "variant": variant,
            "situation": "s1", "outcome": outcome, "requires_handoff": False,
            "must_not_pass": False, "fault": "none", "latency_ms": 5.0, "cost_usd": 0.001,
        }

    baseline_turns = [_turn("mx-1", "es-MX", "MX", "case_confirmation"),
                      _turn("mx-2", "es-MX", "MX", "clarification")]
    router_turns = [_turn("mx-1", "es-MX", "MX", "case_confirmation"),
                    _turn("mx-2", "es-MX", "MX", "case_confirmation")]
    summary = {
        "run_id": "test-resolution",
        "kind": "resolution",
        "eval_version": "test",
        "n": 2,
        "situations": {"n": 1, "ids": ["s1"]},
        "case_mix": {"n": 2},
        "system": {"baseline": system_metrics(baseline_turns),
                   "router_v2": system_metrics(router_turns)},
        "paired_resolution": {"n": 2, "fixed": ["mx-2"], "broken": [],
                              "net": 1, "net_share": 0.5,
                              "interval_95": [0.0, 1.0], "above_zero": False},
        "spend": {"n": 0, "cap_usd": 0.45, "spent_usd": 0.0, "capped": False},
        "prices": "test",
        "measured_commit": "abc123",
        "notes": [],
    }
    validate_has_n(summary)
    report = render_resolution(summary)
    assert "## Breakdown by language variant" in report
    assert "## Breakdown by account country" in report
    assert "es-MX" in report and "MX" in report
    # Every number in the breakdown is read from the summary.
    assert "| es-MX | router_v2 | 2 of 2 |" in report
    assert "| es-MX | baseline | 1 of 2 |" in report
    assert "not broken down by customer segment" in report
