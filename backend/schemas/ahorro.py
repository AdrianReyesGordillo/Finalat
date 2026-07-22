"""Pydantic schemas for the Ahorro (Savings) module."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.utils.validators import (
    validate_and_sanitize_name,
    validate_monetary_amount,
)


class AhorroCreate(BaseModel):
    """Schema for creating a new savings entry."""

    amount: float = Field(..., description="Monetary amount (0.01–999,999,999.99)")
    account_name: str = Field(..., description="Account name (max 100 chars)")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        validated = validate_monetary_amount(v, "amount")
        return float(validated)

    @field_validator("account_name")
    @classmethod
    def validate_account_name(cls, v: str) -> str:
        return validate_and_sanitize_name(v, "account_name", 100)


class AhorroUpdate(BaseModel):
    """Schema for updating a savings entry (partial update)."""

    amount: Optional[float] = Field(None, description="Monetary amount (0.01–999,999,999.99)")
    account_name: Optional[str] = Field(None, description="Account name (max 100 chars)")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        validated = validate_monetary_amount(v, "amount")
        return float(validated)

    @field_validator("account_name")
    @classmethod
    def validate_account_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_and_sanitize_name(v, "account_name", 100)


class AhorroResponse(BaseModel):
    """Schema for a single savings entry in the response."""

    id: str
    amount: float
    account_name: str
    created_at: datetime
    updated_at: datetime


class AhorroListResponse(BaseModel):
    """Schema for the savings list response with aggregate total."""

    items: list[AhorroResponse]
    total_savings: float = Field(description="Aggregate total savings amount")
    failed_count: int = Field(
        default=0, description="Number of entries that failed decryption"
    )
