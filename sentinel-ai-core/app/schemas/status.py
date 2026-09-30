"""
Canonical transaction status enum and raw-string mapping.

Bridges the heterogeneous status strings produced by the Gold layer
(e.g. "Refunded", "POSTED") to the uniform API vocabulary exposed to
the chat orchestrator and front-end.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TransactionStatus(str, Enum):
    """Canonical transaction statuses as used across the API layer."""

    posted = "posted"
    pending = "pending"
    reversed = "reversed"
    declined = "declined"
    disputed = "disputed"


@dataclass(frozen=True)
class StatusCandidate:
    """Result of mapping a raw Gold status string to the canonical enum."""

    status: TransactionStatus
    i18n_key: str  # e.g. "status.reversed" – used by the front-end for locale strings


# Lookup table: lowercase raw Gold values → canonical status + i18n key
_RAW_TO_CANDIDATE: dict[str, StatusCandidate] = {
    # posted variants
    "posted": StatusCandidate(TransactionStatus.posted, "status.posted"),
    "settled": StatusCandidate(TransactionStatus.posted, "status.posted"),
    "completed": StatusCandidate(TransactionStatus.posted, "status.posted"),
    "approved": StatusCandidate(TransactionStatus.posted, "status.posted"),
    # pending variants
    "pending": StatusCandidate(TransactionStatus.pending, "status.pending"),
    "processing": StatusCandidate(TransactionStatus.pending, "status.pending"),
    "in_process": StatusCandidate(TransactionStatus.pending, "status.pending"),
    "authorized": StatusCandidate(TransactionStatus.pending, "status.pending"),
    # reversed / refunded variants
    "reversed": StatusCandidate(TransactionStatus.reversed, "status.reversed"),
    "refunded": StatusCandidate(TransactionStatus.reversed, "status.reversed"),
    "chargeback": StatusCandidate(TransactionStatus.reversed, "status.reversed"),
    "voided": StatusCandidate(TransactionStatus.reversed, "status.reversed"),
    # declined variants
    "declined": StatusCandidate(TransactionStatus.declined, "status.declined"),
    "rejected": StatusCandidate(TransactionStatus.declined, "status.declined"),
    "failed": StatusCandidate(TransactionStatus.declined, "status.declined"),
    # disputed variants
    "disputed": StatusCandidate(TransactionStatus.disputed, "status.disputed"),
    "under_review": StatusCandidate(TransactionStatus.disputed, "status.disputed"),
    "in_dispute": StatusCandidate(TransactionStatus.disputed, "status.disputed"),
}

# Fallback when the raw value is unknown
_FALLBACK = StatusCandidate(TransactionStatus.posted, "status.posted")


def to_candidate(raw_status: str) -> StatusCandidate:
    """
    Map a raw Gold status string to a :class:`StatusCandidate`.

    The lookup is case-insensitive. Unknown values fall back to
    ``TransactionStatus.posted`` so callers always receive a valid candidate.

    Parameters
    ----------
    raw_status:
        Any status string coming from the Gold layer, e.g. ``"Refunded"``,
        ``"POSTED"``, ``"under_review"``.

    Returns
    -------
    StatusCandidate
        Frozen dataclass holding the canonical enum member and its i18n key.
    """
    return _RAW_TO_CANDIDATE.get(raw_status.strip().lower(), _FALLBACK)
