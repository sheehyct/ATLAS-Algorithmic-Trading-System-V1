"""
Verify TradingView data matches the user's chart
TradingView uses different adjustment methodology than Alpaca
"""
import vectorbtpro as vbt
import pandas as pd

print("Fetching SPY data from TradingView...")
print("=" * 70)

# Fetch SPY data from TradingView for October 2023
# TVData uses 'limit' instead of start/end - fetch last 500 daily bars to get Oct 2023
# SPY needs exchange specification for TradingView
tv_data = vbt.TVData.pull(
    "AMEX:SPY",  # SPY is listed on NYSE Arca (shown as AMEX on TradingView)
    timeframe="1d",
    limit=500  # Get enough history to include Oct 2023
)

print("\nOctober 2023 SPY Data from TradingView:")
print("=" * 70)

# Get OHLCV data
ohlcv = tv_data.get()
print(ohlcv)

print("\n" + "=" * 70)
print("COMPARISON WITH YOUR CHART:")
print("=" * 70)

# Your chart values
chart_values = {
    "2023-10-04": {"high": 436.49, "low": 425.43},
    "2023-10-05": {"high": 435.47, "low": 421.17},
    "2023-10-13": {"high": 437.09, "low": 429.96}
}

for date_str, expected in chart_values.items():
    print(f"\n{date_str}:")
    try:
        # Convert string date to datetime
        target_date = pd.to_datetime(date_str)

        # Find matching row
        matching_rows = ohlcv[ohlcv.index.date == target_date.date()]

        if not matching_rows.empty:
            row = matching_rows.iloc[0]
            print(f"  TV Data:    HIGH=${row['High']:.2f}, LOW=${row['Low']:.2f}")
            print(f"  Your Chart: HIGH=${expected['high']:.2f}, LOW=${expected['low']:.2f}")

            # Check if they match
            high_diff = abs(row['High'] - expected['high'])
            low_diff = abs(row['Low'] - expected['low'])

            if high_diff < 0.10 and low_diff < 0.10:
                print(f"  Status: PERFECT MATCH")
            elif high_diff < 1.00 and low_diff < 1.00:
                print(f"  Status: CLOSE (within $1)")
            else:
                print(f"  Status: MISMATCH - Diff: HIGH=${high_diff:.2f}, LOW=${low_diff:.2f}")
        else:
            print(f"  No data for this date")

    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 70)
print("BAR CLASSIFICATION CHECK:")
print("=" * 70)

# Check if Oct 5 is correctly an inside bar
try:
    oct4_rows = ohlcv[ohlcv.index.date == pd.to_datetime("2023-10-04").date()]
    oct5_rows = ohlcv[ohlcv.index.date == pd.to_datetime("2023-10-05").date()]

    if not oct4_rows.empty and not oct5_rows.empty:
        oct4 = oct4_rows.iloc[0]
        oct5 = oct5_rows.iloc[0]

        print(f"Oct 4: HIGH=${oct4['High']:.2f}, LOW=${oct4['Low']:.2f}")
        print(f"Oct 5: HIGH=${oct5['High']:.2f}, LOW=${oct5['Low']:.2f}")

        # Check classification
        if oct5['High'] < oct4['High'] and oct5['Low'] > oct4['Low']:
            print("Oct 5 Classification: 1 (INSIDE BAR) - CORRECT")
        elif oct5['High'] > oct4['High'] and oct5['Low'] >= oct4['Low']:
            print("Oct 5 Classification: 2U (BULLISH) - WRONG")
        elif oct5['High'] <= oct4['High'] and oct5['Low'] < oct4['Low']:
            print("Oct 5 Classification: 2D (BEARISH) - WRONG")
        else:
            print("Oct 5 Classification: 3 (OUTSIDE) - WRONG")

except Exception as e:
    print(f"Error in classification: {e}")

print("\n" + "=" * 70)
print("CONCLUSION:")
print("If TradingView data matches your chart, we need to switch")
print("from Alpaca to TradingView as our data source for backtesting.")
