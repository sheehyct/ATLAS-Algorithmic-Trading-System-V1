\---
title: Stop signals
description: Learn how to analyze and apply stop signals using VectorBT PRO
icon: material/select-compare
---

# :material-select-compare: Stop signals

Our goal is to use large-scale backtesting to compare the performance of trading with and without stop
loss (SL), trailing stop (TS), and take profit (TP) signals. To ensure this analysis is comprehensive,
we will conduct a large number of experiments across three dimensions: instruments, time, and
parameters.

First, we will select 10 cryptocurrencies by market capitalization (excluding stablecoins such as USDT)
and gather 3 years of their daily pricing data. Specifically, we will backtest the period from 2018 to
2021, as this range includes periods of sharp price declines (such as corrections after the all-time
high in December 2017 and during the coronavirus crisis in March 2020) as well as surges (the all-time
high in December 2020). This provides a balanced perspective. For each instrument, we will split this
period into 400 smaller, overlapping time windows, each lasting 6 months. We will run our tests on each
of these windows to account for different market conditions. For each instrument and time window, we
will generate an entry signal at the very first bar and determine an exit signal according to the stop
configuration. We will test 100 stop values, increasing by 1% increments, and compare the performance
of each one to trading randomly and holding during that specific time window. In total, we will conduct
2,000,000 tests.

!!! important
    Make sure you have at least 16 GB of free RAM available, or memory swapping enabled.

## Parameters

The first step is to define the parameters of the analysis pipeline. As discussed above, we will
backtest 3 years of pricing data, use 400 time windows, 10 cryptocurrencies, and 100 stop values. We
will also set fees and slippage to 0.25% each, and the initial capital to $100. The absolute amount
does not matter, but it must be consistent across all assets to allow for direct comparison. Feel free
to change any parameter of interest.

