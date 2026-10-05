import subprocess
import sys
from datetime import date
from pathlib import Path

from app.ai import charge_ranker as ranker
from app.orchestrator.types import Candidate, TransactionStatus
from eval import charge_examples as gen
from eval import eval_charge_ranker as ev

CORE = Path(__file__).resolve().parents[1]
TODAY = date(2026, 6, 17)


def _row(candidate_id: str, amount: str, merchant: str, day: str) -> Candidate:
    return Candidate(candidate_id, TransactionStatus.APPROVED, amount, "USD", merchant, day, "2026-06-17")


POOL = [
    _row("a", "320.00", "Cafe Central", "2026-06-12"),
    _row("b", "1000.00", "ACME Store", "2026-06-10"),
    _row("c", "750.00", "ACME Store", "2026-06-08"),
]


def test_evaluation_does_not_import_the_training_module() -> None:
    code = "import sys, eval.eval_charge_ranker; sys.exit('eval.train_charge_ranker' in sys.modules)"
    assert subprocess.run([sys.executable, "-c", code], cwd=CORE).returncode == 0
    assert "train_charge_ranker" not in (CORE / "eval" / "eval_charge_ranker.py").read_text(encoding="utf-8")


def test_the_current_rules_pick_one_exact_match_and_ask_otherwise() -> None:
    ordered, pick = ev.rules_fixed("cargo de 1000.00 en ACME Store", TODAY, POOL)
    assert pick is not None and pick.candidate_id == "b"
    ordered, pick = ev.rules_fixed("un cargo en ACME Store", TODAY, POOL)
    assert pick is None and {row.candidate_id for row in ordered[:2]} == {"b", "c"}


def test_the_rules_miss_an_amount_in_words_and_the_selector_keeps_it() -> None:
    weights = [0.0] * len(ranker.FEATURES)
    weights[ranker.FEATURES.index("words_match")] = 4.0
    model = ranker.ChargeRanker(tuple(weights), 1.0, 0.0)
    text = "cobro de setecientos cincuenta"
    assert ev.rules_fixed(text, TODAY, POOL)[1] is None
    ordered, pick = ev.learned(model)(text, TODAY, POOL)
    assert ordered[0].candidate_id == "c" and pick is not None


def test_the_score_counts_wrong_automatic_picks_and_asks() -> None:
    assert ev._score(POOL, POOL[0], "b")["wrong_automatic"] is True
    assert ev._score(POOL, None, "b") == {
        "right_first": False, "right_in_top3": True, "wrong_automatic": False, "asks": True,
    }


def test_a_block_reports_counts_and_a_range_for_each_metric() -> None:
    example = gen.Example("CX-1", "CLI-1", "b", "2026-06-17", "es-419", "direct", "test", "t", True, False)
    other = gen.Example("CX-2", "CLI-2", "b", "2026-06-17", "pt-BR", "direct", "test", "t", False, False)
    out = ev.block([(example, ev._score(POOL, None, "a")), (other, ev._score(POOL, POOL[0], "b"))])
    assert out["n"] == 2
    assert out["right_first"]["count"] == 1
    low, high = out["right_first"]["range_95"]
    assert low <= out["right_first"]["rate"] <= high
