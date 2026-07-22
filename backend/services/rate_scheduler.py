"""Rate Scheduler — Periodic fetching of financial instrument rates.

Scheduler configuration (Mexico City timezone):
─────────────────────────────────────────────────────
DAILY (02:00-02:30 AM):
  02:00 AM - Ualá (vigencia-based cache)
  02:15 AM - Nu (vigencia-based cache)
  02:30 AM - CETES/Banxico (API oficial)

WEEKLY (Monday 02:45-03:45 AM):
  02:45 AM - Stori
  03:00 AM - Mercado Pago
  03:15 AM - Klar
  03:30 AM - Finsus
  03:45 AM - Didi
─────────────────────────────────────────────────────

Each task has up to 4 retries with ~3.3 min between attempts (fits in 15 min window).
"""

import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import async_session
from backend.models.instruments import Instrument
from backend.services.banxico import get_tasas_cetes, clear_cache as clear_banxico_cache
from backend.services.nu import fetch_nu_rates, clear_cache as clear_nu_cache
from backend.services.stori import fetch_stori_rates, clear_cache as clear_stori_cache
from backend.services.scrapers.uala import fetch_uala_rates, clear_cache as clear_uala_cache
from backend.services.scrapers.mercadopago import fetch_mercadopago_rates, clear_cache as clear_mp_cache
from backend.services.scrapers.klar import fetch_klar_rates, clear_cache as clear_klar_cache
from backend.services.scrapers.finsus import fetch_finsus_rates, clear_cache as clear_finsus_cache
from backend.services.scrapers.didi import fetch_didi_rates, clear_cache as clear_didi_cache

logger = logging.getLogger(__name__)

try:
    from zoneinfo import ZoneInfo
    MEXICO_TZ = ZoneInfo("America/Mexico_City")
except ImportError:
    import pytz  # type: ignore
    MEXICO_TZ = pytz.timezone("America/Mexico_City")

# Retry config
MAX_RETRIES = 4
RETRY_DELAY_SECONDS = 200  # ~3.3 min


# ---------------------------------------------------------------------------
# DB sync helper
# ---------------------------------------------------------------------------

async def _sync_rates_to_db(product_map: dict, rates: list[dict], institution: str) -> None:
    """Update instrument rates in the database from scraped data."""
    async with async_session() as db:
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

        await db.commit()


async def _sync_cetes_to_db(tasas: list[dict]) -> None:
    """Update CETES rates in the database from Banxico data."""
    async with async_session() as db:
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

        await db.commit()


# ---------------------------------------------------------------------------
# Retry wrapper
# ---------------------------------------------------------------------------

async def _run_with_retry(name: str, task_fn, max_retries=MAX_RETRIES, delay=RETRY_DELAY_SECONDS):
    """Execute a task with retries."""
    for attempt in range(1, max_retries + 1):
        try:
            await task_fn()
            return
        except Exception as e:
            if attempt < max_retries:
                logger.warning(
                    "[Scheduler] %s: attempt %d/%d failed (%s). Retrying in %ds...",
                    name, attempt, max_retries, str(e), delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "[Scheduler] %s: FAILED after %d attempts. Last error: %s",
                    name, max_retries, str(e),
                )


# ---------------------------------------------------------------------------
# Individual fetch tasks
# ---------------------------------------------------------------------------

async def _fetch_cetes():
    clear_banxico_cache()
    tasas = await get_tasas_cetes()
    await _sync_cetes_to_db(tasas)
    logger.info("[Scheduler] CETES updated: %d rates", len(tasas))


async def _fetch_nu():
    clear_nu_cache()
    data = await fetch_nu_rates()
    await _sync_rates_to_db(
        {
            "Cajita Turbo": "Nu Cuenta",
            "Cajitas Nu": "Nu Cajitas",
            "Ahorro Congelado 7 días": "Nu Congelado 7 días",
            "Ahorro Congelado 28 días": "Nu Congelado 28 días",
            "Ahorro Congelado 90 días": "Nu Congelado 90 días",
            "Ahorro Congelado 180 días": "Nu Congelado 180 días",
        },
        data["rates"],
        "Nu México",
    )
    logger.info("[Scheduler] Nu updated. Vigencia: %s", data.get("vigencia"))


async def _fetch_uala():
    clear_uala_cache()
    data = await fetch_uala_rates()
    await _sync_rates_to_db(
        {
            "Ualá Cuenta (Tasa Base)": "Ualá Cuenta",
            "Ualá Cuenta (Tasa Plus)": "Ualá Cuenta Plus",
            "Ualá Cuenta (Tasa Plus Alta)": "Ualá Cuenta Plus Alta",
            "Ualá Reserva a Plazo": "Ualá Reserva a Plazo",
        },
        data["rates"],
        "Ualá",
    )
    logger.info("[Scheduler] Ualá updated. Vigencia: %s", data.get("vigencia"))


async def _fetch_stori():
    clear_stori_cache()
    data = await fetch_stori_rates()
    await _sync_rates_to_db(
        {
            "Stori Apartados": "Stori Apartados",
            "Stori Inversión+ 30 días": "Stori Inversión+ 30 días",
            "Stori Inversión+ 90 días": "Stori Inversión+ 90 días",
            "Stori Inversión+ 180 días": "Stori Inversión+ 180 días",
        },
        data["rates"],
        "Stori",
    )
    logger.info("[Scheduler] Stori updated. %d products.", len(data["rates"]))


