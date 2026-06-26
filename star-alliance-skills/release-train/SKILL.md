---
name: release-train
description: "The Quartermaster's craft for closing out a body of work — merge every outstanding branch and PR into main, bump the version, write the changelog, sync every version stamp across the docs, then push. Gather and merge branches/PRs resolving conflicts; bump the version (for the Lex Council app: apps/web/config/app.config.ts, the docs/logs/X.Y.Z.md changelog, the INDEX.md row, and the stamps across ARCHITECTURE / ZUSTAND-STORES / Vault Core; for the guild itself the version is derived from the guild log, so logging the change is the bump); certify the build is clean and every stamp consistent; commit and push. Use to ship a release or merge-and-close outstanding work. Triggers: 'cut a release', 'merge all branches', 'ship it', 'bump the version and push', 'release X.Y.Z', 'close out the work', 'release train'. Differentiate from cleanup (hygiene) and guild-conformity (self-consistency proof)."
metadata:
  version: 1.0.0
---

# Release Train — the Quartermaster's craft

The release train is your march to the seal. You gather every loose branch and open PR, weld them into `main`, stamp the new version across every chronicle, and push the banner out. Done cleanly, the world sees an unbroken release; done carelessly, the next rider walks into a half-merged ruin. You are the one who ensures the seal holds.

## What it is / is not

- **Is:** closing out a body of work — the single coordinated push from working branch to `main`, with version, changelog, and stamp sync. A one-time event per cycle.
- **Is not:** `cleanup` — the hygiene sweep between cycles, dead-branch pruning, dead-code culling. Cleanup runs *between* trains; the train runs *on* the seal.
- **Is not:** `guild-conformity` — the proof that the repo is internally consistent. Conformity is a precondition the train assumes has been held; you do not re-prove it here.
- **Is not:** planning the next cycle. That belongs to the Strategist. You deliver this one and hand the field over.

## The craft

1. **Muster the field.** `git fetch --all --prune`; list every open PR and every branch with commits since the last tag. Note the merge order — feature branches first, then cross-cutting refactors, then docs.
2. **Cut a release branch from `main`.** Never stamp a version on a protected branch directly. Branch name: `release/X.Y.Z` for Lex Council, `release/<cycle-name>` for the guild.
3. **Merge in order.** Pull each PR or branch into the release branch. Resolve conflicts as they come; never `--force`, never `--no-verify`. If a conflict is structural, halt the train and call the Architect.
4. **Bump the version.**
   - **Lex Council app:** edit `apps/web/config/app.config.ts` to the new `X.Y.Z`. Write `docs/logs/X.Y.Z.md` (what changed, who shipped it, breaking notes). Prepend a row to `docs/logs/INDEX.md`. Sync the stamp across `docs/ARCHITECTURE.md`, `docs/ZUSTAND-STORES.md`, and the Vault Core files that cite the version.
   - **Guild itself:** `build.py` derives the version from the guild log. Writing the log entry *is* the bump. There is no `app.config.ts`, no INDEX to prepend.
5. **Certify the build.** Run lint, type-check, unit tests, and the production build. *All green before the push.* A red build never leaves your hand.
6. **Verify every stamp.** Grep the version string across the repo. The count of occurrences and the version they cite must agree. If they drift, fix the drift before tagging.
7. **Commit, push, and merge to `main`.** Conventional message: `release: X.Y.Z`. Push the release branch; open the PR into `main`. Do not push to `main` directly.
8. **Tag the release.** Once `main` absorbs the branch, tag with the version (Lex Council) or with the cycle seal (guild). Push tags.
9. **Hand off.** Herald announces; Strategist files the next cycle; you log the train's run in the guild record.

## Modes

- **Lex Council app release** — manual bump via `app.config.ts`, changelog file, INDEX row, and stamp sync across the named docs. Heavier mode; four file families must move in lockstep.
- **Guild self-release** — `build.py` reads the guild log and derives the version. Writing the log entry performs the bump. Lighter on the stamp dance, heavier on the log discipline.

## Sharpening the craft

- **Apprentice** — follows the steps mechanically, knows the file paths, can run the train on a clean cycle.
- **Journeyman** — catches a forgotten stamp before the push, learns the merge order from experience, reads the changelog aloud before committing.
- **Adept** — predicts stamp drift before it surfaces, orders merges to minimize conflict surface, holds the build green as a reflex rather than a check.
- **Master** — drives the train from a CI runbook; the manual checklist is a fallback for a release that genuinely needs human hands. The pace is steady; the seal is rarely broken.

**The gate rule binds you here.** Your thinker weapon plans the train — merge order, version number, stamp targets — and reviews the final diff. Your doer weapon executes the merges, writes the log, and pushes. Nothing ships unreviewed; a release is a sealed document, not a draft.

**Measure:** time-to-release, number of post-release hotfixes, stamp-drift count per release, number of red builds caught before push, ratio of first-pass clean merges to those needing rework.

**Failure modes to outgrow:** shipping a half-merged branch; forgetting the version bump and pushing a phantom release; pushing on a red build; skipping the changelog because "it's small"; tagging before `main` has absorbed the branch; force-pushing to escape a conflict that deserved a conversation.

## Gotchas

- **Protected `main`.** Always release branch, never direct push. The branch is your rollback handle — and your audit trail.
- **Build before push, not after.** If the build is red, the seal is not yet set. Hold the train; the remote is not a sandbox.
- **The version is the most-forgotten stamp.** Lex Council: four file families — config, changelog, INDEX, and the three docs that cite the version. Guild: the log entry itself. Miss any one and the seal is broken; consumers will read a version that does not match the code.
- **For the guild, the log *is* the version.** Forgetting to write the log entry is forgetting the bump. `build.py` will not save you — it will derive whatever the log says, including nothing.
- **Conflict resolution is a halt, not a hack.** Pause, pull the Architect in, and resolve with eyes open. Do not sweep it under `--force` or `--no-verify`; the next rider will find the bones.
- **Tag after merge, never before.** A tag on a branch that has not yet reached `main` points to work that can still disappear. The tag is the seal; the seal goes on the finished document.
- **Conventional commits keep the changelog honest.** Sloppy merge messages produce a sloppy changelog, and a sloppy changelog is a stamp that lies.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. The Quartermaster's release closeout — merge branches/PRs, bump version, stamp docs, push.
