---
title: Portfolio
description: Documentation on simulating and analyzing portfolios in VectorBT PRO
icon: material/chart-areaspline
---

# :material-chart-areaspline: Portfolio

A portfolio refers to any combination of financial assets held by a trader. In VBT, a
"portfolio" is a multidimensional structure designed to simulate and track multiple independent as
well as dependent portfolio instances. The primary function of a portfolio is to apply trading
logic to a set of inputs and simulate a realistic trading environment, known as "simulation". The
outputs of this simulation are orders and other information that users can use to assess the
portfolio's performance, a process also referred to as "reconstruction" or "post-analysis".
Both phases are isolated, which allows for a variety of interesting use cases in quantitative
analysis and data science.

The main class for simulating and analyzing portfolios (that is, actual backtesting) is
[Portfolio](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio). This is a standard Python
class that subclasses [Analyzable](https://vectorbt.pro/pvt_6d1b3986/api/generic/analyzable/#vectorbtpro.generic.analyzable.Analyzable)
and provides access to a variety of Numba-compiled functions. It is structured similarly to other
analyzable classes, featuring diverse class methods for instantiation from different types of inputs
(such as [Portfolio.from_signals](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from_signals),
which accepts signals). This stateful class can wrap and index any Pandas-like objects it contains,
compute metrics, and display (sub-)plots for quick introspection of the stored data.

## Simulation

So, what is a simulation? It is simply a sophisticated loop! :doughnut:

A typical simulation in VBT takes some inputs (such as signals), gradually iterates over their
rows (representing time steps in the real world) using a for-loop, and at each row runs the trading
logic by issuing and executing orders. It then updates the current state of the trading environment,
such as the cash balance and position size. This process mirrors how we would approach algorithmic
trading in reality: at each minute, hour, or day (each row), we decide what to do (the trading
logic) and place an order if we wish to change our market position.

Now, let's discuss execution. The core of VBT's backtesting engine is entirely Numba-compiled
for optimal performance. The engine's functionality is distributed across many functions within the
[portfolio.nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/) sub-package, covering everything from core order execution
commands to the calculation of P&L in trade records. It is important to note that these functions
are not intended for direct use (unless specifically required); instead, they are called by Python
functions higher in the stack. These higher-level functions handle proper pre-processing of input
data and post-processing of output data.

In the following sections, we will discuss order execution and processing, and we will gradually
implement a collection of simple pipelines to better illustrate various simulation concepts.

## Primitive commands

Keep in mind that VBT is an exceptionally raw backtester: its primary commands are "buy"
:green_circle: and "sell" :red_circle:. This means that any strategy that can be expressed as a set
of these commands is supported out of the box. It also means that more complex orders, such as
limit and stop-loss orders, must be implemented manually. In contrast to other backtesting
frameworks, where processing is monolithic and functionality is written in an
[object-oriented manner](https://en.wikipedia.org/wiki/Object-oriented_programming), Numba forces
VBT to implement most functionality in a procedural way.

!!! info
    Even though Numba supports OOP by compiling Python classes with `@jitclass`, they are treated as
    functions, must be statically typed, and have performance drawbacks that prevent us from
    adopting them at this time.

Functions related to order execution are primarily found in [portfolio.nb.core](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/).
The functions implementing our two primary commands are [buy_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.buy_nb)
and [sell_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.sell_nb). In addition to the
requested size and price of an order, the main input for each of these functions is the current
account state of type [AccountState](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.AccountState).
This includes the cash balance, position size, and other details about the current environment.
Whenever we buy or sell, the function creates and returns a new state of the same type. It also
returns an order result of type [OrderResult](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.OrderResult),
which includes the filled size, slippage-adjusted price, transaction fee, order side, status
information indicating whether the order succeeded or failed, and helpful details about any failure.

### Buying

The buy operation consists of two distinct actions: "long-buy," implemented by
[long_buy_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.long_buy_nb), and "short-buy,"
implemented by [short_buy_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.short_buy_nb).
The first opens or increases a long position, while the second reduces a short position. By chaining
these two actions, we can reverse a short position, which is handled automatically by
[buy_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.buy_nb). This function checks the
current position (if any) and calls the appropriate function.

Suppose we have $100 available and want to buy 1 share at a price of $15:

```pycon
>>> from vectorbtpro import *

>>> account_state = vbt.pf_enums.AccountState(
...     cash=100.0,
...     position=0.0,
...     debt=0.0,  # (1)!
...     locked_cash=0.0,  # (2)!
...     free_cash=100.0  # (3)!
... )
>>> order_result, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=account_state,
...     size=1.0,
...     price=15.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=1.0,
    price=15.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=85.0,
    position=1.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=85.0
)
```

1. Debt is non-zero only when leveraging or shorting.
2. Locked cash is non-zero only when leveraging or shorting.
3. Free cash differs from the regular cash balance only when leveraging or shorting.

The returned state shows that we spent $15 and increased our position by 1 share. The order result
contains details about the executed order: we bought 1 share for $15, with no transaction fees.
Since order side and status are fields of the named tuples
[OrderSide](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.OrderSide) and
[OrderStatus](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.OrderStatus), we can look up what
those numbers mean as follows:

```pycon
>>> vbt.pf_enums.OrderSide._fields[order_result.side]
'Buy'

>>> vbt.pf_enums.OrderStatus._fields[order_result.status]
'Filled'
```

!!! info
    If any value is `-1` and cannot be found in the named tuple, the information is unavailable.

Now, with the new state, let's execute a transaction that uses up the remaining cash:

```pycon
>>> order_result, new_account_state2 = vbt.pf_nb.buy_nb(
...     account_state=new_account_state,  # (1)!
...     size=np.inf,  # (2)!
...     price=15.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=5.666666666666667,
    price=15.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state2)
AccountState(
    cash=0.0,
    position=6.666666666666667,
    debt=0.0,
    locked_cash=0.0,
    free_cash=0.0
)
```

1. Use the previous account state as input.
2. Infinity indicates use of the entire balance.

Since VBT was originally designed for cryptocurrency and fractional shares, the default
behavior is to buy as much as possible (here, `5.67`), even if this amount is less than requested.
But what if we want to buy only whole shares? Let's specify a size granularity of 1 to ensure only
integer amounts are allowed:

```pycon
>>> order_result, new_account_state = vbt.pf_nb.buy_nb(
...     account_state,
...     size=np.inf,
...     price=15.0,
...     size_granularity=1
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=6.0,
    price=15.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=10.0,
    position=6.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=10.0
)
```

Now we have bought exactly 6 shares. With the new account state, let's repeat the transaction:

```pycon
>>> order_result, new_account_state2 = vbt.pf_nb.buy_nb(
...     new_account_state,  # (1)!
...     size=np.inf,
...     price=15.0,
...     size_granularity=1
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=np.nan,
    price=np.nan,
    fees=np.nan,
    side=-1,
    status=1,
    status_info=5
)
>>> vbt.pprint(new_account_state2)
AccountState(
    cash=10.0,
    position=6.0,
    debt=0.0,
    free_cash=10.0
)
```

1. Use the account state from the previous operation.

The account state remains unchanged. The presence of NaNs in the order result suggests a failed
order. To look up the meaning of the status and status information values, we can use
[OrderStatus](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.OrderStatus) and
[OrderStatusInfo](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.OrderStatusInfo):

```pycon
>>> vbt.pf_enums.OrderStatus._fields[order_result.status]
'Ignored'

>>> vbt.pf_enums.OrderStatusInfo._fields[order_result.status_info]
'SizeZero'

>>> vbt.pf_enums.status_info_desc[order_result.status_info]  # (1)!
'Size is zero'
```

1. A list is available with more detailed descriptions of different statuses.

Here, the status "Size is zero" means that, after considering the cash balance and applying size
granularity, the (potentially) filled order size is zero, so the order is ignored. Ignored orders
have no effect on the trading environment and are simply, well, *ignored*. Sometimes, when a specific
requirement cannot be met, the status will be "Rejected," indicating the request could not be
fulfilled and an error can be thrown if desired.

For example, let's try to buy more than is possible:

```pycon
>>> order_result, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=account_state, 
...     size=1000.0, 
...     price=15.0,
...     allow_partial=False
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=np.nan,
    price=np.nan,
    fees=np.nan,
    side=-1,
    status=2,
    status_info=12
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=100.0,
    position=0.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=100.0
)

>>> vbt.pf_enums.OrderStatus._fields[order_result.status]
'Rejected'

>>> vbt.pf_enums.status_info_desc[order_result.status_info]
'Final size is less than requested'
```

There are many other parameters to control execution. Let's use 50% of the cash, and apply 1% in
fees and slippage:

```pycon
>>> order_result, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=account_state, 
...     size=np.inf, 
...     price=15.0,
...     fees=0.01,  # (1)!
...     slippage=0.01,  # (2)!
...     percent=0.5  # (3)!
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=3.2676534980230696,
    price=15.15,
    fees=0.4950495049504937,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=50.0,
    position=3.2676534980230696,
    debt=0.0,
    locked_cash=0.0,
    free_cash=50.0
)
```

1. 0.01 = 1%. This is always paid in cash. To specify fixed fees, use `fixed_fees` instead.
2. 0.01 = 1%. This is applied to the price. By artificially increasing the price, you always put
yourself at a disadvantage, but this can be useful to make backtesting more realistic.
3. 0.01 = 1%. This is applied to the resources used to open or increase a position.

The final fees and the price adjusted with slippage are shown in the order result.

Whenever we place an order, we can specify any price. As a result, it is possible that the provided
price is, perhaps by mistake, higher than the highest price of that bar or lower than the lowest
price of that bar. Also, if the user wants to use the closing price and specifies slippage,
this could result in unrealistic prices. To prevent such mistakes, the function performs an OHLC
check. For this, we need to specify the `price_area` argument of type
[PriceArea](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.PriceArea) with the price boundaries,
and indicate what should happen if a boundary is violated using `price_area_vio_mode` of type
[PriceAreaVioMode](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.PriceAreaVioMode):

```pycon
>>> price_area = vbt.pf_enums.PriceArea(
...     open=10,
...     high=14,
...     low=8,
...     close=12
... )
>>> order_result, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=account_state,
...     size=np.inf,
...     price=np.inf,
...     price_area=price_area,
...     price_area_vio_mode=vbt.pf_enums.PriceAreaVioMode.Error
... )
ValueError: Adjusted order price is above the highest price
```

### Selling

The sell operation consists of two distinct actions: "long-sell," implemented by
[long_sell_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.long_sell_nb),
and "short-sell," implemented by [short_sell_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.short_sell_nb).
The first reduces a long position, while the second opens or increases a short position. By chaining
these two actions, we can reverse a long position. This is handled automatically by
[sell_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.sell_nb), which checks the current
position (if any) and calls the appropriate function.

The function for selling accepts the same arguments as buying, but uses them in the opposite
direction. Let's remove 2 shares from a position of 10 shares:

```pycon
>>> account_state = vbt.pf_enums.AccountState(
...     cash=0.0,
...     position=10.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=0.0
... )
>>> order_result, new_account_state = vbt.pf_nb.sell_nb(
...     account_state=account_state,
...     size=2.0,
...     price=15.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=2.0,
    price=15.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=30.0,
    position=8.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=30.0
)
```

The size in the order result remains positive, but the side has changed from 0 to 1:

```pycon
>>> vbt.pf_enums.OrderSide._fields[order_result.side]
'Sell'
```

### Shorting

Shorting is a regular sell operation with [sell_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.sell_nb),
but with one key difference: it now involves the debt and the locked cash balance. When we short,
we borrow shares and sell them to buyers at the market price. This increases the cash balance,
turns the position size negative, and registers the received cash as debt, which is subtracted from
the free cash balance. When we buy back some shares, the debt decreases in proportion to the value of
the shares bought back, while the free cash may increase or decrease depending on whether the repurchase
price was higher or lower than the average short-selling price. Once we cover the short position
entirely, the debt becomes zero and the free cash returns to the same level as the regular cash balance.

!!! note
    You should not treat debt as an absolute amount of cash you owe, since you owe shares, not cash.
    It is used to calculate the average leverage and entry price of the short position, which then
    helps determine changes in the free cash balance with each trade.

To borrow any shares, we need a positive free cash balance to use as collateral. The exact amount
of free cash required for shorting depends on the margin; by default, you need to have funds available
in your margin account equal to the value of the shares to be borrowed. For example, if you short a stock
and the new position is worth $100, you are required to have the $100 obtained from the short sale plus
an additional $100 in cash, for a total of $200. Depending on the definition, this is a 100% (before sale)
or 200% (after sale) initial margin requirement. Maintenance margin and liquidation checks are currently
the responsibility of the user.

```pycon
>>> account_state = vbt.pf_enums.AccountState(
...     cash=100.0,
...     position=0.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=100.0
... )
>>> order_result, new_account_state = vbt.pf_nb.sell_nb(
...     account_state=account_state, 
...     size=np.inf,  # (1)!
...     price=15.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=6.666666666666667,
    price=15.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=200.0,
    position=-6.666666666666667,
    debt=100.0,
    locked_cash=100.0,
    free_cash=0.0
)
```

1. Short-sell as much as possible.

!!! info
    Infinity is a special value in VBT and usually means "go as far as you can".

Here is what happened. First, we moved all available free cash ($100) into the locked cash balance,
so it is now collateral for the shorting operation. Because the default leverage is 1, we have borrowed
shares worth $100, which has been added to the regular cash balance and also recorded as debt. This
corresponds to (minus = borrowed) 6.67 shares. However, since we have doubled the cash balance, it
could be used for other assets. To prevent this, all operations use only the free cash balance. Since
the free cash is now zero, how can we buy back the borrowed shares? Remember, the debt and the locked
cash together represent the total amount of cash we used at the start. By adding these amounts to the
free cash, we get our cash limit for the current buy operation, which matches the regular cash if we
are only dealing with one asset.

To adjust the margin, use the `leverage` argument. For example, setting it to 2 will allow us to
borrow twice as many shares as can be covered by the current free cash:

```pycon
>>> account_state = vbt.pf_enums.AccountState(
...     cash=100.0,
...     position=0.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=100.0
... )
>>> order_result, new_account_state = vbt.pf_nb.sell_nb(
...     account_state=account_state, 
...     size=np.inf,
...     price=15.0,
...     leverage=2
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=13.333333333333334,
    price=15.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=300.0,
    position=-13.333333333333334,
    debt=200.0,
    locked_cash=100.0,
    free_cash=0.0
)
```

The debt-to-locked-cash ratio is now 2, which matches the leverage we specified.

!!! info
    You can specify a different leverage for each short-sell order, even within the same position.

Let's try running the same operation again, but this time using the new account state:

```pycon
>>> order_result, new_account_state2 = vbt.pf_nb.sell_nb(
...     account_state=new_account_state, 
...     size=np.inf,
...     price=15.0,
...     leverage=2
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=np.nan,
    price=np.nan,
    fees=np.nan,
    side=-1,
    status=2,
    status_info=6
)
>>> vbt.pprint(new_account_state2)
AccountState(
    cash=300.0,
    position=-13.333333333333334,
    debt=200.0,
    locked_cash=100.0,
    free_cash=0.0
)

>>> vbt.pf_enums.OrderStatus._fields[order_result.status]
'Rejected'

>>> vbt.pf_enums.status_info_desc[order_result.status_info]
'Not enough cash'
```

We see that VBT prevents the free cash balance from going negative.

To order any quantity possible, we can use unlimited leverage:

```pycon
>>> order_result, new_account_state = vbt.pf_nb.sell_nb(
...     account_state=account_state, 
...     size=1000, 
...     price=15.0, 
...     leverage=np.inf
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=1000.0,
    price=15.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=15100.0,
    position=-1000.0,
    debt=15000.0,
    locked_cash=100.0,
    free_cash=0.0
)
```

What is the effective leverage of this operation?

```pycon
>>> new_account_state.debt / new_account_state.locked_cash
150.0
```

If we calculate the current portfolio value, it still defaults to the initial cash,
since no transaction costs were involved and no additional trades were made:

```pycon
>>> new_account_state.cash + new_account_state.position * order_result.price
100.0
```

As we can see, the positive cash balance and the negative position size keep the total value balanced.
Now, let's illustrate buying back some shares using [buy_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.buy_nb).
First, we will borrow 10 shares with 2x leverage and sell them at $10 per share:

```pycon
>>> order_result, new_account_state = vbt.pf_nb.sell_nb(
...     account_state=account_state, 
...     size=10.0, 
...     price=15.0,
...     leverage=2
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=10.0,
    price=15.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=250.0,
    position=-10.0,
    debt=150.0,
    locked_cash=75.0,
    free_cash=25.0
)
```

Let's buy back 5 shares at $30 per share (my condolences):

```pycon
>>> order_result, new_account_state2 = vbt.pf_nb.buy_nb(
...     account_state=new_account_state, 
...     size=5.0, 
...     price=30.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=5.0,
    price=30.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state2)
AccountState(
    cash=100.0,
    position=-5.0,
    debt=75.0,
    locked_cash=37.5,
    free_cash=-12.5
)
```

We executed the order for $150, which was deducted from the regular cash balance. The position has
been reduced by half, resulting in 5 borrowed shares. Along with the position, the debt and locked
cash have also been reduced by half. Given the absolute amount of released debt ($75), we can
calculate the P&L by subtracting the total spent cash from the total released debt, resulting in
-$75. This operation also released some locked cash - $37.5 - which was added back to our
free cash balance, yielding -$37.5 and making it negative. A negative free cash balance means we
will not be able to buy any other assets apart from reducing short positions, which could release
additional funds. Profits and losses are shared among all assets within the same group with cash
sharing. Even with negative free cash, we can still buy back more shares, since the sum of
`debt`, `locked_cash`, and `free_cash` is greater than zero.

In addition to using debt and locked cash to compute effective leverage, we can also calculate
the average entry price of the entire position:

```pycon
>>> new_account_state2.debt / abs(new_account_state2.position)
15.0
```

Suppose instead the price drops to $10 per share (my congratulations!):

```pycon
>>> order_result, new_account_state2 = vbt.pf_nb.buy_nb(
...     account_state=new_account_state, 
...     size=5.0, 
...     price=10.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=5.0,
    price=10.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state2)
AccountState(
    cash=200.0,
    position=-5.0,
    debt=75.0,
    locked_cash=37.5,
    free_cash=87.5
)
```

We see that the debt and locked cash have decreased to the same levels as before (because
we bought back the same number of shares), but the free cash balance is now $87.5, netting $25
in profit! The calculation is straightforward: take the total amount of spent cash
($5 * 10 = $50) and subtract it from the total released debt (0.5 * $150 = $75) to get the P&L.
When we add the P&L, released locked cash (0.5 * $75 = $37.5), and existing free cash ($25),
we get the new free cash of $87.5, which is immediately available for all other assets.

Let's compute the equity to confirm the profit:

```pycon
>>> st0 = account_state
>>> st1 = new_account_state2
>>> avg_entry_price = st1.debt / abs(st1.position)  # (1)!
>>> new_equity = st1.cash + st1.position * avg_entry_price
>>> new_equity - st0.cash
25.0
```

1. The remaining shares are still valued at $15.

Let's close out the open short position using the same price:

```pycon
>>> order_result, new_account_state3 = vbt.pf_nb.buy_nb(
...     account_state=new_account_state2, 
...     size=5.0, 
...     price=10.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=5.0,
    price=10.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state3)
AccountState(
    cash=150.0,
    position=0.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=150.0
)
```

The free cash balance now equals the regular cash balance, and we are debt-free! Additionally,
the last two operations have brought us $50 in profit, or (15 - 10) * 10 = $50.

Finally, let's try to close the position using an extremely high price!

```pycon
>>> order_result, new_account_state3 = vbt.pf_nb.buy_nb(
...     account_state=new_account_state2, 
...     size=5.0, 
...     price=100.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=2.0,
    price=100.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state3)
AccountState(
    cash=0.0,
    position=-3.0,
    debt=45.0,
    locked_cash=22.5,
    free_cash=-67.5
)
```

We were able to buy back only 2 shares out of the remaining 5. If we try the same operation again,
we will see the "Not enough cash" message because `debt + locked_cash + free_cash` is less than or
equal to zero. We also notice the regular cash balance drops to zero, indicating we have exhausted all
our capital; however, you should not rely on this balance alone when making trading decisions!
If another asset buys shares using leverage, the regular cash balance may become negative.
This does not necessarily mean we are out of cash—only free cash (along with debt and
locked cash when covering shorts) gives us the correct information.

### Leverage

Although VBT allows setting any cash amount (even infinite) and ordering as many shares as
the user wants, this approach comes with some drawbacks: infinite cash leads to an infinite portfolio value,
which makes certain operations on that value impossible, such as converting a target percentage into a target
number of shares. Also, the more cash we have, the smaller the potential contribution of positions to the
portfolio value, thus lowering the magnitude of portfolio returns. What we really want is to multiply those
contributions without inflating the cash balance, which can be effectively done using leverage.

Leverage involves borrowing additional funds to buy shares. In contrast to shorting, leverage is
applied to long positions and borrows cash rather than shares. However, the underlying mechanism is quite
similar. First, we multiply the available free cash by `leverage`. Next, we determine the order
value and the fraction to be borrowed. Finally, we move the borrowed cash to `debt`, declare a
part of the free cash as collateral, and move it to `locked_cash`.
Since locked cash must be spent to buy a portion of the shares, it changes the way we calculate effective
leverage: use `debt / locked_cash + 1` instead of `debt / locked_cash`.

Suppose we have $100 in our margin account and want to buy $200 worth of shares.
As we learned earlier, we can specify infinite leverage and VBT will calculate the effective
leverage for us:

```pycon
>>> account_state = vbt.pf_enums.AccountState(
...     cash=100.0,
...     position=0.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=100.0
... )
>>> order_result, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=account_state, 
...     size=20, 
...     price=10.0,
...     leverage=np.inf
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=20,
    price=10.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=-100.0,
    position=20.0,
    debt=100.0,
    locked_cash=100.0,
    free_cash=0.0
)
```

As shown, $100 is deducted from our free cash balance, and an additional $100 is borrowed,
which brings the effective leverage to 2:

```pycon
>>> new_account_state.debt / new_account_state.locked_cash + 1
2.0
```

Buying 10 shares instead would use no leverage, since the transaction can be fully
covered by the free cash, even if leverage is set to infinity:

```pycon
>>> order_result, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=account_state, 
...     size=10, 
...     price=10.0,
...     leverage=np.inf
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=10,
    price=10.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=0.0,
    position=10.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=0.0
)
```

Is it possible to use only a portion of our own free cash while borrowing the rest?
Yes! The command [buy_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.buy_nb) accepts
the argument `leverage_mode` of type [LeverageMode](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.LeverageMode),
which supports two modes: "lazy" and "eager" leveraging. The first mode is the default and
enables leverage only if the quantity to be bought cannot be fulfilled with your own resources.
The second mode enables leverage for any quantity and requires the leverage to be set explicitly.
Using infinite leverage in this mode will raise an error.

!!! note
    Shorting supports "lazy" leveraging only.

Let's buy 10 shares with 3x leverage:

```pycon
>>> order_result, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=account_state, 
...     size=10, 
...     price=10.0,
...     leverage=3,
...     leverage_mode=vbt.pf_enums.LeverageMode.Eager
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=10,
    price=10.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=0.0,
    position=10.0,
    debt=66.66666666666667,
    locked_cash=33.333333333333336,
    free_cash=66.66666666666666
)
```

We have used only $33.33 from our free cash balance as collateral to borrow an additional $66.67,
making a total of $100 spent to buy the desired quantity.

How do we repay the debt? When selling, the debt and locked cash balances decrease proportionally
to the number of shares sold. This is the same procedure used when (partially) closing
a short position. The main difference is in the calculation of P&L: we take the total of the released
debt and locked cash and subtract them from the cash received from the sale.

First, we will use 2x leverage to buy 10 shares at $20 per share:

```pycon
>>> order_result, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=account_state, 
...     size=10, 
...     price=20.0,
...     leverage=2
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=10,
    price=20.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=-100.0,
    position=10.0,
    debt=100.0,
    locked_cash=100.0,
    free_cash=0.0
)
```

Now let's sell 5 shares at $5 per share (my condolences):

```pycon
>>> order_result, new_account_state2 = vbt.pf_nb.sell_nb(
...     account_state=new_account_state, 
...     size=5.0, 
...     price=5.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=5.0,
    price=5.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state2)
AccountState(
    cash=-75.0,
    position=5.0,
    debt=50.0,
    locked_cash=50.0,
    free_cash=-25.0
)
```

We have retrieved $25 from this operation, which was added to the regular cash balance.
The debt and locked cash have both been cut in half because half of the leveraged position
has been closed. The P&L for this operation is the cash received ($25) minus the released debt ($50)
and locked cash ($50), for a total loss of $75. By adding this number to the released locked cash,
we get a new free cash of -$25, a change that is applied to all other assets using the same
cash balance, preventing them from opening or increasing positions.

Another way to calculate the P&L is using equity:

```pycon
>>> st0 = account_state
>>> st1 = new_account_state2
>>> avg_entry_price = (st1.debt + st1.locked_cash) / abs(st1.position)  # (1)!
>>> new_equity = st1.cash + st1.position * avg_entry_price
>>> new_equity - st0.cash
-75.0
```

1. The remaining shares are valued at $20.

Now, let's say that instead of the price dipping, it jumps to $40 per share (my congratulations!):

```pycon
>>> order_result, new_account_state2 = vbt.pf_nb.sell_nb(
...     account_state=new_account_state, 
...     size=5.0, 
...     price=40.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=5.0,
    price=40.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state2)
AccountState(
    cash=100.0,
    position=5.0,
    debt=50.0,
    locked_cash=50.0,
    free_cash=150.0
)
```

We have received $200 from this operation, which has been added to the regular cash balance.
The debt and locked cash have both been cut in half because half of the leveraged position
has been closed. The P&L for this operation is the cash received ($200) minus the released debt ($50)
and locked cash ($50), making it a profit of $100. By adding this amount to the released locked cash,
we get a new free cash balance of $150, which can now be used by all other assets sharing the same balance.

Let's close out the remaining position at the same price:

```pycon
>>> order_result, new_account_state2 = vbt.pf_nb.sell_nb(
...     account_state=new_account_state, 
...     size=5.0, 
...     price=40.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=5.0,
    price=40.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state2)
AccountState(
    cash=300.0,
    position=0.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=300.0
)
```

We made a profit of $200, which is the same as if we had used only our own cash:

```pycon
>>> account_state = vbt.pf_enums.AccountState(
...     cash=200.0,
...     position=0.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=200.0
... )
>>> _, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=account_state, 
...     size=10, 
...     price=20.0
... )
>>> _, new_account_state2 = vbt.pf_nb.sell_nb(
...     account_state=new_account_state, 
...     size=10.0, 
...     price=40.0
... )
>>> new_account_state2.free_cash - account_state.free_cash
200.0
```

### Symmetry

Long and short positions behave symmetrically. For example, let's open two opposite positions using an
infinite size and 10x leverage, and close them with a $5 per share price difference
in favor of the current position:

```pycon
>>> account_state = vbt.pf_enums.AccountState(
...     cash=100.0,
...     position=0.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=100.0
... )

>>> _, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=account_state, 
...     direction=vbt.pf_enums.Direction.LongOnly,
...     size=np.inf, 
...     price=10.0,
...     leverage=10
... )
>>> _, new_account_state = vbt.pf_nb.sell_nb(
...     account_state=new_account_state, 
...     direction=vbt.pf_enums.Direction.LongOnly,
...     size=np.inf, 
...     price=15.0
... )
>>> vbt.pprint(new_account_state)
AccountState(
    cash=600.0,
    position=0.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=600.0
)

>>> _, new_account_state = vbt.pf_nb.sell_nb(
...     account_state=account_state, 
...     direction=vbt.pf_enums.Direction.ShortOnly,
...     size=np.inf, 
...     price=10.0,
...     leverage=10
... )
>>> _, new_account_state = vbt.pf_nb.buy_nb(
...     account_state=new_account_state, 
...     direction=vbt.pf_enums.Direction.ShortOnly,
...     size=np.inf, 
...     price=5.0
... )
>>> vbt.pprint(new_account_state)
AccountState(
    cash=600.0,
    position=0.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=600.0
)
```

### Reversing

Positions in VBT can be reversed with a single order. To reverse a position, the `direction`
argument should remain at its default value—`Direction.Both`. Let's start with a position of 10 shares,
reverse it to the maximum extent in the short direction, and then reverse it again
to the maximum extent in the opposite (long) direction:

```pycon
>>> account_state = vbt.pf_enums.AccountState(
...     cash=0.0,
...     position=10.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=0.0
... )
>>> order_result, new_account_state = vbt.pf_nb.sell_nb(
...     account_state=account_state, 
...     size=np.inf, 
...     price=15.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=20.0,
    price=15.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=300.0,
    position=-10.0,
    debt=150.0,
    locked_cash=150.0,
    free_cash=0.0
)

>>> order_result, new_account_state2 = vbt.pf_nb.buy_nb(
...     account_state=new_account_state, 
...     size=np.inf, 
...     price=15.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=20.0,
    price=15.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state2)
AccountState(
    cash=0.0,
    position=10.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=0.0
)
```

Both operations are symmetric and cancel each other out with repeated execution,
so we have ultimately returned to our initial account state.

### Closing

To close out a position and avoid a reversal, we can either specify the exact size
or an infinite size along with the current direction via the `direction` argument of type
[Direction](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.Direction).
For example, if we are in a long position and specify the long-only direction, the position
will not be reversed:

```pycon
>>> account_state = vbt.pf_enums.AccountState(
...     cash=0.0,
...     position=10.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=0.0
... )
>>> order_result, new_account_state = vbt.pf_nb.sell_nb(
...     account_state=account_state, 
...     size=np.inf, 
...     price=15.0, 
...     direction=vbt.pf_enums.Direction.LongOnly
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=10.0,
    price=15.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=150.0,
    position=0.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=150.0
)
```

!!! note
    Using the [buy_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.buy_nb)
    and [sell_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.sell_nb) commands guarantees
    execution of the order in the long and short direction, respectively.

We can also use commands that are guaranteed to execute within the current position
and not open an opposite one: [long_sell_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.long_sell_nb)
for long positions and [short_buy_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.short_buy_nb)
for short positions. These do not require the `direction` argument, just a size of infinity:

```pycon
>>> account_state = vbt.pf_enums.AccountState(
...     cash=0.0,
...     position=10.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=0.0
... )
>>> order_result, new_account_state = vbt.pf_nb.long_sell_nb(
...     account_state=account_state, 
...     size=np.inf, 
...     price=15.0
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=10.0,
    price=15.0,
    fees=0.0,
    side=1,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_account_state)
AccountState(
    cash=150.0,
    position=0.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=150.0
)
```

### Pipeline/1

Even with just these two essential commands, you can already build a backtesting pipeline of any
complexity or flexibility. As mentioned earlier, a simulation is simply a loop that iterates
over timestamps. Let's create a simplified pipeline that puts $1 into Bitcoin each time it detects
a [Golden Cross](https://www.investopedia.com/terms/g/goldencross.asp) entry signal, and sells $1
otherwise. Our goal is a single number: the final value of the portfolio.

```pycon
>>> @njit
... def pipeline_1_nb(close, entries, exits, init_cash=100):
...     account_state = vbt.pf_enums.AccountState(  # (1)!
...         cash=float(init_cash),
...         position=0.0,
...         debt=0.0,
...         locked_cash=0.0,
...         free_cash=float(init_cash)
...     )
...     for i in range(close.shape[0]):
...         if entries[i]:
...             _, account_state = vbt.pf_nb.buy_nb(  # (2)!
...                 account_state=account_state,
...                 size=1 / close[i],
...                 price=close[i]
...             )
...         if exits[i]:
...             _, account_state = vbt.pf_nb.sell_nb(
...                 account_state=account_state,
...                 size=1 / close[i],
...                 price=close[i]
...             )
...     return account_state.cash + account_state.position * close[-1]  # (3)!

>>> data = vbt.YFData.pull("BTC-USD", end="2022-01-01")
>>> sma_50 = vbt.talib("SMA").run(data.get("Close"), 50)
>>> sma_200 = vbt.talib("SMA").run(data.get("Close"), 200)
>>> entries = sma_50.real_crossed_above(sma_200)
>>> exits = sma_50.real_crossed_below(sma_200)

>>> pipeline_1_nb(
...     data.get("Close").values, 
...     entries.values, 
...     exits.values
... )
210.71073253390762
```

1. Initial account state.
2. Execute the order and return a new account state.
3. Calculate the final portfolio value.

!!! hint
    Adding the suffix `_nb` to indicate a Numba-compiled function is not required,
    but it remains a good convention in VBT.

We can validate this pipeline using one of the preset simulation methods:

```pycon
>>> vbt.Portfolio.from_orders(
...     data.get("Close"), 
...     size=entries.astype(int) - exits.astype(int), 
...     size_type="value"
... ).final_value
210.71073253390762
```

## Order execution

Using the primitive commands is convenient when we know the exact direction of the order and can be sure
that the provided arguments are appropriate. However, we often encounter more complex requirements, such 
as target percentages that may change the order direction based on the current value. In addition, these 
commands do not validate their arguments; for example, if a user accidentally passes a negative order 
price, no error will be thrown. Also, we need a better way to represent an order—it is not considered 
good practice to pass all parameters, such as slippage, as keyword arguments.

All checks and preprocessing steps are handled in the
[execute_order_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.execute_order_nb) function.
The first input to this function is an order execution state of type
[ExecState](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.ExecState).
This state contains the same information as the account state shown above but also includes additional
details about the current valuation. The second input is a named tuple of type
[Order](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.Order) that represents an order.
The third argument is the price area, which we have already discussed.

### Order

In VBT, an order is represented by a [named tuple](https://realpython.com/python-namedtuple/).
Named tuples offer an efficient and lightweight alternative to data classes in both the Python and
Numba environments. They can be easily created and processed. Let's create an instance of an order:

```pycon
>>> order = vbt.pf_enums.Order()
>>> vbt.pprint(order)
Order(
    size=np.inf,
    price=np.inf,
    size_type=0,
    direction=2,
    fees=0.0,
    fixed_fees=0.0,
    slippage=0.0,
    min_size=np.nan,
    max_size=np.nan,
    size_granularity=np.nan,
    leverage=1.0,
    leverage_mode=0,
    reject_prob=0.0,
    price_area_vio_mode=0,
    allow_partial=True,
    raise_reject=False,
    log=False
)
```

You can access the tuple's attributes using dot notation:

```pycon
>>> order.direction
2
```

Other than that, it behaves just like any other tuple in Python:

```pycon
>>> order[3]
2

>>> tuple(order)  # (1)!
(inf,
 inf,
 0,
 2,
 0.0,
 0.0,
 0.0,
 nan,
 nan,
 nan,
 1.0,
 0,
 0.0,
 0,
 True,
 False,
 False)
```

1. Convert to a regular tuple.

When working with Numba, there is still the issue of default arguments: even though you can
construct a new tuple in Numba using only default arguments as shown above, if you want to override
some values, the values to override must be strictly on the left side of the tuple's definition.
Otherwise, Numba requires you to explicitly provide all the default arguments that come before them:

```pycon
>>> @njit
... def create_order_nb():
...     return vbt.pf_enums.Order()  # (1)!

>>> create_order_nb()
Order(size=inf, price=inf, ...)

>>> @njit
... def create_order_nb(size, price):
...     return vbt.pf_enums.Order(size=size, price=price)  # (2)!

>>> create_order_nb(1, 15)
Order(size=1, price=15, ...)

>>> @njit
... def create_order_nb(size, price, direction):
...     return vbt.pf_enums.Order(size=size, price=price, direction=direction)  # (3)!

>>> create_order_nb(1, 15, 2)
Failed in nopython mode pipeline (step: nopython frontend)
```

1. Uses only the default values.
2. Overrides the default values of arguments on the left side.
3. Attempts to override default values at different positions.

Another issue involves data types. In the example above, where integer size and price are provided,
Numba handles them without problems. However, if you create such an order in a loop and provide a float
for one of the arguments instead of an integer as before, Numba will throw an error because it cannot
unify the data types. Therefore, you should cast all arguments to their target data types before
constructing an order.

Both issues can be resolved by using the
[order_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.order_nb) function:

```pycon
>>> @njit
... def create_order_nb(size, price, direction):
...     return vbt.pf_nb.order_nb(size=size, price=price, direction=direction)

>>> create_order_nb(1, 15, 2)
Order(size=1.0, price=15.0, ..., direction=2, ...)
```

Notice that the size and price arguments are automatically cast to floats.

!!! hint
    Whenever possible, use [order_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.order_nb)
    instead of [Order](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.Order).

To create an order that closes the current position, you can use
[close_position_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.close_position_nb):

```pycon
>>> vbt.pf_nb.close_position_nb(15)  # (1)!
Order(size=0.0, price=15.0, size_type=6, ...)
```

1. Uses a size of zero and a size type of `TargetAmount`.

### Validation

After constructing the order, [execute_order_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.execute_order_nb)
will check whether the order's arguments have valid data types and values. For example, let's
try passing a negative price:

```pycon
>>> exec_state = vbt.pf_enums.ExecState(
...     cash=100.0,
...     position=0.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=100.0,
...     val_price=15.0,
...     value=100.0
... )
>>> vbt.pf_nb.execute_order_nb(
...     exec_state,
...     vbt.pf_nb.order_nb(price=-15)
... )
ValueError: order.price must be finite and 0 or greater
```

### Price resolution

Once the inputs are validated, [execute_order_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.execute_order_nb)
uses them to determine whether to run the buy or sell command. Before that, it performs some preprocessing.

Vectorbt is not tied to any particular data schema and can work with tick data or bar data.
However, it allows you to provide the current candle (`price_area`) for validation and resolution.
If provided, VBT will consider the order price as a price point within four bounds:
the opening, high, low, and closing prices. Since order execution must occur strictly within these bounds,
setting the order price to `-np.inf` or `np.inf` will replace it with the opening or closing price,
respectively. So, when you see a default price set to `np.inf`, remember that it means the
close price :writing_hand:

```pycon
>>> price_area = vbt.pf_enums.PriceArea(
...     open=10,
...     high=14,
...     low=8,
...     close=12
... )
>>> order_result, new_exec_state = vbt.pf_nb.execute_order_nb(  # (1)!
...     exec_state=exec_state,
...     order=vbt.pf_nb.order_nb(size=np.inf, price=-np.inf),
...     price_area=price_area
... )
>>> order_result.price
10.0

>>> order_result, new_exec_state = vbt.pf_nb.execute_order_nb(  # (2)!
...     exec_state=exec_state,
...     order=vbt.pf_nb.order_nb(size=np.inf, price=np.inf),
...     price_area=price_area
... )
>>> order_result.price
12.0

>>> order_result, new_exec_state = vbt.pf_nb.execute_order_nb(  # (3)!
...     exec_state=exec_state,
...     order=vbt.pf_nb.order_nb(size=np.inf, price=np.inf)
... )
>>> order_result.price
nan
```

1. Price is replaced by the open price. Order executed.
2. Price is replaced by the close price (default). Order executed.
3. Price becomes `np.nan` since the price area is not defined. Order ignored.

### Size type conversion

Primitive commands only accept size as a number of shares, so any size type defined in
[SizeType](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.SizeType) must be converted to `Amount`.
Different size types require different information for conversion; for example,
`TargetAmount` needs to know the current position size, while `Value` also requires the current valuation
price.

Let's execute an order so that the new position has 3 shares:

```pycon
>>> order_result, new_exec_state = vbt.pf_nb.execute_order_nb(
...     exec_state=exec_state,
...     order=vbt.pf_nb.order_nb(
...         size=3, 
...         size_type=vbt.pf_enums.SizeType.TargetAmount
...     ),
...     price_area=price_area
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=3.0,
    price=12.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_exec_state)
ExecState(
    cash=64.0,
    position=3.0,
    debt=0.0,
    locked_cash=0.0,
    free_cash=64.0,
    val_price=15.0,
    value=100.0
)
```

Since we are not in the market, VBT used [buy_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.buy_nb)
to buy 3 shares. If we were already in the market with 10 shares, it would have used
[sell_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.sell_nb) to sell 7 shares.

### Direction

The [order_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.order_nb) function takes the
`direction` argument for two reasons: to resolve the direction of the order based on the sign of the
`size` argument, and to decide whether to reverse the position or simply close it out. When the direction
is `LongOnly` or `Both`, a positive size means buying, while a negative size means selling.
When the direction is `ShortOnly`, the opposite applies: a positive size means selling and a negative
size means buying. This is because a positive size means increasing a position, which corresponds to
buying to increase a long position and selling to increase a short position. For example, if the direction
is `ShortOnly` and the size is negative infinity, any short position will be closed out and any long
position will be enlarged.

### Valuation

For the valuation price, it is the latest available price at the time of decision-making,
or the price used to calculate the portfolio value. In many simulation methods, the valuation
price defaults to the order price, but sometimes it makes more sense to use the open or previous
close price for the conversion step. By separating the valuation and order price, we can introduce
a time gap between order placement and execution. This matters because, in reality, orders cannot
always be executed right away.

Let's place an order for 100% of the portfolio value:

```pycon
>>> order_result, new_exec_state = vbt.pf_nb.execute_order_nb(
...     exec_state=exec_state,
...     order=vbt.pf_nb.order_nb(
...         size=1.0, 
...         size_type=vbt.pf_enums.SizeType.TargetPercent
...     ),
...     price_area=price_area
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=6.666666666666667,
    price=12.0,
    fees=0.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_exec_state)
ExecState(
    cash=20.0,
    position=6.666666666666667,
    debt=0.0,
    locked_cash=0.0,
    free_cash=20.0,
    val_price=15.0,
    value=100.0
)
```

Why didn't we spend the entire cash? To convert the target percentage to the target amount of shares,
VBT used the provided order execution state, where `val_price` is $15 and `value` is $100,
which resulted in `100 / 15 = 6.67`. The closer the valuation price is to the order price,
the closer the calculation result will match the target requirement.

By default, if you place multiple orders within the same bar (for example, in pairs trading),
VBT will not update the portfolio value after each order. This is because it assumes trading
decisions are made before execution, and updating the value would affect those decisions.
Additionally, an order typically causes only a marginal immediate change in the value,
such as through commissions. To force VBT to update the valuation price and value,
you can enable `update_value`:

```pycon
>>> order_result, new_exec_state = vbt.pf_nb.execute_order_nb(
...     exec_state=exec_state,
...     order=vbt.pf_nb.order_nb(
...         size=1.0, 
...         size_type=vbt.pf_enums.SizeType.TargetPercent,
...         fixed_fees=10,
...         slippage=0.01
...     ),
...     price_area=price_area,
...     update_value=True
... )
>>> vbt.pprint(order_result)
OrderResult(
    size=6.666666666666667,
    price=12.120000000000001,
    fees=10.0,
    side=0,
    status=0,
    status_info=-1
)
>>> vbt.pprint(new_exec_state)
ExecState(
    cash=9.199999999999989,
    position=6.666666666666667,
    debt=0.0,
    locked_cash=0.0,
    free_cash=9.199999999999989,
    val_price=12.120000000000001,
    value=90.0
)
```

Notice how the new valuation price is set to the close price adjusted for slippage,
and the value is decreased by the fixed commission. Any additional orders placed after this one
will use the updated value and will likely result in a different outcome.

!!! note
    Use this feature only if you can control the order in which orders appear within a bar
    and when you have intra-bar data.

### Pipeline/2

Let's create another simplified pipeline that places orders based on a target percentage array.
In this case, we will keep 50% of the portfolio value in shares and rebalance monthly.
We will calculate the portfolio value based on the open price at the start of each bar and place orders
at the end of each bar (to make it realistic). Also, we will fill asset value and portfolio value arrays
to later plot the allocation at each bar.

```pycon
>>> @njit
... def pipeline_2_nb(open, close, target_pct, init_cash=100):
...     asset_value_out = np.empty(close.shape, dtype=float_)  # (1)!
...     value_out = np.empty(close.shape, dtype=float_)
...     exec_state = vbt.pf_enums.ExecState(  # (2)!
...         cash=float(init_cash),
...         position=0.0,
...         debt=0.0,
...         locked_cash=0.0,
...         free_cash=float(init_cash),
...         val_price=np.nan,
...         value=np.nan
...     )
...
...     for i in range(close.shape[0]):
...         if not np.isnan(target_pct[i]):  # (3)!
...             val_price = open[i]
...             value = exec_state.cash + val_price * exec_state.position  # (4)!
...
...             exec_state = vbt.pf_enums.ExecState(  # (5)!
...                 cash=exec_state.cash,
...                 position=exec_state.position,
...                 debt=exec_state.debt,
...                 locked_cash=exec_state.locked_cash,
...                 free_cash=exec_state.free_cash,
...                 val_price=val_price,
...                 value=value
...             )
...             order = vbt.pf_nb.order_nb(  # (6)!
...                 size=target_pct[i],
...                 price=close[i],
...                 size_type=vbt.pf_enums.SizeType.TargetPercent
...             )
...             _, exec_state = vbt.pf_nb.execute_order_nb(  # (7)!
...                 exec_state=exec_state,
...                 order=order
...             )
...
...         asset_value_out[i] = exec_state.position * close[i]  # (8)!
...         value_out[i] = exec_state.cash + exec_state.position * close[i]
...         
...     return asset_value_out, value_out
```

1. Create two empty arrays of floating-point type. Remember that using `np.empty` will produce arrays
with uninitialized (garbage) values, so you should overwrite them.
2. The initial execution state for orders.
3. No order is executed if the target percentage is `np.nan` (which means do not rebalance).
4. Calculate the portfolio value at the start of the bar (valuation).
5. Create a new execution state after recalculating the valuation.
6. Create a new order tuple using the close price.
7. Execute the order and update the execution state.
8. Fill in the arrays (each element should be set individually).

Now let's run the pipeline on our Bitcoin data:

```pycon
>>> symbol_wrapper = data.get_symbol_wrapper()  # (1)!
>>> target_pct = symbol_wrapper.fill()
>>> target_pct.vbt.set(0.5, every="M", inplace=True)  # (2)!

>>> asset_value, value = pipeline_2_nb(
...     data.get("Open").values, 
...     data.get("Close").values, 
...     target_pct.values
... )
>>> asset_value = symbol_wrapper.wrap(asset_value)  # (3)!
>>> value = symbol_wrapper.wrap(value)
>>> allocations = (asset_value / value).rename(None)  # (4)!
>>> allocations.vbt.scatterplot(trace_kwargs=dict(
...     marker=dict(
...         color=allocations, 
...         colorscale="Temps", 
...         size=3,
...         cmin=0.3,
...         cmid=0.5,
...         cmax=0.7
...     )
... )).show()
```

1. We cannot use `data.wrapper` because it contains OHLC as columns. Instead, we need a wrapper that has
symbols as columns, allowing us to fill the array with target percentages.
2. Fill the array with NaNs and set all data points at the beginning of each month to `0.5`.
3. Use the same wrapper to convert the NumPy array back to a Pandas Series.
4. Divide the asset value by the portfolio value to obtain the allocation.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/documentation/pf/pipeline_2_allocation1.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/documentation/pf/pipeline_2_allocation1.dark.svg#only-dark){: .iimg loading=lazy }

!!! hint
    Each point represents a revaluation at the end of each bar.

As you can see, allocations are regularly pulled back to the target level of 50%.

Let's validate the pipeline using [Portfolio.from_orders](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from_orders):

```pycon
>>> pf = vbt.Portfolio.from_orders(
...     data, 
...     size=target_pct, 
...     size_type="targetpercent"
... )
>>> pf.allocations.vbt.scatterplot(trace_kwargs=dict(
...     marker=dict(
...         color=allocations, 
...         colorscale="Temps", 
...         size=3,
...         cmin=0.3,
...         cmid=0.5,
...         cmax=0.7
...     )
... )).show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/documentation/pf/pipeline_2_allocation2.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/documentation/pf/pipeline_2_allocation2.dark.svg#only-dark){: .iimg loading=lazy }

One of the greatest advantages of using VBT is that you can run your minimalistic trading
environment in any Python function, even inside the objective functions of machine learning models.
There is no need to trigger the entire backtesting pipeline as a script or use other complex
processes as most backtesting frameworks require :face_with_spiral_eyes:

## Order processing

Order execution takes an order instruction and translates it into a buy or sell operation.
It is the user's responsibility to handle the returned order execution state and result.

Typically, you will post-process and append each successful order to a list for later analysis—
this is where order and log records come into play. Additionally, you may want to raise an error if
an order has been rejected and a certain flag in the requirements is set. All of this is managed by
[process_order_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.process_order_nb).

### Order records

Order records are a [structured](https://numpy.org/doc/stable/user/basics.rec.html) NumPy array with
the data type [order_dt](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.order_dt), which contains
information about each successful order. Each order in this array is considered completed; in VBT's
context, you should treat an order as a trade. Since Numba is used here, lists and other inefficient
data structures for storing such complex information cannot and should not be used. Because orders
contain fields with variable data types, a record array is the best data structure to use. A record
array is a standard NumPy array with a complex data type and behaves similarly to a Pandas DataFrame.

Because any NumPy array is not appendable, you must initialize an empty array of sufficient size and
fill it with new information as needed. For this, you need a counter—a simple integer that points to
the index of the next record to be written.

!!! info
    While you can append to a NumPy array, doing so creates a new array. Do not try this at home :smile:

Let's create an array with two order records and set up a counter:

```pycon
>>> order_records = np.empty(2, dtype=vbt.pf_enums.order_dt)
>>> order_count = 0
```

You should not access this array yet because it contains uninitialized memory, so you must manually set
all the values in the array and use it with caution.

```pycon
>>> order_records
array([(4585679916398730403, ..., 4583100142070297783),
       (4582795628349012822, ..., 4576866499094039639)],
      dtype={'names':['id','col','idx','size','price','fees','side'], ...})
```

Let's execute an order using [execute_order_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.execute_order_nb)
at the 678th bar and fill the first record in the array:

```pycon
>>> exec_state = vbt.pf_enums.ExecState(
...     cash=100.0,
...     position=0.0,
...     debt=0.0,
...     locked_cash=0.0,
...     free_cash=100.0,
...     val_price=15.0,
...     value=100.0
... )
>>> order_result, new_exec_state = vbt.pf_nb.execute_order_nb(
...     exec_state=exec_state,
...     order=vbt.pf_nb.order_nb(size=np.inf, price=15.0)
... )
>>> if order_result.status == vbt.pf_enums.OrderStatus.Filled:  # (1)!
...     order_records["id"][order_count] = order_count  # (2)!
...     order_records["col"][order_count] = 0
...     order_records["idx"][order_count] = 678  # (3)!
...     order_records["size"][order_count] = order_result.size
...     order_records["price"][order_count] = order_result.price
...     order_records["fees"][order_count] = order_result.fees
...     order_records["side"][order_count] = order_result.side
...     order_count += 1

>>> order_records[0]
(0, 0, 678, 6.66666667, 15., 0., 0)

>>> order_count
1
```

1. Check that the order has been filled.
2. Order IDs start at 0 and follow the counter.
3. The index of the current bar.

!!! note
    When writing to a record field element, first select the field and then the index.

At the next bar, we will reverse the position and fill the second record:

```pycon
>>> order_result, new_exec_state2 = vbt.pf_nb.execute_order_nb(
...     exec_state=new_exec_state,
...     order=vbt.pf_nb.order_nb(size=-np.inf, price=16.0)
... )
>>> if order_result.status == vbt.pf_enums.OrderStatus.Filled:
...     order_records["id"][order_count] = order_count  # (1)!
...     order_records["col"][order_count] = 0
...     order_records["idx"][order_count] = 679
...     order_records["size"][order_count] = order_result.size
...     order_records["price"][order_count] = order_result.price
...     order_records["fees"][order_count] = order_result.fees
...     order_records["side"][order_count] = order_result.side
...     order_count += 1

>>> order_records[1]
(1, 0, 679, 13.33333333, 16., 0., 1)

>>> order_count
2
```

1. Remember to increment the order ID.

Here are the order records that we have filled:

```pycon
>>> order_records
array([(0, 0, 678,  6.66666667, 15., 0., 0),
       (1, 0, 679, 13.33333333, 16., 0., 1)],
      dtype={'names':['id','col','idx','size','price','fees','side'], ...})
```

However, instead of setting each of these records manually, you can use
[process_order_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.process_order_nb) to do
this automatically! There is one small adjustment: both the order records and the counter must be set
per column, since VBT mainly works with multi-column data. This means the order records array must
be two-dimensional and the counter array must be one-dimensional (both with only one column in this example):

```pycon
>>> order_records = np.empty((2, 1), dtype=vbt.pf_enums.order_dt)
>>> order_counts = np.full(1, 0, dtype=int_)

>>> order_result1, new_exec_state1 = vbt.pf_nb.process_order_nb(
...     0, 0, 678,  # (1)!
...     exec_state=exec_state,
...     order=vbt.pf_nb.order_nb(size=np.inf, price=15.0),
...     order_records=order_records,
...     order_counts=order_counts
... )
>>> order_result2, new_exec_state2 = vbt.pf_nb.process_order_nb(
...     0, 0, 679,
...     exec_state=new_exec_state,
...     order=vbt.pf_nb.order_nb(size=-np.inf, price=16.0),
...     order_records=order_records,
...     order_counts=order_counts
... )

>>> order_records
array([(0, 0, 678,  6.66666667, 15., 0., 0),
       (1, 0, 679, 13.33333333, 16., 0., 1)],
      dtype={'names':['id','col','idx','size','price','fees','side'], ...})
      
>>> order_counts
array([2])
```

1. Current group, column, and index (row).

These filled order records form the backbone of the post-analysis phase.

### Log records

Log records use the data type [log_dt](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.log_dt) and
are similar to order records but have a few key differences: they are saved regardless of whether the
order has been filled, and they include information about the current execution state, the order request,
and the new execution state. This approach allows you to fully track and diagnose issues related to
order processing.

```pycon
>>> order_records = np.empty((2, 1), dtype=vbt.pf_enums.order_dt)
>>> order_counts = np.full(1, 0, dtype=int_)
>>> log_records = np.empty((2, 1), dtype=vbt.pf_enums.log_dt)
>>> log_counts = np.full(1, 0, dtype=int_)

>>> order_result1, new_exec_state1 = vbt.pf_nb.process_order_nb(
...     0, 0, 678,
...     exec_state=exec_state,
...     order=vbt.pf_nb.order_nb(size=np.inf, price=15.0, log=True),  # (1)!
...     order_records=order_records,
...     order_counts=order_counts,
...     log_records=log_records,
...     log_counts=log_counts
... )
>>> order_result2, new_exec_state2 = vbt.pf_nb.process_order_nb(
...     0, 0, 679,
...     exec_state=new_exec_state,
...     order=vbt.pf_nb.order_nb(size=-np.inf, price=16.0, log=True),
...     order_records=order_records,
...     order_counts=order_counts,
...     log_records=log_records,
...     log_counts=log_counts
... )

>>> log_records
array([[(0, 0, 0, 678, ..., 0., 15., 100., 0)],
       [(1, 0, 0, 679, ..., 0., 15., 100., 1)]],
      dtype={'names':['id','group',...,'res_status_info','order_id'], ...})
```

1. Logging for each order must be explicitly enabled.

!!! note
    Logging affects both performance and memory usage. Use it only when truly needed.

### Pipeline/3

Let's extend the [last pipeline](#pipeline2) to independently process any number of columns and
gradually fill order records. This approach allows us to backtest multiple parameter combinations
by taking advantage of array multidimensionality!

```pycon
>>> @njit
... def pipeline_3_nb(open, close, target_pct, init_cash=100):
...     order_records = np.empty(close.shape, dtype=vbt.pf_enums.order_dt)  # (1)!
...     order_counts = np.full(close.shape[1], 0, dtype=int_)
...
...     for col in range(close.shape[1]):  # (2)!
...         exec_state = vbt.pf_enums.ExecState(
...             cash=float(init_cash),
...             position=0.0,
...             debt=0.0,
...             locked_cash=0.0,
...             free_cash=float(init_cash),
...             val_price=np.nan,
...             value=np.nan
...         )
...
...         for i in range(close.shape[0]):
...             if not np.isnan(target_pct[i, col]):  # (3)!
...                 val_price = open[i, col]
...                 value = exec_state.cash + val_price * exec_state.position
...
...                 exec_state = vbt.pf_enums.ExecState(
...                     cash=exec_state.cash,
...                     position=exec_state.position,
...                     debt=exec_state.debt,
...                     locked_cash=exec_state.locked_cash,
...                     free_cash=exec_state.free_cash,
...                     val_price=val_price,
...                     value=value
...                 )
...                 order = vbt.pf_nb.order_nb(
...                     size=target_pct[i, col],
...                     price=close[i, col],
...                     size_type=vbt.pf_enums.SizeType.TargetPercent
...                 )
...                 _, exec_state = vbt.pf_nb.process_order_nb(
...                     col, col, i,  # (4)!
...                     exec_state=exec_state,
...                     order=order,
...                     order_records=order_records,
...                     order_counts=order_counts
...                 )
...         
...     return vbt.nb.repartition_nb(order_records, order_counts)  # (4)!
```

1. Since we cannot know the number of orders in advance, let's prepare for the worst-case scenario:
one record per bar. Remember, order records must be aligned column-wise.
2. Iterate over the columns in `close` and run our logic for each one.
3. Now that every array passed to the pipeline must be two-dimensional, remember to specify
the column when accessing an array element. In indexing, the row comes first, then the column :point_up:
4. Use [repartition_nb](https://vectorbt.pro/pvt_6d1b3986/api/generic/nb/base/#vectorbtpro.generic.nb.base.repartition_nb) to flatten
the final order records array (this concatenates records from all columns into a one-dimensional array).
5. Since each column represents an independent backtest, groups correspond to columns.

!!! info
    We flatten (repartition) order records because most records remain unfilled,
    which wastes memory. By flattening, we compress them effectively, without losing any information,
    since each record tracks the column it belongs to.

Our pipeline now expects all arrays to be two-dimensional. Let's test three different values
for the parameter `every`, which controls re-allocation periodicity. To do this, we need to
expand all arrays so they have the same number of columns as the number of parameter combinations.

```pycon
>>> every = pd.Index(["M", "Q", "Y"], name="every")

>>> open = data.get("Open").vbt.tile(3, keys=every)  # (1)!
>>> close = data.get("Close").vbt.tile(3, keys=every)
>>> close
every                                 M             Q             Y
Date                                                               
2014-09-17 00:00:00+00:00    457.334015    457.334015    457.334015
2014-09-18 00:00:00+00:00    424.440002    424.440002    424.440002
2014-09-19 00:00:00+00:00    394.795990    394.795990    394.795990
...                                 ...           ...           ...
2021-12-29 00:00:00+00:00  46444.710938  46444.710938  46444.710938
2021-12-30 00:00:00+00:00  47178.125000  47178.125000  47178.125000
2021-12-31 00:00:00+00:00  46306.445312  46306.445312  46306.445312

[2663 rows x 3 columns]

>>> target_pct = symbol_wrapper.fill().vbt.tile(3, keys=every)
>>> target_pct.vbt.set(0.5, every="M", columns=["M"], inplace=True)  # (2)!
>>> target_pct.vbt.set(0.5, every="Q", columns=["Q"], inplace=True)
>>> target_pct.vbt.set(0.5, every="Y", columns=["Y"], inplace=True)

>>> order_records = pipeline_3_nb(
...     open.values, 
...     close.values, 
...     target_pct.values
... )
>>> order_records
array([( 0, 0,   14, 1.29056570e-01,   383.61499023, 0., 0),  << first column
       ( 1, 0,   45, 1.00206092e-02,   325.74899292, 0., 0),
       ( 2, 0,   75, 7.10912824e-03,   379.24499512, 0., 1),
       ...
       (84, 0, 2571, 7.79003416e-04, 48116.94140625, 0., 0),
       (85, 0, 2602, 3.00678739e-03, 61004.40625   , 0., 1),
       (86, 0, 2632, 6.84410394e-04, 57229.828125  , 0., 0),
       ( 0, 1,   13, 1.32947604e-01,   386.94400024, 0., 0),  << second column
       ( 1, 1,  105, 1.16132613e-02,   320.19299316, 0., 0),
       ( 2, 1,  195, 1.83187063e-02,   244.22399902, 0., 0),
       ...
       (27, 1, 2478, 7.74416872e-03, 35040.8359375 , 0., 0),
       (28, 1, 2570, 2.08567037e-03, 43790.89453125, 0., 1),
       (29, 1, 2662, 1.72637091e-03, 46306.4453125 , 0., 1),
       ( 0, 2,  105, 1.60816173e-01,   320.19299316, 0., 0),  << third column
       ( 1, 2,  470, 2.34573523e-02,   430.56698608, 0., 1),
       ( 2, 2,  836, 3.81744650e-02,   963.74298096, 0., 1),
       ...
       ( 5, 2, 1931, 2.83026812e-02,  7193.59912109, 0., 1),
       ( 6, 2, 2297, 3.54188390e-02, 29001.72070312, 0., 1),
       ( 7, 2, 2662, 1.14541249e-02, 46306.4453125 , 0., 1)],
      dtype={'names':['id','col','idx','size','price','fees','side'], ...})
```

1. Use [BaseAccessor.tile](https://vectorbt.pro/pvt_6d1b3986/api/base/accessors/#vectorbtpro.base.accessors.BaseAccessor.tile)
to populate columns and add a new column level for our parameter combinations.
2. Change only the corresponding column.

### Wrapping

This output is exactly what [Portfolio](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio)
expects as input: order records, along with a few other arguments, can be used to reconstruct
the simulation state, including the regular cash balance and the position size at each time step.
The reconstructed state allows you to model the equity curve, then calculate returns, and finally
derive related metrics such as the classic Sharpe ratio. So, how do we construct a portfolio?
Instead of using a class method, we will provide the data directly to the class. For this,
only three arguments are required: a wrapper, a close series, and order records. Ideally,
we should also provide arguments that were used during the simulation, such as the initial cash:

```pycon
>>> vbt.phelp(vbt.Portfolio)
Portfolio.__init__(
    self,
    wrapper,
    order_records,
    *,
    close,
    open=None,
    high=None,
    low=None,
    log_records=None,
    cash_sharing=False,
    init_cash='auto',
    ...
)
```

!!! hint
    See the `*`? This means any argument after `order_records` must be specified as a keyword argument.

Let's do the wrapping step:

```pycon
>>> pf = vbt.Portfolio(
...     close.vbt.wrapper,
...     order_records,
...     open=open,
...     close=close,
...     init_cash=100  # (1)!
... )
```

1. Make sure to use the same initial cash as during the simulation.

You can now interact with the portfolio the same way as if you simulated it with any preset method:

```pycon
>>> pf.sharpe_ratio
every
MS    1.267804
Q     1.309943
Y     1.393820
Name: sharpe_ratio, dtype: float64
```

## Flexible indexing

The issue with bringing all arrays to the same shape, as we did above, is that it unnecessarily
consumes memory. Even though the only array with different data in each column is `target_pct`, 
we have almost tripled memory consumption by having to expand other arrays like `close`. 
Imagine how expensive it would be to align dozens of such array-like arguments :face_exhaling:

Flexible indexing lets us avoid this alignment step and access each element of an array based
solely on its shape. For example, there is no need to tile `close` three times if each row remains
the same in every column. We can simply return the same row element, regardless of the column
being accessed. The same applies to a one-dimensional array with elements per column—return the
same column element for each row. The only requirement is that the array must have one dimension
if it should broadcast against rows or columns, and two dimensions if it should broadcast against
both rows and columns. Any scalars should be transformed into one of these formats; otherwise,
we will encounter an ugly Numba error.

For actual indexing, we can use the following Numba-compiled functions:

* One-dimensional array (generic): [flex_select_1d_nb](https://vectorbt.pro/pvt_6d1b3986/api/base/flex_indexing/#vectorbtpro.base.flex_indexing.flex_select_1d_nb).
* One-dimensional array (per row): [flex_select_1d_pr_nb](https://vectorbt.pro/pvt_6d1b3986/api/base/flex_indexing/#vectorbtpro.base.flex_indexing.flex_select_1d_pr_nb).
* One-dimensional array (per column): [flex_select_1d_pc_nb](https://vectorbt.pro/pvt_6d1b3986/api/base/flex_indexing/#vectorbtpro.base.flex_indexing.flex_select_1d_pc_nb).
* Two-dimensional array: [flex_select_nb](https://vectorbt.pro/pvt_6d1b3986/api/base/flex_indexing/#vectorbtpro.base.flex_indexing.flex_select_nb).

Let's see how to use them in different scenarios:

```pycon
>>> per_row_arr = np.array([1, 2, 3])
>>> per_col_arr = np.array([4, 5])
>>> per_elem_arr = np.array([
...     [6, 7],
...     [8, 9],
...     [10, 11]
... ])

>>> vbt.flex_select_1d_pr_nb(per_row_arr, 2)  # (1)!
3

>>> vbt.flex_select_1d_pc_nb(per_col_arr, 1)  # (2)!
5

>>> vbt.flex_select_nb(per_elem_arr, 2, 1)  # (3)!
11
```

1. Get the value under the third row.
2. Get the value under the second column.
3. Get the value under the third row and second column.

One-dimensional indexing functions work only for arguments that are one-dimensional by design,
such as initial capital (which only makes sense provided per column, not per element).
But what if the user should also be able to pass `per_row_arr` or `per_col_arr` as fully-broadcast arrays?
In this case, the user needs to expand both arrays to two dimensions, following [NumPy's broadcasting
rules](https://numpy.org/doc/stable/user/basics.broadcasting.html), and use exclusively 
[flex_select_nb](https://vectorbt.pro/pvt_6d1b3986/api/base/flex_indexing/#vectorbtpro.base.flex_indexing.flex_select_nb). The reason
for this is that Numba is not flexible enough to allow operations on both one-dimensional
and two-dimensional arrays, so we must choose the indexing function in advance.

```pycon
>>> per_row_arr_2d = per_row_arr[:, None]  # (1)!
>>> per_row_arr_2d
array([[1],
       [2],
       [3]])
       
>>> vbt.flex_select_nb(per_row_arr_2d, 2, 1)
3

>>> per_col_arr_2d = per_col_arr[None]  # (2)!
>>> per_col_arr_2d
array([[4, 5]])

>>> vbt.flex_select_nb(per_col_arr_2d, 2, 1)
5
```

1. Create the second axis of length one: from `(3,)` to `(3, 1)`.
2. Create the first axis of length one: from `(2,)` to `(1, 2)`.

This provides the same results as if we had aligned the arrays before indexing, which is memory-intensive:

```pycon
>>> target_shape = (3, 2)

>>> vbt.broadcast_array_to(per_row_arr, target_shape[0])[2]
3

>>> vbt.broadcast_array_to(per_col_arr, target_shape[1])[1]
5

>>> vbt.broadcast_array_to(per_row_arr_2d, target_shape)[2, 1]
3

>>> vbt.broadcast_array_to(per_col_arr_2d, target_shape)[2, 1]
5
```

!!! hint
    If you are not sure whether a flexible array will be indexed correctly, try broadcasting it with NumPy!

### Rotational indexing

But what happens if the index is out of bounds? For example, suppose we are iterating over 6 columns, but 
an array holds data for only 3. In this situation, VBT can rotate the index and return the first element 
in the array for the fourth column, the second element for the fifth column, and so on:

```pycon
>>> vbt.flex_select_1d_pr_nb(per_row_arr, 100, rotate_rows=True)  # (1)!
2

>>> vbt.flex_select_1d_pc_nb(per_col_arr, 100, rotate_cols=True)  # (2)!
4

>>> vbt.flex_select_nb(per_elem_arr, 100, 100, rotate_rows=True, rotate_cols=True)
8
```

1. Resolves to index 100 % 3 == 1 and element 2.
2. Resolves to index 100 % 2 == 0 and element 4.

If you find this behavior odd and would prefer an error instead: rotational indexing is actually very helpful 
when testing multiple assets and parameter combinations. Without it (the default), we would need to tile 
the asset DataFrame by the number of parameter combinations. With it, we can pass the data 
without tiling and avoid wasting memory. Still, in many cases, VBT ensures that all arrays 
can broadcast against each other as needed.

### Pipeline/4

Let's adapt the previous pipeline for flexible indexing. Usually, we do not know which of the 
provided arrays has the full shape, or there may not be any array with the full shape at all. 
We need to introduce another argument—`target_shape`—to specify the full shape for our loops 
to iterate over. We will also try out rotational indexing, which is not supported 
by any preset simulation methods.

```pycon
>>> @njit
... def pipeline_4_nb(
...     target_shape, 
...     open, 
...     close, 
...     target_pct, 
...     init_cash=100,
...     rotate_cols=False
... ):
...     init_cash_ = vbt.to_1d_array_nb(np.asarray(init_cash))  # (1)!
...     open_ = vbt.to_2d_array_nb(np.asarray(open))  # (2)!
...     close_ = vbt.to_2d_array_nb(np.asarray(close))
...     target_pct_ = vbt.to_2d_array_nb(np.asarray(target_pct))
...     order_records = np.empty(target_shape, dtype=vbt.pf_enums.order_dt)
...     order_counts = np.full(target_shape[1], 0, dtype=int_)
...
...     for col in range(target_shape[1]):
...         init_cash_elem = vbt.flex_select_1d_pc_nb(
...             init_cash_, col, rotate_cols=rotate_cols)  # (3)!
...
...         exec_state = vbt.pf_enums.ExecState(
...             cash=float(init_cash_elem),
...             position=0.0,
...             debt=0.0,
...             locked_cash=0.0,
...             free_cash=float(init_cash_elem),
...             val_price=np.nan,
...             value=np.nan
...         )
...
...         for i in range(target_shape[0]):
...             open_elem = vbt.flex_select_nb(
...                 open_, i, col, rotate_cols=rotate_cols)  # (4)!
...             close_elem = vbt.flex_select_nb(
...                 close_, i, col, rotate_cols=rotate_cols)
...             target_pct_elem = vbt.flex_select_nb(
...                 target_pct_, i, col, rotate_cols=rotate_cols)
...
...             if not np.isnan(target_pct_elem):
...                 value = exec_state.cash + open_elem * exec_state.position
...
...                 exec_state = vbt.pf_enums.ExecState(
...                     cash=exec_state.cash,
...                     position=exec_state.position,
...                     debt=exec_state.debt,
...                     locked_cash=exec_state.locked_cash,
...                     free_cash=exec_state.free_cash,
...                     val_price=open_elem,
...                     value=value
...                 )
...                 order = vbt.pf_nb.order_nb(
...                     size=target_pct_elem,
...                     price=close_elem,
...                     size_type=vbt.pf_enums.SizeType.TargetPercent
...                 )
...                 _, exec_state = vbt.pf_nb.process_order_nb(
...                     col, col, i,
...                     exec_state=exec_state,
...                     order=order,
...                     order_records=order_records,
...                     order_counts=order_counts
...                 )
...         
...     return vbt.nb.repartition_nb(order_records, order_counts)
```

1. This line allows us to pass a one-dimensional flexible array or a scalar. Notice how we
assign the result to a new variable (with a trailing underscore) and then use it for indexing.
2. Same concept for two-dimensional flexible arrays.
3. Select the current element of the initial cash array. Remember, indexing functions
with the `1d` suffix require one-dimensional arrays.
4. Since none of the three arrays are guaranteed to have the full shape now,
we must use flexible indexing instead of `open[i, col]`. Indexing functions
without the `1d` suffix expect two-dimensional arrays.

Thanks to flexible indexing, we can now use all arrays without tiling:

```pycon
>>> target_shape = vbt.broadcast_shapes(  # (1)!
...     data.get("Open").values.shape,
...     data.get("Close").values.shape,
...     target_pct.values.shape
... )
>>> target_shape
(2663, 3)

>>> order_records = pipeline_4_nb(
...     target_shape,
...     data.get("Open").values,
...     data.get("Close").values,
...     target_pct.values
... )
>>> len(order_records)
125
```

1. We need to build the target shape for iteration. This also acts as a broadcasting check.

This approach also lets us provide target percentages as a constant to re-allocate at each bar!
Since constants do not affect the target shape, we only need to broadcast the price shapes:

```pycon
>>> target_shape = vbt.broadcast_shapes(
...     data.get("Open").values.shape,
...     data.get("Close").values.shape
... )
>>> target_shape
(2663,)

>>> target_shape = vbt.to_2d_shape(target_shape)  # (1)!
>>> target_shape
(2663, 1)

>>> order_records = pipeline_4_nb(
...     target_shape,
...     data.get("Open").values,
...     data.get("Close").values,
...     0.5
... )
len(order_records)
2663
```

1. Target shape must always be two-dimensional.

This operation has produced the same number of orders as there are elements in the data:

```pycon
>>> np.prod(symbol_wrapper.shape_2d)
2663
```

To demonstrate rotational indexing, let's pull multiple symbols and run the simulation 
without having to tile or otherwise modify them:

```pycon
>>> mult_data = vbt.YFData.pull(
...     ["BTC-USD", "ETH-USD"], 
...     end="2022-01-01",
...     missing_index="drop"
... )
```

[=100% "Symbol 2/2"]{: .candystripe .candystripe-animate }

```pycon
>>> mult_symbol_wrapper = mult_data.get_symbol_wrapper()
>>> mult_target_pct = pd.concat([
...     mult_symbol_wrapper.fill().vbt.set(0.5, every=every[i])
...     for i in range(len(every))
... ], axis=1, keys=every)  # (1)!

>>> target_shape = vbt.broadcast_shapes(
...     vbt.tile_shape(mult_data.get("Open").values.shape, len(every)),  # (2)!
...     vbt.tile_shape(mult_data.get("Close").values.shape, len(every)), 
...     mult_target_pct.values.shape
... )
>>> target_shape
(1514, 6)

>>> order_records = pipeline_4_nb(
...     target_shape,
...     mult_data.get("Open").values,  # (3)!
...     mult_data.get("Close").values,
...     mult_target_pct.values,
...     rotate_cols=True
... )
>>> len(order_records)
142
```

1. This is another way to construct the target percentage array.
2. Since broadcasting does not support rotations, use [tile_shape](https://vectorbt.pro/pvt_6d1b3986/api/base/reshaping/#vectorbtpro.base.reshaping.tile_shape)
to tile the shape of `open` and `close` manually. Do not tile the actual array!
3. There is no need to tile any array thanks to rotational indexing.

Without rotation, we would get an _"IndexError: index out of bounds"_ error, as the 
number of columns in the target shape is greater than that in the price arrays.

## Grouping

Using groups, we can combine multiple columns into the same backtesting basket :basket:

Typically, a group consists of several columns that belong to a single portfolio entity 
and should be backtested as a single unit. Most often, we use groups to share capital among 
multiple columns, but groups can also bind columns on a logical level. During a simulation, 
it is up to us to use grouping as needed. For example, while 
[process_order_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.process_order_nb) requires 
a group index, it only uses it for filling log records and nothing else. After the simulation, 
VBT provides many tools to help us aggregate and analyze different types of information 
by group, such as portfolio value.

Groups can be built and supplied in two ways: as group lengths or as a group map. 
Group lengths are easier to manage, marginally faster, and require columns to be organized into 
monolithic groups. A group map, on the other hand, allows the columns of a group to be distributed 
arbitrarily and offers greater flexibility overall. Simulation methods mainly use group lengths (since 
asset columns, unlike parameter columns, are generally located together), 
while group maps are mostly used by generic functions for pre- and post-analysis. 
Both formats can be easily generated by a
[Grouper](https://vectorbt.pro/pvt_6d1b3986/api/base/grouping/base/#vectorbtpro.base.grouping.base.Grouper) instance.

### Group lengths

Let's create a custom column index with 5 assets and assign them to 2 groups. Because group lengths 
only support monolithic groups, the assets in each group must be next to each other:

```pycon
>>> columns = pd.Index(["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD"])
>>> mono_grouper = vbt.Grouper(columns, group_by=[0, 0, 0, 1, 1])
>>> mono_grouper.get_group_lens()  # (1)!
array([3, 2])
```

1. Using [Grouper.get_group_lens](https://vectorbt.pro/pvt_6d1b3986/api/base/grouping/base/#vectorbtpro.base.grouping.base.Grouper.get_group_lens)

The first element in the returned array is the number of columns with the label `0`, 
and the second element is the number of columns with the label `1`.

!!! hint
    [Grouper](https://vectorbt.pro/pvt_6d1b3986/api/base/grouping/base/#vectorbtpro.base.grouping.base.Grouper) accepts either 
    a list of integers or a sequence of strings as input and will convert everything into a 
    Pandas Index to treat as group labels. The labels **do not** need to be alphanumerically sorted.

If we use distributed groups, group length generation will fail:

```pycon
>>> dist_grouper = vbt.Grouper(columns, group_by=[0, 1, 0, 1, 1])
>>> dist_grouper.get_group_lens()
ValueError: group_by must form monolithic groups
```

So, how do we define logic per group? Here is a template:

```pycon
>>> group_lens = mono_grouper.get_group_lens()

>>> group_end_idxs = np.cumsum(group_lens)  # (1)!
>>> group_start_idxs = group_end_idxs - group_lens  # (2)!

>>> for group in range(len(group_lens)):  # (3)!
...     from_col = group_start_idxs[group]
...     to_col = group_end_idxs[group]
...     # (4)!
...
...     for col in range(from_col, to_col):  # (5)!
...         pass  # (6)!
```

1. Get the end column index of each group (excluding).
2. Get the start column index of each group (including).
3. Iterate over all groups.
4. Define your logic for each group here.
5. Iterate over all columns in the group.
6. Define your logic for each column in the group here.

### Group map

A group map consists of a tuple with two arrays:

1. A one-dimensional array containing column indices sorted by group.
2. A one-dimensional array specifying the length of each group in the first array.

This means a group map turns distributed groups into monolithic ones, allowing you to work with 
any group arrangement:

```pycon
>>> mono_grouper.get_group_map()
(array([0, 1, 2, 3, 4]), array([3, 2]))

>>> dist_grouper.get_group_map()
(array([0, 2, 1, 3, 4]), array([2, 3]))
```

In the second example, the first two (`2`) column indices in the first array belong to the first group, 
while the remaining three (`3`) column indices belong to the second group.

Here is a template for working with a group map:

```pycon
>>> group_map = dist_grouper.get_group_map()

>>> group_idxs, group_lens = group_map
>>> group_start_idxs = np.cumsum(group_lens) - group_lens  # (1)!

>>> for group in range(len(group_lens)):
...     group_len = group_lens[group]
...     start_idx = group_start_idxs[group]
...     col_idxs = group_idxs[start_idx : start_idx + group_len]  # (2)!
...     # (3)!
... 
...     for k in range(len(col_idxs)):  # (4)!
...         col = col_idxs[k]
...         # (5)!
```

1. Get the start index of each group in the first array.
2. Get the column indices for the group in the first array.
3. Define your logic for each group here.
4. Iterate over all column indices in the group.
5. Define your logic for each column in the group here.

### Call sequence

When sharing capital between multiple assets, we may want to process one column before the others. 
This is useful, for example, when closing positions before opening new ones to free up capital. 
If we look at the templates for both grouping formats above, the place to change 
the processing order is in the for-loop over the columns. How can we adjust this order programmatically? 
This is where the call sequence comes into play.

A call sequence is an array of column indices representing the order in which columns should be processed. 
For example, if you want to process the third column first, the first column second, and the second column 
third, your call sequence would be `[2, 0, 1]`. You always move from left to right in the call sequence, 
selecting the current column index. This approach has one major advantage: you can use another array, 
such as an array of order values, to (arg-)sort the call sequence.

Sorting is handled by the function [insert_argsort_nb](https://vectorbt.pro/pvt_6d1b3986/api/utils/array_/#vectorbtpro.utils.array_.insert_argsort_nb), 
which takes an array of values to sort by and an array of indices, sorting the indices in-place using 
[insertion sort](https://en.wikipedia.org/wiki/Insertion_sort) according to the order of 
the values in the first array. This algorithm works best for small arrays and requires no additional 
memory—perfect for asset groups!

Suppose you have three assets: one with no position, one with a short position, and one with a long position. 
If you want to close all positions, you should process the assets that will free up funds first, 
so you have enough cash to close other positions. To do this, start by using 
[approx_order_value_nb](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/nb/core/#vectorbtpro.portfolio.nb.core.approx_order_value_nb) 
to estimate the order value for each operation:

```pycon
>>> position = np.array([0.0, -10.0, 10.0])
>>> val_price = np.array([10.0, 25.0, 15.0])
>>> debt = np.array([0.0, 100.0, 0.0])
>>> locked_cash = np.array([0.0, 100.0, 0.0])
>>> order_value = np.empty(3, dtype=float_)

>>> for col in range(len(position)):
...     exec_state = vbt.pf_enums.ExecState(
...         cash=200.0,  # (1)!
...         position=position[col],  # (2)!
...         debt=debt[col],
...         locked_cash=locked_cash[col],
...         free_cash=0.0,
...         val_price=val_price[col],
...         value=100.0
...     )
...     order_value[col] = vbt.pf_nb.approx_order_value_nb(
...         exec_state=exec_state,
...         size=0.,
...         size_type=vbt.pf_enums.SizeType.TargetAmount,
...         direction=vbt.pf_enums.Direction.Both
...     )
    
>>> order_value  # (3)!
array([0., 50., -150.])
```

1. Cash-related information is defined per group using a constant.
2. Position-related information is defined per column using an array.
3. A positive number means outbound cash flow; a negative number means inbound cash flow.

In this case, closing the second column requires about $50, while the third column would 
bring in about $150 by closing out the position. Let's create a call sequence and sort 
it by order value:

```pycon
>>> from vectorbtpro.utils.array_ import insert_argsort_nb

>>> call_seq = np.array([0, 1, 2])  # (1)!
>>> insert_argsort_nb(order_value, call_seq)
>>> call_seq
array([2, 0, 1])
```

1. Always begin with a simple range.

!!! note
    Both the order value and the call sequence are sorted in-place!

Now we can modify the for-loop to iterate over the call sequence instead:

```pycon
>>> for k in range(len(call_seq)):  # (1)!
...     c = call_seq[k]
...     col = from_col + c

>>> for k in range(len(call_seq)):  # (2)!
...     c = call_seq[k]
...     col = col_idxs[c]
```

1. For group lengths.
2. For a group map.

!!! hint
    It is good practice to use consistent variable names. Here, `k` is the index in the call sequence, 
    `c` is the column index within a group, and `col` is the global column index.

### Pipeline/5

Let's upgrade our previous pipeline to rebalance groups of assets. To better illustrate how 
important sorting by order value is when rebalancing multi-asset portfolios, we will introduce another 
argument, `auto_call_seq`, to switch between sorting and not sorting. We will use group lengths 
as the grouping format because of its simplicity. Also, now we need to keep 
a lot of position-related information in arrays rather than constants, since this information 
corresponds to columns instead of groups. Additionally, since we already know how to fill order records, 
let's track the allocation at each bar instead.

```pycon
>>> @njit
... def pipeline_5_nb(
...     target_shape,  # (1)!
...     group_lens,  # (2)!
...     open,
...     close, 
...     target_pct,  # (3)!
...     init_cash=100,
...     auto_call_seq=True,
...     rotate_cols=False
... ):
...     init_cash_ = vbt.to_1d_array_nb(np.asarray(init_cash))
...     open_ = vbt.to_2d_array_nb(np.asarray(open))
...     close_ = vbt.to_2d_array_nb(np.asarray(close))
...     target_pct_ = vbt.to_2d_array_nb(np.asarray(target_pct))
...     alloc = np.empty(target_shape, dtype=float_)  # (4)!
...
...     group_end_idxs = np.cumsum(group_lens)
...     group_start_idxs = group_end_idxs - group_lens
...
...     for group in range(len(group_lens)):  # (5)!
...         group_len = group_lens[group]
...         from_col = group_start_idxs[group]
...         to_col = group_end_idxs[group]
...
...         # (6)!
...         init_cash_elem = vbt.flex_select_1d_pc_nb(
...             init_cash_, group, rotate_cols=rotate_cols)
...     
...         last_position = np.full(group_len, 0.0, dtype=float_)  # (7)!
...         last_debt = np.full(group_len, 0.0, dtype=float_)
...         last_locked_cash = np.full(group_len, 0.0, dtype=float_)
...         cash_now = float(init_cash_elem)
...         free_cash_now = float(init_cash_elem)
...
...         order_value = np.empty(group_len, dtype=float_)  # (8)!
...         call_seq = np.empty(group_len, dtype=int_)
... 
...         for i in range(target_shape[0]):  # (9)!
...             # (10)!
...             value_now = cash_now
...             for c in range(group_len):
...                 col = from_col + c
...                 open_elem = vbt.flex_select_nb(
...                     open_, i, col, rotate_cols=rotate_cols)
...                 value_now += last_position[c] * open_elem  # (11)!
...         
...             # (12)!
...             for c in range(group_len):
...                 col = from_col + c
...                 open_elem = vbt.flex_select_nb(
...                     open_, i, col, rotate_cols=rotate_cols)
...                 target_pct_elem = vbt.flex_select_nb(
...                     target_pct_, i, col, rotate_cols=rotate_cols)
...                 exec_state = vbt.pf_enums.ExecState(
...                     cash=cash_now,
...                     position=last_position[c],
...                     locked_cash=last_locked_cash[c],
...                     debt=last_debt[c],
...                     free_cash=free_cash_now,
...                     val_price=open_elem,
...                     value=value_now,
...                 )
...                 order_value[c] = vbt.pf_nb.approx_order_value_nb(  # (13)!
...                     exec_state=exec_state,
...                     size=target_pct_elem,
...                     size_type=vbt.pf_enums.SizeType.TargetPercent,
...                     direction=vbt.pf_enums.Direction.Both
...                 )
...                 call_seq[c] = c  # (14)!
... 
...             if auto_call_seq:
...                 vbt.pf_nb.insert_argsort_nb(order_value, call_seq)  # (15)!
... 
...             for k in range(len(call_seq)):  # (16)!
...                 c = call_seq[k]  # (17)!
...                 col = from_col + c  # (18)!
...
...                 open_elem = vbt.flex_select_nb(
...                     open_, i, col, rotate_cols=rotate_cols)
...                 close_elem = vbt.flex_select_nb(
...                     close_, i, col, rotate_cols=rotate_cols)
...                 target_pct_elem = vbt.flex_select_nb(
...                     target_pct_, i, col, rotate_cols=rotate_cols)
...
...                 if not np.isnan(target_pct_elem):  # (19)!
...                     order = vbt.pf_nb.order_nb(
...                         size=target_pct_elem,
...                         price=close_elem,
...                         size_type=vbt.pf_enums.SizeType.TargetPercent,
...                         direction=vbt.pf_enums.Direction.Both
...                     )
...                     exec_state = vbt.pf_enums.ExecState(
...                         cash=cash_now,
...                         position=last_position[c],
...                         debt=last_debt[c],
...                         locked_cash=last_locked_cash[c],
...                         free_cash=free_cash_now,
...                         val_price=open_elem,
...                         value=value_now,
...                     )
...                     _, new_exec_state = vbt.pf_nb.process_order_nb(
...                         group=group,
...                         col=col,
...                         i=i,
...                         exec_state=exec_state,
...                         order=order
...                     )
...                     cash_now = new_exec_state.cash
...                     free_cash_now = new_exec_state.free_cash
...                     value_now = new_exec_state.value
...                     last_position[c] = new_exec_state.position
...                     last_debt[c] = new_exec_state.debt
...                     last_locked_cash[c] = new_exec_state.locked_cash
...
...             # (20)!
...             value_now = cash_now
...             for c in range(group_len):
...                 col = from_col + c
...                 close_elem = vbt.flex_select_nb(
...                     close_, i, col, rotate_cols=rotate_cols)
...                 value_now += last_position[c] * close_elem
...
...             # (21)!
...             for c in range(group_len):
...                 col = from_col + c
...                 close_elem = vbt.flex_select_nb(
...                     close_, i, col, rotate_cols=rotate_cols)
...                 alloc[i, col] = last_position[c] * close_elem / value_now
... 
...     return alloc
```

1. The second number in the target shape tracks assets (across parameter combinations). It does not track groups.
2. The group lengths array must contain as many elements as there are groups, and the sum of this array 
must equal the number of columns in `target_shape`.
3. Target allocations must be provided per asset, so the array should broadcast against `target_shape`.
4. Allocations must be filled per asset, so use the same shape as `target_shape`.
5. Iterate over groups.
6. Here, create various arrays that should exist only per group, such as the cash balance, 
position size per asset, and other state information. Remember, different groups represent independent, 
isolated tests and should not be connected in any way!
7. We cannot create a single instance of [ExecState](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/enums/#vectorbtpro.portfolio.enums.ExecState) 
as before, because the order execution state contains information for each asset. Therefore, 
we need to keep track of its fields using separate variables (constants for data per group, 
arrays for data per asset).
8. We could also create these two arrays at each bar, but frequent creation of arrays 
slows down the simulation. It is better to create an array just once and re-fill it as needed.
9. Iterate over time steps (bars), as in previous pipelines.
10. Calculate the value of each group (= portfolio value) by iterating over the assets in the group 
and adding their position value to the current cash balance.
11. The last position array is only for this group, so we use `c`, not `col`.
12. Prepare the order value and call sequence arrays.
13. Approximate the value of a potential order. At the beginning of the bar, use the open price.
14. Store the current column index within this group. This will relate order values to column indices.
15. Sort both arrays in-place so column indices with lower order values appear first 
in the call sequence.
16. Next, execute orders by iterating over the newly sorted call sequence.
17. Get the associated column index within the group.
18. Get the associated global column index.
19. Perform the same logic as in the previous pipeline.
20. Calculate the group value again, now using the updated position and the close price. 
This is done outside the `np.nan` check to track the allocation at each bar.
21. Calculate the current allocation of each asset and write it to the output array.

Wow, this became complex really fast! :dizzy_face:

But it is not as complex as it may seem. We simply take a set of columns and split them into 
groups. Then, for each group, we define a mini-pipeline that applies our logic only to the columns 
within that group, treating it as a single portfolio unit. At the beginning of each bar, we calculate 
the portfolio value and build a call sequence to rearrange the columns by their order value. We then 
iterate over this sequence and execute an order in each column. Finally, at the end of each bar, 
we recalculate the portfolio value and store the real allocation of each asset in the output array.

The best part of this pipeline is that it closely mimics how preset simulation methods work in VBT, 
and it is one of the most flexible pieces of code you can actually write!

Let's allocate 70% to BTC and 30% to ETH, and rebalance on a monthly basis:

```pycon
>>> mult_target_pct = mult_symbol_wrapper.fill()
>>> mult_target_pct.vbt.set([[0.7, 0.3]], every="M", inplace=True)
>>> grouper = vbt.Grouper(mult_symbol_wrapper.columns, group_by=True)
>>> group_lens = grouper.get_group_lens()

>>> target_shape = vbt.broadcast_shapes(
...     mult_data.get("Open").values.shape,
...     mult_data.get("Close").values.shape,
...     mult_target_pct.values.shape
... )
>>> target_shape
(1514, 2)

>>> alloc = pipeline_5_nb(
...     target_shape,
...     group_lens,
...     mult_data.get("Open").values,
...     mult_data.get("Close").values,
...     mult_target_pct.values
... )
>>> alloc = mult_symbol_wrapper.wrap(alloc)
>>> alloc.vbt.plot(
...    trace_kwargs=dict(stackgroup="one"),
...    use_gl=False
... ).show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/documentation/pf/pipeline_5_auto_call_seq.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/documentation/pf/pipeline_5_auto_call_seq.dark.svg#only-dark){: .iimg loading=lazy }

!!! info
    As you might have noticed, some allocations do not add up exactly to 100%. This is because we used the 
    open price for group valuation and decision-making, while the actual orders were executed using 
    the close price. By the way, it is a bad sign when everything aligns perfectly—this could mean 
    your simulation is too ideal for the real world.

And here is the same procedure but without sorting the call sequence array:

```pycon
>>> alloc = pipeline_5_nb(
...     target_shape,
...     group_lens,
...     mult_data.get("Open").values,
...     mult_data.get("Close").values,
...     mult_target_pct.values,
...     auto_call_seq=False
... )
>>> alloc = mult_symbol_wrapper.wrap(alloc)
>>> alloc.vbt.plot(
...    trace_kwargs=dict(stackgroup="one"),
...    use_gl=False
... ).show()
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/documentation/pf/pipeline_5_wo_auto_call_seq.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/documentation/pf/pipeline_5_wo_auto_call_seq.dark.svg#only-dark){: .iimg loading=lazy }

As we can see, some rebalancing steps could not be completed at all because long operations 
were executed before short operations, leaving them without the required funds.

The biggest advantage of this pipeline is its flexibility: we can turn off grouping via `group_by=False` 
to run the entire logic per column (each group will then contain only one column). We can also test 
multiple weight combinations with multiple groups, without having to tile the pricing data 
thanks to rotational indexing. This, for example, cannot be done even with 
[Portfolio.from_orders](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from_orders) :wink:

```pycon
>>> groups = pd.Index([0, 0, 1, 1], name="group")
>>> target_alloc = pd.Index([0.7, 0.3, 0.5, 0.5], name="target_alloc")

>>> final_columns = vbt.stack_indexes((  # (1)!
...     groups,
...     target_alloc, 
...     vbt.tile_index(mult_symbol_wrapper.columns, 2)
... ))
>>> final_wrapper = mult_symbol_wrapper.replace(  # (2)!
...     columns=final_columns,
...     group_by="group"
... )
>>> mult_target_pct = final_wrapper.fill(group_by=False)  # (3)!
>>> mult_target_pct.vbt.set(target_alloc.values[None], every="M", inplace=True)
>>> group_lens = final_wrapper.grouper.get_group_lens()

>>> n_groups = final_wrapper.grouper.get_group_count()
>>> target_shape = vbt.broadcast_shapes(
...     vbt.tile_shape(mult_data.get("Open").values.shape, n_groups),  # (4)!
...     vbt.tile_shape(mult_data.get("Close").values.shape, n_groups), 
...     mult_target_pct.values.shape
... )
>>> target_shape
(1514, 4)

>>> alloc = pipeline_5_nb(
...     target_shape,
...     group_lens,
...     mult_data.get("Open").values,
...     mult_data.get("Close").values, 
...     mult_target_pct.values,
...     rotate_cols=True
... )
>>> alloc = mult_target_pct.vbt.wrapper.wrap(alloc)
>>> alloc
group                                       0                   1          
target_alloc                    0.7       0.3       0.5       0.5
symbol                      BTC-USD   ETH-USD   BTC-USD   ETH-USD
Date                                                             
2017-11-09 00:00:00+00:00  0.000000  0.000000  0.000000  0.000000
2017-11-10 00:00:00+00:00  0.000000  0.000000  0.000000  0.000000
2017-11-11 00:00:00+00:00  0.000000  0.000000  0.000000  0.000000
2017-11-12 00:00:00+00:00  0.000000  0.000000  0.000000  0.000000
2017-11-13 00:00:00+00:00  0.000000  0.000000  0.000000  0.000000
...                             ...       ...       ...       ...
2021-12-27 00:00:00+00:00  0.703817  0.296183  0.504464  0.495536
2021-12-28 00:00:00+00:00  0.703452  0.296548  0.504026  0.495974
2021-12-29 00:00:00+00:00  0.708035  0.291965  0.509543  0.490457
2021-12-30 00:00:00+00:00  0.706467  0.293533  0.507650  0.492350
2021-12-31 00:00:00+00:00  0.704346  0.295654  0.505099  0.494901

[1514 rows x 4 columns]
```

1. Build a new column hierarchy with three levels: groups, weights, and assets. 
Each level must have the same length.
2. Create a new (grouped) wrapper with the new column hierarchy.
3. Create the target percentage array with the same shape as the new wrapper and fill it with NaN.
4. We are using rotational indexing—tile the shapes of `open` and `close` by the number of groups 
for the shapes to broadcast correctly, and build the target shape.

## Contexts

Sometimes you may want to create a simulation method that takes a user-defined function (UDF) and 
calls it to make a trading decision. Such a UDF would need access to the simulation's state—like the 
current position size and direction—as well as other relevant information, which could quickly involve 
dozens of variables. Remember, since full-scale OOP is not possible in Numba, we need to pass data 
using primitive containers such as tuples. However, using variable positional arguments or a regular tuple 
would be cumbersome for the user because each field can only be accessed by integer index or tuple 
unpacking. To make this easier, we usually pass such information as a named tuple, often called a 
(simulation) "context".

### Pipeline/6

Let's build a simple pipeline that iterates over rows and columns and, at each element, 
calls a UDF to get an order and execute it!

First, we need to answer the question, "What information does a UDF need?" 
In most cases, we just include everything available:

```pycon
>>> SimContext = namedtuple("SimContext", [
...     "open",  # (1)!
...     "high",
...     "low",
...     "close",
...     "init_cash",
...     "col",  # (2)!
...     "i",
...     "price_area",  # (3)!
...     "exec_state"
... ])
```

1. Arguments passed to the simulator.
2. Loop variables.
3. State information, either unpacked (for marginal speed) or as named tuples (for convenience).

Here is our pipeline that accepts and calls an order function:

```pycon
>>> @njit
... def pipeline_6_nb(
...     open, high, low, close, 
...     order_func_nb, order_args=(), 
...     init_cash=100
... ):
...     order_records = np.empty(close.shape, dtype=vbt.pf_enums.order_dt)
...     order_counts = np.full(close.shape[1], 0, dtype=int_)
...
...     for col in range(close.shape[1]):
...         exec_state = vbt.pf_enums.ExecState(
...             cash=float(init_cash),
...             position=0.0,
...             debt=0.0,
...             locked_cash=0.0,
...             free_cash=float(init_cash),
...             val_price=np.nan,
...             value=np.nan
...         )
...
...         for i in range(close.shape[0]):
...             val_price = open[i, col]
...             value = exec_state.cash + val_price * exec_state.position
...
...             price_area = vbt.pf_enums.PriceArea(
...                 open[i, col],
...                 high[i, col],
...                 low[i, col],
...                 close[i, col]
...             )
...             exec_state = vbt.pf_enums.ExecState(
...                 cash=exec_state.cash,
...                 position=exec_state.position,
...                 debt=exec_state.debt,
...                 locked_cash=exec_state.locked_cash,
...                 free_cash=exec_state.free_cash,
...                 val_price=val_price,
...                 value=value
...             )
...             sim_ctx = SimContext(  # (1)!
...                 open=open,
...                 high=high,
...                 low=low,
...                 close=close,
...                 init_cash=init_cash,
...                 col=col,
...                 i=i,
...                 price_area=price_area,
...                 exec_state=exec_state
...             )
...             order = order_func_nb(sim_ctx, *order_args)  # (2)!
...             _, exec_state = vbt.pf_nb.process_order_nb(
...                 col, col, i,
...                 exec_state=exec_state,
...                 order=order,
...                 price_area=price_area,
...                 order_records=order_records,
...                 order_counts=order_counts
...             )
...         
...     return vbt.nb.repartition_nb(order_records, order_counts)
```

1. Initialize the simulation context (creates a named tuple).
2. Call the UDF by first passing the context, then any user-defined arguments.

Now let's write our own order function that generates orders based on signals:

```pycon
>>> @njit  # (1)!
... def signal_order_func_nb(c, entries, exits):
...     if entries[c.i, c.col] and c.exec_state.position == 0:  # (2)!
...         return vbt.pf_nb.order_nb()
...     if exits[c.i, c.col] and c.exec_state.position > 0:
...         return vbt.pf_nb.close_position_nb()
...     return vbt.pf_nb.order_nothing_nb()

>>> broadcasted_args = vbt.broadcast(  # (3)!
...     dict(
...         open=data.get("Open").values,
...         high=data.get("High").values,
...         low=data.get("Low").values,
...         close=data.get("Close").values,
...         entries=entries.values,  # (4)!
...         exits=exits.values
...     ),
...     min_ndim=2
... )

>>> pipeline_6_nb(
...     broadcasted_args["open"],
...     broadcasted_args["high"], 
...     broadcasted_args["low"], 
...     broadcasted_args["close"], 
...     signal_order_func_nb,
...     order_args=(
...         broadcasted_args["entries"],
...         broadcasted_args["exits"]
...     )
... )
array([( 0, 0,  300, 0.34786966,   287.46398926, 0., 0),
       ( 1, 0,  362, 0.34786966,   230.64399719, 0., 1),
       ( 2, 0,  406, 0.26339233,   304.61801147, 0., 0),
       ( 3, 0, 1290, 0.26339233,  6890.52001953, 0., 1),
       ( 4, 0, 1680, 0.33210511,  5464.86669922, 0., 0),
       ( 5, 0, 1865, 0.33210511,  9244.97265625, 0., 1),
       ( 6, 0, 1981, 0.31871477,  9633.38671875, 0., 0),
       ( 7, 0, 2016, 0.31871477,  6681.06298828, 0., 1),
       ( 8, 0, 2073, 0.2344648 ,  9081.76171875, 0., 0),
       ( 9, 0, 2467, 0.2344648 , 35615.87109375, 0., 1),
       (10, 0, 2555, 0.17333543, 48176.34765625, 0., 0)],
      dtype={'names':['id','col','idx','size','price','fees','side'], ...})
```

1. Remember to decorate your order function with `@njit` as well!
2. All information can be accessed just like attributes on any Python object.
3. Prices and signals do not use flexible indexing, so we need to broadcast them to the full shape.
4. These two arrays were generated for the [first pipeline](#pipeline1).

We have just created our own shallow version of [Portfolio.from_order_func](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from_order_func)
functionality—neat! :boom:

Your homework is to extend this pipeline to use flexible indexing :wink:

## Performance

When it comes to performance, Numba code can be a real roller coaster :roller_coaster:

Numba is a just-in-time (JIT) compiler that analyzes and optimizes your code and ultimately uses the 
[LLVM compiler library](https://github.com/numba/llvmlite) to generate machine code for your Python 
functions. However, even if a function looks efficient on paper, Numba may sometimes generate 
suboptimal machine code because some variables or types do not interact optimally. In such cases, 
the code may still run much faster than native Python (or even another JIT compiler), but there 
can still be significant room for improvement—which may be hard to find, even for experienced users. 
For example, even switching the lines where variables are defined can unexpectedly have a 
positive or negative impact on performance.

Aside from following [official tips](https://numba.pydata.org/numba-doc/latest/user/performance-tips.html), 
there are also best practices you should always keep in mind when designing and optimizing 
Numba-compiled functions:

1. Numba works very well with loops and is often even more efficient with them than with vectorized operations.
That's why 90% of VBT's functionality relies on loops.
2. Numba performs poorly when new arrays are repeatedly created and small chunks of memory are allocated
inside loops. It is much better to create larger arrays before the iteration begins and use them as
buffers to store temporary information. Keep in mind that NumPy operations that produce a new array,
such as `np.cumsum`, create a new array each time.
3. Reading and writing one array element at a time is more efficient than processing elements in chunks.
4. Basic math operations such as `-`, `+`, `*`, and `/` should be preferred over their NumPy equivalents.
5. When passing a function as an argument to another function, arguments to that function should be accepted
in a packed format (`args`) instead of an unpacked format (`*args`). While this rule is occasionally broken
by VBT itself, these cases are typically benchmarked to ensure acceptable performance.
6. Packing named tuples inside other named tuples (as shown above) is not recommended,
but sometimes it does not have any negative effect.
7. NumPy arrays are almost always a better option than lists and dictionaries.
8. Even if enabling the `fastmath=True` option improves performance, be aware that it comes with various
[compromises](https://llvm.org/docs/LangRef.html#fast-math-flags) related to numeric operations.
9. Avoid iterating over elements of an array directly. Instead, iterate over a range of the same length
and use the loop variable to select the corresponding element.
10. When overwriting a variable, ensure it remains the same type.

!!! hint
    As a rule of thumb: the simpler the code, the easier it will be for Numba to analyze and optimize it.

### Benchmarking

To benchmark a simulator, you can use the [timeit](https://docs.python.org/3/library/timeit.html) module.
If possible, generate sample data of sufficient size and prepare for the worst-case scenario, where orders
are issued and executed at every time step to test the simulator under full load. Also, be sure to run
tests throughout the simulator's development to monitor how its execution time and stability change over time.

!!! note
    Generation of sample data and preparation of other inputs must be done before benchmarking.

Let's generate 1-minute random OHLC data for one year using 
[RandomOHLCData](https://vectorbt.pro/pvt_6d1b3986/api/data/custom/random_ohlc/#vectorbtpro.data.custom.random_ohlc.RandomOHLCData):

```pycon
>>> test_data = vbt.RandomOHLCData.pull(
...     start="2020-01-01", 
...     end="2021-01-01",
...     timeframe="1min",  # (1)!
...     std=0.0001,  # (2)!
...     symmetric=True  # (3)!
... )
>>> test_data.resample("1d").plot().show()  # (4)!
```

1. Set the tick frequency to 1 minute.
2. Set the tick volatility to 0.01%.
3. Use symmetric returns (50% negative return is equal to 100% positive return).
4. Plot to verify that the generated data is realistic. Here, we resample to daily
frequency for faster plotting.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/documentation/pf/simulation_random_ohlc_data.light.svg#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/documentation/pf/simulation_random_ohlc_data.dark.svg#only-dark){: .iimg loading=lazy }

Next, prepare all the data. This includes filling signals so that there is at least one 
order at each bar, which represents the worst-case scenario for performance and memory:

```pycon
>>> test_open = test_data.get("Open").values[:, None]  # (2)!
>>> test_high = test_data.get("High").values[:, None]
>>> test_low = test_data.get("Low").values[:, None]
>>> test_close = test_data.get("Close").values[:, None]
>>> test_entries = np.full(test_data.get_symbol_wrapper().shape, False)[:, None]
>>> test_exits = np.full(test_data.get_symbol_wrapper().shape, False)[:, None]
>>> test_entries[0::2] = True  # (3)!
>>> test_exits[1::2] = True  # (4)!
>>> del test_data  # (5)!

>>> test_entries.shape
(527041, 1)
```

1. Generate random OHLC data with symmetric returns.
2. Get a column, extract the NumPy array, and expand the array to two dimensions (skip this step if
your data is already two-dimensional).
3. Place an entry at every second bar starting from the first bar.
4. Place an exit at every second bar starting from the second bar.
5. Delete the data object to free up memory.

Each array contains 527,041 data points.

Now, let's check how our simulator performs with this data:

```pycon
>>> %%timeit  # (1)!
>>> pipeline_6_nb(
...     test_open, 
...     test_high, 
...     test_low, 
...     test_close, 
...     signal_order_func_nb,
...     order_args=(
...         test_entries, 
...         test_exits
...     )
... )
79.4 ms ± 290 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
```

1. This magic command works only in a Jupyter environment and only if placed at the beginning of the cell.
If you are running the code as a script, use the `timeit` module instead.

Generating half a million orders in 80 milliseconds on an Apple M1 is impressive! :fire:

To better demonstrate how even a small change can impact performance, let's create a new
order function that also creates a zero-sized empty array:

```pycon
>>> @njit
... def subopt_signal_order_func_nb(c, entries, exits):
...     _ = np.empty(0)  # (1)!
...
...     if entries[c.i, c.col] and c.exec_state.position == 0:
...         return vbt.pf_nb.order_nb()
...     if exits[c.i, c.col] and c.exec_state.position > 0:
...         return vbt.pf_nb.close_position_nb()
...     return vbt.pf_nb.order_nothing_nb()

>>> %%timeit
>>> pipeline_6_nb(
...     test_open, 
...     test_high, 
...     test_low, 
...     test_close, 
...     subopt_signal_order_func_nb,
...     order_args=(
...         test_entries, 
...         test_exits
...     )
... )
130 ms ± 675 µs per loop (mean ± std. dev. of 7 runs, 1 loop each)
```

1. Here

As you can see, creating an empty array at each bar increased execution time by more than 50%.
This demonstrates an important lesson: always create arrays outside of loops, and create them only once!

### Auto-parallelization

Because of path dependencies (where the current state depends on the previous state), we cannot parallelize 
the loop that iterates over rows (time). However, since VBT lets us
define multi-column backtesting logic, we can parallelize the loop that iterates over 
columns or groups of columns, as long as those columns or groups are independent
of each other, using only Numba. This is one of the main reasons VBT 
favors two-dimensional data layouts.

Automatic parallelization with Numba is straightforward: simply replace the `range` you wish to 
parallelize with `numba.prange`, and instruct Numba to parallelize the function by passing 
`parallel=True` to the `@njit` decorator. This will attempt to execute the code in the loop simultaneously 
using multiple parallel threads. You can read more about automatic parallelization with Numba 
[here](https://numba.pydata.org/numba-doc/latest/user/parallel.html) and about the
available threading layers [here](https://numba.pydata.org/numba-doc/latest/user/threading-layer.html).
On a MacBook Air (M1, 2020), enabling parallelization reduces processing time by 2–3 times on average.
Typically, simple arithmetic-heavy code without array creation can be parallelized more effectively
than more complex, vectorization-heavy code.

!!! important
    You can modify the same array from multiple threads, as done by many functions in VBT.
    Just make sure that multiple threads (columns, in this case) are not modifying the same elements
    or the same data in general!

Here is a simple example of a function that computes the expanding maximum on two-dimensional data,
with and without automatic parallelization:

```pycon
>>> arr = np.random.uniform(size=(1000000, 10))

>>> @njit
... def expanding_max_nb(arr):
...     out = np.empty_like(arr, dtype=float_)
...     for col in range(arr.shape[1]):
...         maxv = -np.inf
...         for i in range(arr.shape[0]):
...             if arr[i, col] > maxv:
...                 maxv = arr[i, col]
...             out[i, col] = maxv
...     return out

>>> %timeit expanding_max_nb(arr)
40.7 ms ± 558 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

>>> @njit(parallel=True)  # (1)!
... def parallel_expanding_max_nb(arr):
...     out = np.empty_like(arr, dtype=float_)
...     for col in prange(arr.shape[1]):  # (2)!
...         maxv = -np.inf
...         for i in range(arr.shape[0]):
...             if arr[i, col] > maxv:
...                 maxv = arr[i, col]
...             out[i, col] = maxv
...     return out

>>> %timeit parallel_expanding_max_nb(arr)
26.6 ms ± 437 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)
```

1. This is the first change.
2. This is the second change.

Now it is your turn: enable automatic parallelization of columns in the [sixth pipeline](#pipeline6) 
and benchmark it. Just remember to reduce the number of rows and increase the number of columns.

### Caching

Even if you have optimized the simulation pipeline for the best possible performance,
the actual compilation step can greatly reduce those time savings. However, the good news is that
Numba does not need to recompile the function on subsequent executions, provided you pass the same
argument **types** (not data!). This means you only have to wait once if you want to test the 
same function across many parameter combinations within the same Python runtime. Unfortunately,
if even one argument changes type or you restart the Python runtime, Numba will need to recompile. 

Fortunately, Numba offers a solution to avoid recompilation even after a runtime restart, known as
[caching](https://numba.pydata.org/numba-doc/latest/developer/caching.html).
To enable caching, simply pass `cache=True` to the `@njit` decorator.

!!! important
    Avoid enabling caching for functions that take complex, user-defined data, such as
    (named) tuples and other functions. This can sometimes lead to hidden bugs and kernel crashes if the
    data changes in a later runtime. Also, make sure your function does not use global variables.
    For example, the [fifth pipeline](#pipeline5) is perfectly cacheable, while the [sixth pipeline](#pipeline6)
    is not cacheable unless `order_func_nb` is cacheable as well.

Make sure to define any cached function inside a Python file rather than in a notebook cell, since
Numba needs a clear filepath to introspect the function. To invalidate the cache, navigate to the
directory where the function resides and remove the `__pycache__` directory. You can use
the command `rm -rf __pycache__` from your terminal to do this.

!!! hint
    A good practice is to invalidate the cache every time you change the code of a cached function,
    to avoid any potential side effects. Also, keep caching disabled while developing a function
    and only enable it once the function is fully implemented.

### AOT compilation

With [ahead-of-time compilation](https://numba.pydata.org/numba-doc/dev/user/pycc.html), you can compile
a function once and eliminate compilation overhead at runtime. Although this Numba feature
is not widely used in VBT because it would limit flexible input data, it can be helpful
when you know the argument types in advance. Let's pre-compile our [fifth pipeline](#pipeline5)!

To do this, you must specify the explicit signature of the function. You can read more about this in the
[types](https://numba.pydata.org/numba-doc/dev/reference/types.html#numba-types) reference.

```pycon
>>> from numba.pycc import CC
>>> cc = CC('pipeline_5')  # (1)!

>>> sig = "f8[:, :](" \ # (2)!
...       "UniTuple(i8, 2), " \ # (3)!
...       "i8[:], " \ # (4)!
...       "f8[:, :], " \ # (5)!
...       "f8[:, :], " \
...       "f8[:, :], " \
...       "f8[:], " \ # (6)!
...       "b1, " \ # (7)!
...       "b1" \
...       ")"

>>> cc.export('pipeline_5_nb', sig)(pipeline_5_nb)   # (8)!
>>> cc.compile() # (9)!
```

1. Initialize a new module.
2. The function should return a two-dimensional array of 64-bit floating-point type (allocations).
3. Tuple with two 64-bit integers (`target_shape`).
4. One-dimensional array of 64-bit integer type (`group_lens`).
5. Two-dimensional array of 64-bit floating-point type (`open`, `close`, and `target_pct`).
6. One-dimensional array of 64-bit floating-point type (`init_cash`).
7. Boolean value (`auto_call_seq` and `rotate_cols`).
8. Register the function with the provided signature. You can bind multiple signatures
to the same function.
9. Compile the module.

This generates an extension module named `pipeline_5`. On macOS, the actual filename will be
`pipeline_5.cpython-37m-darwin.so`. You can import this module like any regular Python module
and run the function `pipeline_5_nb` from that module:

```pycon
>>> import pipeline_5

>>> mult_alloc = pipeline_5.pipeline_5_nb(
...     target_shape,
...     group_lens,
...     vbt.to_2d_array(mult_data.get("Open")).astype("f8", copy=False),  # (1)!
...     vbt.to_2d_array(mult_data.get("Close")).astype("f8", copy=False),
...     vbt.to_2d_array(mult_target_pct).astype("f8", copy=False),
...     vbt.to_1d_array(100).astype("f8", copy=False),
...     auto_call_seq=True,  # (2)!
...     rotate_cols=True
... )
```

1. This ensures the array has the correct dimensionality and data type.
2. Keyword arguments must be passed as positional arguments. Default values must also be specified explicitly.

That was lightning fast! :zap:

!!! important
    Make sure that the provided arguments exactly match the registered signature,
    otherwise you may encounter errors that are very difficult to debug. For example,
    setting `init_cash` to `100` would result in an "index is out of bounds" error,
    while casting the array to integer would cause all allocations to be zero!

## Summary

We have explored in detail many components of a typical simulator in VBT. Simulation
is the main step in backtesting a trading strategy, and by mastering it you will
gain advanced skills that can be applied throughout VBT's rich
Numba ecosystem.

One of the key takeaways from this documentation is that implementing a custom
simulator is as easy (or as complex) as any other Numba-compiled function. There is little reason
to use the preset simulation methods such as [Portfolio.from_signals](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from_signals)
if you can achieve the same results, boost performance, utilize rotational
indexing, caching, and AOT compilation by designing your own pipeline from scratch. After all, it is
simply a set of loops that move over the shape of a matrix, execute orders, update the simulation state,
and store output data. Everything else is up to your imagination :mage:

[:material-language-python: Python code](https://vectorbt.pro/pvt_6d1b3986/assets/jupytext/documentation/portfolio/index.py.txt){ .md-button target="blank_" }