async def _fetch_mercadopago():
    clear_mp_cache()
    data = await fetch_mercadopago_rates()
    await _sync_rates_to_db(
        {"Mercado Pago Cuenta": "Mercado Pago"},
        data["rates"],
        "Mercado Libre",
    )
    logger.info("[Scheduler] Mercado Pago updated.")


async def _fetch_klar():
    clear_klar_cache()
    data = await fetch_klar_rates()
    await _sync_rates_to_db(
        {
            "Klar Cuenta": "Klar Cuenta",
            "Klar Inversión (máxima)": "Klar Inversión",
        },
        data["rates"],
        "Klar",
    )
    logger.info("[Scheduler] Klar updated. Vigencia: %s", data.get("vigencia"))


async def _fetch_finsus():
    clear_finsus_cache()
    data = await fetch_finsus_rates()
    await _sync_rates_to_db(
        {
            "Finsus Tasa Especial": "Finsus Tasa Especial",
            "Finsus Inversión": "Finsus Inversión",
        },
        data["rates"],
        "Finsus",
    )
    logger.info("[Scheduler] Finsus updated. %d products.", len(data["rates"]))


async def _fetch_didi():
    clear_didi_cache()
    data = await fetch_didi_rates()
    await _sync_rates_to_db(
        {"Didi Cuenta": "Didi Cuenta"},
        data["rates"],
        "Didi (99 Pay)",
    )
    logger.info("[Scheduler] Didi updated.")


# ---------------------------------------------------------------------------
# Scheduled wrappers (with retry)
# ---------------------------------------------------------------------------

async def scheduled_fetch_uala():
    await _run_with_retry("Ualá", _fetch_uala)

async def scheduled_fetch_nu():
    await _run_with_retry("Nu", _fetch_nu)

async def scheduled_fetch_cetes():
    await _run_with_retry("CETES", _fetch_cetes)

async def scheduled_fetch_stori():
    await _run_with_retry("Stori", _fetch_stori)

async def scheduled_fetch_mercadopago():
    await _run_with_retry("Mercado Pago", _fetch_mercadopago)

async def scheduled_fetch_klar():
    await _run_with_retry("Klar", _fetch_klar)

async def scheduled_fetch_finsus():
    await _run_with_retry("Finsus", _fetch_finsus)

async def scheduled_fetch_didi():
    await _run_with_retry("Didi", _fetch_didi)


# ---------------------------------------------------------------------------
# Scheduler setup
# ---------------------------------------------------------------------------

scheduler = AsyncIOScheduler()


def setup_scheduler() -> None:
    """Register all cron jobs on the scheduler instance."""

    # DAILY tasks (02:00 - 02:30 AM Mexico City)
    scheduler.add_job(
        scheduled_fetch_uala,
        trigger=CronTrigger(hour=2, minute=0, timezone=MEXICO_TZ),
        id="fetch_uala_daily",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_fetch_nu,
        trigger=CronTrigger(hour=2, minute=15, timezone=MEXICO_TZ),
        id="fetch_nu_daily",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_fetch_cetes,
        trigger=CronTrigger(hour=2, minute=30, timezone=MEXICO_TZ),
        id="fetch_cetes_daily",
        replace_existing=True,
    )

    # WEEKLY tasks (Monday 02:45 - 03:45 AM Mexico City)
    scheduler.add_job(
        scheduled_fetch_stori,
        trigger=CronTrigger(day_of_week="mon", hour=2, minute=45, timezone=MEXICO_TZ),
        id="fetch_stori_weekly",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_fetch_mercadopago,
        trigger=CronTrigger(day_of_week="mon", hour=3, minute=0, timezone=MEXICO_TZ),
        id="fetch_mercadopago_weekly",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_fetch_klar,
        trigger=CronTrigger(day_of_week="mon", hour=3, minute=15, timezone=MEXICO_TZ),
        id="fetch_klar_weekly",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_fetch_finsus,
        trigger=CronTrigger(day_of_week="mon", hour=3, minute=30, timezone=MEXICO_TZ),
        id="fetch_finsus_weekly",
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_fetch_didi,
        trigger=CronTrigger(day_of_week="mon", hour=3, minute=45, timezone=MEXICO_TZ),
        id="fetch_didi_weekly",
        replace_existing=True,
    )


async def run_initial_sync() -> None:
    """Run all scrapers once at startup (single attempt, no retry)."""
    tasks = [
        ("Ualá", _fetch_uala),
        ("Nu", _fetch_nu),
        ("CETES", _fetch_cetes),
        ("Stori", _fetch_stori),
        ("Mercado Pago", _fetch_mercadopago),
        ("Klar", _fetch_klar),
        ("Finsus", _fetch_finsus),
        ("Didi", _fetch_didi),
    ]

    for name, task_fn in tasks:
        try:
            await task_fn()
        except Exception as e:
            logger.warning("[Startup] %s failed: %s (will use seed data)", name, str(e))
        await asyncio.sleep(2)  # Be polite between requests
