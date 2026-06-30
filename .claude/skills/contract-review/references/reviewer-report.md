---
type: reference
title: Reviewer's report structure
skill: contract-review
version: 1.0.0
---

# Reviewer's report structure

The deliverable of a review. A report a principal can read top-to-bottom and act on:
the deal-level verdict first, the ranked flags next, the redline summary, the open
questions, and the advisory hand-off that keeps the skill on the recommend side of the
line. Lead with the verdict; bury nothing material below the fold.

## 1. Header

- Document reviewed (title, version/date), parties, **our side**, deal type.
- Reviewer (the Translator), review date, governing-law expectation, client risk
  appetite as confirmed by the Butler.
- One-line scope note: *"Advisory review of an inbound agreement. Recommendations for
  counsel's review and the principal's decision — not legal advice, not an approval to
  sign."*

## 2. Deal-level risk verdict

A single overall verdict, stated first:

- **Risk rating:** Critical / High / Medium / Low — the highest unresolved severity
  drives it.
- **One-paragraph bottom line:** can this be signed as-is (rare), signed after the
  Critical/High flags are negotiated, or should it be rejected/re-papered? Name the two
  or three issues that decide it.
- **Count summary:** e.g. "3 Critical, 5 High, 4 Medium, 2 Low — 2 must-change before
  signing."

## 3. Flag table (sorted Critical → Cosmetic)

| # | Clause / § | Severity | Disposition | Issue (one line) | Recommended edit |
|---|-----------|----------|-------------|------------------|------------------|
| 1 | §9 Liability | Critical | Reject | No cap — unlimited exposure. | Insert mutual 12-mo-fees cap w/ carve-outs. |
| 2 | §4 IP | Critical | Reject | All-IP assignment, no background carve-out. | Limit to deliverables; retain background IP. |
| 3 | §12 Renewal | High | Negotiate | Silent auto-renew, 90-day notice. | 30-day non-renewal window + price cap. |

Each row links to its detailed entry. Sort by severity so deal-breakers are read first.

## 4. Detailed findings

One entry per non-trivial flag:

- **Clause & quoted text** — the exact contract language (never paraphrased).
- **Why it is a risk** — who it favours, what it costs us on a bad day; **label risk
  opinion vs settled law**.
- **Severity & disposition** — and the basis (document / citable law / confirmed
  preference).
- **Redline** — strike / insert / fallback per `redline-and-risk-scoring.md`.

## 5. Redline summary

The consolidated strike/insert set, ready to drop into a markup or send to the
counterparty — so the negotiator does not reassemble it from the findings.

## 6. Open questions

Facts the review could not resolve and that change the recommendation:

- Deal value / contract size (drives the cap number).
- Is the IP core to the client's business? (drives assignment posture)
- Client's risk appetite and must-have terms.
- Jurisdiction-specific enforceability (e.g. non-compete) needing counsel input.

State each as a question with the decision it unblocks. Do not paper these with
plausible defaults — ask.

## 7. Advisory hand-off (the closing line — non-negotiable)

End every report with language that keeps the skill advisory:

> *"The above are recommended positions and risk observations for the review of
> qualified counsel and the decision of the principal. This review is not binding legal
> advice and is not an approval to execute. Routed to the certify gate for sign-off; no
> signature or commitment is made by this review."*

Then route to the certify gate. A human lawyer decides; a principal signs. You advise.

## Tone & format

- Plainspoken and decisive on risk; never alarmist, never reassuring-to-a-fault. "This
  exposes us to X" not "this is fine" and not "this is catastrophic" unless it is.
- Quote, don't paraphrase, the clauses you flag.
- Lead with the verdict; sort by severity; make every recommendation actionable.
- Mark clearly throughout what is opinion versus settled law.
