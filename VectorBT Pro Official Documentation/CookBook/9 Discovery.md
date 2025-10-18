---
title: Discovery
description: Recipes for discovering the API of VectorBT PRO
icon: material/file-tree
---

# :material-file-tree: Discovery

You can display the arguments and, optionally, the description of any Python function or class by using
[phelp](https://vectorbt.pro/pvt_6d1b3986/api/utils/formatting/#vectorbtpro.utils.formatting.phelp). For example, this makes it easy to
quickly view the inputs, outputs, and parameters accepted by an indicator's `run()` function.

```python title="Print the specification of the TA-Lib's ATR"
vbt.phelp(vbt.talib("atr").run)
```

!!! note
    This is not the same as calling Python's `help` command. It only works on functions.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can list the attributes of any Python object by using 
[pdir](https://vectorbt.pro/pvt_6d1b3986/api/utils/formatting/#vectorbtpro.utils.formatting.pdir). This is helpful when you want to 
check if an object has a specific attribute without searching through the API documentation.

```python title="Print the properties and methods of the Portfolio class"
vbt.pdir(vbt.PF)
```

!!! tip
    You can even use this on third-party objects, such as packages!

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Most VBT objects can be expanded and pretty-formatted to quickly reveal their contents
with [pprint](https://vectorbt.pro/pvt_6d1b3986/api/utils/formatting/#vectorbtpro.utils.formatting.pprint). This is a simple way to
visually confirm that an object has the correct shape and grouping.

```python title="Print the configuration of a Data instance"
vbt.pprint(data)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Most VBT objects can be linked to the API reference on the website and the source code on GitHub
by using [open_api_ref](https://vectorbt.pro/pvt_6d1b3986/api/utils/module_/#vectorbtpro.utils.module.open_api_ref). The function
accepts a VBT object, its name, or its absolute path inside the package. It can also take third-party
objects; in this case, it will search for them using [:simple-duckduckgo: DuckDuckGo](https://duckduckgo.com/)
and open the first link it finds.

```python title="How to open the online API reference"
vbt.open_api_ref(vbt.nb)  # (1)!
vbt.open_api_ref(vbt.nb.rolling_mean_nb)  # (2)!
vbt.open_api_ref(vbt.PF)  # (3)!
vbt.open_api_ref(vbt.Data.run)  # (4)!
vbt.open_api_ref(vbt.Data.features)  # (5)!
vbt.open_api_ref(vbt.ADX.adx_crossed_above)  # (6)!
vbt.open_api_ref(vbt.settings)  # (7)!
vbt.open_api_ref(pf.get_sharpe_ratio)  # (8)!
vbt.open_api_ref((pf, "sharpe_ratio"))  # (9)!
vbt.open_api_ref(pd.DataFrame)  # (10)!
vbt.open_api_ref("vbt.PF")  # (11)!
vbt.open_api_ref("SizeType")  # (12)!
vbt.open_api_ref("DataFrame", module="pandas")  # (13)!
vbt.open_api_ref("numpy.char.find", resolve=False)  # (14)!
```

1. Module.
2. Function.
3. Class.
4. Method.
5. Property.
6. Generated method or property.
7. Instance.
8. Method of an instance.
9. Any attribute of an instance (note: you cannot use `pf.sharpe_ratio` here).
10. Third-party objects work too.
11. Shortcut.
12. Find an object across the package.
13. Find an object across a third-party package.
14. Use the reference without checking its validity.

!!! tip
    To get the link without opening it, use [get_api_ref](https://vectorbt.pro/pvt_6d1b3986/api/utils/module_/#vectorbtpro.utils.module.get_api_ref).
    It takes the same arguments.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To open the first result for any search query, use [imlucky](https://vectorbt.pro/pvt_6d1b3986/api/utils/module_/#vectorbtpro.utils.module.imlucky).

```python title="Ask a question if you feel lucky"
vbt.imlucky("How to create a structured NumPy array?")  # (1)!
```

1. Opens https://numpy.org/doc/stable/user/basics.rec.html.