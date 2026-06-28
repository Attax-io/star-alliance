---
type: Document
title: Deploy and rollback
description: Status-before-deploy, deploy as forward-only, rollback as a first-class rehearsed move, and the release pipeline.
timestamp: 2026-06-28T00:00:00Z
---

# Deploy and rollback — the reversible-deploy discipline

Source: SAW `.claude/commands/` — remote-status, remote-deploy, remote-rollback, remote-logs,
test-pr-docker, release; `.claude/skills/deployment-sop`, `release-patterns`.

The governing idea: **a deploy is a state transition you must be able to reverse on demand.**
Every forward move (`remote-deploy`) has a defined inverse (`remote-rollback`), and the
inverse is treated as a normal operation — rehearsed, scripted, and reported — not an
emergency improvisation.

## remote-status — look before you leap (compare running vs. registry)

Never deploy blind. status compares the **commit SHA running in the container**
(`docker inspect … org.opencontainers.image.revision`) against the **latest built image** in
the registry / the latest commit on the integration branch, plus CI build state. Three
outcomes drive three different next actions:

- **SHAs match** → up-to-date, no action.
- **SHAs differ + build complete** → "ready to deploy", offer `remote-deploy`.
- **SHAs differ + build in progress / failed** → wait (show ETA) or fix CI first.

The principle: **a deploy is a diff between a known current state and a known target.** If you
cannot name both the running revision and the target revision, you are not ready to deploy.

## remote-deploy — forward, then prove it

deploy pulls the latest image, starts the (self-contained, no source-mount) staging compose,
**waits for the health check**, and reports the running revision + URL. Success is not "the
command returned" — success is a tri-condition:

- container running and **healthy**
- health endpoint returns **200**
- image revision **matches** the intended target commit

Failure modes have named first-responses: pull failed → check registry auth / disk; health
failed → read logs, check DB connection, **and `remote-rollback` is offered as the immediate
recovery.** The principle: **the deploy is not done until health proves it; an unproven
deploy is a pending rollback.**

## remote-rollback — the inverse, treated as first-class

This is the most detailed command in the pack, and that is the point: **rollback is designed,
not improvised.** Its shape:

1. **Assess** — capture the current (broken) revision and health, document the issue.
2. **Enumerate targets** — list recent images on the host, cross-referenced with `git log`
   commit messages so a human picks a *meaningful* target, not a bare SHA.
3. **Select** — argument = explicit commit SHA; no argument = recommend the last known stable
   (the image *before* current) and confirm.
4. **Back up first** — copy the compose file to a timestamped `.backup` before mutating it.
   The rollback is itself reversible.
5. **Pull → repoint → restart** — pull the target image, `sed` the compose tag to the pinned
   SHA (not `:latest`), restart, watch startup logs.
6. **Verify the inverse** — `docker ps`, health endpoint, and **confirm the running SHA is the
   target** (rollback gets the same proof-of-health a deploy gets).
7. **Document + prevent** — file a ticket for the broken version (logs, symptoms, what to test
   for next time), tag it, notify the team. Pin the rollback image until a verified fix exists.
8. **Restore-to-latest** — when fixed, `sed` the tag back to `:latest` and `remote-deploy`
   normally. The loop returns to its resting state.

Principles embedded here:

- **Back up before you mutate** — the recovery action must itself be recoverable.
- **Pin to a specific revision, never to `:latest`** during a rollback — you are deliberately
  leaving the moving target.
- **A rollback that is not verified healthy is not a rollback** — same proof gate as deploy.
- **Every rollback produces a prevention artifact** — the ticket that says how to detect this
  class of failure before the next deploy. A rollback without a postmortem will recur.

Note a deliberate variation across sources: `deployment-sop` describes a code-level rollback
(`git revert {sha}` → push → auto-redeploy), while `remote-rollback` does an image-tag
rollback (repoint compose to a prior built image). Both are valid; the *craft* (assess →
back up → revert to a known-good → prove health → document) is identical. The mechanism is
pluggable; the discipline is not. See `health-and-observability.md` for the proof step.

## release — the heavyweight, phase-gated forward move

`release` is deploy's big sibling: a full version cut, run in **strict phase order, no phase
skipped**, each phase reporting before the next begins:

1. **Pre-release validation** — clean tree, on the right branch, in sync with remote, all open
   PRs' CI green. BLOCKER on any.
2. **Merge open PRs** in dependency order; rebase dependents; wait for CI between merges.
3. **Version bump** — update only *active* version references (not historical changelog
   mentions), commit, push.
4. **Tag + GitHub Release** — annotated tag, release notes grouped by commit type
   (feat/fix/docs/chore), stats.
5. **Branch sync** — bring every long-lived branch into agreement; verify with empty
   `git log A..B` both directions.
6. **Cleanup** — delete merged PR branches (remote + local), prune, gc, final verification
   dump.

The principle: **a release is a pipeline of gated phases, not a single command.** Its success
criteria are checkable facts (tag on remote, release not-draft, branches in sync, zero stale
branches, clean tree) — the same "prove it" stance as a deploy, scaled up.

> A second deliberate variation: `release.md` squash-merges; `release-patterns` forbids squash
> in favor of rebase-only. The merge strategy is a project choice. What both insist on,
> identically: **ticket-referenced commits, CI-green before merge, and an independent review
> gate before the merge button.** Adopt the invariants; let each project pick the mechanics.
