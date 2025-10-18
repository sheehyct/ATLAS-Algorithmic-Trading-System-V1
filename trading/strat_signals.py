"""
STRAT Signal Generator for Algorithmic Trading
Phase 3 Implementation - Trading Logic Integration

This module generates precise STRAT trading signals based on:
1. Pattern detection (2-1-2, 3-1-2, Rev Strats)
2. TFC (Time Frame Continuity) alignment verification
3. Exact trigger prices (inside bar ± $0.01)

Critical STRAT Rules:
- Entry ALWAYS happens at exact price levels (inside bar ± tolerance)
- Never enter on pattern completion, only on trigger break
- TFC alignment must match pattern direction for high probability
- Stops at inside bar opposite extreme
- Targets at previous structural levels (pivots)
"""

import pandas as pd
import numpy as np
import vectorbtpro as vbt
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
from numba import njit

# Import our core components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from core.analyzer import STRATAnalyzer, PatternType, Direction
from core.components import PivotDetector, InsideBarTracker

# Configure logging
logger = logging.getLogger(__name__)


@njit
def clean_strat_signals_nb(long_en, long_ex, short_en, short_ex):
    """
    Clean STRAT entry/exit signals to ensure proper position state tracking.

    Following VBT Pro Cookbook pattern (CookBook/17 Signals.md).

    Rules:
    - Long entry only when flat or in short position
    - Long exit only when in long position
    - Short entry only when flat or in long position
    - Short exit only when in short position

    Args:
        long_en: Boolean array for long entries
        long_ex: Boolean array for long exits (2U->2D reversals)
        short_en: Boolean array for short entries
        short_ex: Boolean array for short exits (2D->2U reversals)

    Returns:
        Tuple of (cleaned_long_en, cleaned_long_ex, cleaned_short_en, cleaned_short_ex)
    """
    new_long_en = np.full_like(long_en, False)
    new_long_ex = np.full_like(long_ex, False)
    new_short_en = np.full_like(short_en, False)
    new_short_ex = np.full_like(short_ex, False)

    for col in range(long_en.shape[1]):
        position = 0  # 0=flat, 1=long, -1=short

        for i in range(long_en.shape[0]):
            # Long entry: only when not already long
            if long_en[i, col] and position != 1:
                new_long_en[i, col] = True
                position = 1
            # Short entry: only when not already short
            elif short_en[i, col] and position != -1:
                new_short_en[i, col] = True
                position = -1
            # Long exit: only when in long position
            elif long_ex[i, col] and position == 1:
                new_long_ex[i, col] = True
                position = 0
            # Short exit: only when in short position
            elif short_ex[i, col] and position == -1:
                new_short_ex[i, col] = True
                position = 0

    return new_long_en, new_long_ex, new_short_en, new_short_ex


@dataclass
class STRATSignal:
    """Container for a STRAT trading signal with all required details"""
    timestamp: pd.Timestamp
    pattern_type: str  # '2-1-2', '3-1-2', 'Rev Strat', etc.
    direction: str  # 'long' or 'short'
    trigger_price: float  # Exact entry price (inside bar ± $0.01)
    stop_price: float  # Stop loss level
    target_price: float  # Primary target (structural level)
    tfc_score: float  # Time Frame Continuity score (0.0 to 1.0)
    tfc_alignment: str  # 'bullish', 'bearish', 'mixed'
    pattern_bars: List[int]  # Bar classifications forming the pattern
    confidence: float  # Overall confidence (pattern + TFC)
    risk_reward: float  # Risk/reward ratio
    notes: str = ""  # Additional notes or warnings
    exit_timestamp: Optional[pd.Timestamp] = None  # When position was exited
    exit_reason: str = ""  # 'reversal', 'stop', 'target'
    exit_price: float = 0.0  # Actual exit price


