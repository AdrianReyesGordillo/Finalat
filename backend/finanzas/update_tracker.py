"""Tracks the last update date for data sections using SQLite.

All tracker entries are scoped by user_id for per-user data isolation.
"""
from datetime import date, datetime
from app.finanzas.database import get_db
from app.finanzas.timezone import today as mx_today


def get_last_update(section: str, user_id: str = "") -> str | None:
    """Returns the last update date for a section as 'YYYY-MM-DD', or None."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT last_update FROM update_tracker WHERE section = ? AND user_id = ?",
            (section, user_id)
        ).fetchone()
        return row["last_update"] if row else None


def mark_updated(section: str, user_id: str = "") -> str:
    """Marks a section as updated today. Returns today's date string."""
    today = mx_today().isoformat()
    with get_db() as conn:
        conn.execute(
            """INSERT INTO update_tracker (user_id, section, last_update) VALUES (?, ?, ?)
               ON CONFLICT(user_id, section) DO UPDATE SET last_update = ?""",
            (user_id, section, today, today)
        )
    return today


def is_monday() -> bool:
    """Returns True if today is Monday (weekday 0)."""
    return mx_today().weekday() == 0


def is_friday() -> bool:
    """Returns True if today is Friday (weekday 4)."""
    return mx_today().weekday() == 4


def is_first_of_month() -> bool:
    """Returns True if today is the 1st day of the month."""
    return mx_today().day == 1


def is_fifteenth() -> bool:
    """Returns True if today is the 15th day of the month."""
    return mx_today().day == 15


# Map of schedule types to their check functions
SCHEDULE_CHECKS = {
    "monday": is_monday,
    "friday": is_friday,
    "first_of_month": is_first_of_month,
    "fifteenth": is_fifteenth,
}


def needs_update(section: str, schedule: str = "monday", user_id: str = "") -> bool:
    """Returns True if today matches the schedule and the section hasn't been updated today.

    schedule: 'monday' | 'first_of_month' | 'fifteenth'
    """
    check_fn = SCHEDULE_CHECKS.get(schedule, is_monday)
    if not check_fn():
        return False
    last = get_last_update(section, user_id)
    if last is None:
        return True
    return last != mx_today().isoformat()


def get_status(section: str, schedule: str = "monday", user_id: str = "") -> dict:
    """Returns full status info for a section."""
    today = mx_today()
    last_str = get_last_update(section, user_id)
    last_date = datetime.strptime(last_str, "%Y-%m-%d").date() if last_str else None

    schedule_labels = {
        "monday": "isMonday",
        "friday": "isFriday",
        "first_of_month": "isFirstOfMonth",
        "fifteenth": "isFifteenth",
    }

    check_fn = SCHEDULE_CHECKS.get(schedule, is_monday)

    return {
        "section": section,
        "lastUpdate": last_str,
        schedule_labels.get(schedule, "isMonday"): check_fn(),
        "needsUpdate": needs_update(section, schedule, user_id),
        "daysSinceUpdate": (today - last_date).days if last_date else None,
    }
