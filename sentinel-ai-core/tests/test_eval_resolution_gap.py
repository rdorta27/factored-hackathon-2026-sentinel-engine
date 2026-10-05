from pathlib import Path

import pytest

from eval import resolution_gap
from eval.cases import Case


def _case(case_id: str, resolvable: bool) -> Case:
    return Case(
        id=case_id,
        base_id="s-" + case_id,
        variant="es-MX",
        locale="es-419",
        country="MX",
        turns=["hola"],
        expected_intent="missing",
        expected_category=None,
        expected_outcome="case_confirmation" if resolvable else "handoff",
        requires_handoff=not resolvable,
        must_not_pass=not resolvable,
        selected_reference="TXN-1001",
        expected_rule=None,
        confirm=True,
        split="development",
    )


def _turn(outcome: str, resolvable: bool, label: str = "missing") -> dict:
    return {
        "outcome": outcome,
        "label": label,
        "fault": "none",
        "requires_handoff": not resolvable,
        "must_not_pass": not resolvable,
    }


def test_case_label() -> None:
    assert resolution_gap.case_label(True, True) == "both_resolve"
    assert resolution_gap.case_label(False, False) == "both_fail"
    assert resolution_gap.case_label(True, False) == "different"
    assert resolution_gap.case_label(False, True) == "different"


def test_both_at_the_ceiling_states_the_ceiling_cause() -> None:
    cases = [_case("a", True), _case("b", False)]
    baseline = [_turn("case_confirmation", True), _turn("handoff", False)]
    router = [_turn("case_confirmation", True), _turn("handoff", False, label="charge")]
    summary = resolution_gap.gap_summary("t", cases, baseline, router)
    assert summary["labels"] == {"n": 2, "both_resolve": 1, "both_fail": 1, "different": 0}
    assert summary["ceiling"]["baseline"]["resolvable"] == 1
    assert summary["ceiling"]["router_v2"]["gap"] == 0
    assert summary["intent_differs"]["cases"] == ["b"]
    assert summary["cause"] == "ceiling"
    assert "## Cause: ceiling" in resolution_gap.render(summary)


def test_a_different_outcome_names_the_case() -> None:
    cases = [_case("a", True)]
    summary = resolution_gap.gap_summary(
        "t", cases, [_turn("case_confirmation", True)], [_turn("text", True)]
    )
    assert summary["labels"]["different"] == 1
    assert summary["outcome_differs"]["cases"] == ["a"]
    assert summary["cause"] == "systems_differ"


def test_both_below_the_ceiling_means_the_set_cannot_separate() -> None:
    cases = [_case("a", True)]
    summary = resolution_gap.gap_summary("t", cases, [_turn("text", True)], [_turn("text", True)])
    assert summary["cause"] == "set_cannot_separate"


def test_run_replays_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from app.ai.demo import DemoModel

    def _no_network(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("no connection may be opened")

    monkeypatch.setattr("httpx.Client.post", _no_network)
    summary = resolution_gap.run(
        "test-gap", freeze=False, router_factory=lambda: DemoModel(), recordings_dir=tmp_path
    )
    assert summary["n"] == 56
    assert summary["labels"]["both_resolve"] == 16
    assert summary["labels"]["different"] == 0
    assert summary["ceiling"]["baseline"]["resolvable"] == 16
    assert summary["cause"] == "ceiling"
