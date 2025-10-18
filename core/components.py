"""
STRAT Trading System Core Components
Phase 3 Implementation - Foundation Components

This module implements the three critical components for STRAT trading:
1. Pivot Detector - Uses VBT Pro's PIVOTINFO for finding swing highs/lows
2. Inside Bar Tracker - Manages entry/stop levels based on inside bars
3. Pattern State Machine - Tracks pattern lifecycle with real-time trigger logic

Critical Understanding:
- Every bar starts as a "1" until it breaks a level
- Entries happen at EXACT break levels (inside_bar ± $0.01), not on pattern completion
- Targets are previous pivots (magnitude), not arbitrary ratios
- Failed patterns become opposite opportunities (Rev STRAT)
"""

import pandas as pd
import numpy as np
import vectorbtpro as vbt
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# COMPONENT 1: PIVOT DETECTOR
# ============================================================================

class PivotDetector:
    """
    Detects swing highs/lows using VBT Pro's PIVOTINFO.
    These pivots become the target levels (magnitude) for STRAT trades.

    Key Concepts:
    - Pivots = local highs/lows that become targets
    - PMG (Pivot Machine Gun) = 5+ consecutive pivots
    - Only tracks "untaken" pivots (not yet breached by price)
    """

    def __init__(self, up_threshold: float = 0.2, down_threshold: float = 0.2):
        """
        Initialize Pivot Detector.

        Args:
            up_threshold: Percentage threshold for detecting swing highs (default 0.2%)
            down_threshold: Percentage threshold for detecting swing lows (default 0.2%)
        """
        self.up_threshold = up_threshold
        self.down_threshold = down_threshold
        self.pivot_info = None
        self.untaken_highs = []
        self.untaken_lows = []

    def detect_pivots(self, high: pd.Series, low: pd.Series) -> Dict:
        """
        Detect pivots using VBT Pro's PIVOTINFO.

        Args:
            high: High prices
            low: Low prices

        Returns:
            Dict with pivot information
        """
        # Use VBT Pro's native pivot detection
        self.pivot_info = vbt.PIVOTINFO.run(
            high,
            low,
            up_th=self.up_threshold,
            down_th=self.down_threshold
        )

        # Extract confirmed pivots
        pivot_types = self.pivot_info.conf_pivot  # 1=peak, -1=valley
        pivot_indices = self.pivot_info.conf_idx
        pivot_values = self.pivot_info.conf_value

        # Separate peaks and valleys
        peaks = []
        valleys = []

        for i in range(len(pivot_types)):
            if pivot_types.iloc[i] == 1:  # Peak (swing high)
                peaks.append({
                    'index': pivot_indices.iloc[i],
                    'value': pivot_values.iloc[i],
                    'timestamp': high.index[pivot_indices.iloc[i]] if hasattr(high, 'index') else i
                })
            elif pivot_types.iloc[i] == -1:  # Valley (swing low)
                valleys.append({
                    'index': pivot_indices.iloc[i],
                    'value': pivot_values.iloc[i],
                    'timestamp': low.index[pivot_indices.iloc[i]] if hasattr(low, 'index') else i
                })

        logger.info(f"Detected {len(peaks)} swing highs and {len(valleys)} swing lows")

        return {
            'peaks': peaks,
            'valleys': valleys,
            'pivot_array': self.pivot_info.pivots,  # Raw array for PMG detection
            'pivot_info': self.pivot_info
        }

    def get_untaken_pivots(self, pivots: List[Dict], prices: pd.Series,
                           pivot_type: str = 'high') -> List[Dict]:
        """
        Filter pivots to only those that haven't been breached yet.

        Args:
            pivots: List of pivot dictionaries
            prices: Price series to check against
            pivot_type: 'high' for peaks or 'low' for valleys

        Returns:
            List of untaken pivots
        """
        untaken = []

        for pivot in pivots:
            pivot_idx = pivot['index']
            pivot_value = pivot['value']

            # Check if pivot has been taken out by subsequent price action
            if pivot_idx < len(prices) - 1:
                subsequent_prices = prices.iloc[pivot_idx + 1:]

                if pivot_type == 'high':
                    # High is untaken if price hasn't exceeded it
                    if subsequent_prices.max() < pivot_value:
                        untaken.append(pivot)
                else:  # low
                    # Low is untaken if price hasn't broken below it
                    if subsequent_prices.min() > pivot_value:
                        untaken.append(pivot)

        return untaken

    def detect_pmg(self, pivot_array: np.ndarray, min_count: int = 5) -> List[Dict]:
        """
        Detect Pivot Machine Gun (PMG) patterns - 5+ consecutive pivots.

        Args:
            pivot_array: Array from PIVOTINFO with 1=peak, -1=valley, 0=no pivot
            min_count: Minimum consecutive pivots for PMG (default 5)

        Returns:
            List of PMG patterns with start/end indices
        """
        pmg_patterns = []
        current_run = []

        for i, pivot in enumerate(pivot_array):
            if pivot != 0:  # Peak or valley
                current_run.append((i, pivot))

                # Check if we have a valid PMG
                if len(current_run) >= min_count:
                    # Verify alternating pattern (peak-valley-peak or valley-peak-valley)
                    is_alternating = all(
                        current_run[j][1] != current_run[j+1][1]
                        for j in range(len(current_run)-1)
                    )

                    if is_alternating and len(current_run) == min_count:
                        # Record the PMG pattern
                        pmg_patterns.append({
                            'start_idx': current_run[0][0],
                            'end_idx': current_run[-1][0],
                            'pivot_count': len(current_run),
                            'type': 'bullish' if current_run[0][1] == -1 else 'bearish',
                            'pivots': current_run
                        })
            else:
                # Reset run if no pivot
                if len(current_run) >= min_count:
                    # Save before resetting if we had a valid PMG
                    is_alternating = all(
                        current_run[j][1] != current_run[j+1][1]
                        for j in range(len(current_run)-1)
                    )
                    if is_alternating:
                        pmg_patterns.append({
                            'start_idx': current_run[0][0],
                            'end_idx': current_run[-1][0],
                            'pivot_count': len(current_run),
                            'type': 'bullish' if current_run[0][1] == -1 else 'bearish',
                            'pivots': current_run
                        })
                current_run = []

        logger.info(f"Detected {len(pmg_patterns)} PMG patterns")
        return pmg_patterns

    def get_magnitude_targets(self, current_price: float, untaken_pivots: List[Dict],
                             direction: str = 'long') -> List[float]:
        """
        Get target levels based on untaken pivots in trade direction.

        Args:
            current_price: Current price level
            untaken_pivots: List of untaken pivot dictionaries
            direction: 'long' or 'short'

        Returns:
            List of target prices sorted by distance from current price
        """
        targets = []

        for pivot in untaken_pivots:
            pivot_value = pivot['value']

            if direction == 'long' and pivot_value > current_price:
                targets.append(pivot_value)
            elif direction == 'short' and pivot_value < current_price:
                targets.append(pivot_value)

        # Sort by distance from current price
        if direction == 'long':
            targets.sort()  # Nearest to farthest for longs
        else:
            targets.sort(reverse=True)  # Nearest to farthest for shorts

        return targets


