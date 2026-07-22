"""Module to read and manage Creditos data from SQLite.

All operations are scoped by user_id for per-user data isolation.
"""
from datetime import date
from app.finanzas.database import get_db
from app.finanzas import cache
from app.finanzas.timezone import today as mx_today
from app.finanzas.crypto import encrypt, decrypt


def get_credit_cards(user_id: str) -> dict:
    """Read credit card data for the given user from SQLite. Cached for 5 minutes."""
    cache_key = cache.user_key("creditos_cards", user_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM creditos WHERE user_id = ?", (user_id,)
        ).fetchall()

    cards = []
    for row in rows:
        credit_limit = decrypt(row["credit_limit"], float)
        debt = decrypt(row["debt"], float)
        available = decrypt(row["available"], float)
        payment_date = row["payment_date"]
        minimum_payment = decrypt(row["minimum_payment"], float)
        full_payment = decrypt(row["full_payment"], float)

        usage_percent = round((debt / credit_limit) * 100) if credit_limit > 0 else 0

        days_until = 0
        if payment_date:
            try:
                pay_date = date.fromisoformat(payment_date.split(" ")[0])
                today = mx_today()
                days_until = (pay_date - today).days
                if days_until < 0:
                    days_until = 0
            except (ValueError, TypeError):
                days_until = 0

        cards.append({
            "name": row["name"],
            "color": row["color"],
            "creditLimit": credit_limit,
            "debt": debt,
            "available": available,
            "usagePercent": usage_percent,
            "cutoffDate": row["cutoff_date"],
            "paymentDate": payment_date,
            "minimumPayment": minimum_payment,
            "fullPayment": full_payment,
            "daysUntilPayment": days_until
        })

    # Summary
    total_credit = sum(c["creditLimit"] for c in cards)
    total_debt = sum(c["debt"] for c in cards)
    total_available = sum(c["available"] for c in cards)
    total_payment = sum(c["fullPayment"] for c in cards)
    total_usage = round((total_debt / total_credit) * 100) if total_credit > 0 else 0

    result = {
        "cards": cards,
        "summary": {
            "totalCredit": total_credit,
            "totalDebt": total_debt,
            "totalAvailable": total_available,
            "totalPayment": total_payment,
            "usagePercent": total_usage
        }
    }

    cache.set(cache_key, result, ttl_seconds=300)
    return result


def update_credit_card(user_id: str, name: str, fields: dict) -> str:
    """Update fields for a specific credit card belonging to the user.

    Args:
        user_id: Firebase UID.
        name: Card name to update.
        fields: Dict with any of: debt, available, cutoffDate, paymentDate,
                minimumPayment, fullPayment, creditLimit.

    Returns:
        Today's date string (ISO format).
    """
    from app.finanzas.update_tracker import mark_updated

    # Map API field names to DB column names
    field_map = {
        "creditLimit": "credit_limit",
        "debt": "debt",
        "available": "available",
        "cutoffDate": "cutoff_date",
        "paymentDate": "payment_date",
        "minimumPayment": "minimum_payment",
        "fullPayment": "full_payment",
    }

    # Fields that should be encrypted
    encrypted_fields = {"credit_limit", "debt", "available", "minimum_payment", "full_payment"}

    with get_db() as conn:
        for api_field, value in fields.items():
            col = field_map.get(api_field)
            if col:
                stored_value = encrypt(value) if col in encrypted_fields else value
                conn.execute(
                    f"UPDATE creditos SET {col} = ? WHERE name = ? AND user_id = ?",
                    (stored_value, name, user_id)
                )

        # Auto-calculate available = credit_limit - debt
        if "debt" in fields or "creditLimit" in fields:
            row = conn.execute(
                "SELECT credit_limit, debt FROM creditos WHERE name = ? AND user_id = ?",
                (name, user_id)
            ).fetchone()
            if row:
                available = decrypt(row["credit_limit"], float) - decrypt(row["debt"], float)
                conn.execute(
                    "UPDATE creditos SET available = ? WHERE name = ? AND user_id = ?",
                    (encrypt(available), name, user_id)
                )

    cache.invalidate(cache.user_key("creditos_cards", user_id))
    return mark_updated("creditos", user_id)
