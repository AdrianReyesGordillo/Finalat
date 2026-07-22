"""Creditos (Credit Cards) model — maps to the creditos table."""

import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class Credito(Base):
    """Credit card record with encrypted monetary fields."""

    __tablename__ = "creditos"
    __table_args__ = (
        Index("ix_creditos_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    balance_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fernet-encrypted balance"
    )
    limit_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fernet-encrypted credit limit"
    )
    min_payment_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fernet-encrypted minimum payment"
    )
    card_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    user = relationship("User", back_populates="creditos")
