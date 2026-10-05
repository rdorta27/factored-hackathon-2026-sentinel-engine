"""v8 measurement guards and the verdict (eval-v8-measure tasks 1.2 and 1.4)."""

import json
from pathlib import Path

import pytest

from app.ai.transport import LLMResponse
from eval import measure_v8
from eval.budget import CappedTransport, SpendCapReached
from eval.seal import SealRefused, content_hash

REPLY = json.dumps({"kind": "charge", "language": "es-419", "not_mine": False})


class FakeLive:
    """A live transport with a fixed reply and a fixed cost per call."""

    def __init__(self, cost: float = 0.0) -> None:
        self.cost = cost
        self.calls = 0

    def complete(self, *, model, messages, temperature=0.0):  # type: ignore[no-untyped-def]
        self.calls += 1
        return LLMResponse(content=REPLY, cost_usd=self.cost, tokens_in=10, tokens_out=5)


def _case(case_id: str, split: str, variant=None, base_id=None, tags=(), **extra) -> dict:
    row = {
        "id": case_id,
        "locale": "es-419",
        "country": "MX",
        "turns": [f"texto {case_id}"],
        "expected_intent": "charge",
        "expected_outcome": "clarification",
        "split": split,
    }
    if variant:
        row["variant"] = variant
        row["base_id"] = base_id
        row["locale"] = "pt-BR" if variant == "pt-BR" else "es-419"
        row["country"] = {"es-MX": "MX", "es-CO": "CO", "es-AR": "AR"}.get(variant, "MX")
    if tags:
        row["tags"] = list(tags)
    row.update(extra)
    return row


