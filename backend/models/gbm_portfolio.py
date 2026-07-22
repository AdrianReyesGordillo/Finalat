"""GBM Portfolio model — maps to the gbm_portfolio table."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class GbmPortfolio(Base):
    """GBM Hombroker investment position with encrypted monetary values."""

    __tablename__ = "gbm_portfolio"
    __table_args__ = (
        Index("ix_gbm_portfolio_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    shares: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), nullable=False, comment="Number of shares, precision 6"
    )
    avg_cost_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fernet-encrypted average cost per share"
    )
    market_value_encrypted: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Fernet-encrypted current market value"
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    user = relationship("User", back_populates="gbm_portfolio")
