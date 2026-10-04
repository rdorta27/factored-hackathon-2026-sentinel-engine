"""Case set loading, splits and label provenance."""

from pathlib import Path

import pytest

from eval.cases import base_of, check_splits, load_cases, load_dir, load_labels, validate_case

CASES_DIR = Path(__file__).parent.parent / "eval" / "cases"
RESOLUTION = CASES_DIR / "resolution.jsonl"
LABELS = Path(__file__).parent.parent / "eval" / "labels.json"
EXAMPLES = Path(__file__).parent.parent / "eval" / "examples_v2.json"


def _resolution():  # type: ignore[no-untyped-def]
    return load_cases(RESOLUTION)


def test_missing_label_fails_naming_the_id() -> None:
    with pytest.raises(ValueError, match="no-label-case"):
        validate_case({"id": "no-label-case", "locale": "es-419"}, "test")


def test_splits_share_no_case_id() -> None:
    cases = load_dir(CASES_DIR) + load_dir(CASES_DIR / "sealed")
    assert cases, "the case set must not be empty"
    check_splits(cases)
    assert {c.id for c in cases if c.split == "development"}


def test_validation_split_is_carved_from_development_by_base() -> None:
    import json

    cases = load_dir(CASES_DIR) + load_dir(CASES_DIR / "sealed")
    check_splits(cases)
    development = [c for c in cases if c.split == "development"]
    validation = [c for c in cases if c.split == "validation"]
    assert development and validation, "both splits must exist"
    dev_bases = {base_of(c) for c in development}
    val_bases = {base_of(c) for c in validation}
    assert not (dev_bases & val_bases), "a base cannot sit on two sides"
    assert abs(len(val_bases) / (len(dev_bases) + len(val_bases)) - 0.2) < 0.05
    assert {c.expected_intent for c in validation} == {"charge", "missing", "out_of_scope", "person"}
    # Every variant of a validation base is on the validation side.
    variants = [c for c in cases if c.base_id in val_bases]
    assert variants and all(c.split == "validation" for c in variants)
    # The prompt-v2 examples keep their declared development provenance.
    example_ids = set(json.loads(EXAMPLES.read_text(encoding="utf-8"))["ids"])
    example_cases = [c for c in cases if c.id in example_ids]
    assert example_cases and all(c.split == "development" for c in example_cases)
    # The prompt-v3 examples are a full matrix that stays in development too.
    v3_ids = set(json.loads(EXAMPLES.parent.joinpath("examples_v3.json").read_text(encoding="utf-8"))["ids"])
    assert len(v3_ids) == 32, len(v3_ids)
    v3_cases = [c for c in cases if c.id in v3_ids]
    assert len(v3_cases) == 32 and all(c.split == "development" for c in v3_cases)


def test_check_splits_rejects_a_base_in_two_splits() -> None:
    development = validate_case(_body(id="v-1", split="development"), "test")
    validation = validate_case(_body(id="v-2", split="validation"), "test")
    with pytest.raises(ValueError, match="base b-01"):
        check_splits([development, validation])


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
    assert {"charge", "missing", "out_of_scope", "person"} <= {c.expected_intent for c in cases}


def test_v3_development_cases_cover_openers_status_subtypes_and_slots() -> None:
    cases = [c for c in load_dir(CASES_DIR) if c.id.startswith("v3-")]
    assert len(cases) == 60, len(cases)
    assert all(c.split == "development" for c in cases)
    assert {c.variant for c in cases} == {"es-MX", "es-CO", "es-AR", "pt-BR"}
    assert {c.expected_subtype for c in cases} >= {"greeting", "loan", "balance"}
    assert any(c.expected_intent == "status" for c in cases)
    assert any((c.expected_slots or {}).get("amount") == 1000 for c in cases)
    assert all(c.base_id is not None for c in cases)


def test_v3_bases_stay_out_of_the_validation_split() -> None:
    cases = load_dir(CASES_DIR) + load_dir(CASES_DIR / "sealed")
    check_splits(cases)
    v3_bases = {c.base_id for c in cases if c.id.startswith("v3-")}
    val_bases = {base_of(c) for c in cases if c.split == "validation"}
    assert v3_bases and not (v3_bases & val_bases)


def test_v3_subtype_and_slot_fields_are_validated() -> None:
    good = _body(split="development", base_id=None, variant=None)
    assert validate_case({**good, "expected_subtype": "loan", "expected_intent": "out_of_scope"}, "test")
    with pytest.raises(ValueError, match="subtype"):
        validate_case({**good, "expected_subtype": "loan", "expected_intent": "missing"}, "test")
    with pytest.raises(ValueError, match="subtype"):
        validate_case({**good, "expected_subtype": "loan", "expected_intent": "charge"}, "test")
    with pytest.raises(ValueError, match="amount"):
        validate_case({**good, "expected_slots": {"amount": "mil"}}, "test")


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


def test_resolution_set_has_situations_with_four_cases_each() -> None:
    cases = _resolution()
    check_splits(cases)
    assert 48 <= len(cases) <= 64, len(cases)
    situations = {c.base_id for c in cases}
    assert 12 <= len(situations) <= 16, len(situations)
    for base in situations:
        assert len([c for c in cases if c.base_id == base]) == 4, base


def test_resolution_set_covers_resolve_and_refuse() -> None:
    cases = _resolution()
    outcomes = {c.expected_outcome for c in cases}
    assert {"case_confirmation", "text", "handoff"} <= outcomes
    eligible = [c for c in cases if c.expected_outcome == "case_confirmation"]
    assert eligible and all(c.confirm and not c.must_not_pass for c in eligible)
    refused = [c for c in cases if c.must_not_pass]
    assert refused and all(not c.confirm for c in refused)
    assert {c.expected_rule for c in refused} >= {
        "window.expired", "status.reversed", "already.disputed",
        "amount.high", "fraud.score", "fraud.claim",
    }


def test_resolution_ids_do_not_overlap_the_other_sets() -> None:
    resolution = _resolution()
    others = load_dir(CASES_DIR) + load_dir(CASES_DIR / "sealed")
    assert not ({c.id for c in resolution} & {c.id for c in others})


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
