"""Eligibility tests: each refusal reason plus the 89/90/91 boundary."""

from datetime import date, timedelta

from app.disputes.policy import DisputePolicy, check_eligibility, reference_date
from app.gold.store import GoldRow, MockGoldStore

POLICY = DisputePolicy()
REFERENCE = date(2026, 6, 17)


def day_at(offset_days: int) -> str:
    """ISO date exactly `offset_days` before the reference date."""
    return (REFERENCE - timedelta(days=offset_days)).isoformat()


def row(reference: str, day: str) -> GoldRow:
    found = MockGoldStore(REFERENCE.isoformat()).get(reference, "CUST-0001")
    assert found is not None
    return GoldRow(**{**found.__dict__, "date": day})


def test_eligible_row_passes() -> None:
    ok, reason = check_eligibility(row("TXN-1001", day_at(10)), POLICY, REFERENCE)
    assert ok and reason == ""


def test_day_89_is_inside_the_window() -> None:
    ok, reason = check_eligibility(row("TXN-1001", day_at(89)), POLICY, REFERENCE)
    assert ok, reason


def test_day_90_is_inside_the_window() -> None:
    ok, reason = check_eligibility(row("TXN-1001", day_at(90)), POLICY, REFERENCE)
    assert ok, reason


def test_day_91_is_outside_the_window() -> None:
    ok, reason = check_eligibility(row("TXN-1001", day_at(91)), POLICY, REFERENCE)
    assert not ok
    assert "91 days" in reason and "90-day" in reason


def test_stale_row_refused() -> None:
    ok, reason = check_eligibility(row("TXN-1002", "2026-01-15"), POLICY, REFERENCE)
    assert not ok and "90-day" in reason


def test_refunded_row_refused() -> None:
    ok, reason = check_eligibility(row("TXN-1003", day_at(5)), POLICY, REFERENCE)
    assert not ok and "refunded" in reason


def test_prior_dispute_refused() -> None:
    ok, reason = check_eligibility(row("TXN-1004", day_at(5)), POLICY, REFERENCE)
    assert not ok and "already" in reason


def test_reference_date_defaults_to_dataset_end() -> None:
    # No env var set: the dataset's last date keeps demo charges in-window.
    assert reference_date() == REFERENCE
