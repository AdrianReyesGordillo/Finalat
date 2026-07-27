"""Finanzas routes — dashboard endpoints backed by the real encrypted DB tables.

These endpoints query the SQLAlchemy models (gastos_ingresos, ahorro, creditos,
deudas, afore, gbm_portfolio, categories), decrypt the Fernet-encrypted fields,
and return data in the structure the frontend finanzas views expect.

All endpoints are user-scoped via request.state.user_id (Firebase UID from auth middleware).
"""

import logging
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.gastos_ingresos import GastoIngreso
from backend.models.categories import Category
from backend.models.ahorro import Ahorro
from backend.models.creditos import Credito
from backend.models.deudas import Deuda
from backend.models.afore import Afore
from backend.models.aportaciones import Aportacion
from backend.models.gbm_portfolio import GbmPortfolio
from backend.services.encryption import encryption_service, EncryptionError
from backend.utils.validators import sanitize_string, validate_no_injection, ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["finanzas"])


def _uid(request: Request):
    return getattr(request.state, "user_id", None)


def _dec(ciphertext: str) -> float:
    """Decrypt an encrypted numeric field to float. Returns 0.0 on failure."""
    try:
        return float(encryption_service.decrypt(ciphertext))
    except (EncryptionError, ValueError, InvalidOperation, TypeError):
        return 0.0


# ---------------------------------------------------------------------------
# Data loaders (shared by dashboard + individual endpoints)
# ---------------------------------------------------------------------------


async def _load_gi_records(db: AsyncSession, user_id: str):
    """Load gastos/ingresos records with category names and signed amounts."""
    cat_stmt = select(Category).where(Category.user_id == user_id)
    cats = {c.id: c.name for c in (await db.execute(cat_stmt)).scalars().all()}

    stmt = (
        select(GastoIngreso)
        .where(GastoIngreso.user_id == user_id)
        .order_by(GastoIngreso.entry_date.desc())
    )
    entries = (await db.execute(stmt)).scalars().all()

    records = []
    for e in entries:
        amount = _dec(e.amount_encrypted)
        signed = amount if e.type == "income" else -abs(amount)
        try:
            description = encryption_service.decrypt(e.description_encrypted)
        except EncryptionError:
            description = ""
        records.append({
            "id": e.id,
            "date": e.entry_date.isoformat() if e.entry_date else None,
            "description": description,
            "amount": signed,
            "category": cats.get(e.category_id, "Sin categoría"),
            "type": "ingreso" if e.type == "income" else "gasto",
        })
    return records


async def _load_ahorro(db: AsyncSession, user_id: str):
    stmt = select(Ahorro).where(Ahorro.user_id == user_id)
    rows = (await db.execute(stmt)).scalars().all()

    # Load metadata (color, rates) from account_metadata table
    from sqlalchemy import text
    meta_result = await db.execute(
        text("SELECT record_id, meta_key, meta_value FROM account_metadata WHERE user_id = :uid AND table_name = 'ahorro'"),
        {"uid": user_id}
    )
    all_meta: dict[str, dict] = {}
    for rid, key, value in meta_result.fetchall():
        if rid not in all_meta:
            all_meta[rid] = {}
        all_meta[rid][key] = value

    result = []
    for a in rows:
        balance = _dec(a.amount_encrypted)
        meta = all_meta.get(a.id, {})
        annual_rate = float(meta.get("annualRate", "0"))
        daily_gain = round(balance * (annual_rate / 100) / 365, 2)
        result.append({
            "id": a.id,
            "name": a.account_name,
            "accountName": a.account_name,
            "balance": balance,
            "annualRate": annual_rate,
            "color": meta.get("color", "#1da1f2"),
            "rateCap": float(meta.get("rateCap", "0")),
            "excessRate": float(meta.get("excessRate", "0")),
            "dailyGain": daily_gain,
        })
    return result


async def _load_creditos(db: AsyncSession, user_id: str):
    stmt = select(Credito).where(Credito.user_id == user_id)
    rows = (await db.execute(stmt)).scalars().all()

    # Load metadata (color, dates) from account_metadata table
    from sqlalchemy import text
    meta_result = await db.execute(
        text("SELECT record_id, meta_key, meta_value FROM account_metadata WHERE user_id = :uid AND table_name = 'creditos'"),
        {"uid": user_id}
    )
    all_meta: dict[str, dict] = {}
    for rid, key, value in meta_result.fetchall():
        if rid not in all_meta:
            all_meta[rid] = {}
        all_meta[rid][key] = value

    cards = []
    for c in rows:
        debt = _dec(c.balance_encrypted)
        limit = _dec(c.limit_encrypted)
        min_payment = _dec(c.min_payment_encrypted)
        usage = round((debt / limit * 100), 1) if limit else 0
        meta = all_meta.get(c.id, {})

        # Calculate days until payment
        days_until = None
        payment_date = meta.get("paymentDate")
        if payment_date:
            from datetime import date, datetime
            try:
                pd = datetime.strptime(payment_date, "%Y-%m-%d").date()
                today = date.today()
                # If payment date is in the past, assume next month
                if pd < today:
                    if pd.month == 12:
                        pd = pd.replace(year=pd.year + 1, month=1)
                    else:
                        pd = pd.replace(month=pd.month + 1)
                days_until = (pd - today).days
            except ValueError:
                pass

        cards.append({
            "id": c.id,
            "name": c.card_name,
            "card_name": c.card_name,
            "color": meta.get("color", "#2D2B6B"),
            "debt": debt,
            "balance": debt,
            "creditLimit": limit,
            "limit": limit,
            "minPayment": min_payment,
            "minimum_payment": min_payment,
            "fullPayment": debt,
            "usagePercent": usage,
            "utilization": usage,
            "available": max(limit - debt, 0),
            "cutoffDate": meta.get("cutoffDate"),
            "paymentDate": payment_date,
            "daysUntilPayment": days_until,
        })
    return cards