# ============================================================================
# COMPONENT 2: INSIDE BAR TRACKER
# ============================================================================

class InsideBarTracker:
    """
    Tracks and manages inside bars (Scenario 1) which define entry and stop levels.

    Critical for STRAT:
    - Entry = inside_bar_high + $0.01 (long) or inside_bar_low - $0.01 (short)
    - Stop = opposite side of inside bar
    - Inside bars are the foundation of most STRAT patterns
    """

    def __init__(self, buffer: float = 0.01):
        """
        Initialize Inside Bar Tracker.

        Args:
            buffer: Price buffer for entry triggers (default $0.01)
        """
        self.buffer = buffer
        self.inside_bars = {}  # Dict[index] = {'high': x, 'low': y, 'timestamp': z}

    def mark_inside_bar(self, idx: int, high: float, low: float,
                        timestamp: Optional[datetime] = None) -> None:
        """
        Store an inside bar for pattern reference.

        Args:
            idx: Bar index
            high: Inside bar high
            low: Inside bar low
            timestamp: Optional timestamp
        """
        self.inside_bars[idx] = {
            'high': high,
            'low': low,
            'timestamp': timestamp,
            'governing_high': None,  # Will be set based on pattern context
            'governing_low': None
        }
        logger.debug(f"Marked inside bar at index {idx}: H={high:.2f}, L={low:.2f}")

    def get_trigger_price(self, bar_idx: int, direction: str = 'long') -> Optional[float]:
        """
        Get the trigger price for entering a trade based on inside bar.

        Args:
            bar_idx: Index of the inside bar
            direction: 'long' or 'short'

        Returns:
            Trigger price or None if bar not found
        """
        if bar_idx not in self.inside_bars:
            logger.warning(f"No inside bar found at index {bar_idx}")
            return None

        bar = self.inside_bars[bar_idx]

        if direction == 'long':
            return bar['high'] + self.buffer
        else:  # short
            return bar['low'] - self.buffer

    def get_stop_price(self, bar_idx: int, direction: str = 'long') -> Optional[float]:
        """
        Get the stop loss price based on inside bar.

        Args:
            bar_idx: Index of the inside bar
            direction: 'long' or 'short'

        Returns:
            Stop loss price or None if bar not found
        """
        if bar_idx not in self.inside_bars:
            logger.warning(f"No inside bar found at index {bar_idx}")
            return None

        bar = self.inside_bars[bar_idx]

        if direction == 'long':
            return bar['low']  # Stop at inside bar low for longs
        else:  # short
            return bar['high']  # Stop at inside bar high for shorts

    def get_inside_bar_range(self, bar_idx: int) -> Optional[Tuple[float, float]]:
        """
        Get the full range of an inside bar.

        Args:
            bar_idx: Index of the inside bar

        Returns:
            Tuple of (low, high) or None if not found
        """
        if bar_idx not in self.inside_bars:
            return None

        bar = self.inside_bars[bar_idx]
        return (bar['low'], bar['high'])

    def scan_for_inside_bars(self, df: pd.DataFrame) -> List[int]:
        """
        Scan a DataFrame for all inside bars and mark them.

        Args:
            df: DataFrame with OHLC data

        Returns:
            List of indices where inside bars were found
        """
        inside_bar_indices = []

        for i in range(1, len(df)):
            current = df.iloc[i]
            previous = df.iloc[i-1]

            # Inside bar: high < previous high AND low > previous low
            if current['high'] < previous['high'] and current['low'] > previous['low']:
                self.mark_inside_bar(
                    i,
                    current['high'],
                    current['low'],
                    current.name if hasattr(current, 'name') else None
                )
                inside_bar_indices.append(i)

        logger.info(f"Found {len(inside_bar_indices)} inside bars")
        return inside_bar_indices


