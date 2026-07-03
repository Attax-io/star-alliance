---
name: schema-evolution
description: "The Architect's craft for evolving a structured data model without breaking what already reads it — adding an optional, backward-compatible field to a JSON (or table) schema and threading it through every consumer in lockstep. The method: add the field as OPTIONAL with a safe default, validate it where it's authored (fatal in the generator) and again at the conformance gate, render/consume it everywhere it should appear, document it in the authoring skill, and PROVE old data with the field absent still passes green. Use when adding a field to a shared data model, versioning a record shape, or making a non-breaking migration across producers and consumers. Triggers: 'add a field to', 'extend the schema', 'add an optional field', 'evolve the data model', 'thread this through every consumer', 'backward-compatible migration', 'version this record shape', 'add a column without breaking'. Differentiate from db-rename-sweep (renames an existing name) and transactions-domain-model (loads one fixed domain)."
metadata:
  version: 1.2.0
type: Skill

---
# Schema Evolution — the Architect's craft

You are the keeper of the data model's continuity. A schema is read by many hands — generators,
gates, renderers, exports, other people's scripts — and the moment you add a field, every one of
them is a place the change can break or silently drop. Your craft is to grow the model *additively*:
the new field is optional with a safe default, it is validated where it's born and again where the
guild proves itself, it reaches every consumer that should show it, it is written down for the next
author, and — the seal on the whole thing — **old data that predates the field still passes green**.
A migration that forces every existing record to change at once is a rename, not an evolution; you
do the evolution.

## What it is / is not

- It IS: add an optional, backward-compatible field to a structured model (a JSON like
  `workflows.json` / `members-meta.json`, or a table), validate it at the source and the gate, render
  it through every consumer, document it, and prove records without it still validate.
- It is NOT: `db-rename-sweep` — that changes an *existing* name across its surface. You *add* a new
  name. (A rename is breaking by nature; an added optional field is the opposite.)
- It is NOT: `transactions-domain-model` — that loads one fixed domain's invariants. You change the
  shape of a model, in any domain.
- It is NOT: a breaking migration. If the field must be required-from-day-one, that's a different,
  riskier move (backfill-then-require, two deploys); this craft is the additive, single-pass case.

## The method — the five moves, in order

1. **Add the field as OPTIONAL with a safe default.** The reader must treat *absent* exactly as it
   treats the default — `s.get("class", "mutating")`, `obj.get("swarm") or {}`. Never index a new key
   directly; never let absence mean a crash or a wrong answer. This single decision is what keeps every
   record that predates the field valid.
2. **Validate it where it's authored — fatal in the generator.** Where the field is *written* (the
   producing tool / `build.py`), reject a malformed value loudly: unknown enum, wrong type, a reference
   that doesn't resolve. Authoring-time validation is where a bad value is cheapest to catch — fail the
   build, name the record and the field.
3. **Validate it again at the conformance gate.** The repo's self-agreement check (`conformity_check.py`,
   the guild-conformity craft) gets a rule that the new field, *when present*, is internally consistent
   — it points at things that exist, it obeys the constraints the field implies. "When present" is the
   whole game: a record without the field is conformant by construction.
4. **Render / consume it everywhere it should appear.** Walk every consumer — dashboard renderer,
   export, downstream script — and thread the field through, each one defaulting on absence. A field
   validated but never shown is half-built; a field shown in one view and dropped in another is drift.
5. **Document it in the authoring skill, and PROVE old data passes.** Add the field to the
   skill/playbook that authors this model so the next hand knows it exists and its rules. Then the seal:
   run the gate against the *existing* data (field absent on every old record) and confirm **green** —
   the proof that the evolution is backward-compatible, not a hope.

## Consolidation — collapse duplicates onto one source

The mirror of adding a field: a fact already lives in *many* places that have quietly drifted (this is
how the model armory grew three role tables that disagreed on `sonnet`). Collapsing them onto one source
of truth is an evolution, not a rename — with its own moves:

- **Adopt, don't create.** Before standing up a new SoT, grep for an existing one (`*registry*`, a
  `*.json`, a shared loader). An audit that says "there's no central source — create `data/models.json`"
  is usually wrong: the registry already exists and is half-adopted. Extend the file that is already
  authoritative. Verify the audit's absence-claims yourself first (see [[verify-multiagent-audit]]).
