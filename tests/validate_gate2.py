"""
Gate 2 Validation Script

Demonstrates portfolio heat management in a realistic trading scenario.

Scenario:
1. Start with $100,000 capital, 8% heat limit
2. Attempt to open 5 positions with 2% risk each (10% total risk)
3. Verify 4 positions accepted (8% heat), 5th rejected
4. Close 1 position, verify heat drops to 6%
5. Verify new position now accepted

Expected Result:
- First 4 positions accepted
- 5th position REJECTED (would exceed 8% heat limit)
- After closing position, 6th position ACCEPTED
- Gate 2 PASSED: Portfolio heat never exceeds 8%
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.portfolio_heat import PortfolioHeatManager


def print_separator():
    """Print visual separator."""
    print("\n" + "=" * 70 + "\n")


def validate_gate2():
    """Run Gate 2 validation scenario."""

    print_separator()
    print("GATE 2 VALIDATION: Portfolio Heat Management")
    print_separator()

    # Initialize
    capital = 100000
    heat_manager = PortfolioHeatManager(max_heat=0.08)
    risk_per_position = 2000  # 2% of capital

    print(f"Initial Capital: ${capital:,}")
    print(f"Max Portfolio Heat: {heat_manager.max_heat:.1%}")
    print(f"Risk per Position: ${risk_per_position:,} ({risk_per_position/capital:.1%})")

    # Attempt to add 5 positions
    symbols = ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI']

    print_separator()
    print("PHASE 1: Attempting to Add 5 Positions (2% risk each)")
    print_separator()

    accepted_count = 0
    rejected_count = 0

    for i, symbol in enumerate(symbols, 1):
        print(f"\nPosition {i}: {symbol}")
        print(f"  Proposed Risk: ${risk_per_position:,}")

        # Check if trade accepted
        accepted = heat_manager.can_accept_trade(symbol, risk_per_position, capital)

        if accepted:
            heat_manager.add_position(symbol, risk_per_position)
            current_heat = heat_manager.calculate_current_heat(capital)
            print(f"  Status: ACCEPTED")
            print(f"  Portfolio Heat: {current_heat:.1%}")
            accepted_count += 1
        else:
            print(f"  Status: REJECTED")
            rejected_count += 1

    # Summary after Phase 1
    print_separator()
    print("PHASE 1 SUMMARY")
    print_separator()

    final_heat_phase1 = heat_manager.calculate_current_heat(capital)
    position_count_phase1 = heat_manager.get_position_count()

    print(f"Positions Accepted: {accepted_count}")
    print(f"Positions Rejected: {rejected_count}")
    print(f"Active Positions: {position_count_phase1}")
    print(f"Portfolio Heat: {final_heat_phase1:.1%}")

    # Validate Phase 1 expectations
    assert accepted_count == 4, f"Expected 4 accepted, got {accepted_count}"
    assert rejected_count == 1, f"Expected 1 rejected, got {rejected_count}"
    assert final_heat_phase1 == 0.08, f"Expected 8% heat, got {final_heat_phase1:.1%}"

    print("\n[PASS] Phase 1: Heat limit enforced correctly")

    # Phase 2: Close position and add new one
    print_separator()
    print("PHASE 2: Close Position and Add New Position")
    print_separator()

    close_symbol = 'SPY'
    print(f"\nClosing Position: {close_symbol}")
    heat_manager.remove_position(close_symbol)

    heat_after_close = heat_manager.calculate_current_heat(capital)
    positions_after_close = heat_manager.get_position_count()

    print(f"  Portfolio Heat After Close: {heat_after_close:.1%}")
    print(f"  Active Positions: {positions_after_close}")

    assert heat_after_close == 0.06, f"Expected 6% heat, got {heat_after_close:.1%}"
    assert positions_after_close == 3, f"Expected 3 positions, got {positions_after_close}"

    # Attempt to add new position
    new_symbol = 'AAPL'
    print(f"\nAdding New Position: {new_symbol}")
    print(f"  Proposed Risk: ${risk_per_position:,}")

    accepted = heat_manager.can_accept_trade(new_symbol, risk_per_position, capital)

    if accepted:
        heat_manager.add_position(new_symbol, risk_per_position)
        final_heat_phase2 = heat_manager.calculate_current_heat(capital)
        print(f"  Status: ACCEPTED")
        print(f"  Portfolio Heat: {final_heat_phase2:.1%}")
    else:
        print(f"  Status: REJECTED")
        final_heat_phase2 = heat_manager.calculate_current_heat(capital)

    assert accepted is True, "Expected new position to be accepted"
    assert final_heat_phase2 == 0.08, f"Expected 8% heat, got {final_heat_phase2:.1%}"

    print("\n[PASS] Phase 2: Position replacement working correctly")

    # Final Summary
    print_separator()
    print("GATE 2 VALIDATION RESULT")
    print_separator()

    final_positions = heat_manager.get_active_positions()

    print(f"Final Portfolio Heat: {final_heat_phase2:.1%}")
    print(f"Active Positions: {heat_manager.get_position_count()}")
    print("\nActive Position Details:")
    for symbol, risk in final_positions.items():
        print(f"  {symbol}: ${risk:,} at risk ({risk/capital:.1%})")

    # Validate all constraints met
    max_heat_observed = final_heat_phase2
    assert max_heat_observed <= 0.08, f"Heat exceeded limit: {max_heat_observed:.1%}"

    print_separator()
    print("[PASS] GATE 2 VALIDATION COMPLETE")
    print_separator()

    print("\nValidation Summary:")
    print("  [PASS] Portfolio heat never exceeded 8% limit")
    print("  [PASS] Trades rejected when limit would be exceeded")
    print("  [PASS] Heat recalculated correctly after position close")
    print("  [PASS] New trades accepted after heat reduction")

    print("\n" + "=" * 70)
    print("GATE 2: PASSED")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    try:
        validate_gate2()
    except AssertionError as e:
        print(f"\n[FAIL] Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        sys.exit(1)
