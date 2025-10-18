## 1\. **Features**

-   **What it is:** A high-level overview of what the software can do, its core capabilities, and unique selling points.
-   **Use case for LLM:** Useful when you want to understand "What can this tool do?" or compare it to similar tools. _Example question:_ "Is this tool good for portfolio analysis?"

---

## 2\. **Tutorials**

-   **What it is:** Step-by-step guides aimed at teaching users how to accomplish common tasks, often starting from beginner to more advanced workflows.
-   **Use case for LLM:** Best for finding learning materials, example workflows, or hands-on guidance. _Example question:_ "How do I use this tool to backtest a trading strategy?"

---

## 3\. **Documentation**

-   **What it is:** Comprehensive written reference covering how the tool works, detailed explanations of concepts, configuration options, and more.
-   **Use case for LLM:** Ideal when detailed, authoritative explanations are needed, like looking up options, configuration, or understanding internal logic. _Example question:_ "What does the 'window\_length' parameter mean in this context?"

---

## 4\. **Cookbook**

-   **What it is:** A collection of practical, focused "recipes" solving specific problems or demonstrating cool tricks with the tool.
-   **Use case for LLM:** Great for "How do I…?" queries or when searching for ready-to-go example solutions. _Example question:_ "Show me an example of combining two indicators."

---

## 5\. **API**

-   **What it is:** A detailed reference for all functions, classes, and methods provided by the tool—shows inputs, outputs, and usage for developers.
-   **Use case for LLM:** Go here to find technical details for programming and development, or when writing/debugging code. _Example question:_ "What are the arguments for Portfolio.from\_signals()?"

---

## 6\. **LLM Docs** (Special Section)

-   **What it is:** Consolidated documentation specifically organized for LLM consumption - includes complete API documentation (242k+ lines), general documentation, and file location mappings.
-   **Use case for LLM:** PRIORITY section for LLMs. Contains:
    - `1 Documentaiton_FIle_Locations.md` - Maps all VBT Pro documentation locations
    - `2 General Documentation.md` - Comprehensive general documentation
    - `3 API Documentation.md` - Complete API reference (242,458 lines) with all function signatures, parameters, and examples
-   **When to use:** Search here FIRST for any VBT Pro questions. This folder contains the most complete, searchable format of all documentation.

---

## 7\. **Python Introspection**

-   **What it is:** The ability to programmatically explore, search, and extract information about VectorBT PRO’s API, code structure, and integrated documentation (including class functions, code examples, and method signatures) by directly querying Python objects. VectorBT PRO extends Python’s introspection with its own advanced tools.
    
-   **Use case for LLMs:** - **Dynamic Discovery**: When you (or an LLM agent) need to find relevant classes, functions, or code examples in a highly adaptive way (rather than relying on static docs).
    
-   **Automated Doc-Search**: Scripted or conversational queries for “where is this method documented?” or “show code samples using this API,” enabling LLM workflows to answer user questions even if a docs search term isn’t known in advance.
    
-   **Live Source/Example Extraction:** Pull live code, function signatures, docstrings, or example usages from the installed version of VectorBT PRO—ideal for debugging, research, or dynamic workflows.
    

#### _Example questions:_

-   “Show all code examples for PortfolioOptimizer.”
-   “What are the arguments and docstring for vbt.PFO.from\_optimize\_func?”
-   “Find, extract, and print the source code for this specific method.”

---

### **Summary Table**

| Section | Main Purpose | Example LLM Use Case |
|----------------------|-----------------------------------------------|---------------------------------------------------------------|
| Features | Overview & capabilities | Is this the right tool for my problem? |
| Tutorials | Step-by-step learning | How do I start using this tool? |
| Documentation | Detailed reference & explanations | What does this setting do? |
| Cookbook | Practical examples & recipes | How do I implement this pattern/task? |
| API | Technical details for developers | What's the function signature for X? |
| LLM Docs | Complete searchable reference | **PRIORITY: Search here first for any VBT Pro info** |
| Python Introspection | Programmatic/discovery search & live inspection| Script or query the API/object for examples, signatures, docs |


---

### **How to Use Python Introspection in VectorBT PRO (Additional Guide Located At this Location: <"C:\Strat_Trading_Bot\vectorbt-workspace\VectorBT Pro Official Documentation\VectorBT_Pro_Python_Introspection_Guide.md"> **

VectorBT PRO makes advanced introspection easy with several high-level functions, which you can call directly or within LLM agents/prompts. Here’s a concise guide with key examples:

#### 1\. **Find Documentation Mentions (any object or method):**

python

Copy

```
import vectorbtpro as vbt

# Keyword/code-based search for class or method documentation
docs = vbt.find_docs(vbt.PFO) # All references/documentation to Portfolio Optimizer class
docs_func = vbt.find_docs([vbt.PFO.from_optimize_func]) # For a specific method

# Or directly from the class
docs_direct = vbt.PFO.find_docs(attr="from_optimize_func")
```

#### 2\. **Find Example Code:**

python

Copy

```
examples = vbt.find_examples(vbt.PFO) # All examples for PortfolioOptimizer
example_func = vbt.PFO.find_examples(attr="from_optimize_func") # Method-specific
```

#### 3\. **Extract the Actual Source Code (deep inspection):**

python

Copy

```
source_code = vbt.get_source('vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer')
print(source_code)
```

Or, with the MCP discovery server:

python

Copy

```
from vectorbtpro.mcp_server import get_source

code_str = get_source('vbt.PFO.from_optimize_func')
print(code_str)
```

#### 4\. **Explore Available Properties/Methods, Get Signatures and Docstrings:**

python

Copy

```
vbt.pdir(vbt.PFO) # Dir-like view of methods & properties
vbt.phelp(vbt.PFO.from_optimize_func) # Signature and documentation
```

#### 5\. **Programmatic Documentation/Example Search (all assets):**

python

Copy

```
from vectorbtpro.mcp_server import find

context = find('vbt.Portfolio', asset_names='all') # Search raw doc assets
print(context)
```

---

**Key Advantage:**  
This “Python Introspection” mode lets you (or an AI agent) answer deep, specific, or context-driven queries – even where the term, object name, or example isn’t pre-indexed in static documentation. It’s essential for advanced research, debugging, or LLM-driven self-guided code discovery.

---

_Integrate this workflow for any queries where you want:_

-   Most current/installed API info (“what’s in my version?”)
-   Automated/LLM-driven exploration or curation of examples
-   Exhaustive or customized documentation/code lookups

---

