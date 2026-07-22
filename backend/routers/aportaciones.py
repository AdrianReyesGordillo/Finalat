"""Aportaciones (Contributions) router — CRUD endpoints for /api/aportaciones.

Implements:
- GET /api/aportaciones — List all contribution schedules for authenticated user
- POST /api/aportaciones — Create a new contribution schedule
- PUT /api/aportaciones/{id} — Update an existing contribution schedule
- DELETE /api/aportaciones/{id} — Delete a contribution schedule (with ownership check)

Integrates: Encryption Service, LRU Cache, Update Tracker.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7
"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.aportaciones import Aportacion
from backend.models.database import get_db
from backend.schemas.aportaciones import (
    FREQUENCY_MULTIPLIERS,
    AportacionCreate,
    AportacionListResponse,
    AportacionResponse,
    AportacionUpdate,
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

router = APIRouter(prefix="/api/aportaciones", tags=["aportaciones"])

MODULE_NAME = "aportaciones"
CACHE_LIST_KEY = "aportaciones:list"


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
# Helpers
# ---------------------------------------------------------------------------


def _calculate_annual_projection(amount: float, frequency: str) -> float:
    """Calculate projected annual contribution based on frequency.

    weekly: amount × 52
    biweekly: amount × 26
    monthly: amount × 12
    """
    multiplier = FREQUENCY_MULTIPLIERS.get(frequency, 12)
    return round(amount * multiplier, 2)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
async def list_aportaciones(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all contribution schedules for the authenticated user.

    Returns the list of entries with aggregate annual projection total.
    Entries that fail decryption are excluded with a failed_count indicator.
    """
    # Try cache first
    cached = cache.get(user_id, CACHE_LIST_KEY)
    if cached is not None:
        return JSONResponse(status_code=200, content=success_response(cached))

    # Query database — scoped to user_id
    stmt = (
        select(Aportacion)
        .where(Aportacion.user_id == user_id)
        .order_by(Aportacion.created_at.desc())
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Decrypt and build response
    items: list[dict] = []
    failed_count = 0
    total_annual_projection = 0.0

    for entry in entries:
        try:
            decrypted_amount = encryption_service.decrypt(entry.amount_encrypted)
            amount = float(decrypted_amount)
            annual_projection = _calculate_annual_projection(amount, entry.frequency)
            total_annual_projection += annual_projection
            items.append(
                AportacionResponse(
                    id=entry.id,
                    amount=amount,
                    frequency=entry.frequency,
                    target_name=entry.target_name,
                    start_date=entry.start_date,
                    annual_projection=annual_projection,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at,
                ).model_dump(mode="json")
            )
        except (EncryptionError, ValueError) as exc:
            logger.warning(
                "Failed to decrypt aportacion entry %s for user %s: %s",
                entry.id,
                user_id,
                str(exc),
            )
            failed_count += 1

    response_data = AportacionListResponse(
        items=[AportacionResponse(**item) for item in items],
        total_annual_projection=round(total_annual_projection, 2),
        failed_count=failed_count,
    ).model_dump(mode="json")

    # Store in cache
    cache.set(user_id, CACHE_LIST_KEY, response_data)

    return JSONResponse(status_code=200, content=success_response(response_data))


@router.post("")
async def create_aportacion(
    body: AportacionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new contribution schedule.

    Encrypts the amount before persisting. Invalidates cache and
    records update in the tracker.
    """
    # Encrypt amount
    try:
        encrypted_amount = encryption_service.encrypt(str(body.amount))
    except EncryptionError:
        return JSONResponse(
            status_code=500,
            content=error_response(
                "ENCRYPTION_ERROR", "Could not process encrypted data."
            ),
        )

    # Create record
    new_entry = Aportacion(
        user_id=user_id,
        amount_encrypted=encrypted_amount,
        frequency=body.frequency,
        target_name=body.target_name,
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
    annual_projection = _calculate_annual_projection(body.amount, body.frequency)
    response_item = AportacionResponse(
        id=new_entry.id,
        amount=body.amount,
        frequency=new_entry.frequency,
        target_name=new_entry.target_name,
        start_date=new_entry.start_date,
        annual_projection=annual_projection,
        created_at=new_entry.created_at,
        updated_at=new_entry.updated_at,
    ).model_dump(mode="json")

    return JSONResponse(status_code=201, content=success_response(response_item))


@router.put("/{entry_id}")
async def update_aportacion(
    entry_id: str,
    body: AportacionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing contribution schedule.

    Verifies ownership, encrypts updated amount, invalidates cache,
    and records update in the tracker.
    """
    # Fetch entry scoped to user
    stmt = select(Aportacion).where(
        Aportacion.id == entry_id, Aportacion.user_id == user_id
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        # Check if entry exists for another user (return 403)
        stmt_any = select(Aportacion).where(Aportacion.id == entry_id)
        result_any = await db.execute(stmt_any)
        entry_any = result_any.scalar_one_or_none()
        if entry_any:
            return JSONResponse(
                status_code=403,
                content=forbidden_response(
                    "Access denied to this contribution entry."
                ),
            )
        return JSONResponse(
            status_code=404,
            content=not_found_response("Contribution entry not found."),
        )

    # Apply updates
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

    if body.frequency is not None:
        entry.frequency = body.frequency

    if body.target_name is not None:
        entry.target_name = body.target_name

    if body.start_date is not None:
        entry.start_date = body.start_date

    await db.flush()
    await db.refresh(entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Decrypt amount for response
    try:
        decrypted_amount = float(encryption_service.decrypt(entry.amount_encrypted))
    except (EncryptionError, ValueError):
        decrypted_amount = body.amount if body.amount is not None else 0.0

    annual_projection = _calculate_annual_projection(decrypted_amount, entry.frequency)

    response_item = AportacionResponse(
        id=entry.id,
        amount=decrypted_amount,
        frequency=entry.frequency,
        target_name=entry.target_name,
        start_date=entry.start_date,
        annual_projection=annual_projection,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    ).model_dump(mode="json")

    return JSONResponse(status_code=200, content=success_response(response_item))


@router.delete("/{entry_id}")
async def delete_aportacion(
    entry_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a contribution schedule.

    Verifies ownership (returns 403 for cross-user access attempts).
    """
    # Fetch entry scoped to user (ownership check)
    stmt = select(Aportacion).where(
        Aportacion.id == entry_id, Aportacion.user_id == user_id
    )
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        # Check if entry exists for another user (return 403)
        stmt_any = select(Aportacion).where(Aportacion.id == entry_id)
        result_any = await db.execute(stmt_any)
        entry_any = result_any.scalar_one_or_none()
        if entry_any:
            return JSONResponse(
                status_code=403,
                content=forbidden_response(
                    "Access denied to this contribution entry."
                ),
            )
        return JSONResponse(
            status_code=404,
            content=not_found_response("Contribution entry not found."),
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
            {"message": "Contribution entry deleted successfully."}
        ),
    )
