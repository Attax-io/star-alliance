# Risk Management

## The Three Risk Questions
Risk management is the first job of the trader. Three questions must be answered on every trade:
- Where do we place initial exit orders, both for profits and losses?
- How do we adjust the trade as it develops through time?
- How many shares, contracts, or units do we trade on each position?

The job is essentially to manage the risk in trades, focus on exiting losers at the correct points, and let the upside take care of itself. A few outsized losses can offset the profits of many winners; the edge can be completely eroded by a small number of errors.

## Know Your Stop First (The Absolute Rule)
There is one rule that cannot be broken — perhaps the single most important rule in discretionary trading:
- Always know where you are getting out of the trade if you are wrong, **before** you get in.
- The exact stop placement depends on the pattern, trader, profit target, time frame, and market, but the level must be defined at the time of entry.
- The stop must sit at a meaningful level **outside** the market's noise. A rough guideline: the average range of a single bar on the time frame you are trading. Initial stops placed closer than one average bar's range are working within noise and have likely impaired any edge.

## Position Sizing: Kelly and Fixed Fractional

### The Kelly Criterion (and Its Limits)
The classic Kelly formula gives the optimal percentage of the account to risk per trade, assuming very specific conditions hold:
- f = (Odds × Probwin − Probloss) / Odds
- Odds = Sizewin / Sizeloss

Why Kelly usually fails in practice:
- Most optimized position-sizing approaches are extremely aggressive and accept large drawdowns as a matter of course.
- They assume each trade is independent of the others; in reality, regimes (trends, ranges) produce strings of correlated wins and losses.
- They require inputs like the largest historical loss and assume the future will resemble the past. A single larger-than-expected loss can be fatal under an aggressive Kelly regime.
- A possible compromise: set aside a small portion of capital to apply aggressive sizing rules and trade the rest conservatively.

### Fixed Fractional (The Recommended Approach)
A simple, robust, non-optimized framework. The objective is to **limit risk**, not to maximize returns. The design goals are:
- Define the risk from losing trades.
- Limit risk from a much larger-than-expected losing trade.
- Limit risk from a string of losing trades.
- Limit the total risk from a set of highly correlated positions.
- Limit the total amount of equity placed at risk at any one time.
- Allow easy scaling as the account balance changes.

The rules:
- Risk a consistent percentage of account equity on every trade.
- Under 1% is very conservative; 3% or more is extremely aggressive.
- Plan for the impact of a string of four or five losing trades in a row, or a single loss five times the anticipated maximum loss.
- Example: risking 3% with a 5× loss event = 15% of equity gone. Risking 10% in the same scenario = 50% down and in serious trouble.

## Drawdown and the Asymmetry of Recovery
Drawdown is the amount an equity curve has retreated from its peak. It is one of the truest measures of risk, but future drawdowns must always be extrapolated from history.

The math is asymmetric: a much larger percentage gain is required to recover from any given drawdown.
- Return needed for recovery = D% / (1 − D%)
- A 5% drawdown needs a 5.3% return to recover.
- A 20% drawdown needs a 25% return just to break even.
- A 50% drawdown needs a 100% return to recover (a doubling).

Compound loss from a string of t consecutive losses of N% each (one position at a time):
- Compound loss = (1 − N%)^t
- Example: five consecutive 4% losses is not 20% but ~18.5%, because the account was shrinking after each loss.
- Note: this formula is only valid for consecutive losses on a single-position account. Three simultaneous positions risking N% of the same balance produce a 3N% combined loss if all three are stopped out.

## Calculating Trade Size
Once the per-trade risk percentage is defined, size the position so that the dollar risk at the stop equals the desired dollar risk.
- Trade size = Desired dollar risk ÷ Per-unit risk
- The per-unit risk is the distance between the entry and the initial stop.
- Example: $100,000 account, 1% risk = $1,000 target. Long at $50.00, stop at $47.50 → $2.50 per-share risk → 400 shares.
- The stop location is dictated by the system/pattern; **size is the lever**, not the stop distance.

## Thinking in R Multiples
Express every P&L outcome as a multiple of the initial risk on that trade.
- A loss equal to the original risk is a –1R trade.
- A profit equal to half the initial risk is a +0.5R trade.
- A winner twice the initial risk is a +2R trade.

