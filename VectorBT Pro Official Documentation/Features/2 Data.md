---
title: Data
description: Data features of VectorBT PRO
icon: material/database
---

# :material-database: Data

## FinDataPy

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_8_20.svg){ loading=lazy }

- [x] Introducing a new class for [findatapy](https://github.com/cuemacro/findatapy), designed to 
pull data from Bloomberg, Eikon, Quandl, Dukascopy, and other data sources.

```pycon title="Discover tickers on Dukascopy and pull one day of tick data"
>>> vbt.FinPyData.list_symbols(data_source="dukascopy")
['fx.dukascopy.tick.NYC.AUDCAD',
 'fx.dukascopy.tick.NYC.AUDCHF',
 'fx.dukascopy.tick.NYC.AUDJPY',
 ...
 'fx.dukascopy.tick.NYC.USDTRY',
 'fx.dukascopy.tick.NYC.USDZAR',
 'fx.dukascopy.tick.NYC.ZARJPY']
 
>>> data = vbt.FinPyData.pull(  # (1)!
...     "fx.dukascopy.tick.NYC.EURUSD",
...     start="14 Jun 2016",
...     end="15 Jun 2016"
... )
>>> data.get()
                                     close
Date                                      
2016-06-14 00:00:00.844000+00:00  1.128795
2016-06-14 00:00:01.591000+00:00  1.128790
2016-06-14 00:00:01.743000+00:00  1.128775
2016-06-14 00:00:02.464000+00:00  1.128770
2016-06-14 00:00:02.971000+00:00  1.128760
...                                    ...
2016-06-14 23:59:57.733000+00:00  1.121020
2016-06-14 23:59:58.239000+00:00  1.121030
2016-06-14 23:59:58.953000+00:00  1.121035
2016-06-14 23:59:59.004000+00:00  1.121050
2016-06-14 23:59:59.934000+00:00  1.121055

[82484 rows x 1 columns]

>>> data = vbt.FinPyData.pull(  # (2)!
...     "EURUSD",
...     start="14 Jun 2016",
...     end="15 Jun 2016",
...     timeframe="tick",
...     category="fx",
...     data_source="dukascopy",
...     fields=["bid", "ask", "bidv", "askv"]
... )
>>> data.get()
                                      bid      ask  bidv   askv
Date                                                           
2016-06-14 00:00:00.844000+00:00  1.12877  1.12882  1.00  10.12
2016-06-14 00:00:01.591000+00:00  1.12877  1.12881  1.00   1.00
2016-06-14 00:00:01.743000+00:00  1.12875  1.12880  3.11   3.00
2016-06-14 00:00:02.464000+00:00  1.12875  1.12879  2.21   1.00
2016-06-14 00:00:02.971000+00:00  1.12875  1.12877  2.21   1.00
...                                   ...      ...   ...    ...
2016-06-14 23:59:57.733000+00:00  1.12100  1.12104  1.24   1.50
2016-06-14 23:59:58.239000+00:00  1.12101  1.12105  9.82   1.12
2016-06-14 23:59:58.953000+00:00  1.12102  1.12105  1.50   1.12
2016-06-14 23:59:59.004000+00:00  1.12103  1.12107  1.50   1.12
2016-06-14 23:59:59.934000+00:00  1.12103  1.12108  1.87   2.25

[82484 rows x 4 columns]
```

1. String format.
2. Keyword format.

## Databento

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2023_12_23.svg){ loading=lazy }

