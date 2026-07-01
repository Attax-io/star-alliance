---
name: release-train
description: "The Quartermaster's craft for closing out a body of work — merge every outstanding branch and PR into main, bump the version, write the changelog, sync every version stamp across the docs, then push. Gather and merge branches/PRs resolving conflicts; bump the version (for the Lex Council app: apps/web/package.json, the docs/logs/X.Y.Z.md changelog, the INDEX.md row, and the stamps across ARCHITECTURE / ZUSTAND-STORES / Vault Core; for the guild itself the version is derived from the guild log, so logging the change is the bump); certify the build is clean and every stamp consistent; commit and push. Use to ship a release or merge-and-close outstanding work. Triggers: 'cut a release', 'merge all branches', 'ship it', 'bump the version and push', 'release X.Y.Z', 'close out the work', 'release train'. Differentiate from cleanup (hygiene) and guild-conformity (self-consistency proof)."
metadata:
  version: 1.1.0
type: Skill

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
   - **Lex Council app:** The SINGLE source of truth is `apps/web/package.json` (the `version:` field — currently 1.7.108). Edit it to the new `X.Y.Z`. Then sync that exact version into `apps/web/config/app.config.ts` (the display version, which must **always match** package.json). Write `docs/logs/X.Y.Z.md` (what changed, who shipped it, breaking notes). Prepend a row to `docs/logs/INDEX.md`. Sync the stamp across `docs/ARCHITECTURE.md`, `docs/ZUSTAND-STORES.md`, and the Vault Core files that cite the version.
   - **Guild itself:** `build.py` derives the version from the guild log. Writing the log entry *is* the bump. There is no `package.json`, no INDEX to prepend. A version shown anywhere is a **generated view** — the source file is the one truth (`tools/domain_version.py` reads it per domain id, wired into `build.py`'s `load_domains()`). Never hardcode a version except in its canonical source.
5. **Certify the build.** Run lint, type-check, unit tests, and the production build. *All green before the push.* A red build never leaves your hand.
6. **Verify every stamp.** Grep the version string across the repo. The count of occurrences and the version they cite must agree. If they drift, fix the drift before tagging.
7. **Commit, push, and merge to `main`.** Conventional message: `release: X.Y.Z`. Push the release branch; open the PR into `main`. Do not push to `main` directly.
8. **Tag the release.** Once `main` absorbs the branch, tag with the version (Lex Council) or with the cycle seal (guild). Push tags.
9. **Hand off.** Herald announces; Strategist files the next cycle; you log the train's run in the guild record.

## Modes

- **Lex Council app release** — manual bump via `package.json`, sync the exact version into `app.config.ts`, write changelog file and INDEX row, sync stamp across the named docs. Four file families must move in lockstep, with package.json as the single source.
- **Guild self-release** — `build.py` reads the guild log and derives the version. Writing the log entry performs the bump. Lighter on the stamp dance, heavier on the log discipline.

## Doctrine — versions are read live, never hardcoded

Every version shown on any surface — the dashboard, the app, a status line — is a **generated view** derived from its **source of truth** at build time. Nothing is hand-typed except the source files themselves.

**For any project, version is derived by replaying its append-only log:** count each log entry's `type:` field (if present) or use a heuristic from the filename (structure/reorganization → MAJOR, implementation/proposal → MINOR, else PATCH). Deterministic, order-independent, reproducible — same folder always yields the same version. Concrete: Lex Council Business derives `1.0.1` from 8 vault-log entries at "The Business/vault-logs/" by this rule.

**The Lex Council app:** source truth is `apps/web/package.json` ONLY. `apps/web/config/app.config.ts` is the display mirror — it must **always** match package.json exactly. When the version bumps, edit package.json first, then copy the exact same number into app.config.ts. Never let them diverge.

**The Star Alliance guild:** the project version shown on the dashboard (`GUILD.meta.version`, footer and brand mark) derives from `data/guild-log.json` via `build.py`. The version is not stored anywhere; it is computed. Logging the work (a `structure`, `skill-create`, or `skill-upgrade` entry) *is* the bump. There is no hand-edit of a version field because there is no such field — the log entry type **IS** the version change. The single source of truth for the major/minor/patch tiers is `build.py` itself (`VERSION_MAJOR_TYPES` / `VERSION_MINOR_TYPES`).

**Version history is computed, not stored in a second file.** "How it advanced" is emitted as a derived `versionHistory[]` on the domain object (in `guild-data.json`), never authored in a ledger. A second store drifts; the log (append-only, immutable) is the only durable record.

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
- **The version is the most-forgotten stamp.** Lex Council: five file families — package.json, app.config.ts (display mirror), changelog, INDEX, and the three docs that cite the version. Guild: the log entry itself. Miss any one and the seal is broken; consumers will read a version that does not match the code. **Never bump app.config.ts before package.json** — always edit the source first, then sync to the display.
- **`apps/web/package.json` is the single Lex App version source.** `app.config.ts` is a mirror and must always match exactly — when you bump one, bump the other in the same commit. The architecture discovery found version `1.7.108` canonical in package.json; app.config.ts mirrors it. Tools reading either location must be kept in sync or consumers see phantom version mismatches.
- **For the guild, the log *is* the version.** Forgetting to write the log entry is forgetting the bump. `build.py` will not save you — it will derive whatever the log says, including nothing.
- **Conflict resolution is a halt, not a hack.** Pause, pull the Architect in, and resolve with eyes open. Do not sweep it under `--force` or `--no-verify`; the next rider will find the bones.
- **Tag after merge, never before.** A tag on a branch that has not yet reached `main` points to work that can still disappear. The tag is the seal; the seal goes on the finished document.
- **Conventional commits keep the changelog honest.** Sloppy merge messages produce a sloppy changelog, and a sloppy changelog is a stamp that lies.
- **Commit scope is the task's own files.** When you finalize, stage only what the current task produced. Never sweep unrelated in-flight work into the commit — another session's edits, a half-done UI change, a plan doc awaiting approval. Auto-scope to the task's files and commit; do **not** ask the Guild Master to confirm the file set (it's settled standing policy). Surface the foreign changes you're leaving behind so their owner knows, but leave them out. Routine work finishes on `main`; branch only when the change touches the database / live data.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.1.0** — **Merge three version-reading lessons from the Architecture Build.**
  - (1) Read versions LIVE, never hardcode: a version shown anywhere is a generated view, the source file is the one truth. Pointer to `tools/domain_version.py` (the reader) and `build.py`'s `load_domains()`.
  - (2) Derive a version by replaying an append-only log, generalized beyond the guild: count each entry's `type:`, tier by heuristic (restructure→MAJOR, implementation→MINOR, else PATCH). Deterministic, reproducible, order-independent. Example: Lex Council Business derives `1.0.1` from 8 vault-logs.
  - (3) Version history is computed from the log, never stored in a second file: emitted as `versionHistory[]` in the generated domain object, never authored in a ledger (anti-drift principle).
  - (4) Verification finding: Lex Council App version is canonical in `apps/web/package.json` (currently `1.7.108`), NOT in app.config.ts. `app.config.ts` is the display mirror and must **always match** package.json exactly. Corrected the skill's instructions to name the true source and mandate sync-after-bump.
- **1.0.1** — Add the commit-scope rule (Gotchas): finalize by staging only the task's own files, never bundling unrelated in-flight work, and without asking the Guild Master to confirm scope.
- **1.0.0** — Initial release. The Quartermaster's release closeout — merge branches/PRs, bump version, stamp docs, push.
