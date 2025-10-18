---
title: Arrays
description: Recipes for working with arrays in VectorBT PRO
icon: material/table-multiple
---

# :material-table-multiple: Arrays

## Displaying

Any array, whether it is a NumPy array, Pandas object, or regular list, can be displayed as a table
using [ptable](https://vectorbt.pro/pvt_6d1b3986/api/utils/formatting/#vectorbtpro.utils.formatting.ptable), regardless of its size.
When called in an IPython environment such as Jupyter Lab, the table becomes interactive.

```python title="Print out an array in various ways"
vbt.ptable(df)  # (1)!
vbt.ptable(df, ipython=False)  # (2)!
vbt.ptable(df, ipython=False, tabulate=False)  # (3)!
```

1. Selects a table format based on the current environment.
2. Prints the table as a string formatted by [`tabulate`](https://github.com/astanin/python-tabulate).
3. Prints the table as a string formatted by Pandas.

## Wrapper

A wrapper can be extracted from any array-like object using
[ArrayWrapper.from_obj](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.from_obj).

```python title="Extract the wrapper from various objects"
wrapper = data.symbol_wrapper  # (1)!
wrapper = pf.wrapper  # (2)!
wrapper = df.vbt.wrapper  # (3)!

wrapper = vbt.ArrayWrapper.from_obj(sr)  # (4)!
```

1. `data.wrapper` returns an OHLC wrapper.
2. Most VBT objects have a `wrapper` attribute.
3. The wrapper for a Pandas Series or DataFrame can be accessed through the accessor.
4. Lets VBT extract the wrapper.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

An empty Pandas array can be created with
[ArrayWrapper.fill](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.fill).

```python title="Create an empty array with the same shape, index, and columns as in another array"
new_float_df = wrapper.fill(np.nan)  # (1)!
new_bool_df = wrapper.fill(False)  # (2)!
new_int_df = wrapper.fill(-1)  # (3)!
```

1. Creates a floating-point array.
2. Creates a boolean array.
3. Creates an integer or categorical array.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

A NumPy array can be wrapped with a Pandas Series or DataFrame using
[ArrayWrapper.wrap](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.wrap).

```python title="Convert NumPy array to Pandas"
df = wrapper.wrap(arr)
```

## Product

The product of multiple DataFrames can be achieved using the accessor method
[BaseAccessor.x](https://vectorbt.pro/pvt_6d1b3986/api/base/accessors/#vectorbtpro.base.accessors.BaseAccessor.x).
This method can be called either as an instance method or as a class method.

```python title="Cross-join columns of multiple DataFrames"
new_df1, new_df2 = df1.vbt.x(df2)  # (1)!
new_df1, new_df2, new_df3 = df1.vbt.x(df2, df3)  # (2)!
new_dfs = vbt.pd_acc.x(*dfs)  # (3)!
```

1. For two DataFrames.
2. For three DataFrames.
3. For a variable number of DataFrames.