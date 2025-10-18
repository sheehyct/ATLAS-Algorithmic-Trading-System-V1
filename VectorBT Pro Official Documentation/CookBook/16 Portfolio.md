---
title: Portfolio
description: Recipes for simulating and analyzing portfolios in VectorBT PRO
icon: material/chart-areaspline
---

# :material-chart-areaspline: Portfolio

!!! question
    Find more information in the [Portfolio documentation](https://vectorbt.pro/pvt_6d1b3986/documentation/portfolio/).

## From data

To quickly simulate a portfolio from any OHLC data, you can use [Data.run](https://vectorbt.pro/pvt_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.run)
or pass the data instance (or simply a symbol or `class_name:symbol`) to the simulation method.

```python title="Various way to quickly simulate a portfolio from a Data instance"
pf = data.run("from_holding")  # (1)!
pf = data.run("from_random_signals", n=10)  # (2)!

pf = vbt.PF.from_holding(data)  # (3)!
pf = vbt.PF.from_holding("BTC-USD")  # (4)!
pf = vbt.PF.from_holding("BinanceData:BTCUSDT")  # (5)!
```

1. Simulate a buy-and-hold portfolio from data.
2. Simulate a portfolio from data with 10 entries and 10 exits placed randomly.
3. Same as the first line.
4. Retrieve the symbol "BTC-USD" from Yahoo Finance (default) and simulate a buy-and-hold portfolio.
5. Retrieve the symbol "BTCUSDT" from Binance and simulate a buy-and-hold portfolio.

## From signals

This simulation method is easy to use yet powerful, as long as your strategy can be defined
using signals, such as buy, sell, short sell, and buy to cover.

```python title="Various signal configurations"
pf = vbt.PF.from_signals(data, ...)  # (1)!
pf = vbt.PF.from_signals(open=open, high=high, low=low, close=close, ...)  # (2)!
pf = vbt.PF.from_signals(close, ...)  # (3)!

pf = vbt.PF.from_signals(data, entries, exits)  # (4)!
pf = vbt.PF.from_signals(data, entries, exits, direction="shortonly")  # (5)!
pf = vbt.PF.from_signals(data, entries, exits, direction="both")  # (6)!
pf = vbt.PF.from_signals(  # (7)!
    data, 
    long_entries=long_entries, 
    long_exits=long_exits,
    short_entries=short_entries, 
    short_exits=short_exits,
)
```

1. When a data instance is passed (not a DataFrame!), VBT will extract OHLC data automatically.
2. Same as above, but all price features are passed manually.
3. For tick data or when OHL is not available, pass only the close price.
4. Enter a long position when `entries` is True and exit it when `exits` is True (no short positions).
5. Enter a short position when `entries` is True and exit it when `exits` is True (no long positions).
6. Enter a long position when `entries` is True and a short position when `exits` is True, using reversals.
7. Enter a long position when `long_entries` is True, exit it when `long_exits` is True, enter a short
position when `short_entries` is True, and exit it when `short_exits` is True.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To set different prices or other arguments for long and short signals, create an empty array 
and use each signal type as a mask to assign the corresponding value.

```python title="Manually apply a 1% slippage to the price"
price = data.symbol_wrapper.fill()
price[entries] = data.close * (1 + 0.01)  # (1)!
price[exits] = data.close * (1 - 0.01)
```

1. Entries and exits here are masks: assign values where their value is True.
If you want to replace `data.close` with a NumPy array, use `arr[entries]` on the right side as well.

```python title="Use the ask price for buying and the bid price for selling"
price = (bid_price + ask_price) / 2
price[entries] = ask_price
price[exits] = bid_price
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To exit a trade after a specific amount of time or number of rows, use the `td_stop` argument.
The measurement starts from the opening time of the entry row.

```python title="How to close out a position after some time"
pf = vbt.PF.from_signals(..., td_stop="7 days")  # (1)!
pf = vbt.PF.from_signals(..., td_stop=pd.Timedelta(days=7))
pf = vbt.PF.from_signals(..., td_stop=td_arr)  # (2)!

pf = vbt.PF.from_signals(..., td_stop=7, time_delta_format="rows")  # (3)!
pf = vbt.PF.from_signals(..., td_stop=int_arr, time_delta_format="rows")  # (4)!

pf = vbt.PF.from_signals(..., td_stop=vbt.Param(["1 day", "7 days"]))  # (5)!
```

1. Exit after 7 days.
2. Specify a custom timedelta for each row using an array. For example, you can use 
[`pd.TimedeltaIndex`](https://pandas.pydata.org/docs/reference/api/pandas.TimedeltaIndex.html).
3. Exit after 7 rows (i.e., bars).
4. For each potential entry row, specify after how many rows to exit.
5. Any of the above examples can be tested as a parameter.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To exit a trade at a specific time or row count, use the `dt_stop` argument.
If you pass a timedelta (as above), the position will be exited at the last bar _before_ the target date.
Otherwise, if you provide an exact date or time, the position will be exited _at_ or _after_ that point.
You can override this behavior using the argument config.

```python title="How to close out a position at some time"
import datetime

pf = vbt.PF.from_signals(..., dt_stop="daily")  # (1)!
pf = vbt.PF.from_signals(..., dt_stop=pd.Timedelta(days=1))
pf = vbt.PF.from_signals(  # (2)!
    ..., 
    dt_stop="daily", 
    arg_config=dict(dt_stop=dict(last_before=False))
)

pf = vbt.PF.from_signals(..., dt_stop="16:00")  # (3)!
pf = vbt.PF.from_signals(..., dt_stop=datetime.time(16, 0))
pf = vbt.PF.from_signals(  # (4)!
    ..., 
    dt_stop="16:00", 
    arg_config=dict(dt_stop=dict(last_before=True))
)

pf = vbt.PF.from_signals(..., dt_stop="2024-01-01")  # (5)!
pf = vbt.PF.from_signals(..., dt_stop=pd.Timestamp("2024-01-01"))
pf = vbt.PF.from_signals(  # (6)!
    ..., 
    dt_stop="2024-01-01", 
    arg_config=dict(dt_stop=dict(last_before=True))
)
pf = vbt.PF.from_signals(..., dt_stop=dt_arr)  # (7)!

pf = vbt.PF.from_signals(..., dt_stop=int_arr, time_delta_format="rows")  # (8)!

pf = vbt.PF.from_signals(..., dt_stop=vbt.Param(["1 day", "7 days"]))  # (9)!
```

1. Exit at the last bar before the end of the day.
2. Exit at or after the end of the day.
3. Exit at or after 16:00.
4. Exit at the last bar before 16:00.
5. Exit on or after January 1, 2024. This applies only to entries issued before that date.
6. Exit at the last bar before January 1, 2024. This applies only to entries issued before that date.
7. Specify a custom datetime for each row using an array. For example, you can use 
[`pd.DatetimeIndex`](https://pandas.pydata.org/docs/reference/api/pandas.DatetimeIndex.html).
8. For each potential entry row, specify at which row to exit.
9. Any of the above examples can be tested as a parameter.

!!! note
    Do not confuse `td_stop` with `dt_stop`. "td" stands for timedelta, while 
    "dt" stands for datetime.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To perform multiple actions within a single bar, split each bar into three sub-bars:
opening nanosecond, middle, and closing nanosecond. For example, you can execute your signals at the
end of the bar, and your stop orders will be guaranteed to execute at the first two sub-bars. This lets
you close out a position and enter a new one within the same bar.

```python title="Execute entries at open, exits at close"
x3_open = open.vbt.repeat(3, axis=0)  # (1)!
x3_high = high.vbt.repeat(3, axis=0)
x3_low = low.vbt.repeat(3, axis=0)
x3_close = close.vbt.repeat(3, axis=0)
x3_entries = entries.vbt.repeat(3, axis=0)
x3_exits = exits.vbt.repeat(3, axis=0)

bar_open = slice(0, None, 3)  # (2)!
bar_middle = slice(1, None, 3)
bar_close = slice(2, None, 3)

x3_high.iloc[bar_open] = open.copy()  # (3)!
x3_low.iloc[bar_open] = open.copy()
x3_close.iloc[bar_open] = open.copy()

x3_open.iloc[bar_close] = close.copy()  # (4)!
x3_high.iloc[bar_close] = close.copy()
x3_low.iloc[bar_close] = close.copy()

x3_entries.iloc[bar_middle] = False  # (5)!
x3_entries.iloc[bar_close] = False

x3_exits.iloc[bar_open] = False  # (6)!
x3_exits.iloc[bar_middle] = False

x3_index = pd.Series(x3_close.index)  # (7)!
x3_index.iloc[bar_middle] += pd.Timedelta(nanoseconds=1)
x3_index.iloc[bar_close] += index.freq - pd.Timedelta(nanoseconds=1)
x3_index = pd.Index(x3_index)
x3_open.index = x3_index
x3_high.index = x3_index
x3_low.index = x3_index
x3_close.index = x3_index
x3_entries.index = x3_index
x3_exits.index = x3_index

x3_pf = vbt.PF.from_signals(  # (8)!
    open=x3_open,
    high=x3_high,
    low=x3_low,
    close=x3_close,
    entries=x3_entries,
    exits=x3_exits,
)
pf = x3_pf.resample(close.index, freq=False, silence_warnings=True)  # (9)!
```

1. Split each array into three sub-bars.
2. These slices are used to index a specific sub-bar. They can be applied only with `iloc` or on NumPy
arrays.
3. Set OHLC to open at the first nanosecond.
4. Set OHLC to close at the last nanosecond.
5. Enable entries only at the open, and disable them at other sub-bars.
6. Enable exits only at the close, and disable them at other sub-bars.
7. Prepare the index.
8. Run the simulation.
9. Resample back to the original index.

### Callbacks

To save a piece of information at one timestamp and reuse it at a later timestamp in a callback,
create a NumPy array and pass it to the callback. The array should be one-dimensional and have the
same number of elements as there are columns. You can then read and write the element under the
current column using the same method as accessing the latest position via `c.last_position[c.col]`.
If you need to store more pieces of information, use additional arrays or a single structured array.
For convenience, you can combine multiple arrays into a named tuple.

```python title="Execute only the first signal"
from collections import namedtuple

Memory = namedtuple("Memory", ["signal_executed"])

@njit
def signal_func_nb(c, entries, exits, memory):
    is_entry = vbt.pf_nb.select_nb(c, entries)
    is_exit = vbt.pf_nb.select_nb(c, exits)
    if is_entry and not memory.signal_executed[c.col]:  # (1)!
        memory.signal_executed[c.col] = True  # (2)!
        return True, False, False, False
    if is_exit:
        return False, True, False, False
    return False, False, False, False
    
def init_memory(target_shape):
    return Memory(
        signal_executed=np.full(target_shape[1], False)  # (3)!
    )
    
pf = vbt.PF.from_signals(
    ...,
    entries=entries,
    exits=exits,
    signal_func_nb=signal_func_nb,
    signal_args=(
        vbt.Rep("entries"), 
        vbt.Rep("exits"), 
        vbt.RepFunc(init_memory)
    )
)
```

1. Read the element under the current column.
2. Write the element under the current column.
3. Create a boolean array filled with False, with one element per column.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To overcome the limitation of having only one active built-in limit order at a time, you can create
custom limit orders. This allows you to have multiple active orders at once. Store relevant data in
memory and manually check if the limit order price has been reached on each bar. When the price is
hit, simply generate a signal.

```python title="Breakout strategy by straddling current price with opposing limit orders"
Memory = namedtuple("Memory", ["signal_price"])  # (1)!

@njit
def signal_func_nb(c, signals, memory, limit_delta):
    if np.isnan(memory.signal_price[c.col]):
        signal = vbt.pf_nb.select_nb(c, signals)
        if signal:
            memory.signal_price[c.col] = vbt.pf_nb.select_nb(c, c.close)  # (2)!
    else:
        open = vbt.pf_nb.select_nb(c, c.open)
        high = vbt.pf_nb.select_nb(c, c.high)
        low = vbt.pf_nb.select_nb(c, c.low)
        close = vbt.pf_nb.select_nb(c, c.close)
        above_price = vbt.pf_nb.resolve_limit_price_nb(  # (3)!
            init_price=memory.signal_price[c.col],
            limit_delta=limit_delta,
            hit_below=False
        )
        hit_price, _, _ = vbt.pf_nb.check_price_hit_nb(  # (4)!
            open=open,
            high=high,
            low=low,
            close=close,
            price=above_price,
            hit_below=False
        )
        if not np.isnan(hit_price):
            memory.signal_price[c.col] = np.nan
            return True, False, False, False  # (5)!
        below_price = vbt.pf_nb.resolve_limit_price_nb(  # (6)!
            init_price=memory.signal_price[c.col],
            limit_delta=limit_delta,
            hit_below=True
        )
        hit_price, _, _ = vbt.pf_nb.check_price_hit_nb(
            open=open,
            high=high,
            low=low,
            close=close,
            price=below_price,
            hit_below=True
        )
        if not np.isnan(hit_price):
            memory.signal_price[c.col] = np.nan
            return False, False, True, False
    return False, False, False, False

def init_memory(target_shape):
    return Memory(
        signal_price=np.full(target_shape[1], np.nan)
    )

pf = vbt.PF.from_signals(
    ...,
    signal_func_nb=signal_func_nb,
    signal_args=(
        vbt.Rep("signals"), 
        vbt.RepFunc(init_memory),
        0.1
    ),
    broadcast_named_args=dict(
        signals=signals
    )
)
```

1. Memory with a single array: the price at the time when the latest user signal occurred.
2. Whenever a user signal occurs, save the current price and skip the current bar.
3. Resolve the limit price (i.e., signal price plus delta) for going long.
4. Check whether the limit price has been hit.
5. If so, clear the memory for this asset and return a long entry.
6. The same logic applies for a short entry.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

If signals are generated dynamically and only a subset are actually executed, you may want to keep 
track of all generated signals for later analysis. To do this, use function templates to create 
__global__ custom arrays and fill these arrays during the simulation.

```python title="Place entries and exits randomly and access them outside the simulation"
custom_arrays = dict()

def create_entries_out(wrapper):  # (1)!
    entries_out = np.full(wrapper.shape_2d, False)
    custom_arrays["entries"] = entries_out  # (2)!
    return entries_out

def create_exits_out(wrapper):
    exits_out = np.full(wrapper.shape_2d, False)
    custom_arrays["exits"] = exits_out
    return exits_out

@njit
def signal_func_nb(c, entry_prob, exit_prob, entries_out, exits_out):
    entry_prob_now = vbt.pf_nb.select_nb(c, entry_prob)
    exit_prob_now = vbt.pf_nb.select_nb(c, exit_prob)
    if np.random.uniform(0, 1) < entry_prob_now:
        is_entry = True
        entries_out[c.i, c.col] = True  # (3)!
    else:
        is_entry = False
    if np.random.uniform(0, 1) < exit_prob_now:
        is_exit = True
        exits_out[c.i, c.col] = True
    else:
        is_exit = False
    return is_entry, is_exit, False, False

pf = vbt.PF.from_signals(
    ...,
    signal_func_nb=signal_func_nb,
    signal_args=(
        vbt.Rep("entry_prob"), 
        vbt.Rep("exit_prob"), 
        vbt.RepFunc(create_entries_out),  # (4)!
        vbt.RepFunc(create_exits_out),
    ),
    broadcast_named_args=dict(
        entry_prob=0.1,
        exit_prob=0.1
    )
)

print(custom_arrays)
```

1. Function to create an empty NumPy array. The wrapper contains the shape of the simulation.
2. Store a reference to the array for later use.
3. Write information to the array.
4. Use a template to call the function once the shape of the simulation is known.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To limit the number of active positions within a group, disable any entry signal in a custom signal
function whenever the limit has been reached. The exit signal should be allowed to execute at any time.

```python title="Allow at most one active position at a time"
@njit
def signal_func_nb(c, entries, exits, max_active_positions):
    is_entry = vbt.pf_nb.select_nb(c, entries)
    is_exit = vbt.pf_nb.select_nb(c, exits)
    n_active_positions = vbt.pf_nb.get_n_active_positions_nb(c)
    if n_active_positions >= max_active_positions:
        return False, is_exit, False, False  # (1)!
    return is_entry, is_exit, False, False

pf = vbt.PF.from_signals(
    ...,
    entries=entries,
    exits=exits,
    signal_func_nb=signal_func_nb,
    signal_args=(vbt.Rep("entries"), vbt.Rep("exits"), 1),
    group_by=True  # (2)!
)
```

1. Disable any entry signal.
2. Combine all assets into one group. This can be customized.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To access information on the current or previous position, query the position information records.

```python title="Ignore entries for a number of days after a losing trade"
@njit
def signal_func_nb(c, entries, exits, cooldown):
    entry = vbt.pf_nb.select_nb(c, entries)
    exit = vbt.pf_nb.select_nb(c, exits)
    if not vbt.pf_nb.in_position_nb(c):
        if vbt.pf_nb.has_orders_nb(c):
            if c.last_pos_info[c.col]["pnl"] < 0:  # (1)!
                last_exit_idx = c.last_pos_info[c.col]["exit_idx"]
                if c.index[c.i] - c.index[last_exit_idx] < cooldown:
                    return False, exit, False, False
    return entry, exit, False, False
    
pf = vbt.PF.from_signals(
    ...,
    signal_func_nb=signal_func_nb,
    signal_args=(
        vbt.Rep("entries"), 
        vbt.Rep("exits"), 
        vbt.dt.to_ns(vbt.timedelta("7D"))
    )
)
```

1. If not in a position, the position information records contain information about the last (closed) position.
2. Cooldown should be an integer representing the number of nanoseconds. Any timedelta
should be converted to nanoseconds before execution.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To activate a stop-loss (SL) or another stop order after a certain condition is met, set it initially 
to infinity. Then, update the stop value in a callback once the condition is satisfied.

```python title="Set SL to breakeven after price has moved a certain %"
@njit
def adjust_func_nb(c, perc):
    ...
    sl_stop = c.last_sl_info[c.col]
    if c.i > 0 and np.isinf(sl_stop["stop"]):  # (1)!
        prev_close = vbt.pf_nb.select_nb(c, c.close, i=c.i - 1)
        price_change = prev_close / sl_stop["init_price"] - 1
        if c.last_position[c.col] < 0:
            price_change *= -1
        if price_change >= perc:
            sl_stop["stop"] = 0.0  # (2)!

pf = vbt.PF.from_signals(
    ...,
    sl_stop=np.inf,
    stop_entry_price="fillprice",
    adjust_func_nb=adjust_func_nb, 
    adjust_args=(0.1,),
)
```

1. SL has not yet been activated.
2. Activate an SL order by setting the stop price to the initial price.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

The stop value can be updated not just once, but on every bar.

```python title="ATR-based TSL order"
@njit
def adjust_func_nb(c, atr):
    ...
    if c.i > 0:
        tsl_info = c.last_tsl_info[c.col]
        tsl_info["stop"] = vbt.pf_nb.select_nb(c, atr, i=c.i - 1)

pf = vbt.PF.from_signals(
    ...,
    tsl_stop=np.inf,
    stop_entry_price="fillprice",
    delta_format="absolute",
    broadcast_named_args=dict(atr=atr),
    adjust_func_nb=adjust_func_nb,
    adjust_args=(vbt.Rep("atr"),)
)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To set a ladder dynamically, use `stop_ladder="dynamic"` and then use the current ladder step in a 
callback to pull information from a custom array and override the stop information with that value.

```python title="Set a ladder based on ATR multipliers"
@njit
def adjust_func_nb(c, atr, multipliers, exit_sizes):
    tp_info = c.last_tp_info[c.col]
    if vbt.pf_nb.is_stop_info_ladder_active_nb(tp_info):
        if np.isnan(tp_info["stop"]):
            step = tp_info["step"]
            init_atr = vbt.pf_nb.select_nb(c, atr, i=tp_info["init_idx"])
            tp_info["stop"] = init_atr * multipliers[step]
            tp_info["delta_format"] = vbt.pf_enums.DeltaFormat.Absolute
            tp_info["exit_size"] = exit_sizes[step]
            tp_info["exit_size_type"] = vbt.pf_enums.SizeType.Percent
            
pf = vbt.PF.from_signals(
    ...,
    adjust_func_nb=adjust_func_nb,
    adjust_args=(
        vbt.Rep("atr"),
        np.array([1, 2]),
        np.array([0.5, 1.0])
    ),
    stop_ladder="dynamic",
    broadcast_named_args=dict(atr=atr)
)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Position metrics, such as the current open P&L and return, are available through the 
`last_pos_info` context field. This is an array with one record per column, using the data type
[trade_dt](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.trade_dt).

```python title="By hitting an unrealized profit of 100%, lock in 50% of it with SL"
@njit
def adjust_func_nb(c, x, y):  # (1)!
    pos_info = c.last_pos_info[c.col]
    if pos_info["status"] == vbt.pf_enums.TradeStatus.Open:
        if pos_info["return"] >= x:
            sl_info = c.last_sl_info[c.col]
            if not vbt.pf_nb.is_stop_info_active_nb(sl_info):
                entry_price = pos_info["entry_price"]
                if vbt.pf_nb.in_long_position_nb(c):
                    x_price = entry_price * (1 + x)  # (2)!
                    y_price = entry_price * (1 + y)  # (3)!
                else:
                    x_price = entry_price * (1 - x)
                    y_price = entry_price * (1 - y)
                vbt.pf_nb.set_sl_info_nb(
                    sl_info, 
                    init_idx=c.i, 
                    init_price=x_price,
                    stop=y_price,
                    delta_format=vbt.pf_enums.DeltaFormat.Target
                )
                
pf = vbt.PF.from_signals(
    ..., 
    adjust_func_nb=adjust_func_nb,
    adjust_args=(1.0, 0.5)
)
```

1. Both arguments (x = return as %, y = SL as %) should be provided as single values.
2. The SL is triggered at the price where `x` was reached.
3. The target price of the SL is calculated relative to the entry price so that `x` and `y` use the same scale
   (for example, 10% and 10% -> 0% final return).

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To dynamically determine and apply an optimal position size, create an empty size array filled with NaN.
Then, in a callback, calculate the target size and write it to the size array.

```python title="Risk only 1% of the cash balance with each trade"
@njit
def adjust_func_nb(c, size, sl_stop, delta_format, risk_amount):
    close_now = vbt.pf_nb.select_nb(c, c.close)
    sl_stop_now = vbt.pf_nb.select_nb(c, sl_stop)
    delta_format_now = vbt.pf_nb.select_nb(c, delta_format)
    risk_amount_now = vbt.pf_nb.select_nb(c, risk_amount)
    free_cash_now = vbt.pf_nb.get_free_cash_nb(c)
        
    stop_price = vbt.pf_nb.resolve_stop_price_nb(
        init_price=close_now,
        stop=sl_stop_now,
        delta_format=delta_format_now,
        hit_below=True
    )
    price_diff = abs(close_now - stop_price)
    size[c.i, c.col] = risk_amount_now * free_cash_now / price_diff

pf = vbt.PF.from_signals(
    ...,
    adjust_func_nb=adjust_func_nb,
    adjust_args=(
        vbt.Rep("size"), 
        vbt.Rep("sl_stop"), 
        vbt.Rep("delta_format"), 
        vbt.Rep("risk_amount")
    ),
    size=vbt.RepFunc(lambda wrapper: np.full(wrapper.shape_2d, np.nan)),
    sl_stop=0.1,
    delta_format="percent",
    broadcast_named_args=dict(risk_amount=0.01)
)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To ensure SL/TP considers the average entry price, rather than just the first order entry price,
when accumulation is enabled, set the initial price of the stop record to the position's entry price.

```python title="Apply an SL of 10% to the accumulated position"
@njit
def post_signal_func_nb(c):
    if vbt.pf_nb.order_increased_position_nb(c):
        c.last_sl_info[c.col]["init_price"] = c.last_pos_info[c.col]["entry_price"]
        
pf = vbt.PF.from_signals(
    ...,
    accumulate="addonly",
    sl_stop=0.1,
    post_signal_func_nb=post_signal_func_nb,
)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To check at the end of a bar whether a signal has been executed, use `post_signal_func_nb`
or `post_segment_func_nb`. The first is called right after an order is executed and can
access the result of the executed order through `c.order_result`. The second is called
after all columns in the current group have been processed (just one column if there is no grouping),
cash deposits and earnings have been applied, and the portfolio value and returns have been updated.

```python title="Apply a 20% tax on any positive P&L generated from closing out a position"
@njit
def post_signal_func_nb(c, cash_earnings, tax):
    if vbt.pf_nb.order_closed_position_nb(c):
        pos_info = c.last_pos_info[c.col]
        pnl = pos_info["pnl"]
        if pnl > 0:
            cash_earnings[c.i, c.col] = -tax * pnl
    
tax = 0.2
pf = vbt.PF.from_signals(
    ...,
    post_signal_func_nb=post_signal_func_nb,
    post_signal_args=(vbt.Rep("cash_earnings"), tax),
    cash_earnings=vbt.RepEval("np.full(wrapper.shape_2d, 0.0)")
)
```

!!! tip
    An alternative approach after creating the portfolio:

    ```python
    winning_positions = pf.positions.winning
    winning_idxs = winning_positions.end_idx.values
    winning_pnl = winning_positions.pnl.values
    cash_earnings = pf.get_cash_earnings(group_by=False)
    if pf.wrapper.ndim == 2:
        winning_cols = winning_positions.col_arr
        cash_earnings.values[winning_idxs, winning_cols] += -tax * winning_pnl
    else:
        cash_earnings.values[winning_idxs] += -tax * winning_pnl
    new_pf = pf.replace(cash_earnings=cash_earnings)
    ```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To access the running total return during the simulation, create an empty array for cumulative
returns and update it within the `post_segment_func_nb` callback. The same array can be accessed
by other callbacks to get the total return at any time step.

```python title="Access the running total return from within a simulation"
@njit
def adjust_func_nb(c, cum_return):
    if c.cash_sharing:
        total_return = cum_return[c.group] - 1
    else:
        total_return = cum_return[c.col] - 1
    ...  # (1)!

@njit
def post_segment_func_nb(c, cum_return):
    if c.cash_sharing:
        cum_return[c.group] *= 1 + c.last_return[c.group]
    else:
        for col in range(c.from_col, c.to_col):
            cum_return[col] *= 1 + c.last_return[col]
         
cum_return = None
def init_cum_return(wrapper):
    global cum_return
    if cum_return is None:
        cum_return = np.full(wrapper.shape_2d[1], 1.0)
    return cum_return
    
pf = vbt.PF.from_signals(
    ...,
    adjust_func_nb=adjust_func_nb,
    adjust_args=(vbt.RepFunc(init_cum_return),),
    post_segment_func_nb=post_segment_func_nb,
    post_segment_args=(vbt.RepFunc(init_cum_return),),
)
```

1. Your logic here.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can use the same process to access the running trade records during the simulation.

```python title="Access the running trade records from within a simulation"
from collections import namedtuple

TradeMemory = namedtuple("TradeMemory", ["trade_records", "trade_counts"])

@njit
def adjust_func_nb(c, trade_memory):
    trade_count = trade_memory.trade_counts[c.col]
    trade_records = trade_memory.trade_records[:trade_count, c.col]
    ...  # (1)!

@njit
def post_signal_func_nb(c, trade_memory):
    if vbt.pf_nb.order_filled_nb(c):
        exit_trade_records = vbt.pf_nb.get_exit_trade_records_nb(c)
        trade_memory.trade_records[:len(exit_trade_records), c.col] = exit_trade_records
        trade_memory.trade_counts[c.col] = len(exit_trade_records)
       
trade_memory = None
def init_trade_memory(target_shape):
    global trade_memory
    if trade_memory is None:
        trade_memory = TradeMemory(
            trade_records=np.empty(target_shape, dtype=vbt.pf_enums.trade_dt),  # (2)!
            trade_counts=np.full(target_shape[1], 0)
        )
    return trade_memory
    
pf = vbt.PF.from_random_signals(
    ...,
    post_signal_func_nb=post_signal_func_nb,
    post_signal_args=(vbt.RepFunc(init_trade_memory),),
)
```

1. Your logic here.
2. Create an array with the full shape to handle the worst case of one trade per bar.
If you expect fewer trades, you can limit the number of rows in the shape.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To execute an SL (or any other order type) on the same bar as the entry, you can check
whether the stop order is triggered on this bar and, if so, execute it as a regular signal on the next bar.

```python title="Execute each entry using open price and potentially SL at the same bar"
Memory = namedtuple("Memory", ["stop_price", "order_type"])
memory = None

def init_memory(target_shape):
    global memory
    if memory is None:
        memory = Memory(
            stop_price=np.full(target_shape, np.nan),
            order_type=np.full(target_shape, -1),
        )
    return memory

@njit
def signal_func_nb(c, price, memory, ...):
    if c.i > 0 and not np.isnan(memory.stop_price[c.i - 1, c.col]):
        price[c.i, c.col] = memory.stop_price[c.i - 1, c.col]
        return False, True, False, True
    ...


@njit
def post_signal_func_nb(c, memory, ...):
    if vbt.pf_nb.order_opened_position_nb(c):
        open = vbt.pf_nb.select_nb(c, c.open)
        high = vbt.pf_nb.select_nb(c, c.high)
        low = vbt.pf_nb.select_nb(c, c.low)
        close = vbt.pf_nb.select_nb(c, c.close)
        sl_stop_price, _, _ = vbt.pf_nb.check_stop_hit_nb(
            open=open,
            high=high,
            low=low,
            close=close,
            is_position_long=c.last_position[c.col] > 0,
            init_price=c.last_sl_info["init_price"][c.col],
            stop=c.last_sl_info["stop"][c.col],
            delta_format=c.last_sl_info["delta_format"][c.col],
            hit_below=True,
            can_use_ohlc=True,
            check_open=False,
            hard_stop=c.last_sl_info["exit_price"][c.col] == vbt.pf_enums.StopExitPrice.HardStop,
        )
        if not np.isnan(sl_stop_price):
            memory.stop_price[c.i, c.col] = sl_stop_price
            memory.order_type[c.i, c.col] = vbt.sig_enums.StopType.SL
            vbt.pf_nb.clear_sl_info_nb(c.last_sl_info[c.col])
            vbt.pf_nb.clear_tp_info_nb(c.last_tp_info[c.col])
        
    elif vbt.pf_nb.order_closed_position_nb(c):
        if memory.order_type[c.i - 1, c.col] != -1:
            order = c.order_records[c.order_counts[c.col] - 1, c.col]
            order["stop_type"] = memory.order_type[c.i - 1, c.col]
            order["signal_idx"] = c.i - 1
            order["creation_idx"] = c.i - 1
            order["idx"] = c.i - 1
    ...

pf = vbt.PF.from_signals(
    ...,
    signal_func_nb=signal_func_nb,
    signal_args=(vbt.Rep("price"), vbt.RepFunc(init_memory), ...),
    post_signal_func_nb=post_signal_func_nb,
    post_signal_args=(vbt.RepFunc(init_memory), ...),
    price=vbt.RepFunc(lambda wrapper: np.full(wrapper.shape_2d, -np.inf)),
    sl_stop=0.1,
    stop_entry_price="fillprice"
)
```

## Records

There are several ways to examine the orders, trades, and positions generated by a simulation.
Each one corresponds to a different concept in vectorbtpro. Be sure to understand their differences
by reviewing the examples at the top of the [trades](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/trades/) module.

```python title="Print out information on various records"
print(pf.orders.readable)  # (1)!
print(pf.entry_trades.readable)  # (2)!
print(pf.exit_trades.readable)  # (3)!
print(pf.trades.readable)  # (4)!
print(pf.positions.readable)  # (5)!

print(pf.trade_history)  # (6)!
```

1. Information on orders.
2. Information on trades that open or increase a position.
3. Information on trades that close or decrease a position.
4. Same as `exit_trades` by default.
5. Information on positions.
6. Information on orders and trades merged together.

## Metrics

By default, the year frequency is set to 365 days, assuming each trading day lasts 24 hours. However,
for stocks or other securities, you should change it to 252 days or less. Also, consider trading hours
when working with sub-daily data frequency.

```python title="Change the year frequency"
vbt.settings.returns.year_freq = "auto"  # (1)!

vbt.settings.returns.year_freq = "252 days"  # (2)!
vbt.settings.returns.year_freq = pd.Timedelta(days=252)  # (3)!
vbt.settings.returns.year_freq = pd.offsets.BDay() * 252  # (4)!
vbt.settings.returns.year_freq = pd.Timedelta(hours=6.5) * 252  # (5)!

returns_df.vbt.returns(year_freq="252 days").stats()  # (6)!
pf = vbt.PF.from_signals(..., year_freq="252 days")  # (7)!
```

1. Determine the year frequency automatically.
2. Change the year frequency to 252 days. Assumes daily frequency.
3. Same as above, set as a timedelta.
4. Same as above, set as a date offset (business days).
5. Account for 6.5 trading hours per day. Assumes intra-daily frequency.
6. Year frequency can also be set locally per DataFrame.
7. Year frequency can also be passed directly to the portfolio.

!!! info
    The year frequency will be divided by the frequency of your data to calculate the annualization
    factor. For example, `pd.Timedelta(hours=6.5) * 252` divided by `15 minutes` will result in a
    factor of 6552.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To tell VBT to place zero instead of infinity and NaN in any generated returns, create a
[configuration](https://vectorbt.pro/pvt_6d1b3986/cookbook/configuration/#settings) file (such as `vbt.config`) with the following
content:

```ini
[returns]
inf_to_nan = True
nan_to_zero = True
```

!!! note
    If this does not work, run `vbt.clear_pycache()` and restart the kernel.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To compute a metric based on the returns or other time series of each trade, rather than for the
entire equity, use projections to extract the time series range corresponding to each trade.

```python title="Calculate the average total log return of winning and losing trades"
winning_trade_returns = pf.trades.winning.get_projections(pf.log_returns, rebase=False)
losing_trade_returns = pf.trades.losing.get_projections(pf.log_returns, rebase=False)
avg_winning_trade_return = vbt.pd_acc.returns(winning_trade_returns, log_returns=True).total().mean()
avg_losing_trade_return = vbt.pd_acc.returns(losing_trade_returns, log_returns=True).total().mean()
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To calculate a trade metric purely in Numba, convert order records to trade records, compute the column
map for the trade records, and then reduce each column to a single number.

```python title="Calculate trade win rate in Numba"
order_records = sim_out.order_records  # (1)!

order_col_map = vbt.rec_nb.col_map_nb(
    order_records["col"],
    close.shape[1]  # (2)!
)
trade_records = vbt.pf_nb.get_exit_trades_nb(
    order_records, 
    close, 
    order_col_map
)
trade_col_map = vbt.rec_nb.col_map_nb(
    trade_records["col"], 
    close.shape[1]
)
win_rate = vbt.rec_nb.reduce_mapped_nb(
    trade_records["pnl"], 
    trade_col_map, 
    np.nan, 
    vbt.pf_nb.win_rate_reduce_nb
)
```

1. Simulation output is from a simulation function such as `from_signals_nb`.
2. Close must be a two-dimensional NumPy array.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

The same method applies to drawdown records, which are based on cumulative returns.

```python title="Calculate maximum drawdown duration in Numba"
returns = sim_out.in_outputs.returns

cumulative_returns = vbt.ret_nb.cumulative_returns_nb(returns)  # (1)!
drawdown_records = vbt.nb.get_drawdowns_nb(None, None, None, cumulative_returns)
dd_duration = vbt.nb.range_duration_nb(  # (2)!
    drawdown_records["start_idx"], 
    drawdown_records["end_idx"], 
    drawdown_records["status"]
)
dd_col_map = vbt.rec_nb.col_map_nb(
    drawdown_records["col"],
    returns.shape[1]
)
max_dd_duration = vbt.rec_nb.reduce_mapped_nb(  # (3)!
    dd_duration,
    dd_col_map,
    np.nan,
    vbt.nb.max_reduce_nb
)
```

1. Expects a two-dimensional NumPy array.
2. Returns one value per record.
3. Returns one value per column.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Return metrics are not based on records and can be calculated directly from returns.

```python title="Calculate various return metrics in Numba"
returns = sim_out.in_outputs.returns

total_return = vbt.ret_nb.total_return_nb(returns)  # (1)!
max_dd = vbt.ret_nb.max_drawdown_nb(returns)  # (2)!
sharpe_ratio = vbt.ret_nb.sharpe_ratio_nb(returns, ann_factor=ann_factor)  # (3)!
```

1. Expects a two-dimensional NumPy array.
2. Returns one value per column.
3. Annualization factor is the average number of bars in a year, such as 365.

## Metadata

You can access the columns and groups of the portfolio through its wrapper and grouper, respectively.

```python title="How to get the columns and groups of a Portfolio instance"
print(pf.wrapper.columns)  # (1)!
print(pf.wrapper.grouper.is_grouped())  # (2)!
print(pf.wrapper.grouper.grouped_index)  # (3)!
print(pf.wrapper.get_columns())  # (4)!

columns_or_groups = pf.wrapper.get_columns()
first_pf = pf[columns_or_groups[0]]  # (5)!
```

1. Get the columns, regardless of any grouping.
2. Check whether the object is grouped.
3. If the above is True, get the groups.
4. Get the columns or groups (if grouped). Recommended.
5. Select the first column or group (if grouped) from the object.

## Stacking

Multiple compatible array-based strategies can be included in the same portfolio by stacking their
respective arrays along the columns.

```python title="Simulate and analyze multiple strategies jointly"
strategy_keys = pd.Index(["strategy1", "strategy2"], name="strategy")
entries = pd.concat((entries1, entries2), axis=1, keys=strategy_keys)
exits = pd.concat((exits1, exits2), axis=1, keys=strategy_keys)
pf = vbt.PF.from_signals(data, entries, exits)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can also stack multiple incompatible strategies—such as those requiring different simulation methods
or argument combinations—by simulating them independently and then stacking them for joint analysis.
This combines their data, order records, initial states, in-place output arrays, and more as if they were
stacked before simulation, with grouping disabled.

```python title="Simulate multiple strategies separately but analyze them jointly"
strategy_keys = pd.Index(["strategy1", "strategy2"], name="strategy")
pf1 = vbt.PF.from_signals(data, entries, exits)
pf2 = vbt.PF.from_orders(data, size, price)
pf = vbt.PF.column_stack((pf1, pf2), wrapper_kwargs=dict(keys=strategy_keys))

# ______________________________________________________________

pf = vbt.PF.column_stack(
    (pf1, pf2), 
    wrapper_kwargs=dict(keys=strategy_keys), 
    group_by=strategy_keys.name  # (1)!
)
```

1. Represent each portfolio as a group in the new portfolio.

## Parallelizing

If you want to simulate multiple columns (without cash sharing) or multiple groups (with or without
cash sharing), you can easily parallelize execution in several ways.

```python title="How to parallelize simulation"
pf = vbt.PF.from_signals(..., chunked="threadpool")  # (1)!

# ______________________________________________________________

pf = vbt.PF.from_signals(..., jitted=dict(parallel=True))  # (2)!
```

1. Use chunking with multithreading.
2. Use automatic parallelization within Numba.

You can also parallelize statistics after your portfolio has been simulated.

```python
@vbt.chunked(engine="threadpool")
def chunked_stats(pf: vbt.ChunkedArray(axis=1)) -> "row_stack":
    return pf.stats(agg_func=None)

chunked_stats(pf)  # (1)!

# ______________________________________________________________

pf.chunk_apply(  # (2)!
    "stats", 
    agg_func=None, 
    execute_kwargs=dict(engine="threadpool", merge_func="row_stack")
)

# ______________________________________________________________

pf.stats(agg_func=None, settings=dict(jitted=dict(parallel=True)))  # (3)!
```

1. Use chunking with multithreading.
2. Same as above.
3. Use automatic parallelization within Numba.