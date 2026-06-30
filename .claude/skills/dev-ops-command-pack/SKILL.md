---
name: dev-ops-command-pack
description: "Run a disciplined dev-ops command lifecycle as one gated loop: start work, validate before PR, deploy, prove health, roll back, and retro. Each transition is a checkpoint that can stop the line. Triggers: 'start work on this', 'pre-pr check', 'deploy this', 'roll back the deploy', 'health check the service', 'run a retro', 'cut a release'. Covers the entry AC/DoD gate, the pre-PR validation suite, status-before-deploy, post-deploy health proof, first-class rehearsed rollback, dev-vs-remote command symmetry, and release phases. Differs from release-train (single version-cut pipeline), dev-server (just running the app locally), and performance (profiling/optimization) — this is the full start-to-retro operational loop and the safety gates between its stations."
metadata:
  version: 1.0.0
type: Skill
---

# dev-ops Command Pack

A disciplined operational lifecycle for shipping software, distilled from the Safe Agentic
Workflow (SAW) command suite. The pack is **one loop with a gate at every transition** —
start-work → work → pre-pr → deploy → health → (rollback if needed) → retro → end-work — plus
the periodic and heavyweight moves (audit-deps, release) that hang off it.

The craft here is not any single command. It is the **ordered traversal**: each station
either lets you pass or stops the line, and every forward move has a defined, rehearsed
inverse. Adopt the discipline; the exact tooling (yarn vs. npm, Docker vs. bare, Linear vs.
Jira, squash vs. rebase) is pluggable underneath it.

## What it is

- A **gated lifecycle**: entry gate (AC/DoD), exit gate (pre-PR validation suite), deploy gate
  (status-before, health-after), and a closing reflection (retro/end-work).
- A **reversibility doctrine**: deploy and rollback are symmetric; rollback is designed and
  rehearsed, not improvised, and always produces a prevention artifact.
- A **consistency habit**: tracker status and docs are produced in-loop, never lagging the code.
- A **vocabulary**: one canonical name per operation, with `local-*` / `remote-*` symmetry and
  documented aliases.

## What it is not

- **Not release-train** — that's the single version-cut/publish pipeline. This pack *contains*
  a release station but is the whole start-to-retro loop around it.
- **Not dev-server** — that just launches the app locally. This is the ship-and-operate loop.
- **Not performance** — no profiling or optimization here; this is process and safety, not speed.
- **Not a literal command set to copy** — the SAW commands are templates full of placeholders.
  Distill the gates and the loop shape into whatever harness the project already uses.

## Generative principles

1. **Work that cannot be graded should not be started.** The entry gate is AC/DoD: if a unit
   of work has no Acceptance Criteria or Definition of Done, STOP and route it back — do not
   invent the spec yourself. A gate at the front is cheaper than a rollback at the back.

2. **The implementer runs the suite before asking for review.** pre-pr is a mechanical pass/
   fail (type-check, lint, tests, clean tree, rebased, ticket-referenced commits, docs in the
   same PR), with BLOCKERs that genuinely block. Review grades judgment, not whether the build
   compiles. *(Star Alliance parallel: the verify-gate / independent critic — never let the
   implementer grade its own work.)*

3. **Never deploy blind; never trust an unproven deploy.** Status first: name the running
   revision and the target revision — a deploy is a diff between two known states. Health
   after: container healthy + endpoint 200 + revision matches + dependencies live + disk has
   room. "The command returned" is not success; proof-of-health is.

4. **Every forward move has a rehearsed inverse.** Rollback is first-class: assess, back up the
   config before mutating it, pick a *meaningful* prior revision (cross-referenced with commit
   messages), pin to that specific SHA, restart, prove health with the same gate a deploy uses,
   then file a prevention ticket. A rollback without a postmortem will recur.

5. **A fast lane shortens the loop; it never deletes the gates.** quick-fix may defer
   integration tests and full docs under time pressure, but the safety floor (commit format,
   branch naming, type-check + lint) stays armed, and the deferred gates re-attach after merge.
   Speed is bought by deferral, never by skipping.

6. **Status and docs are outputs of the work, produced in-loop.** Drift between code, tracker,
   and documentation is a defect, not a chore. sync-linear maps real git signal to ticket
   state; update-docs lands in the same PR as the change that needs it.

7. **One canonical verb per operation; collapse parallel families to aliases.** Keep a single
   `local-*` / `remote-*` vocabulary, prefer the stable staging target, and turn duplicate
   command families into documented aliases of one canonical command. Two names for one
   behavior is drift waiting to happen.

8. **Anyone may stop the line.** FORBIDDEN/REQUIRED pairs are shared doctrine: no deploy on red
   CI, no skipped smoke tests on production, no untested migrations, staging-validates-before-
   production, a rollback plan documented *before* a production deploy. Stopping a bad deploy is
   the gate doing its job.

9. **Close the loop.** Non-trivial work isn't done when it ships — it's done after retro
   produces a learning and end-work leaves the session in one of two states only: clean, or a
   documented safe-park a cold session can resume.

## References

- `references/lifecycle-loop.md` — the full station-by-station loop: start-work's AC/DoD gate,
  the pre-pr validation suite, quick-fix's compressed-but-armed lane, sync-linear/update-docs
  consistency, retro/end-work closure, and the periodic audit-deps / test-pr-docker gates.
- `references/deploy-and-rollback.md` — status-before-deploy, deploy-then-prove, the first-class
  rollback procedure (back up → pin → restart → prove → prevent), the phase-gated release
  pipeline, and the deliberate mechanism variations across SAW's sources.
- `references/health-and-observability.md` — the scored multi-signal health dashboard, smoke
  tests + deployment evidence, log triage, dev-vs-remote canonical naming/symmetry, and the
  Stop-the-Line FORBIDDEN/REQUIRED doctrine.
