---
name: session-mining
description: >-
  Mine your own Claude session history for lessons, then turn them into ranked, verified upgrade
  proposals. Use when the user says 'review the last N sessions', 'what did we learn from these
  sessions', 'mine my sessions', 'what should we upgrade/merge/create from past work', 'audit the
  sessions for lessons', 'note down skills we can extract', or any retrospective over prior runs.
  Locates the three session stores (Claude Code project transcripts, Cowork wrappers, scheduled-task
  runs), extracts only signal-bearing turns (corrections + proposals, never tool noise) with
  offset/limit discipline so a 68MB store never blind-reads, hands bulk summarizing to MiniMax doers,
  synthesizes a deduped lesson register, then runs a VERIFY pass against the live repo that kills
  every 'lesson' already shipped. Output is propose-only (apply-gate OFF). The on-demand companion to
  skillsmith's daily routine; uses storm-investigation to synthesize.
metadata:
  version: 1.0.0
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

## Changelog
- **1.0.0** — Initial release. Six-phase pipeline (locate → map → signal-extract → doer-summarize →
  STORM synthesize → verify → propose-only register). `session_map.py` (store join) + `mine_sessions.py`
  (signal-window extractor). Crystallized from the repeated by-hand session-mining retrospectives.
