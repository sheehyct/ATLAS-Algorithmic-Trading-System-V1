from data.alpaca import fetch_alpaca_data
import pandas as pd
from datetime import datetime

print("VERIFYING ADJUSTED DATA ACROSS ALL TIMEFRAMES")
print("=" * 70)
print("\nFetching fresh SPY data with adjustment='all'...")

# Fetch hourly data (which gets resampled to other timeframes in the test)
# Need 730 days to get back to October 2023
hourly = fetch_alpaca_data('SPY', '1H', 730)
daily = fetch_alpaca_data('SPY', '1D', 730)

print("\n" + "=" * 70)
print("OCTOBER 2023 COMPARISON (Key dates from your chart):")
print("=" * 70)

# Check specific October dates
oct_dates = ['2023-10-04', '2023-10-05', '2023-10-13']

for date in oct_dates:
    try:
        d_data = daily.loc[date]
        print(f"\n{date}:")
        print(f"  HIGH: ${d_data['high']:.2f}")
        print(f"  LOW:  ${d_data['low']:.2f}")
        print(f"  OPEN: ${d_data['open']:.2f}")
        print(f"  CLOSE:${d_data['close']:.2f}")
    except:
        print(f"\n{date}: No data")

print("\n" + "=" * 70)
print("YOUR CHART VALUES (from screenshot):")
print("=" * 70)
print("Oct 4: HIGH = $436.49")
print("Oct 5: HIGH = $435.47 (shown as '1' - Inside bar)")
print("Oct 13: HIGH = $437.09, LOW = $429.96")

print("\n" + "=" * 70)
print("VERIFICATION:")
print("=" * 70)
print("If our fetched data matches your chart values above,")
print("then the dividend adjustment fix is working correctly.")