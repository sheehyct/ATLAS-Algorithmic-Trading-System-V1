"""
Test script for Baseline MA-RSI Strategy

This script tests the baseline strategy on SPY with real historical data
to verify the implementation works correctly.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from strategies.baseline_ma_rsi import BaselineStrategy
from data.alpaca import fetch_alpaca_data
import pandas as pd


def test_baseline_strategy():
    """Test the baseline strategy with SPY data."""

    print("=" * 70)
    print("TESTING BASELINE MA-RSI STRATEGY")
    print("=" * 70)

    # Test parameters
    symbol = "SPY"
    period_days = 1825  # 5 years
    timeframe = '1D'
    init_cash = 10000.0

    # Fetch data
    print(f"\n1. Fetching {symbol} data...")
    print(f"   Timeframe: {timeframe}")
    print(f"   Period: {period_days} days (~5 years)")

    try:
        data = fetch_alpaca_data(symbol, timeframe=timeframe, period_days=period_days)
        print(f"   SUCCESS: Fetched {len(data)} bars")
        print(f"   Date range: {data.index[0].date()} to {data.index[-1].date()}")
    except Exception as e:
        print(f"   ERROR: Failed to fetch data: {e}")
        return False

    # Initialize strategy
    print(f"\n2. Initializing Baseline Strategy...")
    print(f"   Parameters:")
    print(f"   - MA Period: 200")
    print(f"   - RSI Period: 2")
    print(f"   - RSI Oversold: 15")
    print(f"   - RSI Overbought: 85")
    print(f"   - ATR Period: 14")
    print(f"   - ATR Multiplier: 2.0")
    print(f"   - Max Hold Days: 14")

    strategy = BaselineStrategy()

    # Generate signals
    print(f"\n3. Generating signals...")
    try:
        signals = strategy.generate_signals(data)
        long_signals = signals['long_entries'].sum()
        short_signals = signals['short_entries'].sum()
        print(f"   SUCCESS: Generated signals")
        print(f"   - Long entry signals: {long_signals}")
        print(f"   - Short entry signals: {short_signals}")
        print(f"   - Total signals: {long_signals + short_signals}")
    except Exception as e:
        print(f"   ERROR: Failed to generate signals: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Run backtest
    print(f"\n4. Running backtest...")
    print(f"   Initial capital: ${init_cash:,.2f}")

    try:
        pf = strategy.backtest(data, init_cash=init_cash)
        print(f"   SUCCESS: Backtest complete")
    except Exception as e:
        print(f"   ERROR: Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Get performance stats
    print(f"\n5. Calculating performance metrics...")
    try:
        stats = strategy.get_performance_stats(pf)
        print(f"   SUCCESS: Metrics calculated")
    except Exception as e:
        print(f"   ERROR: Failed to calculate metrics: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Display results
    print("\n" + "=" * 70)
    print("BASELINE STRATEGY PERFORMANCE RESULTS")
    print("=" * 70)

    print(f"\nReturns:")
    print(f"  Total Return:        {stats['total_return']:>10.2%}")
    buy_hold = (data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1
    print(f"  Buy-and-Hold:        {buy_hold:>10.2%}")
    print(f"  Outperformance:      {stats['total_return'] - buy_hold:>10.2%}")

    print(f"\nRisk Metrics:")
    print(f"  Sharpe Ratio:        {stats['sharpe_ratio']:>10.2f}")
    print(f"  Max Drawdown:        {stats['max_drawdown']:>10.2%}")

    print(f"\nTrade Statistics:")
    print(f"  Total Trades:        {stats['total_trades']:>10.0f}")
    print(f"  Win Rate:            {stats['win_rate']:>10.2%}")
    print(f"  Profit Factor:       {stats['profit_factor']:>10.2f}")
    print(f"  Avg Trade Return:    {stats['avg_trade_return']:>10.2%}")
    print(f"  Avg Winning Trade:   {stats['avg_winning_trade']:>10.2%}")
    print(f"  Avg Losing Trade:    {stats['avg_losing_trade']:>10.2%}")

    # Validation checks
    print("\n" + "=" * 70)
    print("VALIDATION CHECKS")
    print("=" * 70)

    validation_passed = True

    # Check 1: Strategy should generate trades
    if stats['total_trades'] == 0:
        print("FAIL: No trades generated")
        validation_passed = False
    else:
        print(f"PASS: Generated {stats['total_trades']} trades")

    # Check 2: Win rate should be reasonable (25%-75%)
    if 0.25 <= stats['win_rate'] <= 0.75:
        print(f"PASS: Win rate {stats['win_rate']:.2%} is reasonable")
    else:
        print(f"WARNING: Win rate {stats['win_rate']:.2%} may be unusual")

    # Check 3: Sharpe ratio should be calculated
    if not pd.isna(stats['sharpe_ratio']):
        print(f"PASS: Sharpe ratio calculated: {stats['sharpe_ratio']:.2f}")
    else:
        print("FAIL: Sharpe ratio is NaN")
        validation_passed = False

    # Check 4: Max drawdown should be negative
    if stats['max_drawdown'] < 0:
        print(f"PASS: Max drawdown is negative: {stats['max_drawdown']:.2%}")
    else:
        print(f"WARNING: Max drawdown is {stats['max_drawdown']:.2%}")

    print("\n" + "=" * 70)
    if validation_passed:
        print("TEST RESULT: SUCCESS - All validation checks passed")
    else:
        print("TEST RESULT: FAILED - Some validation checks failed")
    print("=" * 70)

    return validation_passed


if __name__ == "__main__":
    success = test_baseline_strategy()
    sys.exit(0 if success else 1)
