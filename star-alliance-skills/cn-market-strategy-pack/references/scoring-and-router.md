---
type: Document
title: Scoring, Core Rules & Router Metadata
description: Exact per-strategy sentiment-score adjustments, the seven core trading rules, and router/priority/regime metadata for all 15 CN-market strategies — reproduced from the source system's YAMLs for fidelity. Analysis and education only; never trades.
timestamp: 2026-06-28T00:00:00Z
---

# Scoring, Core Rules & Router Metadata

This file holds the *exact numeric* layer the family files summarise in prose: the
per-strategy `sentiment_score` adjustments each strategy applies, the seven core
trading rules they reference by number, and the router/priority/regime metadata that
decides which strategy fires when. Every number here is **copied verbatim from the
source system's strategy YAMLs and README** — none is the Merchant's own calibration,
and none is investment advice. The scores adjust an analytical signal score; this skill
grades and records, it never places, sizes-for-execution, or routes an order.

`sentiment_score` is a relative sentiment adjustment applied on top of a base analytical
score, not a price target, position size, or order quantity.

---

## The seven core trading rules (核心交易理念)

The source README lists seven numbered ideas. Each strategy's `core_rules` field cites
the rules it leans on (see the metadata table below).

| # | Rule (原文) | English |
|---|-------------|---------|
| 1 | 严进策略：乖离率 < 5% 才考虑入场 | Strict entry (严进): only consider entry when deviation (乖离率) < 5%. |
| 2 | 趋势交易：MA5 > MA10 > MA20 多头排列 | Trend trading: require a bullish MA stack (MA5 > MA10 > MA20). |
| 3 | 效率优先：量能确认趋势有效性 | Efficiency first: volume must confirm the trend is valid. |
| 4 | 买点偏好：优先回踩均线支撑 | Buy-point preference: prefer a pullback to moving-average support. |
| 5 | 风险排查：利空新闻一票否决 | Risk screen: a single piece of bad news (利空) is a veto. |
| 6 | 量价配合：成交量验证价格运动 | Volume-price agreement: volume must validate the price move. |
| 7 | 强势趋势股放宽：龙头股可适当放宽标准 | Relax for strong trend stocks: sector leaders (龙头) may loosen the criteria. |

---

## Per-strategy scoring table

Each row reproduces the strategy's own `评分调整` (score adjustments) block. Positive
adjustments raise the bullish read; negative ones penalise / flag a reduce-or-exit.

### Trend & momentum

**bull_trend (默认多头趋势 — Default Bull Trend)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 多头排列 + 趋势强度良好 | Bullish MA stack + good trend strength | `+12` |
| 回踩关键均线后企稳 | Stabilises after pulling back to a key MA | `+8` |
| 放量突破关键阻力 | Volume breakout through key resistance | `+10` |
| 跌破 MA20 或趋势转弱 | Breaks below MA20 / trend weakens | `-12` |

**ma_golden_cross (均线金叉 — MA Golden Cross)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| MA5 × MA10 金叉配合量能 | MA5 crosses MA10 with volume | `+10` |
| MA10 × MA20 金叉 | MA10 crosses MA20 | `+8` |
| MACD 零轴上方金叉 | MACD golden cross above the zero axis | extra `+5` |

**volume_breakout (放量突破 — Volume Breakout)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 放量突破确认 | Confirmed volume breakout | `+12` |
| 突破伴随板块共振（板块也走强） | Breakout with sector resonance (sector also strong) | extra `+5` |

**shrink_pullback (缩量回踩 — Shrink Volume Pullback)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 缩量回踩 MA5 | Low-volume pullback to MA5 | `+10` |
| 缩量回踩 MA10 且量能 < 0.6 倍均量 | Low-volume pullback to MA10 with volume < 0.6× average | `+8` |

**dragon_head (龙头策略 — Dragon Head)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 确认为龙头股 | Confirmed sector leader (龙头) | `+10` |
| 板块正处于主动轮动期 | Sector is in active rotation | extra `+5` |

### Reversal, range & sentiment

**bottom_volume (底部放量 — Bottom Volume Surge)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 底部放量确认 | Confirmed bottom volume surge | `+8` |
| 配合阳线 + 新闻催化 | Plus a bullish candle + news catalyst | extra `+5` |

**box_oscillation (箱体震荡 — Box Range Trading)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 箱底企稳 + 缩量 | Box-bottom stabilises + volume shrinks | `+10` |
| 箱底放量攻顶 | Box-bottom volume surge attacking the top | `+12` |
| 箱体向上有效突破 | Valid upward breakout of the box (转趋势策略 — switch to trend strategy) | `+15` |
| 处于箱顶区域 | In the box-top zone (不追高 — do not chase) | `-5` |
| 箱底有效跌破 | Valid breakdown of the box bottom (离场 — exit) | `-15` |

**one_yang_three_yin (一阳夹三阴 — One Yang Three Yin)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 形态成立 + 趋势看多 | Pattern confirmed + bullish trend | `+15` |
| 形态成立但趋势不明 | Pattern confirmed but trend unclear | `+5` |

**emotion_cycle (情绪周期 — Sentiment Cycle)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 情绪底部特征满足3项以上 | Sentiment-bottom features met (≥3 of 5) | `+14` |
| 情绪底部特征满足全部5项 | All 5 sentiment-bottom features met | `+20` |
| 情绪顶部特征满足3项以上 | Sentiment-top features met (≥3 of 5) | `-12` |
| 情绪顶部特征满足全部5项 | All 5 sentiment-top features met | `-20` |
| 情绪平稳区间 | Calm sentiment zone | no adjustment to base score |

### Theme, event & fundamental

**hot_theme (热点题材 — Hot Theme)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 热点处于启动或扩散期，且个股实质受益 | Theme launching/spreading + stock is a substantive beneficiary | `+12` |
| 个股强于板块并有量能确认 | Stock stronger than its sector with volume confirmation | extra `+6` |
| 热点进入分化或退潮 | Theme enters divergence / ebb | `-8` |
| 仅概念蹭热点且乖离率过高 | Concept-only association with excessive deviation | `-12` |

**event_driven (事件驱动 — Event Driven)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 高可信正向事件且价格尚未充分反映 | High-credibility positive event not yet fully priced in | `+14` |
| 正向事件已大幅兑现 | Positive event already largely priced in | `-6` |
| 负面事件仍在发酵 | Negative event still developing | `-15` |
| 事件影响不清晰或信息冲突 | Event impact unclear / conflicting info | stay neutral, lower confidence |

**expectation_repricing (预期重估 — Expectation Repricing)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 正向预期差且价格尚未充分反映 | Positive expectation gap not yet fully priced in | `+15` |
| 正向预期差已被连续大涨兑现 | Positive expectation gap already realised by a sustained rally | `-5` |
| 负向预期差或核心假设被证伪 | Negative expectation gap / core thesis falsified | `-15` |
| 信息不充分但存在潜在修复 | Insufficient info but potential repair | stay neutral, lower confidence |

**growth_quality (成长质量 — Growth Quality)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 收入、利润、现金流和 ROE 同向改善 | Revenue, profit, cash flow and ROE improving together | `+15` |
| 行业景气与公司新闻互相验证 | Sector prosperity and company news corroborate | extra `+6` |
| 高估值但成长未验证 | High valuation but growth unverified | `-8` |
| 增收不增利或现金流恶化 | Revenue up but profit flat, or cash flow deteriorating | `-12` |

### Structural frameworks

**chan_theory (缠论 — Chan / Zen Channel Theory)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 底背驰 + 一买信号 | Bottom divergence (底背驰) + first-buy (一买) signal | `+15` |
| 二买/三买共振 | Second-buy / third-buy (二买/三买) resonance | `+10` |
| 中枢震荡无明确方向 | Hub (中枢) oscillation, no clear direction | hold at base score |
| 顶背驰 / 趋势向下 | Top divergence (顶背驰) / downtrend | `-15` |

**wave_theory (波浪理论 — Elliott Wave Theory)**

| Condition (原文) | English | Adjustment |
|------------------|---------|------------|
| 第2浪底部企稳（黄金坑） | Wave-2 bottom stabilises (golden pit, 黄金坑) | `+15` |
| 第3浪突破确认 | Wave-3 breakout confirmed | `+12` |
| 第5浪末端/顶背离 | End of wave 5 / top divergence | `-10` |
| C浪下跌中 | During a wave-C decline | `-12` |

---

## Router / priority / regime metadata

Reproduced from each YAML's metadata fields. `default_priority` orders display/selection
(smaller = earlier). `default_active` marks the default-active skill set; `default_router`
marks membership in the router fallback set. `market_regimes` are the tape states the
strategy prefers; `core_rules` cite the numbered rules above. Blank cells are absent in
the source YAML.

| Strategy | display_name | category | default_priority | default_active | default_router | market_regimes | core_rules |
|----------|--------------|----------|------------------|----------------|----------------|------------------|------------|
| bull_trend | 默认多头趋势 | trend | 10 | true | true | trending_up | 1, 2, 3 |
| ma_golden_cross | 均线金叉 | trend | 20 | — | — | trending_up | 1, 2, 3 |
| volume_breakout | 放量突破 | trend | 30 | — | — | trending_up | 1, 2, 3 |
| hot_theme | 热点题材 | framework | 35 | — | — | sector_hot | 2, 3, 5, 7 |
| shrink_pullback | 缩量回踩 | trend | 40 | — | true | trending_down, sideways | 1, 2, 4 |
| event_driven | 事件驱动 | framework | 45 | — | — | sector_hot, volatile | 3, 5 |
| box_oscillation | 箱体震荡 | framework | 50 | — | — | sideways | 1, 2, 3 |
| growth_quality | 成长质量 | framework | 55 | — | — | trending_up | 2, 3, 5 |
| bottom_volume | 底部放量 | reversal | 60 | — | — | trending_down | 2, 5 |
| expectation_repricing | 预期重估 | framework | 65 | — | — | volatile, sector_hot | 3, 5, 6 |
| chan_theory | 缠论 | framework | 70 | — | — | volatile | 1, 2, 3, 4 |
| wave_theory | 波浪理论 | framework | 80 | — | — | volatile | 1, 2, 3, 4 |
| dragon_head | 龙头策略 | trend | 90 | — | — | sector_hot | 2, 7 |
| emotion_cycle | 情绪周期 | framework | 100 | — | — | sector_hot | 1, 2, 3, 5 |
| one_yang_three_yin | 一阳夹三阴 | pattern | 110 | — | — | (none) | 2, 4 |

Notes from the source:
- `bull_trend` and `shrink_pullback` are the only two strategies in the **router fallback
  set** (`default_router: true`); `bull_trend` is also the only **default-active** strategy.
- `one_yang_three_yin` declares no `market_regimes` (it is a pure K-line pattern check).
- Lower `default_priority` surfaces earlier; `bull_trend` (10) is the default first read.
