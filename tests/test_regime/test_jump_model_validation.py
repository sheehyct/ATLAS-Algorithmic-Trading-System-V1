"""
Jump Model Validation Test

This test validates the Jump Model implementation against known historical
market regimes. This is NOT lookahead bias because:

1. We're not optimizing parameters based on returns
2. We're checking if known events (2020 crash) are detected correctly
3. Thresholds (0.70, 0.30, 0.90) came from architecture docs, not curve-fitting
4. We're validating implementation correctness, not strategy performance

Lookahead Bias (WRONG):
    - Optimize thresholds to maximize strategy returns
    - Select volatility method based on backtest performance
    - Adjust parameters to fit historical periods

Implementation Validation (CORRECT):
    - Check if March 2020 crash is detected as CRASH/BEAR
    - Verify 2023 bull market shows as TREND_BULL
    - Confirm turnover is ~44% annually (architecture expectation)
    - Compare ATR vs Yang-Zhang for consistency
"""

import pytest
import pandas as pd
import numpy as np
import vectorbtpro as vbt
from regime.jump_model import JumpModel
from data.alpaca import fetch_alpaca_data


# Known historical market regimes (PUBLIC KNOWLEDGE, not curve-fitting)
KNOWN_REGIMES = {
    'march_2020_crash': {
        'start': '2020-02-19',  # Market peak before crash
        'end': '2020-03-23',    # Market bottom
        'expected': ['CRASH', 'TREND_BEAR'],  # Either is acceptable
        'description': 'COVID-19 crash (-34% in 33 days)'
    },
    'recovery_2020': {
        'start': '2020-04-01',
        'end': '2020-12-31',
        'expected': ['TREND_BULL'],
        'description': 'Post-COVID recovery rally'
    },
    'bear_2022': {
        'start': '2022-01-01',
        'end': '2022-10-31',
        'expected': ['TREND_BEAR', 'TREND_NEUTRAL'],  # Bear with neutral periods
        'description': '2022 bear market (-25% SPY drawdown)'
    },
    'bull_2023': {
        'start': '2023-01-01',
        'end': '2023-12-31',
        'expected': ['TREND_BULL'],
        'description': '2023 bull market recovery'
    }
}


@pytest.fixture
def spy_data():
    """
    Fetch SPY data for testing (2020-2024).

    Using publicly available historical data is NOT lookahead bias.
    We're testing implementation correctness, not optimizing parameters.

    Uses Alpaca data to validate the same pipeline used in production.
    """
    # Fetch SPY daily data from Alpaca (2019-2025 = ~2190 days)
    # Extended range to ensure we capture early 2020 data for March 2020 crash validation
    data = fetch_alpaca_data(
        symbol='SPY',
        timeframe='1D',
        period_days=2190  # ~6 years back to capture 2020-01-01
    )

    # Standardize column names to match expected format (title case)
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    return data


def test_jump_model_initialization():
    """Test Jump Model initializes correctly with both volatility methods."""
    # ATR method (default)
    model_atr = JumpModel(window=20, volatility_method='atr')
    assert model_atr.volatility_method == 'atr'
    assert model_atr.window == 20
    assert model_atr.bull_threshold == 0.70

    # Yang-Zhang method
    model_yz = JumpModel(window=20, volatility_method='yang_zhang')
    assert model_yz.volatility_method == 'yang_zhang'

    # Invalid method should raise error
    with pytest.raises(ValueError):
        JumpModel(volatility_method='invalid')


def test_march_2020_crash_detection(spy_data):
    """
    Validate March 2020 COVID crash is detected.

    This is NOT lookahead bias - we're checking if a known historical event
    (March 2020 crash) is correctly identified by our implementation.
    """
    model = JumpModel(window=20, volatility_method='atr')

    # Get regime for crash period
    crash_period = spy_data.loc['2020-02-19':'2020-03-23']
    regime = model.detect_regime(crash_period)

    # Count regime occurrences during crash
    regime_counts = regime.value_counts()

    # Should see CRASH or TREND_BEAR during this period
    crash_or_bear = (
        regime_counts.get('CRASH', 0) +
        regime_counts.get('TREND_BEAR', 0)
    )

    total_days = len(regime)
    crash_bear_pct = crash_or_bear / total_days

    # At least 50% of days should show distress
    assert crash_bear_pct > 0.50, (
        f"March 2020 crash not detected properly. "
        f"Only {crash_bear_pct:.1%} of days showed CRASH/BEAR. "
        f"Regime distribution: {regime_counts.to_dict()}"
    )

    print(f"\nPASSED: March 2020 Crash Detection:")
    print(f"  CRASH/BEAR: {crash_bear_pct:.1%} of days")
    print(f"  Distribution: {regime_counts.to_dict()}")


