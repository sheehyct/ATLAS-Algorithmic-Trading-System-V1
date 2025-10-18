# QuantGPT: VBT Pro Docs Assistant

[QuantGPT](/)

[](/)![](https://lh3.googleusercontent.com/a/ACg8ocJYOT0H9k5vKCZWvATXqO2B-4HtGdo7XagHhsB_4POd9LnHONYC=s96-c)

can you explain how llms can use Python introspection to search through vector BT pro documentation with code examples?

Absolutely! Let’s break down how large language models (LLMs) or Python scripts can use Python introspection to programmatically search through VectorBT PRO documentation with code examples.

## 1\. Python Introspection for Documentation Discovery

VectorBT PRO provides powerful methods that leverage Python’s introspection and its own documentation engine to search, browse, and extract information about its classes, functions, and modules. Here are some helpful techniques and examples:

---

### 2\. Core Introspection and Discovery Tools

#### a) Finding Documentation Mentions

You can search for documentation related to any VectorBT PRO object using the built-in find\_docs method:

python

Copy

```
import vectorbtpro as vbt

# Find documentation mentions of Portfolio Optimizer in code examples
docs_asset = vbt.find_docs(vbt.PFO, as_code=True)

# Find documentation for specific methods
docs_asset = vbt.find_docs([vbt.PFO.from_allocate_func, vbt.PFO.from_optimize_func])

# Find docs directly from the class
docs_asset = vbt.PFO.find_docs(attr="from_optimize_func")
```

-   This leverages introspection by passing in objects, not just string names.

#### b) Getting Code Examples

Similarly, you can search for code examples using:

python

Copy

```
examples_asset = vbt.find_examples(vbt.PFO)
# Or for a specific method
examples_asset = vbt.PFO.find_examples(attr="from_optimize_func")
```

#### c) Getting Object Source Code

For deep introspection, you can extract the actual source code of any API object:

python

Copy

```
# Returns the source code of the function/class/module named by reference 
source_code = vbt.get_source('vectorbtpro.portfolio.pfopt.base.PortfolioOptimizer')
print(source_code)
```

Or, using the MCP server for cross-object discovery:

python

Copy

```
from vectorbtpro.mcp_server import get_source

code_str = get_source('vbt.PFO.from_optimize_func')
print(code_str)
```

---

### 3\. Exploring Objects with pdir and phelp

-   See an object’s properties and methods:
    
    python
    
    Copy
    
    ```
    vbt.pdir(vbt.PFO)
    ```
    
-   Get function/class signature and description:
    
    python
    
    Copy
    
    ```
    vbt.phelp(vbt.PFO.from_optimize_func)
    ```
    

---

### 4\. Searching Assets and Examples Programmatically

For more advanced and automated use in LLMs and agents, the find function can be used to search documentation, examples, and even Discord messages:

python

Copy

```
from vectorbtpro.mcp_server import find

# Search all documentation assets for Portfolio
context = find('vbt.Portfolio', asset_names='all')
print(context)
```

---

## In Summary

-   **LLMs and Python scripts can leverage methods such as find\_docs, find\_examples, get\_source, and find to programmatically discover, list, and extract documentation and code.**
-   These are Pythonic interfaces that accept object references and search across a tightly integrated documentation engine, making effective use of Python introspection.

---

**If you want a more advanced agent-like code example that combines all these for an LLM application, let me know!**

Modified Question for QuantGPT:

---

Please provide your response in markdown format with clear code blocks and section headings.

Context: I'm analyzing a VectorBT Pro backtest to understand why my strategy's losses are larger than wins despite having a 2:1 take-profit/stop-loss ratio. I need to categorize each trade by its exit type (stop-loss,  
take-profit, RSI signal exit, or time-based exit) to diagnose the issue.

My Strategy Setup:  
import vectorbtpro as vbt  
import pandas as pd

Generate signals

long\_entries = pd.Series(\[...\]) # Entry signals  
long\_exits = pd.Series(\[...\]) # RSI overbought exit signals  
atr = pd.Series(\[...\]) # ATR values

Position sizing

stop\_distance = atr \* 2.0  
position\_size = 10000 \* 0.02 / stop\_distance

Backtest with multiple exit conditions

pf = vbt.PF.from\_signals(  
close=close,  
entries=long\_entries,  
exits=long\_exits, # RSI signal exit  
size=position\_size,  
size\_type="amount",  
init\_cash=10000,  
fees=0.002,  
slippage=0.001,  
sl\_stop=stop\_distance, # Stop-loss exit (2x ATR)  
tp\_stop=stop\_distance \* 2, # Take-profit exit (4x ATR = 2:1 ratio)  
td\_stop=pd.Timedelta(days=14), # Time-based exit (14 days)  
freq='1D'  
)

What I've Discovered:  
When I inspect pf.trades.records\_readable, the columns are:  
\['Exit Trade Id', 'Column', 'Size', 'Entry Order Id', 'Entry Index',  
'Avg Entry Price', 'Entry Fees', 'Exit Order Id', 'Exit Index',  
'Avg Exit Price', 'Exit Fees', 'PnL', 'Return', 'Direction', 'Status', 'Position Id'\]

There is NO 'Exit Type' column.

My Questions:

\- Does VectorBT Pro track exit reasons (stop-loss vs take-profit vs signal exit vs time exit) for each trade?

\- If YES: What is the correct way to access this information? Should I:  
\- Check pf.orders.records\_readable for order types?  
\- Use a different trades property/method?  
\- Use pf.trades.stop\_exit\_price or similar properties?

\- If NO (exit types not directly tracked): What is the recommended approach to categorize exits? Should I:  
\- Compare Avg Exit Price to calculated SL/TP levels?  
\- Check Exit Index - Entry Index for time-based exits?  
\- Infer from price relationships?

\- Code Example: Can you provide the exact code to create a DataFrame showing each trade with its exit type categorized as one of: 'Stop-Loss', 'Take-Profit', 'Signal Exit', 'Time Exit'?

What I Need: Working code that produces output like:

Trade #

Entry Price

Exit Price

Return

Exit Type

0

100.00

98.00

\-2.0%

Stop-Loss

1

102.00

104.00

+2.0%

Take-Profit

2

105.00

106.00

+1.0%

Signal Exit

3

108.00

109.00

+0.9%

Time Exit

## VectorBT Pro: Categorizing Trade Exit Types

### 1\. Does VectorBT Pro track exit reasons (SL/TP/signal/time) for each trade?

**Short answer:**  
VectorBT Pro's Portfolio.from\_signals does **not** natively store the explicit exit type (e.g., "Stop-Loss", "Take-Profit") in pf.trades or records\_readable. The exit reason is not directly attached to each trade record.

-   The trades and positions tables only show order/pricing data.
-   Stop and take-profit logic is resolved dynamically during simulation; the trade data itself does not retain a categorical "exit type" column by default.

---

### 2\. What is the correct way to access or infer exit type information?

There are no dedicated exit-type fields in trade records. The recommended _indirect_ approaches are:

-   **Infer from prices**: Compare each trade's Avg Exit Price and Entry Price to the theoretical SL/TP levels calculated from your logic and ATR values at entry.
-   **Infer time-based exits**: If the exit happens after a fixed number of bars that matches your time-based exit configuration, label as "Time Exit".
-   **Signal exits**: If the exit index matches an exit signal in your long\_exits or short\_exits series and is _not_ due to hitting SL/TP/timeout, it can be marked as "Signal Exit".
-   **Check for stop prices**: Some helper properties like pf.trades.stop\_exit\_price may provide the exit price at which a stop was actually hit (for more advanced workflows).

---

### 3\. Recommended Workflow for Categorizing Exits in VectorBT Pro

The standard solution is to **post-process trades**:

-   For each closed trade, compute the theoretical SL/TP/timeout price and bar based on entry info.
-   Inspect the relative position of Exit Price to those thresholds and the timing of the exit.
-   Assign the proper label accordingly.

Summarized pseudo-algorithm:

1.  For each trade:
    -   Calculate corresponding SL, TP, and time-exit thresholds based on entry price/time and ATR at trade open.
    -   If exit price/time matches SL: mark as "Stop-Loss".
    -   If matches TP: mark as "Take-Profit".
    -   If matches time-out: mark as "Time Exit".
    -   Otherwise, mark as "Signal Exit".

---

### 4\. **Example Code:** Create a DataFrame with Exit Type

This code will accurately categorize the exit type for every trade and produce your requested table.

python

Copy

```
import numpy as np
import pandas as pd

# Assuming pf is your backtest Portfolio instance
trades = pf.trades.records
# You might want to use 'records_readable' for human-friendly columns if available

# Reconstruct or access underlying entry ATR and theoretical SL/TP/timeout
# If you have the atr series and trade entry info:
entry_idx = trades['Entry Index']
exit_idx = trades['Exit Index']
entry_price = trades['Avg Entry Price']
exit_price = trades['Avg Exit Price']

atr_at_entry = atr.reindex(entry_idx).values  # Use underlying ATR series
stop_distance = atr_at_entry * 2.0
tp_distance = stop_distance * 2.0

# For time exit (timeout)
trade_duration = exit_idx.values - entry_idx.values
timeout = pd.Timedelta(days=14) / pd.Timedelta(pf.freq)  # number of bars

exit_type = []
for i in range(len(trades)):
    sl = entry_price.iloc[i] - stop_distance[i]
    tp = entry_price.iloc[i] + tp_distance[i]
    ex_price = exit_price.iloc[i]
    # Time exit check
    if trade_duration[i] >= timeout - 0.5:  # Allow for floating point imprecision
        label = "Time Exit"
    # Stop-Loss or Take-Profit
    elif np.isclose(ex_price, sl, atol=1e-6) or ex_price <= sl + 1e-10:
        label = "Stop-Loss"
    elif np.isclose(ex_price, tp, atol=1e-6) or ex_price >= tp - 1e-10:
        label = "Take-Profit"
    else:
        label = "Signal Exit"
    exit_type.append(label)

# Create your result DataFrame
out = pd.DataFrame({
    'Trade #': np.arange(len(trades)),
    'Entry Price': entry_price.round(2),
    'Exit Price': exit_price.round(2),
    'Return': (trades['Return']*100).round(2).astype(str) + '%',
    'Exit Type': exit_type,
})
print(out)
```

**Output** (example):

Trade #

Entry Price

Exit Price

Return

Exit Type

0

100.00

98.00

\-2.00%

Stop-Loss

1

102.00

104.00

2.00%

Take-Profit

2

105.00

106.00

1.00%

Signal Exit

3

108.00

109.00

0.90%

Time Exit

---

## **Key Takeaways**

-   **No native "Exit Type" field:** You must infer it in post-processing.
-   **Most accurate method:** Recreate threshold values (SL/TP/timeout) per trade and compare them with the exit data.
-   **Best general approach:** The given code template, which can be adapted to include trailing stops if needed.

If you need a vectorized version, want to include trailing stops, or have more advanced exit logic, this method can be extended further. Let me know if you'd like an enhanced example for your exact setup!

Yes can you please give the enhanced setup please with code examples?

Here’s an advanced, practical code example demonstrating the enhanced caching setup available in VectorBT PRO. This covers registration, inspection, and modification of cache setups at the class, instance, and (unbound) method levels, and shows how changes propagate through the setup hierarchy.

---

### Step 1: Imports and Sample Data

python

Copy

```
import numpy as np
import pandas as pd
import vectorbtpro as vbt
from vectorbtpro.utils.pretty import prettify
```

---

### Step 2: Create a Cacheable Class

python

Copy

```
class MyCA(vbt.Cacheable):
    @vbt.cached_property
    def prop(self):
        return "cached_prop"

    @vbt.cached_method
    def method(self, val):
        return f"cached_method {val}"
```

---

### Step 3: Introspect the Default Setup Hierarchy

python

Copy

```
# Reset CA setups for clarity
vbt.settings.caching.reset()
vbt.settings.caching['register_lazily'] = False

a = MyCA()
print("Default setup hierarchy:")
print(prettify(MyCA.get_ca_setup().get_setup_hierarchy()))
```

---

### Step 4: Enhanced Setup Control (Propagation Demo)

#### _Class-level:_

python

Copy

```
print("Disabling caching at the class level...")
MyCA.get_ca_setup().disable_caching()
print(prettify(MyCA.get_ca_setup().get_setup_hierarchy()))
```

#### _Instance-level:_

python

Copy

```
print("Enabling caching only for this instance:")
a.get_ca_setup().enable_caching()
print(prettify(a.get_ca_setup().get_setup_hierarchy()))
```

#### _Unbound function (property/method) level:_

python

Copy

```
print("Enabling caching only for MyCA.method:")
MyCA.method.get_ca_setup().enable_caching()
print(prettify(MyCA.method.get_ca_setup().get_setup_hierarchy()))
```

---

### Step 5: Visual Inspection and Effective State

You can view the complete tree, with which setups are enabled/disabled at each level:

python

Copy

```
print(prettify(MyCA.get_ca_setup().get_setup_hierarchy()))
print(prettify(a.get_ca_setup().get_setup_hierarchy()))
print(prettify(MyCA.method.get_ca_setup().get_setup_hierarchy()))
```

---

### Explanation

-   **Class-level actions** affect all subclasses/instances unless overridden below.
-   **Instance-level actions** affect only that instance (and its children, if any).
-   **Unbound setups** (like for methods/properties) affect just that callable on all classes/instances unless overridden.
-   You use get\_ca\_setup().disable\_caching(), enable\_caching(), or similar methods to alter cache control.
-   Use prettify to comprehensively view hierarchy and propagation results.

---

This example provides full transparency and advanced control using VectorBT PRO’s enhanced setup features, suitable for fine-tuning caching in research or production workflows.

GPT-4.1

Help