"""
Gate 2 Risk Management Test Suite

Tests for Portfolio Heat Manager and Risk Manager (Circuit Breakers).
These tests validate Layer 2 of the ATLAS risk management framework.

Gate 2 Requirements:
- Portfolio heat never exceeds 8% (hard limit)
- Trades rejected when limit would be exceeded
- Heat recalculated correctly as positions close
- Drawdown circuit breakers trigger at correct thresholds

Test Coverage:
- PortfolioHeatManager: 10 tests
- RiskManager: 8 tests
- Integration: 1 test
Total: 19 tests
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.portfolio_heat import PortfolioHeatManager
from core.risk_manager import RiskManager


# =============================================================================
# PortfolioHeatManager Tests (10 tests)
# =============================================================================

class TestPortfolioHeatManager:
    """Test suite for PortfolioHeatManager class."""

    def test_single_position_under_limit_accepted(self):
        """
        Test: Single position under heat limit should be accepted.

        Given: Empty portfolio, 8% heat limit
        When: Add position with 5% risk
        Then: Position accepted (under 8% limit)
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        capital = 100000

        # 5% risk position
        accepted = heat_manager.can_accept_trade('SPY', 5000, capital)

        assert accepted is True
        assert heat_manager.calculate_current_heat(capital) == 0.0  # Not added yet

    def test_single_position_at_limit_accepted(self):
        """
        Test: Single position exactly at heat limit should be accepted.

        Given: Empty portfolio, 8% heat limit
        When: Add position with 8% risk
        Then: Position accepted (at limit, not over)
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        capital = 100000

        # 8% risk position (exactly at limit)
        accepted = heat_manager.can_accept_trade('SPY', 8000, capital)

        assert accepted is True

    def test_single_position_exceeding_limit_rejected(self):
        """
        Test: Single position exceeding heat limit should be rejected.

        Given: Empty portfolio, 8% heat limit
        When: Add position with 10% risk
        Then: Position rejected (exceeds 8% limit)
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        capital = 100000

        # 10% risk position (exceeds 8% limit)
        accepted = heat_manager.can_accept_trade('SPY', 10000, capital)

        assert accepted is False

    def test_multiple_positions_approaching_limit(self):
        """
        Test: Multiple positions should be accepted until heat limit reached.

        Given: Empty portfolio, 8% heat limit
        When: Add 3 positions (2% each = 6% total)
        Then: All 3 accepted, 4th position (2% more) rejected
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        capital = 100000

        # Add 3 positions at 2% risk each
        heat_manager.add_position('SPY', 2000)
        heat_manager.add_position('QQQ', 2000)
        heat_manager.add_position('IWM', 2000)

        # Current heat: 6%
        assert heat_manager.calculate_current_heat(capital) == 0.06

        # 4th position would push to 8% - should be accepted
        accepted_at_limit = heat_manager.can_accept_trade('DIA', 2000, capital)
        assert accepted_at_limit is True
        heat_manager.add_position('DIA', 2000)  # Actually add the position

        # 5th position would push to 10% - should be rejected
        accepted_over_limit = heat_manager.can_accept_trade('VTI', 2000, capital)
        assert accepted_over_limit is False

    def test_multiple_positions_exceeding_limit(self):
        """
        Test: Position that would exceed heat limit should be rejected.

        Given: Portfolio with 7% heat
        When: Attempt to add position with 2% risk (would be 9% total)
        Then: Position rejected
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        capital = 100000

        # Add positions totaling 7% risk
        heat_manager.add_position('SPY', 3000)
        heat_manager.add_position('QQQ', 2500)
        heat_manager.add_position('IWM', 1500)

        assert heat_manager.calculate_current_heat(capital) == 0.07

        # New position with 2% risk would push to 9%
        accepted = heat_manager.can_accept_trade('AAPL', 2000, capital)

        assert accepted is False

    def test_position_removal_updates_heat(self):
        """
        Test: Removing position should decrease portfolio heat.

        Given: Portfolio with 3 positions (6% heat)
        When: Remove 1 position (2% risk)
        Then: Heat reduces to 4%
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        capital = 100000

        # Add 3 positions
        heat_manager.add_position('SPY', 2000)
        heat_manager.add_position('QQQ', 2000)
        heat_manager.add_position('IWM', 2000)

        assert heat_manager.calculate_current_heat(capital) == 0.06

        # Remove one position
        heat_manager.remove_position('SPY')

        assert heat_manager.calculate_current_heat(capital) == 0.04
        assert heat_manager.get_position_count() == 2

    def test_position_risk_update_reduces_heat(self):
        """
        Test: Updating position risk (trailing stop) should reduce heat.

        Given: Position with $2,000 risk
        When: Trail stop reduces risk to $1,500
        Then: Portfolio heat decreases accordingly
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        capital = 100000

        # Add position with $2,000 risk
        heat_manager.add_position('AAPL', 2000)
        assert heat_manager.calculate_current_heat(capital) == 0.02

        # Trail stop reduces risk to $1,500
        heat_manager.update_position_risk('AAPL', 1500)

        assert heat_manager.calculate_current_heat(capital) == 0.015

    def test_heat_calculation_accuracy(self):
        """
        Test: Heat calculation should be sum(risks) / capital.

        Given: Various position sizes
        When: Calculate heat
        Then: Accurate percentage returned
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        capital = 100000

        # Add positions with varying risk
        heat_manager.add_position('SPY', 2500)  # 2.5%
        heat_manager.add_position('QQQ', 1750)  # 1.75%
        heat_manager.add_position('IWM', 3250)  # 3.25%

        # Total: $7,500 / $100,000 = 7.5%
        expected_heat = 7500 / 100000
        actual_heat = heat_manager.calculate_current_heat(capital)

        assert actual_heat == pytest.approx(expected_heat, abs=1e-6)
        assert actual_heat == 0.075

    def test_empty_portfolio_zero_heat(self):
        """
        Test: Empty portfolio should have 0% heat.

        Given: No positions
        When: Calculate heat
        Then: Return 0.0
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        capital = 100000

        heat = heat_manager.calculate_current_heat(capital)

        assert heat == 0.0
        assert heat_manager.get_position_count() == 0

    def test_zero_capital_handling(self):
        """
        Test: Zero or negative capital should return 0% heat.

        Given: Portfolio with positions
        When: Calculate heat with capital = 0
        Then: Return 0.0 (avoid division by zero)
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        heat_manager.add_position('SPY', 2000)

        # Zero capital
        heat_zero = heat_manager.calculate_current_heat(0)
        assert heat_zero == 0.0

        # Negative capital (edge case)
        heat_negative = heat_manager.calculate_current_heat(-100000)
        assert heat_negative == 0.0


# =============================================================================
# RiskManager Tests (8 tests)
# =============================================================================

class TestRiskManager:
    """Test suite for RiskManager class."""

    def test_drawdown_calculation_from_peak(self):
        """
        Test: Drawdown should be calculated as (peak - current) / peak.

        Given: Peak equity $100,000
        When: Current equity $85,000
        Then: Drawdown = 15%
        """
        risk_mgr = RiskManager()

        risk_mgr.update_equity(100000)  # Set peak
        assert risk_mgr.peak_equity == 100000

        risk_mgr.update_equity(85000)  # Drop to $85k
        drawdown = risk_mgr.calculate_drawdown()

        assert drawdown == pytest.approx(0.15, abs=1e-6)

    def test_warning_threshold_no_action(self):
        """
        Test: 10% drawdown should trigger WARNING only.

        Given: Peak equity $100,000
        When: Drawdown reaches 10%
        Then: No change to trading_enabled or risk_multiplier
        """
        risk_mgr = RiskManager()

        risk_mgr.update_equity(100000)  # Peak
        risk_mgr.update_equity(90000)   # 10% DD

        assert risk_mgr.trading_enabled is True
        assert risk_mgr.risk_multiplier == 1.0
        assert risk_mgr.calculate_drawdown() == pytest.approx(0.10, abs=1e-6)

    def test_reduce_size_threshold(self):
        """
        Test: 15% drawdown should reduce position sizes by 50%.

        Given: Peak equity $100,000
        When: Drawdown reaches 15%
        Then: risk_multiplier = 0.5, trading still enabled
        """
        risk_mgr = RiskManager()

        risk_mgr.update_equity(100000)  # Peak
        risk_mgr.update_equity(85000)   # 15% DD

        assert risk_mgr.trading_enabled is True
        assert risk_mgr.risk_multiplier == 0.5
        assert risk_mgr.calculate_drawdown() == pytest.approx(0.15, abs=1e-6)

    def test_stop_trading_threshold(self):
        """
        Test: 20% drawdown should halt trading.

        Given: Peak equity $100,000
        When: Drawdown reaches 20%
        Then: trading_enabled = False, risk_multiplier = 0.0
        """
        risk_mgr = RiskManager()

        risk_mgr.update_equity(100000)  # Peak
        risk_mgr.update_equity(80000)   # 20% DD

        assert risk_mgr.trading_enabled is False
        assert risk_mgr.risk_multiplier == 0.0
        assert risk_mgr.calculate_drawdown() == pytest.approx(0.20, abs=1e-6)

    def test_recovery_from_drawdown(self):
        """
        Test: Recovering from drawdown should reset to normal operations.

        Given: 15% drawdown (reduced size)
        When: Equity recovers to within 10% of peak
        Then: risk_multiplier = 1.0, trading enabled
        """
        risk_mgr = RiskManager()

        risk_mgr.update_equity(100000)  # Peak
        risk_mgr.update_equity(85000)   # 15% DD (reduced size)

        assert risk_mgr.risk_multiplier == 0.5

        # Recover to 95k (5% DD)
        risk_mgr.update_equity(95000)

        assert risk_mgr.trading_enabled is True
        assert risk_mgr.risk_multiplier == 1.0

    def test_peak_equity_tracking(self):
        """
        Test: Peak equity should update on new highs.

        Given: Peak equity $100,000
        When: Equity rises to $110,000
        Then: Peak updates to $110,000
        """
        risk_mgr = RiskManager()

        risk_mgr.update_equity(100000)
        assert risk_mgr.peak_equity == 100000

        risk_mgr.update_equity(110000)
        assert risk_mgr.peak_equity == 110000

        risk_mgr.update_equity(105000)
        assert risk_mgr.peak_equity == 110000  # Peak unchanged

    def test_position_size_validation_exceeds_capital(self):
        """
        Test: Position size exceeding 100% of capital should be rejected.

        Given: Capital $100,000
        When: Position value $150,000 (150%)
        Then: Validation fails
        """
        risk_mgr = RiskManager()

        # Position: 300 shares at $500 = $150,000 (150% of capital)
        valid = risk_mgr.validate_position_size(
            position_size=300,
            price=500,
            capital=100000
        )

        assert valid is False

    def test_position_size_validation_large_warning(self, capsys):
        """
        Test: Position size > 50% should print warning but still validate.

        Given: Capital $100,000
        When: Position value $60,000 (60%)
        Then: Validation passes with warning
        """
        risk_mgr = RiskManager()

        # Position: 120 shares at $500 = $60,000 (60% of capital)
        valid = risk_mgr.validate_position_size(
            position_size=120,
            price=500,
            capital=100000
        )

        assert valid is True

        # Check warning was printed
        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "60" in captured.out or "0.6" in captured.out


# =============================================================================
# Integration Test (1 test)
# =============================================================================

class TestIntegration:
    """Integration tests combining heat and drawdown management."""

    def test_combined_heat_and_drawdown_scenario(self):
        """
        Test: Combined heat + drawdown scenario.

        Scenario:
        1. Start with $100k capital
        2. Add 3 positions (6% heat)
        3. Drawdown to 15% (reduce size)
        4. Attempt to add 4th position with reduced risk
        5. Validate all constraints enforced
        """
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        risk_mgr = RiskManager()

        capital = 100000

        # Initial equity
        risk_mgr.update_equity(capital)

        # Add 3 positions (2% risk each)
        heat_manager.add_position('SPY', 2000)
        heat_manager.add_position('QQQ', 2000)
        heat_manager.add_position('IWM', 2000)

        assert heat_manager.calculate_current_heat(capital) == 0.06

        # Simulate drawdown to $85k (15% DD)
        risk_mgr.update_equity(85000)

        assert risk_mgr.risk_multiplier == 0.5
        assert risk_mgr.trading_enabled is True

        # Attempt to add 4th position
        # Base risk: 2% ($2,000)
        # Adjusted risk: 1% ($1,000) due to risk_multiplier
        base_risk = 2000
        adjusted_risk = risk_mgr.get_adjusted_risk(base_risk / capital) * capital

        assert adjusted_risk == 1000  # 50% of base risk

        # Check if position would be accepted
        # Current heat: 6%, New risk: 1%, Total: 7% (under 8% limit)
        accepted = heat_manager.can_accept_trade('AAPL', adjusted_risk, capital)

        assert accepted is True


# =============================================================================
# Test Execution Summary
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