async def _load_deudas(db: AsyncSession, user_id: str):
    stmt = select(Deuda).where(Deuda.user_id == user_id)
    rows = (await db.execute(stmt)).scalars().all()
    deudas = []
    for d in rows:
        total = _dec(d.total_amount_encrypted)
        monthly = _dec(d.monthly_payment_encrypted)
        deudas.append({
            "id": d.id,
            "name": d.creditor_name,
            "creditorName": d.creditor_name,
            "total": total,
            "monthlyPayment": monthly,
            "interestRate": float(d.interest_rate) if d.interest_rate is not None else 0,
            "startDate": d.start_date.isoformat() if d.start_date else None,
        })
    return deudas


async def _load_afore(db: AsyncSession, user_id: str):
    stmt = select(Afore).where(Afore.user_id == user_id)
    row = (await db.execute(stmt)).scalars().first()

    # Get voluntary contribution from Afore aportacion (always, regardless of afore table row)
    voluntary = 0
    afore_aport_stmt = select(Aportacion).where(Aportacion.user_id == user_id)
    aportaciones = (await db.execute(afore_aport_stmt)).scalars().all()
    for a in aportaciones:
        if a.target_name.lower() == "afore":
            try:
                voluntary = float(encryption_service.decrypt(a.amount_encrypted))
            except Exception:
                pass
            break

    if not row:
        return {"balance": 0, "annualReturn": 0, "provider": "", "bimonthlyContribution": 0, "voluntaryContribution": voluntary}

    return {
        "balance": _dec(row.balance_encrypted),
        "annualReturn": 0,
        "provider": row.provider_name,
        "bimonthlyContribution": 0,
        "voluntaryContribution": voluntary,
    }


async def _load_gbm(db: AsyncSession, user_id: str):
    stmt = select(GbmPortfolio).where(GbmPortfolio.user_id == user_id)
    rows = (await db.execute(stmt)).scalars().all()

    # Load metadata (market type)
    from sqlalchemy import text
    meta_result = await db.execute(
        text("SELECT record_id, meta_key, meta_value FROM account_metadata WHERE user_id = :uid AND table_name = 'gbm'"),
        {"uid": user_id}
    )
    all_meta: dict[str, dict] = {}
    for rid, key, value in meta_result.fetchall():
        if rid not in all_meta:
            all_meta[rid] = {}
        all_meta[rid][key] = value

    nacional = []
    usa = []
    total_value_nac = 0.0
    total_cost_nac = 0.0
    total_value_usa = 0.0
    total_cost_usa = 0.0

    for g in rows:
        market_value = _dec(g.market_value_encrypted)
        avg_cost = _dec(g.avg_cost_encrypted)
        shares = float(g.shares) if g.shares is not None else 0
        cost_basis = avg_cost * shares
        gain_loss = round(market_value - cost_basis, 2)
        return_pct = round((gain_loss / cost_basis * 100), 2) if cost_basis > 0 else 0
        market_price = round(market_value / shares, 2) if shares > 0 else 0

        meta = all_meta.get(g.id, {})
        market_type = meta.get("market", "nacional")

        position = {
            "id": g.id,
            "ticker": g.ticker,
            "shares": shares,
            "avgCost": avg_cost,
            "marketPrice": market_price,
            "marketValue": market_value,
            "gainLoss": gain_loss,
            "returnPct": return_pct,
            "section": "Mercado de Capitales Nacional" if market_type == "nacional" else "Mercado de Capitales USA",
            "varDayPct": 0,
            "portfolioPct": 0,
        }

        if market_type == "usa":
            usa.append(position)
            total_value_usa += market_value
            total_cost_usa += cost_basis
        else:
            nacional.append(position)
            total_value_nac += market_value
            total_cost_nac += cost_basis

    # Calculate portfolio percentages
    for pos in nacional:
        pos["portfolioPct"] = round((pos["marketValue"] / total_value_nac * 100), 1) if total_value_nac > 0 else 0
    for pos in usa:
        pos["portfolioPct"] = round((pos["marketValue"] / total_value_usa * 100), 1) if total_value_usa > 0 else 0

    # Get USD/MXN exchange rate
    usd_mxn = 19.5  # fallback
    try:
        import httpx
        resp = httpx.get("https://api.frankfurter.app/latest?base=USD&symbols=MXN", timeout=5, follow_redirects=True)
        if resp.status_code == 200:
            usd_mxn = round(float(resp.json()["rates"]["MXN"]), 4)
    except Exception:
        pass

    total_value = total_value_nac + total_value_usa * usd_mxn
    total_cost = total_cost_nac + total_cost_usa * usd_mxn
    total_gain = round(total_value - total_cost, 2)
    total_return_pct = round((total_gain / total_cost * 100), 2) if total_cost > 0 else 0

    summary = {
        "nacValueMXN": round(total_value_nac, 2),
        "nacionalValueMXN": round(total_value_nac, 2),
        "usaValueUSD": round(total_value_usa, 2),
        "usaValueMXN": round(total_value_usa * usd_mxn, 2),
        "totalValueMXN": round(total_value, 2),
        "totalGainMXN": total_gain,
        "totalReturnPct": total_return_pct,
        "usdMxnRate": usd_mxn,
    }
    return nacional, usa, summary


