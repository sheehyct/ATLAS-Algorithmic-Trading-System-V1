---
title: Datetime
description: Recipes for working with datetime objects in VectorBT PRO
icon: material/calendar
---

# :material-calendar: Datetime

VBT values flexibility, allowing you to create a variety of datetime-related objects from human-readable strings.

## Timestamps

Timestamps represent a single point in time, similar to a datetime object in Python's `datetime` module,
but with enhanced features for data analysis and manipulation.

```python title="How to construct a timestamp"
vbt.timestamp()  # (1)!
vbt.utc_timestamp()  # (2)!
vbt.local_timestamp()  # (3)!
vbt.timestamp(tz="America/New_York")  # (4)!
vbt.timestamp("1 Jul 2020")  # (5)!
vbt.timestamp("7 days ago")  # (6)!
```

1. `pd.Timestamp.now()` (without timezone).
2. `pd.Timestamp.now(tz="utc")` (UTC timezone).
3. `pd.Timestamp.now(tz="tzlocal()")` (local timezone).
4. `pd.Timestamp.now(tz="New_York/America")` (New York timezone).
5. `pd.Timestamp("2020-07-01")`.
6. `pd.Timestamp.now() - pd.Timedelta(days=7)`.

## Timezones

Timezones can be used in timestamps, making them a powerful tool for global time-based data analysis.

```python title="How to construct a timezone"
vbt.timezone()  # (1)!
vbt.timezone("utc")  # (2)!
vbt.timezone("America/New_York")  # (3)!
vbt.timezone("+0500")  # (4)!
```

1. Local timezone.
2. UTC timezone.
3. New York timezone.
4. UTC+5 timezone.

## Timedeltas

Timedeltas handle continuous time spans and precise time differences. They are commonly used for adding or
subtracting durations from timestamps, or for measuring the difference between two timestamps.

```python title="How to construct a timedelta"
vbt.timedelta()  # (1)!
vbt.timedelta("7 days")  # (2)!
vbt.timedelta("weekly")
vbt.timedelta("Y", approximate=True)  # (3)!
```

1. `pd.Timedelta(nanoseconds=1)`.
2. `pd.Timedelta(days=7)`.
3. Approximation for a year.

## Date offsets

Date offsets handle calendar-specific offsets, such as adding a month or skipping weekends with business
days. They are often used for calendar-aware adjustments and recurring periods.

```python title="How to construct a date offset"
vbt.offset("Y")  # (1)!
vbt.offset("YE")  # (2)!
vbt.offset("weekstart")  # (3)!
vbt.offset("monday")
vbt.offset("july")  # (4)!
```

1. `pd.offsets.YearBegin()` (every year begin).
2. `pd.offsets.YearEnd()` (every year end).
3. `pd.offsets.Week(weekday=0)` (every Monday).
4. `pd.offsets.YearBegin(month=7)` (every July).