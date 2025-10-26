"""
Regime Detection Framework

This module provides market regime detection and regime-based capital allocation
for the ATLAS trading system.

Modules:
    jump_model: Jump Model implementation for regime classification
    regime_allocator: Regime-based capital allocation logic

Market Regimes:
    TREND_BULL: Strong bullish trend (jump probability >70%, positive direction)
    TREND_NEUTRAL: Choppy/sideways market (jump probability 30-70%)
    TREND_BEAR: Strong bearish trend (jump probability >70%, negative direction)
    CRASH: Extreme volatility event (special indicators triggered)
"""

from regime.jump_model import JumpModel

__all__ = [
    'JumpModel',
    'RegimeAllocator',
]