# ---------------------------------------------------------------------------
# Update tracker helpers
# ---------------------------------------------------------------------------

from datetime import date as _date_cls, datetime as _dt_cls, timezone as _tz, timedelta as _td

# Mexico City is UTC-6 (simplified, ignoring DST)
_MX_OFFSET = _tz(_td(hours=-6))


def _mx_today() -> _date_cls:
    """Get today's date in Mexico City timezone."""
    return _dt_cls.now(_MX_OFFSET).date()


def _is_schedule_day(schedule: str) -> bool:
    """Check if today (Mexico time) matches the schedule."""
    today = _mx_today()
    if schedule == "monday":
        return today.weekday() == 0
    elif schedule == "friday":
        return today.weekday() == 4
    elif schedule == "first_of_month":
        return today.day == 1
    elif schedule == "fifteenth":
        return today.day == 15
    return False


async def _get_update_status(db: AsyncSession, user_id: str, section: str, schedule: str) -> dict:
    """Get update status for a section.
    
    For NEW users who have never updated a section, always show needsUpdate=True
    regardless of the day of the week, so they get prompted to enter their initial data.
    """
    if not user_id:
        return {"needsUpdate": False, "lastUpdate": None, "daysSinceUpdate": None}

    from sqlalchemy import text
    result = await db.execute(
        text("SELECT meta_value FROM account_metadata WHERE user_id = :uid AND table_name = 'update_tracker' AND record_id = :section AND meta_key = 'last_update'"),
        {"uid": user_id, "section": section}
    )
    row = result.fetchone()
    last_update = row[0] if row else None

    today = _mx_today()
    is_day = _is_schedule_day(schedule)

    # If user has NEVER updated this section, always show notification
    if last_update is None:
        needs_update = True
    elif is_day:
        needs_update = last_update != today.isoformat()
    else:
        needs_update = False

    days_since = None
    if last_update:
        try:
            last_date = _dt_cls.strptime(last_update, "%Y-%m-%d").date()
            days_since = (today - last_date).days
        except ValueError:
            pass

    schedule_labels = {
        "monday": "isMonday",
        "friday": "isFriday",
        "first_of_month": "isFirstOfMonth",
        "fifteenth": "isFifteenth",
    }

    return {
        "section": section,
        "lastUpdate": last_update,
        schedule_labels.get(schedule, "isMonday"): is_day,
        "needsUpdate": needs_update,
        "daysSinceUpdate": days_since,
        "isNewUser": last_update is None,
    }


async def _mark_section_updated(db: AsyncSession, user_id: str, section: str):
    """Mark a section as updated today (Mexico time)."""
    from sqlalchemy import text
    today_str = _mx_today().isoformat()
    await db.execute(
        text("""INSERT INTO account_metadata (user_id, table_name, record_id, meta_key, meta_value)
                VALUES (:uid, 'update_tracker', :section, 'last_update', :val)
                ON CONFLICT (user_id, table_name, record_id, meta_key)
                DO UPDATE SET meta_value = :val"""),
        {"uid": user_id, "section": section, "val": today_str}
    )
    await db.commit()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/dashboard")
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Aggregated financial dashboard summary."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})

    gi_records = await _load_gi_records(db, user_id)
    income = sum(r["amount"] for r in gi_records if r["amount"] > 0)
    expenses = sum(-r["amount"] for r in gi_records if r["amount"] < 0)

    ahorro = await _load_ahorro(db, user_id)
    cards = await _load_creditos(db, user_id)
    deudas = await _load_deudas(db, user_id)
    afore = await _load_afore(db, user_id)
    gbm_nac, gbm_usa, gbm_summary = await _load_gbm(db, user_id)

    total_savings = sum(a["balance"] for a in ahorro)
    total_debt = sum(c["debt"] for c in cards)
    total_limit = sum(c["creditLimit"] for c in cards)
    total_deuda = sum(d["total"] for d in deudas)
    monthly_payment = sum(d["monthlyPayment"] for d in deudas)

    return {
        "gbm": {"positions": gbm_nac + gbm_usa, "nacional": gbm_nac, "usa": gbm_usa, "summary": gbm_summary},
        "creditos": {
            "cards": cards,
            "summary": {
                "totalDebt": total_debt,
                "totalAvailable": max(total_limit - total_debt, 0),
                "totalLimit": total_limit,
            },
        },
        "inversiones": {
            "ahorro": ahorro,
            "afore": afore,
            "summary": {
                "totalSavings": total_savings,
                "totalLoans": 0,
                "total": total_savings + afore["balance"] + gbm_summary["totalValueMXN"],
            },
        },
        "gi": {
            "records": gi_records,
            "summary": {"income": income, "expenses": expenses, "balance": income - expenses},
        },
        "deudas": {"deudas": deudas, "total": total_deuda, "monthlyPayment": monthly_payment},
    }


