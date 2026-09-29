"""Eligibility tests: each refusal reason plus the window boundary."""

from datetime import date

from app.disputes.policy import DEMO_TODAY, DisputePolicy, check_eligibility
from app.gold.store import GoldRow, MockGoldStore

POLICY = DisputePolicy()
AS_OF = "2026-06-20"


def row(reference: str) -> GoldRow:
    found = MockGoldStore(AS_OF).get(reference, "CUST-0001")
    assert found is not None
    return found


def test_eligible_row_passes() -> None:
    ok, reason = check_eligibility(row("TXN-1001"), POLICY)
    assert ok and reason == ""


def test_stale_row_refused() -> None:
    ok, reason = check_eligibility(row("TXN-1002"), POLICY)
    assert not ok and "90-day" in reason


def test_refunded_row_refused() -> None:
    ok, reason = check_eligibility(row("TXN-1003"), POLICY)
    assert not ok and "refunded" in reason


def test_prior_dispute_refused() -> None:
    ok, reason = check_eligibility(row("TXN-1004"), POLICY)
    assert not ok and "already" in reason


def test_window_boundary() -> None:
    base = row("TXN-1001")
    edge = GoldRow(**{**base.__dict__, "date": "2026-03-22"})  # exactly 90 days
    assert check_eligibility(edge, POLICY, DEMO_TODAY)[0]
    over = GoldRow(**{**base.__dict__, "date": "2026-03-21"})  # 91 days
    ok, _ = check_eligibility(over, POLICY, DEMO_TODAY)
    assert not ok


def test_demo_today_is_after_data_end() -> None:
    assert DEMO_TODAY == date(2026, 6, 20)
