"""Module to read and manage Inversiones data from SQLite.

All operations are scoped by user_id for per-user data isolation.
"""
import re
from app.finanzas.database import get_db
from app.finanzas import cache
from app.finanzas.crypto import encrypt, decrypt


def get_ahorro(user_id: str) -> list[dict]:
    """Read savings accounts for the given user from SQLite."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM ahorro WHERE user_id = ?", (user_id,)
        ).fetchall()

    accounts = []
    for row in rows:
        balance = decrypt(row["balance"], float)
        description = decrypt(row["description"], str)
        annual_rate = row["annual_rate"]
        rate_cap = row["rate_cap"] or 0
        excess_rate = row["excess_rate"] or 0
        tax_rate = 0.9  # ISR retención diaria anual (%)

        # Tiered rate calculation
        if rate_cap > 0 and balance > rate_cap:
            gain_capped = rate_cap * (annual_rate - tax_rate) / 100 / 365
            gain_excess = (balance - rate_cap) * (excess_rate - tax_rate) / 100 / 365
            daily_gain = gain_capped + gain_excess
        else:
            net_annual_rate = annual_rate - tax_rate
            daily_gain = (balance * net_annual_rate / 100) / 365

        accounts.append({
            "name": row["name"],
            "description": description,
            "color": row["color"],
            "balance": balance,
            "annualRate": annual_rate,
            "rateCap": rate_cap,
            "excessRate": excess_rate,
            "dailyGain": round(daily_gain, 4)
        })

    return accounts


def get_prestamos(user_id: str) -> list[dict]:
    """Read loans for the given user from SQLite and calculate interest."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM prestamos WHERE user_id = ?", (user_id,)
        ).fetchall()

    loans = []
    for row in rows:
        principal = row["principal"]
        rate = row["rate"]
        term_str = row["term"]
        months = _parse_term_to_months(term_str)

        expected_interest = principal * (rate / 100) * (months / 12)
        total_return = principal + expected_interest

        status_raw = row["status"].lower().strip()
        is_active = status_raw in ["activo", "en curso", "vigente"]
        status_label = "Activo" if is_active else "Pagado"

        loans.append({
            "id": row["id"],
            "borrower": row["borrower"],
            "principal": principal,
            "rate": rate,
            "term": term_str,
            "expectedInterest": round(expected_interest, 2),
            "totalReturn": round(total_return, 2),
            "status": "activo" if is_active else "pagado",
            "statusLabel": status_label
        })

    return loans


def _parse_term_to_months(term_str: str) -> int:
    """Parse term string to number of months."""
    term_lower = term_str.lower().strip()

    numbers = re.findall(r'\d+', term_lower)
    if not numbers:
        return 12

    num = int(numbers[0])

    if 'año' in term_lower or 'year' in term_lower:
        return num * 12
    if 'mes' in term_lower or 'month' in term_lower:
        return num

    return num


