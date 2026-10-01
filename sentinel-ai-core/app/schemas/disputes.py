"""
Pydantic v2 schemas for the /api/v1/disputes endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DisputeCreateRequest(BaseModel):
    """Body for POST /api/v1/disputes."""

    session_id: str = Field(..., description="Active session token")
    transaction_id: str = Field(..., description="Transaction to dispute")
    reason: str = Field(..., min_length=5, description="Customer-provided dispute reason")


class DisputeResponse(BaseModel):
    """Single dispute case representation."""

    dispute_id: str
    customer_id: str
    transaction_id: str
    amount: float
    merchant: Optional[str] = None
    status: str
    escalation_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
