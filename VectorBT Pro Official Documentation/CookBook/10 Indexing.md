---
title: Indexing
description: Recipes for indexing objects in VectorBT PRO
icon: material/button-pointer
---

# :material-button-pointer: Indexing

Most VBT objects, such as data instances and portfolios, can be indexed like regular Pandas objects
using the `[]`, `iloc`, `loc`, and `xs` selectors. The operation applies to all arrays within the
instance, and creates a new instance containing the selected arrays.

```python title="Select a date range of a Data instance"
new_data = data.loc["2020-01-01":"2020-12-31"]
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

There is also a special selector, `xloc`, that accepts a smart indexing instruction. Such an
instruction can include one or more positions, labels, dates, times, ranges, frequencies, or even date
offsets. It is automatically parsed and translated into an array with integer positions, which are then
internally passed to the `iloc` selector.

```python title="Various smart row indexing operations on a Data instance"
new_data = data.xloc[::2]  # (1)!
new_data = data.xloc[np.array([10, 20, 30])]  # (2)!
new_data = data.xloc["2020-01-01 17:30"]  # (3)!
new_data = data.xloc["2020-01-01"]  # (4)!
new_data = data.xloc["2020-01"]  # (5)!
new_data = data.xloc["2020"]  # (6)!
new_data = data.xloc["2020-01-01":"2021-01-01"]  # (7)!
new_data = data.xloc["january":"april"]  # (8)!
new_data = data.xloc["monday":"saturday"]  # (9)!
new_data = data.xloc["09:00":"16:00"]  # (10)!
new_data = data.xloc["16:00":"09:00"]  # (11)!
new_data = data.xloc["monday 09:00":"friday 16:00"]  # (12)!
new_data = data.xloc[
    vbt.autoidx(slice("monday", "friday"), closed_end=True) &  # (13)!
    vbt.autoidx(slice("09:00", "16:00"), closed_end=False)
]
new_data = data.xloc["Y"]  # (14)!
new_data = data.xloc[pd.Timedelta(days=7)]  # (15)!
new_data = data.xloc[df.index.weekday == 0]  # (16)!
new_data = data.xloc[pd.tseries.offsets.BDay()]  # (17)!
```

1. Every second row.
2. Rows 10, 20, and 30.
3. All rows that match the datetime 2020-01-01 17:30.
4. All rows that match the day 2020-01-01.
5. All rows that match the month 2020-01.
6. All rows that match the year 2020.
7. All rows from 2020-01-01 to 2020-12-31 (exclusive).
8. From January to April (exclusive).
9. From Monday to Saturday (exclusive).
10. Between 09:00 and 16:00 (exclusive).
11. Between 16:00 and 09:00 (exclusive).
12. Datetime components can also be combined. Here, between Monday 09:00 and Friday 16:00
(exclusive).
13. Indexers can also be combined like masks. Here, from Monday to Friday (inclusive) between 09:00
and 16:00 (exclusive).
14. Every year start (frequency string).
15. Every 7 days (timedelta).
16. Every Monday (mask).
17. Every business day ([date offset](https://pandas.pydata.org/docs/user_guide/timeseries.html#dateoffset-objects)).

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can select not only rows but also columns by combining
[rowidx](https://vectorbt.pro/pvt_6d1b3986/api/base/indexing/#vectorbtpro.base.indexing.RowIdxr) and
[colidx](https://vectorbt.pro/pvt_6d1b3986/api/base/indexing/#vectorbtpro.base.indexing.ColIdxr) instructions.

```python title="Various smart row and/or column indexing operations on a DataFrame accessor"
new_df = df.vbt.xloc[vbt.colidx(0)].get()  # (1)!
new_df = df.vbt.xloc[vbt.colidx("BTC-USD")].get()  # (2)!
new_df = df.vbt.xloc[vbt.colidx((10, "simple", "BTC-USD"))].get()  # (3)!
new_df = df.vbt.xloc[vbt.colidx("BTC-USD", level="symbol")].get()  # (4)!
new_df = df.vbt.xloc["2020", "BTC-USD"].get()  # (5)!
```

1. First column.
2. Column label "BTC-USD".
3. Column label (10, "simple", "BTC-USD").
4. Any column with symbol "BTC-USD".
5. Year 2020 and column label "BTC-USD". Both can also be wrapped with `rowidx` and `colidx`
respectively, for example, to pass indexer-related keyword arguments.

!!! info
    Without the `get()` call, the accessor will be returned. There is __no need__ for this call
    when indexing other VBT objects, such as portfolios.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Pandas accessors can also be used to modify values under certain rows and columns.
This is not possible for more complex VBT objects.

```python title="Enter at the beginning of the business day, exit at the end"
entries.vbt.xloc[vbt.autoidx(slice("mon", "sat")) & vbt.autoidx("09:00")] = True  # (1)!
exits.vbt.xloc[vbt.autoidx(slice("mon", "sat")) & (vbt.autoidx("16:00") << 1)] = True  # (2)!

entries.vbt.xloc[vbt.pointidx(every="B", at_time="09:00")] = True  # (3)!
exits.vbt.xloc[vbt.pointidx(every="B", at_time="16:00", indexer_method="before")] = True
```

1. Saturday is exclusive.
2. The operation `<< 1` shifts the mask backward to get the last time before 16:00.
3. Another approach by using [PointIdxr](https://vectorbt.pro/pvt_6d1b3986/api/base/indexing/#vectorbtpro.base.indexing.PointIdxr)
with a business day frequency.