"""
Unit tests for BaseStrategy abstract class

Tests:
1. StrategyConfig validation (risk limits, cost limits)
2. Abstract method enforcement (cannot instantiate directly)
3. Backtest integration with mock strategy
4. Performance metrics calculation
5. Edge cases and error handling

Run: uv run pytest tests/test_base_strategy.py -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies.base_strategy import BaseStrategy, StrategyConfig


# Mock concrete strategy for testing
class MockStrategy(BaseStrategy):
    """Simple strategy for testing BaseStrategy functionality"""

    def generate_signals(self, data: pd.DataFrame) -> dict:
        """Generate simple buy-and-hold signals"""
        long_entries = pd.Series(False, index=data.index)
        long_exits = pd.Series(False, index=data.index)

        # Buy on first day, sell on last day
        long_entries.iloc[0] = True
        long_exits.iloc[-1] = True

        # Simple ATR-based stop distance (use 2% of price)
        stop_distance = data['Close'] * 0.02

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
        """Calculate fixed position size (10 shares)"""
        return pd.Series(10.0, index=data.index)

    def get_strategy_name(self) -> str:
        """Return strategy name"""
        return "Mock Test Strategy"


# Fixtures
@pytest.fixture
def valid_config():
    """Valid strategy configuration"""
    return StrategyConfig(
        name="Test Strategy",
        risk_per_trade=0.02,
        max_positions=5,
        enable_shorts=False,
        commission_rate=0.0015,
        slippage=0.0015
    )


@pytest.fixture
def sample_data():
    """Sample OHLCV data for testing"""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

    # Generate realistic price data
    close = 100 + np.cumsum(np.random.randn(100) * 2)
    high = close + np.random.rand(100) * 2
    low = close - np.random.rand(100) * 2
    open_price = close + np.random.randn(100)
    volume = np.random.randint(1000000, 5000000, 100)

    return pd.DataFrame({
        'Open': open_price,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume
    }, index=dates)


# Test StrategyConfig Validation
class TestStrategyConfig:
    """Test StrategyConfig Pydantic validation"""

    def test_valid_config_creation(self, valid_config):
        """Test creating valid configuration"""
        assert valid_config.name == "Test Strategy"
        assert valid_config.risk_per_trade == 0.02
        assert valid_config.max_positions == 5
        assert valid_config.enable_shorts is False
        assert valid_config.commission_rate == 0.0015
        assert valid_config.slippage == 0.0015

    def test_risk_per_trade_bounds(self):
        """Test risk_per_trade validation bounds"""
        # Valid: 0.1% to 5%
        StrategyConfig(name="Test", risk_per_trade=0.001)  # Min
        StrategyConfig(name="Test", risk_per_trade=0.05)   # Max

        # Invalid: Below min
        with pytest.raises(Exception):  # Pydantic ValidationError
            StrategyConfig(name="Test", risk_per_trade=0.0005)

        # Invalid: Above max
        with pytest.raises(Exception):
            StrategyConfig(name="Test", risk_per_trade=0.06)

    def test_max_positions_bounds(self):
        """Test max_positions validation bounds"""
        # Valid: 1 to 20
        StrategyConfig(name="Test", max_positions=1)   # Min
        StrategyConfig(name="Test", max_positions=20)  # Max

        # Invalid: Below min
        with pytest.raises(Exception):
            StrategyConfig(name="Test", max_positions=0)

        # Invalid: Above max
        with pytest.raises(Exception):
            StrategyConfig(name="Test", max_positions=21)

    def test_commission_and_slippage_bounds(self):
        """Test commission_rate and slippage bounds"""
        # Valid: 0% to 1%
        StrategyConfig(name="Test", commission_rate=0.0, slippage=0.0)
        StrategyConfig(name="Test", commission_rate=0.01, slippage=0.01)

        # Invalid: Above max
        with pytest.raises(Exception):
            StrategyConfig(name="Test", commission_rate=0.02)


# Test BaseStrategy Abstract Class
class TestBaseStrategyAbstract:
    """Test abstract class enforcement"""

    def test_cannot_instantiate_directly(self):
        """Test that BaseStrategy cannot be instantiated directly"""
        config = StrategyConfig(name="Test")

        with pytest.raises(TypeError):
            # Should fail: cannot instantiate abstract class
            BaseStrategy(config)

    def test_mock_strategy_instantiation(self, valid_config):
        """Test that concrete implementation can be instantiated"""
        strategy = MockStrategy(valid_config)
        assert strategy.config.name == "Test Strategy"
        assert strategy.get_strategy_name() == "Mock Test Strategy"

    def test_missing_abstract_methods(self, valid_config):
        """Test that missing abstract methods prevent instantiation"""

        # Strategy missing calculate_position_size
        class IncompleteStrategy(BaseStrategy):
            def generate_signals(self, data):
                return {}
            def get_strategy_name(self):
                return "Incomplete"
            # Missing: calculate_position_size

        with pytest.raises(TypeError):
            IncompleteStrategy(valid_config)


# Test BaseStrategy Configuration Validation
class TestBaseStrategyValidation:
    """Test validate_config() method"""

    def test_risk_per_trade_too_high(self):
        """Test validation fails when risk_per_trade > 3%"""
        config = StrategyConfig(name="Test", risk_per_trade=0.04)

        with pytest.raises(ValueError, match="Risk per trade too high"):
            MockStrategy(config)

    def test_combined_costs_too_high(self):
        """Test validation fails when commission + slippage > 0.5%"""
        config = StrategyConfig(
            name="Test",
            commission_rate=0.003,  # 0.3%
            slippage=0.003          # 0.3%
        )  # Total: 0.6% > 0.5%

        with pytest.raises(ValueError, match="Combined costs exceed 0.5%"):
            MockStrategy(config)

    def test_valid_config_passes(self, valid_config):
        """Test valid configuration passes validation"""
        strategy = MockStrategy(valid_config)
        # Should not raise exception
        assert strategy.config.risk_per_trade == 0.02


# Test BaseStrategy Backtest Integration
class TestBaseStrategyBacktest:
    """Test backtest() method and VBT integration"""

    def test_backtest_runs_successfully(self, valid_config, sample_data):
        """Test that backtest() runs without errors"""
        strategy = MockStrategy(valid_config)
        pf = strategy.backtest(sample_data, initial_capital=10000)

        # Verify portfolio object returned
        assert pf is not None
        assert hasattr(pf, 'total_return')
        assert hasattr(pf, 'sharpe_ratio')

    def test_backtest_missing_required_signals(self, valid_config, sample_data):
        """Test backtest fails when generate_signals returns incomplete dict"""

        class BadSignalStrategy(BaseStrategy):
            def generate_signals(self, data):
                # Missing 'stop_distance' key
                return {
                    'long_entries': pd.Series(False, index=data.index),
                    'long_exits': pd.Series(False, index=data.index)
                }

            def calculate_position_size(self, data, capital, stop_distance):
                return pd.Series(10.0, index=data.index)

            def get_strategy_name(self):
                return "Bad Signal Strategy"

        strategy = BadSignalStrategy(valid_config)

        with pytest.raises(ValueError, match="must return.*stop_distance"):
            strategy.backtest(sample_data)

    def test_backtest_invalid_position_size_type(self, valid_config, sample_data):
        """Test backtest fails when calculate_position_size returns wrong type"""

        class BadPositionStrategy(BaseStrategy):
            def generate_signals(self, data):
                return {
                    'long_entries': pd.Series(False, index=data.index),
                    'long_exits': pd.Series(False, index=data.index),
                    'stop_distance': data['Close'] * 0.02
                }

            def calculate_position_size(self, data, capital, stop_distance):
                # Return scalar instead of Series (WRONG)
                return 10.0

            def get_strategy_name(self):
                return "Bad Position Strategy"

        strategy = BadPositionStrategy(valid_config)

        with pytest.raises(ValueError, match="must return pd.Series"):
            strategy.backtest(sample_data)

    def test_backtest_mismatched_index(self, valid_config, sample_data):
        """Test backtest fails when position sizes have mismatched index"""

        class MismatchedIndexStrategy(BaseStrategy):
            def generate_signals(self, data):
                return {
                    'long_entries': pd.Series(False, index=data.index),
                    'long_exits': pd.Series(False, index=data.index),
                    'stop_distance': data['Close'] * 0.02
                }

            def calculate_position_size(self, data, capital, stop_distance):
                # Return Series with WRONG index
                wrong_index = pd.date_range('2020-01-01', periods=len(data), freq='D')
                return pd.Series(10.0, index=wrong_index)

            def get_strategy_name(self):
                return "Mismatched Index Strategy"

        strategy = MismatchedIndexStrategy(valid_config)

        with pytest.raises(ValueError, match="index must match data index"):
            strategy.backtest(sample_data)

    def test_backtest_uses_config_parameters(self, sample_data):
        """Test that backtest uses fees and slippage from config"""
        config = StrategyConfig(
            name="Test",
            commission_rate=0.002,  # 0.2%
            slippage=0.001          # 0.1%
        )

        strategy = MockStrategy(config)
        pf = strategy.backtest(sample_data, initial_capital=10000)

        # Backtest should complete successfully with custom fees
        assert pf is not None


# Test BaseStrategy Performance Metrics
class TestPerformanceMetrics:
    """Test get_performance_metrics() method"""

    def test_performance_metrics_structure(self, valid_config, sample_data):
        """Test that metrics dict has all required keys"""
        strategy = MockStrategy(valid_config)
        pf = strategy.backtest(sample_data, initial_capital=10000)
        metrics = strategy.get_performance_metrics(pf)

        # Verify all required keys present
        required_keys = {
            'total_return', 'sharpe_ratio', 'sortino_ratio', 'max_drawdown',
            'win_rate', 'profit_factor', 'avg_trade', 'total_trades',
            'avg_winner', 'avg_loser'
        }
        assert required_keys.issubset(metrics.keys())

    def test_performance_metrics_types(self, valid_config, sample_data):
        """Test that metrics have correct data types"""
        strategy = MockStrategy(valid_config)
        pf = strategy.backtest(sample_data, initial_capital=10000)
        metrics = strategy.get_performance_metrics(pf)

        # Portfolio-level metrics should be float (not NaN)
        assert isinstance(metrics['total_return'], (float, int))
        assert isinstance(metrics['sharpe_ratio'], (float, int))
        assert isinstance(metrics['max_drawdown'], (float, int))

        # Trade count should be int
        assert isinstance(metrics['total_trades'], (int, np.integer))

    def test_performance_metrics_no_trades(self, valid_config, sample_data):
        """Test metrics when no trades are executed"""

        class NoTradeStrategy(BaseStrategy):
            def generate_signals(self, data):
                # No entries or exits
                return {
                    'long_entries': pd.Series(False, index=data.index),
                    'long_exits': pd.Series(False, index=data.index),
                    'stop_distance': data['Close'] * 0.02
                }

            def calculate_position_size(self, data, capital, stop_distance):
                return pd.Series(10.0, index=data.index)

            def get_strategy_name(self):
                return "No Trade Strategy"

        strategy = NoTradeStrategy(valid_config)
        pf = strategy.backtest(sample_data, initial_capital=10000)
        metrics = strategy.get_performance_metrics(pf)

        # With no trades, trade-based metrics should be NaN
        assert metrics['total_trades'] == 0
        assert np.isnan(metrics['win_rate'])
        assert np.isnan(metrics['profit_factor'])
        assert np.isnan(metrics['avg_trade'])


# Test Edge Cases
class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_dataframe(self, valid_config):
        """Test backtest with empty DataFrame"""
        empty_data = pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        strategy = MockStrategy(valid_config)

        # Should handle gracefully or raise informative error
        with pytest.raises(Exception):
            strategy.backtest(empty_data)

    def test_single_row_dataframe(self, valid_config):
        """Test backtest with single row DataFrame"""
        single_row = pd.DataFrame({
            'Open': [100],
            'High': [102],
            'Low': [99],
            'Close': [101],
            'Volume': [1000000]
        }, index=pd.date_range('2024-01-01', periods=1))

        strategy = MockStrategy(valid_config)

        # VBT handles single-row DataFrames gracefully (no exception)
        # Just verify it completes without error
        pf = strategy.backtest(single_row)
        assert pf is not None
        # With 1 bar, likely no trades
        assert pf.trades.count() >= 0

    def test_strategy_name_returned(self, valid_config):
        """Test get_strategy_name() returns string"""
        strategy = MockStrategy(valid_config)
        name = strategy.get_strategy_name()

        assert isinstance(name, str)
        assert len(name) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
