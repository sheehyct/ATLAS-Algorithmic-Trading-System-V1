# Documentation Index

**Last Updated:** October 18, 2025
**Current Branch:** `feature/risk-management-foundation`
**Purpose:** Navigate the workspace documentation efficiently

**MAJOR UPDATE (Oct 18):** Research documentation consolidated - see Research Documentation section

---

## Quick Start: What to Read First

### New to This Project?
1. **`CLAUDE.md`** - Working relationship, mandatory rules, brutal honesty policy
2. **`research/diagnostic_framework.md`** - How we identify and categorize failures
3. **`research/Medium_Articles_Research_Findings.md`** - Professional vs retail approach
4. **`HANDOFF.md`** - Current session status and next steps

### Continuing Development?
1. **`HANDOFF.md`** - Current status, recent changes, what's next
2. **`active/risk-management-foundation/`** - Current branch implementation docs
3. **VBT Pro documentation** (when uncertain about integration)

### Understanding Past Decisions?
1. **`archives/baseline-ma-rsi/README.md`** - Why we pivoted from previous approach
2. **`history/ARCHIVE_HISTORY.md`** - Session-by-session development timeline
3. **`research/`** - Timeless principles and research findings

---

## Documentation Structure

```
docs/
├── README.md (this file)
├── CLAUDE.md
├── HANDOFF.md
├── System_Architecture_Reference.md
├── active/
│   └── risk-management-foundation/
│       ├── GATE1_RESULTS.md
│       ├── VBT_INTEGRATION_PATTERNS.md
│       ├── WEEK1_EXECUTIVE_BRIEF.md
│       ├── WEEK2_HANDOFF.md
│       └── PROJECT_AUDIT_2025-10-16.md
├── archives/
│   └── baseline-ma-rsi/
│       ├── README.md
│       ├── ARCHIVED_HANDOFF_Oct11.md
│       ├── POSITION_SIZING_VERIFICATION.md
│       ├── STRATEGY_1_BASELINE_RESULTS.md
│       ├── STRATEGY_OVERVIEW.md
│       ├── IMPLEMENTATION_PLAN.md
│       └── BRANCH_COMPARISON.md
├── research/
│   ├── CONSOLIDATED_RESEARCH.md (NEW - Oct 18)
│   ├── Medium_Articles_Research_Findings.md
│   ├── VALIDATION_PROTOCOL.md
│   ├── STRATEGY_2_IMPLEMENTATION_ADDENDUM.md
│   ├── algo_trading_diagnostic_framework.md
│   └── ARCHIVE/
│       ├── README.md (explains consolidation)
│       ├── Advanced_Algorithmic_Trading_Systems.md
│       ├── Algorithmic Trading System.md
│       ├── Algorithmic trading systems with asymmetric risk-reward profiles.md
│       ├── CRITICAL_POSITION_SIZING_CLARIFICATION.md
│       └── STRATEGY_ANALYSIS_AND_DESIGN_SPEC.md
└── history/
    └── ARCHIVE_HISTORY.md
```

---

## Main Documentation (Root Folder)

### CLAUDE.md
**Category:** Timeless Rules
**Read when:** Starting any session
**Purpose:** Working relationship, mandatory workflows, brutal honesty policy

