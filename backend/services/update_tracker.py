"""Update Tracker service — records module update timestamps per user.

Requirements: 17.1, 17.6, 17.7
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.update_tracker import UpdateTracker


async def record_module_update(
    db: AsyncSession, user_id: str, module_name: str
) -> None:
    """Record that a user just performed a write on a given module.

    If a tracker row already exists for this user+module, update it.
    Otherwise insert a new row.

    Args:
        db: The async database session.
        user_id: The authenticated user's Firebase UID.
        module_name: Module identifier (e.g., 'ahorro', 'creditos').
    """
    now = datetime.now(timezone.utc)

    stmt = select(UpdateTracker).where(
        UpdateTracker.user_id == user_id,
        UpdateTracker.module_name == module_name,
    )
    result = await db.execute(stmt)
    tracker = result.scalar_one_or_none()

    if tracker:
        tracker.last_updated_at = now
    else:
        tracker = UpdateTracker(
            user_id=user_id,
            module_name=module_name,
            last_updated_at=now,
        )
        db.add(tracker)
