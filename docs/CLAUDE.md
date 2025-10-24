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

## MANDATORY: Read HANDOFF.md First

**CRITICAL RULE**: Before ANY work in ANY session, ALWAYS read:
```
C:\Strat_Trading_Bot\vectorbt-workspace\docs\HANDOFF.md
```

**HANDOFF.md contains:**
- Current session state and progress
- Recent changes and decisions
- What's working vs broken
- Immediate next steps
- File status (keep/delete/create)

**Never skip this step. Current state context prevents wasted work.**

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

## MANDATORY: VectorBT Pro Implementation Workflow

**THE RULE: VERIFY BEFORE IMPLEMENTING**

Every VBT Pro feature implementation MUST follow this 5-step process:

### STEP 1: SEARCH (No Assumptions)

Use MCP tools to search VBT documentation before writing ANY code:

```python
# Use mcp__vectorbt-pro__search for general queries
mcp__vectorbt-pro__search(
    query="position sizing risk management from_signals",
    asset_names=["examples", "api", "docs"],  # Search order matters
    search_method="hybrid",
    max_tokens=2000
)
```

**Asset Types:**
- "api" - API reference (best for specific API queries)
- "docs" - General documentation (best for concepts)
- "messages" - Discord discussions (best for support queries)
- "examples" - Code examples (best for practical implementation)

**Search Tips:**
- Use 2-4 substantive keywords
- Start with "hybrid" search method
- Check examples first, then API docs
- Don't include "VectorBT Pro" in query (implied)

### STEP 2: VERIFY API (Exact Methods)

Verify that classes and methods actually exist:

```python
# Verify references are valid
mcp__vectorbt-pro__resolve_refnames(
    refnames=["vbt.Portfolio", "vbt.PF", "vbt.Portfolio.from_signals"]
)

# Output format:
# OK vbt.Portfolio vectorbtpro.portfolio.base.Portfolio
# OK vbt.PF vectorbtpro.portfolio.base.Portfolio
# OK vbt.Portfolio.from_signals vectorbtpro.portfolio.base.Portfolio.from_signals
```

**List available methods:**

```python
# See what's available on a class
mcp__vectorbt-pro__get_attrs(
    refname="vbt.Portfolio",
    own_only=False,
    incl_types=True,
    incl_private=False
)

# Look for:
# - from_signals [classmethod]
# - total_return [property]
# - sharpe_ratio [property]
```

### STEP 3: FIND EXAMPLES (Real Usage)

Find how others use the API:

```python
# Find real-world examples
mcp__vectorbt-pro__find(
    refnames=["vbt.Portfolio.from_signals"],
    asset_names=["examples", "messages"],
    aggregate_messages=True,  # Get full thread context
    max_tokens=2000
)
```

**Look for patterns:**
- How is size parameter specified? (pd.Series? np.array?)
- What are common parameter combinations?
- How do examples handle edge cases?

### STEP 4: TEST MINIMAL EXAMPLE (Prove It Works)

Test VBT integration BEFORE full implementation:

```python
# Use mcp__vectorbt-pro__run_code to test
mcp__vectorbt-pro__run_code(
    code="""
import vectorbtpro as vbt
import pandas as pd
import numpy as np

# Minimal test data
np.random.seed(42)
close = pd.Series(100 + np.cumsum(np.random.randn(100)))
entries = pd.Series([True] + [False]*99)
exits = pd.Series([False]*99 + [True])
sizes = pd.Series([10.0]*100)

# Test VBT integration
pf = vbt.PF.from_signals(
    close=close,
    entries=entries,
    exits=exits,
    size=sizes,
    size_type='amount',
    init_cash=10000
)

print(f"Total Return: {pf.total_return:.2%}")
print(f"Sharpe Ratio: {pf.sharpe_ratio:.2f}")
print("SUCCESS: VBT accepts this format")
""",
    restart=False
)
```

**CRITICAL:** If this test fails, DO NOT proceed to full implementation.

### STEP 5: IMPLEMENT (Only After Verification)

ONLY after steps 1-4 are complete:
1. Write the full implementation
2. Use the EXACT data format from step 4
3. Add error handling for edge cases
4. Test with real data

## ENFORCEMENT

**ZERO TOLERANCE for skipping this workflow.**

If you skip ANY step, the implementation WILL fail and waste time debugging.

