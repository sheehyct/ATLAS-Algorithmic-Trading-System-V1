# HANDOFF - ATLAS Trading System Development

## Current Branch
`main` (ATLAS production branch)

## Session Date
**October 18, 2025 - ATLAS Migration Complete, Foundation Implementation Begins**

---

## Context: Strategic Pivot from Previous Approach

**Previous branch:** `feature/baseline-ma-rsi`
**Previous approach:** Fix position sizing bug → implement strategies
**Why pivoted:** Diagnostic framework analysis revealed missing foundational layers

**Key documents that informed pivot:**
- `research/diagnostic_framework.md` - Failure mode taxonomy
- `research/Medium_Articles_Research_Findings.md` - Professional risk management principles
- `archives/baseline-ma-rsi/POSITION_SIZING_VERIFICATION.md` - Position sizing bug analysis

**Archived documentation:** See `archives/baseline-ma-rsi/README.md` for complete context

---

## Key Reference Documents

**CRITICAL - Read These Before Any Implementation:**

1. **System_Architecture_Reference.md** - Theoretical complete system state
   - Defines all 5 strategies with full implementation examples
   - Shows BaseStrategy abstract class pattern
   - Documents expected performance targets and success criteria
   - **Use this as the north star for what we're building**

2. **research/algo_trading_diagnostic_framework.md** - Common failure patterns
   - Taxonomy of failure modes (overfitting, data issues, execution failures)
   - Diagnostic checklists for debugging strategies
   - Professional risk management principles
   - **Read this when strategies fail or underperform**

3. **research/STRATEGY_2_IMPLEMENTATION_ADDENDUM.md** - Mandatory ORB corrections
   - Volume confirmation MANDATORY at 2.0x threshold
   - Sharpe ratio targets doubled (2.0+ minimum)
   - R:R minimum 3:1 with mathematical proof
   - STRAT-lite bias filter as optional enhancement

4. **research/Medium_Articles_Research_Findings.md** - Professional quant approach
   - GMM regime detection methodology
   - Portfolio heat management principles
   - Multi-strategy portfolio construction
   - Expectancy analysis framework

---

## The Foundational Problem

### Three Missing Risk Layers

Reading the diagnostic framework and Medium articles research revealed the system has **three missing risk layers**, not just a position sizing bug:

#### Layer 1: Position Sizing Constraint (COMPLETED Oct 13-15)
**Problem:** 81.8% mean position size, max 142.6% of capital
**Root cause:** Formula correct but missing capital constraint
**Status:** COMPLETED - utils/position_sizing.py implemented with passing tests (Gate 1 PASSED)

```python
# WRONG (current):
position_size = (init_cash * 0.02) / stop_distance

# CORRECT (to implement):
position_size_risk = (init_cash * 0.02) / stop_distance
position_size_capital = init_cash / close
position_size = min(position_size_risk, position_size_capital)  # Hard constraint
```

**Documentation:** `archives/baseline-ma-rsi/POSITION_SIZING_VERIFICATION.md`

---

#### Layer 2: Portfolio Heat Management (Completely Missing)
**Problem:** No constraint on total exposure across multiple strategies
**Current risk:** Running 3 strategies simultaneously could allocate 90% capital with 1.8% total risk
**Professional standard:** 6-8% max total portfolio heat (hard gate, no exceptions)

**Example of what's missing:**
```
Capital: $100,000
Position 1: $2,000 at risk
Position 2: $2,500 at risk
Position 3: $2,000 at risk
Total Heat: $6,500 (6.5%)

New Signal: Would add $2,000 risk
Decision: PASS (would exceed 8% limit) ← This gate doesn't exist yet
```

**Documentation:** `research/Medium_Articles_Research_Findings.md` (Concept 4)

---

#### Layer 3: Regime Awareness (Never Considered)
**Problem:** No concept of "when to trade vs when to stay out"
**Current risk:** Trading with same rules in bull markets AND bear markets
**Proven solution:** GMM regime detection (Sharpe 0.63→1.00, MDD -34%→-15%)

**What's missing:**
- Detect market regime (Bullish/Neutral/Bearish) using Yang-Zhang volatility + SMA crossover
- Only trade ORB/breakout strategies in Bullish regime
- Stay in cash during Neutral/Bearish regimes
- Avoids 2020 crash (-34%), 2022 bear market (-25%)

