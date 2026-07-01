---
name: guild-log
description: "Enforce logging of non-git-visible changes to the Star Alliance guild log. Use this skill whenever a session has changed dashboard markup, renamed UI strings, edited skills-meta.json or members-meta.json, modified guild-log.json directly, reorganized star-alliance-members/ or star-alliance-skills/ folder layout, or made any visual/structural change that won't show up in a git diff as a version bump. Also use when the user says 'log this', 'guild log this', 'did you log it?', 'add a log entry', or any time work ends and it's unclear whether the change was git-visible. Skill audits what was touched, decides auto-derived vs manual logging, runs build_guild_log.py for git-visible changes and log_event.py for the rest, then rebuilds the dashboard via build.py. Ask Atta to confirm before writing."
metadata:
  version: 1.3.0
type: Skill

---
# Guild Log Compliance

The Star Alliance guild log (`guild-log.json`, surfaced through the generated `guild-data.js` that `index.html` loads as `GUILD.log`) is the canonical history of changes across the guild. **If a change isn't logged, the Guild Log view on the dashboard silently misses it** — and future readers (including the agent on the next session) lose the trail.

The logging pipeline has two tiers:

1. **`build_guild_log.py`** — auto-derives entries from git history. Catches: `skill-upgrade` (metadata.version bumps), `member-upgrade` (agent `.md` changes), `skill-create`/`skill-remove`, `member-create`/`member-remove`. Idempotent, deduplicates by commit hash.
2. **`log_event.py`** — manual entries for everything git can't see: dashboard redesigns, UI renames, copy edits, structural reorganizations, folder moves, anything that isn't a version bump.

This skill's job is to ensure **every session that touched the dashboard, the log files directly, or the folder layout leaves a covering entry** in `guild-log.json`.

## Portability (binding)

The guild log ALWAYS lives in the star-alliance repo (data/guild-log.json), no matter which project the guild is deployed into via the MCP server. Never run the bare 'python3 build_guild_log.py' form — it only works when the terminal is inside the star-alliance repo. Always invoke through the portable wrapper, which self-locates the repo from any current directory:

```bash
python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py build
python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py event --type chore --title '...' --who the-quartermaster
python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py rebuild
```

The STAR_ALLIANCE_ROOT env var is set by each host project's .claude/settings.json. If it is unset, the wrapper still self-locates via its own file path and by walking up for VERSIONS.md plus .git.

## When this skill applies

Applies when **any** of the following happened in the current session:

- A dashboard file was edited (`index.html`, `app.css`, `app.js`, `skills-meta.json`, `members-meta.json`, `guild-data.js`).
- A UI string was renamed (sidebar nav, page title, button label, class/id names — anything user-visible).
- The repo layout changed (folder moves, file renames inside `star-alliance-members/` or `star-alliance-skills/`).
- `guild-log.json` was edited directly without going through `log_event.py` or `build_guild_log.py`.
- A skill was created or removed **without** a version bump (rare — most skill changes are version bumps and auto-logged).
- The user explicitly requested logging ("log this", "guild log this", "did you log it?", "add a log entry").
- The session ended and it's unclear whether any change was git-visible.

Does **not** apply when:

- Only skill/member version bumps happened — those are auto-derived by `build_guild_log.py` (still run that script, but no manual entry needed).
- Only `.md` documentation files in the repo root were touched (`README.md`, `VERSIONS.md`) — those have their own change-tracking semantics.
- The session only read files / ran queries without changing anything.
- A matching log entry already exists for today covering the same surface (extend the existing entry instead of creating a duplicate).

## The two-tier logging pipeline

### Tier 1 — `build_guild_log.py` (auto-derived from git)

Scans commit history, synthesizes entries automatically. **Always run this first** — it picks up everything git-visible and is idempotent.

```bash
python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py build            # rebuild guild-log.json from git
python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py build --dry-run  # preview only
```

Detects:
- `skill-upgrade` when `metadata.version` changed in a SKILL.md
- `member-upgrade` when an agent `.md` file changed
- `skill-create`/`skill-remove` when skill directories appear/disappear
- `member-create`/`member-remove` when agent files appear/disappear

Skips commits that already have a matching hand-edited entry (matched by commit hash) — never double-logs.

### Tier 2 — `log_event.py` (manual, for what git can't see)

For changes that **don't show up as a version bump or member file diff**: dashboard redesigns, UI renames, copy edits, structural reorganizations. **Run this AFTER Tier 1**, for the gaps Tier 1 left.