class STRATSignalGenerator:
    """
    Generates precise STRAT entry signals with TFC validation.

    This is the core trading logic that combines:
    - Pattern recognition from STRATAnalyzer
    - TFC scoring for alignment verification
    - Exact entry price calculation
    - Risk management parameters
    """

    # STRAT standard trigger tolerance
    TRIGGER_TOLERANCE = 0.01  # $0.01 as per STRAT methodology

    # Minimum TFC scores for trading
    MIN_TFC_SCORE = 0.50  # Partial alignment minimum
    PREFERRED_TFC_SCORE = 0.80  # FTC or better preferred

    def __init__(self,
                 min_tfc_score: float = 0.50,
                 require_ftfc: bool = False,
                 risk_per_trade: float = 0.01):  # 1% risk default
        """
        Initialize STRAT Signal Generator.

        Args:
            min_tfc_score: Minimum TFC score to generate signals (default 0.50)
            require_ftfc: If True, only generate signals on FTFC (0.95) alignment
            risk_per_trade: Percentage of capital to risk per trade (default 1%)
        """
        self.min_tfc_score = min_tfc_score
        self.require_ftfc = require_ftfc
        self.risk_per_trade = risk_per_trade
        self.signals: List[STRATSignal] = []

        # Initialize components
        self.analyzer = STRATAnalyzer()
        self.pivot_detector = PivotDetector()
        self.inside_tracker = InsideBarTracker()

        logger.info(f"Initialized STRAT Signal Generator (min_tfc={min_tfc_score})")

    def generate_signals(self,
                        hourly_data: pd.DataFrame,
                        daily_data: pd.DataFrame,
                        weekly_data: pd.DataFrame,
                        monthly_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate STRAT trading signals from multi-timeframe data.

        Args:
            hourly_data: 1H OHLCV data (for future entry timing)
            daily_data: 1D OHLCV data (PRIMARY - patterns detected here)
            weekly_data: 1W OHLCV data for TFC
            monthly_data: 1M OHLCV data for TFC

        Returns:
            DataFrame with columns: entry, exit, trigger_price, stop_price,
                                   target_price, tfc_score, pattern, direction
        """
        # Step 1: Classify bars on all timeframes (including Hourly for TFC)
        hourly_class = self._classify_bars(hourly_data)
        daily_class = self._classify_bars(daily_data)
        weekly_class = self._classify_bars(weekly_data)
        monthly_class = self._classify_bars(monthly_data)

        # Step 2: Calculate TFC scores for each DAILY bar using 4 timeframes
        # Note: Patterns detected on Daily, but TFC uses H+D+W+M alignment
        tfc_results = {
            '1H': {'data': hourly_data, 'classifications': hourly_class},
            '1D': {'data': daily_data, 'classifications': daily_class},
            '1W': {'data': weekly_data, 'classifications': weekly_class},
            '1M': {'data': monthly_data, 'classifications': monthly_class}
        }
        continuity_df = self._calculate_daily_tfc_scores(tfc_results)

        # Step 3: Detect patterns in DAILY data (not hourly!)
        patterns = self._detect_patterns(daily_data, daily_class)

        # Step 4: Generate signals for valid patterns with TFC alignment
        signals_list = []
        for pattern in patterns:
            signal = self._validate_and_create_signal(
                pattern, daily_data, continuity_df
            )
            if signal:
                signals_list.append(signal)
                self.signals.append(signal)

        # Step 5: Generate reversal exit signals (vectorized approach)
        exit_data = self._generate_reversal_exits(daily_data, daily_class, signals_list)

        # Step 6: Convert to VBT-compatible DataFrame with cleaned signals
        # Using daily index since we're trading daily patterns
        return self._create_signal_dataframe_with_exits(
            signals_list, daily_data.index, daily_class, exit_data
        )

    def _classify_bars(self, data: pd.DataFrame) -> pd.Series:
        """
        Classify bars using proper STRAT methodology.

        Returns Series with values:
        - 1: Inside bar
        - 2: 2U (bullish directional)
        - -2: 2D (bearish directional)
        - 3: Outside bar
        """
        if len(data) < 2:
            return pd.Series(0, index=data.index)

        classifications = pd.Series(0, index=data.index)

        # Use governing range logic for proper classification
        governing_high = data['high'].iloc[0]
        governing_low = data['low'].iloc[0]

        for i in range(1, len(data)):
            current_high = data['high'].iloc[i]
            current_low = data['low'].iloc[i]

            # Check against governing range
            is_inside = (current_high <= governing_high) and (current_low >= governing_low)
            breaks_high = current_high > governing_high
            breaks_low = current_low < governing_low

            if is_inside:
                classifications.iloc[i] = 1  # Inside bar
            elif breaks_high and breaks_low:
                classifications.iloc[i] = 3  # Outside bar
                governing_high = current_high
                governing_low = current_low
            elif breaks_high:
                classifications.iloc[i] = 2  # 2U
                governing_high = current_high
                governing_low = current_low
            elif breaks_low:
                classifications.iloc[i] = -2  # 2D
                governing_high = current_high
                governing_low = current_low

        return classifications

    def _calculate_daily_tfc_scores(self, results: Dict[str, Dict]) -> pd.DataFrame:
        """
        Calculate TFC scores for DAILY bars using 4 timeframes (H, D, W, M).

        For each daily bar, we check alignment with:
        - Hourly bars within that day
        - Daily bar classification
        - Weekly bar that contains this day
        - Monthly bar that contains this day
        """
        # Get all timeframe data
        h1_data = results['1H']['data']
        h1_class = results['1H']['classifications']
        d1_data = results['1D']['data']
        d1_class = results['1D']['classifications']
        w1_data = results['1W']['data']
        w1_class = results['1W']['classifications']
        m1_data = results['1M']['data']
        m1_class = results['1M']['classifications']

        # Create continuity DataFrame for daily bars
        continuity_df = pd.DataFrame(index=d1_data.index)
        continuity_df['d1_class'] = d1_class

        # Map daily bars to their parent weekly/monthly timeframes AND hourly children
        for idx in continuity_df.index:
            # Find hourly bars within this daily bar
            # Get all hourly bars on this day
            day_start = idx.replace(hour=0, minute=0, second=0)
            day_end = idx.replace(hour=23, minute=59, second=59)

            hourly_on_day = h1_class[(h1_class.index >= day_start) & (h1_class.index <= day_end)]

            # Determine dominant hourly direction for this day
            if len(hourly_on_day) > 0:
                # Count directional bars in hourly
                h_bullish = (hourly_on_day == 2).sum()
                h_bearish = (hourly_on_day == -2).sum()

                # Dominant hourly classification for the day
                if h_bullish > h_bearish:
                    continuity_df.loc[idx, 'h1_class'] = 2  # Bullish hourly day
                elif h_bearish > h_bullish:
                    continuity_df.loc[idx, 'h1_class'] = -2  # Bearish hourly day
                else:
                    continuity_df.loc[idx, 'h1_class'] = 0  # Mixed/neutral
            else:
                continuity_df.loc[idx, 'h1_class'] = 0  # No hourly data

            # Find corresponding weekly bar
            for w1_idx in w1_data.index:
                # Check if this daily bar falls within the weekly bar's range
                week_start = w1_idx
                week_end = w1_idx + pd.Timedelta(days=6)
                if week_start.date() <= idx.date() <= week_end.date():
                    continuity_df.loc[idx, 'w1_class'] = w1_class[w1_idx]
                    break
            else:
                continuity_df.loc[idx, 'w1_class'] = 0  # Unknown

            # Find corresponding monthly bar
            m1_mask = (m1_data.index.year == idx.year) & (m1_data.index.month == idx.month)
            if m1_mask.any():
                continuity_df.loc[idx, 'm1_class'] = m1_class[m1_mask].iloc[0]
            else:
                continuity_df.loc[idx, 'm1_class'] = 0  # Unknown

        # Calculate alignment scores using 4 timeframes
        for idx in continuity_df.index:
            row = continuity_df.loc[idx]

            # Count bullish and bearish directional bars across all 4 timeframes
            bullish_count = 0
            bearish_count = 0

            for tf in ['h1_class', 'd1_class', 'w1_class', 'm1_class']:
                if row[tf] == 2:  # 2U (bullish directional)
                    bullish_count += 1
                elif row[tf] == -2:  # 2D (bearish directional)
                    bearish_count += 1

            # Determine alignment direction
            if bullish_count > 0 and bearish_count == 0:
                direction = 'bullish'
                alignment_count = bullish_count
            elif bearish_count > 0 and bullish_count == 0:
                direction = 'bearish'
                alignment_count = bearish_count
            elif bullish_count > bearish_count:
                direction = 'bullish_mixed'
                alignment_count = bullish_count
            elif bearish_count > bullish_count:
                direction = 'bearish_mixed'
                alignment_count = bearish_count
            else:
                direction = 'neutral'
                alignment_count = 0

            continuity_df.loc[idx, 'direction'] = direction
            continuity_df.loc[idx, 'alignment_count'] = alignment_count

            # Assign confidence based on 4-timeframe alignment
            # Per HANDOFF.md lines 85-90
            if alignment_count == 4:
                confidence = 0.95  # FTFC: All 4 timeframes aligned (H+D+W+M)
                continuity_type = 'Full'
            elif alignment_count == 3:
                confidence = 0.80  # FTC: 3/4 timeframes aligned
                continuity_type = 'Partial'
            elif alignment_count == 2:
                confidence = 0.50  # Partial: 2/4 timeframes aligned
                continuity_type = 'Minimal'
            elif alignment_count == 1:
                confidence = 0.25  # Minimal: 1/4 timeframe aligned
                continuity_type = 'Weak'
            else:
                confidence = 0.10  # No alignment
                continuity_type = 'None'

            continuity_df.loc[idx, 'confidence'] = confidence
            continuity_df.loc[idx, 'continuity_type'] = continuity_type

        return continuity_df

    def _detect_patterns(self, data: pd.DataFrame, classifications: pd.Series) -> List[Dict]:
        """Detect STRAT patterns using the core STRATAnalyzer implementation."""
        patterns: List[Dict] = []

        if len(classifications) < 2:
            return patterns

        analyzer_signals = []
        try:
            analyzer_signals.extend(self.analyzer.detect_212_pattern(data, classifications))
            analyzer_signals.extend(self.analyzer.detect_312_pattern(data, classifications))
            analyzer_signals.extend(self.analyzer.detect_22_reversal_pattern(data, classifications))
        except Exception as exc:
            logger.error(f"Analyzer pattern detection failed: {exc}")
            return patterns

        for analyzer_signal in analyzer_signals:
            converted = self._convert_analyzer_signal(analyzer_signal)
            if converted:
                patterns.append(converted)

        return patterns

    def _convert_analyzer_signal(self, analyzer_signal) -> Optional[Dict]:
        """Map STRATAnalyzer signal objects into generator-friendly dictionaries."""

        if getattr(analyzer_signal, "direction", None) not in (Direction.BULLISH, Direction.BEARISH):
            return None

        direction = 'long' if analyzer_signal.direction == Direction.BULLISH else 'short'
        pattern_type = analyzer_signal.pattern

        inside_bar_idx: Optional[int] = None
        end_index = int(getattr(analyzer_signal, 'trigger_bar_index', -1))
        if end_index < 0:
            return None

        if pattern_type == PatternType.TWO_ONE_TWO:
            pattern_name = '2-1-2'
            inside_bar_idx = end_index - 1 if end_index - 1 >= 0 else None
        elif pattern_type == PatternType.THREE_ONE_TWO:
            pattern_name = '3-1-2'
            inside_bar_idx = end_index - 1 if end_index - 1 >= 0 else None
        elif pattern_type == PatternType.TWO_TWO_REVERSAL:
            pattern_name = '2-2'
        else:
            return None

        return {
            'type': pattern_name,
            'direction': direction,
            'end_index': end_index,
            'bars': list(getattr(analyzer_signal, 'bar_sequence', [])),
            'inside_bar_idx': inside_bar_idx,
            'analyzer_trigger_price': getattr(analyzer_signal, 'trigger_price', None),
            'analyzer_stop_price': getattr(analyzer_signal, 'stop_loss', None),
            'analyzer_target_price': getattr(analyzer_signal, 'target_price', None),
            'analyzer_confidence': getattr(analyzer_signal, 'confidence', None),
        }

    def _validate_and_create_signal(self,
                                   pattern: Dict,
                                   data: pd.DataFrame,
                                   continuity_df: pd.DataFrame) -> Optional[STRATSignal]:
        """
        Validate pattern with TFC and create signal if valid.

        Critical validations:
        1. TFC score must meet minimum threshold
        2. TFC direction must match pattern direction
        3. Risk/reward must be acceptable (>1:1 minimum)
        """
        idx = pattern['end_index']
        timestamp = data.index[idx]

        # Get TFC score and alignment for this bar
        if timestamp not in continuity_df.index:
            logger.warning(f"No TFC data for {timestamp}")
            return None

        tfc_row = continuity_df.loc[timestamp]
        tfc_score = tfc_row['confidence']
        tfc_alignment = tfc_row['direction']

        # Check minimum TFC score
        if tfc_score < self.min_tfc_score:
            return None

        # Check FTFC requirement
        if self.require_ftfc and tfc_score < 0.95:
            return None

        # Verify direction alignment
        pattern_bullish = pattern['direction'] == 'long'
        tfc_bullish = tfc_alignment in ['bullish', 'bullish_strong']

        if pattern_bullish != tfc_bullish and tfc_alignment != 'mixed':
            logger.debug(f"Pattern direction doesn't match TFC: {pattern['direction']} vs {tfc_alignment}")
            return None

        # Calculate entry, stop, and target prices using analyzer data when available
        trigger_price = None
        stop_price = None
        target_price = None

        analyzer_trigger = pattern.get('analyzer_trigger_price')
        analyzer_stop = pattern.get('analyzer_stop_price')
        analyzer_target = pattern.get('analyzer_target_price')

        if analyzer_trigger is not None and analyzer_stop is not None and analyzer_target is not None:
            if pattern['direction'] == 'long':
                trigger_price = analyzer_trigger + self.TRIGGER_TOLERANCE
            else:
                trigger_price = analyzer_trigger - self.TRIGGER_TOLERANCE
            stop_price = analyzer_stop
            target_price = analyzer_target
        elif pattern['inside_bar_idx'] is not None:
            # Pattern with inside bar (2-1-2, 3-1-2)
            inside_idx = pattern['inside_bar_idx']
            inside_high = data['high'].iloc[inside_idx]
            inside_low = data['low'].iloc[inside_idx]

            if pattern['direction'] == 'long':
                trigger_price = inside_high + self.TRIGGER_TOLERANCE
                stop_price = inside_low
                # Target at previous high (bar 1 of pattern)
                target_price = data['high'].iloc[idx-2]
            else:  # short
                trigger_price = inside_low - self.TRIGGER_TOLERANCE
                stop_price = inside_high
                # Target at previous low (bar 1 of pattern)
                target_price = data['low'].iloc[idx-2]
        else:
            # 2-2 pattern (no inside bar)
            current_high = data['high'].iloc[idx]
            current_low = data['low'].iloc[idx]
            window_start = max(0, idx - 3)

            if pattern['direction'] == 'long':
                trigger_price = current_high + self.TRIGGER_TOLERANCE
                stop_price = current_low
                # Target at previous resistance
                target_price = data['high'].iloc[window_start:idx].max() if idx > 0 else current_high
            else:  # short
                trigger_price = current_low - self.TRIGGER_TOLERANCE
                stop_price = current_high
                # Target at previous support
                target_price = data['low'].iloc[window_start:idx].min() if idx > 0 else current_low

        if trigger_price is None or stop_price is None or target_price is None:
            logger.debug('Pattern missing price levels; skipping signal')
            return None

        # Calculate risk/reward
        risk = abs(trigger_price - stop_price)
        reward = abs(target_price - trigger_price)
        risk_reward = reward / risk if risk > 0 else 0

        # Require minimum 1:1 risk/reward
        if risk_reward < 1.0:
            return None

        # Calculate overall confidence incorporating analyzer weighting
        rr_adjustment = 0.7 + 0.3 * min(risk_reward / 3, 1)
        pattern_confidence = pattern.get('analyzer_confidence')
        if pattern_confidence is not None:
            base_confidence = (tfc_score * 0.6) + (min(pattern_confidence, 1.0) * 0.4)
        else:
            base_confidence = tfc_score
        confidence = min(base_confidence * rr_adjustment, 1.0)

        note_parts = [f"TFC: {tfc_row['continuity_type']}"]
        if pattern_confidence is not None:
            note_parts.append(f"AnalyzerConf: {pattern_confidence:.2f}")
        notes = " | ".join(note_parts)

        # Create signal
        signal = STRATSignal(
            timestamp=timestamp,
            pattern_type=pattern['type'],
            direction=pattern['direction'],
            trigger_price=trigger_price,
            stop_price=stop_price,
            target_price=target_price,
            tfc_score=tfc_score,
            tfc_alignment=tfc_alignment,
            pattern_bars=pattern['bars'],
            confidence=confidence,
            risk_reward=risk_reward,
            notes=notes
        )

        logger.info(f"Generated {pattern['type']} {pattern['direction']} signal at {timestamp} "
                   f"(TFC: {tfc_score:.2f}, R:R: {risk_reward:.1f})")

        return signal

    def _generate_reversal_exits(self,
                                 data: pd.DataFrame,
                                 classifications: pd.Series,
                                 signals: List[STRATSignal]) -> Dict:
        """
        Generate reversal exit signals based on 2-2 reversal patterns.

        TRUE 2-2 Reversal Logic (STRAT methodology):
        - Long positions exit on 2U->2D reversal (prev bar 2U, current bar 2D)
        - Short positions exit on 2D->2U reversal (prev bar 2D, current bar 2U)
        - This is a TWO-bar reversal pattern, not single directional bars
        - Allows holding through momentum continuation (2D-2D-2D or 2U-2U-2U)

        Per STRAT documentation:
        - 2-2 reversal requires consecutive directional bars in opposite directions
        - Exit occurs when price reverses against position direction
        - Inside bars (1) and outside bars (3) do NOT trigger exits

        Args:
            data: OHLCV DataFrame
            classifications: Bar classifications (1, 2, -2, 3)
            signals: List of entry signals generated

        Returns:
            Dict with 'long_exits' and 'short_exits' Series
        """
        # Long exits on 2U->2D reversal pattern
        # Previous bar must be 2U (bullish) AND current bar must be 2D (bearish)
        long_exits_raw = (classifications.shift(1) == 2) & (classifications == -2)

        # Short exits on 2D->2U reversal pattern
        # Previous bar must be 2D (bearish) AND current bar must be 2U (bullish)
        short_exits_raw = (classifications.shift(1) == -2) & (classifications == 2)

        logger.info(f"Generated 2-2 reversal exits: {long_exits_raw.sum()} potential long exits (2U->2D), "
                   f"{short_exits_raw.sum()} potential short exits (2D->2U)")

        return {
            'long_exits': long_exits_raw,
            'short_exits': short_exits_raw
        }

    def _create_signal_dataframe_with_exits(self,
                                           signals: List[STRATSignal],
                                           index: pd.DatetimeIndex,
                                           classifications: pd.Series,
                                           exit_data: Dict) -> pd.DataFrame:
        """
        Convert signals to VBT-compatible DataFrame with cleaned entry/exit arrays.

        Returns DataFrame with:
        - long_entries, long_exits: Cleaned boolean arrays for long positions
        - short_entries, short_exits: Cleaned boolean arrays for short positions
        - trigger_price, stop_price, target_price: Price levels
        - Additional metadata columns
        """
        # Step 1: Create entry arrays from signals
        long_entries_raw = pd.Series(False, index=index)
        short_entries_raw = pd.Series(False, index=index)

        for signal in signals:
            if signal.timestamp in index:
                if signal.direction == 'long':
                    long_entries_raw.loc[signal.timestamp] = True
                else:  # short
                    short_entries_raw.loc[signal.timestamp] = True

        # Step 2: Get exit arrays from exit_data
        long_exits_raw = exit_data['long_exits']
        short_exits_raw = exit_data['short_exits']

        # Step 3: Clean signals using VBT Pro pattern
        # Convert to numpy for numba function
        long_en_arr = vbt.to_2d_array(long_entries_raw)
        long_ex_arr = vbt.to_2d_array(long_exits_raw)
        short_en_arr = vbt.to_2d_array(short_entries_raw)
        short_ex_arr = vbt.to_2d_array(short_exits_raw)

        # Apply signal cleaning
        clean_long_en, clean_long_ex, clean_short_en, clean_short_ex = \
            clean_strat_signals_nb(long_en_arr, long_ex_arr, short_en_arr, short_ex_arr)

        # Convert back to Series
        long_entries = pd.Series(clean_long_en.flatten(), index=index)
        long_exits = pd.Series(clean_long_ex.flatten(), index=index)
        short_entries = pd.Series(clean_short_en.flatten(), index=index)
        short_exits = pd.Series(clean_short_ex.flatten(), index=index)

        logger.info(f"Cleaned signals: {long_entries.sum()} long entries, {long_exits.sum()} long exits, "
                   f"{short_entries.sum()} short entries, {short_exits.sum()} short exits")

        # Step 4: Create DataFrame with all signal data
        df = pd.DataFrame(index=index)
        df['long_entries'] = long_entries
        df['long_exits'] = long_exits
        df['short_entries'] = short_entries
        df['short_exits'] = short_exits

        # Add metadata columns
        df['trigger_price'] = np.nan
        df['stop_price'] = np.nan
        df['target_price'] = np.nan
        df['tfc_score'] = np.nan
        df['pattern'] = ''
        df['direction'] = ''
        df['confidence'] = np.nan

        # Populate metadata from signals
        for signal in signals:
            if signal.timestamp in df.index:
                df.loc[signal.timestamp, 'trigger_price'] = signal.trigger_price
                df.loc[signal.timestamp, 'stop_price'] = signal.stop_price
                df.loc[signal.timestamp, 'target_price'] = signal.target_price
                df.loc[signal.timestamp, 'tfc_score'] = signal.tfc_score
                df.loc[signal.timestamp, 'pattern'] = signal.pattern_type
                df.loc[signal.timestamp, 'direction'] = signal.direction
                df.loc[signal.timestamp, 'confidence'] = signal.confidence

        return df

    def _create_signal_dataframe(self,
                                signals: List[STRATSignal],
                                index: pd.DatetimeIndex) -> pd.DataFrame:
        """
        Convert signals to VBT-compatible DataFrame format.

        Returns DataFrame with:
        - entry: Boolean mask for entry signals
        - exit: Boolean mask for exit signals (at target)
        - trigger_price: Exact entry price
        - stop_price: Stop loss level
        - target_price: Take profit level
        - Additional metadata columns
        """
        # Initialize empty DataFrame
        df = pd.DataFrame(index=index)
        df['entry'] = False
        df['exit'] = False
        df['trigger_price'] = np.nan
        df['stop_price'] = np.nan
        df['target_price'] = np.nan
        df['tfc_score'] = np.nan
        df['pattern'] = ''
        df['direction'] = ''
        df['confidence'] = np.nan

        # Populate with signals
        for signal in signals:
            if signal.timestamp in df.index:
                df.loc[signal.timestamp, 'entry'] = True
                df.loc[signal.timestamp, 'trigger_price'] = signal.trigger_price
                df.loc[signal.timestamp, 'stop_price'] = signal.stop_price
                df.loc[signal.timestamp, 'target_price'] = signal.target_price
                df.loc[signal.timestamp, 'tfc_score'] = signal.tfc_score
                df.loc[signal.timestamp, 'pattern'] = signal.pattern_type
                df.loc[signal.timestamp, 'direction'] = signal.direction
                df.loc[signal.timestamp, 'confidence'] = signal.confidence

        return df

    def get_summary(self) -> str:
        """Get summary of generated signals"""
        if not self.signals:
            return "No signals generated"

        total = len(self.signals)
        longs = sum(1 for s in self.signals if s.direction == 'long')
        shorts = total - longs
        avg_tfc = np.mean([s.tfc_score for s in self.signals])
        avg_rr = np.mean([s.risk_reward for s in self.signals])

        patterns = {}
        for s in self.signals:
            patterns[s.pattern_type] = patterns.get(s.pattern_type, 0) + 1

        summary = f"""
Signal Generation Summary:
-------------------------
Total Signals: {total}
  - Long: {longs}
  - Short: {shorts}

Average TFC Score: {avg_tfc:.3f}
Average Risk/Reward: {avg_rr:.2f}

Pattern Distribution:
{chr(10).join(f'  - {p}: {c}' for p, c in patterns.items())}
"""
        return summary