**Documentation:** `research/Medium_Articles_Research_Findings.md` (Concept 1)

---

## Week 1 Objectives (Current Session)

### Deliverables

**1. utils/position_sizing.py**
- Capital-constrained position sizing formula
- VBT-compatible return format (verified with `vbt.phelp()`)
- Unit tests proving position sizes ≤100%

**2. utils/portfolio_heat.py**
- Portfolio heat manager (6-8% hard limit)
- Tracks total risk across all open positions
- Gate function: `can_take_position(proposed_risk, current_heat)` → bool

**3. Unit Tests**
- Position sizing mathematical correctness
- Portfolio heat constraint enforcement
- VBT integration smoke tests

**4. Mathematical Verification Document**
- Prove position sizes never exceed 100% of capital
- Prove portfolio heat never exceeds 8%
- Document VBT integration patterns discovered

---

### Success Metrics (Week 1)

**Position Sizing:**
- Mean position size: 10-30% (down from 81.8%)
- Max position size: ≤100% (down from 142.6%)
- All unit tests pass

**Portfolio Heat:**
- Total exposure never exceeds 8%
- Multiple positions tracked correctly
- Gate function rejects signals when at limit

**VBT Integration:**
- `vbt.PF.from_signals(size=our_sizes)` runs without errors
- Portfolio metrics calculate correctly
- No data type mismatches

---

## Week 2-3 Objectives (Future)

**GMM Regime Detection Implementation:**
1. Yang-Zhang volatility calculation (uses OHLC, not just close)
2. SMA crossover normalized ((SMA20 - SMA50) / SMA50)
3. Gaussian Mixture Model (K=3 clusters)
4. Walk-forward training (expanding window, refit quarterly)
5. Regime mapping (Bullish/Neutral/Bearish based on forward returns)

**Deliverables:**
- `utils/regime_detector.py`
- Standalone backtest (Strategy 4: GMM long-only)
- Integration test with ORB signals
- Out-of-sample validation (2008-2018)

**Success Metrics:**
- Standalone Sharpe >0.8, MDD <20%
- ORB + GMM: Sharpe improvement >20%, MDD reduction >30%
- Validates on out-of-sample data

---

## Week 4 Objectives (Future)

**5-Day Washout Mean Reversion** (replaces Strategy 1 RSI logic):
- Entry: 5 consecutive lower lows + above 200-day SMA
- Exit: Close > 5-day SMA OR 2-3 day time stop
- Expected: 60-70% win rate vs <50% with RSI

**Deliverables:**
- `strategies/washout_mean_reversion.py`
- Backtest results
- Comparison to failed RSI approach

---

## What We're Abandoning (From Research)

### ✗ TFC Confidence Scoring System
**Why:** 6-7 parameters = guaranteed overfitting

**Evidence:**
- Cross-validation consensus (3 independent analyses)
- Requires 60-140 independent observations
- Available: ~50-70 effective observations
- Overfitting probability: >85%

**Decision:** ABANDON entirely (not "fix" or "test")

**Alternative:** Simple TFC alignment (4/4 or 3/4 aligned) with ZERO parameters - can test AFTER GMM if desired

**Documentation:** `research/Medium_Articles_Research_Findings.md` (Executive Summary)

---

### ✗ Strategy 1 RSI Mean Reversion (Current Implementation)
**Why:** Average trade +0.27%, 14-day holds, RSI too sensitive

**Replacement:** 5-day washout (60-70% win rate documented)

**Documentation:** `archives/baseline-ma-rsi/STRATEGY_1_BASELINE_RESULTS.md`

---

## Mandatory VBT-First Methodology

**CRITICAL:** All implementations must integrate with VectorBT Pro from day 1

### Before Writing ANY Code:

**1. Read VBT README Navigation Guide (MANDATORY FIRST STEP)**
```bash
# Location: VectorBT Pro Official Documentation/README.md
# This matrix tells you WHICH documentation to read for your specific problem
# Example: Data fetching issue? README tells you to read Alpaca_API_LLM_Documentation.md
# Example: Portfolio metrics? README tells you to read API Documentation sections
```

**2. Search VBT LLM Docs (Based on README Guidance)**
```bash
# Location: VectorBT Pro Official Documentation/LLM Docs/
# Files:
# - 3 API Documentation.md (242k+ lines - complete reference)
# - 2 General Documentation.md (comprehensive general docs)
# - 4 Alpaca_API_LLM_Documentation.md (Alpaca-specific methods)
```