```bash
python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py event \
  --type dashboard \
  --title "Renamed sidebar nav: Roster → Members" \
  --detail "Full internal sweep — function names, variable names, CSS class, data-view attribute, page-load invocation, and historical log entries all updated." \
  --who Atta \
  --ref the-butler
```

**Valid `--type` values** (from `log_event.py::VALID_TYPES`):

| Type | When |
|---|---|
| `skill-upgrade` | A skill's `metadata.version` was bumped (prefer Tier 1) |
| `skill-create` | A new skill was added to `star-alliance-skills/` (prefer Tier 1) |
| `skill-remove` | A skill was removed (prefer Tier 1) |
| `member-upgrade` | A member's prompt or skills list was updated (prefer Tier 1) |
| `member-create` | A new agent file was added to `star-alliance-members/` (prefer Tier 1) |
| `member-remove` | An agent file was removed (prefer Tier 1) |
| `workflow` | A new star-map workflow was added to `workflows.json` (bumps MINOR, like `dashboard`) |
| `dashboard` | Visual / structural change to the dashboard |
| `structure` | Repo reorganisation (folder moves, renames) |
| `chore` | Anything else worth logging |
| `decision` | A choice made + **why** — kept as a record for future runs, not a change to the project. Use `--title` for the decision, `--detail` for the rationale and the alternative(s) rejected. Does **not** bump the project version. |

**Log decisions, not only changes.** When the guild settles a real choice — picks an
approach, rejects an alternative, fixes a trade-off, sets a convention — record it as a
`decision` so the next run reads it instead of relitigating settled ground. It is the
guild's memory. Example:

```bash
python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py event \
  --type decision \
  --who the-quartermaster \
  --title "Project version derives from the guild log, not a hand-edited field" \
  --detail "Considered a manual version field in guild-log.json; rejected — it drifts and gets forgotten. Deriving from log entry types in build.py means logging any change pumps the version automatically. Cumulative + order-independent so builds are reproducible." \
  --ref guild-log
```

The script auto-stamps `date` to today (YYYY-MM-DD), assigns the next `id` (via `next_id()`), and preserves all existing entries — never overwrites.

## Workflow

### Step 1 — Enumerate what changed

Compile a list of the work done in this session:

1. Run `git status` and `git diff --stat` to see modified/new files.
2. Note which dashboard files were touched (HTML, meta, data, log files).
3. Note any renames (UI strings, file paths, identifiers).
4. Note any folder reorganization (moves inside `star-alliance-members/` or `star-alliance-skills/`).

Produce a short structured list: what was created, modified, renamed, or removed, with file paths / surface names and a one-line reason.

### Step 2 — Classify each change

For each item, ask: **"Is this git-visible to `build_guild_log.py`?"**

- ✅ Version bump in a SKILL.md → Tier 1 (`skill-upgrade`)
- ✅ Agent file edit → Tier 1 (`member-upgrade`)
- ✅ Skill directory added/removed → Tier 1 (`skill-create`/`skill-remove`)
- ✅ Agent file added/removed → Tier 1 (`member-create`/`member-remove`)
- ❌ Dashboard HTML/CSS/JS edit → Tier 2 (`dashboard`)
- ❌ UI string rename → Tier 2 (`dashboard`)
- ❌ Folder reorganization → Tier 2 (`structure`)
- ❌ `guild-log.json` edited directly → Tier 2 (`chore`)
- ❌ Copy edit, color tweak, asset change → Tier 2 (`dashboard` or `chore`)

**If even one item needs Tier 2**, this skill applies. Items that need Tier 1 alone are auto-handled — running `build_guild_log.py` is sufficient.

### Step 3 — Run Tier 1

```bash
python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py build
```

This catches every git-visible change. Skip if you already ran it earlier in the session and nothing new was committed since.

### Step 4 — Run Tier 2 for each non-git-visible change

For each item from Step 2 that needs Tier 2:

```bash
python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py event \
  --type <dashboard|structure|chore> \
  --title "<one-line headline>" \
  --detail "<longer description, optional>" \
  --who "<Atta | member-name>" \
  --ref <related-skill-or-member>  # repeatable
```

Pick `--type` from the valid set. `--ref` is for cross-linking: which skill or member this change touches (use the slug like `the-butler`, `skillsmith`, `vault-log-compliance`).

**Title discipline:**
- Active voice, past tense ("Renamed sidebar nav", "Reorganised folder layout")
- ≤ 80 characters
- Describes the outcome, not the process
- One change per entry — don't bundle unrelated edits

