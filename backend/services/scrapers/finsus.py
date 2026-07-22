"""
Scraping de tasas de Finsus México.
Fuente: https://finsus.mx
"""

import re
import time
import httpx
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

FINSUS_URL = "https://finsus.mx"

CACHE_TTL = 7 * 86400  # 7 días
_cache: Optional[dict] = None
_cache_timestamp: Optional[float] = None

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9",
}


class FinsusScrapingError(Exception):
    pass


async def fetch_finsus_rates() -> dict:
    global _cache, _cache_timestamp

    if _cache and _cache_timestamp and (time.time() - _cache_timestamp) < CACHE_TTL:
        return _cache

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=_HEADERS) as client:
        resp = await client.get(FINSUS_URL)

    if resp.status_code != 200:
        raise FinsusScrapingError(f"HTTP {resp.status_code} al consultar Finsus")

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n")

    rates = []

    # "Tasa especial 11.5%* anual" y "Plazo fijo de 120 días"
    especial_match = re.search(
        r"[Tt]asa\s+especial\s+(\d+\.?\d*)%.*?[Pp]lazo\s+fijo\s+de\s+(\d+)\s+d[ií]as",
        text, re.DOTALL
    )
    if especial_match:
        rates.append({
            "product": "Finsus Tasa Especial",
            "rate": float(especial_match.group(1)),
            "term_days": int(especial_match.group(2)),
            "frozen": True,
            "description": f"Plazo fijo {especial_match.group(2)} días, tasa especial por tiempo limitado",
        })

    # "rendimiento hasta 9.09% anual"
    regular_match = re.search(r"rendimiento\s+hasta\s+(\d+\.\d+)%\s+anual", text, re.IGNORECASE)
    if regular_match:
        rates.append({
            "product": "Finsus Inversión",
            "rate": float(regular_match.group(1)),
            "term_days": None,
            "frozen": False,
            "description": "Inversiones que se adaptan a tus metas",
        })

    if not rates:
        raise FinsusScrapingError("No se pudieron extraer tasas de Finsus")

    result = {
        "rates": rates,
        "vigencia": None,
        "fetched_at": datetime.now().isoformat(),
    }

    _cache = result
    _cache_timestamp = time.time()
    return result


def get_cache_status() -> dict:
    if _cache and _cache_timestamp:
        return {"cached": True, "expires_in_seconds": max(0, int(CACHE_TTL - (time.time() - _cache_timestamp)))}
    return {"cached": False}


def clear_cache():
    global _cache, _cache_timestamp
    _cache = None
    _cache_timestamp = None
