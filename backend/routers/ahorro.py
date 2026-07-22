"""Ahorro (Savings) router — CRUD endpoints for /api/ahorro.

Implements:
- GET /api/ahorro — List all savings entries for authenticated user
- POST /api/ahorro — Create a new savings entry
- PUT /api/ahorro/{id} — Update an existing savings entry
- DELETE /api/ahorro/{id} — Delete a savings entry (with ownership check)

Integrates: Encryption Service, LRU Cache, Update Tracker.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9
"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ahorro import Ahorro
from backend.models.database import get_db
from backend.schemas.ahorro import (
    AhorroCreate,
    AhorroListResponse,
    AhorroResponse,
    AhorroUpdate,
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
from backend.utils.validators import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ahorro", tags=["ahorro"])

MODULE_NAME = "ahorro"
CACHE_LIST_KEY = "ahorro:list"


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
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
async def list_ahorro(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all savings entries for the authenticated user.

    Returns the list of entries with aggregate total savings.
    Entries that fail decryption are excluded with a failed_count indicator.
    """
    # Try cache first
    cached = cache.get(user_id, CACHE_LIST_KEY)
    if cached is not None:
        return JSONResponse(status_code=200, content=success_response(cached))

    # Query database — scoped to user_id
    stmt = select(Ahorro).where(Ahorro.user_id == user_id).order_by(Ahorro.created_at.desc())
    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Decrypt and build response
    items: list[dict] = []
    failed_count = 0
    total_savings = 0.0

    for entry in entries:
        try:
            decrypted_amount = encryption_service.decrypt(entry.amount_encrypted)
            amount = float(decrypted_amount)
            total_savings += amount
            items.append(
                AhorroResponse(
                    id=entry.id,
                    amount=amount,
                    account_name=entry.account_name,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at,
                ).model_dump(mode="json")
            )
        except (EncryptionError, ValueError) as exc:
            logger.warning(
                "Failed to decrypt ahorro entry %s for user %s", entry.id, user_id
            )
            failed_count += 1

    response_data = AhorroListResponse(
        items=[AhorroResponse(**item) for item in items],
        total_savings=round(total_savings, 2),
        failed_count=failed_count,
    ).model_dump(mode="json")

    # Store in cache
    cache.set(user_id, CACHE_LIST_KEY, response_data)

    return JSONResponse(status_code=200, content=success_response(response_data))


@router.post("")
async def create_ahorro(
    body: AhorroCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new savings entry.

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
    new_entry = Ahorro(
        user_id=user_id,
        amount_encrypted=encrypted_amount,
        account_name=body.account_name,
    )
    db.add(new_entry)
    await db.flush()
    await db.refresh(new_entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Build response
    response_item = AhorroResponse(
        id=new_entry.id,
        amount=body.amount,
        account_name=new_entry.account_name,
        created_at=new_entry.created_at,
        updated_at=new_entry.updated_at,
    ).model_dump(mode="json")

    return JSONResponse(status_code=201, content=success_response(response_item))


@router.put("/{entry_id}")
async def update_ahorro(
    entry_id: str,
    body: AhorroUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing savings entry.

    Verifies ownership, encrypts updated amount, invalidates cache,
    and records update in the tracker.
    """
    # Fetch entry scoped to user
    stmt = select(Ahorro).where(Ahorro.id == entry_id, Ahorro.user_id == user_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Savings entry not found."),
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

    if body.account_name is not None:
        entry.account_name = body.account_name

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

    response_item = AhorroResponse(
        id=entry.id,
        amount=decrypted_amount,
        account_name=entry.account_name,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    ).model_dump(mode="json")

    return JSONResponse(status_code=200, content=success_response(response_item))


@router.delete("/{entry_id}")
async def delete_ahorro(
    entry_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a savings entry.

    Verifies ownership (confirmation-aware: the backend ensures the entry
    belongs to the authenticated user before deletion).
    """
    # Fetch entry scoped to user (ownership check)
    stmt = select(Ahorro).where(Ahorro.id == entry_id, Ahorro.user_id == user_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Savings entry not found."),
        )

    await db.delete(entry)
    await db.flush()

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    return JSONResponse(
        status_code=200,
        content=success_response({"message": "Savings entry deleted successfully."}),
    )
