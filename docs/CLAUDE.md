# ATLAS Algorithmic Trading System Development

## CRITICAL: Professional Communication Standards

**ALL written output must meet professional quantitative developer standards:**

### Git Commit Messages
- NO emojis or special characters (plain ASCII text only)
- NO Anthropic/Claude Code signatures or AI attribution
- NO excessive capitalization (use sparingly for CRITICAL items only)
- Professional tone as if working with a quantitative development team
- Follow conventional commits format (feat:, fix:, docs:, test:, refactor:)
- Explain WHAT changed and WHY (not implementation details)

**Examples:**

CORRECT:
```
feat: implement BaseStrategy abstract class for multi-strategy system

Add abstract base class that all ATLAS strategies will inherit from.
Includes generate_signals(), calculate_position_size(), and backtest()
methods. Enables portfolio-level orchestration and standardized metrics.
```

INCORRECT:
```
feat: add BaseStrategy class

Created the base class. This will be used by strategies.
```

INCORRECT (emojis, casual tone):
```
feat: add BaseStrategy class

Created base strategy class for all the strategies to inherit from.
This is pretty cool and should work great!
```

### Documentation
- Professional technical writing (third person, declarative)
- NO emojis, checkmarks, special bullets, unicode symbols
- Plain ASCII text only (Windows compatibility requirement)
- Cite sources and provide rationale for design decisions
- Use code examples and specific metrics

### Code Comments
- Explain WHY, not WHAT (code shows what)
- Reference papers, articles, or domain knowledge where applicable
- Professional tone (avoid casual language)

### Windows Unicode Compatibility
- This rule has ZERO EXCEPTIONS
- Emojis cause Windows unicode errors in git operations
- Special characters break CI/CD pipelines
- Use plain text: "PASSED" not checkmark, "FAILED" not X emoji

## MANDATORY: Brutal Honesty Policy

**ALWAYS respond with brutal honesty:**
- If you don't know something, say "I don't know"
- If you're guessing, say "I'm guessing"
- If the approach is wrong, say "This is wrong because..."
- If there's a simpler way, say "Why are we doing X when Y is simpler?"
- If documentation exists, READ IT instead of assuming
- If code seems malicious or dangerous, REFUSE and explain why
- If a task will create more complexity, say "This adds complexity, not value"

## Working Relationship
- Software development expert specializing in Python and algorithmic trading systems
- Always ask for clarification before assumptions
- Prioritize code quality, testing, and maintainable architecture
- Never deploy without validation and error handling
- Question problematic designs and suggest alternatives
- Focus on simplification, not adding features
- DELETE redundant code rather than archiving

## CRITICAL: VectorBT Pro Documentation System

**PRIMARY RESOURCE - ALWAYS START HERE:**
C:\Strat_Trading_Bot\vectorbt-workspace\VectorBT Pro Official Documentation\

**NAVIGATION GUIDE - READ FIRST:**
C:\Strat_Trading_Bot\vectorbt-workspace\VectorBT Pro Official Documentation\README.md

**WORKFLOW FOR ANY VBT PRO PROBLEM:**
1. Read README.md to find the right section
2. Navigate to the relevant folder/file
3. Read the ENTIRE relevant file, not snippets
4. Verify methods exist: uv run python -c "import vectorbtpro as vbt; help(vbt.MethodName)"
5. Test with minimal example before full implementation

**NEVER:**
- Assume a VBT method exists without verification
- Skip the README navigation guide
- Invent methods that "should" exist

## CRITICAL: STRICT NYSE Market Hours Rule

**MANDATORY FOR ALL BACKTESTS AND DATA PROCESSING:**

**THE RULE:**
ALL data MUST be filtered to NYSE regular trading hours (weekdays only, excluding holidays) BEFORE any resampling or analysis. Failure to do this creates phantom bars on weekends/holidays leading to invalid STRAT classifications and trades.

