# Phase 2 Foundation Implementation - Session Startup

## Current State

**Repository:** ATLAS-Algorithmic-Trading-System-V1 (GitHub)
**Branch:** main
**Phase 1:** COMPLETE (Migration from STRAT to ATLAS)
**Token Budget:** Start fresh for maximum implementation context

---

## Phase 1 Completion Summary

**Completed:**
- Clean ATLAS repository created with professional commit history
- All STRAT components removed (50 files, 63k lines)
- Documentation updated (README, HANDOFF, Architecture, LICENSE)
- Professional communication standards established (CLAUDE.md)
- Position sizing complete (utils/position_sizing.py - Gate 1 PASSED)
- ORB strategy implemented (strategies/orb.py - needs BaseStrategy refactor)

**Repository Status:**
- Working tree: Clean
- Remote: Fully synchronized
- 6 professional commits
- No STRAT references remain

---

## Phase 2 Objectives: Foundation Implementation

### Deliverables (3-5 days)

**Day 1-2: BaseStrategy Abstract Class**
- Create `strategies/base_strategy.py`
- Match System_Architecture_Reference.md specification exactly
- Abstract methods: generate_signals(), calculate_position_size()
- Implemented methods: backtest(), get_performance_metrics()
- Pydantic validation for strategy configs
- VectorBT Pro integration built-in

**Day 2-3: ORB Strategy Refactor**
- Refactor `strategies/orb.py` to inherit BaseStrategy
- Fix RTH filtering bug (timezone/filtering issue)
- Maintain volume confirmation (2.0x mandatory)
- Apply capital-constrained position sizing
- Create unit tests

**Day 3-4: RiskManager Implementation**
- Create `core/risk_manager.py`
- Portfolio heat tracking (6-8% hard limit)
- can_take_position() gate function
- Multi-position risk aggregation
- Circuit breakers for drawdown limits
- Create unit tests

**Day 5: Integrated Validation**
- Run complete system test
- Verify all gates passing (position sizing + portfolio heat)
- Validate VectorBT Pro integration
- Document any issues or deviations

---

## Critical References

**Must Read Before Implementation:**

1. **System_Architecture_Reference.md** (lines 220-378)
   - BaseStrategy abstract class specification
   - Exact method signatures required
   - VectorBT Pro integration pattern

2. **CLAUDE.md** (lines 1-230)
   - Professional communication standards
   - VectorBT Pro 5-step verification workflow
   - Mandatory quality gates

3. **HANDOFF.md**
   - Current implementation status
   - Gate 1 validation results
   - Known blockers (ORB RTH filtering)

4. **docs/research/Medium_Articles_Research_Findings.md**
   - Portfolio heat management principles
   - GMM regime detection (future Phase 3)
   - Professional risk management approach

---

## Implementation Guidelines

### VectorBT Pro Verification (MANDATORY)

**Before implementing ANY VBT feature:**
1. Use MCP tools: `mcp__vectorbt-pro__search()`
2. Verify method exists: `mcp__vectorbt-pro__get_attrs()`
3. Find examples: `mcp__vectorbt-pro__find()`
4. Test minimal example: `mcp__vectorbt-pro__run_code()`
5. ONLY THEN implement

**ZERO TOLERANCE for skipping verification steps.**

### Git Commit Standards

**Format:**
```
<type>: <subject>

<body explaining WHAT changed and WHY>

Reference: <docs if applicable>
```

**Types:** feat, fix, docs, test, refactor
**Tone:** Professional quantitative developer
**NO:** Emojis, AI signatures, excessive caps

### Code Quality Standards

- Type hints required for all functions
- Docstrings for all public methods
- Unit tests before merge
- VectorBT Pro compatibility verified
- Professional comments (explain WHY, not WHAT)

---

## Known Issues and Blockers

### ORB Strategy RTH Filtering Bug
**Location:** strategies/orb.py (fetch_data method)
**Symptom:** Returns 0 bars after trading hours filter
**Likely Cause:** Timezone handling or filter logic
**Priority:** Fix during ORB refactor (Day 2)

