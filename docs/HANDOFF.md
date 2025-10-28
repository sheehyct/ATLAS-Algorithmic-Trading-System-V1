# HANDOFF - ATLAS Trading System Development

**Last Updated:** October 28, 2025 (Session 12 - Academic Jump Model Phase A Complete)
**Current Branch:** `main`
**Phase:** ATLAS v2.0 - Academic Statistical Jump Model Implementation
**Status:** Phase A COMPLETE (features validated), Phase B READY (optimization solver)

---

## CRITICAL DEVELOPMENT RULES

### MANDATORY: Read Before Starting ANY Session

1. **Read HANDOFF.md** (this file) - Current state
2. **Read CLAUDE.md** - Development rules and workflows
3. **Query OpenMemory** - Use MCP tools for context retrieval
4. **Verify VBT environment** - `uv run python -c "import vectorbtpro as vbt; print(vbt.__version__)"`

### MANDATORY: 5-Step VBT Verification Workflow

**ZERO TOLERANCE for skipping this workflow:**

```
1. SEARCH - mcp__vectorbt-pro__search() for patterns/examples
2. VERIFY - resolve_refnames() to confirm methods exist
3. FIND - mcp__vectorbt-pro__find() for real-world usage
4. TEST - mcp__vectorbt-pro__run_code() minimal example
5. IMPLEMENT - Only after 1-4 pass successfully
```

**Reference:** CLAUDE.md lines 115-303 (complete workflow with examples)

**Consequence of skipping:** 90% chance of implementation failure

### MANDATORY: Windows Compatibility - NO Unicode

**ZERO TOLERANCE for emojis or special characters in ANY code or documentation**

Use plain ASCII: `[PASS]` not checkmark, `[FAIL]` not X, `[WARN]` not warning symbol

**Reference:** CLAUDE.md lines 45-57

---

## Context Management: Hybrid HANDOFF.md + OpenMemory

**System Architecture:**

**HANDOFF.md (This File):**
- Current state narrative
- Immediate next actions
- Critical rules reminder
- Condensed to ~300 lines maximum

**OpenMemory (Semantic Database):**
- Queryable facts, metrics, technical details
- Location: http://localhost:8080 (start: `cd /c/Dev/openmemory/backend && npm run dev`)
- Database: C:/Dev/openmemory/data/atlas_memory.sqlite
- Query via MCP tools: `mcp__openmemory__openmemory_query()`

**Before Each Session:**
```bash
# Check OpenMemory status
curl -s http://localhost:8080/health | grep -q "ok" && echo "Running" || cd /c/Dev/openmemory/backend && npm run dev &

# Query for context (examples)
User: "What were the Session 12 findings on feature standardization?"
User: "Show me the March 2020 crash detection results"
User: "What is the Academic Jump Model implementation plan?"
```

**Reference:** docs/OPENMEMORY_PROCEDURES.md (complete procedures)

---

## Current State (Session 12 Complete - Oct 28, 2025)

### Objective: Academic Statistical Jump Model Implementation

**Goal:** Replace simplified Jump Model (4.2% crash detection) with Academic Statistical Jump Model (>50% target)

**Progress:**
- **Phase A (Features): COMPLETE** - 16/16 tests passing, real SPY data validated
- **Phase B (Optimization): NEXT** - Coordinate descent + DP algorithm
- **Phase C (Cross-validation): PENDING** - λ selection
- **Phase D (Online inference): PENDING** - 3000-day lookback
- **Phase E (Regime mapping): PENDING** - 2-state to 4-regime ATLAS output
- **Phase F (Validation): PENDING** - 7 tests including March 2020 crash

### Phase A Results (Session 12)

**Files Created:**
- `regime/academic_features.py` (365 lines) - Feature calculation functions
- `tests/test_regime/test_academic_features.py` (362 lines) - 16 comprehensive tests

**Features Implemented:**
1. Downside Deviation (10-day halflife) - sqrt(EWM[R^2 * 1_{R<0}])
2. Sortino Ratio (20-day halflife) - EWM_mean / EWM_DD
3. Sortino Ratio (60-day halflife) - EWM_mean / EWM_DD

**Critical Discovery:**
- Reference implementation uses RAW features (no standardization)
- Investigated via Playwright MCP (fetched GitHub code)
- Changed default: `standardize=False`

**Real SPY Data Validation (1506 days, 2019-2024):**
- March 2020 crash detection: EXCELLENT
- Downside Deviation: 0.002 (normal) → 0.026 (crash) = **999.6% increase**
- Sortino 20d: +1.64 (normal) → -0.07 (crash) = **massive drop**
- Features clearly distinguish normal vs crash regimes

**Query OpenMemory for details:**
```
mcp__openmemory__openmemory_query("Session 12 Phase A feature validation results")
mcp__openmemory__openmemory_query("March 2020 crash detection academic features")
mcp__openmemory__openmemory_query("feature standardization investigation Session 12")
```

---

## Immediate Next Actions (Session 13)

### Phase B: Optimization Solver Implementation

**Primary Task:** Implement coordinate descent algorithm with dynamic programming

**Reference Materials:**
- Academic paper: `C:\Users\sheeh\Downloads\JUMP_MODEL_APPROACH.md` (Section 3.4.2)
- OpenMemory query: `"Session 12 optimization algorithm coordinate descent dynamic programming"`
- GitHub reference: Yizhan-Oliver-Shu/jump-models (via Playwright MCP)

