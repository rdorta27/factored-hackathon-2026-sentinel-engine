"""ORM model for cases: disputes opened after confirmation and handoff tickets."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DisputeCase(Base):
    """Operational record for a dispute (``kind=dispute``) or a handoff ticket (``kind=handoff``)."""

    __tablename__ = "dispute_cases"

    dispute_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False, default="dispute")
    transaction_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    merchant: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    transaction_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    # Dataset complaints vocabulary: Open, In Process, Escalated, Resolved, Closed, Rejected.
    status: Mapped[str] = mapped_column(String, nullable=False, default="Open")
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String, nullable=True, unique=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escalation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    package: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
