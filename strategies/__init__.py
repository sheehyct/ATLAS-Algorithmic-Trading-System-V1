"""
Strategies module for algorithmic trading strategies.

Contains:
- baseline_ma_rsi.py: Simple 200-day MA + RSI(2) mean reversion strategy
- orb.py: Opening Range Breakout (ORB) strategy with ATR-based position sizing
"""

from .baseline_ma_rsi import BaselineStrategy
from .orb import ORBStrategy

__all__ = ['BaselineStrategy', 'ORBStrategy']