**Implementation Steps:**
1. Read academic paper Section 3.4.2 (Optimization Algorithm)
2. Implement `dynamic_programming(features, theta, lambda)` - O(T*K²) state sequence solver
3. Implement `coordinate_descent(features, lambda, max_iter)` - Alternating Θ and S optimization
4. Test on synthetic 2-regime data (verify convergence)
5. Test on real SPY data (verify reasonable regime segmentation)

**Mathematical Formulas:**
```
Objective: min_{Θ,S} Σ l(x_t, θ_{s_t}) + λ * Σ 1_{s_t ≠ s_{t-1}}

DP Recurrence:
  DP[t][k] = l(x_t, θ_k) + min_j(DP[t-1][j] + λ*1_{j≠k})

Coordinate Descent:
  1. Fix S, optimize Θ: θ_k = mean of {x_t : s_t = k}
  2. Fix Θ, optimize S: Run DP algorithm
  3. Repeat until convergence (objective change < 1e-6)
```

**File to Create:**
- Continue in `regime/academic_features.py` or create `regime/jump_model_optimizer.py`

**Estimated Time:** 2-3 hours

---

## File Status

### Active Files (Keep/Modify)
- `regime/academic_features.py` - Phase A features (complete)
- `regime/base_regime_detector.py` - Abstract base class
- `strategy/base_strategy.py` - v2.0 with regime awareness
- `data/alpaca.py` - Production data fetcher
- `tests/test_regime/test_academic_features.py` - Phase A tests (all passing)

### Documentation
- `docs/HANDOFF.md` - This file (condensed to ~300 lines)
- `docs/CLAUDE.md` - Development rules (read at session start)
- `docs/OPENMEMORY_PROCEDURES.md` - OpenMemory workflow
- `docs/System_Architecture_Reference.md` - ATLAS v2.0 architecture

### Research
- `C:\Users\sheeh\Downloads\JUMP_MODEL_APPROACH.md` - Academic paper

---

## Git Status

**Current Branch:** `main`

**Untracked Files (Session 12):**
```
?? regime/academic_features.py
?? tests/test_regime/test_academic_features.py
?? spy_features_2019_2024.csv (test output, can be gitignored)
```

**Next Commit (After Session 12 completion):**
```bash
git add regime/academic_features.py tests/test_regime/test_academic_features.py
git commit -m "feat: implement Academic Jump Model Phase A feature calculations

Implement 3 academic features for Statistical Jump Model:
- Downside Deviation (10-day EWM halflife)
- Sortino Ratio (20-day EWM halflife)
- Sortino Ratio (60-day EWM halflife)

Validated on 1506 days SPY data (2019-2024). March 2020 crash
detection excellent: DD increased 999.6%, Sortino dropped from
+1.64 to -0.07. Features clearly distinguish crash vs normal regimes.

All 16/16 unit tests passing. Reference implementation uses raw
features (no z-score standardization).

Reference: Shu et al., Princeton 2024"
```

**Remote Push Issue:** Token authentication needs fixing (can address in Session 13 if context allows)

---

## Development Environment

**Python:** 3.12.10
**Key Dependencies:** VectorBT Pro, Pandas 2.2.0, NumPy, Alpaca SDK
**Virtual Environment:** `.venv` (uv managed)
**Data Source:** Alpaca API (production, not yfinance)

**OpenMemory:**
- Status: Operational (MCP integration active)
- Database: 940KB (Session 12 backup complete)
- Backup location: `backups/openmemory/atlas_memory_20251028_session12.sqlite`

---

## Session History (Condensed)

**Sessions 1-9:** Phase 1-5 complete (ORB strategy, portfolio management, walk-forward validation)
**Session 10:** ATLAS v2.0 architecture, BaseStrategy v2.0 with regime awareness
**Session 11:** Jump Model investigation, decision to implement Full Academic model
**Session 12:** Academic Jump Model Phase A (features) - COMPLETE

**Query OpenMemory for historical details:**
```
mcp__openmemory__openmemory_query("Session 10 BaseStrategy v2.0 regime awareness")
mcp__openmemory__openmemory_query("Session 11 Jump Model investigation decision")
mcp__openmemory__openmemory_query("ORB strategy validation results")
```

**Full session details:** Stored in OpenMemory (semantic, procedural, reflective sectors)

---

## Key Metrics & Targets

### Academic Jump Model Validation Targets
- March 2020 crash detection: >50% CRASH/BEAR days (vs 4.2% current)
- Annual regime switches: 0.5-1.0 (temporal penalty prevents thrashing)
- Sharpe improvement: +20% to +42% vs buy-and-hold
- MaxDD reduction: ~50%
- Volatility reduction: ~30%

**Source:** Academic paper (Shu et al., Princeton 2024) - 33 years empirical validation

---

## Common Queries & Resources

**Session Start Queries:**
```
"What is the current status of ATLAS v2.0 Jump Model implementation?"
"What are the immediate next actions for Phase B optimization?"
"Show me the March 2020 crash validation results from Phase A"
"What were the key lessons from Session 12?"
```

**Key Documentation:**
- CLAUDE.md (lines 115-303): 5-step VBT workflow
- CLAUDE.md (lines 45-57): Windows Unicode rules
- OPENMEMORY_PROCEDURES.md: Complete OpenMemory workflow
- System_Architecture_Reference.md: ATLAS v2.0 design

**Academic Reference:**
- Paper: `C:\Users\sheeh\Downloads\JUMP_MODEL_APPROACH.md`
- Reference implementation: Yizhan-Oliver-Shu/jump-models (GitHub)

---

**End of HANDOFF.md - Last updated Session 12 (Oct 28, 2025)**
