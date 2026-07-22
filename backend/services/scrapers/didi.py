"""
Scraping de tasas de Didi (99 Pay) México.
Nota: La página de Didi no es accesible para scraping directo.
Se mantienen los datos del seed y se reconsulta semanalmente por si cambia.
"""

import time
from datetime import datetime
from typing import Optional

# Didi no tiene una página pública accesible con tasas.
# Los datos se mantienen manualmente en el seed.
# Este módulo existe para mantener consistencia con el patrón.

CACHE_TTL = 7 * 86400  # 7 días
_cache: Optional[dict] = None
_cache_timestamp: Optional[float] = None


class DidiScrapingError(Exception):
    pass


async def fetch_didi_rates() -> dict:
    """
    Didi no tiene página pública de tasas accesible.
    Retorna los datos conocidos como fallback.
    """
    global _cache, _cache_timestamp

    if _cache and _cache_timestamp and (time.time() - _cache_timestamp) < CACHE_TTL:
        return _cache

    # Datos conocidos (actualizados manualmente cuando cambian)
    result = {
        "rates": [
            {
                "product": "Didi Cuenta",
                "rate": 15.0,
                "term_days": None,
                "frozen": False,
                "max_amount": 10000,
                "secondary_rate": 7.5,
                "description": "15% GAT sobre primeros $10,000. Excedente 7.5%",
            },
        ],
        "vigencia": None,
        "nota": "Datos no disponibles por scraping. Verificar manualmente.",
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
