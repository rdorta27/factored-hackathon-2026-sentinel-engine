"""ORM model for per-session conversation state."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ConversationRecord(Base):
    """Serialized ``ConversationState`` (includes customer turns). Deleted with the session."""

    __tablename__ = "conversations"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    state: Mapped[str] = mapped_column(Text, nullable=False)
    pending_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
