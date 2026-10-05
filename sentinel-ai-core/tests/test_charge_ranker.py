import json
from datetime import date

import pytest

from app.ai import charge_ranker as ranker
from app.ai.number_words import number_to_words, words_to_numbers
from app.orchestrator.types import Candidate, TransactionStatus

TODAY = date(2026, 6, 17)


def _row(candidate_id: str, amount: str, merchant: str, day: str) -> Candidate:
    return Candidate(candidate_id, TransactionStatus.APPROVED, amount, "USD", merchant, day, "2026-06-17")


POOL = [
    _row("a", "320.00", "Cafe Central", "2026-06-12"),
    _row("b", "1000.00", "ACME Store", "2026-06-10"),
    _row("c", "1000.00", "UNSPECIFIED", "2026-06-05"),
    _row("d", "750.00", "ACME Store", "2026-06-08"),
]


def _model(threshold: float = 0.0) -> ranker.ChargeRanker:
    weights = [0.0] * len(ranker.FEATURES)
    for name, value in {
        "amount_exact": 3.0, "words_match": 3.0, "merchant_exact": 2.0, "merchant_soft_all": 1.0,
        "date_exact": 2.0, "amount_mismatch": -2.0, "merchant_mismatch": -2.0, "date_mismatch": -1.0,
    }.items():
        weights[ranker.FEATURES.index(name)] = value
    return ranker.ChargeRanker(tuple(weights), 1.0, threshold)


def test_every_charge_gets_one_number_per_clue() -> None:
    rows = ranker.feature_matrix("cargo de 1000 en ACME Store", POOL, TODAY)
    assert len(rows) == len(POOL)
    assert all(len(row) == len(ranker.FEATURES) for row in rows)


def test_the_selector_ranks_the_charge_that_the_description_states() -> None:
    result = _model().rank("no reconozco el cargo de 1.000,00 en ACME Store del 10 de junio", POOL, TODAY)
    assert result.ordered[0].candidate_id == "b"
    assert result.pick is not None and result.pick.candidate_id == "b"


def test_an_amount_in_words_reaches_the_right_charge() -> None:
    text = f"cobro de {number_to_words(750, 'es')} en ACME"
    assert words_to_numbers(text) == [750]
    assert _model().rank(text, POOL, TODAY).ordered[0].candidate_id == "d"


def test_a_day_of_the_month_is_not_read_as_an_amount() -> None:
    description = ranker.read_description("cargo del 10 de junio en ACME Store", TODAY, ["ACME Store"])
    assert description.amount is None
    assert description.dates == frozenset({"2026-06-10"})


def test_the_selector_asks_when_it_is_not_sure() -> None:
    result = _model(threshold=0.999).rank("un cargo de 1000", POOL, TODAY)
    assert result.pick is None
    assert len(result.ordered) == len(POOL)


def test_an_empty_pool_gives_no_pick() -> None:
    assert _model().rank("cargo de 10", [], TODAY).pick is None


def _write(path, ranker_model: ranker.ChargeRanker) -> str:
    path.write_text(
        json.dumps({
            "features": list(ranker.FEATURES), "weights": list(ranker_model.weights),
            "temperature": 1.0, "threshold": 0.5,
        }),
        encoding="utf-8",
    )
    return ranker.file_hash(path)


def test_the_service_loads_a_model_file_with_the_recorded_hash(tmp_path) -> None:
    digest = _write(tmp_path / "model.json", _model())
    assert ranker.load_ranker(tmp_path / "model.json", digest).threshold == 0.5


def test_the_service_refuses_a_changed_model_file(tmp_path) -> None:
    digest = _write(tmp_path / "model.json", _model())
    (tmp_path / "model.json").write_text((tmp_path / "model.json").read_text() + " ", encoding="utf-8")
    with pytest.raises(ranker.RankerHashMismatch):
        ranker.load_ranker(tmp_path / "model.json", digest)


def _run_dir(tmp_path, tamper: bool = False):
    digest = _write(tmp_path / "model.json", _model())
    (tmp_path / "summary.json").write_text(json.dumps({"model_sha256": digest}), encoding="utf-8")
    if tamper:
        (tmp_path / "model.json").write_text((tmp_path / "model.json").read_text() + " ", encoding="utf-8")
    return tmp_path


def test_the_switch_is_off_by_default(monkeypatch) -> None:
    monkeypatch.delenv(ranker.SWITCH, raising=False)
    assert ranker.enabled() is False
    assert ranker.selector_from_env() is None


def test_the_switch_loads_the_frozen_model_when_on(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(ranker.SWITCH, "on")
    monkeypatch.setenv(ranker.RUN_DIR, str(_run_dir(tmp_path)))
    assert ranker.selector_from_env() is not None


def test_the_switch_refuses_a_changed_file_when_on(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(ranker.SWITCH, "on")
    monkeypatch.setenv(ranker.RUN_DIR, str(_run_dir(tmp_path, tamper=True)))
    with pytest.raises(ranker.RankerHashMismatch):
        ranker.selector_from_env()


def test_the_loop_does_not_import_the_selector_yet() -> None:
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "app" / "orchestrator" / "step.py").read_text(encoding="utf-8")
    assert "charge_ranker" not in source
