# STRAT Algorithmic Trading System

A professional algorithmic trading system implementing the STRAT methodology for pattern-based market analysis and automated trade execution.

## Overview

This system provides a complete implementation of the STRAT trading methodology, integrating pattern detection, multi-timeframe analysis, and backtesting capabilities using VectorBT Pro and Alpaca Markets data.

### Key Features

- **STRAT Pattern Detection**: Automated identification of 2-1-2, 3-1-2, 2-2 reversals, and Rev STRAT patterns
- **Bar Classification**: Accurate classification of price action into inside bars (1), directional bars (2U/2D), and outside bars (3)
- **Multi-Timeframe Analysis**: Full Time Frame Continuity (TFC) scoring across hourly, daily, weekly, and monthly timeframes
- **Market Hours Filtering**: Strict NYSE regular trading hours filtering with holiday calendar integration
- **Backtesting Engine**: Integration with VectorBT Pro for high-performance strategy validation
- **Real-Time Data**: Alpaca Markets API integration for historical and live market data

## System Architecture

### Core Components

**core/analyzer.py**
- STRATAnalyzer class for bar classification and pattern detection
- Governing range tracking for consecutive inside bars
- Directional pattern identification with confidence scoring

**core/components.py**
- PivotDetector for key price level identification
- InsideBarTracker for multi-bar inside bar sequences
- PatternStateMachine for trade state management

**core/triggers.py**
- Intrabar trigger detection for precise entry timing
- Stop loss and target price calculation

### Data Management

**data/alpaca.py**
- Alpaca Markets API integration
- Historical OHLCV data fetching with adjustment handling
- Market hours validation and filtering

**data/mtf_manager.py**
- Multi-timeframe data resampling (5min, 15min, 1H, 1D, 1W, 1M)
- Market-aligned hourly bars (9:30 AM, 10:30 AM, etc.)
- Eastern timezone handling with DST support

### Trading Signals

**trading/strat_signals.py**
- Signal generation from detected patterns
- Entry, stop loss, and target price calculation
- Pattern confidence blending (TFC + analyzer)
- Exit logic for reversals and target achievement

## Dependencies

This project uses UV for dependency management and requires Python 3.12+.

### Core Dependencies
- **vectorbtpro**: High-performance backtesting and portfolio analytics
- **alpaca-py**: Alpaca Markets API client
- **pandas**: Data manipulation and analysis
- **pandas-market-calendars**: NYSE market hours and holiday calendar
- **numpy**: Numerical computing
- **python-dotenv**: Environment variable management

### Visualization & Analysis
- **matplotlib**: Chart generation
- **plotly**: Interactive visualizations
- **seaborn**: Statistical data visualization
- **dash**: Dashboard framework
- **streamlit**: Web application framework

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **ruff**: Fast Python linter
- **mypy**: Static type checking

## Project Structure

```
vectorbt-workspace/
├── core/               # STRAT methodology implementation
│   ├── analyzer.py     # Pattern detection and bar classification
│   ├── components.py   # Trading components
│   └── triggers.py     # Entry/exit trigger detection
├── data/               # Data management
│   ├── alpaca.py       # Market data fetching
│   └── mtf_manager.py  # Multi-timeframe manager
├── trading/            # Signal generation
│   └── strat_signals.py
├── tests/              # Test suite
│   ├── test_trading_signals.py
│   ├── test_basic_tfc.py
│   └── test_strat_components.py
├── docs/               # Documentation
│   ├── HANDOFF.md      # Current development status
│   └── CLAUDE.md       # Development guidelines
├── STRAT_Knowledge/    # STRAT methodology reference
└── config/             # Configuration files (.env)
```

## Current Status

### Validated Components

- Bar classification with governing range tracking
- Pattern detection (2-1-2, 3-1-2, 2-2 reversals)
- TFC continuity scoring (43.3% high-confidence alignment)
- NYSE market hours filtering (weekends and holidays)
- Multi-timeframe data resampling
- VectorBT Pro portfolio integration

