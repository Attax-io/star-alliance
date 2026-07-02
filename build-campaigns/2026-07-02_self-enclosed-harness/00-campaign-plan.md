---
mode: BUILD
scope: full
status: completed
approval_cadence: hybrid
predecessor: 2026-07-02_self-enclosed-intent-audit (findings, this session)
p0_result: DONE — _saroot.resolve_root() (code-location-first); 5 gates rewired; compiles
p1_result: DONE (repo side) — install.sh Tier3 copies full roster + re-points root; RUN-against-Lex handed off
p2_result: DONE — executor-enforce _p2_half_installed() fail-closed on missing models.json; silent in home repo
p3_result: DONE — butler-skill-gate _is_foreign_bare_skill() provenance refusal; tested
p4_result: DONE — routing-enforce allowlist deny-unknown; thinker-gate fail-closed on missing member file
p5_result: DONE — signals.py sentinel dir aligned + turn-start clears xp-workflow-*; spawn-log.py added+registered
p6_result: DONE (workflow-adopt) — absorb.py scan_workflows/propose_workflows; skill_sync --apply deferred
p7_result: DONE — full compile sweep; conformity_check zero AG/VER/RG/FB/P drift; gate smoke tests pass; vault-log filed
w0_enabled: "no — Cowork (Ollama not reachable)"
workflow_available: "no — Cowork (deterministic Workflow tool absent)"
workflow_emitted: "no — tool absent (portability)"
preview_verification: n/a
verification_class: code-only
current_phase: 7
phases_completed: [P0, P1, P2, P3, P4, P5, P6, P7]
phases_remaining: []
goal_line: >
  Star Alliance installs clean into any project and self-encloses on landing — STAR_ALLIANCE_ROOT
  resolves dynamically, install lands agents+dispatch+settings, gates fail CLOSED on missing config,
  the skill gate refuses non-repo skills, routing denies unknown agents, telemetry counts honestly;
  conformity_check.py green, Lex runs a full high-stakes turn end to end, vault-log written.
  Stop after 20 turns if not met.
standing_instructions: >
  Lead every response to the Guild Master in plain English (CLAUDE.md).
  Full branded harness + Hermes carried on every landing (Guild Master decision, 2026-07-02).
  Claude models are the brain; Hermes/MiniMax the doer. Supabase writes stay with Claude via MCP.
---

# Campaign — Make Star Alliance Self-Enclosed & Portable

## Goal (plain English)

Today the harness is *self-equipped* (its own skills and workflows are real and strong) but not
*self-enclosed*. When it lands in a new project it doesn't reliably run, it lets outside skills and
agents in, and its own usage logs undercount. This campaign makes the full branded, Hermes-carrying
harness **install cleanly anywhere, refuse foreign craft once landed, and tell the truth about what
it ran** — with Lex Council as the first real landing.

## What the corrected audit changed (why this plan is shorter than feared)

Two of the intent audit's "must build" items were already built and were misread:

- **The gates are armed.** They're dispatched through `sa-pretool.py`'s route table, not listed
  individually in `settings.json`. okf-gate, routing-enforce, thinker-gate, butler-skill-gate all
  fire. → No "arm the gates" phase needed; the work is changing *how* they decide (fail-closed +
  provenance), not turning them on.
- **The project installer exists.** `star-alliance-arsenal/install.sh` (Tier 3) already copies
  skills, `dispatch.py`, the arsenal, evolution, and merges CLAUDE.md into a target as a managed
  block. `okf_audit` already walks up to any repo's `workflows.json`, so it travels. → No "build a
  deploy script" phase; the work is fixing what it doesn't yet set (the root path, the agents dir).

The genuinely-weak axes the audit got right and this campaign targets: **portability (one hard-coded
path), isolation-enforcement (P4), telemetry-honesty (P2), and the Lex landing blockers.**

## Lessons carried from memory / audit (G4 / P8)

- `[[two-devices-path-mismatch]]` — `atta` vs `attaselim` home paths break synced config. The
  hard-coded `STAR_ALLIANCE_ROOT` is a live instance of exactly this. Fix drives Phase 0.
- Gates **fail OPEN** on missing config today — correct for the home repo, wrong for a foreign one.
- Hermes carried on every landing (Guild Master) → the landing kit must ship the doer path, not a
  Claude-only core.

## Waves

- **W0** — skipped (Cowork; no Ollama).
- **W1 (recon, read-only)** — confirm the exact call sites each phase touches (root-resolution
  helpers, gate config-load blocks, sentinel dirs, install.sh settings-write step). Explore agents.
- **W2 (design)** — draft the shared `config_presence` guard + the dynamic-root helper as single
  primitives every gate imports (P5 consolidation — do NOT patch each gate inline).
- **W3 (execution)** — phases below, each an independently shippable slice, doer work via Hermes.
- **W4 (synthesis)** — conformity_check, Lex end-to-end turn, vault-log, memory, cleanup.

## Phase list (each independently deployable)

