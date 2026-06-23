---
name: skillsmith
description: "Manage, sync, upgrade, create, and auto-evolve Star Alliance skills across the star-alliance repo and the on-device copies (~/.claude/skills global + per-project .claude/skills). Modes — sync: reconcile repo and device by metadata.version, honoring fork+external exceptions. upgrade: bump a skill's version, regenerate the VERSIONS.md registry, run the Cowork-compliance check, add a changelog entry. create: author a new skill via the official skill-creator, then make it upgradeable. routine: a daily, fully-autonomous self-improvement loop that mines your code, projects, and sessions with the Stanford STORM method (5 personas, contradiction map, synthesis, peer review) to find upgrade routes, new-skill ideas, and bugs, then applies the high-confidence ones (skillsmith itself included). Triggers: 'sync my skills', 'upgrade a skill', 'create a skill', 'install my skills', 'run the skill routine', 'evolve my skills', '/skillsmith'. Scripts in scripts/; procedures in references/."
metadata:
  version: 1.1.7
---

# skillsmith — manage, sync, upgrade, create & auto-evolve Star Alliance skills (v1.1.7)

The control panel for the `star-alliance` repo. It keeps every skill **versioned**,
**Cowork-installable**, and **in sync** between the git repo and the on-device copies — and it
authors new skills (via the official `skill-creator`) already wired into those conventions.
As of **v1.1.0** it also **evolves the library on its own**: the `routine` mode runs daily, mines
your code + projects + sessions, researches every skill with the Stanford **STORM** method, and
autonomously ships the high-confidence upgrades, bug fixes, and new skills — **skillsmith itself
included**.

> **Full procedures live in `references/`.** This body is the router + the invariants; each mode
> points to its playbook. Kept slim on purpose — skillsmith eats its own dog food (description
> ≤1024 chars, body < 500 lines).

## The three locations

| Location | Path | Role |
|---|---|---|
| **repo** | `~/Documents/Claude/Projects/star-alliance` | Distribution source (git: `Attax-io/star-alliance`). Holds `VERSIONS.md`. |
| **global** | `~/.claude/skills` | What `/<skill>` actually loads. A stale global silently runs old code. |
| **project** | `<cwd>/.claude/skills` | Per-project overrides / localizations (may intentionally differ). |

**Canonical version = `metadata.version` in each `SKILL.md` frontmatter.** A *top-level* `version:`
is rejected by the Agent Skills frontmatter validator (allowed top-level keys: `name`, `description`,
`license`, `allowed-tools`, `metadata`, `compatibility`) — so the version lives under `metadata`,
which also matches what vendored skills already do. `VERSIONS.md` mirrors it. (`impeccable` is the
external exception — npx-managed, still ships a top-level `version:`; the reader falls back to it.)

## Modes

| Mode | What it does | Playbook |
|---|---|---|
| **sync** | Reconcile repo ↔ device. Compare versions, install repo-ahead skills onto the device, surface device-ahead / unversioned / diverged copies. Honors forks + externals. | `references/sync-playbook.md` |
| **upgrade** | Bump a skill's `version:`, regenerate `VERSIONS.md`, run the Cowork-compliance check, add a changelog entry, re-sync the device copy. | `references/upgrade-playbook.md` |
| **create** | Author a new skill via the official `skill-creator`, then make it upgradeable (version + registry + Cowork-validate + place in repo + optional install). | `references/create-playbook.md` |
| **routine** | The daily STORM loop. Harvest (code/projects/sessions) → research each skill with the 5-persona STORM method → write the ledger → autonomously apply ≥8/10 findings (upgrade / create / bug-fix, skillsmith last) → commit + push. Fully autonomous, gated, revertible, watchable. | `references/routine-playbook.md` + `references/storm-method.md` |

Cowork limits (the always-on invariant for every mode): `references/cowork-limits.md`.

## When to invoke

- `/skillsmith`, "manage my skills", "skill housekeeping"
- "sync my skills", "install my skills", "is the device up to date", "update the skill registry" → `sync`
- "upgrade the X skill", "bump X's version", "is X cowork-installable", "trim X's description" → `upgrade`
- "create a skill", "make a new skill", "turn this into a skill", "new skill for X" → `create`
- "run the skill routine", "evolve my skills", "improve my skills", "do the daily skill pass", "what should the routine change" → `routine`

Skip when: the user wants to *run* an existing skill (just invoke it), or is editing app code unrelated to the skills repo.

## Helper scripts (do the mechanical work; never edit frontmatter except where noted)