@router.get("/subscription")
async def get_subscription(request: Request):
    """User subscription tier."""
    return {
        "tier": "free",
        "status": "active",
        "permissions": {
            "dashboard_basico": True,
            "gastos_ingresos": True,
            "cursos_gratuitos": True,
            "agente_limitado": True,
            "inversiones": True,
            "agente_ilimitado": True,
            "analisis_avanzado": True,
            "proyecciones": True,
            "soporte_prioritario": False,
        },
        "familyGroup": None,
    }


@router.get("/inversiones")
async def get_inversiones(request: Request, db: AsyncSession = Depends(get_db)):
    """Investment accounts — ahorro, prestamos, afore, summary."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    ahorro = await _load_ahorro(db, user_id)
    afore = await _load_afore(db, user_id)
    total_savings = sum(a["balance"] for a in ahorro)
    return {
        "ahorro": ahorro,
        "prestamos": [],
        "afore": afore,
        "summary": {
            "totalSavings": total_savings,
            "totalLoans": 0,
            "totalLoanInterest": 0,
            "avgLoanRate": 0,
            "total": total_savings + afore["balance"],
        },
    }


@router.get("/inversiones/update-status")
async def inversiones_update_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Check if savings data needs to be updated (Mondays)."""
    user_id = _uid(request)
    return await _get_update_status(db, user_id, "ahorro", "monday")


@router.get("/inversiones/afore/update-status")
async def afore_update_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Check if afore data needs to be updated (1st of month)."""
    user_id = _uid(request)
    return await _get_update_status(db, user_id, "afore", "first_of_month")


@router.get("/inversiones/prestamos/update-status")
async def prestamos_update_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Check if prestamos data needs to be updated (15th of month)."""
    user_id = _uid(request)
    return await _get_update_status(db, user_id, "prestamos", "fifteenth")


@router.post("/inversiones/update-balances")
async def update_balances(request: Request, db: AsyncSession = Depends(get_db)):
    """Update savings account balances by name."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body"})
    balances = body.get("balances", {})
    if not isinstance(balances, dict):
        return JSONResponse(status_code=400, content={"detail": "balances must be an object"})

    stmt = select(Ahorro).where(Ahorro.user_id == user_id)
    rows = (await db.execute(stmt)).scalars().all()

    for account in rows:
        if account.account_name in balances:
            try:
                new_balance = float(balances[account.account_name])
                if new_balance < 0 or new_balance > 999_999_999.99:
                    continue
                account.amount_encrypted = encryption_service.encrypt(str(new_balance))
            except (ValueError, TypeError):
                continue

    await db.commit()
    await _mark_section_updated(db, user_id, "ahorro")
    return {"success": True}


@router.post("/inversiones/mark-updated")
async def mark_updated(request: Request, db: AsyncSession = Depends(get_db)):
    """Mark inversiones as updated today."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False})
    await _mark_section_updated(db, user_id, "ahorro")
    return {"success": True, "updatedAt": _date_cls.today().isoformat()}


@router.post("/inversiones/afore/update-data")
async def afore_update_data(request: Request, db: AsyncSession = Depends(get_db)):
    """Update afore data."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body"})
    stmt = select(Afore).where(Afore.user_id == user_id)
    row = (await db.execute(stmt)).scalars().first()
    if row and "balance" in body:
        try:
            balance = float(body["balance"])
            if balance < 0 or balance > 999_999_999.99:
                return JSONResponse(status_code=400, content={"detail": "Invalid balance value"})
            row.balance_encrypted = encryption_service.encrypt(str(balance))
            await db.commit()
        except (ValueError, TypeError):
            return JSONResponse(status_code=400, content={"detail": "balance must be a number"})
    return {"success": True}


@router.post("/inversiones/prestamos")
async def create_prestamo(request: Request):
    """Create a loan (stub)."""
    return {"success": True, "id": "stub"}


@router.post("/inversiones/prestamos/update-data")
async def update_prestamos_data(request: Request):
    """Update loan data (stub)."""
    return {"success": True}


@router.get("/gbm/portfolio")
async def gbm_portfolio(request: Request, db: AsyncSession = Depends(get_db)):
    """GBM portfolio — nacional, usa, summary."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    nacional, usa, summary = await _load_gbm(db, user_id)
    return {"nacional": nacional, "usa": usa, "summary": summary}