- **Let the canonical side win — drift fixes itself.** When you merge a stale copy into the SoT, keep
  the SoT's value for any field they disagree on. Migrating `app.js`'s hand-keyed `MODELS` onto the
  registry corrected a stale role value *for free*, because the registry was right and the copy was
  the bug.
- **Extract with a real evaluator, never by hand or by an LLM.** To pull a JS object literal into JSON,
  `node -e` eval it; to merge, do it in Python. Transcribing 15 records × 16 fields by eye (or handing
  it to a Claude subagent to retype) drops a field. Machine-extract, machine-merge, diff the result.
- **Emit, then derive.** The build emits the SoT into the artifact every consumer already loads
  (`GUILD.models` in `guild-data.js`); each consumer then *derives* (`const MODELS = GUILD.models`)
  instead of holding a copy. Mind load-timing — the artifact's `<script>` must precede the consumer.
- **Seal it with anti-drift conformity checks** — the move that makes consolidation *stick*. For every
  copy you cannot delete (a fail-safe fallback, a cost sidecar, a generated asset, hand-edited prose),
  add a gate rule that it **equals / is a subset of** the SoT: `_FALLBACK_ROLE == registry`,
  `usage-keys ⊆ registry`, `art-tile exists per id`, `routing-gate prose == data`. Without them the
  copies silently re-diverge; with them the gate fails loudly the instant one drifts — the guard that
  would have caught the original bug.

## DB-Migration Mode — when the "field" is a Postgres table or column

The five moves assume a JSON record shape, where *absence* is safe and the default lives in the
reader. When the thing you are adding is an actual **Postgres table or column** — not a JSON
field — additivity is necessary but not enough: a new table can read green and still be a *silent
data leak*, because the additive instinct ("existing readers don't break") says nothing about
*who is now allowed to read the rows*. This mode complements the additive-JSON guidance; it kicks
in the moment the field is a column on, or the whole of, a tenant-scoped table.

The contract, in one line: **security ships in the same migration file as the structure, or it
does not ship.**

- **RLS in the same migration file as the `CREATE TABLE` — a separate RLS file is forbidden.** The
  same file that creates the table must also `ALTER TABLE … ENABLE ROW LEVEL SECURITY`, declare
  the policies, `CREATE INDEX … ON tbl(user_id)` ("Index for RLS performance — MANDATORY"), and
  add the GRANTs — in that order. Split the RLS into a second file and a window exists where the
  table is live and unprotected; that window is the leak.
- **A mandatory `user_id` index on every RLS-scoped table.** The policy's `USING` clause runs on
  every read and filters on the scoping column, so without the index every query is a scan. The
  index is part of the security change, created in the same file — never deferred.
- **The migration checklist:** RLS-in-same-file → `user_id` index → GRANTs → data-dictionary
  update. Run it in order; an undocumented scoped table is one the next author re-discovers from
  the schema.
- **Policies absent ⇒ stop-the-line.** A migration that creates/alters a tenant-scoped table with
  RLS absent — no `ENABLE ROW LEVEL SECURITY`, a GRANTed path with no covering policy, or RLS in a
  separate file — is a *security* defect, not a backward-compat one, and the additive proof is
  silent about it. Stop; do not thread it through consumers or hand off until structure + RLS +
  index + GRANTs are one atomic file.

Full mode, with the in-order migration template and the stop-the-line rule: see
[`references/db-migration-mode.md`](references/db-migration-mode.md). Grounded in the SAW
`migration-patterns` discipline, adapted to the guild's additive-evolution voice.

## The craft

1. **Name the field, its type, its default, and its absence-meaning** before touching code. "`class`:
   enum `mutating | read-only`, default `mutating`; absent ⇒ mutating" — write that line first. An
   evolution with a fuzzy default breaks the oldest records.
2. **Find every consumer first.** Grep the model's key usages across generator, gate, renderers,
   exports. The set you find is the set you must thread the field through; a missed consumer is the bug.
3. **Apply the five moves in order.** Optional+default → generator-validate → gate-validate (when
   present) → render → document + prove. Order matters: validate before you render, prove last.
4. **Prove both directions.** New data with the field set validates and renders; old data with the
   field absent validates and renders the default. Both, explicitly. The backward case is the one that
   silently rots if unproven.
5. **Hand to the Quartermaster to close.** The conformance gate + dashboard parity are his seals; your
   evolution isn't done until his check is green on both new and old records.

## Sharpening the craft

