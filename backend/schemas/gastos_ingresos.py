"""Pydantic schemas for Gastos/Ingresos (Expenses/Income) module."""

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.utils.validators import (
    validate_and_sanitize_description,
    validate_monetary_amount,
    MONETARY_MIN,
    MONETARY_MAX,
)


class EntryType(str, Enum):
    """Type of financial entry."""

    income = "income"
    expense = "expense"


class GastoIngresoCreate(BaseModel):
    """Schema for creating a new expense/income entry."""

    type: EntryType = Field(..., description="Entry type: income or expense")
    amount: Decimal = Field(
        ...,
        ge=MONETARY_MIN,
        le=MONETARY_MAX,
        description="Monetary amount (0.01–999,999,999.99)",
    )
    description: str = Field(
        ...,
        max_length=500,
        description="Description of the entry (max 500 characters)",
    )
    category_id: str = Field(..., description="Category UUID")
    entry_date: date = Field(..., description="Date of the entry")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        return validate_monetary_amount(v, "amount")

    @field_validator("description")
    @classmethod
    def validate_description_field(cls, v: str) -> str:
        return validate_and_sanitize_description(v, "description", 500)


class GastoIngresoUpdate(BaseModel):
    """Schema for updating an existing expense/income entry."""

    type: Optional[EntryType] = Field(None, description="Entry type: income or expense")
    amount: Optional[Decimal] = Field(
        None,
        ge=MONETARY_MIN,
        le=MONETARY_MAX,
        description="Monetary amount (0.01–999,999,999.99)",
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Description of the entry (max 500 characters)",
    )
    category_id: Optional[str] = Field(None, description="Category UUID")
    entry_date: Optional[date] = Field(None, description="Date of the entry")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            return validate_monetary_amount(v, "amount")
        return v

    @field_validator("description")
    @classmethod
    def validate_description_field(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_and_sanitize_description(v, "description", 500)
        return v


class GastoIngresoResponse(BaseModel):
    """Schema for a single expense/income entry in API responses."""

    id: str
    user_id: str
    type: str
    amount: Decimal
    description: str
    category_id: str
    category_name: Optional[str] = None
    entry_date: date
    created_at: str
    updated_at: str


class CategoryCreate(BaseModel):
    """Schema for creating a new category."""

    name: str = Field(..., max_length=50, description="Category name (max 50 characters)")

    @field_validator("name")
    @classmethod
    def validate_name_field(cls, v: str) -> str:
        from backend.utils.validators import validate_and_sanitize_name
        return validate_and_sanitize_name(v, "name", 50)


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: str = Field(..., max_length=50, description="Category name (max 50 characters)")

    @field_validator("name")
    @classmethod
    def validate_name_field(cls, v: str) -> str:
        from backend.utils.validators import validate_and_sanitize_name
        return validate_and_sanitize_name(v, "name", 50)


class CategoryResponse(BaseModel):
    """Schema for a category in API responses."""

    id: str
    user_id: str
    name: str
    is_system: bool
    created_at: str
    updated_at: str


class SummaryEntry(BaseModel):
    """Single category summary entry."""

    category_id: str
    category_name: str
    total_income: Decimal = Decimal("0.00")
    total_expense: Decimal = Decimal("0.00")


class GastoIngresoSummary(BaseModel):
    """Summary of expenses and income grouped by category."""

    period: str
    total_income: Decimal = Decimal("0.00")
    total_expense: Decimal = Decimal("0.00")
    by_category: list[SummaryEntry] = []
