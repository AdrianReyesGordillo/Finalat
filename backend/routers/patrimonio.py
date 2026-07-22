"""Patrimonio (Net Worth) router — GET endpoint for /api/patrimonio.

Calculates net worth by aggregating:
  Assets: ahorro (amounts) + afore (balances) + gbm_portfolio (market_values)
  Liabilities: deudas (total_amounts) + creditos (balances)
  Net Worth = total_assets - total_liabilities

Always computed in real-time (no cache). Handles partial decryption failures
gracefully by excluding failed entries and reporting failure counts.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6 (mapped as 10.1–10.6 in tasks)
"""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.ahorro import Ahorro
from backend.models.afore import Afore
from backend.models.creditos import Credito
from backend.models.deudas import Deuda
from backend.models.gbm_portfolio import GbmPortfolio
from backend.models.database import get_db
from backend.services.encryption import EncryptionError, encryption_service
from backend.utils.response import error_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/patrimonio", tags=["patrimonio"])


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_current_user_id(request: Request) -> str:
    """Extract user_id from request.state (set by auth middleware)."""
    return request.state.user_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_decrypt_sum(entries, encrypted_field: str) -> tuple[float, int]:
    """Decrypt a field from each entry and sum the values.

    Args:
        entries: List of SQLAlchemy model instances.
        encrypted_field: The name of the encrypted column attribute.

    Returns:
        A tuple of (total_sum, failed_count).
    """
    total = 0.0
    failed_count = 0
    for entry in entries:
        try:
            ciphertext = getattr(entry, encrypted_field)
            decrypted = encryption_service.decrypt(ciphertext)
            total += float(decrypted)
        except (EncryptionError, ValueError, TypeError) as exc:
            logger.warning(
                "Failed to decrypt %s for entry %s: %s",
                encrypted_field,
                getattr(entry, "id", "unknown"),
                type(exc).__name__,
            )
            failed_count += 1
    return total, failed_count


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("")
async def get_patrimonio(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Calculate and return the user's net worth (patrimonio).

    Aggregates assets and liabilities from all financial modules,
    handles partial decryption failures gracefully, and returns
    a breakdown by category. No caching — always real-time.
    """
    total_failed = 0

    # --- Assets ---

    # 1. Ahorro (savings amounts)
    stmt = select(Ahorro).where(Ahorro.user_id == user_id)
    result = await db.execute(stmt)
    ahorro_entries = result.scalars().all()
    ahorro_total, ahorro_failed = _safe_decrypt_sum(ahorro_entries, "amount_encrypted")
    total_failed += ahorro_failed

    # 2. Afore (pension balances)
    stmt = select(Afore).where(Afore.user_id == user_id)
    result = await db.execute(stmt)
    afore_entries = result.scalars().all()
    afore_total, afore_failed = _safe_decrypt_sum(afore_entries, "balance_encrypted")
    total_failed += afore_failed

    # 3. GBM Portfolio (market values)
    stmt = select(GbmPortfolio).where(GbmPortfolio.user_id == user_id)
    result = await db.execute(stmt)
    gbm_entries = result.scalars().all()
    gbm_total, gbm_failed = _safe_decrypt_sum(gbm_entries, "market_value_encrypted")
    total_failed += gbm_failed

    total_assets = ahorro_total + afore_total + gbm_total

    # --- Liabilities ---

    # 4. Deudas (total debt amounts)
    stmt = select(Deuda).where(Deuda.user_id == user_id)
    result = await db.execute(stmt)
    deuda_entries = result.scalars().all()
    deudas_total, deudas_failed = _safe_decrypt_sum(
        deuda_entries, "total_amount_encrypted"
    )
    total_failed += deudas_failed

    # 5. Creditos (credit card balances)
    stmt = select(Credito).where(Credito.user_id == user_id)
    result = await db.execute(stmt)
    credito_entries = result.scalars().all()
    creditos_total, creditos_failed = _safe_decrypt_sum(
        credito_entries, "balance_encrypted"
    )
    total_failed += creditos_failed

    total_liabilities = deudas_total + creditos_total

    # --- Net Worth ---
    net_worth = total_assets - total_liabilities

    response_data = {
        "total": round(net_worth, 2),
        "assets": {
            "ahorro": round(ahorro_total, 2),
            "afore": round(afore_total, 2),
            "gbm": round(gbm_total, 2),
            "total": round(total_assets, 2),
        },
        "liabilities": {
            "deudas": round(deudas_total, 2),
            "creditos": round(creditos_total, 2),
            "total": round(total_liabilities, 2),
        },
    }

    # Include failure metadata if any decryption failed
    if total_failed > 0:
        response_data["meta"] = {"failed_count": total_failed}

    return JSONResponse(status_code=200, content=success_response(response_data))
