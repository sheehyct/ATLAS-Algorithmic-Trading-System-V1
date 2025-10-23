"""
Portfolio Heat Management for Algorithmic Trading Strategies

This module implements Layer 2 (Portfolio Heat) of the ATLAS risk management
framework. Portfolio heat tracks aggregate risk exposure across all open
positions and enforces hard limits to prevent excessive total risk.

CRITICAL: This is a GATING mechanism that sits BEFORE trade execution.
Trades are REJECTED if they would exceed the portfolio heat limit.

Reference: System_Architecture_Reference.md lines 1770-1869
"""

from typing import Dict


class PortfolioHeatManager:
    """
    Tracks aggregate risk across all positions.
    Rejects new trades if total portfolio heat would exceed limit.

    Portfolio heat is defined as: sum(all position risks) / capital

    Example:
        - Position 1: $2,000 at risk
        - Position 2: $2,500 at risk
        - Position 3: $2,000 at risk
        - Capital: $100,000
        - Portfolio heat: ($2,000 + $2,500 + $2,000) / $100,000 = 6.5%

    Professional Standard:
        - Max heat: 6-8% (hard limit, NO exceptions)
        - Heat limit enforced BEFORE trade entry
        - Heat recalculated as stops trail (risk reduces over time)

    Usage:
        >>> heat_manager = PortfolioHeatManager(max_heat=0.08)
        >>> capital = 100000
        >>>
        >>> # Add existing positions
        >>> heat_manager.add_position('SPY', 2000)
        >>> heat_manager.add_position('QQQ', 2500)
        >>>
        >>> # Check if new position accepted
        >>> if heat_manager.can_accept_trade('AAPL', 2000, capital):
        ...     print("Trade accepted")
        ... else:
        ...     print("Trade rejected - heat limit")
    """

    def __init__(self, max_heat: float = 0.08):
        """
        Initialize portfolio heat manager.

        Args:
            max_heat: Maximum portfolio heat as decimal (default 8%)
                     Range: 0.06 to 0.08 (6% to 8%)

        Raises:
            ValueError: If max_heat outside professional range
        """
        if max_heat < 0.06 or max_heat > 0.10:
            raise ValueError(
                f"max_heat must be between 0.06 and 0.10 (6%-10%). "
                f"Got: {max_heat:.1%}"
            )

        self.max_heat = max_heat
        self.active_positions: Dict[str, float] = {}  # symbol -> risk_amount

    def calculate_current_heat(self, capital: float) -> float:
        """
        Calculate current portfolio heat as percentage of capital.

        Args:
            capital: Current account size

        Returns:
            Current heat as decimal (0.0 to 1.0)
            Returns 0.0 if no positions or capital is zero

        Example:
            >>> heat_manager.add_position('SPY', 2000)
            >>> heat_manager.add_position('QQQ', 1500)
            >>> heat = heat_manager.calculate_current_heat(100000)
            >>> print(f"Current heat: {heat:.1%}")  # 3.5%
        """
        if capital <= 0:
            return 0.0

        if not self.active_positions:
            return 0.0

        total_risk = sum(self.active_positions.values())
        return total_risk / capital

    def can_accept_trade(
        self,
        symbol: str,
        position_risk: float,
        capital: float
    ) -> bool:
        """
        Check if new trade would exceed heat limit.

        This is the GATING function that enforces portfolio heat limits.
        Trades are REJECTED if they would push total heat over max_heat.

        Args:
            symbol: Symbol for new trade
            position_risk: Dollar risk for new trade (position_size * stop_distance)
            capital: Current account size

        Returns:
            True if trade accepted, False if rejected

        Side Effects:
            Prints rejection message if trade would exceed heat limit

        Example:
            >>> # Current heat: 7% (3 positions)
            >>> # New trade: $2,000 risk would push to 9%
            >>> accepted = heat_manager.can_accept_trade('AAPL', 2000, 100000)
            >>> # Prints: "REJECTED: Trade would increase heat from 7.0% to 9.0%"
            >>> # Returns: False
        """
        current_heat = self.calculate_current_heat(capital)

        # Calculate what heat would be with new position
        new_total_risk = sum(self.active_positions.values()) + position_risk
        new_heat = new_total_risk / capital if capital > 0 else 0.0

        if new_heat > self.max_heat:
            print(
                f"REJECTED: Trade would increase heat from {current_heat:.1%} "
                f"to {new_heat:.1%}"
            )
            print(f"Max heat: {self.max_heat:.1%}")
            print(f"Symbol: {symbol}, Proposed risk: ${position_risk:,.2f}")
            return False

        return True

    def add_position(self, symbol: str, risk_amount: float):
        """
        Add new position to heat tracking.

        Call this AFTER trade execution to track the position's risk.

        Args:
            symbol: Symbol for new position
            risk_amount: Dollar risk for position (position_size * stop_distance)

        Raises:
            ValueError: If symbol already exists in active positions
            ValueError: If risk_amount is negative

        Example:
            >>> heat_manager.add_position('SPY', 2000)
            >>> heat_manager.add_position('QQQ', 2500)
        """
        if symbol in self.active_positions:
            raise ValueError(
                f"Position for {symbol} already exists. "
                f"Use update_position_risk() to modify."
            )

        if risk_amount < 0:
            raise ValueError(
                f"risk_amount must be non-negative. Got: {risk_amount}"
            )

        self.active_positions[symbol] = risk_amount

    def remove_position(self, symbol: str):
        """
        Remove position from heat tracking (trade closed).

        Call this when a position is closed (stop hit, exit signal, etc.)
        to remove its risk from portfolio heat calculation.

        Args:
            symbol: Symbol for closed position

        Note:
            Silently succeeds if symbol not found (idempotent operation)

        Example:
            >>> heat_manager.remove_position('SPY')
            >>> # Heat reduced by SPY's risk amount
        """
        if symbol in self.active_positions:
            del self.active_positions[symbol]

    def update_position_risk(self, symbol: str, new_risk: float):
        """
        Update risk for existing position (e.g., trailing stop moved).

        As stops trail price, the distance from current price to stop
        decreases, reducing the dollar risk. Call this to update heat
        calculation with new (lower) risk.

        Args:
            symbol: Symbol for existing position
            new_risk: New dollar risk (position_size * new_stop_distance)

        Raises:
            ValueError: If symbol not found in active positions
            ValueError: If new_risk is negative

        Example:
            >>> # Initial risk: $2,000 (entry at $100, stop at $80)
            >>> heat_manager.add_position('AAPL', 2000)
            >>>
            >>> # Price moves to $120, trail stop to $100
            >>> # New risk: $2,000 (still 100 shares * $20)
            >>> heat_manager.update_position_risk('AAPL', 2000)
            >>>
            >>> # Price moves to $140, trail stop to $120
            >>> # New risk: $2,000 (still 100 shares * $20)
            >>> # BUT if position was reduced, risk goes down
        """
        if symbol not in self.active_positions:
            raise ValueError(
                f"Position for {symbol} not found. "
                f"Use add_position() first."
            )

        if new_risk < 0:
            raise ValueError(
                f"new_risk must be non-negative. Got: {new_risk}"
            )

        self.active_positions[symbol] = new_risk

    def get_active_positions(self) -> Dict[str, float]:
        """
        Get current active positions.

        Returns:
            Dictionary mapping symbol -> risk_amount

        Example:
            >>> positions = heat_manager.get_active_positions()
            >>> for symbol, risk in positions.items():
            ...     print(f"{symbol}: ${risk:,.2f} at risk")
        """
        return self.active_positions.copy()

    def get_position_count(self) -> int:
        """
        Get number of active positions.

        Returns:
            Count of active positions

        Example:
            >>> count = heat_manager.get_position_count()
            >>> print(f"Active positions: {count}")
        """
        return len(self.active_positions)

    def reset(self):
        """
        Clear all active positions.

        Useful for testing or starting a new trading session.

        Warning:
            Only use this in testing or controlled environments.
            In live trading, positions should be removed individually
            when they close naturally.
        """
        self.active_positions.clear()
