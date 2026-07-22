"""Module to manage Deudas (loan payments) using SQLite.

All operations are scoped by user_id for per-user data isolation.
"""
from datetime import date, timedelta
from app.finanzas.database import get_db
from app.finanzas import cache
from app.finanzas.timezone import today as mx_today
from app.finanzas.crypto import encrypt, decrypt


def calculate_next_payment_date(temporalidad: str, dia1: int, dia2: int = 0, start_date1: str = "", start_date2: str = "") -> str:
    """Calculate the next payment date based on frequency and payment days."""
    today = mx_today()

    if temporalidad == "quincenal":
        days = sorted(set([dia1] + ([dia2] if dia2 > 0 else [])))

        # Find next occurrence of any payment day in current month
        for d in days:
            try:
                day_clamped = min(d, 28)
                candidate = date(today.year, today.month, day_clamped)
                if candidate > today:
                    return candidate.isoformat()
            except ValueError:
                continue

        # Next month
        next_month = today.month + 1
        next_year = today.year
        if next_month > 12:
            next_month = 1
            next_year += 1

        for d in days:
            try:
                return date(next_year, next_month, min(d, 28)).isoformat()
            except ValueError:
                continue

    else:
        # Monthly
        if start_date1:
            try:
                start = date.fromisoformat(start_date1)
                if start > today:
                    return start.isoformat()
            except (ValueError, TypeError):
                pass

        try:
            candidate = date(today.year, today.month, min(dia1, 28))
            if candidate > today:
                return candidate.isoformat()
        except ValueError:
            pass

        next_month = today.month + 1
        next_year = today.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        try:
            return date(next_year, next_month, min(dia1, 28)).isoformat()
        except ValueError:
            return date(next_year, next_month, 28).isoformat()

    return today.isoformat()


def add_deuda(user_id: str, nombre: str, deuda_total: float, pago_periodo: float, temporalidad: str, dia1: int, dia2: int = 0, start_date1: str = "", start_date2: str = "") -> dict:
    """Add a new debt record for the given user."""
    pagos_restantes = int(deuda_total / pago_periodo) if pago_periodo > 0 else 0

    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO deudas (user_id, nombre, deuda_total, pago_periodo, temporalidad, dia_pago_1, dia_pago_2, pagos_restantes, fecha_inicio_1, fecha_inicio_2)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, nombre, encrypt(deuda_total), encrypt(pago_periodo), temporalidad, dia1, dia2, encrypt(pagos_restantes), start_date1, start_date2)
        )
        record_id = cursor.lastrowid

    cache.invalidate(cache.user_key("deudas_all", user_id))

    next_payment = calculate_next_payment_date(temporalidad, dia1, dia2, start_date1, start_date2)

    return {
        "id": record_id,
        "name": nombre,
        "totalDebt": deuda_total,
        "paymentAmount": pago_periodo,
        "frequency": temporalidad,
        "payDay1": dia1,
        "payDay2": dia2,
        "paymentsRemaining": pagos_restantes,
        "nextPaymentDate": next_payment
    }


