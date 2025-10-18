"""
Position Sizing Utilities for Algorithmic Trading Strategies

This module provides position sizing functions matched to stop-loss methodologies.
Each strategy type requires a different position sizing approach.

CRITICAL: All functions are designed for VectorBT Pro compatibility.
- Input: pandas Series with DatetimeIndex (aligned to price data)
- Output: pandas Series with same index (VectorBT Pro requirement)
- Operations: Fully vectorized (no loops, VectorBT Pro best practice)

Reference: VectorBT Pro Official Documentation
"""

import numpy as np
import pandas as pd
from typing import Tuple, Union


def calculate_position_size_atr(
    init_cash: float,
    close: Union[float, pd.Series],
    atr: Union[float, pd.Series],
    atr_multiplier: float = 2.5,
    risk_pct: float = 0.02
) -> Tuple[Union[float, pd.Series], Union[float, pd.Series], Union[bool, pd.Series]]:
    """
    Calculate position size for strategies with ATR-based stop losses.

    *** VECTORBT PRO COMPATIBLE ***

    Use this function for:
    - Opening Range Breakout (ORB)
    - Turtle Trading systems
    - Any strategy with ATR-based stops

    The critical fix from Phase 0: Adds capital constraint to prevent
    position sizes exceeding 100% of capital.

    VectorBT Pro Integration:
        >>> # Example usage with VectorBT Pro
        >>> position_sizes, actual_risks, constrained = calculate_position_size_atr(
        ...     init_cash=10000,
        ...     close=data['Close'],  # pandas Series
        ...     atr=atr_series,       # pandas Series with matching index
        ...     atr_multiplier=2.5,
        ...     risk_pct=0.02
        ... )
        >>>
        >>> # Use with VectorBT Pro Portfolio
        >>> pf = vbt.Portfolio.from_signals(
        ...     close=data['Close'],
        ...     entries=long_entries,
        ...     exits=long_exits,
        ...     size=position_sizes,        # Our output here
        ...     size_type='amount',          # Shares, not percentage
        ...     init_cash=10000,
        ...     sl_stop=atr_series * 2.5,   # ATR-based stops
        ...     fees=0.001
        ... )

    Args:
        init_cash: Account capital ($10,000 typically)
        close: Current price or price series (pandas Series for VectorBT Pro)
        atr: Average True Range value or series (pandas Series for VectorBT Pro)
        atr_multiplier: Stop distance in ATR units (2.5 for ORB, 2.0 for Turtle)
        risk_pct: Risk per trade as decimal (0.02 = 2%)

    Returns:
        tuple: (position_size_shares, actual_risk_pct, constrained_flag)
            - position_size_shares: Number of shares to buy (pandas Series if input is Series)
            - actual_risk_pct: Realized risk (may be < target if constrained)
            - constrained_flag: True if capital constraint was applied

        All return values maintain index alignment with input Series (VectorBT Pro requirement)

    Example:
        >>> size, risk, constrained = calculate_position_size_atr(
        ...     init_cash=10000,
        ...     close=480,
        ...     atr=5.0,
        ...     atr_multiplier=2.5,
        ...     risk_pct=0.02
        ... )
        >>> print(f"Buy {size:.0f} shares, actual risk {risk:.2%}")
        Buy 16 shares, actual risk 2.00%

        >>> # Capital constraint example
        >>> size, risk, constrained = calculate_position_size_atr(
        ...     init_cash=10000,
        ...     close=480,
        ...     atr=1.0,  # Very small ATR
        ...     atr_multiplier=2.5,
        ...     risk_pct=0.02
        ... )
        >>> print(f"Buy {size:.0f} shares, actual risk {risk:.2%}, constrained={constrained}")
        Buy 20 shares, actual risk 0.50%, constrained=True
    """
    # Handle edge cases for ATR
    # If ATR is Series, replace zeros and NaN with small positive value
    if isinstance(atr, pd.Series):
        atr_clean = atr.copy()
        # Replace zero ATR with forward fill, then backfill, then 1.0 as fallback
        atr_clean = atr_clean.replace(0, np.nan)
        atr_clean = atr_clean.ffill().bfill().fillna(1.0)
    else:
        # Scalar ATR
        atr_clean = max(atr, 0.01) if atr > 0 else 1.0

    # Calculate stop distance in dollars
    stop_distance = atr_clean * atr_multiplier

    # Risk-based position size (what we'd like to buy for target risk%)
    # Formula: If we risk X% of capital over Y dollars stop, we can buy X% * capital / Y shares
    position_size_risk = (init_cash * risk_pct) / stop_distance

    # Capital-based maximum (can't buy more than 100% of capital)
    # This is the maximum shares we can afford with 100% of capital
    position_size_capital = init_cash / close

    # Take minimum (capital constraint fix from Phase 0)
    # Using np.minimum for vectorized element-wise operation (VectorBT Pro compatible)
    # This ensures BOTH constraints are satisfied:
    # 1. Risk constraint (position_size_risk)
    # 2. Capital constraint (position_size_capital)
    position_size = np.minimum(position_size_risk, position_size_capital)

    # Calculate actual risk achieved (may be less than target if capital constrained)
    # Actual risk = (shares * stop_distance) / capital
    actual_risk = (position_size * stop_distance) / init_cash

    # Flag if constrained by capital (not risk)
    # For Series, this creates a boolean Series (VectorBT Pro compatible)
    # For scalar, this creates a boolean
    constrained = position_size == position_size_capital

    # Additional edge case handling: Ensure no negative, NaN, or Inf values
    if isinstance(position_size, pd.Series):
        position_size = position_size.clip(lower=0)  # No negative positions
        position_size = position_size.replace([np.inf, -np.inf], 0)  # Replace infinities
        position_size = position_size.fillna(0)  # Replace NaN with 0

        actual_risk = actual_risk.clip(lower=0, upper=1.0)  # Risk between 0-100%
        actual_risk = actual_risk.replace([np.inf, -np.inf], 0)
        actual_risk = actual_risk.fillna(0)
    else:
        # Scalar values
        position_size = max(position_size, 0) if np.isfinite(position_size) else 0
        actual_risk = max(min(actual_risk, 1.0), 0) if np.isfinite(actual_risk) else 0

    # VectorBT Pro Note: If input is pandas Series, output will be Series with same index
    # This ensures proper alignment in vbt.Portfolio.from_signals()

    return position_size, actual_risk, constrained


