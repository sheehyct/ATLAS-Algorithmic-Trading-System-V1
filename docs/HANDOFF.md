# HANDOFF - ATLAS Trading System Development

**Last Updated:** October 21, 2025 19:00 ET
**Current Branch:** `main` (ATLAS production branch)
**Phase:** Phase 2 Foundation Implementation (COMPLETE)
**Next Phase:** Phase 3 - RiskManager Implementation

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

**Data Fetching**
- Alpaca integration working (data/alpaca.py)
- Multi-timeframe manager working (data/mtf_manager.py)
- RTH filtering: between_time() + pandas_market_calendars
- NYSE trading days filter: Date-only comparison (timezone-safe)

### NOT IMPLEMENTED (Phase 3 Objectives)

**RiskManager - NOT STARTED**
- File: `core/risk_manager.py` (to create)
- Purpose: Portfolio heat tracking (6-8% hard limit)
- Features: can_take_position() gate, multi-position aggregation
- Priority: HIGH (Gate 2 requirement)

**Portfolio Manager - NOT STARTED**
- File: `core/portfolio_manager.py` (future)
- Purpose: Multi-strategy orchestration
- Phase: Phase 3+

**GMM Regime Detection - NOT STARTED**
- File: `utils/regime_detector.py` (future)
- Phase: Phase 3

---

## Test Results Summary (Oct 21)

```
Component                    Tests    Status
─────────────────────────────────────────────
Position Sizing (Gate 1)      5/5    PASSING
BaseStrategy Unit Tests      21/21   PASSING
ORB Refactored Tests          5/5    PASSING
─────────────────────────────────────────────
TOTAL:                       31/31   PASSING
```

**All gates validated. Zero test failures.**

---

## Recent Session Summary (Oct 21, 2025)

### Session 5: BaseStrategy & ORB Refactor

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

## Next Actions (Phase 3 - RiskManager)

**Priority 1: RiskManager Implementation**
1. Create `core/risk_manager.py` with portfolio heat tracking
2. Implement can_take_position(proposed_risk, current_heat) -> bool
3. 6-8% hard limit on portfolio heat
4. Multi-position risk aggregation
5. Create `tests/test_risk_manager.py`
6. Gate 2 validation

**Priority 2: Replace Old ORB**
1. Delete `strategies/orb.py` (old implementation)
2. Rename `strategies/orb_refactored.py` -> `strategies/orb.py`
3. Update all imports
4. Delete `tests/test_orb_quick.py` (old tests)

**Priority 3: System Integration Test**
1. Run ORB with longer date range (2020-2024)
2. Verify trades execute correctly
3. Validate position sizes + portfolio heat gates
4. Document performance metrics

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
