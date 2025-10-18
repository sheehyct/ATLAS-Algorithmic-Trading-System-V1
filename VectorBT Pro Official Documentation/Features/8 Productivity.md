---
title: Productivity
description: Productivity features of VectorBT PRO
icon: material/nut
---

# :material-nut: Productivity

## Iterated decorator

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_6_19.svg){ loading=lazy }

- [x] Thinking about parallelizing a for-loop? No need to hesitate—VBT has a decorator for that.

```pycon title="Emulate a parallelized nested loop to get Sharpe by year and month"
>>> import calendar

>>> @vbt.iterated(over_arg="year", merge_func="column_stack", engine="pathos")  # (1)!
... @vbt.iterated(over_arg="month", merge_func="concat")  # (2)!
... def get_year_month_sharpe(data, year, month):  # (3)!
...     mask = (data.index.year == year) & (data.index.month == month)
...     if not mask.any():
...         return np.nan
...     year_returns = data.loc[mask].returns
...     return year_returns.vbt.returns.sharpe_ratio()

>>> years = data.index.year.unique().sort_values().rename("year")
>>> months = data.index.month.unique().sort_values().rename("month")
>>> sharpe_matrix = get_year_month_sharpe(
...     data,
...     years,
...     {calendar.month_abbr[month]: month for month in months},  # (4)!
... )
>>> sharpe_matrix.transpose().vbt.heatmap(
...     trace_kwargs=dict(colorscale="RdBu", zmid=0), 
...     yaxis=dict(autorange="reversed")
... ).show()
```

1. Iterate over years (in parallel).
2. Iterate over months (sequentially).
3. The function is called for each combination of year and month.
4. Map month numbers to names and pass them as a dict. VBT will extract the keys and use them as labels.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/iterated_decorator.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/iterated_decorator.dark.svg#only-dark){: .iimg loading=lazy }

## Tasks

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_6_19.svg){ loading=lazy }

- [x] Testing multiple parameter combinations usually involves using the `@vbt.parameterized` decorator.
But what if you want to test entirely uncorrelated configurations or even different functions?
The latest addition to VBT lets you execute any sequence of unrelated tests in parallel
by assigning each test to a task.

```pycon title="Simulate SL, TSL, and TP parameters in three separate processes and compare their expectancy"
>>> data = vbt.YFData.pull("BTC-USD")

>>> task1 = vbt.Task(  # (1)!
...     vbt.PF.from_random_signals, 
...     data, 
...     n=100, seed=42,
...     sl_stop=vbt.Param(np.arange(1, 51) / 100)
... )
>>> task2 = vbt.Task(
...     vbt.PF.from_random_signals, 
...     data, 
...     n=100, seed=42,
...     tsl_stop=vbt.Param(np.arange(1, 51) / 100)
... )
>>> task3 = vbt.Task(
...     vbt.PF.from_random_signals, 
...     data, 
...     n=100, seed=42,
...     tp_stop=vbt.Param(np.arange(1, 51) / 100)
... )
>>> pf1, pf2, pf3 = vbt.execute([task1, task2, task3], engine="pathos")  # (2)!

>>> fig = pf1.trades.expectancy.rename("SL").vbt.plot()
>>> pf2.trades.expectancy.rename("TSL").vbt.plot(fig=fig)
>>> pf3.trades.expectancy.rename("TP").vbt.plot(fig=fig)
>>> fig.show()
```

1. A task consists of a function and the arguments you want to pass to that function.
Just creating a task does not execute the function!
2. Execute all three tasks using multiprocessing.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/tasks.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/tasks.dark.svg#only-dark){: .iimg loading=lazy }

## Nested progress bars

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_5_15.svg){ loading=lazy }

- [x] Progress bars are now aware of each other. When a new progress bar starts, it checks whether another
progress bar with the same identifier has already finished its task. If so, the new progress bar
will close itself and delegate its progress to the existing one.

```pycon title="Display progress of three parameters using nested progress bars"
>>> symbols = ["BTC-USD", "ETH-USD"]
>>> fast_windows = range(5, 105, 5)
>>> slow_windows = range(5, 105, 5)
>>> sharpe_ratios = dict()

>>> with vbt.ProgressBar(total=len(symbols), bar_id="pbar1") as pbar1:  # (1)!
...     for symbol in symbols:
...         pbar1.set_description(dict(symbol=symbol), refresh=True)
...         data = vbt.YFData.pull(symbol)
...         
...         with vbt.ProgressBar(total=len(fast_windows), bar_id="pbar2") as pbar2:  # (2)!
...             for fast_window in fast_windows:
...                 pbar2.set_description(dict(fast_window=fast_window), refresh=True)
...                 
...                 with vbt.ProgressBar(total=len(slow_windows), bar_id="pbar3") as pbar3:  # (3)!
...                     for slow_window in slow_windows:
...                         if fast_window < slow_window:
...                             pbar3.set_description(dict(slow_window=slow_window), refresh=True)
...                             fast_sma = data.run("talib_func:sma", fast_window)
...                             slow_sma = data.run("talib_func:sma", slow_window)
...                             entries = fast_sma.vbt.crossed_above(slow_sma)
...                             exits = fast_sma.vbt.crossed_below(slow_sma)
...                             pf = vbt.PF.from_signals(data, entries, exits)
...                             sharpe_ratios[(symbol, fast_window, slow_window)] = pf.sharpe_ratio
...                         pbar3.update()
...                         
...                 pbar2.update()
...                 
...         pbar1.update()
```

