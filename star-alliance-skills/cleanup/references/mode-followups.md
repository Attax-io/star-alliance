---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Mode: followups — full recipe

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/followups_cleanup.py <locate|extract|classify|mark>` — automates locate→extract→classify (+ mark). EXECUTION of the doable items (F4) is Claude's job, not the script.

After a campaign closes, the campaign's `99-risk-sweep.md` (build mode)
or `99-synthesis.md` (audit mode) typically lists 5–10 deferred
follow-up items. The 2026-05-28 solar-system doc-sync audit shipped 8
follow-ups; 5 doable autonomously + 3 needing user hands. Without a
codified pattern, these get handled ad-hoc (each as a one-shot turn)
or silently dropped. This mode codifies the sweep.

> **Auto-spawned by `conquering-campaign` at campaign close** (its v3.3.0 §5.7 calls `spawn_task` → a fresh session/worktree runs `/cleanup followups` with the campaign's `99-risk-sweep.md` ## Open items + touched-surface list inlined in the prompt). So this mode often runs in a session the campaign kicked off — no manual invoke. If that spawn was skipped (Cowork/headless) or the chip dismissed, nothing is lost: the committed `99-risk-sweep.md` is still the durable queue F1 locates (most-recent `status: completed`).

#### Step F1 — Locate the campaign

```bash
# Most recent campaign with status: completed
find lex_council/docs/{audit,build}-campaigns -name "00-campaign-plan.md" \
  -newer /tmp/last_cleanup_marker 2>/dev/null \
  | xargs grep -l "status: completed"
```

If the user invoked `/cleanup followups` with a specific campaign name,
use that; otherwise default to "the most recently-closed campaign whose
follow-ups haven't been swept yet" (track via `/tmp/last_followup_sweep_marker`).

#### Step F2 — Extract follow-up items

Grep the campaign's W4 artifact for the standard markers:

```bash
# Audit mode: 99-synthesis.md "## Code cleanup checklist" + "## Open items"
# Build mode: 99-risk-sweep.md "## Open items" + per-phase "deferred to" mentions
# Vault-log: search for "follow-up", "spawn_task", "future cleanup", "Atta to dispatch"
```

Produce a per-item list with `{ id, surface, description, blocker_hint }`.

#### Step F3 — Classify each item

For each item, decide:

| Class | Examples | Action |
|---|---|---|
| **doable-autonomously** | small code edits, MCP-doable DB checks, `git rm` of confirmed-orphan files, frontmatter sync, RLS verification queries | Do now under autonomous cadence |
| **needs-user-hands** | external dashboard clicks (Supabase delete edge fn, NAS scripts, third-party API config), `[!atta]` block edits, security gates the user explicitly reserved | Surface as checklist; user dispatches |
| **accepted-permanent-exception** | items the user has previously marked as "leave as-is" (cite the prior decision) | Note in followups file; don't surface as actionable |

The classification rubric is empirical — when in doubt, surface as
needs-user-hands. Misclassifying a doable item as needing-hands is
cheap (user can say "do it"); misclassifying a hands item as doable
risks unauthorized actions on a surface the skill can't reach.

#### Step F4 — Parallel execution of doable items

For 3+ doable items: dispatch in parallel as the `language` mode does
its 5 locale subagents. For 1–2 doable items: handle inline (no
subagent fan-out overhead).

For each doable item, run the standard verification gate appropriate
to the surface:

- **Code edit** — tsc + lint on touched files
- **DB refactor** — PDAAV pattern from `conquering-campaign` (probe →
  apply → verify post-state matches pre-state matrix)
- **File delete** — `git ls-files` confirms untracked OR `git rm`
  succeeds cleanly
- **MCP check** — record the SELECT result as evidence in the
  follow-up vault-log

#### Step F5 — Vault log per surface

When ≥3 follow-ups touched the same surface (e.g. 5 DB changes), file
one combined vault-log entry; otherwise file one entry per follow-up
item. Title pattern: `YYYY-MM-DD_<predecessor-campaign>-followups.md`.
Each entry's `predecessor:` frontmatter field points to the campaign
the follow-up extends.

The vault-log also surfaces the **deferred-to-user** checklist + the
**accepted-permanent-exception** list, so future readers can see the
full disposition of the original campaign's follow-up backlog from
one entry.

#### Step F5.5 — Scope the commit (concurrent-actor guard, §L27)

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/commit_scope.py <scan|buildcheck|emit> [--campaign <dir>] [--files a,b,c]`

The followups sweep almost always runs in a **co-mingled working tree** — a parallel session is
editing FE source, DB, all-locale i18n, and the docs daemon is bumping frontmatter counters (§L27).
A `git add -A` here commits someone else's half-finished work and can break `main`. Before committing:

```bash
# 1. Partition the dirty tree: owned vs foreign vs daemon/barrel/i18n tells
python3 ~/.claude/skills/cleanup/scripts/commit_scope.py scan \
  --campaign <predecessor-campaign-dir> \
  --files docs/vault-logs/<this-followup-log>.md,docs/vault-logs/INDEX.md,<other owned>

# 2. Confirm no owned source file imports a foreign-dirty sibling (else main may not build)
python3 ~/.claude/skills/cleanup/scripts/commit_scope.py buildcheck   # exit 2 = risk

# 3. Emit the exact `git add` block for the owned set ONLY — review, then run it
python3 ~/.claude/skills/cleanup/scripts/commit_scope.py emit
```

The script **never commits** — it stages-by-emitting and leaves the decision to you. `--campaign`
auto-derives owned candidates from the campaign dir's own files + its `[[wikilink]]` references;
`--files` adds explicit paths (the followup vault log + INDEX always belong to you). Anything in
`foreign` / `tell:*` is NOT yours — leave it uncommitted. Skip this step only when `git status`
shows a clean tree apart from your own edits.

#### Step F6 — Mark the cleanup marker

```bash
touch /tmp/last_followup_sweep_marker
```

So the next `/cleanup followups` invocation knows where to start.
