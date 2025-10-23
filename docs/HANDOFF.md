# HANDOFF - ATLAS Trading System Development

**Last Updated:** October 22, 2025 (Session 7 - Gate 2 Risk Management)
**Current Branch:** `main` (ATLAS production branch)
**Phase:** Phase 3 - Risk Management (Gate 2 COMPLETE)
**Next Phase:** Phase 4 - PortfolioManager Integration

---

## CRITICAL DEVELOPMENT RULES

### MANDATORY: 5-Step VBT Verification Workflow

**ZERO TOLERANCE for skipping this workflow. Session 5 failures demonstrate why:**

Before implementing ANY VectorBT Pro feature, MUST complete ALL 5 steps:

```
1. SEARCH - mcp__vectorbt-pro__search() for patterns/examples
2. VERIFY - resolve_refnames() to confirm methods exist
3. FIND - mcp__vectorbt-pro__find() for real-world usage
4. TEST - mcp__vectorbt-pro__run_code() minimal example
5. IMPLEMENT - Only after 1-4 pass successfully
```

**Session 5 Evidence (Oct 21):**
- Skipped workflow 3 times before implementing daily-to-intraday broadcasting
- Nearly implemented WRONG code (manual dict mapping, duplicate detection)
- VBT search revealed CORRECT pattern: `align()` method
- Result: 30 minutes of correct implementation vs hours of debugging

**Reference:** CLAUDE.md lines 115-303 (complete workflow with examples)

**Consequence of skipping:** 90% chance of implementation failure, wasted time debugging

---

### MANDATORY: Windows Compatibility - NO Unicode

**ZERO TOLERANCE for emojis or special characters in ANY code or documentation**

**Why:** Windows Git operations fail with unicode errors. CI/CD pipelines break.

**Use:**
- `[PASS]` not checkmark unicode
- `[FAIL]` not X unicode
- `[WARN]` not warning unicode
- Plain ASCII text ONLY

**Session 5 Evidence:** Test files crashed with `UnicodeEncodeError` when using checkmarks

**Reference:** CLAUDE.md lines 45-57 (Windows Unicode Compatibility)

---

## Current System Status

### Working Components (VALIDATED)

**Position Sizing (Gate 1 - PASSED Oct 13-15)**
- File: `utils/position_sizing.py`
- Tests: `tests/test_gate1_position_sizing.py` - 5/5 PASSING
- Mean position size: 10-30% of capital
- Max position size: Never exceeds 100%
- Capital constraint enforced mathematically

**BaseStrategy Abstract Class (COMPLETE Oct 21)**
- File: `strategies/base_strategy.py` (418 lines)
- Tests: `tests/test_base_strategy.py` - 21/21 PASSING
- Abstract methods: generate_signals(), calculate_position_size(), get_strategy_name()
- Implemented methods: backtest(), get_performance_metrics()
- VBT integration: Verified using 5-step workflow
- Fixed: get_performance_metrics() now uses pf.trades.winning.returns.mean()

**ORB Strategy Refactored (COMPLETE Oct 21)**
- File: `strategies/orb_refactored.py` (526 lines)
- Tests: `tests/test_orb_refactored.py` - 5/5 PASSING
- Inherits: BaseStrategy abstract class
- Features: Volume confirmation (2.0x MANDATORY), ATR stops, EOD exits
- RTH Bug: FIXED (timezone issue resolved with date-only comparison)
- Broadcasting: Uses VBT-verified align() pattern
- Result: 1580 bars returned (was 0 before fix)

**Portfolio Heat Manager (Gate 2 - PASSED Oct 22)**
- File: `utils/portfolio_heat.py` (277 lines)
- Tests: `tests/test_gate2_risk_management.py` - 10/10 PASSING
- Features: Aggregate risk tracking, pre-trade gating, 8% hard limit
- Validation: `tests/validate_gate2.py` - PASSED
- Result: Trades rejected when heat would exceed 8% limit

