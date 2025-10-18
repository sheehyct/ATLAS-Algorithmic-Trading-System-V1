---
title: Caching
description: Recipes for caching in VectorBT PRO
icon: material/cached
---

# :material-cached: Caching

When performing a high-level task repeatedly (such as during parameter optimization), it is recommended
to occasionally clear the cache using [clear_cache](https://vectorbt.pro/pvt_6d1b3986/api/registries/ca_registry/#vectorbtpro.registries.ca_registry.clear_cache)
and collect memory garbage. This helps prevent RAM consumption from increasing due to cached and dead
objects.

```python title="Clear cache and collect garbage once every 1000 iterations"
for i in range(1_000_000):
    ...  # (1)!
    
    if i != 0 and i % 1000 == 0:
        vbt.flush()  # (2)!
```

1. Place your code here.
2. Equivalent to calling `vbt.clear_cache()` and `vbt.collect_garbage()`.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To clear the cache for a specific class, method, or instance, pass it directly to the function.

```python title="Clear the cache associated with various objects"
vbt.clear_cache(vbt.PF)  # (1)!
vbt.clear_cache(vbt.PF.total_return)  # (2)!
vbt.clear_cache(pf)  # (3)!
```

1. Applies to all instances and attributes of a specific class.
2. Applies to a specific attribute of all instances of a particular class.
3. Applies to all attributes of a specific class instance.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To display various statistics about the current cache, use [print_cache_stats](https://vectorbt.pro/pvt_6d1b3986/api/registries/ca_registry/#vectorbtpro.registries.ca_registry.print_cache_stats).

```python title="Various way to print cache statistics"
vbt.print_cache_stats()  # (1)!
vbt.print_cache_stats(vbt.PF)  # (2)!
```

1. Displays statistics for the global cache.
2. Displays statistics for a specific object only.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To disable or enable caching globally, use
[disable_caching](https://vectorbt.pro/pvt_6d1b3986/api/registries/ca_registry/#vectorbtpro.registries.ca_registry.disable_caching)
and [enable_caching](https://vectorbt.pro/pvt_6d1b3986/api/registries/ca_registry/#vectorbtpro.registries.ca_registry.enable_caching),
respectively.

```python title="Disable caching globally"
vbt.disable_caching()
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

To disable or enable caching within a code block, use the context managers
[CachingDisabled](https://vectorbt.pro/pvt_6d1b3986/api/registries/ca_registry/#vectorbtpro.registries.ca_registry.CachingDisabled)
and [CachingEnabled](https://vectorbt.pro/pvt_6d1b3986/api/registries/ca_registry/#vectorbtpro.registries.ca_registry.CachingEnabled),
respectively.

```python title="How to disable caching within a code block"
with vbt.CachingDisabled():  # (1)!
    ...  # (2)!

...  # (3)!

with vbt.CachingDisabled(vbt.PF):  # (4)!
    ...
```

1. Disables caching globally.
2. Place your code here that should not use caching.
3. Place your code here that should use the usual behavior.
4. Disables caching for a specific object only.