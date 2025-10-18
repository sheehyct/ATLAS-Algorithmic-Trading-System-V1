---
title: Optimization
description: Recipes for optimizing strategies and pipelines in VectorBT PRO
icon: material/magnify-expand
---

# :material-magnify-expand: Optimization

Optimization involves running a function with various configurations to improve the performance of a
strategy or to enhance the CPU or RAM efficiency of a pipeline.

!!! question
    Learn more in [Pairs trading tutorial](https://vectorbt.pro/pvt_6d1b3986/tutorials/pairs-trading/).

## Parameterization

The simplest approach is to test one parameter combination at a time. This method uses minimal RAM,
but it may take longer to run if the function is not written in pure Numba and has a fixed overhead
(such as converting from Pandas to NumPy and back), which increases the total execution time for each
run. To use this approach, create a pipeline function that accepts individual parameter values and
decorate it with [`@vbt.parameterized`](https://vectorbt.pro/pvt_6d1b3986/api/utils/params/#vectorbtpro.utils.params.parameterized).
To test multiple parameters, wrap each parameter argument with
[Param](https://vectorbt.pro/pvt_6d1b3986/api/utils/params/#vectorbtpro.utils.params.Param).

!!! example
    See an example in [Parameterized decorator](https://vectorbt.pro/pvt_6d1b3986/features/optimization/#parameterized-decorator).

### Decoration

To parameterize any function, decorate (or wrap) it with `@vbt.parameterized`. This returns a new
function with the same name and arguments as the original. The only difference is that the new
function processes the provided arguments, builds all parameter combinations, invokes the original
function for each combination, and merges the results of all combinations.

```python title="Process only one parameter combination at a time"
@vbt.parameterized
def my_pipeline(data, fast_window, slow_window):  # (1)!
    ...
    return result  # (2)!

results = my_pipeline(  # (3)!
    data,
    vbt.Param(fast_windows),  # (4)!
    vbt.Param(slow_windows)
)
```

1. Arguments can be anything. In this example, we expect a data instance and two parameters:
   `fast_window` and `slow_window`. The decorator will pass them as single values.
2. Perform calculations using the current parameter combination and return a result, which can be anything.
3. Call the function the same way as without the decorator.
4. Wrap each set of multiple values in `vbt.Param` for every parameter.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To keep the original function separate from the decorated one, you can apply the decorator after defining
the function and assign the decorated function to a different name.

```python title="Decorate a function later"
def my_pipeline(data, fast_window, slow_window):
    ...
    return result

my_param_pipeline = vbt.parameterized(my_pipeline)
results = my_param_pipeline(...)
```

### Merging

The code above returns a list of results, one for each parameter combination. To also return the grid
of parameter combinations, pass `return_param_index=True` to the decorator. Alternatively, you can
have VBT merge the results into one or more Pandas objects and attach the grid to their index or columns
by specifying a merging function (see [resolve_merge_func](https://vectorbt.pro/pvt_6d1b3986/api/base/reshaping/#vectorbtpro.base.merging.resolve_merge_func)).

```python title="Various merging configurations"
@vbt.parameterized(return_param_index=True)  # (1)!
def my_pipeline(...):
    ...
    return result
    
results, param_index = my_pipeline(...)

# ______________________________________________________________

@vbt.parameterized(merge_func="concat")  # (2)!
def my_pipeline(...):
    ...
    return pf.sharpe_ratio
    
sharpe_ratio = my_pipeline(...)

# ______________________________________________________________

@vbt.parameterized(merge_func="concat")
def my_pipeline(...):
    ...
    return pf.sharpe_ratio, pf.win_rate
    
sharpe_ratio, win_rate = my_pipeline(...)

# ______________________________________________________________
    
@vbt.parameterized(merge_func="column_stack")  # (3)!
def my_pipeline(...):
    ...
    return entries, exits
    
entries, exits = my_pipeline(...)

# ______________________________________________________________

@vbt.parameterized(merge_func="row_stack")  # (4)!
def my_pipeline(...):
    ...
    return pf.value
    
value = my_pipeline(...)

# ______________________________________________________________

@vbt.parameterized(merge_func=("concat", "column_stack"))  # (5)!
def my_pipeline(...):
    ...
    return pf.sharpe_ratio, pf.value
    
sharpe_ratio, value = my_pipeline(...)

# ______________________________________________________________

def merge_func(results, param_index):
    return pd.Series(results, index=param_index)
    
@vbt.parameterized(
    merge_func=merge_func,  # (6)!
    merge_kwargs=dict(param_index=vbt.Rep("param_index"))  # (7)!
)
def my_pipeline(...):
    ...
    return pf.sharpe_ratio
    
sharpe_ratio = my_pipeline(...)
```

1. Return the results along with the parameter grid.
2. If the function returns a single number (or a tuple of numbers), concatenate all into a Series using
the parameter combinations as the index. This is useful for returning metrics like Sharpe ratio.
3. If the function returns an array (or a tuple of arrays), stack all arrays along columns into a DataFrame,
using the parameter combinations as the outermost column level. This is useful for indicator arrays.
4. If the function returns an array (or a tuple of arrays), stack all arrays along rows into a Series or
DataFrame, using the parameter combinations as the outermost index level. Useful for cross-validation.
5. If the function returns a number and an array, return a Series of concatenated numbers and a DataFrame
of arrays stacked along columns.
6. Pass a custom merging function.
7. Use an expression template to pass the parameter index as a keyword argument.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can also use annotations to specify the merging function or functions.

```python
@vbt.parameterized
def my_pipeline(...) -> "concat":  # (1)!
    ...
    return result

# ______________________________________________________________

@vbt.parameterized
def my_pipeline(...) -> ("concat", "column_stack"):  # (2)!
    ...
    return result1, result2

# ______________________________________________________________

@vbt.parameterized
def my_pipeline(...) -> (  # (3)!
    vbt.MergeFunc("concat", wrap=False), 
    vbt.MergeFunc("column_stack", wrap=False)
):
    ...
    return result1, result2
```

1. Concatenates the results.
2. Concatenates the first result and stacks the second result along columns.
3. The same as above but allows specifying keyword arguments for each merging function.

### Generation

You can control the grid of parameter combinations using individual parameters. By default,
vectorbtpro builds a Cartesian product of all parameters. To avoid building the product between
certain parameters, assign them to the same product `level`. To filter out unwanted parameter
configurations, specify a `condition` as a boolean expression using parameter names as variables.
This condition is evaluated for each parameter combination, and only those returning True are kept.
To change how a parameter appears in the parameter index, provide `keys` with human-readable strings.
A parameter can also be hidden entirely by setting `hide=True`.

```python title="Various parameter configurations"

sma_crossover(  # (1)!
    data=data,
    fast_window=vbt.Param(windows, condition="fast_window < slow_window"),
    slow_window=vbt.Param(windows),
)

# ______________________________________________________________

sma_crossover(  # (2)!
    data=vbt.Param(data),
    fast_window=vbt.Param(windows, condition="fast_window < slow_window"),
    slow_window=vbt.Param(windows),
)

# ______________________________________________________________

from itertools import combinations

fast_windows, slow_windows = zip(*combinations(windows, 2))  # (3)!
sma_crossover(
    data=vbt.Param(data, level=0),
    fast_window=vbt.Param(fast_windows, level=1),
    slow_window=vbt.Param(slow_windows, level=1),
)

# ______________________________________________________________

bbands_indicator(  # (4)!
    data=data,
    timeperiod=vbt.Param(timeperiods, level=0),
    upper_threshold=vbt.Param(thresholds, level=1, keys=pd.Index(thresholds, name="threshold")),
    lower_threshold=vbt.Param(thresholds, level=1, hide=True),
    _random_subset=1_000  # (5)!
)
```

1. Builds a product of fast and slow windows, removing those where the fast window is longer than the
slow window (for example, 20 and 50 is valid, but 50 and 20 does not make sense).
2. The same as above but tests only one symbol at a time.
3. The same as above but builds the window combinations manually. The window parameters are now on the
same level and will not create another product.
4. Tests two parameters: time periods and thresholds. Upper and lower thresholds share the same values,
and only one `threshold` level is displayed in the parameter index. Also, select a random subset of
   1,000 parameter combinations.
5. Arguments that are normally passed to the decorator can also be passed to the function itself by
prepending an underscore.

!!! example
    See an example in [Conditional parameters](https://vectorbt.pro/pvt_6d1b3986/features/optimization/#conditional-parameters).

!!! warning
    Testing 6 parameters with 10 values each generates a huge 1 million parameter combinations, so be
    careful not to make your grids too large. Otherwise, the grid generation alone will take a long time.
    This warning does not apply if you use `random_subset`. In that case, VBT selects random
    combinations dynamically instead of building the full grid. See
    [Lazy parameter grids](https://vectorbt.pro/pvt_6d1b3986/features/optimization/#lazy-parameter-grids) for an example.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can also use annotations to specify which arguments are parameters and their default configuration.

```python title="Calculate the SMA crossover for one parameter combination at a time"
@vbt.parameterized
def sma_crossover(
    data,
    fast_window: vbt.Param(condition="fast_window < slow_window"),
    slow_window: vbt.Param,
) -> "column_stack":
    fast_sma = data.run("talib:sma", fast_window, unpack=True)
    slow_sma = data.run("talib:sma", slow_window, unpack=True)
    upper_crossover = fast_sma.vbt.crossed_above(slow_sma)
    lower_crossover = fast_sma.vbt.crossed_below(slow_sma)
    signals = upper_crossover | lower_crossover
    return signals

signals = sma_crossover(data, fast_windows, slow_windows)
```

#### Pre-generation

To obtain the generated parameter combinations before (or without) calling the `@vbt.parameterized`
decorator, you can pass the same parameters to [combine_params](https://vectorbt.pro/pvt_6d1b3986/api/utils/params/#vectorbtpro.utils.params.combine_params).

```python title="Pre-generate parameter combinations"
param_product, param_index = vbt.combine_params(
    dict(
        fast_window=vbt.Param(windows, condition="fast_window < slow_window"),
        slow_window=vbt.Param(windows),
    )
)

# ______________________________________________________________

param_product = vbt.combine_params(
    dict(
        fast_window=vbt.Param(windows, condition="fast_window < slow_window"),
        slow_window=vbt.Param(windows),
    ),
    build_index=False  # (1)!
)
```

1. Do not build the index. Only return the parameter product.

### Execution

Each parameter combination results in a single call to the pipeline function. To execute multiple calls
in parallel, provide a dictionary named `execute_kwargs` containing keyword arguments that will be
forwarded to the [execute](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute) function, which
handles chunking and execution of the function calls.

```python title="Various execution configurations"
@vbt.parameterized  # (1)!
def my_pipeline(...):
    ...
    
# ______________________________________________________________

@vbt.parameterized(execute_kwargs=dict(chunk_len="auto", engine="threadpool"))  # (2)!
@njit(nogil=True)
def my_pipeline(...):
    ...
    
# ______________________________________________________________

@vbt.parameterized(execute_kwargs=dict(n_chunks="auto", distribute="chunks", engine="pathos"))  # (3)!
def my_pipeline(...):
    ...

# ______________________________________________________________

@vbt.parameterized  # (4)!
@njit(nogil=True)
def my_pipeline(...):
    ...

my_pipeline(
    ...,
    _execute_kwargs=dict(chunk_len="auto", engine="threadpool")
)

# ______________________________________________________________

@vbt.parameterized(execute_kwargs=dict(show_progress=False))  # (5)!
@njit(nogil=True)
def my_pipeline(...):
    ...

my_pipeline(
    ...,
    _execute_kwargs=dict(chunk_len="auto", engine="threadpool")  # (6)!
)
my_pipeline(
    ...,
    _execute_kwargs=vbt.atomic_dict(chunk_len="auto", engine="threadpool")  # (7)!
)
```

1. Execute parameter combinations serially.
2. Distribute parameter combinations into chunks of optimal length, and execute all parameter
combinations within each chunk in parallel using multithreading (one parameter combination per thread),
while executing chunks serially.
3. Divide parameter combinations into an optimal number of chunks, and execute all chunks in parallel
using multiprocessing (one chunk per process), while executing parameter combinations within each
chunk serially.
4. Parallelization can be enabled or disabled for each call by prepending an underscore to
`execute_kwargs` and passing it directly to the function.
5. If `execute_kwargs` is already set in the decorator, the values will be merged. To avoid merging,
wrap any of the dictionaries with `vbt.atomic_dict`.
6. `show_progress=False`
7. `show_progress=True` (default)

!!! note
    Threads are easier and faster to spawn than processes. To execute a function in its own process,
    all inputs and parameters must be serialized and then deserialized, which adds overhead.
    Multithreading is preferred, but the function needs to release the GIL, so use Numba compiled
    functions with `nogil=True`, or only use NumPy.

    If that is not possible, use multiprocessing, but make sure the function does not take large
    arrays, or that a single parameter combination takes a substantial amount of time to run.
    Otherwise, parallelization can end up making execution even slower.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To run code before or after the entire process, or even before or after each individual chunk,
[execute](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute) provides several callbacks.

```python title="Clear cache and collect garbage once in 3 chunks"
def post_chunk_func(chunk_idx, flush_every):
    if (chunk_idx + 1) % flush_every == 0:
        vbt.flush()

@vbt.parameterized(
    post_chunk_func=post_chunk_func,
    post_chunk_kwargs=dict(
        chunk_idx=vbt.Rep("chunk_idx", eval_id="post_chunk_kwargs"), 
        flush_every=3
    ),
    chunk_len=10  # (1)!
)  
def my_pipeline(...):
    ...
```

1. Put 10 calls into each chunk, so flushing occurs every 30 calls.

!!! tip
    This works not just with `@vbt.parameterized`, but also with other functions that use
    [execute](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute) along with chunking!

### Total or partial?

You often need to decide whether your pipeline should be totally or partially parameterized.
Total parameterization means running the entire pipeline for each parameter combination.
This approach is simplest and is most suitable when parameters are used across several components
of the pipeline, or when you want to sacrifice some speed for reduced memory usage.

```python title="Parameterize an entire MA crossover pipeline"
@vbt.parameterized(merge_func="concat")  
def ma_crossover_sharpe(data, fast_window, slow_window):
    fast_ma = data.run("vbt:ma", window=fast_window, hide_params=True)
    slow_ma = data.run("vbt:ma", window=slow_window, hide_params=True)
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    pf = vbt.PF.from_signals(data, entries, exits)
    return pf.sharpe_ratio

ma_crossover_sharpe(
    data, 
    vbt.Param(fast_windows, condition="fast_window < slow_window"), 
    vbt.Param(slow_windows)
)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Partial parameterization is a good option when only a small part of the pipeline uses parameters,
and the rest can process results from those parameterized components. This can
lead to faster execution, but often results in higher memory usage.

```python title="Parameterize only the signal part of a MA crossover pipeline"
@vbt.parameterized(merge_func="column_stack")  
def ma_crossover_signals(data, fast_window, slow_window):
    fast_ma = data.run("vbt:ma", window=fast_window, hide_params=True)
    slow_ma = data.run("vbt:ma", window=slow_window, hide_params=True)
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    return entries, exits

def ma_crossover_sharpe(data, fast_windows, slow_windows):
    entries, exits = ma_crossover_signals(data, fast_windows, slow_windows)  # (1)!
    pf = vbt.PF.from_signals(data, entries, exits)  # (2)!
    return pf.sharpe_ratio

ma_crossover_sharpe(
    data, 
    vbt.Param(fast_windows, condition="fast_window < slow_window"), 
    vbt.Param(slow_windows)
)
```

1. Parameter combinations become columns in the entry and exit arrays.
2. The simulator is able to process these additional columns.

### Flat or nested?

Another decision to make is whether to use one decorator for all parameters (flat parameterization)
or to place parameters across multiple decorators to implement a parameter hierarchy (nested parameterization).
Use the former if you want to treat all parameters equally and combine them together for generation
and processing. In this case, the order of the parameter combinations is determined by the order in
which parameters are passed to the function. For example, the values of the first parameter will be
processed sequentially, while the values of any additional parameter will be rotated.

```python title="Process all parameters at the same time in a MA crossover pipeline"
@vbt.parameterized(merge_func="concat")  
def ma_crossover_sharpe(data, symbol, fast_window, slow_window):
    symbol_data = data.select(symbol)  # (1)!
    fast_ma = symbol_data.run("vbt:ma", window=fast_window, hide_params=True)
    slow_ma = symbol_data.run("vbt:ma", window=slow_window, hide_params=True)
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    pf = vbt.PF.from_signals(symbol_data, entries, exits)
    return pf.sharpe_ratio

ma_crossover_sharpe(
    data, 
    vbt.Param(data.symbols), 
    vbt.Param(fast_windows, condition="fast_window < slow_window"), 
    vbt.Param(slow_windows),
)
```

1. Symbol selection depends only on the symbol but is run for every combination of
`symbol`, `fast_window`, and `slow_window`—often unnecessarily!

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

The second approach should be used if you want to set up your own custom parameter hierarchy.
For example, you may want to process some parameters (such as in parallel) differently, limit
the number of times certain parameters are invoked, or add special preprocessing or postprocessing
to specific parameters.

```python title="First process symbols and then windows in a MA crossover pipeline"
@vbt.parameterized(merge_func="concat", eval_id="inner")  # (1)!
def symbol_ma_crossover_sharpe(symbol_data, fast_window, slow_window):
    fast_ma = symbol_data.run("vbt:ma", window=fast_window, hide_params=True)
    slow_ma = symbol_data.run("vbt:ma", window=slow_window, hide_params=True)
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    pf = vbt.PF.from_signals(symbol_data, entries, exits)
    return pf.sharpe_ratio

@vbt.parameterized(merge_func="concat", eval_id="outer")  # (2)!
def ma_crossover_sharpe(data, symbol, fast_windows, slow_windows):
    symbol_data = data.select(symbol)  # (3)!
    return symbol_ma_crossover_sharpe(symbol_data, fast_windows, slow_windows)  # (4)!

ma_crossover_sharpe(  # (5)!
    data, 
    vbt.Param(data.symbols, eval_id="outer"),
    vbt.Param(fast_windows, eval_id="inner", condition="fast_window < slow_window"),
    vbt.Param(slow_windows, eval_id="inner")
)

# ______________________________________________________________

@vbt.parameterized(merge_func="concat", eval_id="outer")
@vbt.parameterized(merge_func="concat", eval_id="inner")
def ma_crossover_sharpe(data, fast_window, slow_window):  # (6)!
    fast_ma = data.run("vbt:ma", window=fast_window, hide_params=True)
    slow_ma = data.run("vbt:ma", window=slow_window, hide_params=True)
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    pf = vbt.PF.from_signals(data, entries, exits)
    return pf.sharpe_ratio

ma_crossover_sharpe(
    vbt.Param(data, eval_id="outer"),
    vbt.Param(fast_windows, eval_id="inner", condition="fast_window < slow_window"),
    vbt.Param(slow_windows, eval_id="inner")
)
```

1. The inner decorator, which iterates over fast and slow windows.
2. The outer decorator, which iterates over symbols.
3. This line now runs only once per symbol, making it more efficient.
4. Call the inner function from within the outer function.
5. Call the outer function with all parameters, specifying for each which function it should be evaluated at.
6. The same function can be parameterized multiple times, with each decorator handling a subset of the parameters.

### Skipping

Parameter combinations can be skipped dynamically by returning
[NoResult](https://vectorbt.pro/pvt_6d1b3986/api/utils/params/#vectorbtpro.utils.params.NoResult) instead of an actual result.

```python title="Skip the parameter combination if an error occurred"
@vbt.parameterized
def my_pipeline(data, fast_window, slow_window):
    try:
        ...
        return result
    except Exception:
        return vbt.NoResult

results = my_pipeline(
    data,
    vbt.Param(fast_windows),
    vbt.Param(slow_windows)
)
```

## Hybrid (mono-chunks)

The approach above calls the original function for each individual parameter combination, which can be
slow when working with many combinations, especially if each function call comes with overhead,
such as when converting a NumPy array to a Pandas object. Keep in mind that 1 millisecond of overhead
adds up to about 17 minutes of extra execution time for one million combinations.

For functions that accept only one combination at a time, there is nothing (aside from parallelization)
that can be done to speed them up. However, if your function can be modified to accept multiple combinations
at once—where each parameter argument is an array rather than a single value—you can instruct
`@vbt.parameterized` to merge all combinations into chunks and call the function on each chunk.
This approach can greatly reduce the number of function calls.

```python title="Test a grid of parameters using mono-chunks"
@vbt.parameterized(mono_n_chunks=?, mono_chunk_len=?, mono_chunk_meta=?)  # (1)!
def my_pipeline(data, fast_windows, slow_windows):  # (2)!
    ...
    return result  # (3)!

results = my_pipeline(  # (4)!
    data,
    vbt.Param(fast_windows),
    vbt.Param(slow_windows)
)

# ______________________________________________________________

@vbt.parameterized(mono_n_chunks="auto")  # (5)!
...

# ______________________________________________________________

@vbt.parameterized(mono_chunk_len=100)  # (6)!
...
```

1. Instruct VBT to create chunks from parameter combinations. Use `mono_n_chunks` to set a target number
of chunks, `mono_chunk_len` to specify the maximum combinations per chunk, or
`mono_chunk_meta` to define chunk metadata directly.
2. The function should now accept multiple values of `fast_windows` and `slow_windows` instead of
single values like `fast_window` and `slow_window`. Each set of values contains
combinations within the same chunk.
3. Perform calculations on the given parameter combinations and return a result
(which should include an outcome for each combination).
4. Call the function as before.
5. Create as many chunks as there are CPU cores.
6. Create chunks with no more than 100 combinations each.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

By default, parameter values are passed as lists to the original function. To pass them as arrays,
or in another format, set a merging function `mono_merge_func` for each parameter.

```python
my_pipeline(
    param_a=vbt.Param(param_a),  # (1)!
    param_b=vbt.Param(param_b, mono_reduce=True),  # (2)!
    param_c=vbt.Param(param_c, mono_merge_func="concat"),  # (3)!
    param_d=vbt.Param(param_d, mono_merge_func="row_stack"),  # (4)!
    param_e=vbt.Param(param_e, mono_merge_func="column_stack"),  # (5)!
    param_f=vbt.Param(param_f, mono_merge_func=vbt.MergeFunc(...))  # (6)!
)
```

1. Places chunk values into a list.
2. The same as above, but returns a single value if all values in the chunk are the same.
3. Concatenates values into a NumPy array or Pandas Series.
4. Stacks chunk values along rows into a NumPy array or Pandas Series/DataFrame.
5. Stacks chunk values along columns into a NumPy array or Pandas DataFrame.
6. Merges chunk values using a custom merging function.

Execution works the same way as in [Parameterization](#parameterization), and chunks can be easily
parallelized. However, keep an eye on RAM usage since multiple parameter combinations
are processed at the same time.

!!! example
    Check out an example in [Mono-chunks](https://vectorbt.pro/pvt_6d1b3986/features/optimization/#mono-chunks).

## Chunking

Chunking is the process of splitting a value (such as an array) of one or more arguments into smaller
parts (called chunks), running the function on each part, and then merging the results back together.
This allows VBT to process only a subset of data at a time, which helps reduce RAM usage
and improves performance through parallelization. Chunking is also highly convenient—
most of the time, you do not need to modify your function, and you will get the same results whether
or not chunking is enabled. To use chunking, create a pipeline function, decorate it with
[`@vbt.chunked`](https://vectorbt.pro/pvt_6d1b3986/api/utils/chunking/#vectorbtpro.utils.chunking.chunked), and specify
how arguments should be chunked and how results should be merged.

!!! example
    See an example in [Chunking](https://vectorbt.pro/pvt_6d1b3986/features/performance/#chunking).

### Decoration

To make any function chunkable, decorate (or wrap) it with `@vbt.chunked`.
This returns a new function with the same name and arguments as the original. The only
difference is that this new function processes the arguments, chunks them, calls the original
function on each chunk, and then merges the results from all chunks.

```python title="Process only a subset of values at a time"
@vbt.chunked
def my_pipeline(data, fast_windows, slow_windows):  # (1)!
    ...
    return result  # (2)!

results = my_pipeline(  # (3)!
    data,
    vbt.Chunked(fast_windows),  # (4)!
    vbt.Chunked(slow_windows)
)
```

1. Arguments can be anything. Here, data is expected, along with already combined fast and slow windows,
as in [Hybrid (mono-chunks)](#hybrid-mono-chunks).
2. Perform calculations on the received chunk of values and return a result, which can be anything.
3. Call the function in the same way as before, just as without the decorator.
4. Wrap any chunkable argument with `vbt.Chunked` or another class.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To keep the original function separate from the decorated one, you can decorate it after its
definition and assign a different name to the decorated function.

```python title="Decorate a function later"
def my_pipeline(data, fast_windows, slow_windows):
    ...
    return result

my_chunked_pipeline = vbt.chunked(my_pipeline)
results = my_chunked_pipeline(...)
```

### Specification

To chunk an argument, you need to provide a chunking specification for that argument. There are three
main ways to specify this.

Approach 1: Pass a dictionary `arg_take_spec` to the decorator. This is the most versatile approach, as it allows
chunking of any nested objects of arbitrary depth, such as lists inside lists.

```python title="Specify chunking rules via arg_take_spec"
@vbt.chunked(
    arg_take_spec=dict(  # (1)!
        array1=vbt.ChunkedArray(axis=1),  # (2)!
        array2=vbt.ChunkedArray(axis=1),
        combine_func=vbt.NotChunked  # (3)!
    ),
    size=vbt.ArraySizer(arg_query="array1", axis=1),  # (4)!
    merge_func="column_stack"  # (5)!
)
def combine_arrays(array1, array2, combine_func):
    return combine_func(array1, array2)

new_array = combine_arrays(array1, array2, np.add)
```

1. A dictionary where keys are argument names and values are chunking rules for those arguments.
2. Split arguments `array1` and `array2` along columns. They must be multidimensional NumPy or Pandas arrays.
3. Provide rules for all arguments. If any argument is missing in `arg_take_spec`, a warning will be shown.
4. Specify from where to take the total size. This is needed to build chunks. It is mostly
optional, as newer versions of VBT can determine it automatically.
5. The merging function must work with the chunked arrays. Here, we stack columns of output arrays back together.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Approach 2: Annotate the function. This is the most convenient approach, allowing you to specify chunking rules
right next to each argument in the function definition.

```python title="Specify chunking rules via annotations"
@vbt.chunked
def combine_arrays(
    array1: vbt.ChunkedArray(axis=1) | vbt.ArraySizer(axis=1),  # (1)!
    array2: vbt.ChunkedArray(axis=1),
    combine_func
) -> "column_stack":
    return combine_func(array1, array2)

new_array = combine_arrays(array1, array2, np.add)
```

1. You can combine multiple VBT annotations with the `|` operator. It does not matter whether
a chunking annotation is a class or an instance. Providing the sizer is mostly optional, as
newer versions of VBT can determine it automatically.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Approach 3: Wrap argument values directly. This lets you switch chunking rules on the fly.

```python title="Specify chunking rules via argument values"
@vbt.chunked
def combine_arrays(array1, array2, combine_func):
    return combine_func(array1, array2)

new_array = combine_arrays(  # (1)!
    vbt.ChunkedArray(array1),
    vbt.ChunkedArray(array2),
    np.add,
    _size=len(array1),  # (2)!
    _merge_func="concat"
)
new_array = combine_arrays(  # (3)!
    vbt.ChunkedArray(array1, axis=0),
    vbt.ChunkedArray(array2, axis=0),
    np.add,
    _size=array1.shape[0],
    _merge_func="row_stack"
)
new_array = combine_arrays(  # (4)!
    vbt.ChunkedArray(array1, axis=1),
    vbt.ChunkedArray(array2, axis=1),
    np.add,
    _size=array1.shape[1],
    _merge_func="column_stack"
)
```

1. Split one-dimensional input arrays and concatenate the output arrays back together.
2. Providing the total size is mostly optional, as newer versions of VBT can determine it automatically.
3. Split two-dimensional input arrays along rows and stack the rows of output arrays together.
4. Split two-dimensional input arrays along columns and stack the columns of output arrays together.

Merging and execution work in the same way as in [Parameterization](#parameterization).

## Hybrid (super-chunks)

You can combine the [parameterized decorator](#parameterization) and the chunked decorator to process only
a subset of parameter combinations at a time, without needing to change the function's design as in
[Hybrid (mono-chunks)](#hybrid-mono-chunks). Although super-chunking may not be as fast as mono-chunking,
it is still useful when you want to process only part of the parameter combinations at a time
(but not all; otherwise, you should just use `distribute="chunks"` in the parameterized decorator
without the chunked decorator) to manage RAM usage, or when you need to perform preprocessing and/or
postprocessing, such as flushing per batch of parameter combinations.

```python title="Execute at most n parameter combinations per process"
@vbt.parameterized
def my_pipeline(data, fast_window, slow_window):  # (1)!
    ...
    return result

@vbt.chunked(
    chunk_len=?,  # (2)!
    execute_kwargs=dict(chunk_len="auto", engine="pathos")  # (3)!
)
def chunked_pipeline(data, fast_windows, slow_windows):  # (4)!
    return my_pipeline(
        data,
        vbt.Param(fast_windows, level=0),
        vbt.Param(slow_windows, level=0)
    )

param_product = vbt.combine_params(  # (5)!
    dict(
        fast_windows=fast_windows,
        slow_windows=slow_windows,
    ),
    build_index=False
)

chunked_pipeline(
    data,
    vbt.Chunked(param_product["fast_windows"]),
    vbt.Chunked(param_product["slow_windows"])
)
```

1. The parameterized function expects a single parameter combination, with each parameter argument as a single value.
2. Split each sequence of parameter values into chunks of n elements.
3. Build super-chunks from chunks, where chunks within each super-chunk execute in parallel,
and super-chunks themselves execute in sequence.
4. The chunked function expects a grid of parameter combinations, with each parameter argument as a sequence
of values. All sequences must have the same length.
5. Build a grid of parameter combinations.

## Raw execution

Whenever VBT needs to execute a function on multiple sets of arguments, it uses the
[execute](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute) function. This function takes
a list of tasks (functions and their arguments) and runs them using the engine selected by the user.
It accepts all the same arguments that you usually provide in `execute_kwargs`.

```python title="Execute multiple indicator configurations in parallel"
sma_func = vbt.talib_func("sma")
ema_func = vbt.talib_func("ema")
tasks = [
    vbt.Task(sma_func, arr, 10),  # (1)!
    vbt.Task(sma_func, arr, 20),
    vbt.Task(ema_func, arr, 10),
    vbt.Task(ema_func, arr, 20),
]
keys = pd.MultiIndex.from_tuples([  # (2)!
    ("sma", 10),
    ("sma", 20),
    ("ema", 10),
    ("ema", 20),
], names=["indicator", "timeperiod"])

indicators_df = vbt.execute(  # (3)!
    tasks,
    keys=keys,
    merge_func="column_stack",
    engine="threadpool"
)
```

1. Each task consists of the function and the (positional and keyword) arguments it needs.
2. Keys appear in the progress bar and in the columns of the new DataFrame.
3. Execute tasks in separate threads and merge them into a DataFrame.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To parallelize a workflow inside a for-loop, place it in a function and decorate
the function with [iterated](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.iterated).
Then, when you execute the decorated function, pass the total number of iterations or a range
to the argument where you expect the iteration variable.

```python title="Execute a regular for-loop in parallel"
# ______________________________ FROM ______________________________

results = []
keys = []
for timeperiod in range(20, 50, 5):
    result = sma_func(arr, timeperiod)
    results.append(result)
    keys.append(timeperiod)
keys = pd.Index(keys, name="timeperiod")
sma_df = pd.concat(map(pd.Series, results), axis=1, keys=keys)

# ______________________________ TO ______________________________

@vbt.iterated(over_arg="timeperiod", merge_func="column_stack", engine="threadpool")
def sma(arr, timeperiod):
    return sma_func(arr, timeperiod)

sma = vbt.iterated(  # (1)!
    sma_func,
    over_arg="timeperiod",
    engine="threadpool",
    merge_func="column_stack"
)

sma_df = sma(arr, range(20, 50, 5))
```

1. Another way to decorate a function.

```python title="Execute a nested for-loop in parallel"
# ______________________________ FROM ______________________________

results = []
keys = []
for fast_window in range(20, 50, 5):
    for slow_window in range(20, 50, 5):
        if fast_window < slow_window:
            fast_sma = sma_func(arr, fast_window)
            slow_sma = sma_func(arr, slow_window)
            result = fast_sma - slow_sma
            results.append(result)
            keys.append((fast_window, slow_window))
keys = pd.MultiIndex.from_tuples(keys, names=["fast_window", "slow_window"])
sma_diff_df = pd.concat(map(pd.Series, results), axis=1, keys=keys)

# ______________________________ TO ______________________________

@vbt.iterated(over_arg="fast_window", merge_func="column_stack", engine="pathos")  # (1)!
@vbt.iterated(over_arg="slow_window", merge_func="column_stack", raise_no_results=False)
def sma_diff(arr, fast_window, slow_window):
    if fast_window >= slow_window:
        return vbt.NoResult
    fast_sma = sma_func(arr, fast_window)
    slow_sma = sma_func(arr, slow_window)
    return fast_sma - slow_sma

sma_diff_df = sma_diff(arr, range(20, 50, 5), range(20, 50, 5))
```

1. Execute the outer loop in parallel using multiprocessing.