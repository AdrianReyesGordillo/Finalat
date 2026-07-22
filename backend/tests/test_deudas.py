"""Unit tests for the Deudas (Debts) router calculations and schema validation."""

import math
from datetime import date
from decimal import Decimal

import pytest

from backend.routers.deudas import (
    _calculate_estimated_payoff_date,
    _calculate_months_elapsed,
    _calculate_remaining_balance,
    _calculate_total_interest,
)
from backend.schemas.deudas import DeudaCreate, DeudaUpdate
from backend.utils.validators import ValidationError


# ---------------------------------------------------------------------------
# Calculation Helper Tests
# ---------------------------------------------------------------------------


class TestCalculateMonthsElapsed:
    """Tests for _calculate_months_elapsed helper."""

    def test_same_month(self):
        today = date.today()
        assert _calculate_months_elapsed(today) == 0

    def test_one_month_ago(self):
        today = date.today()
        if today.month == 1:
            start = date(today.year - 1, 12, today.day)
        else:
            start = date(today.year, today.month - 1, min(today.day, 28))
        assert _calculate_months_elapsed(start) == 1

    def test_twelve_months_ago(self):
        today = date.today()
        start = date(today.year - 1, today.month, min(today.day, 28))
        assert _calculate_months_elapsed(start) == 12

    def test_future_date_returns_zero(self):
        today = date.today()
        future = date(today.year + 1, today.month, today.day)
        assert _calculate_months_elapsed(future) == 0


class TestCalculateRemainingBalance:
    """Tests for _calculate_remaining_balance helper."""

    def test_no_time_elapsed(self):
        today = date.today()
        result = _calculate_remaining_balance(10000.0, 500.0, today)
        assert result == 10000.0

    def test_partial_payment(self):
        today = date.today()
        # 6 months ago
        if today.month > 6:
            start = date(today.year, today.month - 6, min(today.day, 28))
        else:
            start = date(today.year - 1, today.month + 6, min(today.day, 28))
        result = _calculate_remaining_balance(10000.0, 500.0, start)
        # 10000 - (500 * 6) = 7000
        assert result == 7000.0

    def test_overpaid_returns_zero(self):
        # Start date far enough in the past that payments exceed total
        start = date(2020, 1, 1)
        result = _calculate_remaining_balance(1000.0, 500.0, start)
        assert result == 0.0


class TestCalculateEstimatedPayoffDate:
    """Tests for _calculate_estimated_payoff_date helper."""

    def test_already_paid_off(self):
        result = _calculate_estimated_payoff_date(0.0, 500.0, 10.0, date(2023, 1, 1))
        assert result == "paid"

    def test_zero_payment_returns_indefinite(self):
        result = _calculate_estimated_payoff_date(10000.0, 0.0, 10.0, date(2023, 1, 1))
        assert result == "indefinite"

    def test_payment_less_than_interest_returns_indefinite(self):
        # balance=10000, rate=12% annual -> monthly_rate=1%, interest portion = 100
        # payment=50 which is less than interest
        result = _calculate_estimated_payoff_date(10000.0, 50.0, 12.0, date(2023, 1, 1))
        assert result == "indefinite"

    def test_zero_interest_rate(self):
        # Simple division: 10000 / 500 = 20 months
        result = _calculate_estimated_payoff_date(10000.0, 500.0, 0.0, date(2023, 1, 1))
        # Should return a valid ISO date string
        assert result != "indefinite"
        assert result != "paid"
        # Parse as date
        payoff = date.fromisoformat(result)
        assert payoff > date.today()

    def test_normal_amortization_returns_valid_date(self):
        # 10000 balance, 500/month, 6% interest
        result = _calculate_estimated_payoff_date(10000.0, 500.0, 6.0, date(2023, 1, 1))
        assert result != "indefinite"
        assert result != "paid"
        payoff = date.fromisoformat(result)
        assert payoff > date.today()