1. Track iteration over symbols.
2. Track iteration over fast windows.
3. Track iteration over slow windows.

[=100% "Symbol 2/2"]{: .candystripe .candystripe-animate }

[=100% "Fast window 20/20"]{: .candystripe .candystripe-animate }

[=100% "Slow window 20/20"]{: .candystripe .candystripe-animate }

```pycon
>>> sharpe_ratios = pd.Series(sharpe_ratios)
>>> sharpe_ratios.index.names = ["symbol", "fast_window", "slow_window"]
>>> sharpe_ratios
symbol   fast_window  slow_window
BTC-USD  5            10             1.063616
                      15             1.218345
                      20             1.273154
                      25             1.365664
                      30             1.394469
                                          ...
ETH-USD  80           90             0.582995
                      95             0.617568
         85           90             0.701215
                      95             0.616037
         90           95             0.566650
Length: 342, dtype: float64
```

## Annotations

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2023_12_23.svg){ loading=lazy }

- [x] When writing a function, you can specify the meaning of each argument using an annotation
immediately next to the argument. VBT now provides a rich set of in-house annotations tailored to specific
tasks. For example, whether an argument is a parameter can be specified directly in the function instead of
in the [parameterized decorator](https://vectorbt.pro/pvt_6d1b3986/features/optimization/#parameterized-decorator).

```pycon title="Test a cross-validation function with annotations"
>>> @vbt.cv_split(
...     splitter="from_rolling", 
...     splitter_kwargs=dict(length=365, split=0.5, set_labels=["train", "test"]),
...     parameterized_kwargs=dict(random_subset=100),
... )
... def sma_crossover_cv(
...     data: vbt.Takeable,  # (1)!
...     fast_period: vbt.Param(condition="x < slow_period"),  # (2)!
...     slow_period: vbt.Param,  # (3)!
...     metric
... ) -> vbt.MergeFunc("concat"):
...     fast_sma = data.run("sma", fast_period, hide_params=True)
...     slow_sma = data.run("sma", slow_period, hide_params=True)
...     entries = fast_sma.real_crossed_above(slow_sma)
...     exits = fast_sma.real_crossed_below(slow_sma)
...     pf = vbt.PF.from_signals(data, entries, exits, direction="both")
...     return pf.deep_getattr(metric)

>>> sma_crossover_cv(
...     vbt.YFData.pull("BTC-USD", start="4 years ago"),
...     np.arange(20, 50),
...     np.arange(20, 50),
...     "trades.expectancy"
... )
split  set    fast_period  slow_period
0      train  22           33             26.351841
       test   21           34             35.788733
1      train  21           46             24.114027
       test   21           39              2.261432
2      train  30           44             29.635233
       test   30           38              1.909916
3      train  20           49             -7.038924
       test   20           44             -1.366734
4      train  28           44              2.144805
       test   29           38             -4.945776
5      train  35           47             -8.877875
       test   34           37              2.792217
6      train  29           41              8.816846
       test   28           43             36.008302
dtype: float64
```

1. The passed argument must be takeable (for selecting subsets by split).
2. Parameter with a condition requiring it to be less than the slow period.
3. Parameter for the slow period.

## DataFrame product

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_13_0.svg){ loading=lazy }

- [x] Several parameterized indicators can produce DataFrames with different shapes and columns,
which makes creating a Cartesian product tricky because they often share common column levels 
(such as "symbol") that should not be combined. There is now a method to cross-join 
multiple DataFrames block-wise.

```pycon title="Enter when SMA goes above WMA, exit when EMA goes below WMA"
>>> data = vbt.YFData.pull(["BTC-USD", "ETH-USD"], missing_index="drop")
>>> sma = data.run("sma", timeperiod=[10, 20], unpack=True)
>>> ema = data.run("ema", timeperiod=[30, 40], unpack=True)
>>> wma = data.run("wma", timeperiod=[50, 60], unpack=True)
>>> sma, ema, wma = sma.vbt.x(ema, wma)  # (1)!
>>> entries = sma.vbt.crossed_above(wma)
>>> exits = ema.vbt.crossed_below(wma)

>>> entries.columns
MultiIndex([(10, 30, 50, 'BTC-USD'),
            (10, 30, 50, 'ETH-USD'),
            (10, 30, 60, 'BTC-USD'),
            (10, 30, 60, 'ETH-USD'),
            (10, 40, 50, 'BTC-USD'),
            (10, 40, 50, 'ETH-USD'),
            (10, 40, 60, 'BTC-USD'),
            (10, 40, 60, 'ETH-USD'),
            (20, 30, 50, 'BTC-USD'),
            (20, 30, 50, 'ETH-USD'),
            (20, 30, 60, 'BTC-USD'),
            (20, 30, 60, 'ETH-USD'),
            (20, 40, 50, 'BTC-USD'),
            (20, 40, 50, 'ETH-USD'),
            (20, 40, 60, 'BTC-USD'),
            (20, 40, 60, 'ETH-USD')],
           names=['sma_timeperiod', 'ema_timeperiod', 'wma_timeperiod', 'symbol'])
```

