---
name: code-review-craft
metadata:
  version: 1.1.1
type: Skill
description: A deliberate, member-invoked code review of a diff, PR, or file. Reviews four dimensions — correctness bugs, security, simplification and reuse, and efficiency — tags each finding by severity, holds one finding per line, and grounds every finding in evidence: the cited line and the concrete failure case. Refuses scope creep and nitpick noise. Use on "review this diff", "review my PR", "audit this file", "is this change safe", "look over my changes". Differs from the automatic verify-gate hook, which runs unbidden on Stop as a critic — this is the human-asked craft. Differs from bug-fix-workflow, which fixes a known reported bug, and from security-audit, which sweeps one risk dimension; this opens the lens across all four and ends in a review-then-verify loop.
---

# Code Review Craft

The craft of looking hard at code someone is about to ship — a diff, a PR, a single
file — and returning a small set of findings that are **true, located, and worth
acting on**. The reviewer is a second pair of eyes, not a linter and not a rubber
stamp. The goal is to catch the bug that would have shipped, the leak that would have
opened, the duplication that would have rotted — and to say nothing where there is
nothing to say.

## What it is

- A **deliberate, on-demand** review the member runs when asked: "review this diff",
  "review my PR", "audit this file", "is this change safe", "look over my changes".
- A review across **four dimensions** at once: correctness, security, simplification
  and reuse, efficiency. (See `references/review-dimensions.md`.)
- A discipline of **evidence**: every finding cites the exact line and names the
  concrete case where it breaks. (See `references/grounding-findings.md`.)
- A discipline of **restraint**: severity-tagged, one finding per line, scoped to the
  change. (See `references/severity-and-scope.md`.)

## What it is not

- **Not the verify-gate hook.** That critic (`.claude/hooks/verify-gate.py`) fires
  automatically on **Stop**, unbidden, on a turn that changed source. This craft is
  the opposite posture: a human asks for it. The two are complementary — the gate is
  the floor, this is the deliberate pass.
- **Not bug-fix-workflow.** That skill fixes a **known, reported** bug end to end
  (pull → reproduce → fix → close). This one hunts for **unknown** problems in code
  that is presumed working, and stops at findings — it does not fix unless asked.
- **Not a security-audit.** A security audit sweeps **one** risk dimension deeply.
  This opens **all four** lenses on a bounded change. Reach for the dedicated audit
  when security is the whole job.
- **Not a style police.** Formatting, naming taste, and import order are out of scope
  unless they change behavior or meaning.

This craft draws on the same review instinct as the `engineering:code-review` plugin —
correctness first, then reuse and simplification, calibrated to the effort asked for.

## Principles

### 1. Bugs first, then security, then simplification, then efficiency — in that order

The dimensions are not a flat checklist; they are a **priority stack**. A correctness
bug that corrupts data outranks a clever simplification; a leaked secret outranks a
redundant loop. Walk the diff once per dimension, top to bottom, and spend the most
attention where the blast radius is largest. If time is short, the lower dimensions are
the ones you drop — never correctness.

> *Example.* A PR adds caching to a request handler. The efficiency win is real, but
> the cache key omits the tenant id — a **correctness/security** finding (cross-tenant
> data bleed) that the efficiency improvement was hiding. Report the leak; the speedup
> is no longer the headline.

### 2. Ground every finding in evidence — a line and a failing case

A finding without a location is a vibe. State **where** (file:line) and **when it
breaks** (the concrete input, state, or sequence that triggers it). "This might have
an issue" is not a finding; "`parseAmount` at L42 returns `NaN` when the field is an
empty string, which then writes `NaN` to the ledger" is. If you cannot name the failing
case, you do not yet have a finding — you have a question; ask it as a question.

> *Example.* Weak: "Error handling looks fragile here." Grounded: "L88: the `await`
> is not wrapped, so a rejected `fetchUser` promise escapes the `try` and crashes the
> route — repro: call with a deleted user id."

### 3. One finding per line, severity-tagged