You improve along four rungs; your measure is fields added that never broke a reader versus the
silent drops and crashed consumers a careless add leaves behind.

- **Apprentice — field-adder.** You add the key and read it directly. You forget a default, so an old
  record crashes a consumer; you validate nowhere. Measure: consumers crashed on absent field (want
  zero). Outgrow: indexing a new key; no default.
- **Journeyman — defaulter.** Every reader defaults on absence; you validate the value in the
  generator. You thread it through the consumers you remembered. Measure: old-data-passes rate,
  generator-rejects-bad rate. Outgrow: the consumer you forgot to grep for.
- **Artisan — gate-keeper.** You add the "when present, consistent" rule to the conformance check and
  document the field where it's authored. You prove old and new data both green before handing off.
  Measure: gate rules added per field, drift caught pre-handoff. Outgrow: validating without rendering;
  documenting nowhere.
- **Master — continuity-architect.** You design the field's absence-semantics so the oldest record is
  correct by construction, and you can name every consumer before you grep. You know when a field
  *can't* be optional and must be a backfill-then-require migration instead — and you say so. Measure:
  fields shipped needing a follow-up fix (trend to zero). Outgrow: forcing additive on a genuinely
  breaking change.

Track, always: consumers crashed on the absent field (must be zero), old-records-pass-green rate,
generator validations added, gate invariants added, consumers threaded vs consumers found.

## Gotchas

- **Direct index on a new key.** `obj["new_field"]` crashes every record that predates it. Always
  `.get` with the default. This is the single most common break.
- **Default in the reader ≠ default at the gate.** The conformance rule must treat *absent* as
  conformant ("when present, …"). A gate that requires the field flags every old record and turns a
  non-breaking add into a red build.
- **Validated but not rendered.** A field the generator accepts but no consumer shows is invisible
  work — and the next author assumes it's wired. Render it, or don't add it yet.
- **Rendered in one view, dropped in another.** Threading half the consumers is drift the dashboard
  parity check exists to catch. Walk *all* of them.
- **"Optional" that's secretly required.** If downstream logic breaks when the field is absent, it
  isn't optional — you owe a backfill + a required-from migration, two passes, not this one.
- **Enum without a closed check.** An enum field with no "unknown value ⇒ fail" in the generator lets
  a typo (`read_only` vs `read-only`) ship as a silently-wrong record.
- **Forgot the authoring skill.** The next hand re-discovers the field by reading source. Document it
  in the producing skill/playbook in the same pass, or the rule lives only in your head.
- **Proved new, not old.** Testing only the record you just added proves nothing about backward
  compatibility. The absent-field case is the one that matters; prove it green explicitly.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new section/move · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.2.0** — New section **DB-Migration Mode — when the "field" is a Postgres table or column** (+ `references/db-migration-mode.md`): the case the additive-JSON moves don't cover, where additivity is necessary but not sufficient because a new tenant-scoped table can read green and still be a silent data leak. Contract: security ships in the same migration file as the structure — RLS (`ENABLE ROW LEVEL SECURITY` + policies) in the SAME file as `CREATE TABLE` (separate RLS file forbidden), a MANDATORY `user_id` index for RLS performance, the in-order checklist (RLS-in-file → user_id index → GRANTs → data-dictionary update), and policies-absent ⇒ stop-the-line as a security defect, not a backward-compat one. Grounded in the SAW `migration-patterns` skill, adapted to the guild's voice. New section + reference → MINOR.
- **1.1.0** — New section **Consolidation — collapse duplicates onto one source**: the mirror move of additive evolution, for when a fact already lives in many drifted copies. Five moves — adopt-don't-create (grep for the existing SoT; verify an audit's "create X" claim first), let the canonical side win so drift auto-fixes, machine-extract/merge (never by hand or by an LLM), emit-then-derive (with load-timing care), and seal with anti-drift conformity checks (fallback==source, sidecar⊆source, tile-per-id, prose==data). Mined from the model-armory consolidation that collapsed `app.js` MODELS + three role tables onto `star-alliance-arsenal/models.json`. New section → MINOR.
- **1.0.0** — Initial release. The Architect's additive-migration method: add an optional field with a safe default, validate at the generator (fatal) and the conformance gate (when-present), render through every consumer, document it in the authoring skill, and prove records without the field still pass green. Mined from the member-step model fields (`model`/`swarm`) and workflow `class` additions.