1. Build a Cartesian product of three DataFrames while keeping the column level "symbol" untouched.
This can also be done with `vbt.pd_acc.cross(sma, ema, wma)`.

## Compression

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_10_0.svg){ loading=lazy }

- [x] Serialized VBT objects can sometimes use a lot of disk space. With this update, 
VBT now supports a variety of compression algorithms to make files as light as possible! :feather:

```pycon title="Save data without and with compression"
>>> data = vbt.RandomOHLCData.pull("RAND", start="2022", end="2023", timeframe="1 minute")

>>> file_path = data.save()
>>> print(vbt.file_size(file_path))
21.0 MB

>>> file_path = data.save(compression="blosc")
>>> print(vbt.file_size(file_path))
13.3 MB
```

## Faster loading

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_10_0.svg){ loading=lazy }

- [x] If your pipeline does not need accessors, Plotly graphs, or most other optional 
features, you can disable the auto-import feature entirely to reduce VBT's loading 
time to under a second :hourglass_flowing_sand:

```ini title="Define importing settings in vbt.ini"
[importing]
auto_import = False
```

```pycon title="Measure the loading time"
>>> start = utc_time()
>>> from vectorbtpro import *
>>> end = utc_time()
>>> end - start
0.580937910079956
```

## Configuration files

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_9_0.svg){ loading=lazy }

- [x] VBT extends [configparser](https://docs.python.org/3/library/configparser.html) to define its 
own configuration format that allows users to save, introspect, modify, and load any complex 
in-house object. The main advantages of this format are readability and round-tripping: any object can 
be encoded and then decoded back without loss of information. The main features include nested structures, 
references, literal parsing, and evaluation of arbitrary Python expressions. Additionally, 
you can now create a configuration file for VBT and place it in the working directory—
it will be used to update the default settings whenever the package is imported.

```ini title="Define global settings in vbt.ini"
[plotting]
default_theme = dark

[portfolio]
init_cash = 5000

[data.custom.binance.client_config]
api_key = YOUR_API_KEY
api_secret = YOUR_API_SECRET

[data.custom.ccxt.exchanges.binance.exchange_config]
apiKey = &data.custom.binance.client_config.api_key
secret = &data.custom.binance.client_config.api_secret
```

```pycon title="Verify that the settings have been loaded correctly"
>>> from vectorbtpro import *

>>> vbt.settings.portfolio["init_cash"]
5000
```

## Serialization

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_9_0.svg){ loading=lazy }

- [x] Just like machine learning models, every native VBT object can be serialized and saved to 
a binary file. It has never been easier to share data and insights! Another benefit is that only the 
actual content of each object is serialized, not its class definition, so the loaded object 
always uses the most up-to-date class definition. There is also special logic implemented 
to help you "reconstruct" objects if VBT introduces any breaking API changes :construction_site:

```pycon title="Backtest each month of data and save the results for later"
>>> data = vbt.YFData.pull("BTC-USD", start="2022-01-01", end="2022-06-01")

>>> def backtest_month(close):
...     return vbt.PF.from_random_signals(close, n=10)

>>> month_pfs = data.close.resample(vbt.offset("M")).apply(backtest_month)
>>> month_pfs
Date
2022-01-01 00:00:00+00:00    Portfolio(\n    wrapper=ArrayWrapper(\n       ...
2022-02-01 00:00:00+00:00    Portfolio(\n    wrapper=ArrayWrapper(\n       ...
2022-03-01 00:00:00+00:00    Portfolio(\n    wrapper=ArrayWrapper(\n       ...
2022-04-01 00:00:00+00:00    Portfolio(\n    wrapper=ArrayWrapper(\n       ...
2022-05-01 00:00:00+00:00    Portfolio(\n    wrapper=ArrayWrapper(\n       ...
Freq: MS, Name: Close, dtype: object

>>> vbt.save(month_pfs, "month_pfs")  # (1)!

>>> month_pfs = vbt.load("month_pfs")  # (2)!
>>> month_pfs.apply(lambda pf: pf.total_return)
Date
2022-01-01 00:00:00+00:00   -0.048924
2022-02-01 00:00:00+00:00    0.168370
2022-03-01 00:00:00+00:00    0.016087
2022-04-01 00:00:00+00:00   -0.120525
2022-05-01 00:00:00+00:00    0.110751
Freq: MS, Name: Close, dtype: float64
```

1. Save to disk.
2. Load from disk later.

## Data parsing

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_3_0.svg){ loading=lazy }

- [x] Tired of passing open, high, low, and close as separate time series? Portfolio class methods 
now accept a data instance instead of just close and automatically extract the contained OHLC data. 
This small but handy feature saves you time!

```pycon title="Run the example above using the new approach"
>>> data = vbt.YFData.pull("BTC-USD", start="2020-01", end="2020-03")
>>> pf = vbt.PF.from_random_signals(data, n=10)
```

## Index dictionaries

