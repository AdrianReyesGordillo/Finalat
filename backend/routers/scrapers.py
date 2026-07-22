"""Scraper routes — Manual sync endpoints for financial instrument rates.

Provides:
  POST /api/scrapers/sync-all     — sync all scraper sources
  POST /api/scrapers/sync-banxico — sync CETES from Banxico API
  POST /api/scrapers/sync-nu      — sync Nu rates
  POST /api/scrapers/sync-stori   — sync Stori rates
  GET  /api/scrapers/status       — cache status for all scrapers
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.instruments import Instrument
from backend.services.banxico import (
    get_tasas_cetes,
    get_tasa_objetivo,
    get_historico_cetes,
    BanxicoAPIError,
    clear_cache as clear_banxico_cache,
)
from backend.services.nu import fetch_nu_rates, NuScrapingError, get_cache_status as nu_cache_status
from backend.services.stori import fetch_stori_rates, StoriScrapingError, get_cache_status as stori_cache_status
from backend.services.scrapers.uala import fetch_uala_rates, get_cache_status as uala_cache_status
from backend.services.scrapers.mercadopago import fetch_mercadopago_rates, get_cache_status as mp_cache_status
from backend.services.scrapers.klar import fetch_klar_rates, get_cache_status as klar_cache_status
from backend.services.scrapers.finsus import fetch_finsus_rates, get_cache_status as finsus_cache_status
from backend.services.scrapers.didi import fetch_didi_rates, get_cache_status as didi_cache_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/scrapers", tags=["scrapers"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _sync_rates(
    db: AsyncSession, product_map: dict, rates: list[dict], institution: str
) -> dict:
    """Sync scraped rates to DB. Returns summary of updates."""
    updated = []
    now = datetime.now(timezone.utc)

    for rate_info in rates:
        name = product_map.get(rate_info["product"])
        if not name:
            continue

        stmt = select(Instrument).where(
            Instrument.name == name,
            Instrument.institution == institution,
        )
        result = await db.execute(stmt)
        inst = result.scalar_one_or_none()

        if inst:
            inst.annual_rate = rate_info["rate"]
            inst.last_fetched_at = now
            inst.last_fetch_status = "success"
            updated.append({"name": name, "new_rate": rate_info["rate"]})

    await db.commit()
    return {"updated": updated, "count": len(updated)}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/sync-all")
async def sync_all_scrapers(db: AsyncSession = Depends(get_db)):
    """Sync all scraper sources to the database."""
    results = {}

    # Ualá
    try:
        data = await fetch_uala_rates()
        r = await _sync_rates(db, {
            "Ualá Cuenta (Tasa Base)": "Ualá Cuenta",
            "Ualá Cuenta (Tasa Plus)": "Ualá Cuenta Plus",
            "Ualá Cuenta (Tasa Plus Alta)": "Ualá Cuenta Plus Alta",
            "Ualá Reserva a Plazo": "Ualá Reserva a Plazo",
        }, data["rates"], "Ualá")
        results["uala"] = {"ok": True, **r}
    except Exception as e:
        results["uala"] = {"ok": False, "error": str(e)}

    # Nu
    try:
        data = await fetch_nu_rates()
        r = await _sync_rates(db, {
            "Cajita Turbo": "Nu Cuenta",
            "Cajitas Nu": "Nu Cajitas",
            "Ahorro Congelado 7 días": "Nu Congelado 7 días",
            "Ahorro Congelado 28 días": "Nu Congelado 28 días",
            "Ahorro Congelado 90 días": "Nu Congelado 90 días",
            "Ahorro Congelado 180 días": "Nu Congelado 180 días",
        }, data["rates"], "Nu México")
        results["nu"] = {"ok": True, **r}
    except Exception as e:
        results["nu"] = {"ok": False, "error": str(e)}

    # Mercado Pago
    try:
        data = await fetch_mercadopago_rates()
        r = await _sync_rates(db, {
            "Mercado Pago Cuenta": "Mercado Pago",
        }, data["rates"], "Mercado Libre")
        results["mercadopago"] = {"ok": True, **r}
    except Exception as e:
        results["mercadopago"] = {"ok": False, "error": str(e)}

    # Klar
    try:
        data = await fetch_klar_rates()
        r = await _sync_rates(db, {
            "Klar Cuenta": "Klar Cuenta",
            "Klar Inversión (máxima)": "Klar Inversión",
        }, data["rates"], "Klar")
        results["klar"] = {"ok": True, **r}
    except Exception as e:
        results["klar"] = {"ok": False, "error": str(e)}

    # Finsus
    try:
        data = await fetch_finsus_rates()
        r = await _sync_rates(db, {
            "Finsus Tasa Especial": "Finsus Tasa Especial",
            "Finsus Inversión": "Finsus Inversión",
        }, data["rates"], "Finsus")
        results["finsus"] = {"ok": True, **r}
    except Exception as e:
        results["finsus"] = {"ok": False, "error": str(e)}

    # Stori
    try:
        data = await fetch_stori_rates()
        r = await _sync_rates(db, {
            "Stori Apartados": "Stori Apartados",
            "Stori Inversión+ 30 días": "Stori Inversión+ 30 días",
            "Stori Inversión+ 90 días": "Stori Inversión+ 90 días",
            "Stori Inversión+ 180 días": "Stori Inversión+ 180 días",
        }, data["rates"], "Stori")
        results["stori"] = {"ok": True, **r}
    except Exception as e:
        results["stori"] = {"ok": False, "error": str(e)}

    # Didi
    try:
        data = await fetch_didi_rates()
        r = await _sync_rates(db, {
            "Didi Cuenta": "Didi Cuenta",
        }, data["rates"], "Didi (99 Pay)")
        results["didi"] = {"ok": True, **r}
    except Exception as e:
        results["didi"] = {"ok": False, "error": str(e)}

    return {"message": "Sync completed", "results": results}


@router.post("/sync-banxico")
async def sync_banxico(db: AsyncSession = Depends(get_db)):
    """Sync CETES rates from Banxico API."""
    try:
        clear_banxico_cache()
        tasas = await get_tasas_cetes()
    except BanxicoAPIError as e:
        return {"ok": False, "error": e.message, "seconds_to_reset": e.seconds_to_reset}

    updated = []
    now = datetime.now(timezone.utc)
    for tasa in tasas:
        stmt = select(Instrument).where(
            Instrument.instrument_type == "cetes",
            Instrument.term_days == tasa["term_days"],
        )
        result = await db.execute(stmt)
        inst = result.scalar_one_or_none()

        if inst:
            inst.annual_rate = tasa["rate"]
            inst.last_fetched_at = now
            inst.last_fetch_status = "success"
            updated.append({"name": inst.name, "new_rate": tasa["rate"], "date": tasa["date"]})

    await db.commit()
    return {"ok": True, "message": f"Updated {len(updated)} CETES", "updated": updated}


@router.get("/banxico/tasas-cetes")
async def get_cetes_rates():
    """Get current CETES rates from Banxico (cached)."""
    try:
        tasas = await get_tasas_cetes()
        return {"tasas": tasas, "source": "Banco de México (SIE)"}
    except BanxicoAPIError as e:
        return {"error": e.message, "seconds_to_reset": e.seconds_to_reset}


@router.get("/banxico/tasa-objetivo")
async def get_target_rate():
    """Get Banxico target rate."""
    try:
        tasa = await get_tasa_objetivo()
        return {"tasa_objetivo": tasa, "source": "Banco de México (SIE)"}
    except BanxicoAPIError as e:
        return {"error": e.message}


@router.get("/status")
async def scrapers_status():
    """Cache status for all scrapers."""
    return {
        "uala": uala_cache_status(),
        "nu": nu_cache_status(),
        "stori": stori_cache_status(),
        "mercadopago": mp_cache_status(),
        "klar": klar_cache_status(),
        "finsus": finsus_cache_status(),
        "didi": didi_cache_status(),
    }
