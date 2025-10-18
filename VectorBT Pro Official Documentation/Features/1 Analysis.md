---
title: Analysis
description: Analysis features of VectorBT PRO
icon: material/chart-bubble
---

# :material-chart-bubble: Analysis

## Simulation ranges

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_5_15.svg){ loading=lazy }

- [x] Each simulation starts and ends at specific points, usually matching the first and last rows of your
data. You can set a different simulation range beforehand, and now, you can also adjust this range during
the simulation. This flexibility lets you stop the simulation when further processing is unnecessary.
Additionally, the date range is saved in the portfolio object, so all metrics and subplots recognize it.
Processing only the relevant dates speeds up execution and adds a new dimension to your analysis:
isolated time windows :microscope:

```pycon title="Example 1: Simulate a quick liquidation scenario"
>>> @njit
... def post_segment_func_nb(c):
...     value = vbt.pf_nb.get_group_value_nb(c, c.group)
...     if value <= 0:
...         vbt.pf_nb.stop_group_sim_nb(c, c.group)  # (1)!

>>> pf = vbt.PF.from_random_signals(
...     "BTC-USD", 
...     n=10, 
...     seed=42,
...     sim_start="auto",  # (2)!
...     post_segment_func_nb=post_segment_func_nb,
...     leverage=10,
... )
>>> pf.plot_value()  # (3)!
```

1. Stop the simulation of the current group if its value turns negative.
2. Start the simulation at the first signal.
3. Make sure all metrics and subplots use only data up to the liquidation point, even if the portfolio
contains the full original data set (2014 → today).

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/liquidation.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/liquidation.dark.svg#only-dark){: .iimg loading=lazy }

```pycon title="Example 2: Analyze a date range of an already simulated portfolio"
>>> pf = vbt.PF.from_random_signals("BTC-USD", n=10, seed=42)

>>> pf.get_sharpe_ratio(sim_start="2023", sim_end="2024")  # (1)!
1.7846214408154346

>>> pf.get_sharpe_ratio(sim_start="2023", sim_end="2024", rec_sim_range=True)  # (2)!
1.8377982089422782

>>> pf.returns_stats(settings=dict(sim_start="2023", sim_end="2024"))  # (3)!
Start Index                  2023-01-01 00:00:00+00:00
End Index                    2023-12-31 00:00:00+00:00
Total Duration                       365 days 00:00:00
Total Return [%]                             84.715081
Benchmark Return [%]                        155.417419
Annualized Return [%]                        84.715081
Annualized Volatility [%]                     38.49976
Max Drawdown [%]                             20.057773
Max Drawdown Duration                102 days 00:00:00
Sharpe Ratio                                  1.784621
Calmar Ratio                                  4.223554
Omega Ratio                                   1.378076
Sortino Ratio                                 3.059933
Skew                                          -0.39136
Kurtosis                                     13.607937
Tail Ratio                                    1.323376
Common Sense Ratio                            1.823713
Value at Risk                                -0.028314
Alpha                                        -0.103145
Beta                                          0.770428
dtype: object
```

1. Consider only the returns within the specified date range when calculating the Sharpe ratio.
Note that returns may still be affected by data outside the date range (such as open positions).
2. Recursively apply the date range to all metrics that the Sharpe ratio depends on, such as equity,
cash, and orders, treating data outside the range as if it does not exist.
3. Make sure the date range is used consistently for all statistics.

## Expanding trade metrics

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_11_0.svg){ loading=lazy }

- [x] Regular metrics like MAE and MFE only represent the final point of each trade. But what if you want
to see how these metrics develop during the trade? You can now analyze expanding trade metrics as
DataFrames!

```pycon title="Visualize the expanding MFE using projections"
>>> data = vbt.YFData.pull("BTC-USD")
>>> pf = vbt.PF.from_random_signals(data, n=50, tp_stop=0.5)
>>> pf.trades.plot_expanding_mfe_returns().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/expanding_mfe_returns.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/expanding_mfe_returns.dark.svg#only-dark){: .iimg loading=lazy }

## Trade signals

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_8_2.svg){ loading=lazy }

- [x] New trade plotting method that separates entry and exit trades into long entries, long exits,
short entries, and short exits. It supports different styles for positions.

```pycon title="Plot trade signals of a Bollinger Bands strategy"
>>> data = vbt.YFData.pull("BTC-USD")
>>> bb = data.run("bbands")
>>> long_entries = data.hlc3.vbt.crossed_above(bb.upper) & (bb.bandwidth < 0.1)
>>> long_exits = data.hlc3.vbt.crossed_below(bb.upper) & (bb.bandwidth > 0.5)
>>> short_entries = data.hlc3.vbt.crossed_below(bb.lower) & (bb.bandwidth < 0.1)
>>> short_exits = data.hlc3.vbt.crossed_above(bb.lower) & (bb.bandwidth > 0.5)
>>> pf = vbt.PF.from_signals(
...     data, 
...     long_entries=long_entries, 
...     long_exits=long_exits, 
...     short_entries=short_entries, 
...     short_exits=short_exits
... )
>>> pf.plot_trade_signals().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/trade_signals.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/trade_signals.dark.svg#only-dark){: .iimg loading=lazy }