Each finding is a single line: `path:line — SEVERITY: problem. fix.` One issue per
line keeps the list scannable and the fixes atomic. Tag severity so the author triages:
**Critical** (data loss, security hole, crash on a common path), **High** (wrong result
in a real case), **Medium** (works but fragile or duplicated), **Low/Nit** (minor,
optional). Surface Critical and High first; never bury a data-loss bug under three
style nits. (See `references/severity-and-scope.md`.)

### 4. Stay in the diff — refuse scope creep and nitpick noise

Review **what changed**, plus exactly the surrounding code the change depends on or
breaks. Pre-existing debt outside the diff is not this review's job — note it once in a
single "out of scope" line and move on; do not rewrite the file. Likewise, drop
nitpicks that do not change behavior. A review that returns thirty findings, twenty-five
of them cosmetic, has failed: the author cannot find the two that matter. **Calibrate
volume to the effort asked** — a quick "is this safe?" wants the few high-confidence
findings; a thorough audit may surface uncertain ones, clearly flagged as uncertain.

> *Example.* A 12-line bugfix diff. Resist the urge to flag the file's unrelated 200
> lines of legacy formatting. One line: "Out of scope: this module predates the lint
> config; not reviewed." Then review the 12 lines.

### 5. Prefer reuse and deletion over addition

The best review finding is often "this already exists." Before accepting new code, ask
whether the codebase already has the helper, the constant, the component, the token.
Flag duplication and reinvention as simplification findings, and prefer the change that
**removes** code to the one that adds it. (Reuse a design-token constant; never bless a
hardcoded hex.) Simpler-and-smaller beats clever-and-larger.

> *Example.* "L30: this inlines a date-format that `utils/formatDate` already does —
> reuse it and drop the 9 lines."

### 6. Close the loop: review, then verify

A review is advice until its findings are confirmed. End with a **review-then-verify**
handoff: state which findings are certain (grounded by reading) versus which need a run
to confirm, and name the check that would settle each open one — the test to run, the
input to try, the query to inspect. For a Critical or High finding, prefer to actually
reproduce it rather than assert it. The review is done when its load-bearing claims are
either evidenced or explicitly marked "needs a run to confirm."

### 7. Ship complete output — no truncation, no placeholders

A review is worthless if the fix itself is a skeleton. When writing code or prose as part of a review fix:
- **Banned code patterns:** `// ...`, `// rest of code`, `// implement here`, bare `...` as omission, `// similar to above`
- **Banned prose patterns:** "for brevity, the rest follows the same pattern", "I'll leave that as an exercise"
- **At token limit:** pause at a clean breakpoint and end with `[PAUSED — X of Y complete. Send continue to resume from: <next section>]`. On continue, resume exactly — no recap.

## References

- `references/review-dimensions.md` — the four lenses (correctness, security,
  simplification/reuse, efficiency) and what to look for in each.
- `references/grounding-findings.md` — how to turn an observation into an evidenced
  finding; the finding line format; the review-then-verify handoff.
- `references/severity-and-scope.md` — the severity scale, scope boundaries, and how to
  calibrate finding volume to the effort requested.
- `references/security-owasp.md` — the OWASP Top-10 lens for the security dimension: a
  Top-10 mapping (A01 broken access, A03 injection, A06 vulnerable deps, …) plus
  copy-paste scan recipes (hardcoded-secret grep, direct-DB-vs-context-wrapper counts,
  missing-auth and SSRF sweeps, `npm audit --audit-level=high`).

## Changelog

- **1.1.0** — Added `references/security-owasp.md`: an OWASP Top-10 mapping and concrete
  scan recipes for the security dimension (hardcoded-credential grep, direct-DB-call vs
  context-wrapper counts, missing-auth and SSRF sweeps, dependency-vuln audit), with a
  pointer from the security dimension in `review-dimensions.md`. Adapted from the SAW
  security-audit playbook; closes the prior principle-only-no-checklist gap.
- **1.0.0** — Initial release: four-dimension on-demand review (correctness, security,
  simplification/reuse, efficiency) with evidence-grounded, severity-tagged, one-per-line
  findings and a review-then-verify close.
