---
type: Document
title: Harness Upgrade — Strategic Audit 2026-06-28
description: Audit-driven upgrade of the Star Alliance harness — build-once-per-turn, readable git history, consolidated PreToolUse dispatcher, doer size-threshold, armed independent-verification, and real member sub-agent dispatch.
timestamp: 2026-06-28T00:00:00Z
---

# Harness Upgrade — Strategic Audit (2026-06-28)

A deep audit of Star Alliance **as a harness** measured the machinery against its
four goals — cost-efficiency, mechanical discipline, self-improvement, usability —
and found it well-built but **over-ceremonial**: energy spent on ritual (per-edit
rebuilds, opaque commits, banners) while the real levers (true parallel members,
the independent reviewer) sat idle. These changes close that gap.

## Shipped

### Wave A — build once per turn + readable history
- **`build-mark.py`** (new PostToolUse) replaces the two per-edit build hooks
  (`member-table-sync.py`, `guild-source-rebuild.py`) that *each* ran the full
  ~1k-line `build.py` (regenerating ~1.8 MB) on **every** source edit. It now only
  drops a `.claude/state/build-pending` marker.
- **`turn-finalize.sh`** consumes that marker and rebuilds **once** at Stop, for any
  source type (member / skill / workflow / art / guild-log). Build cost is now
  O(1 per turn), not O(edits).
- `turn-finalize.sh` now writes a **meaningful commit subject** derived from the
  changed paths (e.g. `auto: .claude/hooks, docs (+4 more, 7 files)`) instead of the
  opaque `auto: session turn` that made 183/200 commits identical and defeated the
  "read git log before continuing" discipline.
- The old hooks (`member-table-sync.py`, `guild-source-rebuild.py`) are **unwired**
  but left on disk as references.

### Wave B — one PreToolUse dispatcher + doer size-threshold
- **`sa-pretool.py`** (new) consolidates the five separate PreToolUse hooks into one
  in-process dispatcher. Each gate now exposes a pure `check(data)` function
  (`workflow-gate`, `weapon-gate`, `destructive-gate`, `okf-gate`, `high-alert`);
  the dispatcher imports them and routes by tool, paying **one** interpreter
  cold-start per tool instead of up to three. First blocker wins; every check is
  wrapped fail-open. Verified against 7 payload cases (exempt, both block paths,
  valid summon, skill banner, malformed).
- **Doer size-threshold** added to the weapon-doctrine reminder: a MiniMax/Ollama
  summon costs ~80–100 s wall-time, so only offload doer-grade **bulk** (≳1.5 k
  tokens of output / many repetitive transforms). Small jobs stay inline — offloading
  them is net-negative.

### Wave C — independent verification armed by default
- The `verify-gate` (HARNESS-BOOKS 9.9 — "never grade your own work") was opt-in via
  a touch-file and shipped **off**. It is now **armed by default**
  (`.claude/state/verify-gate-armed`). A turn that changed source code cannot close
  until a different member/model has reviewed the working-tree diff and recorded the
  pass: `python3 .claude/hooks/verify_hash.py > .claude/state/verify-pass`.
- **Controls:** one-turn bypass `SA_SKIP_VERIFY=1`; disarm `rm .claude/state/verify-gate-armed`.

### Wave D — real member sub-agents (costume → crew, core increment)
- **`guild/install_agents.py`** (new) generates one real Claude Code agent file per
  member into `.claude/agents/` from the `star-alliance-members/` source of truth
  (standard agent frontmatter only). With these present, `subagent_type: the-developer`
  resolves for real — members can be dispatched **in parallel, context-isolated**,
  and `high-alert.py`'s ⚔ "Member reports for duty" klaxon (which already keyed on a
  real member dispatch) goes live. The inline-persona path remains as the
  single-thread fallback — this only **adds** the real-dispatch option.
- **Next step (flagged, not done):** make the routing gate *prefer* real dispatch for
  parallelizable work by default. That is a routing rewrite and its own focused
  project — deliberately staged, not rushed into this pass.

### Wave E — sprawl check (read-only; ground-truthed)
- **0 orphan skills**: all 69 skills are carried by a member. The audit's "dead skills"
  assumption was **wrong** — nothing to trim. (A reminder of the guild's own
  verify-before-acting lesson: ground load-bearing claims before cutting.)
- **9 workflows** are not named in the routing-gate STEP 2 menu (Sync Rotation,
  Oracle's Scrying, Inquiry / Recon, Local Session, Conversation, Harness Calibration,
  Reflective Cycle, Guild Self-Audit, App Packaging). These are **review candidates,
  not deletions** — there is no usage telemetry, and removing a workflow is
  destructive. Pick which (if any) to retire.

## Open decision (not changed unilaterally)
- **Doctrine tension:** CLAUDE.md says "default sub-agent = MiniMax M3, MiniMax first",
  while members/routing assign each member an Opus/Sonnet **thinker**. Which wins per
  turn is ambiguous. Resolution is a constitutional edit to CLAUDE.md and is left to
  the Guild Master. Recommended framing: *thinker plans & reviews (Claude); doer
  executes bulk (MiniMax) — "MiniMax first" applies to **doer-grade** work only.*

## Net effect
Per-turn self-cost no longer scales with edit count; git history is legible again;
the tool layer pays one gate launch instead of several; the strongest quality gate is
on; and the roster can finally act as a real crew, not a costume.
