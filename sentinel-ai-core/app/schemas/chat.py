"""
Pydantic v2 schemas for the /api/v1/chat endpoint.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming message from the front-end chat widget."""

    session_id: str = Field(..., description="Active session token")
    message: str = Field(..., min_length=1, description="User's natural-language message")
    locale: str = Field(
        default="es-419",
        description="BCP 47 locale tag for the response language",
        pattern=r"^[a-z]{2,3}(-[A-Z]{2,})?$",
    )


class VerifiedFacts(BaseModel):
    """Transaction facts extracted from the Gold layer and confirmed by the session."""

    transaction_id: str
    amount: float
    currency: str
    merchant: Optional[str] = None
    transaction_date: str
    days_since_transaction: int
    is_eligible_for_dispute: bool


class HandoffTicket(BaseModel):
    """
    Structured HIL (Human-In-the-Loop) escalation payload.

    Returned inside ``ChatResponse`` when the orchestrator determines the case
    requires a human agent.  Never contains PII fields (first/last name,
    credit score) – those live in the Gold PII-full table accessible only to
    authorized agents.

    Fields marked "sentinel-login contract" align with the Handoff schema in
    sentinel-login so its i18n card component can render the escalation without
    any frontend changes.
    """

    # ── Core fields (original schema) ───────────────────────────────────────
    customer_id: str = Field(..., description="Opaque customer token (no PII)")
    verified_facts: VerifiedFacts
    escalation_reason: str = Field(
        ..., description="Plain-English explanation of why human intervention is required"
    )
    claim_summary: str = Field(
        ..., description="Short summary of the dispute claim for the receiving agent"
    )

    # ── sentinel-login contract fields ───────────────────────────────────────
    kind: str = Field(
        default="handoff",
        description="sentinel-login card discriminator — always 'handoff'",
    )
    reference: str = Field(
        default="",
        description="Transaction or dispute reference shown on the handoff card",
    )
    reason_key: str = Field(
        default="handoff.escalated",
        description="i18n key used by the sentinel-login card (e.g. 'handoff.high_value_dispute')",
    )
    reason_detail: Optional[str] = Field(
        default=None,
        description="Optional free-text detail rendered below the i18n reason",
    )
    estimated_date: Optional[str] = Field(
        default=None,
        description="ISO-8601 estimated SLA resolution date shown to the customer",
    )
    source: str = Field(
        default="mock",
        description="'mock' for demo runs, 'live' when backed by a real dispute service",
    )


class ChatResponse(BaseModel):
    """Response returned by POST /api/v1/chat."""

    session_id: str
    reply: str = Field(..., description="Natural-language response to show the user")
    response_type: Literal["automated", "handoff"] = Field(
        default="automated",
        description="'automated' = bot handled it; 'handoff' = escalated to a human agent",
    )
    handoff_ticket: Optional[HandoffTicket] = Field(
        default=None,
        description="Populated only when response_type == 'handoff'",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
