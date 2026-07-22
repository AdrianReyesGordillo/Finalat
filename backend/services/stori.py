"""
Servicio de web scraping para obtener tasas de rendimiento de Stori Cuenta+.
Fuente: https://www.storicard.com/stori-cuentamas

Extrae tasas de:
- Apartados (crecimiento diario)
- Stori Inversión+ (30, 60, 90, 180, 360 días)
"""

import re
import time
import httpx
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

STORI_URL = "https://www.storicard.com/stori-cuentamas"

# Caché con TTL de 7 días (no hay fecha de vigencia explícita en la página)
CACHE_TTL_SECONDS = 7 * 86400  # 7 días
_cache: Optional[dict] = None
_cache_timestamp: Optional[float] = None

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Chromium";v="125", "Not.A/Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


class StoriScrapingError(Exception):
    """Error al hacer scraping de la página de Stori."""
    pass


def _parse_rates_from_html(html: str) -> dict:
    """
    Extrae las tasas de rendimiento del HTML de Stori.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")

    rates = []

    # Apartados: "Rendimiento Apartados 7.00% GAT Nominal"
    apartados_match = re.search(
        r"(?:Rendimiento\s+)?Apartados\s+(\d+\.\d+)\s*%\s*GAT\s*Nominal",
        text, re.IGNORECASE
    )
    if apartados_match:
        rates.append({
            "product": "Stori Apartados",
            "rate": float(apartados_match.group(1)),
            "term_days": None,
            "frozen": False,
            "description": "Crecimiento diario, dinero disponible",
        })

    # Inversión+ por plazos: "30 días 7.05% GAT Nominal"
    inversion_pattern = re.findall(
        r"(\d+)\s+días(?:\s*Exclusivo\s+Stori\s+Pro)?\s+(\d+\.\d+)\s*%\s*GAT\s*Nominal",
        text, re.IGNORECASE
    )
    for term, rate in inversion_pattern:
        term_int = int(term)
        rate_float = float(rate)
        is_pro = False

        # Verificar si es exclusivo Stori Pro (buscar en contexto)
        pro_check = re.search(
            rf"{term}\s+días\s*Exclusivo\s+Stori\s+Pro\s+{re.escape(rate)}",
            text, re.IGNORECASE
        )
        if pro_check:
            is_pro = True

        product_name = f"Stori Inversión+ {term} días"
        if is_pro:
            product_name += " (Stori Pro)"

        rates.append({
            "product": product_name,
            "rate": rate_float,
            "term_days": term_int,
            "frozen": True,
            "is_pro_exclusive": is_pro,
            "description": f"Plazo fijo {term} días" + (" - Exclusivo Stori Pro" if is_pro else ""),
        })

    # No hay fecha de vigencia explícita en la página
    # Solo menciona "Por tiempo limitado"
    return {
        "rates": rates,
        "vigencia": None,  # No disponible en la página
        "nota_vigencia": "Por tiempo limitado. Consultar TyC para más información.",
        "fetched_at": datetime.now().isoformat(),
    }


async def fetch_stori_rates() -> dict:
    """
    Consulta la página de Stori y extrae las tasas de rendimiento.
    Caché de 7 días (no hay fecha de vigencia explícita).

    Returns:
        Dict con rates, vigencia, nota_vigencia, fetched_at

    Raises:
        StoriScrapingError si no se puede obtener o parsear la página.
    """
    global _cache, _cache_timestamp

    # Verificar caché vigente
    if _cache and _cache_timestamp and (time.time() - _cache_timestamp) < CACHE_TTL_SECONDS:
        return _cache

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=_HEADERS,
        ) as client:
            response = await client.get(STORI_URL)

        if response.status_code != 200:
            raise StoriScrapingError(
                f"HTTP {response.status_code} al consultar {STORI_URL}"
            )

        result = _parse_rates_from_html(response.text)

        if not result["rates"]:
            raise StoriScrapingError(
                "No se pudieron extraer tasas de la página de Stori. "
                "Es posible que la estructura haya cambiado."
            )

        _cache = result
        _cache_timestamp = time.time()
        return result

    except httpx.HTTPError as e:
        raise StoriScrapingError(f"Error de conexión al consultar Stori: {str(e)}")


def get_cache_status() -> dict:
    """Retorna el estado actual del caché de Stori."""
    if _cache and _cache_timestamp:
        elapsed = time.time() - _cache_timestamp
        remaining = CACHE_TTL_SECONDS - elapsed
        return {
            "cached": True,
            "expires_in_seconds": max(0, int(remaining)),
            "fetched_at": _cache.get("fetched_at"),
            "num_rates": len(_cache.get("rates", [])),
        }
    return {"cached": False}


def clear_cache() -> None:
    """Limpia el caché de Stori."""
    global _cache, _cache_timestamp
    _cache = None
    _cache_timestamp = None
