"""
Strategies module for ATLAS algorithmic trading strategies.

Contains:
- base_strategy.py: Abstract base class for all strategies
- orb.py: Opening Range Breakout (ORB) strategy with ATR-based position sizing
"""

from .base_strategy import BaseStrategy, StrategyConfig
from .orb import ORBStrategy

__all__ = ['BaseStrategy', 'StrategyConfig', 'ORBStrategy']
