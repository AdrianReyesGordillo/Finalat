"""
Financial Dashboard routes — secured with Firebase Auth.

Every endpoint requires a valid Firebase ID token. Data is scoped per user
using the UID from the decoded token, ensuring complete data isolation.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from app.finanzas.gbm_reader import get_full_portfolio, parse_nacional_excel, parse_usa_excel, save_gbm_data
from app.finanzas.gi_manager import add_record, get_all_records, delete_record, update_record
from app.finanzas.creditos_reader import get_credit_cards
from app.finanzas.inversiones_reader import get_all_inversiones
from app.finanzas.deudas_manager import get_all_deudas, add_deuda, delete_deuda
from app.finanzas.update_tracker import get_status, mark_updated
from app.finanzas.database import init_db, migrate_db
from app.finanzas import cache
from app.finanzas.crypto import encrypt, decrypt
from app.services.auth import get_current_user

router = APIRouter(tags=["finanzas"])


def init_finanzas():
    """Initialize the dashboard SQLite DB and run migrations.

    Called from the main app lifespan/startup.
    """
    init_db()
    migrate_db()


# ===== Health (no auth required) =====

@router.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Financial Dashboard API"}


# ===== Claim unclaimed data =====

@router.post("/api/claim-data")
async def claim_unclaimed_data(current_user: dict = Depends(get_current_user)):
    """Assign all unclaimed data (user_id = '') or data marked with the user's
    email to the authenticated user's Firebase UID.

    This handles the migration case where data existed before Firebase Auth
    was implemented. Only rows with empty user_id or matching email are affected.
    Returns the count of rows claimed per table.
    """
    uid = current_user["uid"]
    email = current_user.get("email", "")
    from app.finanzas.database import get_db

    tables = [
        "ahorro", "prestamos", "creditos", "gastos_ingresos",
        "deudas", "gbm_nacional", "gbm_usa", "aportaciones",
        "aportaciones_config", "patrimonio_neto", "update_tracker", "afore",
        "gi_categories",
    ]

    claimed = {}
    with get_db() as conn:
        for table in tables:
            # Claim rows that are unclaimed OR marked with user's email
            result = conn.execute(
                f"UPDATE {table} SET user_id = ? WHERE user_id = '' OR user_id IS NULL OR user_id = ?",
                (uid, email)
            )
            if result.rowcount > 0:
                claimed[table] = result.rowcount

    # Invalidate all caches for this user
    cache.invalidate_prefix(cache.user_key("", uid))

    return {
        "success": True,
        "claimed": claimed,
        "totalRows": sum(claimed.values()),
    }


# ===== User Preferences =====

@router.get("/api/preferences")
async def preferences_get(current_user: dict = Depends(get_current_user)):
    """Get all user preferences as a key-value map."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        rows = conn.execute(
            "SELECT key, value FROM user_preferences WHERE user_id = ?", (uid,)
        ).fetchall()
    return {row["key"]: row["value"] for row in rows}


class PreferenceUpdate(BaseModel):
    key: str
    value: str


@router.post("/api/preferences")
async def preferences_set(payload: PreferenceUpdate, current_user: dict = Depends(get_current_user)):
    """Set a user preference (upsert)."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        conn.execute(
            """INSERT INTO user_preferences (user_id, key, value) VALUES (?, ?, ?)
               ON CONFLICT(user_id, key) DO UPDATE SET value = ?""",
            (uid, payload.key, payload.value, payload.value)
        )
    return {"success": True}


class PreferencesBulkUpdate(BaseModel):
    preferences: dict[str, str]


@router.post("/api/preferences/bulk")
async def preferences_set_bulk(payload: PreferencesBulkUpdate, current_user: dict = Depends(get_current_user)):
    """Set multiple user preferences at once."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        for key, value in payload.preferences.items():
            conn.execute(
                """INSERT INTO user_preferences (user_id, key, value) VALUES (?, ?, ?)
                   ON CONFLICT(user_id, key) DO UPDATE SET value = ?""",
                (uid, key, value, value)
            )
    return {"success": True}


# ===== Subscription & Tier =====

@router.get("/api/subscription")
async def get_subscription(current_user: dict = Depends(get_current_user)):
    """Get the current user's subscription info and permissions."""
    from app.finanzas.subscription import get_user_subscription, get_user_permissions, get_family_group
    uid = current_user["uid"]
    sub = get_user_subscription(uid)
    perms = get_user_permissions(uid)
    family = get_family_group(uid) if sub["tier"] == "family" else None
    return {
        **sub,
        "permissions": perms["permissions"],
        "familyGroup": family,
    }


class SubscriptionUpdate(BaseModel):
    tier: str