**Consequences of skipping:**
- STEP 1 skipped: Assume methods that don't exist
- STEP 2 skipped: Use wrong method signatures
- STEP 3 skipped: Reinvent working patterns incorrectly
- STEP 4 skipped: Discover incompatibility after full implementation
- STEP 5 without 1-4: 90% chance of failure

## When to Consult QuantGPT

If after completing steps 1-4 you are still uncertain:
1. VBT documentation unclear or contradictory
2. Multiple valid approaches found
3. Edge case handling not documented
4. Performance optimization needed

**Ask specific questions with context from steps 1-4.**

## Example: Implementing Position Sizing

**CORRECT Workflow:**

```
1. SEARCH: "position sizing risk management from_signals"
   Result: Found vbt.Portfolio.from_signals with size parameter

2. VERIFY: mcp__vectorbt-pro__get_attrs("vbt.Portfolio.from_signals")
   Result: size parameter exists, accepts pd.Series

3. FIND: mcp__vectorbt-pro__find(["vbt.Portfolio.from_signals"], ["examples"])
   Result: Examples show size as pd.Series of share counts

4. TEST: Minimal example with pd.Series([10, 10, 10, ...])
   Result: Works! Returns valid portfolio

5. IMPLEMENT: Full position sizing with ATR calculations
   Result: Success on first try
```

