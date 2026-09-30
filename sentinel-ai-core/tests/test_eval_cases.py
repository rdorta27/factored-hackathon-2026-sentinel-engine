"""Case set loading, splits and label provenance."""

from pathlib import Path

import pytest

from eval.cases import check_splits, load_dir, load_labels, validate_case

CASES_DIR = Path(__file__).parent.parent / "eval" / "cases"
LABELS = Path(__file__).parent.parent / "eval" / "labels.json"


def test_missing_label_fails_naming_the_id() -> None:
    with pytest.raises(ValueError, match="no-label-case"):
        validate_case({"id": "no-label-case", "locale": "es-419"}, "test")


def test_splits_share_no_case_id() -> None:
    cases = load_dir(CASES_DIR)
    assert cases, "the case set must not be empty"
    check_splits(cases)
    dev = {c.id for c in cases if c.split == "development"}
    held = {c.id for c in cases if c.split == "held_out"}
    assert dev and held


def test_both_locales_and_all_intents_present() -> None:
    cases = load_dir(CASES_DIR)
    assert {c.locale for c in cases} == {"es-419", "pt-BR"}
    assert {c.expected_intent for c in cases} == {"charge", "missing", "out_of_scope", "person"}


def test_labels_provenance_is_recorded() -> None:
    provenance = load_labels(LABELS)
    assert provenance.run_id.strip()
    assert provenance.summary_sha16.strip()
    assert provenance.claim_labels
