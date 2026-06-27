---
name: session-mining
description: >-
  Mine your own Claude session history for lessons, then turn them into ranked, verified upgrade
  proposals. Use when the user says 'review the last N sessions', 'what did we learn from these
  sessions', 'mine my sessions', 'what should we upgrade/merge/create from past work', 'audit the
  sessions for lessons', or any retrospective over prior runs. Also CHECKPOINT: 'save my progress',
  'checkpoint this', 'resume where I left off' — saves/reads working context.
  Locates the three session stores (Claude Code project transcripts, Cowork wrappers, scheduled-task
  runs), extracts only signal-bearing turns (corrections + proposals, never tool noise) with
  offset/limit discipline so a 68MB store never blind-reads, hands bulk summarizing to MiniMax doers,
  synthesizes a deduped lesson register, then runs a VERIFY pass against the live repo that kills
  every 'lesson' already shipped. Output is propose-only (apply-gate OFF). The on-demand companion to
  skillsmith's daily routine; uses storm-investigation to synthesize.
metadata:
  version: 1.3.0
type: Skill

---
# Session Mining

The guild's retrospective engine: **mine past sessions → distil lessons → verify against the live
repo → ship a ranked upgrade plan.** It exists because "review the last N sessions for lessons"
recurs constantly and was re-improvised by hand every time. This is the saved pipeline.

> Two siblings, don't confuse them. **`skillsmith` `routine`** runs this *daily and autonomously*
> (STORM, ≥8/10 auto-apply). **This skill** is the *on-demand, propose-only* version you invoke when
> you want the lessons surfaced and ranked but not auto-applied. It uses **`storm-investigation`** as
> its synthesis method.

## Where the sessions live (Phase 0 — locate)

Three stores. The harness only knows one of them; find all three.

| Store | Path | Holds |
|---|---|---|
| **Claude Code transcripts** | `~/.claude/projects/<slug>/<cliSessionId>.jsonl` | The real conversation bodies (slug = cwd, `/`→`-`). |
| **Cowork wrappers** | `~/Library/Application Support/Claude/claude-code-sessions/**/local_*.json` | Metadata only — `title` + `cwd`, keyed by `cliSessionId` → resolves to the `.jsonl`. |
| **local-agent-mode** | `~/Library/Application Support/Claude/local-agent-mode-sessions/` | Older Cowork store; one message per file, extension-less. Treat as text. |

`scripts/session_map.py --match <cwd-substring>` joins the first two for you: emits a size-sorted TSV
of `bytes · title · cliSessionId · jsonl-path`. The Cowork wrapper's `cliSessionId` is the join key —
a wrapper titled "X" is NOT its own transcript; it points at one.

## The pipeline (run in order)

### Phase 1 — Map
`python3 scripts/session_map.py --match star-alliance --out map.tsv`. Skim titles — they're a free
table of contents of what was done. Pick the window (a project, a date range, "last N").

### Phase 2 — Extract signal (never blind-read)
Transcripts routinely exceed token caps — a star-alliance window was **68MB / 50 sessions**. NEVER
full-read. `scripts/mine_sessions.py --map map.tsv --out digest.txt` pulls only signal turns (user
corrections/requests + assistant proposals/gap-flags), deduped, optionally `--cap` per session and
`--min-bytes` to drop stubs. The default keyword sets target guild/skill mining; override with
`--user-kw`/`--asst-kw` for another lens (bugs, decisions, naming). Output is small enough to Read
directly.

**Incremental re-mining (`--cache <path>`).** Stores only grow — re-running over the same window
re-regexes every transcript from scratch. Pass `--cache mine.cache` and each transcript's extracted
signal is memoized by `size:mtime`; an unchanged `.jsonl` is reused, never reopened. Re-runs over a
mostly-static window drop from seconds to ~tens of ms (measured 3.5s → 0.05s, 579/579 hits, output
byte-identical). The cache is fingerprinted by `--user-kw`/`--asst-kw`/`--cap` — change any of them
and it rebuilds itself, so a stale cache can never serve wrong-lens lines. Safe to delete anytime.

### Phase 3 — Summarize (doer-grade → MiniMax)
For a big window, shard the digest and fan **MiniMax M3** over the shards (per `weapon-utility` /
CLAUDE.md) — each doer returns lesson candidates as JSON: `{lesson, evidence, target, confidence}`.
For a small window (a handful of sessions) the thinker reads `digest.txt` directly and skips the
fan-out. The proven funnel at scale: **8,695 windows → 1,806 raw lessons → 112 distinct.**

### Phase 4 — Synthesize (storm-investigation)
Run `storm-investigation` over the candidates: dedup + cluster, build the **contradiction map**, and
**normalize every free-text target against the real roster** (skills / workflows / members) — a doer
guesses targets loosely; bind them to canonical ids or bucket as new-idea / cross-cutting.

### Phase 5 — VERIFY against the live repo (the pass that earns its keep)
For each surviving lesson, check the **current** repo: does the target file still exist? Is the rule
*already* written / built / enforced? Grep the skill dirs, `workflows.json`, `conformity_check.py`,
member `.md`s, `CLAUDE.md`. **Kill every lesson already shipped.** Past runs found this collapses the
plan hard — the guild is usually more mature than the raw mining suggests, and a proposal that
re-adds an existing rule is worse than no proposal. Honesty over volume.

