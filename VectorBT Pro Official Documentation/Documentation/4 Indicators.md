---
title: Indicators
description: Documentation on handling indicators in VectorBT PRO
icon: material/chart-timeline-variant
---

# :material-chart-timeline-variant: Indicators

The [IndicatorFactory](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory) class is 
one of the most powerful components in the VBT ecosystem. It can wrap any indicator function, 
making it both parameterizable and analyzable.

## Pipeline

An indicator is a pipeline that performs the following steps:

* Accepts input arrays (for example, opening and closing prices).
* Accepts parameters either as scalars or arrays (for example, window size).
* Accepts other relevant arguments and keyword arguments.
* Broadcasts input arrays against each other or to a specific shape.
* Broadcasts parameters against each other to create a fixed set of parameter combinations.
* Calculates output arrays for each parameter combination using the input arrays,
producing the same shape (for example, a rolling average).
* Concatenates the output arrays of all parameter combinations along the columns.
* Converts the results back to the Pandas format.

Let's manually create an indicator that takes two time series, computes their normalized moving
averages, and returns the difference between the two. We will test different shapes as well as 
parameter combinations to see how broadcasting can be leveraged:

```pycon
>>> from vectorbtpro import *

>>> def mov_avg_crossover(ts1, ts2, w1, w2):
...     ts1, ts2 = vbt.broadcast(ts1, ts2)  # (1)!
...
...     w1, w2 = vbt.broadcast(  # (2)!
...         vbt.to_1d_array(w1), 
...         vbt.to_1d_array(w2))
...
...     ts1_mas = []
...     for w in w1:
...         ts1_mas.append(ts1.vbt.rolling_mean(w) / ts1)  # (3)!
...     ts2_mas = []
...     for w in w2:
...         ts2_mas.append(ts2.vbt.rolling_mean(w) / ts2)
...
...     ts1_ma = pd.concat(ts1_mas, axis=1)  # (4)!
...     ts2_ma = pd.concat(ts2_mas, axis=1)
...
...     ts1_ma.columns = vbt.combine_indexes((  # (5)!
...         pd.Index(w1, name="ts1_window"), 
...         ts1.columns))
...     ts2_ma.columns = vbt.combine_indexes((
...         pd.Index(w2, name="ts2_window"), 
...         ts2.columns))
...
...     return ts1_ma.vbt - ts2_ma  # (6)!

>>> def generate_index(n):  # (7)!
...     return vbt.date_range("2020-01-01", periods=n)

>>> ts1 = pd.Series([1, 2, 3, 4, 5, 6, 7], index=generate_index(7))
>>> ts2 = pd.DataFrame({
...     'a': [5, 4, 3, 2, 3, 4, 5],
...     'b': [2, 3, 4, 5, 4, 3, 2]
... }, index=generate_index(7))
>>> w1 = 2
>>> w2 = [3, 4]

>>> mov_avg_crossover(ts1, ts2, w1, w2)
ts1_window                                       2
ts2_window                   3                   4
                   a         b         a         b
2020-01-01       NaN       NaN       NaN       NaN
2020-01-02       NaN       NaN       NaN       NaN
2020-01-03 -0.500000  0.083333       NaN       NaN
2020-01-04 -0.625000  0.075000 -0.875000  0.175000
2020-01-05  0.011111 -0.183333 -0.100000 -0.100000
2020-01-06  0.166667 -0.416667  0.166667 -0.416667
2020-01-07  0.128571 -0.571429  0.228571 -0.821429
```

1. Both time series are converted to Pandas objects with the same shape: `(7, 2)`.
2. Window `w1` becomes `[2, 2]` and window `w2` becomes `[3, 4]`. This results in two parameter
combinations: `(2, 3)` and `(2, 4)`.
3. Calculate the normalized moving average for each window.
4. Concatenate the DataFrames along the column axis.
5. Create a new column hierarchy using the window values as the top level.
6. Calculate the difference between the two concatenated DataFrames.
7. Helper function to generate a datetime-like index.

