---
name: code-unity
description: "The Developer's and Architect's code-unity guardian — enforce ONE source of truth for every type, constant, config value, utility function, API client, service, and data schema the codebase carries. Three phases: establish (mint or locate the canonical SoT module for each domain); audit (scan every surface for fragmentation — same type defined twice, config scattered, utility re-implemented per folder); unify (merge duplicates into the canonical SoT, update every import). Use to stop duplication before it multiplies, enforce a single import path for shared logic, or stand up clean module boundaries. Triggers: 'one source of truth', 'stop duplicating', 'this type is defined twice', 'unify these constants', 'single import path', 'deduplicate types', 'code unity', 'audit duplication'."
metadata:
  version: 1.0.1
type: Skill

---
# code-unity — one source of truth, every module in one location

This is the Developer's and Architect's craft for **code conformity and unity.** A codebase
stays maintainable only when every shared fact — a type, a constant, a config value, a
utility, an API client — lives in exactly **one** place. This skill finds and enforces
that single source of truth (SoT) across every surface, so a type never gets re-typed,
a constant never gets re-defined, and a utility never gets re-implemented in five slightly
different ways across five feature folders.

It is a three-phase loop. Run them in order on a fragmented codebase, or enter at the
phase you need.

## The one principle

**One source of truth, one import path:**
- **The canonical SoT module** — the *only* file where a shared fact lives: `lib/types.ts`,
  `lib/constants.ts`, `lib/config.ts`, `services/api.ts`, `store/index.ts`, etc. One module
  per domain — not one per feature.
- **Every consumer imports from that path** — never re-declares the fact inline. If the
  module moves, one path changes; if a value changes, one line changes.

If a type is defined in two files, the codebase has two sources of truth and integrity is
already lost. Keeping all shared facts in their canonical SoT is the whole job.

## The three phases

| Phase | What it does |
|---|---|
| `establish` | Locate or mint the canonical SoT module for each domain — one types file, one constants module, one config object, one API/service layer. Document the canonical map in a `CODE-UNITY.md` at the project root. |
| `audit` | Scan every surface for fragmentation — duplicate type declarations, scattered constants, re-implemented utilities, multiple API client instantiations. Report ranked by blast radius (how many consumers are affected). |
| `unify` | Merge all duplicates into the canonical SoT, update every import path, and delete the orphan copies. Re-run `audit` to zero. Never break what already runs. |

## When to run which

- **No clear module boundaries, or the SoT map does not exist** → `establish`. Write `CODE-UNITY.md`
  listing the canonical home for each shared domain (types, constants, config, services, state, schema).
- **Boundaries exist but surfaces fragment from them** → `audit`, then `unify` the findings.
- **Before creating any new file** → run the UNITY CHECK: does a canonical SoT for this domain
  already exist? If yes, extend it — never create a parallel module. The unity-gate hook
  fires this reminder automatically at every new-file write.
- **Recurring guard** → `audit` on every structural change; treat a new fragmentation like a
  failing test. The verify-gate critic flags new SoT fragmentation as a BLOCK.

## The fragmentation taxonomy (what "drift" means)

A surface is **fragmented** when it re-declares a fact instead of importing it from the SoT:

- **Duplicate declaration** — a type, interface, enum, or class already defined in the SoT
  module is re-declared inline or in a feature-local file. (`UserRole` defined in three places.)
- **Scattered constant** — a magic value (`MAX_FILE_SIZE`, `API_BASE_URL`, `DEFAULT_LOCALE`)
  hard-coded in multiple files instead of imported from a constants module.
- **Re-implemented utility** — a `formatDate`, `slugify`, or `debounce` written fresh in each
  feature folder instead of imported from `lib/utils`.
- **Parallel service/client** — a second instantiation of an API client, Supabase client,
  or service class instead of importing the singleton from the canonical service layer.
- **Split config** — environment or feature config spread across `next.config.ts`,
  a local `.env` reader, and an inline object instead of one canonical config module.

**Not fragmentation:** a deliberate local variant — a feature-specific helper that is NOT a
duplicate of a shared one, or an intentional override with a comment explaining why.
The `audit` phase subtracts these first (Step 0); a sweep that unifies intentional
variants is a regression, not a fix.

## How the Developer and Architect work

1. **Find or forge the SoT map first.** Before adding anything, read `CODE-UNITY.md`.
   If it does not exist, run `establish` to create it. Never audit against nothing.
2. **Before creating any new file, run the UNITY CHECK.** Search for an existing canonical
   module for that domain. If one exists, extend it — never create a parallel module. If
   the domain is genuinely new, proceed and add it to `CODE-UNITY.md`.
3. **If you find fragmentation, unify before adding.** Run `audit`, rank findings by blast
   radius, then `unify` — move the value to the SoT, update all consumers, remove orphan copies.
4. **One canonical import path.** After unifying, every consumer imports from the same module.
   Standardize import aliases too (`@/lib/types`, not `../../lib/types` in some files).
5. **Make it a standing guard, not a one-time sweep.** Fragmentation regrows; re-audit on
   every structural change.

## Boundaries — what it is not

- It is **not** `design-unity` — that enforces the UI visual language and token system.
  `code-unity` governs shared logic, types, constants, config, and services — the code
  beneath the UI.
- It is **not** `guild-conformity` — that audits the guild repo's own cross-references
  and generated files. `code-unity` audits the *product codebase's* module structure.
- It is **not** `db-rename-sweep` or `schema-evolution` — those handle DB-level renames
  and migrations. `code-unity` audits TYPE and CLIENT-LEVEL duplication in application code.
- It is **not** `spec-driven-development` — that decides WHAT to build. `code-unity`
  ensures what you build doesn't duplicate what already exists.

## Versioning

Own skill. Bump `metadata.version` on any change (PATCH: wording · MINOR: new phase/taxonomy
entry · MAJOR: method-contract change). Regenerate `VERSIONS.md` with
`python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write`, then `python3 build.py`.

## Changelog

- **1.0.0** — Initial release. The Developer's and Architect's code-unity / SoT enforcement
  engine: three-phase loop (establish → audit → unify), full fragmentation taxonomy. Paired
  with the unity-gate hook (PreToolUse reminder on new-file writes and dispatch calls) and
  a verify-gate critic extension that flags new SoT fragmentation as a BLOCK.
