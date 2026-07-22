"""
Servicio de web scraping para obtener tasas de rendimiento de Nu México.
Fuente: https://nu.com.mx/cuenta/rendimientos/

Extrae tasas de:
- Cajita Turbo
- Cajitas Nu (disponible 24/7)
- Ahorro Congelado: 7, 28, 90, 180 días
"""

import re
import time
import httpx
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
import json

NU_URL = "https://nu.com.mx/cuenta/rendimientos/"

# Caché interno con TTL dinámico basado en la fecha de vigencia
_cache: Optional[dict] = None
_cache_expiry: Optional[float] = None

# Headers que simulan un navegador real
_HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Sec-Ch-Ua": '"Chromium";v="125", "Not.A/Brand";v="24"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    },
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-419,es;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
]


class NuScrapingError(Exception):
    """Error al hacer scraping de la página de Nu."""
    pass


def _parse_vigencia(text: str) -> Optional[datetime]:
    """
    Parsea la fecha de vigencia del texto de la página.
    Ejemplo: 'Vigencia al 8 de julio de 2026'
    """
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }

    pattern = r"[Vv]igencia\s+al\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})"
    match = re.search(pattern, text)
    if match:
        dia = int(match.group(1))
        mes_str = match.group(2).lower()
        anio = int(match.group(3))
        mes = meses.get(mes_str)
        if mes:
            return datetime(anio, mes, dia)
    return None


def _parse_fecha_calculo(text: str) -> Optional[datetime]:
    """Parsea la fecha de cálculo."""
    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }
    match = re.search(
        r"[Vv]alores\s+calculados\s+el\s+(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})",
        text
    )
    if match:
        dia = int(match.group(1))
        mes = meses.get(match.group(2).lower())
        anio = int(match.group(3))
        if mes:
            return datetime(anio, mes, dia)
    return None


def _try_parse_next_data(html: str) -> Optional[dict]:
    """
    Intenta extraer datos del script __NEXT_DATA__ si existe (Next.js SSR).
    """
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if script and script.string:
        try:
            return json.loads(script.string)
        except json.JSONDecodeError:
            pass
    return None


def _parse_rates_from_html(html: str) -> dict:
    """
    Extrae las tasas y fechas de vigencia del HTML de la página.
    Usa BeautifulSoup para extraer texto limpio y luego regex.
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")

    rates = []

    # Cajita Turbo
    turbo_match = re.search(
        r"Cajita\s+Turbo.*?Tasa\s+de\s+Rendimiento\s*\n?\s*Anual\s+Fija\s*\n?\s*(\d+\.\d+)\s*%",
        text, re.DOTALL | re.IGNORECASE
    )
    if turbo_match:
        rates.append({
            "product": "Cajita Turbo",
            "rate": float(turbo_match.group(1)),
            "term_days": None,
            "frozen": False,
            "description": "Rendimiento promocional con condiciones especiales",
        })

    # Cajitas Nu (disponible 24/7) — buscar la segunda aparición (después de Turbo)
    # El patrón específico es "Cajitas Nu²" o "Cajitas" con superíndice en la tabla
    cajitas_matches = re.finditer(
        r"Cajitas(?:\s+Nu)?[²\s]*.*?Tasa\s+de\s+Rendimiento\s*\n?\s*Anual\s+Fija\s*\n?\s*(\d+\.\d+)\s*%",
        text, re.DOTALL | re.IGNORECASE
    )
    for m in cajitas_matches:
        rate_val = float(m.group(1))
        # La Cajita Turbo tiene tasa más alta, Cajitas Nu normal es <= 10%
        if rate_val < 10.0:
            rates.append({
                "product": "Cajitas Nu",
                "rate": rate_val,
                "term_days": None,
                "frozen": False,
                "description": "Disponible 24/7, sin congelar",
            })
            break

    # Ahorro Congelado por plazos
    frozen_pattern = re.findall(
        r"Ahorro\s+Congelado\s*\n?\s*(\d+)\s+d[ií]as.*?Tasa\s+de\s+Rendimiento\s*\n?\s*Anual\s+Fija\s*\n?\s*(\d+\.\d+)\s*%",
        text, re.DOTALL | re.IGNORECASE
    )
    for term, rate in frozen_pattern:
        rates.append({
            "product": f"Ahorro Congelado {term} días",
            "rate": float(rate),
            "term_days": int(term),
            "frozen": True,
            "description": f"Saldo congelado por {term} días",
        })

    vigencia = _parse_vigencia(text)
    fecha_calculo = _parse_fecha_calculo(text)

    return {
        "rates": rates,
        "vigencia": vigencia.isoformat() if vigencia else None,
        "fecha_calculo": fecha_calculo.isoformat() if fecha_calculo else None,
        "fetched_at": datetime.now().isoformat(),
    }


async def _fetch_html() -> str:
    """
    Intenta obtener el HTML de la página de Nu con reintentos y headers variados.
    """
    last_error = None
    for headers in _HEADERS_LIST:
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers=headers,
            ) as client:
                response = await client.get(NU_URL)

            if response.status_code == 200:
                return response.text

            last_error = f"HTTP {response.status_code}"
        except httpx.HTTPError as e:
            last_error = str(e)

    raise NuScrapingError(
        f"No se pudo acceder a {NU_URL} después de varios intentos. Último error: {last_error}"
    )


async def fetch_nu_rates() -> dict:
    """
    Consulta la página de Nu y extrae las tasas de rendimiento.
    El caché expira en la fecha de vigencia publicada por Nu.

    Returns:
        Dict con rates, vigencia, fecha_calculo, fetched_at
    
    Raises:
        NuScrapingError si no se puede obtener o parsear la página.
    """
    global _cache, _cache_expiry

    # Verificar caché vigente
    if _cache and _cache_expiry and time.time() < _cache_expiry:
        return _cache

    html = await _fetch_html()
    result = _parse_rates_from_html(html)

    if not result["rates"]:
        raise NuScrapingError(
            "No se pudieron extraer tasas de la página de Nu. "
            "Es posible que la estructura de la página haya cambiado."
        )

    # Calcular expiración del caché basada en la vigencia
    if result["vigencia"]:
        vigencia_dt = datetime.fromisoformat(result["vigencia"])
        # El caché expira a las 4:00 AM del día de vigencia
        expiry_dt = vigencia_dt.replace(hour=4, minute=0, second=0)
        _cache_expiry = expiry_dt.timestamp()
    else:
        # Fallback: caché de 24 horas
        _cache_expiry = time.time() + 86400

    _cache = result
    return result


def get_cache_status() -> dict:
    """Retorna el estado actual del caché de Nu."""
    if _cache and _cache_expiry:
        remaining = _cache_expiry - time.time()
        return {
            "cached": True,
            "expires_in_seconds": max(0, int(remaining)),
            "vigencia": _cache.get("vigencia"),
            "fetched_at": _cache.get("fetched_at"),
            "num_rates": len(_cache.get("rates", [])),
        }
    return {"cached": False}


def clear_cache() -> None:
    """Limpia el caché de Nu."""
    global _cache, _cache_expiry
    _cache = None
    _cache_expiry = None