Why it matters:
- Removes much of the psychological pressure of thinking in actual dollars.
- Lets a trader compare apples to apples across different instruments, position sizes, and capital pools.
- Makes it possible to approach a $10,000 risk and a $100,000 risk with equanimity when both represent the same R on different account sizes.

## The Effect of Position Sizing (Path Dependence)
Sizing decisions are evaluated through Monte Carlo simulation, because intuition fails in path-dependent probability problems. The setup used in the chapter: a system with a positive expectancy of 0.1 per trade, +1.2R winners and –1.0R losers, 250 trades, 1,000 simulated accounts.

Key lessons from the simulations:
- Mean terminal value rises with risk, but standard deviation rises faster — risk-adjusted return worsens before the upside gain compensates.
- At some reckless risk level, additional size no longer adds return; it primarily adds drawdowns and bankruptcies.
- Even a verified positive-expectancy system can produce an account that loses nearly 90% of its value purely from random sequencing.
- One outlier in the $2,000-risk test reached only $12,400 at one point before recovering; one in the $25,000-risk test reached over $2,000,000 while nearly half the parallel accounts went bankrupt.
- The bankruptcy limit makes real trading asymmetric: martingale strategies (doubling after losses) work in theory but invariably blow up in practice.
- Bankruptcies emerge at $3,000–$5,000 risk in the fixed-dollar test, and rise steeply from there. At $25,000 per trade, nearly half of accounts are ruined.

The implication: behavior and decisions must be governed by the most probable outcomes over many trials, not by the one path that is actually realized.

## Fixed Fractional in Action
A fixed-fractional plan (e.g., 2% of equity on every trade) outperforms a comparable fixed-dollar plan on a few important dimensions even when naïve risk-adjusted metrics look worse.
- Mean and median terminal values rise because the bet scales up with a growing account.
- The standard deviation also rises, but the **distribution of terminal values is no longer symmetric** — the extra variability is concentrated in a long right (positive) tail.
- The returns are lognormal, not normal. This is why Sharpe ratios and coefficients of variation can mislead: simplistic measures of risk consistently misprice asymmetric risk profiles.
- The fixed-fractional plan's advantage is **expanded upside and dampened downside potential**, not literal protection from ruin. With commissions and frictions, an account can in theory be driven arbitrarily close to zero through a long string of losses — losing 99.9997% is not meaningfully different from 100%.

The Kelly fraction is the special case where wins and losses are constant in size and trades are independent. In that idealized test, the Kelly-sized accounts dramatically outperformed reasonable constant-risk accounts, with mean and median terminal values far higher — but 4.6% of accounts still closed with greater-than-75% drawdowns. As risk rises above Kelly, the median terminal value actually declines even as the mean rises, because the distribution becomes lottery-like.

## Random and Emotional Sizing
Traders often meddle with size based on a feeling about a trade. The Monte Carlo evidence is clear: random bet sizing, even when the average size matches a fixed-fractional baseline, **underperforms the disciplined plan** and adds symmetric variability (more risk without targeted upside).
- Most discretionary interventions in sizing are harming performance because they are the wrong decisions at the wrong time.
- If you are going to vary size, do two things: understand the impact of random sizing on the system, and keep careful records with objective analysis to confirm the variation is actually adding value.

## Other Sizing Approaches (Briefly)
- **Fixed-percentage allocation** (a position sized as a fixed % of portfolio value): for active, technically motivated positions this number is fairly meaningless — a 5% position in a volatile name can carry more risk than a 50% position in a quiet one.
- **Margin as a fixed % of account** (futures equivalent): in practice, a disaster waiting to happen. Margins are not a clean volatility measure.
- **Equivalent-volatility / equal-risk sizing** (Turtles-style, often using ATR): equalizes each position's daily P&L contribution across markets by trading more size in quieter markets and less in volatile ones. It does not actually equalize risk and can be dangerous when volatility is compressed and the market is overdue for a range expansion.

## The Theoretical Risk Equation
Risk is part of the expected value function:
- Risk = Probability of loss × Expected size of loss

