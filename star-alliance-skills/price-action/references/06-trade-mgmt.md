# Trade Management

## The Edge–Sizing Paradox

Every trade management decision must respect the nature of the signal that produced the entry. Patterns have predictive value only over a specific time horizon and magnitude; outside that window the market degenerates into random noise, and exits, stops, and profit targets must be calibrated to that window rather than to a trader's general preferences.

- A pattern good for a few bars cannot be stretched into a long-term trend follower; large profit targets will not be reached.
- A longer-horizon signal will be chopped up by tight stops sitting inside the post-signal random noise.
- The "sweet spot" of any system is small. Changing stops, targets, or position management can unintentionally destroy an edge.
- Any rule set must be matched to a trader's psychology, but personality cannot override the statistical reality of the signal.
- Work out stop, target, and management rules in advance, then be absolutely, perfectly consistent.

## Placing the Initial Stop

The initial stop sets the ultimate risk point on the trade, removes much of the emotion from the process, and is usually the basis for position sizing.

- Closer stops allow larger positions and larger profits on winners, but lower the win probability.
- Farther stops raise win probability but force smaller position size and larger dollar losses per failure.
- Every trade, without exception, has a precise initial risk point defined at the time of entry. You always know where you are getting out if you are wrong, and that level is respected.

### Fixed-Percentage Stops
- Old-school approach: a flat 10–20% adverse move.
- Defining a fixed loss is better than having no stop at all, but applying the same percentage across markets is not optimal.
- Markets trade at very different volatility levels (a 9% average daily range vs. a 3% range); a 10% stop is inside the noise of the first and far outside the noise of the second.

### Volatility-Based Stops
- Use a multiple of a market's average daily range or a one standard deviation move.
- Volatile markets automatically get wider stops and smaller size; quiet markets get tighter stops and larger size.
- These often make ideal initial stops for discretionary and algorithmic systems alike.

### Market Structure Stops
- Determined by pivot points in the live price action, not by fixed numbers.
- When entering with short-term momentum, the stop sits beyond the nearest pivot low (or, with a trade-off in position size, the penultimate pivot).
- Initial stops are usually wide. It would be very unusual to set an initial stop closer than roughly two ATRs, and they can exceed four ATRs.
- Buying against a sloppy support area with many shadows below: the only sensible stop is beyond the most extreme low. If the market takes out that level on a fakeout, re-enter with a new stop beyond the new extreme.
- Impending volatility events (reports, etc.) can be handled by leaving size normal but pushing the initial stop farther away, used only in rare cases.

## Setting Price Targets

Two families of profit-taking exist: with-trend exits (limit orders, often at preset levels) and countertrend exits (rules activated after the trade gives back from its maximum profit). The choice between fixed targets and open-ended "let winners run" trades is a personal one, but the decisions are not neutral: they interact with the statistical profile of the entry.

### Fixed Profits at Risk Multiples
- If initial risk is known, multiples of that risk become natural profit targets.
- Grimes's personal approach: exit 25–33% of the position on a limit order at 1× the initial risk; the order is entered as soon as the entry fills and is left working GTC.
- Get orders into the book as soon as possible. Modern electronic books have heavy cancel-and-replace activity; a real resting limit order percolates to the top of queue and is often filled first.
- Working profit-taking limits in thin overnight markets can be a benefit; other participants make mistakes and you are paid to provide liquidity.
- Targets can be extended to 2× or 3× risk, with size reduced to one-third to one-half initial before the remainder is managed under a different rule set.
- Whatever the plan, test it on a large sample and be consistent within the rules.

### Market Structure Targets
- Assume your limit will need to be traded through. In backtesting, a limit at $10.00 should not be assumed filled at $10.00; you are guaranteed fill only at $10.01.
- Place limits slightly inside visible chart points: above a visible $10.00 support rather than on or below it; below a visible $20.00 resistance. For intraday "high of the day" exits, place a few cents or ticks below the high.
- It rarely makes sense to place orders on the other side of a visible chart point unless you are deliberately farming stop orders there.
- Common structure-based targets: visible support/resistance, the same on a higher time frame, 52-week or contract highs and lows, session high/low, long accumulation shadows below ranges, distribution above.
- The pivot highs and lows of the swings usually delineate enough structure. If a risk-multiple target would land beyond a visible swing, tighten the order and bring it inside the swing.

## Trailing Stops

Trailing stops define levels that move with the trade. They can be simple (move to breakeven after 1× profit) or algorithmically dynamic. Trailing stops look fantastic in backtests on strongly trending markets because those markets are the ideal environment; the same stops perform much worse in real mixed markets.

