---
name: guild-conformity
description: "The Quartermaster's craft for proving the whole guild read cache agrees with itself and with the Supabase `guild` schema that is its source of truth, then reconciling any contradiction at its source. Wraps the read-only tools/conformity_check.py (which emits a contradiction map across members, skills, domains, workflows, the guild log, and the generated guild-data bundle) plus fixing each real contradiction at its source and re-materializing the cache with `sa push` / `sa dash` until the check passes clean. It is the closing step of every guild workflow and the spine of the Compliance Audit. Use when a workflow is closing, after any structural change, or when you need proof nothing contradicts. Triggers: 'run the conformity check', 'confirm guild conformance', 'does the repo agree with itself', 'conformity sweep', 'reconcile the guild data', 'is everything consistent'. Differentiate from cleanup (app/i18n hygiene) and skillsmith (skill versioning)."
metadata:
  version: 1.7.0
type: Skill

---
# Guild Conformity — the Quartermaster's craft

You are the ledger-warden of the Star Alliance. Your conformity craft is the closing seal on every workflow and the spine of the Compliance Audit itself: you prove the read cache agrees with itself, that it mirrors the Supabase `guild` schema that is its source of truth, and that no logged decision contradicts a written rule. If the chain is broken, you find where, you fix it at its root, and you do not let anything ship that has not passed the check clean.

## What it is / is not

- It IS: run the read-only `tools/conformity_check.py` to emit a contradiction map, triage each flag for false-positive, fix the real ones at the source of truth (the DB spine, edited through its mirrored source files and pushed with `sa push`), regenerate `guild-data.js` / `guild-data.json` with `sa dash`, and re-run until green.
- It is NOT: cleanup — that is app-code and i18n hygiene for the Lex Council codebase. You do not touch it here.
- It is NOT: skillsmith — that crafts and versions individual `SKILL.md` files. You only consume their `metadata.version`; you do not author versions.
- It is NOT: a build step. You orchestrate `sa push` / `sa dash` / `sa pull`; you do not implement the generator, and you never hand-edit the materialized files they emit. (The old `build.py` is retired — its output shapes were ported into `sa dash`.)

## The craft

1. **Trigger.** A workflow closes, or the Compliance Audit workflow calls you. Confirm the member (and any Claude subagents it spawned) have dropped their artefacts and that the reviewing Claude has signed off in the per-step notes before you begin.
2. **Run the check, read-only.** From repo root: `python3 tools/conformity_check.py`. Capture the full contradiction map to your working buffer. Edit nothing yet.
3. **Triage before edit.** For each flag, classify: (a) real contradiction at source, (b) cache drift — `sa dash` (or `sa pull`) needs a refresh, no source change, (c) check false-positive — rule is over-strict or predates the migration, note it, skip. Only (a) is yours to fix this sweep.
4. **Walk the source-of-truth chain.** The DB `guild` schema is the truth; the files are the read cache Claude Code loads. Fix at the mirrored source, then push. Precedence: `star-alliance-members/<id>.md` frontmatter (model, skills) → `data/members-meta.json` (presentation, weaponsDesc) → `data/skills-meta.json` → `star-alliance-skills/<id>/SKILL.md` (metadata.version) → `data/domains.json` → `workflows.json` → `data/guild-log.json`. Edit the highest-precedence anchor that is wrong, then `sa push` it to the DB. Never hand-edit a materialized file — `.claude/agents/*.md`, `~/.claude/skills/`, or `guild-data.js` / `guild-data.json`; the next `sa dash` / `sa pull` silently overwrites it.
5. **Regenerate the cache.** After `sa push` (step 4) has landed your fix in the DB, run `python3 bin/sa dash` to regenerate the `guild-data.*` bundle from the spine. Confirm both generated files are written and byte-identical except for the JS/JSON wrapper. (Reserve `sa pull` for the pure cache-drift path — receiving DB truth onto a stale local copy — never as a post-fix step, since `sa pull` overwrites your local source edits with whatever is currently in the DB.)
6. **Re-run the check.** Repeat steps 2–5 until `tools/conformity_check.py` exits clean. Stop only on green; there is no "almost green."
7. **Log the sweep.** Append a `guild.log` row (`python3 bin/sa log ...`, or the local outbox when offline) naming the workflow, the contradictions resolved (with their classification), the files touched, and the final check status. This is the audit trail the Strategist and the Butler will read.
8. **Handoff.** Return the green light to the Butler so its `report` gate can close the workflow.

## The current (lean) check set

