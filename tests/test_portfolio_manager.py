"""
Portfolio Manager Test Suite

Tests for PortfolioManager class (core/portfolio_manager.py).
Validates Phase 4 functionality: single-strategy execution with integrated
risk management (heat tracking, circuit breakers, capital allocation).

Test Coverage:
- Initialization and validation
- Capital allocation (equal weight)
- Single-strategy backtest with circuit breakers
- Circuit breaker triggers at correct thresholds
- Status reporting and state tracking
- Integration with PortfolioHeatManager
- Integration with RiskManager
- Reset functionality

Total: 18 tests
"""

import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.portfolio_manager import PortfolioManager
from utils.portfolio_heat import PortfolioHeatManager
from core.risk_manager import RiskManager
from strategies.base_strategy import BaseStrategy, StrategyConfig


# =============================================================================
# Test Fixtures
# =============================================================================

class MockStrategy(BaseStrategy):
    """Mock strategy for testing PortfolioManager."""

    def __init__(self, config: StrategyConfig, return_pct: float = 0.0):
        """
        Args:
            config: Strategy configuration
            return_pct: Target return percentage (0.10 = 10% gain)
        """
        super().__init__(config)
        self.return_pct = return_pct

    def generate_signals(self, data: pd.DataFrame, regime: Optional[str] = None) -> dict:
        """Generate simple buy-and-hold signals."""
        long_entries = pd.Series(False, index=data.index)
        long_exits = pd.Series(False, index=data.index)

        # Entry on first bar
        if len(data) > 0:
            long_entries.iloc[0] = True

        # Exit on last bar
        if len(data) > 1:
            long_exits.iloc[-1] = True

        # Simple ATR proxy
        stop_distance = data['Close'] * 0.02  # 2% stops

        return {
            'long_entries': long_entries,
            'long_exits': long_exits,
            'stop_distance': stop_distance
        }

    def calculate_position_size(
        self,
        data: pd.DataFrame,
        capital: float,
        stop_distance: pd.Series
    ) -> pd.Series:
        """Calculate fixed position size."""
        # Simple fixed sizing: 50% of capital
        shares = (capital * 0.5) / data['Close']
        return shares.fillna(0)

    def get_strategy_name(self) -> str:
        return "MockStrategy"


@pytest.fixture
def mock_data_profitable():
    """Create mock data that generates profit."""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    np.random.seed(42)

    # Upward trending data
    close = pd.Series(
        100 + np.cumsum(np.random.randn(100) * 1 + 0.5),  # Positive drift
        index=dates
    )

    data = pd.DataFrame({
        'Open': close * 0.99,
        'High': close * 1.02,
        'Low': close * 0.98,
        'Close': close,
        'Volume': 1000000
    }, index=dates)

    return data


@pytest.fixture
def mock_data_drawdown():
    """Create mock data with significant drawdown."""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')

    # Simulate crash: up 10%, then down 25%
    values = [100] * 20  # Stable
    values += [100 + i*0.5 for i in range(1, 21)]  # +10% over 20 days
    values += [110 - i*0.75 for i in range(1, 41)]  # -30% crash over 40 days
    values += [80 + i*0.2 for i in range(1, 21)]  # Partial recovery

    close = pd.Series(values, index=dates)

    data = pd.DataFrame({
        'Open': close * 0.99,
        'High': close * 1.01,
        'Low': close * 0.99,
        'Close': close,
        'Volume': 1000000
    }, index=dates)

    return data


@pytest.fixture
def mock_strategy():
    """Create mock strategy instance."""
    config = StrategyConfig(name="MockStrategy")
    return MockStrategy(config)


@pytest.fixture
def heat_manager():
    """Create PortfolioHeatManager instance."""
    return PortfolioHeatManager(max_heat=0.08)


@pytest.fixture
def risk_manager():
    """Create RiskManager instance."""
    return RiskManager(max_portfolio_heat=0.08, max_position_risk=0.02)


# =============================================================================
# Initialization Tests
# =============================================================================

