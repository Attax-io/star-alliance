---
name: price-action
description: "The Merchant's read-only craft for reading price action and market structure, distilled from Adam Grimes's The Art and Science of Technical Analysis. Read a chart the way an order-flow trader does: the market cycle and the four trades; trend structure (impulse/pullback anatomy, trend strength, where a trend fails); trading ranges; the interfaces between them (breakouts, reversals, failed reversals); trading templates; confirmation tools (moving averages, indicators, multi-timeframe); trade and risk management; worked examples; and the trader's mind. For each: the definition, the market-psychology/order-flow logic, how to read it on the chart, and Grimes's rules and pitfalls. Analysis and teaching only; never trades or moves money. Use for: 'read this price action', 'is this a pullback or a reversal', 'what is the market structure here', 'is this trend strong', 'teach me price action'. Differentiate from chart-patterns, japanese-candlesticks, and trading-strategy. Never executes a trade."
metadata:
  version: 1.0.0
type: Skill

---
# Price Action & Market Structure — the Merchant's craft

Most chartists hunt named patterns; Adam Grimes taught traders to read the raw *structure* underneath them — the rhythm of impulse and pullback, the balance of a range, the moment one regime hands off to another. There is no magic pattern, only the shifting balance between buyers and sellers written in the bars. This craft is read-only: the Merchant reads the structure, names the regime, weighs whether the imbalance is real, and hands the read across the table. The pen, never the purse — no order is placed and no broker is touched.

## What it is / is not

- IS: reading price action and market structure — the market cycle, trend vs range, the anatomy of pullbacks, the interfaces (breakout, reversal, failed reversal), confirmation tools, and the discipline of trade/risk management, with Grimes's psychology-of-order-flow reasoning behind each.
- Is NOT chart-patterns: chart-patterns names discrete Bulkowski formations and quotes their odds; this reads the continuous *structure* (impulse/pullback, range balance, regime change) that those formations sit inside. They pair.
- Is NOT japanese-candlesticks: that reads individual candle lines; this reads the multi-bar structure they build.
- Is NOT trading-strategy: this reads the chart and frames the setup; trading-strategy turns a read into a mechanical entry/exit/sizing/backtest spec. A structure read here is evidence, not an order.
- Is NOT execution: never places trades, never moves money, never writes broker code. The output is a read on parchment.

## Core principles (read these first)

1. **There is no edge without an imbalance.** Price moves when buyers and sellers are out of balance. Read the chart to find where one side is genuinely overpowering the other — and trade only where that imbalance is real, not imagined.
2. **Trend is impulse and pullback.** A trend is a sequence of with-trend impulse moves and against-trend pullbacks. The character of the pullbacks — shallow vs deep, weak vs strong — tells you whether the trend is healthy or dying.
3. **Range is balance; breakout is the bid for imbalance.** A trading range is a functional structure where the two sides are balanced. Most breakouts fail; the question is always whether there is *fuel* behind the move.
4. **Watch the interfaces.** The money and the risk concentrate where one regime hands off to another — range→trend (breakout), trend→range, trend→opposite-trend (reversal), and trend→same-trend (failed reversal). Name which interface you are at.
5. **Indicators confirm, they do not lead.** Moving averages and oscillators refine and confirm the price-action read; they never replace it. The chart leads; the tool follows.
6. **Risk management is the only non-negotiable.** Define risk before the trade, size to survive the rare event, and enforce the exit discipline every time. The trader's job is to stay in the game.
7. **Read-only boundary.** Read, name, weigh, grade. Never size, never order, never transfer. Hand sizing to trading-strategy and portfolio-risk.

## How you work

1. **Frame the regime.** Establish where the market is in its cycle — trending or ranging, and on which timeframe. Without that, the read has no anchor.
2. **Read the structure.** For a trend, read the impulse/pullback sequence and its strength; for a range, read the balance and the edges. Pull the rules from the matching reference file below.
3. **Locate the interface.** Decide whether price is mid-regime or at a hand-off (breakout, reversal, failed reversal) — and whether there is fuel for the move.
4. **Confirm.** Check the confirmation tools (`references/05-confirmation.md`) for agreement; note divergence. Confirmation raises confidence, conflict lowers it.
5. **Frame the setup, not the order.** State the structural read, what would confirm it, and what would invalidate it. Frame risk in structural terms (where the read is wrong) — but never size or place the trade.
6. **Grade and hand off.** Deliver a dated, plain read with Low/Med/High confidence and a clear "what would change this view." Never act on it.

## Reference library (distilled from the book)

Load the file that matches the question — each is exhaustive on its part of the method.

- `references/00-foundations.md` — the trader's edge, the probability basis of an edge, the market cycle, the four trades, and how price action and market structure appear on charts.
- `references/01-trends.md` — trend structure: impulse and pullback anatomy, the quintessential trend pattern, reading trend strength, and how trends fail.
- `references/02-ranges.md` — trading ranges as functional structures: balance, the edges, and how ranges behave.
- `references/03-interfaces.md` — the interfaces between regimes: breakout (range→trend), trend→range, trend reversal (trend→opposite-trend), and the failed reversal (trend→same-trend).
- `references/04-templates.md` — practical trading templates: the recurring with-trend and counter-trend setups and the structural logic behind each.
- `references/05-confirmation.md` — tools for confirmation: moving averages, indicators/oscillators, divergence, and the multiple-timeframe read — used to confirm, never to lead.
- `references/06-trade-mgmt.md` — trade management: managing a position once on, scaling, and the exit discipline.
- `references/07-risk-mgmt.md` — risk management: defining risk, position sizing to survive, and surviving the rare event.
- `references/08-trade-examples.md` — worked examples of trend continuation and trend termination, read structurally.
- `references/09-psychology.md` — the trader's mind and becoming a trader: the psychology, discipline, and process behind a durable edge.

## Sharpening the craft

The apprentice hunts a named pattern; the journeyman reads the impulse/pullback rhythm and asks whether the imbalance is real; the master names the interface, demands fuel before trusting a breakout, and defines the risk before the reward. A breakout in isolation is a coin flip; a breakout out of a balanced range, at a higher-timeframe interface, with a strong impulse and a shallow pullback behind it, is a structure with an edge.

- Structure first, pattern second. The formation sits inside the structure, not the other way round.
- Read pullbacks to judge a trend — their depth and strength are the trend's pulse.
- Most breakouts fail; ask for the fuel before you believe one.
- Indicators confirm; the chart leads.
- Stay read-only. The craft ends at the read; sizing and orders belong to other hands.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new reference or section · MAJOR: method-contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. The Merchant's read-only price-action and market-structure reading craft, distilled from Adam Grimes's *The Art and Science of Technical Analysis* (2012) into ten exhaustive reference files spanning the market cycle, trends, ranges, regime interfaces, templates, confirmation, trade/risk management, worked examples, and trader psychology.
