---
title: Performance
description: Performance features of VectorBT PRO
icon: material/speedometer
---

# :material-speedometer: Performance

## Chunk caching

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_5_15.svg){ loading=lazy }

- [x] Most workflows that use the VBT's execution framework—such as data pulling, chunking,
parameterization, splitting, and optimization—can now offload intermediate results to disk and
reload them if the workflow crashes and restarts. You can confidently test billions of parameter
combinations on cloud instances without worrying about losing your data.

```pycon title="Execute a basic range with random fallouts while caching successful attempts"
>>> @vbt.parameterized(cache_chunks=True, chunk_len=1)  # (1)!
... def basic_iterator(i):
...     print("i:", i)
...     rand_number = np.random.uniform()
...     if rand_number < 0.2:
...         print("failed ⛔")
...         raise ValueError
...     return i

>>> attempt = 0
>>> while True:
...     attempt += 1
...     print("attempt", attempt)
...     try:
...         basic_iterator(vbt.Param(np.arange(10)))
...         print("completed 🎉")
...         break
...     except ValueError:
...         pass
attempt 1
i: 0
i: 1
failed ⛔
attempt 2
i: 1
i: 2
i: 3
i: 4
failed ⛔
attempt 3
i: 4
i: 5
i: 6
i: 7
i: 8
i: 9
completed 🎉
```

1. Cache each function call.

## Accumulators

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_10.svg){ loading=lazy }

- [x] Most rolling indicators implemented with Pandas and NumPy require multiple passes over the
data. For example, calculating the sum of three arrays requires at least two passes. If you want to
calculate such an indicator iteratively (bar by bar), you either need to pre-calculate everything and
store it in memory or re-calculate each window, which can significantly impact performance.
[Accumulators](https://theboostcpplibraries.com/boost.accumulators), however, maintain an internal
state that allows you to compute an indicator value as soon as a new data point arrives, resulting in
the best possible performance.

```pycon title="Design a one-pass rolling z-score"
>>> @njit
... def fastest_rolling_zscore_1d_nb(arr, window, minp=None, ddof=1):
...     if minp is None:
...         minp = window
...     out = np.full(arr.shape, np.nan)
...     cumsum = 0.0
...     cumsum_sq = 0.0
...     nancnt = 0
...     
...     for i in range(len(arr)):
...         pre_window_value = arr[i - window] if i - window >= 0 else np.nan
...         mean_in_state = vbt.nb.RollMeanAIS(
...             i, arr[i], pre_window_value, cumsum, nancnt, window, minp
...         )
...         mean_out_state = vbt.nb.rolling_mean_acc_nb(mean_in_state)
...         _, _, _, mean = mean_out_state
...         std_in_state = vbt.nb.RollStdAIS(
...             i, arr[i], pre_window_value, cumsum, cumsum_sq, nancnt, window, minp, ddof
...         )
...         std_out_state = vbt.nb.rolling_std_acc_nb(std_in_state)
...         cumsum, cumsum_sq, nancnt, _, std = std_out_state
...         out[i] = (arr[i] - mean) / std
...     return out
    
>>> data = vbt.YFData.pull("BTC-USD")
>>> rolling_zscore = fastest_rolling_zscore_1d_nb(data.returns.values, 14)
>>> data.symbol_wrapper.wrap(rolling_zscore)
Date
2014-09-17 00:00:00+00:00         NaN
2014-09-18 00:00:00+00:00         NaN
2014-09-19 00:00:00+00:00         NaN
                                  ...   
2023-02-01 00:00:00+00:00    0.582381
2023-02-02 00:00:00+00:00   -0.705441
2023-02-03 00:00:00+00:00   -0.217880
Freq: D, Name: BTC-USD, Length: 3062, dtype: float64

>>> (data.returns - data.returns.rolling(14).mean()) / data.returns.rolling(14).std()
Date
2014-09-17 00:00:00+00:00         NaN
2014-09-18 00:00:00+00:00         NaN
2014-09-19 00:00:00+00:00         NaN
                                  ...   
2023-02-01 00:00:00+00:00    0.582381
2023-02-02 00:00:00+00:00   -0.705441
2023-02-03 00:00:00+00:00   -0.217880
Freq: D, Name: Close, Length: 3062, dtype: float64
```

## Chunking

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] A new, innovative chunking mechanism lets you specify how arguments should be chunked. It
automatically splits array-like arguments, passes each chunk to the function for execution, and then
merges the results. This enables you to split large arrays and run any function in a distributed
manner. VBT also features a central registry and provides chunking specifications for all arguments
of most Numba-compiled functions, including simulation functions. Chunking can be enabled with a
single command. You no longer have to worry about out-of-memory errors! :tada:

