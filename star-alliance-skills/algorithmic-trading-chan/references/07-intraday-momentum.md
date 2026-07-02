---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Chapter 7 — Intraday Momentum Strategies

Intraday momentum strategies exploit the same behavioral and structural causes that drive longer-horizon momentum (slow news diffusion, underreaction, large-fund forced trading, stop-order cascades), but at horizons of minutes to a single session. This avoids the two main problems of interday momentum — low Sharpe from infrequent independent signals and post-crisis underperformance. The chapter catalogs concrete strategies spanning the opening-gap, news-driven, leveraged-ETF-rebalancing, and high-frequency (order-book, stop-hunting, order-flow) buckets.

## Why Intraday Momentum?

**Idea:** Move momentum from monthly holding periods down to intraday horizons, where independent signals are abundant and Sharpe is high.
**Rationale:** Monthly momentum gives few independent trades (poor backtest significance) and degrades after crises. Of the four causes of momentum Chans enumerates, three persist intraday — slow news diffusion, underreaction, and forced trading/sell-stops; only the persistence of roll return is too small to matter intraday. An additional cause — stop-order triggering — is most powerful at the open, where clustered overnight stop orders execute simultaneously and cascade.
**Pitfalls:** Long-term drift durations have been compressing as the strategies become known, so a backtest that found multi-day persistence in 1990s data may not survive at the same horizon today.

## Opening Gap Strategy (Futures & Currencies)

**Idea:** A momentum counterpart to Chan's earlier mean-reverting gap strategy — go long when the instrument opens above the prior high, short when it opens below the prior low.
**Rationale:** The overnight session is a multi-hour pause during which stop orders accumulate at price levels far from the prior close. At the open, these orders execute in a burst and one side's triggered stops cascade into further triggers, producing a directional move that often persists into the close.
**Method:**
1. Compute the 90-day rolling standard deviation of one-bar returns as a volatility benchmark.
2. Form a long signal if today's open exceeds yesterday's high by more than `entryZscore × std` (Chan uses `entryZscore = 0.1`); form a short signal on the symmetric downside condition.
3. Hold from open to close on the same day; no overnight exposure.
**Formula / rule:** Long when `op_t > hi_{t-1} · (1 + 0.1 · σ_{90})`; short when `op_t < lo_{t-1} · (1 − 0.1 · σ_{90})`.
**Findings:**
- FSTX (EuroSTOXX 50 futures on Eurex): **APR 13%, Sharpe 1.4, July 16, 2004 – May 17, 2012**.
- GBPUSD with close = 5 p.m. ET and open = 5 a.m. ET (London open): **APR 7.2%, Sharpe 1.3, July 23, 2007 – Feb 20, 2012**.
**Takeaway:** The Friday 5 p.m.–Sunday 5 p.m. gap in FX is a natural "overnight pause" that recreates the same stop-clustering mechanism that drives futures-gap momentum.

## Post-Earnings Announcement Drift (PEAD) — Intraday Version