```sh
# Registry + Cowork-compliance (operates on the repo)
python3 skillsmith/scripts/skill_registry.py report     # per-skill table to stdout
python3 skillsmith/scripts/skill_registry.py check [NAME]# exit 1 on a HARD violation (desc>1024)
python3 skillsmith/scripts/skill_registry.py write       # regenerate VERSIONS.md

# Sync (repo ↔ device)
python3 skillsmith/scripts/skill_sync.py status          # versions across repo/global/project
python3 skillsmith/scripts/skill_sync.py plan            # bucketed recommendations (INSTALL/STAMP/PUSH/FORK/OK)
python3 skillsmith/scripts/skill_sync.py apply --skill NAME [--direction install|push] [--dry]

# Spec-compliance: relocate a stray top-level `version:` into metadata.version
python3 skillsmith/scripts/migrate_version.py --all --exclude impeccable [--dry]

# Routine (daily STORM loop)
python3 skillsmith/scripts/routine_scan.py --days 14 --out skillsmith/routine-logs/scan.json  # Stage A harvest (read-only)
bash    skillsmith/scripts/run_routine.sh                  # full run, headless + logged (what the LaunchAgent calls)
```

Paths default sensibly; override with `--repo` / `--global` / `--project`.
The LaunchAgent that fires `run_routine.sh` daily lives in `assets/com.attax.skillsmith-routine.plist` (install → `~/Library/LaunchAgents/`).

## Workflow

### Step 0 — Pick the mode

| Phrasing | Mode |
|---|---|
| "sync my skills", "install my skills", "update the registry", "is the device current" | `sync` |
| "upgrade X", "bump X's version", "make X cowork-installable" | `upgrade` |
| "create a skill", "make a new skill", "turn this into a skill" | `create` |
| "run the skill routine", "evolve my skills", "the daily pass", "what would the routine change" | `routine` |
| "skill status", "what versions / what's drifted", `/skillsmith` (bare) | run `skill_sync.py plan` + `skill_registry.py check`, then ask which mode |

### Mode: sync
Read **`references/sync-playbook.md`**. In short: `skill_sync.py plan` → for each bucket, INSTALL/STAMP via `apply --direction install` (repo→global); PUSH (device-ahead) is the upgrade flow — review the diff, don't blind-overwrite; FORK + external are manual (the cleanup stub gets guts-only updates; impeccable refreshes via `npx impeccable`); ADD-TO-REPO copies the device skill into the repo + versions it. Then `skill_registry.py write` and commit + push the repo.

### Mode: upgrade
Read **`references/upgrade-playbook.md`**. In short: make the edit → bump `metadata.version` (SemVer: PATCH fix / MINOR new capability / MAJOR breaking) → if the skill keeps a §Changelog or `references/version-history.md`, add an entry → `skill_registry.py check NAME` (fix any desc over 1024 chars or with `<`/`>` by trimming; fix body over ~10k words by extracting recipes to `references/` + leaving `Read references/X.md` pointers — never cut routing logic) → `skill_registry.py write` → re-sync the device copy (`skill_sync.py apply --skill NAME`) → commit + push.

