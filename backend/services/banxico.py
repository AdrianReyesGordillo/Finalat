"""
Servicio para consultar la API del Banco de México (SIE).
Documentación: https://www.banxico.org.mx/SieAPIRest/service/v1/

Series utilizadas:
- SF43936: CETES 28 días (tasa de rendimiento)
- SF43939: CETES 91 días
- SF43942: CETES 182 días
- SF43945: CETES 364 días
- SF61745: Tasa objetivo de Banxico
"""

import httpx
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from backend.config import settings

BMX_TOKEN = settings.BMX_TOKEN
BMX_BASE_URL = "https://www.banxico.org.mx/SieAPIRest/service/v1"

# Series de CETES por plazo
SERIES_CETES = {
    "SF43936": {"name": "CETES 28 días", "term_days": 28},
    "SF43939": {"name": "CETES 91 días", "term_days": 91},
    "SF43942": {"name": "CETES 182 días", "term_days": 182},
    "SF43945": {"name": "CETES 364 días", "term_days": 364},
}

# Serie de tasa objetivo
SERIE_TASA_OBJETIVO = "SF61745"

# Caché en memoria para respetar límites de consulta
_cache: dict[str, dict] = {}
CACHE_TTL_SECONDS = 86400  # 24 horas de caché


class BanxicoAPIError(Exception):
    """Error al consultar la API de Banxico."""

    def __init__(self, message: str, seconds_to_reset: Optional[int] = None):
        self.message = message
        self.seconds_to_reset = seconds_to_reset
        super().__init__(self.message)


def _get_headers() -> dict:
    """Retorna los headers necesarios para la API de Banxico."""
    return {
        "Bmx-Token": BMX_TOKEN,
        "Accept": "application/json",
    }


def _get_from_cache(key: str) -> Optional[dict]:
    """Obtiene datos del caché si no han expirado."""
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry["timestamp"] < CACHE_TTL_SECONDS:
            return entry["data"]
        else:
            del _cache[key]
    return None


def _set_cache(key: str, data: dict) -> None:
    """Almacena datos en el caché."""
    _cache[key] = {
        "data": data,
        "timestamp": time.time(),
    }


async def fetch_series_oportuno(series_ids: str) -> dict:
    """
    Consulta datos oportunos (últimos valores) de una o más series.
    
    Args:
        series_ids: IDs de series separados por coma (ej: "SF43936,SF43939")
    
    Returns:
        Dict con los datos de las series consultadas.
    
    Raises:
        BanxicoAPIError: Si la API retorna error o se superó el límite.
    """
    cache_key = f"oportuno:{series_ids}"
    cached = _get_from_cache(cache_key)
    if cached:
        return cached

    url = f"{BMX_BASE_URL}/series/{series_ids}/datos/oportuno"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=_get_headers())

    if response.status_code == 400:
        # Límite de consultas superado
        try:
            body = response.json()
        except Exception:
            raise BanxicoAPIError(message="Error 400 de Banxico (respuesta no válida)")
        error_info = body.get("error", {})
        seconds_to_reset = error_info.get("secondsToReset")
        raise BanxicoAPIError(
            message=error_info.get("detalle", "Límite de consultas superado"),
            seconds_to_reset=seconds_to_reset,
        )

    if response.status_code != 200:
        raise BanxicoAPIError(
            message=f"Error HTTP {response.status_code} al consultar Banxico"
        )

    if not response.content or not response.content.strip():
        raise BanxicoAPIError(
            message="Banxico devolvió una respuesta vacía. Verifica que BMX_TOKEN esté configurado en .env"
        )

    try:
        data = response.json()
    except Exception:
        raise BanxicoAPIError(
            message=f"Banxico devolvió respuesta no válida: {response.text[:200]}"
        )

    _set_cache(cache_key, data)
    return data


