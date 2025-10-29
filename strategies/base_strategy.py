"""
Base Strategy Abstract Class for ATLAS Trading System v2.0

This module provides the abstract base class that all ATLAS strategies inherit from.
Standardizes signal generation, position sizing, backtesting, and performance metrics.

Design Principles:
- Strategies implement signal generation and position sizing logic
- BaseStrategy handles VectorBT Pro integration and performance metrics
- Pydantic validation ensures configuration correctness
- Regime awareness enables adaptive capital allocation
- VBT-compatible data formats (pd.Series with DatetimeIndex)

v2.0 Enhancements:
- Regime awareness (strategies declare compatible market regimes)
- Universe and rebalance frequency attributes for portfolio management
- Backward compatible with v1.0 signal formats

VBT Integration: VERIFIED (Steps 1-2 complete)
- vbt.Portfolio.from_signals: VERIFIED
- Portfolio properties (total_return, sharpe_ratio, etc.): VERIFIED
- Trade metrics (count, win_rate, winning, losing): VERIFIED

Reference:
- docs/SYSTEM_ARCHITECTURE/2_DIRECTORY_STRUCTURE_AND_STRATEGY_IMPLEMENTATION.md
- docs/ATLAS_V2_IMPLEMENTATION_PLAN.md (Phase 1.2)
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, Union
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
import vectorbtpro as vbt


class StrategyConfig(BaseModel):
    """
    Strategy configuration with Pydantic validation.

    Provides runtime validation of strategy parameters to prevent
    configuration errors and ensure risk management rules are followed.

    Attributes:
        name: Strategy identifier (for logging/reporting)
        universe: Trading universe ('sp500', 'russell1000', 'nasdaq100', 'custom')
        rebalance_frequency: How often to rebalance ('daily', 'weekly', 'monthly', 'quarterly', 'semi_annual')
        regime_compatibility: Dict mapping regime names to boolean (which regimes strategy trades in)
        risk_per_trade: Risk per trade as decimal (default: 2%)
        max_positions: Maximum concurrent positions (default: 5)
        enable_shorts: Allow short positions (default: False)
        commission_rate: Transaction fees as decimal (default: 0.15%)
        slippage: Slippage estimate as decimal (default: 0.15%)

    Validation Rules:
        - Risk per trade: 0.1% to 5% (professional range)
        - Max positions: 1 to 20 (prevents over-diversification)
        - Combined costs: ≤0.5% (prevents excessive friction)

    v2.0 Additions:
        - universe: Defines stock selection pool
        - rebalance_frequency: Controls trading frequency
        - regime_compatibility: Enables adaptive allocation
    """

    name: str
    universe: str = 'sp500'
    rebalance_frequency: str = 'daily'
    regime_compatibility: Dict[str, bool] = Field(
        default_factory=lambda: {
            'TREND_BULL': True,
            'TREND_NEUTRAL': False,
            'TREND_BEAR': False,
            'CRASH': False
        }
    )
    risk_per_trade: float = Field(default=0.02, ge=0.001, le=0.05)
    max_positions: int = Field(default=5, ge=1, le=20)
    enable_shorts: bool = False
    commission_rate: float = Field(default=0.0015, ge=0.0, le=0.01)
    slippage: float = Field(default=0.0015, ge=0.0, le=0.01)

    class Config:
        """Pydantic configuration"""
        frozen = False  # Allow updates during development
        validate_assignment = True  # Validate on attribute changes


class BaseStrategy(ABC):
    """
    Abstract base class for all ATLAS trading strategies.

    Responsibilities:
    - Define interface for signal generation and position sizing
    - Provide standardized VectorBT Pro integration
    - Calculate performance metrics consistently
    - Validate configuration parameters

    All strategies must implement:
    - generate_signals(): Entry/exit signal generation
    - calculate_position_size(): Position sizing logic
    - get_strategy_name(): Strategy identifier

    Common functionality provided:
    - VectorBT Pro backtest() integration
    - Performance metrics calculation
    - Configuration validation

    Example Usage:
        >>> class ORBStrategy(BaseStrategy):
        ...     def generate_signals(self, data):
        ...         # Implement ORB signal logic
        ...         return {'long_entries': ..., 'long_exits': ..., 'stop_distance': ...}
        ...
        ...     def calculate_position_size(self, data, capital, stop_distance):
        ...         # Use utils/position_sizing.py
        ...         return position_sizes
        ...
        ...     def get_strategy_name(self):
        ...         return "Opening Range Breakout"
        ...
        >>> config = StrategyConfig(name="ORB", risk_per_trade=0.02)
        >>> strategy = ORBStrategy(config)
        >>> pf = strategy.backtest(data, initial_capital=10000)
        >>> metrics = strategy.get_performance_metrics(pf)
    """

    def __init__(self, config: StrategyConfig):
        """
        Initialize strategy with validated configuration.

        Args:
            config: StrategyConfig instance with validated parameters

        Raises:
            ValueError: If configuration fails validation rules
            AssertionError: If strategy parameters fail validation

        v2.0 Changes:
            - Now calls validate_parameters() after validate_config()
            - Ensures both StrategyConfig and strategy-specific params are valid
        """
        self.config = config
        self.validate_config()
        self.validate_parameters()  # v2.0: Strategy-specific validation

    def validate_config(self) -> None:
        """
        Validate strategy configuration for risk management compliance.

        Checks:
        1. Risk per trade not excessive (>3% triggers warning)
        2. Combined transaction costs reasonable (<0.5%)

        Raises:
            ValueError: If configuration violates risk management rules

        Note:
            Called automatically during __init__. Can be called again
            if configuration is modified during runtime.
        """
        # Check risk per trade (strict limit at 3%)
        if self.config.risk_per_trade > 0.03:
            raise ValueError(
                f"Risk per trade too high: {self.config.risk_per_trade:.2%}. "
                f"Maximum allowed: 3%. Current: {self.config.risk_per_trade:.2%}"
            )

        # Check combined transaction costs
        total_costs = self.config.commission_rate + self.config.slippage
        if total_costs > 0.005:
            raise ValueError(
                f"Combined costs exceed 0.5%: "
                f"Commission {self.config.commission_rate:.2%} + "
                f"Slippage {self.config.slippage:.2%} = {total_costs:.2%}"
            )

    def validate_parameters(self) -> bool:
        """
        Validate strategy-specific parameters are within acceptable ranges.

        Default implementation returns True (no validation needed).
        Child classes should override this method ONLY if they have
        strategy-specific parameters that need validation.

        Returns:
            True if all parameters valid

        Raises:
            ValueError: If any parameter is outside acceptable range
            AssertionError: If validation assertions fail

        Example:
            >>> def validate_parameters(self) -> bool:
            ...     assert 10 <= self.lookback_period <= 50, \
            ...         f"lookback_period {self.lookback_period} outside range [10, 50]"
            ...     assert 0.0 < self.entry_threshold < 1.0, \
            ...         f"entry_threshold must be between 0 and 1"
            ...     return True

        Note:
            - Called automatically during __init__ after config validation
            - Use assertions for clarity (will raise AssertionError)
            - Provide helpful error messages with actual vs expected values
            - If your strategy has no special parameters, no need to override
        """
        return True  # Default: no validation needed

    def should_trade_in_regime(self, regime: str) -> bool:
        """
        Check if strategy should trade in the given market regime.

        Uses regime_compatibility from StrategyConfig to determine if
        strategy is appropriate for current market conditions.

        Args:
            regime: Current market regime ('TREND_BULL', 'TREND_NEUTRAL', 'TREND_BEAR', 'CRASH')

        Returns:
            True if strategy should be active in this regime

        Example:
            >>> config = StrategyConfig(
            ...     name="52-Week High",
            ...     regime_compatibility={
            ...         'TREND_BULL': True,
            ...         'TREND_NEUTRAL': True,  # Still works!
            ...         'TREND_BEAR': False,
            ...         'CRASH': False
            ...     }
            ... )
            >>> strategy = Strategy(config)
            >>> strategy.should_trade_in_regime('TREND_BULL')  # True
            >>> strategy.should_trade_in_regime('TREND_BEAR')  # False

        Note:
            - Defaults to False for unknown regimes (safety first)
            - Used by generate_signals() to filter signals by regime
            - Portfolio manager uses this for capital allocation
        """
        return self.config.regime_compatibility.get(regime, False)

    @abstractmethod
    def generate_signals(
        self,
        data: pd.DataFrame,
        regime: Optional[str] = None
    ) -> Dict[str, pd.Series]:
        """
        Generate trading signals for the strategy.

        This method contains the core strategy logic. Child classes must
        implement their specific entry/exit rules here.

        Args:
            data: OHLCV DataFrame with DatetimeIndex
                Required columns: Open, High, Low, Close, Volume
                Index: pd.DatetimeIndex (timezone-aware recommended)
            regime: Optional current market regime for filtering signals
                ('TREND_BULL', 'TREND_NEUTRAL', 'TREND_BEAR', 'CRASH')

        Returns:
            Dictionary containing (supports both v1.0 and v2.0 formats):

            v2.0 format (preferred):
            - 'entry_signal': Boolean Series for entries (required)
            - 'exit_signal': Boolean Series for exits (required)
            - 'stop_distance': Float Series for stop loss distances (required)

            v1.0 format (backward compatible):
            - 'long_entries': Boolean Series for long entries
            - 'long_exits': Boolean Series for long exits
            - 'short_entries': Boolean Series for short entries (optional)
            - 'short_exits': Boolean Series for short exits (optional)
            - 'stop_distance': Float Series for stop losses

            All Series must have same index as input data (VBT requirement)

        Example (v2.0 with regime awareness):
            >>> def generate_signals(self, data: pd.DataFrame, regime: Optional[str] = None):
            ...     # Regime filter
            ...     if regime and not self.should_trade_in_regime(regime):
            ...         return {
            ...             'entry_signal': pd.Series(False, index=data.index),
            ...             'exit_signal': pd.Series(False, index=data.index),
            ...             'stop_distance': pd.Series(0.0, index=data.index)
            ...         }
            ...
            ...     # Strategy logic
            ...     entry_signal = data['Close'] > data['High'].shift(1)
            ...     exit_signal = data['Close'] < data['Low'].shift(1)
            ...     stop_distance = atr * 2.5
            ...
            ...     return {
            ...         'entry_signal': entry_signal,
            ...         'exit_signal': exit_signal,
            ...         'stop_distance': stop_distance
            ...     }

        Note:
            - Use boolean Series for entry/exit signals (not 0/1)
            - Ensure all Series have aligned indexes
            - stop_distance should be in price units (dollars, not %)
            - If regime is incompatible, return all False signals
        """
        pass

    @abstractmethod
    def calculate_position_size(
        self,
        data: pd.DataFrame,
        capital: float,
        stop_distance: pd.Series
    ) -> pd.Series:
        """
        Calculate position sizes for each signal.

        This method implements the strategy's position sizing logic.
        Most strategies will use utils/position_sizing.py functions,
        but custom logic is allowed.

        Args:
            data: OHLCV DataFrame (same as generate_signals input)
            capital: Current account capital (float)
            stop_distance: Stop loss distances from generate_signals()

        Returns:
            Position sizes as pd.Series of share counts (not dollars)
            Index must match input data (VBT requirement)

        Example (using utils/position_sizing.py):
            >>> from utils.position_sizing import calculate_position_size_atr
            >>>
            >>> def calculate_position_size(self, data, capital, stop_distance):
            ...     position_sizes, actual_risks, constrained = calculate_position_size_atr(
            ...         init_cash=capital,
            ...         close=data['Close'],
            ...         atr=atr_series,
            ...         atr_multiplier=self.atr_multiplier,
            ...         risk_pct=self.config.risk_per_trade
            ...     )
            ...     return position_sizes  # pd.Series of share counts

        Requirements:
            - Return pd.Series (not scalar or np.array alone)
            - Values are share counts (for size_type='amount')
            - Index matches input data index
            - No negative, NaN, or Inf values (use fillna(0))

        Note:
            Gate 1 requirement: Position sizes must never exceed 100% of capital.
            Use capital constraint: min(risk_based_size, capital / price)
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Return strategy name for logging and reporting.

        Returns:
            Human-readable strategy name (e.g., "Opening Range Breakout")

        Example:
            >>> def get_strategy_name(self) -> str:
            ...     return "Opening Range Breakout (ORB)"
        """
        pass

    def backtest(
        self,
        data: pd.DataFrame,
        initial_capital: float = 10000.0,
        regime: Optional[str] = None
    ) -> vbt.Portfolio:
        """
        Run backtest using VectorBT Pro.

        This method integrates child strategy's signals and position sizing
        with VectorBT Pro's Portfolio simulator. Handles standard VBT integration
        so child classes don't need to reimplement.

        Workflow:
        1. Call child's generate_signals() to get entries/exits/stops (with regime)
        2. Call child's calculate_position_size() to get share counts
        3. Run vbt.Portfolio.from_signals() with standard settings
        4. Return VBT Portfolio object for analysis

        Args:
            data: OHLCV DataFrame with DatetimeIndex
                Required columns: Open, High, Low, Close, Volume
            initial_capital: Starting capital in dollars (default: $10,000)
            regime: Optional market regime for regime-aware strategies
                ('TREND_BULL', 'TREND_NEUTRAL', 'TREND_BEAR', 'CRASH')

        Returns:
            vbt.Portfolio object with backtest results

        Raises:
            ValueError: If signals or position sizes have mismatched indexes
            ValueError: If generate_signals() returns invalid format

        Example:
            >>> # Basic backtest
            >>> pf = strategy.backtest(data, initial_capital=10000)
            >>>
            >>> # Regime-aware backtest (v2.0)
            >>> pf = strategy.backtest(data, initial_capital=10000, regime='TREND_BULL')
            >>>
            >>> print(f"Total Return: {pf.total_return:.2%}")
            >>> print(f"Sharpe Ratio: {pf.sharpe_ratio:.2f}")
            >>> print(f"Max Drawdown: {pf.max_drawdown:.2%}")

        VBT Integration Notes:
            - Uses from_signals() method (signal-based simulator)
            - size_type='amount': Position sizes are share counts
            - sl_stop: ATR-based stop losses from generate_signals()
            - Fees and slippage from StrategyConfig
            - freq='1D': Assumes daily data (change if using intraday)

        VBT Integration: VERIFIED (Steps 1-2 complete)
            - vbt.Portfolio.from_signals: VERIFIED exists
            - All parameters validated by MCP tools

        Signal Format Compatibility:
            - v2.0: 'entry_signal', 'exit_signal', 'stop_distance'
            - v1.0: 'long_entries', 'long_exits', 'stop_distance'
            - Auto-detects format and adapts

        Performance:
            - Fully vectorized (no Python loops)
            - Compiled Numba code (fast execution)
            - Handles large datasets efficiently

        Note:
            This method should NOT be overridden by child classes.
            If you need custom VBT integration, create a new method.
        """
        # Generate signals from child class (pass regime)
        signals = self.generate_signals(data, regime=regime)

        # Auto-detect signal format and normalize to v1.0 format for VBT
        # (VBT from_signals expects 'entries'/'exits' parameters)
        if 'entry_signal' in signals and 'exit_signal' in signals:
            # v2.0 format - convert to v1.0 format for VBT
            long_entries = signals['entry_signal']
            long_exits = signals['exit_signal']
            short_entries = signals.get('short_entry_signal')
            short_exits = signals.get('short_exit_signal')
        elif 'long_entries' in signals and 'long_exits' in signals:
            # v1.0 format - use directly
            long_entries = signals['long_entries']
            long_exits = signals['long_exits']
            short_entries = signals.get('short_entries')
            short_exits = signals.get('short_exits')
        else:
            raise ValueError(
                f"generate_signals() must return either v2.0 format "
                f"('entry_signal', 'exit_signal') or v1.0 format "
                f"('long_entries', 'long_exits'). Got keys: {signals.keys()}"
            )

        # Validate stop_distance exists (required in both formats)
        if 'stop_distance' not in signals:
            raise ValueError(
                "generate_signals() must return 'stop_distance' key"
            )

        # Extract stop distance for position sizing
        stop_distance = signals['stop_distance']

        # Calculate position sizes from child class
        position_sizes = self.calculate_position_size(
            data,
            initial_capital,
            stop_distance
        )

        # Validate position sizes
        if not isinstance(position_sizes, pd.Series):
            raise ValueError(
                f"calculate_position_size() must return pd.Series, "
                f"got {type(position_sizes)}"
            )

        if not position_sizes.index.equals(data.index):
            raise ValueError(
                "Position sizes index must match data index. "
                "Use data.index when creating position_sizes Series."
            )

        # Run VectorBT Pro backtest
        # Pattern validated: vbt.Portfolio.from_signals VERIFIED via MCP
        pf = vbt.Portfolio.from_signals(
            close=data['Close'],
            entries=long_entries,              # Normalized to v1.0 format
            exits=long_exits,                   # Normalized to v1.0 format
            short_entries=short_entries,        # Optional
            short_exits=short_exits,            # Optional
            size=position_sizes,                # From calculate_position_size()
            size_type='amount',                 # Shares, not dollars
            init_cash=initial_capital,
            fees=self.config.commission_rate,
            slippage=self.config.slippage,
            sl_stop=stop_distance,             # ATR-based stops
            freq='1D'                           # Daily data frequency
        )

        return pf

    def get_performance_metrics(self, pf: vbt.Portfolio) -> Dict[str, float]:
        """
        Extract standardized performance metrics from VBT Portfolio.

        Provides consistent metrics across all strategies for comparison
        and reporting. All strategies use the same metric definitions.

        Args:
            pf: VectorBT Portfolio object (from backtest() method)

        Returns:
            Dictionary containing standard performance metrics:
            - total_return: Total return as decimal (0.25 = 25%)
            - sharpe_ratio: Sharpe ratio (annualized)
            - sortino_ratio: Sortino ratio (downside deviation)
            - max_drawdown: Maximum drawdown as decimal (0.15 = 15%)
            - win_rate: Winning trades percentage (0.45 = 45%)
            - profit_factor: Gross profit / gross loss
            - avg_trade: Average trade return (decimal)
            - total_trades: Number of trades executed
            - avg_winner: Average winning trade return
            - avg_loser: Average losing trade return

        Example:
            >>> pf = strategy.backtest(data, initial_capital=10000)
            >>> metrics = strategy.get_performance_metrics(pf)
            >>> print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
            >>> print(f"Win Rate: {metrics['win_rate']:.1%}")

        Note:
            - All returns are decimals (not percentages)
            - Sharpe ratio annualized (assumes daily frequency)
            - If no trades, returns NaN for trade-based metrics
        """
        # Handle case where no trades were executed
        trades_count = pf.trades.count()

        return {
            # Portfolio-level metrics
            'total_return': pf.total_return if not np.isnan(pf.total_return) else 0.0,
            'sharpe_ratio': pf.sharpe_ratio if not np.isnan(pf.sharpe_ratio) else 0.0,
            'sortino_ratio': pf.sortino_ratio if not np.isnan(pf.sortino_ratio) else 0.0,
            'max_drawdown': pf.max_drawdown if not np.isnan(pf.max_drawdown) else 0.0,

            # Trade-level metrics (NaN if no trades)
            'win_rate': pf.trades.win_rate if trades_count > 0 else np.nan,
            'profit_factor': pf.trades.profit_factor if trades_count > 0 else np.nan,
            'avg_trade': pf.trades.returns.mean() if trades_count > 0 else np.nan,
            'total_trades': trades_count,

            # Winner/loser analysis
            # Use VBT Pro built-in properties (verified via MCP tools)
            'avg_winner': (
                pf.trades.winning.returns.mean()
                if trades_count > 0 and pf.trades.winning.count() > 0
                else np.nan
            ),
            'avg_loser': (
                pf.trades.losing.returns.mean()
                if trades_count > 0 and pf.trades.losing.count() > 0
                else np.nan
            ),
        }
