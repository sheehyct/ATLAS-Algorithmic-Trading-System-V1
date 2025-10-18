---
title: Portfolio optimization
description: Learn about portfolio optimization in VectorBT PRO
icon: material/chart-bar-stacked
---

# :material-chart-bar-stacked: Portfolio optimization

Portfolio optimization focuses on constructing a portfolio of assets that seeks to maximize returns and
minimize risk. In this context, a portfolio refers to the distribution of an investor's assets—a weight
vector—which can be optimized for risk tolerance, expected rate of return, cost minimization, and other
objectives. This optimization can be performed regularly to reflect recent changes in market behavior.

In VBT, a portfolio is a collection of asset vectors combined into a larger array along the column
axis. By default, each of these vectors is treated as a separate backtesting instance, but you can apply a
grouping instruction to treat multiple assets as a single unit. Portfolio optimization then becomes the
process of converting a set of pricing vectors (information as input) into a set of allocation vectors
(actions as output), which can then be provided to any simulator.

Thanks to VBT's modular design (and in line with the key principles of data science), optimization and
simulation are handled separately. This enables you to analyze and filter allocation vectors even before
they are backtested. This approach is similar to the typical workflow for working with signals: 1)
generate, 2) pre-analyze, 3) simulate, and 4) post-analyze. In this example, we will cover how to complete
each of these steps for the highest informational yield.

## Data

As always, we should begin by obtaining some data. Because portfolio optimization involves working with a
group of assets, we need to fetch data for more than one symbol. Here, we will fetch one year of hourly
data for 5 different cryptocurrencies:

```pycon
>>> from vectorbtpro import *

>>> data = vbt.BinanceData.pull(
...     ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT"], 
...     start="2020-01-01 UTC", 
...     end="2021-01-01 UTC",
...     timeframe="1h"
... )
```

[=100% "Symbol 5/5"]{: .candystripe .candystripe-animate }

[=100% "Period 9/9"]{: .candystripe .candystripe-animate }

Let's save the data locally to avoid re-fetching it every time we start a new runtime:

```pycon
>>> data.to_hdf()

>>> data = vbt.HDFData.pull("BinanceData.h5")
```

## Allocation

In simple terms, asset allocation is the process of deciding where to invest funds in the market—it is a
horizontal vector composed of weights or amounts of assets at a specific timestamp. For example, to
allocate 50% to `BTCUSDT`, 20% to `ETHUSDT`, and distribute the remainder equally among the other assets,
the allocation vector would be `[0.5, 0.2, 0.1, 0.1, 0.1]`. Frequently, weight allocations sum to 1,
ensuring the entire stake is continuously invested, but you can also choose to invest only a portion of
your balance or specify a particular (continuous or discrete) number of assets instead of weights. Since we
generally want to allocate periodically rather than hold positions indefinitely, we also need to decide on
rebalancing timestamps.

### Manually

Let's manually generate and simulate allocations to better understand how everything works together.

#### Index points

The first step is to decide when to re-allocate. This is straightforward using
[ArrayWrapper.get_index_points](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.get_index_points),
which converts a human-readable query into a list of index positions (also called "index points" or
"allocation points"). These positions are simple numeric indices, where `0` is the first row and
`len(index) - 1` is the last.

For example, let's convert the first day of each month into index points:

```pycon
>>> ms_points = data.wrapper.get_index_points(every="M")
>>> ms_points
array([0, 744, 1434, 2177, 2895, 3639, 4356, 5100, 5844, 6564, 7308, 8027])
```

!!! hint
    You can check the indices above using Pandas:
    
    ```pycon
    >>> data.wrapper.index.get_indexer(
    ...     pd.Series(index=data.wrapper.index).resample(vbt.offset("M")).asfreq().index, 
    ...     method="bfill"
    ... )
    array([0, 744, 1434, 2177, 2895, 3639, 4356, 5100, 5844, 6564, 7308, 8027])
    ```

We can also convert these index points back to timestamps:

```pycon
>>> data.wrapper.index[ms_points]
DatetimeIndex(['2020-01-01 00:00:00+00:00', '2020-02-01 00:00:00+00:00',
               '2020-03-01 00:00:00+00:00', '2020-04-01 00:00:00+00:00',
               '2020-05-01 00:00:00+00:00', '2020-06-01 00:00:00+00:00',
               '2020-07-01 00:00:00+00:00', '2020-08-01 00:00:00+00:00',
               '2020-09-01 00:00:00+00:00', '2020-10-01 00:00:00+00:00',
               '2020-11-01 00:00:00+00:00', '2020-12-01 00:00:00+00:00'],
              dtype='datetime64[ns, UTC]', name='Open time', freq=None)
```

!!! note
    [ArrayWrapper.get_index_points](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.get_index_points)
    always returns indices that can be used on the index, unless `skipna` is disabled.
    In that case, it will return `-1` wherever an index point cannot be found.