### Phase 6 — Deliverable (propose-only)
Ship two things, **apply-gate OFF — nothing written without a separate "go"**:
1. **Lessons Register** — every distinct lesson · evidence · confidence · target · already-done?
2. **Upgrade Plan** — the survivors only, grouped by target (skills / workflows / members), ranked,
   each with the proposed edit. Flag missing-workflow gaps; never improvise a workflow.

Durable doctrine lessons → offer to write a memory. Reusable pipelines spotted → flag as Workflow
Forge candidates. End with the honest call: how many "lessons" survived verify, and how many were
already built.

## Doctrine baked in (from the runs that forged this)
- **Offset/limit on every big read; the harness page/size hint lies** — verify real length from the
  tool that reads the file.
- **Doers read, thinker synthesizes** — MiniMax carries the bulk transcript summarizing; the thinker
  owns Phases 4–6.
- **Verify kills redundancy** — a lesson already in the repo is not a lesson.
- **Propose-only** — this skill never auto-applies. That's `skillsmith routine`'s job, gated at 8/10.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH wording/refs · MINOR new phase/flag · MAJOR
pipeline contract change). Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write` after a bump.

## Incremental mining — last-mine-ts delta (1.1.0)

Full pipeline reruns over all historical sessions are slow and redundant after the first pass. Stamp a watermark so every subsequent run only processes new sessions.

**After each successful mine run, write the watermark:**

```sh
python3 -c "
import time, json, pathlib
wm = pathlib.Path('data/last-mine-ts.json')
wm.write_text(json.dumps({'ts': time.time(), 'iso': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}))
print('watermark written')
"
```

**At the start of the next run, filter sessions newer than the watermark:**

```sh
python3 -c "
import json, pathlib, time
wm_path = pathlib.Path('data/last-mine-ts.json')
since = json.loads(wm_path.read_text())['ts'] if wm_path.exists() else 0
print(f'mining sessions newer than {since} ({time.strftime(\"%Y-%m-%d\", time.gmtime(since))})')
"
# pass `since` as a filter to session_map.py
```

This turns a growing O(n-sessions) rescan into an O(new-sessions) pass. For repos with >20 sessions, the difference is minutes → seconds. The full rescan remains available for a first-run or when a prior mine was incomplete.

## Checkpoint — save/restore working context (1.2.0)

Mining reads PAST sessions for lessons; **checkpoint** writes the CURRENT session's resume note for the
NEXT one. Use it before a likely context loss — compaction, end of day, a handoff, or any time you'd
hate to re-derive "where was I". Distinct from memory (durable facts) and guild-log (non-git changes):
a checkpoint is a *transient* mid-task handoff, overwritten each save.

**Save** — capture git state + decisions + remaining work to a known path:

```sh
mkdir -p .claude/state
{
  echo "# Checkpoint — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "## Git"
  echo "- branch: $(git branch --show-current 2>/dev/null)"
  echo "- last commit: $(git log -1 --oneline 2>/dev/null)"
  echo "- dirty (diff --stat):"; git diff --stat 2>/dev/null | sed 's/^/  /'
  echo "- staged:"; git diff --cached --stat 2>/dev/null | sed 's/^/  /'
} > .claude/state/checkpoint.md
# then APPEND the prose the git state can't carry — the thinker writes these by hand:
#   ## Decisions made   (what was chosen and why)
#   ## Remaining work    (the next concrete steps, in order)
#   ## Gotchas / open    (anything that will bite the next session)
```

**Restore** — first action of a resumed session: read the note, reconcile against reality, then continue.

```sh
[ -f .claude/state/checkpoint.md ] && cat .claude/state/checkpoint.md || echo "no checkpoint"
git status -s        # reconcile: the working tree may have moved since the save
```

Trust the note for *intent* (decisions, next steps), but re-verify *state* against `git status` — the
tree can drift between sessions. A checkpoint older than the last commit on the branch is stale; prefer
the commit history and re-checkpoint. Keep it one file, overwritten per save — it is not a log.

## Changelog
- **1.3.0** — `mine_sessions.py` gains `--cache <path>`: per-transcript signal lines are memoized by
  `size:mtime`, so an unchanged `.jsonl` is reused instead of re-read+re-regexed on every re-mine.
  Cache is fingerprinted on `--user-kw`/`--asst-kw`/`--cap` → any change auto-rebuilds (never serves
  wrong-lens lines). Measured 3.5s → 0.05s (579/579 hits), output byte-identical; no-cache path
  unchanged. Extraction refactored into a pure `extract()`. Complements 1.1.0's watermark (which
  drops out-of-window sessions): the cache also skips unchanged in-window files. New capability → MINOR.
- **1.2.0** — New §Checkpoint: forward-facing save/restore of working context to
  `.claude/state/checkpoint.md` (git state + decisions + remaining work), ported from the gstack
  context-save / context-restore pattern. Complements mining (past→lessons) with continuity
  (now→next-session). New section → MINOR.
- **1.1.0** — New §Incremental mining: documents the `data/last-mine-ts.json` watermark pattern, add watermark-write command after a successful run, and filter command at run start. Prevents full-history rescan on every invocation. New section → MINOR.
- **1.0.0** — Initial release. Six-phase pipeline (locate → map → signal-extract → doer-summarize →
  STORM synthesize → verify → propose-only register). `session_map.py` (store join) + `mine_sessions.py`
  (signal-window extractor). Crystallized from the repeated by-hand session-mining retrospectives.
