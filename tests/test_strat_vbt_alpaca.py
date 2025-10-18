"""
Minimal STRAT Test with VBT Pro using Existing Alpaca Connector
================================================================

Uses VERIFIED VBT Pro methods with our existing Alpaca data fetcher.
All VBT methods have been verified in the documentation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import vectorbtpro as vbt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data.alpaca import fetch_alpaca_data

def classify_bars_with_governing_range(df: pd.DataFrame) -> pd.Series:
    """
    CORRECT STRAT bar classification with governing range tracking.

    Critical: Consecutive inside bars reference the SAME governing range
    until broken by a 2 or 3.
    """
    if len(df) < 2:
        return pd.Series(0, index=df.index)

    # Handle both uppercase and lowercase column names
    high = df['high'].values if 'high' in df.columns else df['High'].values
    low = df['low'].values if 'low' in df.columns else df['Low'].values

    classification = np.zeros(len(df))

    # Initialize governing range with first bar
    governing_high = high[0]
    governing_low = low[0]

    for i in range(1, len(df)):
        current_high = high[i]
        current_low = low[i]

        # Check against GOVERNING range (not just previous bar!)
        is_inside = (current_high <= governing_high) and (current_low >= governing_low)
        breaks_high = current_high > governing_high
        breaks_low = current_low < governing_low

        if is_inside:
            classification[i] = 1  # Inside bar
            # Governing range DOES NOT change!
        elif breaks_high and breaks_low:
            classification[i] = 3  # Outside bar
            governing_high = current_high
            governing_low = current_low
        elif breaks_high:
            classification[i] = 2  # 2U
            governing_high = current_high
            governing_low = current_low
        elif breaks_low:
            classification[i] = -2  # 2D
            governing_high = current_high
            governing_low = current_low

    return pd.Series(classification, index=df.index)

def detect_simple_patterns(df: pd.DataFrame, scenarios: pd.Series) -> dict:
    """Detect basic STRAT patterns for testing."""
    entries = pd.Series(False, index=df.index)
    exits = pd.Series(False, index=df.index)

    if len(df) < 3:
        return {'entries': entries, 'exits': exits}

    for i in range(2, len(df)):
        bar1 = scenarios.iloc[i-2]
        bar2 = scenarios.iloc[i-1]
        bar3 = scenarios.iloc[i]

        # 2-1-2 Bullish: 2D → 1 → 2U
        if bar1 == -2 and bar2 == 1 and bar3 == 2:
            entries.iloc[i] = True
            print(f"  2-1-2 Bullish at {df.index[i]}")

        # 2-1-2 Bearish: 2U → 1 → 2D
        elif bar1 == 2 and bar2 == 1 and bar3 == -2:
            exits.iloc[i] = True
            print(f"  2-1-2 Bearish at {df.index[i]}")

        # 3-1-2 Bullish: 3 → 1 → 2U
        elif bar1 == 3 and bar2 == 1 and bar3 == 2:
            entries.iloc[i] = True
            print(f"  3-1-2 Bullish at {df.index[i]}")

        # 3-1-2 Bearish: 3 → 1 → 2D
        elif bar1 == 3 and bar2 == 1 and bar3 == -2:
            exits.iloc[i] = True
            print(f"  3-1-2 Bearish at {df.index[i]}")

    return {'entries': entries, 'exits': exits}

def main():
    """Test STRAT with VBT Pro using existing Alpaca connector."""

    print("="*60)
    print("STRAT TEST WITH VBT PRO & ALPACA DATA")
    print("="*60)

    # 1. Fetch data using existing Alpaca connector
    symbol = "SPY"
    print(f"\n1. Fetching {symbol} from Alpaca...")

    # Fetch daily data first (more reliable)
    df = fetch_alpaca_data(symbol, timeframe='1D', period_days=30)

    if df is None or df.empty:
        print("ERROR: Could not fetch data from Alpaca")
        return None

    print(f"   Loaded {len(df)} bars")
    print(f"   Date range: {df.index[0]} to {df.index[-1]}")

    # 2. Classify bars with governing range
    print("\n2. Classifying bars with governing range...")
    scenarios = classify_bars_with_governing_range(df)

    # Count classifications
    inside_count = (scenarios == 1).sum()
    up_count = (scenarios == 2).sum()
    down_count = (scenarios == -2).sum()
    outside_count = (scenarios == 3).sum()

    print(f"\n   Classifications:")
    print(f"   Inside (1): {inside_count}")
    print(f"   2U: {up_count}")
    print(f"   2D: {down_count}")
    print(f"   Outside (3): {outside_count}")

    # 3. Detect patterns
    print("\n3. Detecting STRAT patterns...")
    signals = detect_simple_patterns(df, scenarios)

    print(f"\n   Total entries: {signals['entries'].sum()}")
    print(f"   Total exits: {signals['exits'].sum()}")

    if signals['entries'].sum() == 0 and signals['exits'].sum() == 0:
        print("\n   No patterns found - creating synthetic signals for testing")
        # Create some synthetic signals for portfolio testing
        signals['entries'].iloc[5] = True
        signals['exits'].iloc[15] = True

    # 4. Create portfolio - VERIFIED method (Portfolio.md line 32)
    print("\n4. Creating VBT Pro portfolio...")

    # Ensure we have the close column
    close_col = 'close' if 'close' in df.columns else 'Close'

    pf = vbt.PF.from_signals(
        close=df[close_col],
        entries=signals['entries'],
        exits=signals['exits'],
        init_cash=10000,
        fees=0.001,
        freq='1D'
    )

    # 5. Display stats - VERIFIED method (Portfolio.md line 938)
    print("\n5. Portfolio Statistics:")
    print("-"*40)
    stats = pf.stats()

    # Display key metrics
    key_metrics = ['Total Return [%]', 'Sharpe Ratio', 'Max Drawdown [%]', 'Win Rate [%]']
    for metric in key_metrics:
        if metric in stats:
            print(f"{metric}: {stats[metric]}")

    # 6. Create visualization - VERIFIED method (Portfolio.md line 111)
    print("\n6. Creating portfolio visualization...")
    fig = pf.plot()

    output_file = f"strat_alpaca_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    fig.write_html(output_file)
    print(f"   Saved to: {output_file}")

    # 7. Show bar classification summary
    print("\n7. Bar Classification Details:")
    print("-"*40)
    for i in range(min(10, len(df))):
        bar_type = scenarios.iloc[i]
        bar_name = {0: 'Unknown', 1: 'Inside', 2: '2U', -2: '2D', 3: 'Outside'}.get(bar_type, 'Unknown')
        print(f"   {df.index[i].strftime('%Y-%m-%d')}: {bar_name} (H:{df.iloc[i]['high']:.2f}, L:{df.iloc[i]['low']:.2f})")

    return pf

if __name__ == "__main__":
    pf = main()
    if pf is not None:
        print("\n" + "="*60)
        print("TEST COMPLETE")
        print("="*60)
        print("\nAll VBT methods used are VERIFIED from documentation:")
        print("- vbt.PF.from_signals: Portfolio.md line 32")
        print("- pf.stats(): Portfolio.md line 938")
        print("- pf.plot(): Portfolio.md line 111")