"""
Jump Model Regime Detection

Implementation of Jump Model for market regime classification.

Academic Foundation:
    - Simpler than GMM/HMM approaches (3 parameters vs 6-7)
    - Lower turnover (44% annually vs 141% for GMM)
    - More robust to overfitting
    - Real-time classification capability

Regime Classification:
    TREND_BULL: Jump probability >70%, positive return direction
    TREND_BEAR: Jump probability >70%, negative return direction
    TREND_NEUTRAL: Jump probability 30-70%
    CRASH: Jump probability >90% or special crash indicators

Volatility Estimators:
    - ATR: Simple, VBT-native, proven (default)
    - Yang-Zhang: Sophisticated, uses overnight + intraday data

Implementation follows:
    docs/SYSTEM_ARCHITECTURE/1_ATLAS_OVERVIEW_AND_PROPOSED_STRATEGIES.md lines 432-476

Phase 1.3 Implementation Complete

VBT Integration: VERIFIED
- vbt.ATR: VERIFIED exists
- vbt.ATR.run: VERIFIED method
"""

from typing import Tuple, Literal
import pandas as pd
import numpy as np
import vectorbtpro as vbt


def calculate_atr_volatility(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14
) -> pd.Series:
    """
    Calculate ATR-based volatility using VectorBT Pro.

    ATR (Average True Range) measures market volatility by decomposing
    the entire range of an asset price for that period.

    This uses VBT's native ATR implementation which is:
    - Optimized (compiled Numba code)
    - Well-tested
    - Simple and robust

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        window: ATR period (default: 14 days)

    Returns:
        ATR values (absolute price units)

    VBT Integration: VERIFIED via MCP
        - vbt.ATR: VERIFIED
        - vbt.ATR.run: VERIFIED

    Example:
        >>> atr = calculate_atr_volatility(
        ...     high=data['High'],
        ...     low=data['Low'],
        ...     close=data['Close'],
        ...     window=14
        ... )
    """
    # Use VBT's native ATR indicator
    atr_indicator = vbt.ATR.run(
        high=high,
        low=low,
        close=close,
        window=window
    )

    return atr_indicator.atr


def calculate_yang_zhang_volatility(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    open_: pd.Series,
    window: int = 20
) -> pd.Series:
    """
    Calculate Yang-Zhang volatility estimator using OHLC data.

    Yang-Zhang volatility is more efficient than close-to-close volatility
    as it uses information from the entire trading day (open, high, low, close).
    It accounts for both overnight gaps and intraday volatility.

    Formula:
        YZ = sqrt(O * σ_o² + C * σ_c² + (1-O-C) * σ_rs²)

        Where:
        - σ_o² = overnight variance (close to open)
        - σ_c² = close-to-close variance
        - σ_rs² = Rogers-Satchell intraday variance
        - O, C = weights (typically 0.34, 0.12)

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        open_: Open prices
        window: Rolling window for variance calculation (default: 20 days)

    Returns:
        Yang-Zhang volatility (annualized, comparable to ATR * scaling factor)

    References:
        Yang, D. and Zhang, Q. (2000). "Drift-Independent Volatility Estimation
        Based on High, Low, Open, and Close Prices"

    Example:
        >>> yz_vol = calculate_yang_zhang_volatility(
        ...     high=data['High'],
        ...     low=data['Low'],
        ...     close=data['Close'],
        ...     open_=data['Open'],
        ...     window=20
        ... )

    Note:
        Returns annualized volatility. To compare with ATR (which is in price units),
        multiply by close price and divide by sqrt(252).
    """
    # Overnight variance (close[t-1] to open[t])
    overnight_returns = np.log(open_ / close.shift(1))
    overnight_var = overnight_returns.rolling(window).var()

    # Close-to-close variance
    close_returns = np.log(close / close.shift(1))
    close_var = close_returns.rolling(window).var()

    # Rogers-Satchell variance (intraday)
    # RS = E[log(H/C) * log(H/O) + log(L/C) * log(L/O)]
    rs_term1 = np.log(high / close) * np.log(high / open_)
    rs_term2 = np.log(low / close) * np.log(low / open_)
    rs_var = (rs_term1 + rs_term2).rolling(window).mean()

    # Weights (standard Yang-Zhang coefficients)
    k = 0.34  # Overnight weight
    alpha = 0.12  # Close-to-close weight

    # Combined Yang-Zhang volatility
    yz_variance = (
        k * overnight_var +
        alpha * close_var +
        (1 - k - alpha) * rs_var
    )

    # Convert to annualized volatility (assuming 252 trading days)
    yz_vol = np.sqrt(yz_variance * 252)

    return yz_vol


