"""
Intrabar Trigger Detection System for STRAT Trading
Phase 3 Implementation - Priority 2

This module detects precise trigger points within bars:
- Uses 5-minute bars to find exact triggers within hourly patterns
- Detects when price crosses inside bar high/low (with tolerance)
- Tracks pattern state transitions in real-time
- Returns precise entry time, price, and direction for backtesting

Critical Understanding:
- Every bar starts as a "1" (inside) until price breaks a level
- Entry happens at EXACT moment when price crosses the trigger
- Example: 2U-1-? becomes 2U-1-2D at exact moment price hits inside_low - 0.01
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging

# Import our components
from data.mtf_manager import MarketAlignedMTFManager as MultiTimeFrameDataManager, TimeFrameData
from core.analyzer import STRATAnalyzer

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TriggerEvent:
    """Container for a trigger event"""
    timestamp: pd.Timestamp
    parent_timeframe: str  # The higher timeframe pattern (e.g., '1H')
    pattern: str  # Pattern type (e.g., '2U-1-2D')
    trigger_price: float
    trigger_direction: str  # 'long' or 'short'
    inside_bar_high: float
    inside_bar_low: float
    stop_level: float
    confidence: float  # TFC/FTFC confidence score
    base_bar_index: int  # Index in 5-minute data


class IntrabarTriggerDetector:
    """
    Detects precise intrabar triggers using granular timeframe data.

    This is critical for STRAT because entries happen at exact price levels,
    not at bar close. Uses 5-minute data to find triggers within hourly patterns.
    """

    def __init__(self,
                 mtf_manager: MultiTimeFrameDataManager,
                 trigger_tolerance: float = 0.01,
                 min_confidence: float = 0.50):
        """
        Initialize Intrabar Trigger Detector.

        Args:
            mtf_manager: Multi-timeframe data manager instance
            trigger_tolerance: Price tolerance for trigger detection (default $0.01)
            min_confidence: Minimum TFC confidence to consider (default 0.50)
        """
        self.mtf_manager = mtf_manager
        self.trigger_tolerance = trigger_tolerance
        self.min_confidence = min_confidence
        self.strat_analyzer = STRATAnalyzer(enable_ftfc=False)
        self.triggers: List[TriggerEvent] = []

        logger.info(f"Initialized Intrabar Trigger Detector with tolerance ${trigger_tolerance}")

    def detect_triggers_in_pattern(self,
                                  pattern_bar_idx: int,
                                  parent_timeframe: str = '1H',
                                  pattern_type: str = '2-1-2') -> List[TriggerEvent]:
        """
        Detect triggers within a specific pattern using base timeframe data.

        Args:
            pattern_bar_idx: Index of the pattern in parent timeframe
            parent_timeframe: Parent timeframe where pattern exists
            pattern_type: Type of pattern to analyze

        Returns:
            List of trigger events found
        """
        triggers = []

        # Get parent timeframe data
        parent_data = self.mtf_manager.get_timeframe(parent_timeframe)
        if parent_data is None or pattern_bar_idx >= len(parent_data.ohlcv):
            return triggers

        # Get base (5-minute) data
        base_data = self.mtf_manager.get_timeframe('5min')
        if base_data is None:
            return triggers

        # For a 2-1-2 pattern, we need to look at the middle bar (inside bar)
        if pattern_type in ['2-1-2', '3-1-2', '1-2-2']:
            # Get the inside bar from parent timeframe
            if pattern_bar_idx < 1:
                return triggers

            inside_bar = parent_data.ohlcv.iloc[pattern_bar_idx - 1]
            inside_high = inside_bar['High']
            inside_low = inside_bar['Low']
            inside_timestamp = parent_data.ohlcv.index[pattern_bar_idx - 1]

            # Get the current bar timestamp
            current_bar_timestamp = parent_data.ohlcv.index[pattern_bar_idx]

            # Find all 5-minute bars within the current parent bar
            base_bars_mask = (base_data.ohlcv.index >= current_bar_timestamp) & \
                           (base_data.ohlcv.index < current_bar_timestamp + pd.Timedelta(hours=1))
            base_bars = base_data.ohlcv[base_bars_mask]

            # Look for trigger points in the 5-minute data
            for i, (timestamp, bar) in enumerate(base_bars.iterrows()):
                # Check for upside break (long trigger)
                if bar['High'] >= inside_high + self.trigger_tolerance:
                    trigger = TriggerEvent(
                        timestamp=timestamp,
                        parent_timeframe=parent_timeframe,
                        pattern=f"{pattern_type}-UP",
                        trigger_price=inside_high + self.trigger_tolerance,
                        trigger_direction='long',
                        inside_bar_high=inside_high,
                        inside_bar_low=inside_low,
                        stop_level=inside_low,
                        confidence=0.0,  # Will be calculated separately
                        base_bar_index=base_bars_mask.nonzero()[0][i]
                    )
                    triggers.append(trigger)
                    break  # Only take first trigger

                # Check for downside break (short trigger)
                elif bar['Low'] <= inside_low - self.trigger_tolerance:
                    trigger = TriggerEvent(
                        timestamp=timestamp,
                        parent_timeframe=parent_timeframe,
                        pattern=f"{pattern_type}-DOWN",
                        trigger_price=inside_low - self.trigger_tolerance,
                        trigger_direction='short',
                        inside_bar_high=inside_high,
                        inside_bar_low=inside_low,
                        stop_level=inside_high,
                        confidence=0.0,  # Will be calculated separately
                        base_bar_index=base_bars_mask.nonzero()[0][i]
                    )
                    triggers.append(trigger)
                    break  # Only take first trigger

        return triggers

    def scan_for_all_triggers(self,
                             parent_timeframe: str = '1H',
                             patterns_to_scan: Optional[List[str]] = None) -> List[TriggerEvent]:
        """
        Scan entire dataset for all trigger events.

        Args:
            parent_timeframe: Timeframe to scan for patterns
            patterns_to_scan: List of pattern types to look for

        Returns:
            List of all trigger events found
        """
        if patterns_to_scan is None:
            patterns_to_scan = ['2-1-2', '3-1-2', '2-2-2', '3-2-2']

        all_triggers = []

        # Get parent timeframe data
        parent_data = self.mtf_manager.get_timeframe(parent_timeframe)
        if parent_data is None:
            logger.warning(f"No data available for {parent_timeframe}")
            return all_triggers

        # Classify bars in parent timeframe
        ohlcv_lower = parent_data.ohlcv.copy()
        ohlcv_lower.columns = [col.lower() for col in ohlcv_lower.columns]
        classifications = self.strat_analyzer.classify_bars(ohlcv_lower)

        # Scan for each pattern type
        for pattern_type in patterns_to_scan:
            pattern_indices = self._find_pattern_indices(classifications, pattern_type)

            for idx in pattern_indices:
                triggers = self.detect_triggers_in_pattern(idx, parent_timeframe, pattern_type)
                all_triggers.extend(triggers)

        # Sort by timestamp
        all_triggers.sort(key=lambda x: x.timestamp)

        self.triggers = all_triggers
        return all_triggers

    def _find_pattern_indices(self, classifications: pd.Series, pattern_type: str) -> List[int]:
        """
        Find indices where specific patterns occur.

        Args:
            classifications: Series of bar classifications
            pattern_type: Pattern to look for

        Returns:
            List of indices where pattern completes
        """
        indices = []

        if pattern_type == '2-1-2':
            # Look for 2U/2D followed by 1, then 2U/2D
            for i in range(2, len(classifications)):
                bar1 = classifications.iloc[i-2]
                bar2 = classifications.iloc[i-1]
                bar3 = classifications.iloc[i]

                if abs(bar1) == 2 and bar2 == 1 and abs(bar3) == 2:
                    indices.append(i)

        elif pattern_type == '3-1-2':
            # Look for 3 followed by 1, then 2U/2D
            for i in range(2, len(classifications)):
                bar1 = classifications.iloc[i-2]
                bar2 = classifications.iloc[i-1]
                bar3 = classifications.iloc[i]

                if bar1 == 3 and bar2 == 1 and abs(bar3) == 2:
                    indices.append(i)

        elif pattern_type == '2-2-2':
            # Look for three consecutive 2s
            for i in range(2, len(classifications)):
                bar1 = classifications.iloc[i-2]
                bar2 = classifications.iloc[i-1]
                bar3 = classifications.iloc[i]

                if abs(bar1) == 2 and abs(bar2) == 2 and abs(bar3) == 2:
                    indices.append(i)

        elif pattern_type == '3-2-2':
            # Look for 3 followed by two 2s
            for i in range(2, len(classifications)):
                bar1 = classifications.iloc[i-2]
                bar2 = classifications.iloc[i-1]
                bar3 = classifications.iloc[i]

                if bar1 == 3 and abs(bar2) == 2 and abs(bar3) == 2:
                    indices.append(i)

        return indices

    def get_trigger_summary(self) -> pd.DataFrame:
        """
        Get summary DataFrame of all detected triggers.

        Returns:
            DataFrame with trigger details
        """
        if not self.triggers:
            return pd.DataFrame()

        data = []
        for trigger in self.triggers:
            data.append({
                'timestamp': trigger.timestamp,
                'timeframe': trigger.parent_timeframe,
                'pattern': trigger.pattern,
                'direction': trigger.trigger_direction,
                'trigger_price': trigger.trigger_price,
                'stop_level': trigger.stop_level,
                'risk': abs(trigger.trigger_price - trigger.stop_level),
                'confidence': trigger.confidence
            })

        return pd.DataFrame(data)

    def backtest_trigger_accuracy(self,
                                 lookforward_bars: int = 20,
                                 base_timeframe: str = '5min') -> Dict[str, float]:
        """
        Backtest accuracy of detected triggers.

        Args:
            lookforward_bars: Number of bars to look forward after trigger
            base_timeframe: Timeframe to use for evaluation

        Returns:
            Dictionary of accuracy metrics
        """
        if not self.triggers:
            return {'accuracy': 0.0, 'total_triggers': 0}

        base_data = self.mtf_manager.get_timeframe(base_timeframe)
        if base_data is None:
            return {'accuracy': 0.0, 'total_triggers': 0}

        correct_triggers = 0
        total_triggers = len(self.triggers)

        for trigger in self.triggers:
            # Get bars after trigger
            start_idx = trigger.base_bar_index
            end_idx = min(start_idx + lookforward_bars, len(base_data.ohlcv))

            if end_idx <= start_idx:
                continue

            future_bars = base_data.ohlcv.iloc[start_idx:end_idx]

            if trigger.trigger_direction == 'long':
                # Check if price went up before hitting stop
                max_high = future_bars['High'].max()
                min_low = future_bars['Low'].min()

                if max_high > trigger.trigger_price * 1.01:  # 1% profit target
                    if min_low > trigger.stop_level:  # Didn't hit stop first
                        correct_triggers += 1

            else:  # short
                # Check if price went down before hitting stop
                max_high = future_bars['High'].max()
                min_low = future_bars['Low'].min()

                if min_low < trigger.trigger_price * 0.99:  # 1% profit target
                    if max_high < trigger.stop_level:  # Didn't hit stop first
                        correct_triggers += 1

        accuracy = correct_triggers / total_triggers if total_triggers > 0 else 0.0

        return {
            'accuracy': accuracy,
            'correct_triggers': correct_triggers,
            'total_triggers': total_triggers,
            'win_rate': accuracy * 100
        }


def test_intrabar_detector():
    """Test the Intrabar Trigger Detection System"""
    import os
    from dotenv import load_dotenv
    import vectorbtpro as vbt

    # Load environment
    load_dotenv('.env')

    # Setup Alpaca
    api_key = os.getenv('ALPACA_MID_KEY')
    secret_key = os.getenv('ALPACA_MID_SECRET')

    if not api_key or not secret_key:
        raise ValueError("Missing Alpaca credentials in .env")

    vbt.AlpacaData.set_custom_settings(
        client_config=dict(
            api_key=api_key,
            secret_key=secret_key,
            paper=True
        )
    )

    print("\n" + "=" * 60)
    print("TESTING INTRABAR TRIGGER DETECTION")
    print("=" * 60)

    # Create MTF manager and fetch data
    print("\n1. Setting up Multi-Timeframe Data...")
    mtf_manager = MultiTimeFrameDataManager(symbol="SPY", lookback_years=1)
    mtf_manager.fetch_and_resample(
        start_date="2024-08-01",
        end_date="2024-09-27"
    )

    # Create trigger detector
    print("\n2. Initializing Trigger Detector...")
    detector = IntrabarTriggerDetector(mtf_manager, trigger_tolerance=0.01)

    # Scan for triggers
    print("\n3. Scanning for trigger events...")
    triggers = detector.scan_for_all_triggers(parent_timeframe='1H')
    print(f"   Found {len(triggers)} trigger events")

    # Display summary
    if triggers:
        summary = detector.get_trigger_summary()
        print("\n4. Trigger Summary (first 10):")
        print(summary.head(10))

        # Backtest accuracy
        print("\n5. Backtesting trigger accuracy...")
        metrics = detector.backtest_trigger_accuracy(lookforward_bars=12)  # 1 hour forward
        print(f"   Win Rate: {metrics['win_rate']:.1f}%")
        print(f"   Correct: {metrics['correct_triggers']} / {metrics['total_triggers']}")

        # Pattern breakdown
        print("\n6. Triggers by Pattern:")
        pattern_counts = summary['pattern'].value_counts()
        for pattern, count in pattern_counts.items():
            print(f"   {pattern}: {count}")

    print("\n[COMPLETE] Intrabar Trigger Detection test complete")


if __name__ == "__main__":
    test_intrabar_detector()