"""Pydantic schemas for the Aportaciones (Contributions) module."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.utils.validators import (
    validate_and_sanitize_name,
    validate_monetary_amount,
)

# Valid frequency values
VALID_FREQUENCIES = ("weekly", "biweekly", "monthly")

# Frequency multipliers for annual projection
FREQUENCY_MULTIPLIERS = {
    "weekly": 52,
    "biweekly": 26,
    "monthly": 12,
}


class AportacionCreate(BaseModel):
    """Schema for creating a new contribution schedule."""

    amount: float = Field(..., description="Contribution amount (0.01–999,999,999.99)")
    frequency: str = Field(..., description="Frequency: weekly, biweekly, or monthly")
    target_name: str = Field(..., description="Target instrument/account name (max 100 chars)")
    start_date: date = Field(..., description="Start date of the contribution schedule")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        validated = validate_monetary_amount(v, "amount")
        return float(validated)

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        v_lower = v.strip().lower()
        if v_lower not in VALID_FREQUENCIES:
            raise ValueError(
                f"Invalid frequency '{v}'. Must be one of: {', '.join(VALID_FREQUENCIES)}"
            )
        return v_lower

    @field_validator("target_name")
    @classmethod
    def validate_target_name(cls, v: str) -> str:
        return validate_and_sanitize_name(v, "target_name", 100)


class AportacionUpdate(BaseModel):
    """Schema for updating a contribution schedule (partial update)."""

    amount: Optional[float] = Field(None, description="Contribution amount (0.01–999,999,999.99)")
    frequency: Optional[str] = Field(None, description="Frequency: weekly, biweekly, or monthly")
    target_name: Optional[str] = Field(None, description="Target instrument/account name (max 100 chars)")
    start_date: Optional[date] = Field(None, description="Start date of the contribution schedule")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        validated = validate_monetary_amount(v, "amount")
        return float(validated)

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_lower = v.strip().lower()
        if v_lower not in VALID_FREQUENCIES:
            raise ValueError(
                f"Invalid frequency '{v}'. Must be one of: {', '.join(VALID_FREQUENCIES)}"
            )
        return v_lower

    @field_validator("target_name")
    @classmethod
    def validate_target_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_and_sanitize_name(v, "target_name", 100)


class AportacionResponse(BaseModel):
    """Schema for a single contribution schedule in the response."""

    id: str
    amount: float
    frequency: str
    target_name: str
    start_date: date
    annual_projection: float = Field(
        description="Projected annual contribution (amount x frequency multiplier)"
    )
    created_at: datetime
    updated_at: datetime


class AportacionListResponse(BaseModel):
    """Schema for the contributions list response with aggregate annual total."""

    items: list[AportacionResponse]
    total_annual_projection: float = Field(
        description="Aggregate annual projection across all schedules"
    )
    failed_count: int = Field(
        default=0, description="Number of entries that failed decryption"
    )