def get_afore(user_id: str) -> dict:
    """Read afore data for the given user from SQLite."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM afore WHERE user_id = ?", (user_id,)
        ).fetchone()

    if not row:
        return {"balance": 0, "annualReturn": 0, "bimonthlyContribution": 0, "voluntaryContribution": 0}

    return {
        "balance": decrypt(row["balance"], float),
        "annualReturn": row["annual_return"],
        "bimonthlyContribution": decrypt(row["bimonthly_contribution"], float),
        "voluntaryContribution": decrypt(row["voluntary_contribution"], float)
    }


def update_ahorro_balances(user_id: str, balances: dict) -> str:
    """Update savings account balances for the given user.

    Args:
        user_id: Firebase UID.
        balances: dict mapping account name to new balance.

    Returns:
        Today's date string (ISO format).
    """
    from app.finanzas.update_tracker import mark_updated

    with get_db() as conn:
        for name, balance in balances.items():
            conn.execute(
                "UPDATE ahorro SET balance = ? WHERE name = ? AND user_id = ?",
                (encrypt(balance), name, user_id)
            )

    cache.invalidate(cache.user_key("inversiones_all", user_id))
    return mark_updated("ahorro", user_id)


def update_afore_data(user_id: str, fields: dict) -> str:
    """Update afore data for the given user.

    Args:
        user_id: Firebase UID.
        fields: dict with keys like 'balance', 'annualReturn', etc.

    Returns:
        Today's date string (ISO format).
    """
    from app.finanzas.update_tracker import mark_updated

    # Map API field names to DB column names
    field_map = {
        "balance": "balance",
        "annualReturn": "annual_return",
        "bimonthlyContribution": "bimonthly_contribution",
        "voluntaryContribution": "voluntary_contribution",
    }

    # Fields that should be encrypted
    encrypted_fields = {"balance", "bimonthly_contribution", "voluntary_contribution"}

    with get_db() as conn:
        # Ensure afore row exists for user
        existing = conn.execute(
            "SELECT id FROM afore WHERE user_id = ?", (user_id,)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO afore (user_id, balance, annual_return, bimonthly_contribution, voluntary_contribution) VALUES (?, ?, 0, ?, ?)",
                (user_id, encrypt(0), encrypt(0), encrypt(0))
            )

        for api_key, value in fields.items():
            col = field_map.get(api_key)
            if col:
                stored_value = encrypt(value) if col in encrypted_fields else value
                conn.execute(f"UPDATE afore SET {col} = ? WHERE user_id = ?", (stored_value, user_id))

    cache.invalidate(cache.user_key("inversiones_all", user_id))
    return mark_updated("afore", user_id)


def update_prestamos_data(user_id: str, prestamos_updates: list[dict]) -> str:
    """Update prestamos data for the given user.

    Args:
        user_id: Firebase UID.
        prestamos_updates: list of dicts with 'id' and fields to update.

    Returns:
        Today's date string (ISO format).
    """
    from app.finanzas.update_tracker import mark_updated

    with get_db() as conn:
        for update in prestamos_updates:
            row_id = update.get("id")
            if row_id is None:
                continue
            if "principal" in update:
                conn.execute("UPDATE prestamos SET principal = ? WHERE id = ? AND user_id = ?", (update["principal"], row_id, user_id))
            if "rate" in update:
                conn.execute("UPDATE prestamos SET rate = ? WHERE id = ? AND user_id = ?", (update["rate"], row_id, user_id))
            if "term" in update:
                conn.execute("UPDATE prestamos SET term = ? WHERE id = ? AND user_id = ?", (update["term"], row_id, user_id))
            if "status" in update:
                conn.execute("UPDATE prestamos SET status = ? WHERE id = ? AND user_id = ?", (update["status"], row_id, user_id))

    cache.invalidate(cache.user_key("inversiones_all", user_id))
    return mark_updated("prestamos", user_id)


def create_prestamo(user_id: str, principal: float, rate: float, term_months: int) -> dict:
    """Create a new loan for the given user and return the computed record."""
    from app.finanzas.update_tracker import mark_updated

    term_str = f"{term_months} meses"
    expected_interest = principal * (rate / 100) * (term_months / 12)
    total_return = principal + expected_interest

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO prestamos (user_id, borrower, principal, rate, term, status) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, "Préstamo", principal, rate, term_str, "activo")
        )
        new_id = cursor.lastrowid

    cache.invalidate(cache.user_key("inversiones_all", user_id))
    mark_updated("prestamos", user_id)

    return {
        "id": new_id,
        "borrower": "Préstamo",
        "principal": principal,
        "rate": rate,
        "term": term_str,
        "expectedInterest": round(expected_interest, 2),
        "totalReturn": round(total_return, 2),
        "status": "activo",
        "statusLabel": "Activo"
    }


def get_all_inversiones(user_id: str) -> dict:
    """Get all investment data for the given user. Cached for 5 minutes."""
    cache_key = cache.user_key("inversiones_all", user_id)
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    ahorro = get_ahorro(user_id)
    prestamos = get_prestamos(user_id)
    afore = get_afore(user_id)

    total_savings = sum(a["balance"] for a in ahorro)
    active_loans = [l for l in prestamos if l["status"] == "activo"]
    total_loans = sum(l["principal"] for l in active_loans)
    total_loan_interest = sum(l["expectedInterest"] for l in active_loans)
    avg_loan_rate = (sum(l["rate"] for l in active_loans) / len(active_loans)) if active_loans else 0

    result = {
        "ahorro": ahorro,
        "prestamos": prestamos,
        "afore": afore,
        "summary": {
            "totalSavings": total_savings,
            "totalLoans": total_loans,
            "totalLoanInterest": total_loan_interest,
            "avgLoanRate": round(avg_loan_rate, 1)
        }
    }

    cache.set(cache_key, result, ttl_seconds=300)
    return result