@router.post("/api/subscription")
async def update_subscription(payload: SubscriptionUpdate, current_user: dict = Depends(get_current_user)):
    """Update the user's subscription tier (free, student, family)."""
    from app.finanzas.subscription import set_user_subscription, VALID_TIERS, create_family_group
    uid = current_user["uid"]

    if payload.tier not in VALID_TIERS:
        raise HTTPException(status_code=400, detail=f"Tier inválido. Opciones: {VALID_TIERS}")

    # If upgrading to family, create the group automatically
    if payload.tier == "family":
        result = create_family_group(uid)
        return {"success": True, "subscription": result}

    sub = set_user_subscription(uid, payload.tier)
    return {"success": True, "subscription": sub}


# ===== Family Group =====

@router.get("/api/family-group")
async def get_family(current_user: dict = Depends(get_current_user)):
    """Get family group info for the current user."""
    from app.finanzas.subscription import get_family_group
    uid = current_user["uid"]
    group = get_family_group(uid)
    if not group:
        raise HTTPException(status_code=404, detail="No perteneces a un grupo familiar.")
    return group


class FamilyJoinRequest(BaseModel):
    inviteCode: str


@router.post("/api/family-group/join")
async def join_family(payload: FamilyJoinRequest, current_user: dict = Depends(get_current_user)):
    """Join a family group using an invite code."""
    from app.finanzas.subscription import join_family_group
    uid = current_user["uid"]
    try:
        group = join_family_group(uid, payload.inviteCode)
        return {"success": True, "familyGroup": group}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/family-group/leave")
async def leave_family(current_user: dict = Depends(get_current_user)):
    """Leave the current family group (members only, not owner)."""
    from app.finanzas.subscription import leave_family_group
    uid = current_user["uid"]
    try:
        sub = leave_family_group(uid)
        return {"success": True, "subscription": sub}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class FamilyRemoveRequest(BaseModel):
    memberId: str


@router.post("/api/family-group/remove-member")
async def remove_member(payload: FamilyRemoveRequest, current_user: dict = Depends(get_current_user)):
    """Remove a member from the family group (owner only)."""
    from app.finanzas.subscription import remove_family_member
    uid = current_user["uid"]
    try:
        group = remove_family_member(uid, payload.memberId)
        return {"success": True, "familyGroup": group}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/family-group")
async def delete_family(current_user: dict = Depends(get_current_user)):
    """Delete the family group (owner only). All members downgraded to free."""
    from app.finanzas.subscription import delete_family_group
    uid = current_user["uid"]
    try:
        delete_family_group(uid)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Stripe Payments =====

class CheckoutRequest(BaseModel):
    tier: str


