---
type: Document
title: Evidence packaging and handoff
description: After a suite runs, emit a structured pass/coverage evidence block for the PR or tracker — Test Suite, totals, coverage, commands-run, output — and treat the pre-push ci:validate-style command as the gate that produced it.
timestamp: 2026-06-28T00:00:00Z
---

# Evidence packaging and handoff

A green run on your own machine is a claim, not proof. The handoff step — the one that
turns "I tested it" into something a reviewer can trust without re-running anything — is to
**emit a structured evidence block** alongside the change, generated from a real suite run,
and to gate the push on the same command that produced it.

This closes the loop the rest of the skill opens: you chose the layer, killed the flake,
and covered the contract — now you **package verifiable evidence** so the next person (a PR
reviewer, a tracker like Linear/Jira, a release gate) sees exactly what ran and what passed.

## Principle: evidence is a deliverable, not an afterthought

- The implementer must not be the only witness to the green. Attach the run's results to the
  PR/ticket so the verdict survives the context switch and can be audited later.
- Evidence is **generated, never hand-typed**. Copy the real test runner and coverage output;
  a block with made-up numbers is worse than none because it launders a guess as a fact.
- The **same command** that gates the push is the command whose output you paste. If
  `ci:validate` passes locally, that is the evidence; if it does not, there is nothing to hand
  off yet. Never package evidence from a partial or cherry-picked run.

## The evidence block

After the suite runs, emit this structured block into the PR description or the tracker
comment (Markdown). Fill every field from the real run; drop the coverage section only when
coverage was genuinely not collected.

```markdown
**Test Execution Evidence**

**Test Suite**: unit | integration | e2e | full
**Files Changed**: <list the source + test files this run covers>

**Test Results:**
- Total:   <N>
- Passed:  <N>
- Failed:  0
- Skipped: <N>   <!-- each skip needs a one-line reason or a ticket -->

**Coverage** (if collected):
- Statements: <X>%
- Branches:   <X>%
- Functions:  <X>%
- Lines:      <X>%

**Commands Run:**
\`\`\`bash
<the exact command(s), e.g. pnpm test:unit --coverage>
\`\`\`

**Output:**
\`\`\`
<paste the relevant runner summary — the pass/fail tally and the coverage table,
trimmed to what proves the claim, not the full scroll>
\`\`\`
```

Field discipline:

- **Failed must be 0** to hand off. A non-zero failure count is not evidence of success; fix
  or revert first. Do not package a run with known failures and a prose excuse.
- **Skipped is not free** — each skipped test is a hole in the net. List a reason or a ticket
  per skip, so a reviewer can tell an intentional `it.skip` from a silently dropped case.
- **Coverage is reported, not chased.** Paste the numbers as a flashlight on the gaps (see the
  coverage principle in SKILL.md); do not inflate them or treat a percentage as the pass bar.
- **Files Changed scopes the claim** — it tells the reviewer which behaviours this evidence
  speaks for, so they do not assume it vouches for untouched code.

## The pre-push gate

Wire a single composite command that runs the full local verification and **treat it as the
gate**: it must pass before the push, and its run is what produces the evidence above.

```bash
# the one command — same locally and in CI, no config drift
pnpm ci:validate        # (or yarn/npm) typically: typecheck + lint + unit + format-check
```

- Run it **before every push**, not just before opening the PR — a later commit can break a
  passing suite, and stale evidence is a lie.
- The gate command must be **identical locally and in CI** so "passes on my machine" cannot
  diverge from the merge check. CI re-runs it as the source of truth; the local run is your
  fast pre-flight.
- A green `ci:validate` is the precondition for the evidence block. Generate the block from
  *that* run's output — the gate and the evidence are two faces of one verification, not two
  separate chores.
- If the gate does not exist in the repo yet, add it as a package.json script that chains the
  checks, rather than asking each contributor to remember the list.

## Why this matters

Tests that no one can see the results of do not build trust; they build a private belief. The
evidence block plus the gate make the green **portable** — a reviewer, a tracker, and a future
debugger all read the same proof of what ran, on which files, with what coverage, from a
command they can re-run verbatim. That is the difference between "trust me" and "here is the
receipt."
