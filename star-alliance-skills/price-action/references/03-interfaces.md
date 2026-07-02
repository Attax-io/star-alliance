---
type: Document
timestamp: 2026-07-02T12:28:13Z
---

# Interfaces — Breakouts, Reversals & Failures

## The Transition Framework

Markets oscillate between **trends** and **trading ranges**, so the possible transitions are limited.

- **Three primary transitions:**
  - *Breakout:* a trading range resolves into a trend.
  - *Trend termination into range:* an established trend ends and price goes sideways.
  - *Trend reversal:* an established trend ends and a new trend emerges in the opposite direction.
- **Two failure patterns** that complicate the picture:
  - Breakout fails, market remains locked in a larger range.
  - Apparent trend termination fails, the established trend continues.
- **Why it matters:** the difference between "middle-of-the-chart" analysis and trading at the right edge is poorly understood and is a key reason backtest results diverge from live results. Every bar provides new information that can invalidate a prior read.
- **Rule of thumb:** until a new structure confirms, default to trend continuation — an established trend is a powerful force and usually takes substantial contrary pressure and time to end.

---

## Breakout Trade: Range to Trend

A breakout is an attempt to enter in the direction the market is already moving when a support or resistance level gives way. The logic is simple: if a market is going higher, it must take out prior highs; if lower, it must take out prior lows. Many large trend moves began as breakouts.

- **The central problem:** the *majority* of breakout trades fail. Excursions beyond support or resistance are usually short-lived, volatility is high, liquidity is low, and indiscriminate entries get eaten alive by transaction costs and small losses — "death by a thousand cuts."
- **Terminology:** Grimes uses "breakout" for both upside and downside breaks; in this reference, breakout is direction-neutral.
- **The institutional backdrop:** the best breakouts are driven by large players who cannot enter their full size on the breakout itself. They often position *before* the breakout, and then sell into the public's breakout-buying frenzy. Buying where large players are selling (or vice versa) is the pressure that often produces failed breakouts.

---

## Patterns Preceding Good Breakouts

Pre-breakout character is the best filter separating tradable breakouts from noise.

- **Higher lows into resistance (ascending triangle logic):**
  - A market oscillates in a range, then large buyers begin accumulating on declines.
  - Their buying arrests the decline; they turn off buying to avoid paying up; skilled operators even offer some supply at higher prices to book small profit and hold price down.
  - As competition intensifies, declines become shallower; large traders grow more aggressive at higher prices. A mild feedback loop leaves a pattern of shorter swings into resistance.
  - Read: this often sets up excellent breakout trades. The pattern applies inverted to the downside.
- **Tight range near the edge of a larger range:**
  - A consolidation less than roughly 25% of the larger range's height, sitting at the edge of a well-defined range.
  - It shows urgency and conviction — large players are willing to pay higher (or short lower) rather than let price drift back to the middle.
  - Read: this is one of the classic signs that the touched support or resistance is likely to fail, which is a successful breakout.
- **Pre-breakout accumulation (Wyckoff springs and upthrusts):**
  - Large players' positioning shows up as violations of the range that fail and reverse — springs at lows, upthrusts at highs.
  - These short-lived excursions beyond support/resistance are strong evidence of institutional positioning and frequently set up good breakouts.
  - Most accumulation/distribution is invisible, but the points where it cannot be hidden are exactly these edge violations.

---

## Characteristic Patterns at Good Breakouts

A good breakout is driven by institutional interest that eventually pulls in the public, creating a feedback loop.

- **High volatility at the breakout:**
  - A polite, gentle lift through resistance is not a good sign. Good breakouts are driven by unusual order flow.
  - Expect expanded bar ranges on the trading timeframe, and almost always on lower time frames.
  - The most useful quantitative measure is *instantaneous* volatility: the ratio of the current bar's range to a window of previous bars.
- **Slippage is good:**
  - Slippage is the difference between intended and actual execution.
  - Around a real breakout, you should *have to pay up*. Difficulty of entry is a confirming signal.
  - *Positive slippage* — getting filled better than expected — is a warning sign. It means someone was willing to sell to you at a great price, i.e., selling pressure was stronger than expected. Positive slippage around breakouts often signals an impending failure.
- **Immediate satisfaction:**
  - "Immediate" depends on timeframe (seconds for tick traders, days for weekly traders).
  - It does not mean instant win; some back-and-forth around the level is normal.
  - A breakout filled at $20.15 that immediately begins grinding lower is no breakout at all.

---

## Patterns Following Good Breakouts

A sharp move out of the range is followed by a pause and a pullback. *This first pullback is the critical tell.*

- **Pullback holds outside the breakout level:**
  - Market breaks through, trades sharply beyond, then makes a clean pullback that holds outside the level.
  - Intuition: there is real order flow defending the breakout; small players chase; the level is not revisited.
  - Easy to manage — a breakeven stop at entry can be set and largely forgotten.
