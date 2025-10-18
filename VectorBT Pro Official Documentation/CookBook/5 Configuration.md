---
title: Configuration
description: Recipes for configuring VectorBT PRO
icon: material/cog
---

# :material-cog: Configuration

## Objects

!!! question
    Learn more in [Building blocks - Configuring documentation](https://vectorbt.pro/pvt_6d1b3986/documentation/building-blocks/#configuring).

VBT objects that subclass [Configured](https://vectorbt.pro/pvt_6d1b3986/api/utils/pickling/#vectorbtpro.utils.pickling.Configured)
(which represent most of the implemented classes) store the keyword arguments passed 
to their initializer, available under `config`. Copying an object simply involves passing the same
config to the class to create a new instance, which can be done automatically using the `copy()` method.

```python title="Copy a Portfolio instance"
new_pf = pf.copy()
new_pf = vbt.PF(**pf.config)  # (1)!
```

1. Manually.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Since changing any information in-place is strongly discouraged due to caching reasons, to replace
something, copy the config, modify it, and pass it to the class. This can be done automatically with the
`replace()` method.

```python title="Replace initial capital in a Portfolio instance"
new_pf = pf.replace(init_cash=1_000_000)
new_pf = vbt.PF(**vbt.merge_dicts(pf.config, dict(init_cash=1_000_000)))  # (1)!
```

1. Manually.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

In many cases, a VBT object contains other VBT objects. To make changes to a deep
vectorbtpro object, you can enable the `nested_` flag and pass the instruction as a nested dict.

```python title="Enable grouping in the wrapper of a Portfolio instance"
new_pf = pf.replace(wrapper=dict(group_by=True), nested_=True)
new_pf = pf.replace(wrapper=pf.wrapper.replace(group_by=True))  # (1)!
```

1. Manually.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

The same VBT objects can be saved as config files for easy editing.
Such a config file has a format that is very similar to the [INI format](https://en.wikipedia.org/wiki/INI_file)
but includes various extensions such as code expressions and nested dictionaries.
This allows representing objects of any complexity.

```python title="Save a Portfolio instance to a config file and load it back"
pf.save(file_format="config")

# (1)!

pf = vbt.PF.load()
```

1. ...make changes to the file...

## Settings

Settings that control the default behavior of most functionalities in VBT are located
under [_settings](https://vectorbt.pro/pvt_6d1b3986/api/_settings/#vectorbtpro._settings). Each functionality has its own config;
for example, [settings.portfolio](https://vectorbt.pro/pvt_6d1b3986/api/_settings/#vectorbtpro._settings.portfolio) defines the defaults
for the [Portfolio](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio) class. All configs
are combined into a single config that you can access via `vbt.settings`.

```python title="Set the default initial cash"
vbt.settings.portfolio.init_cash = 1_000_000
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

The initial state of any config can be accessed through `options_["reset_dct"]`.

```python title="Get the default initial cash before any changes"
print(vbt.settings.portfolio.options_["reset_dct"]["init_cash"])  # (1)!
```

1. The reset dict is a regular dict, so dot notation does not work here.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Any config can be reset to its initial state using the `reset()` method.

```python title="Reset the Portfolio config"
vbt.settings.portfolio.reset()
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

For convenience, settings can be defined in a text file that will be loaded automatically
the next time VBT is imported. The file should be placed in the directory of the script importing 
the package and be named `vbt.ini` or `vbt.config`. Alternatively, you can set the path to the settings 
file by setting the environment variable `VBT_SETTINGS_PATH`. The file must use the 
[INI format](https://en.wikipedia.org/wiki/INI_file#Format) with extensions provided by vectorbtpro. See
[Pickleable.decode_config](https://vectorbt.pro/pvt_6d1b3986/api/utils/pickling/#vectorbtpro.utils.pickling.Pickleable.decode_config) for examples.

```ini title="Configuration file that defines the default initial cash"
# (1)!
[portfolio]
init_cash = 1_000_000
```

1. The name of the config under [_settings](https://vectorbt.pro/pvt_6d1b3986/api/_settings/#vectorbtpro._settings).

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

This is especially useful for changing settings that only take effect on import,
such as various Numba-related settings, caching, and chunking machinery.

```ini title="Configuration file that disables Numba"
# (1)!
[numba]
disable = True
```

1. The name of the config under [_settings](https://vectorbt.pro/pvt_6d1b3986/api/_settings/#vectorbtpro._settings).

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To save all settings or a specific config to a text file, modify it, and let VBT
load it on import (or manually), use the `save()` method with `file_format="config"`.

```python title="Save Portfolio config and import it automatically"
vbt.settings.portfolio.save("vbt.config", top_name="portfolio")
```

```python title="Save Portfolio config and import it manually"
vbt.settings.portfolio.save("portfolio.config")

# (1)!

vbt.settings.portfolio.load_update("portfolio.config")
```

1. ...make changes to the file and restart the kernel...

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

If the readability of the file does not matter, you can modify the settings in place and then save 
them to a Pickle file in one Python session, allowing them to be automatically imported in the next session.

```python title="Disable Numba in the next Python session"
vbt.settings.numba.disable = True
vbt.settings.save("vbt")
```

!!! warning
    This approach is discouraged if you plan to upgrade VBT frequently, as new releases
    may introduce changes to the settings.