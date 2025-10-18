---
title: Indicators
description: Indicator features of VectorBT PRO
icon: material/chart-timeline-variant
---

# :material-chart-timeline-variant: Indicators

## Hurst exponent

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_6_19.svg){ loading=lazy }

- [x] Estimating the Hurst exponent provides insight into whether your data is a pure white-noise random
process or exhibits underlying trends. VBT offers five (!) different implementations.

```pycon title="Plot rolling Hurst exponent by method"
>>> data = vbt.YFData.pull("BTC-USD", start="12 months ago")
>>> hurst = vbt.HURST.run(data.close, method=["standard", "logrs", "rs", "dma", "dsod"])
>>> fig = vbt.make_subplots(specs=[[dict(secondary_y=True)]])
>>> data.plot(plot_volume=False, ohlc_trace_kwargs=dict(opacity=0.3), fig=fig)
>>> fig = hurst.hurst.vbt.plot(fig=fig, add_trace_kwargs=dict(secondary_y=True))
>>> fig = fig.select_range(start=hurst.param_defaults["window"])
>>> fig.show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/hurst.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/hurst.dark.svg#only-dark){: .iimg loading=lazy }

## Smart Money Concepts

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_6_19.svg){ loading=lazy }

- [x] VBT integrates most of the indicators from the
[Smart Money Concepts (SMC)](https://github.com/joshyattridge/smart-money-concepts) library.

```pycon title="Plot previous high and low"
>>> data = vbt.YFData.pull("BTC-USD", start="6 months ago")
>>> phl = vbt.smc("previous_high_low").run(  # (1)!
...     data.open,
...     data.high,
...     data.low,
...     data.close,
...     data.volume,
...     time_frame=vbt.Default("7D")
... )
>>> fig = data.plot()
>>> phl.previous_high.rename("previous_high").vbt.plot(fig=fig)
>>> phl.previous_low.rename("previous_low").vbt.plot(fig=fig)
>>> (phl.broken_high == 1).rename("broken_high").vbt.signals.plot_as_markers(
...     y=phl.previous_high, 
...     trace_kwargs=dict(marker=dict(color="limegreen")),
...     fig=fig
... )
>>> (phl.broken_low == 1).rename("broken_low").vbt.signals.plot_as_markers(
...     y=phl.previous_low, 
...     trace_kwargs=dict(marker=dict(color="orangered")),
...     fig=fig
... )
>>> fig.show()
```

1. Each SMC indicator requires OHLCV.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/smc.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/smc.dark.svg#only-dark){: .iimg loading=lazy }

## Signal unraveling

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_2_22.svg){ loading=lazy }

- [x] To backtest each signal individually, you can now "unravel" each signal, or each pair of entry and exit
signals, into its own column. This creates a wide, two-dimensional mask that, when backtested, returns
performance metrics for each signal rather than for the entire column.

```pycon title="For each signal, create a separate position with own stop orders"
>>> data = vbt.YFData.pull("BTC-USD")
>>> fast_sma = data.run("talib_func:sma", timeperiod=20)  # (1)!
>>> slow_sma = data.run("talib_func:sma", timeperiod=50)
>>> entries = fast_sma.vbt.crossed_above(slow_sma)
>>> exits = fast_sma.vbt.crossed_below(slow_sma)
>>> entries, exits = entries.vbt.signals.unravel_between(exits, relation="anychain")  # (2)!
>>> pf = vbt.PF.from_signals(
...     data, 
...     long_entries=entries, 
...     short_entries=exits, 
...     size=100,  # (3)!
...     size_type="value",
...     init_cash="auto",  # (4)!
...     tp_stop=0.2, 
...     sl_stop=0.1, 
...     group_by=vbt.ExceptLevel("signal"),  # (5)!
...     cash_sharing=True
... )
>>> pf.positions.returns.to_pd(ignore_index=True).vbt.barplot(
...     trace_kwargs=dict(marker=dict(colorscale="Spectral"))
... ).show()  # (6)!
```

1. Run a TA-Lib function faster without building an indicator: `"talib_func:sma"` vs `"talib:sma"`.
2. Place each pair of entry->exit and exit->entry signals in a separate column.
3. Order $100 worth of the asset.
4. Simulate with infinite cash.
5. Combine all columns (positions) under the same asset into a single portfolio.
6. Show position returns by signal index.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/signal_unraveling.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/signal_unraveling.dark.svg#only-dark){: .iimg loading=lazy }

## Lightweight TA-Lib

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_14_0.svg){ loading=lazy }

- [x] TA-Lib functions wrapped with the indicator factory are very powerful because, unlike the official
TA-Lib implementation, they can broadcast, handle DataFrames, skip missing values, and even resample to a
different timeframe. Although TA-Lib functions are very fast, wrapping them with the indicator factory
adds some overhead. To keep both the speed of TA-Lib and the power of VBT, the added features have
been separated into a lightweight function that you can call just like a regular TA-Lib function.

```pycon title="Run and plot an RSI resampled to the monthly timeframe"
>>> data = vbt.YFData.pull("BTC-USD")
>>> run_rsi = vbt.talib_func("rsi")
>>> rsi = run_rsi(data.close, timeperiod=12, timeframe="M")  # (1)!
>>> rsi
Date
2014-09-17 00:00:00+00:00          NaN
2014-09-18 00:00:00+00:00          NaN
2014-09-19 00:00:00+00:00          NaN
2014-09-20 00:00:00+00:00          NaN
2014-09-21 00:00:00+00:00          NaN
                                   ...
