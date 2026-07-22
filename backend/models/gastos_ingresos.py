"""Gastos/Ingresos (Expenses/Income) model — maps to the gastos_ingresos table."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class GastoIngreso(Base):
    """Expense or income entry with encrypted amount and description."""

    __tablename__ = "gastos_ingresos"
    __table_args__ = (
        Index("ix_gastos_ingresos_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="income or expense"
    )
    amount_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fernet-encrypted monetary amount"
    )
    description_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fernet-encrypted description"
    )
    category_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("categories.id"),
        nullable=False,
    )
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="gastos_ingresos")
    category = relationship("Category", back_populates="gastos_ingresos")
