---
title: Compilation
description: Recipes for Numba compilation in VectorBT PRO
icon: material/speedometer
---

# :material-speedometer: Compilation

You can disable Numba globally by setting an environment variable or by changing the config 
(see [Environment variables](https://numba.readthedocs.io/en/stable/reference/envvars.html)).

!!! note
    Make sure to do this *before* importing VBT.

```python title="Disable Numba via an environment variable"
import os

os.environ["NUMBA_DISABLE_JIT"] = "1"
```

```python title="Disable Numba via the config"
from numba import config

config.DISABLE_JIT = True
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can also achieve this by creating a [configuration](https://vectorbt.pro/pvt_6d1b3986/cookbook/configuration/#settings) file 
(such as `vbt.config`) with the following content:

```ini
[numba]
disable = True
```

!!! note
    All commands above must be executed before importing VBT.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To check whether Numba is enabled, use [is_numba_enabled](https://vectorbt.pro/pvt_6d1b3986/api/utils/checks/#vectorbtpro.utils.checks.is_numba_enabled).

```python title="Check whether Numba is enabled"
print(vbt.is_numba_enabled())
```