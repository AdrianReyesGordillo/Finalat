"""Optimizer router — POST /api/optimizer endpoint.

Accepts investment parameters and returns an optimized allocation plan
using the greedy allocation algorithm.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8
"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.instruments import Instrument
from backend.services.optimizer import (
    AllocationResult,
    InstrumentData,
    Optimizer,
    OptimizerOutput,
)
from backend.utils.response import error_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class OptimizerRequest(BaseModel):
    """Request body for the optimizer endpoint."""

    available_capital: float = Field(
        ...,
        gt=0,
        description="Total capital to invest (positive number).",
    )
    risk_tolerance: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Maximum risk level the user accepts.",
    )
    liquidity_preference: Literal["immediate", "short-term", "flexible"] = Field(
        default="flexible",
        description="Minimum liquidity requirement.",
    )
    max_instruments: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of instruments to allocate to (1-10).",
    )


class AllocationItem(BaseModel):
    """Single allocation in the response."""

    instrument_id: str
    instrument_name: str
    allocated_amount: float
    effective_rate: float
    projected_annual_return: float


class OptimizerResponse(BaseModel):
    """Response body for the optimizer endpoint."""

    allocations: list[AllocationItem]
    total_expected_return: float
    unallocated_capital: float
    message: str | None = None


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_current_user_id(request: Request) -> str:
    """Extract user_id from request.state (set by auth middleware)."""
    return request.state.user_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _instrument_model_to_data(inst: Instrument) -> InstrumentData:
    """Convert an SQLAlchemy Instrument model to an InstrumentData dataclass."""
    return InstrumentData(
        id=inst.id,
        name=inst.name,
        annual_rate=float(inst.annual_rate),
        min_investment=float(inst.min_investment),
        max_investment=float(inst.max_investment) if inst.max_investment is not None else None,
        risk_level=inst.risk_level,
        liquidity_tier=inst.liquidity_tier,
        tiered_rates=inst.tiered_rates,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("")
async def optimize_allocation(
    body: OptimizerRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Generate an optimized investment allocation plan.

    Fetches available instruments from the database, applies the greedy
    allocation algorithm with the user's preferences, and returns the
    recommended allocation plan.
    """
    # Fetch instruments with successful status from DB
    stmt = select(Instrument).where(Instrument.last_fetch_status == "success")
    result = await db.execute(stmt)
    instruments = result.scalars().all()

    if not instruments:
        return JSONResponse(
            status_code=200,
            content=success_response(
                OptimizerResponse(
                    allocations=[],
                    total_expected_return=0.0,
                    unallocated_capital=body.available_capital,
                    message="No instruments available for allocation.",
                ).model_dump()
            ),
        )

    # Convert DB models to optimizer data objects
    instrument_data = [_instrument_model_to_data(inst) for inst in instruments]

    # Run optimizer
    optimizer = Optimizer(instrument_data)
    output: OptimizerOutput = optimizer.allocate(
        total_capital=body.available_capital,
        risk_tolerance=body.risk_tolerance,
        liquidity_preference=body.liquidity_preference,
        max_instruments=body.max_instruments,
    )

    # Build response
    response = OptimizerResponse(
        allocations=[
            AllocationItem(
                instrument_id=a.instrument_id,
                instrument_name=a.instrument_name,
                allocated_amount=a.allocated_amount,
                effective_rate=a.effective_rate,
                projected_annual_return=a.projected_annual_return,
            )
            for a in output.allocations
        ],
        total_expected_return=output.total_expected_return,
        unallocated_capital=output.unallocated_capital,
        message=output.message,
    )

    return JSONResponse(
        status_code=200,
        content=success_response(response.model_dump()),
    )