**3. Python Introspection Verification**
```python
import vectorbtpro as vbt

# Find documentation
vbt.find_docs(vbt.PF.from_signals)

# Find examples
vbt.find_examples(vbt.PF)

# Get method signatures
vbt.phelp(vbt.PF.from_signals)

# Explore available methods
vbt.pdir(vbt.PF)
```

**3. Test Minimal Example**
```python
# BEFORE full implementation, test VBT accepts our data format
uv run python -c "
import vectorbtpro as vbt
import pandas as pd

# Test if VBT accepts our position sizing format
pf = vbt.PF.from_signals(
    close=test_close,
    entries=test_entries,
    exits=test_exits,
    size=our_position_sizes,  # Does this work?
    init_cash=10000
)
print('Success:', pf.total_return)
"
```

**4. ONLY THEN Implement Full Code**

**If any uncertainty → STOP and verify with VBT docs**

---

## Verification Gates (Must Pass Before Proceeding)

### Gate 1: Position Sizing VBT Integration
**Test:**
```python
pf = vbt.PF.from_signals(
    close, entries, exits,
    size=our_position_sizes,  # VBT-compatible format
    init_cash=10000
)
assert pf.total_return is not None
assert pf.sharpe_ratio is not None
```

**Pass criteria:**
- Code runs without errors
- VBT accepts position sizing format
- Portfolio metrics calculate correctly
- Mean position size 10-30%
- Max position size ≤100%

**If fails:** Re-read VBT docs, adjust data format, retest

---

### Gate 2: Portfolio Heat VBT Integration
**Test:**
```python
# Multiple overlapping positions
entries.iloc[10] = True  # Position 1
entries.iloc[15] = True  # Position 2 (overlapping)
entries.iloc[20] = True  # Position 3 (overlapping)

# Apply portfolio heat filter
entries_filtered = apply_portfolio_heat_gate(entries, ...)

# Backtest
pf = vbt.PF.from_signals(close, entries_filtered, exits, ...)

# Verify heat never exceeded 8%
# (calculate from pf.positions or similar)
```

**Pass criteria:**
- Multiple positions tracked correctly
- Heat limit enforced (never exceeds 8%)
- VBT backtest handles filtered signals
- Performance metrics valid

**If fails:** Debug heat calculation, verify signal filtering logic

---

### Gate 3: GMM Regime VBT Integration (Week 2-3)
**Test:**
```python
regime_bullish = gmm_detector.fit_predict(data)  # Boolean Series

entries_filtered = entries & regime_bullish
exits_filtered = exits | ~regime_bullish

pf = vbt.PF.from_signals(close, entries_filtered, exits_filtered, ...)
```

**Pass criteria:**
- Regime filter returns VBT-compatible Series
- Signal filtering works correctly
- Sharpe improvement >15%
- MDD reduction >20%

---

## Current File Structure

```
vectorbt-workspace/
├── core/               # STRAT logic (keep as-is)
│   ├── analyzer.py     # Bar classification (working)
│   ├── components.py   # Pattern detectors (working)
│   └── triggers.py     # Intrabar detection (working)
├── data/               # Data management (keep as-is)
│   ├── alpaca.py       # Alpaca fetching (working)
│   └── mtf_manager.py  # Multi-timeframe manager (working)
├── src/                # OpenAI + VBT Pro integration (NEW - Session 4)
│   ├── main.py         # CLI utilities (hello, vbt-smoke commands)
│   └── vbt_bootstrap.py # VBT Pro OpenAI configuration
├── tests/              # Existing tests (keep)
│   ├── test_strat_vbt_alpaca.py
│   ├── test_basic_tfc.py
│   ├── test_strat_components.py
│   └── test_gate1_position_sizing.py  # Gate 1 tests (PASSING)
├── utils/              # Risk management modules
│   ├── position_sizing.py  # COMPLETE (Gate 1 passed Oct 13-15)
│   └── portfolio_heat.py   # TO CREATE (Week 1 incomplete)
│   └── regime_detector.py  # TO CREATE (Week 2-3)
├── strategies/         # Strategy implementations
│   └── orb.py          # Opening Range Breakout (debugging RTH filtering)
├── docs/               # Reorganized documentation
│   ├── CLAUDE.md           # Timeless rules (UPDATED Session 4D)
│   ├── HANDOFF.md          # This file - current status
│   ├── DOCUMENTATION_INDEX.md  # Navigation guide
│   ├── System_Architecture_Reference.md  # End goal roadmap
│   ├── active/
│   │   └── risk-management-foundation/  # Current branch docs
│   ├── archives/
│   │   └── baseline-ma-rsi/  # Previous branch (preserved)
│   ├── research/
│   │   ├── diagnostic_framework.md
│   │   ├── Medium_Articles_Research_Findings.md
│   │   ├── STRATEGY_2_IMPLEMENTATION_ADDENDUM.md
│   │   └── VALIDATION_PROTOCOL.md
│   └── history/
│       └── ARCHIVE_HISTORY.md
├── .env                # Environment vars (gitignored, OpenAI key configured)
└── pyproject.toml      # Dependencies (VectorBT Pro + OpenAI + intelligence libs)
```

