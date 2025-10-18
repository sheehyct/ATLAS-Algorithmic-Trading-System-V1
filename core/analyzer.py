"""
STRAT Pattern Analyzer for Algorithmic Trading Bot

This module implements Rob Smith's STRAT methodology for pattern recognition:
- Bar classification (1, 2, 3 labeling system)
- Pattern detection (2-1-2, 3-1-2, Rev STRAT)
- Multi-timeframe analysis
- Signal generation with confidence scoring

STRAT Methodology Overview:
- 1 Bar: Inside bar (high < previous high AND low > previous low)
- 2 Bar: Outside bar (high > previous high AND low < previous low)  
- 3 Bar: Directional bar (breaks high OR low, but not both)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from enum import Enum
from collections import deque

# Internal imports
try:
    from config.logging_config import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# FTC analyzer not yet implemented in new structure
FTFC_AVAILABLE = False

class BarType(Enum):
    """STRAT bar classification (Rob Smith methodology)"""
    INSIDE = 1        # Inside bar (1) - contained within previous bar
    DIRECTIONAL = 2   # Directional bar (2) - breaks one side only (2U up or 2D down)
    OUTSIDE = 3       # Outside bar (3) - breaks both sides (engulfs previous bar)

class PatternType(Enum):
    """STRAT pattern types"""
    TWO_ONE_TWO = "2-1-2"           # High probability continuation
    THREE_ONE_TWO = "3-1-2"         # Strong reversal setup
    THREE_TWO_TWO = "3-2-2"         # Outside-Directional-Directional (strong trend)
    TWO_TWO_REVERSAL = "2-2 Reversal"    # Simple directional reversal (2U→2D or 2D→2U)
    TWO_TWO_CONTINUATION = "2-2 Continuation"  # Simple trend continuation (2U→2U or 2D→2D)
    REV_STRAT = "Rev STRAT"         # Failed breakout reversal
    FTFC_COMBO = "FTFC_COMBO"       # Multi-timeframe combination pattern
    TWO_ONE_TWO_REVERSAL = "2-1-2_REVERSAL"  # Reversal variant of 2-1-2
    BROADENING_FORMATION = "BF"     # Broadening formation
    
class Direction(Enum):
    """Trade direction"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"

@dataclass
class STRATSignal:
    """STRAT trading signal with all relevant data"""
    symbol: str
    timeframe: str
    pattern: PatternType
    direction: Direction
    confidence: float           # 0.0 to 1.0
    entry_price: float          # Actual execution price (current bar's price)
    trigger_price: float        # STRAT level that triggers entry (e.g., inside bar high/low)
    stop_loss: float
    target_price: float
    timestamp: datetime
    bar_sequence: List[int]     # e.g., [2, 1, 2]
    trigger_bar_index: int
    risk_reward_ratio: float
    notes: str = ""
    
    # FTFC Integration (Full Timeframe Continuity)
    ftfc_strength: Optional[float] = None        # 0.0 to 1.0 FTFC alignment strength
    ftfc_direction: Optional[str] = None         # 'bullish', 'bearish', 'neutral'
    supporting_timeframes: List[str] = None      # Timeframes supporting this signal
    conflicting_timeframes: List[str] = None     # Timeframes conflicting with signal
    ftfc_enhanced_confidence: Optional[float] = None  # Confidence after FTFC adjustment
    
    def __post_init__(self):
        """Initialize fields after object creation"""
        if self.supporting_timeframes is None:
            self.supporting_timeframes = []
        if self.conflicting_timeframes is None:
            self.conflicting_timeframes = []