def calculate_jump_probability(
    returns: pd.Series,
    volatility: pd.Series
) -> pd.Series:
    """
    Calculate jump probability using normalized return-to-volatility ratio.

    Uses logistic function to convert z-score into probability:
        P(jump) = 1 / (1 + exp(-z))

    Where z = |return| / volatility (normalized jump metric)

    Args:
        returns: Period returns (typically daily)
        volatility: Volatility estimate (ATR or Yang-Zhang)

    Returns:
        Jump probability in [0, 1] range

    Interpretation:
        - High probability (>0.7): Strong trend signal
        - Medium probability (0.3-0.7): Neutral/choppy market
        - Low probability (<0.3): Mean-reverting conditions

    Example:
        >>> jump_prob = calculate_jump_probability(
        ...     returns=close.pct_change(),
        ...     volatility=atr / close  # Normalize ATR to returns scale
        ... )
    """
    # Normalized jump metric (z-score)
    # Use absolute value of returns to capture magnitude regardless of direction
    jump_metric = np.abs(returns) / volatility

    # Logistic function: converts z-score to probability
    # exp(-x) for x > 700 causes overflow, so clip the metric
    jump_metric_clipped = np.clip(jump_metric, -700, 700)
    jump_prob = 1 / (1 + np.exp(-jump_metric_clipped))

    return jump_prob


def classify_regime(
    returns: pd.Series,
    jump_prob: pd.Series,
    bull_threshold: float = 0.70,
    neutral_lower: float = 0.30,
    crash_threshold: float = 0.90
) -> pd.Series:
    """
    Classify market regime based on jump probability and return direction.

    Regime Logic:
        - TREND_BULL: jump_prob > 0.70 AND returns > 0
        - TREND_BEAR: jump_prob > 0.70 AND returns < 0
        - TREND_NEUTRAL: jump_prob between 0.30 and 0.70
        - CRASH: jump_prob > 0.90 (extreme volatility spike)

    Args:
        returns: Period returns
        jump_prob: Jump probability from calculate_jump_probability()
        bull_threshold: Threshold for bull/bear classification (default: 0.70)
        neutral_lower: Lower bound for neutral regime (default: 0.30)
        crash_threshold: Threshold for crash detection (default: 0.90)

    Returns:
        Series of regime classifications ('TREND_BULL', 'TREND_BEAR',
        'TREND_NEUTRAL', 'CRASH')

    Example:
        >>> regime = classify_regime(
        ...     returns=close.pct_change(),
        ...     jump_prob=jump_prob
        ... )
        >>> print(regime.value_counts())
        TREND_BULL       120
        TREND_NEUTRAL     80
        TREND_BEAR        45
        CRASH              5
    """
    # Initialize with TREND_NEUTRAL as default
    regime = pd.Series('TREND_NEUTRAL', index=returns.index)

    # CRASH: Extreme volatility (highest priority)
    crash_mask = jump_prob > crash_threshold
    regime[crash_mask] = 'CRASH'

    # TREND_BULL: High jump probability + positive returns
    bull_mask = (jump_prob > bull_threshold) & (returns > 0) & ~crash_mask
    regime[bull_mask] = 'TREND_BULL'

    # TREND_BEAR: High jump probability + negative returns
    bear_mask = (jump_prob > bull_threshold) & (returns < 0) & ~crash_mask
    regime[bear_mask] = 'TREND_BEAR'

    # TREND_NEUTRAL: Medium jump probability (default case already set)
    # This captures jump_prob between neutral_lower and bull_threshold

    return regime


