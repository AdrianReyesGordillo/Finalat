"""Configuration routes — user preferences, ahorro/creditos/aportaciones CRUD.

Endpoints used by the Configuracion.vue in the finanzas module.
All endpoints are user-scoped via request.state.user_id (Firebase UID).
"""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.ahorro import Ahorro
from backend.models.creditos import Credito
from backend.models.aportaciones import Aportacion
from backend.models.categories import Category
from backend.services.encryption import encryption_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["config"])


def _uid(request: Request) -> Optional[str]:
    return getattr(request.state, "user_id", None)


# ---------------------------------------------------------------------------
# Metadata helpers (persist color, rate, etc. to account_metadata table)
# ---------------------------------------------------------------------------

async def _get_meta(db: AsyncSession, uid: str, table: str, record_id: str) -> dict:
    """Get all metadata for a specific record."""
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT meta_key, meta_value FROM account_metadata WHERE user_id = :uid AND table_name = :tbl AND record_id = :rid"),
        {"uid": uid, "tbl": table, "rid": record_id}
    )
    return {row[0]: row[1] for row in result.fetchall()}


async def _set_meta(db: AsyncSession, uid: str, table: str, record_id: str, meta: dict):
    """Upsert metadata for a record."""
    from sqlalchemy import text
    for key, value in meta.items():
        if value is not None:
            await db.execute(
                text("""INSERT INTO account_metadata (user_id, table_name, record_id, meta_key, meta_value)
                        VALUES (:uid, :tbl, :rid, :key, :val)
                        ON CONFLICT (user_id, table_name, record_id, meta_key)
                        DO UPDATE SET meta_value = :val"""),
                {"uid": uid, "tbl": table, "rid": record_id, "key": key, "val": str(value)}
            )
    await db.commit()


async def _del_meta(db: AsyncSession, uid: str, table: str, record_id: str):
    """Delete all metadata for a record."""
    from sqlalchemy import text
    await db.execute(
        text("DELETE FROM account_metadata WHERE user_id = :uid AND table_name = :tbl AND record_id = :rid"),
        {"uid": uid, "tbl": table, "rid": record_id}
    )
    await db.commit()


async def _get_all_meta(db: AsyncSession, uid: str, table: str) -> dict[str, dict]:
    """Get all metadata for all records of a table, grouped by record_id."""
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT record_id, meta_key, meta_value FROM account_metadata WHERE user_id = :uid AND table_name = :tbl"),
        {"uid": uid, "tbl": table}
    )
    grouped: dict[str, dict] = {}
    for rid, key, value in result.fetchall():
        if rid not in grouped:
            grouped[rid] = {}
        grouped[rid][key] = value
    return grouped


@router.get("/preferences")
async def preferences_get(request: Request, db: AsyncSession = Depends(get_db)):
    """Get all user preferences as a key-value map."""
    uid = _uid(request)
    if not uid:
        return {}
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT key, value FROM user_preferences WHERE user_id = :uid"),
        {"uid": uid}
    )
    return {row[0]: row[1] for row in result.fetchall()}


class PreferenceUpdate(BaseModel):
    key: str
    value: str

    @field_validator("key")
    @classmethod
    def validate_key(cls, v: str) -> str:
        v = v.strip()[:50]
        if not v:
            raise ValueError("Key cannot be empty")
        from backend.utils.validators import validate_no_injection
        validate_no_injection(v, "key")
        return v

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: str) -> str:
        from backend.utils.validators import sanitize_string
        return sanitize_string(v)[:500]


