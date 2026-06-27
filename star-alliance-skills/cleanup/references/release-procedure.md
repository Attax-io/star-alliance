---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Release procedure — phase 2 of cleanup `release` mode

This is the full version-bump recipe the `release` mode runs **after** the
hygiene gate (PR1–PR4) returns green. It was merged in from the retired
standalone `update-app-version` skill (cleanup v1.6.0, 2026-05-29). The
human-readable companion is `lex_council/docs/VERSION-RELEASE-WORKFLOW.md`
— keep the two in sync; when they disagree, **this file + that doc win over
any older copy**.

> The canonical version literal lives in `apps/web/config/app.config.ts`
> (`APP_CONFIG.version`). A SECOND, drift-prone mirror lives in
> `apps/web/package.json` (`"version"`). Treat app.config.ts as authoritative;
> sync-or-freeze package.json as a deliberate per-release call. `packages/*/package.json`
> are genuine `0.0.0` placeholders — never stamp them.

---

## Step R-1 — Confirm scope & classify the bump

Per `lex_council/docs/primary_instructions.md` §3, restate what you understood and confirm before editing:

- **Target version.** Usually the user provides it. If not, increment the **patch** segment by 1 (`1.7.26 → 1.7.27`). Never bump major/minor unless the user explicitly says so.
- **Date.** If unstated, use today's date `DD Month YYYY`. The same string goes in the version log `Date:`, the `INDEX.md` row, and any synced "Last updated" stamps.

```bash
cd lex_council && git status --short && git log --oneline -10
```

Classify into one of two flows:

- **Code-shipping bump** *(common)* — a recent `X.Y.Z perp commit` exists, or there are uncommitted code changes. The perp commit / vault-logs are the changelog source. → R-2 code-shipping flow.
- **Tag-only / docs-sync bump** *(uncommon)* — no new code since the last release shipped. → R-2 tag-only flow; the changelog is intentionally short.

If you can't tell, ask.

## Step R-2 — Compose the changelog

Plain-language readability is the goal — a non-coder should understand what changed.

**Code-shipping flow:**
1. `git show --stat <perp-commit-sha>` for surface area.
2. Read the dated vault-logs in `lex_council/docs/vault-logs/` between the previous release and now — they're authoritative and group into themes.
3. Group by **theme**, not commit (a release is usually 3–8 themes). One or two sentences per bullet, lead with a verb (Added / Changed / Removed / Fixed / Config), name concrete files/routes when it sharpens the bullet.
4. Avoid jargon-only bullets — pair any tag with a clause saying what shipped to a user.

**Tag-only flow** — short by design:
```markdown
## Changes
- **Config:** `apps/web/config/app.config.ts` — version bumped to `X.Y.Z`.
- **Docs:** version stamps synced across `ARCHITECTURE.md`, `Vault Core.md`, and `logs/INDEX.md`.

## Why
[1–2 honest sentences — "tag-only sync, no code changes" is fine if true.]
```

## Step R-3 — Bump the canonical version literal

```
lex_council/apps/web/config/app.config.ts
```
```ts
export const APP_CONFIG = {
  version: '1.7.X',           // ← change this string only
  appName: 'Lex Council',
  portalName: 'Admin Portal',
} as const
```

Increment the last segment by 1. `as const` narrows `version` to a literal, so the only strict-mode failure mode is a typo — re-read after editing.

Then decide the **package.json mirror**: either sync `apps/web/package.json` `"version"` to the new number or knowingly leave it frozen. Never read the app version from it; never assume it's correct.

## Step R-4 — Write the version log file

Create `lex_council/docs/logs/X.Y.Z.md` (housekeeper picks up files missing these three frontmatter keys — write them yourself):

```markdown
---
claude_hits: 0
housekeeper_passes: 0
last_housekeeper_pass: null
---

# Version X.Y.Z

**Date:** DD Month YYYY
**Previous version:** X.Y.(Z-1)

---

## Changes
- **Added:** …
- **Changed:** …
- **Fixed:** …
- **Removed:** …
- **Config:** `apps/web/config/app.config.ts` — version bumped to `X.Y.Z`.

## Why
[2–4 sentences. If a perp commit already shipped the code, say so — readers wonder why the bump commit is content-free.]
```

## Step R-5 — Sync every version stamp in the docs

This is the step the old workflow doc got wrong. The **current, verified (2026-05-29)** target list:

| File | What to update |
|---|---|
| `docs/logs/INDEX.md` | header line `> **Last updated:** DD Month YYYY · **App version:** X.Y.Z` (~line 11) **and** prepend a one-line row to the top of the version table |
| `docs/architecture/ARCHITECTURE.md` | `**Version:** X.Y.Z · **Date:** DD Month YYYY · **Stack:** …` (~line 34) |
| `docs/Vault Core.md` | **THREE stamps** — (1) frontmatter `app_version: X.Y.Z` (~line 6); (2) version-range link `… to [[X.Y.Z]]` (~line 173, only the upper bound moves; `1.6.11` stays); (3) footer `**App version:** X.Y.Z · **Last restructured:** 15 April 2026` (~line 191 — leave "Last restructured" alone) |

**Do NOT touch:**
- `docs/architecture/frontend/ZUSTAND-STORES.md` — **archived 2026-05-21** (`_archived/2026-05-21/`, frozen v1.7.4). No longer a target.
- `docs/INDEX.md` — deleted in the 2026-04-15 restructure; does not exist.
- `apps/web/package.json` — handled in R-3 as a deliberate call, not a blind sweep.
- `packages/*/package.json` — genuine `0.0.0` placeholders.
- `GETTING-STARTED.md` / `TESTING.md` / `TROUBLESHOOTING.md` / `architecture/*` sub-docs carrying their own `**App version:**` stamp — those are last-touched stamps (cold-doc-rotator, keyed off GETTING-STARTED), NOT the global app version.

> **Daemon race:** these docs are touched by a background housekeeper that bumps frontmatter between Read and Edit, so the Edit tool fails with "modified since read" on retry. Use an atomic Python read-modify-write (`open().read()` → `str.replace()` with a count==1 guard → `open('w').write()`) for these stamp edits, not chained Edit calls.

## Step R-6 — Verify, then output the git block

1. **Re-read every modified file** (`Read`, not memory).
2. **Grep the new version** across the stamp surfaces:
   ```bash
   cd lex_council && grep -rn "X.Y.Z" docs/Vault\ Core.md docs/logs/INDEX.md \
     docs/architecture/ARCHITECTURE.md apps/web/config/app.config.ts
   ```
   Expect ≥1 hit per file (Vault Core has three).
3. **Output a single copy-paste bash block and stop. Do NOT run `git push` yourself** unless the user says so. lex_council pushes to `origin/main` (`Attax-io/lex_council`); the workspace root has no remote.
   ```bash
   cd lex_council
   git add apps/web/config/app.config.ts \
           docs/logs/X.Y.Z.md \
           docs/logs/INDEX.md \
           docs/architecture/ARCHITECTURE.md \
           "docs/Vault Core.md"
   git commit -m "X.Y.Z: <one-line summary lifted from the version log's leading themes>"
   git push
   ```
   Add `apps/web/package.json` to the `git add` list only if you synced it in R-3.

## Optional — memory tier review

`VERSION-RELEASE-WORKFLOW.md` §5 asks for a `docs/memory/MEMORY-INDEX.md` tier-demotion review (T1→T2→T3 by `Last Hit` vs the previous version). Useful but slow — only run when the user asks. Offer it once at the end.

## Optional — vault log

A version-bump-only commit is borderline for P8 (the substantive changes were already vault-logged when they shipped, and `logs/X.Y.Z.md` is itself a changelog). Don't re-summarize the changelog in a vault log. If the user wants one for housekeeper reconciliation, keep it minimal (`type: version-bump`, the bumped file, the synced stamps, a pointer to `logs/X.Y.Z.md`).
