---
name: star-alliance-language
type: Skill
description: The guild's shared reading protocol for OKF-tidied repos — how every member quickly, cheaply, and reliably takes in a repo the Quartermaster has kept conformant, on future runs. Read the concept map first (frontmatter + cross-links), open only the few concepts the task needs, never blind-read. Universal — rides every member, like weapon-utility. Use whenever a member starts work in a repo, needs to find where knowledge lives, or asks 'read the repo', 'what's in here', 'map this', 'orient me', 'where is X documented'.
metadata:
  version: 1.0.0
---

# Star Alliance Language — the OKF reading protocol

The **consumer** half of the guild's knowledge standard. Where the **okf** skill
(Quartermaster) *produces* a tidy, OKF-conformant repo, this skill is how **every
member reads it back** — fast, cheap, and the same way every time. It is the
shared "language" the guild speaks when consuming knowledge, the mirror image of
OKF's producer/consumer split.

**Universal.** Like `weapon-utility`, this skill rides *every* member. Any member
beginning work in a repo orients through this protocol first.

## Why this exists

The guild's #1 repeated correction (mined across 46 sessions) is reading
discipline: *don't blind-read large or unknown files.* OKF makes that easy to obey
— because every governed `.md` is **guaranteed** (by the `okf-gate` hook) to open
with a `type:` frontmatter, a member can learn the whole repo's shape from
frontmatter alone, then open only the handful of files the task actually needs.
This skill turns that guarantee into a routine.

## The protocol (do this, in order)

1. **Get the concept map first — one shot, not many reads.**
   ```
   python3 star-alliance-skills/star-alliance-language/scripts/okf_read.py
   ```
   Returns every governed concept as a single line — `path · [type] title —
   description {tags} → N links` — grouped by directory, `index.md` surfaced first
   (progressive disclosure). One command replaces dozens of speculative reads.
2. **Narrow before you open.** Filter the map down to what the task needs:
   - `--dir <subtree>` — scope to one area.
   - `--type Skill|Member|Workflow|Document|…` — only concepts of one type.
   - `--grep <term>` — title/description/tags/path match.
   - `--json` — when a doer or another tool will consume the map.
3. **Read frontmatter, not whole files.** The map already carries each concept's
   `type`, `title`, `description`, `tags`. That is usually enough to decide *which*
   concepts matter. Open the body only for those.
4. **Follow cross-links, don't grep blindly.** To understand a concept's
   neighbourhood:
   ```
   okf_read.py --links <path/to/concept.md>
   ```
   prints outbound and inbound links — the OKF graph. Walk the graph to related
   concepts instead of full-text searching the repo.
5. **Open the few that matter — with discipline.** When you finally read a body,
   honour the guild's reading rules: `offset`/`limit` or `grep` for large/unknown
   files, never a blind full read; loop files one at a time in autonomous runs.
6. **Trust the contract, but verify staleness.** The `type:` is guaranteed; the
   *content* reflects when it was written. If a concept names a file/flag/function,
   confirm it still exists before acting on it.

## When to reach for it

- **Session start in any repo** — orient via the concept map before touching code.
- **"Where is X?"** — `--grep X` over the map beats spelunking.
- **Handing context to a doer** — pipe `--json` map into a `summon.py` prompt so
  the doer gets the repo's shape without you pasting files.
- **After the Quartermaster tidies** — the map is the proof-of-tidy: it should read
  cleanly, every line with a real `type` and title.

## Relationship to the rest of the arsenal

```
  okf                    →  PRODUCE a conformant repo (Quartermaster writes)
  okf-gate (hook)        →  GUARANTEE every governed .md carries `type:`
  star-alliance-language →  CONSUME it efficiently (every member reads)  ← here
  weapon-utility         →  which WEAPON does the reading/doing
```

This skill assumes OKF conformance; it does not enforce it (that's `okf` + the
gate). If the map shows `[?]` types or missing titles, the repo isn't fully tidy —
flag it to the Quartermaster rather than working around it.

## Don't

- Don't blind-read the repo when one `okf_read.py` call gives you the map.
- Don't full-read a body the frontmatter already answered.
- Don't enforce or fix conformance here — that's the producer skill's job.
