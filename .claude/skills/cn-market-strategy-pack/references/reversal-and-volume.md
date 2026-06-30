---
type: Document
title: Reversal, Range & Volume Strategies
description: CN-market reversal/range/sentiment strategies (bottom_volume, box_oscillation, one_yang_three_yin, emotion_cycle) — thesis, selection, entry, exit, regime.
timestamp: 2026-06-28T00:00:00Z
---

# Reversal, Range & Volume Strategies

Strategies for turning points, range-bound markets, and crowd-sentiment extremes —
where the edge is fading exhaustion or working a defined box rather than riding a
clean trend. Higher-variance than trend strategies; demand tighter risk control. All
**read-only** — they grade setups, never trade.

---

## bottom_volume — Bottom Volume Surge (底部放量)

- **Thesis:** After an extended decline, a sudden volume spike on a stabilising price
  marks capitulation and the entry of fresh buyers — a potential reversal. Reversal
  trades are higher-risk than trend-following, so size small.
- **Selection logic:** Confirm a sustained decline (drop > 15% from the 20-day high
  to the recent low; trend status BEAR or STRONG_BEAR). Require a volume anomaly —
  current volume > 3× the 5-day average (volume ratio > 3.0) — appearing *after* a
  phase of extreme low volume. Confirm price stabilisation: a bullish candle
  (close > open) holding the recent low, ideally with a long lower wick showing buyer
  support. Confirm any fundamental catalyst and that average chip cost has converged
  toward current price.
- **Entry:** Small position only (≤ 2–3 tenths). This is a reversal bet, not a
  confirmed trend.
- **Exit:** Strict stop below the recent low — non-negotiable given reversal risk.
- **Regime fit:** trending_down (catching the turn).

## box_oscillation — Box Range Trading (箱体震荡)

- **Thesis:** In a sideways market, price oscillates between box support and box
  resistance; "buy hugging support, sell near resistance" harvests the range. The
  edge is the box's repeated, validated boundaries.
- **Selection logic:** Identify the box over ~60–120 days — the top (resistance) is a
  cluster of 2–3+ tested highs, the bottom (support) a cluster of 2–3+ tested lows; a
  valid box needs each boundary touched at least 2–3 times. Locate current price:
  box-bottom zone (within ~5% of support) is a buy; box-middle third is wait;
  box-top zone (within ~5% of resistance) is a reduce/take-profit. Read volume —
  volume drying up + stabilising at the bottom confirms support; stalling on shrinking
  volume at the top confirms resistance. Box width = (top − bottom) / bottom: < 5% is
  too tight to trade, 5–15% is a standard tradeable box, > 15% allows larger swings.
- **Entry:** Box-bottom zone; stop ~3% below box support. A volume-confirmed break
  (> 2× average) flips the strategy: an upside break converts to a trend strategy with
  a new target of one box-height extension; a downside break means exit and wait
  (old support becomes resistance).
- **Exit:** Reduce/take profit at the box-top zone; exit on a valid downside break of
  support. Distinguish a fake break (intraday touch that closes back inside) from a
  true break (two consecutive closes beyond the boundary on expanding volume).
- **Regime fit:** sideways.

## one_yang_three_yin — One Yang Wraps Three Yin (一阳夹三阴)

- **Thesis:** A K-line consolidation pattern — one big bullish candle, three small
  contracting candles, then another bullish breakout candle — signals the
  consolidation has ended and the prior up-move resumes. A trend-continuation entry.
- **Selection logic:** Over the last 5 sessions: (1) a large bullish candle, body
  > 2% of price; (2) three consecutive bearish/small candles, each holding above day-1's
  open, with shrinking volume (volume ratio < 0.8), closing inside day-1's body;
  (3) a fifth bullish candle closing above day-1's close. Confirm bullish MA alignment
  (MA5 > MA10 > MA20) for the strongest read.
- **Entry:** Near the day-5 close.
- **Exit:** Stop below day-1's open (the pattern's invalidation level).
- **Regime fit:** continuation within an uptrend; the pattern is weaker (and the
  signal smaller) when the broader trend is unclear.

## emotion_cycle — Sentiment Cycle (情绪周期)

- **Thesis:** Crowd emotion cycles through panic → pessimism → doubt → hope →
  optimism → excitement → greed → euphoria. Smart money accumulates at the panic
  bottom and exits at the euphoric top — so trade *against* the crowd extreme. The
  core contrarian framework of the pack.
- **Selection logic:** Turnover rate is the heat gauge — < 0.5%/day is cold/ignored
  (potential bottom), 0.5–2% normal, 2–5% active (do not chase), > 5% hot (watch for a
  top), > 10% extreme overheating (likely a short-term top). Read the 20-day turnover
  trajectory: cooling + shrinking volume = retreating sentiment, be patient; warming +
  surging volume = sentiment igniting, can engage; a sudden single-day volume blow-off
  (5× prior) often means the main force is distributing. Read news tone (good-news-
  realised / earnings-beat / limit-ups → possibly overheated; bad news / broken support
  → pessimism may be forming a bottom; extreme negative retail sentiment is a
  contrarian bottom tell). Watch MA compression + low ATR as a coiled-spring,
  low-emotion setup.
  - **Bottom (buy zone)** — meet 3+ of: 20-day turnover near a 1-year low; volume
    persistently > 50% below the 60-day average; recent news low-key/neutral/negative;
    price at or below MA20 but no panic crash; institutional holdings stable or rising.
  - **Top (reduce zone)** — meet 3+ of: 5-day turnover > 2× the 20-day average;
    pulse-like single-day volume expansion; news dominated by good-news-realised /
    raised targets / retail chasing; price deviation from MA5 > 8%; MACD top divergence.
- **Entry:** Accumulate into the bottom characteristics (be greedy when others panic).
- **Exit:** Reduce into the top characteristics (be cautious when others are greedy).
- **Regime fit:** sector_hot (where sentiment swings are largest); broadly a
  cross-regime sentiment overlay.
