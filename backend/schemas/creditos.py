"""Pydantic schemas for the Creditos (Credit Cards) module.

Defines request and response models for credit card CRUD operations.
Requirements: 4.1, 4.2, 4.3, 4.5, 4.6, 4.7
"""

from datetime import datetime
from typing import Union

from pydantic import BaseModel, Field, field_validator

from backend.utils.validators import (
    validate_and_sanitize_name,
    validate_monetary_amount,
    ValidationError as ValidatorError,
)


class CreditoCreate(BaseModel):
    """Schema for creating a new credit card record."""

    card_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the credit card (max 100 characters).",
    )
    balance: float = Field(
        ...,
        ge=0.0,
        le=999999999.99,
        description="Current balance (0.00–999,999,999.99).",
    )
    limit: float = Field(
        ...,
        ge=0.0,
        le=999999999.99,
        description="Credit limit (0.00–999,999,999.99).",
    )
    minimum_payment: float = Field(
        ...,
        ge=0.0,
        le=999999999.99,
        description="Minimum payment amount (0.00–999,999,999.99).",
    )

    @field_validator("card_name")
    @classmethod
    def validate_card_name(cls, v: str) -> str:
        """Validate and sanitize the card name."""
        try:
            return validate_and_sanitize_name(v, field_name="card_name")
        except ValidatorError as e:
            raise ValueError(e.message)

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, v: float) -> float:
        """Validate balance is within bounds (allows 0.00)."""
        try:
            validated = validate_monetary_amount(v, field_name="balance")
            return float(validated)
        except ValidatorError:
            # Allow 0.00 for balance specifically
            if v == 0.0:
                return 0.0
            raise ValueError(
                "Balance must be between 0.00 and 999,999,999.99."
            )

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: float) -> float:
        """Validate limit is within bounds (allows 0.00)."""
        try:
            validated = validate_monetary_amount(v, field_name="limit")
            return float(validated)
        except ValidatorError:
            # Allow 0.00 for limit specifically
            if v == 0.0:
                return 0.0
            raise ValueError(
                "Limit must be between 0.00 and 999,999,999.99."
            )

    @field_validator("minimum_payment")
    @classmethod
    def validate_minimum_payment(cls, v: float) -> float:
        """Validate minimum payment is within bounds (allows 0.00)."""
        try:
            validated = validate_monetary_amount(v, field_name="minimum_payment")
            return float(validated)
        except ValidatorError:
            # Allow 0.00 for minimum_payment specifically
            if v == 0.0:
                return 0.0
            raise ValueError(
                "Minimum payment must be between 0.00 and 999,999,999.99."
            )


class CreditoUpdate(BaseModel):
    """Schema for updating an existing credit card record.

    All fields are optional; only provided fields are updated.
    """

    card_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Name of the credit card (max 100 characters).",
    )
    balance: float | None = Field(
        default=None,
        ge=0.0,
        le=999999999.99,
        description="Current balance (0.00–999,999,999.99).",
    )
    limit: float | None = Field(
        default=None,
        ge=0.0,
        le=999999999.99,
        description="Credit limit (0.00–999,999,999.99).",
    )
    minimum_payment: float | None = Field(
        default=None,
        ge=0.0,
        le=999999999.99,
        description="Minimum payment amount (0.00–999,999,999.99).",
    )

    @field_validator("card_name")
    @classmethod
    def validate_card_name(cls, v: str | None) -> str | None:
        """Validate and sanitize the card name if provided."""
        if v is None:
            return v
        try:
            return validate_and_sanitize_name(v, field_name="card_name")
        except ValidatorError as e:
            raise ValueError(e.message)

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, v: float | None) -> float | None:
        """Validate balance if provided."""
        if v is None:
            return v
        try:
            validated = validate_monetary_amount(v, field_name="balance")
            return float(validated)
        except ValidatorError:
            if v == 0.0:
                return 0.0
            raise ValueError(
                "Balance must be between 0.00 and 999,999,999.99."
            )

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: float | None) -> float | None:
        """Validate limit if provided."""
        if v is None:
            return v
        try:
            validated = validate_monetary_amount(v, field_name="limit")
            return float(validated)
        except ValidatorError:
            if v == 0.0:
                return 0.0
            raise ValueError(
                "Limit must be between 0.00 and 999,999,999.99."
            )

    @field_validator("minimum_payment")
    @classmethod
    def validate_minimum_payment(cls, v: float | None) -> float | None:
        """Validate minimum payment if provided."""
        if v is None:
            return v
        try:
            validated = validate_monetary_amount(v, field_name="minimum_payment")
            return float(validated)
        except ValidatorError:
            if v == 0.0:
                return 0.0
            raise ValueError(
                "Minimum payment must be between 0.00 and 999,999,999.99."
            )


class CreditoResponse(BaseModel):
    """Schema for a single credit card in API responses."""

    id: str
    card_name: str
    balance: float
    limit: float
    minimum_payment: float
    utilization: Union[float, str] = Field(
        description="Credit utilization percentage (balance/limit × 100) or 'N/A' if limit is 0."
    )
    created_at: datetime
    updated_at: datetime


class CreditoListResponse(BaseModel):
    """Schema for the list credit cards response."""

    items: list[CreditoResponse]
    total_balance: float = Field(description="Sum of all credit card balances.")
    failed_count: int = Field(
        default=0,
        description="Number of records that failed decryption.",
    )