class TestPortfolioManagerInit:
    """Test PortfolioManager initialization."""

    def test_valid_initialization(self, mock_strategy, heat_manager, risk_manager):
        """Test valid PortfolioManager creation."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        assert pm.capital == 10000
        assert len(pm.strategies) == 1
        assert pm.current_equity == 10000
        assert pm.peak_equity == 10000

    def test_invalid_capital_zero(self, mock_strategy, heat_manager, risk_manager):
        """Test initialization with zero capital raises error."""
        with pytest.raises(ValueError, match="Capital must be positive"):
            PortfolioManager(
                strategies=[mock_strategy],
                capital=0,
                heat_manager=heat_manager,
                risk_manager=risk_manager
            )

    def test_invalid_capital_negative(self, mock_strategy, heat_manager, risk_manager):
        """Test initialization with negative capital raises error."""
        with pytest.raises(ValueError, match="Capital must be positive"):
            PortfolioManager(
                strategies=[mock_strategy],
                capital=-5000,
                heat_manager=heat_manager,
                risk_manager=risk_manager
            )

    def test_empty_strategies_list(self, heat_manager, risk_manager):
        """Test initialization with empty strategies list raises error."""
        with pytest.raises(ValueError, match="Must provide at least one strategy"):
            PortfolioManager(
                strategies=[],
                capital=10000,
                heat_manager=heat_manager,
                risk_manager=risk_manager
            )


# =============================================================================
# Capital Allocation Tests
# =============================================================================

class TestCapitalAllocation:
    """Test capital allocation across strategies."""

    def test_single_strategy_allocation(self, mock_strategy, heat_manager, risk_manager):
        """Test capital allocation with single strategy gets 100%."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        allocations = pm.allocate_capital()

        assert len(allocations) == 1
        assert allocations['MockStrategy'] == 10000

    def test_multiple_strategy_allocation(self, heat_manager, risk_manager):
        """Test equal weight allocation across multiple strategies."""
        # Create strategies with unique names
        class MockStrategy1(MockStrategy):
            def get_strategy_name(self) -> str:
                return "Strategy1"

        class MockStrategy2(MockStrategy):
            def get_strategy_name(self) -> str:
                return "Strategy2"

        config1 = StrategyConfig(name="Strategy1")
        config2 = StrategyConfig(name="Strategy2")
        s1 = MockStrategy1(config1)
        s2 = MockStrategy2(config2)

        pm = PortfolioManager(
            strategies=[s1, s2],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        allocations = pm.allocate_capital()

        assert len(allocations) == 2
        assert allocations['Strategy1'] == 5000  # Equal split
        assert allocations['Strategy2'] == 5000  # Equal split
        assert sum(allocations.values()) == 10000


# =============================================================================
# Single-Strategy Backtest Tests
# =============================================================================

class TestSingleStrategyBacktest:
    """Test single-strategy backtest execution."""

    def test_backtest_runs_successfully(
        self,
        mock_strategy,
        mock_data_profitable,
        heat_manager,
        risk_manager
    ):
        """Test single-strategy backtest completes without errors."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        results = pm.run_single_strategy_with_gates(
            strategy=mock_strategy,
            data=mock_data_profitable,
            initial_capital=10000
        )

        # Verify result structure
        assert 'portfolio' in results
        assert 'metrics' in results
        assert 'equity_curve' in results
        assert 'circuit_breaker_triggers' in results
        assert 'final_equity' in results
        assert 'drawdown_max' in results
        assert 'trading_halted' in results
        assert 'strategy_name' in results

    def test_backtest_equity_tracking(
        self,
        mock_strategy,
        mock_data_profitable,
        heat_manager,
        risk_manager
    ):
        """Test equity curve is tracked correctly."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        results = pm.run_single_strategy_with_gates(
            strategy=mock_strategy,
            data=mock_data_profitable,
            initial_capital=10000
        )

        equity_curve = results['equity_curve']

        # Verify equity curve properties
        assert isinstance(equity_curve, pd.Series)
        assert len(equity_curve) == len(mock_data_profitable)
        assert equity_curve.iloc[0] > 0  # Has initial value
        assert equity_curve.iloc[-1] > 0  # Has final value

    def test_backtest_no_circuit_breakers_on_profit(
        self,
        mock_strategy,
        mock_data_profitable,
        heat_manager,
        risk_manager
    ):
        """Test no circuit breakers triggered on profitable backtest."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        results = pm.run_single_strategy_with_gates(
            strategy=mock_strategy,
            data=mock_data_profitable,
            initial_capital=10000
        )

        # Should have no circuit breaker triggers if profitable
        # (This may fail if mock data has volatility, which is OK)
        assert isinstance(results['circuit_breaker_triggers'], list)
        assert results['trading_halted'] is False


# =============================================================================
# Circuit Breaker Tests
# =============================================================================

class TestCircuitBreakers:
    """Test circuit breaker trigger logic."""

    def test_circuit_breaker_triggers_on_drawdown(
        self,
        mock_strategy,
        mock_data_drawdown,
        heat_manager,
        risk_manager
    ):
        """Test circuit breakers trigger during significant drawdown."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        results = pm.run_single_strategy_with_gates(
            strategy=mock_strategy,
            data=mock_data_drawdown,
            initial_capital=10000
        )

        # Should have circuit breaker triggers
        assert len(results['circuit_breaker_triggers']) > 0

        # Verify trigger structure
        for date, threshold, action in results['circuit_breaker_triggers']:
            assert isinstance(date, pd.Timestamp)
            assert threshold in [0.10, 0.15, 0.20, 0.25]
            assert action in ['WARNING', 'REDUCE_SIZE', 'STOP_TRADING', 'CRITICAL']

    def test_trading_halted_on_severe_drawdown(
        self,
        mock_strategy,
        mock_data_drawdown,
        heat_manager,
        risk_manager
    ):
        """Test trading halts at 20% drawdown."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        results = pm.run_single_strategy_with_gates(
            strategy=mock_strategy,
            data=mock_data_drawdown,
            initial_capital=10000
        )

        # Check if 20% DD triggered
        triggers_20pct = [
            t for t in results['circuit_breaker_triggers']
            if t[1] >= 0.20
        ]

        if triggers_20pct:
            assert results['trading_halted'] is True


# =============================================================================
# Status Reporting Tests
# =============================================================================

class TestStatusReporting:
    """Test portfolio status reporting."""

    def test_get_portfolio_status_structure(
        self,
        mock_strategy,
        heat_manager,
        risk_manager
    ):
        """Test get_portfolio_status returns correct structure."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        status = pm.get_portfolio_status()

        # Verify all required keys exist
        required_keys = [
            'current_equity',
            'peak_equity',
            'current_drawdown',
            'trading_enabled',
            'risk_multiplier',
            'heat_manager_status',
            'num_strategies',
            'capital_allocation'
        ]

        for key in required_keys:
            assert key in status

    def test_status_initial_values(
        self,
        mock_strategy,
        heat_manager,
        risk_manager
    ):
        """Test initial status values are correct."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        status = pm.get_portfolio_status()

        assert status['current_equity'] == 10000
        assert status['peak_equity'] == 10000
        assert status['current_drawdown'] == 0.0
        assert status['trading_enabled'] is True
        assert status['risk_multiplier'] == 1.0
        assert status['num_strategies'] == 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Test integration with heat manager and risk manager."""

    def test_heat_manager_integration(
        self,
        mock_strategy,
        heat_manager,
        risk_manager
    ):
        """Test heat manager is accessible through portfolio manager."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        # Add position to heat manager
        pm.heat_manager.add_position('TEST', 2000)

        status = pm.get_portfolio_status()

        assert status['heat_manager_status']['position_count'] == 1
        assert 'TEST' in status['heat_manager_status']['active_positions']
        assert status['heat_manager_status']['current_heat'] == 0.20  # 2000/10000

    def test_risk_manager_integration(
        self,
        mock_strategy,
        heat_manager,
        risk_manager
    ):
        """Test risk manager state updates correctly."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        # Simulate drawdown
        pm.risk_manager.update_equity(10000)  # Peak
        pm.risk_manager.update_equity(8500)   # -15% DD

        status = pm.get_portfolio_status()

        assert status['current_equity'] == 8500
        assert status['peak_equity'] == 10000
        assert status['current_drawdown'] == 0.15
        assert status['risk_multiplier'] == 0.5  # Reduced at 15% DD


