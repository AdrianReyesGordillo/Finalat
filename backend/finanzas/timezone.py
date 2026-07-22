"""Centralized timezone helper for Mexico City (America/Mexico_City).

All date/time operations in the finanzas module should use these helpers
instead of date.today() or datetime.now() to ensure consistent timezone behavior
regardless of the server's system timezone (e.g., UTC on Render).
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

MEXICO_TZ = ZoneInfo("America/Mexico_City")


def today() -> date:
    """Returns today's date in Mexico City timezone."""
    return datetime.now(MEXICO_TZ).date()


def now() -> datetime:
    """Returns current datetime in Mexico City timezone."""
    return datetime.now(MEXICO_TZ)