- [x] Introducing a new class specialized in pulling data from [Databento](https://databento.com/).

```pycon title="Get best bid and offer (BBO) data from Databento"
>>> vbt.BentoData.set_custom_settings(
...     client_config=dict(
...         key="YOUR_KEY"
...     )
... )
>>> params = dict(
...     symbols="ESH3",
...     dataset="GLBX.MDP3",
...     start=vbt.timestamp("2022-10-28 20:30:00"),
...     end=vbt.timestamp("2022-10-28 21:00:00"),
...     schema="tbbo"
... )
>>> vbt.BentoData.get_cost(**params)
1.2002885341644287e-05

>>> data = vbt.BentoData.pull(**params)
>>> data.get()
                                                               ts_event  \
ts_recv                                                                   
2022-10-28 20:30:59.047138053+00:00 2022-10-28 20:30:59.046914657+00:00   
2022-10-28 20:37:53.112494436+00:00 2022-10-28 20:37:53.112246421+00:00   
...
2022-10-28 20:59:15.075191111+00:00 2022-10-28 20:59:15.074953895+00:00   
2022-10-28 20:59:34.607239899+00:00 2022-10-28 20:59:34.606984277+00:00   

                                     rtype  publisher_id  instrument_id  \
ts_recv                                                                   
2022-10-28 20:30:59.047138053+00:00      1             1         206299   
2022-10-28 20:37:53.112494436+00:00      1             1         206299   
...
2022-10-28 20:59:15.075191111+00:00      1             1         206299   
2022-10-28 20:59:34.607239899+00:00      1             1         206299   

                                    action side  depth    price  size  flags  \
ts_recv                                                                        
2022-10-28 20:30:59.047138053+00:00      T    B      0  3955.25     1      0   
2022-10-28 20:37:53.112494436+00:00      T    A      0  3955.00     1      0   
...
2022-10-28 20:59:15.075191111+00:00      T    A      0  3953.75     1      0   
2022-10-28 20:59:34.607239899+00:00      T    A      0  3954.50     2      0   

                                     ts_in_delta  sequence  bid_px_00  \
ts_recv                                                                 
2022-10-28 20:30:59.047138053+00:00        18553  73918214    3954.75   
2022-10-28 20:37:53.112494436+00:00        18334  73926240    3955.00   
...
2022-10-28 20:59:15.075191111+00:00        19294  73945515    3953.75   
2022-10-28 20:59:34.607239899+00:00        18701  73945932    3954.50   

                                     ask_px_00  bid_sz_00  ask_sz_00  \
ts_recv                                                                
2022-10-28 20:30:59.047138053+00:00    3955.25          1          1   
2022-10-28 20:37:53.112494436+00:00    3955.75          1          1   
...
2022-10-28 20:59:15.075191111+00:00    3956.00          1          1   
2022-10-28 20:59:34.607239899+00:00    3956.00          4          1   

                                     bid_ct_00  ask_ct_00 symbol  
ts_recv                                                           
2022-10-28 20:30:59.047138053+00:00          1          1   ESH3  
2022-10-28 20:37:53.112494436+00:00          1          1   ESH3  
...
2022-10-28 20:59:15.075191111+00:00          1          1   ESH3  
2022-10-28 20:59:34.607239899+00:00          3          1   ESH3  
```

## SQL queries

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2023_10_22.svg){ loading=lazy }

- [x] Thanks to [DuckDB](https://duckdb.org/), you can now run SQL queries directly on data instances.

```pycon title="Run a rolling average of 14 days on minute data using SQL"
>>> data = vbt.TVData.pull(
...     "AAPL",
...     exchange="NASDAQ",
...     timeframe="1 minute",
...     tz="America/New_York"
... )

>>> data.sql("""
...     SELECT datetime, AVG(Close) OVER(
...         ORDER BY "datetime" ASC
...         RANGE BETWEEN INTERVAL 14 DAYS PRECEDING AND CURRENT ROW
...     ) AS "Moving Average"
...     FROM "AAPL";
... """)
datetime
2023-09-11 09:30:00-04:00    180.080000
2023-09-11 09:31:00-04:00    179.965000
2023-09-11 09:32:00-04:00    180.000000
2023-09-11 09:33:00-04:00    180.022500
2023-09-11 09:34:00-04:00    179.984000
                                    ...
2023-10-20 15:55:00-04:00    177.786669
2023-10-20 15:56:00-04:00    177.785492
2023-10-20 15:57:00-04:00    177.784322
2023-10-20 15:58:00-04:00    177.783166
2023-10-20 15:59:00-04:00    177.781986
Name: Moving Average, Length: 11700, dtype: float64
```

## DuckDB

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2023_10_22.svg){ loading=lazy }

- [x] [DuckDB](https://duckdb.org/) is a high-performance analytical database system that offers
a robust SQL dialect for interacting with various data stores. Not only can it run analytical queries on 
local data, even if the data does not fit into memory and without needing a distributed framework, 
but it can also query CSV, Parquet, and JSON files directly.

```pycon title="Save minute data to a DuckDB database, and read one day"
>>> data = vbt.TVData.pull(
...     "AAPL",
...     exchange="NASDAQ",
...     timeframe="1 minute",
...     tz="America/New_York"
... )

>>> URL = "database.duckdb"
>>> data.to_duckdb(connection=URL)

>>> day_data = vbt.DuckDBData.pull(
...     "AAPL",
...     start="2023-10-02 09:30:00",
...     end="2023-10-02 16:00:00",
...     tz="America/New_York",
...     connection=URL
... )
>>> day_data.get()
                              Open    High     Low   Close    Volume
datetime
2023-10-02 09:30:00-04:00  171.260  171.34  170.93  171.10   61654.0
2023-10-02 09:31:00-04:00  171.130  172.37  171.13  172.30   53481.0
2023-10-02 09:32:00-04:00  172.310  172.64  172.16  172.64   44750.0
2023-10-02 09:33:00-04:00  172.640  172.97  172.54  172.78   53195.0
2023-10-02 09:34:00-04:00  172.780  173.07  172.75  173.00   47416.0
...                            ...     ...     ...     ...       ...
2023-10-02 15:55:00-04:00  173.300  173.51  173.26  173.51   61619.0
2023-10-02 15:56:00-04:00  173.525  173.59  173.42  173.43   45066.0
2023-10-02 15:57:00-04:00  173.430  173.55  173.42  173.50   45220.0
2023-10-02 15:58:00-04:00  173.510  173.60  173.46  173.56   47371.0
2023-10-02 15:59:00-04:00  173.560  173.78  173.56  173.75  161253.0

[390 rows x 5 columns]
```

## SQLAlchemy

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2023_10_22.svg){ loading=lazy }