def get_all_deudas(user_id: str) -> list[dict]:
    """Read all debts for the given user and calculate next payment dates.
    Cached for 5 minutes. Automatically decrements pagos_restantes when a payment date passes."""
    cache_key = cache.user_key("deudas_all", user_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM deudas WHERE user_id = ?", (user_id,)
        ).fetchall()

    today = mx_today()
    deudas = []
    updates = []  # Collect (pagos_restantes, deuda_total, id) for batch update
    deletes = []  # Collect ids for batch delete

    for row in rows:
        temporalidad = row["temporalidad"]
        dia1 = row["dia_pago_1"]
        dia2 = row["dia_pago_2"]
        fecha_inicio_1 = row["fecha_inicio_1"]
        fecha_inicio_2 = row["fecha_inicio_2"]
        pagos_restantes = decrypt(row["pagos_restantes"], int)
        deuda_total = decrypt(row["deuda_total"], float)
        pago_periodo = decrypt(row["pago_periodo"], float)

        # Check how many payment dates have passed
        payments_due = _count_passed_payments(
            temporalidad, dia1, dia2, pagos_restantes,
            deuda_total, pago_periodo, row["id"], user_id
        )

        # Refresh values after potential update
        if payments_due > 0:
            pagos_restantes = max(0, pagos_restantes - payments_due)
            deuda_total = max(0, deuda_total - (pago_periodo * payments_due))

            # Auto-delete when fully paid
            if pagos_restantes <= 0:
                deletes.append(row["id"])
                continue
            else:
                updates.append((pagos_restantes, deuda_total, row["id"]))

        next_payment = calculate_next_payment_date(temporalidad, dia1, dia2, fecha_inicio_1, fecha_inicio_2)
        next_date = date.fromisoformat(next_payment)
        days_until = (next_date - today).days

        deudas.append({
            "id": row["id"],
            "name": row["nombre"],
            "totalDebt": deuda_total,
            "paymentAmount": pago_periodo,
            "frequency": temporalidad,
            "frequencyLabel": "Quincenal" if temporalidad == "quincenal" else "Mensual",
            "payDay1": dia1,
            "payDay2": dia2,
            "paymentsRemaining": pagos_restantes,
            "nextPaymentDate": next_payment,
            "daysUntilPayment": max(days_until, 0)
        })

    # Batch DB operations in a single connection
    if updates or deletes:
        with get_db() as conn:
            for pagos, total, record_id in updates:
                conn.execute(
                    "UPDATE deudas SET pagos_restantes = ?, deuda_total = ? WHERE id = ? AND user_id = ?",
                    (encrypt(pagos), encrypt(total), record_id, user_id)
                )
            for record_id in deletes:
                conn.execute("DELETE FROM deudas WHERE id = ? AND user_id = ?", (record_id, user_id))

    cache.set(cache_key, deudas, ttl_seconds=300)
    return deudas


def _count_passed_payments(temporalidad, dia1, dia2, pagos_restantes, deuda_total, pago_periodo, deuda_id, user_id: str) -> int:
    """Count how many payment dates have fully passed since last check."""
    from app.finanzas.update_tracker import get_last_update, mark_updated

    tracker_key = f"deuda_decrement_{deuda_id}"
    last_decrement = get_last_update(tracker_key, user_id)
    today = mx_today()

    if pagos_restantes <= 0 or deuda_total <= 0:
        return 0

    # Determine the start date for counting
    if last_decrement:
        start = date.fromisoformat(last_decrement) + timedelta(days=1)
    else:
        # First time: mark today as baseline, don't decrement anything
        mark_updated(tracker_key, user_id)
        return 0

    if start > today:
        return 0

    # Build list of actual payment dates between start and today (inclusive)
    count = 0
    if temporalidad == "quincenal":
        days = sorted(set([dia1] + ([dia2] if dia2 > 0 else [])))
    else:
        days = [dia1]

    # Iterate month by month from start to today
    current_year = start.year
    current_month = start.month

    while True:
        for d in days:
            try:
                payment_date = date(current_year, current_month, min(d, 28))
            except ValueError:
                continue

            # Count if payment_date is >= start AND on or before today
            if payment_date >= start and payment_date <= today:
                count += 1

        # Move to next month
        if current_year == today.year and current_month == today.month:
            break
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    if count > 0:
        mark_updated(tracker_key, user_id)

    return min(count, pagos_restantes)


def delete_deuda(user_id: str, record_id: int) -> bool:
    """Delete a debt by ID, only if it belongs to the user."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM deudas WHERE id = ? AND user_id = ?",
            (record_id, user_id)
        )
        deleted = cursor.rowcount > 0

    if deleted:
        cache.invalidate(cache.user_key("deudas_all", user_id))
    return deleted