**RiskManager (COMPLETE Oct 22)**
- File: `core/risk_manager.py` (258 lines)
- Tests: `tests/test_gate2_risk_management.py` - 8/8 PASSING
- Features: Drawdown circuit breakers, position size validation
- Thresholds: 10% WARNING, 15% REDUCE_SIZE, 20% STOP_TRADING
- Result: Automatic risk reduction during drawdowns

**Data Fetching**
- Alpaca integration working (data/alpaca.py)
- Multi-timeframe manager working (data/mtf_manager.py)
- RTH filtering: between_time() + pandas_market_calendars
- NYSE trading days filter: Date-only comparison (timezone-safe)

### NOT IMPLEMENTED (Phase 4 Objectives)

**Portfolio Manager - NOT STARTED**
- File: `core/portfolio_manager.py` (future)
- Purpose: Multi-strategy orchestration
- Phase: Phase 3+

**GMM Regime Detection - NOT STARTED**
- File: `utils/regime_detector.py` (future)
- Phase: Phase 3

---

## Test Results Summary (Oct 22)

```
Component                      Tests    Status
───────────────────────────────────────────────
Position Sizing (Gate 1)        5/5    PASSING
BaseStrategy Unit Tests        21/21   PASSING
ORB Refactored Tests            5/5    PASSING
Portfolio Heat Manager (Gate 2) 10/10   PASSING
RiskManager (Gate 2)            8/8    PASSING
Integration Test                1/1    PASSING
───────────────────────────────────────────────
TOTAL:                         50/50   PASSING
```

**Gate 1 PASSED. Gate 2 PASSED. Zero test failures.**

---

## Recent Session Summaries

### Session 7: Gate 2 Risk Management Implementation (Oct 22, 2025)

**Objective:**
Implement Layer 2 (Portfolio Heat Management) of the ATLAS risk framework to pass Gate 2 validation.

**Verification Workflow Applied:**
Before implementation, ran modified 5-step workflow to verify VBT has no built-in solution:
1. SEARCH: "portfolio heat risk management multi position aggregate exposure tracking"
2. VERIFY: Scanned all 400+ Portfolio methods - NO pre-trade gating found
3. FIND: Discord messages confirm VBT maintainer states feature doesn't exist
4. CONCLUSION: Custom implementation required (no VBT dependencies)
5. PROCEED: Implement pure Python classes per System_Architecture_Reference.md

**Components Implemented:**

**PortfolioHeatManager (utils/portfolio_heat.py - 277 lines)**
- Tracks aggregate risk across all open positions
- Gating function: can_accept_trade() enforces 8% hard limit
- Position management: add_position(), remove_position(), update_position_risk()
- Heat calculation: sum(all position risks) / capital
- Professional validation: max_heat limited to 6-10% range

**RiskManager (core/risk_manager.py - 258 lines)**
- Drawdown circuit breakers with cascading thresholds
- 10% DD: WARNING (log only, no action)
- 15% DD: REDUCE_SIZE (risk_multiplier = 0.5)
- 20% DD: STOP_TRADING (trading_enabled = False)
- Peak equity tracking and automatic recovery

**Test Coverage (tests/test_gate2_risk_management.py - 400 lines)**
- PortfolioHeatManager: 10 tests covering all scenarios
- RiskManager: 8 tests covering circuit breakers and validation
- Integration: 1 test combining heat + drawdown management
- Total: 19/19 tests PASSING

**Validation Results (tests/validate_gate2.py)**
- Scenario: 5 positions attempted with 2% risk each (10% total)
- Result: 4 positions accepted (8% heat), 5th REJECTED
- After closing 1 position: Heat drops to 6%, new position accepted
- Verification: Portfolio heat NEVER exceeded 8% limit
- Conclusion: Gate 2 PASSED

**Key Architectural Decision:**
- Separated concerns: PortfolioHeatManager (aggregate position risk) vs RiskManager (realized drawdown)
- Pure Python implementation (no VBT API dependencies)
- Pre-trade gating (rejects before execution) vs post-trade monitoring
- Modular design allows independent testing and future integration

