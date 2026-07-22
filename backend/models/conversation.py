"""Conversation Sessions model — maps to the conversation_sessions table."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class ConversationSession(Base):
    """Fina AI advisor conversation session with persisted state."""

    __tablename__ = "conversation_sessions"
    __table_args__ = (
        Index("ix_conversation_sessions_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    current_state: Mapped[str] = mapped_column(
        String(50), nullable=False, default="welcome", comment="FSM state name"
    )
    collected_params: Mapped[Any | None] = mapped_column(
        JSON, nullable=True, comment="Collected optimizer parameters"
    )
    messages: Mapped[Any] = mapped_column(
        JSON, nullable=False, default=list, comment="Conversation message history"
    )
    interaction_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    user = relationship("User", back_populates="conversation_sessions")