These are our [rebalancing](https://www.investopedia.com/terms/r/rebalancing.asp) timestamps!

The main advantage of this method is its flexibility. The `every` argument can be a string,
an integer, a `pd.Timedelta` object, or a `pd.DateOffset` object:

```pycon
>>> example_points = data.wrapper.get_index_points(every=24 * 30)  # (1)!
>>> data.wrapper.index[example_points]
DatetimeIndex(['2020-01-01 00:00:00+00:00', '2020-01-31 00:00:00+00:00',
               '2020-03-01 06:00:00+00:00', '2020-03-31 07:00:00+00:00',
               '2020-04-30 09:00:00+00:00', '2020-05-30 09:00:00+00:00',
               '2020-06-29 12:00:00+00:00', '2020-07-29 12:00:00+00:00',
               '2020-08-28 12:00:00+00:00', '2020-09-27 12:00:00+00:00',
               '2020-10-27 12:00:00+00:00', '2020-11-26 12:00:00+00:00',
               '2020-12-26 17:00:00+00:00'],
              dtype='datetime64[ns, UTC]', name='Open time', freq=None)

>>> date_offset = pd.offsets.WeekOfMonth(week=3, weekday=4)
>>> example_points = data.wrapper.get_index_points(  # (2)!
...     every=date_offset, 
...     add_delta=pd.Timedelta(hours=17)
... )
>>> data.wrapper.index[example_points]
DatetimeIndex(['2020-01-24 17:00:00+00:00', '2020-02-28 17:00:00+00:00',
               '2020-03-27 17:00:00+00:00', '2020-04-24 17:00:00+00:00',
               '2020-05-22 17:00:00+00:00', '2020-06-26 17:00:00+00:00',
               '2020-07-24 17:00:00+00:00', '2020-08-28 17:00:00+00:00',
               '2020-09-25 17:00:00+00:00', '2020-10-23 17:00:00+00:00',
               '2020-11-27 17:00:00+00:00', '2020-12-25 17:00:00+00:00'],
              dtype='datetime64[ns, UTC]', name='Open time', freq=None)
```

1. Every 24 * 30 = 1440 hours.
2. At 17:00 on the last Friday of each month.

!!! hint
    Take a look at the [available date offsets](https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#dateoffset-objects).

You can also use `start` and `end` as human-readable strings (thanks to
[dateparser](https://github.com/scrapinghub/dateparser)!), integers, or `pd.Timestamp` objects
to limit the date range as needed:

```pycon
>>> example_points = data.wrapper.get_index_points(
...     start="April 1st 2020",
...     every="M"
... )
>>> data.wrapper.index[example_points]
DatetimeIndex(['2020-04-01 00:00:00+00:00', '2020-05-01 00:00:00+00:00',
               '2020-06-01 00:00:00+00:00', '2020-07-01 00:00:00+00:00',
               '2020-08-01 00:00:00+00:00', '2020-09-01 00:00:00+00:00',
               '2020-10-01 00:00:00+00:00', '2020-11-01 00:00:00+00:00',
               '2020-12-01 00:00:00+00:00'],
              dtype='datetime64[ns, UTC]', name='Open time', freq=None)
```

Another helpful feature is providing your own dates using the `on` argument.
[ArrayWrapper.get_index_points](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.get_index_points)
will match these dates to the index. If any date is not found, it will simply use the next date
(not the previous one, since we should not look into the future):

```pycon
>>> example_points = data.wrapper.get_index_points(
...     on=["April 1st 2020 19:45", "17 September 2020 00:01"]
... )
>>> data.wrapper.index[example_points]
DatetimeIndex([
    '2020-04-01 20:00:00+00:00', 
    '2020-09-17 01:00:00+00:00'
], dtype='datetime64[ns, UTC]', name='Open time', freq=None)
```

But let's continue with the `ms_points` generated earlier.

#### Filling

We now have our allocation index points, so it's time to fill in the actual allocations at these points.
First, let's create an empty DataFrame with symbols as columns:

```pycon
>>> symbol_wrapper = data.get_symbol_wrapper(freq="1h")  # (1)!
>>> filled_allocations = symbol_wrapper.fill()  # (2)!
>>> filled_allocations
symbol                     ADAUSDT  BNBUSDT  BTCUSDT  ETHUSDT  XRPUSDT
Open time                                                             
2020-01-01 00:00:00+00:00      NaN      NaN      NaN      NaN      NaN
2020-01-01 01:00:00+00:00      NaN      NaN      NaN      NaN      NaN
2020-01-01 02:00:00+00:00      NaN      NaN      NaN      NaN      NaN
...                            ...      ...      ...      ...      ...
2020-12-31 21:00:00+00:00      NaN      NaN      NaN      NaN      NaN
2020-12-31 22:00:00+00:00      NaN      NaN      NaN      NaN      NaN
2020-12-31 23:00:00+00:00      NaN      NaN      NaN      NaN      NaN

[8767 rows x 5 columns]
```

1. Using [Data.get_symbol_wrapper](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.get_symbol_wrapper).
2. Using [ArrayWrapper.fill](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.fill).

Next, we need to generate allocations and assign them at their index points. In this example,
we will create allocations randomly:

```pycon
>>> np.random.seed(42)  # (1)!

>>> def random_allocate_func():
...     weights = np.random.uniform(size=symbol_wrapper.shape[1])
...     return weights / weights.sum()  # (2)!

>>> for idx in ms_points:
...     filled_allocations.iloc[idx] = random_allocate_func()

>>> allocations = filled_allocations[~filled_allocations.isnull().any(axis=1)]
>>> allocations
symbol                      ADAUSDT   BNBUSDT   BTCUSDT   ETHUSDT   XRPUSDT
Open time                                                                  
2020-01-01 00:00:00+00:00  0.133197  0.338101  0.260318  0.212900  0.055485
2020-02-01 00:00:00+00:00  0.065285  0.024308  0.362501  0.251571  0.296334
2020-03-01 00:00:00+00:00  0.009284  0.437468  0.375464  0.095773  0.082010
2020-04-01 00:00:00+00:00  0.105673  0.175297  0.302353  0.248877  0.167800
2020-05-01 00:00:00+00:00  0.327909  0.074759  0.156568  0.196343  0.244421
2020-06-01 00:00:00+00:00  0.367257  0.093395  0.240527  0.277095  0.021727
2020-07-01 00:00:00+00:00  0.220313  0.061837  0.023590  0.344094  0.350166
2020-08-01 00:00:00+00:00  0.346199  0.130452  0.041828  0.293025  0.188497
2020-09-01 00:00:00+00:00  0.067065  0.272119  0.018898  0.499708  0.142210
2020-10-01 00:00:00+00:00  0.297647  0.140040  0.233647  0.245617  0.083048
2020-11-01 00:00:00+00:00  0.232128  0.185574  0.224925  0.214230  0.143143
2020-12-01 00:00:00+00:00  0.584609  0.056118  0.124283  0.028681  0.206309
```

1. Set the random seed to make the results reproducible.
2. Divide by the sum to ensure the weights add up to 1.

That's it! We can now use these weight vectors for simulation.

#### Simulation

The simulation step is simple: use the filled allocations as the size for the target percentage type,
enable grouping with cash sharing, and use a dynamic call sequence.

```pycon
>>> pf = vbt.Portfolio.from_orders(
...     close=data.get("Close"),
...     size=filled_allocations,
...     size_type="targetpercent",
...     group_by=True,  # (1)!
...     cash_sharing=True,
...     call_seq="auto"  # (2)!
... )
```

1. Change this if you have multiple groups.
2. Selling before buying is important!

We can extract the actual allocations produced by the simulation:

```pycon
>>> sim_alloc = pf.get_asset_value(group_by=False).vbt / pf.value
>>> sim_alloc  # (1)!
symbol                      ADAUSDT   BNBUSDT   BTCUSDT   ETHUSDT   XRPUSDT
Open time                                                                  
2020-01-01 00:00:00+00:00  0.133197  0.338101  0.260318  0.212900  0.055485
2020-01-01 01:00:00+00:00  0.132979  0.337881  0.259649  0.214099  0.055393
2020-01-01 02:00:00+00:00  0.133259  0.337934  0.259737  0.213728  0.055342
...                             ...       ...       ...       ...       ...
2020-12-31 21:00:00+00:00  0.636496  0.067686  0.188081  0.035737  0.072000
2020-12-31 22:00:00+00:00  0.634586  0.068128  0.189404  0.035930  0.071952
2020-12-31 23:00:00+00:00  0.638154  0.068205  0.187649  0.035619  0.070373

[8766 rows x 5 columns]
```

1. You can also return this using `pf.allocations`.

We can plot the allocations manually:

```pycon
>>> sim_alloc.vbt.plot(
...    trace_kwargs=dict(stackgroup="one"),
...    use_gl=False
... ).show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/actual_allocations.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/actual_allocations.dark.svg#only-dark){: .iimg loading=lazy }

Or use [Portfolio.plot_allocations](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.plot_allocations):

```pycon
>>> pf.plot_allocations().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/plot_allocations.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/plot_allocations.dark.svg#only-dark){: .iimg loading=lazy }

Without transaction costs such as commissions and slippage, the source and target allocations should
closely match at the allocation points:

```pycon
>>> np.isclose(allocations, sim_alloc.iloc[ms_points])
array([[ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True],
       [ True,  True,  True,  True,  True]])
```

### Allocation method

We have learned how to manually generate, fill, and simulate allocations. But VBT would not
be VBT if it did not provide a convenient function for this! This is where
[PortfolioOptimizer](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer)
comes into play: it offers various class methods for generating allocations.
The workings of this class are quite straightforward (despite the complex implementation): it generates
allocations and stores them in a compressed form for later analysis and simulation.

The allocation generation is managed by the class method
[PortfolioOptimizer.from_allocate_func](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_allocate_func).
If you review the documentation for this method, you will notice that it takes the same arguments as
[ArrayWrapper.get_index_points](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.get_index_points)
to generate index points. Then, at each of these points, it calls a user-defined allocation
function `allocate_func` to produce an allocation vector. Finally, all the returned vectors are concatenated
into a single two-dimensional NumPy array, while the index points are stored in a separate structured NumPy
array of type [AllocPoints](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/records/#vectorbtpro.portfolio.pfopt.records.AllocPoints).

Let's apply the optimizer class to `random_allocate_func`:

```pycon
>>> np.random.seed(42)

>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,  # (1)!
...     random_allocate_func,
...     every="M"  # (2)!
... )
```

1. The wrapper must contain symbols as columns.
2. If you do not provide a frequency, the function will be called at every date.

[=100% "Allocation 12/12"]{: .candystripe .candystripe-animate }

!!! hint
    There is also a convenient method [PortfolioOptimizer.from_random](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_random)
    to generate random allocations. Give it a try!

Now, let's look at the generated random allocations:

```pycon
>>> pfo.allocations  # (1)!
symbol                      ADAUSDT   BNBUSDT   BTCUSDT   ETHUSDT   XRPUSDT
Open time                                                                  
2020-01-01 00:00:00+00:00  0.133197  0.338101  0.260318  0.212900  0.055485
2020-02-01 00:00:00+00:00  0.065285  0.024308  0.362501  0.251571  0.296334
2020-03-01 00:00:00+00:00  0.009284  0.437468  0.375464  0.095773  0.082010
2020-04-01 00:00:00+00:00  0.105673  0.175297  0.302353  0.248877  0.167800
2020-05-01 00:00:00+00:00  0.327909  0.074759  0.156568  0.196343  0.244421
2020-06-01 00:00:00+00:00  0.367257  0.093395  0.240527  0.277095  0.021727
2020-07-01 00:00:00+00:00  0.220313  0.061837  0.023590  0.344094  0.350166
2020-08-01 00:00:00+00:00  0.346199  0.130452  0.041828  0.293025  0.188497
2020-09-01 00:00:00+00:00  0.067065  0.272119  0.018898  0.499708  0.142210
2020-10-01 00:00:00+00:00  0.297647  0.140040  0.233647  0.245617  0.083048
2020-11-01 00:00:00+00:00  0.232128  0.185574  0.224925  0.214230  0.143143
2020-12-01 00:00:00+00:00  0.584609  0.056118  0.124283  0.028681  0.206309
```

1. See [PortfolioOptimizer.get_allocations](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.get_allocations).

We can also fill the entire array so it can be used in simulation:

```pycon
>>> pfo.filled_allocations  # (1)!
symbol                      ADAUSDT   BNBUSDT   BTCUSDT  ETHUSDT   XRPUSDT
Open time                                                                 
2020-01-01 00:00:00+00:00  0.133197  0.338101  0.260318   0.2129  0.055485
2020-01-01 01:00:00+00:00       NaN       NaN       NaN      NaN       NaN
2020-01-01 02:00:00+00:00       NaN       NaN       NaN      NaN       NaN
2020-01-01 03:00:00+00:00       NaN       NaN       NaN      NaN       NaN
...                             ...       ...       ...      ...       ...
2020-12-31 21:00:00+00:00       NaN       NaN       NaN      NaN       NaN
2020-12-31 22:00:00+00:00       NaN       NaN       NaN      NaN       NaN
2020-12-31 23:00:00+00:00       NaN       NaN       NaN      NaN       NaN

[8767 rows x 5 columns]
```

1. See [PortfolioOptimizer.fill_allocations](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.fill_allocations).

!!! note
    A row filled with NaN values means there is no allocation at that timestamp.

Since an instance of [PortfolioOptimizer](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer)
stores not only the allocation vectors but also the index points themselves, you can access them
using [PortfolioOptimizer.alloc_records](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.alloc_records)
and analyze them like regular records:

```pycon
>>> pfo.alloc_records.records_readable
    Id  Group          Allocation Index
0    0  group 2020-01-01 00:00:00+00:00
1    1  group 2020-02-01 00:00:00+00:00
2    2  group 2020-03-01 00:00:00+00:00
3    3  group 2020-04-01 00:00:00+00:00
4    4  group 2020-05-01 00:00:00+00:00
5    5  group 2020-06-01 00:00:00+00:00
6    6  group 2020-07-01 00:00:00+00:00
7    7  group 2020-08-01 00:00:00+00:00
8    8  group 2020-09-01 00:00:00+00:00
9    9  group 2020-10-01 00:00:00+00:00
10  10  group 2020-11-01 00:00:00+00:00
11  11  group 2020-12-01 00:00:00+00:00
```

The allocations can be plotted easily using
[PortfolioOptimizer.plot](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.plot):

```pycon
>>> pfo.plot().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/optimizer.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/optimizer.dark.svg#only-dark){: .iimg loading=lazy }

Since [PortfolioOptimizer](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer)
is a subclass of [Analyzable](https://vectorbt.pro/pvt_6d1b3986/api/generic/analyzable/#vectorbtpro.generic.analyzable.Analyzable),
we can generate statistics to describe the optimizer's current state:

```pycon
>>> pfo.stats()
Start                       2020-01-01 00:00:00+00:00
End                         2020-12-31 23:00:00+00:00
Period                              365 days 06:00:00
Total Records                                      12
Mean Allocation: ADAUSDT                     0.229714
Mean Allocation: BNBUSDT                     0.165789
Mean Allocation: BTCUSDT                     0.197075
Mean Allocation: ETHUSDT                     0.242326
Mean Allocation: XRPUSDT                     0.165096
Name: group, dtype: object
```

What about simulation? [Portfolio](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio)
includes a dedicated class method for this purpose:
[Portfolio.from_optimizer](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from_optimizer).

```pycon
>>> pf = vbt.Portfolio.from_optimizer(data, pfo, freq="1h")

>>> pf.sharpe_ratio
2.097991099869708
```

Alternatively, you can run the simulation directly from the portfolio optimizer:

```pycon
>>> pf = pfo.simulate(data, freq="1h")

>>> pf.sharpe_ratio
2.097991099869708
```

As we can see, VBT continues its modular approach to keep individual backtesting components
as independent as possible while maintaining coherence. Instead of defining all the logic within
a single backtesting module, you can divide the workflow into a set of logically separate,
isolated components, each of which can be maintained independently.

#### Once

To allocate once, you can use [PortfolioOptimizer.from_allocate_func](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_allocate_func)
with `on=0`, or use [PortfolioOptimizer.from_initial](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_initial):

=== "from_allocate_func"

    ```pycon
    >>> def const_allocate_func(target_alloc):
    ...     return target_alloc

    >>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
    ...     symbol_wrapper,
    ...     const_allocate_func,
    ...     [0.5, 0.2, 0.1, 0.1, 0.1],
    ...     on=0
    ... )

    >>> pfo.plot().show()
    ```

=== "from_initial"

    ```pycon
    >>> pfo = vbt.PortfolioOptimizer.from_initial(
    ...     symbol_wrapper,
    ...     [0.5, 0.2, 0.1, 0.1, 0.1]
    ... )

    >>> pfo.plot().show()
    ```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/once.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/once.dark.svg#only-dark){: .iimg loading=lazy }

!!! note
    Even if the lines appear straight on the chart, this does not mean rebalancing happens at each
    timestamp. This effect is mainly due to VBT forward-filling the allocation. In reality,
    the initial allocation is preserved at the first timestamp, and then it typically begins to
    change. That's why periodic or threshold rebalancing is required to maintain the allocation
    over the entire period.

#### Custom array

If you already have an array with allocations in either compressed or filled form,
you can use [PortfolioOptimizer.from_allocations](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_allocations)
and [PortfolioOptimizer.from_filled_allocations](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_filled_allocations)
respectively.

Let's create a compressed array with custom allocations for each quarter:

```pycon
>>> custom_index = vbt.date_range("2020-01-01", "2021-01-01", freq="Q")
>>> custom_allocations = pd.DataFrame(
...     [
...         [0.5, 0.2, 0.1, 0.1, 0.1],
...         [0.1, 0.5, 0.2, 0.1, 0.1],
...         [0.1, 0.1, 0.5, 0.2, 0.1],
...         [0.1, 0.1, 0.1, 0.5, 0.2]
...     ],
...     index=custom_index,
...     columns=symbol_wrapper.columns
... )
```

When you pass a DataFrame, VBT automatically uses its index as the `on` argument
to apply allocations at those (or next) timestamps in the original index:

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_allocations(
...     symbol_wrapper,
...     custom_allocations
... )
>>> pfo.allocations
symbol                     ADAUSDT  BNBUSDT  BTCUSDT  ETHUSDT  XRPUSDT
Open time
2020-01-01 00:00:00+00:00      0.5      0.2      0.1      0.1      0.1
2020-04-01 00:00:00+00:00      0.1      0.5      0.2      0.1      0.1
2020-07-01 00:00:00+00:00      0.1      0.1      0.5      0.2      0.1
2020-10-01 00:00:00+00:00      0.1      0.1      0.1      0.5      0.2
```

However, if you pass a NumPy array, VBT will not be able to parse the dates,
so you must specify the index points manually:

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_allocations(
...     symbol_wrapper,
...     custom_allocations.values,
...     start="2020-01-01",
...     end="2021-01-01",
...     every="Q"
... )
>>> pfo.allocations
symbol                     ADAUSDT  BNBUSDT  BTCUSDT  ETHUSDT  XRPUSDT
Open time
2020-01-01 00:00:00+00:00      0.5      0.2      0.1      0.1      0.1
2020-04-01 00:00:00+00:00      0.1      0.5      0.2      0.1      0.1
2020-07-01 00:00:00+00:00      0.1      0.1      0.5      0.2      0.1
2020-10-01 00:00:00+00:00      0.1      0.1      0.1      0.5      0.2
```

You can also use allocations that have already been filled as input. In this case, you do not
even need to provide a wrapper. Vectorbt will extract the necessary information from the DataFrame
itself. Filled allocations are handled by treating any row where all values are NaN as empty.
Let's use the filled allocations from the previous optimizer as input to another optimizer:

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_filled_allocations(
...     pfo.fill_allocations()
... )
>>> pfo.allocations
symbol                     ADAUSDT  BNBUSDT  BTCUSDT  ETHUSDT  XRPUSDT
Open time
2020-01-01 00:00:00+00:00      0.5      0.2      0.1      0.1      0.1
2020-04-01 00:00:00+00:00      0.1      0.5      0.2      0.1      0.1
2020-07-01 00:00:00+00:00      0.1      0.1      0.5      0.2      0.1
2020-10-01 00:00:00+00:00      0.1      0.1      0.1      0.5      0.2
```

!!! hint
    You can re-run this cell as many times as you like. There is no information loss!

#### Templates

What if you want to use more complex allocation functions that require passing arguments?
One of the coolest features of VBT is templates, which act as a sort of callback.
With templates, you can instruct VBT to run small code snippets at various execution points,
typically whenever new information becomes available.

When a new index point is processed by [PortfolioOptimizer.from_allocate_func](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_allocate_func),
VBT substitutes all templates found in `*args` and `**kwargs` using the current context
and passes them to the allocation function. The template context includes all arguments given
to the class method, plus the generated index points (`index_points`), the current iteration
index (`i`), and the specific index point (`index_point`).

To make our example more interesting, let's rotate and allocate 100% to one asset at a time:

```pycon
>>> def rotation_allocate_func(wrapper, i):
...     weights = np.full(len(wrapper.columns), 0)
...     weights[i % len(wrapper.columns)] = 1
...     return weights

>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     rotation_allocate_func,
...     vbt.Rep("wrapper"),  # (1)!
...     vbt.Rep("i"),
...     every="M"
... )

>>> pfo.plot().show()
```

1. Replace the first and second variable arguments with the wrapper and iteration index, respectively.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/templates.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/templates.dark.svg#only-dark){: .iimg loading=lazy }

You can also use evaluation templates to accomplish the same task:

```pycon
>>> def rotation_allocate_func(symbols, chosen_symbol):
...     return {s: 1 if s == chosen_symbol else 0 for s in symbols}

>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     rotation_allocate_func,
...     vbt.RepEval("wrapper.columns"),  # (1)!
...     vbt.RepEval("wrapper.columns[i % len(wrapper.columns)]"),
...     every="M"
... )

>>> pfo.allocations
symbol                     ADAUSDT  BNBUSDT  BTCUSDT  ETHUSDT  XRPUSDT
Open time
2020-01-01 00:00:00+00:00        1        0        0        0        0
2020-02-01 00:00:00+00:00        0        1        0        0        0
2020-03-01 00:00:00+00:00        0        0        1        0        0
2020-04-01 00:00:00+00:00        0        0        0        1        0
2020-05-01 00:00:00+00:00        0        0        0        0        1
2020-06-01 00:00:00+00:00        1        0        0        0        0
2020-07-01 00:00:00+00:00        0        1        0        0        0
2020-08-01 00:00:00+00:00        0        0        1        0        0
2020-09-01 00:00:00+00:00        0        0        0        1        0
2020-10-01 00:00:00+00:00        0        0        0        0        1
2020-11-01 00:00:00+00:00        1        0        0        0        0
2020-12-01 00:00:00+00:00        0        1        0        0        0
```

1. Evaluate these expressions and use them as arguments for the function.

!!! hint
    The allocation function can return a sequence of values (one per asset), a dictionary (with assets as
    keys), or even a Pandas Series (with assets as the index). In other words, it can return anything
    that can be packed into a list and used as input for a DataFrame. If any asset key is not provided,
    its allocation will be NaN.

#### Groups

Testing a single combination of parameters can be boring, so VBT provides two different
features for parameter combinations: arguments wrapped with the [Param](https://vectorbt.pro/pvt_6d1b3986/api/utils/params/#vectorbtpro.utils.params.Param)
class and group configs. The idea behind the former is similar to what you may have seen in
[broadcast](https://vectorbt.pro/pvt_6d1b3986/api/base/reshaping/#vectorbtpro.base.reshaping.broadcast): wrap a sequence of
values with this class to combine the argument with other arguments or similar parameters.
Let's implement constant-weight asset allocation with various rebalancing intervals:

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     const_allocate_func,
...     [0.5, 0.2, 0.1, 0.1, 0.1],
...     every=vbt.Param(["1M", "2M", "3M"])  # (1)!
... )

>>> pf = pfo.simulate(data, freq="1h")
>>> pf.total_return
every
1M    3.716574
2M    3.435540
3M    3.516401
Name: total_return, dtype: float64
```

1. Create three groups: rebalance monthly, once every two months, and once every three months.

!!! hint
    To hide the progress bar, pass `execute_kwargs=dict(show_progress=False)`.

As you can see, VBT recognizes that the `every` argument is a parameter, so it creates
a column level named after the argument and puts it on top of the symbol columns.

Now, let's define another parameter for weights:

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     const_allocate_func,
...     vbt.Param([
...         [0.5, 0.2, 0.1, 0.1, 0.1],
...         [0.2, 0.1, 0.1, 0.1, 0.5]
...     ], keys=pd.Index(["w1", "w2"], name="weights")),  # (1)!
...     every=vbt.Param(["1M", "2M", "3M"])
... )
```

1. Set a custom name for the parameter in the final column index.

This code produces 6 parameter combinations (groups):

```pycon
>>> pfo.wrapper.grouper.get_index()
MultiIndex([('1M', 'w1'),
            ('1M', 'w2'),
            ('2M', 'w1'),
            ('2M', 'w2'),
            ('3M', 'w1'),
            ('3M', 'w2')],
           names=['every', 'weights'])
```

And applies each combination to the asset columns:

```pycon
>>> pfo.wrapper.columns
MultiIndex([('1M', 'w1', 'ADAUSDT'),
            ('1M', 'w1', 'BNBUSDT'),
            ('1M', 'w1', 'BTCUSDT'),
            ...
            ('3M', 'w2', 'BTCUSDT'),
            ('3M', 'w2', 'ETHUSDT'),
            ('3M', 'w2', 'XRPUSDT')],
           names=['every', 'weights', 'symbol'])
```

To select or plot the allocations for any parameter combination,
you can use Pandas-like indexing **on groups**:

```pycon
>>> pfo[("3M", "w2")].stats()
Start                       2020-01-01 00:00:00+00:00
End                         2020-12-31 23:00:00+00:00
Period                              365 days 06:00:00
Total Records                                       4
Mean Allocation: ADAUSDT                          0.2
Mean Allocation: BNBUSDT                          0.1
Mean Allocation: BTCUSDT                          0.1
Mean Allocation: ETHUSDT                          0.1
Mean Allocation: XRPUSDT                          0.5
Name: (3M, w2), dtype: object
```

!!! note
    When plotting, instead of indexing, you can pass a group name or tuple using the `column` argument.

But what if you have more complex groups? Representing everything with parameters can become
cumbersome when arguments barely overlap. Fortunately, you can use the `group_configs` argument
to pass a list of dictionaries, each representing a group and defining its arguments.
Let's use this method for the example above:

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     const_allocate_func,
...     group_configs=[
...         dict(args=([0.5, 0.2, 0.1, 0.1, 0.1],), every="1M"),
...         dict(args=([0.2, 0.1, 0.1, 0.1, 0.5],), every="2M"),
...         dict(args=([0.1, 0.1, 0.1, 0.5, 0.2],), every="3M"),
...         dict(args=([0.1, 0.1, 0.5, 0.2, 0.1],), every="1M"),
...         dict(args=([0.1, 0.5, 0.2, 0.1, 0.1],), every="2M"),
...         dict(args=([0.5, 0.2, 0.1, 0.1, 0.1],), every="3M"),
...     ]
... )
pfo.wrapper.grouper.get_index()
Int64Index([0, 1, 2, 3, 4, 5], dtype='int64', name='group_config')
```

Unlike the previous example, where VBT created two column levels for the parameters, this
produces only one, where each number is the index of a group config. Now, let's make it more fun
by creating one group with a constant allocation and another group with a random allocation!

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     const_allocate_func,
...     group_configs=[
...         dict(
...             allocate_func=const_allocate_func, 
...             args=([0.5, 0.2, 0.1, 0.1, 0.1],),
...             _name="const"  # (1)!
...         ),
...         dict(
...             allocate_func=random_allocate_func,
...             every="M",
...             _name="random"
...         ),
...     ]
... )
>>> pfo.wrapper.grouper.get_index()
Index(['const', 'random'], dtype='object', name='group_config')
```

1. Assign a name to the config with the reserved key `_name`.

You can also combine [Param](https://vectorbt.pro/pvt_6d1b3986/api/utils/params/#vectorbtpro.utils.params.Param) instances and
group configs for maximum flexibility:

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     const_allocate_func,
...     group_configs={  # (1)!
...         "const": dict(
...             allocate_func=const_allocate_func, 
...             args=([0.5, 0.2, 0.1, 0.1, 0.1],)
...         ),
...         "random": dict(
...             allocate_func=random_allocate_func,
...         ),
...     },
...     every=vbt.Param(["1M", "2M", "3M"])  # (2)!
... )
>>> pfo.wrapper.grouper.get_index()
MultiIndex([('1M',  'const'),
            ('1M', 'random'),
            ('2M',  'const'),
            ('2M', 'random'),
            ('3M',  'const'),
            ('3M', 'random')],
           names=['every', 'group_config'])
```

1. You can also provide group configs as a dictionary with configuration names as keys.
2. Make sure that any parameterized argument is not redefined in any group config.

!!! info
    The column levels for parameters are always placed above those for group configs.

#### Numba

By default, VBT iterates over index points with a standard Python for-loop. This has almost
no effect on performance if the number of allocations is low, which is typical in portfolio
optimization. This is because running the allocation function itself takes much longer than a
single loop iteration. However, when the number of iterations reaches tens of thousands,
it may be worth using Numba for iteration.

To enable Numba, set `jitted_loop` to True. In this case, index points are iterated using
[allocate_meta_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/nb/#vectorbtpro.portfolio.pfopt.nb.allocate_meta_nb),
which passes the current iteration index, the current index point, and `*args`.

!!! note
    Variable keyword arguments are not supported by Numba yet.

Let's implement the rotation example with Numba, rebalancing every day:

```pycon
>>> @njit
... def rotation_allocate_func_nb(i, idx, n_cols):
...     weights = np.full(n_cols, 0)
...     weights[i % n_cols] = 1
...     return weights

>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     rotation_allocate_func_nb,
...     vbt.RepEval("len(wrapper.columns)"),
...     every="D",
...     jitted_loop=True
... )

>>> pfo.allocations.head()
symbol                     ADAUSDT  BNBUSDT  BTCUSDT  ETHUSDT  XRPUSDT
Open time
2020-01-05 00:00:00+00:00      1.0      0.0      0.0      0.0      0.0
2020-01-12 00:00:00+00:00      0.0      1.0      0.0      0.0      0.0
2020-01-19 00:00:00+00:00      0.0      0.0      1.0      0.0      0.0
2020-01-26 00:00:00+00:00      0.0      0.0      0.0      1.0      0.0
2020-02-02 00:00:00+00:00      0.0      0.0      0.0      0.0      1.0
```

#### Distribution

For the best performance, you can also run the allocation function in a distributed way,
as long as each function call does not depend on previous calls. This is only an issue if you
are storing state in a custom variable.

If the jitted loop is disabled, VBT sends all iterations to the
[execute](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute) function, which is
VBT's in-house execution infrastructure. This works much like how indicator parameter
combinations are distributed. In fact, the same argument `execute_kwargs` is available to
control execution.

Let's disable the jitted loop and pass all arguments required by our Numba-compiled function
`rotation_allocate_func_nb` using templates (since the function is not called by
[allocate_meta_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/nb/#vectorbtpro.portfolio.pfopt.nb.allocate_meta_nb)
anymore!):

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     rotation_allocate_func_nb,
...     vbt.Rep("i"),
...     vbt.Rep("index_point"),
...     vbt.RepEval("len(wrapper.columns)"),
...     every="D",
...     execute_kwargs=dict(engine="dask")
... )

>>> pfo.allocations.head()
symbol                     ADAUSDT  BNBUSDT  BTCUSDT  ETHUSDT  XRPUSDT
Open time
2020-01-01 00:00:00+00:00        1        0        0        0        0
2020-01-02 00:00:00+00:00        0        1        0        0        0
2020-01-03 00:00:00+00:00        0        0        1        0        0
2020-01-04 00:00:00+00:00        0        0        0        1        0
2020-01-05 00:00:00+00:00        0        0        0        0        1
```

There is another great option for distributing the allocation process: enable
the jitted loop with [allocate_meta_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/nb/#vectorbtpro.portfolio.pfopt.nb.allocate_meta_nb)
and use chunking. This way, you can split index points into chunks and iterate over each chunk
entirely within Numba. Control chunking with the `chunked` argument, which is resolved and
passed to [chunked](https://vectorbt.pro/pvt_6d1b3986/api/utils/chunking/#vectorbtpro.utils.chunking.chunked).
Just remember to supply a chunking specification for all extra arguments required by the allocation
function:

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     rotation_allocate_func_nb,
...     vbt.RepEval("len(wrapper.columns)"),
...     every="D",
...     jitted_loop=True,
...     chunked=dict(
...         arg_take_spec=dict(args=vbt.ArgsTaker(None)),  # (1)!
...         engine="dask"
...     )
... )
symbol                     ADAUSDT  BNBUSDT  BTCUSDT  ETHUSDT  XRPUSDT
Open time
2020-01-01 00:00:00+00:00      1.0      0.0      0.0      0.0      0.0
2020-01-02 00:00:00+00:00      0.0      1.0      0.0      0.0      0.0
2020-01-03 00:00:00+00:00      0.0      0.0      1.0      0.0      0.0
2020-01-04 00:00:00+00:00      0.0      0.0      0.0      1.0      0.0
2020-01-05 00:00:00+00:00      0.0      0.0      0.0      0.0      1.0
```

1. The argument `n_cols` used by `rotation_allocate_func_nb` is passed as the first argument through `*args`
to [allocate_meta_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/nb/#vectorbtpro.portfolio.pfopt.nb.allocate_meta_nb).
This is why we use [ArgsTaker](https://vectorbt.pro/pvt_6d1b3986/api/utils/chunking/#vectorbtpro.utils.chunking.ArgsTaker) to specify
that the first argument should not be split in any way (since we are chunking rows, not columns).
Otherwise, a warning will be triggered.

If you are not tired of all these distribution options, here is another one: parallelize the iteration
internally with Numba. This can be done with the `jitted` argument, which is resolved and passed
to the `@njit` decorator of [allocate_meta_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/nb/#vectorbtpro.portfolio.pfopt.nb.allocate_meta_nb):

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     rotation_allocate_func_nb,
...     vbt.RepEval("len(wrapper.columns)"),
...     every="D",
...     jitted_loop=True,
...     jitted=dict(parallel=True)
... )

>>> pfo.allocations.head()
symbol                     ADAUSDT  BNBUSDT  BTCUSDT  ETHUSDT  XRPUSDT
Open time
2020-01-01 00:00:00+00:00      1.0      0.0      0.0      0.0      0.0
2020-01-02 00:00:00+00:00      0.0      1.0      0.0      0.0      0.0
2020-01-03 00:00:00+00:00      0.0      0.0      1.0      0.0      0.0
2020-01-04 00:00:00+00:00      0.0      0.0      0.0      1.0      0.0
2020-01-05 00:00:00+00:00      0.0      0.0      0.0      0.0      1.0
```

#### Previous allocation

To access the allocation created in the previous step, you must disable all distribution (in other words,
run the allocation function serially) and use a temporary list or another container
to store all generated allocations. Each time the allocation function is called, it will generate
a new allocation and save it in the container, making it accessible for the next step.
Let's slightly randomize each previous allocation to create a new one:

```pycon
>>> def randomize_prev_allocate_func(i, allocations, mean, std):
...     if i == 0:
...         return allocations[0]  # (1)!
...     prev_allocation = allocations[-1]  # (2)!
...     log_returns = np.random.normal(mean, std, size=len(prev_allocation))  # (3)!
...     returns = np.exp(log_returns) - 1  # (4)!
...     new_allocation = prev_allocation * (1 + returns)  # (5)!
...     new_allocation = new_allocation / new_allocation.sum()  # (6)!
...     allocations.append(new_allocation)  # (7)!
...     return new_allocation

>>> np.random.seed(42)

>>> n_symbols = len(symbol_wrapper.columns)
>>> init_allocation = np.full(n_symbols, 1 / n_symbols)
>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     randomize_prev_allocate_func,
...     i=vbt.Rep("i"),  # (8)!
...     allocations=[init_allocation],  # (9)!
...     mean=0,
...     std=0.5,
...     every="W",
...     start=0,  # (10)!
...     exact_start=True
... )

>>> pfo.plot().show()
```

1. Use the initial allocation at the very first step.
2. For later steps, access the last allocation in the list.
3. Sample random log returns from a normal distribution using the provided parameters.
4. Convert the log returns to simple returns.
5. Apply the simple returns to the previous allocation.
6. Make sure the new allocation sums to 1.
7. Add the new allocation to the list to use at the next step.
8. Instruct VBT to pass the iteration number as `i`.
9. Create a list to be shared among function calls.
10. Start exactly from the first timestamp to use the initial allocation.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/prev_allocation.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/prev_allocation.dark.svg#only-dark){: .iimg loading=lazy }

#### Current allocation

Now that you know how to access the previous allocation, how do you get the current (updated) allocation,
since it has changed over time? You can simply forward-simulate it!

```pycon
>>> def current_allocate_func(price, index_point, alloc_info):
...     prev_alloc_info = alloc_info[-1]
...     prev_index_point = prev_alloc_info["index_point"]
...     prev_allocation = prev_alloc_info["allocation"]
...     if prev_index_point is None:
...         current_allocation = prev_allocation
...     else:
...         prev_price_period = price.iloc[prev_index_point:index_point]  # (1)!
...         prev_pfo = vbt.PFO.from_initial(prev_price_period.vbt.wrapper, prev_allocation)  # (2)!
...         prev_pf = prev_pfo.simulate(prev_price_period)
...         current_allocation = prev_pf.allocations.iloc[-1]  # (3)!
...     alloc_info.append(dict(  # (4)!
...         index_point=index_point,
...         allocation=current_allocation,
...     ))
...     return current_allocation

>>> n_symbols = len(symbol_wrapper.columns)
>>> init_allocation = np.full(n_symbols, 1 / n_symbols)
>>> pfo = vbt.PortfolioOptimizer.from_allocate_func(
...     symbol_wrapper,
...     current_allocate_func,
...     price=data.get("Close"),
...     index_point=vbt.Rep("index_point"),
...     alloc_info=[dict(index_point=None, allocation=init_allocation)],  # (5)!
...     every="W",
...     start=0,
...     exact_start=True
... )
>>> pfo.plot().show()
```

1. Select the prices for the period between the previous step (inclusive) and the current step (exclusive).
2. Create a smaller optimizer that starts from the previous allocation and simulates it for that period.
3. The last allocation in the simulated portfolio is the current allocation.
4. Add the current allocation and its index to the list for the next step.
5. Tip: If you want to access this list later, define it as a separate variable.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/current_allocation.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/current_allocation.dark.svg#only-dark){: .iimg loading=lazy }

The code above accesses the previous allocation, simulates the forward return, and then uses
the last allocation of the simulated portfolio as the new one. This is equivalent to simulating
only the initial allocation :sparkles:

```pycon
>>> init_pfo = vbt.PFO.from_initial(symbol_wrapper, init_allocation)
>>> continuous_pf = pfo.simulate(data.get("Close"))
>>> index_points = symbol_wrapper.get_index_points(every="W", start=0, exact_start=True)
>>> discrete_pfo = vbt.PFO.from_allocations(symbol_wrapper, continuous_pf.allocations.iloc[index_points])
>>> discrete_pfo.plot().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/current_allocation.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/current_allocation.dark.svg#only-dark){: .iimg loading=lazy }

## Optimization

Periodic allocation can be useful, but it offers somewhat limited capabilities compared to what is possible.
Consider a common scenario where you want to rebalance based on a data window instead of just at fixed
points in time. If you use an allocation function, you would need to track either the previous allocation
or the lookback period. To make this process easier, VBT provides an "optimization" function that
operates over a range of timestamps.

### Index ranges

Like index points, index ranges are collections of indices, but each element represents a range of
indices instead of a single point. In VBT, index ranges are usually represented by a
two-dimensional NumPy array, where the first column contains the range start indices (inclusive), and
the second column contains the range end indices (exclusive). Just as we used
[ArrayWrapper.get_index_points](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.get_index_points) to
turn human-readable queries into arrays of indices, we can use
[ArrayWrapper.get_index_ranges](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.get_index_ranges)
to create similar queries for index ranges.

Let's demonstrate how to use this method by dividing the entire period into monthly ranges:

```pycon
>>> example_ranges = data.wrapper.get_index_ranges(every="M")
>>> example_ranges[0]
array([0, 744, 1434, 2177, 2895, 3639, 4356, 5100, 5844, 6564, 7308])

>>> example_ranges[1]
array([744, 1434, 2177, 2895, 3639, 4356, 5100, 5844, 6564, 7308, 8027])
```

Here's what happened: VBT created a new datetime index with a monthly frequency and generated a
range from each pair of values in that index.

To convert each index range back to timestamps:

```pycon
>>> data.wrapper.index[example_ranges[0][0]:example_ranges[1][0]]  # (1)!
DatetimeIndex(['2020-01-01 00:00:00+00:00', '2020-01-01 01:00:00+00:00',
               '2020-01-01 02:00:00+00:00', '2020-01-01 03:00:00+00:00',
               '2020-01-01 04:00:00+00:00', '2020-01-01 05:00:00+00:00',
               ...
               '2020-01-31 18:00:00+00:00', '2020-01-31 19:00:00+00:00',
               '2020-01-31 20:00:00+00:00', '2020-01-31 21:00:00+00:00',
               '2020-01-31 22:00:00+00:00', '2020-01-31 23:00:00+00:00'],
              dtype='datetime64[ns, UTC]', name='Open time', length=744, freq=None)
```

1. The first number (either 0 or 1) selects the bound (left or right), and the second number selects a range.

!!! important
    The right bound (second column) is always exclusive, so you should not use it for indexing
    directly, as it may point to an element beyond the index length.

We can see that the first range covers values from `2020-01-01` to `2020-01-31`, representing one month.

If you want to look back over a set period of time rather than up to the previous allocation timestamp,
you can use the `lookback_period` argument. In the following example, we generate new indices each month
while looking back over the previous 3 months:

```pycon
>>> example_ranges = data.wrapper.get_index_ranges(
...     every="M", 
...     lookback_period="3M"  # (1)!
... )

>>> def get_index_bounds(range_starts, range_ends):  # (2)!
...     for i in range(len(range_starts)):
...         start_idx = range_starts[i]  # (3)!
...         end_idx = range_ends[i]  # (4)!
...         range_index = data.wrapper.index[start_idx:end_idx]
...         yield range_index[0], range_index[-1]

>>> list(get_index_bounds(*example_ranges))
[(Timestamp('2020-01-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-03-31 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-02-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-04-30 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-03-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-05-31 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-04-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-06-30 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-05-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-07-31 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-06-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-08-31 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-07-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-09-30 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-08-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-10-31 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-09-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-11-30 23:00:00+0000', tz='UTC'))]
```

1. The lookback period can also be provided as an integer (which is multiplied by the source frequency),
a `pd.Timedelta` object, or a `pd.DateOffset` object.
2. This is a simple function that returns the first and last timestamp for each index range.
3. Inclusive.
4. Exclusive.

But what if you know the exact dates when each range should start and/or end? Unlike index points, the
`start` and `end` arguments can be collections of indices or timestamps to define the range bounds:

```pycon
>>> example_ranges = data.wrapper.get_index_ranges(
...     start=["2020-01-01", "2020-04-01", "2020-08-01"],
...     end=["2020-04-01", "2020-08-01", "2020-12-01"]
... )

>>> list(get_index_bounds(*example_ranges))
[(Timestamp('2020-01-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-03-31 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-04-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-07-31 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-08-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-11-30 23:00:00+0000', tz='UTC'))]
```

!!! hint
    You can mark the first timestamp as exclusive and the last timestamp as inclusive by setting
    `closed_start` to False and `closed_end` to True, respectively. Note that these settings affect
    the input, but the output always follows the _from inclusive to exclusive_ scheme.

Additionally, if either `start` or `end` is a single value, it will automatically be broadcast to match
the length of the other argument. Let's simulate the movement of an expanding window:

```pycon
>>> example_ranges = data.wrapper.get_index_ranges(
...     start="2020-01-01",
...     end=["2020-04-01", "2020-08-01", "2020-12-01"]
... )

>>> list(get_index_bounds(*example_ranges))
[(Timestamp('2020-01-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-03-31 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-01-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-07-31 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-01-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-11-30 23:00:00+0000', tz='UTC'))]
```

Another useful argument is `fixed_start`, which, when combined with `every`, can also simulate an
expanding window:

```pycon
>>> example_ranges = data.wrapper.get_index_ranges(
...     every="Q",
...     exact_start=True,  # (1)!
...     fixed_start=True
... )

>>> list(get_index_bounds(*example_ranges))
[(Timestamp('2020-01-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-03-30 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-01-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-06-29 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-01-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-09-29 23:00:00+0000', tz='UTC')),
 (Timestamp('2020-01-01 00:00:00+0000', tz='UTC'),
  Timestamp('2020-12-30 23:00:00+0000', tz='UTC'))]
```

1. Without this flag, the first date would be "2020-03-31" as generated by 
[pandas.date_range](https://pandas.pydata.org/docs/reference/api/pandas.date_range.html).

### Optimization method

Similar to [PortfolioOptimizer.from_allocate_func](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_allocate_func),
which is applied on index points, there is a class method
[PortfolioOptimizer.from_optimize_func](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_optimize_func)
that is applied on index ranges. This method works almost identically to its counterpart, except that
each iteration calls an optimization function `optimize_func` that focuses on an index range (available
as `index_slice` through the template context). All index ranges are stored as
records of type [AllocRanges](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/records/#vectorbtpro.portfolio.pfopt.records.AllocRanges),
which is a subclass of [Ranges](https://vectorbt.pro/pvt_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.Ranges).

Let's try a simple example: allocate inversely proportional to the return of an asset. This approach
allocates more to assets that have recently performed poorly, with the expectation of buying them at a
discounted price and that they will turn bullish in the upcoming period.

```pycon
>>> def inv_rank_optimize_func(price, index_slice):
...     price_period = price.iloc[index_slice]  # (1)!
...     first_price = price_period.iloc[0]
...     last_price = price_period.iloc[-1]
...     ret = (last_price - first_price) / first_price  # (2)!
...     ranks = ret.rank(ascending=False)  # (3)!
...     return ranks / ranks.sum()  # (4)!

>>> pfo = vbt.PortfolioOptimizer.from_optimize_func(
...     symbol_wrapper,
...     inv_rank_optimize_func,
...     data.get("Close"),
...     vbt.Rep("index_slice"),  # (5)!
...     every="M"
... )

>>> pfo.allocations
symbol                      ADAUSDT   BNBUSDT   BTCUSDT   ETHUSDT   XRPUSDT
Open time                                                                  
2020-02-01 00:00:00+00:00  0.066667  0.200000  0.266667  0.133333  0.333333
2020-03-01 00:00:00+00:00  0.333333  0.133333  0.266667  0.066667  0.200000
2020-04-01 00:00:00+00:00  0.266667  0.200000  0.133333  0.333333  0.066667
2020-05-01 00:00:00+00:00  0.066667  0.200000  0.266667  0.133333  0.333333
2020-06-01 00:00:00+00:00  0.066667  0.266667  0.200000  0.133333  0.333333
2020-07-01 00:00:00+00:00  0.066667  0.266667  0.200000  0.133333  0.333333
2020-08-01 00:00:00+00:00  0.066667  0.266667  0.333333  0.133333  0.200000
2020-09-01 00:00:00+00:00  0.333333  0.133333  0.266667  0.066667  0.200000
2020-10-01 00:00:00+00:00  0.266667  0.066667  0.133333  0.333333  0.200000
2020-11-01 00:00:00+00:00  0.333333  0.266667  0.066667  0.133333  0.200000
2020-12-01 00:00:00+00:00  0.133333  0.333333  0.266667  0.200000  0.066667
```

1. Select the data within the current index range.
2. Calculate the return of each asset.
3. Calculate the inverse rank of each return.
4. Convert the ranks into weights that sum to 1.
5. Use the [Rep](https://vectorbt.pro/pvt_6d1b3986/api/utils/template/#vectorbtpro.utils.template.Rep) template to instruct VBT 
to replace it with the index slice of type `slice`, which can be easily applied to any Pandas array.

To automatically select the index range from an array, we can wrap the array with
[Takeable](https://vectorbt.pro/pvt_6d1b3986/api/generic/splitting/base/#vectorbtpro.generic.splitting.base.Takeable):

```pycon
>>> def inv_rank_optimize_func(price):
...     first_price = price.iloc[0]
...     last_price = price.iloc[-1]
...     ret = (last_price - first_price) / first_price
...     ranks = ret.rank(ascending=False)
...     return ranks / ranks.sum()

>>> pfo = vbt.PortfolioOptimizer.from_optimize_func(
...     symbol_wrapper,
...     inv_rank_optimize_func,
...     vbt.Takeable(data.get("Close")),
...     every="M"
... )
```

!!! hint
    Although this approach introduces a slight overhead, it has a key advantage over the manual
    approach: VBT knows how to select an index range even when the takeable array is a Pandas object
    whose index or frequency differs from that of the optimization. This is possible thanks to VBT's
    robust resampling.

To validate the allocation array, we first need to access the index ranges over which our portfolio
optimization was performed. These are stored under the same attribute as index points:
[PortfolioOptimizer.alloc_records](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.alloc_records):

```pycon
>>> pfo.alloc_records.records_readable
    Range Id  Group               Start Index                 End Index  \
0          0  group 2020-01-01 00:00:00+00:00 2020-02-01 00:00:00+00:00   
1          1  group 2020-02-01 00:00:00+00:00 2020-03-01 00:00:00+00:00   
2          2  group 2020-03-01 00:00:00+00:00 2020-04-01 00:00:00+00:00   
3          3  group 2020-04-01 00:00:00+00:00 2020-05-01 00:00:00+00:00   
4          4  group 2020-05-01 00:00:00+00:00 2020-06-01 00:00:00+00:00   
5          5  group 2020-06-01 00:00:00+00:00 2020-07-01 00:00:00+00:00   
6          6  group 2020-07-01 00:00:00+00:00 2020-08-01 00:00:00+00:00   
7          7  group 2020-08-01 00:00:00+00:00 2020-09-01 00:00:00+00:00   
8          8  group 2020-09-01 00:00:00+00:00 2020-10-01 00:00:00+00:00   
9          9  group 2020-10-01 00:00:00+00:00 2020-11-01 00:00:00+00:00   
10        10  group 2020-11-01 00:00:00+00:00 2020-12-01 00:00:00+00:00   

            Allocation Index  Status  
0  2020-02-01 00:00:00+00:00  Closed  
1  2020-03-01 00:00:00+00:00  Closed  
2  2020-04-01 00:00:00+00:00  Closed  
3  2020-05-01 00:00:00+00:00  Closed  
4  2020-06-01 00:00:00+00:00  Closed  
5  2020-07-01 00:00:00+00:00  Closed  
6  2020-08-01 00:00:00+00:00  Closed  
7  2020-09-01 00:00:00+00:00  Closed  
8  2020-10-01 00:00:00+00:00  Closed  
9  2020-11-01 00:00:00+00:00  Closed  
10 2020-12-01 00:00:00+00:00  Closed  
```

We observe three different types of timestamps: a start (`start_idx`), an end (`end_idx`), and
an allocation timestamp (`alloc_idx`). The start and end timestamps define our index ranges,
while the allocation timestamps indicate when the allocations were actually placed. By default,
VBT places an allocation at the end of each index range. In cases where the end index
exceeds the bounds (remember that it is an excluded index), the status of the range is marked
as "Open"; otherwise, it is "Closed" (meaning we can safely use that allocation). Allocation
arrays and filled allocation arrays include only closed allocations.

!!! hint
    Use the `alloc_wait` argument to control how many ticks after the range the allocation should be
    placed. The default is `1`. Passing `0` will place the allocation at the last tick within the
    index range, which should be used with caution when optimizing based on the close price.

Let's validate the allocation generated from the first month of data:

```pycon
>>> start_idx = pfo.alloc_records.values[0]["start_idx"]
>>> end_idx = pfo.alloc_records.values[0]["end_idx"]
>>> close_period = data.get("Close").iloc[start_idx:end_idx]
>>> close_period.vbt.rebase(1).vbt.plot().show()  # (1)!
```

1. Rescale all close prices to start from 1 using [GenericAccessor.rebase](https://vectorbt.pro/pvt_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.rebase)
and plot them using [GenericAccessor.plot](https://vectorbt.pro/pvt_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.plot).

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/close_period.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/close_period.dark.svg#only-dark){: .iimg loading=lazy }

We see that `ADAUSDT` produced the highest return and `XRPUSDT` the lowest. This is correctly
reflected by allocating only 6% to ADAUSDT and 33% to XRPUSDT.

Storing index ranges, rather than just index points, in a
[PortfolioOptimizer](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer)
instance also enables new metrics and subplots:

```pycon
>>> pfo.stats()
Start                       2020-01-01 00:00:00+00:00
End                         2020-12-31 23:00:00+00:00
Period                              365 days 06:00:00
Total Records                                      11
Coverage                                     0.915593  << ranges cover 92%
Overlap Coverage                                  0.0  << ranges do not overlap
Mean Allocation: ADAUSDT                     0.181818
Mean Allocation: BNBUSDT                     0.212121
Mean Allocation: BTCUSDT                     0.218182
Mean Allocation: ETHUSDT                     0.163636
Mean Allocation: XRPUSDT                     0.224242
Name: group, dtype: object

>>> pfo.plots().show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/plots.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/tutorials/pf-opt/plots.dark.svg#only-dark){: .iimg loading=lazy }

In the graph above, we see not only when each re-allocation occurs, but also which index range
the re-allocation is based on.

All other features, such as [support for groups](#groups), remain identical to
[PortfolioOptimizer.from_allocate_func](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_allocate_func).

#### Waiting

By default, when generating weights over a specific time period, the weights will be allocated at the
next available timestamp. This has some implications. For example, when calling
[PortfolioOptimizer.from_optimize_func](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.from_optimize_func)
without any arguments, it will optimize over the entire time period but return no allocations,
because there is no next timestamp at which to allocate the generated weights:

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_optimize_func(
...     symbol_wrapper,
...     inv_rank_optimize_func,
...     vbt.Takeable(data.get("Close"))
... )
>>> pfo.allocations
Empty DataFrame
Columns: [BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, ADAUSDT]
Index: []
```

The solution is to set the waiting time to zero:

```pycon
>>> pfo = vbt.PortfolioOptimizer.from_optimize_func(
...     symbol_wrapper,
...     inv_rank_optimize_func,
...     vbt.Takeable(data.get("Close")),
...     alloc_wait=0  # (1)!
... )
>>> pfo.allocations
symbol                     BTCUSDT   ETHUSDT   BNBUSDT   XRPUSDT   ADAUSDT
Open time                                                                 
2020-12-31 23:00:00+00:00      0.2  0.066667  0.266667  0.333333  0.133333
```

1. Here.

#### Numba

Let's perform both the iteration and optimization entirely using Numba. The only difference,
compared to a Numba-compiled allocation function, is that an optimization function takes two
arguments instead of one: the range start and end index. Under the hood, the iteration and
execution are managed by [optimize_meta_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/nb/#vectorbtpro.portfolio.pfopt.nb.optimize_meta_nb).

```pycon
>>> @njit
... def inv_rank_optimize_func_nb(i, start_idx, end_idx, price):
...     price_period = price[start_idx:end_idx]
...     first_price = price_period[0]
...     last_price = price_period[-1]
...     ret = (last_price - first_price) / first_price
...     ranks = vbt.nb.rank_1d_nb(-ret)  # (1)!
...     return ranks / ranks.sum()

>>> pfo = vbt.PortfolioOptimizer.from_optimize_func(
...     symbol_wrapper,
...     inv_rank_optimize_func_nb,
...     data.get("Close").values,  # (2)!
...     every="M",
...     jitted_loop=True
... )

>>> pfo.allocations
symbol                      ADAUSDT   BNBUSDT   BTCUSDT   ETHUSDT   XRPUSDT
Open time                                                                  
2020-02-01 00:00:00+00:00  0.066667  0.200000  0.266667  0.133333  0.333333
2020-03-01 00:00:00+00:00  0.333333  0.133333  0.266667  0.066667  0.200000
2020-04-01 00:00:00+00:00  0.266667  0.200000  0.133333  0.333333  0.066667
2020-05-01 00:00:00+00:00  0.066667  0.200000  0.266667  0.133333  0.333333
2020-06-01 00:00:00+00:00  0.066667  0.266667  0.200000  0.133333  0.333333
2020-07-01 00:00:00+00:00  0.066667  0.266667  0.200000  0.133333  0.333333
2020-08-01 00:00:00+00:00  0.066667  0.266667  0.333333  0.133333  0.200000
2020-09-01 00:00:00+00:00  0.333333  0.133333  0.266667  0.066667  0.200000
2020-10-01 00:00:00+00:00  0.266667  0.066667  0.133333  0.333333  0.200000
2020-11-01 00:00:00+00:00  0.333333  0.266667  0.066667  0.133333  0.200000
2020-12-01 00:00:00+00:00  0.133333  0.333333  0.266667  0.200000  0.066667
```

1. Negate the array to calculate the inverse rank.
2. Make sure to convert any Pandas object to a NumPy array.

The adaptation to Numba is quite simple, right? :wink:

The speedup from this compilation is significant, especially when there are many re-allocation steps
and/or parameter combinations. Try it for yourself!

[:material-language-python: Python code](https://vectorbt.pro/pvt_6d1b3986/assets/jupytext/tutorials/portfolio-optimization/index.py.txt){ .md-button target="blank_" }
[:material-notebook-outline: Notebook](https://github.com/polakowo/vectorbt.pro/blob/main/notebooks/PortfolioOptimization.ipynb){ .md-button target="blank_" }