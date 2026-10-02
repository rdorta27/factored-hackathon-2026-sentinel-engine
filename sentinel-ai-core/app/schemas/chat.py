"""
Canonical contract for ``/api/v1/chat`` and ``/api/v1/transactions``.

Every chat answer is exactly one variant: ``text``, ``clarification``,
``confirm_box``, ``case_confirmation``, ``handoff`` or ``error`` (spec ``chat``).
Replies carry raw values and translation keys, never authored prose; the
client renders the keys in its locale. Shapes follow the former
``sentinel-login`` chat contract (backend removed by decision 009), trimmed to
the spec: no priority, service-level date, queue status or receipt on a
confirmation.

The same models serve the mock and the real adapters: only the ``source``
field says which one produced a confirmation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

StrictModel = ConfigDict(extra="forbid", str_strip_whitespace=True)
Source = Literal["mock", "live"]


class ChatInput(BaseModel):
    """Body of ``POST /api/v1/chat``. Identity comes from the session cookie only.

    Exactly one of ``message`` or ``selected_reference`` is required, and a
    provided message must carry visible text: blank or control-only payloads
    are rejected with 422 instead of producing a clarification turn.
    """

    model_config = ConfigDict(extra="forbid")

    message: Optional[str] = Field(default=None, max_length=2000)
    selected_reference: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9\-]+$",
    )

    @model_validator(mode="after")
    def _exactly_one_meaningful_input(self) -> "ChatInput":
        if self.message is None and self.selected_reference is None:
            raise ValueError("message or selected_reference is required")
        if self.message is not None and self.selected_reference is not None:
            raise ValueError("message and selected_reference are mutually exclusive")
        if self.message is not None and not self.message.strip():
            raise ValueError("message must not be blank")
        return self


class CandidateTransaction(BaseModel):
    """One charge as the interface shows it: listing, chips and confirm box."""

    model_config = StrictModel

    reference: str = Field(min_length=1, max_length=64)
    amount: str = Field(min_length=1, max_length=64)
    currency: str = Field(min_length=1, max_length=8)
    merchant: str = Field(min_length=1, max_length=200)
    date: str = Field(min_length=1, max_length=32)
    status: str = Field(min_length=1, max_length=16)
    eligible: bool
    ineligibleKey: Optional[str] = Field(default=None, max_length=64)


class TransactionList(BaseModel):
    """Response of ``GET /api/v1/transactions``."""

    model_config = StrictModel

    as_of: str = Field(min_length=1, max_length=32)
    transactions: list[CandidateTransaction]


class TextReply(BaseModel):
    model_config = StrictModel

    kind: Literal["text"] = "text"
    message_key: str = Field(min_length=1, max_length=64)


class Clarification(BaseModel):
    model_config = StrictModel

    kind: Literal["clarification"] = "clarification"
    message_key: str = Field(min_length=1, max_length=64)
    missing: str = Field(min_length=1, max_length=200)
    candidates: list[CandidateTransaction] = Field(default_factory=list, max_length=4)


class ConfirmBox(BaseModel):
    """Shown before any write; the confirmation turn sends ``candidate.reference`` back."""

    model_config = StrictModel

    kind: Literal["confirm_box"] = "confirm_box"
    message_key: str = Field(min_length=1, max_length=64)
    candidate: CandidateTransaction


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


class MessageKeys(BaseModel):
    """Translation keys, never prose."""

    model_config = StrictModel

    nextStep: str = Field(min_length=1, max_length=64)
    rule: str = Field(min_length=1, max_length=64)
    noFunds: str = Field(min_length=1, max_length=64)


class CaseConfirmation(BaseModel):
    """Emitted only after the created case was read back from the store."""

    model_config = StrictModel

    kind: Literal["case_confirmation"] = "case_confirmation"
    case_id: str = Field(min_length=1, max_length=64)
    transaction: TransactionFacts
    verified: Literal[True] = True
    verified_at: datetime
    display: ConfirmationDisplay
    messages: MessageKeys
    attempt: int = Field(ge=1)
    source: Source = "mock"


class VerifiedFacts(BaseModel):
    """Transaction facts read from Gold for the session customer."""

    transaction_id: str
    amount: float
    currency: str
    merchant: Optional[str] = None
    transaction_date: str
    days_since_transaction: int
    is_eligible_for_dispute: bool


class HandoffAction(BaseModel):
    """One step the system attempted, from the execution records, failed ones included."""

    model_config = StrictModel

    turn: int = Field(default=1, ge=1)
    step: str
    tool: Optional[str] = None
    outcome: str
    attempt: int = Field(ge=1)
    policy_rule: Optional[str] = None


class ConversationTurn(BaseModel):
    """One turn as the system understood it. Codes and references, never the customer's words."""

    model_config = StrictModel

    turn: int = Field(ge=1)
    customer: str = Field(description="What the customer did, e.g. described_charge, asked_for_person")
    charge: Optional[str] = Field(default=None, description="Charge reference involved, if any")
    system: str = Field(description="Reply kind the system gave")
    rule: Optional[str] = Field(default=None, description="Policy rule or message key behind the reply")
    phase: Optional[str] = Field(default=None, description="Derived conversation phase after this turn")


