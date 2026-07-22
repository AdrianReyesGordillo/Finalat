"""Instruments router — endpoints for /api/instruments.

Implements:
- GET /api/instruments — List all instruments with current rates (public, filterable)
- GET /api/instruments/{id} — Single instrument detail
- POST /api/instruments/refresh — Trigger rate scraper (requires authentication)

Filters: risk_level, liquidity_tier
Includes tiered_rates where applicable.
Flags instruments not updated in 7+ days as "stale".

Requirements: 12.5, 12.6, 12.7, 13.6, 13.7, 13.8
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.instruments import Instrument
from backend.services.rate_scraper import scrape_all_rates
from backend.utils.response import (
    error_response,
    not_found_response,
    success_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/instruments", tags=["instruments"])

# Stale threshold: 7 days
STALE_THRESHOLD_DAYS = 7


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _instrument_to_dict(instrument: Instrument) -> dict:
    """Convert an Instrument model to a response dict.

    Includes a 'stale' flag if last_fetched_at is older than 7 days.

    Args:
        instrument: The Instrument ORM model instance.

    Returns:
        Dict representation of the instrument for API response.
    """
    now = datetime.now(timezone.utc)
    stale = False

    if instrument.last_fetched_at:
        # Handle both timezone-aware and naive datetimes
        last_fetched = instrument.last_fetched_at
        if last_fetched.tzinfo is None:
            last_fetched = last_fetched.replace(tzinfo=timezone.utc)
        stale = (now - last_fetched) > timedelta(days=STALE_THRESHOLD_DAYS)

    return {
        "id": instrument.id,
        "name": instrument.name,
        "annual_rate": float(instrument.annual_rate),
        "min_investment": float(instrument.min_investment),
        "max_investment": float(instrument.max_investment) if instrument.max_investment is not None else None,
        "term": instrument.term,
        "risk_level": instrument.risk_level,
        "liquidity_tier": instrument.liquidity_tier,
        "tiered_rates": instrument.tiered_rates,
        "last_fetch_status": instrument.last_fetch_status,
        "last_fetched_at": instrument.last_fetched_at.isoformat() if instrument.last_fetched_at else None,
        "stale": stale,
        "created_at": instrument.created_at.isoformat() if instrument.created_at else None,
        "updated_at": instrument.updated_at.isoformat() if instrument.updated_at else None,
    }


def _get_current_user_id(request: Request) -> str:
    """Extract user_id from request.state (set by auth middleware).

    Raises HTTPException 401 if user_id is not set (unauthenticated).

    Returns:
        The authenticated user's Firebase UID.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=401,
            detail={
                "success": False,
                "data": None,
                "error": {"code": "UNAUTHORIZED", "message": "Authentication required.", "fields": None},
            },
        )
    return user_id


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("")
async def list_instruments(
    request: Request,
    db: AsyncSession = Depends(get_db),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: low, medium, high"),
    liquidity_tier: Optional[str] = Query(None, description="Filter by liquidity tier: immediate, 1-day, 28-day, custom"),
    include_errors: bool = Query(False, description="Include instruments with fetch errors"),
):
    """List all instruments with current rates.

    This is a PUBLIC endpoint — no authentication required for GET requests.
    Returns only instruments with last_fetch_status="success" by default.
    Flags instruments not updated in 7+ days as "stale".

    Supports filtering by:
    - risk_level: low, medium, high
    - liquidity_tier: immediate, 1-day, 28-day, custom

    Query params:
        risk_level: Filter by risk level
        liquidity_tier: Filter by liquidity tier
        include_errors: If true, includes instruments with fetch errors
    """
    # Build query
    stmt = select(Instrument)

    # By default only show successful fetches
    if not include_errors:
        stmt = stmt.where(Instrument.last_fetch_status == "success")

    # Apply filters
    if risk_level:
        valid_risk_levels = {"low", "medium", "high"}
        if risk_level.lower() not in valid_risk_levels:
            return JSONResponse(
                status_code=400,
                content=error_response(
                    "VALIDATION_ERROR",
                    f"Invalid risk_level. Must be one of: {', '.join(sorted(valid_risk_levels))}",
                ),
            )
        stmt = stmt.where(Instrument.risk_level == risk_level.lower())

    if liquidity_tier:
        valid_liquidity_tiers = {"immediate", "1-day", "28-day", "custom"}
        if liquidity_tier.lower() not in valid_liquidity_tiers:
            return JSONResponse(
                status_code=400,
                content=error_response(
                    "VALIDATION_ERROR",
                    f"Invalid liquidity_tier. Must be one of: {', '.join(sorted(valid_liquidity_tiers))}",
                ),
            )
        stmt = stmt.where(Instrument.liquidity_tier == liquidity_tier.lower())

    # Order by annual_rate descending (best rates first)
    stmt = stmt.order_by(Instrument.annual_rate.desc())

    result = await db.execute(stmt)
    instruments = result.scalars().all()

    # Build response
    items = [_instrument_to_dict(inst) for inst in instruments]

    response_data = {
        "items": items,
        "total": len(items),
    }

    return JSONResponse(status_code=200, content=success_response(response_data))


@router.get("/{instrument_id}")
async def get_instrument(
    instrument_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get a single instrument detail by ID.

    This is a PUBLIC endpoint — no authentication required.

    Args:
        instrument_id: The UUID of the instrument to retrieve.
    """
    stmt = select(Instrument).where(Instrument.id == instrument_id)
    result = await db.execute(stmt)
    instrument = result.scalar_one_or_none()

    if not instrument:
        return JSONResponse(
            status_code=404,
            content=not_found_response("Instrument not found."),
        )

    return JSONResponse(
        status_code=200,
        content=success_response(_instrument_to_dict(instrument)),
    )


@router.post("/refresh")
async def refresh_instruments(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(_get_current_user_id),
):
    """Trigger rate scraper to refresh instrument rates.

    This endpoint requires authentication (admin/manual trigger).
    Invokes the rate scraper service to fetch current rates for all
    known instruments.

    Returns:
        Summary of the scrape operation: updated count, failed count, total.
    """
    try:
        scrape_result = await scrape_all_rates(db)
    except Exception as exc:
        logger.error("Rate scraper failed: %s", str(exc))
        return JSONResponse(
            status_code=500,
            content=error_response(
                "SCRAPER_ERROR",
                "Rate scraper encountered an error. Some instruments may not have been updated.",
            ),
        )

    return JSONResponse(
        status_code=200,
        content=success_response({
            "message": "Rate scrape completed.",
            "updated": scrape_result["updated"],
            "failed": scrape_result["failed"],
            "total": scrape_result["total"],
        }),
    )