Manually creating arrays and setting their data with Pandas can often be challenging. Luckily, there 
is now a feature that offers much-needed assistance! Any broadcastable argument can become an index 
dictionary, which contains instructions on where to set values in the array and fills them in for you. 
It knows exactly which axis needs to be updated and does not create a full array unless necessary, 
saving RAM :heart:

```pycon title="1) Accumulate daily and exit on Sunday vs 2) accumulate weekly and exit on month end"
>>> data = vbt.YFData.pull(["BTC-USD", "ETH-USD"])
>>> tile = pd.Index(["daily", "weekly"], name="strategy")  # (1)!
>>> pf = vbt.PF.from_orders(
...     data.close,
...     size=vbt.index_dict({  # (2)!
...         vbt.idx(
...             vbt.pointidx(every="day"), 
...             vbt.colidx("daily", level="strategy")): 100,  # (3)!
...         vbt.idx(
...             vbt.pointidx(every="sunday"), 
...             vbt.colidx("daily", level="strategy")): -np.inf,  # (4)!
...         vbt.idx(
...             vbt.pointidx(every="monday"), 
...             vbt.colidx("weekly", level="strategy")): 100,
...         vbt.idx(
...             vbt.pointidx(every="monthend"), 
...             vbt.colidx("weekly", level="strategy")): -np.inf,
...     }),
...     size_type="value",
...     direction="longonly",
...     init_cash="auto",
...     broadcast_kwargs=dict(tile=tile)
... )
>>> pf.sharpe_ratio
strategy  symbol 
daily     BTC-USD    0.702259
          ETH-USD    0.782296
weekly    BTC-USD    0.838895
          ETH-USD    0.524215
Name: sharpe_ratio, dtype: float64
```

1. To represent two strategies, you need to tile the same data twice. Create a parameter with
strategy names and pass it as `tile` to the broadcaster so it tiles the columns of each array
(such as price) twice.
2. The index dictionary includes index instructions as keys and data as values to set.
Keys can be row indices, labels, or custom indexer classes such as 
[PointIdxr](https://vectorbt.pro/pvt_6d1b3986/api/base/indexing/#vectorbtpro.base.indexing.PointIdxr).
3. Find the indices of the rows for the start of each day and the column index of "daily", then
set each element at those indices to 100 (= accumulate).
4. Find the indices of the rows that correspond to Sunday. If any value at those indices has already 
been set by a previous instruction, it will be overridden.

## Slicing

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_3_0.svg){ loading=lazy }

- [x] Similar to selecting columns, each VBT object can now slice rows using the
same mechanism as in Pandas :knife: This makes it easy to analyze and plot any subset of 
simulated data, without needing to re-simulate!

```pycon title="Analyze multiple date ranges of the same portfolio"
>>> data = vbt.YFData.pull("BTC-USD")
>>> pf = vbt.PF.from_holding(data, freq="d")

>>> pf.sharpe_ratio
1.116727709477293

>>> pf.loc[:"2020"].sharpe_ratio  # (1)!
1.2699801554196481

>>> pf.loc["2021": "2021"].sharpe_ratio  # (2)!
0.9825161170278687

>>> pf.loc["2022":].sharpe_ratio  # (3)!
-1.0423271337174647
```

1. Get the Sharpe ratio during the year 2020 and before.
2. Get the Sharpe ratio during the year 2021.
3. Get the Sharpe ratio during the year 2022 and after.

## Column stacking

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_3_0.svg){ loading=lazy }

- [x] Complex VBT objects of the same type can be easily stacked along columns. For example, 
you can combine multiple unrelated trading strategies into one portfolio for analysis. 
Under the hood, the final object is still represented as a monolithic multi-dimensional structure 
that can be processed even faster than separate merged objects :lungs:

```pycon title="Analyze two trading strategies separately and then jointly"
>>> def strategy1(data):
...     fast_ma = vbt.MA.run(data.close, 50, short_name="fast_ma")
...     slow_ma = vbt.MA.run(data.close, 200, short_name="slow_ma")
...     entries = fast_ma.ma_crossed_above(slow_ma)
...     exits = fast_ma.ma_crossed_below(slow_ma)
...     return vbt.PF.from_signals(
...         data.close, 
...         entries, 
...         exits, 
...         size=100,
...         size_type="value",
...         init_cash="auto"
...     )

>>> def strategy2(data):
...     bbands = vbt.BBANDS.run(data.close, window=14)
...     entries = bbands.close_crossed_below(bbands.lower)
...     exits = bbands.close_crossed_above(bbands.upper)
...     return vbt.PF.from_signals(
...         data.close, 
...         entries, 
...         exits, 
...         init_cash=200
...     )

>>> data1 = vbt.BinanceData.pull("BTCUSDT")
>>> pf1 = strategy1(data1)  # (1)!
>>> pf1.sharpe_ratio
0.9100317671866922

>>> data2 = vbt.BinanceData.pull("ETHUSDT")
>>> pf2 = strategy2(data2)  # (2)!
>>> pf2.sharpe_ratio
-0.11596286232734827

>>> pf_sep = vbt.PF.column_stack((pf1, pf2))  # (3)!
>>> pf_sep.sharpe_ratio
0    0.910032
1   -0.115963
Name: sharpe_ratio, dtype: float64

>>> pf_join = vbt.PF.column_stack((pf1, pf2), group_by=True)  # (4)!
>>> pf_join.sharpe_ratio
0.42820898354646514
```

