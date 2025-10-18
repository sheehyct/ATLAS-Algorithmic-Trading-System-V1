\---
title: Pairs trading
description: Learn how to develop and optimize a pairs trading strategy using VectorBT PRO
icon: material/chart-multiline
---

# :material-chart-multiline: Pairs trading

A pairs trading strategy is a statistical arbitrage and convergence strategy based on the historical correlation 
between two instruments. It involves taking a long position in one instrument and a short position in the other. 
These offsetting positions create a hedging strategy that aims to profit from both positive and negative trends. 
A high positive correlation, typically at least 0.8, between the two instruments is the main source of the 
strategy's profits. When the correlation deviates, we look to buy the underperforming instrument and sell short 
the outperforming one. If the securities revert to their historical correlation, which is the outcome we aim for, 
a profit is generated from the convergence of their prices. As a result, pairs trading can be used to seek profits 
regardless of market conditions, whether the market is trending up, down, or moving sideways.

## Selection

When designing a pairs trading strategy, it is more important to select pairs based on 
\[cointegration\](https://en.wikipedia.org/wiki/Cointegration) rather than just 
\[correlation\](https://en.wikipedia.org/wiki/Correlation). Correlated instruments usually move in a similar 
way, but over time, the price ratio (or spread) between them may diverge significantly.
Cointegrated instruments, however, do not always move together in the same direction:
the spread between them can widen on some days, but their prices usually "pull back together" 
to the mean, providing optimal conditions for pairs arbitrage trading.

The two main methods for identifying cointegration are the Engle-Granger test and the Johansen test.
We will use the Engle-Granger test, as its augmented version is available in \[\`statsmodels\`\](https://www.statsmodels.org/).
The concept behind the Engle-Granger test is straightforward. We perform a linear regression between the two 
asset prices and check if the residual is stationary using the 
\[Augmented Dickey-Fuller (ADF) test\](https://en.wikipedia.org/wiki/Augmented\_Dickey%E2%80%93Fuller\_test). 
If the residual is stationary, then the two asset prices are cointegrated.

First, let's create a universe of instruments from which to select our pairs. We will search for 
all available USDT symbols on Binance and download their daily history. Instead of downloading 
all of them at once, we will fetch each symbol individually and append it to an HDF file. 
We take this approach because most symbols have limited history, and we want to avoid using extra RAM 
by extending datasets with NaNs. We will also skip this entire process if the file already exists.

!!! note
    Make sure to delete the HDF file if you want to re-fetch.

\`\`\`pycon
>>> from vectorbtpro import \*

>>> SYMBOLS = vbt.BinanceData.list\_symbols("\*USDT")  # (1)!
>>> POOL\_FILE = "temp/data\_pool.h5"
>>> START = "2018"
>>> END = "2023"

>>> # vbt.remove\_dir("temp", with\_contents=True, missing\_ok=True)
>>> vbt.make\_dir("temp")  # (2)!

>>> if not vbt.file\_exists(POOL\_FILE):
...     with vbt.ProgressBar(total=len(SYMBOLS)) as pbar:  # (3)!
...         collected = 0
...         for symbol in SYMBOLS:
...             try:
...                 data = vbt.BinanceData.pull(
...                     symbol, 
...                     start=START,
...                     end=END,
...                     show\_progress=False,
...                     silence\_warnings=True
...                 )
...                 data.to\_hdf(POOL\_FILE)  # (4)!
...                 collected += 1
...             except Exception:
...                 pass
...             pbar.set\_prefix(f"{symbol} ({collected})")  # (5)!
...             pbar.update()
\`\`\`

1. Use a wildcard for the base currency to search for all pairs with USDT as the quote currency.
2. Create a temporary directory where all future artifacts will reside.
3. Display a \[\`tqdm\`\](https://github.com/tqdm/tqdm) progress bar.
4. Save each dataset to the same HDF file under \`POOL\_FILE\`, using the symbol as a key.
5. A descriptive progress bar always helps track the process.

\[=100% "Symbol 423/423"\]{: .candystripe .candystripe-animate }

Although this process takes some time, we now have a file containing data for each symbol under its 
own key. One major advantage of using HDF files (and VBT in particular) is that we can load the entire file 
and join all contained keys with a single command.

We still have one more decision to make: which period should we analyze to select the optimal pair? 
It is important not to use the same date range for both pair selection and strategy backtesting, 
as this could introduce survivorship bias. Therefore, let's reserve a more recent period for backtesting.

\`\`\`pycon
>>> SELECT\_START = "2020"
>>> SELECT\_END = "2021"

>>> data = vbt.HDFData.pull(
...     POOL\_FILE, 
...     start=SELECT\_START, 
...     end=SELECT\_END, 
...     silence\_warnings=True
... )

>>> print(len(data.symbols))
245
\`\`\`

We have imported 245 datasets, but some may be incomplete.
To ensure smooth analysis, we should remove the incomplete datasets.

\`\`\`pycon
>>> data = data.select(\[
...     k 
...     for k, v in data.data.items() 
...     if not v.isnull().any().any()
... \])

>>> print(len(data.symbols))
82
\`\`\`

We have removed a large portion of the incomplete data.

The next step is to find the pairs that pass our cointegration test. There are several approaches to 
finding viable pairs. On one hand, we may have prior knowledge and specifically test a particular pair 
for cointegration. On the other hand, we can search through hundreds of instruments to find any viable 
pairs according to the test results. In this exhaustive search scenario, we might encounter a multiple comparisons 
bias, which is an increased chance of incorrectly identifying a significant p-value when performing many tests. 
For example, if we run 100 tests on random data, we would expect about 5 p-values below 0.05 just by chance.
In practice, we should include a second verification step when identifying pairs in this way, which we will do later.

The test itself is performed using \[\`statsmodels.tsa.stattools.coint\`\](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html).
This function returns a tuple, with the second element being the p-value of interest. Testing each pair 
would require looping through \`82 \* 82\` or 6,724 pairs, and since the \`coint\` function is not especially 
fast, we will parallelize the process using \[\`pathos\`\](https://pathos.readthedocs.io/en/latest/index.html) :zap:

\`\`\`pycon
>>> @vbt.parameterized(  # (1)!
...     merge\_func="concat", 
...     engine="pathos",
...     distribute="chunks",  # (2)!
...     n\_chunks="auto"  # (3)!
... )
... def coint\_pvalue(close, s1, s2):
...     import statsmodels.tsa.stattools as ts  # (4)!
...     import numpy as np
...     return ts.coint(np.log(close\[s1\]), np.log(close\[s2\]))\[1\]

>>> COINT\_FILE = "temp/coint\_pvalues.pickle"

>>> # vbt.remove\_file(COINT\_FILE, missing\_ok=True)
>>> if not vbt.file\_exists(COINT\_FILE):
...     coint\_pvalues = coint\_pvalue(  # (5)!
...         data.close,
...         vbt.Param(data.symbols, condition="s1 != s2"),  # (6)!
...         vbt.Param(data.symbols)
...     )
...     vbt.save(coint\_pvalues, COINT\_FILE)
... else:
...     coint\_pvalues = vbt.load(COINT\_FILE)
\`\`\`

1. This decorator (\[parameterized\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.parameterized)) 
takes arguments wrapped with \[Param\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.Param),
builds their product, and passes each combination to the underlying function.
2. Build chunks of multiple parameter combinations and process these chunks in parallel, while 
combinations within each chunk are processed serially.
3. Set the number of chunks to the number of CPU cores.
4. Since we use multiprocessing, each process must import the libraries it will need.
5. The wrapped function takes the same arguments as the underlying function.
6. Do not compare symbols to themselves.

!!! hint
    Analyzing raw prices can work, but log prices are preferable.

The result is a Pandas Series where each pair of symbols in the index is mapped to its p-value.
If the p-value is small, below a critical threshold (< 0.05), we can reject the hypothesis that 
there is no cointegrating relationship. Let's now arrange the p-values in increasing order:

\`\`\`pycon
>>> coint\_pvalues = coint\_pvalues.sort\_values()

>>> print(coint\_pvalues)
s1        s2      
TUSDUSDT  BUSDUSDT    6.179128e-17
USDCUSDT  BUSDUSDT    7.703666e-14
BUSDUSDT  USDCUSDT    2.687508e-13
TUSDUSDT  USDCUSDT    2.906244e-12
BUSDUSDT  TUSDUSDT    1.853641e-11
                               ...
BTCUSDT   XTZUSDT     1.000000e+00
          EOSUSDT     1.000000e+00
          ENJUSDT     1.000000e+00
          NKNUSDT     1.000000e+00
ZILUSDT   HBARUSDT    1.000000e+00
Length: 6642, dtype: float64
\`\`\`

Is it a coincidence that the most cointegrated pairs are stablecoins? Probably not.

Remember the multiple comparisons bias? Let's test the top pairs by plotting their charts below and 
making sure that the difference between each pair of symbols bounces back and forth around its mean. 
For example, here is an analysis for the pair \`(ALGOUSDT, QTUMUSDT)\`:

\`\`\`pycon
>>> S1, S2 = "ALGOUSDT", "QTUMUSDT"

>>> data.plot(column="Close", symbol=\[S1, S2\], base=1).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/rebased\_price.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/rebased\_price.dark.svg#only-dark){: .iimg loading=lazy }

These prices move together.

\`\`\`pycon
>>> S1\_log = np.log(data.get("Close", S1))  # (1)!
>>> S2\_log = np.log(data.get("Close", S2))
>>> log\_diff = (S2\_log - S1\_log).rename("Log diff")
>>> fig = log\_diff.vbt.plot()
>>> fig.add\_hline(y=log\_diff.mean(), line\_color="yellow", line\_dash="dot")
>>> fig.show()
\`\`\`

1. Avoid \`data.close\[S1\]\`, which creates the close series with all symbols first—it is slower!

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/price\_log\_diff.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/price\_log\_diff.dark.svg#only-dark){: .iimg loading=lazy }

The linear combination of the two prices oscillates around the mean.

## Testing

More data is always better. Let's re-fetch our pair's history with higher granularity.

\`\`\`pycon
>>> DATA\_FILE = "temp/data.pickle"

>>> # vbt.remove\_file(DATA\_FILE, missing\_ok=True)
>>> if not vbt.file\_exists(DATA\_FILE):
...     data = vbt.BinanceData.pull(
...         \[S1, S2\], 
...         start=SELECT\_END,  # (1)!
...         end=END, 
...         timeframe="hourly"
...     )
...     vbt.save(data, DATA\_FILE)
... else:
...     data = vbt.load(DATA\_FILE)

>>> print(len(data.index))
17507
\`\`\`

1. The selection and testing periods should not overlap!

!!! note
    Make sure none of the tickers have been delisted.

We now have 17,507 data points for each symbol.

### Level: Researcher :satellite:

The spread represents the relative performance of both instruments. Whenever the two instruments 
move apart, the spread increases and may reach a certain threshold where we take a long position 
in the underperformer and a short position in the overachiever. This threshold is usually set to 
a number of standard deviations from the mean. All of this is done in a rolling manner, as the 
linear relationship between the instruments is always changing. We will use the prediction error of 
the \[ordinary least squares (OLS)\](https://en.wikipedia.org/wiki/Ordinary\_least\_squares), which is 
the difference between the true value and the predicted value. Fortunately, we have the 
\[OLS\](https://vectorbt.pro/pvt\_6d1b3986/api/indicators/custom/ols/#vectorbtpro.indicators.custom.ols.OLS) indicator, which can 
calculate both the prediction error and the z-score of that error:

\`\`\`pycon
>>> import scipy.stats as st

>>> WINDOW = 24 \* 30  # (1)!
>>> UPPER = st.norm.ppf(1 - 0.05 / 2)  # (2)!
>>> LOWER = -st.norm.ppf(1 - 0.05 / 2)

>>> S1\_close = data.get("Close", S1)
>>> S2\_close = data.get("Close", S2)
>>> ols = vbt.OLS.run(S1\_close, S2\_close, window=vbt.Default(WINDOW))
>>> spread = ols.error.rename("Spread")
>>> zscore = ols.zscore.rename("Z-score")
>>> print(pd.concat((spread, zscore), axis=1))
                             Spread   Z-score
Open time                                    
2021-01-01 00:00:00+00:00       NaN       NaN
2021-01-01 01:00:00+00:00       NaN       NaN
2021-01-01 02:00:00+00:00       NaN       NaN
2021-01-01 03:00:00+00:00       NaN       NaN
2021-01-01 04:00:00+00:00       NaN       NaN
...                             ...       ...
2022-12-31 19:00:00+00:00 -0.121450 -1.066809
2022-12-31 20:00:00+00:00 -0.123244 -1.078957
2022-12-31 21:00:00+00:00 -0.122595 -1.070667
2022-12-31 22:00:00+00:00 -0.125066 -1.088617
2022-12-31 23:00:00+00:00 -0.130532 -1.131498

\[17507 rows x 2 columns\]
\`\`\`

1. One month window.
2. 95% significance level across two tails.

Let's plot the z-score, the two thresholds, and the points where the z-score crosses them:

\`\`\`pycon
>>> upper\_crossed = zscore.vbt.crossed\_above(UPPER)
>>> lower\_crossed = zscore.vbt.crossed\_below(LOWER)

>>> fig = zscore.vbt.plot()
>>> fig.add\_hline(y=UPPER, line\_color="orangered", line\_dash="dot")
>>> fig.add\_hline(y=0, line\_color="yellow", line\_dash="dot")
>>> fig.add\_hline(y=LOWER, line\_color="limegreen", line\_dash="dot")
>>> upper\_crossed.vbt.signals.plot\_as\_exits(zscore, fig=fig)
>>> lower\_crossed.vbt.signals.plot\_as\_entries(zscore, fig=fig)
>>> fig.show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/zscore.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/zscore.dark.svg#only-dark){: .iimg loading=lazy }

If you look closely at the chart above, you will notice many signals of the same type appearing 
one after another. This happens because price fluctuations cause the price to cross each threshold 
repeatedly. This will not cause any issues if we use 
\[Portfolio.from\_signals\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from\_signals)
as our simulation method of choice, since it ignores duplicate signals by default.

Now, we need to construct proper signal arrays. Keep in mind that pairs trading involves two 
opposite positions that should be part of a single portfolio. We need to transform our crossover 
signals into two arrays: long entries and short entries, each with two columns. Whenever there is 
an upper-threshold crossover signal, we issue a short entry signal for the first asset and a long 
entry signal for the second asset. Conversely, when there is a lower-threshold crossover signal, 
we issue a long entry for the first asset and a short entry for the second asset.

\`\`\`pycon
>>> long\_entries = data.symbol\_wrapper.fill(False)
>>> short\_entries = data.symbol\_wrapper.fill(False)

>>> short\_entries.loc\[upper\_crossed, S1\] = True
>>> long\_entries.loc\[upper\_crossed, S2\] = True
>>> long\_entries.loc\[lower\_crossed, S1\] = True
>>> short\_entries.loc\[lower\_crossed, S2\] = True

>>> print(long\_entries.sum())
symbol
ALGOUSDT    52
QTUMUSDT    73
dtype: int64
>>> print(short\_entries.sum())
symbol
ALGOUSDT    73
QTUMUSDT    52
dtype: int64
\`\`\`

Now it is time to simulate our configuration! The position size of each pair should be matched by 
dollar value rather than number of shares; this way, a 5% move in one matches a 5% move in the other. 
To avoid running out of cash, we will make each order's position size dependent on the current equity. 
You might wonder why we can use \[Portfolio.from\_signals\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from\_signals)
even though it does not support target size types. In pairs trading, a position is either opened or 
reversed (closed out and opened again with the opposite sign), so we do not need target size types 
at all—regular size types are sufficient.

\`\`\`pycon
>>> pf = vbt.Portfolio.from\_signals(
...     data,
...     entries=long\_entries,
...     short\_entries=short\_entries,
...     size=10,  # (1)!
...     size\_type="valuepercent100",  # (2)!
...     group\_by=True,  # (3)!
...     cash\_sharing=True,
...     call\_seq="auto"
... )
\`\`\`

1. Open a position whose value matches 10% of the current equity.
2. Size is provided as a percentage of the equity, where 1 = 1%.
3. Pack both positions into the same group, share the same cash balance, and reorder orders so sell 
orders come before buy orders to release cash early.

The simulation is complete. When working with grouped portfolios that involve rebalancing, 
we should always check the allocations first to validate them:

\`\`\`pycon
>>> fig = pf.plot\_allocations()
>>> rebalancing\_dates = data.index\[np.unique(pf.orders.idx.values)\]
>>> for date in rebalancing\_dates:
...     fig.add\_vline(x=date, line\_color="teal", line\_dash="dot")
>>> fig.show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/from\_signals\_allocations.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/from\_signals\_allocations.dark.svg#only-dark){: .iimg loading=lazy }

The result makes sense: positions in both symbols are constantly switching, almost like watching 
a chessboard. Also, the long and short allocations rarely go above the specified 10% position size. 
Now, we should calculate the portfolio statistics to evaluate the profitability of our strategy:

\`\`\`pycon
>>> pf.stats()
Start                          2021-01-01 00:00:00+00:00
End                            2022-12-31 23:00:00+00:00
Period                                 729 days 11:00:00
Start Value                                        100.0
Min Value                                      96.401924
Max Value                                     127.670782
End Value                                     119.930329
Total Return \[%\]                               19.930329
Benchmark Return \[%\]                          -34.051206
Total Time Exposure \[%\]                        89.946878
Max Gross Exposure \[%\]                          12.17734
Max Drawdown \[%\]                                8.592299
Max Drawdown Duration                  318 days 00:00:00
Total Orders                                          34
Total Fees Paid                                      0.0
Total Trades                                          34
Win Rate \[%\]                                       43.75
Best Trade \[%\]                                160.511614
Worst Trade \[%\]                               -54.796964
Avg Winning Trade \[%\]                          41.851493
Avg Losing Trade \[%\]                          -20.499826
Avg Winning Trade Duration    42 days 22:04:17.142857143
Avg Losing Trade Duration               33 days 14:43:20
Profit Factor                                   1.553538
Expectancy                                      0.713595
Sharpe Ratio                                    0.782316
Calmar Ratio                                     1.10712
Omega Ratio                                     1.034258
Sortino Ratio                                   1.221721
Name: group, dtype: object
\`\`\`

We gained almost 20% from the initial portfolio value—a comfortable win, especially considering 
that the benchmark is down nearly 35%. As expected, the portfolio was in a position 90% of the time; 
the only period without a position was the initial phase before the first signal. 
Even with a win rate below 50%, we were profitable because the average winning trade returned 
50% more profit than the average loss, resulting in a long-term profit of $0.70 per trade.

But how can we verify that the simulation closely mirrors the signals it is based on? 
To do this, we can reframe our problem as a portfolio optimization task: 
we will mark the points where the z-score crosses any of the thresholds as allocation points 
and assign the corresponding weights at those times. This is very straightforward using 
\[PortfolioOptimizer\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer):

\`\`\`pycon
>>> allocations = data.symbol\_wrapper.fill()  # (1)!
>>> allocations.loc\[upper\_crossed, S1\] = -0.1
>>> allocations.loc\[upper\_crossed, S2\] = 0.1
>>> allocations.loc\[lower\_crossed, S1\] = 0.1
>>> allocations.loc\[lower\_crossed, S2\] = -0.1
>>> pfo = vbt.PortfolioOptimizer.from\_filled\_allocations(allocations)

>>> print(pfo.allocations)  # (2)!
symbol                     ALGOUSDT  QTUMUSDT
Open time                                    
2021-03-15 10:00:00+00:00       0.1      -0.1
2021-03-23 03:00:00+00:00      -0.1       0.1
2021-04-17 14:00:00+00:00       0.1      -0.1
2021-04-19 00:00:00+00:00      -0.1       0.1
2021-06-03 16:00:00+00:00       0.1      -0.1
2021-06-30 22:00:00+00:00      -0.1       0.1
2021-08-19 06:00:00+00:00       0.1      -0.1
2021-10-02 21:00:00+00:00      -0.1       0.1
2021-11-12 03:00:00+00:00       0.1      -0.1
2022-02-02 09:00:00+00:00      -0.1       0.1
2022-04-28 21:00:00+00:00       0.1      -0.1
2022-07-22 02:00:00+00:00      -0.1       0.1
2022-09-04 01:00:00+00:00       0.1      -0.1
2022-09-27 03:00:00+00:00      -0.1       0.1
2022-10-13 10:00:00+00:00       0.1      -0.1
2022-10-23 19:00:00+00:00      -0.1       0.1
2022-11-08 20:00:00+00:00       0.1      -0.1

>>> pfo.plot().show()
\`\`\`

1. Build an array of weights.
2. Get a compressed allocations array.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/optimizer.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/optimizer.dark.svg#only-dark){: .iimg loading=lazy }

There is also a convenient method to simulate the optimizer:

\`\`\`pycon
>>> pf = pfo.simulate(data, pf\_method="from\_signals")
>>> pf.total\_return
0.19930328736504038
\`\`\`

!!! info
    This method is based on a dynamic signal function that converts target percentages into signals, 
    so the first compilation may take up to a minute (after that, it will be extremely fast). 
    You can also omit the \`pf\_method\` argument to use the cacheable 
    \[Portfolio.from\_orders\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from\_orders)
    with similar results.

What about parameter optimization? There are several parts of the code that are open for parameterization.
The signal generation is affected by the \`WINDOW\`, \`UPPER\`, and \`LOWER\` parameters. 
The simulation part offers more flexibility; for example, you can add stops to limit your exposure 
to adverse price movements. Let's start with the signal generation.

A key challenge is how to combine the \`UPPER\` and \`LOWER\` parameters. We cannot simply pass them 
to their respective crossover functions and expect the results to align; we need to unify the resulting 
columns before combining them later. One useful approach is to build a meta-indicator that encapsulates 
other indicators and handles multiple parameter combinations automatically:

\`\`\`pycon
>>> PTS\_expr = """
...     PTS:
...     x = @in\_close.iloc\[:, 0\]
...     y = @in\_close.iloc\[:, 1\]
...     ols = vbt.OLS.run(x, y, window=@p\_window, hide\_params=True)
...     upper = st.norm.ppf(1 - @p\_upper\_alpha / 2)
...     lower = -st.norm.ppf(1 - @p\_lower\_alpha / 2)
...     upper\_crossed = ols.zscore.vbt.crossed\_above(upper)
...     lower\_crossed = ols.zscore.vbt.crossed\_below(lower)
...     long\_entries = wrapper.fill(False)
...     short\_entries = wrapper.fill(False)
...     short\_entries.loc\[upper\_crossed, x.name\] = True
...     long\_entries.loc\[upper\_crossed, y.name\] = True
...     long\_entries.loc\[lower\_crossed, x.name\] = True
...     short\_entries.loc\[lower\_crossed, y.name\] = True
...     long\_entries, short\_entries
... """

>>> PTS = vbt.IF.from\_expr(PTS\_expr, keep\_pd=True, st=st)  # (1)!
>>> vbt.phelp(PTS.run)  # (2)!
PTS.run(
    close,
    window,
    upper\_alpha,
    lower\_alpha,
    short\_name='pts',
    hide\_params=None,
    hide\_default=True,
    \*\*kwargs
):
    Run \`PTS\` indicator.
    
    \* Inputs: \`close\`
    \* Parameters: \`window\`, \`upper\_alpha\`, \`lower\_alpha\`
    \* Outputs: \`long\_entries\`, \`short\_entries\`
\`\`\`

1. By default, the factory passes two-dimensional NumPy arrays. Use \`keep\_pd\` to pass Pandas objects 
instead. Also, since expressions are processed in isolation from global variables, specify any variables 
that cannot be parsed.
2. Verify the parsed input, parameter, and output names.

Our goal was to create an indicator that accepts an input array with two columns (representing assets), 
runs our pipeline, and returns two signal arrays, each with two columns. To accomplish this, we wrote 
an expression that is standard Python code but includes some useful enhancements. For example, 
we defined the variable \`close\` as an input array by using the prefix \`@in\_\`. Additionally, we 
marked the three parameters—\`window\`, \`upper\_alpha\`, and \`lower\_alpha\`—by adding the prefix \`@p\_\`. 
When we run the expression, the indicator factory replaces \`@in\_close\` with our close prices and 
\`@p\_window\`, \`@p\_upper\_alpha\`, and \`@p\_lower\_alpha\` with the specified parameter values. 
The factory also automatically recognizes well-known variables such as \`vbt\` and \`wrapper\`, 
substituting them with the VBT module and the current Pandas wrapper. The last line lists the 
variables we want to return, and their names will automatically be used as output names.

Now, let's run this indicator across a grid of parameter combinations we want to test. 
Keep in mind that wide parameter grids can lead to out-of-memory errors: 
each parameter combination generates multiple arrays of the same shape as the data. 
To address this, you can use random search to efficiently reduce the number of parameter combinations.

\`\`\`pycon
>>> WINDOW\_SPACE = np.arange(5, 50).tolist()  # (1)!
>>> ALPHA\_SPACE = (np.arange(1, 100) / 1000).tolist()  # (2)!

>>> long\_entries, short\_entries = data.run(  # (3)!
...     PTS, 
...     window=WINDOW\_SPACE,
...     upper\_alpha=ALPHA\_SPACE,
...     lower\_alpha=ALPHA\_SPACE,
...     param\_product=True,
...     random\_subset=1000,  # (4)!
...     seed=42,  # (5)!
...     unpack=True  # (6)!
... )
>>> print(long\_entries.columns)
MultiIndex(\[( 5, 0.007,  0.09, 'ALGOUSDT'),
            ( 5, 0.007,  0.09, 'QTUMUSDT'),
            ( 5, 0.009, 0.086, 'ALGOUSDT'),
            ( 5, 0.009, 0.086, 'QTUMUSDT'),
            ( 5, 0.015, 0.082, 'ALGOUSDT'),
            ...
            (49, 0.091, 0.094, 'QTUMUSDT'),
            (49, 0.094, 0.054, 'ALGOUSDT'),
            (49, 0.094, 0.054, 'QTUMUSDT'),
            (49, 0.095, 0.074, 'ALGOUSDT'),
            (49, 0.095, 0.074, 'QTUMUSDT')\],
           names=\['pts\_window', 'pts\_upper\_alpha', 'pts\_lower\_alpha', 'symbol'\], length=2000)
\`\`\`

1. Test window values from 5 to 49.
2. Test alphas for the upper threshold from 0.1% to 10%.
3. Use \[Data.run\](https://vectorbt.pro/pvt\_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.run) to execute an indicator.
4. Randomly select 1,000 parameter combinations.
5. Make the results deterministic by setting a seed.
6. Return the output arrays instead of an indicator instance.

We used a data instance and instructed it to inspect the \`PTS\` indicator, find its input names 
among the arrays stored in the data instance, and pass these arrays along with the parameters 
to the indicator. This approach allows us to avoid dealing directly with input and output names :tada:

So, which parameter combinations are the most profitable?

\`\`\`pycon
>>> pf = vbt.Portfolio.from\_signals(
...     data,
...     entries=long\_entries,
...     short\_entries=short\_entries,
...     size=10,
...     size\_type="valuepercent100",
...     group\_by=vbt.ExceptLevel("symbol"),  # (1)!
...     cash\_sharing=True,
...     call\_seq="auto"
... )

>>> opt\_results = pd.concat((
...     pf.total\_return,
...     pf.trades.expectancy,
... ), axis=1)
>>> print(opt\_results.sort\_values(by="total\_return", ascending=False))
                                            total\_return  expectancy
pts\_window pts\_upper\_alpha pts\_lower\_alpha                          
41         0.076           0.001                0.503014    0.399218
15         0.079           0.001                0.489249    2.718049
16         0.023           0.016                0.474538    0.104986
6          0.078           0.048                0.445623    0.057574
41         0.028           0.001                0.441388    0.387182
...                                                  ...         ...
43         0.003           0.004               -0.263967   -0.131984
15         0.002           0.049               -0.273170   -0.182113
42         0.002           0.036               -0.316947   -0.110821
35         0.001           0.008               -0.330056   -0.196462
41         0.001           0.015               -0.363547   -0.191341

\[1000 rows x 2 columns\]
\`\`\`

1. Do not group symbols; in other words, group by parameter combination.

Now, let's proceed to the second optimization step. Pick one parameter combination from above 
and test various stop configurations using \[Param\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.Param):

\`\`\`pycon
>>> best\_index = opt\_results.idxmax()\["expectancy"\]  # (1)!
>>> best\_long\_entries = long\_entries\[best\_index\]
>>> best\_short\_entries = short\_entries\[best\_index\]
>>> STOP\_SPACE = \[np.nan\] + np.arange(1, 100).tolist()  # (2)!

>>> pf = vbt.Portfolio.from\_signals(
...     data,
...     entries=best\_long\_entries,
...     short\_entries=best\_short\_entries,
...     size=10,
...     size\_type="valuepercent100",
...     group\_by=vbt.ExceptLevel("symbol"),
...     cash\_sharing=True,
...     call\_seq="auto",
...     sl\_stop=vbt.Param(STOP\_SPACE),  # (3)!
...     tsl\_stop=vbt.Param(STOP\_SPACE),
...     tp\_stop=vbt.Param(STOP\_SPACE),
...     delta\_format="percent100",  # (4)!
...     stop\_exit\_price="close",  # (5)!
...     broadcast\_kwargs=dict(random\_subset=1000, seed=42)  # (6)!
... )

>>> opt\_results = pd.concat((
...     pf.total\_return,
...     pf.trades.expectancy,
... ), axis=1)
>>> print(opt\_results.sort\_values(by="total\_return", ascending=False))
                          total\_return  expectancy
sl\_stop tsl\_stop tp\_stop                          
86.0    98.0     NaN          0.602834    2.740152
47.0    62.0     NaN          0.587525    1.632014
43.0    90.0     NaN          0.579859    1.757150
16.0    62.0     54.0         0.412477    0.448345
2.0     95.0     71.0         0.406624    0.125115
...                                ...         ...
27.0    41.0     20.0        -0.063945   -0.046337
52.0    46.0     20.0        -0.065675   -0.067706
23.0    61.0     22.0        -0.071294   -0.057495
6.0     57.0     31.0        -0.080679   -0.029232
23.0    45.0     22.0        -0.090643   -0.073099

\[1000 rows x 2 columns\]
\`\`\`

1. Select the parameter combination with the highest expectancy.
2. Use NaN or a range from 1% to 99%.
3. The method will create the Cartesian product of all parameter arrays 
(same as using \`param\_product=True\` earlier).
4. All stops are provided as a percentage from the entry price, where 1 = 1%.
5. All orders will be executed at the end of the bar; otherwise, we cannot use \`call\_seq="auto"\`.
6. Randomly select 1,000 parameter combinations and make the results deterministic by setting a seed.

We can see how performance declines with lower SL and TSL values, and how the optimizer
tends to discourage the use of TP stops. Let's examine how a metric of interest depends 
on each type of stop value:

\`\`\`pycon
>>> def plot\_metric\_by\_stop(stop\_name, metric\_name, stat\_name, smooth):
...     from scipy.signal import savgol\_filter
...
...     values = pf.deep\_getattr(metric\_name)  # (1)!
...     values = values.vbt.select\_levels(stop\_name)  # (2)!
...     values = getattr(values.groupby(values.index), stat\_name)()  # (3)!
...     smooth\_values = savgol\_filter(values, smooth, 1)  # (4)!
...     smooth\_values = values.vbt.wrapper.wrap(smooth\_values)  # (5)!
...     fig = values.rename(metric\_name).vbt.plot()
...     smooth\_values.rename(f"{metric\_name} (smoothed)").vbt.plot(
...         trace\_kwargs=dict(line=dict(dash="dot", color="yellow")),
...         fig=fig, 
...     )
...     return fig
\`\`\`

1. This method allows us to access deeply chained attributes in the portfolio object,
such as \`trades.winning.pnl.mean\` for the average P&L of winning trades.
2. The index of any metric is a \`pd.MultiIndex\` with three levels, one for each parameter.
Let's select just one parameter (stop type) for analysis.
3. Since we tested a product of multiple parameters, each stop value might have multiple observations.
Aggregate these observations using a statistic of interest.
4. Apply the \[Savitzky–Golay filter\](https://en.wikipedia.org/wiki/Savitzky%E2%80%93Golay\_filter)
to smooth the values.
5. Because the filter returns a NumPy array, wrap it as a Pandas Series with the same index as our values.

=== "SL"

    \`\`\`pycon
    >>> plot\_metric\_by\_stop(
    ...     "sl\_stop", 
    ...     "trades.expectancy", 
    ...     "median",
    ...     10
    ... ).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/SL.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/SL.dark.svg#only-dark){: .iimg loading=lazy }

=== "TSL"

    \`\`\`pycon
    >>> plot\_metric\_by\_stop(
    ...     "tsl\_stop", 
    ...     "trades.expectancy", 
    ...     "median",
    ...     10
    ... ).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/TSL.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/TSL.dark.svg#only-dark){: .iimg loading=lazy }

=== "TP"

    \`\`\`pycon
    >>> plot\_metric\_by\_stop(
    ...     "tp\_stop", 
    ...     "trades.expectancy", 
    ...     "median",
    ...     10
    ... ).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/TP.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/TP.dark.svg#only-dark){: .iimg loading=lazy }

Now we have a general overview of how stop orders impact strategy performance.

### Level: Engineer :satellite\_orbital:

The approach above works well if you are in the strategy discovery phase.
Pandas and VBT's high-level API enable rapid and easy experimentation.
However, once you finish building a general framework for your strategy, you should 
focus on optimizing for the best CPU and memory performance. This will allow you 
to test the strategy on more assets, longer periods, and more parameter combinations.
Previously, we could test multiple combinations by loading them all into memory.
The only reason we did not encounter issues was thanks to using random search.
To make parameter search more practical, we should both speed up our backtests 
and reduce memory usage.

Let's begin by rewriting our indicator strictly with Numba:

\`\`\`pycon
>>> @njit(nogil=True)  # (1)!
... def pt\_signals\_nb(close, window=WINDOW, upper=UPPER, lower=LOWER):
...     x = np.expand\_dims(close\[:, 0\], 1)  # (2)!
...     y = np.expand\_dims(close\[:, 1\], 1)
...     \_, \_, zscore = vbt.ind\_nb.ols\_nb(x, y, window)  # (3)!
...     zscore\_1d = zscore\[:, 0\]  # (4)!
...     upper\_ts = np.full\_like(zscore\_1d, upper, dtype=float\_)  # (5)!
...     lower\_ts = np.full\_like(zscore\_1d, lower, dtype=float\_)
...     upper\_crossed = vbt.nb.crossed\_above\_1d\_nb(zscore\_1d, upper\_ts)  # (6)!
...     lower\_crossed = vbt.nb.crossed\_above\_1d\_nb(lower\_ts, zscore\_1d)  # (7)!
...     long\_entries = np.full\_like(close, False, dtype=np.bool\_)  # (8)!
...     short\_entries = np.full\_like(close, False, dtype=np.bool\_)
...     short\_entries\[upper\_crossed, 0\] = True  # (9)!
...     long\_entries\[upper\_crossed, 1\] = True
...     long\_entries\[lower\_crossed, 0\] = True
...     short\_entries\[lower\_crossed, 1\] = True
...     return long\_entries, short\_entries
\`\`\`

1. Releases the GIL, enabling multithreading in the future.
2. Select the specific column and expand to two dimensions as required for the next function.
3. This is a Numba-compiled function to run OLS. Every VBT indicator function without the \`\_1d\` suffix 
expects two-dimensional input.
4. Two dimensions in, two dimensions out. Since no more functions below require two-dimensional arrays, 
reduce it to one dimension.
5. Crossover functions need arrays of the same shape, but we want to compare against a single value,
so create an array of the same shape as the single value.
6. Notice the \`\_1d\` suffix? The function expects a one-dimensional input.
7. A crosses below B is equivalent to B crossing above A.
8. The output arrays have the same shape as the input array.
9. Numba does not support labels, so set the target column using its integer index.

Next, let's verify that our indicator produces the same number of signals as before:

\`\`\`pycon
>>> long\_entries, short\_entries = pt\_signals\_nb(data.close.values)  # (1)!
>>> long\_entries = data.symbol\_wrapper.wrap(long\_entries)  # (2)!
>>> short\_entries = data.symbol\_wrapper.wrap(short\_entries)

>>> print(long\_entries.sum())
symbol
ALGOUSDT    52
QTUMUSDT    73
dtype: int64
>>> print(short\_entries.sum())
symbol
ALGOUSDT    73
QTUMUSDT    52
dtype: int64
\`\`\`

1. Numba does not accept Pandas objects, so extract the NumPy array.
2. The function returns NumPy arrays, so wrap them back into the Pandas format.

The signals align perfectly.

Although this function is faster than the expression-based version, it does not solve the memory 
issue because output arrays must still be stored in memory to be passed to the simulator—especially 
when running multiple parameter combinations. To address this, we can wrap both the signal 
generation and simulation steps into a single pipeline and have it return lightweight arrays, such 
as just the total return. By leveraging an effective chunking approach, 
we could run nearly unlimited parameter combinations! :kite:

The next step is to rewrite the simulation part using Numba:

\`\`\`pycon
>>> @njit(nogil=True)
... def pt\_portfolio\_nb(
...     open, 
...     high, 
...     low, 
...     close,
...     long\_entries,
...     short\_entries,
...     sl\_stop=np.nan,
...     tsl\_stop=np.nan,
...     tp\_stop=np.nan,
... ):
...     target\_shape = close.shape  # (1)!
...     group\_lens = np.array(\[2\])  # (2)!
...     sim\_out = vbt.pf\_nb.from\_signals\_nb(  # (3)!
...         target\_shape=target\_shape,
...         group\_lens=group\_lens,
...         auto\_call\_seq=True,  # (4)!
...         open=open,
...         high=high,
...         low=low,
...         close=close,
...         long\_entries=long\_entries,
...         short\_entries=short\_entries,
...         size=10,
...         size\_type=vbt.pf\_enums.SizeType.ValuePercent100,  # (5)!
...         sl\_stop=sl\_stop,
...         tsl\_stop=tsl\_stop,
...         tp\_stop=tp\_stop,
...         delta\_format=vbt.pf\_enums.DeltaFormat.Percent100,
...         stop\_exit\_price=vbt.pf\_enums.StopExitPrice.Close
...     )
...     return sim\_out
\`\`\`

1. Target shape refers to the shape over which the simulator "walks," matching the shape of
our OHLC arrays.
2. One group consists of two columns. When any group has more than one column,
cash sharing is automatically enabled.
3. There are two available functions: \[from\_signals\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/nb/from\_signals/#vectorbtpro.portfolio.nb.from\_signals.from\_signals\_nb)
and \[from\_signal\_func\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/nb/from\_signals/#vectorbtpro.portfolio.nb.from\_signals.from\_signal\_func\_nb).
Since we already have the signal arrays, we should use the first function.
4. This is equivalent to using \`call\_seq="auto"\` as before.
5. Numba functions do not accept enumerated types as strings, only as integers.

Let's run it:

\`\`\`pycon
>>> sim\_out = pt\_portfolio\_nb(
...     data.open.values,
...     data.high.values,
...     data.low.values,
...     data.close.values,
...     long\_entries.values,
...     short\_entries.values
... )
\`\`\`

The output of this function is an instance of the 
\[SimulationOutput\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.SimulationOutput) type,
which you can use to construct a new \[Portfolio\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio)
instance for analysis:

\`\`\`pycon
>>> pf = vbt.Portfolio(
...     data.symbol\_wrapper.regroup(group\_by=True),  # (1)!
...     sim\_out,  # (2)!
...     open=data.open,  # (3)!
...     high=data.high,
...     low=data.low,
...     close=data.close,
...     cash\_sharing=True,
...     init\_cash=100  # (4)!
... )

>>> print(pf.total\_return)
0.19930328736504038
\`\`\`

1. The first argument should be the wrapper. Be sure to enable grouping using the same \`group\_by\` setting as before.
2. The second argument should be either the order records or the simulation output.
3. We must provide the arguments used during simulation, since this information
is not stored in the simulation output.
4. The default initial cash for the simulator is $100. If we do not provide it here, the portfolio
will set it based on the order records, which is a more expensive operation.

Now we need a Numba-compiled version of the analysis part:

\`\`\`pycon
>>> @njit(nogil=True)
... def pt\_metrics\_nb(close, sim\_out):
...     target\_shape = close.shape
...     group\_lens = np.array(\[2\])
...     filled\_close = vbt.nb.fbfill\_nb(close)  # (1)!
...     col\_map = vbt.rec\_nb.col\_map\_nb(  # (2)!
...         col\_arr=sim\_out.order\_records\["col"\], 
...         n\_cols=target\_shape\[1\]
...     )
...     total\_profit = vbt.pf\_nb.total\_profit\_nb(  # (3)!
...         target\_shape=target\_shape,
...         close=filled\_close,
...         order\_records=sim\_out.order\_records,
...         col\_map=col\_map
...     )
...     total\_profit\_grouped = vbt.pf\_nb.total\_profit\_grouped\_nb(  # (4)!
...         total\_profit=total\_profit,
...         group\_lens=group\_lens,
...     )\[0\]  # (5)!
...     total\_return = total\_profit\_grouped / 100  # (6)!
...     trade\_records = vbt.pf\_nb.get\_exit\_trades\_nb(  # (7)!
...         order\_records=sim\_out.order\_records, 
...         close=filled\_close, 
...         col\_map=col\_map
...     )
...     trade\_records = trade\_records\[  # (8)!
...         trade\_records\["status"\] == vbt.pf\_enums.TradeStatus.Closed
...     \]
...     expectancy = vbt.pf\_nb.expectancy\_reduce\_nb(  # (9)!
...         pnl\_arr=trade\_records\["pnl"\]
...     )
...     return total\_return, expectancy
\`\`\`

1. Forward-fill and backward-fill the close price to avoid NaNs in the equity.
2. The column mapper aggregates order records per column for easier mapping.
3. Total profit is calculated directly from the order records. This is one of the few metrics
that does not require any intermediate arrays, making it lightweight and fast.
4. The total profit calculated above is per column. We need to aggregate it by group.
5. Since this function returns an array and we have only one group, extract the sole value.
6. Total return is calculated from total profit using the initial value, which is $100.
7. Aggregate order records into trade records to extract P&L information.
8. Ignore any open trades.
9. Calculate expectancy. Normally this function runs per column. Since
we have only two columns that belong to the same group, we can run it directly.

Do not let this function intimidate you! We have calculated our metrics using only
the close price and order records—a process called "reconstruction."
The principle is simple: start with the metric you want, identify the information it requires,
find the function that provides that information, and repeat as needed.

Let's validate it:

\`\`\`pycon
>>> pt\_metrics\_nb(data.close.values, sim\_out)
(0.19930328736504038, 0.7135952049405152)
\`\`\`

100% accuracy.

Finally, let's combine all parts into a single pipeline and benchmark it:

\`\`\`pycon
>>> @njit(nogil=True)
... def pt\_pipeline\_nb(
...     open, 
...     high, 
...     low, 
...     close,
...     window=WINDOW,  # (1)!
...     upper=UPPER,
...     lower=LOWER,
...     sl\_stop=np.nan,
...     tsl\_stop=np.nan,
...     tp\_stop=np.nan,
... ):
...     long\_entries, short\_entries = pt\_signals\_nb(
...         close, 
...         window=window, 
...         upper=upper, 
...         lower=lower
...     )
...     sim\_out = pt\_portfolio\_nb(
...         open,
...         high,
...         low,
...         close,
...         long\_entries,
...         short\_entries,
...         sl\_stop=sl\_stop,
...         tsl\_stop=tsl\_stop,
...         tp\_stop=tp\_stop
...     )
...     return pt\_metrics\_nb(close, sim\_out)

>>> pt\_pipeline\_nb(
...     data.open.values,
...     data.high.values,
...     data.low.values,
...     data.close.values
... )
(0.19930328736504038, 0.7135952049405152)

>>> %%timeit
... pt\_pipeline\_nb(
...     data.open.values,
...     data.high.values,
...     data.low.values,
...     data.close.values
... )
5.4 ms ± 13.1 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
\`\`\`

1. Use our global defaults as default arguments.

Only 5 milliseconds per complete backtest :fire:

This performance encourages us to try intensive parameter optimization. Fortunately,
there are several ways to do this. The most convenient is to wrap the pipeline with the
\[@parameterized\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.parameterized)
decorator, which builds the parameter grid and calls the pipeline function on every parameter
combination. Since all our Numba functions release the GIL, we can use multithreading!
Let's test all parameter combinations for signal generation by breaking them into chunks
and distributing combinations within each chunk. This process took about 5 minutes on Apple Silicon.

!!! important
    Keep in mind that \`@parameterized\` builds the entire parameter grid even when a random subset
    is specified, which can take a significant amount of time. For example, 6 parameters with 100
    values each will create a grid with \`100 \*\* 6\`, or one trillion combinations, which is far
    too many to combine.

\`\`\`pycon
>>> param\_pt\_pipeline = vbt.parameterized(  # (1)!
...     pt\_pipeline\_nb, 
...     merge\_func="concat",  # (2)!
...     seed=42,
...     engine="threadpool",  # (3)!
...     chunk\_len="auto"
... )

>>> UPPER\_SPACE = \[st.norm.ppf(1 - x / 2) for x in ALPHA\_SPACE\]  # (4)!
>>> LOWER\_SPACE = \[-st.norm.ppf(1 - x / 2) for x in ALPHA\_SPACE\]
>>> POPT\_FILE = "temp/param\_opt.pickle"

>>> # vbt.remove\_file(POPT\_FILE, missing\_ok=True)
>>> if not vbt.file\_exists(POPT\_FILE):
...     param\_opt = param\_pt\_pipeline(
...         data.open.values,
...         data.high.values,
...         data.low.values,
...         data.close.values,
...         window=vbt.Param(WINDOW\_SPACE),
...         upper=vbt.Param(UPPER\_SPACE),
...         lower=vbt.Param(LOWER\_SPACE)
...     )
...     vbt.save(param\_opt, POPT\_FILE)
... else:
...     param\_opt = vbt.load(POPT\_FILE)

>>> total\_return, expectancy = param\_opt  # (5)!
\`\`\`

1. You can either decorate the function directly with \`@\`, or call the decorator with the function as
the first argument.
2. Concatenate each output across all parameter combinations.
3. Create a pool with the same number of threads as there are CPU cores.
4. Convert the alphas to z-score thresholds.
5. The format is the same as that returned by our pipeline.

\[=100% "Chunk 55131/55131"\]{: .candystripe .candystripe-animate }

Now, let's analyze the total return:

\`\`\`pycon
>>> print(total\_return)
window  upper     lower    
5       3.290527  -3.290527    0.000000
                  -3.090232    0.000000
                  -2.967738    0.000000
                  -2.878162    0.000000
                  -2.807034    0.000000
                                    ...
49      1.649721  -1.669593    0.196197
                  -1.664563    0.192152
                  -1.659575    0.190713
                  -1.654628    0.201239
                  -1.649721    0.204764
Length: 441045, dtype: float64

>>> grouped\_metric = total\_return.groupby(level=\["upper", "lower"\]).mean()
>>> grouped\_metric.vbt.heatmap(
...     trace\_kwargs=dict(colorscale="RdBu", zmid=0),
...     yaxis=dict(autorange="reversed")
... ).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/popt\_total\_return.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/popt\_total\_return.dark.svg#only-dark){: .iimg loading=lazy }

The effect of the thresholds appears to be asymmetric: the highest total return is achieved for the lowest
upper threshold and the lowest lower threshold. This means the neutral range between the two thresholds
is shifted downward as much as possible.

However, the \`@parameterized\` decorator has two key limitations: it runs only one parameter combination
at a time, and it must build the entire parameter grid, even when evaluating a random subset.
Why is running one combination at a time a limitation? Because only a few pipeline calls can be
parallelized at once. Even with the special argument \`distribute="chunks"\` that allows you
to parallelize entire chunks, calls within each chunk occur serially in a regular Python loop.
This is not ideal for multithreading, which requires the GIL to be released for the entire
procedure. If you try multiprocessing, the method must serialize all arguments (including the data)
on each pipeline call, which adds significant overhead. This may still be faster than the above approach
in some scenarios.

To process multiple parameter combinations within each thread, we need to split them into chunks and
write a parent Numba function that loops over the combinations in each chunk. Then, we can
parallelize this parent function using multithreading. The steps are: 1) manually construct
the parameter grid, 2) split it into chunks, and 3) iterate over the chunks and pass each to the parent
function for execution. The first step can be accomplished with
\[combine\_params\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.combine\_params), which is the :anatomical\_heart:
of the \`@parameterized\` decorator. The second and third steps can be done using another decorator,
\[@chunked\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/chunking/#vectorbtpro.utils.chunking.chunked), which specializes in argument
chunking. Let's do that! :muscle:

\`\`\`pycon
>>> @njit(nogil=True)
... def pt\_pipeline\_mult\_nb(
...     n\_params: int,  # (1)!
...     open:     tp.Array2d,  # (2)!
...     high:     tp.Array2d, 
...     low:      tp.Array2d, 
...     close:    tp.Array2d,
...     window:   tp.FlexArray1dLike = WINDOW,  # (3)!
...     upper:    tp.FlexArray1dLike = UPPER,
...     lower:    tp.FlexArray1dLike = LOWER,
...     sl\_stop:  tp.FlexArray1dLike = np.nan,
...     tsl\_stop: tp.FlexArray1dLike = np.nan,
...     tp\_stop:  tp.FlexArray1dLike = np.nan,
... ):
...     window\_ = vbt.to\_1d\_array\_nb(np.asarray(window))  # (4)!
...     upper\_ = vbt.to\_1d\_array\_nb(np.asarray(upper))
...     lower\_ = vbt.to\_1d\_array\_nb(np.asarray(lower))
...     sl\_stop\_ = vbt.to\_1d\_array\_nb(np.asarray(sl\_stop))
...     tsl\_stop\_ = vbt.to\_1d\_array\_nb(np.asarray(tsl\_stop))
...     tp\_stop\_ = vbt.to\_1d\_array\_nb(np.asarray(tp\_stop))
...
...     total\_return = np.empty(n\_params, dtype=float\_)  # (5)!
...     expectancy = np.empty(n\_params, dtype=float\_)
...
...     for i in range(n\_params):  # (6)!
...         total\_return\[i\], expectancy\[i\] = pt\_pipeline\_nb(
...             open,
...             high,
...             low,
...             close,
...             window=vbt.flex\_select\_1d\_nb(window\_, i),  # (7)!
...             upper=vbt.flex\_select\_1d\_nb(upper\_, i),
...             lower=vbt.flex\_select\_1d\_nb(lower\_, i),
...             sl\_stop=vbt.flex\_select\_1d\_nb(sl\_stop\_, i),
...             tsl\_stop=vbt.flex\_select\_1d\_nb(tsl\_stop\_, i),
...             tp\_stop=vbt.flex\_select\_1d\_nb(tp\_stop\_, i),
...         )
...     return total\_return, expectancy
\`\`\`

1. Number of parameter combinations in the chunk. This should be equal to the length of each parameter array.
2. These are called \[type hints\](https://realpython.com/lessons/type-hinting/):
they are not used by VBT (yet), but they help you quickly understand the expected argument format.
Type hint \`Array2d\` refers to a two-dimensional NumPy array.
3. The type hint \`FlexArray1dLike\` means either a single value or any NumPy array
that broadcasts against \`n\_params\`.
4. The required function below expects each parameter to be a one-dimensional NumPy array,
so we convert each to 1D in case it is not already. The result is saved to a new variable.
5. Create empty NumPy arrays to return. We will populate them gradually in the loop below.
6. Iterate over all parameter combinations in the chunk.
7. Select the parameter value for the current combination.

The magic of this function is that you do not need to make all parameters into arrays.
Thanks to flexible indexing, you can pass some parameters as arrays and keep others
at their default values. For example, you can test three window combinations like this:

\`\`\`pycon
>>> pt\_pipeline\_mult\_nb(
...     3,
...     data.open.values,
...     data.high.values,
...     data.low.values,
...     data.close.values,
...     window=np.array(\[10, 20, 30\])
... )
(array(\[ 0.11131525, -0.04819178,  0.13124959\]),
 array(\[ 0.01039436, -0.00483853,  0.01756337\]))
\`\`\`

Next, we will wrap the function with the \`@chunked\` decorator. Unlike \`@parameterized\`, we must specify
not only the chunks but also where to get the total number of parameter combinations and how to split
each individual argument. To help with this, VBT provides a collection of annotation classes.
For example, we can instruct \`@chunked\` to obtain the total number of combinations from the argument
\`n\_params\` by annotating this argument with the class \[ArgSizer\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/chunking/#vectorbtpro.utils.chunking.ArgSizer).
Then, we annotate each parameter as a flexible one-dimensional array using the class
\[FlexArraySlicer\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/chunking/#vectorbtpro.utils.chunking.FlexArraySlicer). When \`@chunked\`
builds a new chunk, it will "slice" the corresponding subset of values from each parameter array.

\`\`\`pycon
>>> chunked\_pt\_pipeline = vbt.chunked(
...     pt\_pipeline\_mult\_nb,
...     size=vbt.ArgSizer(arg\_query="n\_params"),
...     arg\_take\_spec=dict(
...         n\_params=vbt.CountAdapter(),
...         open=None,  # (1)!
...         high=None,
...         low=None,
...         close=None,
...         window=vbt.FlexArraySlicer(),
...         upper=vbt.FlexArraySlicer(),
...         lower=vbt.FlexArraySlicer(),
...         sl\_stop=vbt.FlexArraySlicer(),
...         tsl\_stop=vbt.FlexArraySlicer(),
...         tp\_stop=vbt.FlexArraySlicer()
...     ),
...     chunk\_len=1000,  # (2)!
...     merge\_func="concat",  # (3)!
...     execute\_kwargs=dict(  # (4)!
...         chunk\_len="auto",
...         engine="threadpool"
...     )
... )
\`\`\`

1. Set arguments that should be passed without chunking to None.
2. At most 1,000 parameter combinations are passed to \`pt\_pipeline\_mult\_nb\` at once.
3. Concatenate the resulting arrays.
4. In addition to chunking the parameter arrays, we can also bundle chunks into "super chunks".
Each super chunk consists of as many chunks as there are CPU cores, with one chunk per thread.

Here is what happens: whenever you call \`chunked\_pt\_pipeline\`, it retrieves the total number
of parameter combinations from the argument \`n\_params\`. Chunks of length 1,000 are created,
and each chunk is sliced from the parameter arguments; one chunk corresponds to a single call to
\`pt\_pipeline\_mult\_nb\`. To parallelize chunk execution, we group them into super chunks.
Chunks inside each super chunk are processed in parallel, while super chunks themselves run
serially. The progress bar reflects the progress of super chunks.

Now, let's build the complete parameter grid and run our function:

\`\`\`pycon
>>> param\_product, param\_index = vbt.combine\_params(  # (1)!
...     dict(
...         window=vbt.Param(WINDOW\_SPACE),  # (2)!
...         upper=vbt.Param(UPPER\_SPACE),
...         lower=vbt.Param(LOWER\_SPACE)
...     )
... )

>>> COPT\_FILE = "temp/chunked\_opt.pickle"

>>> # vbt.remove\_file(COPT\_FILE, missing\_ok=True)
>>> if not vbt.file\_exists(COPT\_FILE):
...     chunked\_opt = chunked\_pt\_pipeline(
...         len(param\_index),  # (3)!
...         data.open.values,
...         data.high.values,
...         data.low.values,
...         data.close.values,
...         window=param\_product\["window"\],
...         upper=param\_product\["upper"\],
...         lower=param\_product\["lower"\]
...     )
...     vbt.save(chunked\_opt, COPT\_FILE)
... else:
...     chunked\_opt = vbt.load(COPT\_FILE)
\`\`\`

1. Returns a dictionary of new parameter arrays and the associated index.
2. Uses the same format as for \`@parameterized\`.
3. Total number of parameter combinations.

\[=100% "Super chunk 56/56"\]{: .candystripe .candystripe-animate }

This approach runs about 40% faster than the previous method because the overhead of spawning a thread
is proportionally much lower compared to the larger workload within each thread. Additionally, memory
usage does not increase, since \`pt\_pipeline\_mult\_nb\` still processes only one parameter combination at a time.

\`\`\`pycon
>>> total\_return, expectancy = chunked\_opt

>>> total\_return = pd.Series(total\_return, index=param\_index)  # (1)!
>>> expectancy = pd.Series(expectancy, index=param\_index)
\`\`\`

1. The parameter index becomes the index for each array.

There are only two limitations left: generating parameter combinations takes a significant amount of time,
and if execution is interrupted, all optimization results are lost. These issues can be addressed by creating
a while-loop that, at each step, generates a subset of parameter combinations, executes them,
and saves the results to disk. This continues until all combinations have been processed successfully.
Another advantage is that you can resume from where execution last stopped, or even run the
optimization until you find a satisfactory set of parameters.

Suppose you want to include the stop parameters as well, but only execute a random subset of parameter
combinations. Generating all of them with \[combine\_params\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.combine\_params)
would not be feasible:

\`\`\`pycon
>>> GRID\_LEN = len(WINDOW\_SPACE) \* \\
...     len(UPPER\_SPACE) \* \\
...     len(LOWER\_SPACE) \* \\
...     len(STOP\_SPACE) \*\* 3
>>> print(GRID\_LEN)
441045000000
\`\`\`

There are nearly half a trillion parameter combinations :face\_exhaling:

Instead, we can select parameter combinations more efficiently using the
\[pick\_from\_param\_grid\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.pick\_from\_param\_grid) function.
This function takes a dictionary of parameter spaces (order matters), as well as the position of the
combination of interest, and returns the specific parameter combination at that position.
For example, to pick the combination at index 123,456,789:

\`\`\`pycon
>>> GRID = dict(
...     window=WINDOW\_SPACE,
...     upper=UPPER\_SPACE,
...     lower=LOWER\_SPACE,
...     sl\_stop=STOP\_SPACE,
...     tsl\_stop=STOP\_SPACE,
...     tp\_stop=STOP\_SPACE,
... )
>>> vbt.pprint(vbt.pick\_from\_param\_grid(GRID, 123\_456\_789))
dict(
    window=5,
    upper=3.090232306167813,
    lower=-2.241402727604947,
    sl\_stop=45.0,
    tsl\_stop=67.0,
    tp\_stop=89.0
)
\`\`\`

This gives you the exact parameter combination you would get by combining all parameters and running
\`param\_index\[123\_456\_789\]\`, but with almost no impact on performance or memory!

Now, we can build our while-loop. Let's perform a random parameter search until we get at least
100 values with expectancy of 1 or more!

\`\`\`pycon
>>> FOUND\_FILE = "temp/found.pickle"
>>> BEST\_N = 100  # (1)!
>>> BEST\_TH = 1.0  # (2)!
>>> CHUNK\_LEN = 10\_000  # (3)!

>>> # vbt.remove\_file(FOUND\_FILE, missing\_ok=True)
>>> if vbt.file\_exists(FOUND\_FILE):
...     found = vbt.load(FOUND\_FILE)  # (4)!
>>> else:
...     found = None
>>> with (  # (5)!
...     vbt.ProgressBar(
...         desc="Found", 
...         initial=0 if found is None else len(found),
...         total=BEST\_N
...     ) as pbar1,
...     vbt.ProgressBar(
...         desc="Processed"
...     ) as pbar2
... ):
...     while found is None or len(found) < BEST\_N:  # (6)!
...         param\_df = pd.DataFrame(\[
...             vbt.pick\_from\_param\_grid(GRID)  # (7)!
...             for \_ in range(CHUNK\_LEN)
...         \])
...         param\_index = pd.MultiIndex.from\_frame(param\_df)
...         \_, expectancy = chunked\_pt\_pipeline(  # (8)!
...             CHUNK\_LEN,
...             data.open.values,
...             data.high.values,
...             data.low.values,
...             data.close.values,
...             window=param\_df\["window"\],
...             upper=param\_df\["upper"\],
...             lower=param\_df\["lower"\],
...             sl\_stop=param\_df\["sl\_stop"\],
...             tsl\_stop=param\_df\["tsl\_stop"\],
...             tp\_stop=param\_df\["tp\_stop"\],
...             \_chunk\_len=None,
...             \_execute\_kwargs=dict(
...                 chunk\_len=None
...             )
...         )
...         expectancy = pd.Series(expectancy, index=param\_index)
...         best\_mask = expectancy >= BEST\_TH
...         if best\_mask.any():  # (9)!
...             best = expectancy\[best\_mask\]
...             if found is None:
...                 found = best
...             else:
...                 found = pd.concat((found, best))
...                 found = found\[~found.index.duplicated(keep="first")\]
...             vbt.save(found, FOUND\_FILE)
...             pbar1.update\_to(len(found))
...             pbar1.refresh()
...         pbar2.update(len(expectancy))
\`\`\`

1. Number of best parameter combinations to search for.
2. Expectancy threshold after which a parameter combination is considered the best.
3. Number of parameter combinations to process during each iteration of the while-loop.
4. Load cached results from previous execution(s).
5. Create two progress bars: one shows how many best parameter combinations have been found, 
and the other shows the total number of parameter combinations processed.
6. Run the loop until the requested number of best parameter combinations have been found.
7. Generate a random parameter combination \`CHUNK\_LEN\` times.
8. Backtest the generated parameter combinations using chunking.
9. If any parameter combinations that meet the condition are found, concatenate them with others, 
cache to disk, and update the first progress bar.

\[=100% "Found 100/100"\]{: .candystripe .candystripe-animate }

You can now run the cell above, stop execution at any time, and resume later :date:

By grouping similar parameter combinations into the same bucket, you can also aggregate them
to derive a single optimal parameter combination:

\`\`\`pycon
>>> def get\_param\_median(param):  # (1)!
...     return found.index.get\_level\_values(param).to\_series().median()

>>> pt\_pipeline\_nb(
...     data.open.values, 
...     data.high.values, 
...     data.low.values, 
...     data.close.values,
...     window=int(get\_param\_median("window")),
...     upper=get\_param\_median("upper"),
...     lower=get\_param\_median("lower"),
...     sl\_stop=get\_param\_median("sl\_stop"),
...     tsl\_stop=get\_param\_median("tsl\_stop"),
...     tp\_stop=get\_param\_median("tp\_stop")
... )
(0.24251123364060986, 1.7316489316495804)
\`\`\`

1. Get the median of the parameter values.

You can see that the median parameter combination also meets our expectancy condition.

However, sometimes you do not need to test so many parameter combinations. You can simply use
an established parameter optimization framework like \[Optuna\](https://optuna.org/).
This approach offers several advantages: you can use the original \`pt\_pipeline\_nb\` function
without decorators, you do not need to handle large parameter grids, and you can apply
various statistical strategies to improve search effectiveness and reduce the number
of parameter combinations you need to test.

!!! info
    Make sure to install Optuna before running the following cell.

\`\`\`pycon
>>> import optuna

>>> optuna.logging.disable\_default\_handler()
>>> optuna.logging.set\_verbosity(optuna.logging.WARNING)

>>> def objective(trial):
...     window = trial.suggest\_categorical("window", WINDOW\_SPACE)  # (1)!
...     upper = trial.suggest\_categorical("upper", UPPER\_SPACE)  # (2)!
...     lower = trial.suggest\_categorical("lower", LOWER\_SPACE)
...     sl\_stop = trial.suggest\_categorical("sl\_stop", STOP\_SPACE)
...     tsl\_stop = trial.suggest\_categorical("tsl\_stop", STOP\_SPACE)
...     tp\_stop = trial.suggest\_categorical("tp\_stop", STOP\_SPACE)
...     total\_return, expectancy = pt\_pipeline\_nb(
...         data.open.values,
...         data.high.values,
...         data.low.values,
...         data.close.values,
...         window=window,
...         upper=upper,
...         lower=lower,
...         sl\_stop=sl\_stop,
...         tsl\_stop=tsl\_stop,
...         tp\_stop=tp\_stop
...     )
...     if np.isnan(total\_return):
...         raise optuna.TrialPruned()  # (3)!
...     if np.isnan(expectancy):
...         raise optuna.TrialPruned()
...     return total\_return, expectancy

>>> study = optuna.create\_study(directions=\["maximize", "maximize"\])  # (4)!
>>> study.optimize(objective, n\_trials=1000)  # (5)!

>>> trials\_df = study.trials\_dataframe(attrs=\["params", "values"\])
>>> trials\_df.set\_index(\[
...     "params\_window", 
...     "params\_upper", 
...     "params\_lower",
...     "params\_sl\_stop",
...     "params\_tsl\_stop",
...     "params\_tp\_stop"
... \], inplace=True)
>>> trials\_df.index.rename(\[
...     "window", 
...     "upper", 
...     "lower",
...     "sl\_stop",
...     "tsl\_stop",
...     "tp\_stop"
... \], inplace=True)
>>> trials\_df.columns = \["total\_return", "expectancy"\]
>>> trials\_df = trials\_df\[~trials\_df.index.duplicated(keep="first")\]
>>> print(trials\_df.sort\_values(by="total\_return", ascending=False))
                                                    total\_return  expectancy
window upper    lower     sl\_stop tsl\_stop tp\_stop                          
44     1.746485 -3.072346 9.0     67.0     55.0         0.558865    0.184924
42     1.871392 -3.286737 53.0    98.0     55.0         0.500062    0.330489
                                           77.0         0.496029    0.334432
5      1.746485 -1.759648 76.0    94.0     45.0         0.492721    0.043832
43     1.807618 -3.192280 87.0    36.0     60.0         0.475732    0.229682
...                                                          ...         ...
7      2.639845 -3.072346 80.0    95.0     55.0              NaN         NaN
5      3.117886 -3.072346 78.0    90.0     47.0              NaN         NaN
       2.769169 -3.072346 78.0    90.0     55.0              NaN         NaN
7      3.098951 -3.072346 78.0    95.0     55.0              NaN         NaN
       2.607536 -3.072346 78.0    95.0     77.0              NaN         NaN

\[892 rows x 2 columns\]
\`\`\`

1. You can also use \`suggest\_int\` here (pass two bounds instead of a list).
2. You can also use \`suggest\_float\` here (pass two bounds instead of a list).
3. Prune the trial because Optuna does not tolerate NaNs.
4. Maximize both metrics.
5. Run 1,000 non-pruned trials.

The only downside of this approach is that you are limited by the chosen results and cannot 
explore the entire parameter landscape, which is something VBT is fully designed for.

### Level: Architect :flying\_saucer:

Suppose you want full control over execution, such as allowing at most
one rebalancing operation within N days. Additionally, you want to avoid pre-calculating
arrays and do everything in an event-driven manner. For simplicity, let's switch our 
signaling algorithm from cointegration with OLS to a basic distance measure: log prices.

We will implement the strategy as a custom signal function for \[Portfolio.from\_signals\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from\_signals).
This is the most challenging approach because the signal function is called for each column,
while our decisions need to be made per segment (i.e., once for both columns). A good strategy
is to perform calculations for the first column processed at each bar, store results in some
temporary arrays, and then access those arrays from each column to return the signals.
An ideal place to store these arrays is the built-in named tuple \`in\_outputs\`, accessible
both during simulation and analysis.

\`\`\`pycon
>>> InOutputs = namedtuple("InOutputs", \["spread", "zscore"\])  # (1)!

>>> @njit(nogil=True, boundscheck=True)  # (2)!
... def can\_execute\_nb(c, wait\_days):  # (3)!
...     if c.order\_counts\[c.col\] == 0:  # (4)!
...         return True
...     last\_order = c.order\_records\[c.order\_counts\[c.col\] - 1, c.col\]  # (5)!
...     ns\_delta = c.index\[c.i\] - c.index\[last\_order.idx\]  # (6)!
...     if ns\_delta >= wait\_days \* vbt.dt\_nb.d\_ns:  # (7)!
...         return True
...     return False

>>> @njit(nogil=True, boundscheck=True)
... def create\_signals\_nb(c, upper, lower, wait\_days):  # (8)!
...     \_upper = vbt.pf\_nb.select\_nb(c, upper)  # (9)!
...     \_lower = vbt.pf\_nb.select\_nb(c, lower)
...     \_wait\_days = vbt.pf\_nb.select\_nb(c, wait\_days)
...
...     if c.i > 0:  # (10)!
...         prev\_zscore = c.in\_outputs.zscore\[c.i - 1, c.group\]
...         zscore = c.in\_outputs.zscore\[c.i, c.group\]
...         if prev\_zscore < \_upper and zscore > \_upper:  # (11)!
...             if can\_execute\_nb(c, \_wait\_days):
...                 if c.col % 2 == 0:
...                     return False, False, True, False  # (12)!
...                 return True, False, False, False  # (13)!
...         if prev\_zscore > \_lower and zscore < \_lower:
...             if can\_execute\_nb(c, \_wait\_days):
...                 if c.col % 2 == 0:
...                     return True, False, False, False
...                 return False, False, True, False
...     return False, False, False, False  # (14)!

>>> @njit(nogil=True, boundscheck=True)
... def signal\_func\_nb(c, window, upper, lower, wait\_days):  # (15)!
...     \_window = vbt.pf\_nb.select\_nb(c, window)
...         
...     if c.col % 2 == 0:  # (16)!
...         x = vbt.pf\_nb.select\_nb(c, c.close, col=c.col)  # (17)!
...         y = vbt.pf\_nb.select\_nb(c, c.close, col=c.col + 1)
...         c.in\_outputs.spread\[c.i, c.group\] = np.log(y) - np.log(x)  # (18)!
...         
...         window\_start = c.i - \_window + 1  # (19)!
...         window\_end = c.i + 1  # (20)!
...         if window\_start >= 0:  # (21)!
...             s = c.in\_outputs.spread\[window\_start : window\_end, c.group\]
...             s\_mean = np.nanmean(s)
...             s\_std = np.nanstd(s)
...             c.in\_outputs.zscore\[c.i, c.group\] = (s\[-1\] - s\_mean) / s\_std
...     return create\_signals\_nb(c, upper, lower, wait\_days)
\`\`\`

1. Defines a named tuple containing two arrays: spread and its z-score.
2. It is always recommended to enable bound checking while developing a signal function 
to avoid out-of-bounds errors; however, be aware this may slightly reduce performance.
3. Helper Numba function to check whether orders can be placed at the current bar.
4. Checks if this is the asset's first order in the simulation.
5. Retrieves the last order if this is not the asset's first order in the simulation.
6. Gets the elapsed time in nanoseconds between the current bar and the bar of the last order.
7. Checks if the elapsed time is at least \`wait\_days\`. Since we compare nanoseconds,
we must multiply \`wait\_days\` by one day's nanoseconds to get the value in nanoseconds.
8. Another helper Numba function to create signals from the available spread and z-score.
9. Our parameters are flexible arrays rather than single values, so we need to select 
the element corresponding to the current row and column.
10. Crossovers are based on the current and previous value, so ensure the previous value is available.
11. Very basic crossover comparison.
12. Short entry.
13. Long entry.
14. Do not forget this line; otherwise, the function will return None and cause an ugly error.
15. The main signal function, acting as a callback and being called by the simulator. 
The first argument in each signal function is the context of type
\[SignalContext\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.SignalContext). 
Other arguments are user-defined, such as the parameters.
16. If this is the first column in the bar, calculate the spread and its z-score,
since both are group metrics and must be available to both columns.
17. The close price is also a flexible array.
18. Both spread and z-score are two-dimensional arrays with columns representing groups.
19. The z-score is calculated using the mean and standard deviation of a data window.
20. In integer indexing, the stop is exclusive, so add 1 to include the current bar.
21. Ensure the window start is greater than or equal to zero; if it is negative, the last values 
of the array will be used instead!

Now, create a pipeline that runs simulation using the signal function above:

\`\`\`pycon
>>> WAIT\_DAYS = 30

>>> def iter\_pt\_portfolio(
...     window=WINDOW, 
...     upper=UPPER, 
...     lower=LOWER, 
...     wait\_days=WAIT\_DAYS,
...     signal\_func\_nb=signal\_func\_nb,  # (1)!
...     more\_signal\_args=(),
...     \*\*kwargs
... ):
...     return vbt.Portfolio.from\_signals(
...         data,
...         broadcast\_named\_args=dict(  # (2)!
...             window=window,
...             upper=upper,
...             lower=lower,
...             wait\_days=wait\_days
...         ),
...         in\_outputs=vbt.RepEval("""
...             InOutputs(
...                 np.full((target\_shape\[0\], target\_shape\[1\] // 2), np.nan), 
...                 np.full((target\_shape\[0\], target\_shape\[1\] // 2), np.nan)
...             )
...         """, context=dict(InOutputs=InOutputs)),  # (3)!
...         signal\_func\_nb=signal\_func\_nb,  # (4)!
...         signal\_args=(  # (5)!
...             vbt.Rep("window"),  # (6)!
...             vbt.Rep("upper"),
...             vbt.Rep("lower"),
...             vbt.Rep("wait\_days"),
...             \*more\_signal\_args
...         ),
...         size=10,
...         size\_type="valuepercent100",
...         group\_by=vbt.ExceptLevel("symbol"),
...         cash\_sharing=True,
...         call\_seq="auto",
...         delta\_format="percent100",
...         stop\_exit\_price="close",
...         \*\*kwargs
...     )

>>> pf = iter\_pt\_portfolio()
\`\`\`

1. This lets you later replace the signal function with another one—stay tuned!
2. By defining parameters here, you make them flexible; you can
provide single values, or arrays per row, column, or even element.
3. Since we do not know the target shape for the temporary arrays yet, create a Python 
expression that generates the named tuple with arrays and delay evaluation until the target 
shape is known.
4. Instead of passing signal arrays, we now pass the signal function.
5. These arguments appear after the context argument \`c\` in \`signal\_func\_nb\`.
6. Use templates to substitute array names from \`broadcast\_named\_args\` with the actual arrays 
once they are prepared.

Let's visually validate our implementation:

\`\`\`pycon
>>> fig = vbt.make\_subplots(  # (1)!
...     rows=2, 
...     cols=1, 
...     vertical\_spacing=0,
...     shared\_xaxes=True
... )
>>> zscore = pf.get\_in\_output("zscore").rename("Z-score")  # (2)!
>>> zscore.vbt.plot(  # (3)!
...     add\_trace\_kwargs=dict(row=1, col=1),
...     fig=fig
... )
>>> fig.add\_hline(row=1, y=UPPER, line\_color="orangered", line\_dash="dot")
>>> fig.add\_hline(row=1, y=0, line\_color="yellow", line\_dash="dot")
>>> fig.add\_hline(row=1, y=LOWER, line\_color="limegreen", line\_dash="dot")
>>> orders = pf.orders.regroup(group\_by=False).iloc\[:, 0\]  # (4)!
>>> exit\_mask = orders.side\_sell.get\_pd\_mask(idx\_arr="signal\_idx")  # (5)!
>>> entry\_mask = orders.side\_buy.get\_pd\_mask(idx\_arr="signal\_idx")  # (6)!
>>> upper\_crossed = zscore.vbt.crossed\_above(UPPER)
>>> lower\_crossed = zscore.vbt.crossed\_below(LOWER)
>>> (upper\_crossed & ~exit\_mask).vbt.signals.plot\_as\_exits(  # (7)!
...     pf.get\_in\_output("zscore"),
...     trace\_kwargs=dict(
...         name="Exits (ignored)", 
...         marker=dict(color="lightgray"), 
...         opacity=0.5
...     ),
...     add\_trace\_kwargs=dict(row=1, col=1),
...     fig=fig
... )
>>> (lower\_crossed & ~entry\_mask).vbt.signals.plot\_as\_entries(
...     pf.get\_in\_output("zscore"),
...     trace\_kwargs=dict(
...         name="Entries (ignored)", 
...         marker=dict(color="lightgray"), 
...         opacity=0.5
...     ),
...     add\_trace\_kwargs=dict(row=1, col=1),
...     fig=fig
... )
>>> exit\_mask.vbt.signals.plot\_as\_exits(  # (8)!
...     pf.get\_in\_output("zscore"),
...     add\_trace\_kwargs=dict(row=1, col=1),
...     fig=fig
... )
>>> entry\_mask.vbt.signals.plot\_as\_entries(
...     pf.get\_in\_output("zscore"),
...     add\_trace\_kwargs=dict(row=1, col=1),
...     fig=fig
... )
>>> pf.plot\_allocations(  # (9)!
...     add\_trace\_kwargs=dict(row=2, col=1),
...     fig=fig
... )
>>> rebalancing\_dates = data.index\[np.unique(orders.idx.values)\]
>>> for date in rebalancing\_dates:
...     fig.add\_vline(row=2, x=date, line\_color="teal", line\_dash="dot")
>>> fig.update\_layout(height=600)
>>> fig.show()
\`\`\`

1. Create two subplots.
2. The temporary spread array filled in the signal function can be accessed with
\[Portfolio.get\_in\_output\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.get\_in\_output).
It will be automatically converted into a Pandas format for you.
3. Plot the spread on the first subplot.
4. The portfolio object and the orders object are grouped. Since we only need the first asset 
to visualize rebalancing decisions, we ungroup the object and select the first asset.
5. Get the mask for when the first asset was sold, indicating the upper threshold was crossed.
6. Get the mask for when the first asset was bought, indicating the lower threshold was crossed.
7. Plot ignored signals, which are crossover signals that were not executed.
8. Plot executed signals.
9. Plot the allocations on the second subplot.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/iter\_pt\_portfolio.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/iter\_pt\_portfolio.dark.svg#only-dark){: .iimg loading=lazy }

Great! But what about parameter optimization? Since our parameters are defined as flexible arrays,
we can pass them in many formats, including \[Param\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.Param).
Now, let's see how varying the waiting time affects the number of orders:

\`\`\`pycon
>>> WAIT\_SPACE = np.arange(30, 370, 5).tolist()

>>> pf = iter\_pt\_portfolio(wait\_days=vbt.Param(WAIT\_SPACE))
>>> pf.orders.count().vbt.scatterplot(
...     xaxis\_title="Wait days",
...     yaxis\_title="Order count"
... ).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/wait\_days.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/pairs-trading/wait\_days.dark.svg#only-dark){: .iimg loading=lazy }

Keep in mind that the optimization approach above requires a lot of RAM because the OHLC data 
must be tiled as many times as there are parameter combinations. This is the same consideration
as when optimizing \`sl\_stop\` and other built-in parameters.
You may also notice that both compilation and execution take much longer than before.
Signal functions cannot be cached, so the entire simulator must be compiled from scratch
with each runtime. Additionally, we must use a different simulation path than the faster
path based on signal arrays that we used earlier. Also, our z-score implementation is quite slow 
since the mean and standard deviation need to be recomputed for every single bar 
(unlike the previous OLS indicator, which used one of the fastest algorithms available).

\`\`\`pycon
>>> with (vbt.Timer() as timer, vbt.MemTracer() as tracer):
...     iter\_pt\_portfolio(wait\_days=vbt.Param(WAIT\_SPACE))

>>> print(timer.elapsed())
8.62 seconds

>>> print(tracer.peak\_usage())
306.2 MB
\`\`\`

While compilation time is difficult to reduce, execution time can be significantly decreased
by replacing both the mean and standard deviation operations with a z-score accumulator.
A z-score accumulator computes z-scores incrementally, avoiding expensive aggregations.
Fortunately, VBT already includes such an accumulator:
\[rolling\_zscore\_acc\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/rolling/#vectorbtpro.generic.nb.rolling.rolling\_zscore\_acc\_nb).
The process works like this: you provide an input state containing the information 
needed to process the value for this bar, pass it to the accumulator, and receive an output state 
that contains both the calculated z-score and the updated information for the next bar.

The first question is: what information should we store? In general, you need to keep 
the data that the accumulator updates and will require as input for the next bar.
The next question is: how do we store this information? A state usually consists 
of several individual values, but named tuples are immutable. The trick is to use 
a \[structured NumPy array\](https://numpy.org/doc/stable/user/basics.rec.html), which you can think 
of as a regular NumPy array that holds mutable named tuples. We will create a 
one-dimensional array with one tuple per group.

\`\`\`pycon
>>> zscore\_state\_dt = np.dtype(  # (1)!
...     \[
...         ("cumsum", float\_),
...         ("cumsum\_sq", float\_),
...         ("nancnt", int\_)
...     \],
...     align=True,
... )

>>> @njit(nogil=True, boundscheck=True)
... def stream\_signal\_func\_nb(
...     c, 
...     window, 
...     upper, 
...     lower, 
...     wait\_days, 
...     zscore\_state  # (2)!
... ):
...     \_window = vbt.pf\_nb.select\_nb(c, window)
...         
...     if c.col % 2 == 0:
...         x = vbt.pf\_nb.select\_nb(c, c.close, col=c.col)
...         y = vbt.pf\_nb.select\_nb(c, c.close, col=c.col + 1)
...         c.in\_outputs.spread\[c.i, c.group\] = np.log(y) - np.log(x)
...         
...         value = c.in\_outputs.spread\[c.i, c.group\]  # (3)!
...         pre\_i = c.i - \_window
...         if pre\_i >= 0:
...             pre\_window\_value = c.in\_outputs.spread\[pre\_i, c.group\]  # (4)!
...         else:
...             pre\_window\_value = np.nan
...         zscore\_in\_state = vbt.enums.RollZScoreAIS(  # (5)!
...             i=c.i,
...             value=value,
...             pre\_window\_value=pre\_window\_value,
...             cumsum=zscore\_state\["cumsum"\]\[c.group\],
...             cumsum\_sq=zscore\_state\["cumsum\_sq"\]\[c.group\],
...             nancnt=zscore\_state\["nancnt"\]\[c.group\],
...             window=\_window,
...             minp=\_window,
...             ddof=0
...         )
...         zscore\_out\_state = vbt.nb.rolling\_zscore\_acc\_nb(zscore\_in\_state)  # (6)!
...         c.in\_outputs.zscore\[c.i, c.group\] = zscore\_out\_state.value  # (7)!
...         zscore\_state\["cumsum"\]\[c.group\] = zscore\_out\_state.cumsum  # (8)!
...         zscore\_state\["cumsum\_sq"\]\[c.group\] = zscore\_out\_state.cumsum\_sq
...         zscore\_state\["nancnt"\]\[c.group\] = zscore\_out\_state.nancnt
...         
...     return create\_signals\_nb(c, upper, lower, wait\_days)
\`\`\`

1. Specify the fields of a structured array that will hold the state.
2. The structured array will be created later using a template.
3. The z-score is based on the spread.
4. The calculation function also needs the spread value from \`window\` bars ago.
5. Create an input state using all available information.
6. Run the calculation function.
7. Store the returned z-score.
8. Remember to also store the new state.

Next, we will adapt the portfolio function to use the new signal function:

\`\`\`pycon
>>> stream\_pt\_portfolio = partial(  # (1)!
...     iter\_pt\_portfolio,
...     signal\_func\_nb=stream\_signal\_func\_nb,
...     more\_signal\_args=(  # (2)!
...         vbt.RepEval(  # (3)!
...             """
...             n\_groups = target\_shape\[1\] // 2
...             zscore\_state = np.empty(n\_groups, dtype=zscore\_state\_dt)
...             zscore\_state\["cumsum"\] = 0.0
...             zscore\_state\["cumsum\_sq"\] = 0.0
...             zscore\_state\["nancnt"\] = 0
...             zscore\_state
...             """, 
...             context=dict(zscore\_state\_dt=zscore\_state\_dt)
...         ),
...     )
... )
\`\`\`

1. Copy the \`iter\_pt\_portfolio\` function and replace its default signal function.
2. The new signal function expects a structured array as its last argument. This is why
we made it possible to provide additional arguments earlier.
3. Since the number of groups is not known yet, create an expression template that will be
substituted once this information becomes available. The template should create, initialize, and return a new
structured array with the data type defined above.

All set! Let's build the portfolio and validate it by comparing with the previous one:

\`\`\`pycon
>>> stream\_pf = stream\_pt\_portfolio()
>>> print(stream\_pf.total\_return)
0.15210165047643728

>>> pf = iter\_pt\_portfolio()
>>> print(pf.total\_return)
0.15210165047643728
\`\`\`

Finally, let's benchmark the new portfolio using \`WAIT\_SPACE\`:

\`\`\`pycon
>>> with (vbt.Timer() as timer, vbt.MemTracer() as tracer):
...     stream\_pt\_portfolio(wait\_days=vbt.Param(WAIT\_SPACE))

>>> print(timer.elapsed())
1.52 seconds

>>> print(tracer.peak\_usage())
306.2 MB
\`\`\`

!!! info
    Run this cell at least twice, because the simulation may need to compile during the first run.
    This is necessary because compilation is triggered whenever a new set of argument \_\_types\_\_ is detected.
    A single parameter combination and multiple parameter combinations produce two distinct sets of argument types.

The final optimization to further speed up the simulation for multiple parameter combinations is to enable
in-house chunking. There is one important detail: \[Portfolio.from\_signals\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from\_signals)
cannot chunk user-defined arrays automatically, so we must provide the chunking
specifications for all arguments in both \`signal\_args\` and \`in\_outputs\`:

\`\`\`pycon
>>> chunked\_stream\_pt\_portfolio = partial(
...     stream\_pt\_portfolio,
...     chunked=dict(  # (1)!
...         engine="threadpool",
...         arg\_take\_spec=dict(
...             signal\_args=vbt.ArgsTaker(
...                 vbt.flex\_array\_gl\_slicer,  # (2)!
...                 vbt.flex\_array\_gl\_slicer,
...                 vbt.flex\_array\_gl\_slicer,
...                 vbt.flex\_array\_gl\_slicer,
...                 vbt.ArraySlicer(axis=0)  # (3)!
...             ),
...             in\_outputs=vbt.SequenceTaker(\[
...                 vbt.ArraySlicer(axis=1),  # (4)!
...                 vbt.ArraySlicer(axis=1)
...             \])
...         )
...     )
... )

>>> with (vbt.Timer() as timer, vbt.MemTracer() as tracer):
...     chunked\_stream\_pt\_portfolio(wait\_days=vbt.Param(WAIT\_SPACE))

>>> print(timer.elapsed())
520.08 milliseconds

>>> print(tracer.peak\_usage())
306.4 MB
\`\`\`

1. Accepts the same arguments as \`@chunked\`, provided as a dictionary.
2. This special type, widely used by simulators, first chunks the groups, then maps each group to its
respective columns, and finally slices the columns out of a flexible array.
3. An array slicer without a mapper will slice arrays by groups. This is exactly what we
want here, since \`zscore\_state\` has its length equal to the number of groups.
4. Temporary arrays \`spread\` and \`zscore\` are also group metrics, but they are two-dimensional arrays,
so we must use the second axis (columns).

With this optimization, simulation is now an order of magnitude faster than before :dash:

!!! hint
    To reduce memory usage during execution, use the "serial" engine or build super chunks.

## Summary

Pairs trading uses two columns with opposite position signs, making it an almost perfect use case
for VBT's integrated grouping mechanics. It gets even better: most pairs trading strategies
can be implemented using semi-vectorized, iterative, and streaming approaches alike. This
tutorial demonstrates how to incrementally develop a strategy and then optimize it for high
performance and low resource consumption.

We started with the discovery phase, designing and implementing the strategy from
the ground up using various high-level tools without focusing on performance. Once the
strategy's framework was established, we focused on speeding up execution to discover
more profitable configurations in less time. Finally, we moved to an iterative approach to
gain complete control over execution. But this does not have to be the end of the story:
if you are curious, you can build your own simulator and unlock power that others can only
dream of :superhero:

\[:material-language-python: Python code\](https://vectorbt.pro/pvt\_6d1b3986/assets/jupytext/tutorials/pairs-trading.py.txt){ .md-button target="blank\_" }
\[:material-notebook-outline: Notebook\](https://github.com/polakowo/vectorbt.pro/blob/main/notebooks/PairsTrading.ipynb){ .md-button target="blank\_" }