class HandoffPackage(BaseModel):
    """What the advisor receives (REQ-0008). No customer identifier, no raw transcript."""

    model_config = StrictModel

    request: str = Field(description="Intent the system understood, not the customer's words")
    summary: str = Field(default="", description="Deterministic summary of the conversation, from the turns below")
    conversation: list[ConversationTurn] = Field(default_factory=list)
    verified_facts: Optional[VerifiedFacts] = None
    actions_taken: list[HandoffAction] = Field(
        default_factory=list, description="Every step attempted in the conversation, with its turn and outcome"
    )
    evidence: dict[str, str] = Field(default_factory=dict)
    open_questions: list[str] = Field(default_factory=list)
    language: str
    country: str
    phase: str = Field(default="handed_off", description="Derived conversation phase at handoff")


class Handoff(BaseModel):
    """Escalation card for the customer plus the structured package for the advisor."""

    model_config = StrictModel

    kind: Literal["handoff"] = "handoff"
    reference: str = Field(min_length=1, max_length=64)
    reason_key: str = Field(min_length=1, max_length=64)
    reason_detail: Optional[str] = Field(default=None, max_length=500)
    estimated_date: Optional[str] = Field(default=None, max_length=32)
    attempt: Optional[int] = Field(default=None, ge=1)
    source: Source = "mock"
    package: HandoffPackage


class ErrorReply(BaseModel):
    model_config = StrictModel

    kind: Literal["error"] = "error"
    message_key: str = Field(min_length=1, max_length=64)
    trace_id: str = Field(min_length=1, max_length=64)


ChatReply = Union[TextReply, Clarification, ConfirmBox, CaseConfirmation, Handoff, ErrorReply]


# --- /api/v1/disputes -------------------------------------------------------

_REFERENCE = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9\-]+$")


class DisputePreviewInput(BaseModel):
    """Step 1: ask the policy about one own charge. Never writes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reference: str = _REFERENCE
    reason: Optional[str] = Field(default=None, max_length=300)


class DisputeCreateInput(BaseModel):
    """Step 2: open the dispute previewed for this charge."""

    model_config = ConfigDict(extra="forbid")

    reference: str = _REFERENCE


class CaseSummary(BaseModel):
    """One case as the customer sees it. No customer identifier, no advisor package."""

    model_config = StrictModel

    case_id: str
    kind: Literal["dispute", "handoff"]
    status: str
    transaction: Optional[TransactionFacts] = None
    reason_key: Optional[str] = None
    created_at: datetime
    source: Source = "mock"


# --- /api/v1/handoffs (advisor) -----------------------------------------------


class AdvisorTicket(BaseModel):
    """An escalated case as the advisor reads it: why it came, what was verified and tried.

    Role ``advisor`` only. Carries the customer id and country so the advisor knows
    whom to serve; never names or the profile (decision 009).
    """

    model_config = StrictModel

    case_id: str
    status: str
    created_at: datetime
    customer_id: str
    country: str
    reason_key: Optional[str] = None
    reason_detail: Optional[str] = None
    package: HandoffPackage
