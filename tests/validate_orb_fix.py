"""
Validation Script: Confirm ORB Strategy Now Executes Trades

Purpose: Verify the opening range broadcast fix allows trades to execute
Test Period: January 2024 (same period that previously showed 0 trades)

Expected: >0 trades executed

Run: uv run python tests/validate_orb_fix.py
"""

import sys
from pathlib import Path
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))

from strategies.orb_refactored import ORBStrategy, ORBConfig


def main():
    print("=" * 70)
    print("VALIDATION: ORB Strategy Fix - January 2024")
    print("=" * 70)

    # Configure ORB strategy (same as failing test)
    config = ORBConfig(
        name="ORB Validation",
        symbol='SPY',
        risk_per_trade=0.02,
        start_date='2024-01-01',
        end_date='2024-01-31'
    )

    strategy = ORBStrategy(config)

    print("\nStep 1: Fetching data...")
    data_5min, data_daily = strategy.fetch_data()

    print(f"Data fetched: {len(data_5min)} 5-minute bars")

    print("\nStep 2: Running backtest...")
    pf = strategy.backtest(data_5min, initial_capital=10000)

    print("\n" + "=" * 70)
    print("BACKTEST RESULTS - JANUARY 2024")
    print("=" * 70)

    print(f"\nTrades executed: {pf.trades.count()}")

    if pf.trades.count() > 0:
        print("\n[SUCCESS] Strategy now executes trades!")

        metrics = strategy.get_performance_metrics(pf)
        print(f"\nPerformance Metrics:")
        print(f"  Total Return: {metrics['total_return']*100:.2f}%")
        print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
        print(f"  Win Rate: {metrics['win_rate']*100:.1f}%")
        print(f"  Total Trades: {metrics['total_trades']}")

        # Show trade details
        print(f"\nTrade Summary:")
        print(f"  Winning trades: {pf.trades.winning.count()}")
        print(f"  Losing trades: {pf.trades.losing.count()}")

        if pf.trades.winning.count() > 0:
            print(f"  Avg winner: {metrics['avg_winner']*100:.2f}%")
        if pf.trades.losing.count() > 0:
            print(f"  Avg loser: {metrics['avg_loser']*100:.2f}%")

        print("\n" + "=" * 70)
        print("FIX VALIDATED: Opening range broadcast now works correctly")
        print("=" * 70)

    else:
        print("\n[FAILED] Still 0 trades - additional debugging needed")

    print("\n")


if __name__ == '__main__':
    main()
