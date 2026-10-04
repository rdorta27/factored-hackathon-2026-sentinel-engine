"""The MT-06 narrowing cases load, and the offline report matches the review."""

import json
from pathlib import Path

from eval.cases import load_cases
from eval.narrowing_report import CASES, report

REVIEW = Path(__file__).parents[1] / "eval" / "review" / "narrowing.md"


def test_narrowing_cases_load_as_four_variants() -> None:
    cases = load_cases(CASES)
    assert len(cases) == 24
    assert {case.variant for case in cases} == {"es-MX", "es-CO", "es-AR", "pt-BR"}
    bodies = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert all("expected_charge_ids" in body for body in bodies)


def test_offline_report_matches_the_review() -> None:
    numbers = report()
    assert numbers == {
        "n": 24,
        "before": {"right_charge_shown": "20/24", "not_found_said": "4/24"},
        "after": {"right_charge_shown": "24/24", "not_found_said": "24/24"},
    }
    text = REVIEW.read_text(encoding="utf-8")
    assert "20/24" in text and "24/24" in text
