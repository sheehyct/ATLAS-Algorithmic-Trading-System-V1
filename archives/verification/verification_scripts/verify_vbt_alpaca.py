"""
Verify Alpaca data using VectorBT Pro's built-in AlpacaData class
This is the CORRECT way to fetch adjusted data
"""
import vectorbtpro as vbt
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
config_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
load_dotenv(config_path)

# Configure Alpaca credentials for VectorBT Pro
print("Setting up VectorBT Pro AlpacaData with credentials...")
vbt.AlpacaData.set_custom_settings(
    client_config=dict(
        api_key=os.getenv('ALPACA_MID_KEY'),
        secret_key=os.getenv('ALPACA_MID_SECRET'),
        raw_data=False  # Important: Use adjusted data by default
    )
)

print("\nFetching SPY data for October 2023 using VectorBT Pro...")
print("=" * 70)

# Fetch SPY data for October 2023 with proper adjustment
spy_data = vbt.AlpacaData.pull(
    "SPY",
    start="2023-10-01",
    end="2023-10-15",
    timeframe="1 day",
    adjustment="all"  # Critical: Use dividend/split adjusted prices
)

print("\nOctober 2023 SPY Data (PROPERLY ADJUSTED):")
print("=" * 70)

# Get the OHLCV data
ohlcv = spy_data.get()
print(ohlcv)

print("\n" + "=" * 70)
print("SPECIFIC DATES FROM YOUR CHART:")
print("=" * 70)

# Check specific dates
dates_to_check = {
    "2023-10-04": {"high": 436.49, "low": 425.43},
    "2023-10-05": {"high": 435.47, "low": 421.17},  # Should be INSIDE bar (1)
    "2023-10-13": {"high": 437.09, "low": 429.96}
}

for date_str, expected in dates_to_check.items():
    print(f"\n{date_str}:")
    try:
        # Find the row for this date
        matching_rows = ohlcv[ohlcv.index.date == pd.to_datetime(date_str).date()]
        if not matching_rows.empty:
            row = matching_rows.iloc[0]
            print(f"  Our Data:  HIGH=${row['High']:.2f}, LOW=${row['Low']:.2f}")
            print(f"  Your Chart: HIGH=${expected['high']:.2f}, LOW=${expected['low']:.2f}")

            # Check if they match (within $0.50 tolerance for rounding)
            high_diff = abs(row['High'] - expected['high'])
            low_diff = abs(row['Low'] - expected['low'])

            if high_diff < 0.50 and low_diff < 0.50:
                print(f"  ✅ MATCH!")
            else:
                print(f"  ❌ MISMATCH! Diff: HIGH=${high_diff:.2f}, LOW=${low_diff:.2f}")
    except Exception as e:
        print(f"  Error checking date: {e}")

print("\n" + "=" * 70)
print("BAR CLASSIFICATION CHECK:")
print("=" * 70)

# Classify October 5 specifically
try:
    oct4 = ohlcv[ohlcv.index.date == pd.to_datetime("2023-10-04").date()].iloc[0]
    oct5 = ohlcv[ohlcv.index.date == pd.to_datetime("2023-10-05").date()].iloc[0]

    print(f"\nOct 4: HIGH=${oct4['High']:.2f}, LOW=${oct4['Low']:.2f}")
    print(f"Oct 5: HIGH=${oct5['High']:.2f}, LOW=${oct5['Low']:.2f}")

    if oct5['High'] < oct4['High'] and oct5['Low'] > oct4['Low']:
        print("Oct 5 Classification: 1 (INSIDE BAR) ✅ CORRECT!")
    elif oct5['High'] > oct4['High'] and oct5['Low'] >= oct4['Low']:
        print("Oct 5 Classification: 2U (BULLISH) ❌ WRONG!")
    else:
        print(f"Oct 5 Classification: UNKNOWN")

except Exception as e:
    print(f"Error classifying bars: {e}")