"""Unit tests for the Investment Optimizer (Greedy Allocation Algorithm).

Tests cover core functionality:
- Basic greedy allocation with single and multiple instruments
- Tiered rate resolution
- Risk and liquidity filtering
- Min/max investment constraints
- Max instruments limit
- Capital conservation invariant
- Insufficient capital handling
"""

import pytest

from backend.services.optimizer import (
    AllocationResult,
    InstrumentData,
    Optimizer,
    OptimizerOutput,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def make_instrument(
    *,
    id: str = "inst-1",
    name: str = "Test Instrument",
    annual_rate: float = 10.0,
    min_investment: float = 100.0,
    max_investment: float | None = None,
    risk_level: str = "low",
    liquidity_tier: str = "immediate",
    tiered_rates: list[dict] | None = None,
) -> InstrumentData:
    """Helper to create InstrumentData with sensible defaults."""
    return InstrumentData(
        id=id,
        name=name,
        annual_rate=annual_rate,
        min_investment=min_investment,
        max_investment=max_investment,
        risk_level=risk_level,
        liquidity_tier=liquidity_tier,
        tiered_rates=tiered_rates,
    )


# ---------------------------------------------------------------------------
# Tests: Basic allocation
# ---------------------------------------------------------------------------


class TestBasicAllocation:
    """Test basic greedy allocation behavior."""

    def test_single_instrument_full_allocation(self):
        """All capital allocated to a single instrument when no max."""
        instruments = [make_instrument(annual_rate=12.0)]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=10000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        assert len(result.allocations) == 1
        assert result.allocations[0].allocated_amount == 10000.0
        assert result.allocations[0].effective_rate == 12.0
        assert result.allocations[0].projected_annual_return == 1200.0
        assert result.unallocated_capital == 0.0
        assert result.total_expected_return == 1200.0

    def test_multiple_instruments_sorted_by_rate(self):
        """Higher-rate instruments get allocated first."""
        instruments = [
            make_instrument(id="low-rate", name="Low Rate", annual_rate=5.0, max_investment=5000.0),
            make_instrument(id="high-rate", name="High Rate", annual_rate=15.0, max_investment=5000.0),
            make_instrument(id="mid-rate", name="Mid Rate", annual_rate=10.0, max_investment=5000.0),
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=12000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=10,
        )
        # High Rate (15%) gets 5000, Mid Rate (10%) gets 5000, Low Rate (5%) gets 2000
        assert len(result.allocations) == 3
        assert result.allocations[0].instrument_name == "High Rate"
        assert result.allocations[0].allocated_amount == 5000.0
        assert result.allocations[1].instrument_name == "Mid Rate"
        assert result.allocations[1].allocated_amount == 5000.0
        assert result.allocations[2].instrument_name == "Low Rate"
        assert result.allocations[2].allocated_amount == 2000.0
        assert result.unallocated_capital == 0.0

    def test_capital_conservation(self):
        """Total allocated + unallocated equals original capital."""
        instruments = [
            make_instrument(id="a", annual_rate=10.0, max_investment=3000.0),
            make_instrument(id="b", annual_rate=8.0, max_investment=3000.0),
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=10000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=2,
        )
        total_allocated = sum(a.allocated_amount for a in result.allocations)
        assert total_allocated + result.unallocated_capital == 10000.0


# ---------------------------------------------------------------------------
# Tests: Constraints
# ---------------------------------------------------------------------------


class TestConstraints:
    """Test min/max investment and max instruments constraints."""

    def test_respects_min_investment(self):
        """Skip instruments where remaining capital < min_investment."""
        instruments = [
            make_instrument(id="expensive", name="Expensive", annual_rate=20.0, min_investment=5000.0),
            make_instrument(id="cheap", name="Cheap", annual_rate=10.0, min_investment=100.0),
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=1000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        # Only "Cheap" should be allocated because capital < expensive's min
        assert len(result.allocations) == 1
        assert result.allocations[0].instrument_name == "Cheap"
        assert result.allocations[0].allocated_amount == 1000.0

    def test_respects_max_investment(self):
        """Allocation capped at max_investment per instrument."""
        instruments = [
            make_instrument(id="capped", annual_rate=15.0, max_investment=2000.0),
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=5000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        assert result.allocations[0].allocated_amount == 2000.0
        assert result.unallocated_capital == 3000.0

    def test_respects_max_instruments_limit(self):
        """Stop allocating after max_instruments reached."""
        instruments = [
            make_instrument(id=f"inst-{i}", name=f"Inst {i}", annual_rate=float(20 - i), max_investment=10000.0)
            for i in range(10)
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=100000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=3,
        )
        assert len(result.allocations) == 3

    def test_max_instruments_clamped_to_10(self):
        """max_instruments is clamped to 10 even if higher value passed."""
        instruments = [
            make_instrument(id=f"inst-{i}", name=f"Inst {i}", annual_rate=float(20 - i), max_investment=1000.0)
            for i in range(15)
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=100000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=15,
        )
        assert len(result.allocations) <= 10


# ---------------------------------------------------------------------------
# Tests: Filtering
# ---------------------------------------------------------------------------


class TestFiltering:
    """Test risk and liquidity filtering."""

    def test_filters_by_risk_tolerance(self):
        """Instruments with higher risk than tolerance are excluded."""
        instruments = [
            make_instrument(id="low-risk", annual_rate=8.0, risk_level="low"),
            make_instrument(id="med-risk", annual_rate=12.0, risk_level="medium"),
            make_instrument(id="high-risk", annual_rate=18.0, risk_level="high"),
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=10000.0,
            risk_tolerance="low",
            liquidity_preference="flexible",
            max_instruments=10,
        )
        # Only low-risk should be included
        assert len(result.allocations) == 1
        assert result.allocations[0].instrument_id == "low-risk"

    def test_filters_by_liquidity_preference_immediate(self):
        """Only immediate liquidity instruments when preference is 'immediate'."""
        instruments = [
            make_instrument(id="liquid", annual_rate=8.0, liquidity_tier="immediate"),
            make_instrument(id="1day", annual_rate=12.0, liquidity_tier="1-day"),
            make_instrument(id="28day", annual_rate=15.0, liquidity_tier="28-day"),
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=10000.0,
            risk_tolerance="high",
            liquidity_preference="immediate",
            max_instruments=10,
        )
        assert len(result.allocations) == 1
        assert result.allocations[0].instrument_id == "liquid"

    def test_filters_by_liquidity_preference_short_term(self):
        """Immediate + 1-day liquidity when preference is 'short-term'."""
        instruments = [
            make_instrument(id="liquid", name="Liquid", annual_rate=8.0, liquidity_tier="immediate", max_investment=5000.0),
            make_instrument(id="1day", name="1-Day", annual_rate=12.0, liquidity_tier="1-day", max_investment=5000.0),
            make_instrument(id="28day", name="28-Day", annual_rate=15.0, liquidity_tier="28-day", max_investment=5000.0),
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=10000.0,
            risk_tolerance="high",
            liquidity_preference="short-term",
            max_instruments=10,
        )
        assert len(result.allocations) == 2
        ids = [a.instrument_id for a in result.allocations]
        assert "liquid" in ids
        assert "1day" in ids
        assert "28day" not in ids

    def test_filters_by_liquidity_preference_flexible(self):
        """All tiers accepted when preference is 'flexible'."""
        instruments = [
            make_instrument(id="liquid", name="Liquid", annual_rate=8.0, liquidity_tier="immediate", max_investment=25000.0),
            make_instrument(id="1day", name="1-Day", annual_rate=12.0, liquidity_tier="1-day", max_investment=25000.0),
            make_instrument(id="28day", name="28-Day", annual_rate=15.0, liquidity_tier="28-day", max_investment=25000.0),
            make_instrument(id="custom", name="Custom", annual_rate=18.0, liquidity_tier="custom", max_investment=25000.0),
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=100000.0,
            risk_tolerance="high",
            liquidity_preference="flexible",
            max_instruments=10,
        )
        assert len(result.allocations) == 4


# ---------------------------------------------------------------------------
# Tests: Tiered rates
# ---------------------------------------------------------------------------


class TestTieredRates:
    """Test tiered rate resolution."""

    def test_tiered_rate_applies_correct_tier(self):
        """Rate should correspond to the tier containing the allocated amount."""
        instruments = [
            make_instrument(
                id="tiered",
                name="Nu México",
                annual_rate=15.5,
                min_investment=1.0,
                tiered_rates=[
                    {"min_amount": 0, "max_amount": 50000, "rate": 15.5},
                    {"min_amount": 50000.01, "max_amount": 200000, "rate": 14.5},
                    {"min_amount": 200000.01, "max_amount": 1000000, "rate": 13.0},
                ],
            )
        ]
        optimizer = Optimizer(instruments)

        # Allocate 30,000 → should get 15.5% tier
        result = optimizer.allocate(
            total_capital=30000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        assert result.allocations[0].effective_rate == 15.5
        assert result.allocations[0].projected_annual_return == 30000.0 * 15.5 / 100

    def test_tiered_rate_higher_tier(self):
        """Larger amount falls into a lower-rate tier."""
        instruments = [
            make_instrument(
                id="tiered",
                name="Nu México",
                annual_rate=15.5,
                min_investment=1.0,
                tiered_rates=[
                    {"min_amount": 0, "max_amount": 50000, "rate": 15.5},
                    {"min_amount": 50000.01, "max_amount": 200000, "rate": 14.5},
                ],
            )
        ]
        optimizer = Optimizer(instruments)

        # Allocate 100,000 → should get 14.5% tier
        result = optimizer.allocate(
            total_capital=100000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        assert result.allocations[0].effective_rate == 14.5

    def test_no_tiered_rates_uses_base_rate(self):
        """When tiered_rates is None, base annual_rate is used."""
        instruments = [
            make_instrument(id="flat", annual_rate=11.0, tiered_rates=None)
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=5000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        assert result.allocations[0].effective_rate == 11.0


# ---------------------------------------------------------------------------
# Tests: Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_zero_capital(self):
        """Zero capital returns empty allocations with message."""
        instruments = [make_instrument()]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=0.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        assert len(result.allocations) == 0
        assert result.message is not None

    def test_negative_capital(self):
        """Negative capital returns empty allocations with message."""
        instruments = [make_instrument()]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=-1000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        assert len(result.allocations) == 0
        assert result.message is not None

    def test_no_instruments(self):
        """Empty instrument list returns empty allocations with message."""
        optimizer = Optimizer([])
        result = optimizer.allocate(
            total_capital=10000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        assert len(result.allocations) == 0
        assert result.message is not None

    def test_all_instruments_filtered_out(self):
        """All instruments filtered leaves empty allocation with message."""
        instruments = [
            make_instrument(id="risky", annual_rate=20.0, risk_level="high"),
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=10000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        assert len(result.allocations) == 0
        assert result.unallocated_capital == 10000.0
        assert result.message is not None

    def test_capital_less_than_all_min_investments(self):
        """Capital below all min_investment thresholds returns empty with message."""
        instruments = [
            make_instrument(id="a", min_investment=5000.0, annual_rate=10.0),
            make_instrument(id="b", min_investment=10000.0, annual_rate=15.0),
        ]
        optimizer = Optimizer(instruments)
        result = optimizer.allocate(
            total_capital=1000.0,
            risk_tolerance="low",
            liquidity_preference="immediate",
            max_instruments=5,
        )
        assert len(result.allocations) == 0
        assert result.unallocated_capital == 1000.0
        assert result.message is not None