**Files Created:**
- `utils/portfolio_heat.py` (277 lines)
- `core/risk_manager.py` (258 lines)
- `tests/test_gate2_risk_management.py` (400 lines)
- `tests/validate_gate2.py` (100 lines)

**Total:** 1,035 new lines, 0 deletions

**Test Status:**
- Previous: 31/31 PASSING
- Added: 19/19 PASSING
- Current: 50/50 PASSING

**Gates Status:**
- Gate 1 (Position Sizing): PASSED Oct 13-15
- Gate 2 (Portfolio Heat): PASSED Oct 22
- Gate 3 (Strategy Performance): Pending Phase 4 integration

**Next Steps (Phase 4):**
1. Integrate PortfolioHeatManager with PortfolioManager orchestration
2. Implement BaseStrategy integration with heat gating
3. Run multi-strategy backtest with heat limits enforced
4. Validate Gate 3 (ORB performance with all gates active)

**Commits:**
- [Pending] feat: implement portfolio heat and risk management for Gate 2

---

### Session 6: Critical Opening Range Broadcast Bug Fix (Oct 22, 2025)

**Problem Identified:**
- ORB strategy executed 0 trades in January 2024 test period
- Unit tests passing but strategy fundamentally broken
- Classic "green tests, broken system" anti-pattern

**Root Cause:**
Opening range broadcast using align() pattern created ALL NaN values:
- Pattern: `opening_high.align(data['Close'], broadcast_axis=0, method='ffill', join='right')`
- Result: 1580 NaN values (100% of intraday bars)
- Consequence: No price breakout signals (Close > NaN = False)
- Consequence: No directional bias signals (NaN > NaN = False)

**Diagnostic Evidence:**
- Signal decomposition revealed 0 price breakouts and 0 directional bias signals
- Volume filter working correctly (111 bars with 2.0x surge)
- Time filter working correctly (1460 bars after 10:00 AM)
- Bottleneck: Opening range values were ALL NaN after broadcast

**Fix Applied (VBT 5-Step Workflow):**
1. SEARCH: Found reindex/map patterns in VBT Discord examples
2. VERIFY: Tested map by date pattern (standard pandas, no VBT-specific API)
3. FIND: Confirmed pattern in multiple VBT user examples
4. TEST: Validated with mcp__vectorbt-pro__run_code (0 NaN values)
5. IMPLEMENT: Replaced align() with map by date pattern

**New Pattern (orb_refactored.py lines 226-235):**
```python
# Map daily values to intraday by date
opening_high_dict = dict(zip(opening_high.index.date, opening_high.values))
intraday_dates = pd.Series(data.index.date, index=data.index)
opening_high_ff = intraday_dates.map(opening_high_dict)
```

**Additional Fix:**
- ATR reindexing had same bug (lines 293-295)
- Applied same map by date pattern for ATR daily-to-intraday broadcast

**Validation Results:**
- January 2024: 4 trades executed (previously 0)
- Q1 2024 (Jan-Mar): 13 trades executed
- 31 entry signals generated in Jan 2024
- 73 entry signals generated in Q1 2024

**Files Modified:**
- `strategies/orb_refactored.py` (opening range + ATR broadcast)
- `tests/diagnostic_orb_jan2024.py` (signal decomposition diagnostic)
- `tests/validate_orb_fix.py` (validation script)

**Key Lesson:**
- Unit tests must verify functional outcomes, not just code structure
- Opening range bug passed tests because tests checked data types, not values
- Diagnostic decomposition revealed the exact bottleneck condition
- VBT 5-step workflow prevented implementing another broken pattern

**Commits:**
- [Pending] fix: correct opening range and ATR broadcast to use map by date pattern

---

### Session 5: BaseStrategy & ORB Refactor (Oct 21, 2025)