---

## Next Actions (This Session)

### Immediate (After HANDOFF.md update):
1. Create `feature/risk-management-foundation` branch from main
2. Commit documentation reorganization to new branch
3. Begin Session 2: VBT documentation research for position sizing

### Session 2 Plan (4-5 hours):
**Morning (2 hours): VBT Documentation Research**
- Search LLM Docs for "position sizing"
- Run `vbt.phelp(vbt.PF.from_signals)` - verify `size` parameter
- Find working examples with `vbt.find_examples(vbt.PF)`
- Test minimal integration example
- Document findings in `active/risk-management-foundation/VBT_INTEGRATION_PATTERNS.md`

**Afternoon (2-3 hours): Implementation**
- Create `utils/position_sizing.py` using VBT-compatible approach
- Implement capital-constrained formula
- Unit tests (mathematical correctness)
- VBT integration test (Verification Gate 1)

---

## Professional Standards Maintained

**1. VBT-First Methodology**
- Never code without checking VBT docs
- Test minimal examples before full implementation
- Verify data types are VBT-compatible

**2. Accuracy Over Speed**
- Brutal honesty policy (uncertainty → STOP and verify)
- Documentation accuracy paramount
- Mathematical verification required

**3. Isolation Strategy**
- Infrastructure on separate branch
- Failures are isolatable (abandon branch if needed)
- Previous work preserved in archives

**4. Knowledge Preservation**
- Archives preserve negative results (valuable learning)
- Documentation index provides navigation
- Cross-references maintained

---

## Related Documentation

**Must read before proceeding:**
- `research/diagnostic_framework.md` - Failure mode taxonomy
- `research/Medium_Articles_Research_Findings.md` - Professional approach
- `VectorBT Pro Official Documentation/README.md` - VBT navigation guide
- `DOCUMENTATION_INDEX.md` - Find any documentation quickly

**Archive reference:**
- `archives/baseline-ma-rsi/README.md` - Why we pivoted
- `archives/baseline-ma-rsi/POSITION_SIZING_VERIFICATION.md` - What went wrong

**Active development:**
- `active/risk-management-foundation/` - Current branch docs (to be created)

---

## Context Management

**Current context usage:** ~56% (113k/200k tokens)
**Status:** Healthy - documentation migration complete
**Next handoff trigger:** >70% usage or complex multi-file changes

**What to preserve in next HANDOFF:**
- Risk management foundation implementation status
- VBT integration patterns discovered
- Gate pass/fail status
- Mathematical verification results

**Can forget:**
- Detailed documentation migration steps (complete)
- Old branch structure (archived)
- File-by-file categorization details

---

## Key Decisions Made

**Strategic:**
1. Pivot to risk-management-foundation approach (all three layers first)
2. Abandon TFC confidence scoring (6+ parameters = overfitting)
3. Replace RSI mean reversion with 5-day washout (future)

**Tactical:**
1. Create organized documentation structure (active/archives/research/history)
2. VBT-first methodology (verify before coding)
3. Verification gates at each implementation phase

**Technical:**
1. Capital-constrained position sizing formula
2. Portfolio heat manager (6-8% hard limit)
3. GMM regime detection (Yang-Zhang vol + SMA cross)

---

## Mindset Validation Checklist

