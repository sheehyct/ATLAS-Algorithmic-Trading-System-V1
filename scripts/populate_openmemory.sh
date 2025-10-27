#!/bin/bash
# ATLAS OpenMemory Population Script
# Usage: ./scripts/populate_openmemory.sh session8
#
# Purpose: Populate OpenMemory with structured facts from development sessions
# Following hybrid HANDOFF.md + OpenMemory approach

API_URL="http://localhost:8080/memory/add"
AUTH_TOKEN="atlas_openmemory_dev_token_2025"

# Function to add memory
add_memory() {
    local content="$1"
    local sector_hint="$2"
    local metadata="$3"

    curl -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $AUTH_TOKEN" \
      -d "{
        \"content\": \"$content\",
        \"tags\": [\"$sector_hint\", \"session8\", \"orb\"],
        \"metadata\": $metadata
      }"

    echo "" # Newline for readability
}

# Session 8: ORB Empirical Validation
SESSION=8
DATE="2025-10-24"
PHASE="Phase3"

echo "Populating Session 8 ORB Empirical Validation memories..."
echo "=============================================="
echo ""

# Episodic: Test activities
echo "[1/17] Adding NVDA 5-min ORB test results..."
add_memory \
  "Tested NVDA ORB with 5-min opening range over 6 months (Jan-Jun 2024): 33 trades, 54.5% win rate, +2.51% return, Sharpe 0.13" \
  "episodic" \
  "{\"session\": $SESSION, \"date\": \"$DATE\", \"strategy\": \"ORB\", \"symbol\": \"NVDA\", \"test_period\": \"6_months\"}"

echo "[2/17] Adding NVDA 30-min ORB test results..."
add_memory \
  "Tested NVDA ORB with 30-min opening range: 32 trades, 37.5% win rate, +0.01% return, Sharpe 0.00" \
  "episodic" \
  "{\"session\": $SESSION, \"date\": \"$DATE\", \"strategy\": \"ORB\", \"symbol\": \"NVDA\", \"parameter\": \"opening_range_30min\"}"

echo "[3/17] Adding TSLA ORB test results..."
add_memory \
  "Tested TSLA ORB 5-min range: 32 trades, 40.6% win rate, -3.94% return - UNPROFITABLE" \
  "episodic" \
  "{\"session\": $SESSION, \"date\": \"$DATE\", \"strategy\": \"ORB\", \"symbol\": \"TSLA\", \"result\": \"unprofitable\"}"

echo "[4/17] Adding AAPL ORB test results..."
add_memory \
  "Tested AAPL ORB 5-min range: 22 trades, 18.2% win rate, -4.01% return - UNPROFITABLE" \
  "episodic" \
  "{\"session\": $SESSION, \"date\": \"$DATE\", \"strategy\": \"ORB\", \"symbol\": \"AAPL\", \"result\": \"unprofitable\"}"

# Semantic: Validated facts
echo "[5/17] Adding opening range parameter validation..."
add_memory \
  "5-min opening range outperforms 30-min range by 251x in returns on NVDA" \
  "semantic" \
  "{\"session\": $SESSION, \"finding_type\": \"parameter_validation\", \"parameter\": \"opening_range\", \"optimal_value\": \"5min\"}"

echo "[6/17] Adding volume threshold validation..."
add_memory \
  "Volume threshold 2.0x superior to 1.5x: 2.4x better returns, higher win rate (54.5% vs 43.6%)" \
  "semantic" \
  "{\"session\": $SESSION, \"finding_type\": \"parameter_validation\", \"parameter\": \"volume_threshold\", \"optimal_value\": \"2.0x\"}"

echo "[7/17] Adding win rate metric..."
add_memory \
  "ORB win rate on NVDA: 54.5% (exceeds specification target of 15-25%)" \
  "semantic" \
  "{\"session\": $SESSION, \"metric\": \"win_rate\", \"value\": 0.545, \"status\": \"exceeds_target\"}"

echo "[8/17] Adding Sharpe ratio metric..."
add_memory \
  "ORB Sharpe ratio on NVDA: 0.13 (below specification target of 2.0)" \
  "semantic" \
  "{\"session\": $SESSION, \"metric\": \"sharpe_ratio\", \"value\": 0.13, \"target\": 2.0, \"status\": \"below_target\"}"

# Procedural: Workflows and rules
echo "[9/17] Adding symbol selection rule..."
add_memory \
  "Always test ORB strategy on volatile stocks, not stable indices like SPY" \
  "procedural" \
  "{\"session\": $SESSION, \"rule_type\": \"symbol_selection\", \"strategy\": \"ORB\"}"

echo "[10/17] Adding testing best practice..."
add_memory \
  "Use session-scoped pytest fixtures to reduce API calls during testing" \
  "procedural" \
  "{\"session\": $SESSION, \"rule_type\": \"testing_best_practice\", \"component\": \"tests/conftest.py\"}"

echo "[11/17] Adding VBT verification workflow..."
add_memory \
  "Follow 5-step VBT Pro verification workflow before implementing any VBT feature" \
  "procedural" \
  "{\"session\": $SESSION, \"rule_type\": \"development_workflow\", \"critical\": true}"

# Reflective: Insights and lessons
echo "[12/17] Adding symbol-specific insight..."
add_memory \
  "ORB strategy is symbol-specific: works on NVDA but fails on TSLA and AAPL - requires selective universe screening" \
  "reflective" \
  "{\"session\": $SESSION, \"insight_type\": \"strategy_limitation\", \"strategy\": \"ORB\"}"

echo "[13/17] Adding validation period concern..."
add_memory \
  "6 months may be insufficient validation period - NVDA results could be lucky period" \
  "reflective" \
  "{\"session\": $SESSION, \"insight_type\": \"validation_concern\", \"recommendation\": \"test_longer_period\"}"

echo "[14/17] Adding performance gap insight..."
add_memory \
  "Specification targets (Sharpe >2.0, R:R >3:1) not met - may need optimization or longer period" \
  "reflective" \
  "{\"session\": $SESSION, \"insight_type\": \"performance_gap\", \"strategy\": \"ORB\"}"

# Emotional: User preferences and concerns
echo "[15/17] Adding accuracy priority preference..."
add_memory \
  "User mandate: accuracy over speed every time" \
  "emotional" \
  "{\"session\": $SESSION, \"preference_type\": \"development_priority\"}"

echo "[16/17] Adding zero trades concern..."
add_memory \
  "User concerned about zero trades issue from past sessions" \
  "emotional" \
  "{\"session\": $SESSION, \"concern_type\": \"bug_recurrence\"}"

echo "[17/17] Adding RTH filtering requirement..."
add_memory \
  "MANDATORY: All data must be filtered to NYSE regular trading hours before resampling to prevent phantom weekend/holiday bars" \
  "procedural" \
  "{\"session\": $SESSION, \"rule_type\": \"data_filtering\", \"critical\": true, \"component\": \"data_pipeline\"}"

echo ""
echo "=============================================="
echo "Session 8 memories populated successfully!"
echo "Total memories added: 17"
echo ""
echo "Verify with:"
echo "curl -X POST http://localhost:8080/memory/query -H \"Content-Type: application/json\" -d '{\"query\": \"Session 8 ORB validation\", \"filters\": {\"session\": 8}}'"
