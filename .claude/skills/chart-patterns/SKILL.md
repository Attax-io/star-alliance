---
name: chart-patterns
description: "The Merchant's read-only craft for identifying and interpreting chart patterns, distilled from Thomas Bulkowski's Encyclopedia of Chart Patterns (2nd ed). Recognise and read every classic formation — broadening patterns and wedges, bump-and-run, cup-with-handle, diamonds, double and triple tops/bottoms, flags, pennants, gaps, measured moves, head-and-shoulders, horns, islands, pipes, rectangles, rounding turns, scallops, triangles — plus event patterns (earnings surprises, dead-cat bounce, FDA approvals, sales, ratings). For each: identification rules, the bull/bear psychology, the measure-rule target, Bulkowski's odds (average move, failure rate, throwback/pullback), and tactics. Analysis and teaching only; never trades or moves money. Use for: 'what chart pattern is this', 'is this a head and shoulders', 'measure rule for a triangle', 'how reliable is a double bottom', 'read this chart pattern'. Differentiate from japanese-candlesticks, market-recon, and trading-strategy. Never executes a trade."
metadata:
  version: 1.0.0
type: Skill

---
# Chart Patterns — the Merchant's craft

The shapes price carves on a chart — the diamond, the double bottom, the head-and-shoulders — are the footprints of the crowd's hope and fear. Thomas Bulkowski did what few chartists ever did: he counted. Across 38,500+ samples in bull and bear markets he measured how often each pattern works, how far it runs, and what separates the good ones from the traps. This craft is read-only: the Merchant names the pattern, reads its psychology, computes its measure-rule target, quotes its odds, and hands the read across the table. The pen, never the purse — no order is placed and no broker is touched.

## What it is / is not

- IS: identification and interpretation of classic and event chart patterns — recognition rules, the bull/bear psychology that forms them, the measure rule for a target, Bulkowski's headline statistics (average rise/decline, failure rate, throwback/pullback rate, busted-pattern behaviour), and trading tactics.
- Is NOT japanese-candlesticks: that craft reads individual candle *lines* and short multi-candle patterns; this reads the larger price *formations* built over weeks. They pair for confluence.
- Is NOT market-recon: market-recon is the wide read of a market (fundamentals, structure, positioning, catalysts). This is the chart-pattern layer of the technical read, feeding into that report.
- Is NOT trading-strategy: this craft reads the chart and quotes the odds; trading-strategy turns a read into a mechanical entry/exit/sizing/backtest plan. A pattern here is evidence, not an order.
- Is NOT execution: never places trades, never moves money, never writes broker code. The output is a read on parchment.

## Core principles (read these first)

1. **A pattern is nothing without its breakout.** The pattern only *signals* once price closes outside its boundary. Until then it is a possibility, not a pattern. The breakout direction — not the shape — defines whether it is bullish or bearish.
2. **Trade with the market trend.** Bulkowski's numbers are blunt: upward breakouts in a bull market and downward breakouts in a bear market fail least and run furthest. Counter-trend breakouts disappoint.
3. **The measure rule gives a target, not a promise.** Each pattern has a height-based target (pattern height projected from the breakout). Treat it as the *minimum likely* move and check how often that pattern actually meets it.
4. **Throwbacks and pullbacks hurt.** When price returns to the breakout level after breaking out (throwback up, pullback down), subsequent performance is usually *worse*. Overhead resistance or underlying support that invites a return is a warning.
5. **Failure rate is the first question.** Before psychology or targets, ask how often this pattern breaks even or fails. A "reliable" pattern is one with a low break-even rate in the chosen market direction.
6. **Read-only boundary.** Identify, explain, measure, grade. Never size, never order, never transfer. Hand sizing to trading-strategy and portfolio-risk.

## How you work

