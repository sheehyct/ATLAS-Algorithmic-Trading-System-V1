---
title: Knowledge
description: Recipes for managing knowledge assets in VectorBT PRO
icon: material/message-text-outline
---

# :material-message-text-outline: Knowledge

## Assets

Knowledge assets are instances of [KnowledgeAsset](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/base_assets/#vectorbtpro.utils.knowledge.base_assets.KnowledgeAsset)
that contain a list of Python objects (most often dicts) and provide various methods to manipulate them.
For usage examples, see the API documentation for each specific method.

### VBT assets

There are two knowledge assets in VBT: 1) website pages, and 2) Discord messages. The first asset includes
pages and headings from the (mainly private) website. Each data item represents either a page or a page
heading. Pages generally point to one or more other pages or headings, while headings contain text content,
all reflecting the structure of Markdown files. The second asset consists of messages from the "vectorbt.pro"
Discord server, where each data item is a Discord message, which may reference other messages through replies.

The assets are attached to each [release](https://github.com/polakowo/vectorbt.pro/releases) as
`pages.json.zip` and `messages.json.zip`. These are ZIP-compressed JSON files, managed by
[PagesAsset](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.PagesAsset) and
[MessagesAsset](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.MessagesAsset)
classes, respectively. You can load them automatically or manually. For automatic loading, a GitHub token
is required.

!!! hint
    The first pull will download the assets, and subsequent pulls will use cached versions.
    After upgrading VBT, new assets will be downloaded automatically.

```python title="How to load an asset"
env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"  # (1)!
pages_asset = vbt.PagesAsset.pull()
messages_asset = vbt.MessagesAsset.pull()

# ______________________________________________________________

vbt.settings.set("knowledge.assets.vbt.token", "YOUR_GITHUB_TOKEN")  # (2)!
pages_asset = vbt.PagesAsset.pull()
messages_asset = vbt.MessagesAsset.pull()

# ______________________________________________________________

pages_asset = vbt.PagesAsset(/MessagesAsset).pull(release_name="v2024.8.20") # (3)!
pages_asset = vbt.PagesAsset(/MessagesAsset).pull(cache_dir="my_cache_dir") # (4)!
pages_asset = vbt.PagesAsset(/MessagesAsset).pull(clear_cache=True) # (5)!
pages_asset = vbt.PagesAsset(/MessagesAsset).pull(cache=False)  # (6)!

# ______________________________________________________________

pages_asset = vbt.PagesAsset.from_json_file("pages.json.zip") # (7)!
messages_asset = vbt.MessagesAsset.from_json_file("messages.json.zip")
```

1. Set the token as an environment variable.
2. Set the token as a global setting.
3. Use the asset from a different release. By default, the asset of the installed release is used (see `vbt.version`).
4. Specify a custom cache directory. By default, data is stored under 
__$user_cache_dir/knowledge/vbt/$release_name/pages/assets/__ for pages and 
__$user_cache_dir/knowledge/vbt/$release_name/messages/assets/__ for messages.
5. Clear the cache directory and pull the asset again. By default, the asset will not be pulled if it already exists.
6. Create a temporary directory.
7. Load the asset file that has already been downloaded.

### Generic assets

Knowledge assets are not limited to VBT assets—you can build an asset from any list!

```python title="How to load an asset"
asset = vbt.KnowledgeAsset(my_list)  # (1)!
asset = vbt.KnowledgeAsset.from_json_file("my_list.json")  # (2)!
asset = vbt.KnowledgeAsset.from_json_bytes(vbt.load_bytes("my_list.json"))  # (3)!
```

1. Create an instance by wrapping a list directly.
2. Create an instance from a JSON file.
3. Create an instance from JSON bytes.

## Describing

Knowledge assets behave like regular lists, so to describe an asset, you should describe it as a list.
This enables many analysis options, such as checking the length, printing out a random data item, and
more advanced options like printing out the field schema. Most data items in an asset are dicts, so you 
can describe them by their fields.

```python title="How to describe an asset"
print(len(asset))  # (1)!

asset.sample().print()  # (2)!
asset.print_sample()

asset.print_schema()  # (3)!

vbt.pprint(messages_asset.describe())  # (4)!

pages_asset.print_site_schema()  # (5)!
```

1. Get the number of data items.
2. Pick a random data item and print it.
3. Visualize the asset's field schema as a tree. Shows each field, including frequency and type.
Works on all assets where data items are dicts.
4. Describe each field. Works on all assets where data items are dicts.
5. Visualize the URL schema as a tree. Works on pages and headings only.

## Manipulating

A knowledge asset is simply an advanced list: it looks like a VBT object, but behaves like a list.
For manipulation, it provides a collection of methods ending with `item` or `items` to get, set, or
remove data items—either by returning a new asset instance (default) or modifying the asset in place.

```python title="How to manipulate an asset"
d = asset.get_items(0)  # (1)!
d = asset[0]
data = asset[0:100]  # (2)!
data = asset[mask]  # (3)!
data = asset[indices]  # (4)!

# ______________________________________________________________

new_asset = asset.set_items(0, new_d)  # (5)!
asset.set_items(0, new_d, inplace=True)  # (6)!
asset[0] = new_d  # (7)!
asset[0:100] = new_data
asset[mask] = new_data
asset[indices] = new_data

# ______________________________________________________________

new_asset = asset.delete_items(0)  # (8)!
asset.delete_items(0, inplace=True)
asset.remove(0)
del asset[0]
del asset[0:100]
del asset[mask]
del asset[indices]

# ______________________________________________________________

new_asset = asset.append_item(new_d)  # (9)!
asset.append_item(new_d, inplace=True)
asset.append(new_d)

# ______________________________________________________________

new_asset = asset.extend_items([new_d1, new_d2])  # (10)!
asset.extend_items([new_d1, new_d2], inplace=True)
asset.extend([new_d1, new_d2])
asset += [new_d1, new_d2]

# ______________________________________________________________

print(d in asset)  # (11)!
print(asset.index(d))  # (12)!
print(asset.count(d))  # (13)!

# ______________________________________________________________

for d in asset:  # (14)!
    ...
```

1. Get the first data item.
2. Get the first 100 data items.
3. Get the data items that correspond to True in the mask.
4. Get the data items at the positions in the index array.
5. Set the first data item and return a new asset instance.
6. Set the first data item by modifying the asset in place.
7. Built-in methods always modify the existing asset instance.
8. Remove the first data item.
9. Append a new data item.
10. Extend with new data items.
11. Check if the asset contains a data item.
12. Get the position of a data item in the asset.
13. Get the number of data items matching a specific data item.
14. Iterate over data items.

## Querying

A wide range of methods are available to query an asset:
[get](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/base_assets/#vectorbtpro.utils.knowledge.base_assets.KnowledgeAsset.get) /
[select](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/base_assets/#vectorbtpro.utils.knowledge.base_assets.KnowledgeAsset.select),
[query](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/base_assets/#vectorbtpro.utils.knowledge.base_assets.KnowledgeAsset.query) /
[filter](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/base_assets/#vectorbtpro.utils.knowledge.base_assets.KnowledgeAsset.filter),
and [find](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/base_assets/#vectorbtpro.utils.knowledge.base_assets.KnowledgeAsset.find).
The first pair is used to get and process one or more fields from each data item. The `get` method returns the
raw output, while the `select` method returns a new asset instance. The second pair lets you run queries on
the asset using various engines, such as JMESPath. Again, the `query` method returns the raw output, while
the `filter` method returns a new asset instance. Finally, the `find` method is specialized for searching
across one or more fields. By default, it returns a new asset instance.

```python title="How to query an asset"
messages = messages_asset.get()  # (1)!
total_reactions = sum(messages_asset.get("reactions"))  # (2)!
first_attachments = messages_asset.get("attachments[0]['content']", skip_missing=True)  # (3)!
first_attachments = messages_asset.get("attachments.0.content", skip_missing=True)  # (4)!
stripped_contents = pages_asset.get("content", source="x.strip() if x else ''")  # (5)!
stripped_contents = pages_asset.get("content", source=lambda x: x.strip() if x else '')  # (6)!
stripped_contents = pages_asset.get(source="content.strip() if content else ''")  # (7)!

# (8)!

all_contents = pages_asset.select("content").remove_empty().get()  # (9)!
all_attachments = messages_asset.select("attachments").merge().get()  # (10)!
combined_content = messages_asset.select(source=vbt.Sub('[$author] $content')).join()  # (11)!

# ______________________________________________________________

user_questions = messages_asset.query("content if '@maintainer' in mentions else vbt.NoResult")  # (12)!
is_user_question = messages_asset.query("'@maintainer' in mentions", return_type="bool")  # (13)!
all_attachments = messages_asset.query("[].attachments | []", query_engine="jmespath")  # (14)!
all_classes = pages_asset.query("name[obj_type == 'class'].sort_values()", query_engine="pandas")  # (15)!

# (16)!

support messages = messages_asset.filter("channel == 'support'")  # (17)!

# ______________________________________________________________

new_messages_asset = messages_asset.find("@maintainer")  # (18)!
new_messages_asset = messages_asset.find("@maintainer", path="author")  # (19)!
new_messages_asset = messages_asset.find(vbt.Not("@maintainer"), path="author")  # (20)!
new_messages_asset = messages_asset.find(  # (21)!
    ["@maintainer", "from_signals"], 
    path=["author", "content"], 
    find_all=True
)

found_fields = messages_asset.find(  # (22)!
    ["vbt.Portfolio", "vbt.PF"], 
    return_type="field"
).get()
found_code_matches = messages_asset.find(  # (23)!
    r"(?<!`)`([^`]*)`(?!`)", 
    mode="regex", 
    return_type="match",
).sort().get()
```

1. Get all data items. This is the same as `messages_asset.data`.
2. Get the value from a simple field in each data item. Here, retrieve and sum the number of reactions.
3. Get the value from a nested field in each data item. If the field does not always exist,
skip data items where it is missing.
4. You can also use dot notation for the path to the value.
5. Post-process the value using a source expression. Here, strip the selected value for "content".
6. The source can also be a function.
7. If no value is selected, the source expression or function is applied to the entire data item,
with the data item referred to as "x" and its fields accessed by name.
8. If you need to process results further, use `select` instead of `get`. It accepts the same arguments.
9. Select contents while removing None and empty strings.
10. Select attachments, merge them into a list, and extract.
11. Format the author and content into a string, then join those strings.
12. Return the content if @polakowo is in mentions; otherwise, ignore. The expression here works
similarly to the source expression in `get`.
13. Return True if @polakowo is in mentions; otherwise, return False. Without `return_type="bool"`,
it would act as a filter and return the data items matching the condition.
14. Use JMESPath to extract all attachments.
15. You can also use Pandas as a query engine, where each field becomes a Series.
Here, get the heading name for every data item with object type "class", and sort.
16. If you need to process results further, use `filter` instead of `query`. It accepts the same arguments.
17. Filter messages that belong to the support channel.
18. Find messages that mention @polakowo in any field.
19. Find messages where @polakowo is the author.
20. Find messages where @polakowo is not the author.
21. Find messages where @polakowo is the author and `from_signals` is mentioned in the content.
If `find_all` is False, the conjunction would be "or".
22. Find all fields mentioning either `vbt.Portfolio` or `vbt.PF`.
23. Find all regex matches for code snippets using a single backtick.

!!! tip
    To make chained calls easier to read, use either of the following styles:

    ```python title="How to find admonition types"
    admonition_types = (
        pages_asset.find(
            r"!!!\s+(\w+)", 
            mode="regex", 
            return_type="match"
        )
        .sort()
        .get()
    )
    admonition_types = pages_asset.chain([
        ("find", (r"!!!\s+(\w+)",), dict(mode="regex", return_type="match")),
        "sort",
        "get"
    ])
    ```

### Code

There is a specialized method for finding code, either in single backticks or code blocks.

```python title="How to find code"
found_code_blocks = messages_asset.find_code().get()  # (1)!
found_code_blocks = messages_asset.find_code(language="python").get()  # (2)!
found_code_blocks = messages_asset.find_code(language=True).get()  # (3)!
found_code_blocks = messages_asset.find_code("from_signals").get()  # (4)!
found_code_blocks = messages_asset.find_code("from_signals", in_blocks=False).get()  # (5)!
found_code_blocks = messages_asset.find_code("from_signals", path="attachments").get()  # (6)!
```

1. Find any code blocks across all fields.
2. Find any Python code blocks across all fields.
3. Find code blocks annotated with any language across all fields.
4. Find code blocks that mention `from_signals` across all fields.
5. Find code that mentions `from_signals` across all fields.
6. Find code blocks that mention `from_signals` within attachments.

### Links

Custom knowledge assets like pages and messages have specialized methods for finding data items by
their link. The default behavior matches the target against the end of each link. This approach ensures
that searching for both "https://vectorbt.pro/become-a-member/" and "become-a-member/" will consistently
return "https://vectorbt.pro/become-a-member/". When using "exact" or "end" mode, a variant with or without
a slash is automatically included. This way, searching for "become-a-member" (without a slash) will still
return "https://vectorbt.pro/become-a-member/". The method also ignores other matched links like
"https://vectorbt.pro/become-a-member/#become-a-member" since they belong to the same page.

```python title="How to find links"
new_messages_asset = messages_asset.find_link(  # (1)!
    "https://discord.com/channels/918629562441695344/919715148896301067/923327319882485851"
)
new_messages_asset = messages_asset.find_link("919715148896301067/923327319882485851")  # (2)!

new_pages_asset = pages_asset.find_page(  # (3)!
    "https://vectorbt.pro/pvt_xxxxxxxx/getting-started/installation/"
)
new_pages_asset = pages_asset.find_page("https://vectorbt.pro/pvt_6d1b3986/getting-started/installation/")  # (4)!
new_pages_asset = pages_asset.find_page("installation/")
new_pages_asset = pages_asset.find_page("installation")  # (5)!
new_pages_asset = pages_asset.find_page("installation", aggregate=True)  # (6)!
```

1. Find the message using a Discord URL.
2. Find the message using a suffix such as `channel_id/message_id`.
3. Find the page using a website URL.
4. Find the page using a suffix.
5. A slash will be added automatically if needed.
6. Find the page and also [aggregate](#aggregating) it.

### Objects

You can also find headings that correspond to VBT objects.

```python title="How to find an object"
new_pages_asset = pages_asset.find_obj(vbt.Portfolio)  # (1)!
new_pages_asset = pages_asset.find_obj(vbt.Portfolio, aggregate=True)  # (2)!
new_pages_asset = pages_asset.find_obj(vbt.PF.from_signals, aggregate=True)
new_pages_asset = pages_asset.find_obj(vbt.pf_nb, aggregate=True)
new_pages_asset = pages_asset.find_obj("SignalContext", aggregate=True)
```

1. Get the top-level heading corresponding to the class `Portfolio`.
2. Get the top-level heading corresponding to the class `Portfolio` along with all sub-headings.

### Nodes

You can also traverse pages and messages in a way similar to navigating nodes within a graph.

```python title="How to traverse an asset"
new_vbt_asset = vbt_asset.select_previous(link)  # (1)!
new_vbt_asset = vbt_asset.select_next(link)

# ______________________________________________________________

new_pages_asset = pages_asset.select_parent(link)  # (2)!
new_pages_asset = pages_asset.select_children(link)
new_pages_asset = pages_asset.select_siblings(link)
new_pages_asset = pages_asset.select_descendants(link)
new_pages_asset = pages_asset.select_branch(link)
new_pages_asset = pages_asset.select_ancestors(link)
new_pages_asset = pages_asset.select_parent_page(link)
new_pages_asset = pages_asset.select_descendant_headings(link)

# ______________________________________________________________

new_messages_asset = messages_asset.select_reference(link)
new_messages_asset = messages_asset.select_replies(link)
new_messages_asset = messages_asset.select_block(link)  # (3)!
new_messages_asset = messages_asset.select_thread(link)
new_messages_asset = messages_asset.select_channel(link)
```

1. These methods and those below work on both pages and messages.
2. These methods and those below do not include the link by default (use `incl_link=True` to include it).
3. These methods and those below include the link by default (use `incl_link=False` to exclude it).

!!! note
    Each operation requires at least one full data pass; use sparingly.

## Applying

"Find" and many other methods rely on [KnowledgeAsset.apply](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/base_assets/#vectorbtpro.utils.knowledge.base_assets.KnowledgeAsset.apply),
which executes a function on each data item. These are called asset functions and consist of two
parts: argument preparation and function calling. The main advantage is that arguments are prepared
only once, then passed to each function call. Execution is managed by the powerful
[execute](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute) function, which supports parallelization.

```python title="How to apply a function to an asset"
links = messages_asset.apply("get", "link")  # (1)!

from vectorbtpro.utils.knowledge.base_asset_funcs import GetAssetFunc  # (2)!
args, kwargs = GetAssetFunc.prepare("link")
links = [GetAssetFunc.call(d, *args, **kwargs) for d in messages_asset]

# ______________________________________________________________

links_asset = messages_asset.apply(lambda d: d["link"])  # (3)!
links = messages_asset.apply(lambda d: d["link"], wrap=False)  # (4)!
json_asset = messages_asset.apply(vbt.dump, dump_engine="json")  # (5)!

# ______________________________________________________________

new_asset = asset.apply(  # (6)!
    ...,
    execute_kwargs=dict(
        n_chunks="auto",
        distribute="chunks",
        engine="processpool"
    )
)
```

1. Apply a built-in function. This is equivalent to `get("link")`. Depending on the function,
either a new asset instance or the raw output is returned.
2. The same as above, but performed manually.
3. Apply a custom function. By default, returns a new asset instance.
4. Apply a custom function and return the raw output.
5. Any function that takes a single argument can be used. Here, each message is serialized with JSON.
6. Any operation can be distributed by specifying execution-related keyword arguments.

### Pipelines

Most examples show how to run a chain of standalone operations, but each operation processes the
data at least once. To process data just once, regardless of the number of operations, use asset pipelines.
There are two types: basic and complex. Basic pipelines take a list of tasks (such as functions and
their arguments) and compose them into a single operation that acts on a data item. This composed
operation is then applied to all data items. Complex pipelines use a Python expression in a
functional style, where one function receives a data item and returns a result that becomes
the argument for the next function.

```python title="How to apply a pipeline to an asset"
tasks = [("find", ("@maintainer",), dict(return_type="match")), len, "get"]  # (1)!
tasks = [vbt.Task("find", "@maintainer", return_type="match"), vbt.Task(len), vbt.Task("get")]  # (2)!
mention_count = messages_asset.apply(tasks)  # (3)!

asset_pipeline = vbt.BasicAssetPipeline(tasks) # (4)!
mention_count = [asset_pipeline(d) for d in messages_asset]

# ______________________________________________________________

expression = "get(len(find(d, '@maintainer', return_type='match')))"
mention_count = messages_asset.apply(expression)  # (5)!

asset_pipeline = vbt.ComplexAssetPipeline(expression)  # (6)!
mention_count = [asset_pipeline(d) for d in messages_asset]
```

1. Tasks can be provided as strings, tuples, or functions.
2. Tasks can also be given as instances of [Task](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.Task).
3. Use a list of tasks to get the number of @polakowo mentions in each message.
4. The same as above, but performed manually.
5. Use an expression to get the number of @polakowo mentions in each message.
6. The same as above, but performed manually.

!!! info
    In both pipeline types, arguments are prepared only once during initialization.

### Reducing

[Reducing](https://realpython.com/python-reduce-function/) means merging all data items into one.
This requires a function that takes two data items. Initially, these two data items are the initializer
(such as an empty dict) and the first data item. If the initializer is unknown, the first two
data items are used. The result of this first iteration is then used as the first data item in
the next iteration. Execution is handled by [KnowledgeAsset.reduce](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/base_assets/#vectorbtpro.utils.knowledge.base_assets.KnowledgeAsset.reduce)
and cannot be parallelized since each iteration depends on the previous one.

```python title="How to reduce an asset"
all_attachments = messages_asset.select("attachments").reduce("merge_lists")  # (1)!

from vectorbtpro.utils.knowledge.base_asset_funcs import MergeListsAssetFunc  # (2)!
args, kwargs = MergeListsAssetFunc.prepare()
d1 = []
for d2 in messages_asset.select("attachments"):
    d1 = MergeListsAssetFunc.call(d1, d2, *args, **kwargs)
all_attachments = d1

# ______________________________________________________________

total_reactions = messages_asset.select("reactions").reduce(lambda d1, d2: d1 + d2)  # (3)!
```

1. Apply a built-in function. This is equivalent to `select("attachments").merge_lists()`.
Depending on the function, either a new asset instance or the raw output is returned.
2. The same as above, but performed manually.
3. Apply a custom function. By default, returns the raw output.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can also split a knowledge asset into groups and reduce those groups. Group iteration is handled
by the [execute](https://vectorbt.pro/pvt_6d1b3986/api/utils/execution/#vectorbtpro.utils.execution.execute) function, which supports
parallelization.

```python title="How to reduce groups of an asset"
reactions_by_channel = messages_asset.groupby_reduce(  # (1)!
    lambda d1, d2: d1 + d2["reactions"],
    by="channel",
    initializer=0,
    return_group_keys=True
)

# ______________________________________________________________

result = asset.groupby_reduce(  # (2)!
    ...,
    execute_kwargs=dict(
        n_chunks="auto",
        distribute="chunks",
        engine="processpool"
    )
)
```

1. Get the total number of reactions per channel.
2. Any group-by operation can be distributed by specifying execution-related keyword arguments.

## Aggregating

Since headings are represented as individual data items, they can be aggregated back into their
parent page. This is useful when you want to [format](#formatting) or [display](#browsing) the page.
Note that only headings can be aggregated; pages themselves cannot be aggregated into other pages.

```python title="How to aggregate pages"
new_pages_asset = pages_asset.aggregate()  # (1)!
new_pages_asset = pages_asset.aggregate(append_obj_type=False, append_github_link=False)  # (2)!
```

1. Aggregate headings into the content of the parent page.
2. The same as above, but do not append object type and GitHub source to the API headings.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Messages, on the other hand, can be aggregated across multiple levels: _"message"_, _"block"_, _"thread"_, 
and _"channel"_. Aggregation here means collecting messages that belong to the specified level,
and dumping them into the content of a single, bigger message.

* The _"message"_ level means attachments are included in the content of the message.
* The _"block"_ level combines messages from the same author that reference the same block or
do not reference anything. The link for the block is the link of the first message in the block.
* The _"thread"_ level combines messages from the same channel that are connected by a chain of replies.
The link for the thread is the link of the first message in the thread.
* The _"channel"_ level combines all messages that belong to the same channel.

```python title="How to aggregate messages"
new_messages_asset = messages_asset.aggregate()  # (1)!
new_messages_asset = messages_asset.aggregate(by="message")  # (2)!
new_messages_asset = messages_asset.aggregate(by="block")  # (3)!
new_messages_asset = messages_asset.aggregate(by="thread")  # (4)!
new_messages_asset = messages_asset.aggregate(by="channel")  # (5)!
new_messages_asset = messages_asset.aggregate(
    ...,
    minimize_metadata=True  # (6)!
)
new_messages_asset = messages_asset.aggregate(
    ...,
    dump_metadata_kwargs=dict(dump_engine="nestedtext")  # (7)!
)
```

1. Aggregate into the content of the parent if only one parent exists; otherwise, an error will be raised.
2. Aggregate attachments into the content of the parent message.
3. Aggregate messages into the content of the parent block.
4. Aggregate messages into the content of the parent thread.
5. Aggregate messages into the content of the parent channel.
6. Remove irrelevant keys from metadata before dumping.
7. When adding messages into the parent content, dump their metadata using the selected engine (here, NestedText).

## Formatting

Most Python objects can be dumped (that is, serialized) into strings.

```python title="How to dump an asset"
new_asset = asset.dump()  # (1)!
new_asset = asset.dump(dump_engine="nestedtext", indent=4)  # (2)!

# ______________________________________________________________

print(asset.dump().join())  # (3)!
print(asset.dump().join(separator="\n\n---------------------\n\n"))  # (4)!
print(asset.dump_all())  # (5)!
```

1. Dump each data item. By default, items are dumped into YAML using Ruamel (if installed) or PyYAML.
2. Dump each data item using a custom engine. In this example, NestedText is used with 4 spaces for indentation.
3. Join all dumped data items. The separator is selected automatically.
4. Join all dumped data items using a custom separator.
5. Dump the entire list as a single object.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Custom knowledge assets such as pages and messages can be converted, and optionally saved, in Markdown
or HTML format. Only the "content" field will be converted; other fields are used to build the metadata
block shown at the start of each file.

!!! note
    Without [aggregation](#aggregating), each page heading will become a separate file.

```python title="How to format an asset"
new_pages_asset = pages_asset.to_markdown()  # (1)!
new_pages_asset = pages_asset.to_markdown(root_metadata_key="pages")  # (2)!
new_pages_asset = pages_asset.to_markdown(clear_metadata=False)  # (3)!
new_pages_asset = pages_asset.to_markdown(remove_code_title=False, even_indentation=False)  # (4)!

dir_path = pages_asset.save_to_markdown()  # (5)!
dir_path = pages_asset.save_to_markdown(cache_dir="markdown")  # (6)!
dir_path = pages_asset.save_to_markdown(clear_cache=True)  # (7)!
dir_path = pages_asset.save_to_markdown(cache=False)  # (8)!

# (9)!

# ______________________________________________________________

new_pages_asset = pages_asset.to_html()  # (10)!
new_pages_asset = pages_asset.to_html(to_markdown_kwargs=dict(root_metadata_key="pages"))  # (11)!
new_pages_asset = pages_asset.to_html(make_links=False)  # (12)!
new_pages_asset = pages_asset.to_html(extensions=[], use_pygments=False)  # (13)!

extensions = vbt.settings.get("knowledge.formatting.markdown_kwargs.extensions")
new_pages_asset = pages_asset.to_html(extensions=extensions + ["pymdownx.smartsymbols"])  # (14)!

extensions = vbt.settings.get("knowledge.formatting.markdown_kwargs.extensions")
extensions.append("pymdownx.smartsymbols")  # (15)!

extension_configs = vbt.settings.get("knowledge.formatting.markdown_kwargs.extension_configs")
extension_configs["pymdownx.superfences"]["preserve_tabs"] = False  # (16)!

new_pages_asset = pages_asset.to_html(format_html_kwargs=dict(pygments_kwargs=dict(style="dracula")))  # (17)!
vbt.settings.set("knowledge.formatting.pygments_kwargs.style", "dracula")  # (18)!

style_extras = vbt.settings.get("knowledge.formatting.style_extras")
style_extras.append("""
.admonition.success {
    background-color: #00c8531a;
    border-left-color: #00c853;
}
""")  # (19)!

head_extras = vbt.settings.get("knowledge.formatting.head_extras")
head_extras.append('<link ...>')  # (20)!

body_extras = vbt.settings.get("knowledge.formatting.body_extras")
body_extras.append('<script>...</script>')  # (21)!

vbt.settings.get("knowledge.formatting").reset()  # (22)!

dir_path = pages_asset.save_to_html()  # (23)!

# (24)!
```

1. Convert each data item to a Markdown-formatted string. Returns a new asset instance with a list of strings.
2. Prepend a root key called "pages" (or "messages" for messages) to the metadata block.
3. Keep empty fields in the metadata block. By default, empty fields are removed.
4. Keep the content as is, without removing code titles or adjusting uneven indentation.
5. Save each data item to a Markdown-formatted file. Returns the path to the parent directory.
By default, saves to __$user_cache_dir/knowledge/vbt/$release_name/pages/markdown/__ for pages and
__$user_cache_dir/knowledge/vbt/$release_name/messages/markdown/__ for messages.
6. Specify a different cache directory.
7. Clear the cache directory before saving. By default, a data item is skipped if its file already exists.
8. Create a temporary directory.
9. The `save_to_markdown` method accepts the same arguments as `to_markdown`.
10. Convert each data item to an HTML-formatted string. Returns a new asset instance with a list of strings.
11. The same options available for the `to_markdown` method can be set using `to_markdown_kwargs`.
12. If a URL is found in text, do not make it a link. By default, all URLs become clickable.
13. Disable all Markdown extensions and do not use Pygments for highlighting.
14. Add a new extension to the preset list of Markdown extensions (locally).
15. Add a new extension to the preset list of Markdown extensions (globally).
16. Change a configuration of a Markdown extension.
17. Change the default Pygments highlighting style (locally).
18. Change the default Pygments highlighting style (globally).
19. Add extra CSS at the end of the `<style>` element.
20. Add extra HTML, such as links, at the end of the `<head>` element.
21. Add extra HTML, such as JavaScript, at the end of the `<body>` element.
22. Reset formatting.
23. Save each data item to an HTML-formatted file. Returns the path to the parent directory.
By default, saves to __$user_cache_dir/knowledge/vbt/$release_name/pages/html/__ for pages and
__$user_cache_dir/knowledge/vbt/$release_name/pages/html/__ for messages.
24. The `save_to_html` method accepts the same arguments as `to_html` and `save_to_markdown`.

### Browsing

Pages and messages can be displayed and browsed using static HTML files. When displaying a single item,
VBT creates a temporary HTML file and opens it in the default browser. All links in this file remain
__external__. When displaying multiple items, VBT creates a single HTML file
where the items are shown as iframes that you can navigate using pagination.

```python title="How to display an asset"
file_path = pages_asset.display()  # (1)!
file_path = pages_asset.display(link="documentation/fundamentals")  # (2)!
file_path = pages_asset.display(link="documentation/fundamentals", aggregate=True)  # (3)!

# ______________________________________________________________

file_path = messages_asset.display()  # (4)!
file_path = messages_asset.display(link="919715148896301067/923327319882485851")  # (5)!
file_path = messages_asset.filter("channel == 'announcements'").display()  # (6)!
```

1. Display one or more pages.
2. Select a page to display.
3. If the asset is not aggregated, select a page, find its headings, merge them into one page, and display.
4. Display one or more messages.
5. Choose a message to display.
6. Select messages from the specified channel, aggregate them, and display.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

If you want to browse one or more pages (or headings) like a website, VBT can convert all data items to HTML
and replace all external links with __internal__ links, allowing you to navigate from one page to another locally.
But which page appears first? Pages and headings create a directed graph. If there is a single page from which
all other pages can be accessed, that page is displayed first. If there are multiple such pages, VBT creates
an index page with metadata blocks that let you access the other pages (unless you specify `entry_link`).

```python title="How to browse an asset"
dir_path = pages_asset.browse()  # (1)!
dir_path = pages_asset.browse(aggregate=True)  # (2)!
dir_path = pages_asset.browse(entry_link="documentation/fundamentals", aggregate=True)  # (3)!
dir_path = pages_asset.browse(entry_link="documentation", descendants_only=True, aggregate=True)  # (4)!
dir_path = pages_asset.browse(cache_dir="website")  # (5)!
dir_path = pages_asset.browse(clear_cache=True)  # (6)!
dir_path = pages_asset.browse(cache=False)  # (7)!

# ______________________________________________________________

dir_path = messages_asset.browse()  # (8)!
dir_path = messages_asset.browse(entry_link="919715148896301067/923327319882485851")  # (9)!

# (10)!
```

1. Generate an HTML file for every page and heading (unless already aggregated).
2. Aggregate headings into pages and generate an HTML file for each page.
3. Generate an HTML file for every page and start browsing from the selected page.
4. Generate an HTML file for every page that is a descendant of the selected page.
5. Specify a different cache directory. By default, data is stored under 
__$user_cache_dir/knowledge/vbt/$release_name/pages/html/__ for pages and 
__$user_cache_dir/knowledge/vbt/$release_name/messages/html/__ for messages.
6. Clear the cache directory before saving. By default, a page or heading is skipped if its file already exists.
7. Create a temporary directory.
8. Generate an HTML file for every message (note that there may be a large number of messages!).
9. In addition to the above, select a message to open in the default browser.
10. Messages also accept the same caching-related arguments as pages.

## Combining

Assets can be easily combined. If the target class is not specified, their common superclass is used.
For example, combining [PagesAsset](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.PagesAsset)
and [MessagesAsset](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.MessagesAsset)
produces an instance of [VBTAsset](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.VBTAsset),
which includes features shared by both assets, such as the "link" and "content" fields.

```python title="How to combine multiple assets"
vbt_asset = pages_asset + messages_asset  # (1)!
vbt_asset = pages_asset.combine(messages_asset)  # (2)!
vbt_asset = vbt.VBTAsset.combine(pages_asset, messages_asset)  # (3)!
```

1. Concatenate both lists and wrap them with the common superclass.
2. Concatenate both lists and wrap them with the first class.
3. Concatenate both lists and wrap them with the selected class.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

If both assets contain the same number of data items, you can also merge them at the data item level.
This method works for complex containers, such as nested dictionaries and lists, by flattening their
nested structures into flat dictionaries, merging them, and then unflattening them back into the original
container types.

```python title="How to merge multiple assets"
new_asset = asset1.merge(asset2)  # (1)!
new_asset = vbt.KnowledgeAsset.merge(asset1, asset2)  # (2)!
```

1. Merge both lists and wrap them with the first class.
2. Merge both lists and wrap them with the selected class.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

You can also merge all data items in a single asset into one data item.

```python title="How to merge one asset"
new_asset = asset.merge()  # (1)!
new_asset = asset.merge_dicts()  # (2)!
new_asset = asset.merge_lists()  # (3)!
```

1. Calls either `merge_dicts` or `merge_lists` depending on the data type.
2. Concatenate all lists into one.
3. (Deep-)merge all dictionaries into one.

## Searching

### For objects

There are four methods for searching for any VBT object in pages and messages. The first method
searches for the API documentation of the object. The second method searches for mentions of the object in
the non-API (human-readable) documentation. The third method searches for mentions of the object in Discord
messages. The last method searches for mentions of the object in the code of both pages and messages.

```python title="How to find API-related knowledge about an object"
api_asset = vbt.find_api(vbt.PFO)  # (1)!
api_asset = vbt.find_api(vbt.PFO, incl_bases=False, incl_ancestors=False)  # (2)!
api_asset = vbt.find_api(vbt.PFO, use_parent=True)  # (3)!
api_asset = vbt.find_api(vbt.PFO, use_refs=True)  # (4)!
api_asset = vbt.find_api(vbt.PFO.row_stack)  # (5)!
api_asset = vbt.find_api(vbt.PFO.from_uniform, incl_refs=False)  # (6)!
api_asset = vbt.find_api([vbt.PFO.from_allocate_func, vbt.PFO.from_optimize_func])  # (7)!

# ______________________________________________________________

api_asset = vbt.PFO.find_api()  # (8)!
api_asset = vbt.PFO.find_api(attr="from_optimize_func")
```

1. Find the (aggregated) API page for [PortfolioOptimizer](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer).
It includes the (aggregated) base classes, such as [Configured](https://vectorbt.pro/pvt_6d1b3986/api/utils/pickling/#vectorbtpro.utils.pickling.Configured),
and (non-aggregated) parent modules, such as [portfolio.pfopt.base](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base).
2. Do not include base classes and parent modules; include only this class.
3. Use the (aggregated) parent of this class instead. Here, [portfolio.pfopt.base](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base).
4. Include the (non-aggregated) pages of objects referenced by this object.
5. Find the API page for [PortfolioOptimizer.row_stack](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer.row_stack).
It includes (aggregated) base methods, such as [Wrapping.row_stack](https://vectorbt.pro/pvt_6d1b3986/api/base/wrapping/#vectorbtpro.base.wrapping.Wrapping.row_stack),
(non-aggregated) parent objects such as [PortfolioOptimizer](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer),
and (non-aggregated) references.
6. Do not include references.
7. Search for multiple objects.
8. Call the method directly from the object's interface.

```python title="How to find documentation-related knowledge about an object"
docs_asset = vbt.find_docs(vbt.PFO)  # (1)!
docs_asset = vbt.find_docs(vbt.PFO, incl_shortcuts=False, incl_instances=False)  # (2)!
docs_asset = vbt.find_docs(vbt.PFO, incl_custom=["pf_opt"])  # (3)!
docs_asset = vbt.find_docs(vbt.PFO, incl_custom=[r"pf_opt\s*=\s*.+"], is_custom_regex=True)  # (4)!
docs_asset = vbt.find_docs(vbt.PFO, as_code=True)  # (5)!
docs_asset = vbt.find_docs([vbt.PFO.from_allocate_func, vbt.PFO.from_optimize_func])  # (6)!

docs_asset = vbt.find_docs(vbt.PFO, up_aggregate_th=0)  # (7)!
docs_asset = vbt.find_docs(vbt.PFO, up_aggregate_pages=True)  # (8)!
docs_asset = vbt.find_docs(vbt.PFO, incl_pages=["documentation", "tutorials"])  # (9)!
docs_asset = vbt.find_docs(vbt.PFO, incl_pages=[r"(features|cookbook)"], page_find_mode="regex")  # (10)!
docs_asset = vbt.find_docs(vbt.PFO, excl_pages=["release-notes"])  # (11)!

# ______________________________________________________________

docs_asset = vbt.PFO.find_docs()  # (12)!
docs_asset = vbt.PFO.find_docs(attr="from_optimize_func")
```

1. Find mentions of [PortfolioOptimizer](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer)
across all non-API pages. It searches for full reference names, shortcuts (such as `vbt.PFO`),
imports (such as `from ... import PFO`), typical instance names (such as `pfo =`), and access or call
notations (such as `PFO.`).
2. Include only full reference names and imports.
3. Include custom literal mentions.
4. Include custom regex mentions.
5. Find mentions only as code.
6. Search for multiple objects.
7. By default, if the method matches two-thirds of all headings sharing the same parent,
it takes the (aggregated) parent instead. Here, it takes the entire page if any mention is found.
8. Similarly, if the method matches two-thirds of all pages sharing the same parent page,
it includes the parent page as well.
9. Include only the links from "documentation" and "tutorials" (the targets are substrings).
10. Include only the links from "features" and "cookbook" (the target is a regex).
11. Exclude the links from "release-notes" (the target is a substring).
12. Call the method directly from the object's interface.

```python title="How to find Discord-related knowledge about an object"
messages_asset = vbt.find_messages(vbt.PFO)  # (1)!

# ______________________________________________________________

messages_asset = vbt.PFO.find_messages()  # (2)!
messages_asset = vbt.PFO.find_messages(attr="from_optimize_func")
```

1. This method works the same as above but finds mentions in messages. It accepts the same arguments
related to targets (the first block in `find_docs` recipes) and does not accept arguments related
to pages (the second block in `find_docs` recipes).
2. Call the method directly from the object's interface.

```python title="How to find code examples of an object"
examples_asset = vbt.find_examples(vbt.PFO)  # (1)!

# ______________________________________________________________

examples_asset = vbt.PFO.find_examples()  # (2)!
examples_asset = vbt.PFO.find_examples(attr="from_optimize_func")
```

1. This method works the same as above but finds code mentions in both pages and messages.
2. Call the method directly from the object's interface.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

The first three methods are guaranteed not to overlap, while the last method may return examples
that can also be found by the first three methods. There is also another method that,
by default, calls the first three methods and combines their results into a single asset.
This approach allows you to gather all relevant knowledge about a VBT object.

```python title="How to combine knowledge about an object"
combined_asset = vbt.find_assets(vbt.Trades)  # (1)!
combined_asset = vbt.find_assets(vbt.Trades, asset_names=["api", "docs"])  # (2)!
combined_asset = vbt.find_assets(vbt.Trades, asset_names=["messages", ...])  # (3)!
combined_asset = vbt.find_assets(vbt.Trades, asset_names="all")  # (4)!
combined_asset = vbt.find_assets(  # (5)!
    vbt.Trades, 
    api_kwargs=dict(incl_ancestors=False),
    docs_kwargs=dict(as_code=True),
    messages_kwargs=dict(as_code=True),
)
combined_asset = vbt.find_assets(vbt.Trades, minimize=False)  # (6)!
asset_list = vbt.find_assets(vbt.Trades, combine=False)  # (7)!
combined_asset = vbt.find_assets([vbt.EntryTrades, vbt.ExitTrades])  # (8)!

# ______________________________________________________________

combined_asset = vbt.find_assets("SQL", resolve=False)  # (9)!
combined_asset = vbt.find_assets(["SQL", "database"], resolve=False)  # (10)!

# ______________________________________________________________

messages_asset = vbt.Trades.find_assets()  # (11)!
messages_asset = vbt.Trades.find_assets(attr="plot")
messages_asset = pf.trades.find_assets(attr="expectancy")
```

1. Combine assets for [Trades](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/trades/#vectorbtpro.portfolio.trades.Trades).
2. Use only the API asset and the documentation asset.
3. Place the messages asset first and keep other assets in their usual order by using `...` (Ellipsis).
4. Use all assets, excluding the examples asset (which is already included in other assets).
5. Provide keyword arguments specific to each asset.
6. Disable minimization. This keeps all fields but takes up more context space.
7. Disable combining. Returns a dictionary of assets by their name.
8. Search for multiple objects.
9. Search for arbitrary keywords (not actual VBT objects).
10. Search for multiple keywords.
11. Make a call directly from the object's interface.

```python title="How to browse combined knowledge about an object"
vbt.Trades.find_assets().select("link").print()  # (1)!

file_path = vbt.Trades.find_assets( # (2)!
    asset_names="docs", 
    docs_kwargs=dict(excl_pages="release-notes")
).display()

dir_path = vbt.Trades.find_assets( # (3)!
    asset_names="docs", 
    docs_kwargs=dict(excl_pages="release-notes")
).browse(cache=False)
```

1. Print all found links.
2. Browse all found documentation (excluding release notes) as a single HTML file.
3. Browse all found documentation (excluding release notes) as multiple HTML files.

### Globally

You can search not only for knowledge related to a specific VBT object but also for any VBT items
that match a query in natural language. This process works by embedding both the query and
the data items, calculating their pairwise similarity scores, and sorting the data items by their mean
score in descending order. Since the result contains all the data items from the original set, just
in a different order, it is recommended to select the top-k results before displaying them.

All the methods discussed in [objects](#for-objects) can also be used on queries!

```python title="How to search for knowledge using natural language"
api_asset = vbt.find_api("How to rebalance weekly?", top_k=20)
docs_asset = vbt.find_docs("How to hedge a position?", top_k=20)
messages_asset = vbt.find_messages("How to trade live?", top_k=20)
combined_asset = vbt.find_assets("How to create a custom data class?", top_k=20)
```

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

There is also a specialized [search](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.search)
function that calls [find_assets](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.find_assets),
caches the documents (so the next search runs much faster), and displays the top results
as a static HTML page.

!!! info
    The first time you run this command, it may take up to 15 minutes to prepare and embed documents.
    However, most preparation steps are cached and stored, so future searches will be significantly
    faster without repeating the process.

```python title="How to search for knowledge on VBT using natural language and display top results"
file_path = vbt.search("How to turn df into data?")  # (1)!
found_asset = vbt.search("How to turn df into data?", display=False)  # (2)!
file_path = vbt.search("How to turn df into data?", display_kwargs=dict(open_browser=False))  # (3)!
file_path = vbt.search("How to fix 'Symbols have mismatching columns'?", asset_names="messages")  # (4)!
file_path = vbt.search("How to use templates in signal_func_nb?", asset_names="examples", display=100)  # (5)!
file_path = vbt.search("How to turn df into data?", search_method="embeddings")  # (6)!
```

1. Search API pages, documentation pages, and Discord messages for a query, then display the 20 most relevant results.
2. Return the results instead of displaying them.
3. Do not automatically open the HTML file in the browser.
4. Search Discord messages only.
5. Search and display the 100 most relevant code examples.
6. Disable hybrid mode.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Building an index of embeddings for searching is not always necessary. Instead, you can use BM25,
a fast and reliable algorithm that works completely offline.

```python title="How to search for knowledge on VBT quickly"
file_path = vbt.quick_search("How to fix 'Symbols have mismatching columns'?")
```

!!! hint
    Use this method when your query contains specific keywords. For vague queries, embeddings are a better choice.

## Chatting

Knowledge assets can be used as context when chatting with LLMs. The main method for chatting is
[Contextable.chat](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/chatting/#vectorbtpro.utils.knowledge.chatting.Contextable.chat),
which [dumps](#formatting) the asset instance, combines it with your question and chat history
into messages, sends them to the LLM service, then displays and saves the response. The response
can be shown in various formats, including raw text, Markdown, and HTML. All three formats
support streaming. This method is compatible with multiple LLM APIs, such as OpenAI, LiteLLM, and LLamaIndex.

```python title="How to chat about an asset"
env["OPENAI_API_KEY"] = "<OPENAI_API_KEY>"  # (1)!

# ______________________________________________________________

patterns_tutorial = pages_asset.find_page( # (2)!
    "https://vectorbt.pro/pvt_xxxxxxxx/tutorials/patterns-and-projections/patterns/", 
    aggregate=True
)
patterns_tutorial.chat("How to detect a pattern?")

data_documentation = pages_asset.select_branch("documentation/data").aggregate()  # (3)!
data_documentation.chat("How to convert DataFrame into vbt.Data?")

pfo_api = pages_asset.find_obj(vbt.PFO, aggregate=True)  # (4)!
pfo_api.chat("How to rebalance weekly?")

combined_asset = pages_asset + messages_asset
signal_func_nb_code = combined_asset.find_code("signal_func_nb")  # (5)!
signal_func_nb_code.chat("How to pass an array to signal_func_nb?")

polakowo_messages = messages_asset.filter("author == '@maintainer'").minimize().shuffle()
polakowo_messages.chat("Describe the author of these messages", max_tokens=10_000)  # (6)!

mention_fields = combined_asset.find(
    "parameterize", 
    mode="substring", 
    return_type="field", 
    merge_fields=False
)
mention_counts = combined_asset.find(
    "parameterize", 
    mode="substring", 
    return_type="match", 
    merge_matches=False
).apply(len)
sorted_fields = mention_fields.sort(keys=mention_counts, reverse=True).merge()
sorted_fields.chat("How to parameterize a function?")  # (7)!

vbt.settings.set("knowledge.chat.max_tokens", None)  # (8)!

# ______________________________________________________________

chat_history = []
signal_func_nb_code.chat("How to check if we're in a long position?", chat_history)  # (9)!
signal_func_nb_code.chat("How about short one?", chat_history)  # (10)!
chat_history.clear()  # (11)!
signal_func_nb_code.chat("How to access close price?", chat_history)

# ______________________________________________________________

asset.chat(..., completions="openai", model="o1-mini", system_as_user=True)  # (12)!
# (13)!
# vbt.settings.set("knowledge.chat.completions_configs.openai.model", "o1-mini")
# (14)!
# vbt.OpenAICompletions.set_settings({"model": "o1-mini"})

env["OPENAI_API_KEY"] = "<YOUR_OPENROUTER_API_KEY>"
asset.chat(..., completions="openai", base_url="https://openrouter.ai/api/v1", model="openai/gpt-4o") 
# vbt.settings.set("knowledge.chat.completions_configs.openai.base_url", "https://openrouter.ai/api/v1")
# vbt.settings.set("knowledge.chat.completions_configs.openai.model", "openai/gpt-4o")
# vbt.OpenAICompletions.set_settings({
#     "base_url": "https://openrouter.ai/api/v1", 
#     "model": "openai/gpt-4o"
# })

env["DEEPSEEK_API_KEY"] = "<YOUR_DEEPSEEK_API_KEY>"
asset.chat(..., completions="litellm", model="deepseek/deepseek-coder")
# vbt.settings.set("knowledge.chat.completions_configs.litellm.model", "deepseek/deepseek-coder")
# vbt.LiteLLMCompletions.set_settings({"model": "deepseek/deepseek-coder"})

asset.chat(..., completions="llama_index", llm="perplexity", model="claude-3-5-sonnet-20240620")  # (15)!
# vbt.settings.set("knowledge.chat.completions_configs.llama_index.llm", "anthropic")
# anthropic_config = {"model": "claude-3-5-sonnet-20240620"}
# vbt.settings.set("knowledge.chat.completions_configs.llama_index.anthropic", anthropic_config)
# vbt.LlamaIndexCompletions.set_settings({"llm": "anthropic", "anthropic": anthropic_config})

vbt.settings.set("knowledge.chat.completions", "litellm")  # (16)!

# ______________________________________________________________

asset.chat(..., stream=False)  # (17)!

asset.chat(..., formatter="plain")  # (18)!
asset.chat(..., formatter="ipython_markdown")  # (19)!
asset.chat(..., formatter="ipython_html")  # (20)!

file_path = asset.chat(..., formatter="html")  # (21)!
file_path = asset.chat(..., formatter="html", formatter_kwargs=dict(cache_dir="chat"))  # (22)!
file_path = asset.chat(..., formatter="html", formatter_kwargs=dict(clear_cache=True))  # (23)!
file_path = asset.chat(..., formatter="html", formatter_kwargs=dict(cache=False))  # (24)!
file_path = asset.chat(  # (25)!
    ..., 
    formatter="html", 
    formatter_kwargs=dict(
        to_markdown_kwargs=dict(...),
        to_html_kwargs=dict(...),
        format_html_kwargs=dict(...)
    )
)

asset.chat(..., formatter_kwargs=dict(update_interval=1.0))  # (26)!

asset.chat(..., formatter_kwargs=dict(output_to="response.txt"))  # (27)!

asset.chat(  # (28)!
    ..., 
    system_prompt="You are a helpful assistant",
    context_prompt="Here's what you need to know: $context"
)
```

1. Setting the API key as an environment variable makes it available to all packages.
Another option is passing `api_key` directly or saving it in the settings, as shown for `model` below.
2. Paste a link from the website (for example, the patterns tutorial) and use it as context.
If you do not know the private hash, you can paste the suffix. See [querying](#querying).
3. Select and aggregate all documentation pages related to data, then use them as context.
4. Select the API documentation page for the portfolio optimizer and use it as context.
5. Find all mentions of `signal_func_nb` throughout the code of all pages and messages, then use them as context.
6. Filter all messages by @polakowo and keep only relevant fields to fit more data.
By default, the context is trimmed to 100,000 tokens (the exact allowance depends on the model,
e.g., GPT-4o supports 128,000). Content is shuffled to prevent placing more weight on older or
newer content when trimming the context.
7. Get all fields with at least one "parameterize" mention, sort them by the number of mentions
in descending order, and merge them into a single list. When embeddings are unavailable, this is a common
workflow when there is too much data.
8. Allow unlimited context.
9. Append the question and answer to the chat history.
10. Reuse the chat history to ask another question in the current chat.
11. Clear the chat history to start a new chat.
12. Specify the model and other client and chat-related arguments for the OpenAI API.
13. Save the model in the settings to use by default next time.
14. Same as above.
15. You can define configs by LLM when using LLamaIndex.
16. Set the default class for completions.
17. Disable streaming. By default, streaming is enabled.
18. Print the response.
19. Display the response in Markdown format (requires IPython environment).
20. Display the response in HTML format (requires IPython environment).
21. Store the response in a static HTML file and display it.
22. Specify a different cache directory. By default, data is stored under 
__$user_cache_dir/knowledge/vbt/$release_name/chat__.
23. Clear the cache directory before saving.
24. Create a temporary file.
25. When working with HTML, you can provide many arguments accepted by
[VBTAsset.to_html](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.VBTAsset.to_html).
26. When using an update interval, streaming data is buffered and released periodically.
Note that when displaying HTML, the minimum update interval is 1 second.
27. In addition to displaying, the raw response can also be saved to a file.
28. Customize the system and context prompts.

### About objects

You can chat about a VBT object using [chat_about](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.chat_about).
This function calls the method above, but operates only on code examples. When you pass arguments,
they are automatically distributed between [find_assets](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.find_assets)
and [KnowledgeAsset.chat](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/base_assets/#vectorbtpro.utils.knowledge.base_assets.KnowledgeAsset.chat)
(see [chatting](#chatting) for recipes).

```python title="How to chat about an object"
vbt.chat_about(vbt.Portfolio, "How to get trading expectancy?")  # (1)!
vbt.chat_about(  # (2)!
    vbt.Portfolio, 
    "How to get returns accessor with log returns?", 
    asset_names="api",
    api_kwargs=dict(incl_bases=False, incl_ancestors=False)
)
vbt.chat_about(  # (3)!
    vbt.Portfolio, 
    "How to backtest a basic strategy?", 
    model="o1-mini",
    system_as_user=True,
    max_tokens=100_000,
    shuffle=True
)

# ______________________________________________________________

vbt.Portfolio.chat("How to create portfolio from order records?")  # (4)!
vbt.Portfolio.chat("How to get grouped stats?", attr="stats")
```

1. Find knowledge about [Portfolio](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio)
and ask a question using this knowledge as context.
2. Pass knowledge-related arguments. Here, find API knowledge that includes only the
[Portfolio](https://vectorbt.pro/pvt_6d1b3986/api/portfolio/base/#vectorbtpro.portfolio.base.Portfolio) class.
3. Pass chat-related arguments. In this example, use the o1-mini model on a shuffled context with up to
100,000 tokens. Also, set the user role instead of the system role for the initial instruction.
4. Call the chat function directly from the object's interface.

You can also ask questions about objects that do not technically exist in VBT or about general keywords,
such as "quantstats", which will search for mentions of "quantstats" within pages and messages.

```python title="How to chat about keywords"
vbt.chat_about(
    "sql", 
    "How to import data from a SQL database?", 
    resolve=False,  # (1)!
    find_kwargs=dict(
        ignore_case=True,
        allow_prefix=True,  # (2)!
        allow_suffix=True  # (3)!
    )
)
```

1. Use this option to avoid searching for a VBT object with the same name.
2. Allow prefixes for "sql", such as "from_sql".
3. Allow suffixes for "sql", such as "SQLData".

### Globally

Similar to the global [search](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.search)
function, there is a global function for chatting: [chat](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/custom_assets/#vectorbtpro.utils.knowledge.custom_assets.chat).
It processes documents in the same way, but instead of displaying results, it sends them to
an LLM for completion.

!!! info
    The first time you run this command, it may take up to 15 minutes to prepare and embed documents.
    Most preparation steps are cached and stored, so future searches will be much
    faster and do not need to repeat the process.

```python title="How to chat about VBT"
vbt.chat("How to turn df into data?")  # (1)!
file_path = vbt.chat("How to turn df into data?", formatter="html")  # (2)!
vbt.chat("How to fix 'Symbols have mismatching columns'?", asset_names="messages")  # (3)!
vbt.chat(
    "How to use templates in signal_func_nb?", 
    asset_names="examples", 
    top_k=None, 
    cutoff=None, 
    return_chunks=False
)  # (4)!

chat_history = []
vbt.chat("How to turn df into data?", chat_history)  # (5)!
vbt.chat("What if I have symbols as columns?", chat_history)  # (6)!
vbt.chat("How to replace index of data?", chat_history, incl_past_queries=False)  # (7)!

_, chat = vbt.chat("How to turn df into data?", return_chat=True)  # (8)!
chat.complete("What if I have symbols as columns?")
```

1. Search API pages, documentation pages, and Discord messages for a query, and chat about them.
By default, up to 100 document chunks are used.
2. Accepts the same arguments as `asset.chat`.
3. Chat about Discord messages only.
4. Use the entire (ranked) asset as context.
5. Reuse the chat history to ask a question in the current chat.
6. Take the chat history into account. All user messages will be considered when ranking the context.
7. Take the chat history into account. Only the current query will be considered when ranking the context.
8. Same as above, except the context remains fixed for all later queries.

<div class="separator-container">
    <hr class="separator">
        <span class="separator-text">+</span>
    <hr class="separator">
</div>

Building an index of embeddings for chatting is not always required. Instead, you can use BM25,
a quick and reliable algorithm that works entirely offline. Additionally, this function will use
a smaller context and a less expensive model for completions, such as "gpt-4o-mini"
instead of "gpt-4o".

```python title="How to chat about VBT quickly"
vbt.quick_chat("How to fix 'Symbols have mismatching columns'?")
```

!!! hint
    Use this when your query contains distinctive keywords. For vague queries, embeddings are a better option.

## RAG

VBT uses a set of components for standard RAG. Most of these are orchestrated and deployed
automatically whenever you globally [search](#globally) for knowledge on VBT or [chat](#globally_1) about VBT.

### Tokenizer

The [Tokenizer](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/chatting/#vectorbtpro.utils.knowledge.chatting.Tokenizer) class
and its subclasses provide an interface for converting text into tokens.

```python title="How to tokenize text"
tokenizer = vbt.TikTokenizer()  # (1)!
tokenizer = vbt.TikTokenizer(encoding="o200k_base")
tokenizer = vbt.TikTokenizer(model="gpt-4o")

vbt.TikTokenizer.set_settings(encoding="o200k_base")  # (2)!

token_count = tokenizer.count_tokens(text)  # (3)!
tokens = tokenizer.encode(text)
text = tokenizer.decode(tokens)

# ______________________________________________________________

tokens = vbt.tokenize(text)  # (4)!
text = vbt.detokenize(tokens)

tokens = vbt.tokenize(text, tokenizer="tiktoken", model="gpt-4o")  # (5)!
```

1. Use the `tiktoken` package as a tokenizer.
2. Set the default settings.
3. Use the tokenizer to count tokens in a text, encode text into tokens, or decode tokens back into text.
4. There are also shortcut methods that create a tokenizer for you.
5. The tokenizer type and parameters can be passed as keyword arguments to both methods.

### Embeddings

The [Embeddings](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/chatting/#vectorbtpro.utils.knowledge.chatting.Embeddings) class
and its subclasses provide an interface for generating vector representations of text.

```python title="How to embed text"
embeddings = vbt.OpenAIEmbeddings()  # (1)!
embeddings = vbt.OpenAIEmbeddings(batch_size=256)  # (2)!
embeddings = vbt.OpenAIEmbeddings(model="text-embedding-3-large")  # (3)!
embeddings = vbt.LiteLLMEmbeddings(model="openai/text-embedding-3-large")  # (4)!
embeddings = vbt.LlamaIndexEmbeddings(embedding="openai", model="text-embedding-3-large")  # (5)!
embeddings = vbt.LlamaIndexEmbeddings(embedding="huggingface", model_name="BAAI/bge-small-en-v1.5")

vbt.OpenAIEmbeddings.set_settings(model="text-embedding-3-large")  # (6)!

emb = embeddings.get_embedding(text)  # (7)!
embs = embeddings.get_embeddings(texts)

# ______________________________________________________________

emb = vbt.embed(text)  # (8)!
embs = vbt.embed(texts)

emb = vbt.embed(text, embeddings="openai", model="text-embedding-3-large")  # (9)!
```

1. Use the `openai` package as an embeddings provider.
2. Process embeddings in batches of 256.
3. Specify the model.
4. Use the `litellm` package as an embeddings provider.
5. Use the `llamaindex` package as an embeddings provider.
6. Set the default settings.
7. Use the embeddings provider to get embeddings for one or more texts.
8. There is also a shortcut method that creates an embeddings provider for you. It accepts one or more texts.
9. The embeddings provider type and parameters can be passed as keyword arguments to the method.

### Completions

The [Completions](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/chatting/#vectorbtpro.utils.knowledge.chatting.Completions) class
and its subclasses provide an interface for generating text completions based on user queries.
For arguments such as `formatter`, see [chatting](#chatting).

```python title="How to (auto-)complete a query"
completions = vbt.OpenAICompletions()  # (1)!
completions = vbt.OpenAICompletions(stream=False)
completions = vbt.OpenAICompletions(max_tokens=100_000, tokenizer="tiktoken")
completions = vbt.OpenAICompletions(model="o1-mini", system_as_user=True)
completions = vbt.OpenAICompletions(formatter="html", formatter_kwargs=dict(cache=False))
completions = vbt.LiteLLMCompletions(model="openai/o1-mini", system_as_user=True)  # (2)!
completions = vbt.LlamaIndexCompletions(llm="openai", model="o1-mini", system_as_user=True)  # (3)!

vbt.OpenAICompletions.set_settings(model="o1-mini", system_as_user=True)  # (4)!

completions.get_completion(text)  # (5)!
content = completions.get_completion_content(text)  # (6)!

# ______________________________________________________________

vbt.complete(text)  # (7)!

vbt.complete(text, completions="openai", model="o1-mini", system_as_user=True)  # (8)!
```

1. Use the `openai` package as a completions provider.
2. Use the `litellm` package as a completions provider.
3. Use the `llamaindex` package as a completions provider.
4. Set the default settings.
5. Use the completions provider to get a completion for a text.
6. Get the content string of a completion without formatting.
7. There is also a shortcut method that creates a completions provider for you.
8. The completions provider type and parameters can be passed as keyword arguments to the method.

### Text splitter

The [TextSplitter](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/chatting/#vectorbtpro.utils.knowledge.chatting.TextSplitter) class
and its subclasses provide an interface for splitting text.

```python title="How to split text"
text_splitter = vbt.TokenSplitter()  # (1)!
text_splitter = vbt.TokenSplitter(chunk_size=1000, chunk_overlap=200)
text_splitter = vbt.SegmentSplitter()  # (2)!
text_splitter = vbt.SegmentSplitter(separators=r"\s+")  # (3)!
text_splitter = vbt.SegmentSplitter(separators=[r"(?<=[.!?])\s+", r"\s+", None])  # (4)!
text_splitter = vbt.SegmentSplitter(tokenizer="tiktoken", tokenizer_kwargs=dict(model="gpt-4o"))
text_splitter = vbt.LlamaIndexSplitter(node_parser="SentenceSplitter")  # (5)!

vbt.TokenSplitter.set_settings(chunk_size=1000, chunk_overlap=200)  # (6)!

text_chunks = text_splitter.split_text(text)  # (7)!

# ______________________________________________________________

text_chunks = vbt.split_text(text)  # (8)!

text_chunks = vbt.split_text(text, text_splitter="llamaindex", node_parser="SentenceSplitter")  # (9)!
```

1. Create a splitter that splits text into tokens.
2. Create a splitter that splits text into segments. By default, it splits into paragraphs and sentences,
words (if the sentence is too long), and then tokens (if the word is too long).
3. Split text strictly into words.
4. Split text into sentences, words (if the sentence is too long), and then tokens (if the word is too long).
5. Use the `SentenceSplitter` from the `llamaindex` package as a text splitter.
6. Set the default settings.
7. Use the text splitter to split a text, which returns a generator.
8. There is also a shortcut method that creates a text splitter for you.
9. The text splitter type and parameters can be passed as keyword arguments to the method.

### Object store

The [ObjectStore](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/chatting/#vectorbtpro.utils.knowledge.chatting.ObjectStore) class
and its subclasses provide an interface for efficiently storing and retrieving arbitrary Python objects,
such as text documents and embeddings. These objects must subclass
[StoreObject](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/chatting/#vectorbtpro.utils.knowledge.chatting.StoreObject).

```python title="How to store objects"
obj_store = vbt.DictStore()  # (1)!
obj_store = vbt.MemoryStore(store_id="abc")  # (2)!
obj_store = vbt.MemoryStore(purge_on_open=True)  # (3)!
obj_store = vbt.FileStore(dir_path="./file_store")  # (4)!
obj_store = vbt.FileStore(consolidate=True, use_patching=False)  # (5)!
obj_store = vbt.LMDBStore(dir_path="./lmdb_store")  # (6)!
obj_store = vbt.CachedStore(obj_store=vbt.FileStore())  # (7)!
obj_store = vbt.CachedStore(obj_store=vbt.FileStore(), mirror=True)  # (8)!

vbt.FileStore.set_settings(consolidate=True, use_patching=False)  # (9)!

obj = vbt.TextDocument(id_, text)  # (10)!
obj = vbt.TextDocument.from_data(text)  # (11)!
obj = vbt.TextDocument.from_data(  # (12)!
    {"timestamp": timestamp, "content": text}, 
    text_path="content",
    excl_embed_metadata=["timestamp"],
    dump_kwargs=dict(dump_engine="nestedtext")
)
obj1 = vbt.StoreEmbedding(id1, child_ids=[id2, id3])  # (13)!
obj2 = vbt.StoreEmbedding(id2, parent_id=id1, embedding=embedding2)
obj3 = vbt.StoreEmbedding(id3, parent_id=id1, embedding=embedding3)

with obj_store:  # (14)!
    obj = obj_store[obj.id_]
    obj_store[obj.id_] = obj
    del obj_store[obj.id_]
    print(len(obj_store))
    for id_, obj in obj_store.items():
        ...
```

1. Create an object store based on a simple dictionary, where data persists only for the lifetime of the instance.
2. Create an object store based on a global dictionary (`memory_store`), where data persists for the
lifetime of the Python process.
3. Clear the store upon opening, removing any data saved by previous instances.
4. Create an object store based on a file (without patching) or folder (with patching).
Patching means that additional changes are saved as separate files.
5. Consolidate the folder (if any) into a file and disable patching.
6. Create an object store based on LMDB.
7. Create an object store that caches the operations of another object store internally.
8. Same as above, but also mirrors operations in the global dictionary (`memory_store`) to persist the cache
for the lifetime of the Python process.
9. Set default settings.
10. Create a text document object.
11. Generate an id automatically from the text.
12. Create a text document object with metadata.
13. Create three embedding objects with relationships.
14. An object store is very easy to use: it behaves just like a regular dictionary.

### Document ranker

The [DocumentRanker](https://vectorbt.pro/pvt_6d1b3986/api/utils/knowledge/chatting/#vectorbtpro.utils.knowledge.chatting.DocumentRanker) class
provides an interface for embedding, scoring, and ranking documents.

```python title="How to rank documents"
doc_ranker = vbt.DocumentRanker()  # (1)!
doc_ranker = vbt.DocumentRanker(dataset_id="abc")  # (2)!
doc_ranker = vbt.DocumentRanker(  # (3)!
    embeddings="litellm", 
    embeddings_kwargs=dict(model="openai/text-embedding-3-large")
)
doc_ranker = vbt.DocumentRanker(  # (4)!
    doc_store="file",
    doc_store_kwargs=dict(dir_path="./doc_file_store"),
    emb_store="file",
    emb_store_kwargs=dict(dir_path="./emb_file_store"),
)
doc_ranker = vbt.DocumentRanker(score_func="dot", score_agg_func="max")  # (5)!

vbt.DocumentRanker.set_settings(doc_store="memory", emb_store="memory")  # (6)!

documents = [vbt.TextDocument("text1"), vbt.TextDocument("text2")]  # (7)!

doc_ranker.embed_documents(documents)  # (8)!
emb_documents = doc_ranker.embed_documents(documents, return_documents=True)
embs = doc_ranker.embed_documents(documents, return_embeddings=True)
doc_ranker.embed_documents(documents, refresh=True)  # (9)!

doc_scores = doc_ranker.score_documents("How to use VBT?", documents)  # (10)!
chunk_scores = doc_ranker.score_documents("How to use VBT?", documents, return_chunks=True)
scored_documents = doc_ranker.score_documents("How to use VBT?", documents, return_documents=True)

documents = doc_ranker.rank_documents("How to use VBT?", documents)  # (11)!
scored_documents = doc_ranker.rank_documents("How to use VBT?", documents, return_scores=True)
documents = doc_ranker.rank_documents("How to use VBT?", documents, top_k=50)  # (12)!
documents = doc_ranker.rank_documents("How to use VBT?", documents, top_k=0.1)  # (13)!
documents = doc_ranker.rank_documents("How to use VBT?", documents, top_k="elbow")  # (14)!
documents = doc_ranker.rank_documents("How to use VBT?", documents, cutoff=0.5, min_top_k=20)  # (15)!

# ______________________________________________________________

vbt.embed_documents(documents)  # (16)!
vbt.embed_documents(documents, embeddings="openai", model="text-embedding-3-large")
documents = vbt.rank_documents("How to use VBT?", documents)
```

1. Create a document ranker.
2. Set the store id for both the document store and embedding store.
3. Specify the embeddings provider type and parameters.
4. Specify the object store types for documents and embeddings.
5. Specify the score function and score aggregation function. Both can be callables.
6. Set default settings.
7. A document ranker accepts an iterable of store objects, such as text documents.
8. Use the document ranker to embed documents. Embeddings are stored in an embedding store.
You can also choose to return the embedded documents or the embeddings themselves.
9. If a document or embedding already exists in the store, override it.
10. Assign each document a similarity score relative to the query and return the scores.
You can also specify whether to return the scores for the chunks (by default they are aggregated),
or the documents along with their scores.
11. Rank documents based on similarity scores relative to the query. By default,
this reorders the documents, but you can also choose to return the documents with their scores.
12. Select the top 50 documents.
13. Select the top 10 percent of documents.
14. Select top documents based on an algorithm such as the Elbow method.
15. Select at least the top 20 documents with a similarity score above 0.5.
16. There are also shortcut methods for embedding and ranking that create a document ranker for you.

### Pipeline

The components described above can enhance RAG pipelines, extending their utility beyond the VBT scope.

```python title="How to create a basic RAG pipeline"
data = [
    "The Eiffel Tower is not located in London.",
    "The Great Wall of China is not visible from Jupiter.",
    "HTML is not a programming language."
]
query = "Where the Eiffel Tower is not located?"

documents = map(vbt.TextDocument.from_data, data)
retrieved_documents = vbt.rank_documents(query, documents, top_k=1)
context = "\n\n".join(map(str, retrieved_documents))
vbt.complete(query, context=context)
```

## QuantGPT

If you have a basic question, want to save money, or prefer chatting from a mobile device,
check out [QuantGPT](https://www.quantgpt.chat/), a free service generously hosted by our member
@simrell. QuantGPT uses the same knowledge base (website and Discord) as our ChatVBT function,
powered by the OpenAI Assistants API, which we have replicated with our own RAG.

<div class="grid cards width-fifty" markdown>

- :material-robot:{ .lg .middle } __Ask QuantGPT__

    ---

    [![](https://vectorbt.pro/pvt_6d1b3986/assets/quantgpt.light.webp#only-light){: loading=lazy }](https://www.quantgpt.chat/)
    [![](https://vectorbt.pro/pvt_6d1b3986/assets/quantgpt.dark.webp#only-dark){: loading=lazy }](https://www.quantgpt.chat/)

</div>

!!! info
    Both tools should give similar answers, but ChatVBT (that is, `vbt.chat()`) offers clickable references,
    full control over the knowledge base (which may improve completions), and the flexibility to use
    any LLM, not just OpenAI.