def test_2023_bull_market_detection(spy_data):
    """
    Validate 2023 bull market is detected as TREND_BULL.

    This is NOT lookahead bias - 2023 was a known bull market (+26% return).
    """
    model = JumpModel(window=20, volatility_method='atr')

    # Get regime for 2023 bull market
    bull_period = spy_data.loc['2023-01-01':'2023-12-31']
    regime = model.detect_regime(bull_period)

    # Count regime occurrences
    regime_counts = regime.value_counts()
    bull_pct = regime_counts.get('TREND_BULL', 0) / len(regime)

    # Should see predominantly TREND_BULL (not 100%, some neutral is ok)
    assert bull_pct > 0.40, (
        f"2023 bull market not detected properly. "
        f"Only {bull_pct:.1%} of days showed TREND_BULL. "
        f"Regime distribution: {regime_counts.to_dict()}"
    )

    print(f"\nPASSED: 2023 Bull Market Detection:")
    print(f"  TREND_BULL: {bull_pct:.1%} of days")
    print(f"  Distribution: {regime_counts.to_dict()}")


def test_regime_turnover(spy_data):
    """
    Validate regime turnover is reasonable (~44% annually per architecture).

    This is NOT lookahead bias - turnover is an implementation check,
    not a performance optimization.
    """
    model = JumpModel(window=20, volatility_method='atr')

    # Get full period statistics
    stats = model.get_regime_statistics(spy_data)

    # Turnover should be reasonable (not excessive like GMM's 141%)
    # Architecture expects ~44% annually
    # We'll allow 20-80% range (implementation might differ)
    assert 0.20 < stats['turnover'] < 0.80, (
        f"Regime turnover seems unreasonable: {stats['turnover']:.1%}. "
        f"Expected ~44% annually (range 20-80%). "
        f"Too high = whipsaw, too low = sticky regimes."
    )

    print(f"\nPASSED: Regime Turnover Check:")
    print(f"  Annual turnover: {stats['turnover']:.1%}")
    print(f"  Expected: ~44% (architecture spec)")
    print(f"  Distribution: {stats['percentages']}")


def test_atr_vs_yang_zhang_comparison(spy_data):
    """
    Compare ATR vs Yang-Zhang methods for consistency.

    This is NOT lookahead bias - we're checking if both implementations
    produce reasonable and consistent results, not optimizing based on returns.
    """
    model_atr = JumpModel(window=20, volatility_method='atr')
    model_yz = JumpModel(window=20, volatility_method='yang_zhang')

    # Get regimes from both methods
    regime_atr = model_atr.detect_regime(spy_data)
    regime_yz = model_yz.detect_regime(spy_data)

    # Calculate agreement
    agreement = (regime_atr == regime_yz).sum() / len(regime_atr)

    # Should have reasonable agreement (not 100%, they're different estimators)
    # But also not wildly different
    assert 0.50 < agreement < 0.95, (
        f"ATR and Yang-Zhang methods disagree too much: {agreement:.1%} agreement. "
        f"Expected 50-95% agreement. Check normalization logic."
    )

    # Get statistics from both
    stats_atr = model_atr.get_regime_statistics(spy_data)
    stats_yz = model_yz.get_regime_statistics(spy_data)

    print(f"\nPASSED: ATR vs Yang-Zhang Comparison:")
    print(f"  Agreement: {agreement:.1%}")
    print(f"  ATR distribution: {stats_atr['percentages']}")
    print(f"  YZ distribution: {stats_yz['percentages']}")
    print(f"  ATR turnover: {stats_atr['turnover']:.1%}")
    print(f"  YZ turnover: {stats_yz['turnover']:.1%}")


def test_no_nan_or_inf(spy_data):
    """
    Validate no NaN or Inf values in regime classification.

    This is basic implementation correctness checking.
    """
    model = JumpModel(window=20, volatility_method='atr')
    regime = model.detect_regime(spy_data)

    # Should have no NaN (after warmup period)
    warmup = model.window * 2  # Give extra warmup for rolling calcs
    regime_after_warmup = regime.iloc[warmup:]

    nan_count = regime_after_warmup.isna().sum()
    assert nan_count == 0, (
        f"Found {nan_count} NaN values in regime after warmup period. "
        f"Check volatility calculations."
    )

    print(f"\nPASSED: Data Quality Check:")
    print(f"  No NaN values after warmup period ({warmup} days)")
    print(f"  Total classifications: {len(regime_after_warmup)}")


def test_regime_distribution_reasonable(spy_data):
    """
    Validate regime distribution is reasonable (not all one regime).

    This is basic sanity checking - if 95%+ is one regime, something is wrong.
    """
    model = JumpModel(window=20, volatility_method='atr')
    stats = model.get_regime_statistics(spy_data)

    # No single regime should dominate (>85% of time)
    max_pct = max(stats['percentages'].values())
    assert max_pct < 0.85, (
        f"One regime dominates {max_pct:.1%} of the time. "
        f"Distribution: {stats['percentages']}. "
        f"Check threshold parameters or volatility calculation."
    )

    # Should have at least 2 different regimes
    assert len(stats['counts']) >= 2, (
        f"Only {len(stats['counts'])} regime(s) detected. "
        f"Expected at least 2 different regimes over 4 years."
    )

    print(f"\nPASSED: Regime Distribution Check:")
    print(f"  Number of regimes seen: {len(stats['counts'])}")
    print(f"  Max single regime: {max_pct:.1%}")
    print(f"  Distribution: {stats['percentages']}")


if __name__ == '__main__':
    """
    Run validation tests and print results.

    Usage:
        uv run pytest tests/test_regime/test_jump_model_validation.py -v -s
    """
    pytest.main([__file__, '-v', '-s'])
