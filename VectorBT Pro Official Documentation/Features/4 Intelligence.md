---
title: Intelligence
description: Intelligence features of VectorBT PRO
icon: material/brain
---

# :material-brain: Intelligence

## Source refactorer

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2025_5_11.svg){ loading=lazy }

- [x] Use the source refactorer to automatically enhance any Python code, whether it is a full package,
Python object, or raw string. If the source is larger than expected, it intelligently splits it
into clean AST-based chunks, refactors each using an LLM, and merges them back into polished code.
You can choose to return the result, update the source in place, or copy it to your clipboard.
For full transparency, you can also preview the diff directly in your browser :pencil:

```pycon title="Complete a signal function"
>>> env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"
>>> env["OPENAI_API_KEY"] = "<YOUR_OPENAI_API_KEY>"

>>> source = """
... @njit
... def signal_func_nb(c, entries, exits):
...     is_entry = vbt.pf_nb.select_nb(c, entries)
...     is_exit = vbt.pf_nb.select_nb(c, exits)
...     
...     # TODO: Enter only if no other asset is active
...
...     return is_entry, is_exit, False, False
... """  # (1)!

>>> new_source = vbt.refactor_source(
...     source, 
...     attach_knowledge=True,  # (2)!
...     model="o3-mini",
...     reasoning_effort="high",
...     system_as_user=True,
...     show_diff=True,  # (3)!
... )
>>> print(new_source)

@njit
def signal_func_nb(c, entries, exits):
    is_entry = vbt.pf_nb.select_nb(c, entries)
    is_exit = vbt.pf_nb.select_nb(c, exits)
    for col in range(c.from_col, c.to_col):
        if col != c.col and c.last_position[col] != 0:
            is_entry = False
            break
    return is_entry, is_exit, False, False
```

1. Use **TODO** or **FIXME** comments to provide custom instructions.
2. Attach relevant knowledge from the website and Discord.
3. Show the produced changes in a browser.

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/source_refiner.light.png#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/source_refiner.dark.png#only-dark){: .iimg loading=lazy }

## Quick search & chat

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2025_5_11.svg){ loading=lazy }

- [x] In addition to embeddings, which require prior generation, VBT now supports
[BM25](https://en.wikipedia.org/wiki/Okapi_BM25) for fast, fully offline lexical search.
This is perfect for quickly finding something specific.

```pycon title="Search VBT knowledge for a warning"
>>> env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"

>>> vbt.quick_search("UserWarning: Symbols have mismatching index")
```

=== "Page 1"

    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/quick_search1.light.png#only-light){: .iimg loading=lazy }
    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/quick_search1.dark.png#only-dark){: .iimg loading=lazy }

=== "Page 2"

    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/quick_search2.light.png#only-light){: .iimg loading=lazy }
    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/quick_search2.dark.png#only-dark){: .iimg loading=lazy }

=== "Page 3"

    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/quick_search3.light.png#only-light){: .iimg loading=lazy }
    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/quick_search3.dark.png#only-dark){: .iimg loading=lazy }

## ChatVBT

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2025_3_1.svg){ loading=lazy }

- [x] Similar to SearchVBT, ChatVBT takes search results and forwards
them to an LLM for completion. This allows you to interact seamlessly with the entire VBT knowledge base,
receiving detailed and context-aware responses.

!!! info
    The first time you run this command, it may take up to 15 minutes to prepare and embed documents.
    However, most of the preparation steps are cached and stored, so future searches will be much
    faster and will not require repeating the process.

=== "ChatGPT"

    ```pycon title="Ask VBT a question using ChatGPT"
    >>> env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"
    >>> env["OPENAI_API_KEY"] = "<YOUR_OPENAI_API_KEY>"
    
    >>> vbt.chat("How to rebalance weekly?", formatter="html")
    ```