- [x] [SQLAlchemy](https://www.sqlalchemy.org/) provides a standard interface that allows developers 
to create database-agnostic code for communicating with a wide range of SQL database engines.
With its help, you can now easily store data in SQL databases and read from them as well.

```pycon title="Save minute data to a PostgreSQL database, and read one day"
>>> data = vbt.TVData.pull(
...     "AAPL",
...     exchange="NASDAQ",
...     timeframe="1 minute",
...     tz="America/New_York"
... )

>>> URL = "postgresql://postgres:postgres@localhost:5432"
>>> data.to_sql(engine=URL)

>>> day_data = vbt.SQLData.pull(
...     "AAPL",
...     start="2023-10-02 09:30:00",
...     end="2023-10-02 16:00:00",
...     tz="America/New_York",
...     engine=URL
... )
>>> day_data.get()
                              Open    High     Low   Close    Volume
datetime
2023-10-02 09:30:00-04:00  171.260  171.34  170.93  171.10   61654.0
2023-10-02 09:31:00-04:00  171.130  172.37  171.13  172.30   53481.0
2023-10-02 09:32:00-04:00  172.310  172.64  172.16  172.64   44750.0
2023-10-02 09:33:00-04:00  172.640  172.97  172.54  172.78   53195.0
2023-10-02 09:34:00-04:00  172.780  173.07  172.75  173.00   47416.0
...                            ...     ...     ...     ...       ...
2023-10-02 15:55:00-04:00  173.300  173.51  173.26  173.51   61619.0
2023-10-02 15:56:00-04:00  173.525  173.59  173.42  173.43   45066.0
2023-10-02 15:57:00-04:00  173.430  173.55  173.42  173.50   45220.0
2023-10-02 15:58:00-04:00  173.510  173.60  173.46  173.56   47371.0
2023-10-02 15:59:00-04:00  173.560  173.78  173.56  173.75  161253.0

[390 rows x 5 columns]
```

## PyArrow & FastParquet

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2023_10_22.svg){ loading=lazy }

- [x] Data can be written to Feather with PyArrow and to Parquet using PyArrow or FastParquet.
Parquet performs especially well in write-once, read-many scenarios, providing highly efficient data
compression and decompression, making it a great choice for storing time series data.

```pycon title="Save minute data to a Parquet dataset partitioned by day, and read one day"
>>> data = vbt.TVData.pull(
...     "AAPL",
...     exchange="NASDAQ",
...     timeframe="1 minute",
...     tz="America/New_York"
... )

>>> data.to_parquet(partition_by="day")  # (1)!

>>> day_data = vbt.ParquetData.pull("AAPL", filters=[("group", "==", "2023-10-02")])
>>> day_data.get()
                              Open    High     Low   Close    Volume
datetime
2023-10-02 09:30:00-04:00  171.260  171.34  170.93  171.10   61654.0
2023-10-02 09:31:00-04:00  171.130  172.37  171.13  172.30   53481.0
2023-10-02 09:32:00-04:00  172.310  172.64  172.16  172.64   44750.0
2023-10-02 09:33:00-04:00  172.640  172.97  172.54  172.78   53195.0
2023-10-02 09:34:00-04:00  172.780  173.07  172.75  173.00   47416.0
...                            ...     ...     ...     ...       ...
2023-10-02 15:55:00-04:00  173.300  173.51  173.26  173.51   61619.0
2023-10-02 15:56:00-04:00  173.525  173.59  173.42  173.43   45066.0
2023-10-02 15:57:00-04:00  173.430  173.55  173.42  173.50   45220.0
2023-10-02 15:58:00-04:00  173.510  173.60  173.46  173.56   47371.0
2023-10-02 15:59:00-04:00  173.560  173.78  173.56  173.75  161253.0

[390 rows x 5 columns]
```