### Missing Components
**Not Yet Implemented:**
- strategies/base_strategy.py (PRIMARY TASK)
- core/risk_manager.py (Day 3-4)
- core/portfolio_manager.py (Future Phase 3)
- GMM regime detection (Future Phase 3)

---

## Success Criteria (Phase 2 Complete)

**Must Achieve:**
1. BaseStrategy abstract class working and tested
2. ORB inherits BaseStrategy, all tests passing
3. RiskManager enforces 6-8% portfolio heat limit
4. Integrated backtest runs without errors
5. Mean position size: 10-30%, Max ≤100% (Gate 1)
6. Portfolio heat never exceeds 8% (Gate 2)
7. All unit tests passing (100% pass rate)

**Validation Commands:**
```bash
# Verify environment
uv run python -c "import vectorbtpro as vbt; print(f'VBT {vbt.__version__}')"

# Run tests
uv run pytest tests/test_gate1_position_sizing.py -v
uv run pytest tests/test_base_strategy.py -v  # To create
uv run pytest tests/test_risk_manager.py -v   # To create

# Verify ORB refactor
uv run pytest tests/test_orb_quick.py -v
```

---

## First Actions (Recommended Sequence)

1. **Read HANDOFF.md** (current state)
2. **Read CLAUDE.md** (development standards)
3. **Verify environment** (VBT, dependencies)
4. **Review System_Architecture_Reference.md** (BaseStrategy spec, lines 220-378)
5. **Use VBT MCP tools** to verify Portfolio.from_signals() pattern
6. **Create strategies/base_strategy.py** (start implementation)

---

## Key Architectural Decisions (From Phase 1)

**Naming:** ATLAS (Adaptive Trading with Layered Asset System)

**Philosophy:**
- Expectancy over win rate
- Portfolio-level orchestration
- Professional risk controls (multiple layers)
- Validation-first development

**Technology Stack:**
- VectorBT Pro v2025.10.15
- Python 3.12+
- UV package manager
- OpenAI API (advanced features)
- Alpaca API (data + paper trading)

**5-Strategy Portfolio:**
1. GMM Regime Detection (Phase 3)
2. Five-Day Washout Mean Reversion (Phase 4)
3. Opening Range Breakout (Phase 2 - refactor)
4. Pairs Trading (Phase 5)
5. Semi-Volatility Momentum (Phase 5)

---

## Performance Targets (Reference)

**ORB Strategy (after refactor):**
- Win Rate: 15-25% (low win rate, high R:R)
- Sharpe: 1.5-2.5
- Max DD: <25%
- CAGR: 15-25%
- R:R: >3:1 minimum

**Portfolio (all 5 strategies):**
- Sharpe: >1.0 (excellent: >1.5)
- Max DD: <25% (excellent: <20%)
- CAGR: 10-15% (excellent: >18%)

---

## Questions to Answer During Implementation

1. Does BaseStrategy.backtest() need position sizing integration or leave to strategies?
2. Should RiskManager be singleton or instantiated per strategy?
3. How to handle position sizing when portfolio heat at limit?
4. Should BaseStrategy include regime awareness or add later?
5. ORB RTH filtering: Use pandas_market_calendars or VBT native?

**Document decisions in code comments with rationale.**

---

## End State (Phase 2 Complete)

**File Structure:**
```
strategies/
├── base_strategy.py     ✅ NEW - Abstract base
├── orb.py              ✅ REFACTORED - Inherits BaseStrategy

core/
├── risk_manager.py     ✅ NEW - Portfolio heat
└── __init__.py

tests/
├── test_base_strategy.py    ✅ NEW
├── test_risk_manager.py     ✅ NEW
├── test_orb_quick.py        ✅ UPDATED
└── test_gate1_position_sizing.py  ✅ PASSING (no changes)
```

**Ready for Phase 3:**
- GMM Regime Detection implementation
- Mean Reversion strategy
- Portfolio Manager orchestration

---

**Session Focus:** Build foundation correctly. Speed comes from doing it right the first time, not rushing and refactoring.

**Remember:** Professional quantitative development standards. Every commit is collaborative-ready.