### Moving Averages and Trend Lines
- Moving averages are arbitrary (why 20, 50, or 100 rather than 17, 49, or 103?). They are better than no plan but usually poor stop levels.
- Trend lines are also arbitrary (two traders draw two trend lines) and not suitable stop levels; good trend lines are routinely violated and immediately reversed, and the best entries often come from those reversals.
- If using a trend line as a trailing stop, require significant price action under the line (multiple closes, consolidation, multiple legs), accepting larger losses.

### Wilder's Parabolic SAR
- Created as a complete always-in, flip-on-stop system. Each day the stop moves closer to the extreme trend point by an acceleration factor that itself increases over time.
- Difficult to trade as a stand-alone always-in system, but useful for discretionary trailing-stop levels in trending markets: take first partial profit, then use Parabolic levels as the trail; on a hit, exit and do not flip.
- Internalize the calculation before using it; test on artificial data so you see how it reacts to every market condition.
- The acceleration factor forces many flips in choppy markets.

### LeBeau's Chandelier Stop
- Hangs a stop a fixed multiple of ATRs from the trend extreme, conceptually similar to the Parabolic without the acceleration factor.
- Gives trades more room than the Parabolic, which helps in the early stages of trends, but it locks in less profit in mature trends where the Parabolic would have tightened aggressively.

### Price Action / Market Structure Stops
- Possible rules: first down close in an uptrend, lowest low of three days ago, two consecutive down closes, or stops a multiple of ATR from the prior day's high, low, or close.
- Always test the statistical tendencies behind the rule. For example, stopping out after three consecutive down closes in stocks is a bad plan because the market is statistically primed for a bounce at that point.
- Discretionary traders tend to outperform any rule-based trailing stop on a large sample; they can anticipate where to stop out before a level is hit, or choose to let a level break without exiting.

## Active Management

Active discretionary management is one reason to be a discretionary trader, but it carries risks: more interaction with a process creates a false sense of skill (the slot-machine effect), and decision-making under pressure is hard. Even experienced traders make most of their worst on-the-fly execution decisions at the worst possible point in the market. Active management is acceptable only with a clear plan worked out in advance.

## Scaling In vs. All at Once

The choice between a single entry and multiple entries is partly constrained by market conditions (size, liquidity, the type of setup) and partly by trader inclination. Mean reversion entries often require multiple pieces.

- Define an absolute dollar amount to risk on the trade before scaling.
- Define a drop-dead ultimate stop past which you will not hold the trade.
- Track size and average price continuously so the impact of a loss at the ultimate stop is always known.
- The fact that you can scale into a trade means the market is moving the wrong way; this is a dangerous moment, not an opportunity to add without a plan.

## Taking Partial Profits

Partial profit-taking pays you as the market proves the idea, at the cost of not holding full size into the trades that become big winners. Either approach is viable if it is well planned.

- Make sure partial profit-taking is actually adding to the bottom line; otherwise it just removes edge from the winning trades.
- Early, unplanned partial exits often reflect the natural psychological tendency to lock in any profit, however small.
- Short-term traders on all time frames are especially vulnerable to executing partials in pure noise.

## Taking Partial Losses

Partial losses on the way to a stop anchor P&L to the loss side of entry. Visualize a P&L line moving in time alongside the market line: if you exit part of size into a small loss, the P&L line lags the market thereafter, making recovery harder.

- Decisions made when you are up or down a tiny fraction of the daily ATR on the trade usually do not add value.
- If considering a partial exit at a loss, exiting the entire position at a small loss is often the cleaner choice over deleveraging the P&L in the loss space.
- This is also true in reverse: the same anchoring effect on the profit side is precisely what you want from a partial profit-taking plan.

## Adding to Existing Trades

Adding is conceptually separate from a planned scaling-in entry. Planned scaling accumulates an intended size against a clear risk level, usually as price moves against you. Additions after the initial position is at full size are a different decision.

### Never Add to an Existing Trade
- For systems with a small, time-limited edge, the edge is strongest at the entry. Adding dilutes that moment.

### Add Back Only After Partial Exits
- A trader who exits half at 1× and re-enters half at the original price converts a stop-out into a half-sized loss because the offsetting win cushions it.
- A trader working a range can sell into the top of the range and re-buy at the bottom multiple times, building a cushion before the breakout. The trade-off: on an immediate, clean breakout, she will have less than full size.
- In a strong trend, taking partial profits at the appropriate target and then taking a fresh full-size entry at the next pattern, exiting half of that new entry at its target, gradually builds a larger, essentially risk-free core position. Do not increase size on later entries; growing profits feed overconfidence right as volatility expands near trend ends.