1. Without `partition_by`, the data will be saved to a single Parquet file. You will still be able to
filter rows by any column in newer versions of PyArrow and Pandas.

## Feature-oriented data

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_14_0.svg){ loading=lazy }

- [x] The main limitation of VBT's data class was that it could only store data in a
symbol-oriented format. This meant features such as OHLC had to be combined into a single DataFrame
beforehand. This approach can be somewhat counterproductive, as in VBT, we typically work with these
features separately. For example, when calling `data.close`, VBT scans for "close" columns across 
all symbols, extracts them, and concatenates them into another DataFrame. To address this, the data
class has been redesigned to natively support storing feature-oriented data as well.

```pycon title="Create a feature-oriented data instance from various portfolio time series"
>>> data = vbt.YFData.pull(["AAPL", "MSFT", "GOOG"])
>>> pf = data.run("from_random_signals", n=[10, 20, 30])

>>> pf_data = vbt.Data.from_data(
...     vbt.feature_dict({
...         "cash": pf.cash,
...         "assets": pf.assets,
...         "asset_value": pf.asset_value,
...         "value": pf.value
...     })
... )
>>> pf_data.get(feature="cash", symbol=(10, "AAPL"))
Date
1980-12-12 05:00:00+00:00      100.000000
1980-12-15 05:00:00+00:00      100.000000
1980-12-16 05:00:00+00:00      100.000000
1980-12-17 05:00:00+00:00      100.000000
1980-12-18 05:00:00+00:00      100.000000
                                      ...
2023-08-25 04:00:00+00:00    81193.079771
2023-08-28 04:00:00+00:00    81193.079771
2023-08-29 04:00:00+00:00    81193.079771
2023-08-30 04:00:00+00:00    81193.079771
2023-08-31 04:00:00+00:00    81193.079771
Name: (10, AAPL), Length: 10770, dtype: float64
```

## Parallel data

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_10_0.svg){ loading=lazy }

- [x] Data fetching and updating can be easily parallelized.

```pycon title="Benchmark fetching multiple symbols serially and concurrently"
>>> symbols = ["SPY", "TLT", "XLF", "XLE", "XLU", "XLK", "XLB", "XLP", "XLY", "XLI", "XLV"]

>>> with vbt.Timer() as timer:
...     data = vbt.YFData.pull(symbols)
>>> print(timer.elapsed())
4.52 seconds

>>> with vbt.Timer() as timer:
...     data = vbt.YFData.pull(symbols, execute_kwargs=dict(engine="threadpool"))
>>> print(timer.elapsed())
918.54 milliseconds
```

## Trading View

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_9_0.svg){ loading=lazy }

- [x] A new class specialized for pulling data from [TradingView](https://www.tradingview.com/) is
now available.

```pycon title="Pull 1-minute AAPL data"
>>> data = vbt.TVData.pull(
...     "NASDAQ:AAPL",
...     timeframe="1 minute",
...     tz="US/Eastern"
... )
>>> data.get()
                             Open    High     Low   Close   Volume
datetime
2022-12-05 09:30:00-05:00  147.75  148.31  147.50  148.28  37769.0
2022-12-05 09:31:00-05:00  148.28  148.67  148.28  148.49  10525.0
2022-12-05 09:32:00-05:00  148.50  148.73  148.30  148.30   4860.0
2022-12-05 09:33:00-05:00  148.25  148.73  148.25  148.64   5306.0
2022-12-05 09:34:00-05:00  148.62  148.97  148.52  148.97   5808.0
...                           ...     ...     ...     ...      ...
2023-01-17 15:55:00-05:00  135.80  135.91  135.80  135.86  37573.0
2023-01-17 15:56:00-05:00  135.85  135.88  135.80  135.88  18796.0
2023-01-17 15:57:00-05:00  135.88  135.93  135.85  135.91  21019.0
2023-01-17 15:58:00-05:00  135.90  135.97  135.89  135.95  20934.0
2023-01-17 15:59:00-05:00  135.94  136.00  135.84  135.94  86696.0

[11310 rows x 5 columns]
```

## Symbol search

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_7_0.svg){ loading=lazy }

