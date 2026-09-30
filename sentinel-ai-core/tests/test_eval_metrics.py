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
