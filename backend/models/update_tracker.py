"""Update Tracker model — maps to the update_tracker table."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class UpdateTracker(Base):
    """Records when a user last updated each financial module."""

    __tablename__ = "update_tracker"
    __table_args__ = (
        Index("ix_update_tracker_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    module_name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Module identifier (ahorro, creditos, etc.)"
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # Relationship
    user = relationship("User", back_populates="update_tracker")
