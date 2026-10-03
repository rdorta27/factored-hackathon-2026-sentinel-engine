"""A slow Gold read ends in a handoff without a case number, inside the budget."""

import time
from datetime import date

from app.observability.observer import TurnObserver
from app.observability.writer import Recorder
from app.orchestrator.step import MAX_ATTEMPTS, Ports, step
from app.orchestrator.types import ConversationState, Language, OutcomeKind, TextInput
from app.tools.bound import GoldTimeout, SessionBoundLookup, gold_timeout_s
from app.tools.fake import InMemoryTools
from tests.test_grounding import ChargeModel


class SlowGold:
    def __init__(self, delay: float) -> None:
        self.delay = delay

    def get(self, reference: str, customer_id: str):  # type: ignore[no-untyped-def]
        time.sleep(self.delay)
        return None

    def list_for_customer(self, customer_id: str):  # type: ignore[no-untyped-def]
        time.sleep(self.delay)
        return []


def test_three_timeouts_hand_off_within_the_total_budget(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    budget = 0.05
    monkeypatch.setenv("SENTINEL_GOLD_TIMEOUT_S", str(budget))
    assert gold_timeout_s() == budget
    bound = SessionBoundLookup(SlowGold(0.4), "CUST-0001", InMemoryTools())
    recorder = Recorder(path=None, salt="test-salt")
    ports = Ports(
        idempotency_scope="s1",
        tools=bound,
        model=ChargeModel(),
        today=date(2026, 6, 17),
        observer=TurnObserver(recorder, "c" * 16, "d" * 16, "MX"),
    )
    started = time.monotonic()
    result = step(
        TextInput("no reconozco un cargo"),
        ConversationState(language=Language.ES_419),
        ports,
    )
    elapsed = time.monotonic() - started
    assert result.kind is OutcomeKind.HANDOFF
    assert result.case_number is None
    assert result.attempt == MAX_ATTEMPTS
    assert elapsed < budget * MAX_ATTEMPTS + 0.15
    timeouts = [record for record in recorder.records if record.outcome == "timeout"]
    assert len(timeouts) == MAX_ATTEMPTS
    assert {record.tool for record in timeouts} == {"lookup_transactions"}


def test_a_fast_read_is_unchanged(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("SENTINEL_GOLD_TIMEOUT_S", "1")
    from app.tools.gold import MockGoldStore

    bound = SessionBoundLookup(MockGoldStore(as_of="2026-06-17"), "CUST-0001", InMemoryTools())
    rows = bound.lookup_transactions()
    assert rows
    assert not isinstance(rows, GoldTimeout)