# ============================================================================
# COMPONENT 3: PATTERN STATE MACHINE
# ============================================================================

class PatternState(Enum):
    """States for STRAT pattern lifecycle"""
    SCANNING = "scanning"          # Looking for pattern
    PENDING = "pending"            # Pattern partially formed
    TRIGGERED = "triggered"        # Pattern complete, ready to trade
    IN_FORCE = "in_force"         # Pattern active, can enter
    ENTERED = "entered"           # Trade taken
    COMPLETE = "complete"         # Target hit
    FAILED = "failed"             # Stop hit or pattern invalidated


@dataclass
class PatternContext:
    """Context for a pattern being tracked"""
    pattern_type: str              # e.g., "2-1-2", "3-1-2"
    bars_seen: List[int] = field(default_factory=list)  # Classification of bars seen so far
    inside_bar_idx: Optional[int] = None  # Index of the inside bar
    direction: Optional[str] = None       # 'bullish' or 'bearish'
    entry_trigger: Optional[float] = None # Price level that triggers entry
    stop_level: Optional[float] = None    # Stop loss level
    targets: List[float] = field(default_factory=list)  # Target levels from pivots
    trigger_time: Optional[datetime] = None
    entry_price: Optional[float] = None
    entry_time: Optional[datetime] = None


class PatternStateMachine:
    """
    Tracks pattern lifecycle from formation to completion.

    Critical Concept: Patterns transition through states based on real-time price action.
    A pattern can be "triggered" (complete) but still needs price to break the inside bar
    level to become "in force" (tradeable).
    """

    def __init__(self, inside_bar_tracker: InsideBarTracker,
                 pivot_detector: Optional[PivotDetector] = None):
        """
        Initialize Pattern State Machine.

        Args:
            inside_bar_tracker: Reference to Inside Bar Tracker
            pivot_detector: Optional reference to Pivot Detector for targets
        """
        self.inside_bar_tracker = inside_bar_tracker
        self.pivot_detector = pivot_detector
        self.patterns = {}  # Dict[pattern_id] = (state, context)
        self.pattern_counter = 0

    def start_pattern(self, pattern_type: str, first_bar: int) -> int:
        """
        Begin tracking a new pattern.

        Args:
            pattern_type: Type of pattern (e.g., "2-1-2")
            first_bar: Classification of first bar

        Returns:
            Pattern ID for tracking
        """
        pattern_id = self.pattern_counter
        self.pattern_counter += 1

        context = PatternContext(
            pattern_type=pattern_type
        )
        context.bars_seen = [first_bar]

        self.patterns[pattern_id] = (PatternState.SCANNING, context)
        logger.debug(f"Started tracking pattern {pattern_id} ({pattern_type})")

        return pattern_id

    def update_pattern(self, pattern_id: int, new_bar: int,
                      bar_high: float, bar_low: float) -> PatternState:
        """
        Update pattern with new bar information.

        Args:
            pattern_id: ID of pattern to update
            new_bar: Classification of new bar (1, 2, -2, 3)
            bar_high: High of the new bar
            bar_low: Low of the new bar

        Returns:
            New state of the pattern
        """
        if pattern_id not in self.patterns:
            logger.warning(f"Pattern {pattern_id} not found")
            return None

        state, context = self.patterns[pattern_id]
        context.bars_seen.append(new_bar)

        # Check pattern completion based on type
        if context.pattern_type == "2-1-2":
            if len(context.bars_seen) == 2 and context.bars_seen[-1] == 1:
                # We have "2-1", move to pending
                state = PatternState.PENDING
                # Mark the inside bar
                self.inside_bar_tracker.mark_inside_bar(
                    len(context.bars_seen) - 1, bar_high, bar_low
                )
                context.inside_bar_idx = len(context.bars_seen) - 1

            elif len(context.bars_seen) == 3:
                # Pattern complete, determine direction
                if context.bars_seen[0] == 2 and context.bars_seen[2] == -2:
                    # 2U-1-2D (bearish)
                    context.direction = 'bearish'
                elif context.bars_seen[0] == -2 and context.bars_seen[2] == 2:
                    # 2D-1-2U (bullish)
                    context.direction = 'bullish'

                # Pattern is triggered (complete)
                state = PatternState.TRIGGERED

                # Set entry trigger and stop levels
                if context.inside_bar_idx is not None:
                    if context.direction == 'bullish':
                        context.entry_trigger = self.inside_bar_tracker.get_trigger_price(
                            context.inside_bar_idx, 'long'
                        )
                        context.stop_level = self.inside_bar_tracker.get_stop_price(
                            context.inside_bar_idx, 'long'
                        )
                    else:
                        context.entry_trigger = self.inside_bar_tracker.get_trigger_price(
                            context.inside_bar_idx, 'short'
                        )
                        context.stop_level = self.inside_bar_tracker.get_stop_price(
                            context.inside_bar_idx, 'short'
                        )

        # Update pattern state
        self.patterns[pattern_id] = (state, context)
        return state

    def check_trigger(self, pattern_id: int, current_high: float,
                     current_low: float) -> bool:
        """
        Check if price has broken the trigger level to make pattern "in force".

        This is the critical moment when a bar transforms from "1" to "2",
        making the pattern tradeable.

        Args:
            pattern_id: ID of pattern to check
            current_high: Current bar's high
            current_low: Current bar's low

        Returns:
            True if pattern is now in force
        """
        if pattern_id not in self.patterns:
            return False

        state, context = self.patterns[pattern_id]

        # Only check triggered patterns
        if state != PatternState.TRIGGERED:
            return False

        # Check if price broke the trigger level
        if context.direction == 'bullish' and current_high >= context.entry_trigger:
            # Pattern is now in force - can enter long
            self.patterns[pattern_id] = (PatternState.IN_FORCE, context)
            context.trigger_time = datetime.now()
            logger.info(f"Pattern {pattern_id} IN FORCE - Bullish at {context.entry_trigger:.2f}")
            return True

        elif context.direction == 'bearish' and current_low <= context.entry_trigger:
            # Pattern is now in force - can enter short
            self.patterns[pattern_id] = (PatternState.IN_FORCE, context)
            context.trigger_time = datetime.now()
            logger.info(f"Pattern {pattern_id} IN FORCE - Bearish at {context.entry_trigger:.2f}")
            return True

        return False

    def enter_trade(self, pattern_id: int, entry_price: float) -> bool:
        """
        Mark pattern as entered when trade is taken.

        Args:
            pattern_id: ID of pattern
            entry_price: Actual entry price

        Returns:
            True if successfully marked as entered
        """
        if pattern_id not in self.patterns:
            return False

        state, context = self.patterns[pattern_id]

        if state == PatternState.IN_FORCE:
            context.entry_price = entry_price
            context.entry_time = datetime.now()
            self.patterns[pattern_id] = (PatternState.ENTERED, context)
            logger.info(f"Pattern {pattern_id} ENTERED at {entry_price:.2f}")
            return True

        return False

    def check_exit(self, pattern_id: int, current_high: float,
                  current_low: float) -> str:
        """
        Check if trade should exit (hit target or stop).

        Args:
            pattern_id: ID of pattern
            current_high: Current bar's high
            current_low: Current bar's low

        Returns:
            'complete' if target hit, 'failed' if stop hit, 'active' if still running
        """
        if pattern_id not in self.patterns:
            return 'unknown'

        state, context = self.patterns[pattern_id]

        if state != PatternState.ENTERED:
            return 'not_entered'

        # Check stop loss
        if context.direction == 'bullish' and current_low <= context.stop_level:
            self.patterns[pattern_id] = (PatternState.FAILED, context)
            logger.info(f"Pattern {pattern_id} FAILED - Stop hit at {context.stop_level:.2f}")
            return 'failed'
        elif context.direction == 'bearish' and current_high >= context.stop_level:
            self.patterns[pattern_id] = (PatternState.FAILED, context)
            logger.info(f"Pattern {pattern_id} FAILED - Stop hit at {context.stop_level:.2f}")
            return 'failed'

        # Check targets
        if context.targets:
            if context.direction == 'bullish' and current_high >= context.targets[0]:
                self.patterns[pattern_id] = (PatternState.COMPLETE, context)
                logger.info(f"Pattern {pattern_id} COMPLETE - Target hit at {context.targets[0]:.2f}")
                return 'complete'
            elif context.direction == 'bearish' and current_low <= context.targets[0]:
                self.patterns[pattern_id] = (PatternState.COMPLETE, context)
                logger.info(f"Pattern {pattern_id} COMPLETE - Target hit at {context.targets[0]:.2f}")
                return 'complete'

        return 'active'

    def get_pattern_state(self, pattern_id: int) -> Optional[PatternState]:
        """Get current state of a pattern."""
        if pattern_id in self.patterns:
            return self.patterns[pattern_id][0]
        return None

    def get_pattern_context(self, pattern_id: int) -> Optional[PatternContext]:
        """Get context of a pattern."""
        if pattern_id in self.patterns:
            return self.patterns[pattern_id][1]
        return None


