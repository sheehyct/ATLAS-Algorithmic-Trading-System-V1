"""
Baseline Strategy: 200-day MA + RSI(2) Mean Reversion

Research-proven strategy with documented high win rates over 30 years.
Serves as benchmark for TFC-based approach.

Strategy Rules:
    Entry (Long):
        - Price > 200-day MA (bullish trend)
        - RSI(2) < 15 (oversold)

    Entry (Short):
        - Price < 200-day MA (bearish trend)
        - RSI(2) > 85 (overbought)

    Exit Rules:
        - Profit target: 2x ATR
        - Stop loss: 2x ATR
        - Time exit: 14 days max hold
        - Mean reversion exit: RSI crosses opposite threshold

References:
    - Connors Research: Short-Term Trading Strategies That Work
    - Larry Connors RSI(2) strategy
"""

import vectorbtpro as vbt
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict


class BaselineStrategy:
    """
    Simple momentum-mean reversion baseline strategy.

    Combines trend filter (200-day MA) with mean reversion entry (RSI(2)).
    Uses ATR-based position sizing and multiple exit conditions.
    """

    def __init__(
        self,
        ma_period: int = 200,
        rsi_period: int = 2,
        rsi_oversold: float = 15.0,
        rsi_overbought: float = 85.0,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
        max_hold_days: int = 14,
    ):
        """
        Initialize baseline strategy with parameters.

        Args:
            ma_period: Moving average period (default: 200)
            rsi_period: RSI period (default: 2)
            rsi_oversold: RSI oversold threshold for long entries (default: 15)
            rsi_overbought: RSI overbought threshold for short entries (default: 85)
            atr_period: ATR period for stops/targets (default: 14)
            atr_multiplier: ATR multiplier for stops/targets (default: 2.0)
            max_hold_days: Maximum holding period in days (default: 14)
        """
        self.ma_period = ma_period
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.max_hold_days = max_hold_days

    def generate_signals(
        self,
        data: pd.DataFrame,
    ) -> Dict[str, pd.Series]:
        """
        Generate long and short entry/exit signals.

        Args:
            data: DataFrame with OHLCV data (columns: Open, High, Low, Close, Volume)

        Returns:
            Dictionary containing:
                - long_entries: Boolean series for long entries
                - long_exits: Boolean series for long exits
                - short_entries: Boolean series for short entries
                - short_exits: Boolean series for short exits
                - atr: ATR values for position sizing
        """
        # Normalize column names (handle both lowercase and capitalized)
        close = data['Close'] if 'Close' in data.columns else data['close']
        high = data['High'] if 'High' in data.columns else data['high']
        low = data['Low'] if 'Low' in data.columns else data['low']

        # Calculate indicators using VectorBT Pro's TA-Lib integration
        ma200 = vbt.talib("SMA").run(close, timeperiod=self.ma_period).real
        rsi = vbt.talib("RSI").run(close, timeperiod=self.rsi_period).real
        atr = vbt.talib("ATR").run(high, low, close, timeperiod=self.atr_period).real

        # Long signals
        uptrend = close > ma200
        oversold = rsi < self.rsi_oversold
        long_entries = uptrend & oversold

        overbought = rsi > self.rsi_overbought
        long_exits = overbought

        # Short signals
        downtrend = close < ma200
        short_entries = downtrend & overbought
        short_exits = oversold

        return {
            'long_entries': long_entries,
            'long_exits': long_exits,
            'short_entries': short_entries,
            'short_exits': short_exits,
            'atr': atr,
            'ma200': ma200,
            'rsi': rsi
        }

    def backtest(
        self,
        data: pd.DataFrame,
        init_cash: float = 10000.0,
        fees: float = 0.002,
        slippage: float = 0.001,
        risk_per_trade: float = 0.02,
    ) -> vbt.Portfolio:
        """
        Run backtest and return portfolio object.

        Args:
            data: DataFrame with OHLCV data (columns: Open, High, Low, Close, Volume)
            init_cash: Initial capital (default: 10000)
            fees: Trading fees per trade as decimal (default: 0.002 = 0.2%)
            slippage: Slippage per trade as decimal (default: 0.001 = 0.1%)
            risk_per_trade: Risk per trade as fraction of equity (default: 0.02 = 2%)

        Returns:
            VectorBT Portfolio object with backtest results
        """
        # Generate signals
        signals = self.generate_signals(data)

        # Normalize column names
        close = data['Close'] if 'Close' in data.columns else data['close']
        high = data['High'] if 'High' in data.columns else data['high']
        low = data['Low'] if 'Low' in data.columns else data['low']
        open_price = data['Open'] if 'Open' in data.columns else data['open']

        # Calculate stops and targets
        stop_distance = signals['atr'] * self.atr_multiplier

        # Position sizing: Fixed risk per trade based on ATR stop
        # Size = (Account Value * Risk%) / Stop Distance
        position_size = init_cash * risk_per_trade / stop_distance

        # Replace NaN and inf values with 0
        position_size = position_size.replace([np.inf, -np.inf], 0).fillna(0)

        # Run portfolio simulation using VectorBT Pro
        pf = vbt.PF.from_signals(
            close=close,
            open=open_price,
            high=high,
            low=low,
            entries=signals['long_entries'],
            exits=signals['long_exits'],
            short_entries=signals['short_entries'],
            short_exits=signals['short_exits'],
            size=position_size,
            size_type="amount",
            init_cash=init_cash,
            fees=fees,
            slippage=slippage,
            sl_stop=stop_distance,
            tp_stop=stop_distance * 2,
            td_stop=pd.Timedelta(days=self.max_hold_days),
            freq='1D'
        )

        return pf

    def get_performance_stats(self, pf: vbt.Portfolio) -> Dict[str, float]:
        """
        Extract key performance statistics from portfolio.

        Args:
            pf: VectorBT Portfolio object

        Returns:
            Dictionary with performance metrics
        """
        stats = {}

        try:
            trade_count = pf.trades.count()
            stats['total_return'] = pf.total_return
            stats['sharpe_ratio'] = pf.sharpe_ratio
            stats['max_drawdown'] = pf.max_drawdown
            stats['win_rate'] = pf.trades.win_rate
            stats['total_trades'] = trade_count
            stats['avg_trade_return'] = pf.trades.returns.mean() if trade_count > 0 else 0.0
            stats['profit_factor'] = pf.trades.profit_factor if trade_count > 0 else 0.0
            stats['avg_winning_trade'] = pf.trades.winning.returns.mean() if len(pf.trades.winning.returns) > 0 else 0.0
            stats['avg_losing_trade'] = pf.trades.losing.returns.mean() if len(pf.trades.losing.returns) > 0 else 0.0
        except Exception as e:
            print(f"Warning: Could not calculate some stats: {e}")

        return stats


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("BASELINE MA-RSI STRATEGY TEST")
    print("=" * 60)

    # Import data fetcher
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from data.alpaca import fetch_alpaca_data

    # Fetch SPY data
    print("\nFetching SPY data (last 5 years, daily)...")
    symbol = "SPY"
    data = fetch_alpaca_data(symbol, timeframe='1D', period_days=1825)

    print(f"Fetched {len(data)} daily bars")
    print(f"Date range: {data.index[0].date()} to {data.index[-1].date()}")

    # Run baseline strategy
    print("\nRunning baseline strategy...")
    strategy = BaselineStrategy()
    pf = strategy.backtest(data, init_cash=10000.0)

    # Print results
    print("\n" + "=" * 60)
    print("BASELINE STRATEGY RESULTS")
    print("=" * 60)

    stats = strategy.get_performance_stats(pf)

    print(f"\nTotal Return: {stats['total_return']:.2%}")
    print(f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {stats['max_drawdown']:.2%}")
    print(f"Win Rate: {stats['win_rate']:.2%}")
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Avg Trade Return: {stats['avg_trade_return']:.2%}")
    print(f"Profit Factor: {stats['profit_factor']:.2f}")
    print(f"Avg Winning Trade: {stats['avg_winning_trade']:.2%}")
    print(f"Avg Losing Trade: {stats['avg_losing_trade']:.2%}")

    # Buy-and-hold comparison
    buy_hold_return = (data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1
    print(f"\nBuy-and-Hold Return: {buy_hold_return:.2%}")
    print(f"Strategy vs Buy-and-Hold: {stats['total_return'] - buy_hold_return:.2%}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