**Idea:** Buy stocks at the open if their earnings announcement (released after yesterday's close, before today's open) caused a sufficiently large gap-up; short on a sufficiently large gap-down; exit at the close. The trader never reads the news — the open-to-prior-close return is the entire signal.
**Rationale:** PEAD has been documented since Bernard and Thomas (1989). The slow-diffusion cause of momentum operates most strongly on the day of a fresh earnings release, so the largest and cleanest intraday drift signal sits at the open. Intraday (open-to-close) harvesting is the natural horizon once the drift is short.
**Method:**
1. Build a daily boolean array flagging each stock whose earnings was announced after yesterday's 4 p.m. ET and before today's 9:30 a.m. ET.
2. Compute the 90-day rolling std of the previous-close-to-today's-open return as the "surprise threshold."
3. Long if `retC2O ≥ +0.5 · σ` and there is an earnings flag; short if `retC2O ≤ −0.5 · σ` and the flag is set.
4. Position P&L is the open-to-close return, summed across names and divided by 30 (Chan's realized cap on simultaneous positions in his S&P 500 backtest) to produce a portfolio return series.
**Formula / rule:** Entry trigger: `|retC2O| ≥ 0.5 · σ_{90, retC2O}`; direction = sign of `retC2O`; hold from open to close.
**Findings:** S&P 500 universe, **Jan 3, 2011 – April 24, 2012: APR 6.7%, Sharpe 1.5**. Because it is intraday, the strategy can be levered at least 4×, giving roughly **27% annualized**.
**Pitfalls:**
- Look-ahead bias in using 30 as the maximum-position divisor — the cap should be pre-set rather than read from the realized max.
- Overnight (close-to-open) returns following the trade are **negative on average**, so extending the hold to the next day destroys performance.
- PEAD's persistence has shortened over decades; the 1-day drift of older studies has become an intraday drift, and may compress further.
**Takeaway:** Don't try to be smart about the news content; let the gap size and the timing flag do the work, and never hold the position overnight.

## Drift from Other Corporate & Macro Events

**Idea:** The same open-to-close "surprise-then-drift" template that works on earnings also works on other scheduled announcements.
**Rationale:** Any announcement that prompts investors to reevaluate fair value should push the price partway to a new equilibrium; underreaction produces an intraday drift. The trader does not need event-specific fundamental knowledge — the same technical template applies.
**Method (template, identical structure to PEAD):**
1. Maintain a daily flag for each event type (earnings guidance, analyst rating/recommendation change, same-store sales, airline load factor, M&A, index addition/deletion, macro release).
2. Compute the 90-day std of the previous-close-to-today-open return.
3. Enter at the open in the direction of the gap when the gap exceeds a threshold and the event flag is set; exit at the close.
**Findings:**
- A purely technical model applied to M&A announcements extracts **about 3% APR**.
- Contrary to popular belief (Hafez, 2011), the acquiree's stock falls *more* than the acquirer's on the initial announcement.
- Index inclusion/deletion still generates momentum, but in modern data the drift is compressed to **intraday** (Shankar and Miller, 2006).
- On EURUSD, FOMC and CPI releases show **no significant momentum** in Chan's tests.
- On GBPUSD, U.K. macro releases and BOE rate decisions produced **at least 10 minutes** of momentum (Clare and Courtenay, 2001), but that result uses pre-1999 data and the window is likely shorter today.
**Pitfalls:** Macroeconomic-news drift windows are short and may have decayed below tradable thresholds; do not assume pre-2000 findings transfer unchanged.
**Takeaway:** The PEAD template is a general "overnight-news drift" strategy — the same code structure generalizes to any machine-readable event feed (e.g., Dow Jones/Newsware's tagged newswire).

## Leveraged-ETF Rebalancing Strategy

**Idea:** Buy a 3× leveraged (or short-leveraged) ETF in the late afternoon when the prior close-to-3:45 p.m. return has been strongly positive (or strongly negative), and exit at the close, harvesting the forced rebalancing flow of the ETF sponsor.
**Rationale:** A leveraged ETF sponsor must restore the leverage ratio to 3× at the end of every day. If the underlying dropped, the sponsor sells the underlying across the close to shrink notional; if it rose, the sponsor buys. This forced one-way flow *creates* momentum in the underlying at the close, which the trader captures by entering the leveraged ETF shortly before that flow arrives. Both leveraged-long and leveraged-short (inverse) ETFs in the same underlying push the underlying in the *same* direction, because both must rebalance to restore the same sign of exposure. The leveraged ETF is the trading vehicle because its 3× exposure magnifies the induced move.
**Method:**
1. Compute today's return from yesterday's close to 15 minutes before today's close.
2. If the return > +2%, buy the leveraged-long ETF (e.g., DRN, the 3× RMZ); if the return < −2%, sell (or buy the inverse leveraged ETF).
3. Exit at the market close.
**Formula / rule:** Position = sign of `ret_{t-1 close → 3:45 p.m.}` whenever `|ret| > 2%`; entry at 3:45 p.m., exit at close.
**Findings:** Trading DRN (3× MSCI US REIT ETF) over **October 12, 2011 – October 25, 2012: APR 15%, Sharpe 1.8**. End-January 2009, total AUM of all leveraged ETFs (long + short) was **$19 billion** (Cheng and Madhavan, 2009); a 1% SPX move forces rebalancing trades equal to **~17% of market-on-close volume**, indicating large market impact.
**Pitfalls:** A counter-flow of investor redemptions from the leveraged ETF could in principle neutralize the sponsor's rebalancing buys, but Chan's backtest finds this did not happen often. The strategy's capacity scales with total leveraged-ETF AUM, not with the trader's own capital.
**Takeaway:** Forced end-of-day rebalancing is a structural, schedule-driven source of momentum that is most powerful in the last 15 minutes of trading; the leveraged ETF is a 3×-levered claim on a flow the trader can predict in advance.

## Order-Book Imbalance Strategies

**Idea:** Imbalances between displayed bid and ask size, or across the full depth of book, predict the next-tick direction; trade in the predicted direction.
**Rationale:** A large bid relative to the ask signals an excess of resting buy interest, so subsequent marketable buy orders are more likely than sell orders, nudging the price up. The information content of displayed size is supported by academic findings: a near-linear relationship between bid/ask size imbalance and short-horizon price changes on Nasdaq (Maslov and Mills, 2001), with the same effect holding for full-book imbalance on the Stockholm exchange (Hellström and Simonsen, 2006), and stronger for low-volume names.

## Ratio Trade (Pro-Rata Markets)

**Idea:** In markets that fill orders pro-rata (e.g., CME Eurodollar futures), join a large existing bid rather than lifting the ask, so that you are allocated a share of the incoming buy flow.
**Rationale:** The original large bid represents buying pressure; by joining it, the trader is paid to wait for the price to move up. If the bid ticks up, the trader sells into the next order; if it does not, the trader can still sell back into the original bid (now at a known liquidity pool) and lose only commissions. Expected fill proportion equals own-order-size / aggregate-size-at-bid.
**Method:**
1. Watch the order book; trigger when bid size is "much larger" than ask size.
2. Submit a buy limit at the current best bid; wait for partial fill.
3. If the bid ticks up, sell at the new bid (or at the ask if spread > round-trip commission); if it does not, sell back at the original bid.
**Pitfalls:** The "much larger" threshold must be calibrated to the venue's order-flow distribution; the trade is only profitable if the bid-size signal's edge exceeds pro-rata fill uncertainty.

## Ticking / Quote Matching

**Idea:** In markets where the bid-ask spread is greater than two ticks, place a buy at the best bid + 1 tick; if filled, immediately try to sell at the best ask − 1 tick; if not, fall back to selling at the original bid.
**Rationale:** The +1-tick buy prices you ahead of all other passive bidders but is still "inside the spread" enough that the tick has positive expected return. The −1-tick sell similarly positions you ahead of passive sellers. The trade works only if **round-trip commission per share < spread − 2 ticks**.
**Method:**
1. Confirm bid-ask spread > 2 ticks.
2. Submit buy limit at best_bid + 1 tick.
3. On fill, submit sell limit at best_ask − 1 tick.
4. If sell not filled, sell at original best_bid (loss bounded to commissions + 1 tick).
**Pitfalls:**
- The original best bidder may cancel the moment she sees she has been front-run, leaving you with a worse exit price.
- The original bidder may have *intentionally* placed the large bid to induce exactly this behavior, then sells to you at +1 tick and immediately cancels — the "ticking trap."

## Momentum Ignition / Flipping (Time-Priority Markets)

**Idea:** Synthesize the appearance of buying pressure yourself, sell into the price response, and then buy the inventory back cheaper.
**Rationale:** A large displayed bid creates the same informational effect as an organic bid-ask imbalance, so other market participants will lift the ask in anticipation of an uptick. In time-priority markets, the flipper captures the spread once and then rides the price back, pocketing a tick at each end. Detection of flippers requires feed-level information about cancellation vs. fill rates (e.g., Nasdaq ITCH, EDGX Book Feed, BATS PITCH).
**Method:**
1. With roughly balanced bid/ask sizes, simultaneously post a large buy limit at the best bid and a small sell limit at the best ask.
2. When the small sell fills (others lifting the ask on the illusion of buying pressure), immediately cancel the large buy.
3. Buy back at the now-rebalanced best bid from the participants who overpaid.
**Pitfalls:**
- A counter-party may call the bluff and actually fill the large buy, leaving the flipper with a loss.
- Counter-strategy: if you suspect a large displayed bid is from a flipper, sell to it to drive the bid down, then cover the short after panicked participants capitulate and dump at the ask.

## Stop Hunting

**Idea:** When price nears a known support or resistance level — including round-number levels or those published by banks/brokerages — push the next tick through the level to trigger the cluster of stop orders on the other side, then trade in the resulting momentum.
**Rationale:** A nonuniform distribution of stop orders accumulates at published and psychologically round support/resistance levels. When price breaches a support level, sell stops trigger and cascade; the same asymmetry holds in reverse for resistance. This is documented in FX (Osler, 2000, 2001). Because the stops sit at the level, the trader can pre-position and use a small push to capture a disproportionately large move.
**Method:**
1. Identify candidate support/resistance levels (published daily levels or round numbers in the vicinity of current price).
2. As price approaches the level, submit a market order in the breakout direction to trigger the cluster of stops on the far side.
3. Once stops fire and momentum carries price through the level, cover/close for profit.
**Pitfalls:** Other high-frequency participants may run the same strategy; the level may not hold enough stops to pay for the entry; published levels from a single source may be stale or self-fulfilling in ways that have already been exploited.

## Order-Flow Imbalance

**Idea:** Compute a signed transaction volume ("order flow") and use its recent cumulative or average value to predict short-term price direction.
**Rationale:** Market makers infer information from the sign and urgency of incoming orders. When informed traders (e.g., a hedge fund reacting to breaking news) submit large same-sign market orders, market makers widen quotes and skew prices against the informed side, embedding the information in price. Order flow is therefore a direct read on private information not yet in the public price (Lyons, 2001).
**Method:**
1. Classify each transaction as positive (at the ask / market buy) or negative (at the bid / market sell); magnitude is the trade size.
2. Aggregate order flow over a short look-back (cumulative or rolling average).
3. Take a position in the direction of the recent net order flow.
**Findings:** Empirical research shows order flow is a strong short-horizon predictor of price direction.
**Pitfalls / practical notes:**
- In equities/futures, transaction prices are reported, so order flow can be reconstructed from tick data.
- In OTC FX, dealers typically do **not** report transactions, so FX traders must either trade FX futures (where flow is observable) or subscribe to a flow data provider.
**Takeaway:** If you can see the order book and the prints, you have an information stream that is strictly richer than best-bid/best-ask/last — most of the edge in modern HFT comes from mining that stream.

## Meta-Lessons on High-Frequency Momentum

**Idea:** The HFT strategies above interact — and collectively constrain each other.
**Findings & Pitfalls:**
- High-frequency traders can only profit from *slower* traders; if only HFTs remain, net average profit collapses to zero.
- The prevalence of front-running strategies has caused market makers to display much smaller quoted sizes. NBBO sizes in AAPL are often just a few hundred shares; even SPY on ARCA often shows under 10,000.
- Market makers only requote at the same prices after the small displayed orders are filled; large inventories are also a reason they avoid displaying size, independent of the HFT risk.
- Institutional block orders have largely been replaced by many small "child" orders scattered across venues and time, partly to defeat the HFT strategies described above.
- All HFT momentum strategies carry symmetric short-side variants.
