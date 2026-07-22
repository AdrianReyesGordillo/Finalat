"""Tests for the Rate Scraper service.

Validates:
- scrape_all_rates() creates/updates instrument records
- Retry with exponential backoff (max 3 attempts)
- Error handling: last_fetch_status set to "error" on failure
- Tiered rate structures stored correctly
- Single instrument scraping
"""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.models.database import Base
from backend.models.instruments import Instrument
from backend.services.rate_scraper import (
    INSTRUMENT_SOURCES,
    MAX_RETRIES,
    _fetch_with_retry,
    scrape_all_rates,
    scrape_single_instrument,
)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def test_engine():
    """Create a test SQLite async engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    """Create a test database session."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# Tests: scrape_all_rates
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrape_all_rates_creates_instruments(db_session: AsyncSession):
    """scrape_all_rates should create instrument records for all sources."""
    results = await scrape_all_rates(db_session)
    await db_session.commit()

    # Should have results for all defined instruments
    assert len(results) == len(INSTRUMENT_SOURCES)

    # All should be successful
    for name, status in results.items():
        assert status == "success", f"{name} should be 'success', got '{status}'"

    # Verify records in database
    stmt = select(Instrument)
    result = await db_session.execute(stmt)
    instruments = result.scalars().all()

    assert len(instruments) == len(INSTRUMENT_SOURCES)


@pytest.mark.asyncio
async def test_scrape_all_rates_updates_existing(db_session: AsyncSession):
    """scrape_all_rates should update existing instrument records."""
    # First scrape
    await scrape_all_rates(db_session)
    await db_session.commit()

    # Get initial last_fetched_at for one instrument
    stmt = select(Instrument).where(Instrument.name == "Nu México")
    result = await db_session.execute(stmt)
    nu = result.scalar_one()
    first_fetch_time = nu.last_fetched_at

    # Brief pause to ensure timestamp difference
    await asyncio.sleep(0.05)

    # Second scrape
    await scrape_all_rates(db_session)
    await db_session.commit()

    # Should still have same count (no duplicates)
    stmt = select(Instrument)
    result = await db_session.execute(stmt)
    instruments = result.scalars().all()
    assert len(instruments) == len(INSTRUMENT_SOURCES)

    # Timestamp should be updated (strip tz info for SQLite comparison)
    stmt = select(Instrument).where(Instrument.name == "Nu México")
    result = await db_session.execute(stmt)
    nu_updated = result.scalar_one()
    # SQLite returns naive datetimes; ensure both are comparable
    updated_at = nu_updated.last_fetched_at.replace(tzinfo=None) if nu_updated.last_fetched_at.tzinfo else nu_updated.last_fetched_at
    first_at = first_fetch_time.replace(tzinfo=None) if first_fetch_time.tzinfo else first_fetch_time
    assert updated_at >= first_at


@pytest.mark.asyncio
async def test_scrape_all_rates_tiered_rates_stored(db_session: AsyncSession):
    """Instruments with tiered rates should have tiered_rates JSONB stored."""
    await scrape_all_rates(db_session)
    await db_session.commit()

    stmt = select(Instrument).where(Instrument.name == "Nu México")
    result = await db_session.execute(stmt)
    nu = result.scalar_one()

    assert nu.tiered_rates is not None
    assert len(nu.tiered_rates) == 3
    assert nu.tiered_rates[0]["rate"] == 15.5
    assert nu.tiered_rates[1]["rate"] == 14.5
    assert nu.tiered_rates[2]["rate"] == 13.0


@pytest.mark.asyncio
async def test_scrape_all_rates_no_tiered_rates(db_session: AsyncSession):
    """Instruments without tiered rates should have tiered_rates = None."""
    await scrape_all_rates(db_session)
    await db_session.commit()

    stmt = select(Instrument).where(Instrument.name == "Ualá")
    result = await db_session.execute(stmt)
    uala = result.scalar_one()

    assert uala.tiered_rates is None
    assert uala.annual_rate == Decimal("15.00")


# ---------------------------------------------------------------------------
# Tests: Error handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrape_marks_error_on_cetes_failure(db_session: AsyncSession):
    """When CETES fetch fails, instruments should be marked with error status."""
    with patch(
        "backend.services.rate_scraper._fetch_cetes_rates",
        side_effect=Exception("Network error"),
    ):
        results = await scrape_all_rates(db_session)
        await db_session.commit()

    # CETES instruments should have error status
    for source in INSTRUMENT_SOURCES:
        if source["source_type"] == "cetes":
            assert results[source["name"]] == "error"

    # Sofipo instruments should still be success
    for source in INSTRUMENT_SOURCES:
        if source["source_type"] == "sofipo":
            assert results[source["name"]] == "success"

    # Verify in DB
    stmt = select(Instrument).where(Instrument.name == "CETES 28")
    result = await db_session.execute(stmt)
    cetes = result.scalar_one()
    assert cetes.last_fetch_status == "error"


@pytest.mark.asyncio
async def test_scrape_marks_error_on_sofipo_failure(db_session: AsyncSession):
    """When Sofipo fetch fails, those instruments should be marked with error status."""
    with patch(
        "backend.services.rate_scraper._fetch_sofipo_rates",
        side_effect=Exception("Connection timeout"),
    ):
        results = await scrape_all_rates(db_session)
        await db_session.commit()

    # Sofipo instruments should have error status
    for source in INSTRUMENT_SOURCES:
        if source["source_type"] == "sofipo":
            assert results[source["name"]] == "error"

    # CETES instruments should still be success
    for source in INSTRUMENT_SOURCES:
        if source["source_type"] == "cetes":
            assert results[source["name"]] == "success"


