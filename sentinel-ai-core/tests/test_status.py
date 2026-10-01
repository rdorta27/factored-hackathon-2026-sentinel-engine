"""
Unit tests for TransactionStatus.to_candidate().
"""

from __future__ import annotations

import pytest

from app.schemas.status import TransactionStatus, to_candidate


class TestToCandidate:
    def test_refunded_maps_to_reversed(self) -> None:
        candidate = to_candidate("Refunded")
        assert candidate.status == TransactionStatus.reversed
        assert candidate.i18n_key == "status.reversed"

    def test_refunded_case_insensitive(self) -> None:
        assert to_candidate("REFUNDED").status == TransactionStatus.reversed
        assert to_candidate("refunded").status == TransactionStatus.reversed

    def test_posted_variants(self) -> None:
        for raw in ("POSTED", "posted", "Settled", "Completed", "Approved"):
            candidate = to_candidate(raw)
            assert candidate.status == TransactionStatus.posted, f"Failed for {raw!r}"

    def test_pending_variants(self) -> None:
        for raw in ("pending", "PROCESSING", "Authorized"):
            candidate = to_candidate(raw)
            assert candidate.status == TransactionStatus.pending, f"Failed for {raw!r}"

    def test_declined_variants(self) -> None:
        for raw in ("declined", "Rejected", "FAILED"):
            candidate = to_candidate(raw)
            assert candidate.status == TransactionStatus.declined, f"Failed for {raw!r}"

    def test_disputed_variants(self) -> None:
        for raw in ("disputed", "under_review", "in_dispute"):
            candidate = to_candidate(raw)
            assert candidate.status == TransactionStatus.disputed, f"Failed for {raw!r}"

    def test_chargeback_maps_to_reversed(self) -> None:
        assert to_candidate("chargeback").status == TransactionStatus.reversed

    def test_unknown_falls_back_to_posted(self) -> None:
        candidate = to_candidate("totally_unknown_value")
        assert candidate.status == TransactionStatus.posted

    def test_whitespace_stripped(self) -> None:
        candidate = to_candidate("  Refunded  ")
        assert candidate.status == TransactionStatus.reversed

    def test_i18n_key_format(self) -> None:
        for raw, expected_key in [
            ("posted", "status.posted"),
            ("pending", "status.pending"),
            ("Refunded", "status.reversed"),
            ("declined", "status.declined"),
            ("disputed", "status.disputed"),
        ]:
            assert to_candidate(raw).i18n_key == expected_key
