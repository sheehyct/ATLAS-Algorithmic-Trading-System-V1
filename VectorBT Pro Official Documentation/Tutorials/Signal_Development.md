\---
title: Generation
description: Learn about signal generation in VectorBT PRO
icon: material/broadcast
---

# :material-broadcast: Generation

Signals add an extra layer of abstraction on top of orders. Instead of specifying every detail about 
what needs to be ordered at each timestamp, you can define what a typical order should look like and 
then decide when to issue such an order. In VBT, this timing decision is made using signals, 
which are represented as boolean masks: \`True\` stands for "order" and \`False\` means "no order". The 
meaning of each signal can be changed either statically or dynamically, depending on the current 
simulation state. For example, you can instruct the simulator to ignore an "order" signal if you are 
already in the market, which is not possible with the "from-orders" method alone. Because VBT 
emphasizes data science, it is much easier to compare multiple strategies with the same trading 
conditions but different signal permutations (for example, order timings and directions). This 
approach reduces errors and leads to more fair experiments.

Since buying and selling are constant activities, it is ideal to include the order direction within 
each signal as well. However, because booleans only have two states, they cannot represent the three 
possibilities: "order to buy", "order to sell", and "no order". As a result, signals are typically 
distributed across two or more boolean arrays, each representing a different decision dimension. The 
most common way to define signals is by using two direction-unaware arrays: :one: entries and :two: 
exits. The meaning of these two arrays changes based on the direction, which is specified using a 
separate variable. For instance, when only the long direction is enabled, an entry signal opens a 
new long position and an exit signal closes it. When both directions are enabled, an entry signal 
opens a new long position, and an exit signal reverses it to open a short one. For more precise 
control over whether to reverse a position or simply close it, you can define four 
direction-aware arrays: :one: long entries, :two: long exits, :three: short entries, and :four: 
short exits. This method provides the greatest flexibility.

For example, to open a long position, close it, open a short position, and then reverse it, the 
signals would look like this:

| Long entry | Long exit | Short entry | Short exit |
|------------|-----------|-------------|------------|
| True       | False     | False       | False      |
| False      | True      | False       | False      |
| False      | False     | True        | False      |
| True       | False     | False       | False      |

The same strategy can also be defined using an entry signal, an exit signal, and a direction:

| Entry      | Exit       | Direction       |
|------------|------------|-----------------|
| True       | False      | Long only       |
| False      | True       | Long only       |
| True/False | False/True | Short only/Both |
| True       | False      | Long only/Both  |

!!! info
    Direction-unaware signals can be easily converted to direction-aware signals:

    \* True, True, Long only :material-arrow-right: True, True, False, False.
    \* True, True, Short only :material-arrow-right: False, False, True, True.
    \* True, True, Both :material-arrow-right: True, False, True, False.

    However, direction-aware signals cannot be converted to direction-unaware signals
    if both directions are enabled and there is an exit signal present:

    \* False, True, False, True :material-arrow-right: :question:

    Therefore, it is important to carefully evaluate which conditions you are interested in
    before generating signals.

You might wonder why not use an integer data type, where a positive number means "order to buy," a 
negative number means "order to sell," and zero means "no order," as is done in backtrader. Boolean 
arrays are much easier for users to generate and maintain. In addition, a boolean NumPy array uses 
eight times less memory than a 64-bit signed integer NumPy array. Boolean masks are also much more 
convenient to combine and analyze than integer arrays. For example, you can combine two masks with 
the logical OR (\`|\` in NumPy) operator, or sum the elements in a mask to get the number of signals. 
Since booleans are a subtype of integers, they behave just like regular integers in most math 
expressions.

## Comparison

Properly generating signals can sometimes be much more challenging than simulating them. This is 
because you need to consider not only the distribution of signals but also how they interact 
across multiple boolean arrays. For example, setting both an entry and exit at the same 
timestamp will effectively cancel both. That's why VBT offers many functions and techniques 
to support you in this process.

Signal generation usually begins by comparing two or more numeric arrays. Remember, when 
comparing entire arrays, you iterate over each row and column (that is, each element) 
in a vectorized way and compare their scalar values at each element. Essentially, you run the 
same comparison operation on every single element across all the arrays being compared. Let's 
look at an example using Bollinger Bands for two different assets. At each timestamp, 
we will place a signal whenever the low price is below the lower band, expecting the price to 
reverse back to its rolling mean:

\`\`\`pycon
>>> from vectorbtpro import \*

>>> data = vbt.BinanceData.pull(
...     \["BTCUSDT", "ETHUSDT"\], 
...     start="2021-01-01",
...     end="2022-01-01"
... )
>>> data.get("Low")
symbol                      BTCUSDT  ETHUSDT
Open time                                   
2021-01-01 00:00:00+00:00  28624.57   714.29
2021-01-02 00:00:00+00:00  28946.53   714.91
2021-01-03 00:00:00+00:00  31962.99   768.71
...                             ...      ...
2021-12-29 00:00:00+00:00  46096.99  3604.20
2021-12-30 00:00:00+00:00  45900.00  3585.00
2021-12-31 00:00:00+00:00  45678.00  3622.29

\[365 rows x 2 columns\]

>>> bb = vbt.talib("BBANDS").run(
...     data.get("Close"),
...     timeperiod=vbt.Default(14),  # (1)!
...     nbdevup=vbt.Default(2),
...     nbdevdn=vbt.Default(2)
... )
>>> bb.lowerband  # (2)!
symbol                          BTCUSDT      ETHUSDT
Open time                                           
2021-01-01 00:00:00+00:00           NaN          NaN
2021-01-02 00:00:00+00:00           NaN          NaN
2021-01-03 00:00:00+00:00           NaN          NaN
...                                 ...          ...
2021-12-29 00:00:00+00:00  44943.280004  3712.190071
2021-12-30 00:00:00+00:00  44861.191483  3662.827659
2021-12-31 00:00:00+00:00  44882.974796  3617.893036

\[365 rows x 2 columns\]

>>> mask = data.get("Low") < bb.lowerband  # (3)!
>>> mask
symbol                     BTCUSDT  ETHUSDT
Open time                                  
2021-01-01 00:00:00+00:00    False    False
2021-01-02 00:00:00+00:00    False    False
2021-01-03 00:00:00+00:00    False    False
...                            ...      ...
2021-12-29 00:00:00+00:00    False     True
2021-12-30 00:00:00+00:00    False     True
2021-12-31 00:00:00+00:00    False    False

\[365 rows x 2 columns\]

>>> mask.sum()  # (4)!
symbol
BTCUSDT    36
ETHUSDT    28
dtype: int64
\`\`\`

1. Wrap each parameter with \[Default\](https://vectorbt.pro/pvt\_6d1b3986/api/base/reshaping/#vectorbtpro.base.reshaping.Default)
to hide its column level. Alternatively, you can pass a list of parameters to hide with \`hide\_params\`.
2. Get the lower band as a Pandas object. You can list all output names of an indicator using \`bb.output\_names\`.
3. Compare two numeric arrays element-wise.
4. Get the number of signals in each column for a better overview.

This operation has created a mask that is true whenever the low price dips below the lower band. 
Such an array can already be used in a simulation! But let's see what happens when we try to compare 
the lower band generated for multiple combinations of the (upper and lower) multipliers:

\`\`\`pycon
>>> bb\_mult = vbt.talib("BBANDS").run(
...     data.get("Close"),
...     timeperiod=vbt.Default(14),
...     nbdevup=\[2, 3\],
...     nbdevdn=\[2, 3\]  # (1)!
... )
>>> mask = data.get("Low") < bb\_mult.lowerband
ValueError: Can only compare identically-labeled DataFrame objects
\`\`\`

1. Two parameter combinations: (14, 2, 2) and (14, 3, 3)

The issue here is that Pandas cannot compare DataFrames with different columns. The left
DataFrame contains the columns \`BTCUSDT\` and \`ETHUSDT\`, while the right DataFrame from the 
Bollinger Bands indicator now has the columns \`(2, 2, BTCUSDT)\`, \`(2, 2, ETHUSDT)\`, 
\`(3, 3, BTCUSDT)\`, and \`(3, 3, ETHUSDT)\`. So, what is the solution? Right, VBT! By appending 
\`vbt\` to the \_left\_ operand, you are comparing the accessor object of type 
\[BaseAccessor\](https://vectorbt.pro/pvt\_6d1b3986/api/base/accessors/#vectorbtpro.base.accessors.BaseAccessor) instead of the 
DataFrame itself. This triggers the so-called \[magic method\](https://rszalski.github.io/magicmethods/)
\`\_\_lt\_\_\` of that accessor. This method takes the DataFrame under the accessor and the DataFrame on 
the right and combines them using \[BaseAccessor.combine\](https://vectorbt.pro/pvt\_6d1b3986/api/base/accessors/#vectorbtpro.base.accessors.BaseAccessor.combine)
and \[numpy.less\](https://numpy.org/doc/stable/reference/generated/numpy.less.html) as the \`combine\_func\`.
As a result, the shapes and indexes of both DataFrames are broadcasted using VBT's powerful 
broadcasting mechanism, which overcomes the Pandas limitation.

As a result, VBT compares \`(2, 2, BTCUSDT)\` and \`(3, 3, BTCUSDT)\` only with \`BTCUSDT\`,
and \`(2, 2, ETHUSDT)\` and \`(3, 3, ETHUSDT)\` only with \`ETHUSDT\`, leveraging NumPy for performance!

\`\`\`pycon
>>> mask = data.get("Low").vbt < bb\_mult.lowerband  # (1)!
>>> mask
bbands\_nbdevup                          2               3
bbands\_nbdevdn                          2               3
symbol                    BTCUSDT ETHUSDT BTCUSDT ETHUSDT
Open time                                                
2021-01-01 00:00:00+00:00   False   False   False   False
2021-01-02 00:00:00+00:00   False   False   False   False
2021-01-03 00:00:00+00:00   False   False   False   False
...                           ...     ...     ...     ...
2021-12-29 00:00:00+00:00   False    True   False   False
2021-12-30 00:00:00+00:00   False    True   False   False
2021-12-31 00:00:00+00:00   False   False   False   False

\[365 rows x 4 columns\]

>>> mask.sum()
bbands\_nbdevup  bbands\_nbdevdn  symbol 
2               2               BTCUSDT    53
                                ETHUSDT    48
3               3               BTCUSDT    10
                                ETHUSDT     9
dtype: int64
\`\`\`

1. \`vbt\` must always be called on the left operand.

!!! note
    For VBT to compare shapes that are not broadcastable, both DataFrames must 
    share at least one column level in common, such as \`symbol\` in the example above.

As you may remember from the indicator documentation, each indicator provides 
several helper methods for comparison: \`{name}\_above\`, \`{name}\_equal\`, and 
\`{name}\_below\`, which essentially do the same as what we did above:

\`\`\`pycon
>>> mask = bb\_mult.lowerband\_above(data.get("Low"))  # (1)!
>>> mask.sum()
bbands\_nbdevup  bbands\_nbdevdn  symbol 
2               2               BTCUSDT    53
                                ETHUSDT    48
3               3               BTCUSDT    10
                                ETHUSDT     9
dtype: int64
\`\`\`

1. Our indicator does not have an input or output for the low price, so we need
to reverse the comparison order and check whether the lower band is above the low price.

### Thresholds

To compare a numeric array against two or more scalar thresholds as parameter combinations, we can use
the same approach by either appending \`vbt\` or by calling the method
\[BaseAccessor.combine\](https://vectorbt.pro/pvt\_6d1b3986/api/base/accessors/#vectorbtpro.base.accessors.BaseAccessor.combine). Let's
calculate the bandwidth of our single-combination indicator, which is the upper band minus the lower band
divided by the middle band, and check whether it is higher than two different thresholds:

\`\`\`pycon
>>> bandwidth = (bb.upperband - bb.lowerband) / bb.middleband

>>> mask = bandwidth.vbt > vbt.Param(\[0.15, 0.3\], name="threshold")  # (1)!
>>> mask.sum()
threshold  symbol 
0.15       BTCUSDT    253
           ETHUSDT    316
0.30       BTCUSDT     65
           ETHUSDT    136
dtype: int64

>>> mask = bandwidth.vbt.combine(
...     \[0.15, 0.3\],  # (2)!
...     combine\_func=np.greater, 
...     keys=pd.Index(\[0.15, 0.3\], name="threshold")  # (3)!
... )
>>> mask.sum()
threshold  symbol 
0.15       BTCUSDT    253
           ETHUSDT    316
0.30       BTCUSDT     65
           ETHUSDT    136
dtype: int64
\`\`\`

1. Passes both objects to \[BaseAccessor.combine\](https://vectorbt.pro/pvt\_6d1b3986/api/base/accessors/#vectorbtpro.base.accessors.BaseAccessor.combine),
broadcasts them using \[broadcast\](https://vectorbt.pro/pvt\_6d1b3986/api/base/reshaping/#vectorbtpro.base.reshaping.broadcast),
and combines them using \[numpy.greater\](https://numpy.org/doc/stable/reference/generated/numpy.greater.html).
With broadcasting, each value in \`vbt.Param\` is combined with each column in the array. This works only
for scalars.
2. When passing a list, the DataFrame is compared to each item in the list.
3. The \`keys\` argument appends a column level describing the items in the list.

The latest example also works with arrays instead of scalars. Alternatively, we can use
\[pandas.concat\](https://pandas.pydata.org/docs/reference/api/pandas.concat.html) to manually stack the
results of any comparison and treat them as separate combinations:

\`\`\`pycon
>>> mask = pd.concat(
...     (bandwidth > 0.15, bandwidth > 0.3), 
...     keys=pd.Index(\[0.15, 0.3\], name="threshold"), 
...     axis=1
... )
>>> mask.sum()
threshold  symbol 
0.15       BTCUSDT    253
           ETHUSDT    316
0.30       BTCUSDT     65
           ETHUSDT    136
dtype: int64
\`\`\`

### Crossovers

So far, we have explored basic vectorized comparison operations, but one operation appears
disproportionately often in technical analysis: crossovers. A crossover refers to a situation where two
time series cross each other. There are two ways to identify crossovers: naive and native. The naive
approach compares both time series in a vectorized way and then selects the first \`True\` value from each
"partition" of \`True\` values. In VBT's terminology, a partition for signal processing is a consecutive
sequence of \`True\` values produced by the comparison. While we already know how to perform the
comparison, the second step can be accomplished with the accessor for signals:
\[SignalsAccessor\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor), which can be
accessed via the attribute \`vbt.signals\` on any Pandas object.

Specifically, we will use the method \[SignalsAccessor.first\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.first),
which takes a mask, assigns a rank to each \`True\` value within each partition using
\[SignalsAccessor.pos\_rank\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.pos\_rank)
(numbered from 0 to the length of the respective partition), and then keeps only those \`True\` values
that have rank 0. Let's get the crossovers where the low price dips below the lower band:

\`\`\`pycon
>>> low\_below\_lband = data.get("Low") < bb.lowerband
>>> mask = low\_below\_lband.vbt.signals.first()
>>> mask.sum()
symbol
BTCUSDT    21
ETHUSDT    20
dtype: int64
\`\`\`

To confirm the operation was successful, let's plot the \`BTCUSDT\` column of both time series
using \[GenericAccessor.plot\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.plot)
and the generated signals with \[SignalsSRAccessor.plot\_as\_markers\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsSRAccessor.plot\_as\_markers):

\`\`\`pycon
>>> btc\_low = data.get("Low", "BTCUSDT").rename("Low")  # (1)!
>>> btc\_lowerband = bb.lowerband\["BTCUSDT"\].rename("Lower Band")
>>> btc\_mask = mask\["BTCUSDT"\].rename("Signals")

>>> fig = btc\_low.vbt.plot()  # (2)!
>>> btc\_lowerband.vbt.plot(fig=fig)
>>> btc\_mask.vbt.signals.plot\_as\_markers(
...     y=btc\_low, 
...     trace\_kwargs=dict(
...         marker=dict(
...             color="#DFFF00"
...         )
...     ),
...     fig=fig
... )  # (3)!
>>> fig.show()
\`\`\`

1. Rename the column for the legend.
2. The first plotting method returns a figure, which must be passed to each subsequent plotting method.
3. We are using \`btc\_low\` as the Y-values at which to place the markers.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/crossovers.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/crossovers.dark.svg#only-dark){: .iimg loading=lazy }

!!! hint
    To wait for a confirmation, use \[SignalsAccessor.nth\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.nth)
    to select the n-th signal in each partition.

However, there is a catch: if the first low value is already below the first lower band value, it will also
produce a crossover signal. To address this, we need to pass \`after\_false=True\`, which will discard the first
partition if there is no \`False\` value beforehand.

\`\`\`pycon
>>> mask = low\_below\_lband.vbt.signals.first(after\_false=True)
>>> mask.sum()
symbol
BTCUSDT    21
ETHUSDT    20
dtype: int64
\`\`\`

Here's another catch: if the first values in the indicator are NaN, which results in \`False\`
values in the mask, and the first value after the last NaN yields \`True\`, the \`after\_false\` argument
becomes ineffective. To resolve this, we need to manually set those positions in the mask to \`True\`.
Let's illustrate this with sample data:

\`\`\`pycon
>>> sample\_low = pd.Series(\[10, 9, 8, 9, 8\])
>>> sample\_lband = pd.Series(\[np.nan, np.nan, 9, 8, 9\])
>>> sample\_mask = sample\_low < sample\_lband
>>> sample\_mask.vbt.signals.first(after\_false=True)  # (1)!
0    False
1    False
2     True
3    False
4     True
dtype: bool

>>> sample\_mask\[sample\_lband.ffill().isnull()\] = True  # (2)!
>>> sample\_mask.vbt.signals.first(after\_false=True)
0    False
1    False
2    False
3    False
4     True
dtype: bool
\`\`\`

1. The first crossover should not occur because we do not know what happens at those NaN values,
while the second crossover is valid.
2. Forward fill the indicator values to identify only the initial NaN values, and set the
mask to \`True\` at those positions to make \`after\_false\` effective again.

Alternatively, we can remove the buffer, perform the operation, and then add the buffer back:

\`\`\`pycon
>>> buffer = sample\_lband.ffill().isnull().sum(axis=0).max()  # (1)!
>>> buffer
2

>>> sample\_buf\_mask = sample\_low.iloc\[buffer:\] < sample\_lband.iloc\[buffer:\]
>>> sample\_buf\_mask = sample\_buf\_mask.vbt.signals.first(after\_false=True)
>>> sample\_mask = sample\_low.vbt.wrapper.fill(False)
>>> sample\_mask.loc\[sample\_buf\_mask.index\] = sample\_buf\_mask
>>> sample\_mask
0    False
1    False
2    False
3    False
4     True
dtype: bool
\`\`\`

1. Find the maximum length of each first consecutive series of NaN values across all columns.

!!! info
    We can apply the buffer-exclusive approach described above to almost any operation in VBT.

But here comes another issue: what if our data contains gaps and we encounter a NaN in the middle
of a partition? In this case, we should set the second part of the partition to \`False\`, because
forward-filling that NaN value would make waiting for a confirmation difficult. However, performing
many operations on larger arrays just to find crossovers can be quite resource-intensive. Fortunately,
VBT uses its own Numba-compiled function \[crossed\_above\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/base/#vectorbtpro.generic.nb.base.crossed\_above\_nb)
to find crossovers iteratively, which is the second, native method. To use this function,
we can use the methods \[GenericAccessor.crossed\_above\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.crossed\_above)
and \[GenericAccessor.crossed\_below\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.crossed\_below),
accessible via the \`vbt\` attribute on any Pandas object:

\`\`\`pycon
>>> mask = data.get("Low").vbt.crossed\_below(bb.lowerband, wait=1)  # (1)!
>>> mask.sum()
symbol
BTCUSDT    15
ETHUSDT    11
dtype: int64
\`\`\`

1. Waits one bar for confirmation.

!!! info
    If the time series crosses back during the confirmation period \`wait\`, the signal will not be set.
    To set the signal anyway, use forward shifting.

As with other comparison methods, each indicator comes with helper methods \`{name}\_crossed\_above\` and
\`{name}\_crossed\_below\` for generating the crossover masks:

\`\`\`pycon
>>> mask = bb.lowerband\_crossed\_above(data.get("Low"), wait=1)
>>> mask.sum()
symbol
BTCUSDT    15
ETHUSDT    11
dtype: int64
\`\`\`

## Logical operators

Once we have generated two or more masks (conditions), we can combine them into a single mask using
logical operators. Common logical operators include:

\* \_AND\_ (\`&\` or \[numpy.logical\_and\](https://numpy.org/doc/stable/reference/generated/numpy.logical\_and.html)):
for each element, returns True whenever all the conditions are True.
\* \_OR\_ (\`|\` or \[numpy.logical\_or\](https://numpy.org/doc/stable/reference/generated/numpy.logical\_or.html)):
for each element, returns True whenever any of the conditions are True.
\* \_NOT\_ (\`~\` or \[numpy.logical\_not\](https://numpy.org/doc/stable/reference/generated/numpy.logical\_not.html)):
for each element, returns True whenever the condition is False.
\* \_XOR\_ (\`^\` or \[numpy.logical\_xor\](https://numpy.org/doc/stable/reference/generated/numpy.logical\_xor.html)):
for each element, returns True whenever only one of the conditions is True.

!!! note
    Do not use \`and\`, \`or\`, or \`not\` on arrays. These only work on single boolean values.
    For example, instead of \`mask1 and mask2\`, use \`mask1 & mask2\`. Instead of \`mask1 or mask2\`,
    use \`mask1 | mask2\`. Instead of \`not mask\`, use \`~mask\`.

For example, let's combine four conditions for a signal: the low price dips below the lower band \_AND\_
the bandwidth is above some threshold (a downward breakout while expanding), \_OR\_ the high price rises
above the upper band \_AND\_ the bandwidth is below some threshold (an upward breakout while squeezing):

\`\`\`pycon
>>> cond1 = data.get("Low") < bb.lowerband
>>> cond2 = bandwidth > 0.3
>>> cond3 = data.get("High") > bb.upperband
>>> cond4 = bandwidth < 0.15

>>> mask = (cond1 & cond2) | (cond3 & cond4)
>>> mask.sum()
symbol
BTCUSDT    25
ETHUSDT    13
dtype: int64
\`\`\`

To test multiple thresholds and broadcast exclusively using VBT:

\`\`\`pycon
>>> cond1 = data.get("Low").vbt < bb.lowerband
>>> cond2 = bandwidth.vbt > vbt.Param(\[0.3, 0.3, 0.4, 0.4\], name="cond2\_th")  # (1)!
>>> cond3 = data.get("High").vbt > bb.upperband
>>> cond4 = bandwidth.vbt < vbt.Param(\[0.1, 0.2, 0.1, 0.2\], name="cond4\_th")  # (2)!

>>> mask = (cond1.vbt & cond2).vbt | (cond3.vbt & cond4)  # (3)!
>>> mask.sum()
cond2\_th  cond4\_th  symbol 
0.3       0.1       BTCUSDT    11
                    ETHUSDT    10
          0.2       BTCUSDT    28
                    ETHUSDT    27
0.4       0.1       BTCUSDT     9
                    ETHUSDT     5
          0.2       BTCUSDT    26
                    ETHUSDT    22
dtype: int64
\`\`\`

1. Tests two thresholds in the second condition, repeating them so that each is compared with both thresholds
in the fourth condition.
2. Tests two thresholds in the fourth condition, tiling them so that each is compared with both thresholds
in the second condition.
3. Notice that \`vbt\` is appended to each operand on the left.
Adding it to any operand on the right is redundant.

### Cartesian product

Combining two or more arrays using a Cartesian product is a bit more complex because each array
has the column level \`symbol\`, which should not be combined with itself. Here is the trick:
First, convert the columns of each array to their integer positions. Then, split each position array
into "blocks" (smaller arrays). Blocks will be combined with each other, but the positions within each
block will not; that is, each block serves as a parameter combination. Then, combine all blocks using
a combinatorial function of your choice (see \[itertools\](https://docs.python.org/3/library/itertools.html)
for various options, or \[generate\_param\_combs\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.generate\_param\_combs)),
and finally, flatten each array with blocks and use it for column selection. While this may sound complex,
it is not difficult to implement!

\`\`\`pycon
>>> cond1 = data.get("Low").vbt < bb.lowerband
>>> cond2 = bandwidth.vbt > vbt.Param(\[0.3, 0.4\], name="cond2\_th")  # (1)!
>>> cond3 = data.get("High").vbt > bb.upperband
>>> cond4 = bandwidth.vbt < vbt.Param(\[0.1, 0.2\], name="cond4\_th")

>>> i1 = np.split(np.arange(len(cond1.columns)), len(cond1.columns) // 2)  # (2)!
>>> i2 = np.split(np.arange(len(cond2.columns)), len(cond2.columns) // 2)
>>> i3 = np.split(np.arange(len(cond3.columns)), len(cond3.columns) // 2)
>>> i4 = np.split(np.arange(len(cond4.columns)), len(cond4.columns) // 2)

>>> i1
\[array(\[0, 1\])\]
>>> i2
\[array(\[0, 1\]), array(\[2, 3\])\]
>>> i3
\[array(\[0, 1\])\]
>>> i4
\[array(\[0, 1\]), array(\[2, 3\])\]

>>> i1, i2, i3, i4 = zip(\*product(i1, i2, i3, i4))  # (3)!

>>> i1
(array(\[0, 1\]), array(\[0, 1\]), array(\[0, 1\]), array(\[0, 1\]))
>>> i2
(array(\[0, 1\]), array(\[0, 1\]), array(\[2, 3\]), array(\[2, 3\]))
>>> i3
(array(\[0, 1\]), array(\[0, 1\]), array(\[0, 1\]), array(\[0, 1\]))
>>> i4
(array(\[0, 1\]), array(\[2, 3\]), array(\[0, 1\]), array(\[2, 3\]))

>>> i1 = np.asarray(i1).flatten()  # (4)!
>>> i2 = np.asarray(i2).flatten()
>>> i3 = np.asarray(i3).flatten()
>>> i4 = np.asarray(i4).flatten()

>>> i1
\[0 1 0 1 0 1 0 1\]
>>> i2
\[0 1 0 1 2 3 2 3\]
>>> i3
\[0 1 0 1 0 1 0 1\]
>>> i4
\[0 1 2 3 0 1 2 3\]

>>> cond1 = cond1.iloc\[:, i1\]  # (5)!
>>> cond2 = cond2.iloc\[:, i2\]
>>> cond3 = cond3.iloc\[:, i3\]
>>> cond4 = cond4.iloc\[:, i4\]

>>> mask = (cond1.vbt & cond2).vbt | (cond3.vbt & cond4)  # (6)!
>>> mask.sum()
cond2\_th  cond4\_th  symbol 
0.3       0.1       BTCUSDT    11
                    ETHUSDT    10
          0.2       BTCUSDT    28
                    ETHUSDT    27
0.4       0.1       BTCUSDT     9
                    ETHUSDT     5
          0.2       BTCUSDT    26
                    ETHUSDT    22
dtype: int64
\`\`\`

1. Each DataFrame should contain only unique parameter combinations (and columns in general).
2. Split each position array into blocks with symbols.
3. Combine all blocks (parameter combinations) using the Cartesian product.
4. Flatten each array with blocks to get an array that can be used for indexing.
5. Use the final positions to select the columns from each DataFrame so that each DataFrame has the
same number of columns.
6. All columns now have the same length but still different labels :material-arrow-right:
let VBT's broadcaster handle the alignment.

In newer versions of VBT, the same effect can be achieved with a single call to
\[BaseAccessor.cross\](https://vectorbt.pro/pvt\_6d1b3986/api/base/accessors/#vectorbtpro.base.accessors.BaseAccessor.cross):

\`\`\`pycon
>>> cond1 = data.get("Low").vbt < bb.lowerband
>>> cond2 = bandwidth.vbt > vbt.Param(\[0.3, 0.4\], name="cond2\_th")
>>> cond3 = data.get("High").vbt > bb.upperband
>>> cond4 = bandwidth.vbt < vbt.Param(\[0.1, 0.2\], name="cond4\_th")

>>> cond1, cond2, cond3, cond4 = vbt.pd\_acc.x(cond1, cond2, cond3, cond4)  # (1)!
>>> mask = (cond1.vbt & cond2).vbt | (cond3.vbt & cond4)
\`\`\`

1. \`x\` is an alias for \`cross\`. Another option: \`cond1.vbt.x(cond2, cond3, cond4)\`.

A simpler and less error-prone approach is to build an indicator that handles parameter
combinations for us :grin:

For this, we will write an indicator expression similar to the code we wrote for a single
parameter combination, and use \[IndicatorFactory.from\_expr\](https://vectorbt.pro/pvt\_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.from\_expr)
to auto-build an indicator by parsing that expression. The logic, including the specification of
all inputs, parameters, and outputs, is contained within the expression itself. We will use the annotation
\`@res\_talib\_bbands\` to resolve the inputs and parameters expected by TA-Lib's \`BBANDS\`
indicator, and "copy" them to our indicator by also adding the prefix \`talib\` to the parameter names.
Then, we perform the usual signal generation logic, substituting the custom parameters \`cond2\_th\`
and \`cond4\_th\` with their individual values, and return the entire result as an output \`mask\`
with the proper annotation.

\`\`\`pycon
>>> MaskGenerator = vbt.IF.from\_expr("""
... upperband, middleband, lowerband = @res\_talib\_bbands
... bandwidth = (upperband - lowerband) / middleband
... cond1 = low < lowerband
... cond2 = bandwidth > @p\_cond2\_th
... cond3 = high > upperband
... cond4 = bandwidth < @p\_cond4\_th
... @out\_mask:(cond1 & cond2) | (cond3 & cond4)
... """)

>>> vbt.phelp(MaskGenerator.run, incl\_doc=False)  # (1)!
Indicator.run(
    high,
    low,
    close,
    cond2\_th,
    cond4\_th,
    bbands\_timeperiod=Default(value=5),
    bbands\_nbdevup=Default(value=2),
    bbands\_nbdevdn=Default(value=2),
    bbands\_matype=Default(value=0),
    bbands\_timeframe=Default(value=None),
    short\_name='custom',
    hide\_params=None,
    hide\_default=True,
    \*\*kwargs
)

>>> mask\_generator = MaskGenerator.run(
...     high=data.get("High"),
...     low=data.get("Low"),
...     close=data.get("Close"),
...     cond2\_th=\[0.3, 0.4\],
...     cond4\_th=\[0.1, 0.2\],
...     bbands\_timeperiod=vbt.Default(14),
...     param\_product=True
... )  # (2)!
>>> mask\_generator.mask.sum()
custom\_cond2\_th  custom\_cond4\_th  symbol 
0.3              0.1              BTCUSDT    11
                                  ETHUSDT    10
                 0.2              BTCUSDT    28
                                  ETHUSDT    27
0.4              0.1              BTCUSDT     9
                                  ETHUSDT     5
                 0.2              BTCUSDT    26
                                  ETHUSDT    22
dtype: int64
\`\`\`

1. See the arguments that the run method expects.
2. Run the indicator on the Cartesian product of all parameters.

!!! info
    Even though the indicator factory includes "indicator" in its name, we can use it to generate
    signals just as easily. This is because signals are simply boolean arrays that always match the
    shape of the input.

## Shifting

To compare the current value to any previous (not future!) value, we can use forward shifting.
You can also use this to shift the final mask to delay order execution. For example, let's generate
a signal whenever the low price dips below the lower band AND the bandwidth change (that is, the
difference between the current and previous bandwidth) is positive:

\`\`\`pycon
>>> cond1 = data.get("Low") < bb.lowerband
>>> cond2 = bandwidth > bandwidth.shift(1)  # (1)!

>>> mask = cond1 & cond2
>>> mask.sum()
symbol
BTCUSDT    42
ETHUSDT    39
dtype: int64
\`\`\`

1. The shifted array contains the previous values.

!!! important
    Never attempt to shift backwards, as this can lead to look-ahead bias! Use either a positive number in
    \[DataFrame.shift\](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.shift.html),
    or VBT's accessor method \[GenericAccessor.fshift\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.fshift).

Another way to shift observations is by selecting the first observation within a rolling window.
This is especially useful when the rolling window has a variable size based on a frequency.
Let's do the same logic as above, but determine the bandwidth change relative to one week ago,
instead of yesterday:

\`\`\`pycon
>>> cond2 = bandwidth > bandwidth.rolling("7d").apply(lambda x: x\[0\])

>>> mask = cond1 & cond2
>>> mask.sum()
symbol
BTCUSDT    33
ETHUSDT    28
dtype: int64
\`\`\`

!!! hint
    Prefer variable windows over fixed ones if your data contains gaps.

The approach above is a step in the right direction, but it introduces two possible issues:
all windows will be either 6 days long or less, and the rolling application of a custom Python function
in Pandas is not very efficient. The first issue can be solved by rolling a window of 8 days and
checking that the first observation is exactly 7 days before the current timestamp:

\`\`\`pycon
>>> def exactly\_ago(sr):  # (1)!
...     if sr.index\[0\] == sr.index\[-1\] - vbt.timedelta("7d"):
...         return sr.iloc\[0\]
...     return np.nan

>>> cond\_7d\_ago = bandwidth.rolling("8d").apply(exactly\_ago, raw=False)
>>> cond2 = bandwidth > cond\_7d\_ago

>>> mask = cond1 & cond2
>>> mask.sum()
symbol
BTCUSDT    29
ETHUSDT    26
dtype: int64
\`\`\`

1. By passing \`raw=False\`, the input will be a Pandas Series.

The second issue can be solved by looping with Numba. The main challenge, however, is solving
both issues at once, since we want to access the timestamp of the first observation.
This requires working on a Pandas Series rather than a NumPy array, but Numba cannot operate on Pandas
Series :expressionless:

Therefore, we can use VBT's accessor method \[GenericAccessor.rolling\_apply\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.rolling\_apply),
which provides two modes: regular and meta. The regular mode rolls over the data of a Pandas object
like Pandas does but does not provide information about the current window :no\_good:
The meta mode rolls over the \_\_metadata\_\_ of a Pandas object, so we can easily select data
from any array corresponding to the current window :ok\_hand:

\`\`\`pycon
>>> @njit
... def exactly\_ago\_meta\_nb(from\_i, to\_i, col, index, freq, arr):  # (1)!
...     if index\[from\_i\] == index\[to\_i - 1\] - freq:  # (2)!
...         return arr\[from\_i, col\]  # (3)!
...     return np.nan

>>> cond\_7d\_ago = vbt.pd\_acc.rolling\_apply(
...     "8d",
...     exactly\_ago\_meta\_nb,
...     bandwidth.index.values,  # (4)!
...     vbt.timedelta("7d").to\_timedelta64(),
...     vbt.to\_2d\_array(bandwidth),
...     wrapper=bandwidth.vbt.wrapper  # (5)!
... )
>>> cond2 = bandwidth > cond\_7d\_ago

>>> mask = cond1 & cond2
>>> mask.sum()
symbol
BTCUSDT    29
ETHUSDT    26
dtype: int64
\`\`\`

1. The meta function must take three arguments: the current window start index, window end index, and column.
2. The window end index is exclusive, so use \`to\_i - 1\` to get the last index in the window.
3. Use the current column index to select the column. Make sure all arrays are two-dimensional.
4. Here are our three user-defined arguments.
5. The wrapper contains the metadata needed for iterating and building the final Pandas object.

If this approach feels intimidating, there is an even simpler method:
\[GenericAccessor.ago\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.ago), which
can forward-shift the array by any delta:

\`\`\`pycon
>>> cond2 = bandwidth > bandwidth.vbt.ago("7d")

>>> mask = cond1 & cond2
>>> mask.sum()
symbol
BTCUSDT    29
ETHUSDT    26
dtype: int64

>>> bandwidth.iloc\[-8\]
symbol
BTCUSDT    0.125477
ETHUSDT    0.096458
Name: 2021-12-24 00:00:00+00:00, dtype: float64

>>> bandwidth.vbt.ago("7d").iloc\[-1\]
symbol
BTCUSDT    0.125477
ETHUSDT    0.096458
Name: 2021-12-31 00:00:00+00:00, dtype: float64
\`\`\`

!!! hint
    This method returns exact matches. If there is no exact match, the value will be NaN.
    To return the previous index value instead, pass \`method="ffill"\`. The method also accepts a sequence
    of deltas that can be applied per element.

## Truth value testing

What if we want to test whether a certain condition was met within a period of time in the past?
To do this, we need to create an expanding or rolling window and use truth value testing with
\[numpy.any\](https://numpy.org/doc/stable/reference/generated/numpy.any.html) or
\[numpy.all\](https://numpy.org/doc/stable/reference/generated/numpy.all.html) within this window.
Because Pandas does not implement rolling aggregation using \`any\` and \`all\`, we need to be
more creative and treat booleans as integers: use \`max\` for logical OR and \`min\` for logical AND.
Also, remember to cast the resulting array to a boolean data type to generate a valid mask.

Let's generate a signal whenever the low price goes below the lower band AND there was a downward
crossover of the close price with the middle band in the past 5 candles:

\`\`\`pycon
>>> cond2 = data.get("Close").vbt.crossed\_below(bb.middleband)
>>> cond2 = cond2.rolling(5, min\_periods=1).max().astype(bool)

>>> mask = cond1 & cond2
>>> mask.sum()
symbol
BTCUSDT    36
ETHUSDT    28
dtype: int64
\`\`\`

!!! note
    Be cautious when setting \`min\_periods\` to a higher number and converting to a boolean data type:
    each NaN will become \`True\`. Always replace NaNs with zeros before casting.

If the window size is fixed, you can also use \[GenericAccessor.rolling\_any\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.rolling\_any)
and \[GenericAccessor.rolling\_all\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.rolling\_all),
which are tailored for rolling truth value testing:

\`\`\`pycon
>>> cond2 = data.get("Close").vbt.crossed\_below(bb.middleband)
>>> cond2 = cond2.vbt.rolling\_any(5)

>>> mask = cond1 & cond2
>>> mask.sum()
symbol
BTCUSDT    36
ETHUSDT    28
dtype: int64
\`\`\`

Another way to perform the same rolling operations is by using the accessor method
\[GenericAccessor.rolling\_apply\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.rolling\_apply)
and setting \`reduce\_func\_nb\` to "any" or "all". Use the argument \`wrap\_kwargs\`
to instruct VBT to fill NaNs with \`False\` and change the data type. This method also allows
passing flexible windows. For example, let's roll a window of 5 days:

\`\`\`pycon
>>> cond2 = data.get("Close").vbt.crossed\_below(bb.middleband)
>>> cond2 = cond2.vbt.rolling\_apply(
...     "5d", "any",  # (1)!
...     minp=1, 
...     wrap\_kwargs=dict(fillna=0, dtype=bool)
... )

>>> mask = cond1 & cond2
>>> mask.sum()
symbol
BTCUSDT    36
ETHUSDT    28
dtype: int64
\`\`\`

1. "any" is translated to \[any\_reduce\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/apply\_reduce/#vectorbtpro.generic.nb.apply\_reduce.any\_reduce\_nb).

Let's try something more complex: check whether the bandwidth contracted to 10% or less at any time
within a month using an expanding window, then reset the window at the start of the next month.
This approach uses the first timestamp of each month as a time anchor for our condition. We will
use VBT's resampling logic, which lets us aggregate values by mapping any source index
(anchor points) to any target index (our index).

\`\`\`pycon
>>> anchor\_points = data.wrapper.get\_index\_points(  # (1)!
...     every="M", 
...     start=0,  # (2)!
...     exact\_start=True
... )
>>> anchor\_points
array(\[  0,  31,  59,  90, 120, 151, 181, 212, 243, 273, 304, 334\])

>>> left\_bound = np.full(len(data.wrapper.index), np.nan)  # (3)!
>>> left\_bound\[anchor\_points\] = anchor\_points
>>> left\_bound = vbt.nb.ffill\_1d\_nb(left\_bound).astype(int\_)
>>> left\_bound = bandwidth.index\[left\_bound\]
>>> left\_bound
DatetimeIndex(\['2021-01-01 00:00:00+00:00', '2021-01-01 00:00:00+00:00',
               '2021-01-01 00:00:00+00:00', '2021-01-01 00:00:00+00:00',
               '2021-01-01 00:00:00+00:00', '2021-01-01 00:00:00+00:00',
               ...
               '2021-12-01 00:00:00+00:00', '2021-12-01 00:00:00+00:00',
               '2021-12-01 00:00:00+00:00', '2021-12-01 00:00:00+00:00',
               '2021-12-01 00:00:00+00:00', '2021-12-01 00:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', ...)

>>> right\_bound = data.wrapper.index  # (4)!
>>> right\_bound
DatetimeIndex(\['2021-01-01 00:00:00+00:00', '2021-01-02 00:00:00+00:00',
               '2021-01-03 00:00:00+00:00', '2021-01-04 00:00:00+00:00',
               '2021-01-05 00:00:00+00:00', '2021-01-06 00:00:00+00:00',
               ...
               '2021-12-26 00:00:00+00:00', '2021-12-27 00:00:00+00:00',
               '2021-12-28 00:00:00+00:00', '2021-12-29 00:00:00+00:00',
               '2021-12-30 00:00:00+00:00', '2021-12-31 00:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', ...)

>>> mask = (bandwidth <= 0.1).vbt.resample\_between\_bounds(  # (5)!
...     left\_bound, 
...     right\_bound,
...     "any",
...     closed\_lbound=True,  # (6)!
...     closed\_rbound=True,
...     wrap\_kwargs=dict(fillna=0, dtype=bool)
... )
>>> mask.index = right\_bound
>>> mask.astype(int).vbt.ts\_heatmap().show()
\`\`\`

1. Find the position of the first timestamp in each month using
\[ArrayWrapper.get\_index\_ranges\](https://vectorbt.pro/pvt\_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.get\_index\_ranges).
2. Remove this and the next line if you do not want to include the first month, in case it is incomplete.
3. The left bound of each window is the corresponding anchor point (start of each month).
Create an integer array the same size as our index, fill the anchor points at their positions,
and forward fill them.
4. The right bound of each window is the current index.
5. Use \[GenericAccessor.resample\_between\_bounds\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.resample\_between\_bounds)
to map the mask values to their windows and aggregate each window using the "any" operation.
6. Make both bounds inclusive to include every single timestamp in the month.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/ts\_heatmap.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/ts\_heatmap.dark.svg#only-dark){: .iimg loading=lazy }

You can see how the signal for the bandwidth reaching the 10% mark propagates through each month,
and then the calculation resets and repeats.

## Periodically

To set signals at regular intervals, such as at 18:00 each Tuesday, we have several options.
One approach is to compare different attributes of the source and target datetime.
For example, to get the timestamps for each Tuesday, you can compare
\[pandas.DatetimeIndex.weekday\](https://pandas.pydata.org/docs/reference/api/pandas.DatetimeIndex.weekday.html#pandas.DatetimeIndex.weekday)
to 1 (Monday is 0 and Sunday is 6):

\`\`\`pycon
>>> min\_data = vbt.BinanceData.pull(  # (1)!
...     \["BTCUSDT", "ETHUSDT"\], 
...     start="2021-01-01 UTC",  # (2)!
...     end="2021-02-01 UTC",
...     timeframe="1h"
... )
>>> index = min\_data.wrapper.index
>>> tuesday\_index = index\[index.weekday == 1\]
>>> tuesday\_index
DatetimeIndex(\['2021-01-05 00:00:00+00:00', '2021-01-05 01:00:00+00:00',
               '2021-01-05 02:00:00+00:00', '2021-01-05 03:00:00+00:00',
               '2021-01-05 04:00:00+00:00', '2021-01-05 05:00:00+00:00',
               ...
               '2021-01-26 18:00:00+00:00', '2021-01-26 19:00:00+00:00',
               '2021-01-26 20:00:00+00:00', '2021-01-26 21:00:00+00:00',
               '2021-01-26 22:00:00+00:00', '2021-01-26 23:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
\`\`\`

1. Fetch hourly data for a better illustration.
2. Remember to use the UTC timezone for crypto data.

Next, we can select only those timestamps that occur at a specific time:

\`\`\`pycon
>>> tuesday\_1800\_index = tuesday\_index\[tuesday\_index.hour == 18\]
>>> tuesday\_1800\_index
DatetimeIndex(\['2021-01-05 18:00:00+00:00', '2021-01-12 18:00:00+00:00',
               '2021-01-19 18:00:00+00:00', '2021-01-26 18:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
\`\`\`

Since each attribute comparison produces a mask, you can obtain your signals using logical operations.
For example, to get the timestamps corresponding to each Tuesday at 17:30, compare the weekday to Tuesday
AND the hour to 17 AND the minute to 30:

\`\`\`pycon
>>> tuesday\_1730\_index = index\[
...     (index.weekday == 1) & 
...     (index.hour == 17) & 
...     (index.minute == 30)
... \]
>>> tuesday\_1730\_index
DatetimeIndex(\[\], dtype='datetime64\[ns, UTC\]', name='Open time', freq='H')
\`\`\`

As we can see, combining these conditions did not produce any exact matches because our index is hourly.
But what if we want to get the previous or next timestamp when there is no exact match?
In that case, the approach above will not work. Instead, we can use the function
\[pandas.Index.get\_indexer\](https://pandas.pydata.org/docs/reference/api/pandas.Index.get\_indexer.html),
which takes an array of index labels and searches for their corresponding positions in the index.
For example, let's get the position of January 7th in our index:

\`\`\`pycon
>>> index.get\_indexer(\[vbt.timestamp("2021-01-07", tz=index.tz)\])  # (1)!
array(\[144\])
\`\`\`

1. Be sure to provide the timezone if the index is timezone-aware!

If we look for an index that does not exist, it returns \`-1\`:

\`\`\`pycon
>>> index.get\_indexer(\[vbt.timestamp("2021-01-07 17:30:00", tz=index.tz)\]) 
array(\[-1\])
\`\`\`

!!! warning
    Do not use the result directly for indexing if there is a chance of no match. For example,
    if any positions returned are \`-1\` and you use them to select timestamps, the position will be replaced
    by the latest timestamp in the index.

To get either the exact match or the previous one, pass \`method='ffill'\`. To get the next one, pass
\`method='bfill'\`:

\`\`\`pycon
>>> index\[index.get\_indexer(
...     \[vbt.timestamp("2021-01-07 17:30:00", tz=index.tz)\],
...     method="ffill"
... )\]
DatetimeIndex(\['2021-01-07 17:00:00+00:00'\], ...)

>>> index\[index.get\_indexer(
...     \[vbt.timestamp("2021-01-07 17:30:00", tz=index.tz)\],
...     method="bfill"
... )\]
DatetimeIndex(\['2021-01-07 18:00:00+00:00'\], ...)
\`\`\`

Returning to our example, we first need to generate the target index for our query to search in the
source index. Use \[pandas.date\_range\](https://pandas.pydata.org/docs/reference/api/pandas.date\_range.html)
to get the timestamp for each Tuesday at midnight, then add a timedelta of 17 hours and 30 minutes.
Next, convert the target index to positions (row indices) where our signals will be placed.
Then, extract the Pandas symbol wrapper from our data instance and use it to create a new mask
with the same number of columns as our symbols. Finally, set \`True\` at the generated positions
of that mask:

\`\`\`pycon
>>> each\_tuesday = vbt.date\_range(index\[0\], index\[-1\], freq="tuesday")  # (1)!
>>> each\_tuesday\_1730 = each\_tuesday + pd.Timedelta(hours=17, minutes=30)  # (2)!
>>> each\_tuesday\_1730
DatetimeIndex(\['2021-01-05 17:30:00+00:00', '2021-01-12 17:30:00+00:00',
               '2021-01-19 17:30:00+00:00', '2021-01-26 17:30:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', freq=None)

>>> positions = index.get\_indexer(each\_tuesday\_1730, method="bfill")

>>> min\_symbol\_wrapper = min\_data.get\_symbol\_wrapper()  # (3)!
>>> mask = min\_symbol\_wrapper.fill(False)  # (4)!
>>> mask.iloc\[positions\] = True  # (5)!
>>> mask.sum()
symbol
BTCUSDT    4
ETHUSDT    4
dtype: int64
\`\`\`

1. The timezone is included in both timestamps and will be used automatically.
2. Adding a timedelta to a datetime creates a new datetime.
3. Use \[Data.get\_symbol\_wrapper\](https://vectorbt.pro/pvt\_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.get\_symbol\_wrapper)
to get a Pandas wrapper with symbols as columns.
4. Use \[ArrayWrapper.fill\](https://vectorbt.pro/pvt\_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.ArrayWrapper.fill)
to create an array the same shape as the wrapper and fill it with \`False\` values.
5. Positions are integer row indices, so use \`iloc\` to select the elements at those rows.

Let's confirm that all signals match 18:00 on Tuesday, which is the first date after the requested
17:30 on Tuesday in an hourly index:

\`\`\`pycon
>>> mask\[mask.any(axis=1)\].index.strftime("%A %T")  # (1)!
Index(\['Tuesday 18:00:00', 'Tuesday 18:00:00', 'Tuesday 18:00:00',
       'Tuesday 18:00:00'\],
      dtype='object', name='Open time')
\`\`\`

1. Details for the string format can be found \[here\](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior).

The solution above is only needed if you know just a single time boundary. For example,
if you want 17:30 on Tuesday or later, you know only the left boundary, while the right boundary is infinity
(or there may be no data after this datetime at all). When both time boundaries are known,
you can easily use the first approach and combine it with VBT's signal selection mechanism.
For example, place a signal at 17:00 on Tuesday or later, but not later than 17:00 on Wednesday.
This means placing signals from the left boundary up to the right boundary,
then selecting the first signal in that partition:

\`\`\`pycon
>>> tuesday\_after\_1700 = (index.weekday == 1) & (index.hour >= 17)
>>> wednesday\_before\_1700 = (index.weekday == 2) & (index.hour < 17)
>>> main\_cond = tuesday\_after\_1700 | wednesday\_before\_1700
>>> mask = min\_symbol\_wrapper.fill(False)
>>> mask\[main\_cond\] = True
>>> mask = mask.vbt.signals.first()
>>> mask\[mask.any(axis=1)\].index.strftime("%A %T")
Index(\['Tuesday 17:00:00', 'Tuesday 17:00:00', 'Tuesday 17:00:00',
       'Tuesday 17:00:00'\],
      dtype='object', name='Open time')
\`\`\`

The third and final approach is the VBT way :heart\_on\_fire:

This method uses the two accessor methods \[BaseAccessor.set\](https://vectorbt.pro/pvt\_6d1b3986/api/base/accessors/#vectorbtpro.base.accessors.BaseAccessor.set)
and \[BaseAccessor.set\_between\](https://vectorbt.pro/pvt\_6d1b3986/api/base/accessors/#vectorbtpro.base.accessors.BaseAccessor.set\_between),
which let you set elements of an array conditionally in a more intuitive way.

Place a signal at 17:30 each Tuesday or later:

\`\`\`pycon
>>> mask = min\_symbol\_wrapper.fill(False)
>>> mask.vbt.set(
...     True, 
...     every="tuesday", 
...     at\_time="17:30", 
...     inplace=True
... )
>>> mask\[mask.any(axis=1)\].index.strftime("%A %T")
Index(\['Tuesday 18:00:00', 'Tuesday 18:00:00', 'Tuesday 18:00:00',
       'Tuesday 18:00:00'\],
      dtype='object', name='Open time')
\`\`\`

Place a signal after 18:00 each Tuesday (exclusive):

\`\`\`pycon
>>> mask = min\_symbol\_wrapper.fill(False)
>>> mask.vbt.set(
...     True, 
...     every="tuesday", 
...     at\_time="18:00", 
...     add\_delta=pd.Timedelta(nanoseconds=1),  # (1)!
...     inplace=True
... )
>>> mask\[mask.any(axis=1)\].index.strftime("%A %T")
Index(\['Tuesday 19:00:00', 'Tuesday 19:00:00', 'Tuesday 19:00:00',
       'Tuesday 19:00:00'\],
      dtype='object', name='Open time')
\`\`\`

1. Add a nanosecond to exclude 18:00.

Fill signals between 12:00 each Monday and 17:00 each Tuesday:

\`\`\`pycon
>>> mask = min\_symbol\_wrapper.fill(False)
>>> mask.vbt.set\_between(
...     True, 
...     every="monday", 
...     start\_time="12:00", 
...     end\_time="17:00", 
...     add\_end\_delta=pd.Timedelta(days=1),  # (1)!
...     inplace=True
... )
>>> mask\[mask.any(axis=1)\].index.strftime("%A %T")
Index(\['Monday 12:00:00', 'Monday 13:00:00', 'Monday 14:00:00',
       'Monday 15:00:00', 'Monday 16:00:00', 'Monday 17:00:00',
       'Monday 18:00:00', 'Monday 19:00:00', 'Monday 20:00:00',
       ...
       'Tuesday 10:00:00', 'Tuesday 11:00:00', 'Tuesday 12:00:00',
       'Tuesday 13:00:00', 'Tuesday 14:00:00', 'Tuesday 15:00:00',
       'Tuesday 16:00:00'\],
      dtype='object', name='Open time', length=116)
\`\`\`

1. Add a day to reach Wednesday.

Place a signal exactly at midnight on January 7th, 2021:

\`\`\`pycon
>>> mask = min\_symbol\_wrapper.fill(False)
>>> mask.vbt.set(
...     True, 
...     on="January 7th 2021 UTC",  # (1)!
...     indexer\_method=None,  # (2)!
...     inplace=True
... )
>>> mask\[mask.any(axis=1)\].index
DatetimeIndex(\['2021-01-07 00:00:00+00:00'\], ...)
\`\`\`

1. Human-readable datetime strings are accepted.
2. The default method is \`bfill\`, which selects the next timestamp if there is no exact match.

Fill signals between 12:00 on January 1st/7th and 12:00 on January 2nd/8th, 2021:

\`\`\`pycon
>>> mask = min\_symbol\_wrapper.fill(False)
>>> mask.vbt.set\_between(
...     True, 
...     start=\["2021-01-01 12:00:00", "2021-01-07 12:00:00"\],  # (1)!
...     end=\["2021-01-02 12:00:00", "2021-01-08 12:00:00"\],
...     inplace=True
... )
>>> mask\[mask.any(axis=1)\].index
DatetimeIndex(\['2021-01-01 12:00:00+00:00', '2021-01-01 13:00:00+00:00',
               '2021-01-01 14:00:00+00:00', '2021-01-01 15:00:00+00:00',
               '2021-01-01 16:00:00+00:00', '2021-01-01 17:00:00+00:00',
               ...
               '2021-01-08 06:00:00+00:00', '2021-01-08 07:00:00+00:00',
               '2021-01-08 08:00:00+00:00', '2021-01-08 09:00:00+00:00',
               '2021-01-08 10:00:00+00:00', '2021-01-08 11:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
\`\`\`

1. The first range is built from the first element in \`start\` and \`end\`, and the second range
is built from the second element. You can also use human-readable datetime strings,
but those take extra time to map (to enable, see \[settings.datetime\](https://vectorbt.pro/pvt\_6d1b3986/api/\_settings/#vectorbtpro.\_settings.datetime)).

Fill signals in the first two hours of each week:

\`\`\`pycon
>>> mask = min\_symbol\_wrapper.fill(False)
>>> mask.vbt.set\_between(
...     True, 
...     every="monday",
...     split\_every=False,  # (1)!
...     add\_end\_delta="2h",
...     inplace=True
... )
>>> mask\[mask.any(axis=1)\].index
DatetimeIndex(\['2021-01-04 00:00:00+00:00', '2021-01-04 01:00:00+00:00',
               '2021-01-11 00:00:00+00:00', '2021-01-11 01:00:00+00:00',
               '2021-01-18 00:00:00+00:00', '2021-01-18 01:00:00+00:00',
               '2021-01-25 00:00:00+00:00', '2021-01-25 01:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
\`\`\`

1. Otherwise, ranges will be built from each pair of week starts.

See the API documentation for more examples.

## Iteratively

With Numba, we can write iterative logic that is just as fast as vectorized counterparts.
But which approach is better? There is no definitive answer. Overall, using vectors is often more
effective and more user-friendly because it removes the need to loop over data and automates
many mechanisms related to indexes and columns. Consider how powerful broadcasting is,
and how many extra lines of code it would take to implement the same thing iteratively.
Numba also does not allow us to work with labels or complex data types, only with numeric data,
which means you need skills and creativity to design efficient algorithms.

Most vectorized functions, as well as non-vectorized but compiled functions,
are specifically tailored for one particular task and perform it reliably. When writing your own
loop, however, you are responsible for fully implementing the required logic. Vectors are like Lego
bricks that let you easily build even the most impressive creations, while custom loops require
you to learn how to manufacture each Lego brick first :bricks:

Nevertheless, most of the functionality in VBT is powered by loops, not vectors—it should really
be called loopbt :grimacing: The main reason is simple: most operations cannot be performed
using vectors because they may introduce path dependencies, need complex data structures,
require intermediate calculations or data buffers, call third-party functions periodically,
or all of these at once. Efficiency is also a factor: you can design algorithms that loop over the data
\[only once\](https://en.wikipedia.org/wiki/One-pass\_algorithm), whereas the same logic with vectors
may read the whole dataset a dozen times. This also applies to memory usage! Lastly,
defining and running a strategy at each time step is exactly how you would do it in the real world
(and in any other backtesting framework), and as traders, we should aim to mimic real-world
behavior as closely as possible.

Enough with theory! Let's implement the first example from \[Logical operators\](#logical-operators)
using a custom loop. Unless your signals rely on multiple assets or another column grouping,
you should always start with just one column:

\`\`\`pycon
>>> @njit  # (1)!
... def generate\_mask\_1d\_nb(  # (2)!
...     high, low,  # (3)!
...     uband, mband, lband,  # (4)!
...     cond2\_th, cond4\_th  # (5)!
... ):
...     out = np.full(high.shape, False)  # (6)!
...     
...     for i in range(high.shape\[0\]):  # (7)!
...         # (8)!
...         bandwidth = (uband\[i\] - lband\[i\]) / mband\[i\]
...         cond1 = low\[i\] < lband\[i\]
...         cond2 = bandwidth > cond2\_th
...         cond3 = high\[i\] > uband\[i\]
...         cond4 = bandwidth < cond4\_th
...         signal = (cond1 and cond2) or (cond3 and cond4)  # (9)!
...         out\[i\] = signal  # (10)!
...         
...     return out

>>> mask = generate\_mask\_1d\_nb(
...     data.get("High")\["BTCUSDT"\].values,  # (11)!
...     data.get("Low")\["BTCUSDT"\].values,
...     bb.upperband\["BTCUSDT"\].values,
...     bb.middleband\["BTCUSDT"\].values,
...     bb.lowerband\["BTCUSDT"\].values,
...     0.30,
...     0.15
... )
>>> symbol\_wrapper = data.get\_symbol\_wrapper()
>>> mask = symbol\_wrapper\["BTCUSDT"\].wrap(mask)  # (12)!
>>> mask.sum()
25
\`\`\`

1. Remember to use \`@njit\` to Numba-compile the function.
2. A good convention is to use the \`nb\` suffix for Numba-compiled functions, and \`1d\_nb\` for those that
work on just one column of data.
3. These are the data arrays required for our logic.
4. These are the Bollinger Bands arrays needed by our logic.
5. Thresholds. These can also be set as keyword arguments with default values.
6. Create a boolean array matching the shape of your data arrays, filling it with the default value
\`False\` (meaning no signal).
7. Iterate over the rows, each representing a timestamp.
8. This is where the main logic goes. Perform all operations one element at a time instead of on arrays,
which is great for memory efficiency.
9. When working with single values, use \`and\` instead of \`&\`, \`or\` instead of \`|\`, and \`not\` instead of \`~\`.
10. Write the current signal to the array.
11. Because we are using a one-dimensional Numba-compiled function, we must pass one-dimensional NumPy arrays.
12. Since the mask is generated only for the \`BTCUSDT\` symbol, select that column from the wrapper and wrap
the array.

We now have the same number of signals as before—magic!

To make the function work on multiple columns, you can write another Numba-compiled function that loops
over the columns and calls \`generate\_mask\_1d\_nb\` for each one:

\`\`\`pycon
>>> @njit
... def generate\_mask\_nb(  # (1)!
...     high, low,
...     uband, mband, lband,
...     cond2\_th, cond4\_th
... ):
...     out = np.empty(high.shape, dtype=np.bool\_)  # (2)!
...     
...     for col in range(high.shape\[1\]):  # (3)!
...         out\[:, col\] = generate\_mask\_1d\_nb(  # (4)!
...             high\[:, col\], low\[:, col\],
...             uband\[:, col\], mband\[:, col\], lband\[:, col\],
...             cond2\_th, cond4\_th
...         )
...         
...     return out

>>> mask = generate\_mask\_nb(
...     vbt.to\_2d\_array(data.get("High")),  # (5)!
...     vbt.to\_2d\_array(data.get("Low")),
...     vbt.to\_2d\_array(bb.upperband),
...     vbt.to\_2d\_array(bb.middleband),
...     vbt.to\_2d\_array(bb.lowerband),
...     0.30,
...     0.15
... )
>>> mask = symbol\_wrapper.wrap(mask)
>>> mask.sum()
symbol
BTCUSDT    25
ETHUSDT    13
dtype: int64
\`\`\`

1. Remove \`1d\` from the name if the function takes two-dimensional arrays.
2. Create an empty boolean array to hold the results from \`generate\_mask\_1d\_nb\`.
If you use \`np.empty\` instead of \`np.full\`, be sure to override every value. Otherwise,
unevaluated elements will remain uninitialized and be essentially garbage.
3. Iterate over the columns, which represent assets.
4. Select the current column from each array, and call the one-dimensional function.
5. Use \[to\_2d\_array\](https://vectorbt.pro/pvt\_6d1b3986/api/base/reshaping/#vectorbtpro.base.reshaping.to\_2d\_array)
to cast any array to two dimensions and convert it to NumPy.

A more "vectorbtonic" approach is to create a stand-alone indicator where you specify
the function, the required data, and what it returns. The indicator factory then takes care of everything else!

\`\`\`pycon
>>> MaskGenerator = vbt.IF(  # (1)!
...     input\_names=\["high", "low", "uband", "mband", "lband"\],
...     param\_names=\["cond2\_th", "cond4\_th"\],
...     output\_names=\["mask"\]
... ).with\_apply\_func(generate\_mask\_1d\_nb, takes\_1d=True)  # (2)!
>>> mask\_generator = MaskGenerator.run(  # (3)!
...     data.get("High"),
...     data.get("Low"),
...     bb.upperband,
...     bb.middleband,
...     bb.lowerband,
...     \[0.3, 0.4\],
...     \[0.1, 0.2\],
...     param\_product=True  # (4)!
... )
>>> mask\_generator.mask.sum()
custom\_cond2\_th  custom\_cond4\_th  symbol 
0.3              0.1              BTCUSDT    11
                                  ETHUSDT    10
                 0.2              BTCUSDT    28
                                  ETHUSDT    27
0.4              0.1              BTCUSDT     9
                                  ETHUSDT     5
                 0.2              BTCUSDT    26
                                  ETHUSDT    22
dtype: int64
\`\`\`

1. Create the indicator's interface and specify the apply function.
2. You could also use \`generate\_mask\_nb\` with \`takes\_1d=False\`.
3. Run the indicator. Notice you do not need to worry about the correct type and shape of each array!
4. Test the Cartesian product of different threshold combinations.

How about shifting and testing truth values? Simple use cases like fixed shifts and windows are
easy to implement. Below, we compare the current value to the value a certain number of steps earlier:

\`\`\`pycon
>>> @njit
... def value\_ago\_1d\_nb(arr, ago):
...     out = np.empty(arr.shape, dtype=float\_)  # (1)!
...     for i in range(out.shape\[0\]):
...         if i - ago >= 0:  # (2)!
...             out\[i\] = arr\[i - ago\]
...         else:
...             out\[i\] = np.nan  # (3)!
...     return out

>>> arr = np.array(\[1, 2, 3\])
>>> value\_ago\_1d\_nb(arr, 1)
array(\[nan, 1., 2.\])
\`\`\`

1. Use \`np.empty\` only if you guarantee that each array element will be set. Also, when your data involves
NaN values, set the dtype to float!
2. Before accessing a previous element, make sure it is within the bounds of the array.
3. If the previous element is outside the array, set its value to NaN.

!!! important
    Always check that the element you access is within array bounds.
    Unless you have enabled \`NUMBA\_BOUNDSCHECK\`, Numba will not raise an error if you try to
    access a non-existent element. Instead, it will silently continue the calculation, and your kernel
    may eventually crash. If this happens, restart your kernel, disable Numba, or enable bounds
    checking to locate the bug and rerun your function.

Here is how you can test if any condition was true within a fixed window (a variable time interval):

\`\`\`pycon
>>> @njit
... def any\_in\_window\_1d\_nb(arr, window):
...     out = np.empty(arr.shape, dtype=np.bool\_)  # (1)!
...     for i in range(out.shape\[0\]):
...         from\_i = max(0, i + 1 - window)  # (2)!
...         to\_i = i + 1  # (3)!
...         out\[i\] = np.any(arr\[from\_i:to\_i\])  # (4)!
...     return out

>>> arr = np.array(\[False, True, True, False, False\])
>>> any\_in\_window\_1d\_nb(arr, 2)
array(\[False, True, True, True, False\])
\`\`\`

1. You can use a boolean empty array if no NaN values are present.
2. Get the left bound of the window.
3. Get the right bound of the window.
4. Use these bounds to select all elements in the window and check if any of them is \`True\`.

Once dates and times are involved, such as when you want to compare the current value
to the value exactly 5 days earlier, it is better to pre-calculate as many intermediate
steps as possible. However, you can also work directly with a datetime-like index in Numba.
Here is how you can test if any condition was true inside a variable window (a fixed time interval):

\`\`\`pycon
>>> @njit
... def any\_in\_var\_window\_1d\_nb(arr, index, freq):  # (1)!
...     out = np.empty(arr.shape, dtype=np.bool\_)
...     from\_i = 0
...     for i in range(out.shape\[0\]):
...         if index\[from\_i\] <= index\[i\] - freq:  # (2)!
...             for j in range(from\_i + 1, index.shape\[0\]):  # (3)!
...                 if index\[j\] > index\[i\] - freq:
...                     from\_i = j
...                     break  # (4)!
...         to\_i = i + 1
...         out\[i\] = np.any(arr\[from\_i:to\_i\])
...     return out

>>> arr = np.array(\[False, True, True, False, False\])
>>> index = vbt.date\_range("2020", freq="5min", periods=len(arr)).values  # (5)!
>>> freq = vbt.timedelta("10min").to\_timedelta64()  # (6)!
>>> any\_in\_var\_window\_1d\_nb(arr, index, freq)
array(\[False, True, True, True, False\])
\`\`\`

1. Use an array of type \`np.datetime64\` as the index and a constant of type \`np.timedelta64\` as the frequency.
2. Test if the previous left bound is still valid, meaning it falls within the current time interval.
3. If not, find the new left bound with a separate loop over the index.
4. Once found, set \`from\_i\` to the new left bound and exit the second loop.
5. Create an index with a 5-minute timeframe and convert it to a NumPy datetime array.
6. Define a frequency of 10 minutes and convert it to a NumPy timedelta value.

!!! hint
    In general, it is easier to design iterative functions using regular Python and only compile
    them with Numba after sufficient testing, since debugging is simpler in Python than in Numba.

Keep in mind that Numba (and VBT) supports many more features for processing numeric data
than for datetime or timedelta data. Fortunately, you can safely convert datetime and timedelta data
to integers outside of Numba, and most functions will keep working as before:

\`\`\`pycon
>>> any\_in\_var\_window\_1d\_nb(arr, vbt.dt.to\_ns(index), vbt.dt.to\_ns(freq))
array(\[False, True, True, True, False\])
\`\`\`

Why does this work? By converting datetime or timedelta to an integer, we get the total number
of nanoseconds that represent the object. For a datetime, this value is the number of nanoseconds
since the \[Unix Epoch\](https://en.wikipedia.org/wiki/Unix\_time), which is 00:00:00 UTC on January 1, 1970:

\`\`\`pycon
>>> vbt.dt.to\_ns(index)  # (1)!
array(\[1577836800000000000, 1577837100000000000, 1577837400000000000,
       1577837700000000000, 1577838000000000000\])
       
>>> vbt.dt.to\_ns(index - np.datetime64(0, "ns")) # (2)!
array(\[1577836800000000000, 1577837100000000000, 1577837400000000000,
       1577837700000000000, 1577838000000000000\])

>>> vbt.dt.to\_ns(freq)  # (3)!
600000000000

>>> vbt.dt.to\_ns(freq) / 1000 / 1000 / 1000 / 60  # (4)!
10.0
\`\`\`

1. The index as a timedelta in nanoseconds after 1970.
2. This is the same as converting a datetime to a timedelta by subtracting the Unix Epoch.
3. Frequency as a timedelta in nanoseconds.
4. Convert nanoseconds into minutes.

## Generators

Writing custom loops is powerful and enjoyable, but VBT also provides functions that can
make things easier—especially for generating signals. The most flexible helper function is the Numba-compiled
\[generate\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/nb/#vectorbtpro.signals.nb.generate\_nb) and its accessor class method
\[SignalsAccessor.generate\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.generate).
These take a target shape, initialize a boolean output array filled with \`False\` values, then
iterate over columns. For each column, they call a "placement function", which is a regular UDF
that modifies the mask in place. After making changes, the placement function should return either
the position of the last placed signal or \`-1\` if there is no signal.

All context information for the current iteration is passed via a context of type
\[GenEnContext\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/enums/#vectorbtpro.signals.enums.GenEnContext). This context provides
the current output mask segment to modify, the inclusive range start, exclusive range end,
the column, and the full output mask. This lets you make patches wherever needed. With this
approach, VBT manages the array setup and column loops, and helps you select the correct
subset of output data to modify.

Let's place a signal at 17:00 (UTC) every Tuesday:

\`\`\`pycon
>>> @njit
... def place\_func\_nb(c, index):  # (1)!
...     last\_i = -1  # (2)!
...     for out\_i in range(len(c.out)):  # (3)!
...         i = c.from\_i + out\_i  # (4)!
...         weekday = vbt.dt\_nb.weekday\_nb(index\[i\])  # (5)!
...         hour = vbt.dt\_nb.hour\_nb(index\[i\])
...         if weekday == 1 and hour == 17:  # (6)!
...             c.out\[out\_i\] = True  # (7)!
...             last\_i = out\_i
...     return last\_i  # (8)!

>>> mask = vbt.pd\_acc.signals.generate(  # (9)!
...     symbol\_wrapper.shape,  # (10)!
...     place\_func\_nb,
...     vbt.dt.to\_ns(symbol\_wrapper.index),  # (11)!
...     wrapper=symbol\_wrapper  # (12)!
... )
>>> mask.sum()
symbol
BTCUSDT    0
ETHUSDT    0
dtype: int64
\`\`\`

1. The placement function receives a context and any other user-defined arguments.
2. Create a variable to track the position of the last placed signal (if any).
3. Iterate over the output array with a local index.
4. Get the global index to retrieve the current timestamp. For example, if the array segment
has 3 elements (\`len(out)\`) and the start index is 2 (\`from\_i\`), then the first element
is at position 2 (\`i\`) and the last at position 5.
5. \[dt\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/datetime\_nb/) provides Numba-compiled functions for working with datetimes
and timedeltas, but usually expects integer representations!
6. Check if the current timestamp is 17:00 on a Tuesday.
7. If it is, place a signal using the local index; otherwise, continue to the next timestamp.
8. Make sure the returned index is local, not global.
9. Call \[SignalsAccessor.generate\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.generate)
as a class method of \[SignalsAccessor\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor).
10. Provide the shape to iterate over.
11. Provide the index in integer form (total number of nanoseconds).
12. Provide the wrapper to wrap the resulting NumPy array.

!!! info
    Segments in \[generate\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/nb/#vectorbtpro.signals.nb.generate\_nb)
    are always full columns.

But, since our index is a daily index, there will not be any signal. Instead, let's place a signal
at the next available timestamp:

\`\`\`pycon
>>> @njit
... def place\_func\_nb(c, index):
...     last\_i = -1
...     for out\_i in range(len(c.out)):
...         i = c.from\_i + out\_i
...         weekday = vbt.dt\_nb.weekday\_nb(index\[i\])
...         hour = vbt.dt\_nb.hour\_nb(index\[i\])
...         if weekday == 1 and hour == 17:
...             c.out\[out\_i\] = True
...             last\_i = out\_i
...         else:
...             past\_target\_midnight = vbt.dt\_nb.past\_weekday\_nb(index\[i\], 1)  # (1)!
...             past\_target = past\_target\_midnight + 17 \* vbt.dt\_nb.h\_ns  # (2)!
...             if (i > 0 and index\[i - 1\] < past\_target) and \\
...                 index\[i\] > past\_target:  # (3)!
...                 c.out\[out\_i\] = True
...                 last\_i = out\_i
...     return last\_i

>>> mask = vbt.pd\_acc.signals.generate(
...     symbol\_wrapper.shape,
...     place\_func\_nb,
...     vbt.dt.to\_ns(symbol\_wrapper.index),
...     wrapper=symbol\_wrapper
... )
>>> mask.sum()
symbol
BTCUSDT    52
ETHUSDT    52
dtype: int64

>>> mask.index\[mask.any(axis=1)\].strftime('%A %m/%d/%Y')  # (4)!
Index(\['Thursday 01/07/2021', ..., 'Thursday 12/30/2021'\],
      dtype='object', name='Open time')
\`\`\`

1. Get the timestamp of midnight on the previous Tuesday.
2. Get the timestamp for 17:00 on the previous Tuesday.
3. Check if the previous timestamp was before and the current timestamp is after the target time.
4. All generated signals should occur on Wednesdays.

The key point in the code above is that all datetime logic is handled using simple integers!

!!! important
    When converting to integer format, each datetime object's timezone is effectively set to UTC.
    So, make sure any value compared to the UTC timestamp is also in UTC.

But what if you want to support multiple parameter combinations? We cannot use the above function
with the indicator factory because it does not look like an apply function. Fortunately, VBT
offers a dedicated indicator factory subclass for signal generation:
\[SignalFactory\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/factory/#vectorbtpro.signals.factory.SignalFactory).
This class supports several generation modes, set by the \`mode\` argument of type
\[FactoryMode\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/enums/#vectorbtpro.signals.enums.FactoryMode). In this case, the mode is
\`FactoryMode.Entries\` because our function generates signals based only on the target shape, not on
other signal arrays. The signal factory can accept any combination of inputs, parameters, and in-place outputs
to build the skeleton of our new indicator class.

The signal factory includes the class method \[SignalFactory.with\_place\_func\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/factory/#vectorbtpro.signals.factory.SignalFactory.with\_place\_func),
which is similar to the familiar \`from\_apply\_func\`. It takes a placement function and
generates a custom function that performs all the necessary pre- and post-processing for
\[generate\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/nb/#vectorbtpro.signals.nb.generate\_nb).
(Note that other modes may use different generation functions.) This custom function, for example,
prepares arguments and assigns them to the correct positions in the placement function call.
It is then passed to \[IndicatorFactory.with\_custom\_func\](https://vectorbt.pro/pvt\_6d1b3986/api/indicators/factory/#vectorbtpro.indicators.factory.IndicatorFactory.with\_custom\_func).
As a result, you get an indicator class with a \`run\` method you can use with any custom
shape or parameter grid. Convenient, right?

Let's parameterize the exact-match placement function with two parameters: weekday and hour.

\`\`\`pycon
>>> @njit
... def place\_func\_nb(c, weekday, hour, index):  # (1)!
...     last\_i = -1
...     for out\_i in range(len(c.out)):
...         i = c.from\_i + out\_i
...         weekday\_now = vbt.dt\_nb.weekday\_nb(index\[i\])
...         hour\_now = vbt.dt\_nb.hour\_nb(index\[i\])
...         if weekday\_now == weekday and hour\_now == hour:
...             c.out\[out\_i\] = True
...             last\_i = out\_i
...     return last\_i

>>> EntryGenerator = vbt.SignalFactory(
...     mode="entries",
...     param\_names=\["weekday", "hour"\]
... ).with\_place\_func(
...     entry\_place\_func\_nb=place\_func\_nb,  # (2)!
...     entry\_settings=dict(  # (3)!
...         pass\_params=\["weekday", "hour"\],
...     ),
...     var\_args=True  # (4)!
... )
>>> entry\_generator = EntryGenerator.run(
...     symbol\_wrapper.shape,  # (5)!
...     1, 
...     \[0, 17\],  # (6)!
...     vbt.dt.to\_ns(symbol\_wrapper.index),  # (7)!
...     input\_index=symbol\_wrapper.index,  # (8)!
...     input\_columns=symbol\_wrapper.columns
... )
>>> entry\_generator.entries.sum()
custom\_weekday  custom\_hour  symbol 
2               0            BTCUSDT    52
                             ETHUSDT    52
                17           BTCUSDT     0
                             ETHUSDT     0
dtype: int64
\`\`\`

1. Each indicator function must first accept the input shape, then (optionally)
inputs, in-place outputs, parameters, and finally any additional arguments.
2. In \`FactoryMode.Entries\`, provide your placement function as \`entry\_place\_func\_nb\`.
3. Provide settings to ensure specific inputs, in-place outputs, and parameters are passed to
the placement function. If omitted, nothing will be passed!
4. Enable variable arguments to allow passing the index as an extra positional argument.
5. Input shape must be given if neither inputs nor in-place outputs provide it.
6. Test two time combinations: 00:00 and 17:00.
7. Possible thanks to \`var\_args\`.
8. Pass Pandas metadata for wrapping output arrays.

!!! note
    The \`FactoryMode.Entries\` mode does not require you to generate only entry signals during simulation.
    You can produce any mask, including exits, as long as they do not depend on entries.

The indicator function matches all midnight times but not afternoon times, as expected,
since our index is daily and only contains midnight times. You can easily plot the indicator
with the attached \`plot\` method, which knows how to visualize each mode:

\`\`\`pycon
>>> entry\_generator.plot(column=(1, 0, "BTCUSDT")).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/signal\_factory.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/signal\_factory.dark.svg#only-dark){: .iimg loading=lazy }

### Exits

After creating the position entry mask, we need to determine the position exit mask. When exits are
independent of entries, we can use the generator introduced above. However, in some cases, the exit
logic is entirely dependent on the entry signal. For example, a stop loss exit signal only exists
because of the entry signal that triggered the stop loss. There is also no guarantee that each entry
will have a corresponding exit. Therefore, this mode should only be used when entries do not depend
on exits, but exits depend on entries. In this case, generation is performed using the Numba-compiled
function \[generate\_ex\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/nb/#vectorbtpro.signals.nb.generate\_ex\_nb) and its accessor
instance method \[SignalsAccessor.generate\_exits\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.generate\_exits).
The provided context is now of type \[GenExContext\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/enums/#vectorbtpro.signals.enums.GenExContext)
and includes the input mask along with other generator-related arguments.

The generator receives an entry mask array and, for each column, visits every entry signal,
calling a UDF to place one or more exit signals that follow it. Remember how we accepted \`from\_i\`
and \`to\_i\` in the placement functions above? The previous mode always passed \`0\` as \`from\_i\` and
\`len(index)\` as \`to\_i\` because we could set our signals anywhere in the entire column.
Here, \`from\_i\` is usually the position immediately after the previous entry, while \`to\_i\` is
typically the index of the next entry, which limits our decision range to the segment between each
pair of entries.

!!! warning
    Be aware that knowing the position of the next entry signal may introduce look-ahead bias.
    Use it only for iteration purposes, and never set data based on \`to\_i\`!

Let's generate an entry each quarter and an exit at the following date:

\`\`\`pycon
>>> @njit
... def exit\_place\_func\_nb(c):
...     c.out\[0\] = True  # (1)!
...     return 0

>>> entries = symbol\_wrapper.fill(False)
>>> entries.vbt.set(True, every="Q", inplace=True)
>>> entries.index\[entries.any(axis=1)\]
DatetimeIndex(\['2021-03-31 00:00:00+00:00', '2021-06-30 00:00:00+00:00',
               '2021-09-30 00:00:00+00:00', '2021-12-31 00:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
              
>>> exits = entries.vbt.signals.generate\_exits(exit\_place\_func\_nb)  # (2)!
>>> exits.index\[exits.any(axis=1)\]
DatetimeIndex(\['2021-04-01 00:00:00+00:00', '2021-07-01 00:00:00+00:00',
               '2021-10-01 00:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
\`\`\`

1. Place an exit at the first position in the segment.
2. Unlike \[SignalsAccessor.generate\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.generate),
this method is bound to a Pandas object containing entries and uses its metadata.

We can adjust the distance to the entry signal using the \`wait\` parameter, which defaults to 1.
Let's instruct VBT to begin each segment at the same timestamp as the entry:

\`\`\`pycon
>>> exits = entries.vbt.signals.generate\_exits(
...     exit\_place\_func\_nb,
...     wait=0
... )
>>> exits.index\[exits.any(axis=1)\]
DatetimeIndex(\['2021-03-31 00:00:00+00:00', '2021-06-30 00:00:00+00:00',
               '2021-09-30 00:00:00+00:00', '2021-12-31 00:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
\`\`\`

Next, let's implement a variable waiting time based on a frequency. We will wait exactly 7 days
before placing an exit:

\`\`\`pycon
>>> @njit
... def exit\_place\_func\_nb(c, index, wait\_td):
...     for out\_i in range(len(c.out)):
...         i = c.from\_i + out\_i
...         if index\[i\] >= index\[c.from\_i\] + wait\_td:  # (1)!
...             return out\_i  # (2)!
...     return -1

>>> exits = entries.vbt.signals.generate\_exits(
...     exit\_place\_func\_nb,
...     vbt.dt.to\_ns(entries.index),  # (3)!
...     vbt.dt.to\_ns(vbt.timedelta("7d")),
...     wait=0
... )
>>> exits.index\[exits.any(axis=1)\]
DatetimeIndex(\['2021-04-07 00:00:00+00:00', '2021-07-07 00:00:00+00:00',
               '2021-10-07 00:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
\`\`\`

1. Check whether enough time has passed since the entry. For \`c.from\_i\`
to correspond to the entry's index, set \`wait\` to zero.
2. By returning the index, the generator will automatically set the respective element to True.
3. Additional arguments are provided here.

But what happens to the exit for an entry if the next entry occurs less than 7 days later?
Will an exit still be placed? No!

\`\`\`pycon
>>> entries = symbol\_wrapper.fill(False)
>>> entries.vbt.set(True, every="5d", inplace=True)
>>> exits = entries.vbt.signals.generate\_exits(
...     exit\_place\_func\_nb,
...     vbt.dt.to\_ns(entries.index),
...     vbt.dt.to\_ns(vbt.timedelta("7d")),
...     wait=0
... )
>>> exits.index\[exits.any(axis=1)\]
DatetimeIndex(\[\], dtype='datetime64\[ns, UTC\]', name='Open time', freq='D')
\`\`\`

By default, each segment is limited to the space between two surrounding entries.
To make this segment infinite, you can disable \`until\_next\`:

\`\`\`pycon
>>> exits = entries.vbt.signals.generate\_exits(
...     exit\_place\_func\_nb,
...     vbt.dt.to\_ns(entries.index),
...     vbt.dt.to\_ns(vbt.timedelta("7d")),
...     wait=0,
...     until\_next=False
... )
>>> exits.index\[exits.any(axis=1)\]
DatetimeIndex(\['2021-01-08 00:00:00+00:00', '2021-01-13 00:00:00+00:00',
               '2021-01-18 00:00:00+00:00', '2021-01-23 00:00:00+00:00',
               '2021-01-28 00:00:00+00:00', '2021-02-02 00:00:00+00:00',
               ...
               '2021-12-04 00:00:00+00:00', '2021-12-09 00:00:00+00:00',
               '2021-12-14 00:00:00+00:00', '2021-12-19 00:00:00+00:00',
               '2021-12-24 00:00:00+00:00', '2021-12-29 00:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
\`\`\`

!!! note
    In this case, it may be impossible to determine which exit belongs to which entry.
    Two or more entries may generate an exit at the same timestamp, so be careful!

In this example, the generated signals follow the sequence: \`entry1\`, \`entry2\`, \`exit1\`, \`entry3\`,
\`exit2\`, and so on. If you pass these signals to the simulator, it will execute \`entry1\` and ignore
\`entry2\` because there was no prior exit—you are still in the market. It will then properly execute
\`exit1\`. Afterward, it will open a new position with \`entry3\` and immediately close it with \`exit2\`,
which was originally intended for \`entry2\` (but that entry was ignored). To prevent this,
enable \`skip\_until\_exit\` to avoid processing any new entry signal that comes before an exit for a
previous entry signal. This setup matches the simulation order.

\`\`\`pycon
>>> exits = entries.vbt.signals.generate\_exits(
...     exit\_place\_func\_nb,
...     vbt.dt.to\_ns(entries.index),
...     vbt.dt.to\_ns(vbt.timedelta("7d")),
...     wait=0,
...     until\_next=False,
...     skip\_until\_exit=True
... )
>>> exits.index\[exits.any(axis=1)\]
DatetimeIndex(\['2021-01-08 00:00:00+00:00', '2021-01-18 00:00:00+00:00',
               '2021-01-28 00:00:00+00:00', '2021-02-07 00:00:00+00:00',
               '2021-02-17 00:00:00+00:00', '2021-02-27 00:00:00+00:00',
               ...
               '2021-11-04 00:00:00+00:00', '2021-11-14 00:00:00+00:00',
               '2021-11-24 00:00:00+00:00', '2021-12-04 00:00:00+00:00',
               '2021-12-14 00:00:00+00:00', '2021-12-24 00:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
\`\`\`

!!! note
    Always make sure to use \`skip\_until\_exit\` together with \`until\_next\` set to False.

Finally, to make the process parametrizable, use \`FactoryMode.Exits\` as the mode and provide any
supporting information with the prefix \`exit\`:

\`\`\`pycon
>>> @njit
... def exit\_place\_func\_nb(c, wait\_td, index):  # (1)!
...     for out\_i in range(len(c.out)):
...         i = c.from\_i + out\_i
...         if index\[i\] >= index\[c.from\_i\] + wait\_td:
...             return out\_i
...     return -1

>>> ExitGenerator = vbt.SignalFactory(
...     mode="exits",
...     param\_names=\["wait\_td"\]
... ).with\_place\_func(
...     exit\_place\_func\_nb=exit\_place\_func\_nb,
...     exit\_settings=dict(
...         pass\_params=\["wait\_td"\],
...     ),
...     var\_args=True,
...     wait=0,  # (2)!
...     until\_next=False,
...     skip\_until\_exit=True,
...     param\_settings=dict(  # (3)!
...         wait\_td=dict(
...             post\_index\_func=lambda x: x.map(lambda y: str(vbt.timedelta(y)))
...         )
...     ),
... )
>>> exit\_generator = ExitGenerator.run(
...     entries,  # (4)!
...     \[
...         vbt.timedelta("3d").to\_timedelta64(),  # (5)!
...         vbt.timedelta("7d").to\_timedelta64()
...     \],
...     symbol\_wrapper.index.values
... )
>>> exit\_generator.exits.sum()
custom\_wait\_td   symbol 
3 days 00:00:00  BTCUSDT    73
                 ETHUSDT    73
7 days 00:00:00  BTCUSDT    36
                 ETHUSDT    36
dtype: int64
\`\`\`

1. Remember to switch the order of the parameters and user-defined arguments.
2. Parameters for the generator can be passed as regular keyword arguments, including to the \`run\` method.
3. Convert the index level with timedeltas to strings so you can easily select different values.
The \`post\_index\_func\` function must take the original index and return a new index.
4. There is no need to provide the input shape or Pandas metadata because both can be derived
from the entries array.
5. Test two timedelta combinations. Before passing, convert the index and timedeltas to NumPy.
Here, you can use datetimes and timedeltas directly, without converting them to integers.

If desired, you can remove redundant entries:

\`\`\`pycon
>>> new\_entries = exit\_generator.entries.vbt.signals.first(  # (1)!
...     reset\_by=exit\_generator.exits,  # (2)!
...     allow\_gaps=True,  # (3)!
... )
>>> new\_entries.index\[new\_entries\[("7 days 00:00:00", "BTCUSDT")\]\]
DatetimeIndex(\['2021-01-01 00:00:00+00:00', '2021-01-11 00:00:00+00:00',
               '2021-01-21 00:00:00+00:00', '2021-01-31 00:00:00+00:00',
               '2021-02-10 00:00:00+00:00', '2021-02-20 00:00:00+00:00',
               ...
               '2021-11-17 00:00:00+00:00', '2021-11-27 00:00:00+00:00',
               '2021-12-07 00:00:00+00:00', '2021-12-17 00:00:00+00:00',
               '2021-12-27 00:00:00+00:00'\],
              dtype='datetime64\[ns, UTC\]', name='Open time', freq=None)
\`\`\`

1. Use \[SignalsAccessor.first\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.first)
to select the first \`True\` value in each partition.
2. Reset the partition when an exit signal is found.
3. The partition may contain \`False\` values.

After this step, each exit is guaranteed to occur after the entry it was generated for.

### Both

Instead of generating entry and exit signals separately, we can merge them. This approach is
especially useful when an exit depends on an entry and an entry also depends on an exit.
This kind of logic can be implemented using the Numba-compiled function
\[generate\_enex\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/nb/#vectorbtpro.signals.nb.generate\_enex\_nb) and its accessor class
method \[SignalsAccessor.generate\_both\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.generate\_both).
The generation process works as follows: first, two empty output masks are created for entries and
exits. Then, for each column, the entry placement function is called to generate one or more entry
signals. The generator then finds the position of the last generated entry signal and calls the exit
placement function on the segment that follows that entry. Next, the entry placement function runs
again. This cycle repeats until the column is completely traversed. The provided context is of type
\[GenEnExContext\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/enums/#vectorbtpro.signals.enums.GenEnExContext) and includes all
relevant information for the current turn and iteration.

Let's demonstrate the full capability of this method by placing an entry when the price falls
below one threshold, and an exit when the price rises above another threshold. The signals are
generated strictly one after another, and both the entry and exit prices are set to the close price.

\`\`\`pycon
>>> @njit
... def entry\_place\_func\_nb(c, low, close, th):
...     if c.from\_i == 0:  # (1)!
...         c.out\[0\] = True
...         return 0
...     exit\_i = c.from\_i - c.wait  # (2)!
...     exit\_price = close\[exit\_i, c.col\]  # (3)!
...     hit\_price = exit\_price \* (1 - th)
...     for out\_i in range(len(c.out)):
...         i = c.from\_i + out\_i
...         if low\[i, c.col\] <= hit\_price:  # (4)!
...             return out\_i
...     return -1

>>> @njit
... def exit\_place\_func\_nb(c, high, close, th):  # (5)!
...     entry\_i = c.from\_i - c.wait
...     entry\_price = close\[entry\_i, c.col\]
...     hit\_price = entry\_price \* (1 + th)
...     for out\_i in range(len(c.out)):
...         i = c.from\_i + out\_i
...         if high\[i, c.col\] >= hit\_price:
...             return out\_i
...     return -1

>>> entries, exits = vbt.pd\_acc.signals.generate\_both(  # (6)!
...     symbol\_wrapper.shape,
...     entry\_place\_func\_nb=entry\_place\_func\_nb,
...     entry\_place\_args=(vbt.Rep("low"), vbt.Rep("close"), 0.1),  # (7)!
...     exit\_place\_func\_nb=exit\_place\_func\_nb,
...     exit\_place\_args=(vbt.Rep("high"), vbt.Rep("close"), 0.2),
...     wrapper=symbol\_wrapper,
...     broadcast\_named\_args=dict(  # (8)!
...         high=data.get("High"),
...         low=data.get("Low"),
...         close=data.get("Close")
...     ),
...     broadcast\_kwargs=dict(post\_func=np.asarray)  # (9)!
... )

>>> fig = data.plot(
...     symbol="BTCUSDT", 
...     ohlc\_trace\_kwargs=dict(opacity=0.5), 
...     plot\_volume=False
... )
>>> entries\["BTCUSDT"\].vbt.signals.plot\_as\_entries(
...     y=data.get("Close", "BTCUSDT"), fig=fig)
>>> exits\["BTCUSDT"\].vbt.signals.plot\_as\_exits(
...     y=data.get("Close", "BTCUSDT"), fig=fig)
>>> fig.show()  # (10)!
\`\`\`

1. Place the first entry signal at the initial timestamp, since there is no previous signal
for the threshold comparison.
2. Find the (global) index of the most recent opposite signal using \`c.from\_i - c.wait\`.
3. Apply the percentage threshold to the initial close price.
4. Place an entry signal if the low price falls below the threshold.
5. For the exit placement function, note two key differences:
an exit is guaranteed to have a preceding entry, and the threshold is now above
the entry close price and must be crossed upward by the high price.
6. The accessor method is a class method, as it does not depend on any existing array
and only requires the target shape.
7. Distribute three price arrays across two functions: high, low, and close.
Use VBT's \[Rep\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/template/#vectorbtpro.utils.template.Rep) template to substitute
names with their broadcasted arrays.
8. Broadcast all arrays to match the target shape.
9. Make sure to convert the broadcasted arrays to NumPy.
10. Plot the OHLC price data, entries, and exits.
Set the OHLC chart to be more transparent so the signals are easier to see.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/both.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/both.dark.svg#only-dark){: .iimg loading=lazy }

To parameterize this logic, use \`FactoryMode.Both\` as the mode. Since the functions require input
arrays that broadcast to the input shape, VBT will not require you to provide the input shape,
as it will automatically determine it from the input arrays:

\`\`\`pycon
>>> BothGenerator = vbt.SignalFactory(
...     mode="both",
...     input\_names=\["high", "low", "close"\],
...     param\_names=\["entry\_th", "exit\_th"\]
... ).with\_place\_func(
...     entry\_place\_func\_nb=entry\_place\_func\_nb,
...     entry\_settings=dict(
...         pass\_inputs=\["low", "close"\],
...         pass\_params=\["entry\_th"\],
...     ),
...     exit\_place\_func\_nb=exit\_place\_func\_nb,
...     exit\_settings=dict(
...         pass\_inputs=\["high", "close"\],
...         pass\_params=\["exit\_th"\],
...     )
... )
>>> both\_generator = BothGenerator.run(
...     data.get("High"),
...     data.get("Low"),
...     data.get("Close"),
...     \[0.1, 0.2\],
...     \[0.2, 0.3\],
...     param\_product=True
... )
>>> fig = data.plot(
...     symbol="BTCUSDT", 
...     ohlc\_trace\_kwargs=dict(opacity=0.5), 
...     plot\_volume=False
... )
>>> both\_generator.plot(
...     column=(0.1, 0.3, "BTCUSDT"), 
...     entry\_y=data.get("Close", "BTCUSDT"), 
...     exit\_y=data.get("Close", "BTCUSDT"), 
...     fig=fig
... )
>>> fig.show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/both2.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/both2.dark.svg#only-dark){: .iimg loading=lazy }

### Chained exits

In VBT, a chain refers to a special sequence of entry and exit signals where each exit
follows exactly one entry, and each entry (except the first one) follows exactly one exit.
This structure makes it simple to match each exit to its corresponding entry and vice versa.
The previous example is a perfect illustration of a chain, as each signal from threshold crossing
depends only on the most recent opposite signal. Now, suppose you have already generated an array of
entries, and each of those entries should be valid only if there was a prior exit. Otherwise,
the entry should be ignored. This scenario is very similar to using \`FactoryMode.Exits\` with
\`skip\_until\_exit\` enabled and \`until\_next\` disabled.

However, the \`FactoryMode.Chain\` mode offers the following: it uses the
\[generate\_enex\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/nb/#vectorbtpro.signals.nb.generate\_enex\_nb) generator with the entry
placement function \[first\_place\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/nb/#vectorbtpro.signals.nb.first\_place\_nb) to select
only the first entry signal after each exit, along with any custom exit placement function.
At the end, you receive two arrays: cleaned entries (often called \`new\_entries\`) and exits (\`exits\`).

It is important to note that entries and exits generated during the signal generation phase do not
need to be used as entries and exits for simulation. For example, you might generate entry signals
from a moving average crossover, where each signal mimics a limit order, and use an exit placement
function to generate signals for filling those limit orders. As a result, these newly generated
signals can be used as actual entries in your simulation. If a new "entry" signal occurs before the
previous "exit" signal, it will be ignored. You can also track the fill price with another array.

\`\`\`pycon
>>> @njit
... def exit\_place\_func\_nb(c, low, request\_price, fill\_price\_out):
...     entry\_req\_price = request\_price\[c.from\_i - c.wait, c.col\]  # (1)!
...     for out\_i in range(len(c.out)):
...         i = c.from\_i + out\_i
...         if low\[i, c.col\] <= entry\_req\_price:  # (2)!
...             fill\_price\_out\[i, c.col\] = entry\_req\_price
...             return out\_i
...     return -1

>>> ChainGenerator = vbt.SignalFactory(
...     mode="chain",
...     input\_names=\["low", "request\_price"\],
...     in\_output\_names=\["fill\_price\_out"\]
... ).with\_place\_func(  # (3)!
...     exit\_place\_func\_nb=exit\_place\_func\_nb,
...     exit\_settings=dict(
...         pass\_inputs=\["low", "request\_price"\],
...         pass\_in\_outputs=\["fill\_price\_out"\],
...     ),
...     fill\_price\_out=np.nan  # (4)!
... )

>>> fast\_ma = vbt.talib("SMA").run(
...     data.get("Close"), 
...     vbt.Default(10), 
...     short\_name="fast\_ma"
... )
>>> slow\_ma = vbt.talib("SMA").run(
...     data.get("Close"), 
...     vbt.Default(20), 
...     short\_name="slow\_ma"
... )
>>> entries = fast\_ma.real\_crossed\_above(slow\_ma)  # (5)!
>>> entries.sum()
symbol
BTCUSDT    10
ETHUSDT     8
dtype: int64

>>> chain\_generator = ChainGenerator.run(
...     entries,
...     data.get("Low"),
...     data.get("Close") \* (1 - 0.1)  # (6)!
... )
>>> request\_mask = chain\_generator.new\_entries  # (7)!
>>> request\_mask.sum()
symbol
BTCUSDT    4
ETHUSDT    5
dtype: int64

>>> request\_price = chain\_generator.request\_price  # (8)!
>>> request\_price\[request\_mask.any(axis=1)\]
symbol                       BTCUSDT   ETHUSDT
Open time                                     
2021-02-04 00:00:00+00:00  33242.994  1436.103
2021-03-11 00:00:00+00:00  51995.844  1643.202
2021-04-02 00:00:00+00:00  53055.009  1920.321
2021-06-07 00:00:00+00:00  30197.511  2332.845
2021-06-15 00:00:00+00:00  36129.636  2289.186
2021-07-05 00:00:00+00:00  30321.126  1976.877
2021-07-06 00:00:00+00:00  30798.009  2090.250
2021-07-27 00:00:00+00:00  35512.083  2069.541

>>> fill\_mask = chain\_generator.exits  # (9)!
>>> fill\_mask.sum()
symbol
BTCUSDT    3
ETHUSDT    4
dtype: int64

>>> fill\_price = chain\_generator.fill\_price\_out  # (10)!
>>> fill\_price\[fill\_mask.any(axis=1)\]
symbol                       BTCUSDT   ETHUSDT
Open time                                     
2021-03-24 00:00:00+00:00        NaN  1643.202
2021-05-19 00:00:00+00:00  33242.994  1920.321
2021-06-08 00:00:00+00:00        NaN  2332.845
2021-06-18 00:00:00+00:00  36129.636       NaN
2021-07-13 00:00:00+00:00        NaN  1976.877
2021-07-19 00:00:00+00:00  30798.009       NaN
\`\`\`

1. Retrieve the limit price assigned at the entry.
2. Check if this price has been reached. If so, record the signal along with the fill price.
3. The entry function and its related settings are automatically populated by VBT.
4. If you do not specify a default, VBT will create the in-place output array using \`np.empty\`.
If you provide a default, VBT will use \`np.full\` to create the array and fill it with the default value.
We need the second option because our function does not overwrite every element.
5. Generate a signal array for limit order requests based on moving average crossovers.
6. Use a limit price set at 10% below the close price.
7. New entries contain filtered order request signals. Many signals are ignored because
they appear before the previous signal's limit price could be reached.
8. This is the input array used as the limit order price. Use the request mask
to obtain the price for each request order.
9. Exits contain signals for orders that have been filled, generated by the exit placement function.
Each fill signal matches a corresponding request signal.
10. This output array contains the order fill prices. Use the fill mask
to obtain the price for each filled order.

For example, the first limit order for \`BTCUSDT\` was requested on \`2021-02-04\` and filled on \`2021-05-19\`.
The first limit order for \`ETHUSDT\` was requested on \`2021-03-11\` and filled on \`2021-03-24\`.
To simulate this process, you can pass \`fill\_mask\` as the entries or order size, and \`fill\_price\` as the order price.

!!! hint
    If you want each new limit order to replace any pending one instead of ignoring pending orders, use
    \`FactoryMode.Exits\` and then select the last input signal before each output signal.

## Preset generators

A wide range of preset signal generators is available \[here\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/generators/),
which use the modes discussed above. Preset indicators are designed for specific tasks and are ready
to use without any need for custom placement functions. Their naming follows a clear convention:

\* Plain generators have no suffix.
\* Exit generators use the suffix \`X\`.
\* Both generators use the suffix \`NX\`.
\* Chain exit generators use the suffix \`CX\`.

### Random

Do you dislike randomness in trading? There is one important case where randomness is actually
welcome: trading strategy benchmarking. For example, comparing one RSI configuration to another is
not always meaningful, since both strategy instances might be inherently suboptimal. Choosing one
could simply mean picking the lesser of two evils. Random signals, however, open up a whole new
universe of unexplored strategies. Generating enough random signal permutations on a market can
reveal the underlying structure and behavior of that market, and may help determine whether your
trading strategy is driven by a true edge or simply by chance.

There are two types of random signal generation: count-based and probability-based. The count-based
method takes a target number of signals, \`n\`, to place within a certain period and guarantees to
place this number unless the period is too short. The probability-based method takes a probability,
\`prob\`, of placing a signal at each timestamp. If the probability is too high, a signal may be placed
at every timestamp; if too low, no signals may be placed. Both types can be used with the same
accessor methods: \[SignalsAccessor.generate\_random\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.generate\_random)
to spread entry signals across an entire column, \[SignalsAccessor.generate\_random\_exits\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.generate\_random\_exits)
to distribute exit signals after each entry and before the next entry, and \[SignalsAccessor.generate\_random\_both\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.generate\_random\_both)
to chain entry and exit signals one after the other.

!!! warning
    Generating an exact number of signals may introduce look-ahead bias because it involves knowledge
    of the next opposite signal or the end of the column. Use this with care, and only when the
    placement of the last signal is predetermined, such as when trading on a per-month basis.

Let's generate a signal on average once every 10 timestamps:

\`\`\`pycon
>>> btcusdt\_wrapper = symbol\_wrapper\["BTCUSDT"\]
>>> mask = vbt.pd\_acc.signals.generate\_random(
...     btcusdt\_wrapper.shape,
...     prob=1 / 10,
...     wrapper=btcusdt\_wrapper,
...     seed=42  # (1)!
... )
>>> mask\_index = mask.index\[mask\]
>>> (mask\_index\[1:\] - mask\_index\[:-1\]).mean()  # (2)!
Timedelta('8 days 03:20:55.813953488')
\`\`\`

1. Make the calculation deterministic.
2. Calculate the average distance between two neighboring signals in the mask.

!!! note
    The more signals you generate, the closer the average neighbor distance will be to the target average.

Now, let's generate exactly one signal each week. To do this, we will generate an "entry" signal on
each Monday and an "exit" signal as our target signal. This avoids look-ahead bias because we have
already defined the bounds of the generation period.

\`\`\`pycon
>>> monday\_mask = btcusdt\_wrapper.fill(False)
>>> monday\_mask.vbt.set(True, every="monday", inplace=True)  # (1)!
>>> mask = monday\_mask.vbt.signals.generate\_random\_exits(wait=0)  # (2)!
>>> mask\_index = mask.index\[mask\]
>>> mask\_index.strftime("%W %A")  # (3)!
Index(\['01 Tuesday', '02 Wednesday', '03 Wednesday', '04 Friday', '05 Friday',
       '06 Tuesday', '07 Thursday', '08 Tuesday', '09 Friday', '10 Saturday',
       '11 Friday', '12 Saturday', '13 Monday', '14 Friday', '15 Monday',
       ...
       '41 Wednesday', '42 Friday', '43 Thursday', '44 Sunday', '45 Sunday',
       '46 Sunday', '47 Saturday', '48 Saturday', '49 Tuesday', '50 Thursday',
       '51 Sunday', '52 Tuesday'\],
      dtype='object', name='Open time')
\`\`\`

1. Set \`True\` on each Monday using \[BaseAccessor.set\](https://vectorbt.pro/pvt\_6d1b3986/api/base/accessors/#vectorbtpro.base.accessors.BaseAccessor.set).
2. Generate exactly one signal after the previous Monday and before the next one. With \`wait=0\`, we
allow placing a signal immediately after Monday midnight.
3. Print the week number and weekday of each signal.

To parameterize the number of signals and the probability, you can use indicators with the prefixes
\`RAND\` and \`RPROB\`, respectively. A powerful feature of these indicators is that they can accept
parameters as array-like objects. This means you can pass \`n\` per column and \`prob\` per column, per
row, or even per element in the target shape.

Let's use \[RPROB\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/generators/rprob/#vectorbtpro.signals.generators.rprob.RPROB) to
gradually generate more signals over time. We will start with a probability of 0% and end at 100%,
placing a signal at each timestamp:

\`\`\`pycon
>>> prob = np.linspace(0, 1, len(symbol\_wrapper.index))  # (1)!
>>> rprob = vbt.RPROB.run(
...     symbol\_wrapper.shape,  # (2)!
...     vbt.Default(vbt.to\_2d\_pr\_array(prob)),  # (3)!
...     seed=42,
...     input\_index=symbol\_wrapper.index,
...     input\_columns=symbol\_wrapper.columns
... )
>>> rprob.entries.astype(int).vbt.ts\_heatmap().show()  # (4)!
\`\`\`

1. Use \[numpy.linspace\](https://numpy.org/doc/stable/reference/generated/numpy.linspace.html)
to fill the probability values between 0 and 1.
2. Provide the input shape since the indicator does not take input arrays.
3. Use \[to\_2d\_pr\_array\](https://vectorbt.pro/pvt\_6d1b3986/api/base/reshaping/#vectorbtpro.base.reshaping.to\_2d\_pr\_array) to
expand the array to two dimensions so each value matches a row rather than a column
(see broadcasting rules). Wrap this with \[Default\](https://vectorbt.pro/pvt\_6d1b3986/api/base/reshaping/#vectorbtpro.base.reshaping.Default)
to hide the parameter.
4. Plot the final distribution.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/rprob.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/rprob.dark.svg#only-dark){: .iimg loading=lazy }

To try multiple values, you can supply them as a list. Let's show that a fixed probability of 50%
yields, on average, the same number of signals as a probability that increases from 0% to 100%,
though the distributions are quite different:

\`\`\`pycon
>>> rprob = vbt.RPROB.run(
...     symbol\_wrapper.shape,
...     \[0.5, vbt.to\_2d\_pr\_array(prob)\],
...     seed=42,
...     input\_index=symbol\_wrapper.index,
...     input\_columns=symbol\_wrapper.columns
... )
>>> rprob.entries.sum()
rprob\_prob  symbol 
0.5         BTCUSDT    176
            ETHUSDT    187
array\_0     BTCUSDT    183
            ETHUSDT    178
dtype: int64
\`\`\`

### Stops

Stop signals are an important element of signal development because they allow you to propagate a
stop condition through time. VBT provides two main stop signal generators: a basic
generator that compares a single time series to any stop condition, and a specialized generator
that works with candlestick data and stop order conditions that are common in trading.

The first type can be used via the Numba-compiled function \[stop\_place\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/nb/#vectorbtpro.signals.nb.stop\_place\_nb)
and its accessor instance method \[SignalsAccessor.generate\_stop\_exits\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.generate\_stop\_exits).
There are also indicator classes \[STX\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/generators/stx/#vectorbtpro.signals.generators.stx.STX)
and \[STCX\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/generators/stcx/#vectorbtpro.signals.generators.stcx.STCX) that make the
stop parameterizable. Let's use the accessor method to generate take profit (TP) signals.
This requires four inputs: entry signals (\`entries\`), the entry price for the stop (\`entry\_ts\`),
the high price (\`ts\`), and the actual stop(s) in % to compare against the high price (\`stop\`).
Use the crossover entries generated previously. Run the method in chained exits mode to ensure
VBT waits for an exit and removes any entry signals that appear before.

\`\`\`pycon
>>> new\_entries, exits = entries.vbt.signals.generate\_stop\_exits(
...     data.get("Close"),
...     data.get("High"),
...     stop=0.1,
...     chain=True
... )
>>> new\_entries\[new\_entries.any(axis=1)\]
symbol                     BTCUSDT  ETHUSDT
Open time                                  
2021-02-04 00:00:00+00:00     True    False
2021-03-10 00:00:00+00:00     True    False
...
2021-11-07 00:00:00+00:00     True    False
2021-12-02 00:00:00+00:00    False     True

>>> exits\[exits.any(axis=1)\]
symbol                     BTCUSDT  ETHUSDT
Open time                                  
2021-02-06 00:00:00+00:00     True    False
2021-03-13 00:00:00+00:00     True    False
...
2021-10-15 00:00:00+00:00    False     True
2021-10-19 00:00:00+00:00     True    False
\`\`\`

But how do we determine the stop price? Fortunately, the Numba-compiled function also accepts a
(required) in-place output array \`stop\_ts\` that will be filled with the stop price of each exit. By default,
VBT assumes you are not interested in this array, so to save memory,
it creates an empty (uninitialized) array, passes it to Numba, and deletes it afterward. To
have it return the array, you should pass an empty dictionary \`out\_dict\`, where the accessor
method can place the array. When you provide an \`out\_dict\`, VBT will create a full (initialized)
array with \`np.nan\`, pass it to Numba, and store it in the dictionary:

\`\`\`pycon
>>> out\_dict = {}
>>> new\_entries, exits = entries.vbt.signals.generate\_stop\_exits(
...     data.get("Close"),
...     data.get("High"),
...     stop=0.1,
...     chain=True,
...     out\_dict=out\_dict
... )
>>> out\_dict\["stop\_ts"\]\[exits.any(axis=1)\]
symbol                       BTCUSDT   ETHUSDT
Open time                                     
2021-02-06 00:00:00+00:00  40630.326       NaN
2021-03-13 00:00:00+00:00  61436.749       NaN
...
2021-10-15 00:00:00+00:00        NaN  3866.797
2021-10-19 00:00:00+00:00  63179.721       NaN
\`\`\`

!!! hint
    You can also pass your own (pre-created) \`stop\_ts\` inside \`out\_dict\`, and
    VBT will override only the elements corresponding to the exits.

You can do the same with the corresponding indicator class. Let's try something different:
test two trailing stop loss (TSL) parameters, where the condition follows the high price upward
and is triggered once the low price crosses the stop value downward. The high price can be specified
with the argument \`follow\_ts\`. The entry price will be the open price (even though we generated entries
using the close price, let's assume this situation for now), so we will also allow placing
the first signal at the entry bar by setting \`wait\` to zero:

\`\`\`pycon
>>> stcx = vbt.STCX.run(  # (1)!
...     entries,
...     data.get("Open"),
...     ts=data.get("Low"),
...     follow\_ts=data.get("High"),
...     stop=-0.1,  # (2)!
...     trailing=\[False, True\],  # (3)!
...     wait=0  # (4)!
... )
>>> fig = data.plot(
...     symbol="BTCUSDT", 
...     ohlc\_trace\_kwargs=dict(opacity=0.5), 
...     plot\_volume=False
... )
>>> stcx.plot(
...     column=(-0.1, True, "BTCUSDT"), 
...     entry\_y="entry\_ts",  # (5)!
...     exit\_y="stop\_ts", 
...     fig=fig
... )
>>> fig.show()
\`\`\`

1. Indicators usually assume you want all optional arrays, so you do not need to
pass anything. If you are not interested, pass \`stop\_ts=None\` to save some RAM.
2. For a downward crossover condition, specify a negative stop value.
3. Test both SL and TSL.
4. Set waiting time to zero only if the entry price is the open price.
5. When plotting, you can provide \`y\` as an attribute of the indicator instance.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/stcx.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/stcx.dark.svg#only-dark){: .iimg loading=lazy }

!!! note
    Waiting time cannot be higher than 1. If waiting time is 0, \`entry\_ts\` should be the
    first value in the bar. If waiting time is 1, \`entry\_ts\` should be the last value in the bar;
    otherwise, the stop could have also been hit at the first bar.

    By setting waiting time to zero, you may have an entry and an exit on the same bar.
    Multiple orders on the same bar can only be handled using a flexible order function
    or by converting signals directly into order records. When passed directly to
    \[Portfolio.from\_signals\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from\_signals),
    any conflicting signals will be ignored.

If you want to place only SL, TSL, TP, and TTP orders, a more complete approach is to
use the full OHLC data, as utilized by the Numba-compiled function
\[ohlc\_stop\_place\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/nb/#vectorbtpro.signals.nb.ohlc\_stop\_place\_nb),
the accessor instance method \[SignalsAccessor.generate\_ohlc\_stop\_exits\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.SignalsAccessor.generate\_ohlc\_stop\_exits),
and the corresponding indicator classes \[OHLCSTX\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/generators/ohlcstx/#vectorbtpro.signals.generators.ohlcstx.OHLCSTX)
and \[OHLCSTCX\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/generators/ohlcstcx/#vectorbtpro.signals.generators.ohlcstcx.OHLCSTCX).
The main advantage of this approach is that you can check for all stop order conditions at the same time.

Let's generate signals based on a
\[stop loss and trailing stop loss combo\](https://www.investopedia.com/articles/trading/08/trailing-stop-loss.asp)
of 10% and 15%, respectively:

\`\`\`pycon
>>> ohlcstcx = vbt.OHLCSTCX.run(
...     entries,
...     data.get("Close"),  # (1)!
...     data.get("Open"),  # (2)!
...     data.get("High"),
...     data.get("Low"),
...     data.get("Close"),
...     sl\_stop=vbt.Default(0.1),  # (3)!
...     tsl\_stop=vbt.Default(0.15),
...     is\_entry\_open=False  # (4)!
... )
>>> ohlcstcx.plot(column=("BTCUSDT")).show()  # (5)!
\`\`\`

1. Entry price. Here, we use the close price since the entries array was generated using it.
2. OHLC.
3. Stop parameters.
4. Entry price is the close price. Enable this flag if the entry price is the open price.
5. The indicator instance automatically plots the candlestick data.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/ohlcstcx.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/ohlcstcx.dark.svg#only-dark){: .iimg loading=lazy }

Keep in mind that there is no intra-candle data. If there was a large price fluctuation in
both directions, we could not determine whether SL was triggered before TP or vice versa.
Certain assumptions must be made:

\* If a stop is hit before the open price, the stop price becomes the current open price.
This is especially true for \`wait=1\` and \`is\_entry\_open=True\`.
\* Trailing stop can only be based on the previous high/low price, not the current one.
\* We pessimistically assume that any SL is triggered before any TP.

A common tricky situation occurs when the entry price is the open price and you are waiting one bar.
For example, what happens if the condition is met during the waiting period? You cannot place 
an exit signal at the entry bar. Instead, the function waits until the next bar and checks 
whether the condition is still valid for the open price. If it is, the signal is placed with the stop
price set to the open price. If not, the function simply waits for the next opportunity.
If the stop is trailing, the target price will update as usual at the entry timestamp.
To avoid logical bugs, it is recommended to use the close price as the entry price when \`wait\` is one bar
(which is the default).

When working with multiple stop types simultaneously, you may want to know which exact type
was triggered. This information is stored in the \`stop\_type\` array (machine-readable)
and the \`stop\_type\_readable\` array (human-readable):

\`\`\`pycon
>>> ohlcstcx.stop\_type\_readable\[ohlcstcx.exits.any(axis=1)\]
symbol                    BTCUSDT ETHUSDT
Open time                                
2021-02-22 00:00:00+00:00     TSL    None
2021-03-23 00:00:00+00:00    None     TSL
2021-03-24 00:00:00+00:00     TSL    None
2021-04-18 00:00:00+00:00      SL     TSL
2021-05-12 00:00:00+00:00      SL    None
2021-06-08 00:00:00+00:00    None      SL
2021-06-18 00:00:00+00:00      SL    None
2021-07-09 00:00:00+00:00    None     TSL
2021-07-19 00:00:00+00:00      SL    None
2021-09-07 00:00:00+00:00     TSL     TSL
2021-11-16 00:00:00+00:00     TSL     TSL
2021-12-03 00:00:00+00:00    None      SL
2021-12-29 00:00:00+00:00    None      SL
2021-12-31 00:00:00+00:00      SL    None
\`\`\`

All stop types are listed in the enumerated type \[StopType\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/enums/#vectorbtpro.signals.enums.StopType).

Both stop signal generation modes are very flexible with inputs. For example, if any element in 
the \`ts\` and \`follow\_ts\` arrays is NaN (default), it will be replaced by the corresponding element in \`entry\_ts\`.
If only an element in \`follow\_ts\` is NaN, it will be replaced 
by the minimum or maximum (depending on the sign of the stop value) of the element in both other arrays.
Similarly, in the second mode, you can provide only \`entry\_price\`, and VBT will auto-populate 
the open price if \`is\_entry\_open\` is enabled, or the close price otherwise. Without \`high\`, 
VBT will use the maximum of \`open\` and \`close\`. Generally, you are not required to provide 
every piece of information except for the entry price, but it is best to provide as much 
detail as you can for better decision-making and to closely simulate real-world conditions.

For example, let's run the same as above but specify only the entry price:

\`\`\`pycon
>>> ohlcstcx = vbt.OHLCSTCX.run(
...     entries,
...     data.get("Close"),
...     sl\_stop=vbt.Default(0.1),
...     tsl\_stop=vbt.Default(0.15),
...     is\_entry\_open=False
... )
>>> ohlcstcx.plot(column=("BTCUSDT")).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/ohlcstcx2.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/ohlcstcx2.dark.svg#only-dark){: .iimg loading=lazy }

The same flexibility applies to parameters: just like the probability parameter 
in random signal generators, you can pass each parameter as an array, such as one element per row, 
column, or even element. Let's treat every second entry as a short entry and reverse the \[trailing
take profit\](https://capitalise.ai/trailing-take-profit-manage-your-risk-while-locking-the-profits/)
(TTP) logic for it:

\`\`\`pycon
>>> entry\_pos\_rank = entries.vbt.signals.pos\_rank(allow\_gaps=True)  # (1)!
>>> short\_entries = (entry\_pos\_rank >= 0) & (entry\_pos\_rank % 2 == 1)  # (2)!

>>> ohlcstcx = vbt.OHLCSTCX.run(
...     entries,
...     data.get("Close"),
...     data.get("Open"),
...     data.get("High"),
...     data.get("Low"),
...     data.get("Close"),
...     tsl\_th=vbt.Default(0.2),  # (3)!
...     tsl\_stop=vbt.Default(0.1),
...     reverse=vbt.Default(short\_entries),  # (4)!
...     is\_entry\_open=False
... )
>>> ohlcstcx.plot(column=("BTCUSDT")).show()
\`\`\`

1. Rank each entry signal by its position among all entry signals using 
\[SignalsAccessor.pos\_rank\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.pos\_rank).
2. Select only those entries whose position is odd, meaning those not divisible by 2.
These will be our short entries.
3. TTP information consists of two parts: a take profit threshold (\`tsl\_th\`) that needs to be crossed upward,
and a trailing stop loss (\`tsl\_stop\`) that is enabled once the threshold is crossed.
4. The short entry mask becomes our reversal mask.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/ohlcstcx3.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/ohlcstcx3.dark.svg#only-dark){: .iimg loading=lazy }

You can then split both final arrays into four direction-aware arrays for simulation:

\`\`\`pycon
>>> long\_entries = ohlcstcx.new\_entries.vbt & (~short\_entries)  # (1)!
>>> long\_exits = ohlcstcx.exits.vbt.signals.first\_after(long\_entries)  # (2)!
>>> short\_entries = ohlcstcx.new\_entries.vbt & short\_entries
>>> short\_exits = ohlcstcx.exits.vbt.signals.first\_after(short\_entries)

>>> fig = data.plot(
...     symbol="BTCUSDT", 
...     ohlc\_trace\_kwargs=dict(opacity=0.5), 
...     plot\_volume=False
... )
>>> long\_entries\["BTCUSDT"\].vbt.signals.plot\_as\_entries(
...     ohlcstcx.entry\_price\["BTCUSDT"\],
...     trace\_kwargs=dict(marker=dict(color="limegreen"), name="Long entries"), 
...     fig=fig
... )
>>> long\_exits\["BTCUSDT"\].vbt.signals.plot\_as\_exits(
...     ohlcstcx.stop\_price\["BTCUSDT"\],
...     trace\_kwargs=dict(marker=dict(color="orange"), name="Long exits"),
...     fig=fig
... )
>>> short\_entries\["BTCUSDT"\].vbt.signals.plot\_as\_entries(
...     ohlcstcx.entry\_price\["BTCUSDT"\],
...     trace\_kwargs=dict(marker=dict(color="magenta"), name="Short entries"),
...     fig=fig
... )
>>> short\_exits\["BTCUSDT"\].vbt.signals.plot\_as\_exits(
...     ohlcstcx.stop\_price\["BTCUSDT"\],
...     trace\_kwargs=dict(marker=dict(color="red"), name="Short exits"),
...     fig=fig
... )
>>> fig.show()
\`\`\`

1. We cannot use the original \`entries\` array since the generator ignored some entries
that came too early. But since new entries retain their positions, we can identify
long signals by inverting the short array and combining it with the new entry array using the \_AND\_ operation.
2. A useful feature of the chained exits mode is that each exit always follows its entry directly—
there are no other entries in between, so we can use \[SignalsAccessor.first\_after\](https://vectorbt.pro/pvt\_6d1b3986/api/signals/accessors/#vectorbtpro.signals.accessors.first\_after)
for this task.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/ohlcstcx4.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/signal-dev/ohlcstcx4.dark.svg#only-dark){: .iimg loading=lazy }

It seems like all trades are winners, thanks to a range-bound but still volatile market :four\_leaf\_clover:

\[:material-language-python: Python code\](https://vectorbt.pro/pvt\_6d1b3986/assets/jupytext/tutorials/signal-development/generation.py.txt){ .md-button target="blank\_" }
\[:material-notebook-outline: Notebook\](https://github.com/polakowo/vectorbt.pro/blob/main/notebooks/SignalDevelopment.ipynb){ .md-button target="blank\_" }