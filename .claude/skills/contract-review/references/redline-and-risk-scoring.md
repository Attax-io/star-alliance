---
type: reference
title: Redline and risk scoring
skill: contract-review
version: 1.0.0
---

# Redline and risk scoring

How to turn a read into ranked flags and concrete edits. Two instruments: a **severity
rubric** that sorts the report by blast radius, and a **redline pattern** that hands the
negotiator usable language instead of complaints.

## Severity rubric — score by blast radius, not by oddness

Rank each flag by **impact if it triggers × likelihood it triggers** — not by how
unusual the wording reads. Polished boilerplate can hide a Critical; an awkward sentence
can be Cosmetic.

| Severity | Meaning | Examples |
|----------|---------|----------|
| **Critical** | Could sink the deal or cause uncapped/existential loss. Must change before signing. | Uncapped liability; one-way open-ended indemnity; perpetual all-IP assignment with no background carve-out; mandatory arbitration in a hostile distant seat with one-way fee-shifting. |
| **High** | Materially one-sided; real money or lock-in at stake. Negotiate hard. | One-way termination-for-convenience; silent auto-renewal with 90-day notice; confidentiality covering only their disclosures; cap carve-outs that uncap only our side. |
| **Medium** | Off-market or asymmetric, worth pushing but survivable. | Short cure period for our breach vs long for theirs; broad assignment/change-of-control on their side only; "as is" warranty disclaimer. |
| **Low** | Minor tilt or tidy-up; raise if cheap, concede if needed. | Undefined terms ("workdays"), net-60 vs net-30, notice-by-fax mechanics. |
| **Cosmetic** | No risk; clarity/consistency only. | Cross-reference typos, defined-term capitalization drift. |

A flag's severity drives **sort order** in the report (Critical first) and the
**accept / negotiate / reject** call below.

## Accept / negotiate / reject

Each flag gets one disposition:

- **Accept** — standard and fair; no change sought. (Record it; a clean clause is signal
  that the rest is not boilerplate.)
- **Negotiate** — off-market or asymmetric; propose an edit and a fallback you would
  live with.
- **Reject** — unacceptable as written; must change or the deal does not proceed.
  Reserve for Critical and the worst High flags; if everything is "reject" the report
  loses its force.

Tie the disposition to the basis (document text, citable governing law, or a
client/firm preference the Butler confirmed). If the right call depends on a fact you do
not have — deal value, whether IP is core, the client's risk appetite, jurisdiction
enforceability — mark it **Open question** and ask; do not default-guess.

## The redline pattern — strike / insert / fallback

For every negotiate/reject flag, give the negotiator three things:

1. **Strike** — the exact language to remove (quote it).
2. **Insert** — the exact replacement language to propose.
3. **Fallback** — the position you would accept if they refuse the insert.

A flag without an insert makes someone do the work twice. Worked examples:

**Missing liability cap (Critical):**
- Strike: *(nothing — the clause is absent)*
- Insert: "Except for the carve-outs below, each party's aggregate liability under this
  Agreement shall not exceed the fees paid or payable in the twelve (12) months
  preceding the event giving rise to the claim. Carve-outs (uncapped, both parties):
  breach of confidentiality, indemnification obligations, IP infringement, and gross
  negligence or wilful misconduct."
- Fallback: 2x trailing-12-month fees; carve-outs must stay mutual.

**One-way indemnity (Critical / High):**
- Strike: "Vendor shall indemnify Customer against any and all claims arising out of
  this Agreement."
- Insert: a mutual indemnity scoped to each party's own breach, negligence, and IP
  infringement, with a duty to defend, notice, and control-of-defense for the
  indemnifying party.
- Fallback: keep one-way but narrow triggers to defined IP-infringement and gross
  negligence, and bring it under the liability cap.

**Silent auto-renewal (High):**
- Strike: "This Agreement shall automatically renew for successive one-year terms."
- Insert: "...unless either party gives written notice of non-renewal at least thirty
  (30) days before the end of the then-current term," plus a cap on any renewal price
  increase.
- Fallback: 60-day window is acceptable; price-increase cap is not negotiable.

**Broad IP assignment, no carve-out (Critical):**
- Strike: "All intellectual property created by Vendor shall be the sole property of
  Customer."
- Insert: assignment limited to the **deliverables**, with an express carve-out
  retaining Vendor's pre-existing IP, tools, libraries, and know-how, and a license to
  Customer to use them only as embedded in the deliverables.
- Fallback: assign deliverables + grant Customer a license to background IP; never a
  full assignment of background IP.

## Reviewer discipline

- Quote the exact clause text you are flagging — never paraphrase the contract into a
  flag.
- Separate **risk opinion** from **settled law**; label each.
- Sort the flag table Critical → Cosmetic so the principal reads the deal-breakers
  first.
- Everything routes to the certify gate as a recommendation; you do not approve or sign.