Pretty neat! We just built a flexible pipeline that can handle arbitrary input and parameter 
combinations. The resulting DataFrame shows each column as a specific window combination applied 
to each column in both `ts1` and `ts2`. But is this pipeline user-friendly? :thinking:  
Dealing with broadcasting, output concatenation, and column hierarchies makes this process 
very similar to working with regular Pandas code.

The pipeline above can be easily standardized using 
[IndicatorBase.run_pipeline](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.run_pipeline).
This method conveniently prepares inputs, parameters, and columns. However, you still need to perform 
the calculation and output concatenation yourself by providing a `custom_func`.  
Let's update the example:

```pycon
>>> def custom_func(ts1, ts2, w1, w2):
...     ts1_mas = []
...     for w in w1:
...         ts1_mas.append(vbt.nb.rolling_mean_nb(ts1, w) / ts1)  # (1)!
...     ts2_mas = []
...     for w in w2:
...         ts2_mas.append(vbt.nb.rolling_mean_nb(ts2, w) / ts2)
...
...     ts1_ma = np.column_stack(ts1_mas)  # (2)!
...     ts2_ma = np.column_stack(ts2_mas)
...
...     return ts1_ma - ts2_ma  # (3)!

>>> outputs = vbt.IndicatorBase.run_pipeline(
...     num_ret_outputs=1,
...     custom_func=custom_func,
...     inputs=dict(ts1=ts1, ts2=ts2),
...     params=dict(w1=w1, w2=w2)
... )
>>> outputs
(<vectorbtpro.base.wrapping.ArrayWrapper at 0x7fb188993160>,
 [array([[1, 1],
         [2, 2],
         [3, 3],
         [4, 4],
         [5, 5],
         [6, 6],
         [7, 7]]),
  array([[5, 2],
         [4, 3],
         [3, 4],
         [2, 5],
         [3, 4],
         [4, 3],
         [5, 2]])],
 array([0, 1, 0, 1]),
 [],
 [array([[        nan,         nan,         nan,         nan],
         [        nan,         nan,         nan,         nan],
         [-0.5       ,  0.08333333,         nan,         nan],
         [-0.625     ,  0.075     , -0.875     ,  0.175     ],
         [ 0.01111111, -0.18333333, -0.1       , -0.1       ],
         [ 0.16666667, -0.41666667,  0.16666667, -0.41666667],
         [ 0.12857143, -0.57142857,  0.22857143, -0.82142857]])],
 [[2, 2], [3, 4]],
 [Int64Index([2, 2, 2, 2], dtype='int64'),
  Int64Index([3, 3, 4, 4], dtype='int64')],
 [])
```