- [x] Most data classes can retrieve the complete list of symbols available for an exchange, and
optionally filter the list using a [globbing](https://en.wikipedia.org/wiki/Glob_(programming)) or
[regular expression](https://en.wikipedia.org/wiki/Regular_expression) pattern. This also works for
local data classes.

```pycon title="Get all XRP pairs listed on Binance"
>>> vbt.BinanceData.list_symbols("XRP*")
{'XRPAUD',
 'XRPBEARBUSD',
 'XRPBEARUSDT',
 'XRPBIDR',
 'XRPBKRW',
 'XRPBNB',
 'XRPBRL',
 'XRPBTC',
 'XRPBULLBUSD',
 'XRPBULLUSDT',
 'XRPBUSD',
 'XRPDOWNUSDT',
 'XRPETH',
 'XRPEUR',
 'XRPGBP',
 'XRPNGN',
 'XRPPAX',
 'XRPRUB',
 'XRPTRY',
 'XRPTUSD',
 'XRPUPUSDT',
 'XRPUSDC',
 'XRPUSDT'}
```

## Symbol classes

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_7_0.svg){ loading=lazy }

- [x] Since VBT leverages multi-indexes in Pandas, you can associate each symbol with one or more
classes, such as sectors. This allows you to analyze the performance of a trading strategy relative
to each class.

```pycon title="Compare equal-weighted portfolios for three sectors"
>>> classes = vbt.symbol_dict({
...     "MSFT": dict(sector="Technology"),
...     "GOOGL": dict(sector="Technology"),
...     "META": dict(sector="Technology"),
...     "JPM": dict(sector="Finance"),
...     "BAC": dict(sector="Finance"),
...     "WFC": dict(sector="Finance"),
...     "AMZN": dict(sector="Retail"),
...     "WMT": dict(sector="Retail"),
...     "BABA": dict(sector="Retail"),
... })
>>> data = vbt.YFData.pull(
...     list(classes.keys()),
...     classes=classes,
...     missing_index="drop"
... )
>>> pf = vbt.PF.from_orders(
...     data,
...     size=vbt.index_dict({0: 1 / 3}),  # (1)!
...     size_type="targetpercent",
...     group_by="sector",
...     cash_sharing=True
... )
>>> pf.value.vbt.plot().show()
```

1. There are three assets in each group. Allocate 33.3% to each asset at the first bar.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/classes.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/classes.dark.svg#only-dark){: .iimg loading=lazy }

## Runnable data

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_5_0.svg){ loading=lazy }

- [x] Tired of figuring out which arguments are required by an indicator? Data instances can now
recognize the arguments of any indicator or function, map them to column names, and run the
function by passing in the required columns. You can also change the mapping, override indicator
parameters, and query indicators by name. The data instance will search all integrated indicator
packages and return the first (and best) match it finds.

```pycon title="Run Stochastic RSI by data"
>>> data = vbt.YFData.pull("BTC-USD")
>>> stochrsi = data.run("stochrsi")
>>> stochrsi.fastd
Date
2014-09-17 00:00:00+00:00          NaN
2014-09-18 00:00:00+00:00          NaN
2014-09-19 00:00:00+00:00          NaN
2014-09-20 00:00:00+00:00          NaN
2014-09-21 00:00:00+00:00          NaN
                                   ...
2023-01-15 00:00:00+00:00    96.168788
2023-01-16 00:00:00+00:00    91.733393
2023-01-17 00:00:00+00:00    78.295255
2023-01-18 00:00:00+00:00    48.793133
2023-01-20 00:00:00+00:00    26.242474
Name: Close, Length: 3047, dtype: float64
```

## Data transformation

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_2_3.svg){ loading=lazy }

- [x] After fetching data, how do you change it? There is a new method that puts all symbols into a
single DataFrame and passes it to a UDF for transformation.

```pycon title="Remove weekends"
>>> data = vbt.YFData.pull(["BTC-USD", "ETH-USD"], start="2020-01-01", end="2020-01-14")
>>> new_data = data.transform(lambda df: df[~df.index.weekday.isin([5, 6])])
>>> new_data.close
symbol                         BTC-USD     ETH-USD
Date
2020-01-01 00:00:00+00:00  7200.174316  130.802002
2020-01-02 00:00:00+00:00  6985.470215  127.410179
2020-01-03 00:00:00+00:00  7344.884277  134.171707
2020-01-06 00:00:00+00:00  7769.219238  144.304153
2020-01-07 00:00:00+00:00  8163.692383  143.543991
2020-01-08 00:00:00+00:00  8079.862793  141.258133
2020-01-09 00:00:00+00:00  7879.071289  138.979202
2020-01-10 00:00:00+00:00  8166.554199  143.963776
2020-01-13 00:00:00+00:00  8144.194336  144.226593
```

## Synthetic OHLC

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_2_1.svg){ loading=lazy }

- [x] New basic models are available for generating synthetic OHLC data.
These are especially useful for leakage detection.

