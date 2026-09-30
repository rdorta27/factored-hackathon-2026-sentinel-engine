"""Contract tests: every variant serializes, rejects extras, carries keys."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.chat.contract import (
    CandidateTransaction,
    CaseConfirmation,
    Clarification,
    ConfirmationDisplay,
    ErrorReply,
    Handoff,
    MessageKeys,
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
        verified_at=datetime.now(timezone.utc),
        verified=True,
        display=ConfirmationDisplay(
            amount="1000.00",
            currency="MXN",
            merchant="ACME Store",
            referenceDate="2026-06-17",
            slaDate="2026-06-19",
        ),
        messages=MessageKeys(
            nextStep="nextStepAdvisorReview",
            rule="ruleEligible",
            queue="queueInReview",
            noFunds="noFundsHeld",
        ),
    )


def test_text_carries_a_message_key() -> None:
    assert TextReply(message_key="greetingHelp").model_dump()["kind"] == "text"


def test_clarification_carries_candidates() -> None:
    reply = Clarification(
        message_key="clarifyAmbiguous",
        missing="transaction",
        candidates=[
            CandidateTransaction(
                reference="TXN-1001",
                amount="1000.00",
                currency="MXN",
                merchant="ACME Store",
                date="2026-06-10",
                eligible=True,
            )
        ],
    )
    assert reply.candidates[0].eligible is True


def test_confirmation_requires_verified_true() -> None:
    with pytest.raises(ValidationError):
        CaseConfirmation(**{**_confirmation().model_dump(), "verified": False})


def test_confirmation_carries_keys_and_raw_values() -> None:
    body = _confirmation().model_dump(mode="json")
    assert body["messages"]["nextStep"] == "nextStepAdvisorReview"
    assert body["display"]["slaDate"] == "2026-06-19"
    # No server-authored prose and no hold field survive in the contract.
    assert "hold" not in body
    assert "no_funds_held" not in body
    assert "next_steps" not in body
    assert "expected_timeline" not in body


def test_handoff_uses_a_reason_key() -> None:
    reply = Handoff(reference="HO-CASE-0001", reason_key="reasonHighRisk")
    dumped = reply.model_dump()
    assert dumped["reason_key"] == "reasonHighRisk"
    assert "reason" not in dumped
    assert "advisor_received" not in dumped


def test_error_carries_a_key_and_trace() -> None:
    dumped = ErrorReply(message_key="errorGeneric", trace_id="abc123").model_dump()
    assert dumped["message_key"] == "errorGeneric"
    assert "message" not in dumped


def test_extra_fields_rejected_everywhere() -> None:
    with pytest.raises(ValidationError):
        TextReply(message_key="hi", customer_id="CUST-9999")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        Clarification(message_key="hi", missing="x", role="admin")  # type: ignore[call-arg]
    with pytest.raises(ValidationError):
        ErrorReply(message_key="hi", trace_id="t", debug="stack")  # type: ignore[call-arg]


def test_candidate_list_is_capped() -> None:
    with pytest.raises(ValidationError):
        Clarification(
            message_key="clarifyAmbiguous",
            missing="transaction",
            candidates=[
                CandidateTransaction(
                    reference=f"TXN-{1000 + i}",
                    amount="1.00",
                    currency="MXN",
                    merchant="Shop",
                    date="2026-06-10",
                    eligible=True,
                )
                for i in range(5)
            ],
        )