**Completed:**
1. BaseStrategy verification against System_Architecture_Reference.md spec
2. Fixed VBT API bug in get_performance_metrics() using 5-step workflow
3. Created comprehensive test suite (21 tests)
4. Refactored ORB to inherit BaseStrategy
5. Fixed RTH filtering bug (timezone mismatch)
6. Reinstalled TA-Lib (lost during ATLAS migration)
7. Added ta-lib>=0.6.0 to pyproject.toml

**Critical Bugs Fixed:**

**Bug 1: VBT API Usage**
- Problem: pf.trades.returns[condition] caused MappedArray iteration error
- Root cause: Incorrect VBT API pattern
- Fix: Use pf.trades.winning.returns.mean() and pf.trades.losing.returns.mean()
- Verified: 5-step workflow (mcp__vectorbt-pro__search, find, run_code)

**Bug 2: RTH Filtering Returns 0 Bars**
- Problem: data_5min filtered to 0 bars after trading days filter
- Root cause: Timezone mismatch (data_5min tz-aware vs trading_days tz-naive)
- Fix: Date-only comparison using .date attribute on both sides
- Result: 1580 bars returned (was 0)

**Bug 3: Daily-to-Intraday Broadcasting**
- Problem: Duplicate label errors when reindexing
- Root cause: Using deprecated reindex pattern
- Fix: VBT-verified align() pattern from Discord examples
- Pattern: `opening_high.align(data['Close'], broadcast_axis=0, method='ffill', join='right')`

**Commits:**
- a11017d: fix: correct VBT API usage in BaseStrategy.get_performance_metrics()
- 7092ff1: feat: refactor ORB strategy to inherit BaseStrategy

---

## Key Reference Documents

**TIER 1 - Read Every Session:**
1. `docs/HANDOFF.md` - This file (current state)
2. `docs/CLAUDE.md` - Development rules (5-step VBT workflow lines 115-303)

**TIER 2 - Implementation:**
3. `docs/System_Architecture_Reference.md` - System architecture (lines 220-378 BaseStrategy spec)
4. `docs/research/STRATEGY_2_IMPLEMENTATION_ADDENDUM.md` - ORB requirements (volume 2.0x mandatory)

**TIER 3 - Guides:**
5. `docs/OpenAI_VBT/RESOURCE_UTILIZATION_GUIDE.md` - VBT MCP tools reference
6. `docs/OpenAI_VBT/PRACTICAL_DEVELOPMENT_EXAMPLES.md` - Implementation patterns

---

## File Structure (Current)

```
vectorbt-workspace/
├── strategies/
│   ├── base_strategy.py         [COMPLETE] Abstract base (418 lines)
│   ├── orb.py                   [OLD] Original implementation
│   ├── orb_refactored.py        [NEW] Inherits BaseStrategy (526 lines)
│   └── __init__.py              [FIXED] Correct imports
│
├── utils/
│   ├── position_sizing.py       [COMPLETE] Gate 1 validated (222 lines)
│   ├── portfolio_heat.py        [NOT STARTED] Gate 2 (Phase 3)
│   └── regime_detector.py       [NOT STARTED] GMM (Phase 3)
│
├── core/
│   ├── risk_manager.py          [NOT STARTED] Portfolio heat (Phase 3)
│   └── portfolio_manager.py     [NOT STARTED] Multi-strategy (Phase 3+)
│
├── tests/
│   ├── test_gate1_position_sizing.py    [PASSING] 5/5 tests
│   ├── test_base_strategy.py            [PASSING] 21/21 tests
│   ├── test_orb_refactored.py           [PASSING] 5/5 tests
│   └── test_orb_quick.py                [OLD] Original ORB tests
│
└── data/
    ├── alpaca.py                [WORKING] Data fetching
    └── mtf_manager.py           [WORKING] Multi-timeframe
```

---

## Next Actions (Phase 4 - PortfolioManager Integration)

