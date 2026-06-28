---
type: Document
title: Trend & Momentum Strategies
description: CN-market trend/momentum strategies (bull_trend, ma_golden_cross, volume_breakout, shrink_pullback, dragon_head) — thesis, selection, entry, exit, regime.
timestamp: 2026-06-28T00:00:00Z
---

# Trend & Momentum Strategies

Strategies that ride an established up-move: confirm a bullish structure, prefer
buying a controlled pullback over chasing strength, and demand volume to validate
price. All are **read-only**: they grade a setup, they do not place orders.

These strategies lean on the system's **core trading rules**:
1. Strict entry — only consider entry when deviation (乖离率) from the reference MA is < 5%.
2. Trend trade — MA5 > MA10 > MA20 bullish alignment.
3. Efficiency first — volume must confirm the trend is real.
4. Buy-point preference — favour a pullback to MA support over a breakout chase.
5. Risk screen — a single materially bad news item is a veto.
6. Volume-price agreement — volume validates the price move.
7. Strong-trend relaxation — sector leaders may relax the deviation limit.

---

## bull_trend — Default Bull Trend (默认多头趋势)

- **Thesis:** The default lens for routine single-stock analysis. In an established
  uptrend, the highest-odds, lowest-risk action is to buy a controlled pullback that
  holds support, not to chase an extended price. The bias is "trend up + risk
  controlled + do not chase."
- **Selection logic:** Confirm bullish MA alignment (MA5 ≥ MA10 ≥ MA20 with MA20
  sloping up). If price has broken meaningfully below MA20, downgrade the bullish
  weight. Check rhythm: when price is stretched far from MA5/MA10, flag "wait for a
  pullback" rather than buy. Validate any breakout or bounce day with expanding
  volume; a rally on shrinking volume is suspect, and stalling on heavy volume warns
  of disagreement.
- **Entry:** Buy a pullback that holds a key MA rather than chasing highs; or a
  volume-confirmed break of valid resistance. If there is no clear edge, the correct
  output is "stand aside" — avoid over-trading.
- **Exit:** Reference stop below MA20 or the structural swing low; reduce when price
  breaks MA20 or the trend weakens.
- **Regime fit:** trending_up. This is the default router strategy.

## ma_golden_cross — MA Golden Cross (均线金叉)

- **Thesis:** A faster MA crossing above a slower MA, confirmed by volume, marks a
  trend reversal or continuation. The classic momentum trigger.
- **Selection logic:** Primary signal — MA5 crosses above MA10 within the last ~3
  sessions. Stronger (slower but more reliable) signal — MA10 crosses above MA20.
  Check whether MACD is also in a golden cross, ideally above the zero axis. The
  background matters: a cross emerging from consolidation is the strongest; a cross
  within an existing uptrend is continuation; a cross deep inside a decline is weak
  and needs more confirmation.
- **Entry:** Near the level of the crossing MAs, with deviation < 5% so you are not
  chasing. The cross day should trade above its 5-day average volume (volume ratio
  > 1.2 is a positive tell).
- **Exit:** Stop below the crossing-MA cluster / structural low; the signal is
  weakened if price falls back through the crossed averages.
- **Regime fit:** trending_up.

## volume_breakout — Volume Breakout (放量突破)

- **Thesis:** A close above a known resistance level on heavy volume signals real
  demand overwhelming supply. Volume is the proof that the breakout is not a fake.
- **Selection logic:** Identify resistance (often the 20-day high or the top of a
  prior trading platform). Require breakout-day volume > 2× the 5-day average
  (volume ratio > 2.0), cross-checked against history. The close must sit above the
  resistance level and in the upper ~30% of the day's range (a strong close).
  Screen for risk — no major bad news, valuation not bubble-stretched.
- **Entry:** Near the breakout level; a next-day open back above the level helps
  distinguish a true breakout from a false one. Keep deviation < 5%.
- **Exit:** Stop ~3% below the breakout level (failed breakout = exit). Sector
  confirmation (the whole sector strengthening) raises conviction.
- **Regime fit:** trending_up.

## shrink_pullback — Shrink-Volume Pullback (缩量回踩)

- **Thesis:** In a healthy uptrend, a pullback to MA support on *shrinking* volume
  is profit-taking exhausting itself, not distribution — the ideal continuation
  entry. Falling volume into support is the key tell.
- **Selection logic:** Precondition — stock must already be in an uptrend
  (MA5 > MA10 > MA20). Detect a pullback to near MA5 (within ~1%) or MA10 (within
  ~2%) where pullback volume is < 70% of the 5-day average (shrink-volume signature).
  Confirm chips are healthy (profitable share ~50–80%) and there is no bad news.
- **Entry:** At MA5 (preferred) or MA10 (secondary), with MA5 deviation < 2% — the
  best buy zone is right at support holding.
- **Exit:** Stop at the MA20 level (loss of the deeper trend support).
- **Regime fit:** trending_down or sideways *within* a larger uptrend (the dip).
  Also a default-router strategy.

## dragon_head — Dragon Head / Sector Leader (龙头策略)

- **Thesis:** When a sector rotates into favour, the leader (龙头) that moves first and
  hardest carries the rotation; identifying it captures the strongest relative
  strength. Tied to rule 7 (strong-trend leaders may relax entry discipline).
- **Selection logic:** Confirm the stock's sector is among the top recent gainers via
  sector rankings, and that the stock led the sector's launch (first to rise / limit
  up). Check momentum — leaders typically show turnover > 5% and volume ratio > 1.5.
  Check relative strength — a true leader beats its sector average by 2%+ on up days.
  Confirm a sector-level catalyst (policy, event, earnings) in the news.
- **Entry:** Leaders may relax the deviation limit to ~7%, but above ~10% still
  warrants caution.
- **Exit:** When sector leadership rotates away or the stock stops outperforming its
  sector; manage against the sector's own rollover.
- **Regime fit:** sector_hot.
