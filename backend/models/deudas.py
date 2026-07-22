"""Deudas (Debts) model — maps to the deudas table."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class Deuda(Base):
    """Debt record with encrypted monetary fields and interest rate."""

    __tablename__ = "deudas"
    __table_args__ = (
        Index("ix_deudas_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    creditor_name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_amount_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fernet-encrypted total debt amount"
    )
    monthly_payment_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fernet-encrypted monthly payment"
    )
    interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, comment="Annual interest rate 0.00-100.00"
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    user = relationship("User", back_populates="deudas")
