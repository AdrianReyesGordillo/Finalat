"""Creditos (Credit Cards) router — CRUD endpoints for /api/creditos.

Implements:
- GET /api/creditos — List all credit card entries for authenticated user
- POST /api/creditos — Create a new credit card record
- PUT /api/creditos/{id} — Update an existing credit card record
- DELETE /api/creditos/{id} — Delete a credit card record (with ownership check)

Integrates: Encryption Service, LRU Cache, Update Tracker.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9
"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.creditos import Credito
from backend.models.database import get_db
from backend.schemas.creditos import (
    CreditoCreate,
    CreditoListResponse,
    CreditoResponse,
    CreditoUpdate,
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

router = APIRouter(prefix="/api/creditos", tags=["creditos"])

MODULE_NAME = "creditos"
CACHE_LIST_KEY = "creditos:list"


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


def calculate_utilization(balance: float, limit: float) -> float | str:
    """Calculate credit utilization percentage.

    Args:
        balance: The current credit card balance.
        limit: The credit card limit.

    Returns:
        Utilization percentage rounded to 2 decimals, or "N/A" if limit is 0.
    """
    if limit == 0:
        return "N/A"
    return round((balance / limit) * 100, 2)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
async def list_creditos(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all credit card entries for the authenticated user.

    Returns the list of entries with aggregate total balance.
    Entries that fail decryption are excluded with a failed_count indicator.
    """
    # Try cache first
    cached = cache.get(user_id, CACHE_LIST_KEY)
    if cached is not None:
        return JSONResponse(status_code=200, content=success_response(cached))

    # Query database — scoped to user_id
    stmt = (
        select(Credito)
        .where(Credito.user_id == user_id)
        .order_by(Credito.created_at.desc())
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Decrypt and build response
    items: list[dict] = []
    failed_count = 0
    total_balance = 0.0

    for entry in entries:
        try:
            decrypted_balance = float(
                encryption_service.decrypt(entry.balance_encrypted)
            )
            decrypted_limit = float(
                encryption_service.decrypt(entry.limit_encrypted)
            )
            decrypted_min_payment = float(
                encryption_service.decrypt(entry.min_payment_encrypted)
            )

            total_balance += decrypted_balance
            utilization = calculate_utilization(decrypted_balance, decrypted_limit)

            items.append(
                CreditoResponse(
                    id=entry.id,
                    card_name=entry.card_name,
                    balance=decrypted_balance,
                    limit=decrypted_limit,
                    minimum_payment=decrypted_min_payment,
                    utilization=utilization,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at,
                ).model_dump(mode="json")
            )
        except (EncryptionError, ValueError) as exc:
            logger.warning(
                "Failed to decrypt credito entry %s for user %s",
                entry.id,
                user_id,
            )
            failed_count += 1

    response_data = CreditoListResponse(
        items=[CreditoResponse(**item) for item in items],
        total_balance=round(total_balance, 2),
        failed_count=failed_count,
    ).model_dump(mode="json")

    # Store in cache
    cache.set(user_id, CACHE_LIST_KEY, response_data)

    return JSONResponse(status_code=200, content=success_response(response_data))


@router.post("")
async def create_credito(
    body: CreditoCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new credit card record.

    Encrypts balance, limit, and minimum_payment before persisting.
    Invalidates cache and records update in the tracker.
    """
    # Encrypt monetary fields
    try:
        encrypted_balance = encryption_service.encrypt(str(body.balance))
        encrypted_limit = encryption_service.encrypt(str(body.limit))
        encrypted_min_payment = encryption_service.encrypt(str(body.minimum_payment))
    except EncryptionError:
        return JSONResponse(
            status_code=500,
            content=error_response(
                "ENCRYPTION_ERROR", "Could not process encrypted data."
            ),
        )

    # Create record
    new_entry = Credito(
        user_id=user_id,
        balance_encrypted=encrypted_balance,
        limit_encrypted=encrypted_limit,
        min_payment_encrypted=encrypted_min_payment,
        card_name=body.card_name,
    )
    db.add(new_entry)
    await db.flush()
    await db.refresh(new_entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Build response
    utilization = calculate_utilization(body.balance, body.limit)
    response_item = CreditoResponse(
        id=new_entry.id,
        card_name=new_entry.card_name,
        balance=body.balance,
        limit=body.limit,
        minimum_payment=body.minimum_payment,
        utilization=utilization,
        created_at=new_entry.created_at,
        updated_at=new_entry.updated_at,
    ).model_dump(mode="json")

    return JSONResponse(status_code=201, content=success_response(response_item))


@router.put("/{entry_id}")
async def update_credito(
    entry_id: str,
    body: CreditoUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing credit card record.

    Verifies ownership, encrypts updated monetary fields, invalidates cache,
    and records update in the tracker. Returns 403 on cross-user access.
    """
    # Fetch entry scoped to user
    stmt = select(Credito).where(Credito.id == entry_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Credit card record not found."),
        )

    # Cross-user access check — return 403
    if entry.user_id != user_id:
        return JSONResponse(
            status_code=403,
            content=forbidden_response(
                "You do not have permission to access this resource."
            ),
        )

    # Apply updates
    try:
        if body.balance is not None:
            entry.balance_encrypted = encryption_service.encrypt(str(body.balance))
        if body.limit is not None:
            entry.limit_encrypted = encryption_service.encrypt(str(body.limit))
        if body.minimum_payment is not None:
            entry.min_payment_encrypted = encryption_service.encrypt(
                str(body.minimum_payment)
            )
    except EncryptionError:
        return JSONResponse(
            status_code=500,
            content=error_response(
                "ENCRYPTION_ERROR", "Could not process encrypted data."
            ),
        )

    if body.card_name is not None:
        entry.card_name = body.card_name

    await db.flush()
    await db.refresh(entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Decrypt all fields for response
    try:
        decrypted_balance = float(
            encryption_service.decrypt(entry.balance_encrypted)
        )
        decrypted_limit = float(
            encryption_service.decrypt(entry.limit_encrypted)
        )
        decrypted_min_payment = float(
            encryption_service.decrypt(entry.min_payment_encrypted)
        )
    except (EncryptionError, ValueError):
        # Fallback: use provided values where available
        decrypted_balance = body.balance if body.balance is not None else 0.0
        decrypted_limit = body.limit if body.limit is not None else 0.0
        decrypted_min_payment = (
            body.minimum_payment if body.minimum_payment is not None else 0.0
        )

    utilization = calculate_utilization(decrypted_balance, decrypted_limit)

    response_item = CreditoResponse(
        id=entry.id,
        card_name=entry.card_name,
        balance=decrypted_balance,
        limit=decrypted_limit,
        minimum_payment=decrypted_min_payment,
        utilization=utilization,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    ).model_dump(mode="json")

    return JSONResponse(status_code=200, content=success_response(response_item))


@router.delete("/{entry_id}")
async def delete_credito(
    entry_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a credit card record.

    Verifies ownership before deletion. Returns 403 on cross-user access.
    """
    # Fetch entry (not scoped — to distinguish 404 from 403)
    stmt = select(Credito).where(Credito.id == entry_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Credit card record not found."),
        )

    # Cross-user access check — return 403
    if entry.user_id != user_id:
        return JSONResponse(
            status_code=403,
            content=forbidden_response(
                "You do not have permission to access this resource."
            ),
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
            {"message": "Credit card record deleted successfully."}
        ),
    )