2024-01-18 00:00:00+00:00    64.210811
2024-01-19 00:00:00+00:00    64.210811
2024-01-20 00:00:00+00:00    64.210811
2024-01-21 00:00:00+00:00    64.210811
2024-01-22 00:00:00+00:00    64.210811
Freq: D, Name: Close, Length: 3415, dtype: float64

>>> plot_rsi = vbt.talib_plot_func("rsi")
>>> plot_rsi(rsi).show()
```

1. Parameters are applied to the target timeframe.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/native_talib.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/native_talib.dark.svg#only-dark){: .iimg loading=lazy }

## Indicator search

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_11_1.svg){ loading=lazy }

- [x] VBT implements or integrates more than 500 indicators, making it hard to keep track
of them all. To make indicators easier to find, several new methods are available for globally searching
for indicators.

```pycon title="List all moving average indicators"
>>> vbt.IF.list_indicators("*ma")
[
    'vbt:MA',
    'talib:DEMA',
    'talib:EMA',
    'talib:KAMA',
    'talib:MA',
    ...
    'technical:ZEMA',
    'technical:ZLEMA',
    'technical:ZLHMA',
    'technical:ZLMA'
]

>>> vbt.indicator("technical:ZLMA")  # (1)!
vectorbtpro.indicators.factory.technical.ZLMA
```

1. Same as `vbt.IF.get_indicator`.

## Indicators for ML

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_8_2.svg){ loading=lazy }

- [x] Want to feed indicators as features to a machine-learning model? There is no need to run 
them individually: you can tell VBT to run all indicators from an indicator package on 
the given data instance. The data instance will recognize the input names of each indicator and supply 
the required data. You can also easily change the defaults for each indicator.

```pycon title="Run all talib indicators on entire BTC-USD history"
>>> data = vbt.YFData.pull("BTC-USD")
>>> features = data.run("talib", mavp=vbt.run_arg_dict(periods=14))
>>> features.shape
(3046, 175)
```

## Signal detection

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_8_0.svg){ loading=lazy }

- [x] VBT includes an indicator that uses a robust peak detection algorithm based on z-scores.
This indicator can be used to identify outbreaks and outliers in any time series data.

```pycon title="Detect sudden changes in the bandwidth of a Bollinger Bands indicator"
>>> data = vbt.YFData.pull("BTC-USD")
>>> fig = vbt.make_subplots(rows=2, cols=1, shared_xaxes=True)
>>> bbands = data.run("bbands")
>>> bbands.loc["2022"].plot(add_trace_kwargs=dict(row=1, col=1), fig=fig)
>>> sigdet = vbt.SIGDET.run(bbands.bandwidth, factor=5)
>>> sigdet.loc["2022"].plot(add_trace_kwargs=dict(row=2, col=1), fig=fig)
>>> fig.show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/signal_detection.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/signal_detection.dark.svg#only-dark){: .iimg loading=lazy }

