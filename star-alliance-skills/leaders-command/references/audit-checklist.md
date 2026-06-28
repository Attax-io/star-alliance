---
type: Document
title: Audit checklist — the six command failure modes and the rewrite
timestamp: 2026-06-28T00:00:00Z
---

# AUDIT mode — critique and rewrite a draft order

Run a draft order through the six failure modes. Each is a confirmed cause of a wasted
round-trip, a wrong result, or burned tokens. Score, then rewrite.

## The six failure modes

| # | Failure | Tell | The fix (axiom) |
|---|---|---|---|
| 1 | **Buried lede** | The actual ask is in paragraph three; sentence one is throat-clearing | Move the deliverable to line one (axiom 2) |
| 2 | **Ambiguity** | A word could mean two things — "the file", "soon", "clean it up", "etc." | Name the exact file/number/format; replace "etc." with the full list (axiom 3) |
| 3 | **Missing input** | The subordinate would have to ask for a path, a constraint, or a prior decision to start | Add every fact it can't look up; for a doer/subagent, assume zero shared memory (axiom 4) |
| 4 | **No bounds** | No scope, no anti-goals — the subordinate could touch anything | State what NOT to do/touch and the limits (axiom 5) |
| 5 | **No output contract** | "review this", "look into it" — no definition of done | Specify the return shape + acceptance criteria so the result is verifiable in one pass (axiom 6) |
| 6 | **Wrong register** | Jargon aimed at the Guild Master, or hand-holding aimed at a peer member | Right-size: plain English + options for the human; intent + latitude for a member (axiom 7) |

## The audit score

Count the failure modes present. **0 = ready to send.** Any **missing input or no output
contract (3 or 5) is a hard block** — those two guarantee a loop. Buried lede and ambiguity
(1, 2) are token-tax, not blockers, but fix them anyway. Note the count and the specific
fixes, then rewrite.

## Worked audit

> **Draft:** "Hey can you take a look at the auth stuff and see if there's anything off,
> would be great to clean it up when you get a chance."

- (1) Buried lede — no clear deliverable. (2) Ambiguity — "the auth stuff", "anything off",
  "clean it up". (3) Missing input — which files? (4) No bounds. (5) No output contract —
  "take a look" can't be graded. (6) Register — vague for any subordinate.
- **Score: 6/6 — hard block on 3 and 5.**

> **Rewrite:** **Order:** Audit `app/auth/` for the OWASP Top-10 and return the findings.
> **Intent:** We're hardening before launch; correctness over style nits.
> **Context:** Auth lives in `app/auth/`; RLS is on, sessions are JWT.
> **Constraints:** Review only — do not edit. Skip pure formatting.
> **Output contract:** A markdown table `file | line | OWASP-id | severity | fix`. If clean,
> say "no findings."

## The one-line test

If you cannot say in one sentence **what comes back and how you'll know it's right**, the
order has no output contract yet — that is the first thing to fix.