```pycon title="Backtest at most 100 parameter combinations at once"
>>> @vbt.chunked(
...     chunk_len=100,
...     merge_func="concat",  # (1)!
...     execute_kwargs=dict(  # (2)!
...         clear_cache=True,
...         collect_garbage=True
...     )
... )
... def backtest(data, fast_windows, slow_windows):  # (3)!
...     fast_ma = vbt.MA.run(data.close, fast_windows, short_name="fast")
...     slow_ma = vbt.MA.run(data.close, slow_windows, short_name="slow")
...     entries = fast_ma.ma_crossed_above(slow_ma)
...     exits = fast_ma.ma_crossed_below(slow_ma)
...     pf = vbt.PF.from_signals(data.close, entries, exits)
...     return pf.total_return

>>> param_product = vbt.combine_params(  # (4)!
...     dict(
...         fast_window=vbt.Param(range(2, 100), condition="fast_window < slow_window"),
...         slow_window=vbt.Param(range(2, 100)),
...     ),
...     build_index=False
... )
>>> backtest(
...     vbt.YFData.pull(["BTC-USD", "ETH-USD"]),  # (5)!
...     vbt.Chunked(param_product["fast_window"]),  # (6)!
...     vbt.Chunked(param_product["slow_window"])
... )
```

1. Concatenate the Series returned by each chunk into one Series.
2. Show a progress bar, and also clear cache and collect garbage after processing each chunk.
3. This function takes a data instance, as well as two parameter arrays: fast and slow window lengths.
Both arrays will have the same number of values; for example, the first combination matches the
first value in `fast_windows` with the first value in `slow_windows`.
4. Generate conditional parameter combinations.
5. Do not split the data into chunks.
6. Split both parameter arrays into chunks.

[=100% "Chunk 48/48"]{: .candystripe .candystripe-animate }

```pycon
fast_window  slow_window  symbol 
2            3            BTC-USD    193.124482
                          ETH-USD     12.247315
             4            BTC-USD    159.600953
                          ETH-USD     15.825041
             5            BTC-USD    124.703676
                                        ...    
97           98           ETH-USD      3.947346
             99           BTC-USD     25.551881
                          ETH-USD      3.442949
98           99           BTC-USD     27.943574
                          ETH-USD      3.540720
Name: total_return, Length: 9506, dtype: float64
```

