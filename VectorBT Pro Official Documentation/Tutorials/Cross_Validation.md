\---
title: Cross-validation
description: Learn how to cross-validate a trading strategy using VectorBT PRO
icon: material/check-all
---

# :material-check-all: Cross-validation

??? youtube "Cross-validation on YouTube"
    <iframe class="youtube-video" src="https://www.youtube.com/embed/\_BSSPZplLHs?si=s-lqiyASBqeGigW9" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

After developing a rule-based or machine learning-based strategy, it is time to backtest it. If our first
backtest yields a low Sharpe ratio, we might tweak the strategy to try to improve it. After several rounds
of parameter adjustments, we may arrive at a "flawless" set of parameters and a strategy showing an
exceptional Sharpe ratio. However, in live trading, the strategy may perform poorly, resulting in losses.
What went wrong?

Markets naturally contain noise—small and frequent inconsistencies in price data. When designing a
strategy, we should avoid optimizing for a single period, because the model may fit the historical data so
closely that it fails to predict the future effectively. This is similar to tuning a car for one specific
racetrack and expecting it to perform equally well everywhere. Especially with VBT, which allows us to
search large databases of historical market data for patterns, it can be easy to create complex rules that
appear highly accurate at predicting price changes (see \[\_p\_-hacking\](https://en.wikipedia.org/wiki/Data\_dredging))
but make random guesses when applied to data outside the sample used to build the model.

Overfitting (also known as \[curve fitting\](https://en.wikipedia.org/wiki/Curve\_fitting)) typically occurs
for one or more of these reasons: mistaking noise for signal, or excessively tweaking too many parameters.
To avoid overfitting, we should use \[cross-validation\](https://en.wikipedia.org/wiki/Cross-validation\_(statistics))
(CV), which involves splitting a data sample into complementary subsets, analyzing one subset called the
training or \_in-sample\_ (IS) set, and validating the analysis on the other subset called the validation or
\_out-of-sample\_ (OOS) set. This procedure is repeated until we have multiple OOS periods and can calculate
statistics from all these results combined. The key questions we need to ask are: are our parameter choices
robust in the IS periods? Is our performance robust in the OOS periods? If not, we are essentially guessing,
and as quant investors we should not leave room for second-guessing when real money is at stake.

Let's consider a simple strategy based on a moving average crossover.

First, we will pull some data:

\`\`\`pycon
>>> from vectorbtpro import \*

>>> data = vbt.BinanceData.pull("BTCUSDT", end="2022-11-01 UTC")
>>> data.index
DatetimeIndex(\['2017-08-17 00:00:00+00:00', '2017-08-18 00:00:00+00:00',
               '2017-08-19 00:00:00+00:00', '2017-08-20 00:00:00+00:00',
               ...
               '2022-10-28 00:00:00+00:00', '2022-10-29 00:00:00+00:00',
               '2022-10-30 00:00:00+00:00', '2022-10-31 00:00:00+00:00'\],
    dtype='datetime64\[ns, UTC\]', name='Open time', length=1902, freq='D')
\`\`\`

Next, let's create a parameterized mini-pipeline that takes data and parameters and returns the Sharpe
ratio, which should reflect our strategy's performance on that test period:

\`\`\`pycon
>>> @vbt.parameterized(merge\_func="concat")  # (1)!
... def sma\_crossover\_perf(data, fast\_window, slow\_window):
...     fast\_sma = data.run("sma", fast\_window, short\_name="fast\_sma")  # (2)!
...     slow\_sma = data.run("sma", slow\_window, short\_name="slow\_sma")
...     entries = fast\_sma.real\_crossed\_above(slow\_sma)
...     exits = fast\_sma.real\_crossed\_below(slow\_sma)
...     pf = vbt.Portfolio.from\_signals(
...         data, entries, exits, direction="both")  # (3)!
...     return pf.sharpe\_ratio  # (4)!
\`\`\`

1. The \[@parameterized\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.parameterized) decorator allows
\`sma\_crossover\_perf\` to accept arguments wrapped with \[Param\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.Param),
build the grid of parameter combinations, run \`sma\_crossover\_perf\` for each, and combine the results using
concatenation.
2. Use \[Data.run\](https://vectorbt.pro/pvt\_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.run) to execute an indicator on a data instance.
3. Enable shorting by marking exit signals as short entry signals.
4. This function returns a single value, which becomes a Series after processing all parameter combinations.

Let's test a grid of \`fast\_window\` and \`slow\_window\` combinations over one year of that data:

\`\`\`pycon
>>> perf = sma\_crossover\_perf(  # (1)!
...     data\["2020":"2020"\],  # (2)!
...     vbt.Param(np.arange(5, 50), condition="x < slow\_window"),  # (3)!
...     vbt.Param(np.arange(5, 50)),  # (4)!
...     \_execute\_kwargs=dict(  # (5)!
...         clear\_cache=50,  # (6)!
...         collect\_garbage=50
...     )
... )
>>> perf
fast\_window  slow\_window
5            6              0.625318
             7              0.333243
             8              1.171861
             9              1.062940
             10             0.635302
                                 ...   
46           48             0.534582
             49             0.573196
47           48             0.445239
             49             0.357548
48           49            -0.826995
Length: 990, dtype: float64
\`\`\`

1. Even with the \`parameterized\` decorator, the function arguments remain the same as
\`sma\_crossover\_perf\`.
2. \[Data\](https://vectorbt.pro/pvt\_6d1b3986/api/data/base/#vectorbtpro.data.base.Data) instances can be sliced like standard Pandas objects.
Remember, the right bound is inclusive.
3. Using a fast SMA window longer than the slow SMA window does not make sense, so we set a condition to
reduce parameter combinations.
4. No condition is needed for the second parameter, since the first already enforces this relationship.
5. Any arguments intended for the \[@parameterized\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.parameterized)
decorator must be prefixed with \`\_\`.
6. By default, the \`parameterized\` decorator uses the \[SerialEngine\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.SerialEngine)
to execute each parameter combination. This engine accepts arguments to clear the cache and
collect memory garbage. Here, we do this every 50 iterations to manage memory usage.

\[=100% "Combination 990/990"\]{: .candystripe .candystripe-animate }

It took 30 seconds to test 990 parameter combinations, or about 30 milliseconds per run. Below, we sort
the Sharpe ratios in descending order to find the best parameter combinations:

\`\`\`pycon
>>> perf.sort\_values(ascending=False)
fast\_window  slow\_window
15           20             3.669815
14           19             3.484855
15           18             3.480444
14           21             3.467951
13           19             3.457093
                                 ...   
36           41             0.116606
             37             0.075805
42           43             0.004402
10           12            -0.465247
48           49            -0.826995
Length: 990, dtype: float64
\`\`\`

It appears that \`fast\_window=15\` and \`slow\_window=20\` could make us very wealthy! But before putting all
our savings on that configuration, let's test it on the following year:

\`\`\`pycon
>>> best\_fast\_window, best\_slow\_window = perf.idxmax()  # (1)!
>>> sma\_crossover\_perf(
...     data\["2021":"2021"\],
...     best\_fast\_window,  # (2)!
...     best\_slow\_window
... )
-1.1940481501019478
\`\`\`

1. Retrieve the parameter values with the highest Sharpe ratio.
2. There is no need to wrap the parameters with \[Param\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.Param)
if they are single values or if we do not want to build a parameter grid. They are simply forwarded to
\`sma\_crossover\_perf\`.

The result is disappointing, but did we at least outperform a baseline? Let's calculate the Sharpe ratio
for the buy-and-hold strategy during that year:

\`\`\`pycon
>>> data\["2021":"2021"\].run("from\_holding").sharpe\_ratio  # (1)!
0.9641311236043749
\`\`\`

1. \[Data.run\](https://vectorbt.pro/pvt\_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.run) accepts not only indicator names, but also
portfolio method names. The first run may take some time because it needs to be compiled.

It seems that our strategy performed very poorly :speak\_no\_evil:

But this was only one optimization test. What if that period was an outlier and our strategy actually
performs well \_on average\_? Let's try to answer this by repeating the test above on each consecutive
180-day period in the data:

\`\`\`pycon
>>> start\_index = data.index\[0\]  # (1)!
>>> period = pd.Timedelta(days=180)  # (2)!
>>> all\_is\_bounds = {}  # (3)!
>>> all\_is\_bl\_perf = {}
>>> all\_is\_perf = {}
>>> all\_oos\_bounds = {}  # (4)!
>>> all\_oos\_bl\_perf = {}
>>> all\_oos\_perf = {}
>>> split\_idx = 0
>>> period\_idx = 0

>>> with vbt.ProgressBar() as pbar:  # (5)!
...     while start\_index + 2 \* period <= data.index\[-1\]:  # (6)!
...         pbar.set\_prefix(str(start\_index))
...
...         is\_start\_index = start\_index
...         is\_end\_index = start\_index + period - pd.Timedelta(nanoseconds=1)  # (7)!
...         is\_data = data\[is\_start\_index : is\_end\_index\]
...         is\_bl\_perf = is\_data.run("from\_holding").sharpe\_ratio
...         is\_perf = sma\_crossover\_perf(
...             is\_data,
...             vbt.Param(np.arange(5, 50), condition="x < slow\_window"),
...             vbt.Param(np.arange(5, 50)),
...             \_execute\_kwargs=dict(
...                 clear\_cache=50,
...                 collect\_garbage=50
...             )
...         )
...
...         oos\_start\_index = start\_index + period  # (8)!
...         oos\_end\_index = start\_index + 2 \* period - pd.Timedelta(nanoseconds=1)
...         oos\_data = data\[oos\_start\_index : oos\_end\_index\]
...         oos\_bl\_perf = oos\_data.run("from\_holding").sharpe\_ratio
...         best\_fw, best\_sw = is\_perf.idxmax()
...         oos\_perf = sma\_crossover\_perf(oos\_data, best\_fw, best\_sw)
...         oos\_perf\_index = is\_perf.index\[is\_perf.index == (best\_fw, best\_sw)\]
...         oos\_perf = pd.Series(\[oos\_perf\], index=oos\_perf\_index)  # (9)!
...
...         all\_is\_bounds\[period\_idx\] = (is\_start\_index, is\_end\_index)
...         all\_oos\_bounds\[period\_idx + 1\] = (oos\_start\_index, oos\_end\_index)
...         all\_is\_bl\_perf\[(split\_idx, period\_idx)\] = is\_bl\_perf
...         all\_oos\_bl\_perf\[(split\_idx, period\_idx + 1)\] = oos\_bl\_perf
...         all\_is\_perf\[(split\_idx, period\_idx)\] = is\_perf
...         all\_oos\_perf\[(split\_idx, period\_idx + 1)\] = oos\_perf
...         start\_index = start\_index + period  # (10)!
...         split\_idx += 1
...         period\_idx += 1
...         pbar.update()  # (11)!
\`\`\`

1. Get the first date in the index. This has the type \[pandas.Timestamp\](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Timestamp.html).
2. Define the period using \[pandas.Timedelta\](https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.html)
so it can be added to \[pandas.Timestamp\](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Timestamp.html).
3. Store range start (inclusive) and end (exclusive) indexes, baseline (i.e., buy-and-hold) performance,
and optimization performance for each IS period.
4. Store range start and end indexes, baseline performance, and validation performance for each OOS period.
5. Be sure to install \[tqdm\](https://github.com/tqdm/tqdm) to display the progress bar.
6. Why use a while-loop instead of a for-loop? Because we do not know the number of splits in advance. We
process one split, increment the starting date, and repeat. This works naturally as a while-loop, and we
continue as long as both periods are fully covered by our index.
7. The right bound of the IS period should be \*\*exclusive\*\* because we do not want it to overlap with the
left bound of the OOS period. Since \[pandas.DataFrame.loc\](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.loc.html)
includes the right bound, we simply subtract one nanosecond from it (keep this trick in mind!).
8. The IS period covers the days from \[0, 180), while the OOS period covers the days from \[180, 360).
9. The function call above returns a single value, but we convert it to a Series with the proper
index so we know which parameter combination it corresponds to.
10. The next IS period starts where the current IS period ends.
11. Update the progress bar to indicate this split has been processed.

\[=100% "Period 9/9"\]{: .candystripe .candystripe-animate }

\`\`\`pycon
>>> is\_period\_ranges = pd.DataFrame.from\_dict(  # (1)!
...     all\_is\_bounds, 
...     orient="index",
...     columns=\["start", "end"\]
... )
>>> is\_period\_ranges.index.name = "period"
>>> oos\_period\_ranges = pd.DataFrame.from\_dict(
...     all\_oos\_bounds, 
...     orient="index",
...     columns=\["start", "end"\]
... )
>>> oos\_period\_ranges.index.name = "period"
>>> period\_ranges = pd.concat((is\_period\_ranges, oos\_period\_ranges))  # (2)!
>>> period\_ranges = period\_ranges.drop\_duplicates()
>>> period\_ranges
                           start                                 end
period                                                              
0      2017-08-17 00:00:00+00:00 2018-02-12 23:59:59.999999999+00:00
1      2018-02-13 00:00:00+00:00 2018-08-11 23:59:59.999999999+00:00
2      2018-08-12 00:00:00+00:00 2019-02-07 23:59:59.999999999+00:00
3      2019-02-08 00:00:00+00:00 2019-08-06 23:59:59.999999999+00:00
4      2019-08-07 00:00:00+00:00 2020-02-02 23:59:59.999999999+00:00
5      2020-02-03 00:00:00+00:00 2020-07-31 23:59:59.999999999+00:00
6      2020-08-01 00:00:00+00:00 2021-01-27 23:59:59.999999999+00:00
7      2021-01-28 00:00:00+00:00 2021-07-26 23:59:59.999999999+00:00
8      2021-07-27 00:00:00+00:00 2022-01-22 23:59:59.999999999+00:00
9      2022-01-23 00:00:00+00:00 2022-07-21 23:59:59.999999999+00:00

>>> is\_bl\_perf = pd.Series(all\_is\_bl\_perf)  # (3)!
>>> is\_bl\_perf.index.names = \["split", "period"\]
>>> oos\_bl\_perf = pd.Series(all\_oos\_bl\_perf)
>>> oos\_bl\_perf.index.names = \["split", "period"\]
>>> bl\_perf = pd.concat((  # (4)!
...     is\_bl\_perf.vbt.select\_levels("period"), 
...     oos\_bl\_perf.vbt.select\_levels("period")
... ))
>>> bl\_perf = bl\_perf.drop\_duplicates()
>>> bl\_perf
period
0    1.846205
1   -0.430642
2   -1.741407
3    3.408079
4   -0.556471
5    0.954291
6    3.241618
7    0.686198
8   -0.038013
9   -0.917722
dtype: float64

>>> is\_perf = pd.concat(all\_is\_perf, names=\["split", "period"\])  # (5)!
>>> is\_perf
split  period  fast\_window  slow\_window
0      0       5            6              1.766853
                            7              2.200321
                            8              2.698365
                            9              1.426788
                            10             0.849323
                                                ...   
8      8       46           48             0.043127
                            49             0.358875
               47           48             1.093769
                            49             1.105751
               48           49             0.159483
Length: 8910, dtype: float64

>>> oos\_perf = pd.concat(all\_oos\_perf, names=\["split", "period"\])
>>> oos\_perf
split  period  fast\_window  slow\_window
0      1       19           34             0.534007
1      2       6            7             -1.098628
2      3       18           20             1.687363
3      4       14           18             0.035346
4      5       18           21             1.877054
5      6       20           27             2.567751
6      7       11           18            -2.061754
7      8       29           30             0.965434
8      9       25           28             1.253361
dtype: float64

>>> is\_best\_mask = is\_perf.index.vbt.drop\_levels("period").isin(  # (6)!
...     oos\_perf.index.vbt.drop\_levels("period"))
>>> is\_best\_perf = is\_perf\[is\_best\_mask\]
>>> is\_best\_perf
split  period  fast\_window  slow\_window
0      0       19           34             4.380746
1      1       6            7              2.538909
2      2       18           20             4.351354
3      3       14           18             3.605775
4      4       18           21             3.227437
5      5       20           27             3.362096
6      6       11           18             4.644594
7      7       29           30             3.379370
8      8       25           28             2.143645
dtype: float64
\`\`\`

1. If each value in a dict has multiple elements, use
\[pandas.DataFrame.from\_dict\](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.from\_dict.html#pandas.DataFrame.from\_dict)
to combine them into a single DataFrame.
2. We know the bounds of each IS and OOS set, but since OOS periods essentially become the next IS period,
let's create just one Series keyed by period.
3. If each value in a dict is a single element, you can wrap the dict directly with a Series.
4. The approach is the same as for bounds, but we need to remove the \`split\` level first.
5. If each value in a dict is a Series, use \[pandas.concat\](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.concat.html)
to concatenate them into a single Series.
6. Get the performance for the best parameter combination in each IS set using the index
from the corresponding OOS set. Since both Series are linked by \`split\`, \`fast\_window\`, and
\`slow\_window\`, remove \`period\` before doing this operation.

We have collected information for 9 splits and 10 periods. Now it is time to evaluate the results!
The index of each Series makes it easy to connect information and analyze everything together: the
\`split\` level connects elements within the same split, the \`period\` level links elements in the
same time period, and \`fast\_window\` and \`slow\_window\` relate elements by parameter combination.
To begin, let's compare their distributions:

\`\`\`pycon
>>> pd.concat((
...     is\_perf.describe(),
...     is\_best\_perf.describe(),
...     is\_bl\_perf.describe(),
...     oos\_perf.describe(),
...     oos\_bl\_perf.describe()
... ), axis=1, keys=\[
...     "IS", 
...     "IS (Best)", 
...     "IS (Baseline)", 
...     "OOS (Test)", 
...     "OOS (Baseline)"
... \])
                IS  IS (Best)  IS (Baseline)  OOS (Test)  OOS (Baseline)
count  8882.000000   9.000000       9.000000    9.000000        9.000000
mean      0.994383   3.514881       0.818873    0.639993        0.511770
std       1.746003   0.843435       1.746682    1.480066        1.786012
min      -3.600854   2.143645      -1.741407   -2.061754       -1.741407
25%      -0.272061   3.227437      -0.430642    0.035346       -0.556471
50%       1.173828   3.379370       0.686198    0.965434       -0.038013
75%       2.112042   4.351354       1.846205    1.687363        0.954291
max       4.644594   4.644594       3.408079    2.567751        3.408079
\`\`\`

Although the OOS results are much lower than the best IS results, our strategy still outperforms the
baseline on average! Over 50% of periods have a Sharpe ratio of 0.96 or higher, while the baseline's
median sits at only -0.03. Another way to analyze this data is by plotting it. Since all these Series
can be linked by period, we will use the \`period\` level as the X-axis and the performance (Sharpe in
this case) as the Y-axis. Most Series can be shown as lines, but because IS sets include multiple
parameter combinations, we should show their distributions as boxes instead:

\`\`\`pycon
>>> fig = is\_perf.vbt.boxplot(  # (1)!
...     by\_level="period",  # (2)!
...     trace\_kwargs=dict(  # (3)!
...         line=dict(color="lightskyblue"), 
...         opacity=0.4,
...         showlegend=False
...     ),
...     xaxis\_title="Period",  # (4)!
...     yaxis\_title="Sharpe",
... )
>>> is\_best\_perf.vbt.select\_levels("period").vbt.plot(  # (5)!
...     trace\_kwargs=dict(
...         name="Best", 
...         line=dict(color="limegreen", dash="dash")
...     ), 
...     fig=fig  # (6)!
... )
>>> bl\_perf.vbt.plot(
...     trace\_kwargs=dict(
...         name="Baseline", 
...         line=dict(color="orange", dash="dash")
...     ), 
...     fig=fig
... )
>>> oos\_perf.vbt.select\_levels("period").vbt.plot(
...     trace\_kwargs=dict(
...         name="Test", 
...         line=dict(color="orangered")
...     ), 
...     fig=fig
... )
>>> fig.show()
\`\`\`

1. Use \[GenericAccessor.boxplot\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.boxplot).
2. This Series has many levels; we need to choose which level(s) to aggregate by.
3. This argument controls the appearance of the trace (see \[plotly.graph\_objects.Box\](https://plotly.github.io/plotly.py-docs/generated/plotly.graph\_objects.Box.html)).
4. The first plotting method will create a Plotly figure and set it up, so pass layout settings such as axis labels here.
5. Use \[GenericAccessor.plot\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.plot).
6. Make sure to pass the figure to plot the new trace on, otherwise it will create a new figure.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/cv/example.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/cv/example.dark.svg#only-dark){: .iimg loading=lazy }

Here is how to interpret the plot above.

The green line tracks the performance of the best parameter combination in each IS set. The fact that it
touches the highest point in each box shows that our best-parameter selection algorithm works correctly.
The dashed orange line represents the performance of the "buy-and-hold" strategy during each period as
the baseline. The red line shows the test performance; it starts at the second range and corresponds to
the parameter combination that delivered the best result in the previous period (that is, the previous
green dot).

The semi-transparent blue boxes show the distribution of Sharpe ratios during the IS (training) periods,
meaning each box summarizes 990 parameter combinations tested in each optimization period. There is no
box on the far right because the last period is an OOS (test) period. For example, period \`6\` (which is
the seventh period, since counting starts at 0) includes all Sharpe ratios from \`1.07\` to \`4.64\`.
That likely means there was an upward trend during that period. Here is the proof:

\`\`\`pycon
>>> is\_perf\_split6 = is\_perf.xs(6, level="split")  # (1)!
>>> is\_perf\_split6.describe()
count    990.000000
mean       3.638821
std        0.441206
min        1.073553
25%        3.615566
50%        3.696611
75%        3.844124
max        4.644594
dtype: float64

>>> first\_left\_bound = period\_ranges.loc\[6, "start"\]
>>> first\_right\_bound = period\_ranges.loc\[6, "end"\]
>>> data\[first\_left\_bound : first\_right\_bound\].plot().show()  # (2)!
\`\`\`

1. Select the values for the \`split\` level equal to \`6\` and collect statistics for them.
2. Plot the candlestick chart for that period to confirm visually.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/cv/example\_candlestick.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/cv/example\_candlestick.dark.svg#only-dark){: .iimg loading=lazy }

No matter which parameter combination we select for that time, the Sharpe ratio remains relatively high
and could give us a false sense of strategy performance. To make sure this is not the case, we need to
compare the test performance to other points. That's the main reason we drew lines over the
\[box plot\](https://en.wikipedia.org/wiki/Box\_plot). For example, we can see that for period \`6\`, both
the baseline and test performances are below the first quartile (or 25th percentile). They are worse
than at least 75% of the parameter combinations tested during that time range:

\`\`\`pycon
>>> oos\_perf.xs(6, level="period")
split  fast\_window  slow\_window
5      20           27             2.567751
dtype: float64

>>> is\_perf\_split6.quantile(0.25)  # (1)!
3.615566166097048
\`\`\`

1. 25% of parameter combinations have a Sharpe ratio below that value, including our
parameter combination used for testing.

The chart gives us mixed feelings: on the one hand, the chosen parameter combination outperforms most of
the combinations tested during 5 different time periods. On the other hand, it fails to beat even the
lowest-performing 25% of parameter combinations in 3 other periods. In defense of our strategy, the
number of splits is relatively low. Most statisticians agree that at least 100 samples are needed for
meaningful results, so this analysis offers only a small glimpse into the true performance of the
SMA crossover.

So, how can we make all of this simpler?

\[:material-language-python: Python code\](https://vectorbt.pro/pvt\_6d1b3986/assets/jupytext/tutorials/cross-validation/index.py.txt){ .md-button target="blank\_" }
\[:material-notebook-outline: Notebook\](https://github.com/polakowo/vectorbt.pro/blob/main/notebooks/CrossValidation.ipynb){ .md-button target="blank\_" }