| Phase | Goal | Risk | Deployable result |
|---|---|---|---|
| **P0 — Portability root** | `STAR_ALLIANCE_ROOT` resolves dynamically (script location → `CLAUDE_PROJECT_DIR` → cwd) instead of a hard-coded home path; settings.json stops hard-coding it | 🟢 green | Harness stops silently breaking on the `attaselim` device and in Lex |
| **P1 — Landing kit** | `install.sh` Tier-3 + `install_agents.py` write the target's `.claude/agents/`, ship `dispatch.py`, and emit a settings.json with the resolved root. Run against Lex | 🟠 amber | Lex actually runs a high-stakes turn (agents spawnable, dispatch present, root set) |
| **P2 — Fail-closed guard** | One shared `config_presence` guard: when models.json / workflows.json / roster is absent, gates BLOCK, not wave through. Every gate imports it | 🟠 amber | In a foreign or half-installed repo the harness refuses to run half-open |
| **P3 — Skill provenance refusal** | `butler-skill-gate` (+ unity/member skill gates) reject any skill whose SKILL.md is not under the repo's own `star-alliance-skills/`. Add the doctrine line | 🟠 amber | The core P4 mechanism: the guild refuses global craft |
| **P4 — Agent allowlist** | `routing-enforce` denies unknown (non-roster) subagents instead of waving them through (lines 144-145); `thinker-gate` fails CLOSED on unknown/error | 🟠 amber | No foreign agent spawns under guild authority |
| **P5 — Telemetry honesty** | (a) unify the workflow sentinel dir (`turn-start.py` clears `.claude/state/` but `once_per_turn()` reads `state/`); (b) log skill *activation*, not just `tool_name=="Skill"`; (c) PostToolUse on Task/Agent → dispatch-log | 🟢 green | Logs stop lying; skill/agent/workflow counts become real |
| **P6 — Absorption (optional)** | `skill_sync --apply` auto-copies detected add-to-repo skills; extend `absorb.py` with a workflow-adopt branch | 🟢 green | Inward absorption becomes one command, not manual |
| **P7 — Verify & close** | `conformity_check.py` green (AG/VER/P/RG/FB/PD); one full Lex high-stakes turn end-to-end; vault-log; memory entries; dead-code sweep | — | Campaign complete, intent met |

## Per-task model-assignment table (P2)

| Task | Wave | Run-by | Brain | Doer | Output |
|---|---|---|---|---|---|
| Recon: root helpers + gate config loads + sentinel dirs + install settings-step | W1 | Explore ×2 (parallel) | Sonnet | — | `01-recon.md` |
| Design shared `resolve_root()` + `config_presence` guard | W2 | Strategist | Opus | — | `02-primitives.md` |
| P0 root fix | W3 | specialist → dispatch | Sonnet | Hermes Developer | `10-p0.md` |
| P1 landing kit (install.sh + install_agents) | W3 | specialist → dispatch | Opus | Hermes Developer | `11-p1.md` |
| P2 fail-closed guard (all gates import) | W3 | specialist → dispatch | Opus | Hermes Developer | `12-p2.md` |
| P3 skill provenance refusal | W3 | specialist → dispatch | Opus | Hermes Developer | `13-p3.md` |
| P4 agent allowlist / thinker fail-closed | W3 | specialist → dispatch | Opus | Hermes Developer | `14-p4.md` |
| P5 telemetry (3 sub-fixes) | W3 | specialist → dispatch | Sonnet | Hermes Developer | `15-p5.md` |
| P6 absorption (optional) | W3 | specialist → dispatch | Sonnet | Hermes Developer | `16-p6.md` |
| Synthesis: conformity + Lex turn + vault-log | W4 | Butler + Strategist | Opus | — | `99-risk-sweep.md` |

## Consolidation plan (P5 — extract before patching N gates)

- **`resolve_root()`** — ONE helper. Every gate + tool that reads `STAR_ALLIANCE_ROOT` calls it.
  Do not sprinkle `os.environ.get(...) or os.getcwd()` across 12 files (that's the current smell).
- **`config_presence(required=[...])`** — ONE guard used by P2. Gates call it and block on absence
  rather than each re-implementing a try/except that returns `{}` and falls open.

## Cleanup plan (candidates only — grep-proof authorises the rm at §5.1)

- `guild-routing-gate.sh.bak`, `.bak2`, `workflows.json.bak` — confirm superseded, then remove.
- Any per-gate inline root-resolution once `resolve_root()` lands.

## Forced single-question gate

- **P1 writes into Lex (a second repo).** Before the installer touches the Lex folder, fire ONE
  `AskUserQuestion` confirming the exact Lex path and that it may write there — writing into a
  second project is irreversible-ish and outside this repo's blast radius.

## Success criteria (Q9)

1. On this `attaselim` device, no tool fails because `STAR_ALLIANCE_ROOT` points at a missing path.
2. Running the installer against Lex leaves `.claude/agents/` populated, `dispatch.py` present, and
   `STAR_ALLIANCE_ROOT` resolving to Lex — and Lex completes one full high-stakes turn.
3. A skill placed outside `star-alliance-skills/` is refused by the skill gate.
4. An unknown (non-roster) subagent spawn is denied by routing-enforce.
5. In a repo with config removed, the gates BLOCK instead of waving through.
6. Workflow/skill/agent telemetry counts match what actually ran in a test turn.
7. `conformity_check.py` exits green; vault-log written; memory entries saved.

## Sequencing note

P0 → P1 unblock Lex and are low-risk mechanical fixes — do them first and you have a running second
landing within the day. P2–P4 are the "self-enclosed" heart (half-day each, ship independently).
P5 is cheap honesty. P6 is optional polish. Nothing here is a big-bang; every phase deploys alone.