# ============================================================================
# TESTING UTILITIES
# ============================================================================

def test_components():
    """Basic test of all three components."""

    print("=" * 60)
    print("TESTING STRAT COMPONENTS")
    print("=" * 60)

    # Create sample data
    dates = pd.date_range('2024-01-01', periods=20, freq='D')
    high = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                     111, 110, 112, 114, 113, 115, 117, 116, 118, 120], index=dates)
    low = pd.Series([98, 99, 100, 101, 102, 103, 104, 105, 106, 107,
                    108, 109, 110, 111, 112, 113, 114, 115, 116, 117], index=dates)

    # Test Pivot Detector
    print("\n1. Testing Pivot Detector...")
    pivot_detector = PivotDetector()
    pivots = pivot_detector.detect_pivots(high, low)
    print(f"   Found {len(pivots['peaks'])} peaks and {len(pivots['valleys'])} valleys")

    # Test PMG detection
    pmg_patterns = pivot_detector.detect_pmg(pivots['pivot_array'])
    print(f"   Found {len(pmg_patterns)} PMG patterns")

    # Test Inside Bar Tracker
    print("\n2. Testing Inside Bar Tracker...")
    inside_tracker = InsideBarTracker()

    # Create a simple DataFrame for testing
    df = pd.DataFrame({
        'high': high,
        'low': low,
        'open': (high + low) / 2,
        'close': (high + low) / 2
    })

    inside_bars = inside_tracker.scan_for_inside_bars(df)
    print(f"   Found {len(inside_bars)} inside bars at indices: {inside_bars[:5]}...")

    # Test Pattern State Machine
    print("\n3. Testing Pattern State Machine...")
    state_machine = PatternStateMachine(inside_tracker, pivot_detector)

    # Simulate a 2-1-2 pattern
    pattern_id = state_machine.start_pattern("2-1-2", 2)  # Start with 2U
    print(f"   Started pattern {pattern_id}")

    # Add inside bar
    state = state_machine.update_pattern(pattern_id, 1, 101.5, 100.5)
    print(f"   After adding inside bar: state = {state}")

    # Complete pattern
    state = state_machine.update_pattern(pattern_id, -2, 102, 99)
    print(f"   After completing pattern: state = {state}")

    # Check trigger
    triggered = state_machine.check_trigger(pattern_id, 100, 98.5)
    print(f"   Pattern triggered: {triggered}")

    print("\n" + "=" * 60)
    print("COMPONENT TESTING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_components()