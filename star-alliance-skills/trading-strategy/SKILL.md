---
name: trading-strategy
description: "The Merchant's craft for read-only trading-strategy design that ships a written, dated strategy spec and never places a trade or writes broker code. Take a market view (often from market-recon) and forge it into an executable-on-paper plan: scope the instrument, horizon, and regime; define a falsifiable edge with mechanical entry, exit, stop, time-stop, and invalidation rules; size the position by risk-per-trade and stop distance; frame a backtest with costs, in/out-of-sample split, and metrics (hit rate, payoff, expectancy, drawdown); then hand off a graded spec with a clear invalidation trigger. Four modes: trend-following, mean-reversion, event/catalyst-driven, systematic rules-based screen. Differentiate from market-recon (the read), portfolio-risk (the book), and storm-investigation (general research). Triggers: 'build a trading strategy', 'design an entry/exit plan', 'backtest this idea', 'how should I size this trade', 'turn this view into a strategy'. Never executes a trade or transfer."
metadata:
  version: 0.1.0
---

# Trading Strategy — the Merchant's craft

A craft of rules over hunches. A market view is a rumor until it is hammered into entry, exit, sizing, and risk — a written, dated plan that can be tested, falsified, and handed across the table without losing its shape. A blade untested is just metal; a strategy untested is just hope. The Merchant's job here is to take the read from market-recon and forge it into a spec a sober trader could paper-trade tomorrow, with no orders placed and no broker touched.

## What it is / is not

- IS: a written, dated strategy spec covering instrument/universe, horizon, regime fit, signal/thesis, entry trigger, exit rules (target, stop, time-stop, invalidation), position sizing, risk-per-trade, and a backtest framing with metrics and caveats.
- Is NOT market-recon: market-recon is the read of the field — sentiment, structure, flow. Trading-strategy is the plan built on that read, not the read itself.
- Is NOT portfolio-risk: portfolio-risk thinks at the book level (correlations, drawdown caps, capital allocation across strategies). This skill thinks at the per-strategy level; sizing outputs here feed the portfolio's risk budget, they do not set it.
- Is NOT execution: never places trades, never transfers funds, never writes code that calls a broker, exchange, or wallet. The output is a spec on parchment, not an order on a book.

## The craft

1. Scope the strategy and restate the read-only boundary. Name the instrument or universe, the horizon (intraday, swing, position), and the regime the strategy is built for (trending, ranging, low-vol, event-laden). Restate plainly: no orders, no transfers, no broker code. If a member's request edges toward execution, hand them a spec, not a yes.
2. Define the edge and the rules. State the signal or thesis in one sentence. Then make every rule mechanical and falsifiable: precise entry trigger, target exit, stop-loss, time-stop, and an explicit invalidation condition ("if X happens, this strategy is dead"). Vague rules breed quiet drift; mechanical rules survive the heat of the day.
3. Size the position. Convert risk-per-trade (a suggested percentage of notional book) and stop distance into position size. State max concurrent risk, a correlation cap against other open strategies, and how the size scales or shrinks in drawdown. For tail-risk or shock-prone regimes, defer to storm-investigation's framing before sizing in. Suggest, never mandate — sizing here is a draft for the requesting member and the portfolio-risk skill to ratify.
4. Frame the backtest. Pick a sample window that includes a regime resembling today, split in-sample and out-of-sample, and account for costs, slippage, and borrow where relevant. Track hit rate, payoff ratio, expectancy, max drawdown, and a Sharpe-ish ratio. Flag the usual traps: overfitting, curve-fitting, survivorship bias, look-ahead.
5. Write and hand off the dated strategy spec. Compile thesis, the rules table, sizing draft, backtest result and its caveats, a clear "what would invalidate this strategy" line, and a confidence grade of Low, Med, or High. Date and version the spec. Hand it to the requesting member. Never act on it.

## Modes

- **Trend-following.** Ride directional moves; cut on break, trail on confirmation.
- **Mean-reversion.** Fade the stretch; target the band, stop the rout.
- **Event/catalyst-driven.** Trade the print, the filing, the release; define the window.
- **Systematic / rules-based screen.** Rank, filter, and trigger on a rule set without discretion.

## Sharpening the craft

The apprentice curves a beautiful backtest and calls it proof. The journeyman checks out-of-sample and counts the costs. The master writes the invalidation condition first, before the entry, before the backtest — because a strategy without a defined death is not a strategy, it is a hope with a stop-loss.

- Keep out-of-sample discipline sacred. If it was not tested blind, it is not tested.
- Judge by expectancy, not win-rate. Many small losses fund a few large wins; that is fine if the math is honest.
- Paper-trade before conviction. A spec that survives paper is stronger than a spec that survived only a spreadsheet.
- Calibrate confidence. Low when the edge is thin or the sample small; High only after out-of-sample, costs, and regime match.
- Cross-check legality with the Lex Council where the rules touch securities law, insider windows, or restricted lists — a clean spec still has to be a lawful one.

## Gotchas

- Overfitting and curve-fitting: a backtest that fits the past perfectly usually fits the future poorly.
- Ignoring transaction costs, slippage, and borrow — they eat edges that look fat on paper.
- Survivorship-biased samples: universes that quietly dropped their losers lie about the payoff ratio.
- Look-ahead bias: any rule that uses tomorrow's close by sleight of hand is a fairy tale.
- The execution reflex: when a member asks "so place it?", answer with the spec and its grade, never a yes.
- Confidence inflation under conviction — a strong thesis is not a strong edge; rate the evidence, not the feeling.
- Undated or un-versioned specs rot. Date them, version them, or they will be cited against you.

## Versioning

Own skill. Bump metadata.version on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate VERSIONS.md with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog

- **0.1.0** — Initial release. A read-only strategy-design craft that turns a market view into a dated, falsifiable, backtest-framed spec without ever touching a broker.
