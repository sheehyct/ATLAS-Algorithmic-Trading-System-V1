"""
Portfolio Manager Validation with ORB Strategy

This example demonstrates PortfolioManager integration with the ORB strategy,
showing circuit breaker triggers and risk management in action.

Usage:
    uv run python examples/validate_portfolio_manager_orb.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategies.orb import ORBStrategy, ORBConfig
from core.portfolio_manager import PortfolioManager
from utils.portfolio_heat import PortfolioHeatManager
from core.risk_manager import RiskManager


def main():
    """Run ORB strategy through PortfolioManager."""

    print("="*70)
    print("PORTFOLIO MANAGER VALIDATION: ORB STRATEGY")
    print("="*70)

    # Initialize ORB strategy
    print("\n1. Initializing ORB Strategy...")
    orb_config = ORBConfig(
        name="ORB_NVDA",
        symbol="NVDA",
        opening_minutes=5,  # 5-minute opening range (validated in Session 8)
        atr_stop_multiplier=2.5,
        volume_multiplier=2.0,  # 2.0x volume threshold (validated)
        start_date="2024-01-01",
        end_date="2024-06-30"
    )

    orb_strategy = ORBStrategy(orb_config)
    print(f"   Strategy: {orb_strategy.get_strategy_name()}")
    print(f"   Symbol: {orb_config.symbol}")
    print(f"   Opening Range: {orb_config.opening_minutes} minutes")

    # Initialize risk management components
    print("\n2. Initializing Risk Management...")
    heat_manager = PortfolioHeatManager(max_heat=0.08)  # 8% max heat
    risk_manager = RiskManager(
        max_portfolio_heat=0.08,
        max_position_risk=0.02
    )
    print(f"   Max Portfolio Heat: {heat_manager.max_heat:.0%}")
    print(f"   Max Position Risk: {risk_manager.max_position_risk:.0%}")
    print(f"   Circuit Breakers: 10% (WARNING), 15% (REDUCE), 20% (HALT)")

    # Create PortfolioManager
    print("\n3. Creating PortfolioManager...")
    pm = PortfolioManager(
        strategies=[orb_strategy],
        capital=10000,
        heat_manager=heat_manager,
        risk_manager=risk_manager
    )
    print(f"   Initial Capital: ${pm.capital:,.2f}")
    print(f"   Strategies: {len(pm.strategies)}")

    # Fetch data
    print("\n4. Fetching Market Data...")
    data_5min, data_daily = orb_strategy.fetch_data()
    print(f"   5-min Bars: {len(data_5min)}")
    print(f"   Daily Bars: {len(data_daily)}")
    print(f"   Period: {data_5min.index[0]} to {data_5min.index[-1]}")
    print(f"   Columns: {list(data_5min.columns)}")

    # Run backtest through PortfolioManager
    # Note: ORB strategy's backtest() internally uses both data_5min and data_daily
    # but PortfolioManager.run_single_strategy_with_gates() calls strategy.backtest()
    # which will call fetch_data() again. For now, we pass data_5min to show intent.
    print("\n5. Running Backtest with Integrated Risk Management...")
    results = pm.run_single_strategy_with_gates(
        strategy=orb_strategy,
        data=data_5min,
        initial_capital=10000
    )

    # Display summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    print(f"\nPerformance:")
    print(f"  Final Equity:    ${results['final_equity']:,.2f}")
    print(f"  Total Return:    {results['metrics']['total_return']:.2%}")
    print(f"  Sharpe Ratio:    {results['metrics']['sharpe_ratio']:.2f}")
    print(f"  Max Drawdown:    {results['drawdown_max']:.2%}")

    print(f"\nTrade Statistics:")
    print(f"  Total Trades:    {results['metrics']['total_trades']:.0f}")
    if results['metrics']['total_trades'] > 0:
        print(f"  Win Rate:        {results['metrics']['win_rate']:.2%}")
        print(f"  Avg Trade:       {results['metrics']['avg_trade']:.2%}")

    print(f"\nRisk Management:")
    print(f"  Circuit Breakers: {len(results['circuit_breaker_triggers'])} triggered")
    print(f"  Trading Halted:   {'YES' if results['trading_halted'] else 'NO'}")

    if results['circuit_breaker_triggers']:
        print(f"\nCircuit Breaker Details:")
        for date, threshold, action in results['circuit_breaker_triggers']:
            print(f"  {date.date()}: {threshold:.0%} DD -> {action}")

    # Get final portfolio status
    status = pm.get_portfolio_status()
    print(f"\nFinal Portfolio Status:")
    print(f"  Current Equity:   ${status['current_equity']:,.2f}")
    print(f"  Peak Equity:      ${status['peak_equity']:,.2f}")
    print(f"  Current DD:       {status['current_drawdown']:.2%}")
    print(f"  Trading Enabled:  {status['trading_enabled']}")
    print(f"  Risk Multiplier:  {status['risk_multiplier']:.1f}x")

    print("\n" + "="*70)
    print("[SUCCESS] PortfolioManager validation complete!")
    print("="*70)

    return results


if __name__ == "__main__":
    main()
