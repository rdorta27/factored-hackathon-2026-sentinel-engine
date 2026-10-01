"""ORM model for authenticated sessions."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class SessionState(Base):
    """One server-side session. The key is a hash of the cookie token, never the token."""

    __tablename__ = "session_states"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default="customer")
    reference_date: Mapped[date] = mapped_column(Date, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