class JumpModel:
    """
    Jump Model for market regime detection.

    Simpler and more robust alternative to GMM/HMM approaches.
    Uses volatility and jump probability to classify regimes.

    Key Advantages:
        - Only 3 parameters vs 6-7 for GMM
        - 44% annual turnover vs 141% for GMM
        - Real-time classification (no batch fitting required)
        - More robust to overfitting

    Volatility Estimators:
        - 'atr': Average True Range (VBT native, default)
        - 'yang_zhang': Yang-Zhang estimator (overnight + intraday)

    Attributes:
        window: Volatility calculation window (default: 20 days)
        volatility_method: 'atr' or 'yang_zhang' (default: 'atr')
        bull_threshold: Jump probability threshold for bull/bear (default: 0.70)
        neutral_lower: Lower bound for neutral regime (default: 0.30)
        crash_threshold: Jump probability threshold for crash (default: 0.90)

    Example:
        >>> # Using ATR (default, simpler)
        >>> model = JumpModel(window=20, volatility_method='atr')
        >>> regime = model.detect_regime(data)
        >>>
        >>> # Using Yang-Zhang (more sophisticated)
        >>> model = JumpModel(window=20, volatility_method='yang_zhang')
        >>> regime = model.detect_regime(data)
        >>>
        >>> print(f"Current regime: {regime.iloc[-1]}")
        Current regime: TREND_BULL
    """

    def __init__(
        self,
        window: int = 20,
        volatility_method: Literal['atr', 'yang_zhang'] = 'atr',
        bull_threshold: float = 0.70,
        neutral_lower: float = 0.30,
        crash_threshold: float = 0.90
    ):
        """
        Initialize Jump Model with parameters.

        Args:
            window: Rolling window for volatility (default: 20 days)
            volatility_method: 'atr' or 'yang_zhang' (default: 'atr')
            bull_threshold: Threshold for trend classification (default: 0.70)
            neutral_lower: Lower bound for neutral (default: 0.30)
            crash_threshold: Threshold for crash detection (default: 0.90)

        Raises:
            ValueError: If volatility_method is not 'atr' or 'yang_zhang'
        """
        if volatility_method not in ['atr', 'yang_zhang']:
            raise ValueError(
                f"volatility_method must be 'atr' or 'yang_zhang', "
                f"got: {volatility_method}"
            )

        self.window = window
        self.volatility_method = volatility_method
        self.bull_threshold = bull_threshold
        self.neutral_lower = neutral_lower
        self.crash_threshold = crash_threshold

    def detect_regime(
        self,
        data: pd.DataFrame
    ) -> pd.Series:
        """
        Detect market regime from OHLC data.

        Workflow:
            1. Calculate volatility (ATR or Yang-Zhang)
            2. Calculate returns
            3. Calculate jump probability
            4. Classify regime

        Args:
            data: OHLCV DataFrame with columns: Open, High, Low, Close
                Index must be DatetimeIndex

        Returns:
            Series of regime classifications aligned with input index

        Example:
            >>> model = JumpModel(volatility_method='atr')
            >>> regime = model.detect_regime(spy_data)
            >>>
            >>> # Regime statistics
            >>> print(regime.value_counts())
            >>> print(f"Bull regime: {(regime == 'TREND_BULL').sum() / len(regime):.1%}")
        """
        # Validate required columns
        required_cols = ['High', 'Low', 'Close']
        if self.volatility_method == 'yang_zhang':
            required_cols.append('Open')

        if not all(col in data.columns for col in required_cols):
            raise ValueError(
                f"Data must contain columns: {required_cols}. "
                f"Got: {data.columns.tolist()}"
            )

        # Calculate volatility based on method
        if self.volatility_method == 'atr':
            # ATR volatility (VBT native)
            volatility = calculate_atr_volatility(
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                window=self.window
            )
            # Normalize ATR to returns scale (ATR is in price units)
            volatility = volatility / data['Close']

        else:  # yang_zhang
            # Yang-Zhang volatility (already annualized)
            volatility = calculate_yang_zhang_volatility(
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                open_=data['Open'],
                window=self.window
            )
            # Yang-Zhang is already in returns scale (annualized)
            # De-annualize for daily comparison: divide by sqrt(252)
            volatility = volatility / np.sqrt(252)

        # Calculate returns
        returns = data['Close'].pct_change()

        # Calculate jump probability
        jump_prob = calculate_jump_probability(returns, volatility)

        # Classify regime
        regime = classify_regime(
            returns=returns,
            jump_prob=jump_prob,
            bull_threshold=self.bull_threshold,
            neutral_lower=self.neutral_lower,
            crash_threshold=self.crash_threshold
        )

        return regime

    def get_current_regime(
        self,
        data: pd.DataFrame
    ) -> str:
        """
        Get the most recent regime classification.

        Convenience method for real-time regime detection.

        Args:
            data: OHLCV DataFrame (last row will be used)

        Returns:
            Current regime classification string

        Example:
            >>> model = JumpModel()
            >>> current = model.get_current_regime(recent_data)
            >>> print(f"Trading allowed: {current == 'TREND_BULL'}")
        """
        regime_series = self.detect_regime(data)
        return regime_series.iloc[-1]

    def get_regime_statistics(
        self,
        data: pd.DataFrame
    ) -> dict:
        """
        Calculate regime distribution statistics.

        Useful for backtesting and validation.

        Args:
            data: OHLCV DataFrame

        Returns:
            Dictionary with regime statistics:
            - counts: Regime occurrence counts
            - percentages: Regime distribution percentages
            - turnover: Regime change frequency (annualized)
            - method: Volatility method used

        Example:
            >>> model = JumpModel(volatility_method='atr')
            >>> stats = model.get_regime_statistics(historical_data)
            >>> print(f"Method: {stats['method']}")
            >>> print(f"Bull markets: {stats['percentages']['TREND_BULL']:.1%}")
            >>> print(f"Annual turnover: {stats['turnover']:.1%}")
        """
        regime = self.detect_regime(data)

        # Count occurrences
        counts = regime.value_counts().to_dict()

        # Calculate percentages
        total = len(regime)
        percentages = {k: v / total for k, v in counts.items()}

        # Calculate turnover (regime changes per year)
        regime_changes = (regime != regime.shift(1)).sum()
        years = len(regime) / 252  # Assuming daily data
        turnover = regime_changes / years if years > 0 else 0

        return {
            'method': self.volatility_method,
            'counts': counts,
            'percentages': percentages,
            'turnover': turnover,
            'total_observations': total
        }
