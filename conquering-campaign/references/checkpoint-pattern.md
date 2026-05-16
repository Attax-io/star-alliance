# The Checkpoint Pattern

When a subagent can't verify something at audit time (DB pooler down, MCP unavailable, third-party API throttled, environment offline), don't guess and don't omit. Insert a checkpoint marker, register it in `CHECKPOINTS.md`, and ship the doc with the marker visible.

The pattern preserves three properties simultaneously:

1. **The doc still ships.** Readers see the marker rather than a delayed publication.
2. **The unverified claim is explicit.** No silent "we don't really know this" lurking inside an authoritative-looking number.
3. **The follow-up is mechanical.** When the blocker clears, run queries, replace markers, promote, log.

## The marker format

```html
<!-- CHECKPOINT: CHK-<id> · <one-line description> · expected: <best-known value or "unknown"> -->
```

- `<id>` is short and stable. Reuse the same id across multiple files if the same query resolves them all (e.g., `CHK-1a` for "live tables count" might appear in BACKEND.md and the synthesis).
- The description is short — what the marker is asserting / awaiting.
- `expected:` records what the migration-derived or otherwise-best-effort value was at audit time. It's the falsifiable claim.

After the blocker clears and the marker is resolved, change the prefix:

- `<!-- CHECKPOINT-RESOLVED: CHK-<id> · <YYYY-MM-DD> · live=<value> · ... -->`
- `<!-- CHECKPOINT-OPEN: CHK-<id> · <YYYY-MM-DD> · still pending because <reason> · non-blocking -->`

This way `grep` for `CHECKPOINT:` finds only unresolved markers; `grep` for `CHECKPOINT-RESOLVED:` is the audit trail; `grep` for `CHECKPOINT-OPEN:` finds the items still outstanding by design.

## Inline placement

Place markers as close to the claim as possible. For inline counts, the marker goes right after the number:

```markdown
**Total live views:** ~86 <!-- CHECKPOINT: CHK-1b · live views count from pg_views · expected: 86 -->
```

For full sections that need rebuilding from live data, mark the section header:

```markdown
## Tables Inventory <!-- CHECKPOINT: CHK-2 · live BASE TABLE list from information_schema · expected: ~106 -->
```

Always end a CHECKPOINT-tagged doc with a `## Pending Checkpoints` section that lists every marker (so a future run can `grep` them in one place):

```markdown
## §X. Pending Checkpoints

- `CHK-1a` — live BASE TABLE count
- `CHK-1b` — live view count
- `CHK-2` — full live tables list
- ...
```

## The CHECKPOINTS.md registry

Lives at `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/CHECKPOINTS.md`. Two sections:

- **§1 Queries to run** — exact SQL / commands to execute when the blocker clears, in copy-paste-ready form. One block per checkpoint id.
- **§2 Reconciliation table** — one row per checkpoint with: id, claim in staged docs, best-effort value at audit time, _pending_ live value column (filled in later), source query reference, resolution action.

Optionally a §3 "outcomes that change based on data" — what the doc looks like if live = expected vs live > expected vs live < expected. This makes the reconciliation faster.

## When the blocker clears

Runbook:

1. **Probe the resource.** One trivial call (e.g., `SELECT 1`). Don't burn through the full query batch if the connection is still flaky.
2. **Run all queries from §1 in one batch.** Save raw output to `01b-<resource>-snapshot.md` (or whatever numbering keeps it adjacent to the audit it's reconciling).
3. **Walk §2 row by row.** For each, compare audit-time value against live. Note discrepancies.
4. **Update each staged doc.** Replace the marker with the live value:
   - If the value matches expectations and is non-controversial: `<!-- CHECKPOINT-RESOLVED: CHK-<id> · <date> · live=<value> -->` (or remove the marker entirely, your call).
   - If the value differs significantly: keep a brief note in the doc explaining the gap, mark `RESOLVED`, and surface the discrepancy in the follow-up vault-log.
   - If the resource still can't answer the question (e.g., DB advisor doesn't surface deploy-time edge-function flags): change to `CHECKPOINT-OPEN` and note why it's open. Non-blocking; can ship anyway.
5. **Run `grep -rn 'CHECKPOINT:' docs/staged/` and confirm zero hits** before promotion. (Resolved/open markers don't match — they're prefixed differently.)
6. **Promote staged → live.** `mv` each file. Remove the empty `staged/` directory.
7. **Emit a follow-up vault-log** that references the original campaign log and lists what was reconciled.

## Anti-patterns

- **Don't silently fill in a guess.** If the audit can't verify something, the value is unknown — say so. The whole point is to avoid creating new doc drift while reconciling old drift.
- **Don't put the marker far from the claim.** Readers should see the marker right next to the number.
- **Don't use checkpoint markers for things that *can* be verified now but are inconvenient to verify.** Markers are for genuine blockers, not for laziness. If the answer is in `git log`, run `git log` — that's not a checkpoint, it's just the work.
- **Don't promote staged docs while markers are still unresolved unless explicitly accepting "ship with marker visible."** That should be a deliberate choice, not an oversight.

## Why this pattern works

The campaign's value is in the evidence trail. A doc that says "X = 5" with no source can drift in a single edit. A doc that says "X = 5 [verified 2026-05-10 via pg_views, see audit-campaigns/.../CHK-1b]" carries its own audit on its back.

Checkpoint markers are the lightweight version of that — they explicitly mark what hasn't been verified and where to verify it. When the blocker clears, the marker becomes a permanent breadcrumb showing how the number got there.
