"""Rate Scraper service — fetches and stores current instrument rates.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.6
(Task 6.1)

This module implements a rate scraping architecture that:
- Fetches current annual rates for Mexican financial instruments
- Supports tiered rate structures (e.g., different rates per amount range)
- Uses exponential backoff retry (1s, 2s, 4s — max 3 attempts)
- On failure: retains previous rates, marks last_fetch_status = "error"
- On success: updates rate data, sets last_fetch_status = "success"

For this implementation, mock/stub data sources simulate the scraping logic
since actual URLs may change. The architecture supports real scraping later
by replacing the fetch functions with real HTTP calls.
"""

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.instruments import Instrument

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data Source Definitions
# ---------------------------------------------------------------------------

# Each source defines the instruments it provides along with their static
# metadata. The `fetch_fn` for each source simulates fetching current rates.
# To switch to real scraping, replace the mock functions with actual HTTP calls.

INSTRUMENT_SOURCES: list[dict[str, Any]] = [
    {
        "name": "Nu México",
        "source_type": "sofipo",
        "term": "liquid",
        "risk_level": "low",
        "liquidity_tier": "immediate",
        "min_investment": Decimal("0.01"),
        "max_investment": None,
        "tiered_rates": [
            {"min_amount": 0, "max_amount": 50000, "rate": 15.5},
            {"min_amount": 50000, "max_amount": 200000, "rate": 14.5},
            {"min_amount": 200000, "max_amount": None, "rate": 13.0},
        ],
        "annual_rate": Decimal("15.50"),  # headline rate (top tier)
    },
    {
        "name": "Ualá",
        "source_type": "sofipo",
        "term": "liquid",
        "risk_level": "low",
        "liquidity_tier": "immediate",
        "min_investment": Decimal("0.01"),
        "max_investment": None,
        "tiered_rates": None,
        "annual_rate": Decimal("15.00"),
    },
    {
        "name": "CETES 28",
        "source_type": "cetes",
        "term": "28",
        "risk_level": "low",
        "liquidity_tier": "28-day",
        "min_investment": Decimal("100.00"),
        "max_investment": None,
        "tiered_rates": None,
        "annual_rate": Decimal("11.00"),
    },
    {
        "name": "CETES 91",
        "source_type": "cetes",
        "term": "91",
        "risk_level": "low",
        "liquidity_tier": "custom",
        "min_investment": Decimal("100.00"),
        "max_investment": None,
        "tiered_rates": None,
        "annual_rate": Decimal("11.05"),
    },
    {
        "name": "CETES 182",
        "source_type": "cetes",
        "term": "182",
        "risk_level": "low",
        "liquidity_tier": "custom",
        "min_investment": Decimal("100.00"),
        "max_investment": None,
        "tiered_rates": None,
        "annual_rate": Decimal("10.90"),
    },
    {
        "name": "CETES 364",
        "source_type": "cetes",
        "term": "364",
        "risk_level": "low",
        "liquidity_tier": "custom",
        "min_investment": Decimal("100.00"),
        "max_investment": None,
        "tiered_rates": None,
        "annual_rate": Decimal("10.50"),
    },
    {
        "name": "Stori",
        "source_type": "sofipo",
        "term": "liquid",
        "risk_level": "low",
        "liquidity_tier": "immediate",
        "min_investment": Decimal("0.01"),
        "max_investment": None,
        "tiered_rates": None,
        "annual_rate": Decimal("15.00"),
    },
    {
        "name": "Mercado Pago",
        "source_type": "sofipo",
        "term": "liquid",
        "risk_level": "low",
        "liquidity_tier": "immediate",
        "min_investment": Decimal("0.01"),
        "max_investment": None,
        "tiered_rates": None,
        "annual_rate": Decimal("14.50"),
    },
    {
        "name": "Klar",
        "source_type": "sofipo",
        "term": "liquid",
        "risk_level": "low",
        "liquidity_tier": "immediate",
        "min_investment": Decimal("0.01"),
        "max_investment": None,
        "tiered_rates": None,
        "annual_rate": Decimal("15.00"),
    },
    {
        "name": "Finsus",
        "source_type": "sofipo",
        "term": "liquid",
        "risk_level": "low",
        "liquidity_tier": "1-day",
        "min_investment": Decimal("1.00"),
        "max_investment": Decimal("2000000.00"),
        "tiered_rates": [
            {"min_amount": 1, "max_amount": 50000, "rate": 15.32},
            {"min_amount": 50000, "max_amount": 500000, "rate": 15.04},
            {"min_amount": 500000, "max_amount": 2000000, "rate": 14.72},
        ],
        "annual_rate": Decimal("15.32"),
    },
    {
        "name": "Didi",
        "source_type": "sofipo",
        "term": "liquid",
        "risk_level": "low",
        "liquidity_tier": "immediate",
        "min_investment": Decimal("0.01"),
        "max_investment": None,
        "tiered_rates": None,
        "annual_rate": Decimal("15.00"),
    },
]


