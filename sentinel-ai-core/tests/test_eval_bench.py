"""Component benchmark over the identical case set, offline."""

from pathlib import Path

import pytest

from eval.bench_router import run_bench
from eval.cases import load_dir

CASES_DIR = Path(__file__).parent.parent / "eval" / "cases"
FIXTURES = Path(__file__).parent.parent / "app" / "ai" / "fixtures"


def test_both_models_ran_the_identical_set() -> None:
    cases = [c for c in load_dir(CASES_DIR) if c.split == "development" and c.fault == "none"]
    result = run_bench(cases, repetitions=2, fixtures_dir=FIXTURES)
    assert result["identical_set"] is True
    assert result["router"]["n"] == result["baseline"]["n"] == len(cases)
    assert set(result["router"]["intent"]["per_class"]) == {"charge", "missing", "out_of_scope", "person"}
    assert set(result["router"]["by_locale"]) == {"es-419", "pt-BR"}


def test_repeated_case_reports_agreement_and_variability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import httpx

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("no HTTP connection may be opened during the bench")

    monkeypatch.setattr("httpx.Client.post", _forbidden)
    cases = load_dir(CASES_DIR)[:4]
    result = run_bench(cases, repetitions=3, fixtures_dir=FIXTURES)
    stability = result["router"]["stability"]
    assert stability["runs"] == 3
    assert 0.0 <= stability["agreement"] <= 1.0
    assert result["router"]["latency_ms"]["n"] == 4 * 3
    assert result["router"]["cost_usd"]["n"] == 4 * 3
