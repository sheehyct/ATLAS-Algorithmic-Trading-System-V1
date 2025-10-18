---
title: Persistence
description: Recipes for persisting data in VectorBT PRO
icon: material/tray-arrow-down
---

# :material-tray-arrow-down: Persistence

Any Python object can be serialized and saved to disk as a pickle file using [save](https://vectorbt.pro/pvt_6d1b3986/api/utils/pickling/#vectorbtpro.utils.pickling.save).

```python title="Save a dict to a file"
cache = dict(data=data, indicator=indicator, pf=pf)
vbt.save(cache, "cache.pickle")
```

!!! important
    If a file with the same name already exists, it will be overwritten.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

A pickle file can then be loaded and deserialized using [load](https://vectorbt.pro/pvt_6d1b3986/api/utils/pickling/#vectorbtpro.utils.pickling.load).

```python title="Load the dict back"
cache = vbt.load("cache.pickle")
```

!!! note
    The file can be read in another Python environment or even on another machine (such as a cloud
    environment). Just make sure that the Python and package versions on both ends are approximately
    the same.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Pickle files usually take up a considerable amount of space. To reduce the size, compression can be used.
The recommended compression algorithm for binary files is [blosc](https://github.com/Blosc/c-blosc).
To later load the compressed file, pass the `compression` argument in exactly the same way to the loader, 
or simply append the ".blosc" extension to the filename so the loader recognizes it automatically.
The supported algorithms and their possible extensions are listed under `extensions` in
[settings.pickling](https://vectorbt.pro/pvt_6d1b3986/api/_settings/#vectorbtpro._settings.pickling).

```python title="Specify the compression explicitly"
vbt.save(cache, "cache.pickle", compression="blosc")
cache = vbt.load("cache.pickle", compression="blosc")
```

```python title="Specify the compression implicitly"
vbt.save(cache, "cache.pickle.blosc")
cache = vbt.load("cache.pickle.blosc")
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

VBT objects that subclass [Pickleable](https://vectorbt.pro/pvt_6d1b3986/api/utils/pickling/#vectorbtpro.utils.pickling.Pickleable)
can also be saved individually. The benefit is that the class name and, optionally, the compression 
algorithm will be included in the filename by default, making loading simpler. The object can be 
loaded back using the `load()` method of the object's class.

```python title="Save a portfolio under 'Portfolio.pickle.blosc' and load it back"
pf.save(compression="blosc")
pf = vbt.PF.load()
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

If a VBT object was saved with an older package version and loading it with a newer version throws 
an error (for example, due to a different argument order), the object can still be reconstructed by 
creating and registering a [RecInfo](https://vectorbt.pro/pvt_6d1b3986/api/utils/pickling/#vectorbtpro.utils.pickling.RecInfo) instance 
before loading.

```python title="Reconstruct an older BinanceData instance"
def modify_state(rec_state):  # (1)!
    return vbt.RecState(
        init_args=rec_state.init_args,
        init_kwargs=rec_state.init_kwargs,
        attr_dct=rec_state.attr_dct,
    )

rec_info = vbt.RecInfo(
    vbt.get_id_from_class(vbt.BinanceData),
    vbt.BinanceData,
    modify_state
)
rec_info.register()
data = vbt.BinanceData.load()
```

1. Change the arguments to be passed to the class here.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

If you encounter issues with saving an instance of a specific class, set the reconstruction id
`_rec_id` with any string, and then reconstruct the object using this id (the first argument of
`RecInfo`).

```python title="Set a custom identifier to a class and reconstruct its instance using another class"
class MyClass1(vbt.Configured):  # (1)!
    _rec_id = "MyClass"
    ...
    
my_obj = MyClass1()
vbt.save(my_obj, "my_obj")

# (2)!

class MyClass2(vbt.Configured):
    ...

rec_info = vbt.RecInfo("MyClass", MyClass2)
rec_info.register()
my_obj = vbt.load("my_obj")  # (3)!
```

1. `vbt.Configured` can be replaced by any other VBT class that subclasses it.
2. ...restart the kernel...
3. The resulting object is of the class `MyClass2` even though it was saved as `MyClass1`.