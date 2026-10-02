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
    cases = load_dir(CASES_DIR) + load_dir(CASES_DIR / "sealed")
    assert cases, "the case set must not be empty"
    check_splits(cases)
    assert {c.id for c in cases if c.split == "development"}


def test_working_dir_holds_no_held_out_case() -> None:
    # Held-out cases live only under eval/cases/sealed/, sealed by hash.
    assert not [c.id for c in load_dir(CASES_DIR) if c.split == "held_out"]


def test_retired_held_out_cases_are_not_sealed_again() -> None:
    import json

    retired = json.loads((CASES_DIR / "retired.json").read_text(encoding="utf-8"))["cases"]
    assert len(retired) == 10
    sealed = load_dir(CASES_DIR / "sealed")
    ids = {c.id for c in sealed}
    texts = {turn.strip().lower() for c in sealed for turn in c.turns}
    for case in retired:
        assert case["id"] not in ids
        assert not {t.strip().lower() for t in case["turns"]} & texts


def test_both_locales_and_all_intents_present() -> None:
    cases = load_dir(CASES_DIR)
    assert {c.locale for c in cases} == {"es-419", "pt-BR"}
    assert {c.expected_intent for c in cases} == {"charge", "missing", "out_of_scope", "person"}


def test_labels_provenance_is_recorded() -> None:
    provenance = load_labels(LABELS)
    assert provenance.run_id.strip()
    assert provenance.summary_sha16.strip()
    assert provenance.claim_labels


def _body(**extra):  # type: ignore[no-untyped-def]
    body = {
        "id": "v-1", "locale": "es-419", "country": "AR", "turns": ["che, no reconozco este débito"],
        "expected_intent": "charge", "expected_outcome": "clarification", "split": "held_out",
        "base_id": "b-01", "variant": "es-AR",
    }
    body.update(extra)
    return body


def test_variant_fields_are_loaded() -> None:
    case = validate_case(_body(), "test")
    assert (case.base_id, case.variant, case.perturbation) == ("b-01", "es-AR", None)
    pt = validate_case(_body(locale="pt-BR", country="MX", variant="pt-BR"), "test")
    assert pt.variant == "pt-BR"


@pytest.mark.parametrize(
    "extra",
    [{"locale": "pt-BR"}, {"country": "MX"}, {"base_id": None}, {"variant": "es-PE"}],
)
def test_variant_contradicting_locale_or_country_fails(extra) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError, match="v-1"):
        validate_case(_body(**extra), "test")


def test_confirm_field_is_loaded_and_defaults_false() -> None:
    assert validate_case(_body(), "test").confirm is False
    assert validate_case(_body(confirm=True), "test").confirm is True
    assert validate_case(_body(confirm=False), "test").confirm is False


def test_resolution_file_is_not_part_of_the_directory_load() -> None:
    # The resolution set is loaded explicitly; the development load never sees it.
    from eval.cases import RESOLUTION_FILE

    assert RESOLUTION_FILE == "resolution.jsonl"
    ids = {c.id for c in load_dir(CASES_DIR)}
    assert not any(case_id.startswith("res-") for case_id in ids)


def test_noisy_case_names_one_perturbation_and_its_base() -> None:
    case = validate_case(_body(tags=["noisy"], perturbation="amount_shift"), "test")
    assert case.perturbation == "amount_shift"
    with pytest.raises(ValueError, match="perturbation"):
        validate_case(_body(tags=["noisy"]), "test")
    with pytest.raises(ValueError, match="base_id"):
        validate_case(_body(tags=["noisy"], perturbation="date_shift", base_id=None, variant=None), "test")
    with pytest.raises(ValueError, match="not tagged noisy"):
        validate_case(_body(perturbation="date_shift"), "test")
