"""Pydantic schemas for the Afore (Pension Fund) module."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.utils.validators import (
    validate_and_sanitize_name,
    validate_monetary_amount,
)


class AforeCreate(BaseModel):
    """Schema for creating a new Afore record."""

    provider_name: str = Field(..., description="Afore provider name (max 100 chars)")
    balance: float = Field(..., description="Current balance (0.01–999,999,999.99)")
    last_update_date: date = Field(..., description="Date of last Afore statement update")

    @field_validator("provider_name")
    @classmethod
    def validate_provider_name(cls, v: str) -> str:
        return validate_and_sanitize_name(v, "provider_name", 100)

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, v: float) -> float:
        validated = validate_monetary_amount(v, "balance")
        return float(validated)


class AforeUpdate(BaseModel):
    """Schema for updating an Afore record (partial update)."""

    provider_name: Optional[str] = Field(None, description="Afore provider name (max 100 chars)")
    balance: Optional[float] = Field(None, description="Current balance (0.01–999,999,999.99)")
    last_update_date: Optional[date] = Field(None, description="Date of last Afore statement update")

    @field_validator("provider_name")
    @classmethod
    def validate_provider_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_and_sanitize_name(v, "provider_name", 100)

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        validated = validate_monetary_amount(v, "balance")
        return float(validated)


class AforeResponse(BaseModel):
    """Schema for a single Afore record in the response."""

    id: str
    provider_name: str
    balance: float
    last_update_date: date
    created_at: datetime
    updated_at: datetime


class AforeListResponse(BaseModel):
    """Schema for the Afore list response with aggregate total."""

    items: list[AforeResponse]
    total_balance: float = Field(description="Aggregate total Afore balance across all providers")
    failed_count: int = Field(
        default=0, description="Number of entries that failed decryption"
    )
