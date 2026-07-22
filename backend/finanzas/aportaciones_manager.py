"""Module to manage Aportaciones (contributions) using SQLite.

Supports weekly (semanal), biweekly (quincenal), and monthly (mensual) frequencies.
All operations are scoped by user_id for per-user data isolation.
Maintains a window of previous month, current month, and next month.
"""
from datetime import date, timedelta
from app.finanzas.database import get_db, USE_POSTGRES
from app.finanzas import cache
from app.finanzas.timezone import today as mx_today
from app.finanzas.crypto import decrypt


def _get_aportaciones_config(user_id: str) -> list[dict]:
    """Get aportaciones config for the user from DB. Returns empty if none configured."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM aportaciones_config WHERE user_id = ? ORDER BY id", (user_id,)
        ).fetchall()
    return [
        {
            "category": decrypt(r["category"], str),
            "amount": decrypt(r["amount"], float),
            "person": decrypt(r["person"], str),
            "color": r["color"],
            "frequency": r["frequency"] if "frequency" in r.keys() else "semanal",
        }
        for r in rows
    ]


def _get_weeks_of_month(year: int, month: int) -> list[dict]:
    """Get all weeks (Sun-Sat) that overlap with the given month."""
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    weeks = []
    current = first_day
    days_since_sunday = (current.weekday() + 1) % 7
    week_start = current - timedelta(days=days_since_sunday)

    while week_start <= last_day:
        week_end = week_start + timedelta(days=6)
        if week_end >= first_day and week_start <= last_day:
            weeks.append({
                "week_start": week_start.isoformat(),
                "week_end": week_end.isoformat(),
            })
        week_start += timedelta(days=7)

    return weeks


def _get_biweekly_periods_of_month(year: int, month: int) -> list[dict]:
    """Get biweekly (quincenal) periods for a month: 1-15 and 16-end."""
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    mid = date(year, month, 15)
    return [
        {"week_start": first_day.isoformat(), "week_end": mid.isoformat()},
        {"week_start": date(year, month, 16).isoformat(), "week_end": last_day.isoformat()},
    ]


def _get_monthly_periods_of_month(year: int, month: int) -> list[dict]:
    """Get a single monthly period for the month: 1-end."""
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    return [{"week_start": first_day.isoformat(), "week_end": last_day.isoformat()}]


def _get_periods_for_frequency(frequency: str, year: int, month: int) -> list[dict]:
    """Get periods based on frequency type."""
    if frequency == "quincenal":
        return _get_biweekly_periods_of_month(year, month)
    elif frequency == "mensual":
        return _get_monthly_periods_of_month(year, month)
    else:  # semanal (default)
        return _get_weeks_of_month(year, month)


def _purge_old_aportaciones(user_id: str):
    """Keep only 3 months of data for this user."""
    today = mx_today()

    if today.month == 1:
        prev_month_start = date(today.year - 1, 12, 1)
    else:
        prev_month_start = date(today.year, today.month - 1, 1)

    with get_db() as conn:
        conn.execute(
            "DELETE FROM aportaciones WHERE user_id = ? AND week_start < ?",
            (user_id, prev_month_start.isoformat())
        )


def _cleanup_orphaned_aportaciones(user_id: str, config_list: list[dict]):
    """Delete aportaciones records whose category+person no longer exists in config."""
    # Build set of valid (category, person) pairs
    valid_pairs = {(c["category"], c["person"]) for c in config_list}

    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category, person FROM aportaciones WHERE user_id = ?",
            (user_id,)
        ).fetchall()

        for row in rows:
            pair = (row["category"], row["person"])
            if pair not in valid_pairs:
                conn.execute(
                    "DELETE FROM aportaciones WHERE user_id = ? AND category = ? AND person = ?",
                    (user_id, row["category"], row["person"])
                )


def ensure_month_records(user_id: str, year: int, month: int):
    """Ensure all aportacion records exist for the given month and user.

    Creates records based on each config's frequency.
    Uses INSERT ... ON CONFLICT DO NOTHING (PostgreSQL) or checks before insert (SQLite)
    to prevent duplicate records.
    """
    config_list = _get_aportaciones_config(user_id)
    if not config_list:
        return  # No config = nothing to generate

    today = mx_today().isoformat()
    changed = False

    with get_db() as conn:
        for config in config_list:
            frequency = config.get("frequency", "semanal")
            periods = _get_periods_for_frequency(frequency, year, month)

            for period in periods:
                if USE_POSTGRES:
                    existing = conn.execute(
                        """SELECT id, status, week_end FROM aportaciones
                           WHERE user_id = ? AND category = ? AND COALESCE(person, '') = ? AND week_start = ?""",
                        (user_id, config["category"], config["person"] or "", period["week_start"])
                    ).fetchone()

                    if not existing:
                        status = "atrasada" if period["week_end"] < today else "pendiente"
                        try:
                            conn.execute(
                                """INSERT INTO aportaciones (user_id, category, week_start, week_end, status, person)
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                (user_id, config["category"], period["week_start"], period["week_end"], status, config["person"] or "")
                            )
                            changed = True
                        except Exception:
                            pass  # Unique constraint violation — record already exists
                    else:
                        if existing["status"] == "pendiente" and existing["week_end"] < today:
                            conn.execute(
                                "UPDATE aportaciones SET status = 'atrasada' WHERE id = ?",
                                (existing["id"],)
                            )
                            changed = True
                else:
                    existing = conn.execute(
                        """SELECT id, status, week_end FROM aportaciones
                           WHERE user_id = ? AND category = ? AND week_start = ? AND person = ?""",
                        (user_id, config["category"], period["week_start"], config["person"])
                    ).fetchone()

                    if not existing:
                        status = "atrasada" if period["week_end"] < today else "pendiente"
                        conn.execute(
                            """INSERT INTO aportaciones (user_id, category, week_start, week_end, status, person)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (user_id, config["category"], period["week_start"], period["week_end"], status, config["person"])
                        )
                        changed = True
                    else:
                        if existing["status"] == "pendiente" and existing["week_end"] < today:
                            conn.execute(
                                "UPDATE aportaciones SET status = 'atrasada' WHERE id = ?",
                                (existing["id"],)
                            )
                            changed = True

    if changed:
        cache.invalidate_prefix(cache.user_key("aportaciones", user_id))


def get_aportaciones(user_id: str, year: int, month: int) -> dict:
    """Get all aportaciones for a given month and user.

    Navigation is restricted to: previous month, current month, next month.
    Returns categories grouped with their periods for the requested month only.
    Only includes categories that still exist in aportaciones_config.
    """
    config_list = _get_aportaciones_config(user_id)
    if not config_list:
        # No config — clean up any orphaned aportaciones records
        _cleanup_orphaned_aportaciones(user_id, [])
        return {"weeks": [], "categories": [], "month": month, "year": year}

    _purge_old_aportaciones(user_id)
    _cleanup_orphaned_aportaciones(user_id, config_list)

    # Enforce navigation limit: only allow prev, current, next month
    today = mx_today()
    requested = date(year, month, 1)

    # Calculate prev and next month boundaries
    if today.month == 1:
        prev_month_start = date(today.year - 1, 12, 1)
    else:
        prev_month_start = date(today.year, today.month - 1, 1)

    if today.month == 12:
        next_month_start = date(today.year + 1, 1, 1)
    else:
        next_month_start = date(today.year, today.month + 1, 1)

    # Clamp requested month to allowed range
    if requested < prev_month_start:
        year, month = prev_month_start.year, prev_month_start.month
    elif requested > next_month_start:
        year, month = next_month_start.year, next_month_start.month

    # Only ensure records for the requested month
    ensure_month_records(user_id, year, month)

    # Check cache (after ensure_month_records which may invalidate)
    cached_key = cache.user_key(f"aportaciones_{year}_{month}", user_id)
    cached = cache.get(cached_key)
    if cached is not None:
        return cached

    # Fetch records for the requested month only
    # A period belongs to this month if it overlaps with the month range
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, category, person, week_start, week_end, status
               FROM aportaciones
               WHERE user_id = ? AND week_start <= ? AND week_end >= ?
               ORDER BY category, person, week_start""",
            (user_id, last_day.isoformat(), first_day.isoformat())
        ).fetchall()

    # Organize by category + person
    categories = {}
    for row in rows:
        cat = row["category"]
        person = row["person"] or ""
        key = f"{cat}|{person}" if person else cat

        if key not in categories:
            amount = 0
            frequency = "semanal"
            color = "#1da1f2"
            for c in config_list:
                config_person = c["person"] or ""
                if c["category"] == cat and config_person == person:
                    amount = c["amount"]
                    frequency = c.get("frequency", "semanal")
                    color = c.get("color", "#1da1f2")
                    break

            categories[key] = {
                "category": cat,
                "person": person,
                "amount": amount,
                "frequency": frequency,
                "color": color,
                "weeks": []
            }

        categories[key]["weeks"].append({
            "id": row["id"],
            "weekStart": row["week_start"],
            "weekEnd": row["week_end"],
            "status": row["status"],
        })

    # Sort weeks within each category
    for cat_data in categories.values():
        cat_data["weeks"].sort(key=lambda w: w["weekStart"])

    # Order categories to match the order in aportaciones_config
    config_order = {f"{c['category']}|{c['person']}" if c.get("person") else c["category"]: i for i, c in enumerate(config_list)}
    sorted_categories = sorted(categories.values(), key=lambda cat: config_order.get(f"{cat['category']}|{cat['person']}" if cat['person'] else cat['category'], 999))

    result = {
        "categories": sorted_categories,
        "month": month,
        "year": year,
    }

    cache.set(cached_key, result, ttl_seconds=300)
    return result


def update_aportacion_status(user_id: str, aportacion_id: int, status: str) -> bool:
    """Update the status of an aportacion record belonging to the user."""
    valid_statuses = ("pendiente", "realizada")
    if status not in valid_statuses:
        return False

    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE aportaciones SET status = ? WHERE id = ? AND user_id = ?",
            (status, aportacion_id, user_id)
        )
        updated = cursor.rowcount > 0

    if updated:
        cache.invalidate_prefix(cache.user_key("aportaciones", user_id))
    return updated