## Pivot detection

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_7_1.svg){ loading=lazy }

- [x] The pivot detection indicator is a tool for finding when the price trend is reversing. By identifying
support and resistance areas, it helps spot significant price changes while filtering out short-term
fluctuations and reducing noise. It works simply: a peak is registered when the price jumps above
one threshold, and a valley is recorded when the price falls below another. Another advantage is
that, unlike the [regular Zig Zag indicator](https://www.investopedia.com/ask/answers/030415/what-zig-zag-indicator-formula-and-how-it-calculated.asp),
which tends to look ahead, our indicator only returns confirmed pivot points and is safe to use in backtesting.

```pycon title="Plot the last pivot value"
>>> data = vbt.YFData.pull("BTC-USD", start="2020", end="2023")
>>> fig = data.plot(plot_volume=False)
>>> pivot_info = data.run("pivotinfo", up_th=1.0, down_th=0.5)
>>> pivot_info.plot(fig=fig, conf_value_trace_kwargs=dict(visible=False))
>>> fig.show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/pivot_detection.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/pivot_detection.dark.svg#only-dark){: .iimg loading=lazy }

## Technical indicators

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_7_0.svg){ loading=lazy }

- [x] VBT integrates most of the indicators and consensus classes from freqtrade's
[technical](https://github.com/freqtrade/technical) library.

```pycon title="Compute and plot the summary consensus with a one-liner"
>>> vbt.YFData.pull("BTC-USD").run("sumcon", smooth=100).plot().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/sumcon.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/sumcon.dark.svg#only-dark){: .iimg loading=lazy }

## Renko chart

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_7_0.svg){ loading=lazy }

- [x] Unlike regular charts, a [Renko chart](https://www.investopedia.com/terms/r/renkochart.asp)
is built using price movements. Each "brick" appears when the price changes by a specified amount.
Because the output has irregular time intervals, only one column can be processed at once. As with
everything, VBT's implementation can translate a huge number of data points very fast thanks to Numba.

```pycon title="Resample closing price into a Renko format"
>>> data = vbt.YFData.pull("BTC-USD", start="2021", end="2022")
>>> renko_ohlc = data.close.vbt.to_renko_ohlc(1000, reset_index=True)  # (1)!
>>> renko_ohlc.vbt.ohlcv.plot().show()
```

1. Bitcoin is very volatile, so the brick size is set to 1000.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/renko_chart.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/renko_chart.dark.svg#only-dark){: .iimg loading=lazy }

## Rolling OLS

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_3_0.svg){ loading=lazy }

- [x] Rolling regressions are models for analyzing changing relationships among variables over time.
In VBT, this is implemented as an indicator that takes two time series and returns the slope, intercept,
prediction, error, and the z-score of the error at each time step. This indicator can be used for
cointegration tests, such as determining optimal rebalancing timings in pairs trading, and is also
(literally) 1000x faster than the statsmodels equivalent
[RollingOLS](https://www.statsmodels.org/dev/generated/statsmodels.regression.rolling.RollingOLS.html) :fire:

```pycon title="Determine the spread between BTC and ETH"
>>> data = vbt.YFData.pull(
...     ["BTC-USD", "ETH-USD"], 
...     start="2022", 
...     end="2023",
...     missing_index="drop"
... )
>>> ols = vbt.OLS.run(
...     data.get("Close", "BTC-USD"), 
...     data.get("Close", "ETH-USD")
... )
>>> ols.plot_zscore().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/rolling_ols.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/rolling_ols.dark.svg#only-dark){: .iimg loading=lazy }

## TA-Lib time frames

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_2_0.svg){ loading=lazy }

- [x] Comparing indicators on different time frames involves many nuances. Now, all TA-Lib indicators
support a parameter that resamples the input arrays to a target time frame, calculates the indicator, and
then resamples the output arrays back to the original time frame. This makes parameterized MTF analysis
easier than ever!

!!! example "Tutorial"
    Learn more in the [MTF analysis](https://vectorbt.pro/pvt_6d1b3986/tutorials/mtf-analysis) tutorial.

```pycon title="Run SMA on multiple time frames and display the whole thing as a heatmap"
>>> h1_data = vbt.BinanceData.pull(
...     "BTCUSDT", 
...     start="3 months ago UTC", 
...     timeframe="1h"
... )
>>> mtf_sma = vbt.talib("SMA").run(
...     h1_data.close, 
...     timeperiod=14, 
...     timeframe=["1d", "4h", "1h"], 
...     skipna=True
... )
>>> mtf_sma.real.vbt.ts_heatmap().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/talib_time_frames.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/talib_time_frames.dark.svg#only-dark){: .iimg loading=lazy }

## 1D-native indicators

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_10.svg){ loading=lazy }