**Detail discipline:**
- Explain what was changed and why
- Name the specific files/surfaces touched
- For renames: list before → after for each renamed thing
- For bugs: include the symptom, root cause, and fix

### Step 5 — Rebuild the dashboard data

The dashboard loads one generated file, `guild-data.js` (`const GUILD = { meta, members, skills, domains, log }`), built from `guild-log.json` plus the skill/agent/meta sources by `build.py`. **Always run this after Step 3 and Step 4** so the dashboard's Guild Log view shows the new entries.

```bash
python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py rebuild
```

The same command also refreshes the skills, members, and domains in `guild-data.js`. Safe to run any time; `build.py --check` reports whether content actually changed.

**This is also how the project version bumps.** `build.py` derives `GUILD.meta.version` (the one SemVer for the whole Star Alliance, shown on the dashboard brand + footer) from the guild log: each entry's `type` bumps a tier — `structure`→MAJOR, `skill-create`/`member-create`/`dashboard`/`workflow`→MINOR, everything else→PATCH. So logging the change in Step 3/4 and rebuilding here *is* the version pump — there is no separate number to hand-edit. (The tier map lives in `VERSION_MAJOR_TYPES` / `VERSION_MINOR_TYPES` in `build.py`.)

### Step 6 — Verify

1. Read the first 20 lines of `guild-log.json` — confirm your new entry is at the top with the expected `id`, `type`, `title`.
2. Run `python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py rebuild` and confirm the entry now appears in `guild-data.json` under `log.entries` (the JSON mirror of `guild-data.js`).
3. (Optional) Open `index.html` in a browser, click **Guild Log** in the nav, confirm the entry renders.

## Common pitfalls

### Forgetting to hide sibling views in a multi-view dashboard
**Symptom:** A new view (e.g. `logView`) gets added to the HTML alongside existing views, but the existing `show*()` functions aren't updated to hide the new one. Users see the new view "leak" into other views after navigation — once they click the new view, switching to any old view leaves it rendered below. **Why it matters:** this is a real class of bug, not a one-off. Every dashboard view-swap function must hide ALL sibling views, not just the two it directly replaces. **Fix (prevention):** when adding a new view, audit every existing `show*()` function — every one must include `document.getElementById('<newView>').style.display='none'`. When adding a new view, treat it like adding a column to a database — every existing function needs updating, not just the new one. **Fix (detection):** after any view-related change, run a flow test: navigate to view A → view B → view A, and verify with `getComputedStyle().display` that exactly one view is visible at a time.

### Forgetting Tier 2 after a UI rename
**Symptom:** Renamed "Roster" → "Members" across `index.html`, only the sidebar nav was changed, the page load throws `ReferenceError`, you fix it, ship it — no log entry exists. **The lesson (M1):** UI string renames are NEVER git-visible to `build_guild_log.py` — they don't bump a version, they don't add/remove files. Always run `log_event.py --type dashboard` after.

### Bundling unrelated changes into one entry
**Symptom:** One log entry covers a UI rename + a folder reorganization + a copy edit. **Why it's bad:** the entry becomes hard to scan, and future "find when X happened" queries miss the actual change date. **Fix:** one entry per coherent unit of change. The threshold is "could you undo this change without affecting the other items in the entry?"

### Editing `guild-log.json` directly
**Symptom:** Hand-edited `guild-log.json` to add an entry. **Why it's bad:** the manual entry collides with `next_id()` (Tier 2 auto-stamps `id`; hand-edits can clash). Also bypasses the canonical schema — typos and missing fields slip in. **Fix:** always use `log_event.py` for manual entries. Reserve hand-edits for fixing genuine bugs in the file.

### Editing `guild-data.js` directly
**Symptom:** Hand-edited `guild-data.js` to add an entry. **Why it's bad:** it's auto-generated by `build.py` from `guild-log.json` + the skill/agent sources — your hand-edit gets clobbered on the next build. The header even says "do not edit by hand." **Fix:** edit `guild-log.json` via `log_event.py`, then run `build.py`.

### Skipping `build.py` after Step 4
**Symptom:** Logged the change in `guild-log.json`, but the dashboard's Guild Log view doesn't show it. **Why:** `guild-data.js` is the file the HTML actually loads — it's a snapshot, not a live read. **Fix:** always run `python3 build.py` after Step 4.

