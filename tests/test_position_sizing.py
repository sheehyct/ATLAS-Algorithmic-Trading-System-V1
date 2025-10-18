"""
Unit Tests for Position Sizing Module

Tests the ATR-based position sizing function for:
- Mathematical correctness
- Capital constraint enforcement
- Edge case handling
- VectorBT Pro compatibility (vectorization, index alignment)
"""

import pytest
import numpy as np
import pandas as pd
from utils.position_sizing import calculate_position_size_atr, validate_position_size


class TestATRPositionSizingMathematics:
    """Test mathematical correctness of ATR-based position sizing"""

    def test_basic_risk_based_sizing(self):
        """Test position sizing when risk constraint is binding"""
        init_cash = 10000
        close = 480.0
        atr = 5.0
        atr_multiplier = 2.5
        risk_pct = 0.02

        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Expected calculation:
        # stop_distance = 5.0 * 2.5 = 12.5
        # position_size_risk = (10000 * 0.02) / 12.5 = 16 shares
        # position_size_capital = 10000 / 480 = 20.83 shares
        # position_size = min(16, 20.83) = 16 shares (risk binding)

        assert position_size == pytest.approx(16.0, abs=0.01)
        assert actual_risk == pytest.approx(0.02, abs=0.001)  # Achieves target 2%
        assert constrained == False  # Not capital constrained

    def test_capital_constraint_active(self):
        """Test position sizing when capital constraint is binding"""
        init_cash = 10000
        close = 480.0
        atr = 1.0  # Very small ATR
        atr_multiplier = 2.5
        risk_pct = 0.02

        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Expected calculation:
        # stop_distance = 1.0 * 2.5 = 2.5
        # position_size_risk = (10000 * 0.02) / 2.5 = 80 shares
        # position_size_capital = 10000 / 480 = 20.83 shares
        # position_size = min(80, 20.83) = 20.83 shares (capital binding)

        expected_capital_size = 10000 / 480
        assert position_size == pytest.approx(expected_capital_size, abs=0.01)
        assert actual_risk < risk_pct  # Achieves less than target (capital limited)
        assert constrained == True  # Capital constrained

    def test_never_exceeds_100_percent_capital(self):
        """Mathematical proof: Position value never exceeds 100% of capital"""
        init_cash = 10000
        close = 480.0
        atr = 0.5  # Extreme low ATR
        atr_multiplier = 2.5
        risk_pct = 0.02

        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Position value = position_size * close
        position_value = position_size * close

        # MUST be <= init_cash (100% of capital)
        assert position_value <= init_cash
        assert position_value / init_cash <= 1.0


class TestEdgeCases:
    """Test edge case handling"""

    def test_zero_atr_handled_gracefully(self):
        """Test that zero ATR doesn't cause division by zero"""
        init_cash = 10000
        close = 480.0
        atr = 0.0  # Zero ATR
        atr_multiplier = 2.5
        risk_pct = 0.02

        # Should not raise exception
        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Should return valid position size (using fallback ATR)
        assert np.isfinite(position_size)
        assert position_size >= 0

    def test_nan_atr_handled(self):
        """Test that NaN ATR values are handled"""
        init_cash = 10000
        close = pd.Series([480, 490, 500], index=pd.date_range('2024-01-01', periods=3))
        atr = pd.Series([5.0, np.nan, 6.0], index=close.index)  # NaN in middle
        atr_multiplier = 2.5
        risk_pct = 0.02

        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Should not have NaN in output
        assert not position_size.isna().any()
        assert not actual_risk.isna().any()

        # All position sizes should be valid
        assert (position_size >= 0).all()

    def test_extreme_high_atr(self):
        """Test with extremely high ATR (position sizes should be very small)"""
        init_cash = 10000
        close = 480.0
        atr = 100.0  # Very high ATR
        atr_multiplier = 2.5
        risk_pct = 0.02

        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Position size should be small but valid
        assert position_size < 5  # Very small position
        assert position_size >= 0
        assert np.isfinite(position_size)

    def test_negative_close_price_handled(self):
        """Test that negative prices don't cause issues (should not happen in practice)"""
        init_cash = 10000
        close = -480.0  # Invalid negative price
        atr = 5.0
        atr_multiplier = 2.5
        risk_pct = 0.02

        # Should not crash, but result should be handled
        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Should return zero position or handle gracefully
        # (Capital constraint would be negative, min should give 0)
        assert position_size >= 0  # At minimum, no negative positions