async def fetch_series_historico(
    series_ids: str, fecha_ini: str, fecha_fin: str
) -> dict:
    """
    Consulta datos históricos de una o más series.
    
    Args:
        series_ids: IDs de series separados por coma.
        fecha_ini: Fecha inicio formato YYYY-MM-DD.
        fecha_fin: Fecha fin formato YYYY-MM-DD.
    
    Returns:
        Dict con los datos históricos.
    """
    cache_key = f"historico:{series_ids}:{fecha_ini}:{fecha_fin}"
    cached = _get_from_cache(cache_key)
    if cached:
        return cached

    url = f"{BMX_BASE_URL}/series/{series_ids}/datos/{fecha_ini}/{fecha_fin}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=_get_headers())

    if response.status_code == 400:
        try:
            body = response.json()
        except Exception:
            raise BanxicoAPIError(message="Error 400 de Banxico (respuesta no válida)")
        error_info = body.get("error", {})
        raise BanxicoAPIError(
            message=error_info.get("detalle", "Límite de consultas superado"),
            seconds_to_reset=error_info.get("secondsToReset"),
        )

    if response.status_code != 200:
        raise BanxicoAPIError(
            message=f"Error HTTP {response.status_code} al consultar Banxico"
        )

    if not response.content or not response.content.strip():
        raise BanxicoAPIError(
            message="Banxico devolvió una respuesta vacía. Verifica que BMX_TOKEN esté configurado en .env"
        )

    try:
        data = response.json()
    except Exception:
        raise BanxicoAPIError(
            message=f"Banxico devolvió respuesta no válida: {response.text[:200]}"
        )

    _set_cache(cache_key, data)
    return data


async def get_tasas_cetes() -> list[dict]:
    """
    Obtiene las tasas actuales de CETES (28, 91, 182, 364 días).
    
    Returns:
        Lista de dicts con: serie_id, name, term_days, rate, date
    """
    series_ids = ",".join(SERIES_CETES.keys())
    data = await fetch_series_oportuno(series_ids)

    results = []
    bmx_data = data.get("bmx", {})
    series_list = bmx_data.get("series", [])

    for serie in series_list:
        serie_id = serie.get("idSerie", "")
        serie_info = SERIES_CETES.get(serie_id, {})
        datos = serie.get("datos", [])

        if datos:
            ultimo = datos[-1]
            valor = ultimo.get("dato", "N/E")
            fecha = ultimo.get("fecha", "")

            # El valor puede venir como "N/E" si no hay dato
            if valor != "N/E":
                results.append({
                    "serie_id": serie_id,
                    "name": serie_info.get("name", serie_id),
                    "term_days": serie_info.get("term_days"),
                    "rate": float(valor),
                    "date": fecha,
                })

    return results


async def get_tasa_objetivo() -> Optional[dict]:
    """
    Obtiene la tasa objetivo de Banxico.
    
    Returns:
        Dict con: rate, date o None si no hay dato.
    """
    data = await fetch_series_oportuno(SERIE_TASA_OBJETIVO)

    bmx_data = data.get("bmx", {})
    series_list = bmx_data.get("series", [])

    if series_list:
        serie = series_list[0]
        datos = serie.get("datos", [])
        if datos:
            ultimo = datos[-1]
            valor = ultimo.get("dato", "N/E")
            if valor != "N/E":
                return {
                    "rate": float(valor),
                    "date": ultimo.get("fecha", ""),
                }

    return None


async def get_historico_cetes(
    term_days: int = 28, months_back: int = 12
) -> list[dict]:
    """
    Obtiene el histórico de tasas de CETES para un plazo específico.
    
    Args:
        term_days: Plazo en días (28, 91, 182, 364).
        months_back: Meses hacia atrás para consultar.
    
    Returns:
        Lista de dicts con: date, rate
    """
    # Encontrar la serie correspondiente al plazo
    serie_id = None
    for sid, info in SERIES_CETES.items():
        if info["term_days"] == term_days:
            serie_id = sid
            break

    if not serie_id:
        return []

    fecha_fin = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fecha_ini = (
        datetime.now(timezone.utc) - timedelta(days=months_back * 30)
    ).strftime("%Y-%m-%d")

    data = await fetch_series_historico(serie_id, fecha_ini, fecha_fin)

    results = []
    bmx_data = data.get("bmx", {})
    series_list = bmx_data.get("series", [])

    if series_list:
        serie = series_list[0]
        datos = serie.get("datos", [])
        for dato in datos:
            valor = dato.get("dato", "N/E")
            if valor != "N/E":
                results.append({
                    "date": dato.get("fecha", ""),
                    "rate": float(valor),
                })

    return results


def clear_cache() -> None:
    """Limpia todo el caché."""
    _cache.clear()