class TestCalculateTotalInterest:
    """Tests for _calculate_total_interest helper."""

    def test_zero_interest_rate(self):
        # No interest: total_interest should be 0 or near 0
        # 10000 / 500 = 20 months, 500*20 - 10000 = 0
        result = _calculate_total_interest(10000.0, 500.0, 0.0, 10000.0)
        assert result == 0.0

    def test_normal_interest_positive(self):
        # 10000 at 6% with 500/month
        result = _calculate_total_interest(10000.0, 500.0, 6.0, 10000.0)
        assert result > 0.0

    def test_zero_payment_returns_zero(self):
        result = _calculate_total_interest(10000.0, 0.0, 6.0, 10000.0)
        assert result == 0.0

    def test_payment_less_than_interest_returns_zero(self):
        # 10000 at 12% -> monthly interest = 100, payment = 50
        result = _calculate_total_interest(10000.0, 50.0, 12.0, 10000.0)
        assert result == 0.0


# ---------------------------------------------------------------------------
# Schema Validation Tests
# ---------------------------------------------------------------------------


class TestDeudaCreateSchema:
    """Tests for DeudaCreate Pydantic schema."""

    def test_valid_creation(self):
        data = DeudaCreate(
            creditor_name="Bank of Mexico",
            total_amount=50000.0,
            monthly_payment=2000.0,
            interest_rate=12.5,
            start_date=date(2024, 1, 15),
        )
        assert data.creditor_name == "Bank of Mexico"
        assert data.total_amount == 50000.0
        assert data.monthly_payment == 2000.0
        assert data.interest_rate == 12.5
        assert data.start_date == date(2024, 1, 15)

    def test_interest_rate_zero(self):
        data = DeudaCreate(
            creditor_name="Friend",
            total_amount=1000.0,
            monthly_payment=100.0,
            interest_rate=0.0,
            start_date=date(2024, 6, 1),
        )
        assert data.interest_rate == 0.0

    def test_interest_rate_max(self):
        data = DeudaCreate(
            creditor_name="Lender",
            total_amount=5000.0,
            monthly_payment=500.0,
            interest_rate=100.0,
            start_date=date(2024, 1, 1),
        )
        assert data.interest_rate == 100.0

    def test_interest_rate_over_100_rejected(self):
        with pytest.raises(Exception):
            DeudaCreate(
                creditor_name="Lender",
                total_amount=5000.0,
                monthly_payment=500.0,
                interest_rate=100.01,
                start_date=date(2024, 1, 1),
            )

    def test_interest_rate_negative_rejected(self):
        with pytest.raises(Exception):
            DeudaCreate(
                creditor_name="Lender",
                total_amount=5000.0,
                monthly_payment=500.0,
                interest_rate=-1.0,
                start_date=date(2024, 1, 1),
            )

    def test_creditor_name_too_long_rejected(self):
        with pytest.raises(Exception):
            DeudaCreate(
                creditor_name="A" * 101,
                total_amount=5000.0,
                monthly_payment=500.0,
                interest_rate=10.0,
                start_date=date(2024, 1, 1),
            )

    def test_total_amount_zero_rejected(self):
        with pytest.raises(Exception):
            DeudaCreate(
                creditor_name="Bank",
                total_amount=0.0,
                monthly_payment=500.0,
                interest_rate=10.0,
                start_date=date(2024, 1, 1),
            )


class TestDeudaUpdateSchema:
    """Tests for DeudaUpdate Pydantic schema."""

    def test_partial_update_creditor_only(self):
        data = DeudaUpdate(creditor_name="New Bank")
        assert data.creditor_name == "New Bank"
        assert data.total_amount is None
        assert data.monthly_payment is None

    def test_partial_update_amount(self):
        data = DeudaUpdate(total_amount=75000.0)
        assert data.total_amount == 75000.0
        assert data.creditor_name is None

    def test_all_fields_update(self):
        data = DeudaUpdate(
            creditor_name="Updated Bank",
            total_amount=60000.0,
            monthly_payment=2500.0,
            interest_rate=8.0,
            start_date=date(2024, 3, 1),
        )
        assert data.creditor_name == "Updated Bank"
        assert data.total_amount == 60000.0
        assert data.monthly_payment == 2500.0
        assert data.interest_rate == 8.0
        assert data.start_date == date(2024, 3, 1)
