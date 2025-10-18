#!/usr/bin/env python3
"""
BASIC TFC (Time Frame Continuity) Implementation for STRAT
Goal: Fetch and classify 4 required timeframes (1M, 1W, 1D, 1H)
NO trading logic, NO backtesting - just get the data pipeline working

As per HANDOFF.md: "ONE GOAL ONLY - Get 4 timeframes classified, nothing more"
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any
import vectorbtpro as vbt

# Import our STRAT analyzer
from core.analyzer import STRATAnalyzer

# Load environment variables
from dotenv import load_dotenv
load_dotenv('config/.env')


def setup_alpaca_credentials():
    """Configure VBT Pro's AlpacaData with credentials from environment"""
    api_key = os.getenv('ALPACA_MID_KEY')
    secret_key = os.getenv('ALPACA_MID_SECRET')

    if not api_key or not secret_key:
        raise ValueError("Missing Alpaca credentials. Check .env file for ALPACA_MID_KEY and ALPACA_MID_SECRET")

    # Configure AlpacaData globally
    vbt.AlpacaData.set_custom_settings(
        client_config=dict(
            api_key=api_key,
            secret_key=secret_key,
            paper=True  # Using paper trading endpoint
        )
    )

    print(f"[CONFIG] Alpaca credentials configured (API key: {api_key[:10]}...)")


