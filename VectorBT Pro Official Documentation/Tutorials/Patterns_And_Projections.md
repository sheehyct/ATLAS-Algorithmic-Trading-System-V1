\---
title: Patterns
description: Learn about identifying patterns using VectorBT PRO
icon: material/star-shooting-outline
---

# :material-star-shooting-outline: Patterns

Patterns help bring order to what may seem like chaos. They appear throughout nature—such as circles 
in road signs or rectangles in windows and doors. Just as children gradually learn to navigate an 
entirely unknown environment by recognizing regularities, participants in financial markets must also 
learn to operate within their complex, ever-changing surroundings. Much like children who rely on 
parents, teachers, or even Google for guidance, we have a valuable tool to aid our understanding: 
quantitative analysis.

In finance, patterns are distinctive formations formed by price movements on a chart and form 
the foundation of technical analysis. They can provide clues about what prices might do next, based 
on past behavior. For example, we can search for all previous occurrences of the same pattern we see 
today to analyze how events unfolded each time, enabling more nuanced trading decisions that consider 
multiple possibilities. Patterns are particularly valuable for identifying transition points between 
rising and falling trends, which is key to successful trade entries and exits. However, patterns do 
not guarantee future results, nor do they last forever. Unlike the real world, where structure and 
behavior tend to be consistent, financial markets are dominated by noise and 
\[false positives\](https://en.wikipedia.org/wiki/False\_positives\_and\_false\_negatives) that arise from 
intense interactions among people, systems, and other entities. Discovering something that performs 
just slightly better than random in a specific market regime is already an accomplishment—an 
exciting game with probabilities.

Let's walk through a simple use case where we want to identify the 
\[Double Top\](https://www.investopedia.com/terms/d/doubletop.asp) pattern.
We will start by pulling two years of daily \`BTCUSDT\` history as our baseline data:

\`\`\`pycon
>>> from vectorbtpro import \*

>>> data = vbt.BinanceData.pull(
...     "BTCUSDT", 
...     start="2020-06-01 UTC", 
...     end="2022-06-01 UTC"
... )
>>> data.plot().show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/data.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/data.dark.svg#only-dark){: .iimg loading=lazy }

A quick visual inspection suggests the most apparent occurrence of this pattern was between October
and December 2021:

\`\`\`pycon
>>> data\_window = data.loc\["2021-09-25":"2021-11-25"\]
>>> data\_window.plot(plot\_volume=False).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/data\_window.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/data\_window.dark.svg#only-dark){: .iimg loading=lazy }

As humans, we can easily detect patterns visually in data. But how can we accomplish this
programmatically, where everything is represented by numbers? It would be costly, unnecessary, and
likely ineffective to train a \[DNN\](https://en.wikipedia.org/wiki/Deep\_learning) for such a simple
task. Following the principle "the simpler the algorithm, the better" for noisy data, we should
design an algorithm that tackles the problem using simple loops and basic math.

Since each pattern is matched against a single feature of the data, we will use the
\[typical price\](https://en.wikipedia.org/wiki/Typical\_price):

\`\`\`pycon
>>> price\_window = data\_window.hlc3
>>> price\_window.vbt.plot().show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/hlc3.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/hlc3.dark.svg#only-dark){: .iimg loading=lazy }

Next, let's design the pattern. Price patterns are identified using a series of lines or curves.
For example, the "Double Top" pattern can be represented by the following array:

\`\`\`pycon
>>> pattern = np.array(\[1, 2, 3, 2, 3, 2\])
>>> pd.Series(pattern).vbt.plot().show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/double\_top\_pattern.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/double\_top\_pattern.dark.svg#only-dark){: .iimg loading=lazy }

It is important to note that the length and absolute values in the pattern definition do not matter.
Whether the pattern scales from 1 to 3 or 1 to 60, it will be stretched horizontally and vertically to
align with the corresponding price data. What matters for computation is the relative positioning of
each point. For instance, the first point \`2\` comes exactly in the middle between \`1\` and \`3\`,
meaning if the asset rises in price to match the second point, it should ideally make the same move
to reach the first peak. Furthermore, since some values like \`2\` and \`3\` repeat, we do not expect the
price at those points to deviate significantly, which helps define support and resistance levels.

Another key rule relates to the horizontal structure of the pattern: regardless of the value at any
given point, the location (timing) of a point is always relative to its neighboring points. For
example, if the first point was matched on \`2020-01-01\` and the second on \`2020-01-03\`, the third
point should be matched on \`2020-01-06\`. If any part of the pattern takes longer to form, changing
the horizontal structure, a match becomes less likely.

## Interpolation

Once we have defined our pattern, we need to ensure that both the pattern and the price array are the
same length. In image processing, increasing the size of an image involves reconstructing the image
by \[interpolating\](https://en.wikipedia.org/wiki/Interpolation) new pixels, while reducing the size
involves \[downsampling\](https://en.wikipedia.org/wiki/Downsampling\_(signal\_processing)) the existing
pixels. In pattern processing, the approach is similar, but we work with one-dimensional arrays
instead of two-dimensional ones. We also prefer interpolation (stretching) over downsampling
(shrinking) to avoid losing information. This means that if the price array is shorter than the
pattern, it should be stretched to match the pattern's length, rather than compressing the pattern to
fit the price.

There are four main interpolation modes in pattern processing: linear, nearest neighbor, discrete,
and mixed. All of these are implemented using the Numba-compiled function
\[interp\_resize\_1d\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/patterns/#vectorbtpro.generic.nb.patterns.interp\_resize\_1d\_nb),
which takes an array, a target size, and an interpolation mode of type
\[InterpMode\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/enums/#vectorbtpro.generic.enums.InterpMode). The implementation is very
efficient: it iterates through the array only once and does not require creating extra arrays except
for the final output.

### Linear

The linear interpolation algorithm estimates new values by connecting two adjacent known values with a
straight line (see \[here\](https://scientific-python.readthedocs.io/en/latest/notebooks\_rst/1\_Interpolation/1D\_interpolation.html#linear-interpolation)
for an illustration).

Let's stretch our pattern array to 10 points:

\`\`\`pycon
>>> resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...     pattern, 10, vbt.enums.InterpMode.Linear
... )
>>> resized\_pattern
array(\[1.        , 1.55555556, 2.11111111, 2.66666667, 2.77777778,
       2.22222222, 2.33333333, 2.88888889, 2.55555556, 2.        \])
\`\`\`

This mode works best when the target size is close to \`2 \* n - 1\`, where \`n\` is the original array 
size. In this case, the characteristics of the resized array closely match those of the original. 
Otherwise, the relationship between points may be distorted, unless the target size is significantly 
larger than the original. This is best illustrated below, where we resize the array to lengths of 7, 11, 
and 30 points:

\`\`\`pycon
>>> def plot\_linear(n):
...     resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...         pattern, n, vbt.enums.InterpMode.Linear
...     )
...     return pd.Series(resized\_pattern).vbt.plot()
\`\`\`

=== "7 points"

    \`\`\`pycon
    >>> plot\_linear(7).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/linear\_7.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/linear\_7.dark.svg#only-dark){: .iimg loading=lazy }

=== "11 points"

    \`\`\`pycon
    >>> plot\_linear(11).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/linear\_11.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/linear\_11.dark.svg#only-dark){: .iimg loading=lazy }

=== "30 points"

    \`\`\`pycon
    >>> plot\_linear(30).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/linear\_30.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/linear\_30.dark.svg#only-dark){: .iimg loading=lazy }

Why does the first graph look so "ugly"? This happens because the algorithm maintains the same
distance between each pair of points in the resized array. To stretch a 6-point array to 7 points,
the algorithm splits the graph of the 6-point array into 7 parts and selects the value at the midpoint
of each part, like this:

\`\`\`pycon
>>> resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...     pattern, 7, vbt.enums.InterpMode.Linear
... )
>>> ratio = (len(pattern) - 1) / (len(resized\_pattern) - 1)
>>> new\_points = np.arange(len(resized\_pattern)) \* ratio
>>> fig = pd.Series(pattern).vbt.plot()
>>> pd.Series(resized\_pattern, index=new\_points).vbt.scatterplot(fig=fig)
>>> fig.show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/linear\_7\_scatter.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/linear\_7\_scatter.dark.svg#only-dark){: .iimg loading=lazy }

As you can see, linear interpolation is about selecting a specific number of equidistant values from
the original array. The more points there are, the better the result. The main issue is that when the
target size is suboptimal, the scale of the resized array changes. In the example above, the pattern
is distorted and the original link between points with a value of \`2\` is lost. However, other
interpolation algorithms may perform better in these cases.

### Nearest

The nearest neighbor algorithm selects the value of the closest point and does not consider other
values at all (see \[here\](https://scientific-python.readthedocs.io/en/latest/notebooks\_rst/1\_Interpolation/1D\_interpolation.html#nearest-aka-piecewise-interpolation)
for an illustration). With this approach, the resized array consists only of values from the original
array, so there are no intermediate floating-point values:

\`\`\`pycon
>>> resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...     pattern, 10, vbt.enums.InterpMode.Nearest
... )
>>> resized\_pattern
array(\[1., 2., 2., 3., 3., 2., 2., 3., 3., 2.\])
\`\`\`

!!! info
    For consistency, the resized array is always floating-point.

Below are resized arrays for different target sizes:

\`\`\`pycon
>>> def plot\_nearest(n):
...     resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...         pattern, n, vbt.enums.InterpMode.Nearest
...     )
...     return pd.Series(resized\_pattern).vbt.plot()
\`\`\`

=== "7 points"

    \`\`\`pycon
    >>> plot\_nearest(7).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/nearest\_7.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/nearest\_7.dark.svg#only-dark){: .iimg loading=lazy }

=== "11 points"

    \`\`\`pycon
    >>> plot\_nearest(11).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/nearest\_11.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/nearest\_11.dark.svg#only-dark){: .iimg loading=lazy }

=== "30 points"

    \`\`\`pycon
    >>> plot\_nearest(30).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/nearest\_30.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/nearest\_30.dark.svg#only-dark){: .iimg loading=lazy }

As you can see, each graph is a step curve with horizontal and vertical lines. Because of this, it can
be challenging to use when we expect the price to change smoothly rather than jump abruptly. This
interpolation mode should only be used if the original array is granular enough to smooth out the
transitions between local extrema.

!!! hint
    The \`2 \* n - 1\` guideline does not apply to this mode.

### Discrete

The discrete interpolation algorithm selects a value if it is closer to the target position than the
other values; if not, it assigns a value of NaN. This mode ensures that each value from the original
array appears only once in the output, but it may still change their temporal distribution. It is best
used in scenarios where transitions between points are not important.

\`\`\`pycon
>>> resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...     pattern, 10, vbt.enums.InterpMode.Discrete
... )
>>> resized\_pattern
array(\[ 1., nan,  2., nan,  3.,  2., nan,  3., nan,  2.\])
\`\`\`

Here is a comparison of arrays resized to different target sizes:

\`\`\`pycon
>>> def plot\_discrete(n):
...     resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...         pattern, n, vbt.enums.InterpMode.Discrete
...     )
...     return pd.Series(resized\_pattern).vbt.plot(
...         trace\_kwargs=dict(
...             line=dict(dash="dot"),
...             connectgaps=True
...         )
...     )
\`\`\`

=== "7 points"

    \`\`\`pycon
    >>> plot\_discrete(7).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/discrete\_7.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/discrete\_7.dark.svg#only-dark){: .iimg loading=lazy }

=== "11 points"

    \`\`\`pycon
    >>> plot\_discrete(11).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/discrete\_11.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/discrete\_11.dark.svg#only-dark){: .iimg loading=lazy }

=== "30 points"

    \`\`\`pycon
    >>> plot\_discrete(30).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/discrete\_30.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/discrete\_30.dark.svg#only-dark){: .iimg loading=lazy }

Each graph contains exactly 6 points that have been mapped to a new interval by aiming to keep the
distance between them as equal as possible. Similar to linear interpolation, this mode also gives the
best results when the target size is \`2 \* n - 1\`, while other sizes distort the temporal distribution
of the points. However, unlike linear interpolation, this mode preserves the absolute values of the
original array, so the point \`2\` is always guaranteed to be midway between points \`1\` and \`3\`.

### Mixed

The mixed interpolation algorithm combines the linear and discrete interpolation algorithms. First, it
applies the discrete interpolator, and if the value is NaN, it then applies the linear interpolator.
This approach ensures that each value from the original array is included at least once to preserve
the original scale, while intermediate values are filled using linear interpolation—giving us the best
of both worlds.

\`\`\`pycon
>>> resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...     pattern, 10, vbt.enums.InterpMode.Mixed
... )
>>> resized\_pattern
array(\[1.        , 1.55555556, 2.        , 2.66666667, 3.        ,
       2.        , 2.33333333, 3.        , 2.55555556, 2.        \])
\`\`\`

Let's show how the mixed approach "fixes" the scale issue of the linear approach:

\`\`\`pycon
>>> def plot\_mixed(n):
...     lin\_resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...         pattern, n, vbt.enums.InterpMode.Linear
...     )
...     mix\_resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...         pattern, n, vbt.enums.InterpMode.Mixed
...     )
...     fig = pd.Series(lin\_resized\_pattern, name="Linear").vbt.plot()
...     pd.Series(mix\_resized\_pattern, name="Mixed").vbt.plot(fig=fig)
...     return fig
\`\`\`

=== "7 points"

    \`\`\`pycon
    >>> plot\_mixed(7).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/mixed\_7.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/mixed\_7.dark.svg#only-dark){: .iimg loading=lazy }

=== "11 points"

    \`\`\`pycon
    >>> plot\_mixed(11).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/mixed\_11.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/mixed\_11.dark.svg#only-dark){: .iimg loading=lazy }

=== "30 points"

    \`\`\`pycon
    >>> plot\_mixed(30).show()
    \`\`\`

    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/mixed\_30.light.svg#only-light){: .iimg loading=lazy }
    !\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/mixed\_30.dark.svg#only-dark){: .iimg loading=lazy }

!!! info
    As you may have noticed, the last pattern line on the graph is not completely straight.
    This is because mixed interpolation uses both linear and discrete approaches to retain the original
    scale. Producing a perfectly straight line would require passing through the data multiple times, and
    for performance reasons, we chose efficiency over complete visual smoothness.

We have restored the original connections between the various points, so this algorithm should be 
(and is) the default choice for interpolation without gaps.

\`\`\`pycon
>>> resized\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...     pattern, len(price\_window), vbt.enums.InterpMode.Mixed
... )
>>> resized\_pattern.shape
(62,)
\`\`\`

## Rescaling

After bringing the pattern and the price to the same length, we also need to match their scales to make 
them comparable. To do this, we compute the minimum and maximum of both the pattern and the price, then 
rescale the pattern to match the scale of the price. We can use the Numba-compiled function 
\[rescale\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/array\_/#vectorbtpro.utils.array\_.rescale\_nb), which takes an array, 
the scale of the array, and the target scale:

\`\`\`pycon
>>> pattern\_scale = (resized\_pattern.min(), resized\_pattern.max())
>>> price\_window\_scale = (price\_window.min(), price\_window.max())
>>> rescaled\_pattern = vbt.utils.array\_.rescale\_nb(
...     resized\_pattern, pattern\_scale, price\_window\_scale
... )
>>> rescaled\_pattern = pd.Series(rescaled\_pattern, index=price\_window.index)
\`\`\`

Now we can finally overlay the pattern on top of the price:

\`\`\`pycon
>>> fig = price\_window.vbt.plot()
>>> rescaled\_pattern.vbt.plot(
...     trace\_kwargs=dict(
...         fill="tonexty", 
...         fillcolor="rgba(255, 0, 0, 0.25)"
...     ), 
...     fig=fig
... )
>>> fig.show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/rescaled\_pattern.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/rescaled\_pattern.dark.svg#only-dark){: .iimg loading=lazy }

### Rebasing

Another way to match the scales of both arrays is rebasing. When rebasing, the first value of both arrays
is made equal, and all other values are rescaled based on their relative distance from the starting point.
This is useful if your pattern should enforce a specific percentage change from the starting value.
For example, let's ensure a relative distance of 60% between the peak and the starting point:

\`\`\`pycon
>>> pct\_pattern = np.array(\[1, 1.3, 1.6, 1.3, 1.6, 1.3\])
>>> resized\_pct\_pattern = vbt.nb.interp\_resize\_1d\_nb(
...     pct\_pattern, len(price\_window), vbt.enums.InterpMode.Mixed
... )
>>> rebased\_pattern = resized\_pct\_pattern / resized\_pct\_pattern\[0\]
>>> rebased\_pattern \*= price\_window.values\[0\]
>>> rebased\_pattern = pd.Series(rebased\_pattern, index=price\_window.index)
>>> fig = price\_window.vbt.plot()
>>> rebased\_pattern.vbt.plot(
...     trace\_kwargs=dict(
...         fill="tonexty", 
...         fillcolor="rgba(255, 0, 0, 0.25)"
...     ), 
...     fig=fig
... )
>>> fig.show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/rebased\_pattern.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/rebased\_pattern.dark.svg#only-dark){: .iimg loading=lazy }

## Fitting

Interpolation and rescaling are required to bring both the pattern and the price to the same
length and scale so they can be compared and combined as regular NumPy arrays. Rather than performing
the above steps manually, let's use a special function that does the entire job for us:
\[fit\_pattern\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/patterns/#vectorbtpro.generic.nb.patterns.fit\_pattern\_nb).

\`\`\`pycon
>>> new\_pattern, \_ = vbt.nb.fit\_pattern\_nb(
...     price\_window.values,  # (1)!
...     pct\_pattern,  # (2)!
...     interp\_mode=vbt.enums.InterpMode.Mixed,
...     rescale\_mode=vbt.enums.RescaleMode.Rebase  # (3)!
... )
\`\`\`

1. The first argument is a price array. Since Numba does not recognize Pandas objects,
extract the NumPy array from your Series.
2. The second argument is a pattern array. You can pass this as-is, since it is already in NumPy format.
3. See \[RescaleMode\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/enums/#vectorbtpro.generic.enums.RescaleMode).

What does \`\_\` mean? The function actually returns two arrays: one for the pattern and one for the maximum
error (see \[Max error\](#max-error)). Since we do not need the maximum error array, we ignore it by using
\`\_\` instead of a variable name. Let's check that the automatically generated array matches the manually
generated one:

\`\`\`pycon
>>> np.testing.assert\_array\_equal(new\_pattern, rebased\_pattern)
\`\`\`

No errors are raised—both arrays are identical!

## Similarity

Now that our arrays are perfectly comparable, how do we calculate their similarity? The algorithm is
simple: compute the absolute, element-wise differences between the two arrays and add them up (also known
as \[Mean Absolute Error\](https://en.wikipedia.org/wiki/Mean\_absolute\_error) or MAE). At the same time,
compute the maximum possible absolute, element-wise differences and add those up. The maximum distance is
calculated relative to the global minimum and maximum value. Finally, divide both totals and subtract from
1 to get the similarity score, which ranges between 0 and 1:

\`\`\`pycon
>>> abs\_distances = np.abs(rescaled\_pattern - price\_window.values)
>>> mae = abs\_distances.sum()
>>> max\_abs\_distances = np.column\_stack((
...     (price\_window.max() - rescaled\_pattern), 
...     (rescaled\_pattern - price\_window.min())
... )).max(axis=1)
>>> max\_mae = max\_abs\_distances.sum()
>>> similarity = 1 - mae / max\_mae
>>> similarity
0.8726845123416802
\`\`\`

To penalize large distances and make pattern detection more "strict," you can switch the distance measure
to the root of the sum of squared differences (also called
\[Root Mean Squared Error\](https://en.wikipedia.org/wiki/Root-mean-square\_deviation) or RMSE):

\`\`\`pycon
>>> quad\_distances = (rescaled\_pattern - price\_window.values) \*\* 2
>>> rmse = np.sqrt(quad\_distances.sum())
>>> max\_quad\_distances = np.column\_stack((
...     (price\_window.max() - rescaled\_pattern), 
...     (rescaled\_pattern - price\_window.min())
... )).max(axis=1) \*\* 2
>>> max\_rmse = np.sqrt(max\_quad\_distances.sum())
>>> similarity = 1 - rmse / max\_rmse
>>> similarity
0.8484851233108504
\`\`\`

As another option, you could also remove the root from the equation above and calculate just the sum of
squared differences (also known as \[Mean Squared Error\](https://en.wikipedia.org/wiki/Mean\_squared\_error) or MSE):

\`\`\`pycon
>>> quad\_distances = (rescaled\_pattern - price\_window.values) \*\* 2
>>> mse = quad\_distances.sum()
>>> max\_quad\_distances = np.column\_stack((
...     (price\_window.max() - rescaled\_pattern), 
...     (rescaled\_pattern - price\_window.min())
... )).max(axis=1) \*\* 2
>>> max\_mse = max\_quad\_distances.sum()
>>> similarity = 1 - mse / max\_mse
>>> similarity
0.9770432421418718
\`\`\`

!!! note
    Since the maximum distance is now the absolute maximum distance squared, the similarity
    will often exceed 90%. Do not forget to adjust your thresholds accordingly.

If you are not excited about writing the code above each time you need to measure similarity 
between two arrays, do not worry! As with everything, there is a convenient Numba-compiled function 
\[pattern\_similarity\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/patterns/#vectorbtpro.generic.nb.patterns.pattern\_similarity\_nb), 
which combines all the steps above to produce a single score. This function accepts many options
for interpolation, rescaling, and distance measurement, and runs in 
\[O(n)\](https://en.wikipedia.org/wiki/Time\_complexity) time without creating any new arrays. 
Due to its exceptional efficiency and Numba compilation, you can run this function millions of times in 
a fraction of a second :fire: The only difference from our approach above is that it rescales the price array 
to the pattern scale, not the other way around (which we did for plotting purposes).

Let's see the power of this function by replicating our pipeline above:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(price\_window.values, pattern)
0.8726845123416802
\`\`\`

This produces the same score as our manual calculation :eyes:

Now, let's calculate the similarity score for \`pct\_pattern\` with rebasing:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     pct\_pattern, 
...     rescale\_mode=vbt.enums.RescaleMode.Rebase  # (1)!
... )
0.8647140967291362
\`\`\`

1. See \[RescaleMode\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/enums/#vectorbtpro.generic.enums.RescaleMode)

Let's get the similarity score by interpolating the pattern using nearest-neighbor interpolation,
rebasing, and RMSE:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     pct\_pattern, 
...     interp\_mode=vbt.enums.InterpMode.Nearest,  # (1)!
...     rescale\_mode=vbt.enums.RescaleMode.Rebase,
...     distance\_measure=vbt.enums.DistanceMeasure.RMSE  # (2)!
... )
0.76151009787845
\`\`\`

1. See \[InterpMode\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/enums/#vectorbtpro.generic.enums.InterpMode).
2. See \[DistanceMeasure\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/enums/#vectorbtpro.generic.enums.DistanceMeasure).

Often, we are not only interested in getting the similarity measure but also in visualizing and
debugging the pattern. In this case, we can call the accessor method
\[GenericSRAccessor.plot\_pattern\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericSRAccessor.plot\_pattern),
which reconstructs the similarity calculation and visually displays various artifacts. To produce an
accurate plot, provide the same arguments as you did to the similarity calculation function. Our last
example produced a similarity of 75%. Let's visualize the fit:

\`\`\`pycon
>>> price\_window.vbt.plot\_pattern(
...     pct\_pattern, 
...     interp\_mode="nearest",  # (1)!
...     rescale\_mode="rebase",
...     fill\_distance=True
... ).show()
\`\`\`

1. Here, you can provide each option as a string.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/plot\_pattern.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/plot\_pattern.dark.svg#only-dark){: .iimg loading=lazy }

We can see that the largest discrepancy appears at the valley in the middle. The interpolated pattern
expects the price to dip deeper than it actually does. Let's add 15% to that point to increase the
similarity:

\`\`\`pycon
>>> adj\_pct\_pattern = np.array(\[1, 1.3, 1.6, 1.45, 1.6, 1.3\])
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     adj\_pct\_pattern, 
...     interp\_mode=vbt.enums.InterpMode.Nearest,
...     rescale\_mode=vbt.enums.RescaleMode.Rebase,
...     distance\_measure=vbt.enums.DistanceMeasure.RMSE
... )
0.8086016654243109
\`\`\`

Here is how the discrete interpolation applied to the new pattern looks:

\`\`\`pycon
>>> price\_window.vbt.plot\_pattern(
...     adj\_pct\_pattern, 
...     interp\_mode="discrete",
...     rescale\_mode="rebase",
... ).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/plot\_pattern\_discrete.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/plot\_pattern\_discrete.dark.svg#only-dark){: .iimg loading=lazy }

The pattern trace appears as a scatter plot rather than a line plot because the similarity score is
calculated only at those points, and the grayed out points are ignored. If we calculate the similarity
score again, we see a higher value than before because the pattern at those points matches the price
more closely:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     adj\_pct\_pattern, 
...     interp\_mode=vbt.enums.InterpMode.Discrete,
...     rescale\_mode=vbt.enums.RescaleMode.Rebase,
...     distance\_measure=vbt.enums.DistanceMeasure.RMSE
... )
0.8719692914480557
\`\`\`

### Relative

Since the price is not static and may change significantly during the period of comparison, it is better to
calculate the relative distance (error) instead of the absolute distance. For example, if the first price
point is \`10\` and the last price point is \`1000\`, the distance to the latter would have a much greater
impact on the similarity score than the distance to the former. Let's re-calculate the score manually and
automatically using relative distances:

\`\`\`pycon
>>> abs\_pct\_distances = abs\_distances / rescaled\_pattern
>>> pct\_mae = abs\_pct\_distances.sum()
>>> max\_abs\_pct\_distances = max\_abs\_distances / rescaled\_pattern
>>> max\_pct\_mae = max\_abs\_pct\_distances.sum()
>>> similarity = 1 - pct\_mae / max\_pct\_mae
>>> similarity
0.8732697724295595

>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     pct\_pattern, 
...     error\_type=vbt.enums.ErrorType.Relative  # (1)!
... )
0.8732697724295594
\`\`\`

1. See \[ErrorType\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/enums/#vectorbtpro.generic.enums.ErrorType).

The difference is not very large in this scenario, but here is what happens when the price moves sharply:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     np.array(\[10, 30, 100\]),
...     np.array(\[1, 2, 3\]),
...     error\_type=vbt.enums.ErrorType.Absolute
... )
0.8888888888888888

>>> vbt.nb.pattern\_similarity\_nb(
...     np.array(\[10, 30, 100\]),
...     np.array(\[1, 2, 3\]),
...     error\_type=vbt.enums.ErrorType.Relative
... )
0.9575911789652247
\`\`\`

In both examples, the pattern has been rescaled to \`\[10, 55, 100\]\` using the min-max rescaler (which is the
default). In the first example, the normalized error is \`abs(30 - 55) / (100 - 30) = 0.36\`, while in the
second example, the normalized error is \`(abs(30 - 55) / 55) / ((100 - 30) / 30) = 0.19\`, which also takes
into account the volatility of the price.

### Inverse

You can also invert the pattern internally:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(price\_window.values, pattern, invert=True)
0.32064009029620244

>>> price\_window.vbt.plot\_pattern(pattern, invert=True).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/inverted\_pattern.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/inverted\_pattern.dark.svg#only-dark){: .iimg loading=lazy }

!!! note
    This is not the same as simply inverting the score.

To produce the inverted pattern manually:

\`\`\`pycon
>>> pattern.max() + pattern.min() - pattern
array(\[3, 2, 1, 2, 1, 2\])
\`\`\`

### Max error

Sometimes, you may want to define patterns as "corridors" within which the price should move.
If any of the corridor points are violated, you can either set the distance at that point to the
maximum distance (\`max\_error\_strict=False\`), or set the entire similarity to NaN
(\`max\_error\_strict=True\`). Such a corridor is referred to as "maximum error". This error can be
provided through the array-like argument \`max\_error\`, which should be defined in the same way as the
pattern. It mostly needs to have the same length and scale as the pattern.

For example, if you choose min-max rescaling and the pattern is defined from \`1\` to \`6\`, a maximum
error of \`0.5\` would be \`0.5 / (6 - 1) = 0.1\`, that is, 10% of the pattern's scale. Let's check the
similarity of our original pattern without and with a corridor of \`0.5\`:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     pattern,
... )
0.8726845123416802

>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     pattern, 
...     max\_error=np.array(\[0.5, 0.5, 0.5, 0.5, 0.5, 0.5\]),
... )
0.8611332262389184
\`\`\`

Since \`max\_error\` is a flexible argument, you can also provide it as a zero-dimensional or
one-dimensional array with one value, which will be applied to each point in the pattern:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     pattern, 
...     max\_error=np.array(\[0.5\]),  # (1)!
... )
0.8611332262389184
\`\`\`

1. The argument cannot be provided as a constant (\`0.5\`). It must always be an array.

The similarity score has decreased, meaning some corridor points were violated.
Let's visualize the whole thing to see the exact points:

\`\`\`pycon
>>> price\_window.vbt.plot\_pattern(
...     pattern, 
...     max\_error=0.5  # (1)!
... ).show()
\`\`\`

1. You can provide constants here.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/max\_error.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/max\_error.dark.svg#only-dark){: .iimg loading=lazy }

We see two points that were violated, so their distance to the price was set to the maximum
possible distance, which lowered the similarity. If we enable strict mode, the similarity becomes NaN
to let the user know that it did not pass the test:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     pattern, 
...     max\_error=np.array(\[0.5\]),
...     max\_error\_strict=True
... )
nan
\`\`\`

If you are interested in relative distances using \`ErrorType.Relative\`, the maximum error should
be provided as a percentage change:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     pattern, 
...     max\_error=np.array(\[0.1\]),  # (1)!
...     error\_type=vbt.enums.ErrorType.Relative
... )
0.8548520433078988

>>> price\_window.vbt.plot\_pattern(
...     pattern, 
...     max\_error=0.1,
...     error\_type="relative"
... ).show()
\`\`\`

1. Corridor of 10% at any point.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/max\_error\_relative.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/max\_error\_relative.dark.svg#only-dark){: .iimg loading=lazy }

The same applies for rescaling using rebasing mode, where each error, regardless of error type, should
be given as a percentage change. For example, if the current pattern value has been mapped to a price of
\`12000\` and the maximum error is \`0.1\`, the corridor will cover all values from \`12000 \* 0.9 = 10800\`
to \`12000 \* 1.1 = 13200\`. Let's allow deviations for the adjusted percentage pattern of no more than
20% at the first level, 10% at the second level, and 5% at the third level:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     adj\_pct\_pattern, 
...     rescale\_mode=vbt.enums.RescaleMode.Rebase,
...     max\_error=np.array(\[0.2, 0.1, 0.05, 0.1, 0.05, 0.1\]),
...     max\_error\_strict=True
... )
nan

>>> price\_window.vbt.plot\_pattern(
...     adj\_pct\_pattern, 
...     rescale\_mode="rebase",
...     max\_error=np.array(\[0.2, 0.1, 0.05, 0.1, 0.05, 0.1\])
... ).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/max\_error\_rebase.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/max\_error\_rebase.dark.svg#only-dark){: .iimg loading=lazy }

As shown, some points fall outside the corridor. If we add an additional 5% to all points,
the pattern passes the test easily:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     adj\_pct\_pattern, 
...     rescale\_mode=vbt.enums.RescaleMode.Rebase,
...     max\_error=np.array(\[0.2, 0.1, 0.05, 0.1, 0.05, 0.1\]) + 0.05,
...     max\_error\_strict=True
... )
0.8789689066239321
\`\`\`

#### Interpolation

Is there a way to provide the maximum error discretely? In other words, can we force the function
to adhere to the corridor only at certain points, rather than gradually at all points? By default,
the maximum error is interpolated in the same way as the pattern (linearly in our case).
To make the maximum error array interpolate differently, provide a different mode as
\`max\_error\_interp\_mode\`. For example, let's require only the peak points to be within the corridor of 10%.
For this, use the discrete interpolation mode and set all intermediate points to NaN:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     adj\_pct\_pattern, 
...     rescale\_mode=vbt.enums.RescaleMode.Rebase,
...     max\_error=np.array(\[np.nan, np.nan, 0.1, np.nan, 0.1, np.nan\]),
...     max\_error\_interp\_mode=vbt.enums.InterpMode.Discrete,
...     max\_error\_strict=True
... )
0.8789689066239321

>>> price\_window.vbt.plot\_pattern(
...     adj\_pct\_pattern, 
...     rescale\_mode="rebase",
...     max\_error=np.array(\[np.nan, np.nan, 0.1, np.nan, 0.1, np.nan\]),
...     max\_error\_interp\_mode="discrete"
... ).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/max\_error\_discrete.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/max\_error\_discrete.dark.svg#only-dark){: .iimg loading=lazy }

Even though the scatter points of the maximum error are connected by a greyed-out line, the price is only
required to be between each pair of purple points, not between those lines.

#### Max distance

Final question: is there a way to adjust the maximum distance? Yes! You can use the maximum error as the
maximum distance by enabling \`max\_error\_as\_maxdist\`. This has the following effect:
the smaller the maximum distance at any point, the more the price volatility at that point
affects the similarity. Let's compare our original pattern without and with a maximum distance cap
of \`0.5\` (10% of the scale):

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(price\_window.values, pattern)
0.8726845123416802

>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, 
...     pattern, 
...     max\_error=np.array(\[0.5\]),
...     max\_error\_as\_maxdist=True
... )
0.6193594883412921
\`\`\`

This method introduces a penalty for increased price volatility.

!!! note
    You can also set a different maximum distance at different points in the pattern.
    Keep in mind that points with a larger maximum distance will have more weight in the
    similarity calculation than points with a smaller maximum distance. For example, if there are two points
    with maximum distances of \`100\` and \`1\` respectively, even with a perfect match at the second point,
    the similarity would be determined mostly by the distance at the first point.

### Further filters

When matching a large number of price windows against a pattern, we may want to skip windows
where the volatility is either too low or too high. You can do this by setting the arguments
\`min\_pct\_change\` and \`max\_pct\_change\`, respectively:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, pattern, max\_pct\_change=0.3
... )
nan
\`\`\`

An added benefit is improved performance: if the test fails, the price window is only traversed once
to get the minimum and maximum value.

We can also filter out similarity scores that fall below a predefined threshold.
For example, to set the minimum similarity to 90%:

\`\`\`pycon
>>> vbt.nb.pattern\_similarity\_nb(
...     price\_window.values, pattern, min\_similarity=0.9
... )
nan
\`\`\`

!!! hint
    Do not worry about NaNs, they simply mean "didn't pass some tests, should be ignored during analysis".

Setting a similarity threshold also improves performance: if the algorithm detects that the threshold can
no longer be reached, even if the remaining points matched perfectly, it will stop and set the final
score to NaN. Depending on the threshold, this can make the computation about 30% faster on average.

## Rolling similarity

Now that we have learned the theory behind pattern recognition, it is time to put it into practice.
To search for a pattern within a price space, we need to roll a window across that space.
This can be done using the accessor method
\[GenericAccessor.rolling\_pattern\_similarity\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.rolling\_pattern\_similarity),
which accepts the same arguments as before, plus the window length to roll.
If you set the window length to \`None\`, it will default to the length of the pattern array.

Let's roll a window of 30 data points over the entire typical price, and match it against a pattern
that uses a discrete soft corridor of 5%:

\`\`\`pycon
>>> price = data.hlc3

>>> similarity = price.vbt.rolling\_pattern\_similarity(
...     pattern, 
...     window=30,
...     error\_type="relative",
...     max\_error=0.05,
...     max\_error\_interp\_mode="discrete"
... )
>>> similarity.describe()
count    701.000000
mean       0.499321
std        0.144088
min        0.148387
25%        0.394584
50%        0.502231
75%        0.607962
max        0.838393
dtype: float64
\`\`\`

We can see that among 701 comparisons, roughly half have a score below 50%.
The highest score is around 84%. Let's visualize the best match:

\`\`\`pycon
>>> end\_row = similarity.argmax() + 1  # (1)!
>>> start\_row = end\_row - 30
>>> fig = data.iloc\[start\_row:end\_row\].plot(plot\_volume=False)
>>> price.iloc\[start\_row:end\_row\].vbt.plot\_pattern(
...     pattern, 
...     error\_type="relative",  # (2)!
...     max\_error=0.05,
...     max\_error\_interp\_mode="discrete",
...     plot\_obj=False, 
...     fig=fig
... )
>>> fig.show()
\`\`\`

1. Get the start (inclusive) and end (exclusive) row of the window with the highest similarity.
2. Be sure to use the same parameters that were used to calculate the similarity.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/max\_rolling\_similarity.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/max\_rolling\_similarity.dark.svg#only-dark){: .iimg loading=lazy }

Pretty accurate, right? And this window matches even better than the one we examined previously.
But what about the lowest similarity? Is it the same as inverting the pattern? No!

\`\`\`pycon
>>> end\_row = similarity.argmin() + 1
>>> start\_row = end\_row - 30
>>> fig = data.iloc\[start\_row:end\_row\].plot(plot\_volume=False)
>>> price.iloc\[start\_row:end\_row\].vbt.plot\_pattern(
...     pattern, 
...     invert=True,
...     error\_type="relative",
...     max\_error=0.05,
...     max\_error\_interp\_mode="discrete",
...     plot\_obj=False, 
...     fig=fig
... )
>>> fig.show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/min\_rolling\_similarity.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/min\_rolling\_similarity.dark.svg#only-dark){: .iimg loading=lazy }

Inverting the score will invalidate all the requirements set initially, so you should
always start a new pattern search with the \`invert\` flag enabled:

\`\`\`pycon
>>> inv\_similarity = price.vbt.rolling\_pattern\_similarity(
...     pattern, 
...     window=30,
...     invert=True,  # (1)!
...     error\_type="relative",
...     max\_error=0.05,
...     max\_error\_interp\_mode="discrete"
... )
>>> end\_row = inv\_similarity.argmax() + 1  # (2)!
>>> start\_row = end\_row - 30
>>> fig = data.iloc\[start\_row:end\_row\].plot(plot\_volume=False)
>>> price.iloc\[start\_row:end\_row\].vbt.plot\_pattern(
...     pattern, 
...     invert=True,
...     error\_type="relative",
...     max\_error=0.05,
...     max\_error\_interp\_mode="discrete",
...     plot\_obj=False, 
...     fig=fig
... )
>>> fig.show()
\`\`\`

1. Here.
2. We are looking for the highest similarity.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/inv\_rolling\_similarity.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/inv\_rolling\_similarity.dark.svg#only-dark){: .iimg loading=lazy }

The best match is not a perfect fit, but it is still much better than the previous one.

### Indicator

Once you have finalized the optimal pattern parameters through exploration and debugging, you should
consider integrating the pattern detection component into your backtesting stack. This can be achieved
by running the process inside an indicator. Since indicators must return output arrays of the same shape
as their input arrays, you can safely use the rolling pattern similarity as the output.
For this, you can use the \[PATSIM\](https://vectorbt.pro/pvt\_6d1b3986/api/indicators/custom/patsim/#vectorbtpro.indicators.custom.patsim.PATSIM)
indicator, which takes a price array as its only input and accepts all arguments related to
calculating pattern similarity as parameters, including the pattern array itself. Another benefit
of this indicator is its ability to automatically convert arguments provided as a string (such as \`interp\_mode\`)
into a Numba-compatible format. Finally, indicators are excellent for testing multiple window sizes,
since the accuracy of pattern detection heavily depends on the choice of window length.

Let's test several window combinations using the same setup as above:

\`\`\`pycon
>>> patsim = vbt.PATSIM.run(
...     price, 
...     vbt.Default(pattern),  # (1)!
...     error\_type=vbt.Default("relative"),
...     max\_error=vbt.Default(0.05),
...     max\_error\_interp\_mode=vbt.Default("discrete"),
...     window=\[30, 45, 60, 75, 90\]
... )
\`\`\`

1. Wrap with \[Default\](https://vectorbt.pro/pvt\_6d1b3986/api/base/reshaping/#vectorbtpro.base.reshaping.Default)
to hide the parameter from columns.

You can plot how the similarity develops using \[PATSIM.plot\](https://vectorbt.pro/pvt\_6d1b3986/api/indicators/custom/patsim/#vectorbtpro.indicators.custom.patsim.PATSIM.plot).
Like any other plotting method, it allows only one column to be plotted, so you need
to specify the column name beforehand using the \`column\` argument:

\`\`\`pycon
>>> patsim.wrapper.columns  # (1)!
Int64Index(\[30, 45, 60, 75, 90\], dtype='int64', name='patsim\_window')

>>> patsim.plot(column=60).show()
\`\`\`

1. Review the column names generated by this indicator. If there are multiple column
levels, you need to provide the column name as a tuple.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/patsim.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/patsim.dark.svg#only-dark){: .iimg loading=lazy }

The generated similarity series is as fascinating as the price series itself,
and can be used for all kinds of technical analysis on its own :triangular\_ruler:

An even more informative plot can be produced by
\[PATSIM.overlay\_with\_heatmap\](https://vectorbt.pro/pvt\_6d1b3986/api/indicators/custom/patsim/#vectorbtpro.indicators.custom.patsim.PATSIM.overlay\_with\_heatmap),
which overlays a price line with a similarity heatmap:

\`\`\`pycon
>>> patsim.overlay\_with\_heatmap(column=60).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/patsim\_heatmap.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/patsim\_heatmap.dark.svg#only-dark){: .iimg loading=lazy }

!!! info
    Bright vertical lines on the graph are located at the very end of their windows, marking
    where the pattern is considered completed. This makes the similarity score safe to use in backtesting.

So, how do we use this indicator to generate signals? We can compare the resulting similarity score
to a threshold to generate signals. In the example above, let's set a threshold of 80%
to build the exit signals:

\`\`\`pycon
>>> exits = patsim.similarity >= 0.8
>>> exits.sum()
patsim\_window
30     6
45     8
60    14
75     0
90     5
dtype: int64
\`\`\`

If you want to test multiple thresholds, you can use the parameter \`min\_similarity\`,
which sets all scores below it to NaN and also makes pattern recognition faster on average.
Deriving the signals is then as simple as checking whether each element is NaN. Let's also
test the inverted pattern:

\`\`\`pycon
>>> patsim = vbt.PATSIM.run(
...     price, 
...     vbt.Default(pattern),
...     error\_type=vbt.Default("relative"),
...     max\_error=vbt.Default(0.05),
...     max\_error\_interp\_mode=vbt.Default("discrete"),
...     window=\[30, 45, 60, 75, 90\],
...     invert=\[False, True\],
...     min\_similarity=\[0.7, 0.8\],
...     param\_product=True  # (1)!
... )
>>> exits = ~patsim.similarity.isnull()  # (2)!
>>> exits.sum()
patsim\_window  patsim\_invert  patsim\_min\_similarity
30             False          0.7                      68
                              0.8                       6
               True           0.7                      64
                              0.8                       2
...            ...            ...                     ...
90             False          0.7                      61
                              0.8                       5
               True           0.7                      70
                              0.8                       8
dtype: int64
\`\`\`

1. Build the Cartesian product of all parameters with more than one element.
Keep in mind that the number of parameter combinations can grow quickly: testing three parameters
with 10 elements each results in 1,000 combinations.
2. Any element that is not NaN is a potential signal.

If you are not interested in having the window as a backtestable parameter, but instead want to
create a signal as soon as any of the windows at that row crosses the similarity threshold, you can
react immediately once a pattern of any length is detected. This is easily achieved
using Pandas:

\`\`\`pycon
>>> groupby = \[  # (1)!
...     name for name in patsim.wrapper.columns.names 
...     if name != "patsim\_window"
... \]
>>> max\_sim = patsim.similarity.groupby(groupby, axis=1).max()  # (2)!
>>> entries = ~max\_sim.xs(True, level="patsim\_invert", axis=1).isnull()  # (3)!
>>> exits = ~max\_sim.xs(False, level="patsim\_invert", axis=1).isnull()  # (4)!
\`\`\`

1. Group by each column level except \`patsim\_window\`.
2. Select the highest score among all windows.
3. Select non-NaN scores among columns where \`patsim\_invert\` is \`True\` to build entries.
4. Select non-NaN scores among columns where \`patsim\_invert\` is \`False\` to build exits.

Now, let's plot the entry and exit signals corresponding to the threshold of 80%:

\`\`\`pycon
>>> fig = data.plot(ohlc\_trace\_kwargs=dict(opacity=0.5))
>>> entries\[0.8\].vbt.signals.plot\_as\_entries(price, fig=fig)
>>> exits\[0.8\].vbt.signals.plot\_as\_exits(price, fig=fig)
>>> fig.show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/patsim\_signals.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/patsim\_signals.dark.svg#only-dark){: .iimg loading=lazy }

Apart from a few missed regular and inverted double top patterns, the indicator works well.
By further tweaking the pattern similarity parameters and choosing a stricter pattern
configuration, you could easily filter out most failed patterns.

## Search

Searching for patterns of variable length using indicators with a parameterizable window is expensive.
Each window requires allocating an array at least the same size as the entire price array.
We need a more compact representation of pattern search results.
Fortunately, VBT's native support for record arrays makes this possible!

The procedural logic is implemented by the Numba-compiled function
\[find\_pattern\_1d\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/records/#vectorbtpro.generic.nb.records.find\_pattern\_1d\_nb)
and its two-dimensional version \[find\_pattern\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/records/#vectorbtpro.generic.nb.records.find\_pattern\_nb).
Here is the idea: iterate over the rows of a price array, and at each row,
iterate over a range of windows going forward or backward. For each window, run the
\[pattern\_similarity\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/patterns/#vectorbtpro.generic.nb.patterns.pattern\_similarity\_nb)
function to get the similarity score. If the score meets all requirements and is not NaN,
create a NumPy record of the type \[pattern\_range\_dt\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/enums/#vectorbtpro.generic.enums.pattern\_range\_dt),
which stores the start index (inclusive), the end index (exclusive, or inclusive if it's the last index),
and the similarity score. This record is appended to a record array and returned to the user.
The function supports selecting rows and windows randomly with a specified probability to reduce
the number of candidates and can handle overlapping pattern ranges. It is also extremely
time and memory efficient :zap:

Let's search for the pattern we defined above by rolling a window with sizes ranging from 30 to 90
and require the similarity score to be at least 85%:

\`\`\`pycon
>>> pattern\_range\_records = vbt.nb.find\_pattern\_1d\_nb(
...     price.values,  # (1)!
...     pattern,
...     window=30,  # (2)!
...     max\_window=90,
...     error\_type=vbt.enums.ErrorType.Relative,
...     max\_error=np.array(\[0.05\]),  # (3)!
...     max\_error\_interp\_mode=vbt.enums.InterpMode.Discrete,
...     min\_similarity=0.85
... )
>>> pattern\_range\_records
array(\[(0, 0, 270, 314, 1, 0.86226468), (1, 0, 484, 540, 1, 0.89078042)\])
\`\`\`

1. Our price contains only one asset, so we use the one-dimensional version of this function.
2. If \`max\_window\` is provided, the \`window\` argument becomes the minimum window.
3. Always wrap any array-like argument with NumPy when working with Numba-compiled functions.

The call returned two records, with 86% and 89% (!) similarity, respectively.
The first window is \`314 - 270 = 44\` data points long, and the second is \`540 - 484 = 56\`.
Let's plot the second fit, including the 30 bars that follow the pattern:

\`\`\`pycon
>>> start\_row = pattern\_range\_records\[1\]\["start\_idx"\]
>>> end\_row = pattern\_range\_records\[1\]\["end\_idx"\]
>>> fig = data.iloc\[start\_row:end\_row + 30\].plot(plot\_volume=False)
>>> price.iloc\[start\_row:end\_row\].vbt.plot\_pattern(
...     pattern, 
...     error\_type="relative",
...     max\_error=0.05,
...     max\_error\_interp\_mode="discrete",
...     plot\_obj=False, 
...     fig=fig
... )
>>> fig.show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/find\_pattern.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/find\_pattern.dark.svg#only-dark){: .iimg loading=lazy }

Voilà, this is the same pattern we examined at the beginning of this tutorial! This example shows
how important it is to test a dense grid of windows to find optimal matches. Unlike the
\[PATSIM\](https://vectorbt.pro/pvt\_6d1b3986/api/indicators/custom/patsim/#vectorbtpro.indicators.custom.patsim.PATSIM) indicator, this approach
uses almost no memory and includes several tricks to speed up calculation,
such as pre-calculating the price's expanding minimum and maximum values.

As is often the case, using the raw Numba-compiled function is all fun and games until you come across a
more convenient method that wraps it: \[PatternRanges.from\_pattern\_search\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges.from\_pattern\_search).
This class method takes all parameters accepted by \[find\_pattern\_1d\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/records/#vectorbtpro.generic.nb.records.find\_pattern\_1d\_nb),
builds a grid of parameter combinations, splits the price array into one-dimensional column arrays,
and executes each parameter combination on each column array using the
\[execute\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute) function, which supports both
sequential and parallel processing. After processing all input combinations, the method concatenates
the resulting record arrays and wraps them with the class
\[PatternRanges\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges).
This class extends the base class \[Ranges\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.Ranges)
by adding the similarity field and various pattern analysis and plotting methods. Enough theory;
let's do the same as above using this method:

\`\`\`pycon
>>> pattern\_ranges = vbt.PatternRanges.from\_pattern\_search(
...     price,  # (1)!
...     pattern,
...     window=30,
...     max\_window=90,
...     error\_type="relative",  # (2)!
...     max\_error=0.05,  # (3)!
...     max\_error\_interp\_mode="discrete",
...     min\_similarity=0.85
... )
>>> pattern\_ranges
<vectorbtpro.generic.ranges.PatternRanges at 0x7f8bdab039d0>
\`\`\`

1. Accepts Pandas objects.
2. Accepts strings.
3. Accepts constants.

If the price is a Pandas object, there is also an accessor method
\[GenericAccessor.find\_pattern\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor.find\_pattern)
that calls the class method above and can save you a few lines:

\`\`\`pycon
>>> pattern\_ranges = price.vbt.find\_pattern(
...     pattern,
...     window=30,
...     max\_window=90,
...     error\_type="relative",
...     max\_error=0.05,
...     max\_error\_interp\_mode="discrete",
...     min\_similarity=0.85
... )
\`\`\`

Let's view the records in a human-readable format:

\`\`\`pycon
>>> pattern\_ranges.records\_readable
   Pattern Range Id  Column               Start Index  \\
0                 0       0 2021-02-26 00:00:00+00:00   
1                 1       0 2021-09-28 00:00:00+00:00   

                  End Index  Status  Similarity  
0 2021-04-11 00:00:00+00:00  Closed    0.862265  
1 2021-11-23 00:00:00+00:00  Closed    0.890780 
\`\`\`

Additionally, the returned \[PatternRanges\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges) instance
stores the search configuration used to generate those records for each column.
The property \[PatternRanges.search\_configs\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges.search\_configs)
returns a list of these configurations, with each one being an instance of the data class
\[PSC\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PSC) (short for "Pattern Search Config").
There is one search configuration for each column.

!!! hint
    Please refer to the \[documentation of PSC\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PSC)
    for detailed descriptions of each parameter used in pattern search.

\`\`\`pycon
>>> pattern\_ranges.wrapper.columns
Int64Index(\[0\], dtype='int64')

>>> pattern\_ranges.search\_configs
\[PSC(
    pattern=array(\[1, 2, 3, 2, 3, 2\]), 
    window=30, 
    max\_window=120, 
    row\_select\_prob=1.0, 
    window\_select\_prob=1.0, 
    roll\_forward=False,
    interp\_mode=3, 
    rescale\_mode=0, 
    vmin=nan, 
    vmax=nan, 
    pmin=nan, 
    pmax=nan, 
    invert=False, 
    error\_type=1, 
    distance\_measure=0, 
    max\_error=array(\[0.05\]), 
    max\_error\_interp\_mode=2, 
    max\_error\_as\_maxdist=False, 
    max\_error\_strict=False, 
    min\_pct\_change=nan, 
    max\_pct\_change=nan, 
    min\_similarity=0.85, 
    max\_one\_per\_row=True,
    max\_overlap=0, 
    max\_records=None, 
    name=None
)\]
\`\`\`

This configuration instance contains all the argument names and values passed to
\[find\_pattern\_1d\_nb\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/nb/records/#vectorbtpro.generic.nb.records.find\_pattern\_1d\_nb).
Why do we need to keep it? For plotting! Remember how inconvenient it was to provide the
exact same arguments to a plotting method that were used in the similarity calculation.
To make things more streamlined, each pattern range instance keeps track of the search configuration
for each column to be plotted. Plotting itself is handled by the method
\[PatternRanges.plot\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges.plot),
which uses the \[Ranges.plot\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.Ranges.plot)
method to plot the data and ranges, and the
\[GenericSRAccessor.plot\_pattern\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericSRAccessor.plot\_pattern)
method to plot the patterns:

\`\`\`pycon
>>> pattern\_ranges.plot().show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/pattern\_ranges.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/pattern\_ranges.dark.svg#only-dark){: .iimg loading=lazy }

By default, it fills the distance between the price and the pattern (set \`fill\_distance=False\` to hide this),
and does not display the corridor (set \`plot\_max\_error=True\` to show it).
As with any other subclass of \[Analyzable\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/analyzable/#vectorbtpro.generic.analyzable.Analyzable),
an instance of \[PatternRanges\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges)
behaves in many ways like a regular Pandas object. For example, you can filter a date range using the regular
\`loc\` and \`iloc\` operations to zoom in on any pattern programmatically.

!!! note
    When selecting a date range, the indexing operation will filter out all range records
    that do not \*completely\* fall within the new date range. That is, if a pattern range
    starts on \`2020-01-01\` and lasts until \`2021-01-01\`, it will be included in the new
    pattern range instance if the new date range fully contains that period, for example
    \`2019-01-01\` to \`2021-01-01\`, but not \`2019-01-01\` to \`2020-12-31\`.

\`\`\`pycon
>>> pattern\_ranges.loc\["2021-09-01":"2022-01-01"\].plot().show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/pattern\_ranges\_zoomed.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/pattern\_ranges\_zoomed.dark.svg#only-dark){: .iimg loading=lazy }

!!! info
    You might have noticed that the bright area is larger than the window by one bar, and the green
    marker is located a bit farther from the last window point. This is because the field \`end\_idx\`
    represents the exclusive end of the range: the first point after the last window point.
    This approach is needed to properly calculate the duration of any range. The only exception is when the
    last window point is the last point in the entire price array; in such cases, the marker will be
    placed at that point and the range will be marked as open. Open ranges do not mean that the pattern
    is not completed, though.

Since all information is now represented using records, we can query various useful
metrics to describe the results:

\`\`\`pycon
>>> pattern\_ranges.stats()
Start                 2020-06-01 00:00:00+00:00
End                   2022-05-31 00:00:00+00:00
Period                        730 days 00:00:00
Total Records                                 2
Coverage                               0.136986
Overlap Coverage                            0.0
Duration: Min                  44 days 00:00:00
Duration: Median               50 days 00:00:00
Duration: Max                  56 days 00:00:00
Similarity: Min                        0.862265
Similarity: Median                     0.876523
Similarity: Max                         0.89078
dtype: object
\`\`\`

Here, for example, we see that there are two non-overlapping patterns covering 13.7% of the
entire period. We also see various duration and similarity quantiles.

### Overlapping

In the example above, we searched a total of \`90 - 30 + 1 = 61\` windows at each row.
Why did we not get any overlapping ranges? By default, overlapping is not allowed.
There are two optional mechanisms in place. First, when multiple windows start at the
same row, the algorithm selects the one with the highest similarity. This ensures that the
number of filled records is always equal to or less than the number of rows in the price array.
Second, when there are multiple consecutive records that overlap in ranges (regardless of whether
they start at the same row), the algorithm also selects the one with the highest similarity.

However, sometimes you may want to allow overlapping ranges. For example, one pattern
might start right before another ends, or a large pattern might cover a range that includes
smaller patterns. These cases can be addressed by adjusting the \`overlap\_mode\` argument, which is of
type \[OverlapMode\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/enums/#vectorbtpro.generic.enums.OverlapMode). Setting it to \`AllowAll\`
disables both mechanisms and appends every single record. Setting it to \`Allow\` disables
the second mechanism and only filters out ranges starting at the same row. Setting it to \`Disallow\`
enables both mechanisms (default), while setting it to any other positive integer specifies
the maximum number of rows that any two neighboring ranges are allowed to overlap.

!!! important
    Setting the argument to \`AllowAll\` may produce a record array larger than the price array.
    In this case, you need to manually increase the number of records allocated by setting \`max\_records\`,
    for example, \`max\_records=len(price) \* 2\`.

Let's allow overlapping ranges as long as they do not start at the same row:

\`\`\`pycon
>>> pattern\_ranges = price.vbt.find\_pattern(
...     pattern,
...     window=30,
...     max\_window=120,
...     error\_type="relative",
...     max\_error=0.05,
...     max\_error\_interp\_mode="discrete",
...     min\_similarity=0.85,
...     overlap\_mode="allow"  # (1)!
... )

>>> pattern\_ranges.count()
16

>>> pattern\_ranges.overlap\_coverage
0.9642857142857143
\`\`\`

1. Here

Now we see that instead of 2, there are 16 detected ranges.
Also, ranges overlap by 96%, which means that almost all ranges share rows with other ranges.
Let's visualize the result:

\`\`\`pycon
>>> pattern\_ranges.plot(plot\_zones=False, plot\_patterns=False).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/pattern\_ranges\_overlap.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/pattern\_ranges\_overlap.dark.svg#only-dark){: .iimg loading=lazy }

As shown in the graph, there are only two global matches, each confirmed by windows of
different lengths. If we set \`overlap\_mode="disallow"\`, only the most similar windows in each
region would remain.

!!! info
    There is an argument controlling the direction in which windows are rolled: \`roll\_forward\`.
    If this argument is \`False\` (default), ranges are sorted by the end index and may have multiple
    records pointing to the same start index. Otherwise, ranges are sorted by the start index and
    may have multiple records pointing to the same end index.

### Random selection

Sometimes, not every row and window combination is worth searching. If the input data is too large,
or if there are too many parameter combinations, the search could take a long time
in VBT terms (although it would still be incredibly fast!). To make
searchable regions more sparse, we can introduce a probability of picking a specific row or window.
For example, if the probability is \`0.5\`, the algorithm would search every second row or window on average.
Let's set a probability of 50% for rows and 25% for windows, and benchmark the execution to see
if the process would be about 8 times faster on average:

\`\`\`pycon
>>> def run\_prob\_search(row\_select\_prob, window\_select\_prob):
...     return price.vbt.find\_pattern(
...         pattern,
...         window=30,
...         max\_window=120,
...         row\_select\_prob=row\_select\_prob,  # (1)!
...         window\_select\_prob=window\_select\_prob,
...         error\_type="relative",
...         max\_error=0.05,
...         max\_error\_interp\_mode="discrete",
...         min\_similarity=0.8,  # (2)!
...     )

>>> %timeit run\_prob\_search(1.0, 1.0)
111 ms ± 247 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

>>> %timeit run\_prob\_search(0.5, 0.25)
15 ms ± 183 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)
\`\`\`

1. Both arguments must be between 0 and 1.
2. Lower the similarity threshold to capture more ranges.

Just note that unless you set a random seed (\`seed\` argument), detected pattern ranges
may vary greatly with each method call. Let's run \`run\_prob\_search\` 100 times and
plot the number of filled records:

\`\`\`pycon
>>> run\_prob\_search(1.0, 1.0).count()  # (1)!
6

>>> pd.Series(\[
...     run\_prob\_search(0.5, 0.25).count() 
...     for i in range(100)
... \]).vbt.plot().show()
\`\`\`

1. Get the maximum possible number of detected patterns.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/random\_selection.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/random\_selection.dark.svg#only-dark){: .iimg loading=lazy }

!!! hint
    The lower the selection probabilities, the less likely you are to detect all patterns
    in a single call. Always make sure to run the same search multiple times to assess
    the stability of the detection accuracy.

### Params

The advantage of the class method \[PatternRanges.from\_pattern\_search\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges.from\_pattern\_search)
is its ability to act like a full-blown indicator. It uses the same broadcasting and
parameter combining mechanism as VBT's broadcaster; both rely on the function
\[combine\_params\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.combine\_params). To mark any argument
as a parameter, wrap it with \[Param\](https://vectorbt.pro/pvt\_6d1b3986/api/utils/params/#vectorbtpro.utils.params.Param).
This enables the parameter to be broadcast and combined with others,
and it will appear as its own level in the final column hierarchy.

Let's test four patterns: "V-Top", "V-Bottom", a rising market, and a falling market pattern.

\`\`\`pycon
>>> pattern\_ranges = price.vbt.find\_pattern(
...     vbt.Param(\[
...         \[1, 2, 1\],
...         \[2, 1, 2\],
...         \[1, 2, 3\],
...         \[3, 2, 1\]
...     \]),
...     window=30,
...     max\_window=120,
... )
\`\`\`

\[=100% "Param 4/4"\]{: .candystripe .candystripe-animate }

Since we provided more than one parameter combination, the executor displayed a progress bar.
Let's count the number of found patterns:

\`\`\`pycon
>>> pattern\_ranges.count()
pattern
list\_0    3
list\_1    0
list\_2    7
list\_3    3
Name: count, dtype: int64
\`\`\`

We see that the \`pattern\` argument received four lists. Let's make it more readable
by providing an index that assigns each list a name:

\`\`\`pycon
>>> pattern\_ranges = price.vbt.find\_pattern(
...     vbt.Param(\[
...         \[1, 2, 1\],
...         \[2, 1, 2\],
...         \[1, 2, 3\],
...         \[3, 2, 1\]
...     \], keys=\["v-top", "v-bottom", "rising", "falling"\]),
...     window=30,
...     max\_window=120,
... )
>>> pattern\_ranges.count()
pattern
v-top       3
v-bottom    0
rising      7
falling     3
Name: count, dtype: int64
\`\`\`

Let's display the three detected falling patterns:

\`\`\`pycon
>>> pattern\_ranges.plot(column="falling").show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/params\_falling.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/params\_falling.dark.svg#only-dark){: .iimg loading=lazy }

But there are many more falling patterns on the chart. Why were they not recognized?
There are three reasons: 1) the algorithm searched only regions that are at least 30 bars long, 2) the default
minimum similarity threshold is 85%, so the algorithm chose only regions most similar to a straight line, and
3) the algorithm removed any overlapping regions.

Now, let's pass multiple parameters. In this case, their values will be combined to form a
Cartesian product of all parameter combinations. Let's also test multiple similarity thresholds:

\`\`\`pycon
>>> pattern\_ranges = price.vbt.find\_pattern(
...     vbt.Param(\[
...         \[1, 2, 1\],
...         \[2, 1, 2\],
...         \[1, 2, 3\],
...         \[3, 2, 1\]
...     \], keys=\["v-top", "v-bottom", "rising", "falling"\]),
...     window=30,
...     max\_window=120,
...     min\_similarity=vbt.Param(\[0.8, 0.85\])
... )
>>> pattern\_ranges.count()
pattern   min\_similarity
v-top     0.80              6
          0.85              3
v-bottom  0.80              3
          0.85              0
rising    0.80              8
          0.85              7
falling   0.80              6
          0.85              3
Name: count, dtype: int64
\`\`\`

We can now see some detected "V-Bottom" ranges:

\`\`\`pycon
>>> pattern\_ranges.plot(column=("v-bottom", 0.8)).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/params\_v\_bottom.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/params\_v\_bottom.dark.svg#only-dark){: .iimg loading=lazy }

What if we do not want to build a product of some parameters? For example, if we want
to use different window lengths for different patterns, this can be achieved by providing a level.
Parameters set to the same level are not combined, but instead are simply broadcast together.

\`\`\`pycon
>>> pattern\_ranges = price.vbt.find\_pattern(
...     vbt.Param(\[
...         \[1, 2, 1\],
...         \[2, 1, 2\],
...         \[1, 2, 3\],
...         \[3, 2, 1\]
...     \], keys=\["v-top", "v-bottom", "rising", "falling"\], level=0),
...     window=vbt.Param(\[30, 30, 7, 7\], level=0),  # (1)!
...     max\_window=vbt.Param(\[120, 120, 30, 30\], level=0),
...     min\_similarity=vbt.Param(\[0.8, 0.85\], level=1)  # (2)!
... )
>>> pattern\_ranges.count()
pattern   window  max\_window  min\_similarity
v-top     30      120         0.80               6
                              0.85               3
v-bottom  30      120         0.80               3
                              0.85               0
rising    7       30          0.80              27
                              0.85              23
falling   7       30          0.80              25
                              0.85              15
Name: count, dtype: int64
\`\`\`

1. Must have the same length as other parameters on the same level.
2. Will be combined with blocks of parameters that share the same level.

!!! note
    If you use levels, you must provide a level for all parameters. You can also reorder
    some parameters in the column hierarchy by assigning them a lower or higher level.

### Configs

It is important to note that when using multiple assets, each parameter will be applied over
the entire price array. But what if you want to search for different patterns in the prices
of different assets? Remember how each instance of \[PatternRanges\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges)
keeps track of the search configuration for each column in
\[PatternRanges.search\_configs\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges.search\_configs)?
Similarly, you can manually provide search configurations using the \`search\_configs\` argument,
which must be a list of \[PSC\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PSC) instances
(for the entire price array) or a list of lists of \[PSC\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PSC)
instances (for each column). This way, you can define custom parameter combinations.

To demonstrate this, let's fetch the prices for the \`BTCUSDT\` and \`ETHUSDT\` symbols,
and search for the "Double Top" pattern in both assets, as well as for any occurrence of the latest
30 bars in each asset individually:

\`\`\`pycon
>>> mult\_data = vbt.BinanceData.pull(
...     \["BTCUSDT", "ETHUSDT"\], 
...     start="2020-06-01 UTC", 
...     end="2022-06-01 UTC"
... )
>>> mult\_price = mult\_data.hlc3

>>> pattern\_ranges = mult\_price.vbt.find\_pattern(
...     search\_configs=\[
...         vbt.PSC(pattern=\[1, 2, 3, 2, 3, 2\], window=30),  # (1)!
...         \[
...             vbt.PSC(pattern=mult\_price.iloc\[-30:, 0\]),  # (2)!
...             vbt.PSC(pattern=mult\_price.iloc\[-30:, 1\]),
...         \]
...     \],
...     min\_similarity=0.8  # (3)!
... )
>>> pattern\_ranges.count()
search\_config  symbol 
0              BTCUSDT    6
1              ETHUSDT    4
2              BTCUSDT    5
3              ETHUSDT    8
Name: count, dtype: int64
\`\`\`

1. Each \`PSC\` instance in the outer list is applied to the entire array.
2. Each \`PSC\` instance in the inner list is applied per column.
3. If an argument should apply to all columns, provide it as a regular argument.

!!! hint
    You can provide arguments to \[PSC\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PSC)
    in a human-readable format. Each config will be automatically prepared for use in Numba.

We see the column hierarchy now contains two levels: the search config identifier
and the column name. Let's make it more descriptive by choosing a name for each config:

\`\`\`pycon
>>> pattern\_ranges = mult\_price.vbt.find\_pattern(
...     search\_configs=\[
...         vbt.PSC(pattern=\[1, 2, 3, 2, 3, 2\], window=30, name="double\_top"),
...         \[
...             vbt.PSC(pattern=mult\_price.iloc\[-30:, 0\], name="last"),
...             vbt.PSC(pattern=mult\_price.iloc\[-30:, 1\], name="last"),
...         \]
...     \],
...     min\_similarity=0.8
... )
>>> pattern\_ranges.count()
search\_config  symbol 
double\_top     BTCUSDT    6
               ETHUSDT    4
last           BTCUSDT    5
               ETHUSDT    8
Name: count, dtype: int64
\`\`\`

You can also combine search configurations and parameters. In this case, the method will clone
the provided search configurations for each parameter combination, and override the parameters
of each search configuration with the current parameter combination. Let's test various rescaling modes:

\`\`\`pycon
>>> pattern\_ranges = mult\_price.vbt.find\_pattern(
...     search\_configs=\[
...         vbt.PSC(pattern=\[1, 2, 3, 2, 3, 2\], window=30, name="double\_top"),
...         \[
...             vbt.PSC(pattern=mult\_price.iloc\[-30:, 0\], name="last"),
...             vbt.PSC(pattern=mult\_price.iloc\[-30:, 1\], name="last"),
...         \]
...     \],
...     rescale\_mode=vbt.Param(\["minmax", "rebase"\]),
...     min\_similarity=0.8,
...     open=mult\_data.open,  # (1)!
...     high=mult\_data.high,
...     low=mult\_data.low,
...     close=mult\_data.close,
... )
>>> pattern\_ranges.count()
rescale\_mode  search\_config  symbol 
minmax        double\_top     BTCUSDT    6
                             ETHUSDT    4
              last           BTCUSDT    5
                             ETHUSDT    8
rebase        double\_top     BTCUSDT    0
                             ETHUSDT    0
              last           BTCUSDT    2
                             ETHUSDT    2
Name: count, dtype: int64
\`\`\`

1. Provide OHLC for plotting.

For example, our search for a pattern based on the last 30 bars in \`ETHUSDT\` found 8 occurrences
that are similar by shape (using min-max rescaling) and only 2 occurrences that are similar by both
shape and percentage change (using rebasing):

\`\`\`pycon
>>> pattern\_ranges.plot(column=("rebase", "last", "ETHUSDT")).show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/configs\_and\_params.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/configs\_and\_params.dark.svg#only-dark){: .iimg loading=lazy }

The first range has a similarity of 85%, while the second range is still open and has a similarity
of 100%. This makes sense because it was used as the pattern.

!!! note
    Again, an open range does not mean that it has not finished developing. It only means that the last
    point in the range is also the last point in the price array, so the duration can be calculated correctly.

### Mask

How do we use a pattern range instance to generate signals? Since such an instance usually
stores only ranges that meet a certain similarity threshold, we only need to determine whether
there is any range that closes at a specific row and column. This mask can be generated by calling
the property \[PatternRanges.last\_pd\_mask\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges.last\_pd\_mask):

\`\`\`pycon
>>> mask = pattern\_ranges.last\_pd\_mask
>>> mask.sum()  # (1)!
rescale\_mode  search\_config  symbol 
minmax        touble\_top     BTCUSDT    6
                             ETHUSDT    4
              last           BTCUSDT    5
                             ETHUSDT    8
rebase        touble\_top     BTCUSDT    0
                             ETHUSDT    0
              last           BTCUSDT    2
                             ETHUSDT    2
dtype: int64
\`\`\`

1. Count of \`True\` values in the mask.

We can then use this mask, for example, in \[Portfolio.from\_signals\](https://vectorbt.pro/pvt\_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio.from\_signals).

### Indicator

If you do not need to plot or analyze pattern ranges, you can use the same
\[PATSIM\](https://vectorbt.pro/pvt\_6d1b3986/api/indicators/custom/patsim/#vectorbtpro.indicators.custom.patsim.PATSIM) indicator used
previously to generate a Series or DataFrame of similarity scores. What was not discussed earlier is
that this indicator also accepts the arguments \`max\_window\`, \`row\_select\_prob\`, and \`window\_select\_prob\`.
Let's confirm that the indicator produces the same similarity scores as pattern ranges:

\`\`\`pycon
>>> pattern\_ranges = price.vbt.find\_pattern(
...     pattern,
...     window=30,
...     max\_window=120,
...     row\_select\_prob=0.5,
...     window\_select\_prob=0.5,
...     overlap\_mode="allow",  # (1)!
...     seed=42
... )
>>> pr\_mask = pattern\_ranges.map\_field(
...     "similarity", 
...     idx\_arr=pattern\_ranges.last\_idx.values
... ).to\_pd()
>>> pr\_mask\[~pr\_mask.isnull()\]
Open time
2021-03-23 00:00:00+00:00    0.854189
2021-03-26 00:00:00+00:00    0.853817
2021-04-10 00:00:00+00:00    0.866913
2021-04-11 00:00:00+00:00    0.866106
2021-11-17 00:00:00+00:00    0.868276
2021-11-18 00:00:00+00:00    0.873757
2021-11-21 00:00:00+00:00    0.890225
2021-11-23 00:00:00+00:00    0.892541
2021-11-24 00:00:00+00:00    0.879475
2021-11-26 00:00:00+00:00    0.877245
2021-11-27 00:00:00+00:00    0.872172
dtype: float64

>>> patsim = vbt.PATSIM.run(
...     price,
...     vbt.Default(pattern),  # (2)!
...     window=vbt.Default(30),
...     max\_window=vbt.Default(120),
...     row\_select\_prob=vbt.Default(0.5),
...     window\_select\_prob=vbt.Default(0.5),
...     min\_similarity=vbt.Default(0.85),  # (3)!
...     seed=42
... )
>>> ind\_mask = patsim.similarity
>>> ind\_mask\[~ind\_mask.isnull()\]
Open time
2021-03-23 00:00:00+00:00    0.854189
2021-03-26 00:00:00+00:00    0.853817
2021-04-10 00:00:00+00:00    0.866913
2021-04-11 00:00:00+00:00    0.866106
2021-11-17 00:00:00+00:00    0.868276
2021-11-18 00:00:00+00:00    0.873757
2021-11-21 00:00:00+00:00    0.890225
2021-11-23 00:00:00+00:00    0.892541
2021-11-24 00:00:00+00:00    0.879475
2021-11-26 00:00:00+00:00    0.877245
2021-11-27 00:00:00+00:00    0.872172
dtype: float64
\`\`\`

1. This is the only mode supported in \[PATSIM\](https://vectorbt.pro/pvt\_6d1b3986/api/indicators/custom/patsim/#vectorbtpro.indicators.custom.patsim.PATSIM).
2. Use \`Default\` for each argument to hide it from columns.
3. This is the default threshold in \[PatternRanges.from\_pattern\_search\](https://vectorbt.pro/pvt\_6d1b3986/api/generic/ranges/#vectorbtpro.generic.ranges.PatternRanges.from\_pattern\_search).

## Combination

We have learned how to generate signals from a single pattern found in one array, but what about scenarios
where signals should only be triggered when a combination of patterns is found across different arrays?
For example, how can we quantify convergence and divergence? To combine multiple patterns conditionally,
we need to combine their similarity scores. In the example below, we search for a bearish divergence
between the high price and MACD:

\`\`\`pycon
>>> price\_highs = vbt.PATSIM.run(
...     data.high, 
...     pattern=np.array(\[1, 3, 2, 4\]),  # (1)!
...     window=40,
...     max\_window=50
... )
>>> macd = data.run("talib\_macd").macd  # (2)!
>>> macd\_lows = vbt.PATSIM.run(
...     macd, 
...     pattern=np.array(\[4, 2, 3, 1\]),  # (3)!
...     window=40,
...     max\_window=50
... )

>>> fig = vbt.make\_subplots(
...     rows=3, cols=1, shared\_xaxes=True, vertical\_spacing=0.02
... )
>>> fig.update\_layout(height=500)
>>> data.high.rename("Price").vbt.plot(
...     add\_trace\_kwargs=dict(row=1, col=1), fig=fig
... )
>>> macd.rename("MACD").vbt.plot(
...     add\_trace\_kwargs=dict(row=2, col=1), fig=fig
... )
>>> price\_highs.similarity.rename("Price Sim").vbt.plot(
...     add\_trace\_kwargs=dict(row=3, col=1), fig=fig
... )
>>> macd\_lows.similarity.rename("MACD Sim").vbt.plot(
...     add\_trace\_kwargs=dict(row=3, col=1), fig=fig
... )
>>> fig.show()
\`\`\`

1. Two rising highs.
2. Use \[Data.run\](https://vectorbt.pro/pvt\_6d1b3986/api/data/base/#vectorbtpro.data.base.Data.run) to quickly run indicators.
3. Two falling highs.

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/macd\_divergence.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/macd\_divergence.dark.svg#only-dark){: .iimg loading=lazy }

By reviewing the chart, we can see that the chosen parameters accurately represent the events we
are seeking. The regions where the price and MACD are rising and falling, respectively, also lead
to rising similarity scores. We can also find the optimal similarity threshold that yields a reasonable
number of crossovers, such as 80%. Additionally, the points where the price similarity line crosses
the threshold often occur slightly before those of the MACD, so it is not sufficient to simply test
whether both crossovers happen at the same time. We need to introduce a waiting period using the rolling
"any" operation. For example, below we generate an exit signal if both similarities have crossed
the threshold during the last 10 bars, not necessarily at the same time:

\`\`\`pycon
>>> cond1 = (price\_highs.similarity >= 0.8).vbt.rolling\_any(10)
>>> cond2 = (macd\_lows.similarity >= 0.8).vbt.rolling\_any(10)
>>> exits = cond1 & cond2
>>> fig = data.plot(ohlc\_trace\_kwargs=dict(opacity=0.5))
>>> exits.vbt.signals.plot\_as\_exits(data.close, fig=fig)
>>> fig.show()
\`\`\`

!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/macd\_divergence\_exits.light.svg#only-light){: .iimg loading=lazy }
!\[\](https://vectorbt.pro/pvt\_6d1b3986/assets/images/tutorials/patterns/macd\_divergence\_exits.dark.svg#only-dark){: .iimg loading=lazy }

For more ideas, see \[Signal Development\](https://vectorbt.pro/pvt\_6d1b3986/tutorials/signal-development).

\[:material-language-python: Python code\](https://vectorbt.pro/pvt\_6d1b3986/assets/jupytext/tutorials/patterns-and-projections/patterns.py.txt){ .md-button target="blank\_" }
\[:material-notebook-outline: Notebook\](https://github.com/polakowo/vectorbt.pro/blob/main/notebooks/PatternsProjections.ipynb){ .md-button target="blank\_" }