**Priority 1: PortfolioManager Implementation**
1. Create `core/portfolio_manager.py` (multi-strategy orchestration)
2. Integrate PortfolioHeatManager with can_take_position() gating
3. Integrate RiskManager drawdown circuit breakers
4. Implement capital allocation across strategies
5. Create `tests/test_portfolio_manager.py`

**Priority 2: BaseStrategy Heat Integration**
1. Add heat gating to BaseStrategy.backtest() method
2. Modify backtest to check heat before executing trades
3. Update ORB tests to verify heat integration
4. Document integration pattern for future strategies

**Priority 3: Multi-Strategy Integration Test**
1. Run ORB with heat limits enforced (2020-2024)
2. Verify trades rejected at 8% heat limit
3. Validate drawdown circuit breakers trigger correctly
4. Document Gate 3 performance metrics (Sharpe >2.0, R:R >3:1)

**Priority 4: Code Cleanup**
1. Delete `strategies/orb.py` (old implementation)
2. Rename `strategies/orb_refactored.py` -> `strategies/orb.py`
3. Update all imports
4. Delete `tests/test_orb_quick.py` (old tests)

---

## Known Issues (Non-Blocking)

**1. Pandas Deprecation Warnings**
- Location: strategies/orb_refactored.py lines 225-228
- Issue: align() broadcast_axis and method parameters deprecated
- Impact: Warnings only, functionality works
- Fix: Can update to new pattern (align then fillna) in future

**2. Pydantic Deprecation Warning**
- Location: strategies/base_strategy.py StrategyConfig
- Issue: class-based config deprecated in Pydantic 2.0
- Impact: Warning only, functionality works
- Fix: Migrate to ConfigDict in future

---

## Dependencies (pyproject.toml)

**Critical:**
- vectorbtpro @ git (v2025.10.15)
- pandas>=2.1.0
- numpy>=1.26.0
- pandas-market-calendars>=4.0.0
- ta-lib>=0.6.0 (added Oct 21, requires C:\ta-lib)

**Development:**
- pytest>=7.0.0
- openai>=1.51.0 (VBT MCP embeddings)
- lmdbm, bm25s, tiktoken (VBT search assets)

---

## Development Workflow Checklist

**Every Session Start:**
- [ ] Read HANDOFF.md (this file)
- [ ] Read CLAUDE.md lines 1-114 (professional standards)
- [ ] Verify environment: `uv run python -c "import vectorbtpro as vbt; print(vbt.__version__)"`
- [ ] Check Next Actions section above

**Every VBT Implementation:**
- [ ] Step 1: mcp__vectorbt-pro__search()
- [ ] Step 2: resolve_refnames() + get_attrs()
- [ ] Step 3: mcp__vectorbt-pro__find()
- [ ] Step 4: mcp__vectorbt-pro__run_code()
- [ ] Step 5: Implement only after 1-4 pass

**Before Committing:**
- [ ] All tests passing (uv run pytest -v)
- [ ] No emojis or unicode in code/docs
- [ ] Professional commit message (feat/fix/docs/test/refactor)
- [ ] Update HANDOFF.md if major changes

---

## Performance Targets (Reference)

**Position Sizing (Gate 1):**
- Mean: 10-30% of capital (PASSING)
- Max: <=100% of capital (PASSING)

**Portfolio Heat (Gate 2):**
- Total exposure: 6-8% max (NOT YET IMPLEMENTED)

**ORB Strategy (Gate 3):**
- Sharpe: >2.0 (backtests needed with longer period)
- R:R: >3:1 (backtests needed)
- Win Rate: 15-25% expected
- Net Expectancy: >0.5% per trade

---

## Contact & Credentials

**Alpaca Accounts:**
- MID Account: Algo Trader Plus subscription (used for ORB)
- Credentials: config/.env (ALPACA_MID_KEY, ALPACA_MID_SECRET)

**TA-Lib:**
- C Library: C:\ta-lib
- Python: ta-lib>=0.6.0 in pyproject.toml
- Verify: `uv run python -c "import talib; print(len(talib.get_functions()))"`

---

**End of HANDOFF.md**
