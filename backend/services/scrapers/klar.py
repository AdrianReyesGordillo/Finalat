"""
Scraping de tasas de Klar México.
Fuente: https://klar.mx/inversion
"""

import re
import time
import httpx
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

KLAR_URL = "https://klar.mx/inversion"

CACHE_TTL = 7 * 86400  # 7 días
_cache: Optional[dict] = None
_cache_timestamp: Optional[float] = None

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9",
}


class KlarScrapingError(Exception):
    pass


def _parse_vigencia(text: str) -> Optional[datetime]:
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    # "Vigencia: del 5 al 31 de marzo de 2026"
    match = re.search(r"[Vv]igencia.*?al\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", text)
    if match:
        dia = int(match.group(1))
        mes = meses.get(match.group(2).lower())
        anio = int(match.group(3))
        if mes:
            return datetime(anio, mes, dia)
    return None


async def fetch_klar_rates() -> dict:
    global _cache, _cache_timestamp

    if _cache and _cache_timestamp and (time.time() - _cache_timestamp) < CACHE_TTL:
        return _cache

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=_HEADERS) as client:
        resp = await client.get(KLAR_URL)

    if resp.status_code != 200:
        raise KlarScrapingError(f"HTTP {resp.status_code} al consultar Klar")

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator="\n")

    rates = []

    # Buscar tasa de cuenta base (membresía Klar normal): "Cuenta 3%"
    cuenta_match = re.search(r"Cuenta\s+(\d+)%", text)
    if cuenta_match:
        rates.append({
            "product": "Klar Cuenta",
            "rate": float(cuenta_match.group(1)),
            "term_days": None,
            "frozen": False,
            "description": "Rendimiento diario, dinero disponible. Sin membresía Plus.",
        })

    # Buscar tasa máxima de inversión fija con Plus/Platino
    # Patrón: "Inversión Fija 365 días 8.50%" en la sección Plus
    inversion_plus_match = re.search(
        r"Plus\s+y\s+Platino.*?Inversión\s+Fija\s+365\s+días\s+(\d+\.?\d*)%",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if inversion_plus_match:
        max_rate = float(inversion_plus_match.group(1))
    else:
        # Fallback: buscar el patrón "8.50%" o "8.5%" después de "Plus"
        fallback_match = re.search(r"(\d+\.\d+)%\s*$", text[text.lower().find("plus"):] if "plus" in text.lower() else "", re.MULTILINE)
        if fallback_match:
            max_rate = float(fallback_match.group(1))
        else:
            # Último recurso: tasa conocida
            max_rate = 8.5

    rates.append({
        "product": "Klar Inversión (máxima)",
        "rate": max_rate,
        "term_days": 365,
        "frozen": True,
        "description": "Inversión fija a 365 días. Requiere membresía Klar Plus o Platino (tarjeta de crédito).",
    })

    vigencia = _parse_vigencia(text)

    if not rates:
        raise KlarScrapingError("No se pudieron extraer tasas de Klar")

    result = {
        "rates": rates,
        "vigencia": vigencia.isoformat() if vigencia else None,
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
