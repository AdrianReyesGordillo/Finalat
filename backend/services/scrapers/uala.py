"""
Scraping de tasas de Ualá México.
Fuentes:
- https://www.uala.mx/cuenta-con-rendimiento
- https://www.uala.mx/reserva-a-plazo
"""

import re
import time
import httpx
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

UALA_CUENTA_URL = "https://www.uala.mx/cuenta-con-rendimiento"
UALA_RESERVA_URL = "https://www.uala.mx/reserva-a-plazo"

_cache: Optional[dict] = None
_cache_expiry: Optional[float] = None

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9",
}


class UalaScrapingError(Exception):
    pass


def _parse_vigencia(text: str) -> Optional[datetime]:
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    # "Oferta vigente al 29 de junio de 2026"
    match = re.search(
        r"[Oo]ferta\s+vigente\s+al\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})",
        text
    )
    if match:
        dia = int(match.group(1))
        mes = meses.get(match.group(2).lower())
        anio = int(match.group(3))
        if mes:
            return datetime(anio, mes, dia)
    return None


def _parse_cuenta(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    rates = []

    # Tasa Base: 6.75%
    base_match = re.search(r"Tasa\s+de\s+rendimiento\s+(\d+\.\d+)%\s+anual\s+fija.*?GAT\s+NOMINAL\s+(\d+\.\d+)%.*?saldo\s+m[áa]ximo\s+de\s+\$?([\d,]+)", text, re.DOTALL | re.IGNORECASE)
    if base_match:
        rates.append({
            "product": "Ualá Cuenta (Tasa Base)",
            "rate": float(base_match.group(1)),
            "term_days": None,
            "frozen": False,
            "max_amount": float(base_match.group(3).replace(",", "")),
            "description": "Rendimiento diario sin condiciones, disponible 24/7",
        })

    # Tasa Plus: 12%
    plus_match = re.search(r"Tasa\s+Plus\.\s+Tasa\s+de\s+rendimiento\s+(\d+\.\d+)%\s+anual", text, re.IGNORECASE)
    if plus_match:
        rates.append({
            "product": "Ualá Cuenta (Tasa Plus)",
            "rate": float(plus_match.group(1)),
            "term_days": None,
            "frozen": False,
            "max_amount": 30000,
            "description": "Requiere consumo mínimo de $3,000 al mes",
        })

    # Tasa Plus Más Alta: 15%
    plus_alta_match = re.search(r"Tasa\s+Plus\s+M[áa]s\s+Alta\.\s+Tasa\s+de\s+rendimiento\s+(\d+\.\d+)%\s+anual", text, re.IGNORECASE)
    if plus_alta_match:
        rates.append({
            "product": "Ualá Cuenta (Tasa Plus Alta)",
            "rate": float(plus_alta_match.group(1)),
            "term_days": None,
            "frozen": False,
            "max_amount": 30000,
            "description": "Requiere consumo mínimo de $6,000 al mes",
        })

    return rates


def _parse_reserva(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    rates = []

    # "Tasa de rendimiento 7.40% anual fija"
    match = re.search(r"Tasa\s+de\s+rendimiento\s+(\d+\.\d+)%\s+anual\s+fija.*?plazo\s+de\s+(\d+)\s+d[ií]as", text, re.DOTALL | re.IGNORECASE)
    if match:
        rates.append({
            "product": "Ualá Reserva a Plazo",
            "rate": float(match.group(1)),
            "term_days": int(match.group(2)),
            "frozen": True,
            "max_amount": None,
            "description": f"Plazo fijo {match.group(2)} días, tasa fija anual",
        })

    return rates


async def fetch_uala_rates() -> dict:
    global _cache, _cache_expiry

    if _cache and _cache_expiry and time.time() < _cache_expiry:
        return _cache

    rates = []
    vigencia = None

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=_HEADERS) as client:
        # Cuenta con rendimiento
        resp = await client.get(UALA_CUENTA_URL)
        if resp.status_code == 200:
            rates.extend(_parse_cuenta(resp.text))
            vigencia = _parse_vigencia(resp.text)

        # Reserva a plazo
        resp2 = await client.get(UALA_RESERVA_URL)
        if resp2.status_code == 200:
            rates.extend(_parse_reserva(resp2.text))
            if not vigencia:
                vigencia = _parse_vigencia(resp2.text)

    if not rates:
        raise UalaScrapingError("No se pudieron extraer tasas de Ualá")

    result = {
        "rates": rates,
        "vigencia": vigencia.isoformat() if vigencia else None,
        "fetched_at": datetime.now().isoformat(),
    }

    # Caché hasta la vigencia o 7 días
    if vigencia:
        _cache_expiry = vigencia.replace(hour=4, minute=0).timestamp()
    else:
        _cache_expiry = time.time() + 7 * 86400

    _cache = result
    return result


def get_cache_status() -> dict:
    if _cache and _cache_expiry:
        return {"cached": True, "expires_in_seconds": max(0, int(_cache_expiry - time.time()))}
    return {"cached": False}


def clear_cache():
    global _cache, _cache_expiry
    _cache = None
    _cache_expiry = None