### `log_event.py` crashes with `KeyError: 'id'`
**Symptom:** `KeyError: 'id'` from `next_id()` when entries from Tier 1 (which lack an `id` field, only `_derived: true`) are already in the log. **Why:** the original `next_id()` generator expression didn't filter out auto-derived entries. **Fix:** the canonical `log_event.py` in this repo's `next_id()` already guards with `if "id" in e`. If you forked or vendored an older copy, patch it.

### Forgetting the `--ref` flag
**Symptom:** Logged a dashboard change with no `--ref`, so the Guild Log entry isn't cross-linked to the relevant member (e.g. the Butler). **Why it matters:** the dashboard renders `ref` chips next to each log entry — without them, the entry looks orphaned. **Fix:** pass `--ref <member-or-skill-slug>` for every entry that touches a named surface. Repeatable.

## Verification checklist

- [ ] Step 1 enumerated all changes (git status read; changes categorized)
- [ ] Step 2 classified each change as Tier 1 or Tier 2
- [ ] Step 3 ran `build_guild_log.py` (idempotent — safe to re-run)
- [ ] Step 4 ran `log_event.py` for each Tier 2 change with `--type`, `--title`, optional `--detail`/`--ref`/`--who`
- [ ] Step 5 ran `python3 $STAR_ALLIANCE_ROOT/tools/guild_log.py rebuild` to regenerate `guild-data.js` (+ its `guild-data.json` mirror)
- [ ] Step 6 read back `guild-log.json` AND confirmed `guild-data.json`'s `log.entries` reflects the new entry after the rebuild
- [ ] Each Tier 2 entry's title is ≤ 80 chars, active voice, past tense
- [ ] Each Tier 2 entry's detail names the specific files/surfaces touched

## Related

- `build_guild_log.py` (Tier 1 — auto-derives from git)
- `log_event.py` (Tier 2 — manual entries)
- `build.py` (regenerates `guild-data.js` — the single `const GUILD` file — from all sources)
- `VERSIONS.md` (skill registry — bump and re-register this skill on version change)
- `vault-log-compliance` (sister skill — covers Lex Council's wikilinked vault-logs in Obsidian; the two systems are intentionally separate)
- `skillsmith` (runs the `quick_validate.py` Cowork compliance check on every skill — re-run after editing this SKILL.md to confirm the description stays ≤ 1024 chars and the body stays < 500 lines)

## Changelog

| Version | Date | Summary |
|---|---|---|
| **1.3.0** | 2026-07-01 | Portability: every command block now invokes the new portable wrapper tools/guild_log.py (build / event / rebuild) via $STAR_ALLIANCE_ROOT so the skill works from ANY project cwd when the guild is deployed via the MCP server, not only inside the star-alliance repo. Added the Portability (binding) section. Scripts now also honor the STAR_ALLIANCE_ROOT env name. |
| **1.2.1** | 2026-06-26 | Body-consistency fix (skillsmith routine STORM): the 1.2.0 bump shipped the `workflow` log type (in `log_event.py::VALID_TYPES` + `build.py::VERSION_MINOR_TYPES`) and the `decision` type but left the SKILL.md half-documented — added the missing `workflow` row to the valid-`--type` table, and backfilled the missing **1.2.0** changelog row below. |
| **1.2.0** | 2026-06-26 | Added the `decision` log type (record a choice + **why**, version-neutral via `VERSION_IGNORE_TYPES`) and the "Log decisions, not only changes" guidance, plus the `workflow` log type for new star-map workflows (bumps MINOR like `dashboard`). Shipped alongside the project's decision-logging + Butler report-back standard. |
| **1.1.0** | 2026-06-25 | Repointed the pipeline to the rebuilt dashboard: the four generated globals (`skills-data.js`/`members.js`/`domains.js`/`guild-log.js`) and `guild-dashboard.html` were consolidated into a single `guild-data.js` (`const GUILD`) built by `build.py` and loaded by `index.html`/`app.css`/`app.js`. Updated every reference (Step 5 rebuild, the "editing the generated file" pitfall, the verify steps, the checklist, Related), and the trigger list (`skills-meta.json`/`members-meta.json` replace `dashboard-meta.json`; `guild-log.js` no longer exists). |
| **1.0.0** | 2026-06-24 | Initial release. Codifies the two-tier pipeline (`build_guild_log.py` for git-visible changes, `log_event.py` for the rest) as a single enforcement skill, defines the end-to-end workflow (enumerate → classify → Tier 1 → Tier 2 → rebuild → verify), and ships seven named pitfalls drawn from real misses in the rename + dashboard work earlier this session. |