**INCORRECT Workflow (DON'T DO THIS):**

```
1. Assume vbt.Portfolio has a position_sizing parameter
2. Write full implementation
3. Test
4. Get error: "position_sizing parameter doesn't exist"
5. Search documentation to debug
6. Rewrite implementation
7. Test again
8. Repeat...

Result: Wasted 2 hours vs 30 minutes with correct workflow
```

## CRITICAL: STRICT NYSE Market Hours Rule

**MANDATORY FOR ALL BACKTESTS AND DATA PROCESSING:**

**THE RULE:**
ALL data MUST be filtered to NYSE regular trading hours (weekdays only, excluding holidays) BEFORE any resampling or analysis. Failure to do this creates phantom bars on weekends/holidays leading to invalid trades and backtests.

**IMPLEMENTATION REQUIREMENTS:**
1. Filter weekends using: `vbt.utils.calendar.is_weekday(df.index)`
2. Filter NYSE holidays using: `pandas_market_calendars` library
3. Apply BOTH filters BEFORE resampling hourly to daily data
4. Verify no Saturday/Sunday bars exist in final dataset
5. Verify no holiday bars exist (Christmas, Thanksgiving, etc.)

**WHY THIS IS CRITICAL:**
- Alpaca API can return midnight bars on Saturdays from Friday extended hours
- Pandas resample creates phantom bars if weekends/holidays not filtered
- Phantom bars create false patterns and invalid trade signals
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

## Development Standards

### Session Start Routine

**MANDATORY FIRST STEPS:**

```bash
# 1. Read HANDOFF.md (ALWAYS FIRST)
cat C:\Strat_Trading_Bot\vectorbt-workspace\docs\HANDOFF.md

# 2. Read CLAUDE.md (this file - refresh development rules)
cat C:\Strat_Trading_Bot\vectorbt-workspace\docs\CLAUDE.md

# 3. Verify VectorBT Pro accessible
uv run python -c "import vectorbtpro as vbt; print(f'VBT Pro {vbt.__version__} loaded')"

# 4. Check environment
uv run python -c "import pandas as pd; import numpy as np; print('Environment OK')"

# 5. Review current task from HANDOFF.md "Next Actions" section
```

## MANDATORY Quality Gates

Before claiming ANY functionality works:

1. **Test it**: Run the actual code
2. **Verify output**: Check the results are correct
3. **Measure performance**: Back claims with numbers
4. **Check VBT compliance**: Use proper vectorization where possible
5. **Document evidence**: Show actual output

**ZERO TOLERANCE for unverified claims**

## Verification Gate: Volume Confirmation

**MANDATORY FOR ALL PRICE BREAKOUT STRATEGIES**

All breakout strategies (ORB, range breakouts, etc.) MUST include volume confirmation.

**THE RULE:**
Entry signals require minimum 2.0x average volume threshold.

**WHY THIS IS MANDATORY:**
- Research evidence: Breakouts with 2x volume achieve ~53% success rates
- Without volume confirmation: significantly higher failure rate
- Reduces false signals and improves R:R ratio
- Industry standard for professional breakout systems

**IMPLEMENTATION PATTERN:**

```python
def generate_signals(self, data: pd.DataFrame) -> dict:
    """Generate entry signals with MANDATORY volume confirmation."""

    # Price breakout signal
    price_breakout_long = data['Close'] > opening_high

    # CRITICAL: Volume confirmation (MANDATORY)
    volume_ma_20 = data['Volume'].rolling(20).mean()
    volume_surge = data['Volume'] > (volume_ma_20 * 2.0)  # 2.0x threshold

    # Entry signals (volume confirmation REQUIRED)
    long_entries = price_breakout_long & volume_surge

    return {
        'long_entries': long_entries,
        'volume_confirmed': volume_surge,  # Track for analysis
        'volume_ma': volume_ma_20
    }
```

**VERIFICATION CHECKLIST:**

After backtest, verify volume confirmation is working:

```python
# Verify 100% of entries have volume confirmation
trades = pf.trades.records_readable
volume_confirmed_rate = trades['volume_surge'].sum() / len(trades)

print(f"Volume confirmation rate: {volume_confirmed_rate:.1%}")
assert volume_confirmed_rate >= 0.95, "Volume filter not working correctly"
```

**REJECTION CRITERIA:**

If a breakout strategy does NOT include volume confirmation:
- REJECT the implementation
- Request addition of 2.0x volume filter
- Re-verify after correction

**NOT OPTIONAL. NOT A PARAMETER TO OPTIMIZE.**

The 2.0x threshold is based on research and MUST be hardcoded.

## Integration with OpenAI_VBT Development Guides

The following guides provide detailed workflows for tool selection and implementation:

**Tool Selection and Usage:**
- `docs/OpenAI_VBT/RESOURCE_UTILIZATION_GUIDE.md`
  - Decision tree: Which resource to use
  - VBT MCP tools (search, find, get_attrs, get_source, run_code)
  - API provider selection (OpenAI for VBT embeddings, Claude Max for dev)
  - Filesystem operations (read HANDOFF.md first!)
  - Project documentation hierarchy (TIER 1-4)

**Practical Implementation:**
- `docs/OpenAI_VBT/PRACTICAL_DEVELOPMENT_EXAMPLES.md`
  - Session startup pattern (mandatory first steps)
  - VBT API discovery workflow (6-step process)
  - Implementing new strategy components
  - Debugging VBT integration issues
  - Data pipeline development
  - Risk management implementation

**Navigation:**
- `docs/OpenAI_VBT/DEVELOPMENT_GUIDES_OVERVIEW.md`
  - Quick reference for guide usage
  - Integration with existing documentation
  - Tool selection matrix
  - Critical rules summary

**CRITICAL:** These guides complement the 5-step VBT workflow above.

**Workflow Integration:**
1. Use RESOURCE_UTILIZATION_GUIDE.md decision tree to select the right tool
2. Follow PRACTICAL_DEVELOPMENT_EXAMPLES.md for implementation patterns
3. Reference DEVELOPMENT_GUIDES_OVERVIEW.md for quick lookups
4. Always follow the 5-step VBT verification workflow for ANY VBT feature

**Example Integration:**

```
Task: Implement ATR-based position sizing

Step 1: Check RESOURCE_UTILIZATION_GUIDE.md decision tree
        -> "Need to understand VBT API" -> Use VBT MCP tools

Step 2: Follow 5-step VBT workflow (from this file)
        -> SEARCH, VERIFY, FIND, TEST, IMPLEMENT

Step 3: Reference PRACTICAL_DEVELOPMENT_EXAMPLES.md Section 3
        -> "Implementing New Strategy Component"
        -> Follow the 6-step pattern with code examples

Step 4: Test minimal example using patterns from guides

Step 5: Implement full code

Result: Correct implementation on first try
```

## Context Management

### MANDATORY Handoff Triggers
- Context window >50%: Prepare handoff
- Context window >70%: MANDATORY handoff to HANDOFF.md
- Complex changes >10 files: STOP and simplify
- Repeating questions: Sign of context fatigue

### File Management Policy
- DELETE redundant files, don't archive
- Keep <15 core Python files
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

## Account Trading Constraints

**Schwab Level 1 Options Approval - Strategy Impact**

The live trading account has Schwab Level 1 options approval (cash account, no margin).

**Constraint Summary:**
- CAN trade: Long stock, long calls/puts, cash-secured puts, long straddles/strangles
- CANNOT: Short stock, short options (naked or covered), credit/debit spreads

**Strategy Compatibility:**
- Currently implemented ORB strategy: FULLY COMPATIBLE (long-only)
- Future strategies: Some will require modification or replacement

**Detailed Analysis:**
See HANDOFF.md "Account Constraints (Schwab Level 1 Options Approval)" section for:
- Complete capability matrix
- Strategy-by-strategy compatibility assessment
- Level 1-compatible alternatives for incompatible strategies

**Future Development Approach:**
When reaching implementation of strategies requiring shorts or spreads:
1. Use Playwright MCP to research Level 1-compatible alternatives
2. Evaluate relative strength rotation vs pairs trading
3. Consider long puts for directional bearish exposure
4. Assess inverse ETF tracking error vs long puts

**Reference:** HANDOFF.md Session 7 brainstorming, MCP_SETUP.md for Playwright usage

## DO NOT

1. Create new dashboard files (VBT native plotting sufficient)
2. Add test files before fixing production
3. Use pickle.dump (use vbt.save if needed)
4. Skip VBT Pro documentation
5. Make assumptions without verification
6. Create complex solutions when simple ones exist
7. Archive files instead of deleting them
8. Generate synthetic market data
9. Use emojis or special characters in ANY output
10. Skip reading HANDOFF.md at session start
11. NEVER skip the 5-step VBT verification workflow
12. NEVER deliver VBT code without testing with run_code()
13. NEVER claim something "should work" without proof

## Key Reference Documents

**TIER 1 - Read Every Session:**
- `docs/HANDOFF.md` - Current state (READ FIRST)
- `docs/CLAUDE.md` - This file (development rules)

**TIER 2 - Reference When Needed:**
- `docs/System_Architecture_Reference.md` - System design
- `docs/OpenAI_VBT/RESOURCE_UTILIZATION_GUIDE.md` - Tool selection
- `docs/OpenAI_VBT/PRACTICAL_DEVELOPMENT_EXAMPLES.md` - Implementation patterns
- `VectorBT Pro Official Documentation/README.md` - VBT navigation

**TIER 3 - Strategy-Specific:**
- `docs/research/STRATEGY_2_IMPLEMENTATION_ADDENDUM.md` - ORB requirements
- `docs/research/algo_trading_diagnostic_framework.md` - Debugging strategies
- `docs/research/CONSOLIDATED_RESEARCH.md` - Research findings

**TIER 4 - Deep Research:**
- `docs/research/VALIDATION_PROTOCOL.md` - Testing methodology
- `docs/research/ARCHIVE/` - Failed attempts (valuable learning)

## Summary: Critical Workflows

### Every Session:
```
1. Read HANDOFF.md (mandatory first step)
2. Read CLAUDE.md sections 1-7 (refresh rules)
3. Verify environment (VBT, dependencies)
4. Check Next Actions in HANDOFF.md
5. Plan approach (which files to modify, what to test)
```

### Every VBT Implementation:
```
1. SEARCH documentation (mcp__vectorbt-pro__search)
2. VERIFY API exists (resolve_refnames, get_attrs)
3. FIND examples (mcp__vectorbt-pro__find)
4. TEST minimal example (mcp__vectorbt-pro__run_code)
5. IMPLEMENT full code (only after 1-4 pass)
6. DOCUMENT findings in HANDOFF.md
```

### Every Claim:
```
1. Test the code (actually run it)
2. Verify output (check results are correct)
3. Measure performance (back with numbers)
4. Show evidence (paste actual output)
5. Document in HANDOFF.md
```

### Zero Tolerance Items:
- Emojis or special characters in ANY output
- Skipping HANDOFF.md at session start
- Skipping VBT verification workflow (5 steps)
- Claiming code works without testing
- Creating breakout strategies without volume confirmation
- Assuming VBT methods exist without verification

---

**Last Updated:** October 18, 2025 - ATLAS Project
**Version:** 2.0 - Post-STRAT Migration
**Status:** PRODUCTION - All STRAT references removed