```pycon title="Generate 3 months of synthetic data using Geometric Brownian Motion"
>>> data = vbt.GBMOHLCData.pull("R", start="2022-01", end="2022-04")
>>> data.plot().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/synthetic_ohlc.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/synthetic_ohlc.dark.svg#only-dark){: .iimg loading=lazy }

## Data saver

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_1_1.svg){ loading=lazy }

- [x] Imagine a script that can periodically pull the latest data from an exchange and save it to
disk, all without your intervention. VBT implements two classes that can do exactly this: one that
saves to CSV and another that saves to HDF.

```python title="BTCUSDT_1m_saver.py"
from vectorbtpro import *

import logging
logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    if vbt.CSVDataSaver.file_exists():
        csv_saver = vbt.CSVDataSaver.load()
        csv_saver.update()
        init_save = False
    else:
        data = vbt.BinanceData.pull(
            "BTCUSDT",
            start="10 minutes ago UTC",
            timeframe="1 minute"
        )
        csv_saver = vbt.CSVDataSaver(data)
        init_save = True
    csv_saver.update_every(1, "minute", init_save=init_save)
    csv_saver.save()  # (1)!
```

1. The CSV data saver only stores the latest data update, which serves as the starting point for the
next update. Be sure to save it and re-use it in the next runtime.

```console title="Run in console and then interrupt"
$ python BTCUSDT_1m_saver.py
2023-02-01 12:26:36.744000+00:00 - 2023-02-01 12:36:00+00:00: : 1it [00:01,  1.22s/it]
INFO:vectorbtpro.data.saver:Saved initial 10 rows from 2023-02-01 12:27:00+00:00 to 2023-02-01 12:36:00+00:00
INFO:vectorbtpro.utils.schedule_:Starting schedule manager with jobs [Every 1 minute do update(save_kwargs=None) (last run: [never], next run: 2023-02-01 13:37:38)]
INFO:vectorbtpro.data.saver:Saved 2 rows from 2023-02-01 12:36:00+00:00 to 2023-02-01 12:37:00+00:00
INFO:vectorbtpro.data.saver:Saved 2 rows from 2023-02-01 12:37:00+00:00 to 2023-02-01 12:38:00+00:00
INFO:vectorbtpro.utils.schedule_:Stopping schedule manager
```

```console title="Run in console again to continue"
$ python BTCUSDT_1m_saver.py
INFO:vectorbtpro.utils.schedule_:Starting schedule manager with jobs [Every 1 minute do update(save_kwargs=None) (last run: [never], next run: 2023-02-01 13:42:08)]
INFO:vectorbtpro.data.saver:Saved 5 rows from 2023-02-01 12:38:00+00:00 to 2023-02-01 12:42:00+00:00
INFO:vectorbtpro.utils.schedule_:Stopping schedule manager
```

## Polygon.io

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_1_1.svg){ loading=lazy }

- [x] Welcome a new class specialized in pulling data from [Polygon.io](https://polygon.io/)!

```pycon title="Get one month of 30-minute AAPL data from Polygon.io"
>>> vbt.PolygonData.set_custom_settings(
...     client_config=dict(
...         api_key="YOUR_API_KEY"
...     )
... )
>>> data = vbt.PolygonData.pull(
...     "AAPL",
...     start="2022-12-01",  # (1)!
...     end="2023-01-01",
...     timeframe="30 minutes",
...     tz="US/Eastern"
... )
>>> data.get()
                             Open    High     Low     Close   Volume  \
Open time                                                              
2022-12-01 04:00:00-05:00  148.08  148.08  147.04  147.3700  50886.0   
2022-12-01 04:30:00-05:00  147.37  147.37  147.12  147.2600  16575.0   
2022-12-01 05:00:00-05:00  147.31  147.51  147.20  147.3800  20753.0   
2022-12-01 05:30:00-05:00  147.43  147.56  147.38  147.3800   7388.0   
2022-12-01 06:00:00-05:00  147.30  147.38  147.24  147.2400   7416.0   
...                           ...     ...     ...       ...      ...   
2022-12-30 17:30:00-05:00  129.94  130.05  129.91  129.9487  35694.0   
2022-12-30 18:00:00-05:00  129.95  130.00  129.94  129.9500  15595.0   
2022-12-30 18:30:00-05:00  129.94  130.05  129.94  130.0100  20287.0   
2022-12-30 19:00:00-05:00  129.99  130.04  129.99  130.0000  12490.0   
2022-12-30 19:30:00-05:00  130.00  130.04  129.97  129.9700  28271.0   

                           Trade count      VWAP  
