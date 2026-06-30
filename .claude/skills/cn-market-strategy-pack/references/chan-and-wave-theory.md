---
type: Document
title: Chan & Elliott Wave Frameworks
description: CN-market structural frameworks (chan_theory, wave_theory) — thesis, selection, entry, exit, regime — for level/structure-based buy/sell points.
timestamp: 2026-06-28T00:00:00Z
---

# Chan & Elliott Wave Frameworks

Two structural frameworks that read the market as nested levels and waves rather than
single signals. Both are subjective-count disciplines — they identify *where in a
structure* price sits and grade a buy/sell point from it, and both call for
confirmation from other indicators. **Read-only**: they grade structure, never trade.

---

## chan_theory — Chan / Zen Channel Theory (缠论)

- **Thesis:** Price builds a nested hierarchy — fractal → pen → segment → hub (中枢) →
  trend. Reading the hub structure and divergence locates the strongest, level-aware
  buy/sell points. Divergence is the highest-priority signal.
- **Selection logic:**
  - **Structure (hub identification):** From ~60 days of daily data, read the
    high/low sequence. A *hub* is the overlap zone of three consecutive sub-moves where
    price oscillates; a *trend* is three same-level hubs all moving the same direction.
    Decide whether price is in an oscillating hub (≥1 hub) or a trend segment (broken
    out of the hub).
  - **Divergence (top priority):** *Top divergence* — price makes a new high but the
    MACD red-bar area shrinks → sell/reduce. *Bottom divergence* — price makes a new
    low but the MACD green-bar area shrinks → buy/add. Compare MACD against the
    price highs/lows.
  - **Buy/sell point grade:** *First buy* (strongest) — bottom divergence in the last
    hub of a downtrend. *Second buy* — first pullback after leaving the down-hub that
    does not break the hub high. *Third buy* — break above after hub oscillation,
    without re-entering the hub. Sell points (first/second/third sell) are the mirror.
- **Entry:** Driven by the buy-point grade and *level* — daily-level buy points carry
  moderate weight; weekly-level buy points carry larger weight; multi-level resonance
  (daily + weekly same direction) is the strongest. Position size scales with the
  level and grade.
- **Exit:** Stop at the prior low (on a buy) or prior high (on a sell). A top
  divergence or a turn to a down-trend is the sell trigger.
- **Output:** State current state (uptrend / downtrend / hub oscillation), whether a
  divergence exists and at what level, and the current buy/sell-point type (or "no
  clear buy/sell point").
- **Regime fit:** volatile.

## wave_theory — Elliott Wave Theory (波浪理论)

- **Thesis:** Markets run a recurring 5-wave impulse + 3-wave corrective cycle.
  Locating the current wave gives both a directional read and a Fibonacci-based price
  target. The count is subjective, so it must be cross-checked.
- **Selection logic:**
  - **Identify the wave** from ~120 days of data plus trend data. *Impulse (1-3-5):*
    wave 1 is the first reversal leg on mild volume expansion; wave 3 is the strongest,
    usually high-volume, MACD-strong, and never the shortest wave; wave 5 typically has
    weaker volume and ends after a top divergence appears. *Corrective (A-B-C):* wave A
    is the first drop on heavier volume (often mistaken for a dip); wave B is a weak,
    shrinking-volume bounce (high trap risk); wave C is the second, often deeper drop
    that completes the correction.
  - **Golden positions:** wave 2 usually retraces 38.2–61.8% of wave 1; wave 3 commonly
    extends to 1.618–2.618× of wave 1; wave 4 must not enter wave 1's price territory
    (a rule violation forces a recount); wave C's target equals or exceeds wave A's
    length from the wave-A top.
- **Entry (best buy points):** wave-2 pullback stabilising (the "golden pit," safest,
  stop below the wave-1 start); wave-4 pullback stabilising (secondary, stop below the
  wave-1 top); early wave-3 breakout on a volume break above the wave-1 high. Avoid
  chasing the end of wave 5 (top-divergence risk).
- **Exit / risk:** Do not size up on a wave-B bounce (trap nature). If a wave rule is
  violated (e.g. wave 4 invades wave 1), recount. Tag the count's confidence
  (high/medium/low) and validate with other technical indicators.
- **Output:** Current likely wave position (e.g. "mid wave 3" or "suspected wave-4
  correction"), key Fibonacci support/resistance (0.382 / 0.618 / 1.618), a buy / wait
  / avoid call, and the count confidence.
- **Regime fit:** volatile.
