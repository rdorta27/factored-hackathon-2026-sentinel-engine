"""Structured chat response contract shared with the future real orchestrator."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StrictModel = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TextReply(BaseModel):
    model_config = StrictModel

    kind: Literal["text"] = "text"
    message_key: str = Field(min_length=1, max_length=64)


class CandidateTransaction(BaseModel):
    model_config = StrictModel

    reference: str = Field(min_length=1, max_length=64)
    amount: str = Field(min_length=1, max_length=64)
    currency: str = Field(min_length=1, max_length=8)
    merchant: str = Field(min_length=1, max_length=200)
    date: str = Field(min_length=1, max_length=32)
    eligible: bool
    ineligibleKey: str | None = Field(default=None, max_length=64)


class Clarification(BaseModel):
    model_config = StrictModel

    kind: Literal["clarification"] = "clarification"
    message_key: str = Field(min_length=1, max_length=64)
    missing: str = Field(min_length=1, max_length=200)
    candidates: list[CandidateTransaction] = Field(default_factory=list, max_length=4)


class TransactionFacts(BaseModel):
    model_config = StrictModel

    amount: str = Field(min_length=1, max_length=64)
    currency: str = Field(min_length=1, max_length=8)
    merchant: str = Field(min_length=1, max_length=200)
    date: str = Field(min_length=1, max_length=32)


class ConfirmationDisplay(BaseModel):
    """Locale-neutral values. The client formats; it never invents the currency."""

    model_config = StrictModel

    amount: str = Field(min_length=1, max_length=64)
    currency: str = Field(min_length=1, max_length=8)
    merchant: str = Field(min_length=1, max_length=200)
    referenceDate: str = Field(min_length=1, max_length=32)
    slaDate: str = Field(min_length=1, max_length=32)


class MessageKeys(BaseModel):
    """Translation keys, never prose. The client renders them in its locale."""

    model_config = StrictModel

    nextStep: str = Field(min_length=1, max_length=64)
    rule: str = Field(min_length=1, max_length=64)
    queue: str = Field(min_length=1, max_length=64)
    noFunds: str = Field(min_length=1, max_length=64)


class CaseConfirmation(BaseModel):
    model_config = StrictModel

    kind: Literal["case_confirmation"] = "case_confirmation"
    case_id: str = Field(min_length=1, max_length=64)
    transaction: TransactionFacts
    state: str = Field(min_length=1, max_length=64)
    priority: str = Field(min_length=1, max_length=32)
    verified_at: datetime
    verified: Literal[True]
    display: ConfirmationDisplay
    messages: MessageKeys
    source: Literal["mock", "live"] = "mock"


class Handoff(BaseModel):
    model_config = StrictModel

    kind: Literal["handoff"] = "handoff"
    reference: str = Field(min_length=1, max_length=64)
    reason_key: str = Field(min_length=1, max_length=64)
    reason_detail: str | None = Field(default=None, max_length=500)
    estimated_date: str | None = Field(default=None, max_length=32)
    source: Literal["mock", "live"] = "mock"


class ErrorReply(BaseModel):
    model_config = StrictModel

    kind: Literal["error"] = "error"
    message_key: str = Field(min_length=1, max_length=64)
    trace_id: str = Field(min_length=1, max_length=64)


ChatReply = TextReply | Clarification | CaseConfirmation | Handoff | ErrorReply
