"""Structured chat response contract shared with the future real orchestrator."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

StrictModel = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TextReply(BaseModel):
    model_config = StrictModel

    kind: Literal["text"] = "text"
    text: str = Field(min_length=1, max_length=2000)


class Clarification(BaseModel):
    model_config = StrictModel

    kind: Literal["clarification"] = "clarification"
    text: str = Field(min_length=1, max_length=2000)
    missing: str = Field(min_length=1, max_length=200)


class TransactionFacts(BaseModel):
    model_config = StrictModel

    amount: str = Field(min_length=1, max_length=64)
    currency: str = Field(min_length=1, max_length=8)
    merchant: str = Field(min_length=1, max_length=200)
    date: str = Field(min_length=1, max_length=32)


class CaseConfirmation(BaseModel):
    model_config = StrictModel

    kind: Literal["case_confirmation"] = "case_confirmation"
    case_id: str = Field(min_length=1, max_length=64)
    transaction: TransactionFacts
    state: str = Field(min_length=1, max_length=64)
    priority: str = Field(min_length=1, max_length=32)
    next_steps: list[str] = Field(min_length=1, max_length=8)
    expected_timeline: str = Field(min_length=1, max_length=200)
    verified_at: datetime
    verified: Literal[True]
    hold: str = Field(min_length=1, max_length=200)
    eligibility: str = Field(min_length=1, max_length=500)
    sla_deadline: datetime
    receipt_ref: str = Field(min_length=1, max_length=64)
    queue_status: str = Field(min_length=1, max_length=200)
    source: Literal["mock", "live"] = "mock"


class Handoff(BaseModel):
    model_config = StrictModel

    kind: Literal["handoff"] = "handoff"
    reference: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=1, max_length=500)
    advisor_received: str = Field(min_length=1, max_length=1000)
    estimated_time: str = Field(min_length=1, max_length=200)
    source: Literal["mock", "live"] = "mock"


class ErrorReply(BaseModel):
    model_config = StrictModel

    kind: Literal["error"] = "error"
    message: str = Field(min_length=1, max_length=500)
    trace_id: str = Field(min_length=1, max_length=64)


ChatReply = TextReply | Clarification | CaseConfirmation | Handoff | ErrorReply