# ---------------------------------------------------------------------------
# Mock Fetch Functions (simulate real HTTP scraping)
# ---------------------------------------------------------------------------


async def _fetch_cetes_rates(client: httpx.AsyncClient) -> dict[str, Decimal]:
    """Simulate fetching CETES rates from Banxico.

    In production, this would scrape or call the Banxico API for current
    government bond yields at various terms.

    Returns:
        Dict mapping instrument name to current annual rate.
    """
    # Simulate network latency
    await asyncio.sleep(0.1)

    # Mock response — in production, parse from Banxico API/website
    return {
        "CETES 28": Decimal("11.00"),
        "CETES 91": Decimal("11.05"),
        "CETES 182": Decimal("10.90"),
        "CETES 364": Decimal("10.50"),
    }


async def _fetch_sofipo_rates(client: httpx.AsyncClient) -> dict[str, dict[str, Any]]:
    """Simulate fetching rates from Sofipo/fintech providers.

    In production, this would scrape public pages of Nu, Ualá, Stori, etc.

    Returns:
        Dict mapping instrument name to rate data including tiered_rates if applicable.
    """
    # Simulate network latency
    await asyncio.sleep(0.1)

    # Mock response — in production, scrape from provider websites
    return {
        "Nu México": {
            "annual_rate": Decimal("15.50"),
            "tiered_rates": [
                {"min_amount": 0, "max_amount": 50000, "rate": 15.5},
                {"min_amount": 50000, "max_amount": 200000, "rate": 14.5},
                {"min_amount": 200000, "max_amount": None, "rate": 13.0},
            ],
        },
        "Ualá": {"annual_rate": Decimal("15.00"), "tiered_rates": None},
        "Stori": {"annual_rate": Decimal("15.00"), "tiered_rates": None},
        "Mercado Pago": {"annual_rate": Decimal("14.50"), "tiered_rates": None},
        "Klar": {"annual_rate": Decimal("15.00"), "tiered_rates": None},
        "Finsus": {
            "annual_rate": Decimal("15.32"),
            "tiered_rates": [
                {"min_amount": 1, "max_amount": 50000, "rate": 15.32},
                {"min_amount": 50000, "max_amount": 500000, "rate": 15.04},
                {"min_amount": 500000, "max_amount": 2000000, "rate": 14.72},
            ],
        },
        "Didi": {"annual_rate": Decimal("15.00"), "tiered_rates": None},
    }


# ---------------------------------------------------------------------------
# Retry Logic with Exponential Backoff
# ---------------------------------------------------------------------------

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0  # 1s, 2s, 4s