@router.post("/preferences")
async def preferences_set(payload: PreferenceUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    """Set a user preference (upsert)."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    from sqlalchemy import text
    await db.execute(
        text("""INSERT INTO user_preferences (user_id, key, value) VALUES (:uid, :key, :val)
                ON CONFLICT (user_id, key) DO UPDATE SET value = :val"""),
        {"uid": uid, "key": payload.key, "val": payload.value}
    )
    await db.commit()
    return {"success": True}


# ---------------------------------------------------------------------------
# Config: Ahorro (Savings Accounts)
# ---------------------------------------------------------------------------

class AhorroCreate(BaseModel):
    name: str
    description: str = ""
    annualRate: float = 0
    color: str = "#1da1f2"
    rateCap: float = 0
    excessRate: float = 0

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        from backend.utils.validators import validate_and_sanitize_name
        return validate_and_sanitize_name(v, "name", 100)

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        import re
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            return "#1da1f2"
        return v

    @field_validator("annualRate", "rateCap", "excessRate")
    @classmethod
    def validate_rates(cls, v: float) -> float:
        if v < 0 or v > 100:
            return 0
        return v


class AhorroUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    annualRate: Optional[float] = None
    color: Optional[str] = None
    rateCap: Optional[float] = None
    excessRate: Optional[float] = None


@router.get("/config/ahorro")
async def config_ahorro_list(request: Request, db: AsyncSession = Depends(get_db)):
    """List all savings accounts for the user."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content=[])
    stmt = select(Ahorro).where(Ahorro.user_id == uid)
    rows = (await db.execute(stmt)).scalars().all()
    all_meta = await _get_all_meta(db, uid, "ahorro")
    result = []
    for a in rows:
        try:
            balance = float(encryption_service.decrypt(a.amount_encrypted))
        except Exception:
            balance = 0
        meta = all_meta.get(a.id, {})
        result.append({
            "id": a.id,
            "name": a.account_name,
            "description": meta.get("description", ""),
            "balance": balance,
            "annual_rate": float(meta.get("annualRate", "0")),
            "color": meta.get("color", "#1da1f2"),
            "rate_cap": float(meta.get("rateCap", "0")),
            "excess_rate": float(meta.get("excessRate", "0")),
        })
    return result


@router.post("/config/ahorro")
async def config_ahorro_create(payload: AhorroCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new savings account."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    record = Ahorro(
        id=str(uuid.uuid4()),
        user_id=uid,
        account_name=payload.name,
        amount_encrypted=encryption_service.encrypt("0"),
    )
    db.add(record)
    await db.commit()
    await _set_meta(db, uid, "ahorro", record.id, {
        "description": payload.description,
        "annualRate": payload.annualRate,
        "color": payload.color,
        "rateCap": payload.rateCap,
        "excessRate": payload.excessRate,
    })
    return {"success": True, "id": record.id}


@router.put("/config/ahorro/{account_id}")
async def config_ahorro_update(account_id: str, payload: AhorroUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    """Update a savings account."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    stmt = select(Ahorro).where(Ahorro.id == account_id, Ahorro.user_id == uid)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return JSONResponse(status_code=404, content={"detail": "Account not found"})
    if payload.name is not None:
        record.account_name = payload.name
    await db.commit()
    meta_update = {}
    if payload.description is not None:
        meta_update["description"] = payload.description
    if payload.annualRate is not None:
        meta_update["annualRate"] = payload.annualRate
    if payload.color is not None:
        meta_update["color"] = payload.color
    if payload.rateCap is not None:
        meta_update["rateCap"] = payload.rateCap
    if payload.excessRate is not None:
        meta_update["excessRate"] = payload.excessRate
    if meta_update:
        await _set_meta(db, uid, "ahorro", account_id, meta_update)
    return {"success": True}


@router.delete("/config/ahorro/{account_id}")
async def config_ahorro_delete(account_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Delete a savings account."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    stmt = select(Ahorro).where(Ahorro.id == account_id, Ahorro.user_id == uid)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return JSONResponse(status_code=404, content={"detail": "Account not found"})
    await db.delete(record)
    await db.commit()
    await _del_meta(db, uid, "ahorro", account_id)
    return {"success": True}


# ---------------------------------------------------------------------------
# Config: Creditos (Credit Cards)
# ---------------------------------------------------------------------------

class CreditoCreate(BaseModel):
    name: str
    color: str = "#1da1f2"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        from backend.utils.validators import validate_and_sanitize_name
        return validate_and_sanitize_name(v, "name", 100)

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        import re
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            return "#1da1f2"
        return v


class CreditoUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


@router.get("/config/creditos")
async def config_creditos_list(request: Request, db: AsyncSession = Depends(get_db)):
    """List all credit cards for the user."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content=[])
    stmt = select(Credito).where(Credito.user_id == uid)
    rows = (await db.execute(stmt)).scalars().all()
    all_meta = await _get_all_meta(db, uid, "creditos")
    result = []
    for c in rows:
        meta = all_meta.get(c.id, {})
        result.append({"id": c.id, "name": c.card_name, "color": meta.get("color", "#1da1f2")})
    return result


@router.post("/config/creditos")
async def config_creditos_create(payload: CreditoCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new credit card."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    record = Credito(
        id=str(uuid.uuid4()),
        user_id=uid,
        card_name=payload.name,
        balance_encrypted=encryption_service.encrypt("0"),
        limit_encrypted=encryption_service.encrypt("0"),
        min_payment_encrypted=encryption_service.encrypt("0"),
    )
    db.add(record)
    await db.commit()
    await _set_meta(db, uid, "creditos", record.id, {"color": payload.color})
    return {"success": True, "id": record.id}


@router.put("/config/creditos/{card_id}")
async def config_creditos_update(card_id: str, payload: CreditoUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    """Update a credit card."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    stmt = select(Credito).where(Credito.id == card_id, Credito.user_id == uid)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return JSONResponse(status_code=404, content={"detail": "Card not found"})
    if payload.name is not None:
        record.card_name = payload.name
    await db.commit()
    meta_update = {}
    if payload.color is not None:
        meta_update["color"] = payload.color
    if meta_update:
        await _set_meta(db, uid, "creditos", card_id, meta_update)
    return {"success": True}


@router.delete("/config/creditos/{card_id}")
async def config_creditos_delete(card_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Delete a credit card."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    stmt = select(Credito).where(Credito.id == card_id, Credito.user_id == uid)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return JSONResponse(status_code=404, content={"detail": "Card not found"})
    await db.delete(record)
    await db.commit()
    await _del_meta(db, uid, "creditos", card_id)
    return {"success": True}


# ---------------------------------------------------------------------------
# Config: Aportaciones
# ---------------------------------------------------------------------------

class AportacionCreate(BaseModel):
    category: str
    amount: float
    person: str = ""
    color: str = "#1da1f2"
    frequency: str = "semanal"

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        from backend.utils.validators import validate_and_sanitize_name
        return validate_and_sanitize_name(v, "category", 100)

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: float) -> float:
        if v < 0 or v > 999_999_999.99:
            raise ValueError("Amount out of range")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        import re
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            return "#1da1f2"
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        valid = ("semanal", "quincenal", "mensual")
        if v not in valid:
            return "semanal"
        return v


class AportacionUpdate(BaseModel):
    category: Optional[str] = None
    amount: Optional[float] = None
    person: Optional[str] = None
    color: Optional[str] = None
    frequency: Optional[str] = None


@router.get("/config/aportaciones")
async def config_aportaciones_list(request: Request, db: AsyncSession = Depends(get_db)):
    """List all aportaciones for the user. Auto-creates 'Afore' if missing."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content=[])
    stmt = select(Aportacion).where(Aportacion.user_id == uid)
    rows = (await db.execute(stmt)).scalars().all()

    # Ensure default "Afore" aportacion exists
    has_afore = any(a.target_name.lower() == "afore" for a in rows)
    if not has_afore:
        from datetime import date
        from backend.models.database import async_session
        async with async_session() as new_db:
            # Ensure user exists in users table (for FK constraint)
            from sqlalchemy import text
            await new_db.execute(
                text("""INSERT INTO users (user_id, email) VALUES (:uid, '')
                        ON CONFLICT (user_id) DO NOTHING"""),
                {"uid": uid}
            )
            await new_db.commit()

            afore_record = Aportacion(
                id=str(uuid.uuid4()),
                user_id=uid,
                amount_encrypted=encryption_service.encrypt("0"),
                frequency="semanal",
                target_name="Afore",
                start_date=date.today(),
            )
            new_db.add(afore_record)
            await new_db.commit()
            # Save metadata
            from sqlalchemy import text
            await new_db.execute(
                text("""INSERT INTO account_metadata (user_id, table_name, record_id, meta_key, meta_value)
                        VALUES (:uid, 'aportaciones', :rid, 'color', '#10b981')
                        ON CONFLICT (user_id, table_name, record_id, meta_key) DO UPDATE SET meta_value = '#10b981'"""),
                {"uid": uid, "rid": afore_record.id}
            )
            await new_db.execute(
                text("""INSERT INTO account_metadata (user_id, table_name, record_id, meta_key, meta_value)
                        VALUES (:uid, 'aportaciones', :rid, 'system', 'true')
                        ON CONFLICT (user_id, table_name, record_id, meta_key) DO UPDATE SET meta_value = 'true'"""),
                {"uid": uid, "rid": afore_record.id}
            )
            await new_db.commit()
        # Re-query with original session
        rows = (await db.execute(stmt)).scalars().all()

    all_meta = await _get_all_meta(db, uid, "aportaciones")
    result = []
    for a in rows:
        try:
            amount = float(encryption_service.decrypt(a.amount_encrypted))
        except Exception:
            amount = 0
        meta = all_meta.get(a.id, {})
        result.append({
            "id": a.id,
            "category": a.target_name,
            "amount": amount,
            "person": meta.get("person", ""),
            "color": meta.get("color", "#1da1f2"),
            "frequency": a.frequency,
            "system": meta.get("system") == "true" or a.target_name.lower() == "afore",
        })
    return result


@router.post("/config/aportaciones")
async def config_aportaciones_create(payload: AportacionCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new aportacion."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    from datetime import date
    record = Aportacion(
        id=str(uuid.uuid4()),
        user_id=uid,
        amount_encrypted=encryption_service.encrypt(str(payload.amount)),
        frequency=payload.frequency,
        target_name=payload.category,
        start_date=date.today(),
    )
    db.add(record)
    await db.commit()
    await _set_meta(db, uid, "aportaciones", record.id, {"person": payload.person, "color": payload.color})
    return {"success": True, "id": record.id}


@router.put("/config/aportaciones/{config_id}")
async def config_aportaciones_update(config_id: str, payload: AportacionUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    """Update an aportacion."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    stmt = select(Aportacion).where(Aportacion.id == config_id, Aportacion.user_id == uid)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    if payload.category is not None and not record.target_name.lower() == "afore":
        record.target_name = payload.category
    if payload.amount is not None:
        record.amount_encrypted = encryption_service.encrypt(str(payload.amount))
    if payload.frequency is not None:
        record.frequency = payload.frequency
    await db.commit()
    meta_update = {}
    if payload.person is not None:
        meta_update["person"] = payload.person
    if payload.color is not None:
        meta_update["color"] = payload.color
    if meta_update:
        await _set_meta(db, uid, "aportaciones", config_id, meta_update)

    # If this is the Afore aportacion, sync voluntary contribution to afore table
    if record.target_name.lower() == "afore" and payload.amount is not None:
        from backend.models.afore import Afore as AforeModel
        afore_stmt = select(AforeModel).where(AforeModel.user_id == uid)
        afore_record = (await db.execute(afore_stmt)).scalars().first()
        if afore_record:
            # Store voluntary contribution amount in metadata
            from sqlalchemy import text
            await db.execute(
                text("""INSERT INTO account_metadata (user_id, table_name, record_id, meta_key, meta_value)
                        VALUES (:uid, 'afore', :rid, 'voluntary_contribution', :val)
                        ON CONFLICT (user_id, table_name, record_id, meta_key) DO UPDATE SET meta_value = :val"""),
                {"uid": uid, "rid": afore_record.id, "key": "voluntary_contribution", "val": str(payload.amount)}
            )
            await db.commit()

    return {"success": True}


@router.delete("/config/aportaciones/{config_id}")
async def config_aportaciones_delete(config_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Delete an aportacion. Cannot delete the system 'Afore' aportacion."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    stmt = select(Aportacion).where(Aportacion.id == config_id, Aportacion.user_id == uid)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return JSONResponse(status_code=404, content={"detail": "Not found"})
    if record.target_name.lower() == "afore":
        return JSONResponse(status_code=400, content={"detail": "La aportación de Afore no puede eliminarse."})
    await db.delete(record)
    await db.commit()
    await _del_meta(db, uid, "aportaciones", config_id)
    return {"success": True}


# ---------------------------------------------------------------------------
# GI Categories CRUD (POST/PUT/DELETE — GET already in finanzas router)
# ---------------------------------------------------------------------------

class CategoryCreate(BaseModel):
    name: str


class CategoryUpdate(BaseModel):
    name: str


@router.post("/gi/categories")
async def create_gi_category(payload: CategoryCreate, request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new gastos/ingresos category."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    # Check duplicate
    stmt = select(Category).where(Category.user_id == uid, Category.name == payload.name)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        return JSONResponse(status_code=400, content={"detail": "Ya existe una categoría con ese nombre."})
    record = Category(
        id=str(uuid.uuid4()),
        user_id=uid,
        name=payload.name,
        is_system=False,
    )
    db.add(record)
    await db.commit()
    return {"success": True, "id": record.id}


@router.put("/gi/categories/{category_id}")
async def update_gi_category(category_id: str, payload: CategoryUpdate, request: Request, db: AsyncSession = Depends(get_db)):
    """Update a category name."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    stmt = select(Category).where(Category.id == category_id, Category.user_id == uid)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return JSONResponse(status_code=404, content={"detail": "Category not found"})
    record.name = payload.name
    await db.commit()
    return {"success": True}


@router.delete("/gi/categories/{category_id}")
async def delete_gi_category(category_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Delete a category. Cannot delete system categories."""
    uid = _uid(request)
    if not uid:
        return JSONResponse(status_code=401, content={"success": False})
    stmt = select(Category).where(Category.id == category_id, Category.user_id == uid)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return JSONResponse(status_code=404, content={"detail": "Category not found"})
    if record.is_system:
        return JSONResponse(status_code=400, content={"detail": "Las categorías predeterminadas no se pueden eliminar."})
    await db.delete(record)
    await db.commit()
    return {"success": True}