### Add Without Taking Partial Exits (Pyramiding)
- Reverse pyramids (1, 2, 4, 8, 16 …) are top-heavy. A small dip wipes out all accumulated profit, and trends become more volatile at the end. The probability of success is vanishingly small, and a "win" leaves the trader psychologically unprepared for the size.
- Reverse pyramids have a payoff close to a lottery ticket; treat them accordingly.
- Proper pyramids (largest size first, then successively smaller additions: 20, 16, 12 …) keep the average price near the base and can weather late-trend volatility better, but they add another random element to risk and sizing and should only be used when the additional upside compensates on a risk-adjusted basis.
- Decide whether additions are separate trades (each with its own entry and management rules) or one combined position with an averaged cost basis, and apply that decision consistently.
- The most important question is whether the addition adds value to the overall P&L; the default answer for many traders is no.

## Time Stops

A trade is usually initiated because an imbalance is expected to resolve within a short window. If that resolution does not happen quickly, much of the edge has gone out of the trade. Time stops exit positions that have not moved within a defined window, accepting the loss of some winners in exchange for a higher expectancy on the remaining set.

- Best trades often work right away. Trades that are flat early are usually less energetic and less profitable even when they eventually work, so the time stop still adds value.
- Implementation options: exit at the market when the window expires, or progressively tighten the stop very close to current prices as the window runs down (Parabolic-style). The latter cuts open risk while preserving the possibility of a delayed win, but is more advanced.

## Tightening Stops

Tightening stops always trades some probability of the trade working for some give-back protection. Move stops in response to market structure and shifting probabilities, never in response to fear or the desire to avoid losses.

### When the Trade Reaches a Risk-Multiple Target
- If the market reaches the mirror of the initial stop (1× the initial risk in the favorable direction), the pattern is working as expected. A failure from that level usually means a larger-scale failure, and there is no need to take a full-sized loss.
- For traders taking profits at 2× risk, tightening the stop to breakeven on the remainder eliminates open risk on the trade; a stop-out at worst produces a flat trade because the locked-in gain on the closed portion offsets the loss on the open portion. This significantly reduces return volatility for short-term swing traders.

### When Sharp Momentum Develops
- In a parabolic, runaway trend, very tight stops are justified. A stop worked each day under the previous day's low rides the move and exits on the first sign of reversal, booking the profit.
- This kind of tight trail is a profit-taking exit as much as a protective stop; in a parabolic move you actually want to be taken out.
- Parabolic moves are emotionally dangerous; tight stops on at least part of the position remove emotion from the exit decision.

### Tightening Against a Range Is Difficult
- Ranges are random and full of outside spikes, with low volume and liquidity. Medium-sized orders can move price dramatically. Tightening stops in a range is effectively a time stop; if that is not the intent, leave the stop near the initial risk point through the range and tighten only once a new trend develops.

## Widening Stops

The default rule is simple: do not move a stop in the direction of risk. Position size is calculated against the initial stop; widening it undercuts the position-sizing plan. Grimes's standing rule is that a stop can never be moved in the direction of risk, with two precisely defined exceptions:

- When a tightening of the stop was clearly an error. The stop is moved back out, but only as far as the day on which the error was made.
- When emerging market structure requires a slightly wider stop. Newer traders should never do this, because they cannot yet separate emotional reactions from legitimate market feel.

There is a third rare case: if you are scaling into a trade and a volatility-expanding event hits after only part of the intended size is on, you can choose not to complete the buying program and instead move the stop further out. The total bottom-line risk is unchanged, but the position is smaller against a wider stop.

## Managing Gaps Beyond Stops

Round-the-clock trading is reducing, but not eliminating, the gap problem. Overnight news or a shock event can open a market many times the intended risk beyond the stop. The damage is made worse when the trader has to make emotional decisions on the fly.

- Understand each market's tendencies around the open. Most equity gaps are reversed; an opening down-tick often trades up into the gap.
- The day's high or low is often set in early trading. If a long position gaps down and immediately trades up, place a new stop under the day's low to allow for recovery. If it gaps down and immediately presses lower or breaks out of the opening range, the trend is likely to continue down all day; exit immediately.
- These events will eventually produce stunning losses. Have a plan in advance, and follow it with perfect discipline.

## Portfolio Considerations

Any set of assets held at the same time behaves as a portfolio, even for short-term traders. Modern portfolio theory's assumptions are flawed, but the intuition that correlations shift and cluster in stress is correct, and it has direct implications for active books.