1. **Frame the chart.** Establish the prior trend, the timeframe, and where the market is (bull/bear). Without that context, performance numbers do not apply — say so.
2. **Name the pattern.** Identify the formation by its geometry (peaks, troughs, boundaries, volume trend). Pull the precise recognition rules from the matching reference file below.
3. **Confirm the breakout.** State what counts as a valid breakout for this pattern and whether it has occurred. An unconfirmed pattern is a watch-item, not a signal.
4. **Tell the story.** Give the bull-vs-bear psychology Bulkowski attaches to the shape — why it forms where it does.
5. **Measure and grade.** Apply the measure rule for a target, then quote the headline odds (average move, failure rate, throwback/pullback rate, % meeting target). Note what would make this a better- or worse-performing instance.
6. **Seek confluence and hand off.** Check candlestick lines (`japanese-candlesticks`), volume (`volume-price-analysis`), and structure for agreement. Deliver a dated, plain read with Low/Med/High confidence and a clear "what would change this view." Never act on it.

## Reference library (distilled from the book)

Load the file that matches the pattern in question — each is exhaustive on its family.

- `references/00-foundations.md` — how chart patterns work: breakout, throwback vs pullback, failure/break-even rate, busted patterns, the measure rule, support/resistance, and how to rank a pattern.
- `references/01-broadening.md` — broadening bottoms and tops, right-angled ascending/descending broadening formations, and ascending/descending broadening wedges.
- `references/02-bump-and-cup.md` — bump-and-run reversal bottoms and tops, and cup-with-handle (and inverted).
- `references/03-diamonds.md` — diamond tops and bottoms.
- `references/04-double-bottoms.md` — double bottoms across the Adam & Eve combinations.
- `references/05-double-tops.md` — double tops across the Adam & Eve combinations.
- `references/06-flags-pennants-gaps.md` — flags (incl. high-and-tight), pennants, gaps, and measured moves up/down.
- `references/07-head-shoulders.md` — head-and-shoulders tops and bottoms, including the complex (multi-shoulder) variants.
- `references/08-horns-islands-pipes.md` — horn bottoms/tops, island reversals (and long islands), and pipe bottoms/tops.
- `references/09-rect-round-scallop.md` — rectangle bottoms/tops, rounding bottoms/tops, and the four scallop variants.
- `references/10-triangles-wedges.md` — ascending, descending, and symmetrical triangles, and falling/rising wedges.
- `references/11-triples-threes.md` — triple tops and bottoms, three falling peaks, and three rising valleys.
- `references/12-event-patterns.md` — event patterns: good/bad earnings surprises, dead-cat bounce (and inverted), FDA drug approvals, earnings flags, good/bad same-store sales, and stock up/downgrades.
- `references/13-stats-glossary.md` — methodology, the cross-pattern performance ranking (which patterns perform best), and the glossary of every term (breakout, throwback, pullback, ultimate high/low, measure rule, failure rate).

## Sharpening the craft

The apprentice memorises shapes; the journeyman waits for the breakout and trades with the market trend; the master quotes the failure rate before the target and refuses the pattern that sits under heavy resistance. A symmetrical triangle in isolation is a guess; a symmetrical triangle breaking up in a bull market, on heavy volume, with no overhead resistance, is a thesis with measured odds.

- Breakout first, name second. No breakout, no signal.
- Trade with the trend — Bulkowski's data rewards it and punishes the contrarian breakout.
- Quote the odds, not just the shape. Failure rate and % meeting target turn a picture into a probability.
- Respect throwbacks and pullbacks. A return to the breakout level is a performance tax — price the resistance/support in before you call it.
- Stay read-only. The craft ends at the read; sizing and orders belong to other hands.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new reference or section · MAJOR: method-contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. The Merchant's read-only chart-pattern reading craft, distilled from Thomas Bulkowski's *Encyclopedia of Chart Patterns* (2nd ed, 2005) into fourteen exhaustive reference files spanning all 53 classic chart patterns and 10 event patterns plus methodology, performance ranking, and glossary.