=== "High-reasoning ChatGPT"

    ```pycon title="Ask VBT a question using a high-reasoning ChatGPT"
    >>> env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"
    >>> env["OPENAI_API_KEY"] = "<YOUR_OPENAI_API_KEY>"
    
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions_configs.openai.model", 
    ...     "o3-mini"  # (1)!
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions_configs.openai.reasoning_effort", 
    ...     "high"  # (2)!
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions_configs.openai.system_as_user", 
    ...     True  # (3)!
    ... )

    >>> vbt.chat("How to rebalance weekly?", formatter="html")
    ```

    1. Discover [more models](https://platform.openai.com/docs/models). Note that the availability of
    this model depends on your tier. If your tier does not support o3-mini, try another model, such as o1-mini.
    2. Do not forget to update `openai` to the latest version.
    3. Some models do not support system prompts.

=== "DeepSeek R1 (OpenRouter)"

    ```pycon title="Ask VBT a question using DeepSeek R1"
    >>> env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"
    >>> env["OPENAI_API_KEY"] = "<YOUR_OPENAI_API_KEY>"  # (1)!
    >>> env["OPENROUTER_API_KEY"] = "<YOUR_OPENROUTER_API_KEY>"

    >>> vbt.settings.set(
    ...     "knowledge.chat.completions_configs.openai.base_url", 
    ...     "https://openrouter.ai/api/v1"
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions_configs.openai.api_key", 
    ...     env["OPENROUTER_API_KEY"]
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions_configs.openai.model", 
    ...     "deepseek/deepseek-r1"  # (2)!
    ... )

    >>> vbt.chat("How to rebalance weekly?", formatter="html")
    ```

    1. Required for embeddings.
    2. Discover [more models](https://openrouter.ai/models).

=== "Claude 3.5 Sonnet (LiteLLM)"

    ```pycon title="Ask VBT a question using Claude 3.5 Sonnet"
    >>> env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"
    >>> env["OPENAI_API_KEY"] = "<YOUR_OPENAI_API_KEY>"  # (1)!
    >>> env["ANTHROPIC_API_KEY"] = "<YOUR_ANTHROPIC_API_KEY>"
    
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions", 
    ...     "litellm"
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions_configs.litellm.model", 
    ...     "anthropic/claude-3-5-sonnet-20241022"  # (2)!
    ... )

    >>> vbt.chat("How to rebalance weekly?", formatter="html")
    ```
    
    1. Required for embeddings.
    2. Discover [more models](https://docs.litellm.ai/docs/providers).

=== "DeepSeek R1 (LlamaIndex, locally)"

    !!! note
        Make sure you have the required hardware :material-integrated-circuit-chip:

        The Hugging Face extension for LlamaIndex is required for [embeddings](https://docs.llamaindex.ai/en/stable/examples/embeddings/huggingface/)
        and [LLMs](https://docs.llamaindex.ai/en/stable/examples/llm/huggingface/). Please ensure it is installed.

    ```pycon title="Ask VBT a question using DeepSeek R1 (locally)"
    >>> env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"

    >>> vbt.settings.set(
    ...     "knowledge.chat.embeddings", 
    ...     "llama_index"
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.embeddings_configs.llama_index.embedding", 
    ...     "huggingface"
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.embeddings_configs.llama_index.model_name", 
    ...     "BAAI/bge-small-en-v1.5"  # (1)!
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions", 
    ...     "llama_index"
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions_configs.llama_index.llm", 
    ...     "huggingface"
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions_configs.llama_index.model_name", 
    ...     "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"  # (2)!
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.completions_configs.llama_index.tokenizer_name", 
    ...     "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"
    ... )
    >>> vbt.settings.set(
    ...     "knowledge.chat.rank_kwargs.dataset_id", 
    ...     "local"
    ... )

    >>> vbt.chat("How to rebalance weekly?", formatter="html")
    ```

    1. Discover [more embedding models](https://huggingface.co/spaces/mteb/leaderboard).
    2. Discover [more DeepSeek models](https://huggingface.co/deepseek-ai).

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/chatvbt.light.gif#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/chatvbt.dark.gif#only-dark){: .iimg loading=lazy }

## SearchVBT

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2025_3_1.svg){ loading=lazy }

- [x] Want to find specific information using natural language on the website or Discord?
VBT provides a powerful smart search feature called SearchVBT. Enter your query and it will
generate an HTML page with well-structured search results. Behind the scenes, SearchVBT uses a
[RAG](https://en.wikipedia.org/wiki/Retrieval-augmented_generation) pipeline to embed, rank, and
retrieve only the most relevant documents from VBT, ensuring precise and efficient search results.

!!! info
    The first time you run this command, it may take up to 15 minutes to prepare and embed documents.
    However, most preparation steps are cached and stored, so future searches will be significantly
    faster without needing to repeat the process.

```pycon title="Search VBT knowledge for a warning"
>>> env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"
>>> env["OPENAI_API_KEY"] = "<YOUR_API_KEY>"

>>> vbt.search("How to run indicator expressions?")
```

=== "Page 1"

    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/searchvbt1.light.png#only-light){: .iimg loading=lazy }
    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/searchvbt1.dark.png#only-dark){: .iimg loading=lazy }

=== "Page 2"

    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/searchvbt2.light.png#only-light){: .iimg loading=lazy }
    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/searchvbt2.dark.png#only-dark){: .iimg loading=lazy }

=== "Page 3"

    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/searchvbt3.light.png#only-light){: .iimg loading=lazy }
    ![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/searchvbt3.dark.png#only-dark){: .iimg loading=lazy }

## Self-aware classes

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_12_15.svg){ loading=lazy }

- [x] Each VBT class offers methods to explore its features, including its API, associated
documentation, Discord messages, and code examples. You can even interact with it directly via an LLM!

```pycon title="Ask portfolio optimizer a question"
>>> env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"
>>> env["OPENAI_API_KEY"] = "<YOUR_API_KEY>"

>>> vbt.PortfolioOptimizer.find_assets().get("link")
['https://vectorbt.pro/pvt_xxxxxxxx/api/portfolio/pfopt/base/#vectorbtpro.portfolio.pfopt.base',
 'https://vectorbt.pro/pvt_xxxxxxxx/api/generic/analyzable/#vectorbtpro.generic.analyzable.Analyzable',
 'https://vectorbt.pro/pvt_xxxxxxxx/api/base/wrapping/#vectorbtpro.base.wrapping.Wrapping',
 ...
 'https://vectorbt.pro/pvt_xxxxxxxx/features/optimization/#riskfolio-lib',
 'https://vectorbt.pro/pvt_xxxxxxxx/features/optimization/#portfolio-optimization',
 'https://vectorbt.pro/pvt_xxxxxxxx/features/optimization/#pyportfolioopt',
 ...
 'https://discord.com/channels/x/918629995415502888/1064943203071045753',
 'https://discord.com/channels/x/918629995415502888/1067718833646874634',
 'https://discord.com/channels/x/918629995415502888/1067718855734075403',
 ...]

>>> vbt.PortfolioOptimizer.chat("How to rebalance weekly?", formatter="html")
```

![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/knowledge_assets.light.gif#only-light){: .iimg loading=lazy }
![](https://vectorbt.pro/pvt_6d1b3986/assets/images/features/knowledge_assets.dark.gif#only-dark){: .iimg loading=lazy }

## Knowledge assets

![](https://vectorbt.pro/pvt_6d1b3986/assets/badges/new-in/v2024_11_12.svg){ loading=lazy }

- [x] Each [release](https://github.com/polakowo/vectorbt.pro/releases) now includes valuable
knowledge assets—JSON files containing private website content and the complete "vectorbt.pro" Discord
history. These assets can be used with LLMs and services like Cursor. In addition, VBT offers
a palette of classes for working with these assets, providing functions such as
converting to Markdown and HTML files, browsing the website offline, performing targeted searches,
interacting with LLMs, and much more!

```pycon title="Gather all pages and messages that define signal_func_nb"
>>> env["GITHUB_TOKEN"] = "<YOUR_GITHUB_TOKEN>"

>>> pages_asset = vbt.PagesAsset.pull()  # (1)!
>>> messages_asset = vbt.MessagesAsset.pull()
>>> vbt_asset = pages_asset + messages_asset
>>> code = vbt_asset.find_code("def signal_func_nb", return_type="item")
>>> code.print_sample()  # (2)!
```

1. The first pull will download the assets, while subsequent pulls will use the cached versions.
2. Print a random code snippet.

```yaml
link: https://discord.com/channels/x/918630948248125512/1251081573147742298
block: https://discord.com/channels/x/918630948248125512/1251081573147742298
thread: https://discord.com/channels/x/918630948248125512/1250844139952541837
reference: https://discord.com/channels/x/918630948248125512/1250844139952541837
replies:
- https://discord.com/channels/x/918630948248125512/1251083513336299610
channel: support
timestamp: '2024-06-14 07:51:31'
author: '@polakowo'
content: Something like this
mentions:
- '@fei'
attachments:
- file_name: Screenshot_2024-06-13_at_20.29.45-B4517.png
  content: |-
    Here's the text extracted from the image:

    ```python
    @njit
    def signal_func_nb(c, entries, exits, wait):
        is_entry = vbt.pf_nb.select_nb(c, entries)
        if is_entry:
            return True, False, False, False
        is_exit = vbt.pf_nb.select_nb(c, exits)
        if is_exit:
            if vbt.pf_nb.in_position_nb(c):
                last_order = vbt.pf_nb.get_last_order_nb(c)
                if c.index[c.i] - c.index[last_order["idx"]] >= wait:
                    return False, True, False, False
        return False, False, False, False

    pf = vbt.PF.from_random_signals(
        "BTC-USD",
        n=100,
        signal_func_nb=signal_func_nb,
        signal_args=(
            vbt.Rep("entries"),
            vbt.Rep("exits"),
            vbt.dt.to_ns(vbt.timedelta("1000 days"))
        )
    )
    ```
reactions: 0
```

## And many more...

- [ ] Look forward to more killer features being added every week!

[:material-language-python: Python code](https://vectorbt.pro/pvt_6d1b3986/assets/jupytext/features/intelligence.py.txt){ .md-button target="blank_" }