\`\`\`pycon
>>> from vectorbtpro import \*
>>> import ipywidgets

>>> seed = 42
>>> symbols = \[
...     "BTC-USD", "ETH-USD", "XRP-USD", "BCH-USD", "LTC-USD", 
...     "BNB-USD", "EOS-USD", "XLM-USD", "XMR-USD", "ADA-USD"
... \]
>>> start\_date = vbt.utc\_timestamp("2018-01-01")
>>> end\_date = vbt.utc\_timestamp("2021-01-01")
>>> time\_delta = end\_date - start\_date
>>> window\_len = vbt.timedelta("180d")
>>> window\_cnt = 400
>>> exit\_types = \["SL", "TS", "TP", "Random", "Holding"\]
>>> step = 0.01  # (1)!
>>> stops = np.arange(step, 1 + step, step)

>>> vbt.settings.wrapping\["freq"\] = "d"
>>> vbt.settings.plotting\["layout"\]\["template"\] = "vbt\_dark"
>>> vbt.settings.portfolio\["init\_cash"\] = 100.  # (2)!
>>> vbt.settings.portfolio\["fees"\] = 0.0025  # (3)!
>>> vbt.settings.portfolio\["slippage"\] = 0.0025  # (4)!

>>> pd.Series({
...     "Start date": start\_date,
...     "End date": end\_date,
...     "Time period (days)": time\_delta.days,
...     "Assets": len(symbols),
...     "Window length": window\_len,
...     "Windows": window\_cnt,
...     "Exit types": len(exit\_types),
...     "Stop values": len(stops),
...     "Tests per asset": window\_cnt \* len(stops) \* len(exit\_types),
...     "Tests per window": len(symbols) \* len(stops) \* len(exit\_types),
...     "Tests per exit type": len(symbols) \* window\_cnt \* len(stops),
...     "Tests per stop type and value": len(symbols) \* window\_cnt,
...     "Tests total": len(symbols) \* window\_cnt \* len(stops) \* len(exit\_types)
... })
Start date                       2018-01-01 00:00:00+00:00
End date                         2021-01-01 00:00:00+00:00
Time period (days)                                    1096
Assets                                                  10
Window length                            180 days 00:00:00
Windows                                                400
Exit types                                               5
Stop values                                            100
Tests per asset                                     200000
Tests per window                                      5000
Tests per exit type                                 400000
Tests per stop type and value                         4000
Tests total                                        2000000
dtype: object
\`\`\`

1. 1%
2. $100
3. 0.25%
4. 0.25%

Our configuration produces sample sizes with enough statistical power to analyze four variables: assets
(200k tests per asset), time (5k tests per time window), exit types (400k tests per exit type), and
stop values (4k tests per stop type and value). Similar to Tableau's approach to dimensions and
measures, we can group our performance metrics by each of these variables. However, we will mainly
focus on 5 exit types: SL exits, TS exits, TP exits, random exits, and holding exits (executed at the
last bar).

\`\`\`pycon
>>> cols = \["Open", "Low", "High", "Close", "Volume"\]
>>> yfdata = vbt.YFData.pull(symbols, start=start\_date, end=end\_date)
\`\`\`

\[=100% "Symbol 10/10"\]{: .candystripe .candystripe-animate }

\`\`\`pycon
>>> yfdata.data.keys()
dict\_keys(\['BTC-USD', 'ETH-USD', 'XRP-USD', 'BCH-USD', 'LTC-USD', 
           'BNB-USD', 'EOS-USD', 'XLM-USD', 'XMR-USD', 'ADA-USD'\])

>>> yfdata.data\["BTC-USD"\].shape
(1096, 7)
\`\`\`

The data instance \`yfdata\` contains a dictionary of OHLCV data, keyed by cryptocurrency name. Each
DataFrame contains 1096 rows (days) and 5 columns (O, H, L, C, and V). You can plot each DataFrame as
follows:

\`\`\`pycon
>>> yfdata.plot(symbol="BTC-USD").show()  # (1)!
\`\`\`

1. Only one symbol can be plotted at a time.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/yfdata.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/yfdata.dark.svg#only-dark){: .iimg loading=lazy }

Since assets are one of the dimensions we want to analyze, VBT expects us to combine them as
columns into a single DataFrame and label them clearly. To do this, we swap assets and features to
create a dictionary of DataFrames, now with assets as columns and keyed by feature name, such as "Open".

\`\`\`pycon
>>> ohlcv = yfdata.concat()

>>> ohlcv.keys()
dict\_keys(\['Open', 'High', 'Low', 'Close', 
           'Volume', 'Dividends', 'Stock Splits'\])

>>> ohlcv\['Open'\].shape
(1096, 10)
\`\`\`

## Time windows

Next, we will use a 6-month sliding window over the entire time period and take 400 "snapshots" of
each price DataFrame within this window. Each snapshot is a subset of data to be backtested
independently. Like assets and other variables, snapshots also need to be stacked horizontally as
columns. As a result, we will obtain 180 rows (window length in days) and 4000 columns (10 assets x
400 windows). Each column will represent the price of one asset within one specific time window.

\`\`\`pycon
>>> splitter = vbt.Splitter.from\_n\_rolling(  # (1)!
...     ohlcv\["Open"\].index, 
...     n=window\_cnt,
...     length=window\_len.days
... )

>>> split\_ohlcv = {}
>>> for k, v in ohlcv.items():  # (2)!
...     split\_ohlcv\[k\] = splitter.take(v, into="reset\_stacked")  # (3)!
>>> print(split\_ohlcv\["Open"\].shape)
(180, 4000)

>>> split\_indexes = splitter.take(ohlcv\["Open"\].index)  # (4)!
>>> print(split\_indexes)
split
0      DatetimeIndex(\['2018-01-01 00:00:00+00:00', '2...
1      DatetimeIndex(\['2018-01-03 00:00:00+00:00', '2...
2      DatetimeIndex(\['2018-01-06 00:00:00+00:00', '2...
3      DatetimeIndex(\['2018-01-08 00:00:00+00:00', '2...
4      DatetimeIndex(\['2018-01-10 00:00:00+00:00', '2...
                             ...                        
395    DatetimeIndex(\['2020-06-26 00:00:00+00:00', '2...
396    DatetimeIndex(\['2020-06-28 00:00:00+00:00', '2...
397    DatetimeIndex(\['2020-06-30 00:00:00+00:00', '2...
398    DatetimeIndex(\['2020-07-03 00:00:00+00:00', '2...
399    DatetimeIndex(\['2020-07-05 00:00:00+00:00', '2...
Length: 400, dtype: object

>>> print(split\_indexes\[10\])  # (5)!
DatetimeIndex(\['2018-01-24 00:00:00+00:00', '2018-01-25 00:00:00+00:00',
               '2018-01-26 00:00:00+00:00', '2018-01-27 00:00:00+00:00',
               '2018-01-28 00:00:00+00:00', '2018-01-29 00:00:00+00:00',
               ...
               '2018-07-17 00:00:00+00:00', '2018-07-18 00:00:00+00:00',
               '2018-07-19 00:00:00+00:00', '2018-07-20 00:00:00+00:00',
               '2018-07-21 00:00:00+00:00', '2018-07-22 00:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Date', length=180, freq='D')
\`\`\`

1. Create an instance of \[Splitter\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/splitting/base/#vectorbtpro.generic.splitting.base.Splitter).
2. For each DataFrame with symbols in \`ohlcv\`...
3. Split the DataFrame into chunks and stack those chunks into one DataFrame by resetting its index.
Resetting the index prevents the operation from producing many NaNs.
4. We also want to know the index of each split. To do this, split the index in the same way as above,
but instead of stacking, store the result in a Series indexed by split label.
5. Here is the index of the split with the label \`10\`.

A great feature of VBT is its use of \[hierarchical indexing\](https://pandas.pydata.org/pandas-docs/stable/user\_guide/advanced.html)
to store valuable information for each backtest. This ensures that the column hierarchy is preserved throughout
the entire backtesting pipeline—from signal generation to performance modeling—and can be easily
extended. Currently, our columns have the following hierarchy:

\`\`\`pycon
>>> split\_ohlcv\["Open"\].columns
MultiIndex(\[(  0, 'BTC-USD'),
            (  0, 'ETH-USD'),
            (  0, 'XRP-USD'),
            ...
            (399, 'XLM-USD'),
            (399, 'XMR-USD'),
            (399, 'ADA-USD')\],
           names=\['split', 'symbol'\], length=4000)
\`\`\`

This multi-index captures three parameters: the symbol, the start date of the time window, and its end
date. Later, we will extend this multi-index with exit types and stop values, so that each of the 2
million tests has its own price series.

## Entry signals

Unlike most other backtesting libraries, VBT does not store signals as a signed integer array.
Instead, it splits signals into two boolean arrays—entries and exits—which makes manipulation much
easier. At the beginning of each time window, let's generate an entry signal indicating a buy order.
The DataFrame will have the same shape, index, and columns as the price DataFrame, so VBT can link
their elements together.

\`\`\`pycon
>>> entries = pd.DataFrame.vbt.signals.empty\_like(split\_ohlcv\["Open"\])
>>> entries.iloc\[0, :\] = True

>>> entries.shape
(180, 4000)
\`\`\`

## Exit signals

For each of the entry signals we created, we will generate an exit signal according to our five exit
types: SL, TS, TP, random, and holding. We will also concatenate their DataFrames into a single (huge)
DataFrame with 180 rows and 2,000,000 columns, each representing a separate backtest. Since exit
signals are boolean, their memory usage remains manageable.

Let's first generate exit signals according to stop conditions. We want to test 100 different stop
values with a 1% increment, starting from 1% and ending at 100% (that is, find the timestamp where
the price exceeds the entry price by 100%). When OHLC data is checked against these conditions, the
position closes at (or shortly after) the time the particular stop is hit.

!!! hint
    We use \[OHLCSTX\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/generators/ohlcstx/#vectorbtpro.signals.generators.ohlcstx.OHLCSTX)
    instead of the built-in stop-loss in \[Portfolio.from\_signals\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from\_signals)
    because we want to analyze signals before simulation. Also, constructing parameter grids is easier
    this way. For a reality check, you can run the same setup using
    \[Portfolio.from\_signals\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from\_signals) alone.

\`\`\`pycon
>>> sl\_ohlcstx = vbt.OHLCSTX.run(
...     entries,  # (1)!
...     entry\_price=split\_ohlcv\["Close"\],  # (2)!
...     open=split\_ohlcv\["Open"\], 
...     high=split\_ohlcv\["High"\], 
...     low=split\_ohlcv\["Low"\], 
...     close=split\_ohlcv\["Close"\], 
...     sl\_stop=list(stops),  # (3)!
...     stop\_type=None  # (4)!
... )
>>> sl\_exits = sl\_ohlcstx.exits.copy()  # (5)!
>>> sl\_price = sl\_ohlcstx.close.copy()  # (6)!
>>> sl\_price\[sl\_exits\] = sl\_ohlcstx.stop\_price
>>> del sl\_ohlcstx  # (7)!

>>> sl\_exits.shape
(180, 400000)

>>> tsl\_ohlcstx = vbt.OHLCSTX.run(
...     entries, 
...     entry\_price=split\_ohlcv\["Close"\], 
...     open=split\_ohlcv\["Open"\], 
...     high=split\_ohlcv\["High"\], 
...     low=split\_ohlcv\["Low"\], 
...     close=split\_ohlcv\["Close"\], 
...     tsl\_stop=list(stops),
...     stop\_type=None
... )
>>> tsl\_exits = tsl\_ohlcstx.exits.copy()
>>> tsl\_price = tsl\_ohlcstx.close.copy()
>>> tsl\_price\[tsl\_exits\] = tsl\_ohlcstx.stop\_price
>>> del tsl\_ohlcstx

>>> tsl\_exits.shape
(180, 400000)

>>> tp\_ohlcstx = vbt.OHLCSTX.run(
...     entries, 
...     entry\_price=split\_ohlcv\["Close"\], 
...     open=split\_ohlcv\["Open"\], 
...     high=split\_ohlcv\["High"\], 
...     low=split\_ohlcv\["Low"\], 
...     close=split\_ohlcv\["Close"\], 
...     tp\_stop=list(stops),
...     stop\_type=None
... )
>>> tp\_exits = tp\_ohlcstx.exits.copy()
>>> tp\_price = tp\_ohlcstx.close.copy()
>>> tp\_price\[tp\_exits\] = tp\_ohlcstx.stop\_price
>>> del tp\_ohlcstx

>>> tp\_exits.shape
(180, 400000)
\`\`\`

1. The \[OHLCSTX\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/generators/ohlcstx/#vectorbtpro.signals.generators.ohlcstx.OHLCSTX)
indicator is an exit generator, so the first input array is always an entry mask.
2. The second input array is the entry price. This is set to the closing price,
because we cannot execute the stop at the same bar as the entry signal anyway.
3. Providing a parameter as a list will test each value in that list across the entire input.
4. The \`stop\_type\` argument is an "in-place output," filled with various useful info.
Since we only need the exits and stop price arrays, set it to \`None\` to save memory.
5. Assign output arrays to variables. Copy them so you can delete the indicator instance later.
6. The order price is the stop price at the exit time, and the closing price otherwise.
7. Delete the indicator instance to free up memory.

This extends our column hierarchy with a new column level to indicate the stop value.
We just need to make this consistent across all DataFrames:

\`\`\`pycon
>>> def rename\_stop\_level(df):
...     return df.vbt.rename\_levels({
...         "ohlcstx\_sl\_stop": "stop\_value",
...         "ohlcstx\_tsl\_stop": "stop\_value",
...         "ohlcstx\_tp\_stop": "stop\_value"
...     }, strict=False)

>>> sl\_exits = rename\_stop\_level(sl\_exits)
>>> tsl\_exits = rename\_stop\_level(tsl\_exits)
>>> tp\_exits = rename\_stop\_level(tp\_exits)

>>> sl\_price = rename\_stop\_level(sl\_price)
>>> tsl\_price = rename\_stop\_level(tsl\_price)
>>> tp\_price = rename\_stop\_level(tp\_price)

>>> sl\_exits.columns
MultiIndex(\[(0.01,   0, 'BTC-USD'),
            (0.01,   0, 'ETH-USD'),
            (0.01,   0, 'XRP-USD'),
            ...
            ( 1.0, 399, 'XLM-USD'),
            ( 1.0, 399, 'XMR-USD'),
            ( 1.0, 399, 'ADA-USD')\],
           names=\['stop\_value', 'split', 'symbol'\], length=400000)
\`\`\`

A major feature of VBT is its strong emphasis on data science, allowing us to apply popular
analysis tools to nearly any part of the backtesting pipeline. For example, let's explore how the
number of exit signals depends on the stop type and value:

\`\`\`pycon
>>> pd.Series({
...     "SL": sl\_exits.vbt.signals.total().mean(),
...     "TS": tsl\_exits.vbt.signals.total().mean(),
...     "TP": tp\_exits.vbt.signals.total().mean()
... }, name="avg\_num\_signals")
SL    0.428585
TS    0.587100
TP    0.520042
Name: avg\_num\_signals, dtype: float64

>>> def groupby\_stop\_value(df):
...     return df.vbt.signals.total().groupby("stop\_value").mean()

>>> pd.DataFrame({
...     "Stop Loss": groupby\_stop\_value(sl\_exits),
...     "Trailing Stop": groupby\_stop\_value(tsl\_exits),
...     "Take Profit": groupby\_stop\_value(tp\_exits)
... }).vbt.plot(
...     xaxis\_title="Stop value", 
...     yaxis\_title="Avg number of signals"
... ).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/avg\_num\_signals.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/avg\_num\_signals.dark.svg#only-dark){: .iimg loading=lazy }

We see that TS is by far the most common exit signal. The SL and TP curves track closely up to
a stop value of 50% and then diverge, with TP dominating. While it may seem that bulls are mostly
in charge, especially for larger price moves, remember that it is much easier to achieve a 50% profit
than a 50% loss, since the latter requires a 100% profit to recover. This means that negative downward
spikes tend to dominate small to medium price changes (and potentially shake out weak hands). These
are well-known dynamics in cryptocurrency markets.

To simplify our analysis going forward, we want to ensure that each column has at least one exit
signal to close the position. If a column has no exit signal, we should add one at the last
timestamp. We do this by combining the stop exits with a last-bar exit using the \_OR\_ rule and
selecting whichever signal comes first:

\`\`\`pycon
>>> sl\_exits.iloc\[-1, :\] = True
>>> tsl\_exits.iloc\[-1, :\] = True
>>> tp\_exits.iloc\[-1, :\] = True

>>> sl\_exits = sl\_exits.vbt.signals.first\_after(entries)  # (1)!
>>> tsl\_exits = tsl\_exits.vbt.signals.first\_after(entries)
>>> tp\_exits = tp\_exits.vbt.signals.first\_after(entries)

>>> pd.Series({
...     "SL": sl\_exits.vbt.signals.total().mean(),
...     "TS": tsl\_exits.vbt.signals.total().mean(),
...     "TP": tp\_exits.vbt.signals.total().mean()
... }, name="avg\_num\_signals")
SL    1.0
TS    1.0
TP    1.0
Name: avg\_num\_signals, dtype: float64
\`\`\`

1. Select the first exit after each entry using \[SignalsAccessor.first\_after\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.first\_after).

Next, we will generate signals for the two remaining exit types: random and holding. These will
act as benchmarks to compare SL, TS, and TP against.

"Holding" exit signals are placed at the very last bar of each time series. In most cases, we do not
need to bother with these, since we can simply assess open positions. However, for consistency,
we want each column to have exactly one signal. Another reason is to ensure the shape and columns
match those of the stop signals, so we can concatenate all DataFrames later.

\`\`\`pycon
>>> hold\_exits = pd.DataFrame.vbt.signals.empty\_like(sl\_exits)
>>> hold\_exits.iloc\[-1, :\] = True
>>> hold\_price = vbt.broadcast\_to(split\_ohlcv\["Close"\], sl\_price)

>>> hold\_exits.shape
(180, 400000)
\`\`\`

To generate random exit signals, simply shuffle any signal array. The only requirement is that
each column contains exactly one signal.

\`\`\`pycon
>>> rand\_exits = hold\_exits.vbt.shuffle(seed=seed)  # (1)!
>>> rand\_price = hold\_price

>>> rand\_exits.shape
(180, 400000)
\`\`\`

1. This operation returns a new array.

The final step is to concatenate all DataFrames along the column axis and add a new column level
called \`exit\_type\`:

\`\`\`pycon
>>> exits = pd.DataFrame.vbt.concat(
...     sl\_exits, 
...     tsl\_exits, 
...     tp\_exits, 
...     rand\_exits, 
...     hold\_exits, 
...     keys=pd.Index(exit\_types, name="exit\_type")
... )
>>> del sl\_exits  # (1)!
>>> del tsl\_exits
>>> del tp\_exits
>>> del rand\_exits
>>> del hold\_exits

>>> exits.shape
(180, 2000000)

>>> price = pd.DataFrame.vbt.concat(
...     sl\_price, 
...     tsl\_price, 
...     tp\_price, 
...     rand\_price, 
...     hold\_price, 
...     keys=pd.Index(exit\_types, name="exit\_type")
... )
>>> del sl\_price
>>> del tsl\_price
>>> del tp\_price
>>> del rand\_price
>>> del hold\_price

>>> price.shape
\`\`\`

1. Delete DataFrames to free up memory.

The \`exits\` array now contains 2,000,000 columns—one for each backtest. The column hierarchy is
complete, with one tuple of parameters per backtest.

\`\`\`pycon
>>> exits.columns
MultiIndex(\[(     'SL', 0.01,   0, 'BTC-USD'),
            (     'SL', 0.01,   0, 'ETH-USD'),
            (     'SL', 0.01,   0, 'XRP-USD'),
            ...
            ('Holding',  1.0, 399, 'XLM-USD'),
            ('Holding',  1.0, 399, 'XMR-USD'),
            ('Holding',  1.0, 399, 'ADA-USD')\],
           names=\['exit\_type', 'stop\_value', 'split', 'symbol'\], 
           length=2000000)
\`\`\`

!!! warning
    One boolean array takes roughly 400 MB of RAM:

    \`\`\`pycon
    >>> print(exits.vbt.getsize())
    390.0 MB
    \`\`\`

    One floating array takes roughly 3 GB of RAM:

    \`\`\`pycon
    >>> print(price.vbt.getsize())
    2.9 GB
    \`\`\`

This setup allows us to group signals by one or more levels and easily analyze them together.
For example, let's compare different exit types and stop values by the average distance
from exit signal to entry signal (in days):

\`\`\`pycon
>>> avg\_distance = entries.vbt.signals.between\_ranges(target=exits)\\  # (1)!
...     .duration.mean()\\
...     .groupby(\["exit\_type", "stop\_value"\])\\
...     .mean()\\
...     .unstack(level="exit\_type")

>>> avg\_distance.mean()
exit\_type
Holding    179.000000
Random      89.432010
SL         124.686960
TP         113.887502
TS         104.159855
dtype: float64

>>> avg\_distance\[exit\_types\].vbt.plot(
...     xaxis\_title="Stop value", 
...     yaxis\_title="Avg distance to entry"
... ).show()
\`\`\`

1. Using \[SignalsAccessor.between\_ranges\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.between\_ranges).

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/avg\_distance.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/avg\_distance.dark.svg#only-dark){: .iimg loading=lazy }

This scatterplot gives a more detailed look at the distribution of exit signals.
As expected, plain holding exits occur exactly 179 days after entry (the maximum possible), while
random exits are distributed evenly across the time window and are not affected by any stop value.
We are most interested in the stop curves, which are flat, indicating high price volatility during
our timeframe. The lower the curve, the greater the likelihood of hitting a stop.
For example, a TS of 20% is hit after an average of only 30 days, while SL and TP stops would
take 72 and 81 days, respectively. But is an early exit actually beneficial?

## Simulation

Now comes the actual backtesting part:

\`\`\`pycon
>>> %%time
>>> pf = vbt.Portfolio.from\_signals(
...     split\_ohlcv\["Close"\],  # (1)!
...     entries, 
...     exits, 
...     price=price
... )

>>> len(pf.orders)
3995570
CPU times: user 21.2 s, sys: 9.11 s, total: 30.3 s
Wall time: 51.5 s
\`\`\`

1. We usually want to provide OHLC prices rather than just the closing price, but since OHLC was
already used to generate the signal arrays, the closing price is sufficient here.

Pretty easy, right?

The simulation took about 50 seconds on my Apple M1 and produced a total of 3,995,570 orders
ready for analysis (should be 4 million, but some price data appear to be missing).
Keep in mind that any floating array generated by the portfolio object with the same shape as our
exit signals, such as portfolio value or returns, requires 8 \* 180 \* 2,000,000 bytes, or almost 3 GB
of RAM. We can analyze anything from trades to Sharpe ratio, but given the size of the data,
we will focus on a fast-to-calculate metric: total return.

\`\`\`pycon
>>> total\_return = pf.total\_return
>>> del pf  # (1)!

>>> total\_return.shape
(2000000,)
\`\`\`

1. Delete the portfolio instance to free up memory.

If your computer takes a long time to run the simulation, you can:

\* Use \[Google Colab\](https://colab.research.google.com/).
\* Reduce the parameter space (for example, lower stop value granularity from 1% to 2%).
\* Use random search (for example, pick a random subset of columns).
\* Cast to \`np.float32\` or lower (if supported).
\* Split the exit signals into chunks and simulate each chunk separately. Just make sure each
chunk matches the shape of the price and entries arrays (and remember to delete the previous
portfolio before running a new one):

\`\`\`pycon
>>> total\_returns = \[\]
>>> for i in vbt.ProgressBar(range(len(exit\_types))):  # (1)!
...     exit\_type\_columns = exits.columns.get\_level\_values("exit\_type")
...     chunk\_mask = exit\_type\_columns == exit\_types\[i\]
...     chunk\_pf = vbt.Portfolio.from\_signals(
...         split\_ohlcv\["Close"\], 
...         entries, 
...         exits.loc\[:, chunk\_mask\],  # (2)!
...         price=price.loc\[:, chunk\_mask\]
...     )
...     total\_returns.append(chunk\_pf.total\_return)
...     
...     del chunk\_pf
...     vbt.flush()  # (3)!
    
>>> total\_return = pd.concat(total\_returns)

>>> total\_return.shape
\`\`\`

1. Iterate over exit types.
2. Select the columns that correspond to the current exit type.
3. Delete the portfolio instance and force garbage collection.

\[=100% "Chunk 5/5"\]{: .candystripe .candystripe-animate }

\`\`\`pycon
>>> total\_return = pd.concat(total\_returns)

>>> total\_return.shape
(2000000,)
\`\`\`

This approach has similar execution time but is much easier on memory.

## Performance

The first step is always to look at the baseline distribution:

\`\`\`pycon
>>> return\_by\_type = total\_return.unstack(level="exit\_type")\[exit\_types\]

>>> return\_by\_type\["Holding"\].describe(percentiles=\[\])
count    400000.000000
mean          0.086025
std           0.824799
min          -0.910154
50%          -0.139127
max           6.490103
Name: Holding, dtype: float64

>>> purple\_color = vbt.settings\["plotting"\]\["color\_schema"\]\["purple"\]
>>> return\_by\_type\["Holding"\].vbt.histplot(
...     xaxis\_title="Total return",
...     xaxis\_tickformat=".2%",
...     yaxis\_title="Count",
...     trace\_kwargs=dict(marker\_color=purple\_color)
... ).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/holding\_histplot.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/holding\_histplot.dark.svg#only-dark){: .iimg loading=lazy }

The distribution of holding performance across time windows is highly left-skewed. On one hand,
this indicates prolonged sideways and bearish regimes within our timeframe. On the other hand,
since the price of any asset can rise infinitely but only fall to zero, the distribution is naturally
denser on the left and sparser on the right. Every second return is a loss of more than 6%, but
thanks to occasional bull runs, the strategy still achieves an average profit of 9%.

Let's add other strategies to our analysis:

\`\`\`pycon
>>> pd.DataFrame({
...     "Mean": return\_by\_type.mean(),
...     "Median": return\_by\_type.median(),
...     "Std": return\_by\_type.std(),
... })
               Mean    Median       Std
exit\_type                              
SL         0.054361 -0.158458  0.764171
TS         0.057613 -0.093185  0.692137
TP         0.036844  0.077450  0.465555
Random     0.025284 -0.073612  0.575394
Holding    0.086025 -0.139127  0.824799

>>> return\_by\_type.vbt.boxplot(
...     trace\_kwargs=dict(boxpoints=False),  # (1)!
...     yaxis\_title="Total return",
...     yaxis\_tickformat=".2%"
... ).show()
\`\`\`

1. Plotly may be slow when drawing a huge number of outlier points.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/return\_by\_type.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/return\_by\_type.dark.svg#only-dark){: .iimg loading=lazy }

None of the strategies outperforms the baseline's average return. However, the TP strategy is the most
consistent—while it sets an upper bound that limits extreme profits (note the missing outliers),
its trade returns are less volatile and mostly positive. SL and TS are unbounded at the top because some
stops are never triggered, causing those columns to fall back to plain holding. The random strategy is
interesting, too: while its average return is lower, it ranks second after TP in terms of median return
and volatility.

To further support this picture, let's calculate each strategy's win rate:

\`\`\`pycon
>>> (return\_by\_type > 0).mean().rename("win\_rate")
exit\_type
SL         0.305702
TS         0.364098
TP         0.585405
Random     0.405520
Holding    0.402250
Name: win\_rate, dtype: float64
\`\`\`

Almost 60% of TP trades are profitable—a stark contrast to the other strategies. However, a high
win rate does not guarantee long-term trading success if your winning trades are much smaller
than your losing ones. Therefore, let's group by stop type and value and calculate the
\[expectancy\](https://www.icmarkets.com/blog/reward-to-risk-win-ratio-and-expectancy/):

\`\`\`pycon
>>> init\_cash = vbt.settings.portfolio\["init\_cash"\]

>>> def get\_expectancy(return\_by\_type, level\_name):
...     grouped = return\_by\_type.groupby(level\_name, axis=0)
...     win\_rate = grouped.apply(lambda x: (x > 0).mean())
...     avg\_win = grouped.apply(lambda x: init\_cash \* x\[x > 0\].mean())
...     avg\_win = avg\_win.fillna(0)
...     avg\_loss = grouped.apply(lambda x: init\_cash \* x\[x < 0\].mean())
...     avg\_loss = avg\_loss.fillna(0)
...     return win\_rate \* avg\_win - (1 - win\_rate) \* np.abs(avg\_loss)
    
>>> expectancy\_by\_stop = get\_expectancy(return\_by\_type, "stop\_value")

>>> expectancy\_by\_stop.mean()
exit\_type
SL         5.436087
TS         5.761281
TP         3.684371
Random     2.362847
Holding    8.602499
dtype: float64

>>> expectancy\_by\_stop.vbt.plot(
...     xaxis\_title="Stop value", 
...     yaxis\_title="Expectancy"
... ).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/expectancy\_by\_stop.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/expectancy\_by\_stop.dark.svg#only-dark){: .iimg loading=lazy }

Each strategy can steadily add to our account over time, with the holding strategy emerging as
the clear winner—we can expect to add nearly $9 out of every $100 invested after each
6-month holding period. The only configuration that outperforms the baseline is TS, specifically
with stop values ranging from 20% to 40%. The weakest performers are SL and TS with stop values
around 45% and 60%, which seem to be triggered at the bottoms of major corrections, making them
even worse than random exits. The TP strategy, on the other hand, outperforms the random exit
strategy once the stop value crosses 30%. In general, patience seems to pay off in cryptocurrencies.

Finally, let's see how these strategies fare under different market conditions. We will use a simplified
regime classification that divides holding returns into 20 bins and calculates each strategy's
expectancy within those bins (the last bin is excluded for chart readability). Due to the highly
skewed distribution of holding returns, we need to ensure that the bins are equal in size.

\`\`\`pycon
>>> return\_values = np.sort(return\_by\_type\["Holding"\].values)
>>> idxs = np.ceil(np.linspace(0, len(return\_values) - 1, 21)).astype(int)
>>> bins = return\_values\[idxs\]\[:-1\]

>>> def bin\_return(return\_by\_type):
...     classes = pd.cut(return\_by\_type\["Holding"\], bins=bins, right=True)
...     new\_level = np.array(classes.apply(lambda x: x.right))
...     new\_level = pd.Index(new\_level, name="bin\_right")
...     return return\_by\_type.vbt.add\_levels(new\_level, axis=0)

>>> binned\_return\_by\_type = bin\_return(return\_by\_type)

>>> expectancy\_by\_bin = get\_expectancy(binned\_return\_by\_type, "bin\_right")

>>> expectancy\_by\_bin.vbt.plot(
...     trace\_kwargs=dict(mode="lines"),
...     xaxis\_title="Total return of holding",
...     xaxis\_tickformat=".2%",
...     yaxis\_title="Expectancy"
... ).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/expectancy\_by\_bin.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/stop-signals/expectancy\_by\_bin.dark.svg#only-dark){: .iimg loading=lazy }

The chart above confirms the general intuition behind stop orders:
SL and TS help limit losses during downtrends, TP works well for short-term trades seeking quick gains,
and holding excels in high-growth markets. Interestingly, random exits perform poorly in sideways and
bullish periods, but they often match or outperform stop exits in bear markets.

## Bonus: Dashboard

Dashboards can be a powerful way to interact with your data.

Let's first define the components of our dashboard. We have two types of components: controls
(such as an asset dropdown) and graphs. Controls set parameters and trigger updates for the graphs.

\`\`\`pycon
>>> range\_starts = pd.DatetimeIndex(list(map(lambda x: x\[0\], split\_indexes)))
>>> range\_ends = pd.DatetimeIndex(list(map(lambda x: x\[-1\], split\_indexes)))

>>> symbol\_lvl = return\_by\_type.index.get\_level\_values("symbol")
>>> split\_lvl = return\_by\_type.index.get\_level\_values("split")
>>> range\_start\_lvl = range\_starts\[split\_lvl\]
>>> range\_end\_lvl = range\_ends\[split\_lvl\]

>>> asset\_multi\_select = ipywidgets.SelectMultiple(
...     options=symbols,
...     value=symbols,
...     rows=len(symbols),
...     description="Symbols"
... )
>>> dates = np.unique(yfdata.wrapper.index)
>>> date\_range\_slider = ipywidgets.SelectionRangeSlider(
...     options=dates,
...     index=(0, len(dates)-1),
...     orientation="horizontal",
...     readout=False,
...     continuous\_update=False
... )
>>> range\_start\_label = ipywidgets.Label()
>>> range\_end\_label = ipywidgets.Label()
>>> metric\_dropdown = ipywidgets.Dropdown(
...     options=\["Mean", "Median", "Win Rate", "Expectancy"\],
...     value="Expectancy"
... )
>>> stop\_scatter = vbt.Scatter(
...     trace\_names=exit\_types,
...     x\_labels=stops, 
...     xaxis\_title="Stop value", 
...     yaxis\_title="Expectancy"
... )
>>> stop\_scatter\_img = ipywidgets.Image(
...     format="png",
...     width=stop\_scatter.fig.layout.width,
...     height=stop\_scatter.fig.layout.height
... )
>>> bin\_scatter = vbt.Scatter(
...     trace\_names=exit\_types,
...     x\_labels=expectancy\_by\_bin.index, 
...     trace\_kwargs=dict(mode="lines"),
...     xaxis\_title="Total return of holding",
...     xaxis\_tickformat="%",
...     yaxis\_title="Expectancy"
... )
>>> bin\_scatter\_img = ipywidgets.Image(
...     format="png",
...     width=bin\_scatter.fig.layout.width,
...     height=bin\_scatter.fig.layout.height
... )
\`\`\`

The second step is to define the update function, which is triggered whenever any control 
is changed. We also call this function manually to initialize the graphs with default parameters.

\`\`\`pycon
>>> def update\_scatter(\*args, \*\*kwargs):
...     \_symbols = asset\_multi\_select.value
...     \_from = date\_range\_slider.value\[0\]
...     \_to = date\_range\_slider.value\[1\]
...     \_metric\_name = metric\_dropdown.value
...     
...     range\_mask = (range\_start\_lvl >= \_from) & (range\_end\_lvl <= \_to)
...     asset\_mask = symbol\_lvl.isin(\_symbols)
...     filt = return\_by\_type\[range\_mask & asset\_mask\]
...     
...     filt\_binned = bin\_return(filt)
...     if \_metric\_name == "Mean":
...         filt\_metric = filt.groupby("stop\_value").mean()
...         filt\_bin\_metric = filt\_binned.groupby("bin\_right").mean()
...     elif \_metric\_name == "Median":
...         filt\_metric = filt.groupby("stop\_value").median()
...         filt\_bin\_metric = filt\_binned.groupby("bin\_right").median()
...     elif \_metric\_name == "Win Rate":
...         filt\_metric = (filt > 0).groupby("stop\_value").mean()
...         filt\_bin\_metric = (filt\_binned > 0).groupby("bin\_right").mean()
...     elif \_metric\_name == "Expectancy":
...         filt\_metric = get\_expectancy(filt, "stop\_value")
...         filt\_bin\_metric = get\_expectancy(filt\_binned, "bin\_right")
...         
...     stop\_scatter.fig.update\_layout(yaxis\_title=\_metric\_name)
...     stop\_scatter.update(filt\_metric)
...     stop\_scatter\_img.value = stop\_scatter.fig.to\_image(format="png")
...     
...     bin\_scatter.fig.update\_layout(yaxis\_title=\_metric\_name)
...     bin\_scatter.update(filt\_bin\_metric)
...     bin\_scatter\_img.value = bin\_scatter.fig.to\_image(format="png")
...     
...     range\_start\_label.value = np.datetime\_as\_string(
...         \_from.to\_datetime64(), unit="D")
...     range\_end\_label.value = np.datetime\_as\_string(
...         \_to.to\_datetime64(), unit="D")
    
>>> asset\_multi\_select.observe(update\_scatter, names="value")
>>> date\_range\_slider.observe(update\_scatter, names="value")
>>> metric\_dropdown.observe(update\_scatter, names="value")
>>> update\_scatter()
\`\`\`

In the final step, we define the dashboard layout and run it:

\`\`\`pycon
>>> dashboard = ipywidgets.VBox(\[
...     asset\_multi\_select,
...     ipywidgets.HBox(\[
...         range\_start\_label,
...         date\_range\_slider,
...         range\_end\_label
...     \]),
...     metric\_dropdown,
...     stop\_scatter\_img,
...     bin\_scatter\_img
... \])
>>> dashboard
\`\`\`

<div class="grid cards width-eighty" markdown>

- :material-monitor-dashboard:{ .lg .middle } \_\_Dashboard\_\_

    ---

    Run the notebook to view the dashboard!

</div>

## Summary

Large-scale backtesting is useful for much more than just hyperparameter optimization. When used
thoughtfully, it provides a way to explore complex trading phenomena. By leveraging multidimensional
arrays, dynamic compilation, and pandas integration—as done by VBT—you can quickly gain
new insights by applying popular data science tools to each part of your backtesting pipeline.

In this example, we ran 2 million tests to see how various stop values affect stop signals' performance
and how stop signals compare to holding and random trading. The results confirm many of our earlier
beliefs about stop signals across different market conditions, but they also reveal optimal
configurations that may have worked well in recent years of trading cryptocurrencies.

\[:material-language-python: Python code\](https://vectorbt.pro/pvt\_6d1b3986/assets/jupytext/tutorials/stop-signals.py.txt){ .md-button target="blank\_" }
\[:material-notebook-outline: Notebook\](https://github.com/polakowo/vectorbt.pro/blob/main/notebooks/StopSignals.ipynb){ .md-button target="blank\_" }