1. Use [rolling_mean_nb](https://vectorbt.pro/pvt_6d1b3986/api/generic/nb/rolling/#vectorbtpro.generic.nb.rolling.rolling_mean_nb).
2. Concatenate the NumPy arrays along the column axis.
3. Calculate the difference between the two concatenated NumPy arrays.

With much less code, we performed the entire calculation using only NumPy and Numba—a big win!
But what is this complex output?

This raw output is designed for internal use by VBT and is not intended for direct use. It contains 
metadata necessary for working with the indicator. Additionally, if you review the source of this 
function, you will see that it accepts many different arguments. This complexity provides great 
flexibility, as each argument corresponds to a specific step in the pipeline. But do not worry: we 
will not use this function directly.

## Factory

Instead, we will use [IndicatorFactory](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory),
which simplifies [IndicatorBase.run_pipeline](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.run_pipeline)
by providing a unified interface and various automations. Let's use the factory 
to wrap our `custom_func`:

```pycon
>>> MADiff = vbt.IF(
...     class_name='MADiff',
...     input_names=['ts1', 'ts2'],
...     param_names=['w1', 'w2'],
...     output_names=['diff'],
... ).with_custom_func(custom_func)

>>> madiff = MADiff.run(ts1, ts2, w1, w2)
>>> madiff.diff
madiff_w1                                        2
madiff_w2                    3                   4
                   a         b         a         b
2020-01-01       NaN       NaN       NaN       NaN
2020-01-02       NaN       NaN       NaN       NaN
2020-01-03 -0.500000  0.083333       NaN       NaN
2020-01-04 -0.625000  0.075000 -0.875000  0.175000
2020-01-05  0.011111 -0.183333 -0.100000 -0.100000
2020-01-06  0.166667 -0.416667  0.166667 -0.416667
2020-01-07  0.128571 -0.571429  0.228571 -0.821429
```

!!! hint
    `vbt.IF` is a shortcut for [IndicatorFactory](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory).

As you can see, [IndicatorFactory](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory) 
takes the specification for our indicator and creates a Python class that knows how to communicate with 
[IndicatorBase.run_pipeline](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.run_pipeline) 
and manage and format its results. Specifically, it attaches the class method `MADiff.run`, which 
works just like `custom_func` but prepares and forwards all arguments to 
[IndicatorBase.run_pipeline](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.run_pipeline) 
under the hood. Whenever we call the `run` method, it initializes and returns an instance of `MADiff` 
containing all the input and output data.

You may wonder: *"Why does the factory create a class instead of a function? Wouldn't 
an indicator function be more intuitive?"* If you have read [Building blocks](https://vectorbt.pro/pvt_6d1b3986/documentation/building-blocks),
you may already be familiar with the class [Analyzable](https://vectorbt.pro/pvt_6d1b3986/api/generic/analyzable/#vectorbtpro.generic.analyzable.Analyzable),
the main class for analyzing data. The indicator class created by the factory is a subclass of 
[Analyzable](https://vectorbt.pro/pvt_6d1b3986/api/generic/analyzable/#vectorbtpro.generic.analyzable.Analyzable), so you not only 
get access to the output, but also to many methods for analyzing this output. For example,
the factory automatically provides `crossed_above`, `cross_below`, `stats`, and many other 
methods for each input and output in the indicator:

```pycon
>>> madiff.diff_stats(column=(2, 3, 'a'))
Start        2020-01-01 00:00:00
End          2020-01-07 00:00:00
Period           7 days 00:00:00
Count                          5
Mean                    -0.16373
Std                     0.371153
Min                       -0.625
Median                  0.011111
Max                     0.166667
Min Index    2020-01-04 00:00:00
Max Index    2020-01-06 00:00:00
Name: (2, 3, a), dtype: object
```

### Workflow

The main goal of [IndicatorFactory](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory)
is to create a stand-alone indicator class that includes a `run` method for executing the indicator. 
To accomplish this, it needs to know what inputs, parameters, and outputs to expect. You can provide 
this information using `input_names`, `param_names`, and other arguments in the constructor:

```pycon
>>> MADiff_factory = vbt.IF(
...     class_name='MADiff',
...     input_names=['ts1', 'ts2'],
...     param_names=['w1', 'w2'],
...     output_names=['diff'],
... )
>>> MADiff_factory.Indicator
vectorbtpro.indicators.factory.MADiff
```

When initialized, it builds the skeleton of our indicator class, which is a type of
[IndicatorBase](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase). This is accessible via 
[IndicatorFactory.Indicator](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.Indicator).
Even though the factory creates the constructor for this class and attaches various
properties and methods, we cannot run the indicator yet:

```pycon
>>> MADiff_factory.Indicator.run()
NotImplementedError: 
```

This is because we still need to provide the calculation function. There are several methods 
starting with the prefix `with_`. The fundamental method, used by all others, is 
[IndicatorFactory.with_custom_func](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.with_custom_func)
(which we used earlier). It overrides the abstract `run` method to execute the indicator using 
[IndicatorBase.run_pipeline](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.run_pipeline)
and returns a fully functional indicator class:

```pycon
>>> MADiff = MADiff_factory.with_custom_func(custom_func)
>>> MADiff
vectorbtpro.indicators.factory.MADiff
```

The calculation function has now been successfully attached, so we can run this indicator!

## Factory methods

Factory methods come in two forms: instance and class methods. Instance methods, with the prefix `with_`, 
such as [IndicatorFactory.with_custom_func](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.with_custom_func),
require instantiating the indicator factory. This means you need to call `vbt.IF(...)` and manually provide 
the required information as we did with `MADiff`.  
Class methods, with the prefix `from_`, such as [IndicatorFactory.from_expr](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.from_expr),
can (semi-)automatically parse the required information.

### From custom function

The method [IndicatorFactory.with_custom_func](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.with_custom_func)
accepts a "custom function", which is the most flexible way to define an indicator. However, with this
flexibility comes added responsibility: as the user, you must handle iterating through parameters, manage
caching, and concatenate columns for each parameter combination (usually using
[apply_and_concat](https://vectorbt.pro/pvt_6d1b3986/api/base/combining/#vectorbtpro.base.combining.apply_and_concat)). You must also ensure
that each output array has the correct number of columns, equal to the number of columns in the input
arrays multiplied by the number of parameter combinations. In addition, your custom function receives
commands passed by the pipeline, so it is up to you to properly process those commands.

For example, if your custom function needs the index and columns alongside the NumPy arrays, you can
instruct the pipeline to pass the wrapper by setting `pass_wrapper=True` in `with_custom_func`. This and
all other arguments are forwarded directly to
[IndicatorBase.run_pipeline](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.run_pipeline),
which handles communication with your custom function.

### From apply function

The method [IndicatorFactory.with_apply_func](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.with_apply_func)
greatly simplifies indicator development. It creates a `custom_func` that handles caching, iteration over
parameters with [apply_and_concat](https://vectorbt.pro/pvt_6d1b3986/api/base/combining/#vectorbtpro.base.combining.apply_and_concat),
output concatenation with [column_stack](https://vectorbt.pro/pvt_6d1b3986/api/base/reshaping/#vectorbtpro.base.reshaping.column_stack), and
then passes this function to [IndicatorFactory.with_custom_func](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.with_custom_func).
Your only task is to write an "apply function," which accepts a single parameter combination and performs
the calculation. The resulting outputs are automatically concatenated along the column axis.

!!! note
    An apply function has mostly the same signature as a custom function, but the parameters
    are individual values instead of multiple values.

Let's create our indicator using an apply function:

```pycon
>>> def apply_func(ts1, ts2, w1, w2):
...     ts1_ma = vbt.nb.rolling_mean_nb(ts1, w1) / ts1
...     ts2_ma = vbt.nb.rolling_mean_nb(ts2, w2) / ts2
...     return ts1_ma - ts2_ma

>>> MADiff = vbt.IF(
...     class_name='MADiff',
...     input_names=['ts1', 'ts2'],
...     param_names=['w1', 'w2'],
...     output_names=['diff'],
... ).with_apply_func(apply_func)

>>> madiff = MADiff.run(ts1, ts2, w1, w2)
>>> madiff.diff
madiff_w1                                        2
madiff_w2                    3                   4
                   a         b         a         b
2020-01-01       NaN       NaN       NaN       NaN
2020-01-02       NaN       NaN       NaN       NaN
2020-01-03 -0.500000  0.083333       NaN       NaN
2020-01-04 -0.625000  0.075000 -0.875000  0.175000
2020-01-05  0.011111 -0.183333 -0.100000 -0.100000
2020-01-06  0.166667 -0.416667  0.166667 -0.416667
2020-01-07  0.128571 -0.571429  0.228571 -0.821429
```

That's all you need! Under the hood, the code creates a custom function that iterates over all
parameter combinations and calls `apply_func` on each one. If you print `ts1`, `ts2`, `w1`, and `w2`,
you would see that `ts1` and `ts2` remain the same, while `w1` and `w2` are now individual values.
This design allows you to simplify your code, working with one set of parameters at a time without 
worrying about multiple parameter combinations.

Another advantage of this method is that apply functions are a natural fit in VBT :monkey:, so you
can use most regular and Numba-compiled functions that take two-dimensional NumPy arrays directly as
apply functions. For example, let's build an indicator for rolling covariance:

```pycon
>>> RollCov = vbt.IF(
...     class_name='RollCov',
...     input_names=['ts1', 'ts2'],
...     param_names=['w'],
...     output_names=['rollcov'],
... ).with_apply_func(vbt.nb.rolling_cov_nb)

>>> rollcov = RollCov.run(ts1, ts2, [2, 3])
>>> rollcov.rollcov
rollcov_w            2                   3
               a     b         a         b
2020-01-01   NaN   NaN       NaN       NaN
2020-01-02 -0.25  0.25       NaN       NaN
2020-01-03 -0.25  0.25 -0.666667  0.666667
2020-01-04 -0.25  0.25 -0.666667  0.666667
2020-01-05  0.25 -0.25  0.000000  0.000000
2020-01-06  0.25 -0.25  0.666667 -0.666667
2020-01-07  0.25 -0.25  0.666667 -0.666667
```

In this example, both input arrays and the window parameter are passed directly to
[rolling_cov_nb](https://vectorbt.pro/pvt_6d1b3986/api/generic/nb/rolling/#vectorbtpro.generic.nb.rolling.rolling_cov_nb).

#### Custom iteration

We can easily emulate `apply_func` using `custom_func` and
[apply_and_concat](https://vectorbt.pro/pvt_6d1b3986/api/base/combining/#vectorbtpro.base.combining.apply_and_concat).
For example, if we need the index of the current iteration or want access to all parameter
combinations:

```pycon
>>> from vectorbtpro.base.combining import apply_and_concat

>>> def apply_func(i, ts1, ts2, w):  # (1)!
...     return vbt.nb.rolling_cov_nb(ts1, ts2, w[i])

>>> def custom_func(ts1, ts2, w):
...     return apply_and_concat(len(w), apply_func, ts1, ts2, w)  # (2)!

>>> RollCov = vbt.IF(
...     class_name='RollCov',
...     input_names=['ts1', 'ts2'],
...     param_names=['w'],
...     output_names=['rollcov'],
... ).with_custom_func(custom_func)
```

1. Unlike our previous `apply_func`, an apply function used in
[apply_and_concat](https://vectorbt.pro/pvt_6d1b3986/api/base/combining/#vectorbtpro.base.combining.apply_and_concat)
must take the index of the iteration and select the parameters manually using this index.
2. [apply_and_concat](https://vectorbt.pro/pvt_6d1b3986/api/base/combining/#vectorbtpro.base.combining.apply_and_concat)
requires the number of iterations, which is simply the length of any parameter array.

The same result can be achieved using [IndicatorFactory.with_apply_func](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.with_apply_func)
and `select_params=False`:

```pycon
>>> RollCov = vbt.IF(
...     class_name='RollCov',
...     input_names=['ts1', 'ts2'],
...     param_names=['w'],
...     output_names=['rollcov'],
... ).with_apply_func(apply_func, select_params=False)
```

#### Execution

Since the same apply function is called multiple times—once per parameter combination—we can
use one of VBT's preset execution engines to distribute these calls sequentially (default),
across multiple threads, or across multiple processes. In fact, the function
[apply_and_concat](https://vectorbt.pro/pvt_6d1b3986/api/base/combining/#vectorbtpro.base.combining.apply_and_concat),
which is used to iterate over all parameter combinations, handles this automatically by forwarding
all calls to the executor function [execute](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute).
By passing keyword arguments in `execute_kwargs`, we can define how to distribute these calls.
For example, to disable the progress bar:

```pycon
>>> RollCov = vbt.IF(
...     class_name='RollCov',
...     input_names=['ts1', 'ts2'],
...     param_names=['w'],
...     output_names=['rollcov'],
... ).with_apply_func(vbt.nb.rolling_cov_nb)

>>> RollCov.run(
...     ts1, ts2, np.full(100, 2),
...     execute_kwargs=dict(show_progress=False)
... )
```

[=100% "Iteration 100/100"]{: .candystripe .candystripe-animate }

#### Numba

When the apply function is Numba-compiled, the indicator factory also makes the parameter selection
function Numba-compiled (with the GIL released), allowing for multithreading.
This behavior can be disabled by setting `jit_select_params` to False. The keyword
arguments used to configure the Numba-compiled function can be supplied via the `jit_kwargs` argument.

!!! note
    Setting `jit_select_params` will remove all keyword arguments since variable keyword arguments
    are not supported by Numba (yet). To pass keyword arguments to the apply function anyway,
    set `remove_kwargs` to False or use the `kwargs_as_args` argument, which specifies which keyword
    arguments should be supplied as (variable) positional arguments.

Additionally, you can explicitly set `jitted_loop` to True to loop over each parameter combination
in a Numba loop. This can speed up iteration for shallow inputs with a large number of columns,
but may slow it down otherwise.

!!! note
    In this case, the execution will be performed by Numba, so you cannot use `execute_kwargs` anymore.

#### Debugging

Sometimes it is not clear which arguments are being passed to `apply_func`.
Debugging in this case is usually simple: just replace your apply function with a generic
function that accepts variable arguments and prints them.

```pycon
>>> def apply_func(*args, **kwargs):
...     for i, arg in enumerate(args):
...         print("arg {}: {}".format(i, type(arg)))
...     for k, v in kwargs.items():
...         print("kwarg {}: {}".format(k, type(v)))
...     raise NotImplementedError

>>> RollCov = vbt.IF(
...     class_name='RollCov',
...     input_names=['ts1', 'ts2'],
...     param_names=['w'],
...     output_names=['rollcov'],
... ).with_apply_func(apply_func, select_params=False)

>>> try:
...     RollCov.run(ts1, ts2, [2, 3], some_arg="some_value")
... except:
...     pass
arg 0: <class 'int'>
arg 1: <class 'numpy.ndarray'>
arg 2: <class 'numpy.ndarray'>
arg 3: <class 'list'>
kwarg some_arg: <class 'str'>
```

### From parsing

Parsers offer the most convenient way to build indicator classes. For example, there are dedicated
parser methods for third-party technical analysis packages that can automatically or semi-automatically
derive the specification of each indicator. Additionally, a powerful expression parser can help you avoid
writing complex Python functions for simple indicators. Let's *express* our indicator as an expression:

```pycon
>>> MADiff = vbt.IF.from_expr(
...     "rolling_mean(@in_ts1, @p_w1) / @in_ts1 - rolling_mean(@in_ts2, @p_w2) / @in_ts2",
...     factory_kwargs=dict(class_name="MADiff")  # (1)!
... )
>>> madiff = MADiff.run(ts1, ts2, w1, w2)
>>> madiff.out
madiff_w1                                        2
madiff_w2                    3                   4
                   a         b         a         b
2020-01-01       NaN       NaN       NaN       NaN
2020-01-02       NaN       NaN       NaN       NaN
2020-01-03 -0.500000  0.083333       NaN       NaN
2020-01-04 -0.625000  0.075000 -0.875000  0.175000
2020-01-05  0.011111 -0.183333 -0.100000 -0.100000
2020-01-06  0.166667 -0.416667  0.166667 -0.416667
2020-01-07  0.128571 -0.571429  0.228571 -0.821429
```

1. We can still override any information passed to the factory class.

Notice that we did not need to call `vbt.IF(...)`? [IndicatorFactory.from_expr](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.from_expr)
is a class method that parses `input_names` and other information directly from the expression and
creates a factory instance using only this information. It is amazing how we reduced our first
implementation with `mov_avg_crossover` to just this while still enjoying all the features, right?

## Run methods

Once you have built your indicator class, it is time to run it. The primary method for executing an
indicator is the class method [IndicatorBase.run](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.run).
This method accepts positional and keyword arguments based on the specifications provided to the
[IndicatorFactory](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory).
These arguments include input arrays, in-place output arrays, and parameters. Any additional arguments
are forwarded down to [IndicatorBase.run_pipeline](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.run_pipeline), 
which may use them to set up the pipeline or forward them further down to the custom function
and, if provided, the apply function.

To see which arguments the `run` method accepts, use [phelp](https://vectorbt.pro/pvt_6d1b3986/api/utils/formatting/#vectorbtpro.utils.formatting.phelp):

```pycon
>>> vbt.phelp(MADiff.run)
MADiff.run(
    ts1,
    ts2,
    w1,
    w2,
    short_name='madiff',
    hide_params=None,
    hide_default=True,
    **kwargs
):
    Run `MADiff` indicator.
    
    * Inputs: `ts1`, `ts2`
    * Parameters: `w1`, `w2`
    * Outputs: `out`
    
    Pass a list of parameter names as `hide_params` to hide their column levels.
    Set `hide_default` to False to show the column levels of the parameters with a default value.
    
    Other keyword arguments are passed to `MADiff.run_pipeline`.
```

We can see that `MADiff.run` takes two input time series, `ts1` and `ts2`, two parameters, `w1` and `w2`,
and produces a single output time series, `diff`. When you call the class method, it runs the indicator
and returns a new instance of `MADiff` with all data ready for analysis. Specifically,
you can access the output as a regular instance attribute, `MADiff.diff`.

The second method for running indicators is [IndicatorBase.run_combs](https://vectorbt.pro/pvt_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorBase.run_combs).
This method accepts the same inputs as the method above, but computes all combinations of the given
parameters using a combinatorial function and returns **multiple** indicator instances that can be
combined with each other. This is useful for comparing multiple indicators of the **same type** but with
different parameters, such as when testing a moving average crossover, which involves two
[MA](https://vectorbt.pro/pvt_6d1b3986/api/indicators/custom/ma/#vectorbtpro.indicators.custom.ma.MA) instances applied to the same time series:

```pycon
>>> ts = pd.Series([3, 2, 1, 2, 3])
>>> fast_ma, slow_ma = vbt.MA.run_combs(
...     ts, [2, 3, 4], 
...     short_names=['fast_ma', 'slow_ma'])
>>> fast_ma.ma_crossed_above(slow_ma)
fast_ma_window             2      3
slow_ma_window      3      4      4
0               False  False  False
1               False  False  False
2               False  False  False
3               False  False  False
4                True   True  False
```

In the example above, [MA.run_combs](https://vectorbt.pro/pvt_6d1b3986/api/indicators/custom/ma/#vectorbtpro.indicators.custom.MA.ma.run_combs)
generated the combinations of `window` using [itertools.combinations](https://docs.python.org/3/library/itertools.html#itertools.combinations)
with `r=2`. The first set of window combinations was passed to the first instance, and the second set
to the second instance. The same example can be replicated using only the `run` method:

```pycon
>>> windows = [2, 3, 4]
>>> fast_windows, slow_windows = zip(*combinations(windows, 2))
>>> fast_ma = vbt.MA.run(ts, fast_windows, short_name='fast_ma')
>>> slow_ma = vbt.MA.run(ts, slow_windows, short_name='slow_ma')
>>> fast_ma.ma_crossed_above(slow_ma)
fast_ma_window             2      3
slow_ma_window      3      4      4
0               False  False  False
1               False  False  False
2               False  False  False
3               False  False  False
4                True   True  False
```

The main advantage of a single `run_combs` call over multiple `run` calls is that it does not need to
re-compute each combination, thanks to smart caching.

!!! note
    `run_combs` should only be used for combining multiple indicators. To test multiple
    parameter combinations, use `run` and provide parameters as lists.

## Preset indicators

VBT provides a collection of preset, fully Numba-compiled indicators (such as 
[ATR](https://vectorbt.pro/pvt_6d1b3986/api/indicators/custom/atr/#vectorbtpro.indicators.custom.atr.ATR)) that benefit from 
manual caching, extension, and plotting. You can use them as inspiration
for how to create indicators in a classic yet efficient way.

!!! note
    VBT uses SMA and EMA, while other technical analysis libraries and TradingView use
    Wilder's method. There is no right or wrong method.
    See [different smoothing methods](https://www.macroption.com/atr-calculation/).

[:material-language-python: Python code](https://vectorbt.pro/pvt_6d1b3986/assets/jupytext/documentation/indicators/index.py.txt){ .md-button target="blank_" }