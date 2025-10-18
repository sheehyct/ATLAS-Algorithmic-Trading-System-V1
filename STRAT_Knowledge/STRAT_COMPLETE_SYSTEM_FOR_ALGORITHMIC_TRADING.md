# The STRAT Trading System: Complete Algorithmic Implementation Guide

Rob Smith's STRAT methodology represents one of the most mechanically precise price action systems ever developed for financial markets. Created by a 30-year CBOE floor trader and refined through decades of real-world application, the system eliminates discretionary interpretation in favor of exact, programmable rules. **Smith passed away in July 2023**, but his legacy lives on through a vibrant community led primarily by Alex (@AlexsOptions) and Sara "Strat Sniper," who continue developing tools and education around his original framework. The methodology works across all asset classes and timeframes, providing algorithmic traders with clear entry/exit signals, risk management protocols, and probability assessment frameworks based on multi-timeframe analysis.

## Rob Smith's original STRAT framework: Three scenarios describe all possible price action

The STRAT system begins with a deceptively simple premise articulated in Smith's first Universal Truth: "From one bar to the next, there are only three scenarios that can possibly occur. It is impossible for price to do anything else." This foundational insight eliminates ambiguity in market analysis by classifying every candlestick into one of three mutually exclusive categories based purely on mathematical relationships between consecutive bars' highs and lows.

**Scenario 1 (Inside Bar)** occurs when the current bar's range is completely contained within the previous bar's range. Algorithmically: `IF (current_high < previous_high) AND (current_low > previous_low) THEN scenario = 1`. This represents market consolidation where buyers and sellers agree on current prices, creating an equilibrium state. Inside bars signal indecision and compression, often preceding explosive directional moves. Critically, inside bars use strict inequality operators—equal highs or lows do not qualify as inside bars.

**Scenario 2 (Directional Bar)** takes out ONE side of the previous bar's range but not both. This breaks into two subtypes: **2U (2-Up)** when `(current_high > previous_high) AND (current_low >= previous_low)`, and **2D (2-Down)** when `(current_low < previous_low) AND (current_high <= previous_high)`. Directional bars represent momentum and trending behavior, showing one side (buyers or sellers) gaining control. These bars form the backbone of continuation and reversal patterns throughout the system.

**Scenario 3 (Outside Bar)** breaks BOTH the high and low of the previous bar, creating a broadening formation. The algorithm: `IF (current_high > previous_high) AND (current_low < previous_low) THEN scenario = 3`. Smith emphasized that "you cannot have a Scenario 3 without going Scenario 2 first"—the bar must break one direction before reversing to create the outside bar. These bars represent increased volatility and range expansion, often signaling major market decisions or reversals. Scenario 3 bars further subdivide into 3U (closes bullish) and 3D (closes bearish).

This numbering system (1-2-3) provides the language for describing multi-bar patterns. A **2-1-2 pattern** means directional bar, inside bar, then directional bar in the opposite direction—one of the system's primary reversal formations. Every pattern name in STRAT derives from this sequential numbering convention, enabling precise pattern recognition algorithms without subjective interpretation.

## Timeframe continuity: The probability multiplier that determines trade quality

Smith's second Universal Truth states: "Price must trade in the direction of timeframe continuity." This principle transforms STRAT from a single-timeframe pattern system into a multi-dimensional probability framework. Timeframe continuity exists when 2+ higher timeframes show the same directional pattern, typically identified through 2-2 continuation patterns (consecutive directional bars breaking the same direction) or 1-3 patterns (inside bar followed by outside bar).

The standard timeframe hierarchy for most traders uses **five major timeframes**: Quarterly, Monthly, Weekly, Daily, and 60-minute (hourly). Rob Smith emphasized you are "a prisoner of how software wished to present the data to you" when viewing only one timeframe. Charts represent "visualizations of statistical data"—different time aggregations reveal different market realities. Position traders might substitute Yearly for the 60-minute, while day traders add 30-minute, 15-minute, 5-minute, and even 1-minute timeframes below the 60-minute control timeframe.

**Full Time Frame Continuity (FTFC)** represents the optimal trading condition—when ALL analyzed timeframes align in the same direction. The mathematical definition: `FTFC_UP = (Current_Price > Quarterly_Open) AND (Current_Price > Monthly_Open) AND (Current_Price > Weekly_Open) AND (Current_Price > Daily_Open) AND (Current_Price > Hourly_Open)`. The bearish version inverts all operators to less-than comparisons. An alternative method checks candle colors: `FTFC_UP = (Quarterly_Candle == GREEN) AND (Monthly == GREEN) AND (Weekly == GREEN) AND (Daily == GREEN) AND (Hourly == GREEN)`, where GREEN means the current price trades above the timeframe's open.

Timeframe alignment dramatically affects probability. With only 2 timeframes aligned, pattern success rates hover around 60-65%. With 3 timeframes, probability increases to 70-75%. **FTFC (4-5 aligned timeframes) pushes success rates to 80-85%**. The algorithmic formula: `aligned_probability = base_probability × (1.0 + 0.15 × num_aligned_timeframes)`. This creates a quantifiable probability multiplier based on timeframe consensus.

### Control versus conflict: The current moment versus historical alignment

The **"control" timeframe** concept addresses which timeframe has decisive weight in immediate trading decisions. Rob Smith declared: "Whatever is happening NOW, through the current 60-minute candlestick, has more weight as evidence than all higher timeframes." The 60-minute serves as the standard "in control" timeframe because it balances showing intraday momentum while filtering noise—short enough to capture current action, long enough to avoid false signals.

Control manifests in two forms: **Buyers in control** when price trades above ALL timeframe opens (FTFC Up), and **Sellers in control** when price trades below ALL timeframe opens (FTFC Down). The critical algorithmic principle: `IF current_60min_candle.color == GREEN THEN immediate_bias = BULLISH` regardless of higher timeframe colors. This creates tension between respecting the current moment versus following higher timeframe alignment.

**Conflict** exists when timeframes show opposing directional signals or any Scenario 1 (inside bar) appears on higher timeframes. Detection algorithm: `FOR each timeframe: IF timeframe.has_scenario_1() THEN return "CONFLICT"`. Alternatively, if timeframe opens are NOT all aligned (some above price, some below), conflict exists. The trading rule remains absolute: `IF Conflict = TRUE THEN DO NOT TRADE`. Visual indicators typically show gray or yellow coloring during conflict states, warning traders to wait for resolution.

FTFC can be visualized as bands: Upper Band = MAX(all timeframe opens), Lower Band = MIN(all timeframe opens). When price exceeds the upper band, FTFC Up exists. When price falls below the lower band, FTFC Down exists. Between the bands represents conflict where no full continuity exists.

### The multi-timeframe decision tree for algorithmic selection

Determining which timeframe to base trades on requires a systematic decision process. The algorithm starts by identifying trading style: day traders use 5M/15M triggers with 60M/Daily/Weekly confirmation; swing traders use 1H/4H triggers with Daily/Weekly/Monthly confirmation; position traders use Daily triggers with Weekly/Monthly/Quarterly confirmation.

```
FUNCTION select_trading_timeframe(trade_style):
    // STEP 1: Set timeframes based on style
    IF trade_style == "day_trading":
        trigger_TF = [5M, 15M]
        confirmation_TFs = [60M, Daily, Weekly]
    
    // STEP 2: Check higher timeframe alignment
    FOR each TF in confirmation_TFs:
        IF TF shows 2-2 pattern:
            record_direction(TF)
    
    // STEP 3: Verify no Scenario 1 on higher TFs
    IF any_scenario_1_present(confirmation_TFs):
        RETURN "WAIT - Inside bar on higher TF"
    
    // STEP 4: Check for alignment
    IF all_directions_aligned(confirmation_TFs):
        alignment_direction = get_common_direction()
    ELSE:
        RETURN "NO TRADE - Conflict present"
    
    // STEP 5: Find actionable signal on trigger TF
    FOR candle in trigger_TF:
        IF pattern_matches_actionable_signal(candle):
            IF pattern_direction == alignment_direction:
                RETURN {
                    "entry_TF": trigger_TF,
                    "stop_TF": one_level_below(trigger_TF),
                    "target_TF": highest(confirmation_TFs),
                    "direction": alignment_direction
                }
```

This creates a multi-timeframe precision approach: **Analysis TF** (higher timeframe for direction), **Entry TF** (medium timeframe for pattern), **Trigger TF** (lower timeframe for exact entry), **Stop TF** (lowest timeframe for tight stop), and **Target TF** (highest timeframe for maximum target). For example, a day trader checks Daily/Weekly for 2-2 alignment, identifies a 2-1-2 pattern on 60-minute, enters when the 15-minute goes "in force," places stops using 5-minute structure, and targets using Daily chart measured moves.

### Decoupling: Timeframe opens achieving independence

**Decoupling** is a community term popularized by Alex (@AlexsOptions) that describes the phenomenon where different timeframe opens become independent from each other, allowing each timeframe's participants to make separate directional decisions. This concept provides critical insights into market timing and risk management, particularly in the early phases of new timeframe periods.

The core mechanism: when a higher timeframe period begins (new month, new week, new day), its open price initially **couples** with all lower timeframes that start simultaneously. For example, on the first trading day of a new month, the Monthly open, Weekly open, and Daily open all occur at the same price level. At this moment, all three timeframes are "coupled"—they share an identical starting reference point.

**Decoupling occurs as time progresses and lower timeframes complete their cycles while higher timeframes continue**. The Weekly open "decouples" from the Monthly open after the first week ends—starting in week 2, the Weekly open resets to a new price level while the Monthly open remains fixed at the beginning-of-month price. Similarly, the Daily open decouples from the Weekly open after the first day of the week ends—starting on day 2 of the week, each new Daily open establishes at its own price level while the Weekly open stays anchored to Monday's opening price.

### The progressive decoupling sequence

The algorithmic representation of the decoupling timeline:

```
// MONTH START (Day 1, Week 1)
Monthly_Open = Current_Price
Weekly_Open = Current_Price  // COUPLED to Monthly
Daily_Open = Current_Price   // COUPLED to both Monthly and Weekly
Status: All timeframes COUPLED

// WEEK 1, Day 2+
Monthly_Open = Original_Month_Start_Price  // FIXED
Weekly_Open = Original_Week_Start_Price    // FIXED (still Week 1)
Daily_Open = New_Daily_Start_Price         // DECOUPLED - resets each day
Status: Daily DECOUPLED from Weekly/Monthly

// WEEK 2, Day 1
Monthly_Open = Original_Month_Start_Price  // FIXED
Weekly_Open = New_Week_Start_Price         // DECOUPLED - resets after Week 1
Daily_Open = New_Week_Start_Price          // COUPLED to new Weekly open
Status: Weekly DECOUPLED from Monthly; Daily coupled to Weekly

// WEEK 2, Day 2+
Monthly_Open = Original_Month_Start_Price  // FIXED
Weekly_Open = Week_2_Start_Price           // FIXED (for this week)
Daily_Open = New_Daily_Start_Price         // DECOUPLED - resets each day
Status: All timeframes operating independently
```

This progressive independence creates windows where smaller timeframe participants can **negate or reinforce** the larger timeframe direction. When the Weekly open decouples from the Monthly open, weekly traders can break the weekly low, creating a 2D (down) scenario that opposes a bullish monthly candle. When the Daily open decouples from the Weekly open, daily traders can reverse the weekly direction by taking out the daily high/low in opposition to the weekly trend.

### Trading implications: The first period hazard

The decoupling concept introduces a critical risk management principle: **exercise caution entering positions during the first period of a new higher timeframe** because smaller timeframes remain coupled and lack the independence to provide confirming or negating signals.

**First week of the month hazard**: On the first trading day of a new month, Monthly, Weekly, and Daily opens are identical (coupled). If monthly participants push price higher, the weekly and daily timeframes move in lockstep—they cannot provide independent confirmation because they share the same starting point. A trader entering long based on "all timeframes green" fails to recognize these timeframes haven't truly decoupled yet. Once the first week completes and the Weekly open decouples in week 2, weekly participants might immediately reverse the move by taking out the week 1 low, negating the monthly direction and stopping out traders who entered too early.

**First day of the week hazard**: Similarly, on Monday (first day of a new week), the Weekly and Daily opens couple at the same price. Daily participants cannot provide independent confirmation of the weekly direction until Tuesday when the Daily open decouples. Entering trades on Monday based on "daily and weekly alignment" ignores that these timeframes haven't gained independence yet.

The algorithmic trading rule: `IF (current_day == first_day_of_month) OR (current_day == first_day_of_week) THEN position_size = position_size × 0.5 OR wait_for_decoupling = TRUE`. Alex specifically recommends either trading smaller position sizes on these first periods or waiting entirely until lower timeframes decouple and can provide genuine independent confirmation or negation.

### Decoupling detection and information gathering

Algorithmically detecting when timeframes have decoupled:

```
FUNCTION check_decoupling_status(current_datetime):
    month_start = get_month_start_datetime()
    week_start = get_week_start_datetime()  
    day_start = get_day_start_datetime()
    
    // Check if we're in first week of month
    IF current_datetime < month_start + 5_trading_days:
        monthly_weekly_coupled = TRUE
    ELSE:
        monthly_weekly_coupled = FALSE
        
    // Check if we're on first day of week
    IF current_datetime.date == week_start.date:
        weekly_daily_coupled = TRUE
    ELSE:
        weekly_daily_coupled = FALSE
    
    // Determine decoupling status
    IF monthly_weekly_coupled == TRUE:
        RETURN "HIGH_RISK - Monthly and Weekly coupled, wait for week 1 completion"
    ELSE IF weekly_daily_coupled == TRUE:
        RETURN "MODERATE_RISK - Weekly and Daily coupled, wait for day 1 completion"  
    ELSE:
        RETURN "DECOUPLED - All timeframes operating independently"
```

Once timeframes decouple, traders gain "more accurate information about market conditions" because each timeframe's participants make independent decisions. A decoupled Weekly timeframe taking out its low provides genuine negation of the Monthly direction rather than being artificially forced into alignment by coupled opens. A decoupled Daily timeframe breaking its high confirms the Weekly direction through independent participant action rather than shared starting points.

### Practical application: The Boeing example

Alex's Boeing (BA) chart example demonstrates decoupling in action. The setup showed a 2-2 to 3 reversal pattern where the weekly high was taken out (suggesting bullish continuation), but then price reversed. The decoupling concept explains why: if this occurred early in a new week or month when timeframes were still coupled, the initial break lacked confirmation from independent timeframe participants. Once timeframes decoupled and gained independence, participants at the decoupled timeframe level reversed the move, taking out lows and negating the higher timeframe direction.

