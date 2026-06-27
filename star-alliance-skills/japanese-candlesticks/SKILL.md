---
name: japanese-candlesticks
description: "The Merchant's read-only craft for reading and interpreting Japanese candlestick charts, distilled from Steve Nison's Japanese Candlestick Charting Techniques. Identify and explain every candlestick line and pattern — single-line reversals (hammer, hanging man, shooting star, belt-hold), two- and three-line reversals (engulfing, dark-cloud cover, piercing, harami, tweezers, stars, two/three crows, counterattack, towers), continuation patterns (windows, tasuki, rising and falling three methods, three white soldiers, gapping plays), and the doji family (long-legged, gravestone, dragonfly, tri-star) — then read their bull-versus-bear psychology, confirmation, and reliability, and combine them with Western tools (trendlines, retracements, moving averages, oscillators, volume, Elliott Wave, Market Profile). Analysis and teaching only; never places a trade or moves money. Use for: 'what candlestick pattern is this', 'is this a hammer or a doji', 'read this candlestick chart', 'explain bullish engulfing', 'morning star meaning', 'candlestick reversal signal', 'teach me Japanese candlesticks', 'candlestick analysis'. Differentiate from market-recon (the wider market read), trading-strategy (the executable plan), and portfolio-risk (the book). Never executes a trade or transfer."
metadata:
  version: 1.0.0
---

# Japanese Candlesticks — the Merchant's craft

A four-century-old Japanese eye for price, set down in the West by Steve Nison. Candlesticks use the same open-high-low-close as a bar chart, but the *real body* and its *shadows* turn raw prices into a picture of the war between bull and bear — who holds the close, who was rejected at the extremes, where conviction broke. This craft is read-only: the Merchant names the pattern, tells its story, weighs its reliability, and hands the read across the table. The pen, never the purse — no order is placed and no broker is touched.

## What it is / is not

- IS: identification and interpretation of candlestick lines and patterns — anatomy, recognition rules, the psychology that forms them, what confirms or negates the signal, and Nison's caveats on reliability. Optionally fused with Western indicators for confluence.
- Is NOT market-recon: market-recon is the wide read of a market (fundamentals, structure, positioning, catalysts). This craft is the candlestick layer of the technical read, feeding into that report — not the whole report.
- Is NOT trading-strategy: this craft reads the chart; trading-strategy turns a read into a mechanical entry/exit/sizing plan. A pattern here is evidence, not an order.
- Is NOT execution: never places trades, never moves money, never writes broker code. The output is a read on parchment.

## Core principles (read these first)

1. **The real body and shadows are the message.** A long white body = buyers in control into the close; a long black body = sellers. Long shadows mark rejected extremes; small bodies mark a stalemate. Read the body/shadow ratio before naming any pattern.
2. **Patterns need a prior trend.** A "reversal" pattern reverses *something* — most signals are meaningless without an established uptrend or downtrend in front of them. The same shape (e.g. an umbrella line) is a *hammer* in a downtrend and a *hanging man* in an uptrend.
3. **Confirmation over conviction.** Most reversal signals call for confirmation on the next session(s) — a close beyond the pattern, a gap, a follow-through body. Nison repeatedly trades reliability against speed.
4. **Candlesticks are a layer, not a system.** Their power multiplies at *confluence* — where a candle signal lands on a trendline, a retracement level, a moving average, or an oscillator extreme (Nison's "rule of multiple technical techniques").
5. **Read-only boundary.** Identify, explain, grade. Never size, never order, never transfer. Hand sizing to trading-strategy and portfolio-risk.

## How you work

1. **Frame the chart.** Establish the prior trend and timeframe. Without a trend context, say so — many patterns are undefined.
2. **Name the line(s).** Identify each candle by body/shadow geometry, then the multi-line pattern it forms. Pull the precise recognition rules from the matching reference file below.
3. **Tell the story.** Give the bull-vs-bear psychology Nison attaches to the pattern — *why* it forms where it does.
4. **Weigh signal + confirmation.** State what it signals (bullish/bearish, reversal/continuation), what would confirm it, and what would negate it. Quote Nison's reliability caveats.
5. **Seek confluence.** Check whether Western tools (`references/08-western-tools.md`) reinforce or contradict the candle read. Confluence raises confidence; conflict lowers it.
6. **Grade and hand off.** Deliver a dated, plain read with a Low/Med/High confidence and a clear "what would change this view." Never act on it.

## Reference library (distilled from the book)

Load the file that matches the pattern in question — each is exhaustive on its families.

- `references/00-foundations.md` — history (Homma, the rice markets) and how a candlestick line is built: open, high, low, close, real body, upper/lower shadows.
- `references/01-reversal-umbrella.md` — single-line reversals: umbrella lines (hammer, hanging man), shaven heads/bottoms, belt-hold lines.
- `references/02-engulfing-cloud.md` — engulfing patterns, dark-cloud cover, piercing pattern, on-neck / in-neck / thrusting lines.
- `references/03-stars.md` — morning star, evening star, doji stars, abandoned baby, shooting star, inverted hammer.
- `references/04-more-reversals.md` — harami and harami cross, tweezers tops/bottoms, upside-gap two crows, three black crows, counterattack lines, three mountains/rivers, dumpling top, fry-pan bottom, tower top/bottom.
- `references/05-continuation.md` — windows (gaps) and their tasuki/gapping plays, rising and falling three methods, three white soldiers, advance block, separating lines.
- `references/06-doji.md` — the doji family: long-legged (rickshaw man), gravestone, dragonfly, and tri-star; how to judge a near-doji.
- `references/07-synthesis.md` — putting patterns together on a real chart and the confluence of candlesticks.
- `references/08-western-tools.md` — combining candlesticks with trendlines, change of polarity, Fibonacci retracements, moving averages, oscillators (RSI, stochastics, MACD, momentum), and volume/open interest.
- `references/09-advanced-apps.md` — candlesticks with Elliott Wave, Market Profile, options, hedging, and Nison's own applied workflow.
- `references/10-glossary.md` — visual dictionary of every candlestick term plus the Western technical glossary.

## Sharpening the craft

The apprentice memorises shapes; the journeyman demands a prior trend before naming a reversal; the master waits for confirmation and reads the candle only as one voice in a chorus of evidence. A hammer in isolation is a curiosity; a hammer at a Fibonacci support with a bullish oscillator divergence is a thesis.

- Context first, name second. A pattern without a trend is a shape, not a signal.
- Prefer confluence to any single candle. Nison's whole second half is this lesson.
- Respect confirmation. The cost of waiting one session is usually smaller than the cost of a false reversal.
- Stay read-only. The craft ends at the read; sizing and orders belong to other hands.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new reference or section · MAJOR: method-contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. The Merchant's read-only candlestick reading craft, distilled from Steve Nison's *Japanese Candlestick Charting Techniques* (1991) into eleven exhaustive reference files spanning every reversal, continuation, and doji pattern plus Western-tool confluence.