### Correlated Positions
- Correlations are unstable. Diverse, seemingly unrelated markets all tend to move toward correlation 1.0 in financial stress; diversification benefits disappear exactly when they are most needed.
- Equity traders do not have as many independent positions as they think. If you would not take equivalent open risk in a single index product, you almost certainly should not have that risk spread across a stock book, because the names will move together in a shock.
- The long and short sides of a technical book often do not offset in a sell-off. Longs get stopped at the worst point and shorts hold steady because the patterns are slow to flip, and the account suffers in the subsequent reversal.
- Forex books can be unintentionally concentrated. A book that is long AUDUSD, JPYUSD, and EURUSD is heavily short USD whether that was intended or not.
- Watch for shifts in correlation; the shifts are usually more dangerous than the levels.
- Practical risk rules:
  - Equity traders: define X as the percentage of the portfolio risked on any one trade. Risk no more than 2X–3X in highly correlated positions such as multiple stocks in the same sector, and assume that correlations across your full book are higher than they look.
  - Futures and forex traders: risk no more than 1.5X–2X in highly correlated groups (precious metals, petroleum products, grains, or currencies sharing regional or economic influence). Assume the worst-case scenario of the group moving as one.
  - Plan for the worst so that individual positions do not aggregate into unacceptable portfolio risk.

### Maximum Portfolio Risk
- Set a hard limit on total damage per day, defined as the total loss if every long and every short hit its designated loss. The probability of this day happening is small, but the financial and psychological impact of a 50% single-day hit is essentially unrecoverable.
- Manage risk first; the upside will take care of itself.

## Practical Issues: Monitoring, Review, and Execution

Monitoring and reviewing positions is a daily obligation, and the more you want to skip it, the more important it is. Skipping reviews after losses is precisely when the work matters most.

- Newer traders should trade fewer markets and know them deeply rather than spreading across many.
- For shorter time frames, screening tools should include: P&L for each position (day's change, closed portion, total from inception), distance to predefined stop and target levels on a volatility-adjusted basis (ATR or standard deviation, not raw points), gap openings in positions and related markets, and a "large move" screen that flags any market up or down by more than a chosen standard deviation multiple on the day.
- The simpler these tools are, the more robust and useful they are. A simple text graph of where current price sits in the day's range (open and last as deciles of the daily range, with color coding at the extremes) is one of the most useful intraday visualization tools available.

### Practical Execution Tips
- You can be a price maker (add liquidity with resting limits) or a price taker (hit bids and offers). Liquidity-adding rebates are valuable for high-volume short-term traders, but limit orders carry adverse selection; you will be in every losing trade and may price yourself out of some winners.
- True market orders have no price limit and no recourse on poor fills, and they can be filled outside the day's printed range. Slippage is a serious cost in some markets. Large market orders consume displayed liquidity, signal informed flow, and cause market makers to widen spreads and step away, which magnifies the impact.
- Use marketable limit orders (a buy limit placed at or above the offer, a sell limit at or under the bid) as the default, not pure market orders. They cap slippage to the limit price, can fail to fill if the market runs, and any unfilled portion continues to work as a resting limit. The only routine exception is a stop-loss exit where you genuinely want out at any cost.
- Execute at least one side of each trade on a limit order when possible. Paying the spread on both sides is a serious loss of efficiency, especially for short-term traders; a scalper playing 0.10/0.10 with 0.02 of spread on each side turns 0.10 winners into 0.06 and 0.10 losers into 0.14.
- In losing trades, do not work the order. Hit the bid to get out rather than offering lower and lower into a falling market; failing offers add pressure that drives price still lower.

### Large Orders in Thin Markets
- There is an unavoidable trade-off between urgency and price impact. Faster execution moves the market more.
- Three general approaches:
  - Break the order into smaller pieces, work them just in front of the bid, and use hidden orders; probe between the bid and offer for other hidden liquidity. Place very large orders so that matching another hidden block produces a clean print. After a large fill the displayed book will adjust, so be patient.
  - Counterintuitively, thin books are often more liquid than they look. Showing most or all of the bid size near the offer can attract a natural seller and complete the order at one price, offsetting the times the market instantly jumps away.
  - Use an execution algorithm. Most algorithms implement the first approach with constant vigilance and often with preferred access to dark pools.
- Partial exits in thin markets should be taken in the direction of price movement; you will rarely sell the very top or cover the very bottom, but the spread cost of being wrong is high and illiquid markets move faster in the anticipated direction.
- When mistakes happen (wrong side, wrong market, wrong price, canceled exit), fix the mistake immediately. Do not justify keeping the position, do not think, do not try to trade out of it. This is a discipline that must be enforced every time.