@router.post("/gbm/upload")
async def gbm_upload(request: Request, db: AsyncSession = Depends(get_db)):
    """Upload GBM Excel files and update portfolio."""
    import openpyxl
    from io import BytesIO

    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})

    form = await request.form()
    nacional_file = form.get("nacional")
    usa_file = form.get("usa")

    def parse_num(value) -> float:
        if value is None or value == "-":
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        if s in ("-", "", "N/A"):
            return 0.0
        s = s.replace("$", "").replace("%", "").replace(",", "").strip()
        neg = s.startswith("-")
        if neg:
            s = s[1:]
        try:
            r = float(s)
            return -r if neg else r
        except (ValueError, TypeError):
            return 0.0

    def parse_excel(content: bytes) -> list[dict]:
        wb = openpyxl.load_workbook(BytesIO(content), read_only=True)
        ws = wb.active
        instruments = []
        for row in ws.iter_rows(values_only=True):
            if not row or row[0] is None:
                continue
            cell0 = str(row[0]).strip()
            if cell0 in ("Mercado de Capitales Nacional", "Mercado de Capitales USA",
                         "Fondos de Inversión Deuda", "Efectivo", "Liquidez",
                         "Emisora/Fondo", "App GBM Portfolio", ""):
                continue
            if cell0.startswith("EFEC.") and parse_num(row[5]) == 0:
                continue
            if cell0 == "efectivo" and parse_num(row[5]) < 1:
                continue
            try:
                ticker = cell0
                shares = parse_num(row[1])
                avg_cost = parse_num(row[2])
                market_value = parse_num(row[5])
                if market_value > 0:
                    instruments.append({
                        "ticker": ticker,
                        "shares": shares,
                        "avg_cost": avg_cost,
                        "market_value": market_value,
                    })
            except (IndexError, TypeError):
                continue
        wb.close()
        return instruments

    # Parse files
    all_positions = []
    if nacional_file and hasattr(nacional_file, "read"):
        content = await nacional_file.read()
        for pos in parse_excel(content):
            pos["market"] = "nacional"
            all_positions.append(pos)
    if usa_file and hasattr(usa_file, "read"):
        content = await usa_file.read()
        for pos in parse_excel(content):
            pos["market"] = "usa"
            all_positions.append(pos)

    if not all_positions:
        return JSONResponse(status_code=400, content={"detail": "No se encontraron posiciones en los archivos."})

    # Delete existing GBM data for this user
    from sqlalchemy import delete as sql_delete
    await db.execute(sql_delete(GbmPortfolio).where(GbmPortfolio.user_id == user_id))
    # Delete old metadata
    from sqlalchemy import text
    await db.execute(
        text("DELETE FROM account_metadata WHERE user_id = :uid AND table_name = 'gbm'"),
        {"uid": user_id}
    )

    # Insert new positions
    for pos in all_positions:
        import uuid
        record = GbmPortfolio(
            id=str(uuid.uuid4()),
            user_id=user_id,
            ticker=pos["ticker"],
            shares=pos["shares"],
            avg_cost_encrypted=encryption_service.encrypt(str(pos["avg_cost"])),
            market_value_encrypted=encryption_service.encrypt(str(pos["market_value"])),
        )
        db.add(record)
        await db.flush()
        # Save market type and extra data as metadata
        from sqlalchemy import text
        await db.execute(
            text("""INSERT INTO account_metadata (user_id, table_name, record_id, meta_key, meta_value)
                    VALUES (:uid, 'gbm', :rid, 'market', :val)
                    ON CONFLICT (user_id, table_name, record_id, meta_key) DO UPDATE SET meta_value = :val"""),
            {"uid": user_id, "rid": record.id, "val": pos["market"]}
        )

    await db.commit()
    await _mark_section_updated(db, user_id, "gbm")

    return {"success": True, "positions": len(all_positions)}


@router.get("/gbm/update-status")
async def gbm_update_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Check if GBM data needs to be updated (Fridays)."""
    user_id = _uid(request)
    return await _get_update_status(db, user_id, "gbm", "friday")


@router.get("/creditos")
async def get_creditos(request: Request, db: AsyncSession = Depends(get_db)):
    """Credit cards with summary."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    cards = await _load_creditos(db, user_id)
    total_debt = sum(c["debt"] for c in cards)
    total_limit = sum(c["creditLimit"] for c in cards)
    total_available = max(total_limit - total_debt, 0)
    usage_percent = round((total_debt / total_limit * 100), 1) if total_limit else 0
    return {
        "cards": cards,
        "items": cards,
        "summary": {
            "totalDebt": total_debt,
            "totalAvailable": total_available,
            "totalLimit": total_limit,
            "totalCredit": total_limit,
            "totalPayment": sum(c["minPayment"] for c in cards),
            "usagePercent": usage_percent,
        },
    }


