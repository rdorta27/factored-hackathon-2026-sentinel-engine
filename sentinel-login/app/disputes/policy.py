"""Deterministic eligibility: pure function of row, policy, and reference date."""

import os
from dataclasses import dataclass
from datetime import date

from app.gold.store import GoldRow

# The system's notion of "today" for the dispute window.
#
# It is not the wall clock on purpose: the demo dataset is static and ends on
# 2026-06-17, so against the real date every charge would be months outside the
# 90-day window and nothing would ever be eligible. Override with
# SENTINEL_REFERENCE_DATE (ISO date) for another demo window.
DEFAULT_REFERENCE_DATE = "2026-06-17"
ENV_VAR = "SENTINEL_REFERENCE_DATE"


def reference_date() -> date:
    """Effective reference date, from the environment or the dataset end."""
    raw = os.environ.get(ENV_VAR, DEFAULT_REFERENCE_DATE)
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return date.fromisoformat(DEFAULT_REFERENCE_DATE)


@dataclass(frozen=True)
class DisputePolicy:
    """Synthetic banking policy, injected from configuration per country."""

    window_days: int = 90
    article: str = "Art. 4"


def check_eligibility(
    row: GoldRow, policy: DisputePolicy, today: date | None = None
) -> tuple[bool, str]:
    """Return (eligible, reason). Reason is empty when eligible."""
    reference = today or reference_date()
    age = (reference - date.fromisoformat(row.date)).days
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