- **Pullback violates the level:**
  - The market *does* come back through the breakout level. This is more common than the clean version.
  - Why it works anyway: large players are often working a hybrid valuation/technical approach and are happy to add at lower prices. They are not obligated to defend the level precisely.
  - Three-group model (large players, naive short-term traders, noise traders):
    - Large players may not be ready to commit full capital right after the breakout (incomplete accumulation, profit-taking at the level, or uncertainty before an event).
    - Pullback triggers naive short-term traders to recognize "failed breakout" and sell en masse just below the level.
    - Large players absorb that inventory.
    - When selling dries up, large players resume aggressive buying.
    - Short-term traders then chase, propelling the real trend.
  - **Lesson:** do not expect levels to hold cleanly. A pullback that violates the breakout level can be the *catalyst* for the real move.

---

## Patterns of Failed Breakouts

Breakouts fail frequently, and the failures can be violent. Markets probe levels where resting orders cluster, and that probing is the engine of many failed breakouts.

- **Why stops cluster:** short-term traders define risk at visible pivots and previous-day extremes, so stops pile up just outside the range. A large player who wants to sell into that liquidity may paradoxically *buy first* — pushing price just far enough to trigger the stops, then selling into the resulting burst of buying.
- **Failure test of the breakout level:**
  - A brief excursion beyond a significant level followed by an immediate reversal.
  - "Immediate" is timeframe-dependent: a working rule is no more than two or three bars outside the level, then strong momentum reversing.
  - In good failure tests, the close of the reversal bar is back on the other side of the level — old-school chartists called this a "turkey shoot."
  - Even when the close of the reversal bar is ambiguous, lower time frame action often shows the tell: in a failed upside breakout, bounces are slow and reluctant, the market "goes down a lot easier than it goes up." Sharp downside momentum typically emerges within several bars.
  - If no such momentum appears, it is more likely a simple pullback is underway — and pullbacks do not need to hold outside the level.
  - **Distinguishing signal in every case:** lack of conviction and momentum beyond the level, read on price action and lower time frames.
- **Failed pullback following a breakout:**
  - Unlike typical pullback failures that produce flat consolidations, breakout pullbacks tend to fail with *strong momentum* out of the pattern, or fail on a second test of the extreme reached after the pullback.
  - There is usually too much order flow for the market to simply go dead after a breakout.
  - A flat consolidation outside the pre-breakout range is usually *constructive* for the breakout, indicating real conviction.
  - Best failure pullbacks produce a sharp reversal out of the wrong side of the pullback formation — e.g., sellers push below support, hold a small consolidation below it, then buyers bid the market back above support with large bars and momentum. The presence of sharp momentum against the pullback is a reality the whole market must acknowledge.
- **Failure pullback (the trade after the failure):**
  - Once the breakout failure is confirmed by sharp countertrend momentum, the first pullback against the failed direction is often tradable.
  - This is the classic "you should be out of Dodge" signal if holding a losing breakout trade.
  - On a higher time frame, this whole sequence often appears simply as strong momentum away from the breakout level, or as price rejection at the level.

---

## Trend to Trading Range

Trends that end as ranges do so through a failed pullback. The label is partly semantic — by definition, a trend that fails to continue becomes a non-directional area — but the value is operational: it tells you what to look for, how to differentiate a coming range from a coming reversal, and where to set risk.

- **What usually precedes a failed pullback:**
  - Some form of **momentum divergence** (not sufficient alone, but an initial warning).
  - Lower time frame price action and emerging market structure on the trading timeframe.
  - Extremely high volatility (possible climax or exhaustion).
  - Multiple trend legs in the same direction. After more than three directional pushes, the probability of pullback failure rises.
- **Three forms of pullback failure that lead to ranges:**
  - *Direct transition into a range:* no move out of the pullback; prices stabilize; small initial range expands via excursions above and below that tempt breakout attempts. Buyers and sellers have reached equilibrium. Usually no reason to trade these.
  - *Failure test of the previous trend extreme:* the pullback tests the prior pivot (precisely, falling short, or slightly penetrating). Slight penetration can produce sharper countertrend momentum from trapped traders. The common thread is lack of conviction beyond the previous extreme.
  - *Failure pullback sequence:* sharp countertrend momentum, a small pullback (often tradable), then another strong thrust that exhausts itself near the measured move objective (MMO) — that exhaustion point often defines the initial extreme of the new range.
- **Core rule:** *trends fail when pullbacks fail.* Anyone trading trends, ranges, or breakouts needs to know pullback-failure patterns cold.

---

## Trade Management at Trend-to-Range Transitions

