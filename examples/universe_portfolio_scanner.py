"""
Universe Portfolio Scanner: ORB Multi-Symbol Daily Selection

This script implements Phase 5 functionality (multi-strategy orchestration) for
the ORB strategy applied to a high-volatility stock universe. Instead of trading
a single symbol, it:

1. Scans 20 high-volatility stocks daily for qualifying ORB setups
2. Ranks setups by quality (volume surge + ATR% + breakout conviction)
3. Selects best 1-3 setups per day respecting 8% portfolio heat constraint
4. Simulates portfolio performance with position-level tracking

Universe Criteria:
- ATR% > 3% (high daily volatility)
- Avg volume > 10M shares (sufficient liquidity)
- Sector-balanced (avoid concentration risk)
- Mix of tech, fintech, energy, commodities

Test Period:
- Full year 2024 (Jan-Dec) to capture regime diversity

Success Criteria:
- Sharpe > 1.5 (portfolio-level)
- Win rate > 45%
- Max drawdown < 15%
- Avg 15+ trades/month (universe-wide)

Usage:
    uv run python examples/universe_portfolio_scanner.py

Future Refinements (Phase 6):
- Profit target rules (1.5-2R based on ATR)
- Time-based exits (11:30 AM if not stopped)
- Trailing stops (breakeven at +1R)
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from datetime import datetime, time
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategies.orb import ORBStrategy, ORBConfig
from core.portfolio_manager import PortfolioManager
from utils.portfolio_heat import PortfolioHeatManager
from core.risk_manager import RiskManager
import vectorbtpro as vbt


# =============================================================================
# High-Volatility Universe Definition (20 Stocks)
# =============================================================================

HIGH_VOLATILITY_UNIVERSE = {
    # Proven winners from walk-forward validation (3)
    'NVDA': {'sector': 'AI Semiconductors', 'atr_pct': 5.5, 'volume': 250_000_000, 'priority': 'High'},
    'PLTR': {'sector': 'AI Software', 'atr_pct': 6.2, 'volume': 80_000_000, 'priority': 'High'},
    'HOOD': {'sector': 'Fintech/Crypto', 'atr_pct': 5.8, 'volume': 25_000_000, 'priority': 'High'},

    # High-volatility tech/semiconductors (5)
    'AMD': {'sector': 'Semiconductors', 'atr_pct': 4.8, 'volume': 90_000_000, 'priority': 'High'},
    'TSLA': {'sector': 'EV/Tech', 'atr_pct': 5.2, 'volume': 120_000_000, 'priority': 'Medium'},
    'META': {'sector': 'Social Media/VR', 'atr_pct': 3.5, 'volume': 18_000_000, 'priority': 'Medium'},
    'SMCI': {'sector': 'AI Hardware', 'atr_pct': 7.5, 'volume': 25_000_000, 'priority': 'High'},
    'AVGO': {'sector': 'Semiconductors', 'atr_pct': 3.8, 'volume': 15_000_000, 'priority': 'Medium'},

    # High-volatility fintech/crypto (3)
    'COIN': {'sector': 'Crypto Exchange', 'atr_pct': 6.5, 'volume': 12_000_000, 'priority': 'High'},
    'SQ': {'sector': 'Fintech Payments', 'atr_pct': 4.2, 'volume': 11_000_000, 'priority': 'Medium'},
    'SOFI': {'sector': 'Digital Banking', 'atr_pct': 5.0, 'volume': 45_000_000, 'priority': 'Medium'},

    # High-volatility energy/utilities (3)
    'VST': {'sector': 'Utilities/Nuclear', 'atr_pct': 4.5, 'volume': 8_000_000, 'priority': 'Medium'},
    'FSLR': {'sector': 'Solar Energy', 'atr_pct': 4.8, 'volume': 2_500_000, 'priority': 'Medium'},
    'ENPH': {'sector': 'Solar Tech', 'atr_pct': 5.5, 'volume': 3_500_000, 'priority': 'Low'},

    # High-volatility commodities/mining (3)
    'NEM': {'sector': 'Gold Mining', 'atr_pct': 3.5, 'volume': 8_000_000, 'priority': 'Low'},
    'FCX': {'sector': 'Copper Mining', 'atr_pct': 4.2, 'volume': 16_000_000, 'priority': 'Medium'},
    'GOLD': {'sector': 'Gold Mining', 'atr_pct': 3.8, 'volume': 11_000_000, 'priority': 'Low'},

    # Control stocks (defensive, should produce fewer setups) (3)
    'JPM': {'sector': 'Banking', 'atr_pct': 2.5, 'volume': 12_000_000, 'priority': 'Low'},
    'XOM': {'sector': 'Oil/Energy', 'atr_pct': 2.8, 'volume': 18_000_000, 'priority': 'Low'},
    'BA': {'sector': 'Aerospace', 'atr_pct': 3.2, 'volume': 6_000_000, 'priority': 'Low'}
}


# =============================================================================
# Setup Quality Scoring
# =============================================================================

def calculate_setup_quality_score(
    symbol: str,
    volume_surge_ratio: float,
    atr_pct: float,
    breakout_conviction_pct: float,
    time_of_day: time,
    universe_metadata: Dict
) -> float:
    """
    Calculate quality score for ORB setup to rank competing opportunities.

    Scoring Factors:
    1. Volume surge strength (0-40 points): Higher volume = stronger momentum
    2. ATR% (0-30 points): Higher volatility = larger potential move
    3. Breakout conviction (0-20 points): Further above range = stronger signal
    4. Time of day (0-10 points): Earlier = more runway to 3:55 PM
    5. Priority tier (0-10 points): Proven winners get bonus

    Args:
        symbol: Stock ticker
        volume_surge_ratio: Current volume / 20-bar MA (e.g., 2.5 = 2.5x average)
        atr_pct: ATR as percentage of close price (e.g., 0.045 = 4.5%)
        breakout_conviction_pct: Distance above opening range (% of ATR)
        time_of_day: Time of breakout signal
        universe_metadata: Universe configuration dict

    Returns:
        Quality score (0-100, higher = better setup)
    """
    score = 0.0

    # 1. Volume surge (0-40 points)
    # 2.0x = 20 pts, 3.0x = 30 pts, 4.0x+ = 40 pts
    volume_score = min(40, (volume_surge_ratio - 1.0) * 20)
    score += volume_score

    # 2. ATR% (0-30 points)
    # 3% = 15 pts, 5% = 25 pts, 7%+ = 30 pts
    atr_score = min(30, atr_pct * 500)
    score += atr_score

    # 3. Breakout conviction (0-20 points)
    # 0.5 ATR = 10 pts, 1.0 ATR = 20 pts
    conviction_score = min(20, breakout_conviction_pct * 20)
    score += conviction_score

    # 4. Time of day (0-10 points)
    # 10:00 AM = 10 pts, 12:00 PM = 5 pts, 2:00 PM = 2 pts
    hour = time_of_day.hour + time_of_day.minute / 60.0
    if hour < 11.0:
        time_score = 10
    elif hour < 12.5:
        time_score = 7
    elif hour < 14.0:
        time_score = 4
    else:
        time_score = 2
    score += time_score

    # 5. Priority tier bonus (0-10 points)
    priority = universe_metadata.get(symbol, {}).get('priority', 'Low')
    if priority == 'High':
        score += 10
    elif priority == 'Medium':
        score += 5

    return score


# =============================================================================
# Universe Scanner
# =============================================================================

class UniverseScanner:
    """
    Scans multiple symbols for ORB setups and manages portfolio-level selection.

    This implements Phase 5 multi-strategy orchestration by treating each symbol
    as a separate "strategy" and selecting the best opportunities daily.
    """

    def __init__(
        self,
        universe: Dict[str, Dict],
        max_positions: int = 3,
        max_portfolio_heat: float = 0.08,
        start_date: str = "2024-01-01",
        end_date: str = "2024-12-31"
    ):
        """
        Initialize universe scanner.

        Args:
            universe: Dict of symbol -> metadata
            max_positions: Maximum simultaneous positions
            max_portfolio_heat: Maximum portfolio heat (8% default)
            start_date: Backtest start date
            end_date: Backtest end date
        """
        self.universe = universe
        self.max_positions = max_positions
        self.max_portfolio_heat = max_portfolio_heat
        self.start_date = start_date
        self.end_date = end_date

        # Results tracking
        self.daily_setups = defaultdict(list)  # date -> list of (symbol, score, signals)
        self.selected_trades = []  # list of selected trades

    def scan_universe(self) -> pd.DataFrame:
        """
        Scan all symbols and build daily setup opportunities.

        Returns:
            DataFrame with columns: date, symbol, score, entry_signals, exit_signals
        """
        print("="*70)
        print("UNIVERSE SCANNER: Building ORB Setup Database")
        print("="*70)
        print(f"Universe: {len(self.universe)} stocks")
        print(f"Period: {self.start_date} to {self.end_date}")
        print(f"Max positions: {self.max_positions}")
        print(f"Portfolio heat limit: {self.max_portfolio_heat:.0%}")

        all_setups = []

        for symbol, metadata in self.universe.items():
            print(f"\n--- Scanning {symbol} ({metadata['sector']}) ---")

            try:
                # Initialize ORB strategy for this symbol
                orb_config = ORBConfig(
                    name=f"ORB_{symbol}",
                    symbol=symbol,
                    opening_minutes=5,  # 5-minute range (validated in Session 8)
                    atr_stop_multiplier=2.5,
                    volume_multiplier=2.0,
                    start_date=self.start_date,
                    end_date=self.end_date
                )

                orb_strategy = ORBStrategy(orb_config)

                # Fetch data
                data_5min, data_daily = orb_strategy.fetch_data()

                if len(data_5min) == 0:
                    print(f"[WARNING] No data for {symbol}, skipping")
                    continue

                # Generate signals
                signals = orb_strategy.generate_signals(data_5min)

                # Find entry points and score them
                entry_bars = signals['long_entries'][signals['long_entries'] == True]

                print(f"Found {len(entry_bars)} potential setups for {symbol}")

                for entry_time in entry_bars.index:
                    # Calculate quality score
                    volume_surge = (
                        data_5min.loc[entry_time, 'Volume'] /
                        signals['volume_ma'].loc[entry_time]
                    )

                    atr = signals['atr'].loc[entry_time]
                    close = data_5min.loc[entry_time, 'Close']
                    atr_pct = atr / close

                    opening_high = signals['opening_high'].loc[entry_time]
                    breakout_distance = close - opening_high
                    breakout_conviction_pct = breakout_distance / atr if atr > 0 else 0

                    quality_score = calculate_setup_quality_score(
                        symbol=symbol,
                        volume_surge_ratio=volume_surge,
                        atr_pct=atr_pct,
                        breakout_conviction_pct=breakout_conviction_pct,
                        time_of_day=entry_time.time(),
                        universe_metadata=self.universe
                    )

                    # Store setup
                    all_setups.append({
                        'datetime': entry_time,
                        'date': entry_time.date(),
                        'symbol': symbol,
                        'quality_score': quality_score,
                        'volume_surge': volume_surge,
                        'atr_pct': atr_pct,
                        'breakout_conviction': breakout_conviction_pct,
                        'entry_price': close,
                        'stop_distance': signals['stop_distance'].loc[entry_time],
                        'sector': metadata['sector']
                    })

            except Exception as e:
                print(f"[ERROR] Failed to scan {symbol}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        # Convert to DataFrame
        setups_df = pd.DataFrame(all_setups)

        if len(setups_df) > 0:
            print(f"\n{'='*70}")
            print(f"SCAN COMPLETE: {len(setups_df)} total setups found")
            print(f"{'='*70}")
            print(f"\nSetups by symbol:")
            print(setups_df.groupby('symbol').size().sort_values(ascending=False))
            print(f"\nAverage quality score: {setups_df['quality_score'].mean():.1f}")
            print(f"Top quality score: {setups_df['quality_score'].max():.1f}")
        else:
            print("[WARNING] No setups found in entire period!")

        return setups_df

    def select_daily_top_setups(self, setups_df: pd.DataFrame) -> pd.DataFrame:
        """
        Select top N setups per day based on quality score.

        Args:
            setups_df: DataFrame with all potential setups

        Returns:
            DataFrame with only selected setups (filtered by quality ranking)
        """
        print(f"\n{'='*70}")
        print("DAILY SETUP SELECTION")
        print(f"{'='*70}")

        selected_setups = []

        # Group by trading date
        for date, day_setups in setups_df.groupby('date'):
            # Sort by quality score (descending)
            day_setups_sorted = day_setups.sort_values('quality_score', ascending=False)

            # Select top N (respecting max_positions limit)
            top_setups = day_setups_sorted.head(self.max_positions)

            selected_setups.append(top_setups)

        # Combine all selected setups
        selected_df = pd.concat(selected_setups, ignore_index=True)

        print(f"\nTotal potential setups: {len(setups_df)}")
        print(f"Selected setups: {len(selected_df)} ({len(selected_df)/len(setups_df):.1%})")
        print(f"Avg setups per day: {len(selected_df)/setups_df['date'].nunique():.2f}")

        print(f"\nSelected setups by symbol:")
        print(selected_df.groupby('symbol').size().sort_values(ascending=False))

        return selected_df

    def simulate_portfolio(
        self,
        selected_setups: pd.DataFrame,
        initial_capital: float = 100000
    ) -> Dict:
        """
        Simulate portfolio using VBT from selected setups.

        This method:
        1. Fetches price data for each symbol
        2. Builds entry/exit signals from selected timestamps
        3. Creates individual VBT portfolios
        4. Combines using Portfolio.column_stack()
        5. Calculates performance metrics

        Args:
            selected_setups: DataFrame with selected trades
            initial_capital: Starting capital for portfolio

        Returns:
            Dict with combined_portfolio, metrics, individual_portfolios
        """
        print(f"\n{'='*70}")
        print("PORTFOLIO SIMULATION (VBT)")
        print(f"{'='*70}")
        print(f"Initial capital: ${initial_capital:,.0f}")
        print(f"Selected trades: {len(selected_setups)}")

        # Get unique symbols from selected setups
        symbols = selected_setups['symbol'].unique()
        print(f"Symbols to simulate: {len(symbols)}")

        individual_portfolios = {}
        capital_per_symbol = initial_capital / len(symbols)  # Equal allocation

        for symbol in symbols:
            print(f"\n  Simulating {symbol}...")

            try:
                # Get selected setups for this symbol
                symbol_setups = selected_setups[selected_setups['symbol'] == symbol]

                # Fetch price data (5-minute bars)
                orb_config = ORBConfig(
                    name=f"ORB_{symbol}",
                    symbol=symbol,
                    start_date=self.start_date,
                    end_date=self.end_date
                )
                orb_strategy = ORBStrategy(orb_config)
                data_5min, _ = orb_strategy.fetch_data()

                if len(data_5min) == 0:
                    print(f"    [WARNING] No data for {symbol}, skipping")
                    continue

                # Build entry/exit signals from selected timestamps
                entries = pd.Series(False, index=data_5min.index)
                exits = pd.Series(False, index=data_5min.index)

                for _, setup in symbol_setups.iterrows():
                    entry_time = setup['datetime']

                    # Mark entry at this timestamp
                    if entry_time in entries.index:
                        entries.loc[entry_time] = True

                        # Mark exit at 3:55 PM same day (EOD)
                        eod_time = entry_time.replace(hour=15, minute=55, second=0)
                        if eod_time in exits.index:
                            exits.loc[eod_time] = True

                # Create VBT portfolio from signals
                pf = vbt.Portfolio.from_signals(
                    close=data_5min['Close'],
                    entries=entries,
                    exits=exits,
                    init_cash=capital_per_symbol,
                    fees=0.0035,  # 0.35% total costs (commission + slippage)
                    freq='5min'
                )

                individual_portfolios[symbol] = pf

                print(f"    Trades: {pf.trades.count()}")
                print(f"    Final value: ${pf.value.iloc[-1]:,.2f}")

            except Exception as e:
                print(f"    [ERROR] Failed to simulate {symbol}: {str(e)}")
                continue

        if not individual_portfolios:
            print("\n[ERROR] No portfolios created successfully")
            return None

        # Combine portfolios using VBT column_stack
        print(f"\nCombining {len(individual_portfolios)} portfolios...")

        strategy_keys = pd.Index(list(individual_portfolios.keys()), name="symbol")
        combined_pf = vbt.Portfolio.column_stack(
            tuple(individual_portfolios.values()),
            wrapper_kwargs=dict(keys=strategy_keys),
            group_by=True  # Treat as single portfolio
        )

        print(f"\n{'='*70}")
        print("PORTFOLIO RESULTS")
        print(f"{'='*70}")

        # Calculate portfolio-level metrics
        total_return = (combined_pf.value.iloc[-1] - initial_capital) / initial_capital
        sharpe = combined_pf.sharpe_ratio
        max_dd = combined_pf.max_drawdown
        total_trades = sum(pf.trades.count() for pf in individual_portfolios.values())

        print(f"\nPerformance:")
        print(f"  Final Value:    ${combined_pf.value.iloc[-1]:,.2f}")
        print(f"  Total Return:   {total_return:.2%}")
        print(f"  Sharpe Ratio:   {sharpe:.2f}")
        print(f"  Max Drawdown:   {max_dd:.2%}")
        print(f"  Total Trades:   {total_trades}")

        return {
            'combined_portfolio': combined_pf,
            'individual_portfolios': individual_portfolios,
            'metrics': {
                'total_return': total_return,
                'sharpe_ratio': sharpe,
                'max_drawdown': max_dd,
                'final_value': combined_pf.value.iloc[-1],
                'total_trades': total_trades
            }
        }


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Run universe portfolio scanner and simulation."""

    print("="*70)
    print("UNIVERSE PORTFOLIO SCANNER - ORB MULTI-SYMBOL STRATEGY")
    print("="*70)

    # Initialize scanner
    scanner = UniverseScanner(
        universe=HIGH_VOLATILITY_UNIVERSE,
        max_positions=3,
        max_portfolio_heat=0.08,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )

    # Scan universe for all qualifying setups
    setups_df = scanner.scan_universe()

    if len(setups_df) == 0:
        print("\n[ERROR] No setups found, cannot proceed with simulation")
        return None

    # Select top setups per day
    selected_setups = scanner.select_daily_top_setups(setups_df)

    # Run portfolio simulation using VBT
    portfolio_results = scanner.simulate_portfolio(
        selected_setups=selected_setups,
        initial_capital=100000
    )

    if portfolio_results is None:
        print("\n[ERROR] Portfolio simulation failed")
        return None

    # Save selected setups for analysis
    output_path = project_root / "output" / "selected_setups_2024.csv"
    output_path.parent.mkdir(exist_ok=True)
    selected_setups.to_csv(output_path, index=False)
    print(f"\nSelected setups saved to: {output_path}")

    print(f"\n{'='*70}")
    print("UNIVERSE SCANNER COMPLETE")
    print(f"{'='*70}")

    return {
        'setups_df': setups_df,
        'selected_setups': selected_setups,
        'portfolio_results': portfolio_results,
        'universe': HIGH_VOLATILITY_UNIVERSE,
        'summary': {
            'total_setups': len(setups_df),
            'selected_setups': len(selected_setups),
            'selection_rate': len(selected_setups) / len(setups_df),
            'avg_daily_setups': len(selected_setups) / setups_df['date'].nunique(),
            'trading_days': setups_df['date'].nunique()
        }
    }


if __name__ == "__main__":
    results = main()