@router.get("/creditos/update-status")
async def creditos_update_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Check if credit card data needs to be updated (Mondays)."""
    user_id = _uid(request)
    return await _get_update_status(db, user_id, "creditos", "monday")


@router.post("/creditos/update-card")
async def update_card(request: Request, db: AsyncSession = Depends(get_db)):
    """Update a credit card's balance, limit, payment, and dates by name."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body"})
    card_name = body.get("name")
    if not card_name or not isinstance(card_name, str):
        return JSONResponse(status_code=400, content={"detail": "name is required"})

    # Sanitize and validate card_name
    card_name = sanitize_string(card_name)[:100]
    try:
        validate_no_injection(card_name, "name")
    except ValidationError:
        return JSONResponse(status_code=400, content={"detail": "Invalid card name"})

    stmt = select(Credito).where(Credito.user_id == user_id, Credito.card_name == card_name)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return JSONResponse(status_code=404, content={"detail": "Card not found"})

    # Validate numeric fields
    def _safe_float(val, max_val=999_999_999.99):
        if val is None:
            return None
        try:
            f = float(val)
            if f < 0 or f > max_val:
                return None
            return f
        except (ValueError, TypeError):
            return None

    if "balance" in body and body["balance"] is not None:
        v = _safe_float(body["balance"])
        if v is not None:
            record.balance_encrypted = encryption_service.encrypt(str(v))
    if "limit" in body and body["limit"] is not None:
        v = _safe_float(body["limit"])
        if v is not None:
            record.limit_encrypted = encryption_service.encrypt(str(v))
    if "minPayment" in body and body["minPayment"] is not None:
        v = _safe_float(body["minPayment"])
        if v is not None:
            record.min_payment_encrypted = encryption_service.encrypt(str(v))
    if "fullPayment" in body and body["fullPayment"] is not None:
        v = _safe_float(body["fullPayment"])
        if v is not None:
            record.balance_encrypted = encryption_service.encrypt(str(v))

    await db.commit()

    # Save dates and other metadata (validate date format)
    import re as _re
    from sqlalchemy import text
    meta_fields = {}
    date_pattern = _re.compile(r"^\d{4}-\d{2}-\d{2}$")
    if "cutoffDate" in body and body["cutoffDate"]:
        val = str(body["cutoffDate"])[:10]
        if date_pattern.match(val):
            meta_fields["cutoffDate"] = val
    if "paymentDate" in body and body["paymentDate"]:
        val = str(body["paymentDate"])[:10]
        if date_pattern.match(val):
            meta_fields["paymentDate"] = val
    for key, value in meta_fields.items():
        await db.execute(
            text("""INSERT INTO account_metadata (user_id, table_name, record_id, meta_key, meta_value)
                    VALUES (:uid, 'creditos', :rid, :key, :val)
                    ON CONFLICT (user_id, table_name, record_id, meta_key)
                    DO UPDATE SET meta_value = :val"""),
            {"uid": user_id, "rid": record.id, "key": key, "val": str(value)}
        )
    await db.commit()

    # Invalidate server-side cache for creditos
    from backend.services.cache import cache as server_cache
    server_cache.invalidate(user_id, "creditos")

    return {"success": True}


@router.get("/deudas")
async def get_deudas(request: Request, db: AsyncSession = Depends(get_db)):
    """Debts."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    deudas = await _load_deudas(db, user_id)
    total = sum(d["total"] for d in deudas)
    monthly = sum(d["monthlyPayment"] for d in deudas)
    return {"deudas": deudas, "total": total, "monthlyPayment": monthly}


@router.get("/gi/records")
async def get_gi_records(request: Request, db: AsyncSession = Depends(get_db)):
    """Income/expense records."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    records = await _load_gi_records(db, user_id)
    income = sum(r["amount"] for r in records if r["amount"] > 0)
    expenses = sum(-r["amount"] for r in records if r["amount"] < 0)
    return {"records": records, "summary": {"income": income, "expenses": expenses, "balance": income - expenses}}


@router.get("/gi/categories")
async def get_gi_categories(request: Request, db: AsyncSession = Depends(get_db)):
    """Income/expense categories — returns array of {id, name, system}. Auto-creates defaults."""
    user_id = _uid(request)
    if not user_id:
        return []

    DEFAULT_CATEGORIES = ["Sueldo", "Comida", "Transporte"]

    stmt = select(Category).where(Category.user_id == user_id)
    cats = (await db.execute(stmt)).scalars().all()

    # Auto-create default system categories if missing
    existing_names = {c.name.lower() for c in cats}
    created = False
    for default_name in DEFAULT_CATEGORIES:
        if default_name.lower() not in existing_names:
            import uuid as _uuid
            from sqlalchemy import text
            # Ensure user exists
            await db.execute(text("INSERT INTO users (user_id, email) VALUES (:uid, '') ON CONFLICT (user_id) DO NOTHING"), {"uid": user_id})
            new_cat = Category(
                id=str(_uuid.uuid4()),
                user_id=user_id,
                name=default_name,
                is_system=True,
            )
            db.add(new_cat)
            created = True

    if created:
        await db.commit()
        cats = (await db.execute(stmt)).scalars().all()

    return [{"id": c.id, "name": c.name, "system": c.is_system} for c in cats]


