"""Afore (Pension Fund) model — maps to the afore table."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class Afore(Base):
    """Afore (pension fund) record with encrypted balance."""

    __tablename__ = "afore"
    __table_args__ = (
        Index("ix_afore_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    balance_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fernet-encrypted balance"
    )
    last_update_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    user = relationship("User", back_populates="afore")
