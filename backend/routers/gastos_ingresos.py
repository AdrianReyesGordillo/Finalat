"""Gastos/Ingresos (Expenses/Income) router — CRUD + summary endpoints.

Implements:
- GET /api/gastos-ingresos — List all entries for authenticated user
- POST /api/gastos-ingresos — Create a new expense/income entry
- PUT /api/gastos-ingresos/{id} — Update an existing entry
- DELETE /api/gastos-ingresos/{id} — Delete an entry (with ownership check)
- GET /api/gastos-ingresos/summary — Income/expense totals grouped by category

Integrates: Encryption Service, LRU Cache, Update Tracker.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.categories import Category
from backend.models.database import get_db
from backend.models.gastos_ingresos import GastoIngreso
from backend.schemas.gastos_ingresos import (
    GastoIngresoCreate,
    GastoIngresoResponse,
    GastoIngresoSummary,
    GastoIngresoUpdate,
    SummaryEntry,
)
from backend.services.cache import cache
from backend.services.encryption import EncryptionError, encryption_service
from backend.services.update_tracker import record_module_update
from backend.utils.response import (
    error_response,
    forbidden_response,
    not_found_response,
    success_response,
    validation_error_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gastos-ingresos", tags=["gastos-ingresos"])

MODULE_NAME = "gastos_ingresos"
CACHE_LIST_KEY = "gastos_ingresos:list"
CACHE_SUMMARY_PREFIX = "gastos_ingresos:summary"


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_current_user_id(request: Request) -> str:
    """Extract user_id from request.state (set by auth middleware)."""
    return request.state.user_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _validate_category_ownership(
    db: AsyncSession, category_id: str, user_id: str
) -> Category | None:
    """Validate that a category_id belongs to the given user.

    Returns the category if valid, None otherwise.
    """
    stmt = select(Category).where(
        Category.id == category_id, Category.user_id == user_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _get_period_start(period: str, reference_date: date) -> date:
    """Calculate the start date for a given period relative to a reference date."""
    if period == "daily":
        return reference_date
    elif period == "weekly":
        return reference_date - timedelta(days=reference_date.weekday())
    elif period == "monthly":
        return reference_date.replace(day=1)
    elif period == "yearly":
        return reference_date.replace(month=1, day=1)
    else:
        # Default to monthly
        return reference_date.replace(day=1)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/summary")
async def get_summary(
    request: Request,
    period: str = Query(
        default="monthly",
        description="Period for grouping: daily, weekly, monthly, yearly",
    ),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get income/expense totals grouped by category for the given period.

    Returns total income, total expense, and breakdown by category.
    """
    # Validate period
    valid_periods = ("daily", "weekly", "monthly", "yearly")
    if period not in valid_periods:
        return JSONResponse(
            status_code=400,
            content=validation_error_response(
                f"Invalid period. Must be one of: {', '.join(valid_periods)}",
                fields={"period": f"Must be one of: {', '.join(valid_periods)}"},
            ),
        )

    # Try cache first
    cache_key = f"{CACHE_SUMMARY_PREFIX}:{period}"
    cached = cache.get(user_id, cache_key)
    if cached is not None:
        return JSONResponse(status_code=200, content=success_response(cached))

    # Determine period boundaries
    today = date.today()
    period_start = _get_period_start(period, today)

    # Query entries in the period
    stmt = (
        select(GastoIngreso)
        .where(
            GastoIngreso.user_id == user_id,
            GastoIngreso.entry_date >= period_start,
        )
        .order_by(GastoIngreso.entry_date.desc())
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Get user categories for name lookup
    cat_stmt = select(Category).where(Category.user_id == user_id)
    cat_result = await db.execute(cat_stmt)
    categories = {cat.id: cat.name for cat in cat_result.scalars().all()}

    # Aggregate by category
    category_totals: dict[str, dict] = {}
    total_income = Decimal("0.00")
    total_expense = Decimal("0.00")

    for entry in entries:
        try:
            decrypted_amount = encryption_service.decrypt(entry.amount_encrypted)
            amount = Decimal(decrypted_amount)
        except (EncryptionError, ValueError):
            logger.warning(
                "Failed to decrypt gastos_ingresos entry %s for user %s",
                entry.id,
                user_id,
            )
            continue

        cat_id = entry.category_id
        if cat_id not in category_totals:
            category_totals[cat_id] = {
                "category_id": cat_id,
                "category_name": categories.get(cat_id, "Unknown"),
                "total_income": Decimal("0.00"),
                "total_expense": Decimal("0.00"),
            }

        if entry.type == "income":
            category_totals[cat_id]["total_income"] += amount
            total_income += amount
        else:
            category_totals[cat_id]["total_expense"] += amount
            total_expense += amount

    by_category = [
        SummaryEntry(
            category_id=v["category_id"],
            category_name=v["category_name"],
            total_income=round(v["total_income"], 2),
            total_expense=round(v["total_expense"], 2),
        ).model_dump(mode="json")
        for v in category_totals.values()
    ]

    summary = GastoIngresoSummary(
        period=period,
        total_income=round(total_income, 2),
        total_expense=round(total_expense, 2),
        by_category=[SummaryEntry(**item) for item in by_category],
    ).model_dump(mode="json")

    # Store in cache
    cache.set(user_id, cache_key, summary)

    return JSONResponse(status_code=200, content=success_response(summary))


@router.get("")
async def list_gastos_ingresos(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all expenses/income entries for the authenticated user.

    Returns the list of entries with aggregate totals.
    Entries that fail decryption are excluded with a failed_count indicator.
    """
    # Try cache first
    cached = cache.get(user_id, CACHE_LIST_KEY)
    if cached is not None:
        return JSONResponse(status_code=200, content=success_response(cached))

    # Query database — scoped to user_id
    stmt = (
        select(GastoIngreso)
        .where(GastoIngreso.user_id == user_id)
        .order_by(GastoIngreso.entry_date.desc())
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Get user categories for name lookup
    cat_stmt = select(Category).where(Category.user_id == user_id)
    cat_result = await db.execute(cat_stmt)
    categories = {cat.id: cat.name for cat in cat_result.scalars().all()}

    # Decrypt and build response
    items: list[dict] = []
    failed_count = 0
    total_income = Decimal("0.00")
    total_expense = Decimal("0.00")

    for entry in entries:
        try:
            decrypted_amount = encryption_service.decrypt(entry.amount_encrypted)
            decrypted_description = encryption_service.decrypt(
                entry.description_encrypted
            )
            amount = Decimal(decrypted_amount)

            if entry.type == "income":
                total_income += amount
            else:
                total_expense += amount

            items.append(
                GastoIngresoResponse(
                    id=entry.id,
                    user_id=entry.user_id,
                    type=entry.type,
                    amount=amount,
                    description=decrypted_description,
                    category_id=entry.category_id,
                    category_name=categories.get(entry.category_id),
                    entry_date=entry.entry_date,
                    created_at=entry.created_at.isoformat()
                    if entry.created_at
                    else "",
                    updated_at=entry.updated_at.isoformat()
                    if entry.updated_at
                    else "",
                ).model_dump(mode="json")
            )
        except (EncryptionError, ValueError) as exc:
            logger.warning(
                "Failed to decrypt gastos_ingresos entry %s for user %s",
                entry.id,
                user_id,
            )
            failed_count += 1

    response_data = {
        "items": items,
        "total_income": str(round(total_income, 2)),
        "total_expense": str(round(total_expense, 2)),
        "failed_count": failed_count,
    }

    # Store in cache
    cache.set(user_id, CACHE_LIST_KEY, response_data)

    return JSONResponse(status_code=200, content=success_response(response_data))


@router.post("")
async def create_gasto_ingreso(
    body: GastoIngresoCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new expense/income entry.

    Validates category ownership, encrypts amount and description before
    persisting. Invalidates cache and records update in the tracker.
    """
    # Validate category belongs to the user
    category = await _validate_category_ownership(db, body.category_id, user_id)
    if category is None:
        return JSONResponse(
            status_code=400,
            content=validation_error_response(
                "Invalid category. The category does not exist or does not belong to you.",
                fields={"category_id": "Category not found or does not belong to user."},
            ),
        )

    # Encrypt amount and description
    try:
        encrypted_amount = encryption_service.encrypt(str(body.amount))
        encrypted_description = encryption_service.encrypt(body.description)
    except EncryptionError:
        return JSONResponse(
            status_code=500,
            content=error_response(
                "ENCRYPTION_ERROR", "Could not process encrypted data."
            ),
        )

    # Create record
    new_entry = GastoIngreso(
        user_id=user_id,
        type=body.type.value,
        amount_encrypted=encrypted_amount,
        description_encrypted=encrypted_description,
        category_id=body.category_id,
        entry_date=body.entry_date,
    )
    db.add(new_entry)
    await db.flush()
    await db.refresh(new_entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Build response
    response_item = GastoIngresoResponse(
        id=new_entry.id,
        user_id=new_entry.user_id,
        type=new_entry.type,
        amount=body.amount,
        description=body.description,
        category_id=new_entry.category_id,
        category_name=category.name,
        entry_date=new_entry.entry_date,
        created_at=new_entry.created_at.isoformat() if new_entry.created_at else "",
        updated_at=new_entry.updated_at.isoformat() if new_entry.updated_at else "",
    ).model_dump(mode="json")

    return JSONResponse(status_code=201, content=success_response(response_item))


@router.put("/{entry_id}")
async def update_gasto_ingreso(
    entry_id: str,
    body: GastoIngresoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing expense/income entry.

    Verifies ownership, validates category if changed, encrypts updated fields,
    invalidates cache, and records update in the tracker.
    """
    # Fetch entry scoped to user
    stmt = select(GastoIngreso).where(
        GastoIngreso.id == entry_id, GastoIngreso.user_id == user_id
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        # Check if entry exists but belongs to another user (403 vs 404)
        exists_stmt = select(GastoIngreso).where(GastoIngreso.id == entry_id)
        exists_result = await db.execute(exists_stmt)
        if exists_result.scalar_one_or_none():
            return JSONResponse(
                status_code=403,
                content=forbidden_response(
                    "You do not have permission to access this entry."
                ),
            )
        return JSONResponse(
            status_code=404,
            content=not_found_response("Expense/income entry not found."),
        )

    # Validate category if being changed
    if body.category_id is not None:
        category = await _validate_category_ownership(db, body.category_id, user_id)
        if category is None:
            return JSONResponse(
                status_code=400,
                content=validation_error_response(
                    "Invalid category. The category does not exist or does not belong to you.",
                    fields={
                        "category_id": "Category not found or does not belong to user."
                    },
                ),
            )

    # Apply updates
    if body.type is not None:
        entry.type = body.type.value

    if body.amount is not None:
        try:
            entry.amount_encrypted = encryption_service.encrypt(str(body.amount))
        except EncryptionError:
            return JSONResponse(
                status_code=500,
                content=error_response(
                    "ENCRYPTION_ERROR", "Could not process encrypted data."
                ),
            )

    if body.description is not None:
        try:
            entry.description_encrypted = encryption_service.encrypt(body.description)
        except EncryptionError:
            return JSONResponse(
                status_code=500,
                content=error_response(
                    "ENCRYPTION_ERROR", "Could not process encrypted data."
                ),
            )

    if body.category_id is not None:
        entry.category_id = body.category_id

    if body.entry_date is not None:
        entry.entry_date = body.entry_date

    await db.flush()
    await db.refresh(entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Decrypt for response
    try:
        decrypted_amount = Decimal(encryption_service.decrypt(entry.amount_encrypted))
        decrypted_description = encryption_service.decrypt(entry.description_encrypted)
    except (EncryptionError, ValueError):
        decrypted_amount = body.amount if body.amount is not None else Decimal("0.00")
        decrypted_description = body.description if body.description is not None else ""

    # Get category name
    cat_stmt = select(Category).where(
        Category.id == entry.category_id, Category.user_id == user_id
    )
    cat_result = await db.execute(cat_stmt)
    cat = cat_result.scalar_one_or_none()

    response_item = GastoIngresoResponse(
        id=entry.id,
        user_id=entry.user_id,
        type=entry.type,
        amount=decrypted_amount,
        description=decrypted_description,
        category_id=entry.category_id,
        category_name=cat.name if cat else None,
        entry_date=entry.entry_date,
        created_at=entry.created_at.isoformat() if entry.created_at else "",
        updated_at=entry.updated_at.isoformat() if entry.updated_at else "",
    ).model_dump(mode="json")

    return JSONResponse(status_code=200, content=success_response(response_item))


@router.delete("/{entry_id}")
async def delete_gasto_ingreso(
    entry_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete an expense/income entry.

    Verifies ownership before deletion. Returns 403 if entry belongs to
    another user.
    """
    # Fetch entry scoped to user (ownership check)
    stmt = select(GastoIngreso).where(
        GastoIngreso.id == entry_id, GastoIngreso.user_id == user_id
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        # Check if entry exists but belongs to another user (403 vs 404)
        exists_stmt = select(GastoIngreso).where(GastoIngreso.id == entry_id)
        exists_result = await db.execute(exists_stmt)
        if exists_result.scalar_one_or_none():
            return JSONResponse(
                status_code=403,
                content=forbidden_response(
                    "You do not have permission to access this entry."
                ),
            )
        return JSONResponse(
            status_code=404,
            content=not_found_response("Expense/income entry not found."),
        )

    await db.delete(entry)
    await db.flush()

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    return JSONResponse(
        status_code=200,
        content=success_response(
            {"message": "Expense/income entry deleted successfully."}
        ),
    )