The sweep is Claude-only and lean. `tools/conformity_check.py` runs these tags — know them by their two/three-letter codes:

| Tag | What it proves |
|---|---|
| **P** | `guild-data.js` ↔ `guild-data.json` parity (byte-identical modulo wrapper). Regenerated by `sa dash`. |
| **MCP** | `.mcp.json` registers a guild MCP server. **Stale ghost** — the local MCP server was retired 2026-07-12 and `.mcp.json` is now empty; this tag fires falsely until the tool is reconciled (see RL/DW below). |
| **N** | `meta.counts` match the real member / skill / workflow / domain counts. |
| **K** | Skill dirs == `skills-meta.json` == generated skill ids (no orphan / uncounted skill). |
| **VER** | Every `SKILL.md` `metadata.version` is well-formed and mirrored in `VERSIONS.md`. |
| **BR** | Every member's `model:` is one of the three Claude models (opus / sonnet / haiku) — no non-Claude model anywhere. |
| **R** | Every carried skill exists in `skills-meta.json`; workflow actors ∈ members ∪ {you}; gates valid. |
| **D23** | The report gate: every workflow ends with the Butler `report` step. |
| **C** | The-quartermaster is the last member step before `report` on every mutating workflow (the conformance close). |
| **SD** | Skill ↔ member drill-row coupling, both directions (a carried skill has a `## Skill Drills` row; no stale row for a removed skill). |
| **AG** | `.claude/agents/*.md` match `star-alliance-members/`. **Superseded** — its `guild/install_agents.py --check` shim is retired/absent, so it silently no-ops; cards are now materialized by `sa pull`, and roster parity is proven by the new RC check below. |
| **REG** | Claude-only registry: `models.json` holds only opus / sonnet / haiku (+ `seats.brain`); nothing references a removed non-Claude model. |

