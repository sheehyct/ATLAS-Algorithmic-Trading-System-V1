"""
Quick test script for ORB strategy

Tests basic functionality without full backtest.
Run: uv run python tests/test_orb_quick.py
"""

import sys
from pathlib import Path

# Add workspace root to Python path
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from strategies.orb import ORBStrategy
import pandas as pd

def test_orb_basic():
    """Test ORB strategy basic functionality"""

    print("=" * 70)
    print("ORB STRATEGY QUICK TEST")
    print("=" * 70)

    # Initialize strategy
    strategy = ORBStrategy(
        symbol='SPY',
        opening_minutes=30,
        atr_stop_multiplier=2.5,
        risk_pct=0.02,
        init_cash=10000
    )

    print("\n[1/4] Fetching data (this may take a minute)...")
    # Use shorter date range for quick test
    data_5min, data_daily = strategy.fetch_data(
        start_date='2024-01-01',
        end_date='2024-12-31'
    )

    print(f"\n[2/4] Generating signals...")
    signals = strategy.generate_signals()

    print(f"\n[3/4] Running backtest...")
    portfolio = strategy.run_backtest()

    print(f"\n[4/4] Analyzing expectancy...")
    expectancy = strategy.analyze_expectancy()

    print("\n" + "=" * 70)
    print("QUICK TEST RESULTS")
    print("=" * 70)

    if expectancy:
        print(f"\nExpectancy Status: {expectancy['assessment']}")
        print(f"R:R Ratio: {expectancy['rr_ratio']:.2f}:1")
        print(f"Net Expectancy: {expectancy['net']*100:.2f}%")

    print(f"\nSharpe Ratio: {portfolio.sharpe_ratio:.2f}")
    print(f"Total Trades: {portfolio.trades.count()}")

    # Gate 2 criteria check
    print("\n" + "=" * 70)
    print("GATE 2 CRITERIA CHECK (Preliminary)")
    print("=" * 70)

    sharpe_pass = portfolio.sharpe_ratio >= 2.0
    rr_pass = expectancy['rr_ratio'] >= 3.0 if expectancy else False
    expectancy_pass = expectancy['viable'] if expectancy else False

    print(f"Sharpe > 2.0: {'PASS' if sharpe_pass else 'FAIL'} ({portfolio.sharpe_ratio:.2f})")
    print(f"R:R > 3:1: {'PASS' if rr_pass else 'FAIL'} ({expectancy['rr_ratio']:.2f}:1)" if expectancy else "R:R > 3:1: FAIL (no trades)")
    print(f"Net Exp > 0.5%: {'PASS' if expectancy_pass else 'FAIL'}")

    if sharpe_pass and rr_pass and expectancy_pass:
        print("\n[PRELIMINARY] Strategy shows promise - proceed to full backtest")
    else:
        print("\n[PRELIMINARY] Strategy needs optimization or debugging")

    return strategy

if __name__ == '__main__':
    test_orb_basic()
