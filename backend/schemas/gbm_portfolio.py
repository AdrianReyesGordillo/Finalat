"""Pydantic schemas for the GBM Portfolio module.

Defines request and response models for GBM investment position CRUD operations.
Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
"""

from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator

from backend.utils.validators import (
    validate_monetary_amount,
    ValidationError as ValidatorError,
)


def _validate_ticker(v: str) -> str:
    """Validate ticker: uppercase, max 20 chars, non-empty."""
    if not isinstance(v, str):
        raise ValueError("Ticker must be a string.")
    trimmed = v.strip().upper()
    if not trimmed:
        raise ValueError("Ticker cannot be empty.")
    if len(trimmed) > 20:
        raise ValueError("Ticker must not exceed 20 characters.")
    # Only allow alphanumeric, dots, and hyphens for tickers
    import re
    if not re.match(r"^[A-Z0-9.\-]+$", trimmed):
        raise ValueError("Ticker must contain only letters, digits, dots, or hyphens.")
    return trimmed


def _validate_shares(v: float) -> float:
    """Validate shares: positive, up to 6 decimal places."""
    if v is None:
        return v
    if v <= 0:
        raise ValueError("Shares must be a positive number.")
    # Check up to 6 decimal places
    from decimal import Decimal
    d = Decimal(str(v))
    if d.as_tuple().exponent is not None and abs(d.as_tuple().exponent) > 6:
        raise ValueError("Shares supports up to 6 decimal places.")
    return v


class GbmPortfolioCreate(BaseModel):
    """Schema for creating a new GBM portfolio position."""

    ticker: str = Field(..., description="Ticker symbol (max 20 chars, uppercase)")
    shares: float = Field(..., gt=0, description="Number of shares (positive, up to 6 decimals)")
    avg_cost: float = Field(..., description="Average cost per share (0.01–999,999,999.99)")
    market_value: float = Field(..., description="Current market value (0.01–999,999,999.99)")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        return _validate_ticker(v)

    @field_validator("shares")
    @classmethod
    def validate_shares(cls, v: float) -> float:
        return _validate_shares(v)

    @field_validator("avg_cost")
    @classmethod
    def validate_avg_cost(cls, v: float) -> float:
        try:
            validated = validate_monetary_amount(v, field_name="avg_cost")
            return float(validated)
        except ValidatorError as e:
            raise ValueError(e.message)

    @field_validator("market_value")
    @classmethod
    def validate_market_value(cls, v: float) -> float:
        try:
            validated = validate_monetary_amount(v, field_name="market_value")
            return float(validated)
        except ValidatorError as e:
            raise ValueError(e.message)


class GbmPortfolioUpdate(BaseModel):
    """Schema for updating an existing GBM portfolio position (partial update)."""

    ticker: Optional[str] = Field(None, description="Ticker symbol (max 20 chars, uppercase)")
    shares: Optional[float] = Field(None, gt=0, description="Number of shares (positive, up to 6 decimals)")
    avg_cost: Optional[float] = Field(None, description="Average cost per share (0.01–999,999,999.99)")
    market_value: Optional[float] = Field(None, description="Current market value (0.01–999,999,999.99)")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _validate_ticker(v)

    @field_validator("shares")
    @classmethod
    def validate_shares(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        return _validate_shares(v)

    @field_validator("avg_cost")
    @classmethod
    def validate_avg_cost(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        try:
            validated = validate_monetary_amount(v, field_name="avg_cost")
            return float(validated)
        except ValidatorError as e:
            raise ValueError(e.message)

    @field_validator("market_value")
    @classmethod
    def validate_market_value(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        try:
            validated = validate_monetary_amount(v, field_name="market_value")
            return float(validated)
        except ValidatorError as e:
            raise ValueError(e.message)


class GbmPortfolioPositionResponse(BaseModel):
    """Schema for a single GBM portfolio position in the response."""

    id: str
    ticker: str
    shares: float
    avg_cost: float
    market_value: float
    gain_loss_pct: float = Field(
        description="Gain/loss percentage: ((market_value - avg_cost * shares) / (avg_cost * shares)) * 100"
    )
    created_at: datetime
    updated_at: datetime


class GbmPortfolioListResponse(BaseModel):
    """Schema for the GBM portfolio list response with aggregates."""

    items: list[GbmPortfolioPositionResponse]
    total_market_value: float = Field(description="Sum of all position market values")
    total_gain_loss_pct: float = Field(
        description="Total gain/loss percentage across the portfolio"
    )
    failed_count: int = Field(
        default=0, description="Number of entries that failed decryption"
    )
