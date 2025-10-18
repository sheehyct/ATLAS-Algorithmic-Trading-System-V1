---
title: Plotting
description: Recipes for plotting data in VectorBT PRO
icon: material/chart-bubble
---

# :material-chart-bubble: Plotting

Any Pandas Series or DataFrame can be plotted using an accessor. There are two main ways to plot data:

1. [GenericAccessor](https://vectorbt.pro/pvt_6d1b3986/api/generic/accessors/#vectorbtpro.generic.accessors.GenericAccessor) offers
methods designed for typical vectorbtpro workflows.
2. [PXAccessor](https://vectorbt.pro/pvt_6d1b3986/api/px/accessors/#vectorbtpro.px.accessors.PXAccessor) provides methods based on
[Plotly express](https://plotly.com/python/plotly-express/).

```python title="How to plot a Pandas object"
fig = sr_or_df.vbt.plot()  # (1)!

fig = pd.Series(
    np.asarray(y), 
    index=np.asarray(x)
).vbt.scatterplot()  # (2)!
fig = pf.value.vbt.lineplot()  # (3)!
fig = pf.sharpe_ratio.vbt.barplot()  # (4)!
fig = pf.returns.vbt.qqplot()  # (5)!
fig = pf.allocations.vbt.areaplot(line_shape="hv")  # (6)!
fig = pf.returns.vbt.histplot(trace_kwargs=dict(nbinsx=100))  # (7)!

monthly_returns = pf.returns_acc.resample("M").get()
fig = monthly_returns.vbt.boxplot()   # (8)!
fig = monthly_returns.vbt.heatmap()  # (9)!
fig = monthly_returns.vbt.ts_heatmap()  # (10)!

fig = pf.sharpe_ratio.vbt.heatmap(  # (11)!
    x_level="fast_window", 
    y_level="slow_window",
    symmetric=True
)
fig = pf.sharpe_ratio.vbt.heatmap(  # (12)!
    x_level="fast_window", 
    y_level="slow_window",
    slider_level="symbol",
    symmetric=True
)
fig = pf.sharpe_ratio.vbt.volume(  # (13)!
    x_level="timeperiod", 
    y_level="upper_threshold",
    z_level="lower_threshold",
    symmetric=True
)

# ______________________________________________________________

fig = sr_or_df.vbt.px.ecdf()  # (14)!
```

1. Create a line plot with visible markers. Each column will be a separate trace.
2. Create a scatter plot of variable `x` against variable `y`. Both must be one-dimensional.
3. Display equity as a line plot.
4. Compare Sharpe ratios for different symbols or parameter combinations using a bar plot.
5. Create a Q-Q plot to check if returns are normally distributed. Only one column at a time.
6. Plot allocations as an area plot.
7. Create a histogram of returns with 100 bins. Remove `nbinsx` for automatic binning.
8. Create a box plot of monthly returns.
9. Create a heatmap showing time (y-axis) versus monthly returns (x-axis).
10. Create a heatmap showing monthly returns (y-axis) versus time (x-axis).
11. Create a symmetrical heatmap of Sharpe ratios, with fast windows on the x-axis and slow windows on
the y-axis. The Pandas object must be a Series with two index levels.
12. Create a symmetrical heatmap of Sharpe ratios, with fast windows on the x-axis, slow windows on the
y-axis, and symbols displayed as a slider. The Pandas object must be a Series with three index levels.
13. For three or four parameters, create a volume plot instead.
14. Plot an Empirical Cumulative Distribution Plot using Plotly express.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

A figure created with VBT can be displayed either interactively or as a static image.

```python title="How to display a figure"
fig.show()  # (1)!
fig.show_svg()  # (2)!
fig.show_png()  # (3)!
```

1. Display an interactive figure.
2. Display as a static SVG.
3. Display as a static PNG.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To plot multiple items on the same figure, retrieve the figure from the first plot method and pass it to
each subsequent plot call.

```python title="Plot equity lines of two portfolios in the same figure"
fig = pf1.value.vbt.lineplot()
fig = pf2.value.vbt.lineplot(fig=fig)
fig.show()
```

This also works for plotting multiple columns of a portfolio or other complex objects. When creating a
graph with subplots, you can automatically overlay each column.

```python
pf.plot(per_column=True).show()  # (1)!

fig = pf["BTC-USD"].plot(show_legend=False, show_column_label=True)
fig = pf["ETH-USD"].plot(show_legend=False, show_column_label=True, fig=fig)
fig.show()  # (2)!
```

1. Plot each column on the same figure.
2. Same as above.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

The default theme can be set globally in the settings. Available themes are listed under `themes` in
[settings.plotting](https://vectorbt.pro/pvt_6d1b3986/api/_settings/#vectorbtpro._settings.plotting).

```python title="Set the dark theme"
vbt.settings.set_theme("dark")
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can change trace parameters such as line color and marker shape using `trace_kwargs`. Some plot
methods have multiple such arguments. For the full list of allowed parameters, see the Plotly
documentation for the corresponding trace type, such as
[Scatter](https://plotly.com/python-api-reference/generated/plotly.graph_objects.Scatter.html) for lines.

```python title="Change the color of the upper and lower lines of a Bollinger Bands indicator"
fig = bbands.plot(
    upper_trace_kwargs=dict(line=dict(color="green")),
    lower_trace_kwargs=dict(line=dict(color="red"))
)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can change layout parameters by passing them directly to the plot method as keyword arguments.

```python title="Make the width and height of the plot variable instead of fixed"
fig = df.vbt.plot(width=None, height=None)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can create a plot with multiple subplots using `vbt.make_subplots()`, which accepts [the same
arguments](https://plotly.com/python-api-reference/generated/plotly.subplots.make_subplots.html) as Plotly.

```python title="Create two subplots, one per row"
fig = vbt.make_subplots(rows=2, cols=1)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Most plot methods accept the argument `add_trace_kwargs`
(see [Figure.add_trace](https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html#plotly.graph_objects.Figure.add_trace)),
which you can use to specify which subplot to draw the traces on.

```python title="Plot the first and second DataFrame on the first and second subplot"
df1.vbt.plot(add_trace_kwargs=dict(row=1, col=1), fig=fig)
df2.vbt.plot(add_trace_kwargs=dict(row=2, col=1), fig=fig)
```

!!! note
    The figure `fig` must be created using `vbt.make_subplots()`.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Traces with two different scales but the same time axis can be plotted together by creating a
secondary y-axis.

```python title="Plot the first and second DataFrame on the first and second y-axis"
fig = vbt.make_subplots(specs=[[{"secondary_y": True}]])
df1.vbt.plot(add_trace_kwargs=dict(secondary_y=False), fig=fig)
df2.vbt.plot(add_trace_kwargs=dict(secondary_y=True), fig=fig)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can modify the figure manually after creation. Here, `0` is the index of the trace in the figure.

```python title="Update the title and markers of the scatter plot after creation"
fig = df.vbt.scatterplot()
fig.layout.title.text = "Scatter"
fig.data[0].marker.line.width = 4
fig.data[0].marker.line.color = "black"
```

!!! note
    A plotting method can add multiple traces to the figure.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Plotting-related settings can be defined or changed globally in [settings.plotting](https://vectorbt.pro/pvt_6d1b3986/api/_settings/#vectorbtpro._settings.plotting).

```python title="Change the background of any figure to black"
vbt.settings["plotting"]["layout"]["paper_bgcolor"] = "rgb(0,0,0)"
vbt.settings["plotting"]["layout"]["plot_bgcolor"] = "rgb(0,0,0)"
vbt.settings["plotting"]["layout"]["template"] = "vbt_dark"
```

```python title="Same by registering your own theme"
import plotly.io as pio
import plotly.graph_objects as go

pio.templates["my_black"] = go.layout.Template(
    layout_paper_bgcolor="rgb(0,0,0)",
    layout_plot_bgcolor="rgb(0,0,0)",
)
vbt.settings["plotting"]["layout"]["template"] = "vbt_dark+my_black"
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

By default, Plotly displays a continuous datetime index, including time gaps such as non-business hours
and weekends. To skip these gaps, you can use the `rangebreaks` property.

```python title="Skip non-business hours and weekends"
fig = df.vbt.plot()
fig.update_xaxes(
    rangebreaks=[
        dict(bounds=['sat', 'mon']),
        dict(bounds=[16, 9.5], pattern='hour'),
        # (1)!
    ]
)
```

1. Pass `dict(values=df.isnull().all(axis=1).index)` to also skip NaN rows, or any other index.

!!! note
    Ensure your data has the correct timezone to apply this approach.

```python title="Skip all gaps automatically"
fig = df.vbt.plot()
fig.auto_rangebreaks()  # (1)!
fig.auto_rangebreaks(freq="D")  # (2)!

# ______________________________________________________________

vbt.settings.plotting.auto_rangebreaks = True
vbt.settings.plotting.auto_rangebreaks = dict(freq="D")

# ______________________________________________________________

def pre_show_func(fig):
    fig.auto_rangebreaks(freq="D")
    
vbt.settings.plotting.pre_show_func = pre_show_func  # (4)!
fig = df.vbt.plot()
fig.show()  # (5)!
```

1. Skip gaps based on the detected frequency of the index.
2. Skip gaps using any other frequency. For example, use daily frequency to skip weekends
when the detected frequency is business days.
3. Skip NaN rows, or provide any other index to skip.
4. Run auto-rangebreaks before displaying any figure.
5. You must call the `show()` method for this to take effect.

!!! note
    This approach works only for figures produced by VBT methods.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To display a figure on an interactive HTML page, see [Interactive HTML Export](https://plotly.com/python/interactive-html-export/).

```python title="Save the figure to an HTML file"
fig.write_html("fig.html")
```

```python title="Save multiple figures to the same HTML file"
with open("fig.html", "a") as f:
    f.write(fig1.to_html(full_html=False))
    f.write(fig2.to_html(full_html=False))
    f.write(fig3.to_html(full_html=False))
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To display a figure in a separate browser tab, see [Renderers](https://plotly.com/python/renderers/).

```python title="Make browser the default renderer"
import plotly.io as pio
pio.renderers.default = "browser"
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

If a figure takes too long to display, the amount of data may be the cause.
In this case, [plotly-resampler](https://github.com/predict-idlab/plotly-resampler)
can help by resampling any (primarily scatter) data on the fly.

```python title="Enable plotly-resampler globally"
vbt.settings.plotting.use_resampler = True
```

Another option is to select a specific date range of interest.

```python title="Display one year of data"
fig = fig.select_range(start="2023", end="2024")
```