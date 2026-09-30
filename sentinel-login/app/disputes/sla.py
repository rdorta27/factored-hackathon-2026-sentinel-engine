"""Business-day arithmetic for the SLA. One source of truth for the deadline."""

from datetime import date, timedelta

# Demo holidays, per country-agnostic demo scope. Kept explicit so the
# business-day rule is testable rather than assumed.
HOLIDAYS: frozenset[date] = frozenset()


def add_business_days(start: date, days: int) -> date:
    """Add whole business days (Mon-Fri), skipping weekends and holidays."""
    current = start
    remaining = days
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5 and current not in HOLIDAYS:
            remaining -= 1
    return current