- [x] Previously, custom indicators could only be created by accepting two-dimensional input arrays, which
forced users to adapt all functions accordingly. Now, the indicator factory can split each input array
along columns and pass one column at a time, making it much easier to design indicators that are meant
to be run natively on one-dimensional data (such as TA-Lib!).

```pycon title="Create a TA-Lib powered STOCHRSI indicator"
>>> import talib

>>> params = dict(
...     rsi_period=14, 
...     fastk_period=5, 
...     slowk_period=3, 
...     slowk_matype=0, 
...     slowd_period=3, 
...     slowd_matype=0
... )

>>> def stochrsi_1d(close, *args):
...     rsi = talib.RSI(close, args[0])
...     k, d = talib.STOCH(rsi, rsi, rsi, *args[1:])
...     return rsi, k, d
    
>>> STOCHRSI = vbt.IF(
...     input_names=["close"], 
...     param_names=list(params.keys()),
...     output_names=["rsi", "k", "d"]
... ).with_apply_func(stochrsi_1d, takes_1d=True, **params)

>>> data = vbt.YFData.pull("BTC-USD", start="2022-01", end="2022-06")
>>> stochrsi = STOCHRSI.run(data.close)
>>> fig = stochrsi.k.rename("%K").vbt.plot()
>>> stochrsi.d.rename("%D").vbt.plot(fig=fig)
>>> fig.show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/stochrsi.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/stochrsi.dark.svg#only-dark){: .iimg loading=lazy }

## Parallelizable indicators

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_10.svg){ loading=lazy }

- [x] Processing parameter combinations with the indicator factory can be distributed across multiple threads,
processes, or even in the cloud. This is a huge help when working with slow indicators :snail:

```pycon title="Benchmark a serial and multithreaded rolling min-max indicator"
>>> @njit
... def minmax_nb(close, window):
...     return (
...         vbt.nb.rolling_min_nb(close, window),
...         vbt.nb.rolling_max_nb(close, window)
...     )

>>> MINMAX = vbt.IF(
...     class_name="MINMAX",
...     input_names=["close"], 
...     param_names=["window"], 
...     output_names=["min", "max"]
... ).with_apply_func(minmax_nb, window=14)

>>> data = vbt.YFData.pull("BTC-USD")
```

```pycon
>>> %%timeit
>>> minmax = MINMAX.run(
...     data.close, 
...     np.arange(2, 200),
...     jitted_loop=True
... )
420 ms ± 2.05 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

```pycon
>>> %%timeit
>>> minmax = MINMAX.run(
...     data.close, 
...     np.arange(2, 200),
...     jitted_loop=True,
...     jitted_warmup=True,  # (1)!
...     execute_kwargs=dict(engine="threadpool", n_chunks="auto")  # (2)!
... )
120 ms ± 355 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
```

1. Run one parameter combination to compile the indicator before running others
in a multithreaded fashion.
2. One Numba loop per thread, with the same number of threads as there are cores.

## TA-Lib plotting

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_9.svg){ loading=lazy }

- [x] Every TA-Lib indicator is fully capable of plotting itself, based entirely on output flags!

