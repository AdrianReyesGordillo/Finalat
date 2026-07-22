"""Instruments model — maps to the instruments table."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.database import Base


class Instrument(Base):
    """Financial instrument with rate data (fetched by Rate Scraper)."""

    __tablename__ = "instruments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    annual_rate: Mapped[Decimal] = mapped_column(
        Numeric(8, 4), nullable=False, comment="Annual rate percentage"
    )
    min_investment: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, comment="Minimum investment amount"
    )
    max_investment: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 2), nullable=True, comment="Maximum investment amount (nullable)"
    )
    term: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Term in days or 'liquid'"
    )
    risk_level: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="low, medium, or high"
    )
    liquidity_tier: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="immediate, 1-day, 28-day, or custom"
    )
    tiered_rates: Mapped[Any | None] = mapped_column(
        JSON, nullable=True, comment="Array of {min_amount, max_amount, rate} objects"
    )
    last_fetch_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="success", comment="success or error"
    )
    last_fetched_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )
