STRAT → VectorBT Pro: JSON Contract (LLM-ready)
A) High-level design

You’ll get two objects:

config – static knobs that don’t change per bar (patterns allowed, TFC stack, risk model).

payload – all the indexed arrays VectorBT needs: boolean entries/exits (+ optional short side), plus stop/take-profit expressed either as percentages (native VBT stops) or as price-level exits you generate yourself.

Why two? Because VectorBT Pro cares about shape-aligned arrays (pd.Series/DataFrame) at runtime; while your STRAT logic (patterns/TFC) is configuration used to derive those arrays. 
Vectorbt
+1

B) Compact but VectorBT-Ready JSON Schemas
1) STRATConfig.schema.json (small, stable)

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "STRATConfig",
  "type": "object",
  "additionalProperties": false,
  "required": ["timeframes", "patterns", "risk"],
  "properties": {
    "timeframes": {
      "type": "object",
      "additionalProperties": false,
      "required": ["execution", "stack"],
      "properties": {
        "execution": { "type": "string", "enum": ["15m","30m","60m","D","W"] },
        "stack": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string", "enum": ["15m","30m","60m","D","W","M"] }
        },
        "require_ftfc": { "type": "boolean", "default": true }
      }
    },
    "patterns": {
      "type": "array",
      "items": { "type": "string", "enum": ["212","22U","22D","122","312","322"] }
    },
    "risk": {
      "type": "object",
      "additionalProperties": false,
      "required": ["mode"],
      "properties": {
        "mode": { "type": "string", "enum": ["percent_stops","price_level_exits"] },

        "percent_stops": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "sl_stop": { "type": "number", "exclusiveMinimum": 0 },   // e.g., 0.01 = 1%
            "sl_trail": { "type": "boolean", "default": false },
            "tp_stop": { "type": "number", "exclusiveMinimum": 0 },   // e.g., 0.02 = 2%
            "rr_override": { "type": "number", "exclusiveMinimum": 0 } // optional
          }
        },

        "price_level_exits": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "generate_stop_exits": { "type": "boolean", "default": true },
            "ladder": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["level_ref","scale_out_fraction"],
                "additionalProperties": false,
                "properties": {
                  "level_ref": { "type": "string", "enum": ["prior_pivot","outside_edge","bf_projection","r_multiple"] },
                  "r_multiple": { "type": "number" },
                  "scale_out_fraction": { "type": "number", "minimum": 0, "maximum": 1 }
                }
              }
            }
          }
        }
      }
    }
  }
}


If risk.mode="percent_stops", we’ll pass sl_stop, sl_trail, tp_stop straight into Portfolio.from_signals (native VBT stops). 
Vectorbt

If risk.mode="price_level_exits", we’ll precompute exit arrays (price-level stops/targets) and give those exits to VBT as boolean arrays; this is the route for exact STRAT stops like “other side of the inside bar,” multi-target ladders, etc. (you can also mix with adjust_sl_func_nb later). 
Vectorbt
+2
Vectorbt
+2

2) STRATPayload.schema.json (arrays VBT consumes)

{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "STRATPayload",
  "type": "object",
  "additionalProperties": false,
  "required": ["meta", "index", "price", "signals"],
  "properties": {
    "meta": {
      "type": "object",
      "additionalProperties": false,
      "required": ["symbol","venue","execution_tf"],
      "properties": {
        "symbol": { "type": "string" },
        "venue":  { "type": "string" },
        "execution_tf": { "type": "string", "enum": ["15m","30m","60m","D","W"] }
      }
    },

    "index": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string", "format": "date-time" }
    },

    "price": {
      "type": "object",
      "additionalProperties": false,
      "required": ["open","high","low","close"],
      "properties": {
        "open":  { "type": "array", "items": { "type": "number" } },
        "high":  { "type": "array", "items": { "type": "number" } },
        "low":   { "type": "array", "items": { "type": "number" } },
        "close": { "type": "array", "items": { "type": "number" } }
      }
    },

    "signals": {
      "type": "object",
      "additionalProperties": false,
      "required": ["long_entries","long_exits"],
      "properties": {
        "long_entries": { "type": "array", "items": { "type": "boolean" } },
        "long_exits":   { "type": "array", "items": { "type": "boolean" } },

        "short_entries": { "type": "array", "items": { "type": "boolean" } },
        "short_exits":   { "type": "array", "items": { "type": "boolean" } },

        "stops_native": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "sl_stop": { "type": "number" },          // percent, uniform or per-column
            "sl_trail": { "type": "boolean" },
            "tp_stop": { "type": "number" }
          }
        },

        "stops_price_level": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "sl_price": { "type": "array", "items": [{ "type": "number" },{ "type": "null" }] }, // optional per-bar price
            "tp1_price": { "type": "array", "items": [{ "type": "number" },{ "type": "null" }] },
            "tp2_price": { "type": "array", "items": [{ "type": "number" },{ "type": "null" }] },
            "tp3_price": { "type": "array", "items": [{ "type": "number" },{ "type": "null" }] }
          }
        }
      }
    }
  }
}

index and price let Claude emit everything self-contained and shape-aligned.