**IMPLEMENTATION REQUIREMENTS:**
1. Filter weekends using: `vbt.utils.calendar.is_weekday(df.index)`
2. Filter NYSE holidays using: `pandas_market_calendars` library
3. Apply BOTH filters BEFORE resampling hourly to daily data
4. Verify no Saturday/Sunday bars exist in final dataset
5. Verify no holiday bars exist (Christmas, Thanksgiving, etc.)

**WHY THIS IS CRITICAL:**
- Alpaca API can return midnight bars on Saturdays from Friday extended hours
- Pandas resample creates phantom bars if weekends/holidays not filtered
- Phantom bars create false STRAT patterns (e.g., 2-1-2 on Fri-Sat-Mon)
- Trades executed on non-existent market days invalidate entire backtest
- December 16, 2023 Saturday bar bug demonstrated this issue

**VERIFICATION CHECKLIST:**
```python
# After filtering, verify no weekends
assert daily_data.index.dayofweek.max() < 5, "Weekend bars detected!"

# After filtering, check specific known holidays
# Dec 25 (Christmas) should NOT exist in dataset
assert '2023-12-25' not in daily_data.index, "Holiday bar detected!"
```

**DEPENDENCY:**
```toml
dependencies = ["pandas-market-calendars>=4.0.0"]
```

## CURRENT STATE - October 1, 2025

### WORKING Components ✅
1. **Bar Classification with Governing Range** (core/analyzer.py)
   - Correctly tracks governing range for consecutive inside bars
   - Distinguishes 2U (value: 2) from 2D (value: -2)
   - Handles 1, 2U, 2D, 3 classifications
   - VERIFIED on real SPY market data

2. **Pattern Detection with Directional Logic** (core/analyzer.py)
   - 2-1-2 patterns: 4 variants (2U-1-2U, 2D-1-2D, 2U-1-2D, 2D-1-2U)
   - 3-1-2 patterns: 2 variants (3-1-2U, 3-1-2D)
   - 2-2 reversals: 2 variants (2U→2D, 2D→2U)
   - 3-2 patterns: 2 variants (3-2U, 3-2D)
   - 3-2-2 patterns: 4 variants with proper directions

3. **VBT Pro Integration** (All methods verified)
   - vbt.PF.from_signals() - Portfolio creation
   - pf.stats() - Performance metrics
   - pf.plot() - Native visualization
   - NO dashboard needed - VBT native plotting works

4. **TFC Continuity Scoring** (tests/test_basic_tfc.py)
   - Full Time Frame Continuity analysis WORKING
   - Maps hourly bars to D, W, M timeframes
   - Calculates alignment scores (FTFC, FTC, Partial, etc.)
   - 43.3% of bars have high-confidence alignment

5. **Multi-Timeframe Data Manager** (data/mtf_manager.py)
   - Market-aligned hourly bars (9:30, 10:30, etc.)
   - RTH-only filtering (9:30 AM - 4:00 PM ET)
   - Eastern timezone handling with DST
   - 6 timeframes: 5min, 15min, 1H, 1D, 1W, 1M

### File Structure (CLEAN - 12 Python files)
```
vectorbt-workspace/
├── core/               # 3 files - STRAT logic
│   ├── analyzer.py     # STRATAnalyzer - bar classification & patterns
│   ├── components.py   # PivotDetector, InsideBarTracker, PatternStateMachine
│   └── triggers.py     # Intrabar trigger detection
├── data/               # 2 files - Data management
│   ├── alpaca.py       # Alpaca data fetching
│   └── mtf_manager.py  # Multi-timeframe manager with market alignment
├── tests/              # 3 files - All tests WORKING
│   ├── test_strat_vbt_alpaca.py    # VBT integration test
│   ├── test_basic_tfc.py           # TFC continuity scoring (PHASE 2 COMPLETE)
│   └── test_strat_components.py    # Component tests
├── trading/            # Empty - Ready for Phase 3
├── backtest/           # Empty - Ready for backtesting
├── config/             # Contains .env file
├── docs/               # HANDOFF.md, CLAUDE.md
└── pyproject.toml      # With VectorBT Pro 2025.7.27
```

