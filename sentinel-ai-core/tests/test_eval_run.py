"""Selection and measurement guards: development only, sealed once, offline by default."""

import json
from pathlib import Path

import pytest

from eval import run
from eval.seal import SealRefused


def _row(case_id: str, split: str) -> dict:
    return {
        "id": case_id, "locale": "es-419", "country": "MX", "turns": [f"texto {case_id}"],
        "expected_intent": "charge", "expected_outcome": "clarification", "split": split,
    }


def test_selection_fails_on_a_held_out_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "dev.jsonl").write_text(
        json.dumps(_row("dev-1", "development")) + "\n" + json.dumps(_row("ho-9", "held_out")) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(run, "CASES_DIR", tmp_path)
    called = []
    monkeypatch.setattr(run, "live_transport", lambda *a: called.append(a) or (None, ""))
    with pytest.raises(run.SelectionReadsHeldOut, match="ho-9"):
        run.select("test-select", freeze=False)
    assert called == []


def test_selection_replays_offline_without_recordings(monkeypatch: pytest.MonkeyPatch) -> None:
    def _no_network(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("no connection may be opened")

    monkeypatch.setattr("httpx.Client.post", _no_network)
    summary = run.select("test-select", record=False, freeze=False)
    assert summary["split"] == "development"
    assert summary["spend"]["n"] == 0
    for block in summary["candidates"].values():
        assert block["n"] == summary["n"]
    assert set(summary["routes"]) == {"heuristic", "keyword_miss", "strong"}


def _point(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(run, "SEALED_DIR", tmp_path / "sealed")
    monkeypatch.setattr(run, "SEAL_PATH", tmp_path / "seal.json")
    monkeypatch.setattr(run, "MEASURED_PATH", tmp_path / "measured.json")
    (tmp_path / "sealed").mkdir()
    (tmp_path / "sealed" / "held_out.jsonl").write_text(json.dumps(_row("ho-1", "held_out")) + "\n", encoding="utf-8")


def test_measure_refuses_an_unsealed_set(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _point(monkeypatch, tmp_path)
    with pytest.raises(SealRefused, match="no seal record"):
        run.measure("test-eval")


def test_measure_refuses_a_second_measurement(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from eval.seal import content_hash, record_measured

    _point(monkeypatch, tmp_path)
    digest = content_hash(tmp_path / "sealed")
    (tmp_path / "seal.json").write_text(json.dumps({"hash": digest}), encoding="utf-8")
    record_measured(digest, "2024Q4-eval-v7", tmp_path / "measured.json")
    monkeypatch.setattr(run, "_held_out_summary", lambda *a: pytest.fail("no model call after a refusal"))
    with pytest.raises(SealRefused, match="2024Q4-eval-v7"):
        run.measure("2024Q4-eval-v8")


def test_measurement_summary_builds_offline_on_a_small_sealed_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from eval.report import render_measurement, validate_has_n

    variants = {"es-MX": ("es-419", "MX"), "es-CO": ("es-419", "CO"), "es-AR": ("es-419", "AR"), "pt-BR": ("pt-BR", "MX")}
    rows = []
    for b in range(2):
        for variant, (locale, country) in variants.items():
            rows.append({**_row(f"b{b}-{variant}", "held_out"), "locale": locale, "country": country,
                         "base_id": f"b{b}", "variant": variant})
    rows.append({**rows[0], "id": "n-1", "tags": ["noisy"], "perturbation": "amount_shift"})
    rows.append({**_row("a-1", "held_out"), "tags": ["adversarial"], "must_not_pass": True})
    rows.append({**_row("a-2", "held_out"), "tags": ["adversarial"], "fault": "tool_failure"})
    _point(monkeypatch, tmp_path)
    (tmp_path / "sealed" / "held_out.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8"
    )
    examples = tmp_path / "examples_v2.json"
    examples.write_text(json.dumps({"ids": ["dev-oos-01"]}), encoding="utf-8")
    monkeypatch.setattr(run, "EXAMPLES_PATH", examples)
    monkeypatch.setenv("SENTINEL_LLM_CHEAP_MODEL", "accounts/fireworks/models/gpt-oss-120b")
    monkeypatch.setenv("SENTINEL_LLM_STRONG_MODEL", "accounts/fireworks/models/deepseek-v4p1-flash")
    summary = run._held_out_summary("test-eval", False, 0.45, {"hash": "0" * 64})
    validate_has_n(summary)
    assert set(summary["component"]["versions"]) == {"baseline", "router_v1", "router_v2"}
    assert summary["attacks"]["code_decided"]["ids"] == ["a-2"]
    assert summary["noisy"]["n"] == 1
    assert summary["examples_v2"]["ids"] == ["dev-oos-01"]
    assert "test-eval" in render_measurement(summary)


def test_measurement_report_shows_variant_paired_and_stability_sections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from eval.report import render_measurement

    test_measurement_summary_builds_offline_on_a_small_sealed_set(tmp_path, monkeypatch)
    summary = run._held_out_summary("test-eval", False, 0.45, {"hash": "0" * 64})
    report = render_measurement(summary)
    for heading in ("## Accuracy by version", "## Paired comparisons", "## By variant", "## Stability",
                    "## Noisy twins", "## Safety and system"):
        assert heading in report
    assert "router_v2_vs_baseline" in report
    assert "es-AR: accuracy" in report
    # Every number in the report is read from the summary.
    overall = summary["component"]["versions"]["baseline"]["breakdown"]["overall"]
    assert f"| baseline | {overall['accuracy']} |" in report


def test_resolution_run_builds_offline_with_a_model_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.ai.demo import DemoModel
    from eval.report import render_resolution

    def _no_network(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("no connection may be opened")

    monkeypatch.setattr("httpx.Client.post", _no_network)
    summary = run.resolution(
        "test-resolution",
        record=False,
        freeze=False,
        router_factory=lambda: DemoModel(),
        recordings_dir=tmp_path / "recordings",
    )
    assert summary["kind"] == "resolution"
    assert summary["n"] == 56
    assert summary["situations"]["n"] == 14
    assert summary["spend"]["n"] == 0
    for name, block in summary["system"].items():
        assert block["safe_resolution"]["resolved"] == 16, name
        assert block["unsafe_outcomes"]["count"] == 0, name
        assert block["escalation_quality"]["missed_transfers"] == [], name
    assert summary["paired_resolution"]["net"] == 0
    report = render_resolution(summary)
    assert "simulation over a mock store" in report
    assert "n=56 cases in 14 situations" in report
    assert "R1 safe: PASS" in report
    assert "| router_v2 | 16 of 56 |" in report


def _calibration_row(confidence, correct: bool, index: int) -> dict:
    return {
        "id": f"c-{index}",
        "base_id": None,
        "split": "validation",
        "expected": "charge",
        "predicted": "charge" if correct else "missing",
        "confidence": confidence,
    }


def test_calibration_chooses_cutoffs_on_validation() -> None:
    rows = [
        _calibration_row(0.60, True, 1),
        _calibration_row(0.70, False, 2),
        _calibration_row(0.80, True, 3),
        _calibration_row(0.95, True, 4),
        _calibration_row(0.99, True, 5),
    ]
    cutoffs = run._choose_cutoffs(rows)
    assert cutoffs["t_act"] == 0.80
    assert cutoffs["t_abstain"] == 0.0
    block = run._split_report(rows, cutoffs["t_act"], cutoffs["t_abstain"])
    assert block["actions"]["acted"] == {"n": 3, "share": 0.6}
    assert block["actions"]["clarified"] == {"n": 2, "share": 0.4}
    assert block["actions"]["abstained"] == {"n": 0, "share": 0.0}
    assert block["bands"]["0.60-0.70"]["accuracy"] == 1.0


def test_calibration_without_confidence_abstains_from_choosing() -> None:
    rows = [_calibration_row(None, False, 1)]
    cutoffs = run._choose_cutoffs(rows)
    assert (cutoffs["t_act"], cutoffs["t_abstain"]) == (1.0, 0.0)
    assert run._split_report(rows, 1.0, 0.0)["actions"]["abstained"]["n"] == 1


def test_verify_ignores_spend_and_latency_only() -> None:
    a = {"spend": {"n": 3}, "x": {"latency_ms": {"p50": 1.0}, "accuracy": 0.9}}
    b = {"spend": {"n": 0}, "x": {"latency_ms": {"p50": 900.0}, "accuracy": 0.9}}
    assert run._comparable(a) == run._comparable(b)
    b["x"]["accuracy"] = 0.8
    assert run._comparable(a) != run._comparable(b)
