"""Pydantic schemas for the Deudas (Debts) module."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.utils.validators import (
    validate_and_sanitize_name,
    validate_monetary_amount,
)


class DeudaCreate(BaseModel):
    """Schema for creating a new debt entry."""

    creditor_name: str = Field(..., description="Creditor name (max 100 chars)")
    total_amount: float = Field(..., description="Total debt amount (0.01–999,999,999.99)")
    monthly_payment: float = Field(..., description="Monthly payment amount (0.01–999,999,999.99)")
    interest_rate: float = Field(..., ge=0.0, le=100.0, description="Annual interest rate (0.00–100.00)")
    start_date: date = Field(..., description="Start date of the debt")

    @field_validator("creditor_name")
    @classmethod
    def validate_creditor_name(cls, v: str) -> str:
        return validate_and_sanitize_name(v, "creditor_name", 100)

    @field_validator("total_amount")
    @classmethod
    def validate_total_amount(cls, v: float) -> float:
        validated = validate_monetary_amount(v, "total_amount")
        return float(validated)

    @field_validator("monthly_payment")
    @classmethod
    def validate_monthly_payment(cls, v: float) -> float:
        validated = validate_monetary_amount(v, "monthly_payment")
        return float(validated)


class DeudaUpdate(BaseModel):
    """Schema for updating a debt entry (partial update)."""

    creditor_name: Optional[str] = Field(None, description="Creditor name (max 100 chars)")
    total_amount: Optional[float] = Field(None, description="Total debt amount (0.01–999,999,999.99)")
    monthly_payment: Optional[float] = Field(None, description="Monthly payment amount (0.01–999,999,999.99)")
    interest_rate: Optional[float] = Field(None, ge=0.0, le=100.0, description="Annual interest rate (0.00–100.00)")
    start_date: Optional[date] = Field(None, description="Start date of the debt")

    @field_validator("creditor_name")
    @classmethod
    def validate_creditor_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_and_sanitize_name(v, "creditor_name", 100)

    @field_validator("total_amount")
    @classmethod
    def validate_total_amount(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        validated = validate_monetary_amount(v, "total_amount")
        return float(validated)

    @field_validator("monthly_payment")
    @classmethod
    def validate_monthly_payment(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return v
        validated = validate_monetary_amount(v, "monthly_payment")
        return float(validated)


class DeudaResponse(BaseModel):
    """Schema for a single debt entry in the response."""

    id: str
    creditor_name: str
    total_amount: float
    monthly_payment: float
    interest_rate: float
    start_date: date
    remaining_balance: float = Field(description="Calculated remaining balance")
    estimated_payoff_date: str = Field(description="Estimated payoff date or 'indefinite'")
    total_interest: float = Field(description="Total interest cost over the life of the debt")
    created_at: datetime
    updated_at: datetime


class DeudaListResponse(BaseModel):
    """Schema for the debts list response with aggregate totals."""

    items: list[DeudaResponse]
    total_debt: float = Field(description="Aggregate total debt across all entries")
    total_monthly_payment: float = Field(description="Aggregate monthly payment across all entries")
    failed_count: int = Field(
        default=0, description="Number of entries that failed decryption"
    )