Open time                                         
2022-12-01 04:00:00-05:00         1024  147.2632  
2022-12-01 04:30:00-05:00          412  147.2304  
2022-12-01 05:00:00-05:00          306  147.3466  
2022-12-01 05:30:00-05:00          201  147.4818  
2022-12-01 06:00:00-05:00          221  147.2938  
...                                ...       ...  
2022-12-30 17:30:00-05:00          350  129.9672  
2022-12-30 18:00:00-05:00          277  129.9572  
2022-12-30 18:30:00-05:00          312  130.0034  
2022-12-30 19:00:00-05:00          176  130.0140  
2022-12-30 19:30:00-05:00          366  129.9941  

[672 rows x 7 columns]
```

1. In the timezone provided via `tz`.

## Alpha Vantage

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_1_1.svg){ loading=lazy }

- [x] Welcome a new class specialized in pulling data from [Alpha Vantage](https://www.alphavantage.co/)!

```pycon title="Get Stochastic RSI of IBM from Alpha Vantage"
>>> data = vbt.AVData.pull(
...     "IBM",
...     category="technical-indicators",
...     function="STOCHRSI",
...     params=dict(fastkperiod=14)
... )
>>> data.get()
                              FastD     FastK
1999-12-07 00:00:00+00:00  100.0000  100.0000
1999-12-08 00:00:00+00:00  100.0000  100.0000
1999-12-09 00:00:00+00:00   77.0255   31.0765
1999-12-10 00:00:00+00:00   43.6922    0.0000
1999-12-13 00:00:00+00:00   12.0197    4.9826
...                             ...       ...
2023-01-26 00:00:00+00:00   11.7960    0.0000
2023-01-27 00:00:00+00:00    3.7773    0.0000
2023-01-30 00:00:00+00:00    4.4824   13.4471
2023-01-31 00:00:00+00:00    7.8258   10.0302
2023-02-01 16:00:01+00:00   13.0966   15.8126

[5826 rows x 2 columns]
```

## Nasdaq Data Link

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_1_1.svg){ loading=lazy }

- [x] Welcome a new class specialized in pulling data from [Nasdaq Data Link](https://data.nasdaq.com/)!

```pycon title="Get Index of Consumer Sentiment from Nasdaq Data Link"
>>> data = vbt.NDLData.pull("UMICH/SOC1")
>>> data.get()
                           Index
Date                            
1952-11-30 00:00:00+00:00   86.2
1953-02-28 00:00:00+00:00   90.7
1953-08-31 00:00:00+00:00   80.8
1953-11-30 00:00:00+00:00   80.7
1954-02-28 00:00:00+00:00   82.0
...                          ...
2022-08-31 00:00:00+00:00   58.2
2022-09-30 00:00:00+00:00   58.6
2022-10-31 00:00:00+00:00   59.9
2022-11-30 00:00:00+00:00   56.8
2022-12-31 00:00:00+00:00   59.7

[632 rows x 1 columns]
```

## Data merging

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_1_0.svg){ loading=lazy }

- [x] Often, there is a need to backtest symbols from different exchanges by placing them in the 
same basket. For this purpose, VBT offers a class method that can merge multiple data instances 
into a single one. You can not only combine multiple symbols, but also merge datasets for a single 
symbol—all done automatically!

```pycon title="Pull BTC datasets from various exchanges and plot them relative to their mean"
>>> binance_data = vbt.CCXTData.pull("BTCUSDT", exchange="binance")
>>> bybit_data = vbt.CCXTData.pull("BTCUSDT", exchange="bybit")
>>> bitfinex_data = vbt.CCXTData.pull("BTC/USDT", exchange="bitfinex")
>>> kucoin_data = vbt.CCXTData.pull("BTC-USDT", exchange="kucoin")

>>> data = vbt.Data.merge([
...     binance_data.rename({"BTCUSDT": "Binance"}),
...     bybit_data.rename({"BTCUSDT": "Bybit"}),
...     bitfinex_data.rename({"BTC/USDT": "Bitfinex"}),
...     kucoin_data.rename({"BTC-USDT": "KuCoin"}),
... ], missing_index="drop", silence_warnings=True)

>>> @njit
... def rescale_nb(x):
...     return (x - x.mean()) / x.mean()

>>> rescaled_close = data.close.vbt.row_apply(rescale_nb)
>>> rescaled_close = rescaled_close.vbt.rolling_mean(30)
>>> rescaled_close.loc["2023":"2023"].vbt.plot().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/data_merging.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/data_merging.dark.svg#only-dark){: .iimg loading=lazy }

## Alpaca

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_2.svg){ loading=lazy }

