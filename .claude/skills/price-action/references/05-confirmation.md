# Tools for Confirmation (Indicators & Moving Averages)

## Depth Over Breadth in Tool Selection

A trader's job is to find slight statistical edges by trading real imbalances of buying and selling pressure. Indicators and confirmation tools only help when they are deeply understood, including their quirks and how they interact with one another.

- **Limit scope** to a few simple tools that are completely understood; reject tools that do not add value to the analysis.
- **Filter before deciding**: raw information floods in; pre-filtered, trusted intelligence outperforms volume.
- **Ignore low-value inputs**: stale news, fundamentals outside your time frame, opinions from traders with different styles, and indicators that do not change your read of the structure.
- Patterns become more powerful when **placed in the context of the higher time frame** and **supported by price action on the lower time frame**; this chapter develops that interaction explicitly.

---

## The Moving Average: The Still Center

A moving average is a smoothed summary of price. It represents a rough area of consensus, or the price around which buyers and sellers are roughly balanced.

- **No magic length exists.** No specific period (e.g., 21 EMA, 50 SMA) is statistically better than any other.
- **Crosses and touches are not signals.** Claims like "hedge funds buy here" or "everyone watches this average" do not survive simple statistical tests; edges around average lines are not verifiable.
- **Reduce to first principles**: simple elements, then build up. Mastery requires a perfect grasp of basic behavior.

---

## Using Moving Averages

### As a Trend Indicator

A moving average is useful as a confirming trend tool, especially when scanning many charts quickly. Two related applications:

- **Price persistent on one side**: when price spends most of its time on one side of the average, the market is trending in that direction. Occasional dips or minor piercings are normal.
- **Slope**: a flat average suggests a trading range; up-sloping suggests an uptrend; down-sloping suggests a downtrend.
- Different lengths identify different trends at the same moment; the market can be in an uptrend, a downtrend, and a range simultaneously across time frames. Understand this rather than seeking a single answer.
- A trader reading price structure will almost always identify inflection points **before** a moving average confirms them.

### Avoid Markets in Equilibrium

Markets are usually in equilibrium, and at those times they are random walks. The essence of technical analysis is to identify temporary imbalance and restrict trading to those environments.

- Markets that **chop back and forth on both sides** of an intermediate-term moving average are likely in equilibrium.
- Absence of imbalance is virtually guaranteed when price hugs the average; avoid those environments.
- Simply avoiding equilibrium markets can eliminate many small losing trades and add to the bottom line.

### As a Reference for Trading Pullbacks

Markets move by alternating momentum thrusts and consolidations. Initiating a trade in the middle of an overextended momentum move is usually a poor plan.

- Use a moving average as a **crutch** to prevent buying or shorting an overextended market. The rule is the same in both directions.
- Wait for the market to work off the overextension and return to a short-term state of balance before entering a pullback.
- A simple, effective rule: **do not buy (or short) a pullback that is far from the moving average** once "far" has been precisely defined.
- A moving average is a good reference in a **normal trend**; very strong trends may not pull back as much.
- There is **no inherent edge** to executing at the line itself; context and trade management matter.

### Slope of a Moving Average

The slope is a subjective tool that does not test well quantitatively, but it is useful as a scanning aid and a cue for developing discretionaries.

- The time frame of the average roughly corresponds to the time frame of the trend it captures.
- **Do not** filter trades on this criterion (e.g., only take longs when the average slopes up). The lag will cause missed entries at the start of trends and permitted entries at the end, where most losses occur.
- An attentive trader will read the price-structure turn **before** the average changes slope.
- Slope is most useful when **scanning many charts rapidly**; rely on price structure for actual decisions.

---

## Channels: Emotional Extremes

Channels define excursions away from the area of consensus. Properly drawn, they highlight where the crowd reaches emotional extremes.

- Channels **do not provide barriers**. Lines on charts never stop price. Buying or selling at a band, with rare exceptions in highly mean-reverting instruments, is conceptually flawed.
- Treat the band as an **alert level**: monitor what price does after a touch or excursion rather than treating the line itself as a decision point.
- Bands must be set at a meaningful level. Too close yields noise; too far and they are never touched.

### Bollinger Bands vs. Keltner Channels

**Bollinger Bands** are set at a multiple of the standard deviation of price around an SMA (commonly 2σ around a 20-period SMA).

- Prices are **not normally distributed**; the standard 68/95/99.7 rules do not apply. Empirically, about **88% of closes** fall within two Bollinger standard deviations of a 20-period average, not 95%.
- Standard deviation of price is not a meaningful measure of volatility, so band width does not track most accepted volatility measures well.
- Large price changes create a "Bollinger balloon" effect; as volatility contracts, bands tighten aggressively and trigger on small moves.

**Keltner Channels** (and the closely related STARC modification) use a measure of range as the volatility input.

