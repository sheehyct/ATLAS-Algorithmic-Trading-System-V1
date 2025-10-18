---
title: Signals
description: Recipes for working with signals in VectorBT PRO
icon: material/broadcast
---

# :material-broadcast: Signals

!!! question
    Learn more in the [Signal development tutorial](https://vectorbt.pro/pvt_6d1b3986/tutorials/signal-development/).

## Cleaning

You can clean only two arrays at a time. For more than two arrays, create a custom Numba function to
handle the task.

```python title="Clean 4 arrays"
@njit
def custom_clean_nb(long_en, long_ex, short_en, short_ex):
    new_long_en = np.full_like(long_en, False)
    new_long_ex = np.full_like(long_ex, False)
    new_short_en = np.full_like(short_en, False)
    new_short_ex = np.full_like(short_ex, False)
    
    for col in range(long_en.shape[1]):  # (1)!
        position = 0  # (2)!
        for i in range(long_en.shape[0]):  # (3)!
            if long_en[i, col] and position != 1:
                new_long_en[i, col] = True  # (4)!
                position = 1
            elif short_en[i, col] and position != -1:
                new_short_en[i, col] = True
                position = -1
            elif long_ex[i, col] and position == 1:
                new_long_ex[i, col] = True
                position = 0
            elif short_ex[i, col] and position == -1:
                new_short_ex[i, col] = True
                position = 0
            
    return new_long_en, new_long_ex, new_short_en, new_short_ex
```

1. Iterate over columns (i.e., assets).
2. Set the initial position per column: 0 for no position, 1 for long, and -1 for short.
3. Iterate over rows (i.e., bars).
4. Keep a signal only if the condition above is satisfied; otherwise, skip the signal.

!!! tip
    Convert each input array to NumPy with `arr = vbt.to_2d_array(df)`, and then convert each output
    array back to Pandas with `new_df = df.vbt.wrapper.wrap(arr)`.