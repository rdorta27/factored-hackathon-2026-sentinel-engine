"""Unit checks for the shared evaluation metrics."""

from eval.metrics import (
    automation_proxy,
    intent_metrics,
    safety_pass_rate,
    stability_agreement,
    system_metrics,
)


def test_intent_metrics_match_hand_computed_example() -> None:
    pairs = [("a", "a"), ("a", "b"), ("b", "b"), ("b", "a"), ("b", "b")]
    result = intent_metrics(pairs, labels=["a", "b"])
    assert result["n"] == 5
    assert result["accuracy"] == 0.6
    assert result["per_class"]["a"]["precision"] == round(1 / 2, 4)
    assert result["per_class"]["a"]["recall"] == round(1 / 2, 4)
    assert result["per_class"]["a"]["f1"] == 0.5
    assert result["per_class"]["b"]["support"] == 3
    assert result["confusion"]["a"]["b"] == 1
    assert result["confusion"]["b"]["a"] == 1


def test_safety_names_failures() -> None:
    outcomes = [
        {"id": "ok-1", "must_not_pass": True, "outcome": "clarification"},
        {"id": "bad-1", "must_not_pass": True, "outcome": "case_confirmation"},
        {"id": "plain", "must_not_pass": False, "outcome": "case_confirmation"},
    ]
    result = safety_pass_rate(outcomes)
    assert result["n"] == 2
    assert result["passed"] == 1
    assert result["failures"] == ["bad-1"]


def test_automation_and_stability_fixtures() -> None:
    outcomes = [
        {"id": "a", "outcome": "clarification", "fault": "none"},
        {"id": "b", "outcome": "handoff", "fault": "none"},
        {"id": "c", "outcome": "handoff", "fault": "gold_unavailable"},
    ]
    proxy = automation_proxy(outcomes)
    assert proxy["n"] == 2
    assert proxy["share"] == 0.5
    agreement = stability_agreement([["x", "y"], ["x", "z"], ["x", "y"]])
    assert agreement["n"] == 2
    assert agreement["runs"] == 3
    assert agreement["agreement"] == round((1.0 + 2 / 3) / 2, 4)


def test_system_metrics_undefined_cost_without_resolutions() -> None:
    turns = [
        {"id": "a", "outcome": "clarification", "requires_handoff": False,
         "must_not_pass": False, "fault": "none", "latency_ms": 10.0, "cost_usd": 0.001},
        {"id": "b", "outcome": "handoff", "requires_handoff": True,
         "must_not_pass": False, "fault": "none", "latency_ms": 20.0, "cost_usd": 0.002},
    ]
    result = system_metrics(turns)
    assert result["n"] == 2
    assert result["safe_resolution"]["resolved"] == 0
    assert result["cost_usd"]["per_resolution"] == "not defined"
    assert result["unsafe_outcomes"]["rate"] == "0/2"
    assert result["escalation_quality"]["missed_transfers"] == []
    assert result["latency_ms"]["p50"] == 15.0


def _vcase(case_id: str, base: str, variant: str, intent: str = "charge"):  # type: ignore[no-untyped-def]
    from eval.cases import Case

    locale = "pt-BR" if variant == "pt-BR" else "es-419"
    country = {"es-MX": "MX", "es-CO": "CO", "es-AR": "AR", "pt-BR": "MX"}[variant]
    return Case(
        id=case_id, locale=locale, country=country, turns=(case_id,), expected_intent=intent,
        expected_category=None, expected_outcome="clarification", requires_handoff=False,
        split="held_out", base_id=base, variant=variant,
    )


VARIANT_NAMES = ("es-MX", "es-CO", "es-AR", "pt-BR")


def test_breakdown_reports_n_and_interval_per_variant_and_intent() -> None:
    from eval.intervals import breakdown

    cases = [_vcase(f"b{b}-{v}", f"b{b}", v) for b in range(40) for v in VARIANT_NAMES]
    # es-AR misses every fourth base; the others are always right.
    predicted = [
        "missing" if (c.variant == "es-AR" and int(c.base_id[1:]) % 4 == 0) else "charge" for c in cases
    ]
    result = breakdown(cases, predicted)
    assert result["overall"]["n"] == 160 and result["overall"]["clusters"] == 40
    assert result["by_variant"]["es-AR"]["accuracy"] == 0.75
    assert result["by_variant"]["es-MX"]["accuracy"] == 1.0
    low, high = result["by_variant"]["es-AR"]["interval_95"]
    assert low < 0.75 < high
    assert result["by_intent"]["charge"]["n"] == 160
    # Same seed, same interval.
    assert breakdown(cases, predicted)["by_variant"]["es-AR"]["interval_95"] == [low, high]


def test_thin_breakdown_is_labelled_descriptive() -> None:
    from eval.intervals import breakdown

    cases = [_vcase(f"b{b}-es-MX", f"b{b}", "es-MX") for b in range(8)]
    predicted = ["charge", "missing"] * 4
    block = breakdown(cases, predicted)["by_variant"]["es-MX"]
    assert block["n"] == 8
    assert block["descriptive"] is True


def test_paired_comparison_names_fixed_and_broken_cases() -> None:
    from eval.paired import paired

    cases = [_vcase(f"b{b}-es-MX", f"b{b}", "es-MX") for b in range(5)]
    baseline = ["charge", "missing", "missing", "charge", "charge"]
    router = ["charge", "charge", "charge", "missing", "charge"]
    result = paired(cases, baseline, router)
    assert result["fixed"] == ["b1-es-MX", "b2-es-MX"]
    assert result["broken"] == ["b3-es-MX"]
    assert (result["n"], result["net"], result["net_share"]) == (5, 1, 0.2)
    assert len(result["interval_95"]) == 2


def test_clear_gain_has_an_interval_above_zero() -> None:
    from eval.paired import paired

    cases = [_vcase(f"b{b}-{v}", f"b{b}", v) for b in range(40) for v in VARIANT_NAMES]
    baseline = ["missing" if int(c.base_id[1:]) % 3 == 0 else "charge" for c in cases]
    router = ["charge"] * len(cases)
    assert paired(cases, baseline, router)["above_zero"] is True


def test_variant_loss_is_counted_in_shared_bases() -> None:
    from eval.paired import variant_losses

    cases = [_vcase(f"b{b}-{v}", f"b{b}", v) for b in range(4) for v in VARIANT_NAMES]
    # es-AR wrong on b0 and b2; pt-BR wrong on b1; es-MX and es-CO always right.
    wrong = {("b0", "es-AR"), ("b2", "es-AR"), ("b1", "pt-BR")}
    predicted = ["missing" if (c.base_id, c.variant) in wrong else "charge" for c in cases]
    result = variant_losses(cases, predicted)
    assert result["best"] in ("es-CO", "es-MX")
    assert result["by_variant"]["es-AR"]["lost_bases"] == ["b0", "b2"]
    assert result["by_variant"]["es-AR"]["net_loss"] == 2
    assert result["by_variant"]["pt-BR"]["net_loss"] == 1
    assert result["by_variant"][result["best"]]["net_loss"] == 0
