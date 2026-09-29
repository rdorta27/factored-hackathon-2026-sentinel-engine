"""Deterministic eligibility: pure function of row, policy, and demo date."""

from dataclasses import dataclass
from datetime import date

from app.gold.store import GoldRow

# Simulated demo "today" (decision 003): the static data ends 2026-06-17,
# so the demo clock sits just after it instead of using the real clock.
DEMO_TODAY = date(2026, 6, 20)


@dataclass(frozen=True)
class DisputePolicy:
    """Synthetic banking policy, injected from configuration per country."""

    window_days: int = 90
    article: str = "Art. 4"


def check_eligibility(
    row: GoldRow, policy: DisputePolicy, today: date = DEMO_TODAY
) -> tuple[bool, str]:
    """Return (eligible, reason). Reason is empty when eligible."""
    age = (today - date.fromisoformat(row.date)).days
    if age > policy.window_days:
        return False, (
            f"Transaction is {age} days old, beyond the {policy.window_days}-day "
            f"dispute window ({policy.article})."
        )
    if row.refunded or row.status in ("Refunded", "Reversed"):
        return False, "Transaction was refunded or reversed; nothing to dispute."
    if row.prior_dispute:
        return False, "Transaction already has a dispute on record."
    return True, ""