## Parallel Numba

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] Most Numba-compiled functions have been rewritten to process columns in parallel using
[automatic parallelization with `@jit`](https://numba.readthedocs.io/en/stable/user/parallel.html).
You can enable this with a single command. This approach is best for lightweight functions that are
applied to wide arrays.

```pycon title="Benchmark the rolling mean without and with parallelization"
>>> df = pd.DataFrame(np.random.uniform(size=(1000, 1000)))

>>> %timeit df.rolling(10).mean()  # (1)!
45.6 ms ± 138 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

>>> %timeit df.vbt.rolling_mean(10)  # (2)!
5.33 ms ± 302 µs per loop (mean ± std. dev. of 7 runs, 1 loop each)

>>> %timeit df.vbt.rolling_mean(10, jitted=dict(parallel=True))  # (3)!
1.82 ms ± 5.21 µs per loop (mean ± std. dev. of 7 runs, 1000 loops each)
```

1. Using Pandas.
2. Using Numba without parallelization.
3. Using Numba with parallelization.

## Multithreading

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] Integration of [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor)
from `concurrent.futures`, [ThreadPool](https://pathos.readthedocs.io/en/latest/pathos.html#pathos.pools.ThreadPool)
from `pathos`, and [Dask](https://dask.org/) backend for running multiple chunks across multiple
threads. This is best for speeding up heavyweight functions that release the GIL, such as Numba and C
functions. Multithreading + Chunking + Numba = :muscle:

```pycon title="Benchmark 1000 random portfolios without and with multithreading"
>>> data = vbt.YFData.pull(["BTC-USD", "ETH-USD"])

>>> %timeit vbt.PF.from_random_signals(data.close, n=[100] * 1000)
613 ms ± 37.2 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

>>> %timeit vbt.PF.from_random_signals(data.close, n=[100] * 1000, chunked="threadpool")
294 ms ± 8.91 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

## Multiprocessing

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] Integration of [ProcessPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor)
from `concurrent.futures`, [ProcessPool](https://pathos.readthedocs.io/en/latest/pathos.html#pathos.pools.ProcessPool)
and [ParallelPool](https://pathos.readthedocs.io/en/latest/pathos.html#pathos.pools.ParallelPool) from
`pathos`, [WorkerPool](https://sybrenjansen.github.io/mpire/usage/workerpool/index.html) from
`mpire`, and [Ray](https://www.ray.io/) backend for running multiple chunks across multiple processes.
This is best for speeding up heavyweight functions that do not release the GIL, such as regular Python
functions, as well as lightweight arguments that are easy to serialize. Ever wanted to test billions of
hyperparameter combinations in just a few minutes? Now you can by scaling functions and entire
applications in the cloud using [Ray clusters](https://docs.ray.io/en/latest/cluster/getting-started.html)
:eyes:

```pycon title="Benchmark running a slow function on each column without and with multiprocessing"
>>> @vbt.chunked(
...     size=vbt.ArraySizer(arg_query="items", axis=1),
...     arg_take_spec=dict(
...         items=vbt.ArraySelector(axis=1)
...     ),
...     merge_func=np.column_stack
... )
... def bubble_sort(items):
...     items = items.copy()
...     for i in range(len(items)):
...         for j in range(len(items) - 1 - i):
...             if items[j] > items[j + 1]:
...                 items[j], items[j + 1] = items[j + 1], items[j]
...     return items
                
>>> items = np.random.uniform(size=(1000, 3))

>>> %timeit bubble_sort(items)
456 ms ± 1.36 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

>>> %timeit bubble_sort(items, _execute_kwargs=dict(engine="pathos"))
165 ms ± 1.51 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

## Jitting

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] Jitting stands for just-in-time compiling. In the VBT universe, however, jitting simply
means accelerating. While Numba remains the primary jitter, VBT now allows you to implement
custom jitter classes, such as those for vectorized NumPy or even [JAX](https://github.com/google/jax)
with GPU support. Every jitted function is registered globally, so you can switch between different
implementations or even disable jitting entirely with a single command.

```pycon title="Run different implementations of the cumulative sum"
>>> data = vbt.YFData.pull("BTC-USD", start="7 days ago")
>>> log_returns = np.log1p(data.close.pct_change())
>>> log_returns.vbt.cumsum()  # (1)!
Date
2023-01-31 00:00:00+00:00    0.000000
2023-02-01 00:00:00+00:00    0.024946
2023-02-02 00:00:00+00:00    0.014271
2023-02-03 00:00:00+00:00    0.013310
2023-02-04 00:00:00+00:00    0.008288
2023-02-05 00:00:00+00:00   -0.007967
2023-02-06 00:00:00+00:00   -0.010087
Freq: D, Name: Close, dtype: float64

>>> log_returns.vbt.cumsum(jitted=False)  # (2)!
Date
2023-01-31 00:00:00+00:00    0.000000
2023-02-01 00:00:00+00:00    0.024946
2023-02-02 00:00:00+00:00    0.014271
2023-02-03 00:00:00+00:00    0.013310
2023-02-04 00:00:00+00:00    0.008288
2023-02-05 00:00:00+00:00   -0.007967
2023-02-06 00:00:00+00:00   -0.010087
Freq: D, Name: Close, dtype: float64

>>> @vbt.register_jitted(task_id_or_func=vbt.nb.nancumsum_nb)  # (3)!
... def nancumsum_np(arr):
...     return np.nancumsum(arr, axis=0)

>>> log_returns.vbt.cumsum(jitted="np")  # (4)!
Date
2023-01-31 00:00:00+00:00    0.000000
2023-02-01 00:00:00+00:00    0.024946
2023-02-02 00:00:00+00:00    0.014271
2023-02-03 00:00:00+00:00    0.013310
2023-02-04 00:00:00+00:00    0.008288
2023-02-05 00:00:00+00:00   -0.007967
2023-02-06 00:00:00+00:00   -0.010087
Freq: D, Name: Close, dtype: float64
```

1. Using the built-in Numba-compiled function.
2. Using the built-in function but with Numba disabled → regular Python → slow!
3. Register a NumPy version for the built-in Numba function.
4. Using the NumPy version.

## Caching

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] Caching has been completely reimplemented and is now managed by a central registry.
This enables tracking useful statistics for all cacheable parts of VBT, such as showing the total
cached size in MB. You get full control and transparency :window:

```pycon title="Get the cache statistics after computing the statistics of a random portfolio"
>>> data = vbt.YFData.pull("BTC-USD")
>>> pf = vbt.PF.from_random_signals(data.close, n=5)
>>> _ = pf.stats()

>>> pf.get_ca_setup().get_status_overview(
...     filter_func=lambda setup: setup.caching_enabled,
...     include=["hits", "misses", "total_size"]
... )
                                 hits  misses total_size
object                                                  
portfolio:0.drawdowns               0       1    70.9 kB
portfolio:0.exit_trades             0       1    70.5 kB
portfolio:0.filled_close            6       1    24.3 kB
portfolio:0.init_cash               3       1   32 Bytes
portfolio:0.init_position           0       1   32 Bytes
portfolio:0.init_position_value     0       1   32 Bytes
portfolio:0.init_value              5       1   32 Bytes
portfolio:0.input_value             1       1   32 Bytes
portfolio:0.orders                  9       1    69.7 kB
portfolio:0.total_profit            1       1   32 Bytes
portfolio:0.trades                  0       1    70.5 kB
```

## Hyperfast rolling metrics

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/1_0_0.svg){ loading=lazy }

- [x] Rolling metrics based on returns have been optimized for maximum performance—up to 1000x speedup!

```pycon title="Benchmark the rolling Sortino ratio"
>>> import quantstats as qs

>>> index = vbt.date_range("2020", periods=100000, freq="1min")
>>> returns = pd.Series(np.random.normal(0, 0.001, size=len(index)), index=index)

>>> %timeit qs.stats.rolling_sortino(returns, rolling_period=10)  # (1)!
2.79 s ± 24.8 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

>>> %timeit returns.vbt.returns.rolling_sortino_ratio(window=10)  # (2)!
8.12 ms ± 199 µs per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

1. Using QuantStats.
2. Using VBT.

## And many more...

- [ ] Look forward to more killer features being added every week!

[:material-language-python: Python code](https://vectorbt.pro/pvt_6d1b3986/assets/jupytext/features/performance.py.txt){ .md-button target="blank_" }