async def _fetch_with_retry(
    fetch_fn,
    client: httpx.AsyncClient,
    source_name: str,
) -> Any:
    """Execute a fetch function with exponential backoff retry.

    Retries up to MAX_RETRIES (3) times with delays of 1s, 2s, 4s.

    Args:
        fetch_fn: Async function to call.
        client: httpx async client to pass to the fetch function.
        source_name: Name of the source for logging.

    Returns:
        The result from fetch_fn on success.

    Raises:
        Exception: If all retries are exhausted.
    """
    last_exception: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            result = await fetch_fn(client)
            return result
        except Exception as exc:
            last_exception = exc
            wait_time = BASE_BACKOFF_SECONDS * (2**attempt)
            logger.warning(
                "Fetch attempt %d/%d for '%s' failed: %s. Retrying in %.1fs...",
                attempt + 1,
                MAX_RETRIES,
                source_name,
                str(exc),
                wait_time,
            )
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(wait_time)

    logger.error(
        "All %d fetch attempts for '%s' exhausted. Last error: %s",
        MAX_RETRIES,
        source_name,
        str(last_exception),
    )
    raise last_exception  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Core Scraping Orchestration
# ---------------------------------------------------------------------------


async def _update_instrument(
    db: AsyncSession,
    name: str,
    annual_rate: Decimal,
    source_def: dict[str, Any],
    tiered_rates: Any | None,
    fetch_status: str = "success",
) -> None:
    """Create or update an instrument record in the database.

    On success: updates rate data, sets last_fetch_status='success',
    updates last_fetched_at.
    On error: sets last_fetch_status='error', retains previous rate data.

    Args:
        db: Async database session.
        name: Instrument name.
        annual_rate: Current annual rate percentage.
        source_def: Static metadata from INSTRUMENT_SOURCES.
        tiered_rates: Tiered rate structure (or None).
        fetch_status: 'success' or 'error'.
    """
    now = datetime.now(timezone.utc)

    stmt = select(Instrument).where(Instrument.name == name)
    result = await db.execute(stmt)
    instrument = result.scalar_one_or_none()

    if instrument:
        if fetch_status == "success":
            # Update rate data on success
            instrument.annual_rate = annual_rate
            instrument.tiered_rates = tiered_rates
            instrument.min_investment = source_def["min_investment"]
            instrument.max_investment = source_def["max_investment"]
            instrument.term = source_def["term"]
            instrument.risk_level = source_def["risk_level"]
            instrument.liquidity_tier = source_def["liquidity_tier"]
            instrument.last_fetch_status = "success"
            instrument.last_fetched_at = now
        else:
            # On failure: retain previous rate data, mark status as error
            instrument.last_fetch_status = "error"
            instrument.last_fetched_at = now
    else:
        # Create new instrument record
        instrument = Instrument(
            name=name,
            annual_rate=annual_rate,
            min_investment=source_def["min_investment"],
            max_investment=source_def["max_investment"],
            term=source_def["term"],
            risk_level=source_def["risk_level"],
            liquidity_tier=source_def["liquidity_tier"],
            tiered_rates=tiered_rates,
            last_fetch_status=fetch_status,
            last_fetched_at=now,
        )
        db.add(instrument)


def _find_source_def(name: str) -> dict[str, Any] | None:
    """Find the static source definition for an instrument by name."""
    for source in INSTRUMENT_SOURCES:
        if source["name"] == name:
            return source
    return None