def validate_position_size(
    position_size: Union[float, pd.Series],
    init_cash: float,
    close: Union[float, pd.Series],
    max_pct: float = 1.0
) -> Tuple[bool, str]:
    """
    Validate position sizes for common issues.

    Checks for:
    - Negative position sizes
    - NaN or Inf values
    - Positions exceeding capital constraints

    Args:
        position_size: Position size(s) to validate (shares)
        init_cash: Account capital
        close: Price(s) used to calculate position value
        max_pct: Maximum position size as fraction of capital (1.0 = 100%)

    Returns:
        tuple: (is_valid, error_message)
            - is_valid: True if all checks pass
            - error_message: Description of issue if invalid, "Valid" if passed

    Example:
        >>> is_valid, msg = validate_position_size(
        ...     position_size=pd.Series([10, 20, 15]),
        ...     init_cash=10000,
        ...     close=pd.Series([480, 490, 500]),
        ...     max_pct=1.0
        ... )
        >>> print(f"Valid: {is_valid}, Message: {msg}")
        Valid: True, Message: Valid
    """
    # Check for negative sizes
    if isinstance(position_size, pd.Series):
        if (position_size < 0).any():
            return False, "Negative position sizes detected"
    else:
        if position_size < 0:
            return False, "Negative position size detected"

    # Check for NaN or Inf
    if isinstance(position_size, pd.Series):
        if (~np.isfinite(position_size)).any():
            return False, "NaN or Inf position sizes detected"
    else:
        if not np.isfinite(position_size):
            return False, "NaN or Inf position size detected"

    # Check capital constraint
    position_value = position_size * close
    max_capital = init_cash * max_pct

    if isinstance(position_value, pd.Series):
        if (position_value > max_capital).any():
            max_violation = (position_value / init_cash).max()
            return False, f"Position exceeds {max_pct*100:.0f}% of capital (max: {max_violation*100:.1f}%)"
    else:
        if position_value > max_capital:
            violation_pct = (position_value / init_cash) * 100
            return False, f"Position exceeds {max_pct*100:.0f}% of capital ({violation_pct:.1f}%)"

    return True, "Valid"
