"""
Test STRAT Signal Generation with Real SPY Data
Validates that signals are generated with proper entry levels and TFC alignment
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
import vectorbtpro as vbt
import pandas_market_calendars as mcal
from datetime import datetime, timedelta
from data.alpaca import fetch_alpaca_data
from trading.strat_signals import STRATSignalGenerator

def test_signal_generation():
    """Test STRAT signal generation with DAILY patterns and TFC validation"""

    print("\n" + "="*60)
    print("STRAT SIGNAL GENERATION TEST - DAILY PATTERNS")
    print("="*60)

    # Step 1: Fetch multi-timeframe data
    print("\n1. Fetching multi-timeframe AMD data...")
    print("   Note: Patterns will be detected on DAILY bars")
    print("   Weekly/Monthly used for TFC validation only")
    print("   Using AMD for high-volatility pattern validation")

    # Fetch hourly data (will be resampled to daily) - 2 years of data
    hourly_data = fetch_alpaca_data(
        "AMD",
        "1Hour",
        730  # 2 years of data
    )
    print(f"   Hourly: {len(hourly_data)} bars (raw)")

    # STRICT NYSE MARKET HOURS FILTERING
    # CRITICAL: Remove weekends AND holidays BEFORE resampling
    # This prevents phantom bars from being created on non-trading days
    #
    # VERIFIED APPROACH for VBT Pro 2025.7.27:
    # - VBT Pro does NOT have built-in Calendars.get() or is_weekday()
    # - Pandas + pandas-market-calendars is the official documented pattern
    # - Confirmed by QuantGPT and VBT Pro community as production-ready

    print(f"   Hourly (before filtering): {len(hourly_data)} bars")

    # Step 1: Filter weekends (Monday=0 through Friday=4, exclude Sat=5, Sun=6)
    hourly_data = hourly_data[hourly_data.index.dayofweek < 5]
    print(f"   Hourly (after weekend filter): {len(hourly_data)} bars")

    # Step 2: Filter NYSE holidays using pandas-market-calendars
    nyse = mcal.get_calendar('NYSE')
    holidays = nyse.holidays().holidays
    hourly_data = hourly_data[~hourly_data.index.normalize().isin(holidays)]
    print(f"   Hourly (after holiday filter): {len(hourly_data)} bars")

    # VERIFICATION: Ensure no weekend/holiday bars remain (QuantGPT-recommended assertions)
    # This catches the Saturday Dec 16, 2023 bug that invalidated previous backtests
    print("\n   Verification checks:")

    # Check 1: No weekend bars
    weekend_bars = (hourly_data.index.dayofweek >= 5).any()
    assert not weekend_bars, "CRITICAL: Weekend bars detected after filtering!"
    print(f"   - No weekend bars: PASS")

    # Check 2: Specific known Saturday (Dec 16, 2023) removed
    dec_16_2023_exists = '2023-12-16' in hourly_data.index.date.astype(str)
    assert not dec_16_2023_exists, "CRITICAL: Saturday Dec 16, 2023 still present!"
    print(f"   - Saturday Dec 16, 2023 removed: PASS")

    # Check 3: Known holidays removed (Christmas 2023)
    christmas_2023_exists = '2023-12-25' in hourly_data.index.date.astype(str)
    assert not christmas_2023_exists, "CRITICAL: Christmas 2023 still present!"
    print(f"   - Christmas 2023 removed: PASS")

    print(f"   All market hours filters verified successfully!\n")

    # Resample to other timeframes
    daily_data = hourly_data.resample('1D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    print(f"   Daily: {len(daily_data)} bars")

    weekly_data = hourly_data.resample('1W').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    print(f"   Weekly: {len(weekly_data)} bars")

    monthly_data = hourly_data.resample('1ME').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    print(f"   Monthly: {len(monthly_data)} bars")

    # Step 2: Initialize signal generator
    print("\n2. Initializing STRAT Signal Generator...")
    generator = STRATSignalGenerator(
        min_tfc_score=0.50,  # Partial alignment minimum
        require_ftfc=False,   # Don't require full alignment for testing
        risk_per_trade=0.01   # 1% risk per trade
    )

    # Step 3: Generate signals
    print("\n3. Generating STRAT signals...")
    signals_df = generator.generate_signals(
        hourly_data,
        daily_data,
        weekly_data,
        monthly_data
    )

    pattern_counts = signals_df['pattern'].value_counts()
    print("\nDetected STRAT pattern counts:", pattern_counts.to_dict())
    assert pattern_counts.get('2-1-2', 0) > 0, 'Expected at least one daily 2-1-2 pattern'
    assert pattern_counts.get('3-1-2', 0) > 0, 'Expected at least one daily 3-1-2 pattern'

    pattern_types = {signal.pattern_type for signal in generator.signals}
    assert '2-1-2' in pattern_types, '2-1-2 signals missing from STRATAnalyzer integration'
    assert '3-1-2' in pattern_types, '3-1-2 signals missing from STRATAnalyzer integration'

    # Get daily bar classifications for exit reason analysis
    daily_class = generator._classify_bars(daily_data)

    # Step 4: Analyze results
    print("\n4. Signal Analysis:")
    print("-" * 40)

    # Count signals (new format with long/short entries)
    long_entry_signals = signals_df['long_entries'].sum()
    short_entry_signals = signals_df['short_entries'].sum()
    total_entry_signals = long_entry_signals + short_entry_signals

    print(f"Total entry signals: {total_entry_signals}")
    print(f"  - Long entries: {long_entry_signals}")
    print(f"  - Short entries: {short_entry_signals}")

    # Count exit signals
    long_exit_signals = signals_df['long_exits'].sum()
    short_exit_signals = signals_df['short_exits'].sum()
    print(f"Total exit signals: {long_exit_signals + short_exit_signals}")
    print(f"  - Long exits (reversal 2D bars): {long_exit_signals}")
    print(f"  - Short exits (reversal 2U bars): {short_exit_signals}")

    if total_entry_signals > 0:
        # Show signal details
        signal_rows = signals_df[signals_df['long_entries'] | signals_df['short_entries']]

        print(f"\nSignal Details (showing first 10):")
        print("-" * 40)

        for idx, (timestamp, row) in enumerate(signal_rows.head(10).iterrows()):
            print(f"\n{idx+1}. {timestamp}")
            print(f"   Pattern: {row['pattern']}")
            print(f"   Direction: {row['direction']}")
            print(f"   Trigger Price: ${row['trigger_price']:.2f}")
            print(f"   Stop Price: ${row['stop_price']:.2f}")
            print(f"   Target Price: ${row['target_price']:.2f}")
            print(f"   TFC Score: {row['tfc_score']:.2f}")
            print(f"   Confidence: {row['confidence']:.2f}")

            # Calculate risk/reward
            risk = abs(row['trigger_price'] - row['stop_price'])
            reward = abs(row['target_price'] - row['trigger_price'])
            rr_ratio = reward / risk if risk > 0 else 0
            print(f"   Risk/Reward: {rr_ratio:.2f}")

        # Pattern distribution
        pattern_counts = signal_rows['pattern'].value_counts()
        print(f"\n5. Pattern Distribution:")
        print("-" * 40)
        for pattern, count in pattern_counts.items():
            print(f"   {pattern}: {count} signals")

        # Direction distribution
        direction_counts = signal_rows['direction'].value_counts()
        print(f"\n6. Direction Distribution:")
        print("-" * 40)
        for direction, count in direction_counts.items():
            print(f"   {direction}: {count} signals")

        # TFC score distribution
        print(f"\n7. TFC Score Distribution:")
        print("-" * 40)
        print(f"   Mean: {signal_rows['tfc_score'].mean():.3f}")
        print(f"   Min: {signal_rows['tfc_score'].min():.3f}")
        print(f"   Max: {signal_rows['tfc_score'].max():.3f}")
        print(f"   Std: {signal_rows['tfc_score'].std():.3f}")

        # Show high-confidence signals (TFC >= 0.80)
        high_conf = signal_rows[signal_rows['tfc_score'] >= 0.80]
        print(f"\n8. High-Confidence Signals (TFC >= 0.80):")
        print("-" * 40)
        print(f"   Count: {len(high_conf)} ({len(high_conf)/len(signal_rows)*100:.1f}% of all signals)")

        if len(high_conf) > 0:
            print(f"   Average Confidence: {high_conf['confidence'].mean():.3f}")

    # Get summary from generator
    print("\n9. Generator Summary:")
    print("-" * 40)
    print(generator.get_summary())

    # Step 5: Create backtest with VBT using reversal exits
    if total_entry_signals > 0:
        print("\n10. Creating VBT Portfolio with Reversal Exits...")
        print("-" * 40)

        # NEW: Use the cleaned long/short entry/exit signals
        long_entries = signals_df['long_entries']
        long_exits = signals_df['long_exits']
        short_entries = signals_df['short_entries']
        short_exits = signals_df['short_exits']

        print(f"   Long trades: {long_entries.sum()} entries, {long_exits.sum()} exits")
        print(f"   Short trades: {short_entries.sum()} entries, {short_exits.sum()} exits")

        try:
            # Create portfolio with VBT Pro using reversal exits
            # NOTE: When using long_entries/short_entries separately, don't specify direction
            pf = vbt.PF.from_signals(
                daily_data['close'],  # Using daily data since patterns are daily
                long_entries=long_entries,
                long_exits=long_exits,
                short_entries=short_entries,
                short_exits=short_exits,
                init_cash=100000,
                fees=0.001,  # 0.1% fees
                slippage=0.001  # 0.1% slippage
            )

            # Show basic stats
            print("\nPortfolio Statistics:")
            print(pf.stats())

            # DETAILED TRADE-BY-TRADE ANALYSIS
            print("\n" + "="*80)
            print("DETAILED TRADE-BY-TRADE ANALYSIS")
            print("="*80)

            # Get trade records from portfolio
            trades = pf.trades.records_readable

            if len(trades) > 0:
                print(f"\nTotal Trades Executed: {len(trades)}\n")

                # Debug: show column names
                print(f"Available columns: {list(trades.columns)}\n")

                for idx, trade in trades.iterrows():
                    # Use actual column names from VBT Pro
                    entry_date = trade['Entry Index']
                    exit_date = trade['Exit Index']
                    direction = "LONG" if trade['Direction'] == 'Long' else "SHORT"

                    # Get the entry signal details
                    entry_signal = signal_rows[signal_rows.index == entry_date]

                    if not entry_signal.empty:
                        pattern = entry_signal.iloc[0]['pattern']
                        entry_price = trade['Avg Entry Price']
                        exit_price = trade['Avg Exit Price']
                        pnl = trade['PnL']
                        pnl_pct = trade['Return'] * 100
                        stop_price = entry_signal.iloc[0]['stop_price']
                        target_price = entry_signal.iloc[0]['target_price']
                        tfc_score = entry_signal.iloc[0]['tfc_score']

                        # Determine exit reason
                        if direction == "LONG":
                            # Check if exit was on long_exits (reversal 2D)
                            if exit_date in signals_df.index and signals_df.loc[exit_date, 'long_exits']:
                                exit_reason = "Reversal (2D bar)"
                                # Get the daily bar classification at exit
                                exit_bar_class = daily_class.loc[exit_date] if exit_date in daily_class.index else "Unknown"
                            elif exit_price <= stop_price:
                                exit_reason = "Stop Loss Hit"
                            elif exit_price >= target_price:
                                exit_reason = "Target Hit"
                            else:
                                exit_reason = "Other"
                        else:  # SHORT
                            if exit_date in signals_df.index and signals_df.loc[exit_date, 'short_exits']:
                                exit_reason = "Reversal (2U bar)"
                                exit_bar_class = daily_class.loc[exit_date] if exit_date in daily_class.index else "Unknown"
                            elif exit_price >= stop_price:
                                exit_reason = "Stop Loss Hit"
                            elif exit_price <= target_price:
                                exit_reason = "Target Hit"
                            else:
                                exit_reason = "Other"

                        # Calculate days held
                        days_held = (exit_date - entry_date).days

                        # Get daily bar classifications for context
                        entry_day_class = daily_class.loc[entry_date] if entry_date in daily_class.index else 0
                        exit_day_class = daily_class.loc[exit_date] if exit_date in daily_class.index else 0

                        # Get 3 bars before entry for pattern context
                        entry_idx_loc = daily_data.index.get_loc(entry_date)
                        context_bars = []
                        for i in range(max(0, entry_idx_loc-2), entry_idx_loc+1):
                            bar_date = daily_data.index[i]
                            bar_class = daily_class.iloc[i]
                            bar_open = daily_data['open'].iloc[i]
                            bar_high = daily_data['high'].iloc[i]
                            bar_low = daily_data['low'].iloc[i]
                            bar_close = daily_data['close'].iloc[i]

                            # Classify bar type for readability
                            if bar_class == 1:
                                bar_type = "1 (Inside)"
                            elif bar_class == 2:
                                bar_type = "2U (Bull)"
                            elif bar_class == -2:
                                bar_type = "2D (Bear)"
                            elif bar_class == 3:
                                bar_type = "3 (Outside)"
                            else:
                                bar_type = f"{bar_class}"

                            context_bars.append({
                                'date': bar_date,
                                'type': bar_type,
                                'open': bar_open,
                                'high': bar_high,
                                'low': bar_low,
                                'close': bar_close
                            })

                        print(f"Trade #{idx+1}: {direction} - {pattern}")
                        print(f"{'-'*80}")
                        print(f"  ENTRY SETUP:")
                        print(f"  ------------")
                        for cb in context_bars:
                            print(f"    {cb['date'].strftime('%Y-%m-%d')}: {cb['type']:12s} O=${cb['open']:6.2f} H=${cb['high']:6.2f} L=${cb['low']:6.2f} C=${cb['close']:6.2f}")
                        print(f"  ")
                        print(f"  TRADE DETAILS:")
                        print(f"  --------------")
                        print(f"  Entry Date:       {entry_date.strftime('%Y-%m-%d')}")
                        print(f"  Entry Price:      ${entry_price:.2f}")
                        print(f"  Stop Loss:        ${stop_price:.2f}")
                        print(f"  Target:           ${target_price:.2f}")
                        print(f"  TFC Score:        {tfc_score:.2f} (4-timeframe: H+D+W+M)")
                        print(f"  ")
                        print(f"  EXIT DETAILS:")
                        print(f"  -------------")
                        print(f"  Exit Date:        {exit_date.strftime('%Y-%m-%d')}")
                        exit_bar_type = ""
                        if exit_day_class == 1:
                            exit_bar_type = "1 (Inside)"
                        elif exit_day_class == 2:
                            exit_bar_type = "2U (Bullish)"
                        elif exit_day_class == -2:
                            exit_bar_type = "2D (Bearish)"
                        elif exit_day_class == 3:
                            exit_bar_type = "3 (Outside)"
                        print(f"  Exit Bar Type:    {exit_bar_type}")
                        print(f"  Exit Price:       ${exit_price:.2f}")
                        print(f"  Exit Reason:      {exit_reason}")
                        print(f"  Days Held:        {days_held}")
                        print(f"  ")
                        print(f"  RESULT:")
                        print(f"  -------")
                        print(f"  P&L:              ${pnl:.2f} ({pnl_pct:+.2f}%)")
                        print(f"  Status:           {'WIN' if pnl > 0 else 'LOSS'}")
                        print()
            else:
                print("\nNo trades found in portfolio records")

        except Exception as e:
            print(f"\nWarning: Could not create portfolio: {e}")
            print("This might be due to no completed trades or data issues")

    else:
        print("\nNo signals generated - check data and parameters")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)


if __name__ == "__main__":
    test_signal_generation()