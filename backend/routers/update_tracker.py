"""Update Tracker router — GET endpoint for /api/update-tracker.

Returns last-updated timestamps per module for the authenticated user.
Includes a "stale" flag for modules not updated in more than 7 days.

Requirements: 17.1, 17.2, 17.3, 17.4
"""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.update_tracker import UpdateTracker
from backend.utils.response import success_response

router = APIRouter(prefix="/api/update-tracker", tags=["update-tracker"])

# Modules tracked by the platform
TRACKED_MODULES = [
    "ahorro",
    "creditos",
    "gastos_ingresos",
    "deudas",
    "aportaciones",
    "afore",
    "gbm_portfolio",
]

STALE_THRESHOLD_DAYS = 7


def get_current_user_id(request: Request) -> str:
    """Extract user_id from request.state (set by auth middleware)."""
    return request.state.user_id


@router.get("")
async def get_update_tracker(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Return last-updated timestamps for all tracked modules.

    For each module, returns:
    - module_name: the module identifier
    - last_updated_at: ISO timestamp of last write operation (UTC), or null if never updated
    - stale: True if the module has not been updated in more than 7 days, or if never updated
    """
    # Query all update tracker entries for this user
    stmt = select(UpdateTracker).where(UpdateTracker.user_id == user_id)
    result = await db.execute(stmt)
    trackers = result.scalars().all()

    # Build a lookup by module_name
    tracker_map: dict[str, UpdateTracker] = {
        t.module_name: t for t in trackers
    }

    now = datetime.now(timezone.utc)
    stale_threshold = now - timedelta(days=STALE_THRESHOLD_DAYS)

    modules_status = []
    for module_name in TRACKED_MODULES:
        tracker = tracker_map.get(module_name)
        if tracker:
            last_updated_at = tracker.last_updated_at
            # Ensure timezone-aware comparison
            if last_updated_at.tzinfo is None:
                last_updated_at_aware = last_updated_at.replace(tzinfo=timezone.utc)
            else:
                last_updated_at_aware = last_updated_at
            stale = last_updated_at_aware < stale_threshold
            modules_status.append({
                "module_name": module_name,
                "last_updated_at": last_updated_at.isoformat(),
                "stale": stale,
            })
        else:
            # Module has never been updated
            modules_status.append({
                "module_name": module_name,
                "last_updated_at": None,
                "stale": True,
            })

    return JSONResponse(
        status_code=200,
        content=success_response(modules_status),
    )
