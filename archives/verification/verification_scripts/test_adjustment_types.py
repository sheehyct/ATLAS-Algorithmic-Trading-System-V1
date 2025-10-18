"""
Test different adjustment types to see which matches the chart
"""
import vectorbtpro as vbt
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
load_dotenv(config_path)

# Configure Alpaca credentials
vbt.AlpacaData.set_custom_settings(
    client_config=dict(
        api_key=os.getenv('ALPACA_MID_KEY'),
        secret_key=os.getenv('ALPACA_MID_SECRET')
    )
)

print("Testing different adjustment parameters for SPY...")
print("=" * 70)

# Test different adjustment types
adjustment_types = ["all", "raw", "split", "dividend", None]

for adj_type in adjustment_types:
    print(f"\nAdjustment = '{adj_type}':")
    print("-" * 40)

    try:
        # Fetch with specific adjustment
        if adj_type is None:
            spy_data = vbt.AlpacaData.pull(
                "SPY",
                start="2023-10-04",
                end="2023-10-06",
                timeframe="1 day"
            )
        else:
            spy_data = vbt.AlpacaData.pull(
                "SPY",
                start="2023-10-04",
                end="2023-10-06",
                timeframe="1 day",
                adjustment=adj_type
            )

        # Get OHLCV
        ohlcv = spy_data.get()

        # Show Oct 4 and Oct 5
        for idx, row in ohlcv.iterrows():
            date_str = idx.strftime('%Y-%m-%d')
            print(f"  {date_str}: HIGH=${row['High']:.2f}, LOW=${row['Low']:.2f}")

    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 70)
print("YOUR CHART VALUES:")
print("Oct 4: HIGH=$436.49, LOW=$425.43")
print("Oct 5: HIGH=$435.47, LOW=$421.17")

print("\n" + "=" * 70)
print("ANALYSIS:")
print("The ~$21 difference suggests cumulative dividend adjustments.")
print("SPY pays dividends quarterly (~$1.50-$1.80 per share)")
print("Over 3+ years that could account for the $21 difference")