class TestVectorBTProCompatibility:
    """Test VectorBT Pro compatibility requirements"""

    def test_pandas_series_input_output(self):
        """Test that function accepts and returns pandas Series"""
        init_cash = 10000
        close = pd.Series([480, 490, 500], index=pd.date_range('2024-01-01', periods=3))
        atr = pd.Series([5.0, 5.5, 6.0], index=close.index)
        atr_multiplier = 2.5
        risk_pct = 0.02

        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Output should be pandas Series
        assert isinstance(position_size, pd.Series)
        assert isinstance(actual_risk, pd.Series)
        assert isinstance(constrained, pd.Series)

    def test_index_alignment_preserved(self):
        """Test that output Series has same index as input Series"""
        init_cash = 10000
        date_index = pd.date_range('2024-01-01', periods=5, freq='D')
        close = pd.Series([480, 490, 500, 495, 505], index=date_index)
        atr = pd.Series([5.0, 5.5, 6.0, 5.8, 6.2], index=date_index)
        atr_multiplier = 2.5
        risk_pct = 0.02

        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Index should be preserved
        assert position_size.index.equals(close.index)
        assert actual_risk.index.equals(close.index)
        assert constrained.index.equals(close.index)

    def test_vectorized_no_loops(self):
        """Test that function is vectorized (no explicit loops)"""
        # Test with large Series to ensure vectorization
        init_cash = 10000
        n = 1000
        close = pd.Series(np.random.uniform(400, 600, n), index=pd.date_range('2020-01-01', periods=n))
        atr = pd.Series(np.random.uniform(3, 8, n), index=close.index)
        atr_multiplier = 2.5
        risk_pct = 0.02

        # Should execute quickly (vectorized)
        import time
        start = time.time()
        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )
        elapsed = time.time() - start

        # Should be fast (< 0.1 seconds for 1000 items if vectorized)
        assert elapsed < 0.1

        # Should return correct length
        assert len(position_size) == n
        assert len(actual_risk) == n
        assert len(constrained) == n

    def test_scalar_input_still_works(self):
        """Test that function also works with scalar inputs (backwards compatibility)"""
        init_cash = 10000
        close = 480.0  # Scalar
        atr = 5.0      # Scalar
        atr_multiplier = 2.5
        risk_pct = 0.02

        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Should return scalars
        assert isinstance(position_size, (int, float, np.number))
        assert isinstance(actual_risk, (int, float, np.number))
        assert isinstance(constrained, (bool, np.bool_))


class TestValidationFunction:
    """Test the validate_position_size helper function"""

    def test_valid_position_sizes(self):
        """Test validation passes for valid position sizes"""
        position_size = pd.Series([10, 15, 20])
        init_cash = 10000
        close = pd.Series([480, 490, 500])

        is_valid, message = validate_position_size(position_size, init_cash, close, max_pct=1.0)

        assert is_valid == True
        assert message == "Valid"

    def test_detects_negative_position_sizes(self):
        """Test validation detects negative position sizes"""
        position_size = pd.Series([10, -5, 20])  # Negative value
        init_cash = 10000
        close = pd.Series([480, 490, 500])

        is_valid, message = validate_position_size(position_size, init_cash, close, max_pct=1.0)

        assert is_valid == False
        assert "Negative" in message

    def test_detects_nan_values(self):
        """Test validation detects NaN values"""
        position_size = pd.Series([10, np.nan, 20])  # NaN value
        init_cash = 10000
        close = pd.Series([480, 490, 500])

        is_valid, message = validate_position_size(position_size, init_cash, close, max_pct=1.0)

        assert is_valid == False
        assert "NaN" in message

    def test_detects_capital_constraint_violations(self):
        """Test validation detects positions exceeding capital"""
        position_size = pd.Series([25, 20, 15])  # First position too large
        init_cash = 10000
        close = pd.Series([480, 490, 500])  # 25 * 480 = 12000 > 10000

        is_valid, message = validate_position_size(position_size, init_cash, close, max_pct=1.0)

        assert is_valid == False
        assert "exceeds" in message


class TestRealWorldScenarios:
    """Test with realistic market scenarios"""

    def test_spy_typical_values(self):
        """Test with typical SPY values"""
        init_cash = 10000
        close = 485.0  # Typical SPY price
        atr = 5.5      # Typical SPY ATR
        atr_multiplier = 2.5
        risk_pct = 0.02

        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # Should get reasonable position size
        assert 10 < position_size < 25  # Between 10-25 shares seems reasonable
        assert actual_risk <= risk_pct  # Should not exceed target risk
        assert position_size * close <= init_cash  # Should not exceed capital

    def test_multiple_trading_days(self):
        """Test with realistic multi-day data"""
        init_cash = 10000
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        close = pd.Series([480, 485, 490, 488, 495, 500, 498, 505, 510, 508], index=dates)
        atr = pd.Series([5.0, 5.2, 5.5, 5.3, 5.8, 6.0, 5.9, 6.2, 6.5, 6.3], index=dates)
        atr_multiplier = 2.5
        risk_pct = 0.02

        position_size, actual_risk, constrained = calculate_position_size_atr(
            init_cash, close, atr, atr_multiplier, risk_pct
        )

        # All position sizes should be valid
        assert (position_size > 0).all()
        assert (position_size * close <= init_cash).all()  # Never exceed capital
        assert not position_size.isna().any()
        assert not actual_risk.isna().any()

        # Most trades should achieve close to target risk (unless constrained)
        mean_risk = actual_risk[~constrained].mean()
        assert mean_risk == pytest.approx(risk_pct, abs=0.005)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