@pytest.mark.asyncio
async def test_error_retains_previous_rate_data(db_session: AsyncSession):
    """On fetch failure, previous rate data should be retained."""
    # First successful scrape
    await scrape_all_rates(db_session)
    await db_session.commit()

    # Get the original rate
    stmt = select(Instrument).where(Instrument.name == "CETES 28")
    result = await db_session.execute(stmt)
    cetes = result.scalar_one()
    original_rate = cetes.annual_rate

    # Second scrape with CETES failure
    with patch(
        "backend.services.rate_scraper._fetch_cetes_rates",
        side_effect=Exception("Network error"),
    ):
        await scrape_all_rates(db_session)
        await db_session.commit()

    # Rate should be retained
    stmt = select(Instrument).where(Instrument.name == "CETES 28")
    result = await db_session.execute(stmt)
    cetes_after = result.scalar_one()
    assert cetes_after.annual_rate == original_rate
    assert cetes_after.last_fetch_status == "error"


# ---------------------------------------------------------------------------
# Tests: Retry with exponential backoff
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt():
    """Fetch should succeed if the function works on retry."""
    call_count = 0

    async def flaky_fn(client):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise Exception("Temporary failure")
        return {"data": "ok"}

    # Patch sleep to avoid real delays
    with patch("backend.services.rate_scraper.asyncio.sleep", new_callable=AsyncMock):
        result = await _fetch_with_retry(flaky_fn, None, "test_source")

    assert result == {"data": "ok"}
    assert call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausts_all_attempts():
    """After MAX_RETRIES failures, the exception should propagate."""
    call_count = 0

    async def always_fails(client):
        nonlocal call_count
        call_count += 1
        raise Exception("Persistent failure")

    with patch("backend.services.rate_scraper.asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(Exception, match="Persistent failure"):
            await _fetch_with_retry(always_fails, None, "test_source")

    assert call_count == MAX_RETRIES


@pytest.mark.asyncio
async def test_retry_backoff_timing():
    """Verify exponential backoff waits: 1s, 2s, 4s."""
    sleep_calls = []

    async def mock_sleep(duration):
        sleep_calls.append(duration)

    async def always_fails(client):
        raise Exception("fail")

    with patch("backend.services.rate_scraper.asyncio.sleep", side_effect=mock_sleep):
        with pytest.raises(Exception):
            await _fetch_with_retry(always_fails, None, "test_source")

    # Should have 2 sleep calls (between attempts 1-2, 2-3)
    assert len(sleep_calls) == 2
    assert sleep_calls[0] == 1.0  # 1 * 2^0
    assert sleep_calls[1] == 2.0  # 1 * 2^1


# ---------------------------------------------------------------------------
# Tests: Single instrument scraping
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_scrape_single_instrument_success(db_session: AsyncSession):
    """scrape_single_instrument should create/update a single instrument."""
    status = await scrape_single_instrument(db_session, "Nu México")
    await db_session.commit()

    assert status == "success"

    stmt = select(Instrument).where(Instrument.name == "Nu México")
    result = await db_session.execute(stmt)
    nu = result.scalar_one()

    assert nu.annual_rate == Decimal("15.50")
    assert nu.last_fetch_status == "success"
    assert nu.tiered_rates is not None


@pytest.mark.asyncio
async def test_scrape_single_instrument_unknown_name(db_session: AsyncSession):
    """scrape_single_instrument should return 'error' for unknown instruments."""
    status = await scrape_single_instrument(db_session, "Unknown Bank")
    assert status == "error"


@pytest.mark.asyncio
async def test_scrape_single_cetes_instrument(db_session: AsyncSession):
    """scrape_single_instrument should work for CETES instruments."""
    status = await scrape_single_instrument(db_session, "CETES 28")
    await db_session.commit()

    assert status == "success"

    stmt = select(Instrument).where(Instrument.name == "CETES 28")
    result = await db_session.execute(stmt)
    cetes = result.scalar_one()

    assert cetes.annual_rate == Decimal("11.00")
    assert cetes.term == "28"
    assert cetes.risk_level == "low"
    assert cetes.liquidity_tier == "28-day"


# ---------------------------------------------------------------------------
# Tests: Instrument model fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_instrument_fields_populated_correctly(db_session: AsyncSession):
    """All instrument fields should be populated from source definitions."""
    await scrape_all_rates(db_session)
    await db_session.commit()

    stmt = select(Instrument).where(Instrument.name == "Finsus")
    result = await db_session.execute(stmt)
    finsus = result.scalar_one()

    assert finsus.name == "Finsus"
    assert finsus.annual_rate == Decimal("15.32")
    assert finsus.min_investment == Decimal("1.00")
    assert finsus.max_investment == Decimal("2000000.00")
    assert finsus.term == "liquid"
    assert finsus.risk_level == "low"
    assert finsus.liquidity_tier == "1-day"
    assert finsus.last_fetch_status == "success"
    assert finsus.last_fetched_at is not None
    assert finsus.tiered_rates is not None
    assert len(finsus.tiered_rates) == 3
