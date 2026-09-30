"""Business-day SLA tests: one source of truth for the deadline."""

from datetime import date

from app.disputes.policy import reference_date
from app.disputes.sla import add_business_days

# 2026-06-17 is a Wednesday.
WEDNESDAY = date(2026, 6, 17)


def test_reference_date_is_a_wednesday() -> None:
    assert WEDNESDAY.weekday() == 2
    assert reference_date() == WEDNESDAY


def test_two_business_days_from_wednesday_is_friday() -> None:
    assert add_business_days(WEDNESDAY, 2) == date(2026, 6, 19)


def test_weekend_is_skipped() -> None:
    friday = date(2026, 6, 19)
    assert add_business_days(friday, 1) == date(2026, 6, 22)  # Monday


def test_zero_days_is_the_same_day() -> None:
    assert add_business_days(WEDNESDAY, 0) == WEDNESDAY


def test_five_business_days_is_a_week() -> None:
    assert add_business_days(WEDNESDAY, 5) == date(2026, 6, 24)


def test_confirmation_sla_is_business_days_not_hours() -> None:
    """The card must not claim a 24-hour deadline any more."""
    from app.disputes.service import SLA_BUSINESS_DAYS, sla_deadline

    assert SLA_BUSINESS_DAYS == 2
    assert sla_deadline().date() == date(2026, 6, 19)