1. Analyze the first strategy in its own portfolio.
2. Analyze the second strategy in its own portfolio.
3. Analyze both strategies separately in the same portfolio.
4. Analyze both strategies jointly in the same portfolio.

## Row stacking

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_3_0.svg){ loading=lazy }

- [x] Complex VBT objects of the same type can be easily stacked along rows. For example, 
you can append new data to an existing portfolio, or concatenate in-sample portfolios with 
their out-of-sample counterparts :dna:

```pycon title="Analyze two date ranges separately and then jointly"
>>> def strategy(data, start=None, end=None):
...     fast_ma = vbt.MA.run(data.close, 50, short_name="fast_ma")
...     slow_ma = vbt.MA.run(data.close, 200, short_name="slow_ma")
...     entries = fast_ma.ma_crossed_above(slow_ma)
...     exits = fast_ma.ma_crossed_below(slow_ma)
...     return vbt.PF.from_signals(
...         data.close[start:end], 
...         entries[start:end], 
...         exits[start:end], 
...         size=100,
...         size_type="value",
...         init_cash="auto"
...     )

>>> data = vbt.BinanceData.pull("BTCUSDT")

>>> pf_whole = strategy(data)  # (1)!
>>> pf_whole.sharpe_ratio
0.9100317671866922

>>> pf_sub1 = strategy(data, end="2019-12-31")  # (2)!
>>> pf_sub1.sharpe_ratio
0.7810397448678937

>>> pf_sub2 = strategy(data, start="2020-01-01")  # (3)!
>>> pf_sub2.sharpe_ratio
1.070339534746574

>>> pf_join = vbt.PF.row_stack((pf_sub1, pf_sub2))  # (4)!
>>> pf_join.sharpe_ratio
0.9100317671866922
```

1. Analyze the entire range.
2. Analyze the first date range.
3. Analyze the second date range.
4. Combine both date ranges and analyze them together.

## Index alignment

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_3_0.svg){ loading=lazy }

- [x] There is no longer a limitation requiring each Pandas array to have the same index.
Indexes of all arrays that should broadcast against each other are automatically aligned, as long as they
have the same data type.

```pycon title="Predict ETH price with BTC price using linear regression"
>>> btc_data = vbt.YFData.pull("BTC-USD")
>>> btc_data.wrapper.shape
(2817, 7)

>>> eth_data = vbt.YFData.pull("ETH-USD")  # (1)!
>>> eth_data.wrapper.shape
(1668, 7)

>>> ols = vbt.OLS.run(  # (2)!
...     btc_data.close,
...     eth_data.close
... )
>>> ols.pred
Date
2014-09-17 00:00:00+00:00            NaN
2014-09-18 00:00:00+00:00            NaN
2014-09-19 00:00:00+00:00            NaN
2014-09-20 00:00:00+00:00            NaN
2014-09-21 00:00:00+00:00            NaN
...                                  ...
2022-05-30 00:00:00+00:00    2109.769242
2022-05-31 00:00:00+00:00    2028.856767
2022-06-01 00:00:00+00:00    1911.555689
2022-06-02 00:00:00+00:00    1930.169725
2022-06-03 00:00:00+00:00    1882.573170
Freq: D, Name: Close, Length: 2817, dtype: float64
```

1. ETH-USD history is shorter than BTC-USD history.
2. This now works! Make sure all arrays share the same timeframe and timezone.

## Numba datetime

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_2_3.svg){ loading=lazy }

- [x] Numba does not support datetime indexes (or any other Pandas objects). There are 
also no built-in Numba functions for working with datetime. So, how do you connect data to time? VBT
addresses this gap by implementing a collection of functions to extract various information
from each timestamp, such as the current time and day of the week, to determine whether the bar
is during trading hours.

!!! example "Tutorial"
    Learn more in the [Signal development](https://vectorbt.pro/pvt_6d1b3986/tutorials/signal-development) tutorial.

```pycon title="Plot the percentage change from the start of the month to now"
>>> @njit
... def month_start_pct_change_nb(arr, index):
...     out = np.full(arr.shape, np.nan)
...     for col in range(arr.shape[1]):
...         for i in range(arr.shape[0]):
...             if i == 0 or vbt.dt_nb.month_nb(index[i - 1]) != vbt.dt_nb.month_nb(index[i]):
...                 month_start_value = arr[i, col]
...             else:
...                 out[i, col] = (arr[i, col] - month_start_value) / month_start_value
...     return out
    
>>> data = vbt.YFData.pull(["BTC-USD", "ETH-USD"], start="2022", end="2023")
>>> pct_change = month_start_pct_change_nb(
...     vbt.to_2d_array(data.close), 
...     data.index.vbt.to_ns()  # (1)!
... )
>>> pct_change = data.symbol_wrapper.wrap(pct_change)
>>> pct_change.vbt.plot().show()
```

1. Convert the datetime index to nanosecond format.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/numba_datetime.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/numba_datetime.dark.svg#only-dark){: .iimg loading=lazy }

## Periods ago

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_2_3.svg){ loading=lazy }