Path 1 (native stops): fill signals.stops_native → pass sl_stop, sl_trail, tp_stop directly to VBT. 
Vectorbt

Path 2 (price-level): set stops_price_level and prebuild long_exits (and/or short_exits) where stop/targets hit; then call VBT with those exits (and don’t pass native stops). For advanced logic (move stop to BE after TP1, ladders), this is typically simpler & explicit. 
Vectorbt
+2
GitHub
+2

C) How Claude maps STRAT → VectorBT

Compute bar scenarios and TFC on execution TF, filter to allowed patterns and FTFC/majority direction (from your config).

Emit boolean arrays for long_entries / long_exits (and shorts if you allow).

Stops/targets

If percent_stops: emit sl_stop, sl_trail, tp_stop (e.g., RR=1:2 ⇒ sl_stop=0.01, tp_stop=0.02). VectorBT applies stops around entry using OHLC if provided. 
Vectorbt

If price_level_exits: precompute stop/TP price arrays based on STRAT rules (e.g., inside-bar other side, prior pivot, BF projection) and convert them into exit booleans where high/low crosses those levels. (You can also preserve the price arrays for analysis.) 
Vectorbt

D) Minimal wiring code (VectorBT side)

Path 1 — Native stops (percent):

import vectorbt as vbt
import pandas as pd

idx = pd.to_datetime(payload["index"])
close = pd.Series(payload["price"]["close"], index=idx, name=payload["meta"]["symbol"])

entries = pd.Series(payload["signals"]["long_entries"], index=idx, name="entries")
exits   = pd.Series(payload["signals"]["long_exits"],   index=idx, name="exits")

st = payload["signals"]["stops_native"]
pf = vbt.Portfolio.from_signals(
    close,
    entries=entries,
    exits=exits,
    open=pd.Series(payload["price"]["open"], index=idx),
    high=pd.Series(payload["price"]["high"], index=idx),
    low=pd.Series(payload["price"]["low"], index=idx),
    sl_stop=st.get("sl_stop", None),
    sl_trail=st.get("sl_trail", False),
    tp_stop=st.get("tp_stop", None),
    init_cash=100_000
)

VectorBT will manage stop-loss / take-profit off the acquisition price; providing OHLC improves stop accuracy and avoids look-ahead. 
Vectorbt

Path 2 — Price-level exits (exact STRAT levels):

# Precomputed exits (stop/targets) are already booleans in payload["signals"]["long_exits"]
pf = vbt.Portfolio.from_signals(
    close, entries, exits,
    open=..., high=..., low=...,
    init_cash=100_000
)

This route is ideal for: “stop at inside-bar low,” “T1 prior pivot,” “move stop to BE after T1,” “take-profit ladder,” etc. (See stop/exit helpers and laddering ideas

E) Example (abridged)

{
  "timeframes": { "execution":"60m", "stack":["D","W","M"], "require_ftfc": true },
  "patterns": ["212","22D","122","312"],
  "risk": { "mode":"price_level_exits",
            "price_level_exits": {
              "generate_stop_exits": true,
              "ladder": [
                {"level_ref":"prior_pivot","scale_out_fraction":0.4},
                {"level_ref":"bf_projection","scale_out_fraction":0.3},
                {"level_ref":"r_multiple","r_multiple":3.0,"scale_out_fraction":0.3}
              ]
            }}
}


payload (shape-aligned)

{
  "meta": { "symbol":"AAPL","venue":"NASDAQ","execution_tf":"60m" },
  "index": ["2025-06-02T14:30:00Z","2025-06-02T15:30:00Z", "..."],
  "price": { "open":[...], "high":[...], "low":[...], "close":[...] },
  "signals": {
    "long_entries": [false,true,false,...],
    "long_exits":   [false,false,false, ...],  // will toggle true where stop/targets hit
    "stops_price_level": {
      "sl_price":  [null,229.85,null,...],
      "tp1_price": [null,232.20,null,...],
      "tp2_price": [null,234.00,null,...]
    }
  }
}

Claude’s STRAT logic should:

Generate long_entries only when a whitelisted pattern resolves with TFC.

Turn on long_exits when price crosses sl_price or any TP ladder.

Optionally promote stop to breakeven after tp1_price fills, etc. (classic ladder behavior). 
GitHub

F) Notes & gotchas

Choose the path: If you don’t need exact price-level stops, prefer native percent stops — they’re simpler and integrated (sl_stop, sl_trail, tp_stop). 
Vectorbt

Exact STRAT invalidation (e.g., “other side of the inside bar”): either precompute exits (Path 2) or implement a custom adjust_sl_func_nb to update stop loss each bar. 
Vectorbt
+1

Signal timing: VectorBT evaluates stops within the bar—provide OHLC and build signals at bar close to avoid look-ahead. 
Vectorbt

Multiple orders per bar / complex logic: if you outgrow from_signals, move to from_order_func (Numba callbacks) for full control. 
Vectorbt

Analysis tools: VBT Pro has tutorials on stop signals, edge ratio, and scaling/laddering—useful for tuning STRAT exits. 
VectorBT
+2
VectorBT
+2