### Mode: create
Read **`references/create-playbook.md`**. In short: run the official **`skill-creator`** workflow (capture intent → interview → write `SKILL.md` → optional eval; validate with skill-creator's `quick_validate.py`) to produce the new skill, THEN make it upgradeable: add `metadata.version: 1.0.0`, write a description ≤1024 chars with no `<`/`>`, keep the body lean (extract to `references/` early), drop it into the repo, run `skill_registry.py write`, and (if wanted) `skill_sync.py apply --skill NAME` to install it to the device. Commit + push.

### Mode: routine
Read **`references/routine-playbook.md`** + **`references/storm-method.md`**. The daily self-improvement loop. Five stages: **A Harvest** (`routine_scan.py` — read-only gather of skill versions/status + every mention & friction snippet across the repo, your projects, and session transcripts, + new-skill signals) → **B Research** (run the 4-step STORM method per active skill: 5-persona scan → contradiction map → synthesis dossier → peer review with 1–10 confidence; fan out as a Workflow when the active set is large) → **C Notebook** (write `references/routine-ledger/YYYY-MM-DD.md` incrementally — the committed, watchable memory) → **D Execute** (drive `upgrade-playbook`/`create-playbook` for every finding scoring **≥8/10** that clears the §R4 guards) → **E Report** (one labeled revertible commit per change, `git push`, Run Summary). **Autonomy = fully autonomous** (acts without asking, ≥8/10 gate, forks/externals edited with fork-aware handling per §R4.2, skillsmith self-edits last + validated per §R6). **Budget:** top ~3 actions / ~8 skills STORMed per run (§R5). **Schedule:** a native Claude Code routine `skillsmith-routine` (daily ~06:00 — shows in the app's *Routines* panel) per §R7; the LaunchAgent + `run_routine.sh` are an optional app-closed fallback (hard `$` cap). Watch via the completion notification, today's ledger entry, or run `/skillsmith routine` interactively to watch live.

## Invariants (every mode)

1. **Canonical version is `metadata.version`** (a top-level `version:` fails frontmatter validation). Bump it on every change; regenerate `VERSIONS.md` in the same commit.
2. **Cowork limits hold** (see `references/cowork-limits.md`): description ≤1024 chars with no `<`/`>` (HARD); only `name/description/license/allowed-tools/metadata/compatibility` allowed at top level; SKILL.md under 500 lines (ideal) and well under ~10k words; `references/`, `scripts/`, `assets/` don't count → extract there as the body grows.
3. **The device copy is what runs.** After any repo edit to a skill that loads from `~/.claude/skills`, re-sync the device copy or the old code keeps running (the `cleanup` §L24 lesson).
4. **Respect forks + externals.** Never blind-overwrite a documented fork (the `cleanup` stub, the `conquering-campaign` Cowork edition) or an external (`impeccable`, `npx impeccable`). The scripts skip them; you handle them per their playbook.
5. **Commit + push the repo** at the end (git remote `Attax-io/star-alliance`, `main`).
6. **Self-edits land last + validated.** When any mode — especially `routine` — edits **skillsmith itself**, do it after all other work, then re-validate (`skill_registry.py check skillsmith` + skill-creator `quick_validate.py`) and **revert on failure**. The running process already holds the old skillsmith; a self-edit only takes effect next run. Never hot-swap mid-run. (routine §R6.)
7. **Autonomous actions are gated + reversible.** `routine` only auto-applies findings with STORM peer-review confidence **≥8/10**; every change is its own commit on `main` (never force-push / rebase / `push origin <branch>:main`). A bad run is `git revert`.

## Versioning

This skill is versioned (`metadata.version` in frontmatter, currently **1.1.7**) and self-registers in `VERSIONS.md`. Bump it on every change — PATCH for fixes/wording, MINOR for a new mode or capability, MAJOR for a breaking workflow change — and add a §Changelog row. (The `routine` mode upgrades skillsmith through exactly this contract — see §R6.)

## Changelog

| Version | Date | Summary |
|---|---|---|
| **1.1.7** | 2026-06-20 | **Routine self-fix, run 5 — the message-author provenance lever runs 2–4 deferred as "needs turn-origin semantics, NOT reachable by lexical filters" turns out to be STRUCTURAL.** The routine's own Agent/Workflow fan-out injects user-role *dispatch prompts* (a STORM "MISSION: extract recurring HYGIENE DEBT…" prompt) that log as plain user turns and survived every prior filter. `routine_scan.py` `message_texts` now drops a user turn carrying ANY of three machine-origin markers, none of which a genuine typed turn has: **`isSidechain: True`** (the subagent's OWN session — the dispatch prompt is that subagent's first user turn; the canonical subagent marker), **`sourceToolAssistantUUID`**, or **`toolUseResult`** (the parent session's record of a tool call — tool_result blobs + the dispatched prompt the parent logged). **Ground-truthed** on a Lex session: 6/6 genuine Atta turns carry NONE of these; every machine turn (incl. all 4 logged copies of the dispatch prompt) carries one. **Verified by before/after scan:** friction **6 → 3 snippets** — the 3 cleanly-tagged self-dispatch prompts (`cleanup`×3) dropped, 6/6 real turns preserved. **Residual (deferred ~5/10):** 3 structurally-UNTAGGED survivors — a pasted vault-log/`MEMORY.md` line, a `"Task: …"`-prefixed dispatch prompt, and a numbered analysis-report line — that log as clean user turns with zero machine marker; separating these needs lexical dispatch/paste-format heuristics (fragile), the last and hardest tail. | **Routine self-fix, run 4 — resolves the class-(B) usage-vs-topic residual v1.1.5 deferred as "not reachable by path/keyword/meta filters."** Two changes to `routine_scan.py` reframe friction as a *live-usage* signal, not a *mention* signal: (1) **friction is now SESSION-TRANSCRIPT-USER-TURN-ONLY** — project files (app `docs/`, vault-logs, memory) feed `mention_total` (topical interest → STORM ranking) but can no longer contribute friction. A skill name in a vault-log is a *domain topic* (cleanup the activity, performance the metric, supabase the product) sitting next to ordinary software-friction words; the file *describes* work, it doesn't *exercise* the skill. This alone dropped **32 of 36** snippets — the project-file half prior runs kept trying to path/keyword-filter. (2) New **`is_skill_ref()` usage gate** on the surviving session friction: the name must appear as an actual skill/command reference — the slash-command `/name` or "name skill/mode/command" — not a bare domain noun. The looser "run/use/invoke name" verb-form is rejected on purpose because for a product-named skill it collides hard ("**Use the Supabase** MCP" = the product, "the cleanup **runs**" = the activity). Higher precision, lower recall is the correct trade for an autonomous signal. Also extended `SKILL_META` (drops `**/name/SKILL.md` path globs) and added a definitional/locational user-line drop ("read the X skill", "the skill file is under <path>"). **Verified:** friction collapsed **36 → 6 snippets, frictionful 8 → 2** (`cleanup`, `dev-server`); every survivor genuinely references the skill-as-skill ("the cleanup skill/mode should catch X" — real upgrade hints — plus one `dev-server` pasted-vault-log edge). The bare-domain-noun false positives (`supabase`×6, `performance`, `bug-fix-workflow`, most `cleanup`) are gone. Cleared §R4.5 cooldown via the correctness exception (a ~100%-noise friction signal is a Stage-A correctness defect, not polish). **Residual (low-volume edges, deferred):** a user *pasting* a vault-log line that says "dev-server skill", and the routine's OWN prior STORM dispatch prompts ("the cleanup skill should add…") — both read as genuine skill references; separating them needs author/turn-origin semantics, not lexical filters. |
| **1.1.5** | 2026-06-20 | **Routine self-fix, run 3 — closes the two residual friction classes v1.1.4 deferred + a third it missed.** `routine_scan.py`: (1) **`.claude/` + `worktrees/` added to `SKIP_DIRS`** — agent worktrees (`…/.claude/worktrees/agent-*/`) are throwaway duplicate repo checkouts whose campaign docs were the dominant *project-file* noise (`cleanup`×3, `supabase`×3 traced straight to them); the sessions root `~/.claude/projects` is walked from inside `.claude`, so subdir-only pruning never touches it. (2) **`message_texts` now drops `isMeta: True` transcript messages** — the robust signal for HARNESS-INJECTED content (the available-skills/agents catalog echoes each skill's *description* verbatim as a standalone ≤1024-char block; `lex_cleanup`'s desc — a device skill not even in repo inventory — was mis-flagged as `vault-log-compliance` ×6). This subsumes the string-marker drops and catches the *headerless* echo a marker can't. (3) The string-marker drop (`base directory for this skill:`, `available for use with the Skill tool`, `Available agent types`, `<scheduled-task`) now runs on BOTH string- and list-content messages (v1.1.4 guarded only the list branch, so the catalog/self-prompt — which arrive as STRING content — slipped through). (4) Per-line frontmatter `description:` guard (belt-and-suspenders for any spec-desc echo outside `.claude/`). **Verified:** friction collapsed from the 12-skill/~75-snippet noise baseline to **8 frictionful / 36 snippets**, all genuine — `skillsmith`/`impeccable` (self-prompt) and `vault-log-compliance` (catalog echo) dropped off the list entirely; surviving entries are real `docs/` prose or genuine user instructions. **Deferred (unchanged from run 2):** class (B) topical/word-collision — `supabase`/`performance` matching legitimate `docs/` prose by skill-name-as-topic; needs a usage-vs-topic semantic gate (require a request verb co-occurring inside a typed user message), not reachable by path/keyword/meta filters. |
| **1.1.4** | 2026-06-20 | **Routine self-fix (carried the 2026-06-20 "next-best proposal" to done):** `routine_scan.py` now applies a **source-class filter** so the `frictionful` signal stops being ~100% noise. (1) Files that are skill/command **definitions** (`/.claude/skills\|commands/`), **config permission lists** (`settings.json`/`settings.local.json`), or **generated log indexes** (`vault-logs/INDEX.md`) are skipped entirely — a skill *described* isn't a skill *used* (same principle that already excludes the repo). (2) Per-line **boilerplate** ("Docs consulted", "delegate to", "invoke the X skill", "per X-workflow", "read CLAUDE.md") is dropped from friction. (3) Session transcripts that inject a skill's full SKILL.md (`Base directory for this skill:` header + changelog rows that literally say "bug"/"fix") are dropped at the message level — **185 such injections** were the dominant residual. Verified: noise snippets fell from the all-definitional baseline (cleanup 6→0 own-DONE-items, skillsmith 6→2 self-changelog gone, supabase `.claude` matches gone, transactions/vault-log delegate-boilerplate gone). **Deferred (ledger 2026-06-20, run 2):** two newly-surfaced residual classes — (A) the **system available-skills block** echoes a skill's *description* into the transcript (vault-log-compliance still shows 6 `lex_cleanup`-desc lines; catchable, different vector from the `Base directory` header), and (B) **topical/word-collision** in app docs (`supabase`/`performance`/`dev-server` matching legitimate `docs/` prose; genuinely hard — needs a usage-vs-topic semantic gate). |
| **1.1.3** | 2026-06-20 | **Bug fix (found by the routine itself, day 1):** `routine_scan.py` over-counted quoted descriptions — it stripped the surrounding quotes but left internal `\"`-escapes as 2 chars each, so a quoted desc with N escapes read N chars too long. `cleanup` measured **1025 → phantom `desc>1024` flag** while the authoritative `skill_registry.py check` (which unescapes) read **991 ✓ lean**. Fixed by mirroring the registry's `.replace('\\"', '"')`. The harvest's desc/body status labels now agree with the Cowork gate. Deferred (ledger 2026-06-20): the friction detector keyword-matches the skills' own docs / vault-log "Docs consulted" boilerplate / settings.json permission lines, so "frictionful" is dominated by noise — needs a source-class filter. |
| **1.1.2** | 2026-06-20 | Scheduler moved to a **native Claude Code routine** (`skillsmith-routine`, daily `0 6 * * *`) — it now shows in the app's *Routines* panel beside the other routines, instead of an invisible macOS LaunchAgent. The LaunchAgent (`run_routine.sh` + plist) is demoted to an optional app-closed fallback (it keeps the hard `--max-budget-usd` cap). §R7 rewritten; first run pre-approves tools via "Run now". |
| **1.1.1** | 2026-06-20 | `routine` may now upgrade the fork/external skills too (`cleanup`, `conquering-campaign`, `impeccable`) — Atta opted them in. Edited with fork-aware handling (§R4.2): forks per `sync-playbook.md` §S3 (never blind-overwrite the stub with the monolith), `impeccable` via `npx impeccable` refresh only. Same ≥8/10 gate applies. |
| **1.1.0** | 2026-06-20 | Added the **`routine`** mode — a daily, fully-autonomous STORM-driven self-improvement loop (Harvest → STORM research → ledger → execute ≥8/10 findings → commit/push). New files: `references/routine-playbook.md`, `references/storm-method.md` (Stanford STORM adapted to skill evolution), `references/routine-ledger/` (committed memory), `scripts/routine_scan.py` (read-only harvest of skills × code/projects/sessions), `scripts/run_routine.sh` (headless runner, `--max-budget-usd` capped), `assets/com.attax.skillsmith-routine.plist` (daily LaunchAgent ~06:00). Scope = repo + all `~/Documents/Claude/Projects` + session transcripts. Guards: forks/externals never auto-edited, Cowork-clean-or-revert, cooldown, self-upgrade-last (§R6). Bumps skillsmith itself through its own `upgrade` contract. |
| **1.0.0** | 2026-06-15 | Initial release. Three modes — `sync` (repo↔device reconcile), `upgrade` (version bump + registry + Cowork-compliance), `create` (skill-creator → upgradeable). Scripts: `skill_registry.py` (report/write/check), `skill_sync.py` (status/plan/apply), `migrate_version.py` (top-level → metadata.version). Encodes the conventions established across the 2026-06-15 skills-repo work (canonical `metadata.version`, `VERSIONS.md` registry, Cowork limits incl. the description angle-bracket ban, fork/external exceptions). |

## Related
- `references/sync-playbook.md` · `references/upgrade-playbook.md` · `references/create-playbook.md` · `references/cowork-limits.md`
- `references/routine-playbook.md` · `references/storm-method.md` · `references/routine-ledger/` — the `routine` mode + its STORM engine + its committed memory.
- `scripts/routine_scan.py` (harvest) · `scripts/run_routine.sh` (runner) · `assets/com.attax.skillsmith-routine.plist` (daily LaunchAgent).
- `VERSIONS.md` — the registry skillsmith maintains.
- `README.md` — the repo's versioning + Cowork convention (skillsmith automates it).
- The official `skill-creator` skill — `create` mode delegates to its authoring + validation workflow.