- [x] Welcome a new class specialized in pulling data from [Alpaca](https://alpaca.markets/)!

```pycon title="Get one week of adjusted 1-minute AAPL data from Alpaca"
>>> vbt.AlpacaData.set_custom_settings(
...     client_config=dict(
...         api_key="YOUR_API_KEY",
...         secret_key="YOUR_API_SECRET"
...     )
... )
>>> data = vbt.AlpacaData.pull(
...     "AAPL",
...     start="one week ago 00:00",  # (1)!
...     end="15 minutes ago",  # (2)!
...     timeframe="1 minute",
...     adjustment="all",
...     tz="US/Eastern"
... )
>>> data.get()
                               Open      High       Low     Close  Volume  \
Open time                                                                   
2023-01-30 04:00:00-05:00  145.5400  145.5400  144.0100  144.0200  5452.0   
2023-01-30 04:01:00-05:00  144.0800  144.0800  144.0000  144.0500  3616.0   
2023-01-30 04:02:00-05:00  144.0300  144.0400  144.0100  144.0100  1671.0   
2023-01-30 04:03:00-05:00  144.0100  144.0300  144.0000  144.0300  4721.0   
2023-01-30 04:04:00-05:00  144.0200  144.0200  144.0200  144.0200  1343.0   
...                             ...       ...       ...       ...     ...   
2023-02-03 19:54:00-05:00  154.3301  154.3301  154.3301  154.3301   347.0   
2023-02-03 19:55:00-05:00  154.3300  154.3400  154.3200  154.3400  1438.0   
2023-02-03 19:56:00-05:00  154.3400  154.3400  154.3300  154.3300   588.0   
2023-02-03 19:58:00-05:00  154.3500  154.3500  154.3500  154.3500   555.0   
2023-02-03 19:59:00-05:00  154.3400  154.3900  154.3300  154.3900  3835.0   

                           Trade count        VWAP  
Open time                                           
2023-01-30 04:00:00-05:00          165  144.376126  
2023-01-30 04:01:00-05:00           81  144.036336  
2023-01-30 04:02:00-05:00           52  144.035314  
2023-01-30 04:03:00-05:00           56  144.012680  
2023-01-30 04:04:00-05:00           40  144.021854  
...                                ...         ...  
2023-02-03 19:54:00-05:00           21  154.331340  
2023-02-03 19:55:00-05:00           38  154.331756  
2023-02-03 19:56:00-05:00           17  154.338971  
2023-02-03 19:58:00-05:00           27  154.343090  
2023-02-03 19:59:00-05:00           58  154.357219  

[4224 rows x 7 columns]
```

1. In the timezone provided via `tz`.
2. Remove if you have a paid plan.

## Local data

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] Once you have fetched remote data, you will most likely want to save it to disk. There are two 
new options for this: you can either serialize the entire data class, or save the actual data to 
CSV or HDF5. Each dataset can be stored in a single flat file, which makes handling the data 
easier than using a database. After saving, you can easily load the data back either by 
deserializing or by using data classes that specialize in loading from CSV and HDF5 files. 
These classes support a range of features, including filtering by row and datetime ranges, 
updating, chunking, and even a smart dataset search that can recursively walk through 
sub-directories and return datasets that match a specific glob pattern or regular expression :magnet:

```pycon title="Fetch and save symbols separately, then load them back jointly"
>>> btc_data = vbt.BinanceData.pull("BTCUSDT")
>>> eth_data = vbt.BinanceData.pull("ETHUSDT")

>>> btc_data.to_hdf()
>>> eth_data.to_hdf()

>>> data = vbt.BinanceData.from_hdf(start="2020", end="2021")
```

[=100% "Key 2/2"]{: .candystripe .candystripe-animate }

```pycon
>>> data.close
symbol                      BTCUSDT  ETHUSDT
Open time                                   
2020-01-01 00:00:00+00:00   7200.85   130.77
2020-01-02 00:00:00+00:00   6965.71   127.19
2020-01-03 00:00:00+00:00   7344.96   134.35
2020-01-04 00:00:00+00:00   7354.11   134.20
2020-01-05 00:00:00+00:00   7358.75   135.37
...                             ...      ...
2020-12-27 00:00:00+00:00  26281.66   685.11
2020-12-28 00:00:00+00:00  27079.41   730.41
2020-12-29 00:00:00+00:00  27385.00   732.00
2020-12-30 00:00:00+00:00  28875.54   752.17
2020-12-31 00:00:00+00:00  28923.63   736.42

[366 rows x 2 columns]
```

## And many more...

- [ ] Look forward to more killer features being added every week!

[:material-language-python: Python code](https://vectorbt.pro/pvt_6d1b3986/assets/jupytext/features/data.py.txt){ .md-button target="blank_" }