@router.post("/gi/records")
async def create_gi_record(request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new gasto/ingreso record persisted to the DB."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})

    from datetime import date as date_cls
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body"})

    # Validate & sanitize category name
    category_name = body.get("category", "")
    if not isinstance(category_name, str):
        category_name = ""
    category_name = sanitize_string(category_name)[:50]
    try:
        validate_no_injection(category_name, "category")
    except ValidationError:
        return JSONResponse(status_code=400, content={"detail": "Invalid category name"})

    cat_stmt = select(Category).where(Category.user_id == user_id, Category.name == category_name)
    category = (await db.execute(cat_stmt)).scalars().first()
    if not category:
        category = Category(user_id=user_id, name=category_name or "Sin categoría", is_system=False)
        db.add(category)
        await db.flush()

    raw_type = body.get("type", "gasto")
    entry_type = "income" if raw_type in ("ingreso", "income") else "expense"

    # Validate amount
    try:
        amount = abs(float(body.get("amount", 0)))
        if amount > 999_999_999.99:
            return JSONResponse(status_code=400, content={"detail": "Amount exceeds maximum"})
    except (ValueError, TypeError):
        return JSONResponse(status_code=400, content={"detail": "Invalid amount"})

    # Validate & sanitize description
    description = body.get("description", "")
    if not isinstance(description, str):
        description = ""
    description = sanitize_string(description)[:500]

    entry_date = body.get("date")
    try:
        parsed_date = date_cls.fromisoformat(entry_date) if entry_date else date_cls.today()
    except ValueError:
        parsed_date = date_cls.today()

    record = GastoIngreso(
        user_id=user_id,
        type=entry_type,
        amount_encrypted=encryption_service.encrypt(str(amount)),
        description_encrypted=encryption_service.encrypt(description),
        category_id=category.id,
        entry_date=parsed_date,
    )
    db.add(record)
    await db.commit()
    return JSONResponse(status_code=201, content={"success": True, "data": {"id": record.id}})


@router.put("/gi/records/{record_id}")
async def update_gi_record(record_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Update a gasto/ingreso record."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body"})
    stmt = select(GastoIngreso).where(GastoIngreso.id == record_id, GastoIngreso.user_id == user_id)
    record = (await db.execute(stmt)).scalars().first()
    if not record:
        return JSONResponse(status_code=404, content={"success": False, "error": "not found"})

    if "amount" in body:
        try:
            amount = abs(float(body["amount"]))
            if amount > 999_999_999.99:
                return JSONResponse(status_code=400, content={"detail": "Amount exceeds maximum"})
            record.amount_encrypted = encryption_service.encrypt(str(amount))
        except (ValueError, TypeError):
            return JSONResponse(status_code=400, content={"detail": "Invalid amount"})
    if "description" in body:
        desc = sanitize_string(str(body["description"]))[:500]
        record.description_encrypted = encryption_service.encrypt(desc)
    if "type" in body:
        record.type = "income" if body["type"] in ("ingreso", "income") else "expense"
    if body.get("category"):
        cat_name = sanitize_string(str(body["category"]))[:50]
        cat_stmt = select(Category).where(Category.user_id == user_id, Category.name == cat_name)
        category = (await db.execute(cat_stmt)).scalars().first()
        if category:
            record.category_id = category.id
    await db.commit()
    return {"success": True, "data": {"id": record_id}}


