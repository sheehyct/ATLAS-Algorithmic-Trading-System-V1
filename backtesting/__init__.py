"""
Backtesting Infrastructure

This module provides backtesting and validation frameworks for the ATLAS trading system.

Modules:
    backtest_engine: VectorBT Pro wrapper for strategy backtesting
    walk_forward: Walk-forward analysis for out-of-sample validation
    report_generator: Performance reporting and visualization

Validation Methodology:
    - Walk-forward analysis with 1-year training, 3-month testing windows
    - Performance degradation <30% acceptance criterion
    - Monte Carlo simulation for statistical robustness
    - Transaction cost analysis for high-frequency strategies
"""

__all__ = [
    'BacktestEngine',
    'WalkForwardValidator',
    'ReportGenerator',
]
