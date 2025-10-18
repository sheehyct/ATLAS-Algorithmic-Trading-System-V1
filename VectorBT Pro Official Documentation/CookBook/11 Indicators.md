---
title: Indicators
description: Recipes for working with indicators in VectorBT PRO
icon: material/chart-timeline-variant
---

# :material-chart-timeline-variant: Indicators

!!! question
    Learn more in the [Indicators documentation](https://vectorbt.pro/pvt_6d1b3986/documentation/indicators/).

## Listing

To list the currently supported indicators, use
[IndicatorFactory.list_indicators](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.list_indicators).
You can filter the returned indicator names by location, which can be listed with
[IndicatorFactory.list_locations](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.list_locations),
or by applying a glob or regex pattern.

```python title="List supported indicators and locations"
indicator_names = vbt.IF.list_indicators()  # (1)!
indicator_names = vbt.IF.list_indicators("vbt")  # (2)!
indicator_names = vbt.IF.list_indicators("talib")  # (3)!
indicator_names = vbt.IF.list_indicators("RSI*")  # (4)!
indicator_names = vbt.IF.list_indicators("*ma")  # (5)!
indicator_names = vbt.IF.list_indicators("[a-z]+ma$", use_regex=True)  # (6)!
indicator_names = vbt.IF.list_indicators("*ma", location="pandas_ta")  # (7)!

location_names = vbt.IF.list_locations()  # (8)!
```

1. List all indicators.
2. List all custom-implemented VBT indicators.
3. List all TA-Lib indicators.
4. List any indicators that start with "RSI", such as "RSI" and "RSIIndicator".
5. List any indicators that end with "ma", such as "MA" and "SMA".
6. Same as above but as a regular expression.
7. Same as above but only those offered by Pandas TA.
8. List all locations.

!!! note
    If you do not specify a location, indicators from all locations will be parsed, which may take some time.
    To avoid repeated calls, save the results to a variable.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To get the class of an indicator, use [IndicatorFactory.get_indicator](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.get_indicator).

```python title="How to get the indicator class"
vbt.BBANDS  # (1)!

BBANDS = vbt.IF.get_indicator("pandas_ta:BBANDS")  # (2)!
BBANDS = vbt.indicator("pandas_ta:BBANDS")  # (3)!
BBANDS = vbt.IF.from_pandas_ta("BBANDS")  # (4)!
BBANDS = vbt.pandas_ta("BBANDS")  # (5)!

RSI = vbt.indicator("RSI")  # (6)!
```

1. Custom-implemented VBT indicators can be accessed directly.
2. Get the indicator class by name as returned by `list_indicators`.
3. Same as above.
4. Same as above using the respective function.
5. Same as above.
6. Search for an indicator with the name "RSI" and return the first one found.
Custom, TA-LIB, and Pandas-TA indicators are preferred in that order.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To get familiar with an indicator class, call [phelp](https://vectorbt.pro/pvt_6d1b3986/api/utils/formatting/#vectorbtpro.utils.formatting.phelp)
on the `run` class method, which is used to run the indicator. The specification,
such as input names, is also available through various properties that can be accessed programmatically.

```python title="How to get the specification of an indicator class"
vbt.phelp(vbt.OLS.run)  # (1)!

print(vbt.OLS.input_names)  # (2)!
print(vbt.OLS.param_names)  # (3)!
print(vbt.OLS.param_defaults)  # (4)!
print(vbt.OLS.in_output_names)  # (5)!
print(vbt.OLS.output_names)  # (6)!
print(vbt.OLS.lazy_output_names)  # (7)!
```

1. Get the signature of the `run` class method along with the specification.
2. Get the input names, such as "close" in `talib:SMA`.
These are the arrays on which the indicator is computed.
3. Get the parameter names, such as "timeperiod" in `talib:SMA`.
These are the parameters being tested.
4. Get the parameter defaults.
5. Get the in-place output names, such as "stop_ts" in `vbt:STX`.
These are the arrays written in-place by the indicator.
6. Get the output names, such as "entries" and "exits" in `vbt:RANDNX`.
These are the arrays returned by the indicator.
7. Get the lazy output names, such as "bandwidth" in `vbt:BBANDS`.
These arrays can be optionally calculated after the indicator has finished computing.

## Running

To run an indicator, call the [IndicatorBase.run](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.run)
class method of its class. Pass the input arrays (any array-like objects,
such as Pandas DataFrames or NumPy arrays), parameters (which can be single values or lists for testing
multiple parameter combinations), and other arguments expected by the indicator. Running the indicator
returns __an indicator instance__ (not the actual arrays!).

```python title="How to run an indicator"
bbands = vbt.BBANDS.run(close)  # (1)!
bbands = vbt.BBANDS.run(open)  # (2)!
bbands = vbt.BBANDS.run(close, window=20)  # (3)!
bbands = vbt.BBANDS.run(close, window=vbt.Default(20))  # (4)!
bbands = vbt.BBANDS.run(close, window=20, hide_params=["window"])  # (5)!
bbands = vbt.BBANDS.run(close, window=20, hide_params=True)  # (6)!
bbands = vbt.BBANDS.run(close, window=[10, 20, 30])  # (7)!
bbands = vbt.BBANDS.run(close, window=[10, 20, 30], alpha=[2, 3, 4])  # (8)!
bbands = vbt.BBANDS.run(close, window=[10, 20, 30], alpha=[2, 3, 4], param_product=True)  # (9)!
```

1. Run the indicator on close price with default parameters.
2. Run the indicator on open price. You can pass any time series if the indicator expects only "close".
But if it expects other time series such as "open", "high", or "low", use only "close".
3. Test a window of 20. If the close price is a DataFrame, this will append a new column level called "window".
If the close price is a Series, its name will become a tuple.
4. To avoid adding a new column level, wrap with `Default`.
5. Alternatively, hide the parameter.
6. Hide all parameters. This is only useful when testing one parameter combination,
and you want the output arrays to have the same columns or names as the input arrays.
7. Test three windows. This will produce three Series or DataFrames stacked into one DataFrame along columns.
8. Test three parameter combinations: (10, 2), (20, 3), and (30, 4).
9. Test all combinations between both parameters, resulting in a total of 9 tests.

!!! warning
    Testing a wide grid of parameter combinations will produce large arrays. For example,
    testing 10000 parameter combinations on one year of daily data would create an array that
    takes 30MB of RAM. If the indicator returns three arrays, RAM consumption would be at least 120MB.
    For one year of minute data, this would result in about 40GB. To avoid excessive memory use,
    test only a subset of combinations at a time, such as by using
    [parameterization](https://vectorbt.pro/pvt_6d1b3986/cookbook/optimization#parameterization) or [chunking](https://vectorbt.pro/pvt_6d1b3986/cookbook/optimization#chunking).

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Often, you may want an indicator to skip missing values. For this, use `skipna=True`.
This argument works for any indicator, not just TA-Lib indicators, with one requirement:
the jitted loop must be disabled. When passing a two-dimensional input array, make sure to also
set `split_columns=True` to split its columns and process one column at a time.

```python title="Run an indicator on valid values only"
bbands = vbt.BBANDS.run(close_1d, skipna=True)
bbands = vbt.BBANDS.run(close_2d, split_columns=True, skipna=True)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Another approach is to remove missing values entirely.

```python title="Remove missing values in an indicator"
bbands = bbands.dropna()  # (1)!
bbands = bbands.dropna(how="all")  # (2)!
```

1. Remove any row that has at least one missing value across all outputs.
2. Remove any row that has all values missing across all outputs.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To retrieve the output arrays from an indicator instance, you can access each one as an attribute,
or use various unpacking options such as [IndicatorBase.unpack](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.unpack).

```python title="How to retrieve output arrays"
bbands = vbt.talib("BBANDS").run(close)
upperband_df = bbands.upperband  # (1)!
middleband_df = bbands.middleband
lowerband_df = bbands.lowerband
upperband_df, middleband_df, lowerband_df = bbands.unpack()  # (2)!
output_dict = bbands.to_dict()  # (3)!
output_df = bbands.to_frame()  # (4)!

sma = vbt.talib("SMA").run(close)
sma_df = sma.real  # (5)!
sma_df = sma.sma  # (6)!
sma_df = sma.output  # (7)!
sma_df = sma.unpack()
```

1. Retrieve the upper band array from the indicator instance.
2. Retrieve the output arrays in the same order as in `bbands.output_names`.
3. Retrieve a dictionary with the output arrays.
4. Retrieve a DataFrame with the output arrays stacked along columns.
5. If a TA-Lib indicator has only one output array, it is usually named "real".
6. The only output can also be accessed by the short name of the indicator.
7. The only output also has an alias "output".

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To keep outputs in NumPy format and/or skip any shape checks, use `return_raw="outputs"`.

```python title="Keep NumPy format"
upperband, middleband, lowerband = vbt.talib("BBANDS").run(close, return_raw="outputs")
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

A simpler way to run indicators is by using [Data.run](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.run),
which takes an indicator name or class, determines what input names the indicator expects,
and runs the indicator by automatically passing all the inputs found in the data instance.
This method also supports unpacking and running multiple indicators, which is very useful for
feature engineering.

```python title="How to run indicators automatically"
bbands = data.run("vbt:BBANDS")  # (1)!
bbands = data.run("vbt:BBANDS", window=20)  # (2)!
upper, middle, lower = data.run("vbt:BBANDS", unpack=True)  # (3)!

features_df = data.run(["talib:BBANDS", "talib:RSI"])  # (4)!
bbands, rsi = data.run(["talib:BBANDS", "talib:RSI"], concat=False)  # (5)!
features_df = data.run(  # (6)!
    ["talib:BBANDS", "talib:RSI"], 
    timeperiod=vbt.run_func_dict(talib_bbands=20, talib_rsi=30),
    hide_params=True
)
features_df = data.run(  # (7)!
    ["talib:BBANDS", "vbt:RSI"], 
    talib_bbands=vbt.run_arg_dict(timeperiod=20),
    vbt_rsi=vbt.run_arg_dict(window=30),
    hide_params=True
)
features_df = data.run("talib_all")  # (8)!
```

1. Run `vbt.BBANDS` with the "close" input automatically substituted by `data.close`.
2. Any arguments will be passed to the indicator's `run` class method.
3. The output arrays can be unpacked directly. The `unpack` argument also accepts the options
"dict" and "frame".
4. Run multiple indicators. By default, they will be concatenated into a DataFrame along columns.
The function and output names will appear in the column levels "run_func" and "output" respectively.
5. Do not concatenate indicators but return them as a list.
6. Pass different values under the same parameter name using `run_func_dict`.
7. Pass different keyword arguments to each indicator using `run_arg_dict`.
8. Run all TA-Lib indicators.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To quickly run and plot a TA-Lib indicator on a single parameter combination without using the
indicator factory, use [talib_func](https://vectorbt.pro/pvt_6d1b3986/api/indicators/talib_/#vectorbtpro.indicators.talib.talib_func)
and [talib_plot_func](https://vectorbt.pro/pvt_6d1b3986/api/indicators/talib_/#vectorbtpro.indicators.talib.talib_plot_func)
respectively. Unlike the official TA-Lib implementation, these handle DataFrames,
NaNs, broadcasting, and timeframes properly. The indicator factory's TA-Lib version is based
on these functions.

```python title="Quickly run and plot a TA-Lib indicator"
run_bbands = vbt.talib_func("BBANDS")
upperband, middleband, lowerband = run_bbands(close, timeperiod=2)
upperband, middleband, lowerband = data.run("talib_func:BBANDS", timeperiod=2)  # (1)!

plot_bbands = vbt.talib_plot_func("BBANDS")
fig = plot_bbands(upperband, middleband, lowerband)
```

1. Same as above.

### Parallelization

Parameter combinations are processed using [execute](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute)
so it is straightforward to parallelize their execution.

```python title="Various parallelization configurations"
any_indicator.run(...)  # (1)!

# ______________________________________________________________

numba_indicator.run(  # (2)!
    ...,
    jitted_loop=True,  # (3)!
    jitted_warmup=True,    # (4)!
    execute_kwargs=dict(n_chunks="auto", engine="threadpool")
)

# ______________________________________________________________

python_indicator.run(  # (5)!
    ...,
    execute_kwargs=dict(n_chunks="auto", distribute="chunks", engine="pathos")
)
```

1. By default, the method processes parameter combinations serially (not in parallel).
2. If the indicator is compiled with Numba and `nogil` is enabled, divide parameter combinations
into an optimal number of chunks, and execute all chunks in parallel with multithreading (one chunk per thread).
3. Wrap the loop with Numba that iterates over parameter combinations (required).
4. Dry-run one parameter combination to compile the indicator ahead of distribution (optional).
5. If the indicator is __not__ compiled with Numba, divide parameter combinations into an optimal
number of chunks and execute all chunks in parallel with multiprocessing (one chunk per process),
while processing all parameter combinations within each chunk serially.

## Registration

Custom indicators can be registered with the indicator factory to appear in the list of all indicators.
This allows you to refer to the indicator by name when running a data instance.
Upon registration, you can assign the indicator to a custom location (the default is "custom"),
which serves as a tag or group. This lets you create arbitrary indicator groups. One indicator can be
assigned to multiple locations. Custom indicators take priority over built-in indicators.

```python
vbt.IF.register_custom_indicator(sma_indicator)  # (1)!
vbt.IF.register_custom_indicator(sma_indicator, "SMA")  # (2)!
vbt.IF.register_custom_indicator(sma_indicator, "SMA", location="rolling")  # (3)!
vbt.IF.register_custom_indicator(sma_indicator, "rolling:SMA")
vbt.IF.register_custom_indicator("talib:sma", location="rolling")  # (4)!

vbt.IF.deregister_custom_indicator("SMA", location="rolling")  # (5)!
vbt.IF.deregister_custom_indicator("rolling:SMA")
vbt.IF.deregister_custom_indicator("SMA")  # (6)!
vbt.IF.deregister_custom_indicator(location="rolling")  # (7)!
vbt.IF.deregister_custom_indicator()  # (8)!
```

1. Register an indicator class. The class name will be used as the indicator name.
2. Register an indicator class with a specific name.
3. Register an indicator class with a specific name and under a specific location.
4. Assign a built-in indicator class to a custom location (for example, for tagging).
5. Deregister all indicators with a specific name under a specific location.
6. Deregister all indicators with a specific name under all locations.
7. Deregister all indicators under a specific location.
8. Deregister all indicators under all locations.