- They respond to a simpler, more consistent measure of volatility (bar range), and can be applied to close-only data via true range.
- Behavior: big bars produce wider bands, small bars produce tighter bands, in a measured and controlled way.
- The author's Keltner setting is calibrated to contain between **85 and 90% of total bar range** across a wide universe, with rare "free bars" where the entire bar lies outside the channel.

### Ideas for Using Channels

**Fade a move outside the channels**

- A slight statistical edge to fading moves that reach the upper or lower Keltner channel exists in many markets. Bollinger can be tuned to replicate it.
- Fading makes sense only when the market is **truly extended**; fading in equilibrium produces a steady stream of losses.
- Risk management is essential; the band is not a barrier.

**Enter on a pullback from the bands**

- A market overextended outside the band will, eventually, reverse back inside. The middle of the band is often a reasonable entry in the direction of the original touch.
- A common execution condition: a **close outside the band** marks the touch, then enter near the moving average on the return inside.
- This quantifies a fundamental principle of price action (impulse and consolidation) through the structure of an indicator.

**Slide outside the bands**

- When a market presses into one band and **stays there**, the structure is one-sided and difficult to trade.
- Pullbacks disappear; the pattern is often a higher-time-frame climax with snapback risk.
- Most traders will be tempted to keep fading; usually the better plan is to **stand aside** unless managing a preexisting position.

**Spike through both bands**

- A sharp move through one band immediately reversed and spiked through the other signals that the normal impulse-consolidation cycle has short-circuited.
- The usual expectation: an extended period of consolidation oscillating around a central price, often forming a triangle-type pattern.
- This is a **difficult trading environment** that is best avoided.

---

## MACD: Basic Interpretation

The MACD is a **momentum indicator**, not an overbought/oversold tool. Formally, it measures changes in momentum; in practice, treat it as a proxy for momentum itself.

- A change in momentum is more likely to lead to higher momentum than to reverse it; this persistence is what makes the proxy useful.
- The fast line can pick out inflections not clearly visible in price, mark swings more or less likely to continue, and flag overextended points where momentum may be exhausted.
- Applications transfer to other momentum indicators (ROC, Momentum), but **not** to overbought/oversold indicators (Stochastic, RSI). Different tools measure different things.

### Fast Line Pop

Markets move in alternating waves and retracements. A strong momentum move is usually followed by another move in the same direction after consolidation.

- **Momentum precedes price**: a sharp momentum thrust to new highs is usually followed by higher prices after a pullback. The reverse applies to the downside.
- Indicators do not literally lead price; they are calculated from past prices. What leads price is a strong underlying move, of which the indicator reading is a visual representation.
- A simple rule: after the fast line makes a **significant new high or low** relative to its recent history, enter the pullback in the same direction.
- The MACD is **unbounded**, so use rough intuitive guidelines by comparing to recent history. A more systematic version expresses the value as a percentile of a look-back window (e.g., top or bottom decile) over roughly 40 bars to start.

### Fast Line Behavior in Climax

Pullbacks or consolidations following climax moves are **not** high-probability trend-continuation trades; reversals or long consolidations are more common.

- A momentum move dramatically out of proportion to recent history is suspect. Be cautious about entering the next retracement.
- In extreme conditions the unbounded MACD rescales and recent history compresses into a tight wiggly line. **Disregard the indicator** in those conditions; the move itself is the signal that something is wrong.
- On intraday charts with large overnight gaps, this distortion is frequent; ignore the indicator until normal momentum returns.

### Fast Line Divergence

A new price extreme unaccompanied by a new indicator extreme suggests the dominant group may be losing its grip; a reversal becomes more likely than continuation.

- **Divergences fail about as often as they work.** A working definition of a trend is that it breaks support and resistance; trends also break divergences.
- Countertrend traders using divergences will face steady losses; trend traders using them as warning signs will exit prematurely.
- **Valid divergences require swings.** If price is sliding steadily higher with no retracement between the two points, the apparent divergence on the indicator is not real.
- Divergences are often temporary and fleeting. Treat a divergence as reset or fulfilled when any of these occurs:
  - Price returns to an intermediate-term (e.g., 20-period) moving average.
  - The fast line crosses the zero line from the divergent state.
  - An extended period (roughly 10+ bars) elapses.
- A logical inconsistency in classic divergence: pivot highs and lows are compared to an indicator built from closes. Possible corrections include using the midpoint of the bar or the typical price, or splitting the indicator into bullish-divergence and bearish-divergence variants. Simplicity is to be preferred; verify that any added complexity pays for itself.
- Be protective of open countertrend profits once any of the reset conditions appears.

### Beware of Overextended Fast Line Entries

The baseline expectation for any market is that it will fluctuate; extremes reverse.

- Try to **avoid buying when the fast line is extended into highs** and **avoid selling when it is extended into lows**.
- Many traders find a simple rule preventing entries against such extension improves results, even when the rule cannot be made precisely quantitative.

### Fast Line Drive and Hold

An indicator's ability to reach and stay in overbought territory is often evidence of real strength, not a sign to fade. The reverse is true for oversold.

- One of the common MACD patterns is the fast line pinning in extended territory for an extended period in a strong trend. The inability to back off reflects conviction, not exhaustion.
- A practical filter: look for divergence **only after the fast line has touched or come near the zero line**. If the line is pinned extended, there is no swing to diverge from and the information is unreliable.
- A valid divergence requires a countertrend swing on the price chart, and that swing will usually pull the fast line back to zero.

### Fast Line Hook

A turn in the fast line can be the first hint of emerging momentum, especially at an inflection point. The fast line's sensitivity lets it filter to the most important aspects of price action.

- Example rule: enter short on the first bar whose close turns the fast line down after price has penetrated below the lower band, with no momentum divergence present. The inverse generates longs.
- Hook entries are normally read against the bar close, so apparent entries on a large bar may sit near the bar's low.
- Combine hook entries with spread conditions between the fast and slow lines to filter for structural tension in the market.

### Slope of the Slow Line

The slow line is a 16-period SMA of the fast line, so it inherits all moving average quirks. It is a proxy for intermediate-term momentum, roughly 10 to 20 bars.

- Less noise and fewer false moves than the fast line is a reflection of smoothing and lag; many fast-line signals will be missed.
- Be suspicious of trades that set up **against the slope of the slow line when the slow line has been extended and turned back toward zero**. Treat this as a form of momentum divergence.
- The divergence tends to work itself off later in the extended trend, often accompanied by a complex consolidation on the price chart.

### Position of the Slow Line

The slow line's position relative to zero is itself a trend indicator and suffers the usual problems of any quantitative trend measure.

- Useful tension appears when the fast and slow lines disagree: if the slow line is extended above zero while the fast line pulls back below zero, the setup is often a long opportunity. The reverse applies for shorts.
- This condition highlights structural tension between short-term and intermediate-term momentum and is a real, repeatable layer of information.

---

## Multiple Time Frame Analysis

Multiple time frame analysis adds depth by placing one time frame's pattern in the context of another. The core task is to identify which time frame is in control at any moment.

- A naive assumption that higher time frames are always more important is wrong. Structures on any time frame can take control; control passes from one time frame to another.
- A practical default structure: trading time frame, plus a higher and a lower time frame, usually related by a factor of roughly 3 to 5.
- Master a single time frame before combining them; intuition about cross-time-frame flow requires proficiency on one frame.

### Lower Time Frame Structures within Higher Time Frame Context

The highest-probability single-time-frame trades share a short list of patterns: mean reversion after overextension or climax, the interface between pullback and new trend leg, drives to clear target areas, and failure tests at the extremes of a range with signs of accumulation or distribution. When these forms appear on a higher time frame, lower time frame action will be molded toward resolving them.

**Higher Time Frame Mean Reversion**

- The hardest problem in technical analysis is **distinguishing exhaustion from real strength**. A well-calibrated channel provides a quantitative reference for overextension.
- A buyable-looking pullback on the lower time frame can be neutralized by exhaustion above the channel on the higher time frame. A sloppy short setup on the lower time frame can be neutralized by three pushes down on the higher time frame ending in momentum divergence.
- The most useful contribution of the higher time frame is often to **skip trades that the lower time frame would otherwise have taken**, eliminating losers that fail immediately under the force of higher-time-frame mean reversion.
- Higher time frame considerations are not only filters. They can also justify an entry, for example, a short under a tight daily consolidation when the weekly is dramatically extended above the upper band with momentum divergence.

**Higher Time Frame Pullbacks**

Conditions that make pullbacks high probability on a single time frame, when present on the higher time frame, can motivate and add confidence to lower-time-frame entries:

- A good impulse setting up further continuation.
- Market is not overextended.
- Not on the third or later trend leg.
- No momentum divergence.
- No buying or selling climax.
- Pullback activity and volume lower than the trend leg.

A pullback that is mediocre on the trading time frame can be excellent when it is the first reaction to an overextended move on the higher time frame, and vice versa. Patterns on one time frame that contradict a clear pattern on a higher time frame, especially at potential inflection points, are dangerous; consider skipping, taking on smaller risk, or looking for the higher-time-frame pattern to fail rather than blindly trading the lower-time-frame pattern.

**Higher Time Frame Drives to Targets**

- When a pattern breaks into a drive to a target, lower-time-frame consolidations resolve in the direction of the drive and are reinforced by it.
- These contexts make otherwise uninteresting lower-time-frame patterns tradable.
- The same logic helps monitor an open trade: failures in the lower time frame often foreshadow failures on the trading time frame. Be careful not to overreact to noise on the lower time frame.

**Higher Time Frame Failure Tests**

- The strongest trends on a lower time frame often emerge inside higher-time-frame consolidation areas. A clean, strong uptrend on the daily can occur while the weekly is in a range.
- Trading ranges produce sudden, large moves on the trading time frame; one of the cleanest structures is a test beyond the range that immediately reverses (Wyckoff spring or upthrust). Reactions off the range boundary are tradable.
- Even traders who avoid ranging markets should be aware that opportunities exist on other time frames inside those ranges.

### Timing Entries from Lower Time Frames

The lower time frame usually serves two purposes: timing precise entries into the trading-time-frame pattern, and monitoring evolving conviction during a trade.

- Enter at important structural points on the higher time frame (support, resistance, prior pivots) using lower-time-frame breakouts as the trigger. A small, predictable step on the lower time frame can be amplified into a major move when the higher time frame is at a tipping point.
- Read lower-time-frame structure to add depth to the trading-time-frame read: are there clean consolidations and good breaks (a healthy trend), or are there overextensions and failed momentum pushes (a tired trend)? When the trading-time-frame pattern is approaching resistance, is the lower time frame showing rejection or, instead, tight consolidations that could presage a break?

### Summary of Multiple Time Frame Analysis

Core concepts to internalize:

- The best multi-time-frame examples are obvious. If you have to work to see them, they are probably not there.
- With-trend patterns on the lower time frame are reinforced by a trending higher time frame; countertrend patterns tend to abort.
- Some of the best trends occur inside higher-time-frame consolidation areas.
- An otherwise small breakout on the lower time frame can be amplified at critical tipping points on the higher time frame.
- Ranges on the lower time frame are often continuation patterns on the higher time frame, providing a directional bias for the breakout.
- The character of price action on the lower time frame is informative about underlying buying and selling pressure, but be aware of the extra noise on the lower time frame.

---

## Relative Strength

When related markets are monitored together, a few usually lead and a few usually lag. Significant moves require significant money, so relative outperformance usually reflects informed, committed participants.

- Leaders can be identified to either direction. In uptrends, leaders are the strongest; in downtrends, leaders are the weakest.
- The core rule: **long the strongest in an uptrend; short the weakest in a downtrend.**
- The opposite play, buying laggards because they look cheap, is human nature but is usually wrong. It is more productive to be in the markets with the strongest institutional support, and against those being shed.
- Even relative strength leaders are subject to mean reversion; an unmanaged campaign of buying the strongest will often buy overextended names at the apex. Rebalancing and rotation are required; blind buying is not a path to success.

### Tracking Relative Strength

- The simplest measure is rank by percent change from a fixed point, but this is blind to anything between the two points and can equate very different paths.
- A better anchor is a **significant, visible swing pivot on a broad reference index** for the group, with rate-of-change calculations restarted from each new pivot. This standardizes the starting point across names.
- Forcing a single anchor across **disparate asset classes** rarely makes sense; relative strength is more reliable within a related group.
- Averaging several different rates of change with different weights produces a measure with long look-back and recent responsiveness. Each added component adds complexity; verify that it earns its place. Simple, parsimonious tools usually outperform.

### Trading Relative Strength

A workable skeleton for trading relative strength ideas:

- **Decide the direction.** Establish the overall trend of the group and whether you trade from the long side, the short side, or both; if both, decide whether the book is hedged or simply long-and-short as opportunities appear.
- **Identify candidates.** Rank the strongest and weakest.
- **Enter on weakness into strength.** Buy leaders on pullbacks that do not develop extreme countertrend momentum (no significant new momentum low on the MACD); short laggards into pops.
- **Monitor and adjust.** Watch whether leaders resume leadership as they emerge from the pullback. If the weakness continues long enough, they are no longer leaders and the position should be exited or rotated.
- Execution triggers should align with general pullback rules; the relative strength screen narrows the candidate set, and standard technical patterns do the entry work.
- Recognize that **leadership rotates**. A leader is usually a group, not a single name, and the top of the list can shuffle without changing the underlying thesis. Pattern integrity and trend quality matter alongside the rank.
- Match the execution instrument to the horizon. Sector or asset-class rotation may suit portfolio allocators; individual stocks or contracts suit shorter-term traders. Some comparisons (e.g., equities to real estate) make little sense for short-horizon relative strength.
- The combination of a relative strength screen and well-understood technical patterns on the screened candidates puts the focus on markets that, by definition, are experiencing a real imbalance of buying or selling pressure.

The aim of all of these tools is to focus attention on markets in which a real buying or selling imbalance exists; in those moments, the patterns left in price are tradable, and the tools discussed here exist to confirm and refine that read rather than to replace it.
