---
title: Cross-validation
description: Recipes for cross-validation in VectorBT PRO
icon: material/check-all
---

# :material-check-all: Cross-validation

## Splitting

!!! question
    Learn more in the [Cross-validation tutorial](https://vectorbt.pro/pvt_6d1b3986/tutorials/cross-validation/).

To select a fixed number of windows and optimize the window length so that they collectively cover the
maximum area of the index while keeping the train or test set non-overlapping, use
[Splitter.from_n_rolling](https://vectorbt.pro/pvt_6d1b3986/api/generic/splitting/base/#vectorbtpro.generic.splitting.base.Splitter.from_n_rolling)
with `length="optimize"`. Under the hood, SciPy is used to minimize any empty space.

```python title="Pick longest 20 windows for WFA such that test ranges do not overlap"
splitter = vbt.Splitter.from_n_rolling(
    data.index,
    n=20,
    length="optimize",
    split=0.7,  # (1)!
    optimize_anchor_set=1,  # (2)!
    set_labels=["train", "test"]
)
```

1. 70% for training, 30% for testing.
2. Make the test set non-overlapping. Change to 0 for the train set.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

When using [Splitter.from_rolling](https://vectorbt.pro/pvt_6d1b3986/api/generic/splitting/base/#vectorbtpro.generic.splitting.base.Splitter.from_rolling)
and the last window does not fit, it will be removed, causing a gap on the right-hand side.
To remove the oldest window instead, use `backwards="sorted"`.

```python title="Roll a window that fills more recent data and with no gaps between test sets"
length = 1000
ratio = 0.95
train_length = round(length * ratio)
test_length = length - train_length

splitter = vbt.Splitter.from_rolling(
    data.index,
    length=length,
    split=train_length,
    offset_anchor_set=None,
    offset=-test_length,
    backwards="sorted"
)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To create a gap between the train set and the test set, use
[RelRange](https://vectorbt.pro/pvt_6d1b3986/api/generic/splitting/base/#vectorbtpro.generic.splitting.base.RelRange) with `is_gap=True`.

```python title="Roll an expanding window with a variable train set, a gap of 10 rows, and a test set of 20 rows"
splitter = vbt.Splitter.from_expanding(
    data.index,
    min_length=130,
    offset=10,  # (1)!
    split=(1.0, vbt.RelRange(length=10, is_gap=True), 20),
    split_range_kwargs=dict(backwards=True)  # (2)!
)
```

1. Shift each split by the same number of rows as in the gap.
2. Split each range by first calculating the test set and then the train set.
Otherwise, `1.0` (100%) will be calculated first and will take up the entire split.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To roll a time-periodic window, use [Splitter.from_ranges](https://vectorbt.pro/pvt_6d1b3986/api/generic/splitting/base/#vectorbtpro.generic.splitting.base.Splitter.from_ranges)
with the `every` and `lookback_period` arguments as date offsets.

```python title="Reserve 3 years for training and 1 year for testing"
splitter = vbt.Splitter.from_ranges(
    data.index,
    every="Y",
    lookback_period="4Y",
    split=(
        vbt.RepEval("index.year != index.year[-1]"),  # (1)!
        vbt.RepEval("index.year == index.year[-1]")  # (2)!
    )
)
```

1. The training set should include all years in the split except for the last year.
2. The test set should include only the last year in the split.

### Taking

To split an object along the index (time) axis, first create a
[Splitter](https://vectorbt.pro/pvt_6d1b3986/api/generic/splitting/base/#vectorbtpro.generic.splitting.base.Splitter)
instance and then "take" chunks from that object.

```python title="How to split an object in two lines"
splitter = vbt.Splitter.from_n_rolling(data.index, n=10)
data_chunks = splitter.take(data)  # (1)!

# ______________________________________________________________

splitter = vbt.Splitter.from_ranges(df.index, every="W")
new_df = splitter.take(df, into="reset_stacked")  # (2)!
```

1. VBT object.
2. Regular array.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Most VBT objects also have a `split` method that can combine both operations into a single step.
This method will automatically determine the correct splitting operation based on the supplied arguments.

```python title="How to split an object in one line"
data_chunks = data.split(n=10)  # (1)!

# ______________________________________________________________

new_df = df.vbt.split(every="W")  # (2)!
```

1. VBT object. The method `from_n_rolling` is selected based on `n=10`.
2. Regular array. The method `from_ranges` is selected based on `every="W"`.
The option `into="reset_stacked"` is enabled automatically.

## Testing

To cross-validate a function that takes only one parameter combination at a time across a grid of parameter
combinations, use [`@vbt.cv_split`](https://vectorbt.pro/pvt_6d1b3986/api/generic/splitting/decorators/#vectorbtpro.generic.splitting.decorators.cv_split).
This decorator combines [`@vbt.parameterized`](https://vectorbt.pro/pvt_6d1b3986/api/utils/params/#vectorbtpro.utils.params.parameterized)
(which applies a function to each combination of parameters from a grid and merges the results),
and [`@vbt.split`](https://vectorbt.pro/pvt_6d1b3986/api/generic/splitting/decorators/#vectorbtpro.generic.splitting.decorators.split)
(which applies a function to each split and set combination).

```python title="Cross-validate a function to maximize the Sharpe ratio"
def selection(grid_results):  # (1)!
    return vbt.LabelSel([grid_results.idxmax()])  # (2)!
    
@vbt.cv_split(
    splitter="from_n_rolling",  # (3)!
    splitter_kwargs=dict(n=10, split=0.5, set_labels=["train", "test"]),  # (4)!
    takeable_args=["data"],  # (5)!
    execute_kwargs=dict(),  # (6)!
    parameterized_kwargs=dict(merge_func="concat"),  # (7)!
    merge_func="concat",  # (8)!
    selection=vbt.RepFunc(selection),  # (9)!
    return_grid=False  # (10)!
)
def my_pipeline(data, param1_value, param2_value):  # (11)!
    ...
    return pf.sharpe_ratio

cv_sharpe_ratios = my_pipeline(  # (12)!
    data,
    vbt.Param(param1_values),
    vbt.Param(param2_values)
)

# ______________________________________________________________

@vbt.cv_split(..., takeable_args=None)  # (13)!
def my_pipeline(range_, data, param1_value, param2_value):
    data_range = data.iloc[range_]
    ...
    return pf.sharpe_ratio

cv_sharpe_ratios = my_pipeline(
    vbt.Rep("range_"),
    data,
    vbt.Param([1, 2, 3]),
    vbt.Param([1, 2, 3]),
    _index=data.index  # (14)!
)
```

1. Function that returns the index of the best parameter combination.
2. Find the parameter combination with the highest Sharpe ratio. Wrap with `LabelSel` to let
vectorbtpro know that the returned value is a label, not a position, in case it is an integer.
Also, wrap the value with a list to display the parameter combination in the final index.
3. Name of the splitting method, such as [Splitter.from_n_rolling](https://vectorbt.pro/pvt_6d1b3986/api/generic/splitting/base/#vectorbtpro.generic.splitting.base.Splitter.from_n_rolling).
4. Keyword arguments passed to the splitting method.
5. Names of the arrays that should be split. You can also pass `vbt.Takeable(data)` directly to the function instead.
6. Keyword arguments passed to [execute](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute)
to control the execution of split and set combinations.
7. Keyword arguments passed to `@vbt.parameterized`. Here, we want to concatenate
the results of all parameter combinations into a single Pandas Series.
8. Function used to merge all split and set combinations. Here, we want to concatenate
all of the Pandas Series into a single Pandas Series.
9. Either a specific index or a template used to select the best parameter combination.
10. Whether to return the full grid of parameter combinations, not just the best ones.
11. Similar to `@vbt.parameterized`, VBT will provide only one parameter combination at a time
as single values. Any takeable argument (here, `data`) will include only values that correspond to the
current split and set combination.
12. The returned Pandas Series will contain cross-validation results by split and set combination.
13. Same as above, but select the date range manually within the function.
14. Any argument meant to be passed to the decorator can also be passed directly
to the function by prepending the underscore.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To skip a parameter combination, return [NoResult](https://vectorbt.pro/pvt_6d1b3986/api/utils/params/#vectorbtpro.utils.params.NoResult).
This helps exclude parameter combinations that raise an error.
`NoResult` can also be returned by the selection function to skip an entire split and set combination.
Once excluded, the combination will not appear in the final index.

```python title="Skip split and set combinations where there are no satisfactory parameters"
# (1)!

def selection(grid_results):
    sharpe_ratio = grid_results.xs("Sharpe Ratio", level=-1).astype(float)
    return vbt.LabelSel([sharpe_ratio.idxmax()])

@vbt.cv_split(...)
def my_pipeline(...):
    ...
    stats_sr = pf.stats(agg_func=None)
    if stats_sr["Min Value"] > 0 and stats_sr["Total Trades"] >= 20:  # (2)!
        return stats_sr
    return vbt.NoResult

# ______________________________________________________________

# (3)!

def selection(grid_results):
    sharpe_ratio = grid_results.xs("Sharpe Ratio", level=-1).astype(float)
    min_value = grid_results.xs("Min Value", level=-1).astype(float)
    total_trades = grid_results.xs("Total Trades", level=-1).astype(int)
    sharpe_ratio = sharpe_ratio[(min_value > 0) & (total_trades >= 20)]
    if len(sharpe_ratio) == 0:
        return vbt.NoResult
    return vbt.LabelSel([sharpe_ratio.idxmax()])
    
@vbt.cv_split(...)
def my_pipeline(...):
    ...
    return pf.stats(agg_func=None)
```

1. Filter parameter combinations on the fly, then select the best one from those remaining (if any).
2. Keep a parameter combination only if the minimum portfolio value is greater than 0
(that is, the position was not liquidated) and the number of trades is 20 or higher.
3. Same as above, but return all parameter combinations and filter them in the selection function.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To warm up one or more indicators, instruct VBT to pass a date range instead of selecting it from
the data, and prepend a buffer to this date range. Then, manually select this extended date range from the data
and run your indicators on that date range. Finally, remove the buffer from the indicator(s).

```python title="Warm up a SMA crossover"
@vbt.cv_split(..., index_from="data")
def buffered_sma_pipeline(data, range_, fast_period, slow_period, ...):
    buffer_len = max(fast_period, slow_period)  # (1)!
    buffered_range = slice(range_.start - buffer_len, range_.stop)  # (2)!
    data_buffered = data.iloc[buffered_range]  # (3)!
    
    fast_sma_buffered = data_buffered.run("sma", fast_period, hide_params=True)
    slow_sma_buffered = data_buffered.run("sma", slow_period, hide_params=True)
    entries_buffered = fast_sma_buffered.real_crossed_above(slow_sma_buffered)
    exits_buffered = fast_sma_buffered.real_crossed_below(slow_sma_buffered)
    
    data = data_buffered.iloc[buffer_len:]  # (4)!
    entries = entries_buffered.iloc[buffer_len:]
    exits = exits_buffered.iloc[buffer_len:]
    ...

buffered_sma_pipeline(
    data,  # (5)!
    vbt.Rep("range_"),  # (6)!
    vbt.Param(fast_periods, condition="x < slow_period"),
    vbt.Param(slow_periods),
    ...
)
```

1. Determine the length of the buffer.
2. Extend the date range using the buffer.
3. Select the data corresponding to the extended date range.
4. After running all indicators, remove the buffer.
5. Pass the data as it is (without selection).
6. Instruct VBT to pass the date range as a slice.