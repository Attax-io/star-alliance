---
type: reference
title: Clause checklist — the high-risk roster
skill: contract-review
version: 1.0.0
---

# Clause checklist — the high-risk roster

The clauses where inbound contracts most often tilt against the receiving side. For
each: what the clause does, what *fair* looks like, the one-sided pattern to flag, and
— often the bigger risk — what its **absence** means. Read the contract once for what it
says and once for which of these is missing.

## Indemnity

- **Does:** one party agrees to cover the other's losses/claims arising from defined
  events (IP infringement, breach, negligence).
- **Fair:** mutual where risk is mutual; scoped to defined triggers; tied to the
  indemnifying party's actual fault.
- **One-sided flag:** one-way (only we indemnify), open-ended triggers ("any claim
  arising out of this agreement"), no duty-to-defend/control-of-defense balance, no
  cap.
- **Absence flag:** if there is indemnity but **no liability cap above it**, the
  indemnity is effectively unlimited — pair this clause with the cap every time.

## Limitation of liability (caps)

- **Does:** bounds the maximum a party can owe, and excludes categories (indirect,
  consequential, lost profits).
- **Fair:** mutual cap (commonly 12 months' fees, or 1–2x contract value), with sensible
  carve-outs (confidentiality breach, indemnity, IP, gross negligence) *uncapped on
  both sides equally*.
- **One-sided flag:** cap protects only their liability; carve-outs that uncap *our*
  exposure but not theirs; a cap so high it is meaningless.
- **Absence flag — Critical:** no cap at all = unlimited liability. The single most
  important omission to catch.

## IP assignment & ownership

- **Does:** allocates who owns work product, deliverables, and improvements.
- **Fair:** they own what they pay us to build *for them*; we retain pre-existing IP,
  tools, know-how, and a license to reuse generic components.
- **One-sided flag:** broad present assignment of "all intellectual property" with no
  background-IP carve-out; assignment of improvements to our own tools; perpetual,
  irrevocable, royalty-free grants beyond the deliverable.
- **Absence flag:** no background-IP carve-out means our reusable tooling may transfer
  silently.

## Term, termination & termination-for-convenience

- **Does:** sets duration and the exits.
- **Fair:** symmetric termination rights; termination for cause with cure period;
  termination for convenience available to us (or to neither).
- **One-sided flag:** they can exit for convenience but we cannot; long cure periods for
  their breach, short for ours; survival clauses that keep our obligations alive but not
  theirs.
- **Absence flag:** no termination-for-convenience and no cause exit = locked to the
  full term regardless of performance.

## Auto-renewal / evergreen

- **Does:** renews the term automatically unless notice is given.
- **Fair:** renewal with a reasonable, clearly-stated non-renewal notice window
  (30–60 days), and price-change transparency.
- **One-sided flag — High:** silent auto-renewal, long notice windows (90+ days), notice
  required by a hard-to-meet method, automatic price escalation on renewal.
- **Absence flag:** none — but verify the renewal mechanics are calendared so the window
  is not missed.

## Governing law & dispute resolution

- **Does:** picks the law and forum (courts/arbitration, venue).
- **Fair:** a neutral or our-jurisdiction law; a forum that is not prohibitively
  expensive for us to litigate in.
- **One-sided flag:** their home jurisdiction with hostile or unpredictable law;
  mandatory arbitration in a distant/expensive seat; fee-shifting that only runs one
  way; class-action waivers paired with arbitration.
- **Absence flag:** no governing-law clause leaves the forum to conflict-of-laws
  uncertainty — flag as a gap to fill.

## Confidentiality scope (esp. NDAs)

- **Does:** defines Confidential Information, permitted use, duration, and exclusions.
- **Fair:** mutual obligations; standard exclusions (public, independently developed,
  already known, compelled by law); a defined term (commonly 2–5 years; trade secrets
  may run longer).
- **One-sided flag:** definition only covers *their* disclosures; no standard
  exclusions; perpetual confidentiality on ordinary (non-trade-secret) information;
  residual-knowledge clauses that quietly let *them* use our information.
- **Absence flag:** missing exclusions or missing return/destruction obligation.

## Non-compete / non-solicit

- **Does:** restricts competing or soliciting employees/customers post-term.
- **Fair:** narrow scope, duration, and geography; enforceable under the governing law;
  tied to a legitimate protectable interest.
- **One-sided flag:** broad market/geography, long duration (enforceability is
  jurisdiction-dependent — flag the dependency), one-way only, no consideration.
- **Absence flag:** none, but confirm whether one was expected for the deal type.

## Also scan (lower-frequency, still load-bearing)

- **Warranties & disclaimers** — are we warranting more than we can stand behind; are
  their warranties disclaimed to nothing ("as is")?
- **Payment terms** — net days, late fees, set-off rights, suspension-for-non-payment
  asymmetry.
- **Assignment / change of control** — can they assign to anyone (incl. a competitor)
  while we cannot?
- **Insurance requirements** — are the limits achievable and proportionate?
- **Data protection / security** — DPA present where personal data flows; breach-notice
  duties symmetric?
- **Force majeure** — mutual, and does it excuse *payment* (it usually should not)?
- **Most-favoured-customer / exclusivity** — quiet commitments that bind future deals.
- **Notice mechanics** — method and address realistic and current.
