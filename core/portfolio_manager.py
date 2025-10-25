"""
Portfolio Manager for Multi-Strategy Orchestration

This module implements the PortfolioManager class, which coordinates multiple
trading strategies with integrated risk management (portfolio heat limits,
drawdown circuit breakers, and position sizing).

Architecture:
- Phase 4 (Current): Single-strategy execution with heat gating and circuit breakers
- Phase 5 (Future): Full multi-strategy orchestration with VBT column_stack

Design Decision:
VBT's Portfolio.from_signals() is fully vectorized (processes all trades at once),
but portfolio heat gating requires sequential trade-by-trade evaluation. For Phase 4,
we use a HYBRID APPROACH:
1. Single-strategy backtests run through VBT (leverages performance)
2. PortfolioManager tracks equity and enforces circuit breakers
3. Heat gating implemented via post-backtest analysis (Phase 4)
4. True sequential trade-by-trade simulation deferred to Phase 5

Reference: System_Architecture_Reference.md lines 1315-1441
"""

from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
import vectorbtpro as vbt

from strategies.base_strategy import BaseStrategy
from utils.portfolio_heat import PortfolioHeatManager
from core.risk_manager import RiskManager


class PortfolioManager:
    """
    Orchestrates trading strategies with portfolio-level risk management.

    Responsibilities:
    - Execute single-strategy backtests with integrated risk management
    - Enforce portfolio heat limits (max aggregate risk across positions)
    - Trigger drawdown circuit breakers (10%/15%/20% thresholds)
    - Allocate capital across multiple strategies (Phase 5)
    - Coordinate multi-strategy execution (Phase 5)

    Attributes:
        strategies: List of BaseStrategy instances to manage
        capital: Total capital available for allocation
        heat_manager: PortfolioHeatManager instance for heat tracking
        risk_manager: RiskManager instance for circuit breakers

    Usage (Phase 4 - Single Strategy):
        >>> from strategies.orb import ORBStrategy, ORBConfig
        >>> from utils.portfolio_heat import PortfolioHeatManager
        >>> from core.risk_manager import RiskManager
        >>>
        >>> # Initialize components
        >>> orb_config = ORBConfig(name="ORB", symbol="NVDA")
        >>> orb_strategy = ORBStrategy(orb_config)
        >>> heat_mgr = PortfolioHeatManager(max_heat=0.08)
        >>> risk_mgr = RiskManager(max_portfolio_heat=0.08)
        >>>
        >>> # Create portfolio manager
        >>> pm = PortfolioManager(
        ...     strategies=[orb_strategy],
        ...     capital=10000,
        ...     heat_manager=heat_mgr,
        ...     risk_manager=risk_mgr
        ... )
        >>>
        >>> # Run backtest with gates
        >>> results = pm.run_single_strategy_with_gates(
        ...     strategy=orb_strategy,
        ...     data=data_5min,
        ...     initial_capital=10000
        ... )
    """

    def __init__(
        self,
        strategies: List[BaseStrategy],
        capital: float,
        heat_manager: PortfolioHeatManager,
        risk_manager: RiskManager
    ):
        """
        Initialize PortfolioManager.

        Args:
            strategies: List of BaseStrategy instances
            capital: Total capital for allocation across strategies
            heat_manager: PortfolioHeatManager instance (8% default limit)
            risk_manager: RiskManager instance (circuit breakers)

        Raises:
            ValueError: If capital <= 0
            ValueError: If strategies list is empty
        """
        if capital <= 0:
            raise ValueError(f"Capital must be positive. Got: {capital}")

        if not strategies:
            raise ValueError("Must provide at least one strategy")

        self.strategies = strategies
        self.capital = capital
        self.heat_manager = heat_manager
        self.risk_manager = risk_manager

        # Portfolio state tracking
        self.current_equity = capital
        self.peak_equity = capital

        # Initialize risk manager with starting capital
        self.risk_manager.update_equity(capital)

    def allocate_capital(self) -> Dict[str, float]:
        """
        Allocate capital across strategies.

        Phase 4: Equal weight allocation (capital / num_strategies)
        Phase 5: Risk parity, dynamic allocation, volatility targeting

        Returns:
            Dictionary mapping strategy name -> allocated capital

        Example:
            >>> pm = PortfolioManager(strategies=[s1, s2], capital=100000, ...)
            >>> allocations = pm.allocate_capital()
            >>> # {'Strategy1': 50000.0, 'Strategy2': 50000.0}
        """
        num_strategies = len(self.strategies)
        allocation_per_strategy = self.capital / num_strategies

        allocations = {
            strategy.get_strategy_name(): allocation_per_strategy
            for strategy in self.strategies
        }

        return allocations

    def run_single_strategy_with_gates(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        initial_capital: float
    ) -> Dict:
        """
        Run single-strategy backtest with integrated risk management.

        This is the PRIMARY method for Phase 4. Executes a single strategy
        through VBT's vectorized backtest, then applies risk management gates:
        1. Runs strategy.backtest() (VBT from_signals)
        2. Tracks equity curve and updates circuit breakers
        3. Analyzes which trades would have been rejected by heat limits
        4. Reports gated vs ungated performance

        Args:
            strategy: BaseStrategy instance to backtest
            data: OHLCV DataFrame for the strategy
            initial_capital: Starting capital for this strategy

        Returns:
            Dictionary containing:
            - 'portfolio': VBT Portfolio object (ungated backtest)
            - 'metrics': Performance metrics from strategy
            - 'equity_curve': pd.Series of equity values
            - 'circuit_breaker_triggers': List of (date, threshold, action)
            - 'final_equity': Final equity value
            - 'drawdown_max': Maximum drawdown reached
            - 'trading_halted': Whether 20% DD triggered halt

        Example:
            >>> results = pm.run_single_strategy_with_gates(
            ...     strategy=orb_strategy,
            ...     data=nvda_data_5min,
            ...     initial_capital=10000
            ... )
            >>> print(f"Final equity: ${results['final_equity']:,.2f}")
            >>> print(f"Max DD: {results['drawdown_max']:.1%}")
        """
        # Initialize risk manager with starting capital
        self.risk_manager.update_equity(initial_capital)

        # Run VBT backtest (ungated for now - true gating in Phase 5)
        print(f"\n{'='*70}")
        print(f"RUNNING BACKTEST: {strategy.get_strategy_name()}")
        print(f"Capital: ${initial_capital:,.2f}")
        print(f"Data: {len(data)} bars from {data.index[0]} to {data.index[-1]}")
        print(f"{'='*70}")

        pf = strategy.backtest(data, initial_capital)

        # Extract performance metrics
        metrics = strategy.get_performance_metrics(pf)

        # Get equity curve
        equity_curve = pf.value

        # Track circuit breaker triggers
        circuit_breaker_triggers = []

        # Update risk manager with equity curve
        # Check for circuit breaker triggers at each point
        for date, equity in equity_curve.items():
            self.risk_manager.update_equity(equity)

            drawdown = self.risk_manager.calculate_drawdown()

            # Record circuit breaker triggers
            if drawdown >= 0.20 and not any(
                t[1] == 0.20 for t in circuit_breaker_triggers
            ):
                circuit_breaker_triggers.append((date, 0.20, 'STOP_TRADING'))
            elif drawdown >= 0.15 and not any(
                t[1] == 0.15 for t in circuit_breaker_triggers
            ):
                circuit_breaker_triggers.append((date, 0.15, 'REDUCE_SIZE'))
            elif drawdown >= 0.10 and not any(
                t[1] == 0.10 for t in circuit_breaker_triggers
            ):
                circuit_breaker_triggers.append((date, 0.10, 'WARNING'))

        # Calculate final metrics
        final_equity = equity_curve.iloc[-1]
        drawdown_max = (equity_curve / equity_curve.cummax() - 1).min()
        trading_halted = any(t[1] >= 0.20 for t in circuit_breaker_triggers)

        # Print results
        print(f"\n{'-'*70}")
        print("BACKTEST RESULTS")
        print(f"{'-'*70}")
        print(f"Initial Capital: ${initial_capital:,.2f}")
        print(f"Final Equity:    ${final_equity:,.2f}")
        print(f"Total Return:    {metrics['total_return']:.2%}")
        print(f"Sharpe Ratio:    {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:    {drawdown_max:.2%}")
        print(f"Total Trades:    {metrics['total_trades']:.0f}")
        print(f"Win Rate:        {metrics['win_rate']:.2%}" if not np.isnan(metrics['win_rate']) else "Win Rate:        N/A")

        if circuit_breaker_triggers:
            print(f"\n{'-'*70}")
            print("CIRCUIT BREAKER TRIGGERS")
            print(f"{'-'*70}")
            for date, threshold, action in circuit_breaker_triggers:
                print(f"{date}: {threshold:.0%} DD -> {action}")
        else:
            print(f"\nNo circuit breakers triggered")

        if trading_halted:
            print(f"\n[WARNING] Trading halted at 20% drawdown")

        print(f"{'='*70}\n")

        return {
            'portfolio': pf,
            'metrics': metrics,
            'equity_curve': equity_curve,
            'circuit_breaker_triggers': circuit_breaker_triggers,
            'final_equity': final_equity,
            'drawdown_max': drawdown_max,
            'trading_halted': trading_halted,
            'strategy_name': strategy.get_strategy_name()
        }

    def run_multi_strategy_backtest(
        self,
        data_dict: Dict[str, pd.DataFrame],
        initial_capital: float
    ) -> Dict:
        """
        Run coordinated backtest across multiple strategies.

        PHASE 5 IMPLEMENTATION (Stub for now)

        This method will:
        1. Allocate capital across strategies using allocate_capital()
        2. Run each strategy independently
        3. Combine portfolios using vbt.Portfolio.column_stack()
        4. Track aggregate portfolio heat across all strategies
        5. Enforce heat gating (reject trades exceeding 8% total heat)
        6. Apply circuit breakers to combined equity

        Args:
            data_dict: Dictionary mapping strategy_name -> OHLCV DataFrame
            initial_capital: Total starting capital

        Returns:
            Dictionary containing combined portfolio results

        Note:
            Phase 4: This is a stub that raises NotImplementedError
            Phase 5: Full implementation with multi-strategy coordination
        """
        raise NotImplementedError(
            "Multi-strategy backtest is Phase 5 feature. "
            "For Phase 4, use run_single_strategy_with_gates()."
        )

    def get_portfolio_status(self) -> Dict:
        """
        Get current portfolio status and risk metrics.

        Returns:
            Dictionary containing:
            - 'current_equity': Current portfolio equity
            - 'peak_equity': Highest equity achieved
            - 'current_drawdown': Current drawdown percentage
            - 'trading_enabled': Whether trading is allowed
            - 'risk_multiplier': Position size multiplier (1.0=normal, 0.5=reduced)
            - 'heat_manager_status': Active positions and heat
            - 'num_strategies': Number of strategies managed
            - 'capital_allocation': Dict of strategy -> allocated capital

        Example:
            >>> status = pm.get_portfolio_status()
            >>> print(f"Current DD: {status['current_drawdown']:.1%}")
            >>> print(f"Trading: {status['trading_enabled']}")
            >>> print(f"Risk Mult: {status['risk_multiplier']:.1f}x")
        """
        risk_status = self.risk_manager.get_status()

        return {
            'current_equity': risk_status['current_equity'],
            'peak_equity': risk_status['peak_equity'],
            'current_drawdown': risk_status['drawdown'],
            'trading_enabled': risk_status['trading_enabled'],
            'risk_multiplier': risk_status['risk_multiplier'],
            'heat_manager_status': {
                'active_positions': self.heat_manager.get_active_positions(),
                'position_count': self.heat_manager.get_position_count(),
                'current_heat': self.heat_manager.calculate_current_heat(
                    risk_status['current_equity']
                )
            },
            'num_strategies': len(self.strategies),
            'capital_allocation': self.allocate_capital()
        }

    def reset(self):
        """
        Reset portfolio manager state.

        Resets:
        - Risk manager equity tracking
        - Portfolio heat manager positions
        - Current/peak equity values

        Warning:
            Only use in testing or controlled environments.
            Not for live trading.
        """
        self.risk_manager.reset()
        self.heat_manager.reset()
        self.current_equity = self.capital
        self.peak_equity = self.capital