### Technical Debt

**Priority 1: Stop/Target Price Calculation**
- Current implementation produces incorrect entry and target prices for 2-1-2 patterns
- Index calculation in `_validate_and_create_signal()` requires verification
- Affects trade performance and win rate accuracy

*Recommended Actions:*
1. Investigate `_validate_and_create_signal()` in trading/strat_signals.py (lines 437-572)
2. Verify analyzer methods `_analyze_212_signal()` and `_analyze_312_signal()` return correct price levels
3. Validate index calculations (idx, idx-1, idx-2) align with pattern bar positions
4. Test fixes against known patterns with manual OHLCV verification
5. Ensure entry = inside bar high + $0.01, stop = inside bar low, target = outer bar high/low

**Priority 2: Pattern Classification Refinement**
- Rev STRAT patterns (1-2-2) being misclassified as 2-2 reversals
- Pattern detection logic needs clarification on 3-bar sequences
- Impacts signal quality and trade expectation

*Recommended Actions:*
1. Review `detect_22_reversal_pattern()` logic in core/analyzer.py
2. Verify 3-bar sequences (1-2U-2D) are classified as Rev STRAT, not 2-2 reversals
3. Ensure 2-2 reversals only apply to consecutive directional bars (2U->2D or 2D->2U)
4. Add pattern validation tests for edge cases (inside bars preceding reversals)
5. Cross-reference pattern detection with STRAT methodology documentation

**Priority 3: Exit Logic Enhancement**
- Missing target price exit functionality
- Currently exits only on reversals or stop loss
- Prevents proper profit-taking at calculated targets

*Recommended Actions:*
1. Add target price tracking to signal generation
2. Implement exit condition when price reaches calculated target
3. Ensure VectorBT portfolio exits positions at target prices
4. Validate target exits occur before reversal stops when applicable
5. Test profit-taking behavior across multiple trade scenarios

**Priority 4: Performance Validation**
- Backtest results showing negative returns on uptrending stocks
- Requires systematic validation after bug fixes
- Need performance verification across multiple market conditions

*Recommended Actions:*
1. Re-run backtests after Priority 1-3 fixes are implemented
2. Test on volatile stocks (high pattern diversity) for comprehensive validation
3. Verify winning trades are properly captured (not marked as losses)
4. Compare backtest performance to buy-and-hold benchmark
5. Analyze trade-by-trade results for remaining edge cases

## Development Guidelines

### Market Hours Rule

All data must be filtered to NYSE regular trading hours before analysis:
- Weekdays only (Monday-Friday)
- NYSE holiday calendar filtering
- Prevents phantom bars on weekends/holidays
- Critical for accurate STRAT pattern detection

### Testing Philosophy

- Test with real market data (no synthetic data generation)
- Validate on volatile stocks for diverse pattern detection
- Performance metrics matter more than test pass rates
- Always verify output correctness, not just functionality

### Code Quality Standards

- Brutal honesty: acknowledge unknowns and uncertainties
- Read documentation before assuming method availability
- Prioritize simplicity over feature addition
- Delete redundant code rather than archiving
- Maintain fewer than 10 core files

## Future Development

### Planned Enhancements

1. **Additional Pattern Types**
   - PMG (Pivot Machine Gun) patterns
   - Broadening formations
   - Inside bar continuation patterns

2. **Live Trading Integration**
   - Alpaca paper trading connection
   - Real-time signal generation
   - Position management and monitoring

3. **Performance Optimization**
   - Vectorization of classification logic
   - Parallel processing for multi-symbol analysis
   - Memory optimization for large datasets

4. **Risk Management**
   - Position sizing algorithms
   - Portfolio-level risk controls
   - Drawdown management

## License

Private repository - All rights reserved

## References

STRAT methodology developed by Rob Smith. This implementation is an independent interpretation for educational and trading purposes.