- [x] Instead of writing Numba functions, comparing values at different bars can also be done in a vectorized
way with Pandas. The problem is that there are no built-in functions to easily shift values based on 
timedeltas, nor are there rolling functions to check whether an event happened during a past 
period. This gap is filled by various new accessor methods.

!!! example "Tutorial"
    Learn more in the [Signal development](https://vectorbt.pro/pvt_6d1b3986/tutorials/signal-development) tutorial.

```pycon title="Check whether the price dropped for 5 consecutive bars"
>>> data = vbt.YFData.pull("BTC-USD", start="2022-05", end="2022-08")
>>> mask = (data.close < data.close.vbt.ago(1)).vbt.all_ago(5)
>>> fig = data.plot(plot_volume=False)
>>> mask.vbt.signals.ranges.plot_shapes(
...     plot_close=False, 
...     fig=fig, 
...     shape_kwargs=dict(fillcolor="orangered")
... )
>>> fig.show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/periods_ago.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/periods_ago.dark.svg#only-dark){: .iimg loading=lazy }

## Safe resampling

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_1_2.svg){ loading=lazy }

- [x] [Look-ahead bias](https://www.investopedia.com/terms/l/lookaheadbias.asp) is an ongoing 
risk when working with array data, especially on multiple time frames. Using Pandas alone is strongly
discouraged because it does not recognize that financial data mainly involves bars where timestamps are 
the opening times, and events may occur at any time between bars. Pandas thus incorrectly assumes that 
timestamps indicate the exact time of an event. In VBT, there is a complete collection of functions and 
classes for safely resampling and analyzing data!

!!! example "Tutorial"
    Learn more in the [MTF analysis](https://vectorbt.pro/pvt_6d1b3986/tutorials/mtf-analysis) tutorial.

```pycon title="Calculate SMA on multiple time frames and display on the same chart"
>>> def mtf_sma(close, close_freq, target_freq, timeperiod=5):
...     target_close = close.vbt.realign_closing(target_freq)  # (1)!
...     target_sma = vbt.talib("SMA").run(target_close, timeperiod=timeperiod).real  # (2)!
...     target_sma = target_sma.rename(f"SMA ({target_freq})")
...     return target_sma.vbt.realign_closing(close.index, freq=close_freq)  # (3)!

>>> data = vbt.YFData.pull("BTC-USD", start="2020", end="2023")
>>> fig = mtf_sma(data.close, "D", "daily").vbt.plot()
>>> mtf_sma(data.close, "D", "weekly").vbt.plot(fig=fig)
>>> mtf_sma(data.close, "D", "monthly").vbt.plot(fig=fig)
>>> fig.show()
```

1. Resample the source frequency to the target frequency. Since Close occurs at the end of the bar,
resample it as a "closing event".
2. Calculate the SMA on the target frequency.
3. Resample the target frequency back to the source frequency to show
multiple time frames on the same chart. Because `close` contains gaps, you cannot simply resample to `close_freq`
as this might produce unaligned series. Instead, resample directly to the index of `close`.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/safe_resampling.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/safe_resampling.dark.svg#only-dark){: .iimg loading=lazy }

## Resamplable objects

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_1_2.svg){ loading=lazy }

- [x] You can resample not only time series, but also complex VBT objects! Under the hood,
each object is made up of a collection of array-like attributes, so resampling means aggregating
all the related information together. This is especially helpful if you want to simulate at a higher
frequency for maximum accuracy and then analyze at a lower frequency for better speed.

!!! example "Tutorial"
    Learn more in the [MTF analysis](https://vectorbt.pro/pvt_6d1b3986/tutorials/mtf-analysis) tutorial.

```pycon title="Plot the monthly return heatmap of a random portfolio"
>>> import calendar

>>> data = vbt.YFData.pull("BTC-USD", start="2018", end="2023")
>>> pf = vbt.PF.from_random_signals(data, n=100, direction="both")
>>> mo_returns = pf.resample("M").returns  # (1)!
>>> mo_return_matrix = pd.Series(
...     mo_returns.values, 
...     index=pd.MultiIndex.from_arrays([
...         mo_returns.index.year,
...         mo_returns.index.month
...     ], names=["year", "month"])
... ).unstack("month")
>>> mo_return_matrix.columns = mo_return_matrix.columns.map(lambda x: calendar.month_abbr[x])
>>> mo_return_matrix.vbt.heatmap(
...     is_x_category=True,
...     trace_kwargs=dict(zmid=0, colorscale="Spectral")
... ).show()
```

1. Resample the entire portfolio to monthly frequency and calculate the returns.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/monthly_return_heatmap.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/monthly_return_heatmap.dark.svg#only-dark){: .iimg loading=lazy }

## Formatting engine

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_2.svg){ loading=lazy }

- [x] VBT is a comprehensive library that defines thousands of classes, functions, and objects.
When working with these, you may want to "look inside" an object to better understand
its attributes and contents. Fortunately, there is a formatting engine that can accurately format
any in-house object as a human-readable string. Did you know the API documentation is partly
powered by this engine? :wink:

```pycon title="Introspect a data instance"
>>> data = vbt.YFData.pull("BTC-USD", start="2020", end="2021")

>>> vbt.pprint(data)  # (1)!
YFData(
    wrapper=ArrayWrapper(...),
    data=symbol_dict({
        'BTC-USD': <pandas.core.frame.DataFrame object at 0x7f7f1fbc6cd0 with shape (366, 7)>
    }),
    single_key=True,
    classes=symbol_dict(),
    fetch_kwargs=symbol_dict({
        'BTC-USD': dict(
            start='2020',
            end='2021'
        )
    }),
    returned_kwargs=symbol_dict({
        'BTC-USD': dict()
    }),
    last_index=symbol_dict({
        'BTC-USD': Timestamp('2020-12-31 00:00:00+0000', tz='UTC')
    }),
    tz_localize=datetime.timezone.utc,
    tz_convert='UTC',
    missing_index='nan',
    missing_columns='raise'
)

>>> vbt.pdir(data)  # (2)!
                                            type                                             path
attr                                                                                                     
align_columns                        classmethod                       vectorbtpro.data.base.Data
align_index                          classmethod                       vectorbtpro.data.base.Data
build_feature_config_doc             classmethod                       vectorbtpro.data.base.Data
...                                          ...                                              ...
vwap                                    property                       vectorbtpro.data.base.Data
wrapper                                 property               vectorbtpro.base.wrapping.Wrapping
xs                                      function          vectorbtpro.base.indexing.PandasIndexer

>>> vbt.phelp(data.get)  # (3)!
YFData.get(
    columns=None,
    symbols=None,
    **kwargs
):
    Get one or more columns of one or more symbols of data.
```

1. Similar to Python's `print` command, pretty-prints the contents of any VBT object.
2. Similar to Python's `dir` command, pretty-prints the attributes of a class, object, or module.
3. Similar to Python's `help` command, pretty-prints the signature and docstring of a function.

## Meta methods

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] Many methods, such as rolling apply, now come in two versions: regular (instance methods)
and meta (class methods). Regular methods are bound to a single array and do not need metadata,
while meta methods are not tied to any array and act as micro-pipelines with their own
broadcasting and templating logic. Here, VBT solves one of the main Pandas limitations:
the inability to apply a function to multiple arrays at once.

```pycon title="Compute the rolling z-score on one array and the rolling correlation coefficient on two arrays"
>>> @njit
... def zscore_nb(x):  # (1)!
...     return (x[-1] - np.mean(x)) / np.std(x)

>>> data = vbt.YFData.pull("BTC-USD", start="2020", end="2021")
>>> data.close.rolling(14).apply(zscore_nb, raw=True)  # (2)!
Date
2020-01-01 00:00:00+00:00         NaN
                                  ...
2020-12-27 00:00:00+00:00    1.543527
2020-12-28 00:00:00+00:00    1.734715
2020-12-29 00:00:00+00:00    1.755125
2020-12-30 00:00:00+00:00    2.107147
2020-12-31 00:00:00+00:00    1.781800
Freq: D, Name: Close, Length: 366, dtype: float64

>>> data.close.vbt.rolling_apply(14, zscore_nb)  # (3)!
2020-01-01 00:00:00+00:00         NaN
                                  ...
2020-12-27 00:00:00+00:00    1.543527
2020-12-28 00:00:00+00:00    1.734715
2020-12-29 00:00:00+00:00    1.755125
2020-12-30 00:00:00+00:00    2.107147
2020-12-31 00:00:00+00:00    1.781800
Freq: D, Name: Close, Length: 366, dtype: float64

>>> @njit
... def corr_meta_nb(from_i, to_i, col, a, b):  # (4)!
...     a_window = a[from_i:to_i, col]
...     b_window = b[from_i:to_i, col]
...     return np.corrcoef(a_window, b_window)[1, 0]

>>> data2 = vbt.YFData.pull(["ETH-USD", "XRP-USD"], start="2020", end="2021")
>>> vbt.pd_acc.rolling_apply(  # (5)!
...     14, 
...     corr_meta_nb, 
...     vbt.Rep("a"),
...     vbt.Rep("b"),
...     broadcast_named_args=dict(a=data.close, b=data2.close)
... )
symbol                      ETH-USD   XRP-USD
Date                                         
2020-01-01 00:00:00+00:00       NaN       NaN
...                             ...       ...
2020-12-27 00:00:00+00:00  0.636862 -0.511303
2020-12-28 00:00:00+00:00  0.674514 -0.622894
2020-12-29 00:00:00+00:00  0.712531 -0.773791
2020-12-30 00:00:00+00:00  0.839355 -0.772295
2020-12-31 00:00:00+00:00  0.878897 -0.764446

[366 rows x 2 columns]
```

1. Provides access to the window only.
2. Using Pandas.
3. Using the regular method, which accepts the same function as Pandas.
4. Provides access to one or more entire arrays.
5. Using the meta method, which accepts metadata and variable arguments.

## Array expressions

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] When combining multiple arrays, they often need to be aligned and broadcast before
the operation itself. Pandas alone often falls short because it can be too strict.
Fortunately, VBT includes an accessor class method that can take a regular Python expression,
identify all variable names, extract the arrays from the current context, broadcast them,
and then evaluate the expression (with support for [NumExpr](https://github.com/pydata/numexpr)!) :keyboard:

```pycon title="Evaluate a multiline array expression based on a Bollinger Bands indicator"
>>> data = vbt.YFData.pull(["BTC-USD", "ETH-USD"])

>>> low = data.low
>>> high = data.high
>>> bb = vbt.talib("BBANDS").run(data.close)
>>> upperband = bb.upperband
>>> lowerband = bb.lowerband
>>> bandwidth = (bb.upperband - bb.lowerband) / bb.middleband
>>> up_th = vbt.Param([0.3, 0.4]) 
>>> low_th = vbt.Param([0.1, 0.2])

>>> expr = """
... narrow_bands = bandwidth < low_th
... above_upperband = high > upperband
... wide_bands = bandwidth > up_th
... below_lowerband = low < lowerband
... (narrow_bands & above_upperband) | (wide_bands & below_lowerband)
... """
>>> mask = vbt.pd_acc.eval(expr)
>>> mask.sum()
low_th  up_th  symbol 
0.1     0.3    BTC-USD    344
               ETH-USD    171
        0.4    BTC-USD    334
               ETH-USD    158
0.2     0.3    BTC-USD    444
               ETH-USD    253
        0.4    BTC-USD    434
               ETH-USD    240
dtype: int64
```

## Resource management

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] New profiling tools help you measure the execution time and memory usage of any code block :toolbox:

```pycon title="Profile getting the Sharpe ratio of a random portfolio"
>>> data = vbt.YFData.pull("BTC-USD")

>>> with (
...     vbt.Timer() as timer, 
...     vbt.MemTracer() as mem_tracer
... ):
...     print(vbt.PF.from_random_signals(data.close, n=100).sharpe_ratio)
0.33111243921865163

>>> print(timer.elapsed())
74.15 milliseconds

>>> print(mem_tracer.peak_usage())
459.7 kB
```

## Templates

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] It is easy to extend classes, but since VBT revolves around functions, how do we enhance them or
change their workflow? The easiest way is to introduce a small function (i.e., callback) that the user
can provide and that the main function calls at some point. However, this would require the main function
to know what arguments to pass to the callback and how to handle its outputs. Here is a better idea:
allow most arguments of the main function to become callbacks, then execute those to obtain their actual
values. These arguments are called "templates" and this process is known as "substitution".
Templates are especially useful when some arguments (such as arrays) should be built only
once all required information is available, for example, when other arrays have already been broadcast.
Each substitution opportunity has its own identifier so you can control when a template
should be substituted. In VBT, templates are first-class citizens and are integrated into most
functions for unmatched flexibility! :genie:

```pycon title="Design a template-enhanced resampling functionality"
>>> def resample_apply(index, by, apply_func, *args, template_context={}, **kwargs):
...     grouper = index.vbt.get_grouper(by)  # (1)!
...     results = {}
...     with vbt.ProgressBar() as pbar:
...         for group, group_idxs in grouper:  # (2)!
...             group_index = index[group_idxs]
...             context = {"group": group, "group_index": group_index, **template_context}  # (3)!
...             final_apply_func = vbt.substitute_templates(apply_func, context, eval_id="apply_func")  # (4)!
...             final_args = vbt.substitute_templates(args, context, eval_id="args")
...             final_kwargs = vbt.substitute_templates(kwargs, context, eval_id="kwargs")
...             results[group] = final_apply_func(*final_args, **final_kwargs)
...             pbar.update()
...     return pd.Series(results)

>>> data = vbt.YFData.pull(["BTC-USD", "ETH-USD"], missing_index="drop")
>>> resample_apply(
...     data.index, "Y", 
...     lambda x, y: x.corr(y),  # (5)!
...     vbt.RepEval("btc_close[group_index]"),  # (6)!
...     vbt.RepEval("eth_close[group_index]"),
...     template_context=dict(
...         btc_close=data.get("Close", "BTC-USD"),  # (7)!
...         eth_close=data.get("Close", "ETH-USD")
...     )
... )
```

1. Builds a grouper. Accepts both group-by and resample instructions.
2. Iterates over groups in the grouper. Each group contains a label (such as `2017-01-01 00:00:00+00:00`)
and the row indices corresponding to this label.
3. Creates a new context with information about the current group and any external information provided
by the user.
4. Substitutes the function and arguments using the newly populated context.
5. Simple function to compute the correlation coefficient between two arrays.
6. Defines both arguments as expression templates where data is selected for each group. 
All variables in these expressions will be automatically recognized and replaced by the current context.
After evaluation, the templates will be replaced by their outputs.
7. Specifies any additional information your templates depend on.

[=100% "Group 7/7"]{: .candystripe .candystripe-animate }

```pycon
2017    0.808930
2018    0.897112
2019    0.753659
2020    0.940741
2021    0.553255
2022    0.975911
2023    0.974914
Freq: A-DEC, dtype: float64
```

## And many more...

- [ ] Look forward to more killer features being added every week!

[:material-language-python: Python code](https://vectorbt.pro/pvt_6d1b3986/assets/jupytext/features/productivity.py.txt){ .md-button target="blank_" }