The old brain / doer / profile / dispatch-era checks are **gone** — there is no non-Claude doer layer, no Hermes profile surface, and no dispatch bridge to audit anymore. Some tags above (P's `sa dash` regenerator, MCP, AG) predate the 2026-07 Supabase migration; the new coverage & parity checks below extend the roster and catch exactly the drift those stale tags now miss.

## Adding a new invariant (Artisan rung)

When a recurring contradiction reveals a *missing* rule, you don't just fix the instance — you teach
the check to catch the class. A new invariant lives in **three places at once**, and is not done
until a **negative test proves it bites**:

1. **Enforce it at the source.** If the rule constrains data the cache emits (a structured field, a
   count, an order), validate it where the data is *authored* — the DB spine's mirrored source files —
   and fail `sa push` / `sa dash` loudly on a bad value. Authoring-time is where a violation is cheapest
   to catch. (This is the producer half; the Architect's `schema-evolution` craft is the same discipline
   for an added field.)
2. **Re-assert it at the gate — `tools/conformity_check.py`.** Add the check to the read-only audit with
   a short two-letter tag (like `RC`, `DV`, `RL`, `K`) and a message that names the record, the file,
   and what's wrong — so a future sweep reads like a map, not a riddle. Validate **"when present"** for
   any optional field, so existing records that predate it stay conformant by construction.
3. **Prove it with a negative test.** Hand-break one record so the new rule *should* fire, run
   `tools/conformity_check.py`, and confirm it FAILS with your tag — then revert and confirm GREEN. A rule
   you've only ever seen pass is a rule you haven't tested. An invariant that can't fail isn't enforcing.

Keep the rule **narrow**: it must catch the real contradiction without flagging innocent records. A
new invariant that raises false positives is worse than the gap it closed — it trains the next
Quartermaster to ignore the check. Document the tag's meaning in the check's header legend.

### The anti-drift family — locking a consolidation

A recurring, high-value *class* of invariant: when a duplicated fact is collapsed onto one source of
truth (the Architect's `schema-evolution` consolidation move), every copy you could **not** delete
becomes a drift risk. Seal each one with a gate rule that ties it back to the source — this is what
makes a consolidation *stay* consolidated:

- **`fallback == source`** — a fail-safe literal (a hardcoded dict kept so a broken registry never
  bricks a gate) must equal the registry it shadows. `FB` checks any fallback role/model constant in
  the gates against `models.json` — the exact guard that would have caught the early
  wrong-model-in-a-seat bug that started that whole consolidation.
- **`sidecar ⊆ source`** — an operational side-file (a cost/usage map) may only key ids that exist in
  the source. `MU` checks `models-usage.json` keys ⊆ registry ids.
- **`asset exists per id`** — a convention-keyed asset (art tile, generated doc) must exist for every
  id the source declares. `WART` checks a `weapon-art/<id>.png` per registry weapon.
- **`prose == data`** — hand-edited doctrine prose that names data (the routing-gate's `member (model)`
  lines) is **linted, not regenerated**: `RG` checks the pairs match `guild-data`, so the prose stays
  hand-owned but honest.

Each still earns its negative test (hand-break the copy → confirm the tag fires → revert → green).
Without these, copies silently re-diverge the moment someone edits one; with them the gate bites loudly.

### The two skill surfaces — repo and Claude store

Skills live on TWO layers, each a copy of the DB truth (the guild is Claude-only; there is no separate per-member arsenal to mirror):

| Layer | Location | Role | SoT |
|---|---|---|---|
| **Repo** | `star-alliance-skills/<id>/SKILL.md` | Working copy + git history; edit here, then `sa push` | DB (`guild.skills`) is truth |
| **Claude Store** | `~/.claude/skills/<id>/` | What Claude sessions load locally | derived (materialized by `sa pull`) |

The Supabase `guild.skills` table is the single source of truth. Edit the working copy in the repo, `sa push` it to the DB, and every device runs `sa pull` to re-materialize its store. There is no MCP server serving skills anymore — consumer repos (like Lex Council) get materialized files via `sa pull`, not a live server.

**Drift detection and reconciliation:**

- **Cache drift:** if a materialized copy (`~/.claude/skills/<id>/` or `.claude/agents/<id>.md`) diverges from its source, do NOT hand-patch the copy — re-run `python3 bin/sa pull` to re-materialize it from the DB spine. Hand-editing a derived file is drift the next pull silently overwrites.

**Close-out seal — not ready until:**

1. ✓ `tools/conformity_check.py` is GREEN (real flags only; stale ghosts noted)
2. ✓ No cache drift — every materialized copy matches its source (re-pull only if a copy is stale)
3. ✓ `sa dash` has regenerated the `guild-data.*` bundle (P parity holds)
4. ✓ The sweep is logged to `guild.log`

## New coverage & parity checks (2026-07-12)

Four new guards close a class of drift the lean set missed after the Supabase migration: the sweep
inspected only a hand-listed subset of member cards, never checked that a materialized copy still
matched its source, and never noticed that its own retired-layer tags had gone stale. **These four are
authored here as invariants-to-add — each lands in `tools/conformity_check.py` via its own negative
test (per the Artisan-rung method above), and is NOT yet live in the current sweep** — so do not run
today's check expecting them. When added, each names the record, the file, and what's wrong on failure.

- **RC (roster completeness).** Audit the FULL member roster, not a subset. Truth is `guild.members`,
  mirrored to `star-alliance-members/the-*.md`. Assert both directions across the whole `the-*.md`
  glob: every member has a materialized `.claude/agents/<id>.md` card (except the-butler, a Persona
  with no card), AND no orphan card exists for a member absent from the roster. Catches a **missing
  card** (an uninstalled member whose profile was added but never pulled) and a **stale card** (a card
  left behind after a member was renamed or removed). This is the durable successor to the no-op AG tag.
- **DV (derived-file drift).** Source → derived. Every file materialized by `sa pull` — the agent
  cards, the Claude-store skill copies, and any skill array carried in `data/members-meta.json` — must
  equal what its source declares. A member's `skills:` frontmatter is the source; a derived skill array
  that lists a skill the member no longer carries, or omits one it now carries, is drift. Flag it so it
  is reconciled at source and re-pulled, never hand-patched in the derived copy.
- **RL (retired-layer reference).** Flag any LIVE reference to a retired layer — the Hermes/MiniMax
  doer, `dispatch.py`, the local MCP server and its `.mcp.json` wiring, `build.py` and its generated
  bundles, `install_agents.py`, `skill_sync.py`, the per-turn `turn-finalize.sh` / `build-mark.py`
  chain — anywhere outside `.retired/` and historical logs. Per CLAUDE.md these are all retired; a live
  invocation in code, config, or doctrine is a ghost. **Worked example:** the conformity tool itself
  still runs the `MCP` tag against an empty `.mcp.json` and the `AG` tag against an absent
  `install_agents.py`, and its P failure hint still says "rerun build.py" (now `sa dash`) — the check
  that audits everyone is itself mid-migration, and RL is the guard that names it.
- **DW (doctrine ↔ wiring).** Assert CLAUDE.md's "what still runs / what's retired" list empirically
  against the harness. Every hook CLAUDE.md says runs — `sa-pretool.py`, `guild-routing-gate.sh`, the
  reminder/logger set (`turn-start.py`, `spawn-log.py`, `turn-cost.py`, `guild-flush`) — must actually
  be wired in `.claude/settings.json`; everything it calls retired must NOT be wired. Catches doctrine
  that drifted from the wiring in either direction — the class the stale MCP/AG tags are themselves an
  instance of.

Keep each narrow (validate "when present" so pre-migration records stay conformant) and give each its
negative test before you rely on it.

## Sharpening the craft

You improve along four rungs, and your measure is the count of clean sweeps versus the contradictions you let leak.

- **Apprentice — flag-taker.** You run the check, you edit whatever it points at, you re-run until zero. You miss false-positives, you patch generated files in place, and you treat every flag as gospel. Measure: clean-sweep rate. Outgrow: hand-editing materialized files; conflating check noise (stale ghosts) with real breaks.
- **Journeyman — source-finder.** You trace every flag back to its source-of-truth anchor in the DB spine before touching anything. You learn the precedence chain cold and you keep the cache honest with `sa push` / `sa dash`. Measure: median time to green, number of re-materializes per sweep. Outgrow: fixing the wrong anchor; letting cache drift masquerade as a real break.
- **Artisan — rule-keeper.** You propose new invariants to `tools/conformity_check.py` when a recurring contradiction reveals a missing rule. You maintain the precedence doc and you keep `guild.log` clean enough that the Strategist can audit you. Measure: false-positive rate you catch, invariants you add, audit disputes you settle. Outgrow: adding rules that mask real breaks; bloating the check.
- **Master — contradiction-hunter.** You spot the contradiction before the check does, by reading the chain against a fresh workflow spec in your head. You notice when a tag has gone stale against the wiring (the MCP/AG ghosts) and route the tool's own reconciliation to the Developer. You decide when a contradiction is a spec error and raise it to the Architect, not a fix-it. Measure: contradictions you prevented, false flags you overturned, postmortems filed. Outgrow: confidence without proof; sweeping contradictions under the rug.

Track, always: green-sweep ratio, median re-materializes to green, count of hand-edits to materialized files (must be zero), count of false-positives triaged, count of invariants added.

## Gotchas

- The check emits noise on first run after a new skill is added — `skills-meta.json` lags the new `SKILL.md` by design. Triage as cache drift, not a contradiction.
- The `MCP` and `AG` tags are stale ghosts post-migration (empty `.mcp.json`, absent `install_agents.py`). Do not "fix" them by resurrecting a retired layer — note them in the log and let RL/DW carry the reconciliation of the tool itself.
- `members-meta.json` `weaponsDesc` is a set, not an ordered list. Do not "fix" the order; the check enforces set equality, not sequence.
- `guild-data.js` and `guild-data.json` parity is byte-for-byte modulo wrapper. If parity fails, re-run `sa dash`; do not hand-sync the files (and ignore the tool's stale "rerun build.py" hint).
- Never hand-edit a materialized file — `.claude/agents/*.md`, `~/.claude/skills/`, or the `guild-data.*` bundle. Edit the source, `sa push`, then `sa dash` (or `sa pull` to receive on another device).
- Every workflow must END with the Butler `report` gate, and the last member step before `report` on a mutating workflow must be the-quartermaster. Inserting any step after you breaks the spine.
- `metadata.version` is parsed. A stray pre-1.0 tag like `v0.3-rc` trips it. Bump through skillsmith, not here.
- Every member's model must be one of the three Claude models in `models.json` (opus / sonnet / haiku). If a new model is named, it must be Claude and in the registry first; conformity does not adopt ghosts (the `BR` / `REG` checks enforce this).
- README and domains carry skill-count claims that the check verifies. If you add a skill, update the claim in the same commit, or the next sweep will flag it.
- Never close a workflow on a red check. "One flag is a known stale ghost" is a triage note for the log, not a green light — and the real flags in the same run still bind.

## Edit-time fast-path — `tools/conformity_check.py --member <name>`

The full sweep is the *closing* seal, but some drift is cheaper to catch the instant it's made.
**The moment you assign or remove a skill from a member, run the focused check before moving on:**

```sh
python3 tools/conformity_check.py --member developer   # or architect, herald, …  (the- prefix optional)
```

It audits ONLY that one member's skill↔drill coupling — both directions — without the whole-repo
sweep:
- **SD forward:** every skill in the member's `skills:` frontmatter has a `## Skill Drills` row.
- **R:** every carried skill exists in `skills-meta.json`.
- **SD reverse:** no drill row names a skill the member no longer carries (a stale row left after a
  removal — the failure the full SD check did *not* catch, because it only looks forward).

Exit 0 clean, 1 on drift, fast enough to run after every loadout edit. This is the primary guard for
the [[skillsmith]] Invariant #9 coupling; the full conformity-close remains the backstop. (Mined from
the harness-efficiency session, where a skill landed in two loadouts with no drill row and only the
sweep-time SD flag caught it.)

## Swarm-close

When a workflow ran a `swarm` step (N worker instances on disjoint slices), the **ORCHESTRATOR**
(the Butler) runs the conformity check ONCE after ALL workers finish — workers never run conformity
themselves. Intermediate parallel states would fail (each worker sees only its slice, not the
assembled repo). The Butler collects every slice, integrates, then calls this craft as the closing
seal, exactly as in any other workflow. Nothing else changes.

## Versioning
Own skill. Current: **1.7.0**. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 bin/sa dash`.

## Member-table consistency check

The `## Your Weapons` prose table in each member `.md` is GENERATED from its frontmatter `weapons:` loadout + `members-meta.json` weaponsDesc. `sa dash` re-derives the presentation surface from the DB spine; if it hasn't run, the rendered table can drift while the frontmatter is correct — the sweep reads frontmatter, not rendered prose, so it would not catch it.

**Add to every conformity close:**

```sh
# Spot-check: does each member's prose table match its frontmatter weapons: list?
python3 tools/conformity_check.py --member <name>   # checks skill↔drill coupling
python3 bin/sa dash                                 # re-derive presentation from the DB spine
python3 tools/conformity_check.py                   # full sweep
```

**Invariant to watch:** after any member `.md` edit, confirm `sa push` sent the source to the DB and `sa dash` re-derived the presentation. The old per-turn `build-mark.py` / `turn-finalize.sh` rebuild-and-commit chain is retired (files in `.retired/2026-07-supabase-migration/`); re-materialization is now the explicit `sa dash` / `sa pull` step, not a Stop hook. If you find a live reference to that retired chain, flag it (RL) before closing.

## Changelog
- **1.7.0** — Reconciled to the 2026-07 Supabase migration and added §New coverage & parity checks (2026-07-12): four new guards — `RC` (full-roster card completeness, both directions; successor to the no-op `AG` tag), `DV` (source→derived cache drift), `RL` (live retired-layer references outside `.retired/`), `DW` (doctrine↔wiring asserted against CLAUDE.md + `settings.json`). Body now points at `tools/conformity_check.py`, replaces the retired `build.py` rebuild with `sa push` (fix) + `sa dash` (regenerate), reframes the source-of-truth chain onto the DB spine + read cache, and marks the stale `MCP`/`AG` tags as ghosts the new checks supersede. New checks + migration reconciliation → MINOR.
- **1.6.1** — New §New mechanical checks (2026-07-01): documents `HM` (stale model id vs `models.json`), `MN` (`the-<name>` member-token consistency), `WR` (write-without-read control surface), `GC` (advisory git size >800MB). Doc-only → PATCH.
- **1.5.0** — Added §Swarm-close: the orchestrator (Butler) runs the conformity check ONCE after ALL swarm workers finish; workers never run it themselves. New section → MINOR.
- **1.4.2** — Updated §Member-table consistency check to the then-current build chain; the old `member-table-sync.py` + `autocommit.sh` invariant was stale. Refs → PATCH.
- **1.4.1** — Reconciled the workflow rename: live references to the old "Conformity Sweep" now read **Compliance Audit**; historical mentions left intact. Wording/refs → PATCH.
- **1.4.0** — New §The anti-drift family: names the reusable invariant *class* that locks a source-of-truth consolidation — `fallback == source` (FB), `sidecar ⊆ source` (MU), `asset-per-id` (WART), `prose == data` lint (RG). New section → MINOR.
- **1.3.0** — New §Member-table consistency check: documents the member-table-sync invariant and hook-wiring verification before closing.
- **1.2.0** — Added §Edit-time fast-path (`--member`) + the matching focused per-member skill↔drill audit (SD forward + R + SD reverse). New mode + section → MINOR.
- **1.1.0** — Added §Adding a new invariant — the Artisan-rung method (enforce at source, re-assert at the gate, prove with a negative test). New section → MINOR.
- **1.0.0** — Initial release. The Quartermaster's repo-wide conformity audit and reconcile loop — the closing seal on every workflow.