The trading lesson: `IF pattern_forms AND timeframes_coupled == TRUE THEN wait_for_confirmation = TRUE AND reduce_position_size = 0.5 × normal_size`. Even when perfect STRAT patterns appear, coupled timeframes reduce reliability because lower timeframe participants haven't gained independence to confirm or negate the move. Patience for decoupling completion provides "clearer information" and reduces risk of being trapped in false moves that reverse once timeframes gain independence.

### Integration with FTFC framework

Decoupling enhances the FTFC (Full Time Frame Continuity) framework by adding a temporal dimension to timeframe analysis. The modified FTFC algorithm:

```
FUNCTION enhanced_FTFC_check(price, timeframe_opens, datetime):
    // Standard FTFC check
    basic_FTFC = check_all_opens_alignment(price, timeframe_opens)
    
    // Add decoupling status
    decoupling_status = check_decoupling_status(datetime)
    
    IF basic_FTFC == "FTFC_UP" OR basic_FTFC == "FTFC_DOWN":
        IF decoupling_status == "HIGH_RISK":
            RETURN "FTFC_PRESENT_BUT_COUPLED - Reduce size or wait"
        ELSE IF decoupling_status == "MODERATE_RISK":
            RETURN "FTFC_PRESENT_PARTIAL_COUPLING - Trade cautiously"
        ELSE:  // DECOUPLED
            RETURN basic_FTFC + "_CONFIRMED - Full confidence"
    ELSE:
        RETURN basic_FTFC  // Conflict or no FTFC
```

This creates a hierarchical confirmation system: timeframes must align in direction (FTFC) AND have decoupled (achieved independence) for maximum probability setups. The decoupling concept explains why certain FTFC setups fail—they appeared during coupled periods when timeframes lacked the independence needed for genuine multi-timeframe confirmation.

For algorithmic implementation, track timeframe start dates/times, implement coupled period detection, apply position sizing adjustments during coupled periods, and wait for decoupling completion before entering full-size positions on higher-probability setups. This refinement reduces risk during vulnerable market phases when apparent timeframe alignment lacks the substance of independent participant confirmation.

## Entry techniques: Algorithmic precision for pattern recognition and triggers

The STRAT system identifies specific multi-bar patterns that signal high-probability entry points. Each pattern has exact trigger conditions programmable without discretionary interpretation. The critical concept of a pattern being **"in force"** determines when to enter—patterns exist structurally but only become actionable when price breaks the trigger level.

### 2-2 Reversals: Directional shift without consolidation

The **2-2 reversal** represents the most direct reversal formation—two consecutive directional bars breaking in opposite directions. **Bullish 2-2**: `IF candle[n-1] = 2D (bearish directional) AND candle[n] = 2U (bullish directional) AND located at support/demand zone THEN 2-2 Bullish Reversal exists`. The exact entry trigger: `ENTRY = Long at candle[n-1].high + $0.01`. Stop loss goes `below candle[n].low`, with target at the previous swing high or the high of the candle before the 2D bar.

The pattern becomes "in force" when `price > candle[n-1].high`, meaning price has broken above the bearish directional bar's high, confirming the reversal. Confirmation strengthens when the candle closes above this level. Invalidation occurs `IF price fails to break candle[n-1].high AND continues making lower lows`. The bearish version inverts all logic: 2U followed by 2D at resistance, entry at `candle[n-1].low - $0.01`, stop `above candle[n].high`.

### 3-1-2 Reversals: The highest-probability reversal pattern

The **3-1-2 reversal** combines range expansion, consolidation, and directional breakout in a three-bar sequence. **Bullish 3-1-2**: `IF candle[n-2] = 3D (bearish outside bar) AND candle[n-1] = 1 (inside bar within candle[n-2]) AND candle[n] breaks candle[n-1].high (creating 2U) AND located at support/demand zone THEN 3-1-2 Bullish Reversal exists`.

Entry precision: `ENTRY = Long at inside_bar.high + $0.01`. Conservative traders wait for candle close above the inside bar high. Stop placement options include `below inside_bar.low` (tighter) or `below 3D outside_bar.low` (wider but safer). **Target 1** = `candle[n-2].high` (the outside bar high), **Target 2** = previous resistance level. The pattern goes "in force" the moment price breaks the inside bar high—do NOT wait for candle close in aggressive implementations.

```
// 3-1-2 Bullish Entry System
IF candle[-2].type == "3D" (outside bar, bearish):
    IF candle[-2].high > candle[-3].high:
        IF candle[-2].low < candle[-3].low:
            outside_bar_confirmed = True
            
IF candle[-1].high < candle[-2].high:
    IF candle[-1].low > candle[-2].low:
        inside_bar_confirmed = True
        inside_bar_high = candle[-1].high
        inside_bar_low = candle[-1].low

IF price_at_support_level == True AND downtrend_present == True:
    location_valid = True

IF outside_bar_confirmed AND inside_bar_confirmed AND location_valid:
    IF current_price > inside_bar_high:
        # Pattern "IN FORCE"
        ENTER_LONG:
            entry_price = inside_bar_high + 0.01
            stop_loss = inside_bar_low
            target_1 = candle[-2].high
            position_size = (account_risk × account_value) / (entry_price - stop_loss)
```

Invalidation occurs `IF candle[n] breaks inside_bar.low instead of high` or `IF candle[n] breaks BOTH high AND low` (becomes an outside bar rather than directional break). The market psychology: the outside bar represents major market decision, the inside bar shows consolidation after expansion, and the directional break confirms the reversal with trapped traders on the wrong side.

### Inside bar breakouts: Trading compression releases

Inside bars represent consolidation points where the market must choose direction. The **"mother bar"** is the previous bar that contains the inside bar. Entry rules: `Bullish Breakout: ENTRY = Buy stop at mother_bar.high + $0.01` with `STOP = mother_bar.low` and `TARGET = 1.5:1 to 2:1 risk/reward ratio`. Bearish breakouts invert this logic.

Three confirmation tiers exist: **Aggressive** enters immediately on break, **Conservative** waits for candle close beyond the mother bar range, **Most Conservative** requires the next candle to open beyond the mother bar range. Higher probability setups occur when inside bars form within prevailing trends (trend-aligned) or at key support/resistance levels.

A powerful variation is the **Hikkake Pattern**: inside bar at support in a downtrend, price breaks below inside bar low (false breakout), then reverses to break inside bar high—enter long on the reversal breakout. Invalidation occurs `IF inside bar not triggered within 3 bars THEN cancel pending orders` as pattern effectiveness deteriorates with time.

### Rev Strats (1-2-2 patterns): False breakout traps

The **Rev Strat** or **1-2-2 reversal** exploits false breakouts from inside bars. **Bullish 1-2-2**: `IF candle[n-2] = 1 (inside bar) AND candle[n-1] = 2D (breaks inside_bar.low - FALSE BREAKOUT) AND candle[n] = 2U (breaks candle[n-1].high - REVERSAL) AND located at support/demand zone THEN 1-2-2 Bullish Rev Strat exists`.

