"""Spend cap: stop before the call that would pass it, and never freeze a capped run."""

import pytest

from app.ai.transport import LLMResponse
from eval.budget import CappedTransport, SpendCapReached, assert_freezable


class PricedLive:
    def __init__(self, cost: float) -> None:
        self.cost = cost
        self.calls = 0

    def complete(self, *, model, messages, temperature=0.0):  # type: ignore[no-untyped-def]
        self.calls += 1
        return LLMResponse(content="{}", cost_usd=self.cost)


def test_cap_stops_before_the_call_that_would_pass_it() -> None:
    live = PricedLive(0.1)
    capped = CappedTransport(live, cap_usd=0.35, first_estimate_usd=0.1)
    for _ in range(3):
        capped.complete(model="m", messages=[])
    with pytest.raises(SpendCapReached):
        capped.complete(model="m", messages=[])
    assert live.calls == 3
    assert capped.report() == {"n": 3, "cap_usd": 0.35, "spent_usd": 0.3, "capped": True}


def test_capped_run_is_not_frozen() -> None:
    with pytest.raises(SpendCapReached, match="not frozen"):
        assert_freezable({"capped": True})
    assert_freezable({"capped": False})


def test_recorded_hits_do_not_count_against_the_cap(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.ai.llm import build_messages
    from app.ai.recording import RecordingTransport

    live = PricedLive(0.2)
    capped = CappedTransport(live, cap_usd=0.25, first_estimate_usd=0.2)
    recorder = RecordingTransport(tmp_path, "v1", capped, record=True)
    messages = build_messages("no reconozco este cargo", ["no reconozco este cargo"])
    for _ in range(5):
        recorder.complete(model="m", messages=messages)
    assert live.calls == 1
    assert capped.capped is False
