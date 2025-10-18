---
title: Fundamentals
description: Documentation on fundamental concepts of VectorBT PRO
icon: material/alphabetical-variant
---

# :material-alphabetical-variant: Fundamentals

VBT was designed to address common performance challenges present in many backtesting libraries.
It is built on the idea that each trading strategy instance can be represented in a vectorized format.
This method allows multiple strategy instances to be combined into a single multi-dimensional array,
enabling highly efficient processing and straightforward analysis.

## Stack

Since trading data is time-series based, most aspects of backtesting can be represented as arrays. In 
particular, VBT works with [NumPy arrays](https://numpy.org/doc/stable/user/quickstart.html), which 
are ***very fast*** thanks to optimized, pre-compiled C code. NumPy arrays are supported by many 
scientific packages in the dynamic Python ecosystem, including Pandas, NumPy, and Numba. There is a good 
chance you have already used some of these packages!

While NumPy offers excellent performance, it is not always the most intuitive tool for time series 
analysis. Consider the following moving average example using NumPy:

```pycon
>>> from vectorbtpro import *

>>> def rolling_window(a, window):
...     shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
...     strides = a.strides + (a.strides[-1],)
...     return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)

>>> np.mean(rolling_window(np.arange(10), 3), axis=1)
array([1., 2., 3., 4., 5., 6., 7., 8.])
```

While this approach is very fast, it can take some time to understand what is happening, and it requires 
experience to write such vectorized code correctly. What about other rolling functions used in more 
advanced indicators? And what about resampling, grouping, and other operations involving dates and times?

This is where [Pandas](https://pandas.pydata.org/docs/getting_started/overview.html) comes to the rescue! 
Pandas offers rich time series features, data alignment, NA-friendly statistics, groupby, merge and join 
methods, and many other useful tools. It has two primary data structures: 
[Series](https://pandas.pydata.org/docs/reference/api/pandas.Series.html) (one-dimensional) and
[DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html) (two-dimensional).
You can think of them as NumPy arrays enhanced with valuable information like timestamps and column names.
Our moving average can be written in a single line:

```pycon
>>> index = vbt.date_range("2020-01-01", periods=10)
>>> sr = pd.Series(range(len(index)), index=index)
>>> sr.rolling(3).mean()
2020-01-01    NaN
2020-01-02    NaN
2020-01-03    1.0
2020-01-04    2.0
2020-01-05    3.0
2020-01-06    4.0
2020-01-07    5.0
2020-01-08    6.0
2020-01-09    7.0
2020-01-10    8.0
Freq: D, dtype: float64
```

VBT depends heavily on Pandas, but not in the way you might expect. Pandas has one major 
limitation for our purposes: it becomes slow when working with large datasets and user-defined functions. 
Many built-in functions like the rolling mean use [Cython](https://cython.org/) under the hood, making 
them fast enough. However, when you try to implement a more complex function, such as a rolling ranking 
metric involving multiple time series, things become complicated and slow. Additionally, what about 
functions that cannot be vectorized? For example, a portfolio strategy with money management cannot be 
simulated directly with vector calculations. In such cases, we need to write fast, iterative code that 
processes data element-by-element.

What if I told you there is a Python package that lets you run for-loops at machine code speed? And 
that it works seamlessly with NumPy and does not require you to heavily modify your Python code? This 
would solve many of our problems: our code would become incredibly fast while remaining easy to read. 
This package is [Numba](https://numba.pydata.org/numba-doc/latest/user/5minguide.html). Numba converts a 
subset of Python and NumPy code into efficient machine code.

```pycon
>>> @njit
... def moving_average_nb(a, window_len):
...     b = np.empty_like(a, dtype=float_)
...     for i in range(len(a)):
...         window_start = max(0, i + 1 - window_len)
...         window_end = i + 1
...         if window_end - window_start < window_len:
...             b[i] = np.nan
...         else:
...             b[i] = np.mean(a[window_start:window_end])
...     return b

>>> moving_average_nb(np.arange(10), 3)
array([nan, nan, 1., 2., 3., 4., 5., 6., 7., 8.])
```

Now we can clearly see what is happening: we loop over the time series one timestamp at a time, check
if there is enough data in the window, and if so, calculate its mean. Not only does Numba help 
produce more readable and less error-prone code, it is also as fast as 
[C](https://en.wikipedia.org/wiki/C_(programming_language))!

```pycon
>>> big_a = np.arange(1000000)
>>> %timeit moving_average_nb.py_func(big_a, 10)  # (1)!
6.54 s ± 142 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

>>> %timeit np.mean(rolling_window(big_a, 10), axis=1)  # (2)!
24.7 ms ± 173 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

>>> %timeit pd.Series(big_a).rolling(10).mean()  # (3)!
10.2 ms ± 309 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

>>> %timeit moving_average_nb(big_a, 10)  # (4)!
5.12 ms ± 7.21 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
```

1. Python.
2. NumPy.
3. Pandas.
4. Numba!

!!! hint
    If you are curious about how VBT uses Numba, look for any directory or file named `nb`.
    [This sub-package](https://github.com/polakowo/vectorbt.pro/blob/main/vectorbtpro/generic/nb/)
    contains all the basic functions, while
    [this module](https://github.com/polakowo/vectorbt.pro/blob/main/vectorbtpro/portfolio/nb/from_order_func.py)
    handles some advanced topics (:warning: adults only).

So, where is the catch? Unfortunately, Numba only understands NumPy, not Pandas. This means we lose the 
datetime index and other features essential for time series analysis. This is where VBT comes in: it 
replicates many Pandas functions using Numba and even adds new features to them. As a result, we not 
only make a subset of Pandas faster, but also more powerful!

Here is how it works:

1. Extract the NumPy array from the Pandas object.
2. Run a Numba-compiled function on this array.
3. Wrap the result back using Pandas.

```pycon
>>> arr = sr.values
>>> result = moving_average_nb(arr, 3)
>>> new_sr = pd.Series(result, index=sr.index, name=sr.name)
>>> new_sr
2020-01-01    NaN
2020-01-02    NaN
2020-01-03    1.0
2020-01-04    2.0
2020-01-05    3.0
2020-01-06    4.0
2020-01-07    5.0
2020-01-08    6.0
2020-01-09    7.0
2020-01-10    8.0
Freq: D, dtype: float64
```

Or, using VBT:

```pycon
>>> sr.vbt.rolling_mean(3)
2020-01-01    NaN
2020-01-02    NaN
2020-01-03    1.0
2020-01-04    2.0
2020-01-05    3.0
2020-01-06    4.0
2020-01-07    5.0
2020-01-08    6.0
2020-01-09    7.0
2020-01-10    8.0
Freq: D, dtype: float64
```

## Accessors

Notice how `vbt` is attached directly to the Series object? This is called 
[an accessor](https://pandas.pydata.org/docs/development/extending.html#registering-custom-accessors) –
a convenient way to extend Pandas objects without subclassing them. With an accessor, you can easily switch 
between native Pandas and VBT functionality. In addition, each VBT method is flexible with 
inputs and can work on both Series and DataFrames.

```pycon
>>> df = pd.DataFrame({'a': range(10), 'b': range(9, -1, -1)})
>>> df.vbt.rolling_mean(3)
     a    b
0  NaN  NaN
1  NaN  NaN
2  1.0  8.0
3  2.0  7.0
4  3.0  6.0
5  4.0  5.0
6  5.0  4.0
7  6.0  3.0
8  7.0  2.0
9  8.0  1.0
```

You can learn more about VBT's accessors [here](https://vectorbt.pro/pvt_6d1b3986/api/accessors/). For example, `rolling_mean`
is part of the accessor [GenericAccessor](https://vectorbt.pro/pvt_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor),
which you can access directly using `vbt`. Another popular accessor, [ReturnsAccessor](https://vectorbt.pro/pvt_6d1b3986/api/returns/accessors/#vectorbtpro.returns.accessors.ReturnsAccessor),
is used for processing returns. It is a subclass of `GenericAccessor` and can be accessed using `vbt.returns`.

```pycon
>>> ret = pd.Series([0.1, 0.2, -0.1])
>>> ret.vbt.returns.total()
0.18800000000000017
```

!!! important
    Each accessor expects the data to be in a ready-to-use format. For example, the accessor
    for working with returns expects the data to be returns, not prices!

## Multidimensionality

Remember that VBT differs from traditional backtesters by handling trading data 
as multi-dimensional arrays. Specifically, VBT treats each column as a separate backtesting 
instance rather than a feature. Consider a simple OHLC DataFrame:

```pycon
>>> p1 = pd.DataFrame({
...     'open': [1, 2, 3, 4, 5],
...     'high': [2.5, 3.5, 4.5, 5.5, 6.5],
...     'low': [0.5, 1.5, 2.5, 3.5, 4.5],
...     'close': [2, 3, 4, 5, 6]
... }, index=vbt.date_range("2020-01-01", periods=5))
>>> p1
            open  high  low  close
2020-01-01     1   2.5  0.5      2
2020-01-02     2   3.5  1.5      3
2020-01-03     3   4.5  2.5      4
2020-01-04     4   5.5  3.5      5
2020-01-05     5   6.5  4.5      6
```

Here, the columns are separate features describing the same abstract object: price.
Although it may feel natural to pass this DataFrame to VBT (as you might with 
[scikit-learn](https://scikit-learn.org/stable/) and other ML tools that expect 
DataFrames with features as columns), this approach has several drawbacks in backtesting:

1. Features of different lengths or types are difficult to concatenate with NumPy.
2. Optional features cannot be properly represented as arrays.
3. Multiple backtests could be stacked into a 3-dimensional array (cube), but Pandas would not handle this correctly.
4. Non-changing features and constants would need to be converted into arrays and
replicated across all backtests, resulting in memory waste.

VBT manages this variability of features by processing them as separate arrays.
So, instead of passing one large DataFrame, you provide each feature independently:

```pycon
>>> single_pf = vbt.Portfolio.from_holding(
...     open=p1['open'], 
...     high=p1['high'], 
...     low=p1['low'], 
...     close=p1['close']
... )
>>> single_pf.value
2020-01-01    100.0
2020-01-02    150.0
2020-01-03    200.0
2020-01-04    250.0
2020-01-05    300.0
Freq: D, dtype: float64
```

Now, if you want to process multiple abstract objects, such as ticker symbols, you can simply pass 
DataFrames instead of Series:

```pycon
>>> p2 = pd.DataFrame({
...     'open': [6, 5, 4, 3, 2],
...     'high': [6.5, 5.5, 4.5, 3.5, 2.5],
...     'low': [4.5, 3.5, 2.5, 1.5, 0.5],
...     'close': [5, 4, 3, 2, 1]
... }, index=vbt.date_range("2020-01-01", periods=5))
>>> p2
            open  high  low  close
2020-01-01     6   6.5  4.5      5
2020-01-02     5   5.5  3.5      4
2020-01-03     4   4.5  2.5      3
2020-01-04     3   3.5  1.5      2
2020-01-05     2   2.5  0.5      1

>>> multi_open = pd.DataFrame({
...     'p1': p1['open'],
...     'p2': p2['open']
... })
>>> multi_high = pd.DataFrame({
...     'p1': p1['high'],
...     'p2': p2['high']
... })
>>> multi_low = pd.DataFrame({
...     'p1': p1['low'],
...     'p2': p2['low']
... })
>>> multi_close = pd.DataFrame({
...     'p1': p1['close'],
...     'p2': p2['close']
... })

>>> multi_pf = vbt.Portfolio.from_holding(
...     open=multi_open,
...     high=multi_high,
...     low=multi_low,
...     close=multi_close
... )
>>> multi_pf.value
               p1     p2
2020-01-01  100.0  100.0
2020-01-02  150.0   80.0
2020-01-03  200.0   60.0
2020-01-04  250.0   40.0
2020-01-05  300.0   20.0
```

Here, each column (sometimes called a "line" in VBT) in each feature DataFrame represents 
a separate backtesting instance and creates a separate equity curve. So, adding another backtest
is as easy as adding another column to the features :sparkles:

Keeping features separate has another major advantage: it lets us combine them easily.
Even better, we can combine all backtesting instances at once using vectorization.
For example, here we place an entry signal whenever the previous candle was green and 
an exit signal whenever the previous candle was red (this is a basic example for illustration):

```pycon
>>> candle_green = multi_close > multi_open
>>> prev_candle_green = candle_green.vbt.signals.fshift(1)
>>> prev_candle_green
               p1     p2
2020-01-01  False  False
2020-01-02   True  False
2020-01-03   True  False
2020-01-04   True  False
2020-01-05   True  False

>>> candle_red = multi_close < multi_open
>>> prev_candle_red = candle_red.vbt.signals.fshift(1)
>>> prev_candle_red
               p1     p2
2020-01-01  False  False
2020-01-02  False   True
2020-01-03  False   True
2020-01-04  False   True
2020-01-05  False   True
```

The Pandas objects `multi_close` and `multi_open` can be Series or DataFrames of any shape,
and our micro-pipeline will continue to work as expected.

## Labels

In the example above, we created our multi-OHLC DataFrames with two columns, `p1` and `p2`, so we can
easily identify them later during the analysis phase. For this reason, VBT ensures that these columns
are preserved throughout the entire backtesting pipeline, from signal generation to performance modeling.

But what if individual columns represent more complex configurations, such as those involving multiple
hyperparameter combinations? Storing complex objects as column labels would not work well in such cases.
Fortunately, Pandas offers [hierarchical columns](https://pandas.pydata.org/pandas-docs/stable/user_guide/advanced.html),
which are similar to regular columns but are stacked in multiple layers. Each level in this hierarchy
can help us identify a specific input or parameter.

Take a simple crossover strategy as an example: it depends on the lengths of the fast and slow windows.
Each of these hyperparameters becomes an additional dimension for manipulating data and is stored as a
separate column level. Below is a more complex example showing the column hierarchy of a MACD indicator:

```pycon
>>> macd = vbt.MACD.run(
...     multi_close,
...     fast_window=2,
...     slow_window=(3, 4),
...     signal_window=2,
...     macd_wtype="simple",
...     signal_wtype="weighted"
... )
>>> macd.signal
macd_fast_window               2             2  << fast window for MACD line
macd_slow_window               3             4  << slow window for MACD line
macd_signal_window             2             2  << window for signal line
macd_macd_wtype           simple        simple  << window type for MACD line
macd_signal_wtype       weighted      weighted  << window type for signal line   
                         p1   p2       p1   p2  << price
2020-01-01              NaN  NaN      NaN  NaN
2020-01-02              NaN  NaN      NaN  NaN
2020-01-03              NaN  NaN      NaN  NaN
2020-01-04              0.5 -0.5      NaN  NaN
2020-01-05              0.5 -0.5      1.0 -1.0
```

The columns above represent two different backtesting configurations that can now be easily analyzed and
compared using Pandas. This is a powerful way to analyze data. For example, you could group your
performance by `macd_fast_window` to see how the size of the fast window affects your strategy's
profitability. Pretty magical, right?

## Broadcasting

One of the most important concepts in VBT is broadcasting. Since VBT functions take
time series as independent arrays, they need to know how to connect elements across those arrays so that
there is 1) complete information, 2) across all arrays, and 3) at each time step.

If all arrays are the same size, VBT can easily perform operations on an element-by-element basis.
If any array is smaller in size, VBT tries to "stretch" it to match the length of the other arrays.
This approach is heavily inspired by (and internally based on) [NumPy's broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html).
The main difference from NumPy is that one-dimensional arrays are always specified per row,
since we are primarily working with time series data.

Why is broadcasting important? Because it allows you to pass array-like objects of any shape to almost
every function in VBT, whether they are constants or full DataFrames, and VBT will automatically
determine where each element belongs.

```pycon
>>> part_arrays = dict(
...     close=pd.DataFrame({  # (1)!
...         'a': [1, 2, 3, 4], 
...         'b': [4, 3, 2, 1]
...     }),
...     size=pd.Series([1, -1, 1, -1]),  # (2)!
...     direction=[['longonly', 'shortonly']],  # (3)!
...     fees=0.01  # (4)!
... )
>>> full_arrays = vbt.broadcast(part_arrays)

>>> full_arrays['close']
   a  b
0  1  4
1  2  3
2  3  2
3  4  1

>>> full_arrays['size']
   a  b
0  1  1
1 -1 -1
2  1  1
3 -1 -1

>>> full_arrays['direction']
          a          b
0  longonly  shortonly
1  longonly  shortonly
2  longonly  shortonly
3  longonly  shortonly

>>> full_arrays['fees']
      a     b
0  0.01  0.01
1  0.01  0.01
2  0.01  0.01
3  0.01  0.01
```

1. Specified per element. Does not broadcast.
2. Specified per row. Broadcasts along columns.
3. Specified per column. Broadcasts along rows.
4. Specified per entire array. Broadcasts along rows and columns.

!!! hint
    As a rule of thumb:

    1. If any array is a Pandas object, the output is always a Pandas object.
    2. If any array is two-dimensional, the output is always a two-dimensional array.
    3. If all arrays are constants or one-dimensional, the output is always a one-dimensional array.
    4. If the array is a one-dimensional NumPy array or Series, it is always specified per row.
    5. Lists and other sequences are converted to NumPy arrays before broadcasting.

Unlike NumPy and Pandas, VBT knows how to broadcast labels: if columns or individual column levels in both
objects are different, they are stacked together. For example, you can check whenever the fast moving average is
higher than the slow moving average, using the following window combinations: (2, 3) and (3, 4).

```pycon
>>> fast_ma = vbt.MA.run(multi_close, window=[2, 3], short_name='fast')
>>> slow_ma = vbt.MA.run(multi_close, window=[3, 4], short_name='slow')

>>> fast_ma.ma
fast_window    2    2    3    3
              p1   p2   p1   p2
2020-01-01   NaN  NaN  NaN  NaN
2020-01-02   2.5  4.5  NaN  NaN
2020-01-03   3.5  3.5  3.0  4.0
2020-01-04   4.5  2.5  4.0  3.0
2020-01-05   5.5  1.5  5.0  2.0

>>> slow_ma.ma
slow_window    3    3    4    4
              p1   p2   p1   p2
2020-01-01   NaN  NaN  NaN  NaN
2020-01-02   NaN  NaN  NaN  NaN
2020-01-03   3.0  4.0  NaN  NaN
2020-01-04   4.0  3.0  3.5  3.5
2020-01-05   5.0  2.0  4.5  2.5

>>> fast_ma.ma > slow_ma.ma  # (1)!
ValueError: Can only compare identically-labeled DataFrame objects

>>> fast_ma.ma.values > slow_ma.ma.values  # (2)!
array([[False, False, False, False],
       [False, False, False, False],
       [ True, False, False, False],
       [ True, False,  True, False],
       [ True, False,  True, False]])

>>> fast_ma.ma.vbt > slow_ma.ma  # (3)!
fast_window      2      2      3      3
slow_window      3      3      4      4
                p1     p2     p1     p2
2020-01-01   False  False  False  False
2020-01-02   False  False  False  False
2020-01-03    True  False  False  False
2020-01-04    True  False   True  False
2020-01-05    True  False   True  False
```

1. Comparison with Pandas fails.
2. Comparison with NumPy succeeds.
3. Comparison with VBT succeeds.

!!! hint
    Appending `.vbt` to a Pandas object on the left will broadcast both operands with
    VBT and execute the operation with NumPy/Numba. This gives you the ultimate combination of power 
    and convenience :firecracker:

In contrast to Pandas, VBT broadcasts rows and columns by their absolute positions, not by their labels.
This broadcasting style is very similar to how NumPy handles broadcasting:

```pycon
>>> df1 = pd.DataFrame({'a': [0], 'b': [1]})
>>> df2 = pd.DataFrame({'b': [0], 'a': [1]})
>>> df1 + df2  # (1)!
   a  b
0  1  1

>>> df1.values + df2.values
array([[0, 2]])

>>> df1.vbt + df2  # (2)!
   a  b
   b  a
0  0  2
```

1. Pandas connects column `a` in `df1` with column `a` in `df2`.
2. VBT connects the first column in `df1` with the first column in `df2`, regardless of their labels.

!!! important
    If you pass multiple arrays of data to VBT, make sure that their columns line up positionally!

    If your columns are not properly ordered, you will notice the result has multiple column levels with
    identical labels but different orders.

Another feature of VBT is its ability to broadcast objects with incompatible shapes but overlapping
multi-index levels, meaning those that share the same name or values. Continuing with the previous example,
let's check when the fast moving average is higher than the price:

```pycon
>>> fast_ma.ma > multi_close  # (1)!
ValueError: Can only compare identically-labeled DataFrame objects

>>> fast_ma.ma.values > multi_close.values  # (2)!
ValueError: operands could not be broadcast together with shapes (5,4) (5,2) 

>>> fast_ma.ma.vbt > multi_close  # (3)!
fast_window      2      2      3      3
                p1     p2     p1     p2
2020-01-01   False  False  False  False
2020-01-02   False   True  False  False
2020-01-03   False   True  False   True
2020-01-04   False   True  False   True
2020-01-05   False   True  False   True
```

1. Comparison with Pandas fails.
2. Comparison with NumPy fails.
3. Comparison with VBT succeeds.

And here is even more (stay with me): you can easily test multiple scalar-like hyperparameters
by passing them as a Pandas Index. Let's see whether the price is within certain thresholds:

```pycon
>>> above_lower = multi_close.vbt > vbt.Param([1, 2], name='lower')
>>> below_upper = multi_close.vbt < vbt.Param([3, 4], name='upper')
>>> above_lower.vbt & below_upper
lower           1      1      2      2
upper           3      3      4      4
               p1     p2     p1     p2
2020-01-01   True  False  False  False
2020-01-02  False  False   True  False
2020-01-03  False  False  False   True
2020-01-04  False   True  False  False
2020-01-05  False  False  False  False
```

As you can see, smart broadcasting is :gem: when it comes to merging information.
See [broadcast](https://vectorbt.pro/pvt_6d1b3986/api/base/reshaping/#vectorbtpro.base.reshaping.broadcast) to learn more about
broadcasting principles and new ways to combine arrays.

## Flexible indexing

Broadcasting many large arrays can use a lot of RAM and eventually slow down processing.
That's why VBT introduces the concept of "flexible indexing", which selects one element
from a one-dimensional or two-dimensional array of any shape. For example, if a one-dimensional array
has only one element and needs to be broadcast along 1000 rows, VBT will return that one
element regardless of which row is being queried, since this array would broadcast against any shape:

```pycon
>>> a = np.array([1])

>>> vbt.flex_select_1d_nb(a, 0)
1

>>> vbt.flex_select_1d_nb(a, 1)
1

>>> vbt.flex_select_1d_nb(a, 2)
1
```

This is equivalent to:

```pycon
>>> full_a = np.broadcast_to(a, (1000,))

>>> full_a[2]
1
```

Two-dimensional arrays offer more flexibility. Consider an example where you want to process 1000 columns,
and you have several parameters to apply to each element. Some parameters might be scalars that are
the same for every element, some might be one-dimensional arrays that repeat for each column, and some
might be the same for each row. Instead of broadcasting these arrays fully, you can simply keep the number
of their elements and expand them to two dimensions as needed so they will broadcast correctly with NumPy:

```pycon
>>> a = np.array([[0]])  # (1)!
>>> b = np.array([[1, 2, 3]])  # (2)!
>>> c = np.array([[4], [5], [6]])  # (3)!

>>> vbt.flex_select_nb(a, 2, 1)  # (4)!
0

>>> vbt.flex_select_nb(b, 2, 1)
2

>>> vbt.flex_select_nb(c, 2, 1)
6
```

1. Value per array. Same value for each element.
2. Value per column. Same values for each row.
3. Value per row. Same values for each column.
4. Query the element at the third row and second column.

One nice feature of this approach is that such an operation adds almost no additional memory overhead and
can broadcast in any direction, no matter how large the shape gets. This is one of the keys to how
[Portfolio.from_signals](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from_signals)
can broadcast more than 50 arguments without any loss of memory efficiency or performance :wink:

[:material-language-python: Python code](https://vectorbt.pro/pvt_6d1b3986/assets/jupytext/documentation/fundamentals.py.txt){ .md-button target="blank_" }