- **Set realistic expectations.** Many trends end in ranges, not reversals. Chasing the "buy the low / sell the high" reversal that never comes is a quick way to grind an account down. Sometimes small trades within the range are all the market offers.
- **Confirm the termination.** Look for failure patterns — springs and upthrusts — to distinguish a true termination from a brief test of the new range. Strong momentum beyond the previous trend extreme is an undeniable sign the trend is continuing.
- **Use the higher time frame to set bias.** On the trading timeframe, the new range is noisy and hard to read. On a higher timeframe, the same structure usually resolves as either a continuation or a reversal in that higher timeframe trend. If the higher timeframe shows multiple trend legs in one direction, is overextended, and is showing momentum divergence, the trading timeframe range is more likely a reversal pattern. If the higher timeframe trend is still intact, the range is likely a complex, two-legged pullback — shorting the bottom of such a range is the *wrong* trade on the higher timeframe.
- **Protect profits once the higher timeframe trend reasserts.** Nothing is worse than correctly identifying a termination, correctly trading countertrend, and then aggressively adding to the position right where you should be locking in gains.

---

## Trend to Opposite Trend (Trend Reversal)

The most likely outcome after a trend ends is a range, but sometimes a trend ends and a new trend in the opposite direction emerges without an intervening range. Two scenarios make sudden reversals more probable.

- **Parabolic blow-off into climax:**
  - Trends end in two ways: rolling over as momentum fades, or a parabolic range expansion culminating in a buying or selling climax.
  - In a buying climax, every willing buyer buys. When buying pauses, it is obvious there is no one left to buy; the market collapses into the vacuum. Trapped traders amplify the move.
  - **Warning signs that a trend is primed for a blow-off:**
    - The trend has lasted a long time.
    - Acceleration into a steeper trend — either a series of ever-steepening legs or a single inflection.
    - Multiple trend lines needed to contain the move; many short, steep lines.
    - Bars trading completely outside Keltner channels (multiple "free" bars) — unusual and unsustainable.
  - **Hard rule:** if on the wrong side of a parabolic expansion, limit risk with iron discipline. Do not hold hoping for a return; do not average down. The market *will* reverse eventually, but margin calls do not wait.
  - **Multi-timeframe application:** the same pattern exists on all time frames, with significance scaling accordingly. A climax on a 1-minute chart may mark a few hours; on a daily chart, it can set a high that holds for years.
  - **Best reversal setup:** a parabolic exhaustion on a lower time frame occurring *into* a measured-move objective for a complex pullback on a higher time frame. Entering long against the lower-time-frame climax and with the higher-time-frame structure is one of the most reliable reversal setups in the technical arsenal.
- **Last gasp (failure test after consolidation):**
  - After an extended trend and a well-recognized topping formation (head and shoulders, double top), there are usually many traders shorting in anticipation of a reversal, with stops just beyond the recent highs.
  - There are also traders playing for trend continuation who will buy on the break.
  - Net result: latent buying pressure piled just above the highs.
  - When price probes that area, stops fire, and then the question is whether real buyers step in. If they do not, the high is a fake-out. Shorts reestablish, trapped longs eventually sell, downside momentum develops.
  - This is a special case of a failure test at the prior trend extreme, and is extremely reliable in the right context. The "last gasp" is essentially a Wyckoff upthrust (or spring, inverted) *preceded by enough consolidation that another trend leg seemed primed*. The pattern draws its power from the failure of that potential.
- **Trend change without warning:**
  - Rare, but worth flagging because the absence of a pattern is itself a pattern.
  - Usually driven by fresh information (company-specific news, a crop report, a major economic release) that forces immediate reassessment, produces a feedback loop of position adjustments, and can result in breathtaking moves. Volatility and uncertainty spike together.
- **Change of character:**
  - The common thread across all reversals is a distinct change in how the market is moving — the established pattern is broken, and new movement emerges with strong countertrend momentum.
  - Grimes calls the core skill "Hey, that's different." A downswing bigger than the preceding upswing, after many swings of the opposite character, is the kind of break that intuition flags before it can be quantified.
  - Confirmation can come from other factors or indicators, but stay open to the initial intuition that the pattern has shifted, and verify with lower time frame price action.

---

## Trend to Same Trend (Failed Trend Reversal)

A failed trend reversal is, technically, a "failed failure" — and the distinction from ordinary trend continuation matters because of the trapped traders involved.

- **Why it matters:** when a well-known reversal pattern (a large head and shoulders, a complex pullback's second countertrend leg) draws in countertrend traders, their eventual forced adjustments add fuel to the original trend.
- **Power source:** trapped traders who were aggressively anticipating a reversal. Anytime too many participants are leaning one way, the market is vulnerable to an outsized move in the other direction.
- **Practical note:** these patterns do not require detailed study as a separate category — at root they are trend continuations powered by forced covering of countertrend positions. Recognize the setup, recognize the fuel, and trade accordingly.
