---
title: Data
description: Recipes for working with data in VectorBT PRO
icon: material/database
---

# :material-database: Data

!!! question
    Learn more in the [Data documentation](https://vectorbt.pro/pvt_6d1b3986/documentation/data/).

There are many supported data sources available for OHLC and indicator data. For the complete list,
see the [custom](https://vectorbt.pro/pvt_6d1b3986/api/data/custom/) module.

## Listing

Many data classes offer a class method to list all symbols that can be fetched. Typically, this method
starts with `list_`, such as
[TVData.list_symbols](https://vectorbt.pro/pvt_6d1b3986/api/data/custom/tv/#vectorbtpro.data.custom.tv.TVData.list_symbols),
[SQLData.list_tables](https://vectorbt.pro/pvt_6d1b3986/api/data/custom/sql/#vectorbtpro.data.custom.sql.SQLData.list_tables), or
[CSVData.list_paths](https://vectorbt.pro/pvt_6d1b3986/api/data/custom/csv/#vectorbtpro.data.custom.csv.CSVData.list_paths).
Most of these methods also support client-side filtering of symbols using glob-style or regex-style patterns.

```python title="How to list symbols"
all_symbols = vbt.BinanceData.list_symbols()  # (1)!
usdt_symbols = vbt.BinanceData.list_symbols("*USDT")  # (2)!
usdt_symbols = vbt.BinanceData.list_symbols(r"^.+USDT$", use_regex=True)

all_symbols = vbt.TVData.list_symbols()  # (3)!
nasdaq_symbols = vbt.TVData.list_symbols(exchange_pattern="NASDAQ")  # (4)!
btc_symbols = vbt.TVData.list_symbols(symbol_pattern="BTC*")  # (5)!
pl_symbols = vbt.TVData.list_symbols(market="poland")  # (6)!
usdt_symbols = vbt.TVData.list_symbols(fields=["currency"], filter_by=["USDT"])  # (7)!

def filter_by(market_cap_basic):
    if market_cap_basic is None:
        return False
    return market_cap_basic >= 1_000_000_000_000

trillion_symbols = vbt.TVData.list_symbols(  # (8)!
    fields=["market_cap_basic"], 
    filter_by=vbt.RepFunc(filter_by)
)

all_paths = vbt.FileData.list_paths()  # (9)!
csv_paths = vbt.CSVData.list_paths()  # (10)!
all_csv_paths = vbt.CSVData.list_paths("**/*.csv")  # (11)!
all_data_paths = vbt.HDFData.list_paths("data.h5")  # (12)!
all_paths = vbt.HDFData.list_paths()  # (13)!

all_schemas = vbt.SQLData.list_schemas(engine=engine)  # (14)!
all_tables = vbt.SQLData.list_tables(engine=engine)  # (15)!
```

1. List all Binance symbols.
2. List Binance symbols ending with "USDT".
3. List all TradingView symbols.
4. List TradingView symbols traded on NASDAQ.
5. List TradingView symbols starting with "BTC".
6. List TradingView symbols traded in Poland.
7. List TradingView symbols traded in USD currency.
8. List TradingView symbols with a market capitalization of 1 trillion or more.
9. List all files in the current directory.
10. List CSV files in the current directory.
11. List CSV files in the current directory and all subdirectories.
12. List all keys in the HDF file "data.h5".
13. List all keys in all HDF files in the current directory.
14. List all schemas in a SQL database.
15. List all tables in a SQL database.

## Pulling

Each data class provides a `fetch_symbol()` method to fetch a single symbol and return raw data, typically
as a DataFrame. To return a data instance, use the `pull()` method, which accepts one or more symbols,
calls `fetch_symbol()` for each, and aligns all DataFrames. For testing purposes, use
[YFData](https://vectorbt.pro/pvt_6d1b3986/api/data/custom/yf/#vectorbtpro.data.custom.yf.YFData), which is easy to use but lower in quality.
For production, use more reliable data sources like
[CCXTData](https://vectorbt.pro/pvt_6d1b3986/api/data/custom/ccxt/#vectorbtpro.data.custom.ccxt.CCXTData) for crypto and
[AlpacaData](https://vectorbt.pro/pvt_6d1b3986/api/data/custom/alpaca/#vectorbtpro.data.custom.alpaca.AlpacaData) for stocks.
For technical analysis using the latest data, use
[TVData](https://vectorbt.pro/pvt_6d1b3986/api/data/custom/tv/#vectorbtpro.data.custom.tv.TVData) (TradingView).

!!! hint
    To check which arguments a data class like `YFData` accepts, use `vbt.phelp(vbt.YFData.fetch_symbol)`.

```python title="How to fetch data"
data = vbt.YFData.pull("AAPL")  # (1)!
data = vbt.YFData.pull(["AAPL", "MSFT"])  # (2)!
data = vbt.YFData.pull("AAPL", start="2020")  # (3)!
data = vbt.YFData.pull("AAPL", start="2020", end="2021")  # (4)!
data = vbt.YFData.pull("AAPL", start="1 month ago")  # (5)!
data = vbt.YFData.pull("AAPL", start="1 month ago", timeframe="hourly")  # (6)!
data = vbt.YFData.pull("AAPL", tz="UTC")  # (7)!
data = vbt.YFData.pull(symbols, execute_kwargs=dict(engine="threadpool"))  # (8)!

data = vbt.YFData.pull("AAPL", auto_adjust=False)  # (9)!
data = vbt.BinanceData.pull("BTCUSDT", klines_type="futures")  # (10)!
data = vbt.CCXTData.pull("BTCUSDT", exchange="binanceusdm")  # (11)!
data = vbt.BinanceData.pull("BTCUSDT", tld="us")  # (12)!
data = vbt.TVData.pull("CRYPTOCAP:TOTAL")  # (13)!
```

1. Pull all data for one symbol. Note that some data classes will only return a subset of data by default.
2. Pull all data for multiple symbols. Symbols will be fetched sequentially (one after another).
3. Pull data starting from 2020-01-01 (inclusive). Dates can be strings, `datetime` objects,
or `pd.Timestamp` objects. Dates are assigned the same timezone as the ticker, unless specified otherwise.
4. Pull data between 2020-01-01 (inclusive) and 2021-01-01 (exclusive).
5. Pull data starting 1 month ago. Both `start` and `end` support human-readable string inputs.
6. Pull hourly data starting 1 month ago. Timeframes also support human-readable strings.
7. Pull all data and convert to the UTC timezone. Use this when tickers have different timezones.
8. Pull multiple symbols in parallel. Note that many data providers enforce strict API rate limits,
which could lead to a ban if exceeded.
9. Disable auto-adjustment.
10. Pull BTC/USDT futures data from Binance.
11. Same as above, but using CCXT.
12. Pass `tld` if using an exchange from the US, Japan, or other TLDs.
13. Pull [Crypto Total Market Cap](https://www.tradingview.com/chart/r7sfuYga/?symbol=CRYPTOCAP%3ATOTAL).

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To provide different keyword arguments for different symbols, either pass an argument as a
[symbol_dict](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.symbol_dict), or pass a dictionary with keyword
arguments keyed by symbol as the first argument.

```python title="How to provide keyword arguments by symbol"
data = vbt.TVData.pull(
    ["SPX", "NDX", "VIX"],
    exchange=vbt.symbol_dict({"SPX": "SP", "NDX": "NASDAQ", "VIX": "CBOE"})
)
data = vbt.TVData.pull({  # (1)!
    "SPX": dict(exchange="SP"),
    "NDX": dict(exchange="NASDAQ"),
    "VIX": dict(exchange="CBOE")
})
data = vbt.TVData.pull(["SP:SPX", "NASDAQ:NDX", "CBOE:VIX"])  # (2)!
```

1. Same as above.
2. Same as above, but now symbols include their exchange as a prefix.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

If your data provider requires credentials and you want to fetch multiple symbols, the client will be
created for each symbol, leading to multiple authentications and slower execution.
To avoid this, create the client beforehand and pass it to the `fetch()` method.

```python title="Create a Data client in advance"
client = vbt.TVData.resolve_client(username="YOUR_USERNAME", password="YOUR_PASSWORD")
```

```python title="Use the Data client"
data = vbt.TVData.pull(["NASDAQ:AAPL", "NASDAQ:MSFT"], client=client)

# ______________________________________________________________

vbt.TVData.set_custom_settings(client=client)
data = vbt.TVData.pull(["NASDAQ:AAPL", "NASDAQ:MSFT"])
```

## Persisting

Once fetched, data can be saved in several ways. The most common and recommended approach is to
pickle the data, which saves the entire object, including the arguments used during fetching.
Other options include CSV files ([Data.to_csv](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.to_csv)),
HDF files ([Data.to_hdf](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.to_hdf)), and more.
These methods save only the data itself, not the associated metadata, such as the timeframe.

```python title="How to save data"
data.save()  # (1)!
data.save(compression="blosc")  # (2)!

data.to_csv("data", mkdir_kwargs=dict(mkdir=True))  # (3)!
data.to_csv("AAPL.csv")  # (4)!
data.to_csv("AAPL.tsv", sep="\t")  # (5)!
data.to_csv(vbt.symbol_dict(AAPL="AAPL.csv", MSFT="MSFT.csv"))  # (6)!
data.to_csv(vbt.RepEval("symbol + '.csv'"))  # (7)!

data.to_hdf("data")  # (8)!
data.to_hdf("data.h5")  # (9)!
data.to_hdf("data.h5", key=vbt.RepFunc(lambda symbol: symbol.replace(" ", "_")))  # (10)!
data.to_hdf("data.h5", key=vbt.RepFunc(lambda symbol: "stocks/" + symbol))  # (11)!
data.to_hdf(vbt.RepEval("symbol + '.h5'"), key="df")  # (12)!

data.to_parquet("data")  # (13)!
data.to_parquet(vbt.symbol_dict(
    AAPL="data/AAPL.parquet", 
    MSFT="data/MSFT.parquet"
))  # (14)!
data.to_parquet("data", partition_by="Y")  # (15)!
data.to_parquet(vbt.symbol_dict(
    AAPL="data/AAPL", 
    MSFT="data/MSFT"
), partition_by="Y")  # (16)!

data.to_sql(engine="sqlite:///data.db")  # (17)!
data.to_sql(engine="postgresql+psycopg2://postgres:admin@localhost:5432/data")  # (18)!
data.to_sql(engine=engine, schema="yahoo")  # (19)!
data.to_sql(engine=engine, table=vbt.symbol_dict(AAPL="AAPL", MSFT="MSFT"))  # (20)!
data.to_sql(engine=engine, if_exists="replace")  # (21)!
data.to_sql(engine=engine, attach_row_number=True)  # (22)!
data.to_sql(
    engine=engine, 
    attach_row_number=True, 
    row_number_column="RN",
    from_row_number=vbt.symbol_dict(AAPL=100, MSFT=200), 
    if_exists="append"
)  # (23)!
```

1. Serialize and save to a pickle file (recommended). The filename will be
`{class_name}.pickle`, such as "YFData.pickle".
2. Serialize, compress, and save to a pickle file using the specified compression algorithm.
3. Save one CSV file per symbol in the "data" directory. If the directory does not exist, it will be created.
Each filename will be `{symbol}.csv`, such as "AAPL.csv".
4. If there is only one symbol, save it to a comma-delimited file named "AAPL.csv".
5. Same as above, but save to a tab-delimited file.
6. Specify the file path for each symbol.
7. Use a template to determine the file path based on the symbol.
8. Save all symbols to a single HDF file in the "data" directory. The filename will be `{class_name}.h5`,
such as "YFData.h5". Each symbol will be saved as a separate key, such as "AAPL".
9. Specify the path to the HDF file.
10. Use a template to choose the key based on the symbol. In this example, spaces in symbols
are replaced with underscores.
11. Use a template to save all symbols under the group "stocks" in the HDF file.
12. Save each symbol to a separate HDF file with the key "df".
13. Save one Parquet file per symbol in the "data" directory. Each filename will be
`{symbol}.parquet`, such as "AAPL.parquet".
14. Same as above, but specify the path for each file.
15. Partition each symbol by year start and save it to a separate subdirectory within the "data" directory.
Each subdirectory will be named after the symbol.
16. Same as above, but specify the path for each subdirectory.
17. Save each DataFrame as a table in a SQLite database.
18. Same as above, but save to a PostgreSQL database.
19. Specify a schema (if supported by the database).
20. Specify each table name explicitly.
21. Drop the table if it already exists.
22. Attach a column with row numbers to each DataFrame for easier querying later.
23. Same as above, but generate row numbers starting from a specific value for each symbol,
label the column as "RN", and append to an existing table.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

After saving, data can be loaded using the corresponding class method.

```python title="How to load data"
data = vbt.YFData.load()  # (1)!

data = vbt.Data.from_csv("data")  # (2)!
data = vbt.Data.from_csv("data/*.csv")  # (3)!
data = vbt.Data.from_csv("data/*/**.csv")  # (4)!
data = vbt.Data.from_csv(symbols=["BTC-USD.csv", "ETH-USD.csv"])  # (5)!
data = vbt.Data.from_csv(features=["High.csv", "Low.csv"])  # (6)!
data = vbt.Data.from_csv("BTC-USD", paths="polygon_btc_1hour.csv")  # (7)!
data = vbt.Data.from_csv("AAPL.tsv", sep="\t")  # (8)!
data = vbt.Data.from_csv(["MSFT.csv", "AAPL.tsv"], sep=vbt.symbol_dict(MSFT=",", AAPL="\t"))  # (9)!
data = vbt.Data.from_csv("https://datahub.io/core/s-and-p-500/r/data.csv", match_paths=False)  # (10)!

data = vbt.Data.from_hdf("data")  # (11)!
data = vbt.Data.from_hdf("data.h5")  # (12)!
data = vbt.Data.from_hdf("data.h5/AAPL")  # (13)!
data = vbt.Data.from_hdf(["data.h5/AAPL", "data.h5/MSFT"])  # (14)!
data = vbt.Data.from_hdf(["AAPL", "MSFT"], paths="data.h5", match_paths=False)
data = vbt.Data.from_hdf("data.h5/stocks/*")  # (15)!

data = vbt.Data.from_parquet("data")  # (16)!
data = vbt.Data.from_parquet("AAPL.parquet")  # (17)!
data = vbt.Data.from_parquet("AAPL")  # (18)!

data = vbt.Data.from_sql(engine="sqlite:///data.db")  # (19)!
data = vbt.Data.from_sql("AAPL", engine=engine)  # (20)!
data = vbt.Data.from_sql("yahoo:AAPL", engine=engine)  # (21)!
data = vbt.Data.from_sql("AAPL", schema="yahoo", engine=engine)  # (22)!
data = vbt.Data.from_sql("AAPL", query="SELECT * FROM AAPL", engine=engine)  # (23)!

data = vbt.BinanceData.from_csv("BTCUSDT.csv", fetch_kwargs=dict(timeframe="hourly"))  # (24)!
```

1. Load from the pickle file named "YFData.pickle" and deserialize it into a Python object (recommended).
2. Load all CSV files in the directory named "data".
3. Same as above.
4. Same as above, but recursively.
5. Load two symbols into a symbol-oriented data instance.
6. Load two features into a feature-oriented data instance.
7. Load data from the file "polygon_btc_1hour.csv" and rename the symbol to "BTC-USD".
8. Load one symbol stored in the tab-delimited file "AAPL.tsv".
9. Load one symbol from the comma-delimited file "MSFT.csv" and another from the tab-delimited file "AAPL.tsv".
10. Load CSV data from a URL.
11. Load all symbols from all HDF files in the "data" directory recursively.
12. Load all symbols from the HDF file named "data.h5".
13. Load the symbol "AAPL" from the HDF file named "data.h5".
14. Load the symbols "AAPL" and "MSFT" from the HDF file named "data.h5".
15. Load all symbols under the "stocks" group in the HDF file named "data.h5".
16. Load all Parquet files and partitioned subdirectories in the "data" directory.
17. Load the symbol "AAPL" from the Parquet file named "AAPL.parquet".
18. Load the symbol "AAPL" from the partitioned Parquet directory named "AAPL".
19. Load all symbols from a SQLite database stored locally in the file "data.db".
20. Load the symbol "AAPL" by reading a table with the same name.
21. Load the symbol "AAPL" by reading a table with the same name from the "yahoo" schema.
22. Same as above, but the schema will not become part of the symbol name.
23. Load the symbol "AAPL" by executing an arbitrary SQL query.
24. Load the symbol from the file "BTCUSDT.csv" and wrap it with the `BinanceData` class to allow updating later.
To avoid specifying the timeframe when updating, provide it using `fetch_kwargs`.

## Updating

Some data classes support fetching and appending new data to previously saved data by overriding
the [Data.update_symbol](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.update_symbol) method.
This method scans the data for the latest timestamp and uses it as the start timestamp when
fetching new data with [Data.fetch_symbol](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.fetch_symbol).
The [Data.update](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.update) method performs this process for
each symbol in the data instance. There is no need to provide the client, timeframe, or other arguments,
since they are stored during fetching and reused automatically (unless they are lost by converting
the data instance to Pandas, CSV, or HDF!).

```python title="Download 1-minute data and update it later"
data = vbt.YFData.pull("AAPL", timeframe="1 minute")

# (1)!

data = data.update()  # (2)!
```

1. ...wait a minute...
2. Returns a new instance.

```python title="Download one year of data at a time"
start = 2010
end = 2020
data = None
while start < end:
    if data is None:
        data = vbt.YFData.pull("AAPL", start=str(start), end=str(start + 1))
    else:
        data = data.update(end=str(start + 1))
    start += 1
```

## Wrapping

A custom DataFrame can be wrapped into a data instance using [Data.from_data](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.from_data).
This method accepts either a single DataFrame for one symbol or a dict containing multiple
DataFrames keyed by their symbols.

```python title="Create a new Data instance"
data = ohlc_df.vbt.ohlcv.to_data()  # (1)!
data = vbt.Data.from_data(ohlc_df)

data = close_df.vbt.to_data()  # (2)!
data = vbt.Data.from_data(close_df, columns_are_symbols=True)

data = close_df.vbt.to_data(invert_data=True)  # (3)!
data = vbt.Data.from_data(close_df, columns_are_symbols=True, invert_data=True)

data = vbt.Data.from_data(vbt.symbol_dict({"AAPL": aapl_ohlc_df, "MSFT": msft_ohlc_df}))  # (4)!
data = vbt.Data.from_data(vbt.feature_dict({"High": high_df, "Low": low_df}))  # (5)!
```

1. OHLC DataFrame.
2. Close DataFrame where columns are symbols. Store in a feature-oriented format.
3. Close DataFrame where columns are symbols. Store in a symbol-oriented format.
4. Multiple feature DataFrames keyed by symbol.
5. Multiple symbol DataFrames keyed by feature.

!!! tip
    You do not have to use data instances; you can work with Pandas and even NumPy arrays as well,
    since VBT will convert any array-like object to a NumPy array anyway. However, the Pandas format
    is generally better than the NumPy format, because it also includes a datetime index and backtest
    configuration metadata, such as symbols and parameter combinations in column form.
    Data instances are especially useful for symbol alignment, stacking, resampling, and updating.

## Extracting

Depending on your use case, there are several ways to extract the underlying Pandas Series/DataFrame
from a data instance. To get the original data with one DataFrame per symbol, access the `data` attribute.
This data includes OHLC and other features (possibly of various data types) concatenated together,
which can be helpful for plotting. Note that VBT does not support this format directly;
instead, you are encouraged to represent each feature as a separate DataFrame with columns as symbols.
A feature can be accessed as an attribute (for example, `data.close` for closing price) or
by using [Data.get](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.get).

```python title="How to get symbol-oriented data"
data_per_symbol = data.data  # (1)!
aapl_data = data_per_symbol["AAPL"]  # (2)!

sr_or_df = data.get("Close")  # (3)!
sr_or_df = data["Close"].get()
sr_or_df = data.close

sr_or_df = data.get(["Close"])  # (4)!
sr_or_df = data[["Close"]].get()

sr = data.get("Close", "AAPL")  # (5)!
sr = data["Close"].get(symbols="AAPL")
sr = data.select("AAPL").close

df = data.get("Close", ["AAPL"])  # (6)!
df = data["Close"].get(symbols=["AAPL"])
df = data.select(["AAPL"]).close

aapl_df = data.get(["Open", "Close"], "AAPL")  # (7)!
close_df = data.get("Close", ["AAPL", "MSFT"])  # (8)!
open_df, close_df = data.get(["Open", "Close"], ["AAPL", "MSFT"])  # (9)!
```

1. Get a dictionary with one (OHLC) Series/DataFrame per symbol ("AAPL", "MSFT", etc.).
2. Extract the (OHLC) Series/DataFrame for "AAPL".
3. Get the closing price as a Series (for one symbol) or DataFrame (for multiple symbols, one per column).
4. Get the closing price as a DataFrame, regardless of the number of symbols.
5. Get the closing price for "AAPL" as a Series.
6. Get the closing price for "AAPL" as a DataFrame.
7. Get the opening and closing prices for "AAPL" as a DataFrame with two columns.
8. Get the closing price for "AAPL" and "MSFT" as a DataFrame with two columns.
9. Get the opening and closing prices as a tuple of two DataFrames, each with columns "AAPL" and "MSFT".

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

If a data instance is feature-oriented, the behavior of features and symbols is reversed.

```python title="How to get feature-oriented data"
data_per_feature = feat_data.data  # (1)!
close_data = data_per_feature["Close"]

sr_or_df = data.get("Close") 
sr_or_df = data.select("Close").get()
sr_or_df = data.close

sr = feat_data.get("Close", "AAPL")
sr = feat_data["AAPL"].get(features="Close")  # (2)!
sr = feat_data.select("Close").get(symbols="AAPL")  # (3)!

aapl_df = data.get(["Open", "Close"], "AAPL")
close_df = data.get("Close", ["AAPL", "MSFT"])
aapl_df, msft_df = data.get(["Open", "Close"], ["AAPL", "MSFT"])  # (4)!
```

1. In feature-oriented instances, data dictionaries use features as keys and symbols as columns,
so it is easier to extract feature Series or DataFrames.
2. Indexing (such as `[]`) is applied to columns, which are now symbols.
3. Various methods (such as `select`) are applied to keys, which are now features.
4. DataFrames are per symbol rather than per feature if a tuple is returned.

!!! tip
    To ensure consistent behavior between symbol-oriented and feature-oriented instances, always
    use [Data.get](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.get) to extract your data.

## Changing

There are four main operations to modify features and symbols: adding, selecting, renaming, and removing.
You can add one feature or symbol at a time, while the other operations can be performed on multiple.
Usually, you do not need to specify whether you want to operate on symbols or features,
as this is determined automatically. Both features and symbols are case-insensitive.
Note that each operation does not modify the original data instance, but returns a new one.

```python title="How to add features and symbols"
new_data = data.add_symbol("BTC-USD")  # (1)!
new_data = data.add_symbol("BTC-USD", fetch_kwargs=dict(start="2020"))  # (2)!
btc_df = vbt.YFData.pull("ETH-USD", start="2020").get()
new_data = data.add_symbol("BTC-USD", btc_df)  # (3)!

new_data = data.add_feature("SMA")  # (4)!
new_data = data.add_feature("SMA", run_kwargs=dict(timeperiod=20, hide_params=True))  # (5)!
sma_df = data.run("SMA", timeperiod=20, hide_params=True, unpack=True)
new_data = data.add_feature("SMA", sma_df)  # (6)!

new_data = data.add("BTC-USD", btc_df)  # (7)!
new_data = data.add("SMA", sma_df)  # (8)!
```

1. Pull "BTC-USD" and add it as a symbol.
2. Pull "BTC-USD" from 2020 onwards and add it as a symbol.
3. Add a custom DataFrame as a symbol.
4. Run the SMA indicator and add it as a feature.
5. Run the 20-period SMA indicator and add it as a feature.
6. Add a custom DataFrame as a feature.
7. If some columns are found among the features of the data instance and not among the symbols,
the DataFrame will be added as a symbol.
8. If some columns are found among the symbols of the data instance and not among the features,
the DataFrame will be added as a feature.

!!! note
    Only one feature or symbol can be added at a time. To add a data instance, use `merge` instead.

```python title="How to select features and symbols"
new_data = data.select_symbols("BTC-USD")  # (1)!
new_data = data.select_symbols(["BTC-USD", "ETH-USD"])  # (2)!

new_data = data.select_features("SMA")  # (3)!
new_data = data.select_features(["SMA", "EMA"])  # (4)!

new_data = data.select("BTC-USD")  # (5)!
new_data = data.select("SMA")  # (6)!
new_data = data.select("sma")  # (7)!
```

1. Select one symbol.
2. Select multiple symbols.
3. Select one feature.
4. Select multiple features.
5. If some keys are found among the symbols of the data instance and not among the features,
a symbol will be selected.
6. If some keys are found among the features of the data instance and not among the symbols,
a feature will be selected.
7. Case does not matter!

```python title="How to rename features and symbols"
new_data = data.rename_symbols("BTC-USD", "BTCUSDT")  # (1)!
new_data = data.rename_symbols(["BTC-USD", "ETH-USD"], ["BTCUSDT", "ETHUSDT"])  # (2)!
new_data = data.rename_symbols({"BTC-USD": "BTCUSDT", "ETH-USD": "ETHUSDT"})

new_data = data.rename_features("Price", "Close")  # (3)!
new_data = data.rename_features(["Price", "MovAvg"], ["Close", "SMA"])  # (4)!
new_data = data.rename_features({"Price": "Close", "MovAvg": "SMA"})

new_data = data.rename("BTC-USD", "BTCUSDT")  # (5)!
new_data = data.rename("Price", "Close")  # (6)!
new_data = data.rename("price", "Close")  # (7)!
```

1. Rename the symbol "BTC-USD" to "BTCUSDT".
2. Rename the symbol "BTC-USD" to "BTCUSDT" and the symbol "ETH-USD" to "ETHUSDT".
3. Rename the feature "Price" to "Close".
4. Rename the feature "Price" to "Close" and the feature "MovAvg" to "SMA".
5. If some keys are found among the symbols of the data instance and not among the features,
they will be renamed as symbols.
6. If some keys are found among the features of the data instance and not among the symbols,
they will be renamed as features.
7. The case of the source key does not matter, but the case of the target key does!

```python title="How to remove features and symbols"
new_data = data.remove_symbols("BTC-USD")  # (1)!
new_data = data.remove_symbols(["BTC-USD", "ETH-USD"])  # (2)!

new_data = data.remove_features("SMA")  # (3)!
new_data = data.remove_features(["SMA", "EMA"])  # (4)!

new_data = data.remove("BTC-USD")  # (5)!
new_data = data.remove("SMA")  # (6)!
new_data = data.remove("sma")  # (7)!
```

1. Remove one symbol.
2. Remove multiple symbols.
3. Remove one feature.
4. Remove multiple features.
5. If some keys are found among the symbols of the data instance and not among the features,
they will be removed as symbols.
6. If some keys are found among the features of the data instance and not among the symbols,
they will be removed as features.
7. Case does not matter!

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Instances can be merged along symbols, rows, and columns by using [Data.merge](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.merge).

```python title="Merge multiple different Data instances"
data1 = vbt.YFData.pull("BTC-USD")
data2 = vbt.BinanceData.pull("BTCUSDT")
data3 = vbt.CCXTData.pull("BTC-USDT", exchange="kucoin")
data = vbt.Data.merge(data1, data2, data3, missing_columns="drop")
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To apply a function to each DataFrame and return a new instance, use the method
[Data.transform](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.transform). By default,
it passes a single DataFrame where all individual DataFrames are concatenated along columns.
This is useful for dropping missing values across all symbols. To transform DataFrames
individually, use `per_symbol=True` and/or `per_feature=True`. The only requirement is that
the returned column names are identical across all features and symbols.

```python title="Drop rows with missing values"
new_data = data.transform(lambda df: df.dropna(how="any"))  # (1)!
new_data = data.dropna()  # (2)!
new_data = data.dropna(how="all")  # (3)!

new_data = data.transform(your_func, per_feature=True)
new_data = data.transform(your_func, per_symbol=True)
new_data = data.transform(your_func, per_feature=True, per_symbol=True)  # (4)!
new_data = data.transform(your_func, per_feature=True, per_symbol=True, pass_frame=True)  # (5)!
```

1. Remove any row that has at least one missing value across all features and symbols.
2. Same as above.
3. Remove any row that has all values missing across all features and symbols.
4. One column at a time is passed as a Series.
5. One column at a time is passed as a DataFrame.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

If symbols have different timezones, the final timezone will be set to "UTC". This may cause
some symbols to be shifted in time. For example, if one symbol uses UTC+0200 and another uses UTC+0400,
this will effectively double the common index and result in missing values about half the time.
To align their indexes into a single index, use [Data.realign](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.realign),
which is a special resampling method that produces a single index and correctly orders data by time.

```python title="Realign multiple timezones"
new_data = data.realign()  # (1)!
```

1. To avoid forward filling missing values, pass `ffill=False`.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can easily chain operations that return a new data instance by using dot notation or the `pipe` method.

```python title="Chain multiple operations"
data = (
    vbt.YFData.pull("BTC-USD")
    .add_symbol("ETH-USD")
    .rename({"btc-usd": "BTCUSDT", "eth-usd": "ETHUSDT"})
    .remove(["dividends", "stock splits"])
    .add_feature("SMA")
    .add_feature("EMA")
)

# ______________________________________________________________

data = (
    vbt.YFData
    .pipe("pull", "BTC-USD")  # (1)!
    .pipe("add_symbol", "ETH-USD")
    .pipe("rename", {"btc-usd": "BTCUSDT", "eth-usd": "ETHUSDT"})
    .pipe("remove", ["dividends", "stock splits"])
    .pipe("add_feature", "SMA")
    .pipe("add_feature", "EMA")
)
```

1. The method can be called on both data classes and instances. You can pass a string to call
a method of the data class or instance, or pass any function that expects the instance as the first argument.
To provide arguments to the function, pass the function as a tuple. The second element is the argument's
position or name.