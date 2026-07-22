"""Afore (Pension Fund) router — CRUD endpoints for /api/afore.

Implements:
- GET /api/afore — List all Afore records for authenticated user
- POST /api/afore — Create a new Afore record
- PUT /api/afore/{id} — Update an existing Afore record
- DELETE /api/afore/{id} — Delete an Afore record (with ownership check)

Integrates: Encryption Service, LRU Cache, Update Tracker.

Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.afore import Afore
from backend.models.database import get_db
from backend.schemas.afore import (
    AforeCreate,
    AforeListResponse,
    AforeResponse,
    AforeUpdate,
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

router = APIRouter(prefix="/api/afore", tags=["afore"])

MODULE_NAME = "afore"
CACHE_LIST_KEY = "afore:list"


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
async def list_afore(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all Afore records for the authenticated user.

    Returns the list of records with aggregate total balance.
    Entries that fail decryption are excluded with a failed_count indicator.
    """
    # Try cache first
    cached = cache.get(user_id, CACHE_LIST_KEY)
    if cached is not None:
        return JSONResponse(status_code=200, content=success_response(cached))

    # Query database — scoped to user_id
    stmt = select(Afore).where(Afore.user_id == user_id).order_by(Afore.created_at.desc())
    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Decrypt and build response
    items: list[dict] = []
    failed_count = 0
    total_balance = 0.0

    for entry in entries:
        try:
            decrypted_balance = encryption_service.decrypt(entry.balance_encrypted)
            balance = float(decrypted_balance)
            total_balance += balance
            items.append(
                AforeResponse(
                    id=entry.id,
                    provider_name=entry.provider_name,
                    balance=balance,
                    last_update_date=entry.last_update_date,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at,
                ).model_dump(mode="json")
            )
        except (EncryptionError, ValueError) as exc:
            logger.warning(
                "Failed to decrypt afore entry %s for user %s", entry.id, user_id
            )
            failed_count += 1

    response_data = AforeListResponse(
        items=[AforeResponse(**item) for item in items],
        total_balance=round(total_balance, 2),
        failed_count=failed_count,
    ).model_dump(mode="json")

    # Store in cache
    cache.set(user_id, CACHE_LIST_KEY, response_data)

    return JSONResponse(status_code=200, content=success_response(response_data))


@router.post("")
async def create_afore(
    body: AforeCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new Afore record.

    Encrypts the balance before persisting. Invalidates cache and
    records update in the tracker.
    """
    # Encrypt balance
    try:
        encrypted_balance = encryption_service.encrypt(str(body.balance))
    except EncryptionError:
        return JSONResponse(
            status_code=500,
            content=error_response(
                "ENCRYPTION_ERROR", "Could not process encrypted data."
            ),
        )

    # Create record
    new_entry = Afore(
        user_id=user_id,
        provider_name=body.provider_name,
        balance_encrypted=encrypted_balance,
        last_update_date=body.last_update_date,
    )
    db.add(new_entry)
    await db.flush()
    await db.refresh(new_entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Build response
    response_item = AforeResponse(
        id=new_entry.id,
        provider_name=new_entry.provider_name,
        balance=body.balance,
        last_update_date=new_entry.last_update_date,
        created_at=new_entry.created_at,
        updated_at=new_entry.updated_at,
    ).model_dump(mode="json")

    return JSONResponse(status_code=201, content=success_response(response_item))


@router.put("/{entry_id}")
async def update_afore(
    entry_id: str,
    body: AforeUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing Afore record.

    Verifies ownership, encrypts updated balance, invalidates cache,
    and records update in the tracker. Returns 403 on cross-user access.
    """
    # Fetch entry — check existence first, then ownership
    stmt = select(Afore).where(Afore.id == entry_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Afore record not found."),
        )

    # Ownership check — return 403 if not the owner
    if entry.user_id != user_id:
        return JSONResponse(
            status_code=403,
            content=forbidden_response("You do not have access to this resource."),
        )

    # Apply updates
    if body.balance is not None:
        try:
            entry.balance_encrypted = encryption_service.encrypt(str(body.balance))
        except EncryptionError:
            return JSONResponse(
                status_code=500,
                content=error_response(
                    "ENCRYPTION_ERROR", "Could not process encrypted data."
                ),
            )

    if body.provider_name is not None:
        entry.provider_name = body.provider_name

    if body.last_update_date is not None:
        entry.last_update_date = body.last_update_date

    await db.flush()
    await db.refresh(entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Decrypt balance for response
    try:
        decrypted_balance = float(encryption_service.decrypt(entry.balance_encrypted))
    except (EncryptionError, ValueError):
        decrypted_balance = body.balance if body.balance is not None else 0.0

    response_item = AforeResponse(
        id=entry.id,
        provider_name=entry.provider_name,
        balance=decrypted_balance,
        last_update_date=entry.last_update_date,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    ).model_dump(mode="json")

    return JSONResponse(status_code=200, content=success_response(response_item))


@router.delete("/{entry_id}")
async def delete_afore(
    entry_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete an Afore record.

    Verifies ownership before deletion. Returns 403 on cross-user access.
    """
    # Fetch entry — check existence first, then ownership
    stmt = select(Afore).where(Afore.id == entry_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Afore record not found."),
        )

    # Ownership check — return 403 if not the owner
    if entry.user_id != user_id:
        return JSONResponse(
            status_code=403,
            content=forbidden_response("You do not have access to this resource."),
        )

    await db.delete(entry)
    await db.flush()

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    return JSONResponse(
        status_code=200,
        content=success_response({"message": "Afore record deleted successfully."}),
    )