**Before proceeding, confirm:**
- [ ] Accept expectancy > win rate (30% @ 5:1 beats 70% @ 1:1)
- [ ] ABANDON TFC scoring (not trying to fix it)
- [ ] Comfortable with 40-50% cash allocation
- [ ] Cut mean-reversion losers at 2-3 days (not 14)
- [ ] Enforce 6-8% portfolio heat (no exceptions)
- [ ] Building 5+ strategies (not perfecting one)

**If any checkbox unchecked:** Re-read `research/Medium_Articles_Research_Findings.md` Part 0 Addendum

---

**Last Updated:** 2025-10-18 (Session 4 Complete - OpenAI API Integration)
**Status:** OpenAI API integration COMPLETE, VBT Pro search WORKING, Documentation UPDATED
**Current Branch:** `feature/risk-management-foundation`
**Next Session:** Continue VBT Pro testing OR debug ORB RTH filtering

## Session 2 Summary (Completed)

**Session 2A: VBT Documentation Research (1 hour)**
- Verified vbt.PF.from_signals() accepts size as scalar, Series, or array
- Confirmed default size_type interprets as shares/units
- Happy path tests: All 3 formats PASSED
- Documented in: `docs/active/risk-management-foundation/VBT_INTEGRATION_PATTERNS.md`

**Session 2B: Edge Case Research (1 hour)**
- Mathematical proof: Capital constraint CANNOT exceed 100% of capital
- Verified VBT partial fill behavior (automatic capital protection)
- Tested 8+ edge cases (ATR NaN, fractional shares, oversized positions)
- Empirical results: mean 23.9%, max 23.9% (target: 10-30%) ACHIEVED
- Implementation confidence: 95%

**Commits:**
- f2eb2a3: Documentation reorganization
- 4507e8f: VBT position sizing research complete

**Ready for Implementation:**
All research verified, ready to create `utils/position_sizing.py` with:
- Capital-constrained formula (mathematically proven)
- Input validation (type checks, index matching)
- Edge case handling (NaN→0, Inf→0)
- Post-condition assertions
- VBT-compatible return format (pd.Series of shares)

**Estimated implementation time:** 1-2 hours

---

## Session 3 Summary (October 13-16, 2025)

**Session 3A: Position Sizing Implementation (Oct 13-15)**
- Implemented utils/position_sizing.py with capital-constrained formula
- Created test_gate1_position_sizing.py - ALL TESTS PASSED
- Gate 1 PASSED: Position sizes never exceed 100% of capital
- Mean position size within 10-30% target range

**Session 3B: ORB Strategy Implementation (Oct 15)**
- Implemented strategies/orb.py (Opening Range Breakout)
- Integrated with VBT AlpacaData.pull() for data fetching
- Applied STRATEGY_2_IMPLEMENTATION_ADDENDUM.md corrections
- Known issue: RTH filtering returns 0 bars (needs debugging)

**Session 3E: Article Research Integration (Oct 18)**
- Integrated insights from "Algorithmic Trading: Volume Analysis and De-Risking" article
- Identified critical gaps: volume confirmation, multi-layer stops, enhanced cost modeling
- Updated Strategy 2 requirements with volume confirmation mandatory
- Added slippage modeling to backtest requirements (0.15% + 0.2% fees = 0.35% total)
- Documented multi-symbol validation requirement (SPY, QQQ, IWM minimum)

**Session 3C: Alpaca Authentication Fix (Oct 16)**
- CRITICAL FIX: Discovered .env file contained old API keys
- Root cause: Keys regenerated in Alpaca dashboard but .env never updated
- Updated all three paper trading accounts (BASE, MID, LARGE) with current keys
- Verification: All authentication tests now passing

**Session 3D: Documentation Recovery (Oct 16)**
- Context loss event: Claude Code crash caused chat history loss
- Created PROJECT_AUDIT_2025-10-16.md documenting project state
- Discovered documentation 4-15 days behind actual code state
- Updated HANDOFF.md with current state and key reference documents

**Commits:**
- 9402945: feat: add ATR-based position sizing with capital constraint
- 5c6458d: feat: implement Opening Range Breakout (ORB) strategy
- 3f9aa38: wip: ORB strategy with Alpaca timezone integration issue

