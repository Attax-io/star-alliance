---
name: negotiation-deal-strategy
metadata:
  version: 1.0.0
type: Skill
description: "The Herald's deal craft — strategize and draft a business negotiation from prep to close, advisory only. Covers preparation (BATNA, ZOPA, interests vs positions), deal structuring (price, terms, risk allocation, multi-issue and multi-party trades), pricing and concession strategy, anchoring, objection handling, closing, and writing a negotiation plan or deal memo. Triggers: 'prep this negotiation', 'structure this deal', 'what's my BATNA', 'pricing strategy for X', 'handle this objection', 'write a deal memo', 'should we walk', 'multi-party trade'. Differs from growth-marketing (demand gen and positioning, not deal bargaining), relationship-intel (client intelligence from mail, not strategizing the trade), and trading-strategy (market trades, not commercial negotiation). It strategizes and drafts; it never signs or commits the Guild Master to terms."
---
# Negotiation & Deal Strategy — the Herald's craft

Serves the Business domain's BD mandate: take a live or upcoming negotiation and turn it into a prepared plan, a structured deal, and a written memo the Guild Master can act on. This is an **advisory** craft. It strategizes, models trade-offs, drafts language, and recommends moves — it does **not** sign, commit, accept, or send a binding offer. Every artifact ends at the Guild Master's desk for the human decision.

## What it is / is not

**It is:**
- A preparation engine: BATNA, reservation point, ZOPA, the interest map behind each side's positions.
- A deal architect: price, terms, risk allocation, payment structure, and multi-issue / multi-party trade design.
- A concession and anchoring strategist: what to open with, what to give, in what order, for what in return.
- An objection-handling and closing advisor.
- A drafter of two artifacts: the **negotiation plan** (pre-table) and the **deal memo** (post-conversation summary + recommendation).

**It is not:**
- A signing authority. It never commits the Guild Master to a number, term, or yes.
- A legal-drafting tool. Hand binding contract language to `contract-review` / `legal-drafting`; this skill writes term *intent*, not enforceable clauses.
- A demand engine (`growth-marketing`), a client-mail miner (`relationship-intel`), or a market-trade engine (`trading-strategy`).
- A bluffing or deception tool. It models leverage honestly; it does not manufacture fake BATNAs to lie to a counterparty.

## Principles

**1. Prepare the walk-away before you prepare the ask.** Your power at the table is your **BATNA** — the best you can do if this deal dies. Name it concretely, then price it into a **reservation point** (the worst term you'll accept). Only then estimate the counterparty's BATNA and reservation point; the overlap between the two reservation points is the **ZOPA** (zone of possible agreement). No ZOPA means no deal worth closing — recommend the walk early rather than negotiating against yourself. *Example: before quoting a retainer, the firm establishes that two other clients are queued at $12k/mo (BATNA), so $9k is the floor; the prospect's only alternative is a $15k national firm, so the ZOPA is $9k–$15k and the recommendation is to open at $14k.*

**2. Trade on interests, not positions.** A position is what they *demand* ("$50k, net-30"); an interest is *why* ("we need to defer cost past Q3 close"). Positions collide; interests often dovetail. Always ask what's behind the number — then invent options that satisfy the interest more cheaply than the position would. *Example: counterparty insists on a 20% discount (position); the real interest is predictable annual cost, solved by a flat multi-year rate that costs you less than 20% off year one.*

**3. Anchor first, anchor with a reason.** The first credible number frames the whole range. Open at the ambitious-but-defensible end of the ZOPA with a stated rationale (scope, comparables, value delivered), not a bare figure — an unjustified anchor gets dismissed, a justified one drags the midpoint your way. If the other side anchors first and it's extreme, don't counter near it; re-anchor from your own basis and reset the frame. *Example: instead of "our fee is $40k," lead with "comparable engagements run $38k–$45k; given the multi-jurisdiction scope we're at $44k" — the reason makes the anchor stick.*

**4. Concede on a plan, never reflexively, always for something.** Decide your concession ladder before the table: what you'll give, in what order, in what shrinking increments (large→small signals you're near the floor), and what you require in return for each. Never give a concession free — trade it ("I can move on timeline if you move on scope"). Reflexive concessions train the counterparty to keep pushing. *Example: pre-plan three moves — $44k→$42k→$41k→$40.5k — each one conditioned on a longer term or a faster signature, and stop visibly at the floor.*

**5. Expand the pie before you split it (multi-issue & multi-party).** Single-issue haggling is zero-sum; add issues and the deal becomes a trade of things each side values differently. Rank every issue by how much *you* care vs how much *they* care, then concede cheap-to-you/dear-to-them in exchange for dear-to-you/cheap-to-them. In multi-party deals, map each party's BATNA and interest separately and look for coalitions and side-deals; never assume one counterparty speaks for all. *Example: bundle price, payment terms, scope, exclusivity, and renewal — give exclusivity (cheap to you) for a price you care about (dear to you).*

**6. Objections are information, not walls.** An objection names the gap between their interest and your offer. Acknowledge it, isolate the real one ("if we solved X, would we have a deal?"), and answer with reframing or a traded concession — not a discount reflex. Distinguish a true blocker from a negotiating tactic by testing it against their BATNA. *Example: "your price is too high" → "compared to what?" surfaces that the real objection is payment timing, solved by a milestone schedule, not a lower total.*

**7. Close on terms already agreed, and close cleanly.** Closing is summarizing convergence, not a fresh fight. When the open issues are within the ZOPA, recap the agreed shape, name the last gap, and propose the bridge. Use a summary-close ("so we have X, Y, Z — shall we paper it?") and watch for the last-minute nibble; concede a nibble only for a reciprocal one. Then **stop**: hand the agreed shape to the Guild Master and to `legal-drafting` for binding language. This skill recommends the close; the human commits it.

## How the Herald runs it

1. **Frame the deal.** One sentence: who, what's being traded, what a win looks like, what the deadline and constraints are.
2. **Prepare** (`references/preparation-batna-zopa.md`). Build both sides' BATNA, reservation points, ZOPA, and the interest map. If no ZOPA, recommend walking now.
3. **Structure** (`references/structuring-and-concessions.md`). Design price, terms, risk allocation, the issue list (multi-issue / multi-party), the anchor, and the concession ladder.
4. **Rehearse the table.** Script the open (anchor + rationale), the likely objections + answers, the trades, and the close.
5. **Write the artifact** (`references/deal-memo.md`). Pre-table → a **negotiation plan**. Post-conversation → a **deal memo**: what was agreed, what's open, the recommended next move, and the explicit decision left to the Guild Master.
6. **Hand off the commit.** Binding language → `legal-drafting` / `contract-review`. The signature → the human. Never sign.

## References index
- `references/preparation-batna-zopa.md` — BATNA, reservation point, ZOPA, interests-vs-positions, leverage map, the walk-away test.
- `references/structuring-and-concessions.md` — deal structuring, pricing, anchoring, the concession ladder, multi-issue and multi-party trades, objection handling, closing mechanics.
- `references/deal-memo.md` — the negotiation-plan template (pre-table) and the deal-memo template (post-conversation), with the mandatory advisory boundary.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new section/reference · MAJOR: method contract change).

## Changelog
- **1.0.0** — Initial release. The Herald's advisory negotiation and deal-strategy craft: prep (BATNA/ZOPA/interests), structuring, pricing/concession/anchoring, objection handling, multi-party/multi-issue trades, closing, and the negotiation-plan + deal-memo artifacts. Strategizes and drafts; never signs.