class STRATAnalyzer:
    """
    Core STRAT pattern analyzer implementing Rob Smith's methodology
    
    Features:
    - Real-time bar classification (1, 2, 3 system)
    - Pattern detection for all major STRAT setups
    - Multi-timeframe confluence analysis
    - Confidence scoring based on pattern strength
    - Risk/reward calculation for each signal
    """
    
    def __init__(self, enable_ftfc: bool = True):
        self.logger = logger
        self.min_bars_required = 20  # Minimum bars needed for analysis
        self.enable_ftfc = enable_ftfc and FTFC_AVAILABLE
        self.recent_patterns = deque(maxlen=50)  # Track recent patterns for deduplication
        
        # Pattern confidence weights
        self.pattern_weights = {
            PatternType.TWO_ONE_TWO: 0.85,           # High probability
            PatternType.THREE_ONE_TWO: 0.90,         # Very high probability
            PatternType.THREE_TWO_TWO: 0.88,         # Very high probability (strong trend)
            PatternType.TWO_TWO_REVERSAL: 0.75,      # Good probability for simple reversal
            PatternType.TWO_TWO_CONTINUATION: 0.80,  # Good probability for trend continuation
            PatternType.REV_STRAT: 0.75,             # Good probability
            PatternType.FTFC_COMBO: 0.95,            # Highest probability (multi-timeframe)
            PatternType.TWO_ONE_TWO_REVERSAL: 0.80,  # Good probability
            PatternType.BROADENING_FORMATION: 0.70   # Moderate probability
        }
        
        # Initialize FTFC components if available
        self.ftc_analyzer = None
        self.alpaca_client = None
        
        if self.enable_ftfc:
            try:
                self.alpaca_client = AlpacaDataConnector()
                self.ftc_analyzer = FTCAnalyzer(self.alpaca_client, self)
                self.logger.info("[STRAT] Analyzer initialized with FTFC integration")
            except Exception as e:
                self.logger.warning(f"[STRAT] FTFC initialization failed: {e}")
                self.enable_ftfc = False
                self.logger.info("[STRAT] Analyzer initialized without FTFC")
        else:
            self.logger.info("[STRAT] Analyzer initialized without FTFC")
    
    def classify_bars(self, df: pd.DataFrame) -> pd.Series:
        """
        Classify each bar using STRAT methodology with CORRECT governing range tracking.

        Critical fix: Consecutive inside bars reference the SAME governing range
        until broken by a 2 or 3. Now distinguishes 2U (2) from 2D (-2).

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Series with bar classifications (1=inside, 2=2U, -2=2D, 3=outside)
        """

        if len(df) < 2:
            return pd.Series([], dtype=int)

        # Extract price arrays
        high_values = df['high'].values
        low_values = df['low'].values
        n_bars = len(df)

        # Initialize classifications array
        # CRITICAL: First bar is reference only (not classified)
        # Use -999 as marker for unclassified reference bar
        classifications = np.zeros(n_bars, dtype=int)
        classifications[0] = -999  # Special marker for unclassified reference

        # CRITICAL: Track governing range (persists through inside bars)
        # First bar provides the initial reference range
        governing_high = high_values[0]
        governing_low = low_values[0]

        # Must use loop for stateful governing range tracking
        # Start from bar 1 (first CLASSIFIED bar, using bar 0 as reference)
        for i in range(1, n_bars):
            current_high = high_values[i]
            current_low = low_values[i]

            # Check against GOVERNING range (not just previous bar!)
            is_inside = (current_high <= governing_high) and (current_low >= governing_low)
            breaks_high = current_high > governing_high
            breaks_low = current_low < governing_low

            if is_inside:
                classifications[i] = 1  # Inside bar
                # Governing range DOES NOT change for inside bars!
            elif breaks_high and breaks_low:
                classifications[i] = 3  # Outside bar (3)
                governing_high = current_high
                governing_low = current_low
            elif breaks_high:
                classifications[i] = 2  # 2U - Upward directional
                governing_high = current_high
                governing_low = current_low
            elif breaks_low:
                classifications[i] = -2  # 2D - Downward directional
                governing_high = current_high
                governing_low = current_low

        # Create series with proper index
        strat_series = pd.Series(classifications, index=df.index, name='strat_classification')

        # Count classifications for debug (excluding reference bar)
        # Exclude first bar (-999) from counts
        classified_bars = classifications[classifications != -999]
        inside_count = np.sum(classified_bars == 1)
        up_count = np.sum(classified_bars == 2)
        down_count = np.sum(classified_bars == -2)
        outside_count = np.sum(classified_bars == 3)

        self.logger.debug(f"Classification of {len(df)} bars: "
                         f"{inside_count} inside, {up_count} 2U, {down_count} 2D, "
                         f"{outside_count} outside")

        return strat_series
    
    def _is_duplicate_pattern(self, signal: STRATSignal) -> bool:
        """
        Check if pattern is a duplicate of recently detected patterns.
        
        Args:
            signal: STRATSignal to check for duplication
            
        Returns:
            True if pattern is duplicate, False if new/unique
        """
        # Create pattern fingerprint
        fingerprint = {
            'pattern': signal.pattern.value,
            'timestamp': signal.timestamp,
            'entry_price': round(signal.entry_price, 2),
            'stop_loss': round(signal.stop_loss, 2),
            'target_price': round(signal.target_price, 2),
            'direction': signal.direction.value
        }
        
        # Check against recent patterns
        for recent_pattern in self.recent_patterns:
            if (recent_pattern['pattern'] == fingerprint['pattern'] and
                recent_pattern['timestamp'] == fingerprint['timestamp'] and
                abs(recent_pattern['entry_price'] - fingerprint['entry_price']) < 0.01 and
                recent_pattern['direction'] == fingerprint['direction']):
                return True
        
        # Not a duplicate, add to recent patterns
        self.recent_patterns.append(fingerprint)
        return False
    
    def detect_212_pattern(self, df: pd.DataFrame, strat_classes: pd.Series) -> List[STRATSignal]:
        """
        Detect 2-1-2 patterns (high probability continuation setups)
        
        2-1-2 Pattern (Rob Smith STRAT methodology):
        - Directional bar (2) shows initial directional move (2U up or 2D down)
        - Inside bar (1) shows consolidation within directional bar
        - Directional bar (2) continues the initial direction and triggers entry
        
        Args:
            df: Price data
            strat_classes: Bar classifications
            
        Returns:
            List of 2-1-2 signals found
        """
        
        signals = []
        
        if len(strat_classes) < 3:
            return signals
        
        # VBT PRO COMPATIBLE VECTORIZED 2-1-2 PATTERN DETECTION - NO LOOPS!
        if len(strat_classes) >= 3:
            # Extract classification values for vectorized operations
            class_values = strat_classes.values
            n_bars = len(class_values)
            
            # VECTORIZED 2-1-2 DETECTION using numpy array slicing
            # Create sliding window views of 3 consecutive bars
            bar_1 = class_values[:-2]    # Bars 0 to n-3 (first bar of pattern)
            bar_2 = class_values[1:-1]   # Bars 1 to n-2 (middle bar of pattern)  
            bar_3 = class_values[2:]     # Bars 2 to n-1 (last bar of pattern)
            
            # Detect all 4 types of 2-1-2 patterns with proper direction
            # Bullish patterns
            pattern_2u_1_2u = (bar_1 == 2) & (bar_2 == 1) & (bar_3 == 2)    # Bullish continuation
            pattern_2d_1_2u = (bar_1 == -2) & (bar_2 == 1) & (bar_3 == 2)   # Bullish reversal

            # Bearish patterns
            pattern_2d_1_2d = (bar_1 == -2) & (bar_2 == 1) & (bar_3 == -2)  # Bearish continuation
            pattern_2u_1_2d = (bar_1 == 2) & (bar_2 == 1) & (bar_3 == -2)   # Bearish reversal

            # Find all pattern indices
            bullish_cont_indices = np.where(pattern_2u_1_2u)[0] + 2
            bullish_rev_indices = np.where(pattern_2d_1_2u)[0] + 2
            bearish_cont_indices = np.where(pattern_2d_1_2d)[0] + 2
            bearish_rev_indices = np.where(pattern_2u_1_2d)[0] + 2

            # Process all patterns with directional context
            for idx in bullish_cont_indices:
                signal = self._analyze_212_signal(df, idx, strat_classes)
                if signal and not self._is_duplicate_pattern(signal):
                    signals.append(signal)

            for idx in bullish_rev_indices:
                signal = self._analyze_212_signal(df, idx, strat_classes)
                if signal and not self._is_duplicate_pattern(signal):
                    signals.append(signal)

            for idx in bearish_cont_indices:
                signal = self._analyze_212_signal(df, idx, strat_classes)
                if signal and not self._is_duplicate_pattern(signal):
                    signals.append(signal)

            for idx in bearish_rev_indices:
                signal = self._analyze_212_signal(df, idx, strat_classes)
                if signal and not self._is_duplicate_pattern(signal):
                    signals.append(signal)
        
        self.logger.debug(f"VECTORIZED: Found {len(signals)} 2-1-2 patterns")
        return signals
    
    def detect_312_pattern(self, df: pd.DataFrame, strat_classes: pd.Series) -> List[STRATSignal]:
        """
        Detect 3-1-2 patterns (strong reversal setups)
        
        3-1-2 Pattern (Rob Smith STRAT methodology):
        - Outside bar (3) creates initial range expansion and setup
        - Inside bar (1) shows consolidation within the outside bar
        - Directional bar (2) breaks out of the inside bar (reversal entry)
        
        Args:
            df: Price data  
            strat_classes: Bar classifications
            
        Returns:
            List of 3-1-2 signals found
        """
        
        signals = []
        
        if len(strat_classes) < 3:
            return signals
        
        # VBT PRO COMPATIBLE VECTORIZED 3-1-2 PATTERN DETECTION - NO LOOPS!
        if len(strat_classes) >= 3:
            # Extract classification values for vectorized operations
            class_values = strat_classes.values
            
            # VECTORIZED 3-1-2 DETECTION using numpy array slicing
            # Create sliding window views of 3 consecutive bars
            bar_1 = class_values[:-2]    # Bars 0 to n-3 (first bar of pattern)
            bar_2 = class_values[1:-1]   # Bars 1 to n-2 (middle bar of pattern)  
            bar_3 = class_values[2:]     # Bars 2 to n-1 (last bar of pattern)
            
            # Detect both types of 3-1-2 patterns with proper direction
            pattern_3_1_2u = (bar_1 == 3) & (bar_2 == 1) & (bar_3 == 2)    # Bullish breakout
            pattern_3_1_2d = (bar_1 == 3) & (bar_2 == 1) & (bar_3 == -2)   # Bearish breakout

            # Find pattern indices
            bullish_indices = np.where(pattern_3_1_2u)[0] + 2
            bearish_indices = np.where(pattern_3_1_2d)[0] + 2

            # Process bullish 3-1-2U patterns
            for idx in bullish_indices:
                signal = self._analyze_312_signal(df, idx, strat_classes)
                if signal and not self._is_duplicate_pattern(signal):
                    signals.append(signal)

            # Process bearish 3-1-2D patterns
            for idx in bearish_indices:
                signal = self._analyze_312_signal(df, idx, strat_classes)
                if signal and not self._is_duplicate_pattern(signal):
                    signals.append(signal)
        
        self.logger.debug(f"VECTORIZED: Found {len(signals)} 3-1-2 patterns")
        return signals
    
    def detect_rev_strat_pattern(self, df: pd.DataFrame, strat_classes: pd.Series) -> List[STRATSignal]:
        """
        Detect Rev STRAT patterns (failed breakout reversals)
        
        Rev STRAT Pattern:
        - Price breaks out of range (directional move)
        - Fails to continue (reversal signal)
        - Creates opportunity in opposite direction
        
        Args:
            df: Price data
            strat_classes: Bar classifications
            
        Returns:
            List of Rev STRAT signals found
        """
        
        signals = []
        
        if len(df) < 5:
            return signals
        
        # Look for failed breakout patterns - check recent bars for pattern completion
        # Use reasonable lookback window instead of only absolute last bar
        if len(df) >= 5:
            # Define lookback window: check last 10 bars or all available bars, whichever is smaller
            lookback_window = min(10, len(df) - 4)
            start_index = max(4, len(df) - lookback_window)
            
            for i in range(start_index, len(df)):
                if i >= 4:  # Ensure we have at least 5 bars for Rev STRAT
                    signal = self._analyze_rev_strat_signal(df, i, strat_classes)
                    if signal and not self._is_duplicate_pattern(signal):
                        signals.append(signal)
        
        self.logger.debug(f"Found {len(signals)} Rev STRAT patterns")
        
        # ENHANCED: Check for Rev STRAT patterns that follow 3-1-2 setups
        # This catches cases where a 3-1-2 pattern completes but then reverses on the next bar
        additional_rev_strats = self._detect_post_312_rev_strats(df, strat_classes)
        signals.extend(additional_rev_strats)
        
        return signals
    
    def _detect_post_312_rev_strats(self, df: pd.DataFrame, strat_classes: pd.Series) -> List[STRATSignal]:
        """
        Detect Rev STRAT patterns that follow 3-1-2 setups.
        
        Pattern: 3-1-2D-2U (bearish 3-1-2 followed by bullish reversal)
        Pattern: 3-1-2U-2D (bullish 3-1-2 followed by bearish reversal)
        """
        signals = []
        
        if len(df) < 4:
            return signals
        
        # Look for 3-1-2 patterns followed by reversal bars
        for i in range(3, len(df)):
            # Check if we have a 3-1-2 sequence in the previous 3 bars
            if i >= 3:
                prev_sequence = strat_classes.iloc[i-3:i].tolist()  # 3 bars before current
                current_class = strat_classes.iloc[i]
                
                if prev_sequence == [3, 1, 2] and current_class == 2:
                    # We have 3-1-2-2 sequence - potential Rev STRAT
                    bar1 = df.iloc[i-3]  # Outside bar (3)
                    bar2 = df.iloc[i-2]  # Inside bar (1)
                    bar3 = df.iloc[i-1]  # Directional bar (2)
                    bar4 = df.iloc[i]    # Reversal bar (2)
                    
                    # Determine if this is a valid Rev STRAT
                    # FIXED: More robust direction detection - check actual breakouts, not just comparisons
                    # Bar 3 direction: Did it break out of Bar 2 up or down?
                    bar3_breaks_up = bar3['high'] > bar2['high'] and bar3['low'] >= bar2['low']  # 2U
                    bar3_breaks_down = bar3['low'] < bar2['low'] and bar3['high'] <= bar2['high']  # 2D

                    # Bar 4 direction: Did it break out of Bar 2 up or down?
                    bar4_breaks_up = bar4['high'] > bar2['high'] and bar4['low'] >= bar2['low']  # 2U
                    bar4_breaks_down = bar4['low'] < bar2['low'] and bar4['high'] <= bar2['high']  # 2D

                    # Check for valid reversal patterns
                    if (bar3_breaks_up and bar4_breaks_down) or (bar3_breaks_down and bar4_breaks_up):
                        # Bullish Rev STRAT: 3-1-2D-2U
                        if bar3_breaks_down and bar4_breaks_up:
                            # Check if bar3 failed to reach its target (Bar 1's low)
                            failed_target = bar3['low'] > bar1['low']  # Failed to reach Bar 1's low extreme
                            
                            if failed_target:
                                signal = STRATSignal(
                                    symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                                    timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                                    pattern=PatternType.REV_STRAT,
                                    direction=Direction.BULLISH,
                                    confidence=0.95,  # High confidence for post-312 Rev STRAT
                                    entry_price=bar3['high'] + 0.01,  # Enter when Bar 4 breaks above Bar 3 high (failed breakdown bar)
                                    trigger_price=bar3['high'],       # Failed breakdown bar high trigger
                                    stop_loss=bar3['low'],       # Failed breakdown low
                                    target_price=bar1['high'],   # Outside bar high target
                                    timestamp=df.index[i],
                                    bar_sequence=[3, 1, 2, 2],
                                    trigger_bar_index=i,
                                    risk_reward_ratio=0.0,
                                    notes="Post-312 Rev STRAT BULLISH: 3-1-2D-2U"
                                )
                                
                                # Calculate risk/reward
                                risk = abs(signal.entry_price - signal.stop_loss)
                                reward = abs(signal.target_price - signal.entry_price)
                                signal.risk_reward_ratio = reward / risk if risk > 0 else 0
                                
                                signals.append(signal)
                                self.logger.info(f"Post-312 Rev STRAT BULLISH detected at {df.index[i]}")
                        
                        # Bearish Rev STRAT: 3-1-2U-2D
                        elif bar3_breaks_up and bar4_breaks_down:
                            # Check if bar3 failed to reach its target (Bar 1's high)
                            failed_target = bar3['high'] < bar1['high']  # Failed to reach Bar 1's high extreme
                            
                            if failed_target:
                                signal = STRATSignal(
                                    symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                                    timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                                    pattern=PatternType.REV_STRAT,
                                    direction=Direction.BEARISH,
                                    confidence=0.95,  # High confidence for post-312 Rev STRAT
                                    entry_price=bar3['low'] - 0.01,  # Enter when Bar 4 breaks below Bar 3 low (failed breakout bar)
                                    trigger_price=bar3['low'],        # Failed breakout bar low trigger
                                    stop_loss=bar3['high'],      # Failed breakout high
                                    target_price=bar1['low'],    # Outside bar low target
                                    timestamp=df.index[i],
                                    bar_sequence=[3, 1, 2, 2],
                                    trigger_bar_index=i,
                                    risk_reward_ratio=0.0,
                                    notes="Post-312 Rev STRAT BEARISH: 3-1-2U-2D"
                                )
                                
                                # Calculate risk/reward
                                risk = abs(signal.entry_price - signal.stop_loss)
                                reward = abs(signal.target_price - signal.entry_price)
                                signal.risk_reward_ratio = reward / risk if risk > 0 else 0
                                
                                signals.append(signal)
                                self.logger.info(f"Post-312 Rev STRAT BEARISH detected at {df.index[i]}")
        
        return signals
    
    def _analyze_212_signal(self, df: pd.DataFrame, trigger_index: int, strat_classes: pd.Series) -> Optional[STRATSignal]:
        """Analyze a potential 2-1-2 signal for validity and strength"""
        
        try:
            # Get the three bars in the pattern: 2-1-2 (Directional-Inside-Directional)
            bar1_idx = trigger_index - 2  # First directional bar (2)
            bar2_idx = trigger_index - 1  # Inside bar (1)  
            bar3_idx = trigger_index      # Second directional bar (2) - trigger
            
            bar1 = df.iloc[bar1_idx]
            bar2 = df.iloc[bar2_idx]  
            bar3 = df.iloc[bar3_idx]
            
            # Determine direction based on the initial directional bar's move
            # and confirm the trigger bar continues in same direction
            if bar1_idx > 0:
                bar0 = df.iloc[bar1_idx - 1]  # Bar before the pattern
                
                # Check if first directional bar was bullish (2U)
                bar1_bullish = bar1['high'] > bar0['high'] and bar1['low'] >= bar0['low']
                # Check if first directional bar was bearish (2D)  
                bar1_bearish = bar1['low'] < bar0['low'] and bar1['high'] <= bar0['high']
                
                if bar1_bullish and bar3['high'] > bar2['high']:
                    # Bullish continuation: 2U-1-2U
                    direction = Direction.BULLISH
                    trigger_price = bar2['high']  # STRAT trigger level (inside bar high)
                    entry_price = bar3['open']    # Actual execution price on breakout bar
                    stop_loss = bar2['low']       # Inside bar low
                    # Measured move: project the directional bar's range
                    pattern_height = bar1['high'] - bar1['low']
                    target_price = trigger_price + pattern_height
                    
                elif bar1_bearish and bar3['low'] < bar2['low']:
                    # Bearish continuation: 2D-1-2D
                    direction = Direction.BEARISH  
                    trigger_price = bar2['low']   # STRAT trigger level (inside bar low)
                    entry_price = bar3['open']    # Actual execution price on breakout bar
                    stop_loss = bar2['high']      # Inside bar high
                    # Measured move: project the directional bar's range
                    pattern_height = bar1['high'] - bar1['low']
                    target_price = trigger_price - pattern_height
                    
                else:
                    # Not a valid Rev STRAT reversal pattern
                    self.logger.debug(f"Rev STRAT pattern rejected: No clear reversal found")
                    return None
                    
            else:
                # Cannot analyze first bar - insufficient data
                return None
            
            # Calculate confidence based on pattern strength
            confidence = self._calculate_212_confidence(bar1, bar2, bar3, direction)
            
            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(target_price - entry_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Create signal
            signal = STRATSignal(
                symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                pattern=PatternType.TWO_ONE_TWO,
                direction=direction,
                confidence=confidence,
                entry_price=entry_price,
                trigger_price=trigger_price,
                stop_loss=stop_loss,
                target_price=target_price,
                timestamp=df.index[trigger_index],
                bar_sequence=[2, 1, 2],
                trigger_bar_index=trigger_index,
                risk_reward_ratio=risk_reward_ratio,
                notes=f"2-1-2 {direction.value} breakout pattern"
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing 2-1-2 signal: {e}")
            return None
    
    def _analyze_312_signal(self, df: pd.DataFrame, trigger_index: int, strat_classes: pd.Series) -> Optional[STRATSignal]:
        """Analyze a potential 3-1-2 signal for validity and strength"""
        
        try:
            # Get the three bars in the pattern: 3-1-2 (Outside-Inside-Directional)
            bar1_idx = trigger_index - 2  # Outside bar (3) - setup bar
            bar2_idx = trigger_index - 1  # Inside bar (1) - consolidation
            bar3_idx = trigger_index      # Directional bar (2) - trigger/entry
            
            bar1 = df.iloc[bar1_idx]  # Outside bar
            bar2 = df.iloc[bar2_idx]  # Inside bar  
            bar3 = df.iloc[bar3_idx]  # Directional bar
            
            # For 3-1-2 reversal, determine direction based on which side 
            # the directional bar (bar3) breaks out of the inside bar (bar2)
            if bar3['high'] > bar2['high'] and bar3['low'] >= bar2['low']:
                # Bullish breakout: directional bar breaks above inside bar (2U)
                direction = Direction.BULLISH
                trigger_price = bar2['high']  # STRAT trigger level (inside bar high)
                entry_price = bar3['open']    # Actual execution price on breakout bar
                stop_loss = bar1['low']       # Outside bar low (pattern support)
                # Measured move: use the outside bar's range
                pattern_height = bar1['high'] - bar1['low']
                target_price = trigger_price + pattern_height
                
            elif bar3['low'] < bar2['low'] and bar3['high'] <= bar2['high']:
                # Bearish breakout: directional bar breaks below inside bar (2D)
                direction = Direction.BEARISH  
                trigger_price = bar2['low']   # STRAT trigger level (inside bar low)
                entry_price = bar3['open']    # Actual execution price on breakout bar
                stop_loss = bar1['high']      # Outside bar high (pattern resistance)
                # Measured move: use the outside bar's range
                pattern_height = bar1['high'] - bar1['low']
                target_price = trigger_price - pattern_height
                
            else:
                # Directional bar doesn't properly break the inside bar
                return None
            
            # Calculate confidence based on pattern strength
            confidence = self._calculate_312_confidence(bar1, bar2, bar3, direction)
            
            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(target_price - entry_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Create signal
            signal = STRATSignal(
                symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                pattern=PatternType.THREE_ONE_TWO,
                direction=direction,
                confidence=confidence,
                entry_price=entry_price,
                trigger_price=trigger_price,
                stop_loss=stop_loss,
                target_price=target_price,
                timestamp=df.index[trigger_index],
                bar_sequence=[3, 1, 2],
                trigger_bar_index=trigger_index,
                risk_reward_ratio=risk_reward_ratio,
                notes=f"3-1-2 {direction.value} reversal pattern"
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing 3-1-2 signal: {e}")
            return None
    
    def _analyze_rev_strat_signal(self, df: pd.DataFrame, current_index: int, strat_classes: pd.Series) -> Optional[STRATSignal]:
        """
        Analyze potential Rev STRAT (failed breakout) pattern.
        
        CRITICAL: Proper 4-bar Rev STRAT structure implementation.
        Structure: [2|3]-1-2-2 (4 bars total)
        - Bar 1: MUST be Scenario 2 or 3 (NEVER Scenario 1) - setup bar
        - Bar 2: Inside bar (scenario 1)
        - Bar 3: Directional break that FAILS to reach target (failed breakout)
        - Bar 4: Reversal bar - ENTRY POINT
        """
        
        try:
            # Rev STRAT requires exactly 4 bars for proper analysis
            if current_index < 3:
                return None
            
            # Get the 4-bar sequence: [current_index-3] to [current_index]
            bar1_idx = current_index - 3  # Setup bar (must be Scenario 2 or 3)
            bar2_idx = current_index - 2  # Inside bar (must be Scenario 1) 
            bar3_idx = current_index - 1  # Failed breakout (Scenario 2)
            bar4_idx = current_index       # Reversal bar (Scenario 2) - ENTRY
            
            # Get bar data and classifications
            bar1 = df.iloc[bar1_idx]
            bar2 = df.iloc[bar2_idx] 
            bar3 = df.iloc[bar3_idx]
            bar4 = df.iloc[bar4_idx]
            
            class1 = strat_classes.iloc[bar1_idx]
            class2 = strat_classes.iloc[bar2_idx]
            class3 = strat_classes.iloc[bar3_idx]
            class4 = strat_classes.iloc[bar4_idx]
            
            # CRITICAL CHECK: Bar 1 MUST be Scenario 2 or 3 (NEVER Scenario 1)
            if class1 == 1:
                # REJECT: Rev STRAT cannot start with inside bar
                self.logger.debug(f"REJECTED Rev STRAT: Pattern starts with Scenario 1 (inside bar) - NOT valid Rev STRAT")
                return None
            
            # Validate proper Rev STRAT structure: [2|3]-1-2-2 (with corrected classifications)
            # class1 = 2 or 3 (Directional or Outside), class2 = 1 (Inside), class3 = 2 (Directional), class4 = 2 (Directional)
            if not (class1 in [2, 3] and class2 == 1 and class3 == 2 and class4 == 2):
                self.logger.debug(f"Rev STRAT pattern rejected: Invalid structure {class1}-{class2}-{class3}-{class4}, expected [2|3]-1-2-2")
                return None
            
            # Determine breakout direction from Bar 3 vs Bar 1
            bar3_breaks_high = bar3['high'] > bar1['high']
            bar3_breaks_low = bar3['low'] < bar1['low']
            
            # Determine reversal direction from Bar 4 vs Bar 2
            bar4_breaks_high = bar4['high'] > bar2['high'] 
            bar4_breaks_low = bar4['low'] < bar2['low']
            
            signal = None
            
            # Bearish Rev STRAT: [2|3]-1-2U-2D (2U fails to reach target, enter on 2D)
            if bar3_breaks_high and bar4_breaks_low:
                # Check if Bar 3 broke out of Bar 2 but failed to reach Bar 1's high extreme
                # FIXED: Bar 3 must break above Bar 2 (inside bar) but fail to reach Bar 1's high
                broke_inside_bar = bar3['high'] > bar2['high']  # Bar 3 broke out of inside bar
                failed_target = bar3['high'] < bar1['high']     # But failed to reach Bar 1's high extreme
                failed_breakout = broke_inside_bar and failed_target

                if failed_breakout:
                    confidence = 0.95 if class1 == 3 else 0.85  # Higher confidence for Scenario 3 start
                    self.logger.debug(f"Valid Bearish Rev STRAT found: Bar 3 broke inside bar (${bar3['high']:.2f} > ${bar2['high']:.2f}) but failed target (${bar3['high']:.2f} < ${bar1['high']:.2f})")
                    
                    signal = STRATSignal(
                            symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                            timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                            pattern=PatternType.REV_STRAT,
                            direction=Direction.BEARISH,
                            confidence=confidence,
                            entry_price=bar3['low'] - 0.01,  # Enter when Bar 4 breaks below Bar 3 low (failed breakout bar)
                            trigger_price=bar3['low'],        # Failed breakout bar low trigger
                            stop_loss=bar3['high'],      # Failed breakout high
                            target_price=bar1['low'],    # First bar low in sequence
                            timestamp=df.index[current_index],
                            bar_sequence=[class1, class2, class3, class4],
                            trigger_bar_index=current_index,
                            risk_reward_ratio=0.0,  # Will be calculated in __post_init__
                            notes=f"Rev STRAT BEARISH: {class1}-1-2U-2D (Bar 1 = Scenario {class1})"
                    )
                    
                    self.logger.info(f"Valid Rev STRAT BEARISH detected: Pattern {class1}-1-2U-2D")
            
            # Bullish Rev STRAT: [2|3]-1-2D-2U (2D fails to reach target, enter on 2U)
            elif bar3_breaks_low and bar4_breaks_high:
                # Check if Bar 3 broke out of Bar 2 but failed to reach Bar 1's low extreme
                # FIXED: Bar 3 must break below Bar 2 (inside bar) but fail to reach Bar 1's low
                broke_inside_bar = bar3['low'] < bar2['low']    # Bar 3 broke out of inside bar
                failed_target = bar3['low'] > bar1['low']       # But failed to reach Bar 1's low extreme
                failed_breakout = broke_inside_bar and failed_target

                if failed_breakout:
                    confidence = 0.95 if class1 == 3 else 0.85  # Higher confidence for Scenario 3 start
                    self.logger.debug(f"Valid Bullish Rev STRAT found: Bar 3 broke inside bar (${bar3['low']:.2f} < ${bar2['low']:.2f}) but failed target (${bar3['low']:.2f} > ${bar1['low']:.2f})")
                    
                    signal = STRATSignal(
                        symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                        timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                        pattern=PatternType.REV_STRAT,
                        direction=Direction.BULLISH,
                        confidence=confidence,
                        entry_price=bar3['high'] + 0.01,  # Enter when Bar 4 breaks above Bar 3 high (failed breakdown bar)
                        trigger_price=bar3['high'],        # Failed breakdown bar high trigger
                        stop_loss=bar3['low'],        # Failed breakdown low
                        target_price=bar1['high'],    # First bar high in sequence
                        timestamp=df.index[current_index],
                        bar_sequence=[class1, class2, class3, class4],
                        trigger_bar_index=current_index,
                        risk_reward_ratio=0.0,  # Will be calculated in __post_init__
                        notes=f"Rev STRAT BULLISH: {class1}-1-2D-2U (Bar 1 = Scenario {class1})"
                    )
                    
                    self.logger.info(f"Valid Rev STRAT BULLISH detected: Pattern {class1}-1-2D-2U")
            
            # Calculate risk/reward ratio if signal was created
            if signal:
                risk = abs(signal.entry_price - signal.stop_loss)
                reward = abs(signal.target_price - signal.entry_price) 
                signal.risk_reward_ratio = reward / risk if risk > 0 else 0
                
                # Add Rev STRAT timeframe continuity validation
                continuity_valid = self._validate_rev_strat_continuity(signal, df, current_index)
                if not continuity_valid:
                    self.logger.debug(f"Rev STRAT rejected: timeframe continuity not restored after reversal")
                    return None
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing Rev STRAT signal: {e}")
            return None
    
    def _validate_rev_strat_continuity(self, signal: 'STRATSignal', df: pd.DataFrame, current_index: int) -> bool:
        """
        Validate timeframe continuity for Rev STRAT patterns.
        
        Per STRAT methodology:
        1. Before pattern: Full timeframe continuity in expected reversal direction
        2. During failed breakout: Accept temporary continuity break
        3. After reversal: Continuity must be restored in reversal direction
        
        Args:
            signal: The Rev STRAT signal to validate
            df: Price data 
            current_index: Index of Bar 4 (reversal bar)
            
        Returns:
            True if continuity is properly restored, False otherwise
        """
        try:
            # For Rev STRAT validation, we need to check if the reversal direction
            # aligns with the broader market structure
            
            # Simple implementation: Check if Bar 4 (reversal) is in same direction
            # as Bar 1 (original setup), which indicates continuity restoration
            bar1_idx = current_index - 3
            bar4_idx = current_index
            
            bar1 = df.iloc[bar1_idx]
            bar4 = df.iloc[bar4_idx]
            
            # Determine if Bar 1 and Bar 4 are in the same overall direction
            # This indicates that the failed breakout (Bar 3) was against the trend
            # and Bar 4 restores the original direction
            
            if signal.direction == Direction.BULLISH:
                # For bullish Rev STRAT, check if reversal restores upward bias
                continuity_restored = bar4['close'] > bar4['open']  # Green candle on reversal
            else:
                # For bearish Rev STRAT, check if reversal restores downward bias  
                continuity_restored = bar4['close'] < bar4['open']  # Red candle on reversal
            
            if continuity_restored:
                self.logger.debug(f"Rev STRAT continuity validated: {signal.direction} direction restored")
            
            return continuity_restored
            
        except Exception as e:
            self.logger.error(f"Error validating Rev STRAT continuity: {e}")
            return False  # Default to rejection on error
    
    def detect_322_pattern(self, df: pd.DataFrame, strat_classes: pd.Series) -> List[STRATSignal]:
        """
        Detect 3-2-2 patterns (strong trend continuation)
        
        3-2-2 Pattern (Rob Smith STRAT methodology):
        - Outside bar (3) creates initial range expansion
        - Directional bar (2) shows directional bias (2U or 2D)
        - Directional bar (2) continues trend with strong momentum
        
        Args:
            df: Price data
            strat_classes: Bar classifications
            
        Returns:
            List of 3-2-2 signals found
        """
        signals = []
        
        if len(strat_classes) < 3:
            return signals
        
        # Vectorized detection with proper directional logic
        class_values = strat_classes.values

        # Create sliding window for 3 consecutive bars
        bar_1 = class_values[:-2]   # First bar (must be 3)
        bar_2 = class_values[1:-1]  # Second bar (2U or 2D)
        bar_3 = class_values[2:]    # Third bar (2U or 2D)

        # Detect all 3-2-2 patterns with direction
        # Bullish patterns (3-2U-2U continuation or 3-2D-2U reversal)
        pattern_3_2u_2u = (bar_1 == 3) & (bar_2 == 2) & (bar_3 == 2)      # Bullish continuation
        pattern_3_2d_2u = (bar_1 == 3) & (bar_2 == -2) & (bar_3 == 2)     # Bullish reversal

        # Bearish patterns (3-2D-2D continuation or 3-2U-2D reversal)
        pattern_3_2d_2d = (bar_1 == 3) & (bar_2 == -2) & (bar_3 == -2)    # Bearish continuation
        pattern_3_2u_2d = (bar_1 == 3) & (bar_2 == 2) & (bar_3 == -2)      # Bearish reversal

        # Find all pattern indices
        bull_cont_indices = np.where(pattern_3_2u_2u)[0] + 2
        bull_rev_indices = np.where(pattern_3_2d_2u)[0] + 2
        bear_cont_indices = np.where(pattern_3_2d_2d)[0] + 2
        bear_rev_indices = np.where(pattern_3_2u_2d)[0] + 2

        # Process all patterns
        for i in bull_cont_indices:
            signal = self._analyze_322_signal(df, i, strat_classes)
            if signal and not self._is_duplicate_pattern(signal):
                signals.append(signal)

        for i in bull_rev_indices:
            signal = self._analyze_322_signal(df, i, strat_classes)
            if signal and not self._is_duplicate_pattern(signal):
                signals.append(signal)

        for i in bear_cont_indices:
            signal = self._analyze_322_signal(df, i, strat_classes)
            if signal and not self._is_duplicate_pattern(signal):
                signals.append(signal)

        for i in bear_rev_indices:
            signal = self._analyze_322_signal(df, i, strat_classes)
            if signal and not self._is_duplicate_pattern(signal):
                signals.append(signal)
        
        self.logger.debug(f"Found {len(signals)} 3-2-2 patterns")
        return signals

    def detect_32_pattern(self, df: pd.DataFrame, strat_classes: pd.Series) -> List[STRATSignal]:
        """
        Detect simple 3-2 patterns (immediate breakout from outside bar)

        3-2 Pattern:
        - Outside bar (3) creates range expansion
        - Directional bar (2U or 2D) breaks immediately

        Args:
            df: Price data
            strat_classes: Bar classifications (1, 2, -2, 3)

        Returns:
            List of 3-2 signals found with proper directions
        """
        signals = []

        if len(strat_classes) < 2:
            return signals

        # Vectorized detection of 3-2 patterns
        class_values = strat_classes.values

        # Create sliding window for 2 consecutive bars
        bar_1 = class_values[:-1]  # First bar (must be 3)
        bar_2 = class_values[1:]   # Second bar (2U or 2D)

        # Detect 3-2 patterns with direction
        pattern_3_2u = (bar_1 == 3) & (bar_2 == 2)    # Bullish breakout
        pattern_3_2d = (bar_1 == 3) & (bar_2 == -2)   # Bearish breakout

        # Find pattern indices
        bullish_indices = np.where(pattern_3_2u)[0] + 1
        bearish_indices = np.where(pattern_3_2d)[0] + 1

        # Process bullish 3-2U patterns
        for i in bullish_indices:
            bar1 = df.iloc[i-1]
            bar2 = df.iloc[i]

            signal = STRATSignal(
                symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                pattern=PatternType.THREE_ONE_TWO,  # Using existing pattern type
                direction=Direction.BULLISH,
                confidence=0.85,  # High confidence for immediate breakout
                entry_price=bar2['open'],
                stop_loss=bar1['low'],
                target_price=bar2['high'] + (bar1['high'] - bar1['low']),
                trigger_price=bar1['high'],
                timestamp=df.index[i] if hasattr(df, 'index') else i,
                bar_sequence=[3, 2],
                trigger_bar_index=i,
                risk_reward_ratio=0.0,
                notes="3-2U Bullish Breakout"
            )

            # Calculate risk/reward
            risk = abs(signal.entry_price - signal.stop_loss)
            reward = abs(signal.target_price - signal.entry_price)
            signal.risk_reward_ratio = reward / risk if risk > 0 else 0

            if not self._is_duplicate_pattern(signal):
                signals.append(signal)

        # Process bearish 3-2D patterns
        for i in bearish_indices:
            bar1 = df.iloc[i-1]
            bar2 = df.iloc[i]

            signal = STRATSignal(
                symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                pattern=PatternType.THREE_ONE_TWO,  # Using existing pattern type
                direction=Direction.BEARISH,
                confidence=0.85,  # High confidence for immediate breakout
                entry_price=bar2['open'],
                stop_loss=bar1['high'],
                target_price=bar2['low'] - (bar1['high'] - bar1['low']),
                trigger_price=bar1['low'],
                timestamp=df.index[i] if hasattr(df, 'index') else i,
                bar_sequence=[3, -2],
                trigger_bar_index=i,
                risk_reward_ratio=0.0,
                notes="3-2D Bearish Breakout"
            )

            # Calculate risk/reward
            risk = abs(signal.entry_price - signal.stop_loss)
            reward = abs(signal.target_price - signal.entry_price)
            signal.risk_reward_ratio = reward / risk if risk > 0 else 0

            if not self._is_duplicate_pattern(signal):
                signals.append(signal)

        self.logger.debug(f"Found {len(signals)} 3-2 patterns")
        return signals

    def detect_22_reversal_pattern(self, df: pd.DataFrame, strat_classes: pd.Series) -> List[STRATSignal]:
        """
        Detect simple 2-2 reversal patterns (directional reversal)
        
        2-2 Reversal Pattern:
        - Directional bar (2) in one direction (2U or 2D)
        - Directional bar (2) reverses to opposite direction
        - 2U→2D = Bearish reversal
        - 2D→2U = Bullish reversal
        
        Args:
            df: Price data
            strat_classes: Bar classifications
            
        Returns:
            List of 2-2 reversal signals found
        """
        signals = []
        
        if len(strat_classes) < 2:
            return signals
        
        # Vectorized detection of 2-2 reversals using proper directional classification
        class_values = strat_classes.values

        # Create sliding window for 2 consecutive bars
        bar_1 = class_values[:-1]  # First bar
        bar_2 = class_values[1:]   # Second bar

        # Detect 2-2 reversal patterns with direction
        pattern_2u_2d = (bar_1 == 2) & (bar_2 == -2)    # Bearish reversal
        pattern_2d_2u = (bar_1 == -2) & (bar_2 == 2)    # Bullish reversal

        # Find pattern indices
        bearish_rev_indices = np.where(pattern_2u_2d)[0] + 1
        bullish_rev_indices = np.where(pattern_2d_2u)[0] + 1

        # Process bearish reversals (2U→2D)
        for i in bearish_rev_indices:
            bar1 = df.iloc[i-1]
            bar2 = df.iloc[i]

            # Check for reversal patterns
            if True:  # Pattern already confirmed by classification
                        # Bearish reversal: 2U→2D
                        signal = STRATSignal(
                            symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                            timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                            pattern=PatternType.TWO_TWO_REVERSAL,
                            direction=Direction.BEARISH,
                            confidence=self.pattern_weights[PatternType.TWO_TWO_REVERSAL],
                            entry_price=bar2['open'],
                            stop_loss=bar1['high'],
                            target_price=bar2['low'] - (bar1['high'] - bar1['low']),
                            trigger_price=bar1['low'],
                            timestamp=df.index[i] if hasattr(df, 'index') else i,
                            bar_sequence=[2, -2],
                            trigger_bar_index=i,
                            risk_reward_ratio=0.0,
                            notes="2-2 Bearish Reversal: 2U→2D"
                        )
                        
                        # Calculate risk/reward
                        risk = abs(signal.entry_price - signal.stop_loss)
                        reward = abs(signal.target_price - signal.entry_price)
                        signal.risk_reward_ratio = reward / risk if risk > 0 else 0
                        
                        if not self._is_duplicate_pattern(signal):
                            signals.append(signal)
                            self.logger.debug(f"2-2 Bearish Reversal detected at {df.index[i]}")
                    

        # Process bullish reversals (2D→2U)
        for i in bullish_rev_indices:
            bar1 = df.iloc[i-1]
            bar2 = df.iloc[i]

            # Pattern already confirmed by classification
            signal = STRATSignal(
                symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                pattern=PatternType.TWO_TWO_REVERSAL,
                direction=Direction.BULLISH,
                confidence=self.pattern_weights[PatternType.TWO_TWO_REVERSAL],
                entry_price=bar2['open'],
                stop_loss=bar1['low'],
                target_price=bar2['high'] + (bar1['high'] - bar1['low']),
                trigger_price=bar1['high'],
                timestamp=df.index[i] if hasattr(df, 'index') else i,
                bar_sequence=[-2, 2],
                trigger_bar_index=i,
                risk_reward_ratio=0.0,
                notes="2-2 Bullish Reversal: 2D→2U"
            )

            # Calculate risk/reward
            risk = abs(signal.entry_price - signal.stop_loss)
            reward = abs(signal.target_price - signal.entry_price)
            signal.risk_reward_ratio = reward / risk if risk > 0 else 0

            if not self._is_duplicate_pattern(signal):
                signals.append(signal)
                self.logger.debug(f"2-2 Bullish Reversal detected at {df.index[i]}")
        
        self.logger.debug(f"Found {len(signals)} 2-2 reversal patterns")
        return signals
    
    def detect_22_continuation_pattern(self, df: pd.DataFrame, strat_classes: pd.Series) -> List[STRATSignal]:
        """
        Detect simple 2-2 continuation patterns (trend continuation)
        
        2-2 Continuation Pattern:
        - Directional bar (2) in one direction (2U or 2D)
        - Directional bar (2) continues in same direction
        - 2U→2U = Bullish continuation
        - 2D→2D = Bearish continuation
        
        Args:
            df: Price data
            strat_classes: Bar classifications
            
        Returns:
            List of 2-2 continuation signals found
        """
        signals = []
        
        if len(strat_classes) < 2:
            return signals
        
        # Look for consecutive 2-2 patterns
        for i in range(1, len(strat_classes)):
            if strat_classes.iloc[i-1] == 2 and strat_classes.iloc[i] == 2:
                # Two consecutive directional bars - check if they continue
                bar1 = df.iloc[i-1]
                bar2 = df.iloc[i]
                
                if i > 1:
                    bar0 = df.iloc[i-2]  # Reference bar
                    
                    # Determine direction of each directional bar
                    bar1_up = bar1['high'] > bar0['high'] and bar1['low'] >= bar0['low']
                    bar1_down = bar1['low'] < bar0['low'] and bar1['high'] <= bar0['high']
                    
                    bar2_up = bar2['high'] > bar1['high'] and bar2['low'] >= bar1['low']
                    bar2_down = bar2['low'] < bar1['low'] and bar2['high'] <= bar1['high']
                    
                    # Check for continuation patterns
                    if bar1_up and bar2_up:
                        # Bullish continuation: 2U→2U
                        signal = STRATSignal(
                            symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                            timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                            pattern=PatternType.TWO_TWO_CONTINUATION,
                            direction=Direction.BULLISH,
                            confidence=self.pattern_weights[PatternType.TWO_TWO_CONTINUATION],
                            entry_price=bar2['open'],
                            stop_loss=min(bar1['low'], bar2['low']),
                            target_price=bar2['high'] + (bar2['high'] - bar1['low']),
                            trigger_price=bar2['high'],
                            timestamp=df.index[i] if hasattr(df, 'index') else i,
                            bar_sequence=[2, 2],
                            trigger_bar_index=i,
                            risk_reward_ratio=0.0,
                            notes="2-2 Bullish Continuation: 2U→2U"
                        )
                        
                        # Calculate risk/reward
                        risk = abs(signal.entry_price - signal.stop_loss)
                        reward = abs(signal.target_price - signal.entry_price)
                        signal.risk_reward_ratio = reward / risk if risk > 0 else 0
                        
                        if not self._is_duplicate_pattern(signal):
                            signals.append(signal)
                            self.logger.debug(f"2-2 Bullish Continuation detected at {df.index[i]}")
                    
                    elif bar1_down and bar2_down:
                        # Bearish continuation: 2D→2D
                        signal = STRATSignal(
                            symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                            timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                            pattern=PatternType.TWO_TWO_CONTINUATION,
                            direction=Direction.BEARISH,
                            confidence=self.pattern_weights[PatternType.TWO_TWO_CONTINUATION],
                            entry_price=bar2['open'],
                            stop_loss=max(bar1['high'], bar2['high']),
                            target_price=bar2['low'] - (bar1['high'] - bar2['low']),
                            trigger_price=bar2['low'],
                            timestamp=df.index[i] if hasattr(df, 'index') else i,
                            bar_sequence=[2, 2],
                            trigger_bar_index=i,
                            risk_reward_ratio=0.0,
                            notes="2-2 Bearish Continuation: 2D→2D"
                        )
                        
                        # Calculate risk/reward
                        risk = abs(signal.entry_price - signal.stop_loss)
                        reward = abs(signal.target_price - signal.entry_price)
                        signal.risk_reward_ratio = reward / risk if risk > 0 else 0
                        
                        if not self._is_duplicate_pattern(signal):
                            signals.append(signal)
                            self.logger.debug(f"2-2 Bearish Continuation detected at {df.index[i]}")
        
        self.logger.debug(f"Found {len(signals)} 2-2 continuation patterns")
        return signals
    
    def detect_212_reversal_pattern(self, df: pd.DataFrame, strat_classes: pd.Series) -> List[STRATSignal]:
        """
        Detect 2-1-2 reversal patterns (reversal variant of continuation pattern)
        
        2-1-2 Reversal Pattern:
        - Directional bar (2) in one direction
        - Inside bar (1) consolidation
        - Directional bar (2) reverses the initial direction
        
        Args:
            df: Price data
            strat_classes: Bar classifications
            
        Returns:
            List of 2-1-2 reversal signals found
        """
        signals = []
        
        if len(strat_classes) < 3:
            return signals
        
        # Look for 2-1-2 sequences that reverse direction
        for i in range(2, len(strat_classes)):
            sequence = strat_classes.iloc[i-2:i+1].tolist()
            
            if sequence == [2, 1, 2]:
                # Check if this is a reversal (not continuation)
                signal = self._analyze_212_reversal_signal(df, i, strat_classes)
                if signal and not self._is_duplicate_pattern(signal):
                    signals.append(signal)
        
        self.logger.debug(f"Found {len(signals)} 2-1-2 reversal patterns")
        return signals
    
    def detect_ftfc_combo_pattern(self, df: pd.DataFrame, strat_classes: pd.Series) -> List[STRATSignal]:
        """
        Detect FTFC combination patterns (multi-timeframe alignment)
        
        FTFC Combo Pattern:
        - Requires FTC analyzer integration
        - Multiple timeframes showing same directional bias
        - Enhanced confidence through timeframe alignment
        
        Args:
            df: Price data
            strat_classes: Bar classifications
            
        Returns:
            List of FTFC combo signals found
        """
        signals = []
        
        if not self.enable_ftfc or not self.ftc_analyzer:
            self.logger.debug("FTFC not available - skipping combo patterns")
            return signals
        
        # FTFC combo patterns require FTC analysis integration
        # This would be implemented when FTC analyzer is fully available
        self.logger.debug("FTFC combo pattern detection - integration pending")
        return signals
    
    def _analyze_322_signal(self, df: pd.DataFrame, trigger_index: int, strat_classes: pd.Series) -> Optional[STRATSignal]:
        """Analyze a potential 3-2-2 signal for validity and strength"""
        
        try:
            # Get the three bars: 3-2-2 (Outside-Directional-Directional)
            bar1_idx = trigger_index - 2  # Outside bar (3) - setup
            bar2_idx = trigger_index - 1  # First directional bar (2)
            bar3_idx = trigger_index      # Second directional bar (2) - trigger
            
            bar1 = df.iloc[bar1_idx]  # Outside bar
            bar2 = df.iloc[bar2_idx]  # First directional
            bar3 = df.iloc[bar3_idx]  # Second directional (trigger)
            
            # Check that directional bars continue in same direction
            bar2_up = bar2['high'] > bar1['high'] and bar2['low'] >= bar1['low']
            bar2_down = bar2['low'] < bar1['low'] and bar2['high'] <= bar1['high']
            
            if bar2_up and bar3['high'] > bar2['high'] and bar3['low'] >= bar2['low']:
                # Bullish 3-2U-2U pattern
                direction = Direction.BULLISH
                trigger_price = bar3['high']  # STRAT trigger level
                entry_price = bar3['open']    # Actual execution price
                stop_loss = bar1['low']       # Outside bar low
                pattern_height = bar1['high'] - bar1['low']
                target_price = trigger_price + (pattern_height * 1.5)  # Extended target for strong trend
                
            elif bar2_down and bar3['low'] < bar2['low'] and bar3['high'] <= bar2['high']:
                # Bearish 3-2D-2D pattern
                direction = Direction.BEARISH
                trigger_price = bar3['low']   # STRAT trigger level
                entry_price = bar3['open']    # Actual execution price
                stop_loss = bar1['high']      # Outside bar high
                pattern_height = bar1['high'] - bar1['low']
                target_price = trigger_price - (pattern_height * 1.5)  # Extended target for strong trend
                
            else:
                # Not a valid 3-2-2 continuation
                return None
            
            # High confidence for strong trend patterns
            confidence = self.pattern_weights[PatternType.THREE_TWO_TWO]
            
            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(target_price - entry_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            signal = STRATSignal(
                symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                pattern=PatternType.THREE_TWO_TWO,
                direction=direction,
                confidence=confidence,
                entry_price=entry_price,
                trigger_price=trigger_price,
                stop_loss=stop_loss,
                target_price=target_price,
                timestamp=df.index[trigger_index],
                bar_sequence=[3, 2, 2],
                trigger_bar_index=trigger_index,
                risk_reward_ratio=risk_reward_ratio,
                notes=f"3-2-2 {direction.value} strong trend continuation"
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing 3-2-2 signal: {e}")
            return None
    
    def _analyze_212_reversal_signal(self, df: pd.DataFrame, trigger_index: int, strat_classes: pd.Series) -> Optional[STRATSignal]:
        """Analyze a potential 2-1-2 reversal signal"""
        
        try:
            # Similar to 2-1-2 but check for direction reversal
            bar1_idx = trigger_index - 2  # First directional bar (2)
            bar2_idx = trigger_index - 1  # Inside bar (1)  
            bar3_idx = trigger_index      # Second directional bar (2) - trigger
            
            if bar1_idx <= 0:
                return None
                
            bar0 = df.iloc[bar1_idx - 1]  # Bar before pattern
            bar1 = df.iloc[bar1_idx]      # First directional
            bar2 = df.iloc[bar2_idx]      # Inside bar
            bar3 = df.iloc[bar3_idx]      # Second directional
            
            # Check first directional bar's direction
            bar1_up = bar1['high'] > bar0['high'] and bar1['low'] >= bar0['low']
            bar1_down = bar1['low'] < bar0['low'] and bar1['high'] <= bar0['high']
            
            # Check if trigger bar reverses the initial direction
            if bar1_up and bar3['low'] < bar2['low']:
                # Reversal: was going up, now breaking down
                direction = Direction.BEARISH
                trigger_price = bar2['low']  # STRAT trigger level
                entry_price = bar3['open']   # Actual execution price
                stop_loss = bar1['high']
                target_price = trigger_price - (bar1['high'] - bar1['low'])
                
            elif bar1_down and bar3['high'] > bar2['high']:
                # Reversal: was going down, now breaking up
                direction = Direction.BULLISH
                trigger_price = bar2['high']  # STRAT trigger level
                entry_price = bar3['open']    # Actual execution price
                stop_loss = bar1['low']
                target_price = trigger_price + (bar1['high'] - bar1['low'])
                
            else:
                # Not a reversal pattern
                return None
            
            confidence = self.pattern_weights[PatternType.TWO_ONE_TWO_REVERSAL]
            
            # Calculate risk/reward ratio
            risk = abs(entry_price - stop_loss)
            reward = abs(target_price - entry_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            signal = STRATSignal(
                symbol=df.attrs.get('symbol', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                timeframe=df.attrs.get('timeframe', 'UNKNOWN') if hasattr(df, 'attrs') else 'UNKNOWN',
                pattern=PatternType.TWO_ONE_TWO_REVERSAL,
                direction=direction,
                confidence=confidence,
                entry_price=entry_price,
                trigger_price=trigger_price,
                stop_loss=stop_loss,
                target_price=target_price,
                timestamp=df.index[trigger_index],
                bar_sequence=[2, 1, 2],
                trigger_bar_index=trigger_index,
                risk_reward_ratio=risk_reward_ratio,
                notes=f"2-1-2 {direction.value} reversal pattern"
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error analyzing 2-1-2 reversal signal: {e}")
            return None
    
    def _calculate_212_confidence(self, bar1: pd.Series, bar2: pd.Series, bar3: pd.Series, direction: Direction) -> float:
        """Calculate confidence score for 2-1-2 pattern"""
        
        base_confidence = self.pattern_weights[PatternType.TWO_ONE_TWO]
        
        # Factors that increase confidence:
        # 1. Clear inside bar (well contained)
        # 2. Strong breakout on trigger bar
        # 3. Good volume (if available)
        # 4. Clear range definition
        
        confidence_adjustments = 0.0
        
        # Check inside bar quality (tighter = better)
        inside_range = bar2['high'] - bar2['low']
        outside_range = bar1['high'] - bar1['low']
        
        if outside_range > 0:
            inside_ratio = inside_range / outside_range
            if inside_ratio < 0.5:  # Inside bar is less than 50% of outside bar
                confidence_adjustments += 0.05
        
        # Check breakout strength
        if direction == Direction.BULLISH:
            breakout_strength = (bar3['high'] - bar1['high']) / (bar1['high'] - bar1['low'])
        else:
            breakout_strength = (bar1['low'] - bar3['low']) / (bar1['high'] - bar1['low'])
        
        if breakout_strength > 0.1:  # Strong breakout
            confidence_adjustments += 0.05
        
        # Volume confirmation (if available)
        if 'volume' in bar3.index and 'volume' in bar1.index:
            if bar3['volume'] > bar1['volume'] * 1.2:  # 20% higher volume
                confidence_adjustments += 0.03
        
        final_confidence = min(0.95, base_confidence + confidence_adjustments)
        return final_confidence
    
    def _calculate_312_confidence(self, bar1: pd.Series, bar2: pd.Series, bar3: pd.Series, direction: Direction) -> float:
        """Calculate confidence score for 3-1-2 pattern"""
        
        base_confidence = self.pattern_weights[PatternType.THREE_ONE_TWO]
        
        # 3-1-2 patterns are generally high confidence reversal signals
        confidence_adjustments = 0.0
        
        # Check inside bar containment
        inside_range = bar2['high'] - bar2['low']
        outside_range = bar3['high'] - bar3['low']
        
        if outside_range > 0:
            if inside_range / outside_range < 0.6:  # Well contained inside bar
                confidence_adjustments += 0.03
        
        # Volume analysis (if available)
        if 'volume' in bar3.index and 'volume' in bar1.index:
            if bar3['volume'] > bar1['volume'] * 1.1:  # Increased volume on trigger
                confidence_adjustments += 0.02
        
        final_confidence = min(0.95, base_confidence + confidence_adjustments)
        return final_confidence
    
    def enhance_signal_with_ftfc(self, signal: STRATSignal) -> STRATSignal:
        """
        Enhance STRAT signal with Full Timeframe Continuity (FTFC) analysis.
        
        Args:
            signal: Original STRAT signal
            
        Returns:
            Enhanced signal with FTFC data
        """
        if not self.enable_ftfc or not self.ftc_analyzer:
            return signal
        
        try:
            # Get FTFC analysis for this symbol
            ftc_analysis = self.ftc_analyzer.analyze_ftc(signal.symbol, signal.timeframe)
            
            if ftc_analysis:
                # Update signal with FTFC data
                signal.ftfc_strength = ftc_analysis.ftc_strength
                signal.ftfc_direction = ftc_analysis.ftc_direction
                signal.supporting_timeframes = ftc_analysis.supporting_timeframes.copy()
                signal.conflicting_timeframes = ftc_analysis.conflicting_timeframes.copy()
                
                # Enhance confidence based on FTFC alignment
                signal.ftfc_enhanced_confidence = self._calculate_ftfc_enhanced_confidence(
                    signal.confidence, ftc_analysis, signal.direction
                )
                
                # Log FTFC enhancement
                direction_match = (
                    (signal.direction == Direction.BULLISH and ftc_analysis.ftc_direction == 'bullish') or
                    (signal.direction == Direction.BEARISH and ftc_analysis.ftc_direction == 'bearish')
                )
                
                self.logger.debug(f"[FTFC] Enhanced {signal.pattern.value} signal: "
                                f"strength={ftc_analysis.ftc_strength:.2%}, "
                                f"direction_match={direction_match}, "
                                f"confidence: {signal.confidence:.2%} → {signal.ftfc_enhanced_confidence:.2%}")
            
        except Exception as e:
            self.logger.warning(f"[FTFC] Failed to enhance signal: {e}")
        
        return signal
    
    def _calculate_ftfc_enhanced_confidence(self, base_confidence: float, ftc_analysis, signal_direction: Direction) -> float:
        """
        Calculate FTFC-enhanced confidence score.
        
        Rob Smith's FTFC methodology: Higher timeframe alignment significantly increases confidence.
        """
        # Start with base confidence
        enhanced_confidence = base_confidence
        
        # Check direction alignment
        signal_dir_str = 'bullish' if signal_direction == Direction.BULLISH else 'bearish'
        direction_aligned = (signal_dir_str == ftc_analysis.ftc_direction)
        
        if direction_aligned:
            # Boost confidence based on FTFC strength
            ftfc_boost = ftc_analysis.ftc_strength * 0.15  # Up to 15% boost
            enhanced_confidence += ftfc_boost
            
            # Extra boost for very strong FTFC
            if ftc_analysis.ftc_strength > 0.8:
                enhanced_confidence += 0.05  # Additional 5% for very strong alignment
                
        else:
            # Penalize for conflicting directions
            direction_penalty = ftc_analysis.ftc_strength * 0.20  # Up to 20% penalty
            enhanced_confidence -= direction_penalty
        
        # Additional adjustments based on supporting/conflicting timeframes
        supporting_count = len(ftc_analysis.supporting_timeframes)
        conflicting_count = len(ftc_analysis.conflicting_timeframes)
        
        if supporting_count > conflicting_count:
            enhanced_confidence += 0.03  # Small boost for more supporting timeframes
        elif conflicting_count > supporting_count:
            enhanced_confidence -= 0.03  # Small penalty for more conflicts
        
        # Cap the enhanced confidence
        return max(0.1, min(0.95, enhanced_confidence))
    
    def analyze_symbol(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Dict[str, List[STRATSignal]]:
        """
        Complete STRAT analysis for a symbol
        
        Args:
            df: OHLCV data
            symbol: Trading symbol
            timeframe: Timeframe string
            
        Returns:
            Dictionary with pattern types as keys and signal lists as values
        """
        
        if len(df) < self.min_bars_required:
            self.logger.warning(f"Insufficient data for {symbol} {timeframe}: {len(df)} bars < {self.min_bars_required}")
            return {}
        
        # Add symbol and timeframe metadata to DataFrame
        df.attrs['symbol'] = symbol
        df.attrs['timeframe'] = timeframe
        
        # Classify all bars using STRAT methodology
        strat_classes = self.classify_bars(df)
        
        # Detect all pattern types with proper directional logic
        patterns = {
            'TWO_ONE_TWO': self.detect_212_pattern(df, strat_classes),
            'THREE_ONE_TWO': self.detect_312_pattern(df, strat_classes),
            'THREE_TWO': self.detect_32_pattern(df, strat_classes),  # NEW: 3-2 patterns
            'THREE_TWO_TWO': self.detect_322_pattern(df, strat_classes),
            'TWO_TWO_REVERSAL': self.detect_22_reversal_pattern(df, strat_classes),
            'TWO_TWO_CONTINUATION': self.detect_22_continuation_pattern(df, strat_classes),
            'REV_STRAT': self.detect_rev_strat_pattern(df, strat_classes),
            'TWO_ONE_TWO_REVERSAL': self.detect_212_reversal_pattern(df, strat_classes),
            'FTFC_COMBO': self.detect_ftfc_combo_pattern(df, strat_classes)
            # Note: BROADENING_FORMATION would be added here when implemented
        }
        
        # Enhance signals with FTFC analysis if enabled
        if self.enable_ftfc:
            enhanced_patterns = {}
            for pattern_type, signals in patterns.items():
                enhanced_signals = []
                for signal in signals:
                    enhanced_signal = self.enhance_signal_with_ftfc(signal)
                    enhanced_signals.append(enhanced_signal)
                enhanced_patterns[pattern_type] = enhanced_signals
            patterns = enhanced_patterns
        
        # Count total signals found
        total_signals = sum(len(signals) for signals in patterns.values())
        
        # Calculate FTFC statistics if available
        ftfc_stats = ""
        if self.enable_ftfc and total_signals > 0:
            ftfc_enhanced_count = 0
            avg_ftfc_strength = 0
            
            for signals in patterns.values():
                for signal in signals:
                    if signal.ftfc_enhanced_confidence is not None:
                        ftfc_enhanced_count += 1
                        avg_ftfc_strength += signal.ftfc_strength or 0
            
            if ftfc_enhanced_count > 0:
                avg_ftfc_strength /= ftfc_enhanced_count
                ftfc_stats = f", FTFC enhanced: {ftfc_enhanced_count}/{total_signals} (avg strength: {avg_ftfc_strength:.2%})"
        
        self.logger.info(f"[ANALYSIS] STRAT analysis complete for {symbol} {timeframe}: "
                        f"{total_signals} total signals found{ftfc_stats}")
        
        # Log pattern breakdown
        for pattern_type, signals in patterns.items():
            if signals:
                # Count FTFC enhanced signals for this pattern
                ftfc_count = sum(1 for s in signals if s.ftfc_enhanced_confidence is not None)
                ftfc_info = f" ({ftfc_count} FTFC enhanced)" if ftfc_count > 0 else ""
                self.logger.debug(f"  {pattern_type}: {len(signals)} signals{ftfc_info}")
        
        return patterns
    
    def analyze_patterns(self, df: pd.DataFrame, symbol: str = 'UNKNOWN', timeframe: str = '1H') -> Dict[str, any]:
        """
        Adapter method for backward compatibility with backtest engine.
        
        Converts analyze_symbol output to format expected by simple_backtest_engine.py
        
        Args:
            df: OHLCV data
            symbol: Trading symbol (defaults to 'UNKNOWN')
            timeframe: Timeframe string (defaults to '1H')
            
        Returns:
            Dictionary with 'patterns' key containing pattern analysis
        """
        try:
            # Use existing analyze_symbol method
            patterns_dict = self.analyze_symbol(df, symbol, timeframe)
            
            # Convert to expected format
            patterns_list = []
            for pattern_type, signals in patterns_dict.items():
                for signal in signals:
                    # Convert STRATSignal to dictionary format
                    pattern = {
                        'type': signal.pattern.value if hasattr(signal.pattern, 'value') else str(signal.pattern),
                        'confidence': signal.confidence,
                        'direction': signal.direction.value.lower() if hasattr(signal.direction, 'value') else str(signal.direction).lower(),
                        'bars': signal.bar_sequence,
                        'entry_price': signal.entry_price,
                        'trigger_price': signal.trigger_price,  # CRITICAL: Include trigger price for trade execution
                        'stop_loss': signal.stop_loss,
                        'target_price': signal.target_price,
                        'timestamp': signal.timestamp.isoformat() if hasattr(signal.timestamp, 'isoformat') else str(signal.timestamp),
                        'risk_reward_ratio': signal.risk_reward_ratio,
                        'notes': signal.notes
                    }
                    patterns_list.append(pattern)
            
            return {
                'patterns': patterns_list,
                'symbol': symbol,
                'timeframe': timeframe,
                'total_patterns': len(patterns_list),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Pattern analysis adapter failed for {symbol}: {e}")
            return {
                'patterns': [],
                'symbol': symbol,
                'timeframe': timeframe,
                'total_patterns': 0,
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }

def test_strat_analyzer():
    """Test the STRAT analyzer with sample data"""
    
    print("[TEST] Testing STRAT Analyzer")
    print("=" * 40)
    
    # Create sample OHLCV data for testing
    dates = pd.date_range('2025-07-01', periods=30, freq='D')
    
    # Create realistic price data with some patterns
    np.random.seed(42)  # For reproducible results
    base_price = 100
    prices = []
    
    for i in range(30):
        if i == 0:
            open_price = base_price
        else:
            open_price = prices[-1]['close']
        
        # Add some volatility
        daily_range = np.random.uniform(0.5, 3.0)
        direction = np.random.choice([-1, 1])
        
        high = open_price + daily_range
        low = open_price - daily_range
        close = open_price + (direction * np.random.uniform(0, daily_range))
        
        # Ensure OHLC relationships are valid
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        prices.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': int(np.random.uniform(10000, 100000))
        })
    
    # Create DataFrame
    df = pd.DataFrame(prices, index=dates)
    
    print(f"[DATA] Created sample data: {len(df)} bars")
    print(f"[PRICE] Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    # Test STRAT analyzer
    analyzer = STRATAnalyzer()
    
    # Classify bars
    strat_classes = analyzer.classify_bars(df)
    print(f"[CLASSES] Bar classifications: "
          f"{np.sum(strat_classes == 1)} inside, "
          f"{np.sum(strat_classes == 2)} outside, "
          f"{np.sum(strat_classes == 3)} directional")
    
    # Full analysis
    patterns = analyzer.analyze_symbol(df, 'TEST', '1D')
    
    # Display results
    total_signals = sum(len(signals) for signals in patterns.values())
    print(f"[SIGNALS] Found {total_signals} total STRAT signals:")
    
    for pattern_type, signals in patterns.items():
        print(f"  {pattern_type}: {len(signals)} signals")
        
        # Show details of first signal in each category
        if signals:
            signal = signals[0]
            print(f"    Example: {signal.direction.value} at ${signal.entry_price:.2f}, "
                  f"confidence: {signal.confidence:.2%}")
    
    print("\n[SUCCESS] STRAT Analyzer test complete!")
    return analyzer, df, patterns

if __name__ == "__main__":
    test_strat_analyzer()