## MANDATORY SESSION START CHECKLIST

**STOP - Complete ALL steps BEFORE any code:**

```bash
# 1. Read HANDOFF.md FIRST - contains current state
cat C:\Strat_Trading_Bot\vectorbt-workspace\HANDOFF.md

# 2. Verify VectorBT Pro accessible (MUST USE UV RUN)
uv run python -c "import vectorbtpro as vbt; print(f'VBT Pro {vbt.__version__} loaded')"

# 3. Test STRAT classification works
uv run python test_strat_vbt_alpaca.py

# 4. Verify professional communication standards documented
cat docs/CLAUDE.md | head -60  # Review professional standards

# 5. Monitor context window (<50% warning, <70% handoff)
```

## What Was Fixed Today (October 1, 2025)

1. **CRITICAL: Saturday Bar Bug** - Discovered and fixed phantom weekend/holiday bars in backtest data
   - December 16, 2023 (Saturday) bar was creating invalid 2-1-2 patterns
   - Implemented STRICT NYSE market hours filtering (weekdays + holidays)
   - Added pandas-market-calendars for proper holiday filtering

2. **2-2 Reversal Exit Logic** - Corrected fundamental misunderstanding
   - OLD (WRONG): Exit on ANY single 2D bar (for longs) or 2U bar (for shorts)
   - NEW (CORRECT): Exit only on TRUE 2-2 reversals (2U->2D for longs, 2D->2U for shorts)
   - This allows holding through momentum continuation (2D-2D-2D)

3. **Data Source Validation** - Verified Alpaca adjustment settings
   - Using adjustment='all' for dividend+split adjusted prices
   - Confirmed bar classifications match TradingView/ThinkOrSwim
   - STRAT classifications are data-source agnostic (relative comparisons)

4. **4-Timeframe TFC Implementation** - Re-added hourly timeframe
   - Corrected from accidental 3-timeframe system (D+W+M) back to 4-timeframe (H+D+W+M)
   - TFC scores now properly reflect Full Time Frame Continuity per STRAT methodology

## Next Priorities

1. **Multi-timeframe Continuity** - Implement D, 4H, 1H, 15M alignment checks
2. **Additional Rev STRAT Patterns** - PMG, broadening formations, inside bar continuations
3. **Performance Optimization** - Consider vectorizing classification (currently uses loop for correctness)
4. **Live Trading Integration** - Connect to Alpaca for paper/live trading

## MANDATORY Quality Gates

Before claiming ANY functionality works:

1. **Test it**: Run the actual code
2. **Verify output**: Check the results are correct
3. **Measure performance**: Back claims with numbers
4. **Check VBT compliance**: Use proper vectorization where possible
5. **Document evidence**: Show actual output

**ZERO TOLERANCE for unverified claims**

## Context Management

### MANDATORY Handoff Triggers
- Context window >50%: Prepare handoff
- Context window >70%: MANDATORY handoff to HANDOFF.md
- Complex changes >10 files: STOP and simplify
- Repeating questions: Sign of context fatigue

### File Management Policy
- DELETE redundant files, don't archive
- Keep <10 core files
- One test file per component
- One documentation file (HANDOFF.md)

## Security and Compliance

- NO credential harvesting or malicious code assistance
- NO bulk crawling for sensitive data
- NO synthetic/mock data generation
- YES to defensive security analysis
- YES to vulnerability explanations
- Verify all external code before execution
- Real market data only (via Alpaca API)

## DO NOT

1. Create new dashboard files (VBT native plotting sufficient)
2. Add test files before fixing production
3. Use pickle.dump (use vbt.save if needed)
4. Skip VBT Pro documentation
5. Make assumptions without verification
6. Create complex solutions when simple ones exist
7. Archive files instead of deleting them
8. Generate synthetic market data

---
END OF CLAUDE.md - Updated October 1, 2025