## Edge ratio

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_8_1.svg){ loading=lazy }

- [x] [Edge ratio](https://www.buildalpha.com/eratio/) is a unique metric for quantifying entry
profitability. Unlike most performance metrics, the edge ratio accounts for both open profits and
losses. This can help you find better trade exits.

```pycon title="Compare the edge ratio of an EMA crossover to a random strategy"
>>> data = vbt.YFData.pull("BTC-USD")
>>> fast_ema = data.run("ema", 10, hide_params=True)
>>> slow_ema = data.run("ema", 20, hide_params=True)
>>> entries = fast_ema.real_crossed_above(slow_ema)
>>> exits = fast_ema.real_crossed_below(slow_ema)
>>> pf = vbt.PF.from_signals(data, entries, exits, direction="both")
>>> rand_pf = vbt.PF.from_random_signals(data, n=pf.orders.count() // 2)  # (1)!
>>> fig = pf.trades.plot_running_edge_ratio(
...     trace_kwargs=dict(line_color="limegreen", name="Edge Ratio (S)")
... )
>>> fig = rand_pf.trades.plot_running_edge_ratio(
...     trace_kwargs=dict(line_color="mediumslateblue", name="Edge Ratio (R)"),
...     fig=fig
... )
>>> fig.show()
```

1. The random strategy should have a similar number of orders to allow comparison.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/running_edge_ratio.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/running_edge_ratio.dark.svg#only-dark){: .iimg loading=lazy }

## Trade history

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_8_1.svg){ loading=lazy }

- [x] Trade history is a human-readable DataFrame listing orders, extended with useful details about
entry trades, exit trades, and positions.

```pycon title="Get the trade history of a random portfolio with one signal"
>>> data = vbt.YFData.pull(["BTC-USD", "ETH-USD"], missing_index="drop")
>>> pf = vbt.PF.from_random_signals(
...     data, 
...     n=1,
...     run_kwargs=dict(hide_params=True),
...     tp_stop=0.5, 
...     sl_stop=0.1
... )
>>> pf.trade_history
   Order Id   Column              Signal Index            Creation Index  \
0         0  BTC-USD 2016-02-20 00:00:00+00:00 2016-02-20 00:00:00+00:00   
1         1  BTC-USD 2016-02-20 00:00:00+00:00 2016-06-12 00:00:00+00:00   
2         0  ETH-USD 2019-05-25 00:00:00+00:00 2019-05-25 00:00:00+00:00   
3         1  ETH-USD 2019-05-25 00:00:00+00:00 2019-07-15 00:00:00+00:00   

                 Fill Index  Side    Type Stop Type      Size       Price  \
0 2016-02-20 00:00:00+00:00   Buy  Market      None  0.228747  437.164001   
1 2016-06-12 00:00:00+00:00  Sell  Market        TP  0.228747  655.746002   
2 2019-05-25 00:00:00+00:00   Buy  Market      None  0.397204  251.759872   
3 2019-07-15 00:00:00+00:00  Sell  Market        SL  0.397204  226.583885   

   Fees   PnL  Return Direction  Status  Entry Trade Id  Exit Trade Id  \
0   0.0  50.0     0.5      Long  Closed               0             -1   
1   0.0  50.0     0.5      Long  Closed              -1              0   
2   0.0 -10.0    -0.1      Long  Closed               0             -1   
3   0.0 -10.0    -0.1      Long  Closed              -1              0   

   Position Id  
0            0  
1            0  
2            0  
3            0  
```

## Patterns

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_5_0.svg){ loading=lazy }

- [x] Patterns are distinctive formations created by price movements on a chart and are central to
technical analysis. There are now new dedicated functions and classes for detecting patterns of any
complexity in any type of time series data. The idea is simple: fit a pattern to align with the
scale and period of your selected data window, then compute the element-wise distance between
them to get a single similarity score. You can adjust the threshold for this score to decide above
which value a data window should be marked as "matched." Thanks to Numba, this operation can be
performed hundreds of thousands of times per second! :mag_right:

!!! example "Tutorial"
    Learn more in the [Patterns and projections](https://vectorbt.pro/pvt_6d1b3986/tutorials/patterns-and-projections) tutorial.

```pycon title="Find and plot a descending triangle pattern"
>>> data = vbt.YFData.pull("BTC-USD")
>>> data.hlc3.vbt.find_pattern(
...     pattern=[5, 1, 3, 1, 2, 1],
...     window=100,
...     max_window=700,
... ).loc["2017":"2019"].plot().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/patterns.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/patterns.dark.svg#only-dark){: .iimg loading=lazy }

## Projections

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_5_0.svg){ loading=lazy }

- [x] There are cleaner ways to analyze events and their impact on price than conventional backtesting.
Meet projections! :wave: Not only can they help you assess event performance visually and
quantitatively, but they can also project events into the future to support trading. This is done
by extracting the price range after each event, collecting all these price ranges into a multidimensional
array, and then deriving confidence intervals and other useful statistics from that array. When
combined with patterns, these tools are a quantitative analyst's dream! :stars:

!!! example "Tutorial"
    Learn more in the [Patterns and projections](https://vectorbt.pro/pvt_6d1b3986/tutorials/patterns-and-projections) tutorial.

```pycon title="Find occurrences of the price moving similarly to the last week and project them"
>>> data = vbt.YFData.pull("ETH-USD")
>>> pattern_ranges = data.hlc3.vbt.find_pattern(
...     pattern=data.close.iloc[-7:],
...     rescale_mode="rebase"
... )
>>> delta_ranges = pattern_ranges.with_delta(7)
>>> fig = data.iloc[-7:].plot(plot_volume=False)
>>> delta_ranges.plot_projections(fig=fig)
>>> fig.show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/projections.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/projections.dark.svg#only-dark){: .iimg loading=lazy }

## MAE and MFE

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_3_0.svg){ loading=lazy }

- [x] [Maximum Adverse Excursion (MAE)](https://analyzingalpha.com/maximum-adverse-excursion)
helps you see the maximum loss taken during a trade, also known as the maximum drawdown of the
position. [Maximum Favorable Excursion (MFE)](https://analyzingalpha.com/maximum-favorable-excursion)
shows the highest profit reached during a trade. Analyzing MAE and MFE statistics can help you
improve your exit strategies.

```pycon title="Analyze the MAE of a random portfolio without SL"
>>> data = vbt.YFData.pull("BTC-USD")
>>> pf = vbt.PF.from_random_signals(data, n=50)
>>> pf.trades.plot_mae_returns().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/mae_without_sl.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/mae_without_sl.dark.svg#only-dark){: .iimg loading=lazy }

```pycon title="Analyze the MAE of a random portfolio with SL"
>>> pf = vbt.PF.from_random_signals(data, n=50, sl_stop=0.1)
>>> pf.trades.plot_mae_returns().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/mae_with_sl.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/mae_with_sl.dark.svg#only-dark){: .iimg loading=lazy }

## OHLC-native classes

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_3_0.svg){ loading=lazy }

- [x] Previously, OHLC data was used for simulation, but only the close price was analyzed.
Now, most classes let you track all OHLC data for more accurate quantitative and qualitative analysis.

```pycon title="Plot trades of a random portfolio"
>>> data = vbt.YFData.pull("BTC-USD", start="2020-01", end="2020-03")
>>> pf = vbt.PF.from_random_signals(
...     open=data.open,
...     high=data.high,
...     low=data.low,
...     close=data.close,
...     n=10
... )
>>> pf.trades.plot().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/ohlc_native_classes.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/ohlc_native_classes.dark.svg#only-dark){: .iimg loading=lazy }

## Benchmark

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_4.svg){ loading=lazy }

- [x] The benchmark can now be easily set for your entire portfolio.

```pycon title="Compare Microsoft to S&P 500"
>>> data = vbt.YFData.pull(["SPY", "MSFT"], start="2010", missing_columns="drop")

>>> pf = vbt.PF.from_holding(
...     close=data.data["MSFT"]["Close"],
...     bm_close=data.data["SPY"]["Close"]
... )
>>> pf.plot_cumulative_returns().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/benchmark.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/benchmark.dark.svg#only-dark){: .iimg loading=lazy }

## And many more...

- [ ] Look forward to more killer features being added every week!

[:material-language-python: Python code](https://vectorbt.pro/pvt_6d1b3986/assets/jupytext/features/analysis.py.txt){ .md-button target="blank_" }