---
name: cn-market-strategy-pack
description: "The Merchant's read-only pack of 15 named CN/HK/US/JP/KR-market stock strategies distilled from a daily A-share analysis system; analysis and education only, never trades or moves money. Four families — trend/momentum (bull trend, golden cross, volume breakout, shrink pullback, dragon-head), reversal/range/sentiment (bottom volume, box oscillation, one-yang-three-yin, emotion cycle), theme/event/fundamental (hot theme, event-driven, expectation repricing, growth quality), and structural frameworks (chan, wave) — each with thesis, selection, entry, exit, and the regime it fits, plus a decision-signal layer. Use for 'which strategy fits this stock', 'screen with chan theory', 'is this a dragon-head setup', 'apply a CN-market strategy'. Differs from trading-strategy (one bespoke spec), strategies-review (housekeeping), market-recon (general read), chart-patterns (Bulkowski). Never trades."
metadata:
  version: 1.1.0
type: Skill
---

# CN-Market Strategy Pack — the Merchant's craft

A working trader in the A-share / HK / US / JP / KR markets does not carry one
method; he carries a *book* of named战法 (battle-methods) and reaches for the one the
tape is asking for. This pack distils fifteen such strategies from a production daily
stock-analysis system into a single read-only reference: for each strategy, the
thesis it bets on, how it screens a candidate, where it enters and exits, and the
market regime it belongs to. The Merchant names the strategy, grades the setup against
it, and hands the read across the table. The pen, never the purse — no order is placed
and no broker is touched.

## What it is

- A **catalogue of 15 strategies** grouped into four families, each entry written to
  fixed fields: **Thesis / Selection logic / Entry / Exit / Regime fit**.
- A map from **market regime** (trending_up, trending_down, sideways, sector_hot,
  volatile) to the strategies that fit it — so you can answer "which strategy fits
  this stock / this tape."
- A high-level account of the **screening + decision-signal dashboard** layer that
  turns a strategy read into a structured, reviewable signal.
- Grounded entirely in the source system's strategy YAMLs and its seven core trading
  rules; Chinese terms translated to clear English with the原文 kept where it is the
  name of the thing (中枢, 龙头, 一阳夹三阴).

## What it is NOT

- **Not a trading system.** It never places, sizes-for-execution, or routes an order,
  and writes no broker code. It is analysis and education only.
- **Not a backtest or a bespoke spec.** It does not optimise parameters or ship a
  single dated strategy document — that is `trading-strategy`.
- **Not a general market read or a research report** — that is `market-recon`.
- **Not classic chart-pattern recognition** (diamonds, head-and-shoulders) — that is
  `chart-patterns`; nor candlestick reading — that is `japanese-candlesticks`.
- **Not workflow housekeeping** over a strategy queue — that is `strategies-review`.
- The numeric thresholds quoted (turnover %, volume multiples, deviation %, Fibonacci
  ratios) are the **source system's** defaults, reproduced for fidelity, not the
  Merchant's own calibrated edges and not investment advice.

## Generative principles

1. **Match the strategy to the regime, not the stock to your favourite strategy.**
   Each strategy declares the regime it fits (trend, range, reversal, theme, volatile
   structure). The first move is always to read the tape's regime, then pick the
   battle-method that belongs there. A box strategy in a runaway trend, or a breakout
   strategy in a dead range, is a category error before it is a bad trade.
2. **Volume is the witness; price is the claim.** Across the whole pack — breakout,
   golden cross, bottom-volume reversal, shrink-volume pullback, theme strength —
   volume is what confirms or refutes the price move. A price event without the
   matching volume signature is treated as unproven (core rules 3 and 6).
3. **Prefer the pullback to the chase; bound entry by deviation.** The book's bias is
   to buy support that holds rather than strength that is extended. Entry discipline is
   the deviation (乖离率) limit — under ~5% for most, relaxed only for confirmed sector
   leaders (rules 1, 4, 7).
4. **Separate substance from association, and price-in from priced-in.** For theme,
   event, and expectation strategies the recurring judgment is the same: is the stock a
   *substantive* beneficiary or merely concept-adjacent, and how much of the catalyst
   is *already* in the price? A real catalyst already realised is a reason to fade, not
   chase.
5. **Trade the crowd's extreme, structure the level.** Sentiment strategies fade panic
   and euphoria (emotion_cycle); structural frameworks (chan, wave) locate price within
   nested levels and grade the buy/sell point by level and divergence. Both treat the
   single signal as weaker than its context.
6. **Every read carries its own invalidation.** A strategy grade is incomplete without
   the exit/stop and the condition that would prove it wrong — a broken support, a
   failed breakout, a missed announcement, a faded theme. The decision-signal layer
   makes this explicit (watch_conditions, invalidation, horizon).
7. **Grade, never execute.** The output is a graded read and a decision *signal*, never
   an order. When in doubt the honest output is "stand aside / no clear buy point,"
   not a manufactured trade.

## The screening + decision-signal layer (high level)

The source system does not stop at a strategy read — it sinks each read into a
structured **DecisionSignal** that is queryable, reviewable, and back-testable after
the fact. Useful as a mental model for what a complete strategy output contains:

- **Action** — buy / add / hold / reduce / sell / watch / avoid / alert (not just
  "good/bad").
- **Plan** — entry_low/high, stop_loss, target_price, **invalidation**, and
  **watch_conditions** (what to monitor next).
- **Horizon** — intraday / 1d / 3d / 5d / 10d / swing / long, with sensible defaults by
  market phase.
- **Quality & evidence** — confidence, score, plan_quality (complete/partial/minimal),
  an evidence summary, and a data-quality note.
- **Lifecycle** — a signal is active / expired / invalidated / closed / archived; a new
  opposite signal invalidates the prior one, and signals are de-duplicated by source.
- **Post-hoc review** — signals are scored against later price action and can carry
  useful / not-useful feedback, so the book learns which strategy fired well in which
  regime.

This layer is **read-and-record only** — it logs advice, evidence, risk, and lifecycle;
it never places an order or rebalances a book.

## References

Read the family file that matches the strategy or regime in question:

- **`references/trend-and-momentum.md`** — bull_trend, ma_golden_cross, volume_breakout,
  shrink_pullback, dragon_head. Riding an established up-move; the seven core rules.
- **`references/reversal-and-volume.md`** — bottom_volume, box_oscillation,
  one_yang_three_yin, emotion_cycle. Turning points, range-bound boxes, and
  crowd-sentiment extremes.
- **`references/theme-and-event.md`** — hot_theme, event_driven, expectation_repricing,
  growth_quality. Catalyst-, narrative-, and fundamentals-driven reads.
- **`references/chan-and-wave-theory.md`** — chan_theory, wave_theory. Nested-level and
  wave-count structural frameworks; level-graded buy/sell points.
- **`references/scoring-and-router.md`** — the exact numeric layer: every strategy's
  `sentiment_score` adjustments verbatim from the source YAMLs, the seven core trading
  rules table, and the router/priority/regime metadata (default_router, default_priority,
  market_regimes, core_rules) that decides which strategy fires when. Read this when you
  need the precise score deltas or to reason about strategy selection/priority.

## Changelog

- **1.1.0** — Added `references/scoring-and-router.md`: per-strategy exact
  `sentiment_score` adjustments, the seven core trading rules table, and
  router/priority/regime metadata for all 15 strategies, reproduced verbatim from the
  source system's strategy YAMLs (still analysis/education only — no trades).
- **1.0.0** — Initial pack: 15 strategies across four family reference files with
  thesis / selection / entry / exit / regime, plus the decision-signal layer.
