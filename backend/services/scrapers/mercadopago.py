"""
Scraping de tasas de Mercado Pago México.
Fuente: https://www.mercadopago.com.mx/cuenta
"""

import re
import time
import httpx
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

MP_URL = "https://www.mercadopago.com.mx/cuenta"

CACHE_TTL = 7 * 86400  # 7 días (sin fecha de vigencia)
_cache: Optional[dict] = None
_cache_timestamp: Optional[float] = None

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9",
}


class MercadoPagoScrapingError(Exception):
    pass


async def fetch_mercadopago_rates() -> dict:
    global _cache, _cache_timestamp

    if _cache and _cache_timestamp and (time.time() - _cache_timestamp) < CACHE_TTL:
        return _cache

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=_HEADERS) as client:
        resp = await client.get(MP_URL)

    if resp.status_code != 200:
        raise MercadoPagoScrapingError(f"HTTP {resp.status_code} al consultar Mercado Pago")

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n")

    rates = []

    # "Ganancias de hasta 13% anual"
    match = re.search(r"[Gg]anancias\s+de\s+hasta\s+(\d+)%\s+anual", text)
    if match:
        rates.append({
            "product": "Mercado Pago Cuenta",
            "rate": float(match.group(1)),
            "term_days": None,
            "frozen": False,
            "description": "Rendimiento diario, dinero disponible 24/7",
        })

    if not rates:
        raise MercadoPagoScrapingError("No se pudieron extraer tasas de Mercado Pago")

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
