---
type: Document
title: The dev-ops lifecycle loop
description: The start→work→pre-pr→deploy→health→rollback→retro loop and the gate at each checkpoint.
timestamp: 2026-06-28T00:00:00Z
---

# The dev-ops lifecycle loop

Source: SAW `.claude/commands/` — start-work, end-work, pre-pr, quick-fix, sync-linear,
update-docs, retro, audit-deps, test-pr-docker, release.

The pack is one loop, traversed once per unit of work:

```
start-work → (work) → update-docs → pre-pr → deploy → status/health → [rollback] → sync-linear → retro → end-work
```

Each station is a checkpoint that either lets you pass or stops the line. The craft is not
the individual commands — it is the **ordered traversal with a gate at every transition**.

## start-work — the entry gate (Stop-the-Line: AC/DoD)

Begin only when the work is well-defined. SAW's start-work enforces, in order:

1. **Ticket exists** — a tracked unit of work, not a vibe. Fetch it; confirm status.
2. **AC/DoD check (MANDATORY)** — the ticket must carry **Acceptance Criteria** or a
   **Definition of Done**. If missing or unclear: **STOP. Do not implement.** Route back
   to whoever owns scope. *"Dev agents are NOT responsible for inventing AC/DoD."* This is
   the single most important gate in the pack — it refuses to start work that has no
   definition of "done."
3. **Clean baseline** — start from latest integration branch (`git checkout dev && git pull`),
   no uncommitted changes.
4. **Named branch** — `PREFIX-{number}-{short-description}`, lowercase-hyphen, ticket-tagged.

The principle: **work that cannot be graded should not be started.** A gate at the front is
cheaper than a rollback at the back.

## pre-pr — the exit gate (validation suite + BLOCKERs)

Before a PR exists, run the full validation suite. SAW marks each step PASS / WARNING /
BLOCKER. **BLOCKERs must be fixed; the line does not move past them.** The canonical steps:

1. **CI validate** — type-check + lint + unit tests + format. BLOCKER on any failure.
2. **Docs lint** — auto-fix then verify (`lint:md:fix`, then `lint:md`).
3. **Clean tree** — no uncommitted changes. BLOCKER.
4. **Rebase onto latest integration branch** — `git fetch && git rebase origin/dev`. BLOCKER
   if behind.
5. **Commit-message format** — every commit references the ticket: `type(scope): desc [PREFIX-XXX]`.
   BLOCKER if any commit is unreferenced.
6. **Docs updated in the same PR** — architecture/process/feature docs that the change touched.
7. **PR template fillable** — if you cannot fill every section (summary, changes, testing,
   impact, checklist), the work is not ready.

The principle: **the implementer runs the suite before asking for review, not the reviewer.**
The gate is mechanical (a command that passes or fails), not a matter of opinion.

## quick-fix — the same loop, compressed (never bypassed)

For small, urgent, isolated fixes (< ~50 lines, no architecture change, existing coverage
adequate), SAW offers a fast lane. What it **speeds up**: skip integration/E2E/build when
time-critical; use a minimal PR template; defer non-urgent docs. What it **never skips** —
the safety floor stays armed:

- commit-message format and ticket reference
- branch naming
- TypeScript + lint pass

And it **re-attaches the deferred gates after merge**: run the full suite, finish docs,
verify in production, close the ticket. The principle: **a fast lane shortens the loop; it
does not delete the gates.** Speed is bought by deferral, never by skipping the safety floor.

## sync-linear / update-docs — keeping the world consistent with the work

Two "consistency" stations that run continuously, not just at the end:

- **sync-linear** maps work state → ticket state (Todo → In Progress → Ready for Review →
  In Review → Done/Blocked), derived from real signal (`git log origin/dev..HEAD`,
  `git diff --stat`), and posts a progress comment. Sync **daily, before standup, on major
  progress, on block, on PR transitions.** The tracker is the single source of truth for
  status — it must never lag the code.
- **update-docs** treats documentation as part of the change, not a follow-up: `git diff
  origin/dev --name-only` → categorize → update the affected docs **inside the same PR** →
  lint. *"Always update docs related to the work we are doing within the PR."*

The principle: **status and docs are outputs of the work, produced in-loop — drift between
code, tracker, and docs is a defect, not a chore.**

## retro / end-work — closing the loop

- **retro** is structured reflection on the session: what worked, what to improve, process
  insights (when to delegate vs. do it yourself), metrics, wins. It is the REMEMBER step of
  the loop — non-trivial work is not done until it has produced a learning.
- **end-work** is the clean-exit checklist: commit everything (or document a safe stopping
  point), confirm docs current, update the ticket, **preserve context** (completed / next /
  decisions / blockers / questions) so a cold session resumes smoothly.

The principle: **a session ends in one of two states only — clean (nothing uncommitted, work
complete) or safely-parked (a documented stopping point a future session can resume).** There
is no third "left it in the air" state.

## audit-deps / test-pr-docker — periodic and pre-trust gates

- **audit-deps** is a scheduled hygiene sweep (security `audit`, bundle analysis, `depcheck`
  for unused/missing deps, `outdated`), writing a dated report and filing tickets for each
  finding. Cadence: monthly quick / quarterly full / before major releases / after upgrades.
- **test-pr-docker** validates the deploy *mechanism itself* before you trust it: label a PR
  to trigger an image build, pull the `pr-{n}` image on the target, run it, health-check it.
  The principle: **rehearse the deployment path on a throwaway artifact before you depend on
  it for real releases.**
