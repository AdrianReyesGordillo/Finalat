"""Deudas (Debts) router — CRUD endpoints for /api/deudas.

Implements:
- GET /api/deudas — List all debt entries for authenticated user
- POST /api/deudas — Create a new debt entry
- PUT /api/deudas/{id} — Update an existing debt entry
- DELETE /api/deudas/{id} — Delete a debt entry (with ownership check)

Integrates: Encryption Service, LRU Cache, Update Tracker.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9
"""

import logging
import math
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.deudas import Deuda
from backend.schemas.deudas import (
    DeudaCreate,
    DeudaListResponse,
    DeudaResponse,
    DeudaUpdate,
)
from backend.services.cache import cache
from backend.services.encryption import EncryptionError, encryption_service
from backend.services.update_tracker import record_module_update
from backend.utils.response import (
    error_response,
    forbidden_response,
    not_found_response,
    success_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/deudas", tags=["deudas"])

MODULE_NAME = "deudas"
CACHE_LIST_KEY = "deudas:list"


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_current_user_id(request: Request) -> str:
    """Extract user_id from request.state (set by auth middleware).

    Returns:
        The authenticated user's Firebase UID.
    """
    return request.state.user_id


# ---------------------------------------------------------------------------
# Calculation helpers
# ---------------------------------------------------------------------------


def _calculate_months_elapsed(start_date: date) -> int:
    """Calculate the number of months elapsed since start_date."""
    today = date.today()
    months = (today.year - start_date.year) * 12 + (today.month - start_date.month)
    return max(months, 0)


def _calculate_remaining_balance(
    total_amount: float, monthly_payment: float, start_date: date
) -> float:
    """Calculate remaining balance: total_amount - (monthly_payment × months_elapsed), min 0."""
    months_elapsed = _calculate_months_elapsed(start_date)
    remaining = total_amount - (monthly_payment * months_elapsed)
    return round(max(remaining, 0.0), 2)


def _calculate_estimated_payoff_date(
    remaining_balance: float,
    monthly_payment: float,
    interest_rate: float,
    start_date: date,
) -> str:
    """Calculate estimated payoff date using amortization formula.

    Formula: months = -ln(1 - (balance * monthly_rate / payment)) / ln(1 + monthly_rate)
    If payment <= interest portion, returns 'indefinite'.
    If remaining_balance is 0, returns 'paid' (already paid off).
    """
    if remaining_balance <= 0:
        return "paid"

    if monthly_payment <= 0:
        return "indefinite"

    monthly_rate = interest_rate / 100.0 / 12.0

    # If interest rate is 0, simple division
    if monthly_rate == 0:
        months_remaining = math.ceil(remaining_balance / monthly_payment)
    else:
        # Check if payment covers interest: payment must be > balance * monthly_rate
        interest_portion = remaining_balance * monthly_rate
        if monthly_payment <= interest_portion:
            return "indefinite"

        # Amortization formula
        try:
            numerator = -math.log(1 - (remaining_balance * monthly_rate / monthly_payment))
            denominator = math.log(1 + monthly_rate)
            months_remaining = math.ceil(numerator / denominator)
        except (ValueError, ZeroDivisionError):
            return "indefinite"

    # Calculate payoff date from today
    today = date.today()
    payoff_year = today.year + (today.month + months_remaining - 1) // 12
    payoff_month = (today.month + months_remaining - 1) % 12 + 1
    try:
        payoff_date = date(payoff_year, payoff_month, min(today.day, 28))
    except ValueError:
        payoff_date = date(payoff_year, payoff_month, 28)

    return payoff_date.isoformat()


def _calculate_total_interest(
    total_amount: float,
    monthly_payment: float,
    interest_rate: float,
    remaining_balance: float,
) -> float:
    """Calculate total interest cost: (monthly_payment × total_months) - total_amount.

    If payment doesn't cover interest, returns 0.
    """
    if monthly_payment <= 0:
        return 0.0

    monthly_rate = interest_rate / 100.0 / 12.0

    if monthly_rate == 0:
        total_months = math.ceil(total_amount / monthly_payment)
    else:
        interest_portion = total_amount * monthly_rate
        if monthly_payment <= interest_portion:
            return 0.0
        try:
            numerator = -math.log(1 - (total_amount * monthly_rate / monthly_payment))
            denominator = math.log(1 + monthly_rate)
            total_months = math.ceil(numerator / denominator)
        except (ValueError, ZeroDivisionError):
            return 0.0

    total_interest = (monthly_payment * total_months) - total_amount
    return round(max(total_interest, 0.0), 2)


def _build_deuda_response(
    entry: Deuda, total_amount: float, monthly_payment: float
) -> dict:
    """Build a DeudaResponse dict from a Deuda model and decrypted values."""
    interest_rate = float(entry.interest_rate)
    remaining_balance = _calculate_remaining_balance(
        total_amount, monthly_payment, entry.start_date
    )
    estimated_payoff_date = _calculate_estimated_payoff_date(
        remaining_balance, monthly_payment, interest_rate, entry.start_date
    )
    total_interest = _calculate_total_interest(
        total_amount, monthly_payment, interest_rate, remaining_balance
    )

    return DeudaResponse(
        id=entry.id,
        creditor_name=entry.creditor_name,
        total_amount=total_amount,
        monthly_payment=monthly_payment,
        interest_rate=interest_rate,
        start_date=entry.start_date,
        remaining_balance=remaining_balance,
        estimated_payoff_date=estimated_payoff_date,
        total_interest=total_interest,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    ).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
async def list_deudas(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all debt entries for the authenticated user.

    Returns the list of entries with aggregate total debt and total monthly payment.
    Entries that fail decryption are excluded with a failed_count indicator.
    """
    # Try cache first
    cached = cache.get(user_id, CACHE_LIST_KEY)
    if cached is not None:
        return JSONResponse(status_code=200, content=success_response(cached))

    # Query database — scoped to user_id
    stmt = select(Deuda).where(Deuda.user_id == user_id).order_by(Deuda.created_at.desc())
    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Decrypt and build response
    items: list[dict] = []
    failed_count = 0
    total_debt = 0.0
    total_monthly_payment = 0.0

    for entry in entries:
        try:
            decrypted_total = float(encryption_service.decrypt(entry.total_amount_encrypted))
            decrypted_monthly = float(encryption_service.decrypt(entry.monthly_payment_encrypted))
            total_debt += decrypted_total
            total_monthly_payment += decrypted_monthly
            items.append(
                _build_deuda_response(entry, decrypted_total, decrypted_monthly)
            )
        except (EncryptionError, ValueError) as exc:
            logger.warning(
                "Failed to decrypt deuda entry %s for user %s: %s",
                entry.id,
                user_id,
                str(exc),
            )
            failed_count += 1

    response_data = DeudaListResponse(
        items=[DeudaResponse(**item) for item in items],
        total_debt=round(total_debt, 2),
        total_monthly_payment=round(total_monthly_payment, 2),
        failed_count=failed_count,
    ).model_dump(mode="json")

    # Store in cache
    cache.set(user_id, CACHE_LIST_KEY, response_data)

    return JSONResponse(status_code=200, content=success_response(response_data))


@router.post("")
async def create_deuda(
    body: DeudaCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new debt entry.

    Encrypts total_amount and monthly_payment before persisting.
    Invalidates cache and records update in the tracker.
    """
    # Encrypt monetary fields
    try:
        encrypted_total = encryption_service.encrypt(str(body.total_amount))
        encrypted_monthly = encryption_service.encrypt(str(body.monthly_payment))
    except EncryptionError:
        return JSONResponse(
            status_code=500,
            content=error_response(
                "ENCRYPTION_ERROR", "Could not process encrypted data."
            ),
        )

    # Create record
    new_entry = Deuda(
        user_id=user_id,
        creditor_name=body.creditor_name,
        total_amount_encrypted=encrypted_total,
        monthly_payment_encrypted=encrypted_monthly,
        interest_rate=body.interest_rate,
        start_date=body.start_date,
    )
    db.add(new_entry)
    await db.flush()
    await db.refresh(new_entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Build response
    response_item = _build_deuda_response(
        new_entry, body.total_amount, body.monthly_payment
    )

    return JSONResponse(status_code=201, content=success_response(response_item))


@router.put("/{entry_id}")
async def update_deuda(
    entry_id: str,
    body: DeudaUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing debt entry.

    Verifies ownership, encrypts updated monetary fields, invalidates cache,
    and records update in the tracker.
    """
    # Fetch entry scoped to user
    stmt = select(Deuda).where(Deuda.id == entry_id, Deuda.user_id == user_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        # Check if entry exists for another user (return 403)
        stmt_any = select(Deuda).where(Deuda.id == entry_id)
        result_any = await db.execute(stmt_any)
        entry_any = result_any.scalar_one_or_none()
        if entry_any:
            return JSONResponse(
                status_code=403,
                content=forbidden_response("Access denied to this debt entry."),
            )
        return JSONResponse(
            status_code=404,
            content=not_found_response("Debt entry not found."),
        )

    # Apply updates
    if body.creditor_name is not None:
        entry.creditor_name = body.creditor_name

    if body.total_amount is not None:
        try:
            entry.total_amount_encrypted = encryption_service.encrypt(str(body.total_amount))
        except EncryptionError:
            return JSONResponse(
                status_code=500,
                content=error_response(
                    "ENCRYPTION_ERROR", "Could not process encrypted data."
                ),
            )

    if body.monthly_payment is not None:
        try:
            entry.monthly_payment_encrypted = encryption_service.encrypt(str(body.monthly_payment))
        except EncryptionError:
            return JSONResponse(
                status_code=500,
                content=error_response(
                    "ENCRYPTION_ERROR", "Could not process encrypted data."
                ),
            )

    if body.interest_rate is not None:
        entry.interest_rate = body.interest_rate

    if body.start_date is not None:
        entry.start_date = body.start_date

    await db.flush()
    await db.refresh(entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Decrypt fields for response
    try:
        decrypted_total = float(encryption_service.decrypt(entry.total_amount_encrypted))
        decrypted_monthly = float(encryption_service.decrypt(entry.monthly_payment_encrypted))
    except (EncryptionError, ValueError):
        decrypted_total = body.total_amount if body.total_amount is not None else 0.0
        decrypted_monthly = body.monthly_payment if body.monthly_payment is not None else 0.0

    response_item = _build_deuda_response(entry, decrypted_total, decrypted_monthly)

    return JSONResponse(status_code=200, content=success_response(response_item))


@router.delete("/{entry_id}")
async def delete_deuda(
    entry_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a debt entry.

    Verifies ownership (returns 403 for cross-user access attempts).
    """
    # Fetch entry scoped to user (ownership check)
    stmt = select(Deuda).where(Deuda.id == entry_id, Deuda.user_id == user_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        # Check if entry exists for another user (return 403)
        stmt_any = select(Deuda).where(Deuda.id == entry_id)
        result_any = await db.execute(stmt_any)
        entry_any = result_any.scalar_one_or_none()
        if entry_any:
            return JSONResponse(
                status_code=403,
                content=forbidden_response("Access denied to this debt entry."),
            )
        return JSONResponse(
            status_code=404,
            content=not_found_response("Debt entry not found."),
        )

    await db.delete(entry)
    await db.flush()

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    return JSONResponse(
        status_code=200,
        content=success_response({"message": "Debt entry deleted successfully."}),
    )