@router.post("/api/stripe/create-checkout")
async def create_checkout(payload: CheckoutRequest, current_user: dict = Depends(get_current_user)):
    """Create a Stripe Checkout Session for subscribing to a tier."""
    from app.services.stripe_service import create_checkout_session
    uid = current_user["uid"]
    email = current_user.get("email", "")
    name = current_user.get("name", "")

    if payload.tier not in ("student", "family"):
        raise HTTPException(status_code=400, detail="Solo se puede suscribir a 'student' o 'family'.")

    try:
        url = create_checkout_session(uid, email, payload.tier, name)
        return {"url": url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear sesión de pago: {str(e)}")


@router.post("/api/stripe/create-portal")
async def create_portal(current_user: dict = Depends(get_current_user)):
    """Create a Stripe Customer Portal session for managing billing."""
    from app.services.stripe_service import create_portal_session
    uid = current_user["uid"]
    email = current_user.get("email", "")

    try:
        url = create_portal_session(uid, email)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear portal de facturación: {str(e)}")


from fastapi import Request


@router.post("/api/stripe/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (no auth — verified by Stripe signature)."""
    from app.services.stripe_service import handle_webhook_event

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        result = handle_webhook_event(payload, sig_header)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Dashboard (consolidated) =====

@router.get("/api/dashboard")
async def dashboard_data(current_user: dict = Depends(get_current_user)):
    """Consolidated endpoint for the Dashboard view. User-scoped."""
    uid = current_user["uid"]
    try:
        gbm = get_full_portfolio(uid)
        creditos = get_credit_cards(uid)
        inversiones = get_all_inversiones(uid)
        gi_records = get_all_records(uid)
        deudas = get_all_deudas(uid)

        total_debt = sum(d["totalDebt"] for d in deudas)

        return {
            "gbm": gbm,
            "creditos": creditos,
            "inversiones": inversiones,
            "gi": {"records": gi_records},
            "deudas": {"deudas": deudas, "totalDebt": total_debt}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== GBM Portfolio =====

@router.get("/api/gbm/portfolio")
async def gbm_portfolio(current_user: dict = Depends(get_current_user)):
    """Get GBM portfolio data. User-scoped."""
    uid = current_user["uid"]
    try:
        data = get_full_portfolio(uid)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/gbm/update-status")
async def gbm_update_status(current_user: dict = Depends(get_current_user)):
    """Check if GBM data needs to be updated (Fridays)."""
    uid = current_user["uid"]
    return get_status("gbm", "friday", uid)


@router.post("/api/gbm/upload")
async def gbm_upload(
    nacional: UploadFile = File(...),
    usa: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload new GBM Excel files. User-scoped."""
    uid = current_user["uid"]
    for f in [nacional, usa]:
        if not f.filename.lower().endswith(".xlsx"):
            raise HTTPException(status_code=400, detail=f"El archivo '{f.filename}' no es un .xlsx válido.")

    try:
        nacional_content = await nacional.read()
        usa_content = await usa.read()

        nacional_data = parse_nacional_excel(nacional_content)
        usa_data = parse_usa_excel(usa_content)

        save_gbm_data(uid, nacional_data, usa_data)
        today = mark_updated("gbm", uid)

        return {
            "success": True,
            "updatedAt": today,
            "files": {"nacional": nacional.filename, "usa": usa.filename}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Gastos / Ingresos =====

class GIRecord(BaseModel):
    date: str
    description: str
    category: str
    type: str  # "ingreso" or "gasto"
    amount: float


@router.get("/api/gi/records")
async def gi_get_records(current_user: dict = Depends(get_current_user)):
    """Get all gastos/ingresos records. User-scoped."""
    uid = current_user["uid"]
    try:
        records = get_all_records(uid)
        return {"records": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gi/records")
async def gi_add_record(payload: GIRecord, current_user: dict = Depends(get_current_user)):
    """Add a new gasto/ingreso record. User-scoped."""
    uid = current_user["uid"]
    try:
        record = add_record(
            user_id=uid,
            fecha=payload.date,
            descripcion=payload.description,
            categoria=payload.category,
            tipo=payload.type,
            monto=payload.amount
        )
        return {"success": True, "record": record}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/gi/records/{record_id}")
async def gi_delete_record(record_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a gasto/ingreso record. User-scoped."""
    uid = current_user["uid"]
    try:
        deleted = delete_record(uid, record_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Record not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/gi/records/{record_id}")
async def gi_update_record(record_id: int, payload: GIRecord, current_user: dict = Depends(get_current_user)):
    """Update a gasto/ingreso record. User-scoped."""
    uid = current_user["uid"]
    try:
        updated = update_record(
            user_id=uid,
            record_id=record_id,
            fecha=payload.date,
            descripcion=payload.description,
            categoria=payload.category,
            tipo=payload.type,
            monto=payload.amount
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Record not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== GI Categories =====

DEFAULT_GI_CATEGORIES = ['Sueldo', 'Creditos', 'Prestamos', 'Otros']

# System categories: always present for all users, cannot be edited or deleted.
SYSTEM_GI_CATEGORIES = {'Creditos', 'Sueldo'}


class GICategoryCreate(BaseModel):
    name: str


class GICategoryUpdate(BaseModel):
    name: str | None = None


@router.get("/api/gi/categories")
async def gi_get_categories(current_user: dict = Depends(get_current_user)):
    """Get GI categories for user. Seeds defaults if none exist."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    try:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM gi_categories WHERE user_id = ? ORDER BY sort_order, id",
                (uid,)
            ).fetchall()

            # If no categories exist, seed defaults from existing records or fallback
            if not rows:
                # Check what categories the user already has in their records
                existing = conn.execute(
                    "SELECT id, categoria FROM gastos_ingresos WHERE user_id = ?",
                    (uid,)
                ).fetchall()
                existing_cats = []
                for r in existing:
                    cat = decrypt(r["categoria"], str)
                    if cat:
                        existing_cats.append(cat)

                # Merge: use existing record categories + defaults (deduplicated, preserving order)
                cats_to_seed = []
                seen = set()
                for cat in existing_cats:
                    if cat and cat not in seen:
                        cats_to_seed.append(cat)
                        seen.add(cat)
                for cat in DEFAULT_GI_CATEGORIES:
                    if cat not in seen:
                        cats_to_seed.append(cat)
                        seen.add(cat)

                for idx, cat in enumerate(cats_to_seed):
                    conn.execute(
                        "INSERT INTO gi_categories (user_id, name, sort_order) VALUES (?, ?, ?)",
                        (uid, cat, idx)
                    )

                rows = conn.execute(
                    "SELECT * FROM gi_categories WHERE user_id = ? ORDER BY sort_order, id",
                    (uid,)
                ).fetchall()

        return [{"id": r["id"], "name": r["name"], "system": r["name"] in SYSTEM_GI_CATEGORIES} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/gi/categories")
async def gi_add_category(payload: GICategoryCreate, current_user: dict = Depends(get_current_user)):
    """Add a new GI category. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    try:
        with get_db() as conn:
            # Get next sort_order
            row = conn.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 as next_order FROM gi_categories WHERE user_id = ?",
                (uid,)
            ).fetchone()
            next_order = row["next_order"] if row else 0

            cursor = conn.execute(
                "INSERT INTO gi_categories (user_id, name, sort_order) VALUES (?, ?, ?)",
                (uid, payload.name, next_order)
            )
            new_id = cursor.lastrowid
        return {"success": True, "id": new_id}
    except Exception as e:
        if "UNIQUE" in str(e).upper() or "unique" in str(e):
            raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/gi/categories/{category_id}")
async def gi_update_category(category_id: int, payload: GICategoryUpdate, current_user: dict = Depends(get_current_user)):
    """Update a GI category. Also updates existing records with old name."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    try:
        with get_db() as conn:
            # Get current name for renaming records
            current = conn.execute(
                "SELECT name FROM gi_categories WHERE id = ? AND user_id = ?",
                (category_id, uid)
            ).fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Category not found")

            # Block editing system categories
            if current["name"] in SYSTEM_GI_CATEGORIES:
                raise HTTPException(status_code=403, detail="No se puede editar una categoría del sistema.")

            old_name = current["name"]
            new_name = payload.name if payload.name else old_name

            # Update category
            if payload.name:
                conn.execute(
                    "UPDATE gi_categories SET name = ? WHERE id = ? AND user_id = ?",
                    (new_name, category_id, uid)
                )

            # Rename category in existing gastos_ingresos records
            if payload.name and payload.name != old_name:
                # Since categoria is encrypted, fetch all records and update by ID
                gi_rows = conn.execute(
                    "SELECT id, categoria FROM gastos_ingresos WHERE user_id = ?",
                    (uid,)
                ).fetchall()
                for gi_row in gi_rows:
                    if decrypt(gi_row["categoria"], str) == old_name:
                        conn.execute(
                            "UPDATE gastos_ingresos SET categoria = ? WHERE id = ?",
                            (encrypt(new_name), gi_row["id"])
                        )
                cache.invalidate(cache.user_key("gi_records", uid))

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        if "UNIQUE" in str(e).upper() or "unique" in str(e):
            raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/gi/categories/{category_id}")
async def gi_delete_category(category_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a GI category. Records keep their category text but it won't appear in selector."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    try:
        with get_db() as conn:
            # Check if it's a system category
            cat_row = conn.execute(
                "SELECT name FROM gi_categories WHERE id = ? AND user_id = ?",
                (category_id, uid)
            ).fetchone()
            if not cat_row:
                raise HTTPException(status_code=404, detail="Category not found")
            if cat_row["name"] in SYSTEM_GI_CATEGORIES:
                raise HTTPException(status_code=403, detail="No se puede eliminar una categoría del sistema.")

            result = conn.execute(
                "DELETE FROM gi_categories WHERE id = ? AND user_id = ?",
                (category_id, uid)
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Category not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Créditos =====

@router.get("/api/creditos")
async def creditos_get(current_user: dict = Depends(get_current_user)):
    """Get credit card data. User-scoped."""
    uid = current_user["uid"]
    try:
        data = get_credit_cards(uid)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/creditos/update-status")
async def creditos_update_status(current_user: dict = Depends(get_current_user)):
    """Check if credit card data needs to be updated (Mondays)."""
    uid = current_user["uid"]
    return get_status("creditos", "monday", uid)


class CreditCardUpdate(BaseModel):
    name: str
    debt: float | None = None
    available: float | None = None
    cutoffDate: str | None = None
    paymentDate: str | None = None
    minimumPayment: float | None = None
    fullPayment: float | None = None
    creditLimit: float | None = None


@router.post("/api/creditos/update-card")
async def creditos_update_card(payload: CreditCardUpdate, current_user: dict = Depends(get_current_user)):
    """Update fields for a specific credit card. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.creditos_reader import update_credit_card
    try:
        fields = {k: v for k, v in payload.model_dump().items() if k != "name" and v is not None}
        today = update_credit_card(uid, payload.name, fields)
        return {"success": True, "updatedAt": today}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Inversiones =====

@router.get("/api/inversiones")
async def inversiones_get(current_user: dict = Depends(get_current_user)):
    """Get all investment data. User-scoped."""
    uid = current_user["uid"]
    try:
        data = get_all_inversiones(uid)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/inversiones/update-status")
async def inversiones_update_status(current_user: dict = Depends(get_current_user)):
    """Check if savings data needs to be updated (Mondays)."""
    uid = current_user["uid"]
    return get_status("ahorro", "monday", uid)


@router.get("/api/inversiones/afore/update-status")
async def afore_update_status(current_user: dict = Depends(get_current_user)):
    """Check if afore data needs to be updated (1st of month)."""
    uid = current_user["uid"]
    return get_status("afore", "first_of_month", uid)


@router.post("/api/inversiones/afore/mark-updated")
async def afore_mark_updated(current_user: dict = Depends(get_current_user)):
    """Mark afore data as updated today."""
    uid = current_user["uid"]
    today = mark_updated("afore", uid)
    return {"success": True, "updatedAt": today}


class AforeUpdate(BaseModel):
    balance: float | None = None
    annualReturn: float | None = None
    bimonthlyContribution: float | None = None
    voluntaryContribution: float | None = None


@router.post("/api/inversiones/afore/update-data")
async def afore_update_data(payload: AforeUpdate, current_user: dict = Depends(get_current_user)):
    """Update afore fields. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.inversiones_reader import update_afore_data
    try:
        fields = {k: v for k, v in payload.model_dump().items() if v is not None}
        if not fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        today = update_afore_data(uid, fields)
        return {"success": True, "updatedAt": today}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/inversiones/prestamos/update-status")
async def prestamos_update_status(current_user: dict = Depends(get_current_user)):
    """Check if prestamos data needs to be updated (15th of month)."""
    uid = current_user["uid"]
    return get_status("prestamos", "fifteenth", uid)


@router.post("/api/inversiones/prestamos/mark-updated")
async def prestamos_mark_updated(current_user: dict = Depends(get_current_user)):
    """Mark prestamos data as updated today."""
    uid = current_user["uid"]
    today = mark_updated("prestamos", uid)
    return {"success": True, "updatedAt": today}


class PrestamoUpdate(BaseModel):
    id: int
    principal: float | None = None
    rate: float | None = None
    term: str | None = None
    status: str | None = None


class NuevoPrestamoPayload(BaseModel):
    principal: float
    rate: float
    termMonths: int


@router.post("/api/inversiones/prestamos")
async def prestamos_create(payload: NuevoPrestamoPayload, current_user: dict = Depends(get_current_user)):
    """Create a new loan. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.inversiones_reader import create_prestamo
    try:
        loan = create_prestamo(uid, principal=payload.principal, rate=payload.rate, term_months=payload.termMonths)
        return {"success": True, "loan": loan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PrestamosUpdatePayload(BaseModel):
    updates: list[PrestamoUpdate]


@router.post("/api/inversiones/prestamos/update-data")
async def prestamos_update_data(payload: PrestamosUpdatePayload, current_user: dict = Depends(get_current_user)):
    """Update prestamos data. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.inversiones_reader import update_prestamos_data
    try:
        updates = [u.model_dump(exclude_none=True) for u in payload.updates]
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        today = update_prestamos_data(uid, updates)
        return {"success": True, "updatedAt": today}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/inversiones/mark-updated")
async def inversiones_mark_updated(current_user: dict = Depends(get_current_user)):
    """Mark savings data as updated today."""
    uid = current_user["uid"]
    today = mark_updated("ahorro", uid)
    return {"success": True, "updatedAt": today}


class AhorroBalances(BaseModel):
    balances: dict[str, float]


@router.post("/api/inversiones/update-balances")
async def inversiones_update_balances(payload: AhorroBalances, current_user: dict = Depends(get_current_user)):
    """Update savings account balances. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.inversiones_reader import update_ahorro_balances
    try:
        today = update_ahorro_balances(uid, payload.balances)
        return {"success": True, "updatedAt": today}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Deudas =====

class DeudaRecord(BaseModel):
    name: str
    totalDebt: float
    paymentAmount: float
    frequency: str  # "mensual" or "quincenal"
    payDay1: int
    payDay2: int = 0
    startDate1: str = ""
    startDate2: str = ""


@router.get("/api/deudas")
async def deudas_get(current_user: dict = Depends(get_current_user)):
    """Get all debts. User-scoped."""
    uid = current_user["uid"]
    try:
        deudas = get_all_deudas(uid)
        total_debt = sum(d["totalDebt"] for d in deudas)
        return {"deudas": deudas, "totalDebt": total_debt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/deudas")
async def deudas_add(payload: DeudaRecord, current_user: dict = Depends(get_current_user)):
    """Add a new debt. User-scoped."""
    uid = current_user["uid"]
    try:
        deuda = add_deuda(
            user_id=uid,
            nombre=payload.name,
            deuda_total=payload.totalDebt,
            pago_periodo=payload.paymentAmount,
            temporalidad=payload.frequency,
            dia1=payload.payDay1,
            dia2=payload.payDay2,
            start_date1=payload.startDate1,
            start_date2=payload.startDate2
        )
        return {"success": True, "deuda": deuda}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/deudas/{record_id}")
async def deudas_delete(record_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a debt by ID. User-scoped."""
    uid = current_user["uid"]
    try:
        deleted = delete_deuda(uid, record_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Debt not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Aportaciones =====

class AportacionStatusUpdate(BaseModel):
    id: int
    status: str  # "pendiente" | "realizada" | "atrasada"


@router.get("/api/aportaciones")
async def aportaciones_get(year: int | None = None, month: int | None = None, current_user: dict = Depends(get_current_user)):
    """Get aportaciones for a given month. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.aportaciones_manager import get_aportaciones
    from datetime import date as d
    try:
        today = d.today()
        y = year or today.year
        m = month or today.month
        data = get_aportaciones(uid, y, m)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/aportaciones/update-status")
async def aportaciones_update_status(payload: AportacionStatusUpdate, current_user: dict = Depends(get_current_user)):
    """Update the status of an aportacion. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.aportaciones_manager import update_aportacion_status
    try:
        updated = update_aportacion_status(uid, payload.id, payload.status)
        if not updated:
            raise HTTPException(status_code=400, detail="Invalid ID or status")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== Configuración =====

# --- Ahorro CRUD ---

class AhorroCreate(BaseModel):
    name: str
    description: str = ""
    annualRate: float = 0
    color: str = "#1da1f2"
    rateCap: float = 0
    excessRate: float = 0


class AhorroUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    annualRate: float | None = None
    color: str | None = None
    rateCap: float | None = None
    excessRate: float | None = None


@router.get("/api/config/ahorro")
async def config_ahorro_list(current_user: dict = Depends(get_current_user)):
    """List all savings accounts. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM ahorro WHERE user_id = ?", (uid,)).fetchall()
    result = []
    for row in rows:
        r = dict(row)
        r["description"] = decrypt(r.get("description"), str)
        r["balance"] = decrypt(r.get("balance"), float)
        result.append(r)
    return result


@router.post("/api/config/ahorro")
async def config_ahorro_create(payload: AhorroCreate, current_user: dict = Depends(get_current_user)):
    """Create a new savings account. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO ahorro (user_id, name, description, color, balance, annual_rate, rate_cap, excess_rate) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (uid, payload.name, encrypt(payload.description), payload.color, encrypt(0), payload.annualRate, payload.rateCap, payload.excessRate)
        )
        new_id = cursor.lastrowid
    cache.invalidate(cache.user_key("inversiones_all", uid))
    return {"success": True, "id": new_id}


@router.put("/api/config/ahorro/{account_id}")
async def config_ahorro_update(account_id: int, payload: AhorroUpdate, current_user: dict = Depends(get_current_user)):
    """Update a savings account. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    field_map = {"name": "name", "description": "description", "annualRate": "annual_rate", "color": "color", "rateCap": "rate_cap", "excessRate": "excess_rate"}
    # Fields that need encryption
    encrypted_api_fields = {"description"}
    with get_db() as conn:
        for api_field, value in fields.items():
            col = field_map.get(api_field)
            if col:
                stored_value = encrypt(value) if api_field in encrypted_api_fields else value
                conn.execute(f"UPDATE ahorro SET {col} = ? WHERE id = ? AND user_id = ?", (stored_value, account_id, uid))
    cache.invalidate(cache.user_key("inversiones_all", uid))
    return {"success": True}


@router.delete("/api/config/ahorro/{account_id}")
async def config_ahorro_delete(account_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a savings account. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        result = conn.execute("DELETE FROM ahorro WHERE id = ? AND user_id = ?", (account_id, uid))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Account not found")
    cache.invalidate(cache.user_key("inversiones_all", uid))
    return {"success": True}


# --- Creditos CRUD ---

class CreditoCreate(BaseModel):
    name: str
    color: str = "#1da1f2"


class CreditoConfigUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


@router.get("/api/config/creditos")
async def config_creditos_list(current_user: dict = Depends(get_current_user)):
    """List all credit cards (config). User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        rows = conn.execute("SELECT id, name, color FROM creditos WHERE user_id = ?", (uid,)).fetchall()
    return [dict(row) for row in rows]


@router.post("/api/config/creditos")
async def config_creditos_create(payload: CreditoCreate, current_user: dict = Depends(get_current_user)):
    """Create a new credit card. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO creditos (user_id, name, color) VALUES (?, ?, ?)",
            (uid, payload.name, payload.color)
        )
        new_id = cursor.lastrowid
    cache.invalidate(cache.user_key("creditos_cards", uid))
    return {"success": True, "id": new_id}


@router.put("/api/config/creditos/{card_id}")
async def config_creditos_update(card_id: int, payload: CreditoConfigUpdate, current_user: dict = Depends(get_current_user)):
    """Update a credit card's config. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    with get_db() as conn:
        for field, value in fields.items():
            conn.execute(f"UPDATE creditos SET {field} = ? WHERE id = ? AND user_id = ?", (value, card_id, uid))
    cache.invalidate(cache.user_key("creditos_cards", uid))
    return {"success": True}


@router.delete("/api/config/creditos/{card_id}")
async def config_creditos_delete(card_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a credit card. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        result = conn.execute("DELETE FROM creditos WHERE id = ? AND user_id = ?", (card_id, uid))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Card not found")
    cache.invalidate(cache.user_key("creditos_cards", uid))
    return {"success": True}


# --- Aportaciones Config CRUD ---

class AportacionConfigCreate(BaseModel):
    category: str
    amount: float
    person: str = ""
    color: str = "#1da1f2"
    frequency: str = "semanal"


class AportacionConfigUpdate(BaseModel):
    category: str | None = None
    amount: float | None = None
    person: str | None = None
    color: str | None = None
    frequency: str | None = None


@router.get("/api/config/aportaciones")
async def config_aportaciones_list(current_user: dict = Depends(get_current_user)):
    """List all aportaciones config entries. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM aportaciones_config WHERE user_id = ? ORDER BY id", (uid,)).fetchall()
    result = []
    for row in rows:
        r = dict(row)
        r["category"] = decrypt(r.get("category"), str)
        r["amount"] = decrypt(r.get("amount"), float)
        r["person"] = decrypt(r.get("person"), str)
        result.append(r)
    return result


@router.post("/api/config/aportaciones")
async def config_aportaciones_create(payload: AportacionConfigCreate, current_user: dict = Depends(get_current_user)):
    """Create a new aportacion config. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO aportaciones_config (user_id, category, amount, person, color, frequency) VALUES (?, ?, ?, ?, ?, ?)",
            (uid, encrypt(payload.category), encrypt(payload.amount), encrypt(payload.person), payload.color, payload.frequency)
        )
        new_id = cursor.lastrowid

        # Sync Afore voluntary contribution
        if payload.category.lower() == "afore" and not payload.person:
            conn.execute(
                """INSERT INTO afore (user_id, balance, annual_return, bimonthly_contribution, voluntary_contribution)
                   VALUES (?, ?, 0, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET voluntary_contribution = ?""",
                (uid, encrypt(0), encrypt(0), encrypt(payload.amount), encrypt(payload.amount))
            )
            cache.invalidate(cache.user_key("inversiones_all", uid))

    cache.invalidate_prefix(cache.user_key("aportaciones", uid))
    return {"success": True, "id": new_id}


@router.put("/api/config/aportaciones/{config_id}")
async def config_aportaciones_update(config_id: int, payload: AportacionConfigUpdate, current_user: dict = Depends(get_current_user)):
    """Update an aportacion config entry. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Fields that need encryption
    encrypted_aport_fields = {"category", "amount", "person"}

    with get_db() as conn:
        for field, value in fields.items():
            stored_value = encrypt(value) if field in encrypted_aport_fields else value
            conn.execute(f"UPDATE aportaciones_config SET {field} = ? WHERE id = ? AND user_id = ?", (stored_value, config_id, uid))

        # Sync Afore voluntary contribution if amount changed
        if "amount" in fields:
            row = conn.execute(
                "SELECT category, person FROM aportaciones_config WHERE id = ? AND user_id = ?",
                (config_id, uid)
            ).fetchone()
            if row and decrypt(row["category"], str).lower() == "afore" and not decrypt(row["person"], str):
                conn.execute(
                    """INSERT INTO afore (user_id, balance, annual_return, bimonthly_contribution, voluntary_contribution)
                       VALUES (?, ?, 0, ?, ?)
                       ON CONFLICT(user_id) DO UPDATE SET voluntary_contribution = ?""",
                    (uid, encrypt(0), encrypt(0), encrypt(fields["amount"]), encrypt(fields["amount"]))
                )
                cache.invalidate(cache.user_key("inversiones_all", uid))

    cache.invalidate_prefix(cache.user_key("aportaciones", uid))
    return {"success": True}


@router.delete("/api/config/aportaciones/{config_id}")
async def config_aportaciones_delete(config_id: int, current_user: dict = Depends(get_current_user)):
    """Delete an aportacion config entry and its associated records. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    with get_db() as conn:
        # Get the config details before deleting (needed to clean up aportaciones)
        config_row = conn.execute(
            "SELECT category, person FROM aportaciones_config WHERE id = ? AND user_id = ?",
            (config_id, uid)
        ).fetchone()
        if not config_row:
            raise HTTPException(status_code=404, detail="Config not found")

        # Delete the config
        conn.execute("DELETE FROM aportaciones_config WHERE id = ? AND user_id = ?", (config_id, uid))

        # Delete orphaned aportaciones records for this category+person
        category_plain = decrypt(config_row["category"], str)
        person_plain = decrypt(config_row["person"], str)
        conn.execute(
            "DELETE FROM aportaciones WHERE user_id = ? AND category = ? AND person = ?",
            (uid, category_plain, person_plain)
        )
    cache.invalidate_prefix(cache.user_key("aportaciones", uid))
    return {"success": True}


# ===== Patrimonio Neto =====

@router.get("/api/patrimonio")
async def patrimonio_get(current_user: dict = Depends(get_current_user)):
    """Get patrimonio neto history (last 6 months). User-scoped.
    Automatically takes a snapshot on the 1st of the current month if not already done."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    from datetime import date as d

    today = d.today()
    current_month_key = f"{today.year}-{str(today.month).zfill(2)}"

    # Auto-snapshot on the 1st (or first access of the month)
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM patrimonio_neto WHERE user_id = ? AND month = ?",
            (uid, current_month_key)
        ).fetchone()

    if not existing:
        try:
            inversiones = get_all_inversiones(uid)
            gbm = get_full_portfolio(uid)
            creditos = get_credit_cards(uid)

            total_savings = sum(a["balance"] for a in inversiones.get("ahorro", []))
            total_loans = inversiones.get("summary", {}).get("totalLoans", 0)
            gbm_total = gbm.get("summary", {}).get("totalValueMXN", 0)
            afore_balance = inversiones.get("afore", {}).get("balance", 0)
            total_portfolio = total_savings + total_loans + gbm_total + afore_balance

            total_credit_debt = creditos.get("summary", {}).get("totalDebt", 0)
            patrimonio = total_portfolio - total_credit_debt

            with get_db() as conn:
                conn.execute(
                    """INSERT INTO patrimonio_neto (user_id, month, value) VALUES (?, ?, ?)
                       ON CONFLICT(user_id, month) DO UPDATE SET value = ?""",
                    (uid, current_month_key, encrypt(round(patrimonio, 2)), encrypt(round(patrimonio, 2)))
                )
        except Exception:
            pass

    # Return last 6 months for this user
    with get_db() as conn:
        rows = conn.execute(
            "SELECT month, value FROM patrimonio_neto WHERE user_id = ? ORDER BY month DESC LIMIT 6",
            (uid,)
        ).fetchall()

    history = [{"month": row["month"], "value": decrypt(row["value"], float)} for row in reversed(rows)]
    return {"history": history}


@router.post("/api/patrimonio/snapshot")
async def patrimonio_snapshot(current_user: dict = Depends(get_current_user)):
    """Force a patrimonio neto snapshot for the current month. User-scoped."""
    uid = current_user["uid"]
    from app.finanzas.database import get_db
    from datetime import date as d

    today = d.today()
    current_month_key = f"{today.year}-{str(today.month).zfill(2)}"

    try:
        inversiones = get_all_inversiones(uid)
        gbm = get_full_portfolio(uid)
        creditos = get_credit_cards(uid)

        total_savings = sum(a["balance"] for a in inversiones.get("ahorro", []))
        total_loans = inversiones.get("summary", {}).get("totalLoans", 0)
        gbm_total = gbm.get("summary", {}).get("totalValueMXN", 0)
        afore_balance = inversiones.get("afore", {}).get("balance", 0)
        total_portfolio = total_savings + total_loans + gbm_total + afore_balance

        total_credit_debt = creditos.get("summary", {}).get("totalDebt", 0)
        patrimonio = total_portfolio - total_credit_debt

        with get_db() as conn:
            conn.execute(
                """INSERT INTO patrimonio_neto (user_id, month, value) VALUES (?, ?, ?)
                   ON CONFLICT(user_id, month) DO UPDATE SET value = ?""",
                (uid, current_month_key, encrypt(round(patrimonio, 2)), encrypt(round(patrimonio, 2)))
            )

        return {"success": True, "month": current_month_key, "value": round(patrimonio, 2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