Entry mechanics: `ENTRY = Long at candle[n-1].high + $0.01` (the 2D directional bar's high), `STOP = below candle[n-1].low` (the false breakout low), `TARGET = high of mother bar before inside bar OR previous resistance`. The market psychology reveals retail traders entering short on the 2D breakdown, then getting trapped when big players reverse the move (2U), creating strong momentum from short covering.

This pattern invalidates `IF inside bar forms within ranging market (not at key level)` where false breakouts lack follow-through, or `IF the 2D/2U bar breaks BOTH high AND low of inside bar` (becomes Scenario 3 instead). Location significance matters enormously—Rev Strats at major support/resistance zones have dramatically higher success rates than mid-range formations.

### Hammers and shooters: Exhaustion signals with precise triggers

STRAT hammers and shooters differ from traditional candlestick patterns—they require specific criteria and only become actionable when broken. **Hammer (Bullish Reversal)**: `IF downtrend exists AND candle.body in upper 33% of range AND lower_shadow >= 2 × body_size AND upper_shadow minimal THEN hammer exists`. The body position calculation: `IF (candle.high - body_top) / total_range <= 0.33 THEN body in upper 33%`.

Critically, the hammer pattern goes **"in force"** only when `price breaks hammer.high + $0.01`. Entry occurs at this breakout, confirmation when the next candle closes above hammer high, stop loss below hammer low, target at previous resistance or next 2U directional bar high. If price continues making lower lows without breaking the hammer high, the pattern invalidates—no entry.

**Momo Hammer (Bullish Continuation)** forms DURING uptrends near the high of previous bullish candles, showing pullback/profit-taking with a long lower shadow. When price breaks the momo hammer high, it signals continuation. The primary use: trail stop losses to below the momo hammer low, enabling traders to hold winning positions longer during strong trends.

**Shooter (Bearish Reversal)** inverts the hammer logic: appears after higher highs, body in lower 33% of range, long upper shadow (2x+ body size), minimal lower shadow. Goes "in force" when `price breaks shooter.low - $0.01`. **Momo Shooter (Bearish Continuation)** forms during downtrends and serves primarily for trailing stops above its high. Both shooter types require the breakout to become actionable patterns—their mere existence provides warning but not entry signals.

### Confirmation hierarchy and "in force" status

The **"in force" concept** represents when patterns transition from structural existence to actionable trading signals. Implementation: `FOR reversal patterns (2-2, 3-1-2, 1-2-2): IF price breaks trigger_level THEN pattern = "in force" AND generate_entry_signal`. For hammers/shooters: `IF price breaks hammer.high OR shooter.low THEN pattern = "in force"`. For inside bars: `IF price breaks mother_bar.high OR mother_bar.low THEN pattern = "in force"`.

Three confirmation levels balance entry timing versus false breakout risk: **Level 1 (Aggressive)** enters immediately when price breaks trigger level by $0.01, providing best entry price but higher false breakout risk. **Level 2 (Moderate)** waits for candle CLOSE beyond trigger level, offering reduced false breakouts with good entry prices. **Level 3 (Conservative)** requires the NEXT candle to OPEN beyond trigger level, providing strong confirmation at the cost of missing some price.

Timeframe continuity confirmation overlays on all patterns: Check higher timeframes (Monthly, Weekly, Daily, 60-min) and `IF all timeframes show same direction (all green OR all red) THEN timeframe_continuity = aligned AND entry signal has highest probability`. The hierarchy: identify higher timeframe direction, look for actionable signals on entry timeframe, confirm with 60-minute control timeframe showing same direction.

### Pre-market versus regular hours: Session-specific considerations

Regular trading hours (9:30 AM - 4:00 PM ET) provide optimal conditions—highest liquidity, tightest spreads, most reliable price action. All STRAT patterns function as designed during regular hours with good volume. Pre-market (4:00 AM - 9:30 AM ET, most active 8:00 AM+) features much lower liquidity, higher volatility, wider spreads, and LIMIT ORDERS ONLY (no market orders or stop orders).

STRAT pattern reliability decreases pre-market because lower volume creates false breakouts, prices can gap significantly at market open, and inside bars may not hold at 9:30 AM. The recommendation: `IF trading pre-market THEN pattern_reliability = LOWER`. Best practice uses pre-market for watching pattern formation, preparing entry orders for regular session, and identifying gaps and key levels—NOT for primary entry execution unless very experienced.

The safer approach: `WAIT for 9:30 AM market open → OBSERVE first 15-30 minutes → CONFIRM pattern still valid with regular hours volume → THEN enter with normal STRAT rules`. If strong patterns form pre-market with news catalysts, mark key levels but wait for regular session confirmation. After-hours (4:00 PM - 8:00 PM ET) carries identical limitations. Timeframe continuity remains valid across all sessions, making after-hours useful for analyzing higher timeframe alignment and planning next day's trades.

## Exit techniques and risk management: Mechanical rules for stops and targets

STRAT's exit methodology provides algorithmic precision matching its entry rules. Stop placement, target selection, position sizing, and trade management follow exact formulas eliminating discretionary decisions that plague manual trading systems.

### Stop loss placement: Pattern structure defines initial risk

**Pattern-based stops** use the structure that created the entry signal. For **2-2 patterns**: `Stop_Long = Pattern_Low - buffer` and `Stop_Short = Pattern_High + buffer`. For **3-1-2 reversals**: `Stop_Long = Pattern_Low - ATR_multiplier` (beyond entire pattern range) and `Stop_Short = Pattern_High + ATR_multiplier`. For **2-1-2 patterns**: `Stop_Long = InsideBar_Low - buffer` and `Stop_Short = InsideBar_High + buffer`. For **1-2-2 Rev Strats**: stops go beyond the first directional bar—`Stop_Long = below first 2D candle low`, `Stop_Short = above first 2U candle high`.

The buffer amount typically ranges from $0.01-$0.10 for stocks, 1-5 ticks for futures, depending on asset volatility and spread. ATR multipliers (Average True Range) when used run 1.5x to 2x ATR for stop cushion. STRAT emphasizes **"very tight stops"** using price structure on lower timeframes, enabling small risk per trade with favorable risk/reward ratios. If stopped out, losses remain "very small" by design.

### Trailing stops: Algorithmic methods for protecting profits

AlexsOptions developed a precise trailing stop method alternating between scenarios. **Scenario 1 - Uptrend Trail**: `IF previous_high is violated THEN Trail_Stop = low of prior candle` and `CONTINUE trailing until previous_low is violated` then `SWITCH to Scenario 2`. **Scenario 2 - Downtrend Trail**: `IF previous_low is violated THEN Trail_Stop = high of prior candle` and `CONTINUE trailing until previous_high is violated` then `SWITCH to Scenario 1`.

Implementation uses green trail lines for uptrends (trailing lows) and red trail lines for downtrends (trailing highs), updating with each completed candle. The aggressive **one-bar trailing stop**: `FOR LONG TRADE: Stop_Loss = Low of most recently completed bar`, which ONLY moves UP, never down, updating with EACH candle close. Alternative methods trail using higher timeframe opens as reference points rather than previous bar extremes.

The critical rule: `IF 60M changes color (green to red or red to green) THEN consider exit` as this signals the control timeframe reversing. Similarly, `IF higher TF forms reversal pattern THEN exit OR scale out` protects profits when larger timeframe momentum shifts.

### Target setting: Sequential profit-taking with measured moves

**Primary target sequence** follows pattern structure: **Target 1** = Pattern high/low or next significant level in price structure. **Target 2** = Next structure level beyond Target 1 or broadening formation target. **Target 3** = Extended target based on Pivot Machine Gun levels or Triangle They Out projections.

**Broadening formation targets** use measured moves: (1) Identify broadening formation with diverging trendlines, (2) Measure `range = Distance between trendlines at widest point`, (3) Calculate `Target = Breakout_Point + Range` for bullish breakouts or `Target = Breakout_Point - Range` for bearish breakdowns. Alternative approach trades within the formation: buy near lower trendline, sell near upper trendline, with target at opposite side.

**Pivot Machine Gun (PMG) targets** provide extended profit projections. When price creates 5+ consecutive higher lows (bearish PMG setup) or lower highs (bullish PMG setup), each pivot level becomes a potential take-profit target. On reversal, price "fires through" all these levels rapidly. The ultimate PMG target is the pattern origin (starting point). **Triangle They Out (TTO) targets** project trendlines extended from the consolidation showing how far price can travel, typically reaching resolution on the 4th, 5th, or 6th wave.

### Position sizing and scaling: Mathematical risk management

The foundation: `Standard_Risk = 1-2% of total account per trade` with `Maximum_Total_Risk = No more than 3% across all open positions`. The position size formula eliminates guesswork: `Position_Size = (Account_Value × Risk_Percentage) / Stop_Distance`.

Example calculation: `Account = $100,000`, `Risk = 1% = $1,000`, `Entry = $50`, `Stop = $48`, `Stop_Distance = $2`, therefore `Position_Size = $1,000 / $2 = 500 shares`. This automatically adjusts for volatility—wider stops require smaller position sizes to maintain consistent dollar risk. Market volatility adjustment: `IF Market_Volatility = HIGH THEN Position_Size = Position_Size × 0.75`.

**Scaling out** follows sequential rules: `AT Target_1: Close 25-33% of position AND move stops to break-even on remaining`, `AT Target_2: Close 25-33% of position AND trail stop using previous candle method`, `AT Target_3: Close remaining OR trail aggressively`. **Scaling in** (adding to winners): `IF trade reaches Target_1 AND maintains FTFC THEN Add_Position = 0.5 × Original_Position_Size` with `Stop for new add = Entry of first position` (now at profit).

The **80/20 rule** in STRAT context applies to trade selection rather than position sizing: 80% of profits typically come from 20% of trades (the high-probability FTFC setups). This guides capital allocation—focus on Full Time Frame Continuity trades, reduce position size on lower-conviction setups. The principle: not all patterns deserve equal capital commitment.

### Break-even rules: Protecting capital once profitable

Three triggers for moving stops to break-even provide mechanical rules: **Trigger 1**: `IF price reaches 50% of distance to Target_1 THEN Move Stop to Entry_Price`. **Trigger 2**: `IF 2-candle forms in direction of trade AFTER entry THEN Move Stop to Entry_Price - Commission`. **Trigger 3**: `IF price breaks above higher_timeframe_open (for longs) THEN Move Stop to higher_timeframe_open`.

Algorithmic implementation: `IF Current_Price >= (Entry_Price + (Target_1 - Entry_Price) × 0.5) THEN Stop_Loss = Entry_Price AND Alert("Stop moved to break-even")`. This locks in a no-loss trade while allowing continued profit potential. The higher timeframe open method protects profits by raising stops to structural support levels that confirm trend continuation.

### Full Time Frame Continuity as risk filter

FTFC functions as a mandatory entry condition and risk adjustment mechanism. The entry filter: `CHECK all timeframe opens (Quarterly, Monthly, Weekly, Daily, Hourly)` then `FOR LONG: IF Current_Price > ALL timeframe opens THEN FTFC = TRUE → Trade allowed ELSE FTFC = FALSE → Skip trade`. The inverse applies for shorts.

Risk adjustment based on alignment: `IF FTFC = TRUE (all timeframes aligned) THEN Risk_Per_Trade = 2% (maximum)`, `IF FTFC = PARTIAL (4 of 5 aligned) THEN Risk_Per_Trade = 1%`, `IF FTFC = FALSE THEN Skip_Trade = TRUE`. This creates tiered position sizing reflecting probability—maximum capital commitment only when probability is highest.

Trade management scenario algorithms define exact actions: **Scenario A** (immediate favor): move to break-even after 1:1, scale out 33% at Target_1, trail remainder. **Scenario B** (consolidation): hold with original stop, exit only if stopped or opposite break occurs. **Scenario C** (target reached but FTFC remains): close 50%, move stop to Entry + 50% of gain, look for re-entry. **Scenario D** (FTFC breaks): `IF higher timeframe forms opposite 2-candle THEN EXIT immediately (market order)` and close all positions, wait for FTFC re-establishment before new entries.

### Risk/reward ratios and trade selection

Minimum acceptable ratios provide filtering: `Standard_Minimum = 1:2 (risk 1 to make 2)`, `Preferred = 1:3 or better`, `STRAT_Typical = 1:1.5 to 1:5`. Calculation: `Risk_Reward_Ratio = Stop_Distance / Target_Distance`. Example: Entry $100, Stop $98 (risk $2), Target $106 (gain $6), therefore `R/R = 2/6 = 0.33` (excellent 1:3 ratio).

Trade selection algorithm: `IF Risk_Reward_Ratio > 0.50 THEN REJECT trade` (worse than 1:2), `IF Risk_Reward_Ratio <= 0.33 THEN ACCEPT trade` (1:3 or better). This mechanical filtering eliminates trades with insufficient reward relative to risk, a critical component for long-term profitability.

## Advanced concepts: PMG, broadening formations, and simultaneous breaks

Beyond basic patterns, STRAT incorporates advanced concepts providing magnitude projection, structural understanding, and probability confirmation through market-wide analysis.

### Pivot Machine Gun: Magnitude projection through consecutive pivots

The **Pivot Machine Gun (PMG)** identifies areas where price has created 5+ consecutive lower highs (bearish consolidation) or 5+ consecutive higher lows (bullish consolidation). On trend reversal, price rapidly breaks through ALL these pivot levels in succession, "firing through them like bullets from a machine gun." The minimum requirement is 5 consecutive candles, though many traders require 6+ for higher confidence.

**Bullish PMG setup identification**: (1) Find series of 5+ lower highs in previous candlesticks, (2) Draw horizontal line at each lower high extending right, (3) Each lower high becomes a potential take-profit level, (4) Look for 2D-2U reversal pattern to trigger, (5) Confirm with timeframe continuity. **Bearish PMG setup** inverts this—5+ higher lows followed by 2U-2D reversal.

The market psychology: during formation, price consumes demand/supply through consecutive moves while retail traders place stops below lows/above highs. Market makers build up "ammunition" at each pivot. During reversal, rapid breaks trigger cascading stop losses, increased volatility as retail stops defend levels, and supply/demand imbalance causes swift moves to PMG origin.

Trading implications create extended profit potential. Entry waits for confirmed reversal pattern (2-2 reversal) that must align with timeframe continuity, entering on breakout of reversal pattern. Take-profit levels use each pivot as potential TP, enabling trail stops through each level. The ultimate target reaches the PMG pattern origin (starting point), significantly extending profit potential versus standard patterns. Probability increases during major news events when emotional participation amplifies the "machine gun" effect.

### Broadening formations: The continuous nature of price discovery

Broadening formations represent Smith's third Universal Truth: "The broadening formation occurs constantly on every timeframe and is how we gauge magnitude." Contrary to traditional technical analysis claiming these patterns are rare, Smith emphasized they occur continuously—price constantly trades in series of higher highs AND lower lows creating expanding ranges.

The significance in STRAT: price discovery works through expansion and contraction cycles. **Expanding markets** (higher highs AND lower lows simultaneously) feature Scenario 3 (outside bars) dominance, high volatility, and opportunity for prepared traders. **Contracting markets** (lower highs and higher lows) feature Scenario 1 (inside bars) dominance, consolidation/indecision, and imminent breakouts.

Identification requires connecting successive pivot highs with rising trendline and successive pivot lows with falling trendline, creating a megaphone-shaped pattern. These exist on ALL timeframes simultaneously—lower timeframes show detail, higher timeframes show major structural broadening. When a Scenario 3 (outside bar) appears on higher timeframes, lowering the timeframe reveals the detailed broadening wave structure.

Two primary trading strategies: **Breakout strategy** waits for price to break above upper or below lower trendline with strong volume, waits for retest of broken trendline, enters after retest confirmation, places stop beyond broken trendline, and targets by projecting the range from breakout point. **Swing within pattern** trades bounces off trendlines—long near lower line, short near upper line—requiring precise timing and quick exits.

Rob Smith's warning remains critical: "You'll get chopped up trading too early in price discovery." The correct approach waits for broadening formation to develop, avoids trading initial expansion, catches reversal BACK through the formation, or waits for clear breakout confirmation. Patience prevents whipsaws during the erratic discovery phase.

### Momentum continuations: Multi-bar patterns confirming trend persistence

Momentum continuation patterns signal the prevailing trend will persist, combining directional bars with inside bars to show brief consolidation before resumption. The **2-2 continuation** (two consecutive directional bars breaking the same direction) shows strong momentum. **Bullish 2-2 (2U-2U)**: two consecutive 2-Up candles, each breaking previous high, signaling strong buyer momentum and bullish continuation. **Bearish 2-2 (2D-2D)**: two consecutive 2-Down candles, each breaking previous low, signaling strong seller momentum and bearish continuation.

Primary use for 2-2 continuations: confirm trend on HIGHER timeframes. When monthly, weekly, and daily all show 2-2 alignment in the same direction, this provides full timeframe continuity. Traders then execute actionable signals on lower timeframes in the confirmed direction.

The **2-1-2 continuation** (directional bar → inside bar → directional bar in same direction) represents consolidation within trend before resumption. Bullish 2-1-2: First 2U shows upward momentum, inside bar (1) provides consolidation pause, second 2U breaks inside bar high confirming continuation. Market psychology reveals the directional bar showing momentum, inside bar as market indecision, and break of inside bar as participants deciding trend continues. Failure to break (pattern breaking opposite direction) warns of potential reversal.

The **3-1-2 continuation** (outside bar → inside bar → directional bar in same direction) shows expansion, consolidation, then continuation. Should form WITHIN prevailing trend, NOT at support/resistance (where it would signal reversal instead). The Scenario 3 represents major market decision/expansion, inside bar shows consolidation to a single point making breakout imminent, and directional break confirms trend continuation. Entry occurs on break of inside bar (2U or 2D), stop loss goes to opposite side of inside bar, first target reaches high/low of Scenario 3 candle.

General continuation trading rules mandate checking higher timeframes for continuation patterns, aligning direction across timeframes, and trading actionable signals on lower timeframes in the continuation direction. Critical rules: never fight continuation on higher timeframes, inside bars must NOT be violated during pattern formation, momentum indicated by directional bars breaking the same direction, and skip patterns against timeframe continuity.

### Simultaneous breaks: Institutional participation indicators

Simultaneous breaks occur when multiple related assets or timeframes break in the SAME direction at the SAME time, creating high-probability directional moves signaling institutional participation. The types include: **Time-based breaks** (multiple timeframes breaking simultaneously on the same day), **Price-based breaks** (multiple price levels broken at once, similar to PMG), **Sector-specific breaks** (all stocks in a sector breaking the same direction, like all tech stocks green with SMH green), and **Market-wide breaks** (multiple indices breaking the same direction, like SPY, QQQ, IWM all 2U on daily).

Identification protocol monitors 20 minutes after the hour checking gap lists for breaks, 10 minutes before top of hour looking for breaks that will change the next timeframe, and asks "What's the next 2? What will that create, negate, or do?" Sector analysis monitors biggest stocks in each sector, checks 1-2 representative sector ETFs, looks for concentration of 2s in the same direction. Example: if AAPL, MSFT, GOOGL all 2U plus QQQ 2U, this signals a tech sector break.

Trading implications leverage high probability characteristics: "When there is a high concentration of signals going in the same direction, it is very difficult to turn that around, so you have higher probability moves in that direction." Simultaneous breaks reveal institutional participation (not retail), sector rotation happening, strong directional bias difficult to reverse, and reduced risk of false breakouts.

Entry strategy identifies simultaneous breaks across sectors/indices, looks for STRAT patterns on individual stocks in that sector, enters aligned with simultaneous break direction, places stop loss per individual pattern rules, and extends targets due to strong momentum. Risk management recognizes simultaneous breaks reduce exhaustion risk, enabling holding through minor pullbacks, trailing stop losses as momentum continues, and exiting when correlation breaks or patterns invalidate.

### The flip concept and timeframe resets

When timeframes reset (bottom of hour for 60m, market open/close for daily, Monday for weekly, first of month for monthly, start of quarter for quarterly), they can "flip" the larger timeframe's direction. Example: Monday is 2U making the week 2U, Tuesday forms 2-2 reversal (2U-2D) flipping the week to 2D, and if it's the first week of the month, this can flip the month to red.

Trading the flip: **A flip back INTO FTFC after corrective activity (especially after a Scenario 1) represents highest probability setups**. Monitor 30m/60m for potential flips, look for reversal or continuation taking 60m into FTFC, and combine with simultaneous breaks for maximum probability. During heightened volatility, smaller timeframes matter more as traders can see a week's worth of action in an hour, making flips happen faster and more frequently.

### Additional advanced patterns: TTO, RevStrats, and edge cases

**Triangle They Out (TTO)** represents broadening price consolidation AGAINST the major trend, forming higher highs and lower lows in a triangular pattern. Market makers use this to "keep retail traders out" by triggering stop losses while building positions. The minimum four-wave structure: Wave 1 (smallest, against main trend), Wave 2 (larger, fully engulfs Wave 1, creates first broadening), Wave 3 (larger than Wave 2, continues broadening), Wave 4 (often reversal wave back to original trend, can extend to Wave 5-6).

TTO trading uses two approaches: add to positions in primary trend direction at Wave 4+ reversal, or determine magnitude using trendline projections. Entry strategy identifies major trend via timeframe continuity, waits for TTO pattern completion (minimum Wave 4), looks for STRAT reversal patterns matching higher timeframe trend, and enters on reversal pattern confirmation. Take profit uses Fibonacci retracement to gauge depth, extended trendlines for next targets, holds until higher timeframe target reached, and combines with PMG for extended targets.

**RevStrats** represent strictly defined three-bar reversals: **RevStrat Hammer (1-2D-2U)** where the middle 2D candle must have hammer characteristics (small body in upper 30%, long lower wick 2x+ body, minimal upper wick), and **RevStrat Shooter (1-2U-2D)** where the middle 2U must have shooter characteristics (small body in lower 30%, long upper wick 2x+ body, minimal lower wick). These combine false breakout psychology with exhaustion signals for high-probability reversals.

**Edge cases** require special handling: **Exhaustion risk** occurs when patterns hit targets—don't add positions near targets, consider taking profit, watch for reversal signals. **Failed patterns** result from inside bars violated in wrong direction, price not breaking trigger levels, opposing timeframe continuity, or low volume on breakouts—exit immediately when invalidated. **Gap trading** combines emotional gaps with STRAT setups for "something special"—gaps create immediate scenarios (usually 2 or 3), look for patterns after gaps, high probability if gap direction matches timeframe continuity.

## Current resources and community: The post-Rob Smith era (2023-2025)

Rob Smith passed away July 23, 2023, after a brief illness, leaving behind "one of the most generous free educational trading communities" built on his philosophy that "knowledge should be collaborative and shared, not behind a paid wall." The STRAT community continues thriving through dedicated practitioners who preserve and extend his legacy.

### Key figures leading STRAT education

**Alex (@AlexsOptions)** serves as the primary continuation figure. Started trading crypto in 2015, shifted to stocks and options, and found consistency after discovering STRAT. Co-founder of STAT Trading with Sara and Tom, Alex creates free educational content, live trading streams showing real-time application, and the open-source "Strat Trail Stop" indicator on TradingView. Find Alex on Twitter/X @AlexsOptions, YouTube @AlexsOptions, and alexsoptions.com.

**Sara "Strat Sniper" (@TradeSniperSara)** began trading during 2017's crypto boom, discovered STRAT in 2018 which transformed her trading, and co-founded STAT Trading. Based in Naples, Florida, Sara popularized concepts like Pivot Machine Gun and created educational videos on broadening formations. She appears in Rob Smith's original practitioner list. Find Sara on Twitter/X @TradeSniperSara, YouTube "Sara Strat Sniper," Instagram @realsarastratsniper, and as part of the stratalerts.ai team.

**Tom** serves as tech expert at STAT Trading, handling platform development and technical infrastructure. Together with Alex and Sara, he built the "most powerful scanning tool the Strat community has ever seen."

Other notable practitioners from the GitHub community list include @LevJampolsky, @CyberDog2, @jam_trades, @JamesBradley_, @japor3, @WayoftheMaster7, @ADBYNOT, @chucknfones, @OptionizerSS, @r2dpepsi, @Banker_L83, @R2DayTrades, @FranknBear, @StratDevilDog, and @StratSoldier (who offers TrendSpider discount codes).

### Community platforms and engagement

The **STAT Trading Discord** (completely free) at discord.com/invite/stat-trading-801234481297227786 serves as the primary community hub with 10,474+ members focused on stock market education. Features include real-time support, trade insights, and community collaboration. Multiple other STRAT-focused Discord servers exist (search "thestrat" on DISBOARD), plus general trading Discord servers with STRAT channels.

**Twitter/X** remains the most active STRAT community platform. Search hashtags #TheStrat, #STRAT, #StratGodfather for direct engagement with practitioners and to see Rob Smith's legacy preserved through community posts. The **GitHub repository** at github.com/rickyzcarroll/the-strat created by @rickyzane85 provides comprehensive free resource compilation including terminology, patterns, practitioner lists, and tool links, maintaining Smith's philosophy that knowledge should be collaborative.

**Forex Factory Forums** host an active thread "Trading TheStrat / Rob Smith's Method" with 9+ pages of community discussion, forex-focused applications, and technical chart analysis. Reddit has limited dedicated STRAT presence but discussions occur in general trading subreddits.

### Scanners and software tools for implementation

**STAT Trading Scanner (stratalerts.ai)** created by Alex, Sara, and Tom provides real-time scanning for stocks, ETFs, and crypto with custom platform features for finding setups, evaluating potential, and tracking statistics. The platform is fully operational with free community access.

**TrendSpider** offers built-in STRAT patterns and indicators accessed via Indicators → Patterns → All Patterns → TheStrat. Features include 200+ technical indicators plus STRAT-specific tools, multi-timeframe analysis, automated pattern recognition, real-time scanning capabilities, and strategy backtesting with STRAT patterns. Use discount code "Strat Soldier" for 25% off.

**Alaric Securities HAMMER™ Platform** provides professional-grade integration with chart indicators specifically for STRAT, market scanners (historical and intraday versions), FTC scanners, and TheStrat Patterns multi-column scanners. Documentation includes "The Strat Fundamentals & The Strat HAMMER platform tools" PDF guide.

**MetaTrader Indicators** at thestrat-indicators.com offer TheStrat Levels Indicator (displays entry/exit points for all timeframes), TheStrat Patterns Indicator (real-time pattern recognition), and custom indicators for MT4/MT5 with free tools available.

**TradingView Scripts** feature multiple STRAT indicators (search "The Strat" in TradingView), including AlexsOptions' open-source "Strat Trail Stop" indicator and various community-created indicators. **Think or Swim** users access custom STRAT scripts shared on forums with ability to create custom scans.

**StratScanner.com** provides real-time stocks, ETFs, and crypto scanning specifically tailored to STRAT methodology. Note that **RunStrat.com** is CLOSING DOWN (mentioned in multiple sources), with users migrating to other platforms.

### Educational resources: Courses and free content

**Rob Smith's original course "The Strat"** remains available for $599 through Smith's In the Black or free with annual Ticker Tocker Live Room subscription. The course includes 14+ modules covering complete methodology: time frame continuity, broadening formations, actionable signals, hammers, shooters, and combos. Though Smith passed away in 2023, the course stays accessible.

**Free educational resources** abound maintaining Smith's philosophy. The GitHub repository (rickyzcarroll/the-strat) provides complete terminology guides, pattern explanations with examples, actionable signal descriptions, trading philosophy documentation, and resource links compilation. Rob Smith's YouTube channel "Smith's In the Black" (youtube.com/user/smithsintheblack) contains extensive free video library with original methodology explanations and the 2017 course in an unlisted playlist.

**STAT Trading** offers free strategy guides, blog posts, Discord community, and educational video library at stratalerts.ai. **AlexsOptions YouTube** provides live trading sessions, STRAT education videos, and real-time market analysis described by the community as a "treasure trove" of educational content. **Sara Strat Sniper YouTube** focuses on broadening formations, pattern recognition tutorials, and day trading with STRAT.

**Written resources** include free PDFs and ebooks: "The Strat Patterns PDF Ebook" at strat.trading, "The Strat Fundamentals & The Strat HAMMER platform tools" at alaricsecurities.com, and "THE STRAT TRADING STRATEGY [PDF]" at howtotrade.com. Educational websites like strat.trading, forexbee.co, lucidtrend.com, howtotrade.com, and fxopen.com provide comprehensive lessons and patterns.

**Essential reading** includes Rob Smith's foundational blog post "What Do We Know to Be True About Price Action?" (NewTraderU.com, February 2019), Ticker Tocker newsletters (historical archive available), and Rob Smith's Twitter @RobInTheBlack (archived tweets with educational content preserved by community).

### Recent developments and methodology refinements (2024-2025)

The **post-Rob Smith era** (2023-present) features community-driven continuation of methodology maintaining the "each one teach one" philosophy with no single "official" authority but multiple respected educators. The free education model persists through community leaders while platform integration continues—TrendSpider maintains and updates STRAT features, new scanning platforms emerge like STAT Trading scanner in 2024-2025.

**February 2025** saw FXOpen publish "How Can You Use the STRAT Method in Trading?" offering modern interpretation, practical application covering expanding/contracting market phases, and updates for current market conditions. Throughout 2024, multiple PDF guides published, video content continued from AlexsOptions and Sara, and TikTok presence grew with STRAT education.

**Core principles remain unchanged**: the three candle scenarios (1-2-3), Full Time Frame Continuity, broadening formations, and actionable signals. **Community additions** include enhanced understanding of Pivot Machine Gun (Sara's teaching), Triangle They Out applications, integration with modern trading platforms, options-specific applications, and crypto and futures adaptations.

**Technology advancements** bring AI-assisted STRAT pattern recognition (TrendSpider AI tools), real-time scanning capabilities, mobile app integrations, automated alerting systems, and backtesting capabilities for STRAT strategies. The community philosophy emphasizes free education (Rob Smith's legacy), "each one teach one" mentality, non-competitive collaborative environment, focus on logical rule-based trading, and emotional neutrality in trading decisions.

### Recommended learning path and implementation

**For complete beginners**: Start with the free GitHub repository (github.com/rickyzcarroll/the-strat) learning terminology, understanding three scenarios, and studying basic patterns. Watch Rob Smith's YouTube videos for original explanations and foundation concepts including the 2017 course playlist. Join STAT Trading Discord (free) to connect with active community, ask real-time questions, and see live discussions. Read foundational articles from TrendSpider Learning Center, FXOpen 2025 guide, and HowToTrade.com comprehensive guide.

**For implementation**: Choose a platform with STRAT tools—TrendSpider (most comprehensive), STAT Trading scanner (community-focused), or MetaTrader indicators (free option). Follow active practitioners @AlexsOptions on Twitter/YouTube, @TradeSniperSara on Twitter/YouTube, and #TheStrat hashtag on Twitter. Practice pattern recognition using free TradingView with STRAT scripts, paper trading with STRAT setups, and reviewing historical charts.

**For advanced study**: Consider Rob Smith's paid course ($599) for most comprehensive methodology and complete system understanding. Explore platform-specific advanced features like TrendSpider strategy backtesting, Alaric HAMMER advanced scanning, and custom indicator development. Engage deeply with the community through Forex Factory discussions, Discord advanced channels, and sharing your own analysis.

The STRAT methodology's universal applicability—working across ALL asset classes (stocks, options, forex, commodities, crypto, futures) and ALL timeframes (1-minute to yearly charts)—combined with clear entry/exit signals, built-in risk management, and scalability from beginner to advanced makes it ideal for algorithmic implementation. The cost structure ranges from completely free (GitHub, Discord, YouTube, blog posts, Twitter community) to paid options (Rob's course $599, TrendSpider subscription, STAT Trading premium features), with many traders succeeding using only free resources.

## Synthesis: Building a complete algorithmic STRAT system

Implementing STRAT algorithmically requires combining all components into integrated decision logic. The system architecture flows through these stages:

**Stage 1 - Bar Classification**: For each new bar on each relevant timeframe, execute the scenario classification algorithm determining if the bar is 1 (inside), 2 (directional up/down), or 3 (outside up/down). This creates the fundamental language for all subsequent analysis.

**Stage 2 - Multi-Timeframe State Assessment**: Check FTFC status across all five major timeframes (Quarterly, Monthly, Weekly, Daily, 60-minute), determining if FTFC Up (all green), FTFC Down (all red), or Conflict (mixed). Simultaneously assess each timeframe for 2-2 continuation patterns or scenario 1 inside bars that would block trading.

**Stage 3 - Control Timeframe Analysis**: Evaluate the 60-minute "in control" timeframe for current directional bias, recognizing it carries more weight than historical alignment on higher timeframes. Determine if current 60m action aligns with or conflicts against higher timeframe direction.

**Stage 4 - Pattern Recognition**: Scan for actionable patterns on the entry timeframe (typically 15m for day traders, 1H/4H for swing traders, Daily for position traders). Identify 2-2 reversals, 3-1-2 reversals, 1-2-2 Rev Strats, inside bar breakouts, hammers, shooters, and continuation patterns. Check each pattern's location context (support/resistance zones) for validity.

**Stage 5 - Probability Assessment**: Calculate pattern probability based on timeframe alignment count, FTFC status, simultaneous break concentration, and additional factors like PMG presence or TTO completion. Apply probability multipliers: `aligned_probability = base_probability × (1.0 + 0.15 × num_aligned_timeframes)`.

**Stage 6 - Risk/Reward Calculation**: For each valid pattern, calculate entry price (trigger level ± $0.01), stop loss (pattern structure on lower timeframe), and target (pattern high/low, broadening formation target, or PMG projection). Compute `Risk_Reward_Ratio = Stop_Distance / Target_Distance` and reject if > 0.50 (worse than 1:2).

**Stage 7 - Position Sizing**: Calculate `Position_Size = (Account_Value × Risk_Percentage) / Stop_Distance` with risk percentage adjusted for FTFC status (2% for full FTFC, 1% for partial alignment, 0% for conflict). Apply volatility adjustments if market volatility elevated.

**Stage 8 - Entry Execution**: Monitor for pattern to go "in force" (price breaks trigger level). Execute entry at confirmation level based on aggressiveness setting (immediate break, candle close beyond level, or next candle open beyond level). Place initial stop loss and target orders simultaneously.

**Stage 9 - Trade Management**: Implement break-even rules when price reaches 50% to target or 1:1 risk/reward. Apply trailing stop algorithm (Scenario 1 trailing lows in uptrend, Scenario 2 trailing highs in downtrend). Scale out at sequential targets (25-33% at T1, 25-33% at T2, remainder at T3 or trail).

**Stage 10 - Exit Logic**: Exit immediately if FTFC breaks (higher timeframe forms opposite 2-candle), stop loss hit, targets reached, or pattern invalidates (opposite direction break before trigger). Monitor for control timeframe color change (60m green to red or vice versa) as early exit warning.

**Stage 11 - Advanced Enhancements**: Layer in PMG detection for extended targets, simultaneous break monitoring for probability boosts, TTO recognition for add-on opportunities, and flip tracking for catching timeframe reversals back into FTFC.

The complete system provides mechanical, repeatable decision-making with zero discretion required. Every component—from bar classification through exit execution—follows Boolean logic and mathematical comparisons programmable in any trading platform. The key algorithmic advantages: pattern recognition is binary (patterns exist or don't), entry triggers are exact price levels, stops follow structural rules, targets use measured moves, position sizing follows formulas, and trade management uses conditional logic.

For maximum effectiveness, implement robust testing infrastructure: backtest on historical data across multiple assets and market conditions, forward test on paper trading accounts, optimize parameters (confirmation levels, buffer sizes, ATR multipliers) through systematic evaluation, and monitor live performance with detailed logging of pattern types, timeframe alignment, and outcome statistics.

The STRAT system's greatest strength for algorithmic implementation lies in its complete objectivity—Rob Smith deliberately designed every element to eliminate subjective interpretation, creating what he called trading based on what you KNOW to be true rather than what you THINK. This philosophical foundation translates directly into code, enabling traders to build reliable automated systems executing one of the most battle-tested methodologies in modern technical analysis.