```pycon
>>> data = vbt.YFData.pull("BTC-USD", start="2020", end="2021")

>>> vbt.talib("MACD").run(data.close).plot().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/talib.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/talib.dark.svg#only-dark){: .iimg loading=lazy }

## Indicator expressions

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_8.svg){ loading=lazy }

- [x] Indicators can now be created from expressions. An indicator expression is a regular string representing
Python code enhanced with various extensions. The indicator factory automatically derives all required
information, such as inputs, parameters, outputs, NumPy, VBT, and TA-Lib functions, and even
complex indicators, thanks to a unique format and built-in matching mechanism. Designing indicators
has never been easier!

```pycon title="Build a MACD indicator from an expression"
>>> data = vbt.YFData.pull("BTC-USD", start="2020", end="2021")

>>> expr = """
... MACD:
... fast_ema = @talib_ema(close, @p_fast_w)
... slow_ema = @talib_ema(close, @p_slow_w)
... macd = fast_ema - slow_ema
... signal = @talib_ema(macd, @p_signal_w)
... macd, signal
... """
>>> MACD = vbt.IF.from_expr(expr, fast_w=12, slow_w=26, signal_w=9)  # (1)!
>>> macd = MACD.run(data.close)
>>> fig = macd.macd.rename("MACD").vbt.plot()
>>> macd.signal.rename("Signal").vbt.plot(fig=fig)
>>> fig.show()
```

1. No need to manually set `input_names`, `param_names`, or other information.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/indicator_expressions.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/indicator_expressions.dark.svg#only-dark){: .iimg loading=lazy }

## WorldQuant Alphas

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_8.svg){ loading=lazy }

- [x] Each of [WorldQuant's 101 Formulaic Alphas](https://arxiv.org/pdf/1601.00991.pdf) is now available
as an indicator :eyes:

```pycon title="Run the first alpha"
>>> data = vbt.YFData.pull(["BTC-USD", "ETH-USD", "XRP-USD"], missing_index="drop")

>>> vbt.wqa101(1).run(data.close).out
symbol                      BTC-USD   ETH-USD   XRP-USD
Date                                                   
2017-11-09 00:00:00+00:00  0.166667  0.166667  0.166667
2017-11-10 00:00:00+00:00  0.166667  0.166667  0.166667
2017-11-11 00:00:00+00:00  0.166667  0.166667  0.166667
2017-11-12 00:00:00+00:00  0.166667  0.166667  0.166667
2017-11-13 00:00:00+00:00  0.166667  0.166667  0.166667
...                             ...       ...       ...
2023-01-31 00:00:00+00:00  0.166667  0.166667  0.166667
2023-02-01 00:00:00+00:00  0.000000  0.000000  0.500000
2023-02-02 00:00:00+00:00  0.000000  0.000000  0.500000
2023-02-03 00:00:00+00:00  0.000000  0.500000  0.000000
2023-02-04 00:00:00+00:00 -0.166667  0.333333  0.333333

[1914 rows x 3 columns]
```

## Robust crossovers

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] Crossovers are now robust to NaNs.

```pycon title="Remove a bunch of data points and plot the crossovers"
>>> data = vbt.YFData.pull("BTC-USD", start="2022-01", end="2022-03")
>>> fast_sma = vbt.talib("SMA").run(data.close, vbt.Default(5)).real
>>> slow_sma = vbt.talib("SMA").run(data.close, vbt.Default(10)).real
>>> fast_sma.iloc[np.random.choice(np.arange(len(fast_sma)), 5)] = np.nan
>>> slow_sma.iloc[np.random.choice(np.arange(len(slow_sma)), 5)] = np.nan
>>> crossed_above = fast_sma.vbt.crossed_above(slow_sma, dropna=True)
>>> crossed_below = fast_sma.vbt.crossed_below(slow_sma, dropna=True)

>>> fig = fast_sma.rename("Fast SMA").vbt.lineplot()
>>> slow_sma.rename("Slow SMA").vbt.lineplot(fig=fig)
>>> crossed_above.vbt.signals.plot_as_entries(fast_sma, fig=fig)
>>> crossed_below.vbt.signals.plot_as_exits(fast_sma, fig=fig)
>>> fig.show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/resilient_crossovers.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/resilient_crossovers.dark.svg#only-dark){: .iimg loading=lazy }

## And many more...

- [ ] Look forward to more killer features being added every week!

[:material-language-python: Python code](https://vectorbt.pro/pvt_6d1b3986/assets/jupytext/features/indicators.py.txt){ .md-button target="blank_" }