---
name: check-point-resched
description: Reference documentation for Star Alliance's automatic per-turn checkpoint commit (turn-finalize.sh) and its four veto gates. Use when explaining the autosave-style per-turn commit, why a turn's work sometimes stays unsaved in the working tree, or where to find the kill switches and one-turn overrides that govern the checkpoint. Read-only: documents behavior, does not change it.
metadata:
  version: 1.0.0
type: Skill
---

# Check Point Resched — how the automatic per-turn checkpoint works

This is a reference skill. It documents one specific piece of Star Alliance machinery — the automatic per-turn checkpoint — so the mechanic can be explained, audited, and reasoned about in plain terms. It does not change the mechanism. If the mechanism itself ever changes, the change belongs in `.claude/hooks/turn-finalize.sh` and the surrounding state files; this skill updates afterwards.

## What the checkpoint is

Star Alliance auto-commits **once per turn**. The mechanism is `.claude/hooks/turn-finalize.sh`, a **Stop-event hook** registered in `.claude/settings.json`. On every turn's Stop event it does two things, in order:

1. **Regenerate generated outputs once, if needed.** It runs `build.py`, but only when a build-source change was flagged that turn via the `.claude/state/build-pending` marker set earlier by `build-mark.py`. Otherwise `build.py` is not invoked at turn end — it's idempotent, but skipping the unneeded run keeps the Stop path quiet.
2. **Coalesce the turn's working-tree changes into one commit.** All edits, additions, and deletions from the turn go into a single commit ("commit-only"). The commit subject is meaningful: it leads with the turn's declared workflow (read from `.claude/state/last-workflow`), then the top changed paths and a total file count — so `git log` reads as a ledger of what each turn did, not "auto: session turn". If no workflow has been recorded for the turn, the subject falls back to `"auto: <paths>"`.

The point of coalescing is auditability: one turn, one commit, one human-readable subject. The working tree is never rolled back; only the commit boundary is automated.

## Commit-only, never push

The hook **commits only; it never pushes**. Pushing to a remote still requires an explicit human ask. Every commit carries the trailer:

```
Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

so authorship is attributed even though the commit is auto-created.

## The four veto gates

`turn-finalize.sh` is a **sibling Stop hook** to the gates. A gate's `exit 2` stops the Stop event, but it does **not** abort sibling hooks — so `turn-finalize.sh` re-checks each gate's condition itself and **skips the commit for that turn** when a gate has blocked. Any one of the four gates is enough to hold the commit back; the four are independent and OR-combined. None of them modify the working tree; they only decide whether this turn's commit lands.

In all four cases the work **stays in the working tree** — nothing is lost. It will land on a later clean turn. This is **forward-fix only**: a block prevents THIS round's commit, it never un-commits a previous one.

The four gates, each with the sentinel/condition they honor:

1. **verify-gate** — independent-critic verification (armed by default). `turn-finalize.sh` mirrors `verify-gate.py`'s allow condition using `verify_hash.py` plus the markers `.claude/state/verify-baseline` and `.claude/state/verify-pass`. If source changed this turn and is unverified, the commit is skipped. *(Note: an empty base fails OPEN — the commit proceeds, because there is nothing to verify against.)*

2. **delegation-gate** — drops `.claude/state/delegation-block` when a turn authored heavy inline bulk work with no Claude subagent spawned to carry it. If that sentinel exists, the commit is skipped.

3. **conformance-gate** — drops `.claude/state/conformance-block` when a high-stakes source-changing turn has no Quartermaster conformance pass logged. If present, the commit is skipped.

4. **conformity-precommit-gate** — drops `.claude/state/conformity-precommit-block` when the repo is out of conformity. If present, the commit is skipped.

A gate that is **DISARMED** (per-gate kill-switch files, see below) is treated as if it had passed — it does not block the commit. A gate whose `SA_SKIP_*` env override is set (see below) is also treated as having passed.

## Kill switches and one-turn overrides

The checkpoint is meant to be quiet. There are several ways to silence it without touching `turn-finalize.sh`:

- **Engine-wide kill switch.** `touch evolution/DISARMED` disarms ALL gates (and `turn-finalize`'s honoring of them). This is the global pause button for the evolution engine.
- **Per-gate disarm files.** A Drop file at any of these paths disables exactly that gate:
  - `.claude/state/verify-gate-disarmed`
  - `.claude/state/delegation-gate-disarmed`
  - `.claude/state/conformance-gate-disarmed`
  - `.claude/state/conformity-precommit-disarmed`
- **One-turn env overrides.** Set the corresponding env var in the shell that runs the turn:
  - `SA_SKIP_VERIFY=1` — skip verify-gate for this turn
  - `SA_SOLO=1` — skip delegation-gate for this turn
  - `SA_SKIP_CONFORMANCE=1` — skip conformance-gate for this turn
  - `SA_SKIP_CONFORMITY=1` — skip conformity-precommit-gate for this turn

**Fail-open guarantee.** `turn-finalize.sh` **fails open on everything (exit 0)** — a broken finalize must never block the Stop event. If the hook itself errors out, the turn's work stays in the working tree; the Stop event still completes; the next turn's clean checkpoint will pick the work up.

## Plain-English framing for the Guild Master

Every time one of your turns finishes, the guild automatically saves your work as one tidy checkpoint (a "commit", a single entry in the project's history) — like an autosave in a game. Many small edits in one turn become one history entry, not many. The subject line tells you what the turn did, in plain English.

It only saves **locally**. It never publishes to the shared server (that still needs your explicit "go" — a push). So the autosave is private until you say so.

If the turn's work failed one of the four safety reviews (a "veto gate" — a quick check that the turn passed a quality bar before its work becomes part of the history), the autosave is **held back for that turn**. Your changes are not lost — they simply wait, unsaved-to-history, in your working folder, until a clean turn saves them. Nothing the gates do reverses earlier turns; they only delay the next one.

There is an **emergency off-switch** if the autosave ever needs to be paused — the engine-wide `evolution/DISARMED` file, plus per-gate disarm files for finer control, plus one-turn environment overrides for a single deliberate skip.

## Related

- [[evolution-engine]] — the gates are part of the guild's autonomous self-improvement spine; this skill documents only the per-turn commit half of that engine.
- [[vault-log-compliance]] — the separate durable change ledger. The checkpoint captures *what changed in the working tree*; the vault log captures *what changed in the world* (vaults, migrations, schema, vaulted docs). Both run on every turn; they are not the same pipeline.
- `.claude/hooks/turn-finalize.sh` — the script this skill documents.
- `.claude/settings.json` — where the Stop hook is registered.

## Changelog

- **1.0.0** — Initial release. Reference skill documenting the automatic per-turn checkpoint (`turn-finalize.sh`), its four veto gates, kill switches, commit-only-never-push, and a plain-English framing for the Guild Master.