def _main_rows() -> list[dict]:
    rows = []
    for base in ("b0", "b1"):
        for variant in ("es-MX", "es-CO", "es-AR", "pt-BR"):
            rows.append(_case(f"{base}-{variant}", "held_out", variant, base))
    return rows


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cases = tmp_path / "cases"
    cases.mkdir()
    (cases / "dev.jsonl").write_text(
        json.dumps(_case("dev-1", "development")) + "\n", encoding="utf-8"
    )
    (tmp_path / "examples_v2.json").write_text(json.dumps({"ids": []}), encoding="utf-8")
    (tmp_path / "examples_v3.json").write_text(json.dumps({"ids": []}), encoding="utf-8")

    sealed = tmp_path / "sealed_v8"
    sealed.mkdir()
    (sealed / "intent.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in _main_rows()), encoding="utf-8"
    )
    (sealed / "noisy.jsonl").write_text(
        json.dumps(_case("n-0", "held_out", "es-MX", "b0", ["noisy"], perturbation="amount_shift")) + "\n",
        encoding="utf-8",
    )
    (sealed / "attacks.jsonl").write_text(
        json.dumps(_case("a-0", "held_out", tags=["adversarial"], must_not_pass=True)) + "\n"
        + json.dumps(_case("a-1", "held_out", tags=["adversarial"], fault="tool_failure")) + "\n",
        encoding="utf-8",
    )
    (sealed / "seal.json").write_text(
        json.dumps({"hash": content_hash(sealed), "n": 11}), encoding="utf-8"
    )

    topup = tmp_path / "sealed_v8b"
    topup.mkdir()
    (topup / "topup.jsonl").write_text(
        "".join(json.dumps(_case(f"t-{v}", "held_out", v, "tb0")) + "\n"
                for v in ("es-MX", "es-CO", "es-AR", "pt-BR")),
        encoding="utf-8",
    )
    (topup / "seal.json").write_text(
        json.dumps({"hash": content_hash(topup), "n": 4}), encoding="utf-8"
    )

    measured = tmp_path / "measured.json"
    measured.write_text(json.dumps({"measured": []}), encoding="utf-8")

    monkeypatch.setattr(measure_v8, "CASES_DIR", cases)
    monkeypatch.setattr(measure_v8, "EXAMPLES_V2_PATH", tmp_path / "examples_v2.json")
    monkeypatch.setattr(measure_v8, "EXAMPLES_V3_PATH", tmp_path / "examples_v3.json")
    monkeypatch.setattr(measure_v8, "SEALED_V8_DIR", sealed)
    monkeypatch.setattr(measure_v8, "SEALED_V8_SEAL", sealed / "seal.json")
    monkeypatch.setattr(measure_v8, "SEALED_V8B_DIR", topup)
    monkeypatch.setattr(measure_v8, "SEALED_V8B_SEAL", topup / "seal.json")
    monkeypatch.setattr(measure_v8, "MEASURED_PATH", measured)
    monkeypatch.setattr(measure_v8, "RECORDINGS_DIR", tmp_path / "recordings")
    monkeypatch.setattr(measure_v8, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(measure_v8, "_env", lambda: {
        "base_url": "http://test", "api_key": "test-key", "cheap": "m", "strong": "m",
        "default": "m", "route_rule": "heuristic", "max_tokens": 400,
    })


def _freeze_into(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list:
    written = []

    def _freeze(repo_root, run_id, summary, report_md):
        written.append(summary)
        folder = Path(repo_root) / "evidence" / "evaluation-runs" / run_id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        (folder / "report.md").write_text(report_md, encoding="utf-8")
        return folder

    monkeypatch.setattr(measure_v8, "freeze_run", _freeze)
    return written


def test_measure_refuses_a_second_measurement(tmp_path, monkeypatch) -> None:
    _setup(tmp_path, monkeypatch)
    digest = json.loads((tmp_path / "sealed_v8" / "seal.json").read_text())["hash"]
    (tmp_path / "measured.json").write_text(
        json.dumps({"measured": [{"hash": digest, "run_id": "2024Q4-eval-v8"}]}), encoding="utf-8"
    )
    monkeypatch.setattr(measure_v8, "_live", lambda *a: pytest.fail("no call after a refusal"))
    with pytest.raises(SealRefused, match="2024Q4-eval-v8"):
        measure_v8.measure("2024Q4-eval-v8")


def test_measure_refuses_a_modified_seal(tmp_path, monkeypatch) -> None:
    _setup(tmp_path, monkeypatch)
    (tmp_path / "sealed_v8" / "intent.jsonl").write_text(
        json.dumps(_case("ho-x", "held_out")) + "\n", encoding="utf-8"
    )
    with pytest.raises(SealRefused, match="changed after sealing"):
        measure_v8.measure("2024Q4-eval-v8")


def test_measure_stops_at_the_cap_and_leaves_measured_unchanged(tmp_path, monkeypatch) -> None:
    _setup(tmp_path, monkeypatch)
    monkeypatch.setattr(measure_v8, "_live", lambda env, cap: CappedTransport(FakeLive(0.1), cap_usd=0.0))
    with pytest.raises(SpendCapReached):
        measure_v8.measure("2024Q4-eval-v8", record=True, cap_usd=0.0)
    assert json.loads((tmp_path / "measured.json").read_text())["measured"] == []
    assert not (tmp_path / "evidence").exists()


def test_measure_freezes_then_records_both_hashes(tmp_path, monkeypatch) -> None:
    _setup(tmp_path, monkeypatch)
    written = _freeze_into(tmp_path, monkeypatch)
    monkeypatch.setattr(measure_v8, "_live", lambda env, cap: CappedTransport(FakeLive(0.0), cap_usd=cap))
    summary = measure_v8.measure("2024Q4-eval-v8", record=True, cap_usd=0.45)
    assert summary["kind"] == "held_out_measurement_v8"
    assert set(summary["candidates"]) == set(measure_v8.CANDIDATES)
    assert summary["case_mix"] == {"main": 8, "noisy": 1, "attacks": 2, "topup": 4}
    measured = json.loads((tmp_path / "measured.json").read_text())["measured"]
    assert len(measured) == 2 and len(written) == 1


def test_dry_run_reads_no_sealed_case_and_freezes_nothing(tmp_path, monkeypatch) -> None:
    _setup(tmp_path, monkeypatch)
    (tmp_path / "sealed_v8" / "seal.json").unlink()
    monkeypatch.setattr(measure_v8, "_live", lambda env, cap: CappedTransport(FakeLive(0.0), cap_usd=cap))
    summary = measure_v8.measure("2024Q4-eval-v8-dry", record=True, cap_usd=0.45, dry_run=True)
    assert summary["kind"] == "dry_run"
    assert summary["case_mix"]["main"] == 1
    assert not (tmp_path / "measured.json").read_text().count("hash")


def _fake_summary(unsafe_wording: int = 0, subtype: float = 1.0, d5_above_zero: bool = True,
                  kind: float = 0.99, worst_loss: int = 0) -> dict:
    def block() -> dict:
        return {
            "n": 100,
            "intent": {"accuracy": kind, "n": 100},
            "subtype": {"accuracy": subtype, "n": 40},
            "slots": {"precision": 1.0, "n": 10},
            "drafts": {"rate": 0.0, "n": 10, "rejected": 0, "returned": 10},
            "unsafe_wording": {"rate": f"{unsafe_wording}/10", "count": unsafe_wording, "n": 10, "cases": []},
            "cost_usd": {"total": 0.01, "n": 100},
            "latency_ms": {"p50": 1.0, "p95": 2.0, "n": 100},
            "stability": {"agreement": 1.0, "n": 20, "runs": 3, "recorded_repetitions": 3},
            "variant_losses": {"n": 25, "best": "es-MX", "by_variant": {
                v: {"n": 25, "accuracy": 0.9, "net_loss": worst_loss, "lost_bases": [], "won_bases": []}
                for v in ("es-MX", "es-CO", "es-AR", "pt-BR")
            }},
        }

    return {
        "candidates": {name: block() for name in measure_v8.CANDIDATES},
        "paired": {
            "router_v3_vs_router_v2": {"n": 100, "net": 1, "interval_95": [0.0, 0.1], "above_zero": False},
            "router_v3_vs_baseline": {"n": 100, "net": 10, "interval_95": [0.1, 0.2], "above_zero": d5_above_zero},
            "router_v2_vs_baseline": {"n": 100, "net": 9, "interval_95": [0.1, 0.2], "above_zero": True},
        },
        "attacks": {"n": 84, "candidates": {
            name: {**block(), "unsafe_wording": {"rate": "0/84", "count": 0, "n": 84, "cases": []}}
            for name in measure_v8.CANDIDATES
        }},
        "topup": {"n": 92, "candidates": {name: block() for name in measure_v8.CANDIDATES}},
    }


def test_verdict_serves_v3_when_every_gate_passes() -> None:
    result = measure_v8.verdict(_fake_summary())
    assert result["served"] == "router_v3"
    assert result["failed"] == []
    assert "Served choice: `router_v3`" in measure_v8.render_verdict(result)


def test_verdict_falls_back_to_v2_and_names_the_failed_gate() -> None:
    result = measure_v8.verdict(_fake_summary(unsafe_wording=1))
    assert result["served"] == "router_v2"
    assert "unsafe_wording" in result["failed"]
    assert "unsafe_wording" in measure_v8.render_verdict(result)


def test_verdict_fails_on_a_low_subtype_accuracy() -> None:
    result = measure_v8.verdict(_fake_summary(subtype=0.90))
    assert result["served"] == "router_v2"
    assert result["failed"] == ["subtype_accuracy"]
