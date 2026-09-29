"""Contract tests: every variant serializes and rejects extras."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.chat.contract import (
    CaseConfirmation,
    Clarification,
    ErrorReply,
    Handoff,
    TextReply,
    TransactionFacts,
)


def _confirmation() -> CaseConfirmation:
    return CaseConfirmation(
        case_id="CASE-0001",
        transaction=TransactionFacts(
            amount="1000.00", currency="MXN", merchant="ACME Store", date="2026-06-10"
        ),
        state="Open",
        priority="High",
        next_steps=["Advisor reviews within 2 days"],
        expected_timeline="2 business days",
        verified_at=datetime.now(timezone.utc),
        verified=True,
        hold="Amount 1000.00 MXN temporarily held (simulated).",
        eligibility="Eligible within the 90-day dispute window (Art. 4).",
        sla_deadline=datetime(2026, 6, 21, tzinfo=timezone.utc),
        receipt_ref="RCPT-CASE-0001",
        queue_status="Queued for advisor review.",
    )


def test_text_serializes() -> None:
    reply = TextReply(text="Hello")
    assert reply.model_dump()["kind"] == "text"


def test_clarification_names_missing_datum() -> None:
    reply = Clarification(text="Which charge?", missing="transaction")
    assert reply.missing == "transaction"


def test_confirmation_requires_verified_true() -> None:
    with pytest.raises(ValidationError):
        CaseConfirmation(
            **{**_confirmation().model_dump(), "verified": False},
        )


def test_confirmation_carries_proof_of_work() -> None:
    body = _confirmation().model_dump(mode="json")
    assert "temporarily held (simulated)" in body["hold"]
    assert "Art. 4" in body["eligibility"]
    assert body["sla_deadline"].startswith("2026-06-21")
    assert body["receipt_ref"] == "RCPT-CASE-0001"
    assert "Queued" in body["queue_status"]


def test_handoff_fields() -> None:
    reply = Handoff(
        reference="HO-1",
        reason="High risk",
        advisor_received="summary",
        estimated_time="1 day",
    )
    assert reply.reference == "HO-1"


def test_error_carries_trace_id() -> None:
    reply = ErrorReply(message="Something failed", trace_id="abc123")
    assert reply.trace_id == "abc123"


def test_extra_fields_rejected_everywhere() -> None:
    with pytest.raises(ValidationError):
        TextReply(text="hi", customer_id="CUST-9999")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Clarification(text="hi", missing="x", role="admin")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        ErrorReply(message="hi", trace_id="t", debug="stack")  # type: ignore[call-arg]