**Current State:**
- Position sizing: COMPLETE (Gate 1 passed)
- ORB strategy: IMPLEMENTED (debugging RTH filtering)
- Portfolio heat manager: NOT STARTED (Week 1 incomplete)
- GMM regime detection: NOT STARTED (Week 2-3 future work)

**Enhanced Strategy 2 (ORB) Requirements (from Article Research):**

**Entry Requirements:**
- Price breakout above opening range high
- Volume confirmation: MANDATORY 1.5x average volume threshold
- ATR volatility filter: Ensure sufficient volatility for profitable moves
- Rationale: Volume confirmation reduces false signals (Article: "Volume indicators measure trend strength")

**Exit Requirements:**
- Primary: ATR-based stop loss (2.5x ATR)
- Secondary: Time-based stop (5 days maximum hold)
- Tertiary: Trailing stop (activate at 2:1 R:R ratio)
- Multi-layer approach reduces single point of failure risk

**Cost Modeling:**
- Transaction fees: 0.2% per trade (Alpaca baseline)
- Slippage estimate: 0.15% per trade (Article emphasizes slippage as major risk)
- Total cost per round trip: 0.35%
- CRITICAL: Backtests without slippage overestimate performance

**Multi-Symbol Validation:**
- Must test on minimum 3 symbols: SPY, QQQ, IWM
- Strategy working on single symbol may be curve-fitted
- Professional standard: Validate across market segments
- If strategy only works on SPY, it's overfitted

**Benchmark Comparisons (Required):**
- Compare vs Buy-and-Hold on same symbol
- Compare vs SPY benchmark
- Strategy must outperform both to justify complexity
- Document: Sharpe ratio relative to benchmarks

**Blockers:**
- ORB RTH filtering returns 0 bars after applying trading hours filter
- Need to debug timezone handling or filter logic in strategies/orb.py

---

## Session 4 Summary (October 18, 2025)

**Session 4A: OpenAI API Integration (COMPLETE)**
- Implemented OpenAI API as official LLM provider for VectorBT Pro advanced features
- Created src/main.py with Typer CLI utilities (hello, vbt-smoke commands)
- Created src/vbt_bootstrap.py for VBT Pro OpenAI settings configuration
- Token optimization achieved: 76% reduction (271 output tokens → 64 tokens)
- Settings: REASONING_EFFORT=blank, MAX_OUTPUT_TOKENS=64, using gpt-5-mini for tests
- Updated .env and .env.example with OpenAI configuration
- Dependencies added: openai>=1.51.0, python-dotenv, rich, typer

**Session 4B: MCP Server Configuration (COMPLETE)**
- Configured vectorbt-pro MCP server for Claude Code (separate from Claude Desktop)
- Server status: Connected via stdio transport, local scope
- GitHub token configured for documentation access
- Command: python.exe -m vectorbtpro.mcp_server
- Verified with: claude mcp list

**Session 4C: VBT Pro Documentation Assets (COMPLETE)**
- Downloaded knowledge assets: 9,639 pages + 62,762 Discord messages
- Installed intelligence dependencies: lmdbm==0.0.6, bm25s==0.2.14, tiktoken==0.12.0, lmdb==1.7.5
- BM25 search verified working: vbt.quick_search() returns HTML results
- Asset-based search verified: pages_asset.find_obj() returns documentation
- Embeddings search available but costly (15k+ docs, requires OpenAI API)

**Session 4D: CLAUDE.md VBT Workflow Update (COMPLETE)**
- Fixed 5-step VBT verification workflow with CORRECT function calls
- Removed non-existent imports (VectorBT_Pro.search, run_code)
- Added actual working examples using vbt.quick_search(), vbt.PagesAsset.pull()
- Documented three search methods: BM25 (fast/free), Asset-based (GitHub token), Embeddings (OpenAI API)
- Step 4 now uses direct Python testing instead of non-existent run_code()

**New Files Created:**
- src/main.py (OpenAI CLI: hello smoke test, vbt-smoke config preview)
- src/vbt_bootstrap.py (VBT Pro OpenAI configuration helper)

**Dependencies Updated:**
- pyproject.toml: Added openai, lmdbm, bm25s, tiktoken

**Test Results:**
- OpenAI Responses API: Working (64 token output cap enforced)
- VBT Pro settings: Visible via vbt-smoke command (no more unset values)
- BM25 search: Working (offline, fast, free)
- Asset search: Working (requires GitHub token, already configured)

