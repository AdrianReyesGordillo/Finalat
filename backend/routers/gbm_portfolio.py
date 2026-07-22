"""GBM Portfolio router — CRUD endpoints for /api/gbm-portfolio.

Implements:
- GET /api/gbm-portfolio — List all GBM positions for authenticated user
- POST /api/gbm-portfolio — Create a new GBM position
- PUT /api/gbm-portfolio/{id} — Update an existing GBM position
- DELETE /api/gbm-portfolio/{id} — Delete a GBM position (with ownership check)

Integrates: Encryption Service, LRU Cache, Update Tracker.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
"""

import logging
from decimal import Decimal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.gbm_portfolio import GbmPortfolio
from backend.schemas.gbm_portfolio import (
    GbmPortfolioCreate,
    GbmPortfolioListResponse,
    GbmPortfolioPositionResponse,
    GbmPortfolioUpdate,
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

router = APIRouter(prefix="/api/gbm-portfolio", tags=["gbm-portfolio"])

MODULE_NAME = "gbm"
CACHE_LIST_KEY = "gbm:list"


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


def calculate_gain_loss_pct(market_value: float, avg_cost: float, shares: float) -> float:
    """Calculate gain/loss percentage for a position.

    Formula: ((market_value - avg_cost * shares) / (avg_cost * shares)) * 100
    If avg_cost * shares == 0, returns 0.0 to avoid division by zero.

    Args:
        market_value: Current market value of the position.
        avg_cost: Average cost per share.
        shares: Number of shares held.

    Returns:
        Gain/loss percentage rounded to 2 decimal places.
    """
    cost_basis = avg_cost * shares
    if cost_basis == 0:
        return 0.0
    return round(((market_value - cost_basis) / cost_basis) * 100, 2)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
async def list_gbm_portfolio(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all GBM portfolio positions for the authenticated user.

    Returns the list of positions with aggregate total market value and
    total gain/loss percentage. Entries that fail decryption are excluded
    with a failed_count indicator.
    """
    # Try cache first
    cached = cache.get(user_id, CACHE_LIST_KEY)
    if cached is not None:
        return JSONResponse(status_code=200, content=success_response(cached))

    # Query database — scoped to user_id
    stmt = (
        select(GbmPortfolio)
        .where(GbmPortfolio.user_id == user_id)
        .order_by(GbmPortfolio.created_at.desc())
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    # Decrypt and build response
    items: list[dict] = []
    failed_count = 0
    total_market_value = 0.0
    total_cost_basis = 0.0

    for entry in entries:
        try:
            decrypted_avg_cost = float(
                encryption_service.decrypt(entry.avg_cost_encrypted)
            )
            decrypted_market_value = float(
                encryption_service.decrypt(entry.market_value_encrypted)
            )
            shares = float(entry.shares)

            total_market_value += decrypted_market_value
            total_cost_basis += decrypted_avg_cost * shares

            gain_loss_pct = calculate_gain_loss_pct(
                decrypted_market_value, decrypted_avg_cost, shares
            )

            items.append(
                GbmPortfolioPositionResponse(
                    id=entry.id,
                    ticker=entry.ticker,
                    shares=shares,
                    avg_cost=decrypted_avg_cost,
                    market_value=decrypted_market_value,
                    gain_loss_pct=gain_loss_pct,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at,
                ).model_dump(mode="json")
            )
        except (EncryptionError, ValueError) as exc:
            logger.warning(
                "Failed to decrypt gbm_portfolio entry %s for user %s",
                entry.id,
                user_id,
            )
            failed_count += 1

    # Calculate total gain/loss percentage
    if total_cost_basis > 0:
        total_gain_loss_pct = round(
            ((total_market_value - total_cost_basis) / total_cost_basis) * 100, 2
        )
    else:
        total_gain_loss_pct = 0.0

    response_data = GbmPortfolioListResponse(
        items=[GbmPortfolioPositionResponse(**item) for item in items],
        total_market_value=round(total_market_value, 2),
        total_gain_loss_pct=total_gain_loss_pct,
        failed_count=failed_count,
    ).model_dump(mode="json")

    # Store in cache
    cache.set(user_id, CACHE_LIST_KEY, response_data)

    return JSONResponse(status_code=200, content=success_response(response_data))


@router.post("")
async def create_gbm_position(
    body: GbmPortfolioCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new GBM portfolio position.

    Encrypts avg_cost and market_value before persisting.
    Invalidates cache and records update in the tracker.
    """
    # Encrypt monetary fields
    try:
        encrypted_avg_cost = encryption_service.encrypt(str(body.avg_cost))
        encrypted_market_value = encryption_service.encrypt(str(body.market_value))
    except EncryptionError:
        return JSONResponse(
            status_code=500,
            content=error_response(
                "ENCRYPTION_ERROR", "Could not process encrypted data."
            ),
        )

    # Create record
    new_entry = GbmPortfolio(
        user_id=user_id,
        ticker=body.ticker,
        shares=Decimal(str(body.shares)),
        avg_cost_encrypted=encrypted_avg_cost,
        market_value_encrypted=encrypted_market_value,
    )
    db.add(new_entry)
    await db.flush()
    await db.refresh(new_entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Build response
    gain_loss_pct = calculate_gain_loss_pct(
        body.market_value, body.avg_cost, body.shares
    )

    response_item = GbmPortfolioPositionResponse(
        id=new_entry.id,
        ticker=new_entry.ticker,
        shares=body.shares,
        avg_cost=body.avg_cost,
        market_value=body.market_value,
        gain_loss_pct=gain_loss_pct,
        created_at=new_entry.created_at,
        updated_at=new_entry.updated_at,
    ).model_dump(mode="json")

    return JSONResponse(status_code=201, content=success_response(response_item))


@router.put("/{entry_id}")
async def update_gbm_position(
    entry_id: str,
    body: GbmPortfolioUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing GBM portfolio position.

    Verifies ownership, encrypts updated monetary fields, invalidates cache,
    and records update in the tracker. Returns 403 on cross-user access.
    """
    # Fetch entry (not scoped — to distinguish 404 from 403)
    stmt = select(GbmPortfolio).where(GbmPortfolio.id == entry_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        return JSONResponse(
            status_code=404,
            content=not_found_response("GBM portfolio position not found."),
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
        if body.avg_cost is not None:
            entry.avg_cost_encrypted = encryption_service.encrypt(str(body.avg_cost))
        if body.market_value is not None:
            entry.market_value_encrypted = encryption_service.encrypt(
                str(body.market_value)
            )
    except EncryptionError:
        return JSONResponse(
            status_code=500,
            content=error_response(
                "ENCRYPTION_ERROR", "Could not process encrypted data."
            ),
        )

    if body.ticker is not None:
        entry.ticker = body.ticker
    if body.shares is not None:
        entry.shares = Decimal(str(body.shares))

    await db.flush()
    await db.refresh(entry)

    # Invalidate cache
    cache.invalidate(user_id, MODULE_NAME)

    # Record update
    await record_module_update(db, user_id, MODULE_NAME)

    # Decrypt all fields for response
    try:
        decrypted_avg_cost = float(
            encryption_service.decrypt(entry.avg_cost_encrypted)
        )
        decrypted_market_value = float(
            encryption_service.decrypt(entry.market_value_encrypted)
        )
    except (EncryptionError, ValueError):
        # Fallback: use provided values where available
        decrypted_avg_cost = body.avg_cost if body.avg_cost is not None else 0.0
        decrypted_market_value = (
            body.market_value if body.market_value is not None else 0.0
        )

    shares = float(entry.shares)
    gain_loss_pct = calculate_gain_loss_pct(
        decrypted_market_value, decrypted_avg_cost, shares
    )

    response_item = GbmPortfolioPositionResponse(
        id=entry.id,
        ticker=entry.ticker,
        shares=shares,
        avg_cost=decrypted_avg_cost,
        market_value=decrypted_market_value,
        gain_loss_pct=gain_loss_pct,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    ).model_dump(mode="json")

    return JSONResponse(status_code=200, content=success_response(response_item))


@router.delete("/{entry_id}")
async def delete_gbm_position(
    entry_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a GBM portfolio position.

    Verifies ownership before deletion. Returns 403 on cross-user access.
    """
    # Fetch entry (not scoped — to distinguish 404 from 403)
    stmt = select(GbmPortfolio).where(GbmPortfolio.id == entry_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()

    if not entry:
        return JSONResponse(
            status_code=404,
            content=not_found_response("GBM portfolio position not found."),
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
            {"message": "GBM portfolio position deleted successfully."}
        ),
    )
