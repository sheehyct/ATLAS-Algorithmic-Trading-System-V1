"""
Opening Range Breakout (ORB) Strategy

Strategy Description:
- Entry: Breakout of first 30-minute range with directional bias and volume confirmation
- Exit: End-of-day (3:55 PM ET) OR ATR-based stop loss
- Position Sizing: ATR-based with capital constraint (from Week 1)

Research-Backed Requirements (MANDATORY):
1. Volume confirmation: 2.0× average volume (HARDCODED)
2. Directional bias: Opening bar close > open for longs
3. NO signal exits (RSI/MACD would cut winners)
4. ATR stops: 2.5× multiplier baseline
5. Target metrics: Sharpe > 2.0, R:R > 3:1, Net expectancy > 0.5%

Reference: STRATEGY_2_IMPLEMENTATION_ADDENDUM.md
"""

import pandas as pd
import numpy as np
import vectorbtpro as vbt
from datetime import time
from typing import Dict, Tuple, Optional
import pandas_market_calendars as mcal
import os
from dotenv import load_dotenv

from utils.position_sizing import calculate_position_size_atr

# Load environment variables
load_dotenv('config/.env')


class ORBStrategy:
    """
    Opening Range Breakout Strategy with mandatory volume confirmation.

    Parameters:
    -----------
    symbol : str
        Trading symbol (default: 'SPY')
    opening_minutes : int
        Opening range duration in minutes (default: 30)
    atr_period : int
        ATR calculation period (default: 14)
    atr_stop_multiplier : float
        ATR multiplier for stop distance (default: 2.5)
    risk_pct : float
        Risk percentage per trade (default: 0.02 = 2%)
    init_cash : float
        Initial capital (default: 10000)
    enable_shorts : bool
        Enable short entries (default: False)
    volume_multiplier : float
        Volume confirmation threshold (default: 2.0, HARDCODED per research)

    Attributes:
    -----------
    data_5min : pd.DataFrame
        5-minute OHLCV data
    data_daily : pd.DataFrame
        Daily OHLCV data (for ATR calculation)
    signals : dict
        Generated entry/exit signals
    """

    def __init__(
        self,
        symbol: str = 'SPY',
        opening_minutes: int = 30,
        atr_period: int = 14,
        atr_stop_multiplier: float = 2.5,
        risk_pct: float = 0.02,
        init_cash: float = 10000,
        enable_shorts: bool = False,
        volume_multiplier: float = 2.0  # HARDCODED per research
    ):
        self.symbol = symbol
        self.opening_minutes = opening_minutes
        self.atr_period = atr_period
        self.atr_stop_multiplier = atr_stop_multiplier
        self.risk_pct = risk_pct
        self.init_cash = init_cash
        self.enable_shorts = enable_shorts
        self.volume_multiplier = volume_multiplier

        # Data storage
        self.data_5min = None
        self.data_daily = None
        self.signals = None
        self.portfolio = None

    def fetch_data(
        self,
        start_date: str = '2016-01-01',
        end_date: str = '2025-10-14'
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch intraday and daily data from Alpaca.

        Args:
            start_date: Start date for backtesting (YYYY-MM-DD)
            end_date: End date for backtesting (YYYY-MM-DD)

        Returns:
            Tuple of (5min_data, daily_data)
        """
        # Get Alpaca credentials from environment
        # Using MID account (has Algo Trader Plus subscription)
        api_key = os.getenv('ALPACA_MID_KEY')
        api_secret = os.getenv('ALPACA_MID_SECRET')

        if not api_key or not api_secret:
            raise ValueError(
                "Alpaca MID account credentials not found. "
                "Ensure ALPACA_MID_KEY and ALPACA_MID_SECRET are set in config/.env"
            )

        # Configure Alpaca credentials (VectorBT Pro proper method)
        vbt.AlpacaData.set_custom_settings(
            client_config=dict(
                api_key=api_key,
                secret_key=api_secret
            )
        )

        # Fetch 5-minute data for intraday signals
        # tz parameter ensures consistent timezone handling (VBT Pro best practice)
        data_5min = vbt.AlpacaData.pull(
            self.symbol,
            start=start_date,
            end=end_date,
            timeframe='5Min',
            tz='America/New_York'  # NYSE timezone for consistent alignment
        ).get()  # Official VBT Pro method to extract DataFrame

        # Fetch daily data for ATR calculation
        # tz parameter ensures timezone matches intraday data
        data_daily = vbt.AlpacaData.pull(
            self.symbol,
            start=start_date,
            end=end_date,
            timeframe='1D',
            tz='America/New_York'  # Same timezone as intraday data
        ).get()  # Official VBT Pro method to extract DataFrame

        # Filter to RTH only (9:30 AM - 4:00 PM ET)
        data_5min = data_5min.between_time('09:30', '16:00')

        # Filter NYSE trading days only (no weekends/holidays)
        nyse = mcal.get_calendar('NYSE')
        trading_days = nyse.valid_days(start_date=start_date, end_date=end_date)

        data_5min = data_5min[data_5min.index.normalize().isin(trading_days)]
        data_daily = data_daily[data_daily.index.isin(trading_days)]

        self.data_5min = data_5min
        self.data_daily = data_daily

        print(f"Fetched 5-minute data: {len(data_5min)} bars")
        print(f"Fetched daily data: {len(data_daily)} bars")
        print(f"Date range: {data_5min.index[0]} to {data_5min.index[-1]}")

        return data_5min, data_daily

    def calculate_opening_range(self) -> Dict[str, pd.Series]:
        """
        Calculate opening range for each trading day.

        Returns:
            Dict containing:
            - opening_high: Highest price in first N minutes
            - opening_low: Lowest price in first N minutes
            - opening_close: Last close in opening range
            - opening_open: First open in opening range
        """
        if self.data_5min is None:
            raise ValueError("Must fetch data first using fetch_data()")

        # Group by trading day
        daily_groups = self.data_5min.groupby(self.data_5min.index.date)

        opening_high_list = []
        opening_low_list = []
        opening_close_list = []
        opening_open_list = []
        dates = []

        # Calculate opening range for each day
        for date, day_data in daily_groups:
            # Get first N minutes (opening range)
            # For 30 minutes, that's first 6 bars of 5-minute data
            n_bars = self.opening_minutes // 5
            opening_bars = day_data.iloc[:n_bars]

            if len(opening_bars) < n_bars:
                # Skip days with insufficient data
                continue

            opening_high_list.append(opening_bars['High'].max())
            opening_low_list.append(opening_bars['Low'].min())
            opening_close_list.append(opening_bars['Close'].iloc[-1])
            opening_open_list.append(opening_bars['Open'].iloc[0])
            # Make timestamp timezone-aware to match intraday data
            dates.append(pd.Timestamp(date, tz=self.data_5min.index.tz))

        # Create Series with daily values (timezone-aware index)
        opening_high = pd.Series(opening_high_list, index=dates, name='opening_high')
        opening_low = pd.Series(opening_low_list, index=dates, name='opening_low')
        opening_close = pd.Series(opening_close_list, index=dates, name='opening_close')
        opening_open = pd.Series(opening_open_list, index=dates, name='opening_open')

        # Forward-fill to all intraday bars
        opening_high_ff = opening_high.reindex(
            self.data_5min.index.normalize(), method='ffill'
        ).reindex(self.data_5min.index, method='ffill')

        opening_low_ff = opening_low.reindex(
            self.data_5min.index.normalize(), method='ffill'
        ).reindex(self.data_5min.index, method='ffill')

        opening_close_ff = opening_close.reindex(
            self.data_5min.index.normalize(), method='ffill'
        ).reindex(self.data_5min.index, method='ffill')

        opening_open_ff = opening_open.reindex(
            self.data_5min.index.normalize(), method='ffill'
        ).reindex(self.data_5min.index, method='ffill')

        return {
            'opening_high': opening_high_ff,
            'opening_low': opening_low_ff,
            'opening_close': opening_close_ff,
            'opening_open': opening_open_ff
        }

    def generate_signals(self) -> Dict[str, pd.Series]:
        """
        Generate entry/exit signals with MANDATORY volume confirmation.

        Returns:
            Dict containing:
            - long_entries: Boolean Series for long entries
            - short_entries: Boolean Series for short entries
            - long_exits: Boolean Series for long exits (EOD)
            - short_exits: Boolean Series for short exits (EOD)
            - stop_distance: ATR-based stop distance
            - volume_confirmed: Boolean Series tracking volume filter
        """
        if self.data_5min is None or self.data_daily is None:
            raise ValueError("Must fetch data first using fetch_data()")

        # Calculate opening range
        opening_range = self.calculate_opening_range()
        opening_high = opening_range['opening_high']
        opening_low = opening_range['opening_low']
        opening_close = opening_range['opening_close']
        opening_open = opening_range['opening_open']

        # Directional bias from opening bar
        bullish_opening = opening_close > opening_open
        bearish_opening = opening_close < opening_open

        # Price breakout signals
        price_breakout_long = self.data_5min['Close'] > opening_high
        price_breakout_short = self.data_5min['Close'] < opening_low

        # CRITICAL: Volume confirmation (MANDATORY, HARDCODED at 2.0×)
        volume_ma = self.data_5min['Volume'].rolling(window=20).mean()
        volume_surge = self.data_5min['Volume'] > (volume_ma * self.volume_multiplier)

        # Calculate ATR for stops (on daily timeframe)
        atr_indicator = vbt.talib("ATR").run(
            self.data_daily['High'],
            self.data_daily['Low'],
            self.data_daily['Close'],
            timeperiod=self.atr_period
        )
        atr_daily = atr_indicator.real

        # Forward-fill ATR to intraday bars
        atr_intraday = atr_daily.reindex(
            self.data_5min.index.normalize(), method='ffill'
        ).reindex(self.data_5min.index, method='ffill')

        stop_distance = atr_intraday * self.atr_stop_multiplier

        # Time filter: Only allow entries after opening range ends
        # For 30-minute opening range, entries start at 10:00 AM
        entry_start_time = time(10, 0)  # 10:00 AM
        can_enter = self.data_5min.index.time >= entry_start_time

        # Generate entry signals (ALL conditions required)
        long_entries = (
            price_breakout_long &
            bullish_opening &
            volume_surge &
            can_enter
        )

        short_entries = (
            price_breakout_short &
            bearish_opening &
            volume_surge &
            can_enter &
            self.enable_shorts
        )

        # EOD exit signals (3:55 PM ET - 5 minutes before close)
        eod_time = time(15, 55)
        eod_exit = self.data_5min.index.time == eod_time

        self.signals = {
            'long_entries': long_entries,
            'short_entries': short_entries,
            'long_exits': eod_exit,
            'short_exits': eod_exit,
            'stop_distance': stop_distance,
            'atr': atr_intraday,
            'volume_confirmed': volume_surge,
            'volume_ma': volume_ma,
            'opening_high': opening_high,
            'opening_low': opening_low,
            'opening_close': opening_close,
            'opening_open': opening_open
        }

        # Print signal summary
        total_long = long_entries.sum()
        total_short = short_entries.sum()
        volume_confirmed_pct = volume_surge.sum() / len(volume_surge) * 100

        print(f"\n=== Signal Generation Summary ===")
        print(f"Long entry signals: {total_long}")
        print(f"Short entry signals: {total_short}")
        print(f"Volume confirmation rate: {volume_confirmed_pct:.1f}%")
        print(f"Avg ATR: ${atr_intraday.mean():.2f}")
        print(f"Avg stop distance: ${stop_distance.mean():.2f}")

        return self.signals

    def run_backtest(
        self,
        fees: float = 0.002,
        slippage: float = 0.001
    ) -> vbt.Portfolio:
        """
        Run VectorBT Pro backtest with ATR-based position sizing.

        Args:
            fees: Transaction fees as decimal (default: 0.002 = 0.2%)
            slippage: Slippage as decimal (default: 0.001 = 0.1%)

        Returns:
            VectorBT Portfolio object
        """
        if self.signals is None:
            raise ValueError("Must generate signals first using generate_signals()")

        # Calculate position sizes using Week 1 implementation
        # Use daily close and ATR for position sizing
        daily_close = self.data_5min['Close'].resample('D').last()
        atr_daily = self.signals['atr'].resample('D').last()

        position_sizes, actual_risks, constrained = calculate_position_size_atr(
            init_cash=self.init_cash,
            close=daily_close,
            atr=atr_daily,
            atr_multiplier=self.atr_stop_multiplier,
            risk_pct=self.risk_pct
        )

        # Forward-fill position sizes to intraday bars
        position_sizes_intraday = position_sizes.reindex(
            self.data_5min.index.normalize(), method='ffill'
        ).reindex(self.data_5min.index, method='ffill')

        # Run VectorBT backtest
        self.portfolio = vbt.Portfolio.from_signals(
            close=self.data_5min['Close'],
            entries=self.signals['long_entries'],
            exits=self.signals['long_exits'],
            size=position_sizes_intraday,
            size_type='amount',  # Position sizes are in shares
            sl_stop=self.signals['stop_distance'],  # ATR-based stops
            init_cash=self.init_cash,
            fees=fees,
            slippage=slippage
        )

        # Print backtest summary
        print(f"\n=== Backtest Summary ===")
        print(f"Total return: {self.portfolio.total_return * 100:.2f}%")
        print(f"Sharpe ratio: {self.portfolio.sharpe_ratio:.2f}")
        print(f"Max drawdown: {self.portfolio.max_drawdown * 100:.2f}%")
        print(f"Total trades: {self.portfolio.trades.count()}")
        print(f"Win rate: {self.portfolio.trades.win_rate * 100:.1f}%")

        return self.portfolio

    def analyze_expectancy(self, transaction_costs: float = 0.0035) -> Dict:
        """
        Comprehensive expectancy analysis with efficiency factors.

        MANDATORY Gate 2 requirement from STRATEGY_2_IMPLEMENTATION_ADDENDUM.md

        Args:
            transaction_costs: Total costs per trade (default: 0.35%)

        Returns:
            Dict with expectancy metrics and viability assessment
        """
        if self.portfolio is None:
            raise ValueError("Must run backtest first using run_backtest()")

        trades = self.portfolio.trades

        if trades.count() == 0:
            print("[WARNING] No trades executed - cannot calculate expectancy")
            return None

        win_rate = trades.win_rate

        winning_trades = trades.winning_returns.values
        losing_trades = trades.losing_returns.values

        if len(winning_trades) == 0 or len(losing_trades) == 0:
            print("[WARNING] No winning or losing trades - cannot calculate expectancy")
            return None

        avg_win = np.mean(winning_trades)
        avg_loss = abs(np.mean(losing_trades))

        # Calculate R:R ratio
        rr_ratio = avg_win / avg_loss if avg_loss > 0 else 0

        # 1. Theoretical expectancy
        theoretical_exp = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        # 2. Realized expectancy (80% efficiency from fixed fractional sizing)
        efficiency_factor = 0.80
        realized_exp = theoretical_exp * efficiency_factor

        # 3. Net expectancy (after transaction costs)
        net_exp = realized_exp - transaction_costs

        # Print detailed report
        print("\n" + "=" * 70)
        print("EXPECTANCY ANALYSIS (Gate 2 Requirement)")
        print("=" * 70)

        print(f"\nInput Statistics:")
        print(f"  Win Rate: {win_rate:.2%}")
        print(f"  Avg Winner: {avg_win:.2%}")
        print(f"  Avg Loser: {avg_loss:.2%}")
        print(f"  R:R Ratio: {rr_ratio:.2f}:1")

        print(f"\nExpectancy Breakdown:")
        print(f"  1. Theoretical: {theoretical_exp:.4f} ({theoretical_exp*100:.2f}% per trade)")
        print(f"     Formula: ({win_rate:.2%} x {avg_win:.2%}) - ({1-win_rate:.2%} x {avg_loss:.2%})")

        print(f"\n  2. Realized ({efficiency_factor:.0%} efficiency):")
        print(f"     {realized_exp:.4f} ({realized_exp*100:.2f}% per trade)")
        print(f"     Reason: Fixed fractional sizing drag")

        print(f"\n  3. Net (after costs):")
        print(f"     {net_exp:.4f} ({net_exp*100:.2f}% per trade)")
        print(f"     Costs: {transaction_costs:.2%} per trade")

        # Viability assessment
        print(f"\n{'=' * 70}")
        print("VIABILITY ASSESSMENT")
        print(f"{'=' * 70}")

        viable = False
        assessment = ""

        if net_exp >= 0.008:
            assessment = "[PASS] EXCELLENT"
            detail = "Net expectancy > 0.8% per trade - comfortable margin"
            viable = True
        elif net_exp >= 0.005:
            assessment = "[PASS] GOOD"
            detail = "Net expectancy > 0.5% per trade - viable strategy"
            viable = True
        elif net_exp >= 0.003:
            assessment = "[FAIL] MARGINAL"
            detail = "Net expectancy 0.3-0.5% - barely viable, sensitive to costs"
            viable = False
        elif net_exp >= 0.000:
            assessment = "[FAIL] BREAKEVEN"
            detail = "Net expectancy near zero - not profitable"
            viable = False
        else:
            assessment = "[FAIL] NEGATIVE"
            detail = "Negative net expectancy - losing money"
            viable = False

        print(f"\n{assessment}")
        print(f"  {detail}")

        return {
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'rr_ratio': rr_ratio,
            'theoretical': theoretical_exp,
            'realized': realized_exp,
            'net': net_exp,
            'viable': viable,
            'assessment': assessment
        }