The profound point: the magnitude of the risk depends on **both** the probability and the size. Both must be evaluated together; either dimension in isolation is misleading.

## The Probability/Consequence Grid
Map every risk on a 2×2 of probability (low/high) versus consequence (low/high):
- **Low probability, low consequence:** usually inconsequential — but verify the consequences really are as small as assumed, because these events are rare and easily misjudged.
- **Low probability, high consequence:** the **most dangerous quadrant**. Examples: naked short-option premium positions, tail events, asteroid strikes. Easy to mistake extreme improbability for impossibility. Many serious financial risks live here. Obsessing over them is unhelpful; ignoring them is fatal.
- **High probability, low consequence:** the **second most dangerous quadrant** because traders dismiss them as trivial. Slippage, commissions, and small recurring frictions can eat an account alive in the aggregate.
- **High probability, high consequence:** usually avoided by self-selection; "natural selection" removes traders who take these.

## Thinking in Sample Sizes
Probability thinking requires thinking in large sample sizes, but real traders face the concrete realization of a single outcome. Three traps follow:
- A common psychological error: treating the probability of a plane crash as irrelevant to the passengers actually on board. This collapses the analysis onto a single trial. The real risk is across millions of passengers and many flights.
- You can have a positive expectancy and still lose on a sequence of trades; that sequence is not evidence against the edge. The outcome of any one trade doesn't matter — the sum of results over many trades does.
- Tight stops feel like low risk but are often small, certain losses. A wider stop hit less often can carry lower total risk across many trades, even though it feels riskier on the single trade where it triggers.

## Uncertainty vs. Risk
A common academic definition: risk is uncertainty, with the standard deviation of returns used as a proxy. Three problems with this:
- There is no guarantee that future returns will carry variation similar to the historical record.
- An asset can carry risks that are invisible in its return series (naked short option premium writers, complex derivatives, illiquid structured products). A simple examination of returns cannot reveal these.
- Symmetric risk measures miss asymmetric risk profiles. A fund with 5% annual return, 10% standard deviation, and 5% downside / 15% upside asymmetry is not "riskier" than the 5%/10%/symmetric fund — most of the extra variability is opportunity. Fixed-fractional position sizing shows the same effect in terminal-value distributions.

## Expected Value: The Two Paths
Expected value can be restated as:
- E = Reward − Risk
- Win ratio = Probwin / Probloss
- Reward/risk ratio = Sizewin / Sizeloss

The two paths to positive expectancy:
- A high win ratio, or
- A high reward/risk ratio.
- There is no inherent advantage to high-probability trading, and no reason to believe high-reward/risk trades are inherently better. Any combination producing positive E makes money, before transaction costs.

## The "Risk" of Risk/Reward
Over a large set of trades, the "risk" half of the risk/reward equation is **not actually true risk** in the meaningful sense.
- The outcome of any one trade is effectively a coin flip, even for great traders. Three or four losses in a row is not risk; it is the cost of doing business.
- A retail business treats inventory purchases as a planned expense, not risk. Trading losses within a positive-expectancy framework are the same.
- The distinction is not semantic. The most important belief separating profitable discretionary traders from everyone else is full acceptance that a planned losing trade, in the aggregate, is not risk.

## Trading Without an Edge
The first and most devastating practical risk: the trader has no edge.
- "Futile" traders (Larry Harris) expect to profit but do not, on average, and may be unable to recognize the gap between expectations and results.
- "Inefficient" traders lack the skill, resources, or information to trade profitably, even if they perform all the right steps.
- Markets are a **negative-sum** game due to transaction costs. Without a real edge, no amount of process will save the trader.
- If you don't know what your edge is, you don't have one. Discipline of record keeping and structured performance analysis is non-negotiable; many retail traders bleed money in part because they have never measured their actual results.