**Key sections:**
- VectorBT Pro documentation workflow (MANDATORY)
- NYSE market hours filtering (CRITICAL)
- Position sizing quality gates
- File management policy (DELETE, don't archive)
- Context management triggers

**Updated:** October 1, 2025

---

### HANDOFF.md
**Category:** Active Session State
**Read when:** Starting/ending sessions
**Purpose:** Current development status, next steps, recent decisions

**Contains:**
- Current branch and task
- Critical findings from previous session
- Immediate action items with human review gates
- File status (keep/delete/create)
- Context window management

**Updated:** Continuously (every session)

---

### INFRASTRUCTURE_CAPABILITIES.md (ARCHIVED Oct 16, 2025)
**Location:** `archives/baseline-ma-rsi/INFRASTRUCTURE_CAPABILITIES_Oct9.md`
**Reason:** Documented pre-pivot strategy plan (MA+RSI first, ORB second, TFC third)
**Archived because:** Strategic pivot to risk-management-foundation changed development order

**See instead:**
- Current capabilities: Documented in VectorBT Pro Official Documentation
- Current architecture: `docs/System_Architecture_Reference.md`

---

## Active Documentation (Current Branch)

### active/risk-management-foundation/
**Purpose:** Implementation docs for current branch

**Planned contents:**
- `RISK_MANAGEMENT_PLAN.md` - Overall approach and phases
- `GMM_REGIME_IMPLEMENTATION.md` - Regime detection specifics
- `PORTFOLIO_HEAT_SPEC.md` - Portfolio-wide risk constraints
- `VBT_INTEGRATION_PATTERNS.md` - Verified VBT integration patterns

**Status:** Directory created, files to be added during implementation

---

## Archived Documentation (Historical Branches)

### archives/baseline-ma-rsi/
**Archived:** October 12, 2025
**Reason:** Strategic pivot to risk-management-first approach

**READ THE README FIRST:** `archives/baseline-ma-rsi/README.md`

**Key documents:**

#### ARCHIVED_HANDOFF_Oct11.md
Snapshot of session state when pivot occurred. Shows:
- Position sizing bug discovery (81.8% mean position size)
- Decision to pause and re-evaluate approach
- Awaiting human review

#### POSITION_SIZING_VERIFICATION.md (20 pages)
Mathematical analysis of position sizing bug:
- Formula correct but missing capital constraint
- 43% discrepancy between theoretical and actual risk
- Implications for all future strategies
- Options for fixing (capital-constrained recommended)

#### STRATEGY_1_BASELINE_RESULTS.md
Actual backtest results:
- 3.86% total return vs 54.41% SPY buy-hold
- Sharpe 0.22 (FAIL - target 0.8-1.2)
- Mean reversion wrong for 2021-2025 bull market
- Why RSI exits cut winners short

#### STRATEGY_OVERVIEW.md
Two-branch approach description:
- Branch 1: TFC confidence scoring (experimental)
- Branch 2: MA+RSI baseline (proven)
- Performance expectations and failure criteria

#### IMPLEMENTATION_PLAN.md (1100 lines)
Step-by-step build guide for both branches:
- Phase 1: Environment setup
- Phase 2: Baseline implementation
- Phase 3: TFC confidence implementation
- Phase 4: Comparison and validation
- Phase 5: Paper trading deployment

#### BRANCH_COMPARISON.md
TFC vs Baseline analysis:
- Complexity comparison
- Parameter count (6+ for TFC = overfitting risk)
- Research validation (baseline proven, TFC unproven)
- Decision matrix

**Why preserved:** Negative results are valuable. Documents what DOESN'T work.

---

## Research Documentation (Timeless Reference)

### CONSOLIDATED_RESEARCH.md (NEW - October 18, 2025)
**Source:** Consolidation of 5 research documents
**Purpose:** Single authoritative reference resolving all contradictions
**Lines:** 813 (was 3,176 across 5 files)

**MAJOR UPDATE:** This document consolidates and resolves contradictions from:
- Advanced_Algorithmic_Trading_Systems.md
- Algorithmic Trading System.md
- Algorithmic trading systems with asymmetric risk-reward profiles.md
- CRITICAL_POSITION_SIZING_CLARIFICATION.md
- STRATEGY_ANALYSIS_AND_DESIGN_SPEC.md

**7 Contradictions Resolved:**
1. Volume confirmation: 1.5x vs 2.0x → RESOLVED: 2.0x MANDATORY
2. Position sizing risk_pct: 2% (docs) vs 1% (empirical) → RESOLVED: 1% recommended
3. Sharpe targets: 0.8 vs 2.0 vs 2.396 → RESOLVED: Phased (backtest >2.0, paper >0.8, live >0.5)
4. R:R minimums: 2:1 vs 3:1 → RESOLVED: 3:1 minimum
5. TFC approach: Scoring vs abandonment → RESOLVED: Scoring ABANDONED, classification KEPT
6. Position sizing methods: When to use which → RESOLVED: ATR for ORB, others for future
7. Market hours filtering: Implicit vs explicit → RESOLVED: MANDATORY with code examples

**Use when:**
- Implementing new features (check relevant section first)
- Debugging (check "What NOT To Do" section)
- Performance issues (check targets and red flags)
- Quick reference (comprehensive tables at end)

**Read sequence:**
1. CONSOLIDATED_RESEARCH.md for practical guidance
2. Medium_Articles_Research_Findings.md for deep theory
3. VALIDATION_PROTOCOL.md for testing methodology
4. STRATEGY_2_IMPLEMENTATION_ADDENDUM.md for ORB specifics

**Status:** Authoritative (all contradictions resolved with rationale)

---

### Medium_Articles_Research_Findings.md
**Source:** Cross-validation of 11 Medium articles
**Purpose:** Foundational cross-validated research (THE PRIMARY REFERENCE)

**CRITICAL SECTION - READ FIRST:** Part 0 Addendum (Philosophical Foundation)

**Mindset validation checklist:**
- Accept expectancy > win rate (30% @ 5:1 R:R beats 70% @ 1:1)
- ABANDON TFC scoring (not "fix" it - 6+ parameters = overfitting)
- Comfortable with 40-50% cash allocation
- Cut mean-reversion losers at 2-3 days (not 14)
- Enforce 6-8% portfolio heat limit (no exceptions)
- Build 5+ strategies (not perfect one strategy)

**Technical concepts (after mindset correction):**
1. GMM regime detection (Sharpe 0.63→1.00 proven)
2. Asymmetric risk measurement (downside semi-volatility)
3. 5-day washout mean reversion (replaces RSI logic)
4. Portfolio heat management (6-8% max total exposure)

**Cross-validation:** Opus 4.1, Desktop Sonnet 4.5, Web Sonnet 4.5 consensus

**Never changes:** Mathematical principles are timeless
**NOT consolidated:** This is the source of truth

---

### VALIDATION_PROTOCOL.md (700 lines)
**Purpose:** Testing methodology to prevent 44% failure rate

**5 phases:**
1. Unit testing (Week 1)
2. Backtest validation (Weeks 2-3)
3. Walk-forward analysis (Weeks 4-5)
4. Paper trading (Months 3-8)
5. Live trading (Month 9+)

**Red flags:**
- Backtest Sharpe > 3.0 (overfitted)
- Win rate > 90% (too good to be true)
- Large train-test gap (doesn't generalize)

**Use when:** Validating any strategy before deployment

**Never changes:** Validation principles are universal
**NOT consolidated:** Complete standalone protocol

---

### STRATEGY_2_IMPLEMENTATION_ADDENDUM.md
**Source:** Claude Desktop critical corrections
**Purpose:** ORB-specific implementation requirements

**6 critical corrections:**
1. Volume confirmation 2.0× MANDATORY (not optional)
2. Sharpe targets DOUBLED (min 2.0, not 1.0)
3. R:R minimum RAISED to 3:1 (not 2:1)
4. NEW: Expectancy analysis (mandatory)
5. NEW: STRAT-lite bias filter (optional)
6. ATR 3.0× testing emphasized

**Use when:** Implementing ORB strategy

**NOT consolidated:** Strategy-specific guidance

---

### algo_trading_diagnostic_framework.md
**Source:** Claude Desktop analysis
**Purpose:** Failure mode taxonomy

**Use when:** Things break (which they will)

**Categories:**
- Data/Implementation failures
- Framework mismatch failures
- Overfitting failures
- Edge erosion failures
- Translation failures (visual → code)

**Key question:** "If I ran this with real money tomorrow, would I trust it?"

**Never changes:** Failure modes are universal
**NOT consolidated:** Diagnostic reference

---

### ARCHIVE/ (Consolidated Files - October 18, 2025)

**See:** docs/research/ARCHIVE/README.md for complete consolidation details

**Archived files (DO NOT USE for current development):**
- Advanced_Algorithmic_Trading_Systems.md (136 lines)
- Algorithmic Trading System.md (69 lines)
- Algorithmic trading systems with asymmetric risk-reward profiles.md (145 lines)
- CRITICAL_POSITION_SIZING_CLARIFICATION.md (687 lines)
- STRATEGY_ANALYSIS_AND_DESIGN_SPEC.md (2139 lines)

**Reason:** Contained contradictions, 60%+ redundancy, superseded by CONSOLIDATED_RESEARCH.md

**Historical value:** Preserved for reference, show evolution of understanding

**For current work:** USE CONSOLIDATED_RESEARCH.md instead

---

## Historical Timeline

### history/ARCHIVE_HISTORY.md
**Purpose:** Session-by-session development log

**Contains:**
- September 2025 development sessions
- Phase completions (TFC data pipeline, multi-timeframe classification)
- Critical discoveries (Saturday bar bug, market hours alignment)
- Component development timeline

**Use when:** Understanding how we got to current state

**Format:** Chronological log with accomplishments, next steps, validation commands

---

## Navigation Patterns

### "I need to implement X" → Where do I look?

**VectorBT Pro integration:**
1. `VectorBT Pro Official Documentation/README.md` (ALWAYS START HERE)
2. LLM Docs folder (PRIORITY search)
3. Python introspection (`vbt.phelp()`)
4. If still unclear → `active/risk-management-foundation/VBT_INTEGRATION_PATTERNS.md`

**Risk management:**
1. `research/Medium_Articles_Research_Findings.md` (mindset first)
2. `research/CONSOLIDATED_RESEARCH.md` (practical implementation guidance)
3. `active/risk-management-foundation/` (current implementation)
4. `archives/baseline-ma-rsi/POSITION_SIZING_VERIFICATION.md` (what NOT to do)

**Strategy research:**
1. `research/CONSOLIDATED_RESEARCH.md` (authoritative practical guide)
2. `research/STRATEGY_2_IMPLEMENTATION_ADDENDUM.md` (ORB specifics)
3. `research/Medium_Articles_Research_Findings.md` (mathematical foundations)

**Validation:**
1. `research/VALIDATION_PROTOCOL.md` (5-phase testing methodology)
2. `research/algo_trading_diagnostic_framework.md` (when things fail)

---

### "Why did we abandon X?" → Where do I look?

**Why abandon TFC confidence scoring?**
→ `research/Medium_Articles_Research_Findings.md` (Part 0 Addendum + cross-validation)

**Why abandon baseline-ma-rsi branch?**
→ `archives/baseline-ma-rsi/README.md` (comprehensive explanation)

**Why 81.8% position sizing was wrong?**
→ `archives/baseline-ma-rsi/POSITION_SIZING_VERIFICATION.md` (20-page analysis)

**Why mean reversion failed?**
→ `archives/baseline-ma-rsi/STRATEGY_1_BASELINE_RESULTS.md` (actual results)

---

### "What should I do next?" → Where do I look?

**Immediate next steps:**
→ `HANDOFF.md` (current session status and action items)

**Implementation roadmap:**
→ `active/risk-management-foundation/` (current branch plan)

**Long-term strategy:**
→ `research/Medium_Articles_Research_Findings.md` (4-week roadmap at end)

---

## Document Maintenance Rules

### When to Update

**HANDOFF.md:**
- Every session (start and end)
- When critical findings occur
- When decisions are made

**active/ folder:**
- When implementing features
- When discovering VBT patterns
- When documenting design decisions

**research/ folder:**
- NEVER (timeless references don't change)
- Exception: If new research findings emerge, add NEW files (don't modify existing)

**archives/ folder:**
- NEVER (historical documents are frozen)
- Exception: Can add new archives for abandoned branches

**history/ folder:**
- At end of major phases
- When reaching significant milestones
- Chronological append-only (never edit past entries)

---

### When to Archive

**Archive a branch when:**
- Strategic pivot occurs
- Approach is abandoned based on findings
- Branch becomes historical reference (not actively developed)

**Archive process:**
1. Create `archives/branch-name/` directory
2. Move all branch-specific docs
3. Create comprehensive `README.md` explaining:
   - What was tested
   - Why it was abandoned
   - Key findings (positive and negative)
   - Lessons learned
   - Related active work
4. Update `DOCUMENTATION_INDEX.md` (this file)
5. Update `HANDOFF.md` to reflect new state

**DO NOT:**
- Delete archived docs (preserve negative results)
- Archive timeless research (keep in `research/`)
- Archive session history (keep in `history/`)

---

## Cross-References

**Position sizing:**
- Failed approach: `archives/baseline-ma-rsi/POSITION_SIZING_VERIFICATION.md`
- Correct approach: `research/Medium_Articles_Research_Findings.md` (Concept 2)
- Implementation: `active/risk-management-foundation/` (to be created)

**TFC methodology:**
- Original intent: `archives/baseline-ma-rsi/STRATEGY_OVERVIEW.md`
- Why abandoned: `research/Medium_Articles_Research_Findings.md` (Executive Summary)
- Working TFC code: `core/analyzer.py` (still valid for STRAT classification)

**Regime detection:**
- Research basis: `research/Medium_Articles_Research_Findings.md` (Concept 1)
- GMM approach: Yang-Zhang volatility + SMA crossover
- Implementation: `active/risk-management-foundation/GMM_REGIME_IMPLEMENTATION.md` (to be created)

**Validation:**
- Protocol: `research/VALIDATION_PROTOCOL.md`
- Diagnostic framework: `research/diagnostic_framework.md`
- Past validation example: `archives/baseline-ma-rsi/STRATEGY_1_BASELINE_RESULTS.md`

---

## File Naming Conventions

**Active docs:** `FEATURE_NAME.md` or `COMPONENT_SPEC.md`
**Research docs:** Descriptive names, underscores for spaces
**Archived docs:** Original names preserved (with README.md for context)
**History docs:** `ARCHIVE_HISTORY.md` (chronological append)

**All caps for:** Main index files (HANDOFF, CLAUDE, README)
**Title case for:** Specific features and components

---

## Questions?

**"I can't find X documentation"**
→ Check this index, use Ctrl+F to search

**"Documentation seems outdated"**
→ Check `HANDOFF.md` for current state
→ Archived docs are frozen (intentionally outdated for historical reference)

**"Should I create new documentation?"**
→ Active development: Add to `active/current-branch/`
→ Timeless research: Consult team before adding to `research/`
→ Session notes: Update `HANDOFF.md`

**"How do I navigate VBT documentation?"**
→ `VectorBT Pro Official Documentation/README.md` (comprehensive guide)
→ `CLAUDE.md` (mandatory VBT workflow section)

---

**Last Updated:** October 18, 2025
**Major Update:** Research documentation consolidated (5 files → 1 authoritative CONSOLIDATED_RESEARCH.md)
**Maintained By:** Claude Code (updated every session)
**Version Control:** Git tracks all changes to this file
