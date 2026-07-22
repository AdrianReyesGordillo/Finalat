"""Finanzas stub routes — placeholder endpoints for the financial dashboard.

These endpoints return empty/default data to prevent 404 errors while
the full finanzas module is being integrated. The frontend finanzas views
call these routes when a user navigates to the dashboard.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api", tags=["finanzas"])


@router.get("/dashboard")
async def dashboard(request: Request):
    """Financial dashboard summary."""
    return {
        "gbm": {"positions": [], "total_mxn": 0, "total_usd": 0},
        "creditos": {"cards": []},
        "inversiones": {"accounts": [], "totals": {"total": 0}},
        "gi": {"records": [], "summary": {"income": 0, "expenses": 0, "balance": 0}},
        "deudas": {"deudas": [], "total": 0},
    }


@router.get("/subscription")
async def get_subscription(request: Request):
    """User subscription tier."""
    return {
        "tier": "free",
        "status": "active",
        "permissions": {
            "dashboard_basico": True,
            "gastos_ingresos": True,
            "cursos_gratuitos": True,
            "agente_limitado": True,
            "inversiones": True,
            "agente_ilimitado": True,
            "analisis_avanzado": True,
            "proyecciones": True,
            "soporte_prioritario": False,
        },
        "familyGroup": None,
    }


@router.get("/preferences")
async def get_preferences(request: Request):
    """User preferences."""
    return {"currency": "MXN", "locale": "es-MX"}


@router.get("/inversiones")
async def get_inversiones(request: Request):
    """Investment accounts."""
    return {"accounts": [], "totals": {"total": 0}}


@router.get("/inversiones/update-status")
async def inversiones_update_status(request: Request):
    """Update status for investments."""
    return {"needs_update": False, "last_updated": None}


@router.get("/inversiones/afore/update-status")
async def afore_update_status(request: Request):
    """Update status for Afore."""
    return {"needs_update": False, "last_updated": None}


@router.get("/inversiones/prestamos/update-status")
async def prestamos_update_status(request: Request):
    """Update status for loans."""
    return {"needs_update": False, "last_updated": None}


@router.get("/gbm/portfolio")
async def gbm_portfolio(request: Request):
    """GBM portfolio."""
    return {"positions": [], "total_mxn": 0, "total_usd": 0}


@router.get("/gbm/update-status")
async def gbm_update_status(request: Request):
    """GBM update status."""
    return {"needs_update": False, "last_updated": None}


@router.get("/creditos")
async def get_creditos(request: Request):
    """Credit cards."""
    return {"cards": []}


@router.get("/creditos/update-status")
async def creditos_update_status(request: Request):
    """Credits update status."""
    return {"needs_update": False, "last_updated": None}


@router.get("/deudas")
async def get_deudas(request: Request):
    """Debts."""
    return {"deudas": [], "total": 0}


@router.get("/gi/records")
async def get_gi_records(request: Request):
    """Income/expense records."""
    return {"records": [], "summary": {"income": 0, "expenses": 0, "balance": 0}}


@router.get("/gi/categories")
async def get_gi_categories(request: Request):
    """Income/expense categories."""
    return {"categories": []}


@router.get("/patrimonio")
async def get_patrimonio(request: Request):
    """Net worth / patrimonio."""
    return {"history": [], "current": {"assets": 0, "liabilities": 0, "net_worth": 0}}


@router.get("/aportaciones")
async def get_aportaciones(request: Request):
    """Weekly contribution tracker."""
    return {"weeks": [], "current_streak": 0}
