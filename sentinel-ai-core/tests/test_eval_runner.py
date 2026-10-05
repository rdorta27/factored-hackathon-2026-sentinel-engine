"""System runner replay, fault injection and adversarial convention."""

from pathlib import Path

import pytest

from app.ai.demo import DemoModel
from eval.cases import Case, load_dir
from eval.runner import build_client, match_outcome, run_case, run_system

CASES_DIR = Path(__file__).parent.parent / "eval" / "cases"
FIXTURES = Path(__file__).parent.parent / "app" / "ai" / "fixtures"


def _resolution_case(**overrides) -> Case:  # type: ignore[no-untyped-def]
    body = {
        "id": "res-test",
        "locale": "es-419",
        "country": "MX",
        "turns": ("no reconozco un cargo",),
        "expected_intent": "charge",
        "expected_category": None,
        "expected_outcome": "case_confirmation",
        "requires_handoff": False,
        "split": "development",
        "selected_reference": "TXN-1006",
        "confirm": True,
    }
    body.update(overrides)
    return Case(**body)  # type: ignore[arg-type]


def _case(case_id: str):  # type: ignore[no-untyped-def]
    for case in load_dir(CASES_DIR):
        if case.id == case_id:
            return case
    raise KeyError(case_id)


def test_full_case_is_replayed_and_matched() -> None:
    case = _case("dev-oos-01")
    turn = run_case(build_client(FIXTURES), case)
    assert turn["outcome"] == "text"
    assert turn["matched"] is True
    assert turn["trace_id"] != "unknown"
    assert turn["model"] == "cheap-eval"


def test_first_person_ask_matches_as_offer() -> None:
    turn = run_case(build_client(FIXTURES), _case("dev-person-01"))
    assert turn["outcome"] == "text"
    assert turn["matched"] is True
    assert match_outcome(_case("dev-person-01"), "text", 200, ["person.ask"]) is True
    assert match_outcome(_case("dev-person-01"), "text", 200, []) is False


def test_each_fault_degrades_safely_and_is_recorded() -> None:
    for case_id in ("dev-fault-01", "dev-fault-02", "dev-fault-03"):
        turn = run_case(build_client(FIXTURES), _case(case_id))
        assert turn["outcome"] != "case_confirmation", case_id
        assert turn["matched"] is True, (case_id, turn["outcome"])
        assert turn["trace_id"] != "unknown", case_id


def test_unsafe_rate_uses_full_denominator(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("no HTTP connection may be opened during the run")

    monkeypatch.setattr("httpx.Client.post", _forbidden)
    cases = [c for c in load_dir(CASES_DIR) if c.split == "development"]
    turns = run_system(cases, FIXTURES)
    unsafe = [t for t in turns if t["outcome"] == "case_confirmation" and t["must_not_pass"]]
    assert f"{len(unsafe)}/{len(turns)}" == f"0/{len(turns)}"
    assert match_outcome(_case("dev-adv-01"), "clarification", 200) is True


def test_two_turn_case_checks_the_rule() -> None:
    import dataclasses

    case = _case("dev-rule-03")
    turn = run_case(build_client(FIXTURES), case)
    assert (turn["outcome"], turn["matched"]) == ("handoff", True)
    assert turn["model"] != "unknown"
    wrong = dataclasses.replace(case, expected_rule="fraud.score")
    assert run_case(build_client(FIXTURES), wrong)["matched"] is False


def test_untriggered_rule_case_fails_if_a_rule_fires() -> None:
    assert match_outcome(_case("dev-rule-09"), "confirm_box", 200, ["status.approved"]) is True
    assert match_outcome(_case("dev-rule-09"), "confirm_box", 200, ["amount.high"]) is False


def test_confirm_turn_reaches_a_verified_case_number() -> None:
    turn = run_case(build_client(FIXTURES, DemoModel()), _resolution_case())
    assert turn["outcome"] == "case_confirmation"
    assert turn["matched"] is True


def test_refused_charge_sends_no_third_turn() -> None:
    case = _resolution_case(
        id="res-refused",
        expected_outcome="text",
        expected_rule="window.expired",
        must_not_pass=True,
        selected_reference="TXN-1002",
    )
    turn = run_case(build_client(FIXTURES, DemoModel()), case)
    assert turn["outcome"] == "text"
    assert turn["matched"] is True
    assert turn["must_not_pass"] is True


def test_single_turn_case_stays_single_turn() -> None:
    case = _resolution_case(
        id="res-single",
        selected_reference=None,
        confirm=False,
        expected_outcome="clarification",
    )
    turn = run_case(build_client(FIXTURES, DemoModel()), case)
    assert turn["outcome"] == "clarification"
    assert turn["matched"] is True


class _TimedTransport:
    """A fake transport that sleeps, so the runner records a model latency."""

    def __init__(self, delay_s: float = 0.02) -> None:
        self.delay_s = delay_s
        self.last_latency_ms = 0.0

    def complete(self, *, model: str, messages: list, temperature: float = 0.0):  # type: ignore[no-untyped-def]
        import time

        from app.ai.transport import LLMResponse

        time.sleep(self.delay_s)
        self.last_latency_ms = self.delay_s * 1000
        return LLMResponse(content='{"kind": "charge", "language": "es-419"}', cost_usd=0.001)


def test_live_timing_records_the_model_call_and_labels_the_source() -> None:
    from app.ai.llm import PromptedLLMRouter, RouterConfig

    transport = _TimedTransport()
    router = PromptedLLMRouter(
        transport,
        RouterConfig(cheap_model="cheap-eval", strong_model="strong-eval", default_model="default-eval"),
    )
    turn = run_case(build_client(FIXTURES, router), _resolution_case(), timing="live")
    assert turn["latency_source"] == "live"
    assert turn["model_latency_ms"] is not None
    assert turn["model_latency_ms"] >= 20.0


def test_replay_is_the_default_timing_source() -> None:
    turn = run_case(build_client(FIXTURES), _case("dev-oos-01"))
    assert turn["latency_source"] == "replay"