## Execution Risk
The divergence between intended and actual execution prices (slippage, missed trades, errors). Net effect is negative.
- Newer traders often miss trades from nervousness about (often imagined) risk, or jump the gun and take signals the methodology does not actually call for.
- Some traders randomly alter sizes — taking a few trades at much larger size or scaling in with smaller size — eroding the theoretical edge.
- In liquid markets, paying the spread is usually negligible unless the strategy is high-frequency; for active strategies, even penny spreads in/out are a measurable drag.
- In thin markets (small-cap equities, illiquid futures, currencies), slippage of 10% or more is possible at the worst moments.
- Short-sale availability and other regulatory frictions can prevent an intended execution entirely.
- Mitigations: build good execution skills, invest in infrastructure and broker relationships, and explore new markets on tiny size (e.g., a $50 risk per trade for a trader normally risking $5,000) to surface execution problems before scaling.

## Tail / Event Risk
Extreme, low-probability, high-consequence moves — the most dangerous category for traders.
- Most large standard-deviation events are driven by geopolitics or natural disasters and are completely unpredictable.
- They are mostly unhedgeable: the annualized cost of fully hedging a complex portfolio with options can easily exceed 10%, setting a hurdle rate that very few strategies can beat net of hedge.
- Tail events are not always bad. Being on the right side of a surprise move is a windfall, but exit liquidity at the extreme may also vanish.
- The chapter's example: a boring blue-chip like P&G, on May 6, 2010 (the Flash Crash), erased nearly a decade of price gains in under 30 minutes and recovered most of it within minutes. The move was widely considered impossible, yet it happened — and even larger moves occurred in other names that day.

## Correlation Risk
Diversification effects are most likely to fail exactly when they are most needed.
- An active trader holding five or six positions may believe she is risking 1–3% per position, but if those positions are highly correlated, the true exposure is closer to a single much larger position.
- Correlations spike in financial stress: large pools of money, especially via ETFs and aggregated "risky asset" products, dump en masse in systemic events.
- The trend toward asset aggregation via ETFs is likely to intensify this effect, not reduce it. Always evaluate the possibility that every open position can move against the trader at the same time.

## Liquidity Risk
The danger is not only illiquid markets at quiet times — it is the inability to execute at intended prices precisely when the trader most needs to.
- Moderately sized orders can move markets more than expected, especially in time-sensitive exits at the stop.
- Even normally liquid markets can become thin at the worst moment; HFT market makers can quote tight spreads and then widen them the instant liquidity is taken, on timescales far faster than human reaction.
- Position size relative to average daily volume is the key gauge.

## Regulatory Risk
Often overlooked; can be career-ending in certain environments.
- A change in tax law can impair a hedge or offsetting position.
- Margin increases by exchanges after large moves can break the back of an established trend (the chapter cites multiple 2011 Silver futures margin hikes, and the Hunt brothers' silver episode).
- Short-sale restrictions — up to and including outright bans on certain names or groups — can prevent intended executions.
- Trade-bust rules during crashes (e.g., the Flash Crash) are capricious: a trader who bought the panic and sold the bounce can wake up to find the buy canceled and the sells standing, leaving a short from far below the current price. This destroys any incentive to provide liquidity in a crash.
- The current regulatory frontier — HFT, algorithmic trading, rebate-capture strategies — is likely to produce a rule change in the next several years that materially alters market microstructure.

## Markets Evolve — Do You?
Any trading plan is a specific expression of principles in one specific form. What worked yesterday may stop working tomorrow. This is not a possibility; it is reality.
- A discretionary or systematic program should be subject to a control process, similar to manufacturing/quality control: identify normal variation, then flag events that violate it.
- Markets are far noisier than a manufacturing line and large surprises are normal for many systems, so the control process is not trivial — but it is achievable.
- The danger is not realizing something has changed and continuing to feed capital into a strategy that has become a bottomless hole. A control process provides a defined cutoff at which trading is terminated.

## Disaster Risk
A spectrum from mundane to existential:
- Common: power outage, internet drop, hard drive failure. Backup systems and a plan several steps further than the obvious are essential.
- Severe: natural or man-made disaster in a major financial center; loss of account access for days or weeks.
- Systemic risks often cannot be managed. There is no value in obsessing over the uncontrollable, but there is great value in being as prepared as possible.

## The Central Reframe
Risk management is the first and most important job. The trader's job is to assume the correct kinds of risk at the correct times and manage those risks appropriately. Profits accrue to the trader who works within a net positive-expectancy framework, accepts the planned losses as the cost of doing business, and protects the account from the rare events that would otherwise end the career.