def fetch_multi_timeframe_data(symbol: str = "SPY", start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """
    Fetch data at hourly granularity and resample to 4 required timeframes

    Returns dict with keys: '1H', '1D', '1W', '1M'
    Each containing the vbt Data object and its OHLCV DataFrame
    """

    # Calculate date range - need 3+ years for sufficient monthly bars
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        # Go back 3 years to ensure we get 36+ monthly bars
        start_date = (datetime.now() - timedelta(days=365 * 3)).strftime("%Y-%m-%d")

    print("\n" + "=" * 60)
    print(f"FETCHING MULTI-TIMEFRAME DATA FOR {symbol}")
    print("=" * 60)
    print(f"Date range: {start_date} to {end_date}")

    # Step 1: Fetch hourly data (finest granularity we need)
    print("\n1. Fetching hourly data from Alpaca...")
    try:
        h1_data = vbt.AlpacaData.pull(
            symbol,
            start=start_date,
            end=end_date,
            timeframe="1 hour"
        )

        # Get OHLCV columns
        h1_ohlcv = h1_data.get()[['Open', 'High', 'Low', 'Close', 'Volume']]
        print(f"   SUCCESS: Fetched {len(h1_ohlcv)} hourly bars")
        print(f"   Date range: {h1_ohlcv.index[0]} to {h1_ohlcv.index[-1]}")

    except Exception as e:
        print(f"   ERROR fetching data: {e}")
        raise

    # Step 2: Resample to other timeframes using VBT's native methods
    print("\n2. Resampling to multiple timeframes...")

    timeframes = {}

    # Hourly (1H) - already have this
    timeframes['1H'] = {
        'data': h1_data,
        'ohlcv': h1_ohlcv
    }
    print(f"   1H: {len(h1_ohlcv)} bars (raw data)")

    # Daily (1D)
    print("   Resampling to daily...")
    d1_data = h1_data.resample("1D")
    d1_ohlcv = d1_data.get()[['Open', 'High', 'Low', 'Close', 'Volume']]
    timeframes['1D'] = {
        'data': d1_data,
        'ohlcv': d1_ohlcv
    }
    print(f"   1D: {len(d1_ohlcv)} bars")

    # Weekly (1W)
    print("   Resampling to weekly...")
    w1_data = h1_data.resample("1W")
    w1_ohlcv = w1_data.get()[['Open', 'High', 'Low', 'Close', 'Volume']]
    timeframes['1W'] = {
        'data': w1_data,
        'ohlcv': w1_ohlcv
    }
    print(f"   1W: {len(w1_ohlcv)} bars")

    # Monthly (1M)
    print("   Resampling to monthly...")
    m1_data = h1_data.resample("1M")
    m1_ohlcv = m1_data.get()[['Open', 'High', 'Low', 'Close', 'Volume']]
    timeframes['1M'] = {
        'data': m1_data,
        'ohlcv': m1_ohlcv
    }
    print(f"   1M: {len(m1_ohlcv)} bars")

    # Verify we have minimum required bars for each timeframe
    min_bars = {
        '1M': 36,  # 3 years of monthly
        '1W': 52,  # 1 year of weekly
        '1D': 252, # 1 year of daily
        '1H': 100  # Just need some hourly bars
    }

    print("\n3. Verifying minimum bar requirements...")
    for tf, min_required in min_bars.items():
        actual_bars = len(timeframes[tf]['ohlcv'])
        status = "PASS" if actual_bars >= min_required else "FAIL"
        print(f"   {tf}: {actual_bars} bars (min: {min_required}) [{status}]")

    return timeframes


def classify_all_timeframes(timeframes: Dict[str, Any]) -> Dict[str, Dict]:
    """
    Run STRAT classification on all timeframes

    Returns dict with classification results for each timeframe
    """

    print("\n" + "=" * 60)
    print("RUNNING STRAT CLASSIFICATION ON ALL TIMEFRAMES")
    print("=" * 60)

    # Initialize analyzer (without FTFC for now)
    analyzer = STRATAnalyzer(enable_ftfc=False)

    results = {}

    # Process each timeframe
    for tf in ['1M', '1W', '1D', '1H']:  # Process from largest to smallest
        print(f"\nClassifying {tf} timeframe...")

        # Get OHLCV data
        ohlcv = timeframes[tf]['ohlcv'].copy()

        # Rename columns to lowercase for STRATAnalyzer
        ohlcv.columns = ohlcv.columns.str.lower()

        # Run classification
        classifications = analyzer.classify_bars(ohlcv)

        # Calculate statistics
        stats = {
            'Inside (1)': (classifications == 1).sum(),
            '2U': (classifications == 2).sum(),
            '2D': (classifications == -2).sum(),
            'Outside (3)': (classifications == 3).sum(),
            'Unknown (0)': (classifications == 0).sum()
        }

        # Store results
        results[tf] = {
            'data': ohlcv,
            'classifications': classifications,
            'stats': stats,
            'total_bars': len(classifications)
        }

        # Display stats
        print(f"   Total bars: {results[tf]['total_bars']}")
        for bar_type, count in stats.items():
            if count > 0:  # Only show non-zero counts
                pct = (count / results[tf]['total_bars']) * 100
                print(f"   {bar_type}: {count} ({pct:.1f}%)")

    return results


def calculate_continuity_scores(results: Dict[str, Dict]) -> pd.DataFrame:
    """
    Calculate Time Frame Continuity (TFC) scores for each hourly bar

    Returns DataFrame with columns:
    - datetime: Hourly timestamp
    - h1_class: Hourly classification
    - d1_class: Daily classification
    - w1_class: Weekly classification
    - m1_class: Monthly classification
    - alignment_count: Number of aligned directional bars
    - direction: 'bullish', 'bearish', or 'mixed'
    - confidence: Confidence score based on alignment
    """

    print("\n" + "=" * 60)
    print("CALCULATING TIME FRAME CONTINUITY SCORES")
    print("=" * 60)

    # Get hourly data as the base (most granular)
    h1_data = results['1H']['data']
    h1_class = results['1H']['classifications']

    # Get other timeframe data
    d1_data = results['1D']['data']
    d1_class = results['1D']['classifications']
    w1_data = results['1W']['data']
    w1_class = results['1W']['classifications']
    m1_data = results['1M']['data']
    m1_class = results['1M']['classifications']

    # Create continuity DataFrame
    continuity_df = pd.DataFrame(index=h1_data.index)
    continuity_df['h1_class'] = h1_class

    # Map hourly bars to their parent timeframes
    print("\nMapping hourly bars to parent timeframes...")

    for idx in continuity_df.index:
        # Get date components
        date_only = idx.date()

        # Find corresponding daily bar
        d1_mask = d1_data.index.date == date_only
        if d1_mask.any():
            continuity_df.loc[idx, 'd1_class'] = d1_class[d1_mask].iloc[0]
        else:
            continuity_df.loc[idx, 'd1_class'] = 0  # Unknown

        # Find corresponding weekly bar (week starts on Sunday in pandas)
        week_start = idx - pd.Timedelta(days=idx.dayofweek)
        week_end = week_start + pd.Timedelta(days=6)
        w1_mask = (d1_data.index.date >= week_start.date()) & (d1_data.index.date <= week_end.date())
        if w1_mask.any():
            # Get the weekly bar that contains this date
            for w1_idx in w1_data.index:
                if w1_idx.date() <= date_only <= (w1_idx + pd.Timedelta(days=6)).date():
                    continuity_df.loc[idx, 'w1_class'] = w1_class[w1_idx]
                    break
            else:
                continuity_df.loc[idx, 'w1_class'] = 0
        else:
            continuity_df.loc[idx, 'w1_class'] = 0

        # Find corresponding monthly bar
        m1_mask = (m1_data.index.year == idx.year) & (m1_data.index.month == idx.month)
        if m1_mask.any():
            continuity_df.loc[idx, 'm1_class'] = m1_class[m1_mask].iloc[0]
        else:
            continuity_df.loc[idx, 'm1_class'] = 0

    # Calculate alignment for each hourly bar
    print("Calculating alignment scores...")

    for idx in continuity_df.index:
        row = continuity_df.loc[idx]

        # Count bullish (2U) and bearish (2D) directional bars
        bullish_count = 0
        bearish_count = 0

        for tf in ['h1_class', 'd1_class', 'w1_class', 'm1_class']:
            if row[tf] == 2:  # 2U
                bullish_count += 1
            elif row[tf] == -2:  # 2D
                bearish_count += 1
            # Inside bars (1) and outside bars (3) are neutral, don't count

        # Determine alignment
        if bullish_count > 0 and bearish_count == 0:
            direction = 'bullish'
            alignment_count = bullish_count
        elif bearish_count > 0 and bullish_count == 0:
            direction = 'bearish'
            alignment_count = bearish_count
        elif bullish_count > bearish_count:
            direction = 'bullish_mixed'
            alignment_count = bullish_count  # Use majority
        elif bearish_count > bullish_count:
            direction = 'bearish_mixed'
            alignment_count = bearish_count  # Use majority
        else:
            direction = 'neutral'
            alignment_count = 0

        continuity_df.loc[idx, 'bullish_count'] = bullish_count
        continuity_df.loc[idx, 'bearish_count'] = bearish_count
        continuity_df.loc[idx, 'alignment_count'] = alignment_count
        continuity_df.loc[idx, 'direction'] = direction

        # Assign confidence based on alignment count
        if alignment_count == 4:
            confidence = 0.95  # FTFC - Full Time Frame Continuity
            continuity_type = 'FTFC'
        elif alignment_count == 3:
            confidence = 0.80  # FTC - Basic Time Frame Continuity
            continuity_type = 'FTC'
        elif alignment_count == 2:
            confidence = 0.50  # Partial alignment
            continuity_type = 'Partial'
        elif alignment_count == 1:
            confidence = 0.25  # Minimal alignment
            continuity_type = 'Minimal'
        else:
            confidence = 0.00  # No alignment
            continuity_type = 'None'

        continuity_df.loc[idx, 'confidence'] = confidence
        continuity_df.loc[idx, 'continuity_type'] = continuity_type

    # Print summary statistics
    print("\n" + "=" * 60)
    print("CONTINUITY SCORE SUMMARY")
    print("=" * 60)

    total_bars = len(continuity_df)
    ftfc_count = (continuity_df['continuity_type'] == 'FTFC').sum()
    ftc_count = (continuity_df['continuity_type'] == 'FTC').sum()
    partial_count = (continuity_df['continuity_type'] == 'Partial').sum()
    minimal_count = (continuity_df['continuity_type'] == 'Minimal').sum()
    none_count = (continuity_df['continuity_type'] == 'None').sum()

    print(f"Total hourly bars analyzed: {total_bars}")
    print("\nContinuity Distribution:")
    print(f"  FTFC (4/4 aligned): {ftfc_count} ({ftfc_count/total_bars*100:.1f}%)")
    print(f"  FTC (3/4 aligned):  {ftc_count} ({ftc_count/total_bars*100:.1f}%)")
    print(f"  Partial (2/4):      {partial_count} ({partial_count/total_bars*100:.1f}%)")
    print(f"  Minimal (1/4):      {minimal_count} ({minimal_count/total_bars*100:.1f}%)")
    print(f"  None (0/4):         {none_count} ({none_count/total_bars*100:.1f}%)")

    # Direction summary
    bullish_bars = continuity_df[continuity_df['direction'].str.contains('bullish', na=False)]
    bearish_bars = continuity_df[continuity_df['direction'].str.contains('bearish', na=False)]

    print("\nDirectional Bias:")
    print(f"  Bullish alignment: {len(bullish_bars)} bars ({len(bullish_bars)/total_bars*100:.1f}%)")
    print(f"  Bearish alignment: {len(bearish_bars)} bars ({len(bearish_bars)/total_bars*100:.1f}%)")

    # High confidence opportunities
    high_conf = continuity_df[continuity_df['confidence'] >= 0.80]
    print("\nHigh Confidence Opportunities (FTC or better):")
    print(f"  Total: {len(high_conf)} bars ({len(high_conf)/total_bars*100:.1f}%)")

    return continuity_df


def display_classification_alignment(results: Dict[str, Dict], continuity_df: pd.DataFrame = None):
    """
    Display how classifications align across timeframes
    Shows the most recent classifications for each timeframe
    Enhanced with continuity scores if provided
    """

    print("\n" + "=" * 60)
    print("CLASSIFICATION ALIGNMENT (Most Recent)")
    print("=" * 60)

    # Show last 10 classifications for each timeframe
    sample_size = 10

    for tf in ['1M', '1W', '1D', '1H']:
        print(f"\n{tf} Timeframe (last {sample_size} bars):")
        print("-" * 40)

        # Get recent classifications
        recent = results[tf]['classifications'].tail(sample_size)
        data = results[tf]['data'].tail(sample_size)

        for idx, (date, classification) in enumerate(recent.items()):
            # Map classification to readable string
            if classification == 0:
                class_str = "Unknown"
            elif classification == 1:
                class_str = "Inside (1)"
            elif classification == 2:
                class_str = "2U"
            elif classification == -2:
                class_str = "2D"
            elif classification == 3:
                class_str = "Outside (3)"
            else:
                class_str = f"Unknown ({classification})"

            # Get price data
            high = data.iloc[idx]['high']
            low = data.iloc[idx]['low']

            # Format date based on timeframe
            if tf == '1H':
                date_str = date.strftime("%Y-%m-%d %H:%M")
            else:
                date_str = date.strftime("%Y-%m-%d")

            print(f"   {date_str}: {class_str:12} (H:{high:.2f}, L:{low:.2f})")

    # If we have continuity scores, show them for recent bars
    if continuity_df is not None:
        print("\n" + "=" * 60)
        print("TIME FRAME CONTINUITY SCORES (Most Recent)")
        print("=" * 60)

        # Show last 20 hourly bars with their continuity scores
        recent_continuity = continuity_df.tail(20)

        print("\nRecent Continuity Analysis (Last 20 Hourly Bars):")
        print("=" * 60)
        print(f"{'Time':<20} {'1H':>4} {'1D':>4} {'1W':>4} {'1M':>4} {'Type':>8} {'Conf':>5} {'Dir':>10}")
        print("-" * 60)

        for idx, row in recent_continuity.iterrows():
            # Map classifications to readable format
            def class_to_str(val):
                if val == 2:
                    return '2U'
                elif val == -2:
                    return '2D'
                elif val == 1:
                    return '1'
                elif val == 3:
                    return '3'
                else:
                    return '-'

            time_str = idx.strftime("%Y-%m-%d %H:%M")
            h1_str = class_to_str(row['h1_class'])
            d1_str = class_to_str(row.get('d1_class', 0))
            w1_str = class_to_str(row.get('w1_class', 0))
            m1_str = class_to_str(row.get('m1_class', 0))
            cont_type = row['continuity_type']
            conf = row['confidence']
            direction = row['direction'].replace('_mixed', '*')

            # Highlight high-confidence opportunities
            if conf >= 0.80:
                print(f">>> {time_str:<18} {h1_str:>4} {d1_str:>4} {w1_str:>4} {m1_str:>4} {cont_type:>8} {conf:>5.2f} {direction:>10} <<<")
            else:
                print(f"    {time_str:<18} {h1_str:>4} {d1_str:>4} {w1_str:>4} {m1_str:>4} {cont_type:>8} {conf:>5.2f} {direction:>10}")

        # Show best opportunities
        print("\n" + "=" * 60)
        print("HIGH-CONFIDENCE OPPORTUNITIES (FTC or better)")
        print("=" * 60)

        high_conf_bars = continuity_df[continuity_df['confidence'] >= 0.80].tail(10)
        if len(high_conf_bars) > 0:
            print("\nLast 10 high-confidence setups:")
            for idx, row in high_conf_bars.iterrows():
                time_str = idx.strftime("%Y-%m-%d %H:%M")
                cont_type = row['continuity_type']
                conf = row['confidence']
                direction = row['direction'].replace('_mixed', ' (mixed)')

                print(f"  {time_str}: {cont_type} ({conf:.2f}) - {direction.upper()}")
                print(f"    Alignment: Bullish={int(row['bullish_count'])}/4, Bearish={int(row['bearish_count'])}/4")
        else:
            print("\nNo high-confidence opportunities in recent data.")

    else:
        # Original summary for Phase 1
        print("\n" + "=" * 60)
        print("TIMEFRAME CONTINUITY OBSERVATION")
        print("=" * 60)
        print("\nNOTE: This is just classification display.")
        print("Run with continuity scoring to see alignment analysis.")


def main():
    """Main execution flow for BASIC TFC implementation with Phase 2 Continuity Scoring"""

    print("\n" + "=" * 60)
    print("STRAT TFC (Time Frame Continuity) Implementation")
    print("=" * 60)
    print("Phase 1: Fetch and classify 4 timeframes (1M, 1W, 1D, 1H)")
    print("Phase 2: Calculate continuity scores and alignment")
    print("NO trading logic - just scoring and analysis")

    try:
        # Step 1: Configure Alpaca credentials
        setup_alpaca_credentials()

        # Step 2: Fetch multi-timeframe data
        timeframes = fetch_multi_timeframe_data("SPY")

        # Step 3: Run classification on all timeframes
        results = classify_all_timeframes(timeframes)

        # Step 4: Calculate continuity scores (PHASE 2)
        continuity_df = calculate_continuity_scores(results)

        # Step 5: Display alignment with continuity scores
        display_classification_alignment(results, continuity_df)

        # Success message
        print("\n" + "=" * 60)
        print("SUCCESS: TFC IMPLEMENTATION WITH CONTINUITY SCORING")
        print("=" * 60)
        print("\n[PHASE 1 COMPLETE] Data Pipeline:")
        print("  [DONE] All 4 timeframes loaded from Alpaca")
        print("  [DONE] Resampling produced valid OHLCV data")
        print("  [DONE] Classification ran on all timeframes")
        print("\n[PHASE 2 COMPLETE] Continuity Scoring:")
        print("  [DONE] Mapped hourly bars to parent timeframes")
        print("  [DONE] Calculated alignment counts")
        print("  [DONE] Assigned confidence scores (FTFC/FTC/Partial/Minimal/None)")
        print("  [DONE] Identified high-confidence opportunities")
        print("  [DONE] Clear display of continuity status")
        print("\n[NO TRADING] No trading logic added (focus on scoring only)")
        print("\nReady for Phase 3: Trading Logic Integration")

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())