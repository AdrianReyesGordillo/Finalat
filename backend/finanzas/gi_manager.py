"""Module to manage Gastos/Ingresos using SQLite.

All operations are scoped by user_id for per-user data isolation.
"""
from datetime import date
from dateutil.relativedelta import relativedelta
from app.finanzas.database import get_db
from app.finanzas import cache
from app.finanzas.timezone import today as mx_today
from app.finanzas.crypto import encrypt, decrypt


def add_record(user_id: str, fecha: str, descripcion: str, categoria: str, tipo: str, monto: float) -> dict:
    """Add a new gasto/ingreso record for the given user."""
    # Monto negativo para gastos, positivo para ingresos
    if tipo == "gasto":
        monto = -abs(monto)
    else:
        monto = abs(monto)

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO gastos_ingresos (user_id, fecha, descripcion, categoria, tipo, monto) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, fecha, encrypt(descripcion), encrypt(categoria), tipo, encrypt(monto))
        )
        record_id = cursor.lastrowid

    cache.invalidate(cache.user_key("gi_records", user_id))

    return {
        "id": record_id,
        "date": fecha,
        "description": descripcion,
        "category": categoria,
        "type": tipo,
        "amount": monto
    }


def _purge_old_records(user_id: str):
    """Delete records older than 6 months for the given user."""
    today = mx_today()
    cutoff = date(today.year, today.month, 1) - relativedelta(months=5)

    with get_db() as conn:
        conn.execute(
            "DELETE FROM gastos_ingresos WHERE user_id = ? AND fecha < ?",
            (user_id, cutoff.isoformat())
        )


def get_all_records(user_id: str) -> list[dict]:
    """Read all records for the given user. Cached for 5 minutes.
    Also triggers cleanup of records older than 6 months."""
    cache_key = cache.user_key("gi_records", user_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    _purge_old_records(user_id)

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM gastos_ingresos WHERE user_id = ? ORDER BY fecha DESC",
            (user_id,)
        ).fetchall()

    records = []
    for row in rows:
        records.append({
            "id": row["id"],
            "date": row["fecha"],
            "description": decrypt(row["descripcion"], str),
            "category": decrypt(row["categoria"], str),
            "type": row["tipo"],
            "amount": decrypt(row["monto"], float)
        })

    cache.set(cache_key, records, ttl_seconds=300)
    return records


def delete_record(user_id: str, record_id: int) -> bool:
    """Delete a record by ID, only if it belongs to the user."""
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM gastos_ingresos WHERE id = ? AND user_id = ?",
            (record_id, user_id)
        )
        deleted = cursor.rowcount > 0

    if deleted:
        cache.invalidate(cache.user_key("gi_records", user_id))
    return deleted


def update_record(user_id: str, record_id: int, fecha: str, descripcion: str, categoria: str, tipo: str, monto: float) -> bool:
    """Update an existing gasto/ingreso record, only if it belongs to the user."""
    if tipo == "gasto":
        monto = -abs(monto)
    else:
        monto = abs(monto)

    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE gastos_ingresos SET fecha = ?, descripcion = ?, categoria = ?, tipo = ?, monto = ? WHERE id = ? AND user_id = ?",
            (fecha, encrypt(descripcion), encrypt(categoria), tipo, encrypt(monto), record_id, user_id)
        )
        updated = cursor.rowcount > 0

    if updated:
        cache.invalidate(cache.user_key("gi_records", user_id))
    return updated
