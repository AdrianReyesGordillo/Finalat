"""Investment Optimizer — Greedy Allocation Algorithm.

Distributes investment capital across financial instruments using a greedy
strategy sorted by effective annual rate (descending). Respects per-instrument
min/max constraints, tiered rate structures, risk tolerance, and liquidity
preferences.

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ---------------------------------------------------------------------------
# Liquidity tier ordering (lower index = more liquid)
# ---------------------------------------------------------------------------

LIQUIDITY_ORDER: dict[str, int] = {
    "immediate": 0,
    "1-day": 1,
    "28-day": 2,
    "custom": 3,
}

# Mapping from user's liquidity preference to the maximum tier they accept
LIQUIDITY_PREFERENCE_MAX: dict[str, int] = {
    "immediate": 0,   # only immediate
    "short-term": 1,  # immediate + 1-day
    "flexible": 3,    # all tiers accepted
}

# Risk level ordering (lower index = less risky)
RISK_ORDER: dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class InstrumentData:
    """Represents a financial instrument available for allocation.

    Attributes:
        id: Unique identifier for the instrument.
        name: Human-readable instrument name.
        annual_rate: Base annual rate (percentage). Used when tiered_rates is None.
        min_investment: Minimum amount that can be invested.
        max_investment: Maximum amount that can be invested (None = unlimited).
        risk_level: Risk category ('low', 'medium', 'high').
        liquidity_tier: Liquidity category ('immediate', '1-day', '28-day', 'custom').
        tiered_rates: Optional list of rate tiers, each with min_amount, max_amount, rate.
    """

    id: str
    name: str
    annual_rate: float
    min_investment: float
    max_investment: float | None
    risk_level: str
    liquidity_tier: str
    tiered_rates: list[dict] | None = None

    def get_rate_for_amount(self, amount: float) -> float:
        """Get the effective annual rate for a given investment amount.

        If tiered_rates are defined, returns the rate for the tier that
        contains the given amount. Falls back to the base annual_rate
        if no tier matches or tiered_rates is not defined.

        Args:
            amount: The investment amount to look up.

        Returns:
            The effective annual rate as a percentage.
        """
        if not self.tiered_rates:
            return self.annual_rate

        for tier in self.tiered_rates:
            tier_min = tier.get("min_amount", 0)
            tier_max = tier.get("max_amount", float("inf"))
            if tier_min <= amount <= tier_max:
                return float(tier.get("rate", self.annual_rate))

        # If no tier matches (amount exceeds all tiers), use the last tier's rate
        # or fall back to base rate
        if self.tiered_rates:
            return float(self.tiered_rates[-1].get("rate", self.annual_rate))
        return self.annual_rate


@dataclass
class AllocationResult:
    """A single allocation recommendation.

    Attributes:
        instrument_id: Unique ID of the instrument.
        instrument_name: Human-readable name.
        allocated_amount: Amount allocated to this instrument.
        effective_rate: The annual rate applied (accounting for tiers).
        projected_annual_return: Expected yearly return (amount * rate / 100).
    """

    instrument_id: str
    instrument_name: str
    allocated_amount: float
    effective_rate: float
    projected_annual_return: float


@dataclass
class OptimizerOutput:
    """Complete optimizer result.

    Attributes:
        allocations: List of individual allocation recommendations.
        total_expected_return: Sum of all projected annual returns.
        unallocated_capital: Capital remaining after all allocations.
        message: Optional informational message (e.g., insufficient capital).
    """

    allocations: list[AllocationResult] = field(default_factory=list)
    total_expected_return: float = 0.0
    unallocated_capital: float = 0.0
    message: str | None = None


# ---------------------------------------------------------------------------
# Optimizer class
# ---------------------------------------------------------------------------


class Optimizer:
    """Greedy investment allocation optimizer.

    Distributes capital across instruments sorted by effective annual rate
    (descending), respecting constraints on risk, liquidity, min/max
    investment, and maximum number of instruments.

    Args:
        instruments: List of available instruments for allocation.
    """

    def __init__(self, instruments: list[InstrumentData]) -> None:
        self._instruments = instruments

    def allocate(
        self,
        total_capital: float,
        risk_tolerance: Literal["low", "medium", "high"],
        liquidity_preference: Literal["immediate", "short-term", "flexible"],
        max_instruments: int,
    ) -> OptimizerOutput:
        """Run the greedy allocation algorithm.

        Process:
        1. Filter instruments by risk tolerance and liquidity preference.
        2. Sort eligible instruments by effective rate (descending).
        3. Greedily allocate capital to highest-rate instruments first.
        4. Respect min_investment (skip if insufficient), max_investment (cap).
        5. Stop when capital exhausted or max_instruments reached.

        Args:
            total_capital: Total amount of capital to allocate (positive number).
            risk_tolerance: Maximum risk level the user accepts.
            liquidity_preference: Minimum liquidity the user requires.
            max_instruments: Maximum number of instruments to allocate to (1-10).

        Returns:
            OptimizerOutput with allocations, total return, and unallocated capital.
        """
        if total_capital <= 0:
            return OptimizerOutput(
                unallocated_capital=total_capital,
                message="Capital must be a positive number.",
            )

        max_instruments = max(1, min(max_instruments, 10))

        # Step 1: Filter by risk and liquidity
        eligible = self._filter_instruments(risk_tolerance, liquidity_preference)

        # Step 2: Sort by effective rate descending
        # Use rate for a notional amount (min_investment) to sort
        eligible.sort(
            key=lambda i: i.get_rate_for_amount(i.min_investment),
            reverse=True,
        )

        # Step 3: Greedy allocation
        remaining = total_capital
        allocations: list[AllocationResult] = []
        instruments_used = 0

        for instrument in eligible:
            if instruments_used >= max_instruments:
                break

            if remaining < instrument.min_investment:
                continue

            # Determine allocation amount: min of remaining and max_investment
            if instrument.max_investment is not None:
                alloc_amount = min(remaining, instrument.max_investment)
            else:
                alloc_amount = remaining

            # Ensure we don't allocate below min_investment
            if alloc_amount < instrument.min_investment:
                continue

            # Get the effective rate for this allocation amount
            rate = instrument.get_rate_for_amount(alloc_amount)

            # Calculate projected annual return
            projected_return = alloc_amount * (rate / 100.0)

            allocations.append(
                AllocationResult(
                    instrument_id=instrument.id,
                    instrument_name=instrument.name,
                    allocated_amount=round(alloc_amount, 2),
                    effective_rate=round(rate, 4),
                    projected_annual_return=round(projected_return, 2),
                )
            )

            remaining -= alloc_amount
            instruments_used += 1

            if remaining <= 0:
                remaining = 0.0
                break

        total_return = sum(a.projected_annual_return for a in allocations)

        message = None
        if not allocations:
            message = "Insufficient capital for available instruments after applying filters."

        return OptimizerOutput(
            allocations=allocations,
            total_expected_return=round(total_return, 2),
            unallocated_capital=round(remaining, 2),
            message=message,
        )

    def _filter_instruments(
        self,
        risk_tolerance: str,
        liquidity_preference: str,
    ) -> list[InstrumentData]:
        """Filter instruments by risk and liquidity constraints.

        - Risk: exclude instruments with risk_level exceeding the user's tolerance.
        - Liquidity: exclude instruments with liquidity_tier below the user's preference
          (i.e., less liquid than the user requires).

        Args:
            risk_tolerance: Maximum acceptable risk ('low', 'medium', 'high').
            liquidity_preference: Minimum required liquidity
                ('immediate', 'short-term', 'flexible').

        Returns:
            List of instruments passing both filters.
        """
        max_risk = RISK_ORDER.get(risk_tolerance, 2)
        max_liquidity_tier = LIQUIDITY_PREFERENCE_MAX.get(liquidity_preference, 3)

        eligible: list[InstrumentData] = []
        for instrument in self._instruments:
            # Check risk: instrument risk must not exceed user's tolerance
            inst_risk = RISK_ORDER.get(instrument.risk_level, 2)
            if inst_risk > max_risk:
                continue

            # Check liquidity: instrument's liquidity tier must be within user's
            # accepted range (lower index = more liquid = better)
            inst_liquidity = LIQUIDITY_ORDER.get(instrument.liquidity_tier, 3)
            if inst_liquidity > max_liquidity_tier:
                continue

            eligible.append(instrument)

        return eligible
