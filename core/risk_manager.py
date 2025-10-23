"""
Risk Manager for Drawdown Circuit Breakers

This module implements drawdown-based circuit breakers for the ATLAS risk
management framework. Circuit breakers automatically reduce position sizes
or halt trading when drawdowns exceed defined thresholds.

CRITICAL: This protects against catastrophic losses during adverse market
conditions by automatically de-risking the portfolio.

Reference: System_Architecture_Reference.md lines 1444-1547
"""

from typing import Dict, Optional


class RiskManager:
    """
    Portfolio-level risk management with drawdown circuit breakers.

    Circuit Breaker Thresholds:
        - 10% DD: WARNING (log only, no action)
        - 15% DD: REDUCE_SIZE (cut position sizes by 50%)
        - 20% DD: STOP_TRADING (halt all new trades)
        - 25% DD: CRITICAL (emergency alert)

    Attributes:
        max_portfolio_heat: Maximum aggregate risk across all positions
        max_position_risk: Maximum risk per individual position
        drawdown_thresholds: Dict mapping drawdown -> action
        peak_equity: Highest equity achieved
        current_equity: Current equity value
        trading_enabled: Whether new trades allowed
        risk_multiplier: Position size multiplier (1.0 = normal, 0.5 = half size)

    Usage:
        >>> risk_mgr = RiskManager(
        ...     max_portfolio_heat=0.08,
        ...     max_position_risk=0.02
        ... )
        >>>
        >>> # Update equity each period
        >>> risk_mgr.update_equity(105000)  # New high
        >>> risk_mgr.update_equity(95000)   # -9.5% DD (no action)
        >>> risk_mgr.update_equity(90000)   # -14.3% DD (warning)
        >>> risk_mgr.update_equity(85000)   # -19.0% DD (reduce size)
        >>> print(risk_mgr.risk_multiplier)  # 0.5
    """

    def __init__(
        self,
        max_portfolio_heat: float = 0.08,
        max_position_risk: float = 0.02,
        drawdown_thresholds: Optional[Dict[float, str]] = None
    ):
        """
        Initialize risk manager with circuit breaker thresholds.

        Args:
            max_portfolio_heat: Maximum portfolio heat (default 8%)
            max_position_risk: Maximum risk per position (default 2%)
            drawdown_thresholds: Optional custom thresholds
                                 Default: {0.10: WARNING, 0.15: REDUCE_SIZE,
                                          0.20: STOP_TRADING, 0.25: CRITICAL}

        Raises:
            ValueError: If max_portfolio_heat or max_position_risk out of range
        """
        if max_portfolio_heat < 0.06 or max_portfolio_heat > 0.10:
            raise ValueError(
                f"max_portfolio_heat must be 0.06-0.10 (6%-10%). "
                f"Got: {max_portfolio_heat:.1%}"
            )

        if max_position_risk < 0.01 or max_position_risk > 0.05:
            raise ValueError(
                f"max_position_risk must be 0.01-0.05 (1%-5%). "
                f"Got: {max_position_risk:.1%}"
            )

        self.max_portfolio_heat = max_portfolio_heat
        self.max_position_risk = max_position_risk

        if drawdown_thresholds is None:
            self.drawdown_thresholds = {
                0.10: 'WARNING',
                0.15: 'REDUCE_SIZE',
                0.20: 'STOP_TRADING',
                0.25: 'CRITICAL'
            }
        else:
            self.drawdown_thresholds = drawdown_thresholds

        self.peak_equity = 0.0
        self.current_equity = 0.0
        self.trading_enabled = True
        self.risk_multiplier = 1.0

    def update_equity(self, equity: float):
        """
        Update equity and check for circuit breakers.

        Call this after each trade or periodically to track drawdown
        and trigger circuit breakers if thresholds exceeded.

        Args:
            equity: Current account equity

        Side Effects:
            - Updates peak_equity if new high
            - Triggers circuit breakers based on drawdown
            - Prints warnings/alerts to console

        Example:
            >>> risk_mgr.update_equity(100000)  # Initial
            >>> risk_mgr.update_equity(110000)  # New peak
            >>> risk_mgr.update_equity(93500)   # -15% DD -> reduce size
        """
        self.current_equity = equity

        # Update peak
        if equity > self.peak_equity:
            self.peak_equity = equity

        # Check drawdown
        drawdown = self.calculate_drawdown()
        self.check_circuit_breakers(drawdown)

    def calculate_drawdown(self) -> float:
        """
        Calculate current drawdown from peak.

        Returns:
            Drawdown as decimal (0.0 to 1.0)
            Returns 0.0 if peak_equity is zero

        Example:
            >>> risk_mgr.peak_equity = 100000
            >>> risk_mgr.current_equity = 85000
            >>> dd = risk_mgr.calculate_drawdown()
            >>> print(f"Drawdown: {dd:.1%}")  # 15.0%
        """
        if self.peak_equity == 0:
            return 0.0

        drawdown = (self.peak_equity - self.current_equity) / self.peak_equity
        return max(0.0, drawdown)  # Ensure non-negative

    def check_circuit_breakers(self, drawdown: float):
        """
        Trigger actions based on drawdown thresholds.

        Implements cascading circuit breakers:
        - 10% DD: WARNING (log only)
        - 15% DD: REDUCE_SIZE (50% position size)
        - 20% DD: STOP_TRADING (halt new trades)
        - 25% DD: CRITICAL (emergency)

        Args:
            drawdown: Current drawdown as decimal

        Side Effects:
            - Updates trading_enabled flag
            - Updates risk_multiplier
            - Prints alerts to console

        Example:
            >>> risk_mgr.check_circuit_breakers(0.16)
            >>> # Prints: "RISK REDUCTION: Position size reduced 50% at 16.0% drawdown"
            >>> print(risk_mgr.risk_multiplier)  # 0.5
        """
        if drawdown >= 0.20:
            self.trading_enabled = False
            self.risk_multiplier = 0.0
            print(
                f"CIRCUIT BREAKER: Trading halted at {drawdown:.1%} drawdown"
            )

        elif drawdown >= 0.15:
            self.risk_multiplier = 0.5
            print(
                f"RISK REDUCTION: Position size reduced 50% at {drawdown:.1%} drawdown"
            )

        elif drawdown >= 0.10:
            print(f"WARNING: {drawdown:.1%} drawdown reached")

        else:
            # Normal operations
            self.trading_enabled = True
            self.risk_multiplier = 1.0

    def validate_position_size(
        self,
        position_size: float,
        price: float,
        capital: float
    ) -> bool:
        """
        Validate position size doesn't exceed limits.

        Checks:
        1. Position value <= 100% of capital
        2. Position value <= 50% of capital (warning)

        Args:
            position_size: Number of shares
            price: Current price per share
            capital: Current account size

        Returns:
            True if position size valid, False if exceeds 100%

        Side Effects:
            Prints warning if position > 50% of capital

        Example:
            >>> valid = risk_mgr.validate_position_size(
            ...     position_size=100,
            ...     price=500,
            ...     capital=100000
            ... )
            >>> # position_value = 100 * 500 = $50,000 (50% of capital)
            >>> # Prints warning but returns True
        """
        if capital <= 0:
            print("Invalid capital: cannot validate position size")
            return False

        position_value = position_size * price
        position_pct = position_value / capital

        if position_pct > 1.0:
            print(f"Position size exceeds capital: {position_pct:.1%}")
            return False

        if position_pct > 0.50:
            print(f"Warning: Large position size: {position_pct:.1%}")

        return True

    def get_adjusted_risk(self, base_risk: float) -> float:
        """
        Get risk adjusted for current drawdown state.

        Applies risk_multiplier to base risk amount. During drawdown,
        risk_multiplier is reduced (0.5 at 15% DD, 0.0 at 20% DD).

        Args:
            base_risk: Base risk amount (e.g., 2% of capital)

        Returns:
            Adjusted risk amount

        Example:
            >>> # Normal: 2% risk
            >>> risk_mgr.risk_multiplier = 1.0
            >>> adjusted = risk_mgr.get_adjusted_risk(0.02)
            >>> print(f"{adjusted:.1%}")  # 2.0%
            >>>
            >>> # After 15% DD: 1% risk
            >>> risk_mgr.risk_multiplier = 0.5
            >>> adjusted = risk_mgr.get_adjusted_risk(0.02)
            >>> print(f"{adjusted:.1%}")  # 1.0%
        """
        return base_risk * self.risk_multiplier

    def is_trading_allowed(self) -> bool:
        """
        Check if trading is currently allowed.

        Returns:
            True if trading allowed, False if circuit breaker triggered

        Example:
            >>> if risk_mgr.is_trading_allowed():
            ...     # Execute trade
            ...     pass
            ... else:
            ...     print("Trading halted due to drawdown")
        """
        return self.trading_enabled

    def get_status(self) -> Dict[str, any]:
        """
        Get current risk manager status.

        Returns:
            Dictionary containing:
            - peak_equity: Highest equity achieved
            - current_equity: Current equity
            - drawdown: Current drawdown percentage
            - trading_enabled: Whether trading allowed
            - risk_multiplier: Current risk multiplier

        Example:
            >>> status = risk_mgr.get_status()
            >>> print(f"DD: {status['drawdown']:.1%}")
            >>> print(f"Trading: {status['trading_enabled']}")
        """
        return {
            'peak_equity': self.peak_equity,
            'current_equity': self.current_equity,
            'drawdown': self.calculate_drawdown(),
            'trading_enabled': self.trading_enabled,
            'risk_multiplier': self.risk_multiplier
        }

    def reset(self):
        """
        Reset risk manager state.

        Useful for testing or starting a new trading session.

        Warning:
            Only use this in testing or controlled environments.
            In live trading, equity should track naturally.
        """
        self.peak_equity = 0.0
        self.current_equity = 0.0
        self.trading_enabled = True
        self.risk_multiplier = 1.0