@router.delete("/gi/records/{record_id}")
async def delete_gi_record(record_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Delete a gasto/ingreso record."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    stmt = select(GastoIngreso).where(GastoIngreso.id == record_id, GastoIngreso.user_id == user_id)
    record = (await db.execute(stmt)).scalars().first()
    if record:
        await db.delete(record)
        await db.commit()
    return {"success": True, "message": "Record deleted"}


@router.get("/patrimonio")
async def get_patrimonio(request: Request, db: AsyncSession = Depends(get_db)):
    """Net worth / patrimonio."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False, "error": "unauthorized"})
    ahorro = await _load_ahorro(db, user_id)
    afore = await _load_afore(db, user_id)
    cards = await _load_creditos(db, user_id)
    deudas = await _load_deudas(db, user_id)
    _, _, gbm_summary = await _load_gbm(db, user_id)

    assets = sum(a["balance"] for a in ahorro) + afore["balance"] + gbm_summary["totalValueMXN"]
    liabilities = sum(c["debt"] for c in cards) + sum(d["total"] for d in deudas)
    return {
        "history": [],
        "current": {
            "assets": round(assets, 2),
            "liabilities": round(liabilities, 2),
            "net_worth": round(assets - liabilities, 2),
        },
    }


@router.get("/aportaciones")
async def get_aportaciones(request: Request, db: AsyncSession = Depends(get_db)):
    """Get aportaciones with weekly/biweekly/monthly periods for the given month."""
    from datetime import date, timedelta
    import uuid as uuid_mod

    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"categories": []})

    # Get year/month from query params
    from starlette.requests import Request as _Req
    params = request.query_params
    today = _date_cls.today()
    year = int(params.get("year", today.year))
    month = int(params.get("month", today.month))

    # Load aportaciones config
    stmt = select(Aportacion).where(Aportacion.user_id == user_id)
    rows = (await db.execute(stmt)).scalars().all()

    # Auto-create Afore if missing
    has_afore = any(a.target_name.lower() == "afore" for a in rows)
    if not has_afore:
        from backend.models.database import async_session as _async_session
        async with _async_session() as new_db:
            import uuid as _uuid
            # Ensure user exists in users table (for FK constraint)
            from sqlalchemy import text as _text
            await new_db.execute(
                _text("INSERT INTO users (user_id, email) VALUES (:uid, '') ON CONFLICT (user_id) DO NOTHING"),
                {"uid": user_id}
            )
            await new_db.commit()

            afore_record = Aportacion(
                id=str(_uuid.uuid4()),
                user_id=user_id,
                amount_encrypted=encryption_service.encrypt("0"),
                frequency="semanal",
                target_name="Afore",
                start_date=_date_cls.today(),
            )
            new_db.add(afore_record)
            await new_db.commit()
        # Re-query
        rows = (await db.execute(stmt)).scalars().all()

    from sqlalchemy import text
    meta_result = await db.execute(
        text("SELECT record_id, meta_key, meta_value FROM account_metadata WHERE user_id = :uid AND table_name = 'aportaciones'"),
        {"uid": user_id}
    )
    all_meta: dict[str, dict] = {}
    for rid, key, value in meta_result.fetchall():
        if rid not in all_meta:
            all_meta[rid] = {}
        all_meta[rid][key] = value

    # Load saved period statuses
    status_result = await db.execute(
        text("SELECT record_id, meta_value FROM account_metadata WHERE user_id = :uid AND table_name = 'aportacion_status' AND meta_key = 'status'"),
        {"uid": user_id}
    )
    saved_statuses = {row[0]: row[1] for row in status_result.fetchall()}

    # Generate periods for each category
    categories = []
    for a in rows:
        try:
            amount = float(encryption_service.decrypt(a.amount_encrypted))
        except Exception:
            amount = 0
        meta = all_meta.get(a.id, {})

        # Generate weeks/periods for this month
        weeks = []
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        if a.frequency == "semanal":
            # Generate weekly periods (Mon-Sun)
            current = first_day
            # Go to first Monday
            while current.weekday() != 0:
                current -= timedelta(days=1)
            while current <= last_day:
                week_start = current
                week_end = current + timedelta(days=6)
                if week_end >= first_day and week_start <= last_day:
                    wid = str(uuid_mod.uuid5(uuid_mod.NAMESPACE_DNS, f"{a.id}-{week_start}"))
                    weeks.append({
                        "id": wid,
                        "weekStart": week_start.isoformat(),
                        "weekEnd": week_end.isoformat(),
                        "status": saved_statuses.get(wid, "pendiente"),
                    })
                current += timedelta(days=7)
        elif a.frequency == "quincenal":
            wid1 = str(uuid_mod.uuid5(uuid_mod.NAMESPACE_DNS, f"{a.id}-{year}-{month}-1"))
            wid2 = str(uuid_mod.uuid5(uuid_mod.NAMESPACE_DNS, f"{a.id}-{year}-{month}-2"))
            weeks.append({
                "id": wid1,
                "weekStart": first_day.isoformat(),
                "weekEnd": date(year, month, 15).isoformat(),
                "status": saved_statuses.get(wid1, "pendiente"),
            })
            weeks.append({
                "id": wid2,
                "weekStart": date(year, month, 16).isoformat(),
                "weekEnd": last_day.isoformat(),
                "status": saved_statuses.get(wid2, "pendiente"),
            })
        elif a.frequency == "mensual":
            wid = str(uuid_mod.uuid5(uuid_mod.NAMESPACE_DNS, f"{a.id}-{year}-{month}"))
            weeks.append({
                "id": wid,
                "weekStart": first_day.isoformat(),
                "weekEnd": last_day.isoformat(),
                "status": saved_statuses.get(wid, "pendiente"),
            })

        categories.append({
            "category": a.target_name,
            "person": meta.get("person", ""),
            "amount": amount,
            "color": meta.get("color", "#1da1f2"),
            "frequency": a.frequency,
            "weeks": weeks,
        })

    return {"categories": categories}


@router.post("/aportaciones/update-status")
async def update_aportacion_status(request: Request, db: AsyncSession = Depends(get_db)):
    """Update the status of a specific aportacion period."""
    user_id = _uid(request)
    if not user_id:
        return JSONResponse(status_code=401, content={"success": False})
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body"})
    period_id = body.get("id")
    status = body.get("status", "pendiente")

    # Validate inputs
    if not period_id or not isinstance(period_id, str) or len(period_id) > 100:
        return JSONResponse(status_code=400, content={"detail": "Invalid period id"})
    valid_statuses = ("pendiente", "completado", "parcial")
    if status not in valid_statuses:
        status = "pendiente"

    # Save status in metadata
    from sqlalchemy import text
    await db.execute(
        text("""INSERT INTO account_metadata (user_id, table_name, record_id, meta_key, meta_value)
                VALUES (:uid, 'aportacion_status', :rid, 'status', :val)
                ON CONFLICT (user_id, table_name, record_id, meta_key) DO UPDATE SET meta_value = :val"""),
        {"uid": user_id, "rid": period_id, "val": status}
    )
    await db.commit()
    return {"success": True}