async def scrape_all_rates(db: AsyncSession) -> dict[str, str]:
    """Scrape/fetch rates from all data sources and store in the instruments table.

    This is the main entry point that can be triggered by a cron/scheduled task
    or a manual admin endpoint.

    Fetches from:
    - CETES (Banxico): government bonds (28, 91, 182, 364-day terms)
    - Sofipos: Nu México, Ualá, Stori, Mercado Pago, Klar, Finsus, Didi

    Returns:
        Dict mapping instrument name to fetch status ('success' or 'error').
    """
    results: dict[str, str] = {}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # --- Fetch CETES rates ---
        try:
            cetes_rates = await _fetch_with_retry(
                _fetch_cetes_rates, client, "CETES (Banxico)"
            )
            for name, rate in cetes_rates.items():
                source_def = _find_source_def(name)
                if source_def:
                    await _update_instrument(
                        db=db,
                        name=name,
                        annual_rate=rate,
                        source_def=source_def,
                        tiered_rates=None,
                        fetch_status="success",
                    )
                    results[name] = "success"
        except Exception as exc:
            logger.error("CETES fetch failed after retries: %s", str(exc))
            # Mark all CETES instruments as error
            for source in INSTRUMENT_SOURCES:
                if source["source_type"] == "cetes":
                    await _update_instrument(
                        db=db,
                        name=source["name"],
                        annual_rate=source["annual_rate"],  # fallback rate
                        source_def=source,
                        tiered_rates=None,
                        fetch_status="error",
                    )
                    results[source["name"]] = "error"

        # --- Fetch Sofipo rates ---
        try:
            sofipo_rates = await _fetch_with_retry(
                _fetch_sofipo_rates, client, "Sofipos"
            )
            for name, rate_data in sofipo_rates.items():
                source_def = _find_source_def(name)
                if source_def:
                    await _update_instrument(
                        db=db,
                        name=name,
                        annual_rate=rate_data["annual_rate"],
                        source_def=source_def,
                        tiered_rates=rate_data.get("tiered_rates"),
                        fetch_status="success",
                    )
                    results[name] = "success"
        except Exception as exc:
            logger.error("Sofipo fetch failed after retries: %s", str(exc))
            # Mark all sofipo instruments as error
            for source in INSTRUMENT_SOURCES:
                if source["source_type"] == "sofipo":
                    await _update_instrument(
                        db=db,
                        name=source["name"],
                        annual_rate=source["annual_rate"],  # fallback rate
                        source_def=source,
                        tiered_rates=source.get("tiered_rates"),
                        fetch_status="error",
                    )
                    results[source["name"]] = "error"

    return results


async def scrape_single_instrument(
    db: AsyncSession, instrument_name: str
) -> str:
    """Scrape/fetch rate for a single instrument by name.

    Args:
        db: Async database session.
        instrument_name: Name of the instrument to refresh.

    Returns:
        Fetch status ('success' or 'error').
    """
    source_def = _find_source_def(instrument_name)
    if not source_def:
        logger.error("Unknown instrument: %s", instrument_name)
        return "error"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if source_def["source_type"] == "cetes":
                rates = await _fetch_with_retry(
                    _fetch_cetes_rates, client, f"CETES ({instrument_name})"
                )
                rate = rates.get(instrument_name)
                if rate is None:
                    raise ValueError(
                        f"Instrument '{instrument_name}' not found in CETES response"
                    )
                await _update_instrument(
                    db=db,
                    name=instrument_name,
                    annual_rate=rate,
                    source_def=source_def,
                    tiered_rates=None,
                    fetch_status="success",
                )
                return "success"
            else:
                sofipo_data = await _fetch_with_retry(
                    _fetch_sofipo_rates, client, f"Sofipo ({instrument_name})"
                )
                rate_data = sofipo_data.get(instrument_name)
                if rate_data is None:
                    raise ValueError(
                        f"Instrument '{instrument_name}' not found in Sofipo response"
                    )
                await _update_instrument(
                    db=db,
                    name=instrument_name,
                    annual_rate=rate_data["annual_rate"],
                    source_def=source_def,
                    tiered_rates=rate_data.get("tiered_rates"),
                    fetch_status="success",
                )
                return "success"
        except Exception as exc:
            logger.error(
                "Failed to scrape '%s': %s", instrument_name, str(exc)
            )
            await _update_instrument(
                db=db,
                name=instrument_name,
                annual_rate=source_def["annual_rate"],
                source_def=source_def,
                tiered_rates=source_def.get("tiered_rates"),
                fetch_status="error",
            )
            return "error"
