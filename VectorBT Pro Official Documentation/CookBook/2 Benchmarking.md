---
title: Benchmarking
description: Recipes for measuring execution time and memory usage in VectorBT PRO
icon: material/tape-measure
---

# :material-tape-measure: Benchmarking

To measure the execution time of a code block by running it __only once__, use the
[Timer](https://vectorbt.pro/pvt_6d1b3986/api/utils/profiling/#vectorbtpro.utils.profiling.Timer).

```python title="Measure execution time by running once"
with vbt.Timer() as timer:
    my_pipeline()
  
print(timer.elapsed())
```

!!! note
    The code block may depend on Numba functions that need to be compiled first. To exclude
    any compilation time from the estimate (recommended since compilation may take up to a minute
    while the code block may execute in milliseconds), dry-run the code block.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Another way is to run a code block multiple times and evaluate a statistic, such as the shortest 
average execution time. This is easy to do using the [timeit](https://docs.python.org/3/library/timeit.html)
module and the corresponding vectorbtpro function, which returns the result in a human-readable format.
The benefit of this approach is that it effectively ignores any compilation overhead.

```python title="Measure execution time by running multiple times"
print(vbt.timeit(my_pipeline))
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

There is also a profiling tool for measuring peak memory usage:
[MemTracer](https://vectorbt.pro/pvt_6d1b3986/api/utils/profiling/#vectorbtpro.utils.profiling.MemTracer), which helps determine
the approximate size of all objects generated when running a code block.

```python title="Measure peak memory usage by running once"
with vbt.MemTracer() as tracer:
    my_pipeline()
  
print(tracer.peak_usage())
```