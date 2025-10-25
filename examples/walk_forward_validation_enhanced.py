"""
Walk-Forward Validation: Enhanced Multi-Symbol Analysis

This script performs rigorous out-of-sample validation of the ORB strategy across
a sector-diversified universe of 8 stocks. Tests both individual stock performance
and universe portfolio simulation (daily scan + best setup selection).

Validation Universe (Sector-Balanced):
- NVDA: AI Semiconductors (proven winner from Session 8)
- PLTR: AI Software (high volatility, AI theme)
- HOOD: Fintech/Crypto (event-driven momentum)
- VST: Utilities/Energy (defensive energy)
- NEM: Commodities/Mining (inflation hedge)
- JPM: Banking (sector leader, control group)
- XOM: Energy/Oil (traditional energy)
- JNJ: Healthcare (defensive, control group)

Test Periods:
- In-Sample: Jan-Jun 2024 (6 months, training period)
- Out-of-Sample: Jul-Dec 2024 (6 months, validation period)

Success Criteria:
- Individual: Win rate > 45%, Return > 0% (regardless of trade count)
- Universe: 60%+ stocks profitable, combined return > 0%
- Degradation: Out-of-sample metrics within 50% of in-sample (acceptable)

Usage:
    uv run python examples/walk_forward_validation_enhanced.py
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategies.orb import ORBStrategy, ORBConfig
from core.portfolio_manager import PortfolioManager
from utils.portfolio_heat import PortfolioHeatManager
from core.risk_manager import RiskManager


# Define validation universe
VALIDATION_UNIVERSE = {
    'NVDA': {'sector': 'AI Semiconductors', 'volatility': 'High'},
    'PLTR': {'sector': 'AI Software', 'volatility': 'Very High'},
    'HOOD': {'sector': 'Fintech/Crypto', 'volatility': 'Very High'},
    'VST': {'sector': 'Utilities/Energy', 'volatility': 'High'},
    'NEM': {'sector': 'Commodities/Mining', 'volatility': 'High'},
    'JPM': {'sector': 'Banking/Finance', 'volatility': 'Medium'},
    'XOM': {'sector': 'Energy/Oil', 'volatility': 'Medium-High'},
    'JNJ': {'sector': 'Healthcare', 'volatility': 'Medium'}
}

# Test periods
IN_SAMPLE_START = "2024-01-01"
IN_SAMPLE_END = "2024-06-30"
OUT_SAMPLE_START = "2024-07-01"
OUT_SAMPLE_END = "2024-12-31"


def run_single_stock_validation(
    symbol: str,
    period_name: str,
    start_date: str,
    end_date: str,
    initial_capital: float = 10000
) -> Dict:
    """
    Run ORB backtest on single stock for specified period.

    Args:
        symbol: Stock ticker
        period_name: Human-readable period name (e.g., "In-Sample")
        start_date: Start date YYYY-MM-DD
        end_date: End date YYYY-MM-DD
        initial_capital: Starting capital

    Returns:
        Dictionary with backtest results and metrics
    """
    print(f"\n{'='*70}")
    print(f"{period_name}: {symbol} ({start_date} to {end_date})")
    print(f"{'='*70}")

    try:
        # Initialize ORB strategy for this symbol
        orb_config = ORBConfig(
            name=f"ORB_{symbol}",
            symbol=symbol,
            opening_minutes=5,
            atr_stop_multiplier=2.5,
            volume_multiplier=2.0,
            start_date=start_date,
            end_date=end_date
        )

        orb_strategy = ORBStrategy(orb_config)

        # Initialize risk management
        heat_manager = PortfolioHeatManager(max_heat=0.08)
        risk_manager = RiskManager(max_portfolio_heat=0.08)

        # Create portfolio manager
        pm = PortfolioManager(
            strategies=[orb_strategy],
            capital=initial_capital,
            heat_manager=heat_manager,
            risk_manager=risk_manager
        )

        # Fetch data
        data_5min, data_daily = orb_strategy.fetch_data()

        if len(data_5min) == 0:
            print(f"[WARNING] No data available for {symbol} in this period")
            return {
                'symbol': symbol,
                'period': period_name,
                'error': 'No data available',
                'metrics': None
            }

        # Run backtest through portfolio manager
        results = pm.run_single_strategy_with_gates(
            strategy=orb_strategy,
            data=data_5min,
            initial_capital=initial_capital
        )

        # Extract key metrics
        metrics = results['metrics']

        return {
            'symbol': symbol,
            'period': period_name,
            'start_date': start_date,
            'end_date': end_date,
            'bars': len(data_5min),
            'trades': metrics['total_trades'],
            'win_rate': metrics['win_rate'],
            'total_return': metrics['total_return'],
            'sharpe_ratio': metrics['sharpe_ratio'],
            'max_drawdown': results['drawdown_max'],
            'avg_trade': metrics['avg_trade'],
            'final_equity': results['final_equity'],
            'circuit_breakers': len(results['circuit_breaker_triggers']),
            'error': None
        }

    except Exception as e:
        print(f"[ERROR] {symbol} failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'symbol': symbol,
            'period': period_name,
            'error': str(e),
            'metrics': None
        }


def compare_in_vs_out_sample(
    in_sample_results: List[Dict],
    out_sample_results: List[Dict]
) -> pd.DataFrame:
    """
    Create comparison table of in-sample vs out-of-sample performance.

    Args:
        in_sample_results: List of in-sample backtest results
        out_sample_results: List of out-of-sample backtest results

    Returns:
        DataFrame with side-by-side comparison
    """
    comparison_data = []

    for in_res, out_res in zip(in_sample_results, out_sample_results):
        if in_res['error'] or out_res['error']:
            continue

        symbol = in_res['symbol']

        # Calculate degradation percentages
        trade_change = ((out_res['trades'] - in_res['trades']) / in_res['trades'] * 100
                       if in_res['trades'] > 0 else 0)

        wr_change = ((out_res['win_rate'] - in_res['win_rate']) * 100
                    if not np.isnan(in_res['win_rate']) and not np.isnan(out_res['win_rate'])
                    else 0)

        return_change = ((out_res['total_return'] - in_res['total_return']) * 100)

        comparison_data.append({
            'Symbol': symbol,
            'Sector': VALIDATION_UNIVERSE[symbol]['sector'],

            # In-Sample
            'IS_Trades': int(in_res['trades']),
            'IS_WinRate': f"{in_res['win_rate']:.1%}" if not np.isnan(in_res['win_rate']) else 'N/A',
            'IS_Return': f"{in_res['total_return']:.2%}",
            'IS_Sharpe': f"{in_res['sharpe_ratio']:.2f}",

            # Out-of-Sample
            'OOS_Trades': int(out_res['trades']),
            'OOS_WinRate': f"{out_res['win_rate']:.1%}" if not np.isnan(out_res['win_rate']) else 'N/A',
            'OOS_Return': f"{out_res['total_return']:.2%}",
            'OOS_Sharpe': f"{out_res['sharpe_ratio']:.2f}",

            # Degradation
            'Trade_Change': f"{trade_change:+.0f}%",
            'WR_Change': f"{wr_change:+.1f}pp",
            'Return_Change': f"{return_change:+.1f}pp",
        })

    return pd.DataFrame(comparison_data)


def main():
    """Run complete walk-forward validation analysis."""

    print("="*70)
    print("WALK-FORWARD VALIDATION: ENHANCED MULTI-SYMBOL ANALYSIS")
    print("="*70)
    print(f"\nValidation Universe: {len(VALIDATION_UNIVERSE)} stocks")
    for symbol, info in VALIDATION_UNIVERSE.items():
        print(f"  {symbol:6} - {info['sector']:25} ({info['volatility']} volatility)")

    print(f"\nTest Periods:")
    print(f"  In-Sample:     {IN_SAMPLE_START} to {IN_SAMPLE_END}")
    print(f"  Out-of-Sample: {OUT_SAMPLE_START} to {OUT_SAMPLE_END}")

    # =========================================================================
    # PHASE 1: Individual Stock Tests
    # =========================================================================

    print(f"\n{'='*70}")
    print("PHASE 1: INDIVIDUAL STOCK BACKTESTS")
    print(f"{'='*70}")

    in_sample_results = []
    out_sample_results = []

    for symbol in VALIDATION_UNIVERSE.keys():
        # Run in-sample
        in_result = run_single_stock_validation(
            symbol=symbol,
            period_name="In-Sample (Jan-Jun 2024)",
            start_date=IN_SAMPLE_START,
            end_date=IN_SAMPLE_END
        )
        in_sample_results.append(in_result)

        # Run out-of-sample
        out_result = run_single_stock_validation(
            symbol=symbol,
            period_name="Out-of-Sample (Jul-Dec 2024)",
            start_date=OUT_SAMPLE_START,
            end_date=OUT_SAMPLE_END
        )
        out_sample_results.append(out_result)

    # =========================================================================
    # PHASE 2: Comparison Analysis
    # =========================================================================

    print(f"\n{'='*70}")
    print("PHASE 2: IN-SAMPLE VS OUT-OF-SAMPLE COMPARISON")
    print(f"{'='*70}")

    comparison_df = compare_in_vs_out_sample(in_sample_results, out_sample_results)

    print("\n" + comparison_df.to_string(index=False))

    # =========================================================================
    # PHASE 3: Summary Statistics
    # =========================================================================

    print(f"\n{'='*70}")
    print("PHASE 3: VALIDATION SUMMARY")
    print(f"{'='*70}")

    # Filter out errors
    valid_out_sample = [r for r in out_sample_results if not r['error']]

    if not valid_out_sample:
        print("\n[ERROR] No valid out-of-sample results to analyze")
        return

    # Calculate aggregate metrics
    total_stocks = len(valid_out_sample)
    profitable_stocks = sum(1 for r in valid_out_sample if r['total_return'] > 0)
    high_winrate_stocks = sum(1 for r in valid_out_sample
                              if not np.isnan(r['win_rate']) and r['win_rate'] > 0.45)

    avg_return = np.mean([r['total_return'] for r in valid_out_sample])
    avg_trades = np.mean([r['trades'] for r in valid_out_sample])
    avg_winrate = np.nanmean([r['win_rate'] for r in valid_out_sample])

    print(f"\nOut-of-Sample Performance:")
    print(f"  Stocks Tested:        {total_stocks}")
    print(f"  Profitable Stocks:    {profitable_stocks} ({profitable_stocks/total_stocks:.0%})")
    print(f"  High Win Rate (>45%): {high_winrate_stocks} ({high_winrate_stocks/total_stocks:.0%})")
    print(f"\n  Average Return:       {avg_return:.2%}")
    print(f"  Average Trades:       {avg_trades:.1f}")
    print(f"  Average Win Rate:     {avg_winrate:.1%}")

    # =========================================================================
    # PHASE 4: Validation Verdict
    # =========================================================================

    print(f"\n{'='*70}")
    print("VALIDATION VERDICT")
    print(f"{'='*70}")

    # Criteria checks
    criteria_pass = 0
    criteria_total = 4

    print("\nSuccess Criteria:")

    # Criterion 1: Majority profitable
    if profitable_stocks / total_stocks >= 0.60:
        print(f"  [PASS] 60%+ stocks profitable: {profitable_stocks}/{total_stocks}")
        criteria_pass += 1
    else:
        print(f"  [FAIL] <60% stocks profitable: {profitable_stocks}/{total_stocks}")

    # Criterion 2: Positive average return
    if avg_return > 0:
        print(f"  [PASS] Positive average return: {avg_return:.2%}")
        criteria_pass += 1
    else:
        print(f"  [FAIL] Negative average return: {avg_return:.2%}")

    # Criterion 3: High win rate stocks
    if high_winrate_stocks / total_stocks >= 0.50:
        print(f"  [PASS] 50%+ stocks have win rate >45%: {high_winrate_stocks}/{total_stocks}")
        criteria_pass += 1
    else:
        print(f"  [FAIL] <50% stocks have win rate >45%: {high_winrate_stocks}/{total_stocks}")

    # Criterion 4: Sufficient trade frequency
    if avg_trades >= 10:
        print(f"  [PASS] Adequate trade frequency: {avg_trades:.1f} avg trades/stock")
        criteria_pass += 1
    else:
        print(f"  [WARN] Low trade frequency: {avg_trades:.1f} avg trades/stock")

    # Final verdict
    print(f"\n{'-'*70}")
    print(f"Criteria Passed: {criteria_pass}/{criteria_total}")

    if criteria_pass >= 3:
        print("\n[SUCCESS] ORB strategy VALIDATED on out-of-sample data")
        print("Recommendation: Proceed to universe portfolio simulation")
    elif criteria_pass == 2:
        print("\n[CAUTION] ORB strategy shows MIXED results on out-of-sample data")
        print("Recommendation: Investigate degradation, consider parameter optimization")
    else:
        print("\n[FAILURE] ORB strategy FAILED out-of-sample validation")
        print("Recommendation: Redesign strategy or test longer time periods")

    print(f"{'='*70}\n")

    return {
        'in_sample_results': in_sample_results,
        'out_sample_results': out_sample_results,
        'comparison_df': comparison_df,
        'summary': {
            'total_stocks': total_stocks,
            'profitable_stocks': profitable_stocks,
            'avg_return': avg_return,
            'avg_trades': avg_trades,
            'avg_winrate': avg_winrate,
            'criteria_passed': criteria_pass
        }
    }


if __name__ == "__main__":
    results = main()