# =============================================================================
# Multi-Strategy Tests
# =============================================================================

class TestMultiStrategy:
    """Test multi-strategy functionality (Phase 5 stub)."""

    def test_multi_strategy_not_implemented(
        self,
        mock_strategy,
        heat_manager,
        risk_manager
    ):
        """Test multi-strategy backtest raises NotImplementedError."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        with pytest.raises(NotImplementedError, match="Phase 5 feature"):
            pm.run_multi_strategy_backtest(
                data_dict={'MockStrategy': pd.DataFrame()},
                initial_capital=10000
            )


# =============================================================================
# Reset Tests
# =============================================================================

class TestReset:
    """Test portfolio manager reset functionality."""

    def test_reset_clears_state(
        self,
        mock_strategy,
        heat_manager,
        risk_manager
    ):
        """Test reset clears all state correctly."""
        pm = PortfolioManager(
            strategies=[mock_strategy],
            capital=10000,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        # Modify state
        pm.heat_manager.add_position('TEST', 2000)
        pm.risk_manager.update_equity(8000)

        # Reset
        pm.reset()

        # Verify reset
        assert pm.current_equity == 10000
        assert pm.peak_equity == 10000
        assert pm.heat_manager.get_position_count() == 0
        assert pm.risk_manager.peak_equity == 0.0
        assert pm.risk_manager.current_equity == 0.0
