# Star Alliance → Hermes Migration Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Move the Star Alliance multi-agent guild from Claude Code's infrastructure (`.claude/` hooks, agents, CLAUDE.md) to Hermes Agent's native primitives (profiles, delegate_task, cron, skills, AGENTS.md, MCP).

**Architecture:** Star Alliance is a multi-agent system with 9 member personas, 44 skills, a model arsenal (brain/doer/critic/bench seats), 30+ workflows, a hook-based gate system (20+ Python hooks), an evolution engine, and a Tauri dashboard. The migration maps each Claude Code mechanism to its Hermes equivalent — some are 1:1, some need rearchitecting, some are already done (skills are symlinked).

**Tech Stack:** Python 3.11, Hermes Agent, JSON/YAML config, shell scripts, Tauri (dashboard stays as-is)

---

## Current State Summary

### What's already migrated
- **44 skills** — already symlinked from `star-alliance-skills/` into `~/.hermes/skills/star-alliance/`. Hermes discovers them. ✅ Done.

### What needs migration (7 surfaces)

| # | Surface | Claude Code | Hermes Target | Effort |
|---|---------|-------------|---------------|--------|
| 1 | Project instructions | `CLAUDE.md` (148 lines) | `AGENTS.md` (or `.hermes.md`) | Low — rename + adapt |
| 2 | Agent personas | `.claude/agents/*.md` (9 files) | Hermes profiles (9 profiles) | High — each member becomes a profile |
| 3 | Hooks/gates (20+) | `.claude/hooks/*.py` + `settings.json` | Hermes has no hook system → MCP server + cron + shell-hooks | High — rearchitect |
| 4 | Model routing | `star-alliance-arsenal/models.json` + `summon.py` | Hermes provider config + `delegate_task` model pinning | Medium |
| 5 | Workflows | `workflows.json` (30+ workflows) | Hermes cron + delegate_task patterns | Medium |
| 6 | Build system | `build.py` + `tools/conformity_check.py` | Stays as-is (Python scripts, tool-agnostic) | None |
| 7 | Dashboard | Tauri app (`desktop/`, `app.js`, `app.css`) | Stays as-is (reads generated `guild-data.js`) | None |

### What stays unchanged
- `build.py` — pure Python, no Claude Code dependency
- `tools/conformity_check.py` — pure Python
- `guild/*.py` — pure Python scripts
- `evolution/*.py` — pure Python
- `star-alliance-skills/` — already symlinked into Hermes
- `star-alliance-members/*.md` — source-of-truth member files (not generated)
- `star-alliance-arsenal/models.json` — source-of-truth model registry
- `workflows.json` — source-of-truth workflow definitions
- `data/*.json` — source-of-truth data
- Dashboard (Tauri app, `app.js`, `app.css`, `index.html`)

---

## Migration Strategy: Two Tracks

### Track A: Immediate (project context + member profiles)
Gets Star Alliance running inside Hermes with basic member dispatch. No hooks, no gates — just the personas and project rules.

### Track B: Advanced (hooks → MCP, workflows → cron, model routing)
Replaces Claude Code's hook system with Hermes-native equivalents. This is the hard part.

---

## Track A: Immediate Migration

### Task A1: Create `AGENTS.md` from `CLAUDE.md`

**Objective:** Port the project instructions to Hermes's context file format.

**Files:**
- Create: `AGENTS.md` (in project root)
- Source: `CLAUDE.md` (existing, 148 lines)

**Steps:**

1. Read `CLAUDE.md` fully.
2. Create `AGENTS.md` with the same content, but with these adaptations:
   - Remove Claude Code-specific references: `CLAUDE_PROJECT_DIR`, `.claude/agents/`, `.claude/hooks/`, `CLAUDE_CODE_CHILD_SESSION`
   - Replace `.claude/agents/*.md` references with `~/.hermes/profiles/<member-name>/` 
   - Replace `guild/install_agents.py` references — agents are now Hermes profiles, not generated files
   - Replace hook references with "Hermes MCP server (see `server/star_alliance_mcp.py`)" or "not yet migrated"
   - Replace `$CLAUDE_PROJECT_DIR` with `$STAR_ALLIANCE_ROOT` (already set in settings.json env)
   - Replace "Task tool" with "delegate_task"
   - Replace "subagent" with "delegate_task child"
   - Keep the plain-English, reading-discipline, guild-conduct, and self-execution sections as-is
   - Keep the single-source-of-truth section, but update generated-file paths
3. Verify: `cat AGENTS.md | head -20` shows correct content.
4. Keep `CLAUDE.md` in place for now (Hermes reads `AGENTS.md` first per priority order).

**Commit:** `docs: create AGENTS.md from CLAUDE.md for Hermes migration`

---

### Task A2: Create the 9 Hermes profiles

**Objective:** Each Star Alliance member becomes a Hermes profile with its own session, model, skills, and personality.

**Files:**
- Source: `star-alliance-members/*.md` (9 files)
- Source: `star-alliance-members/README.md`
- Source: `data/members-meta.json` (member presentation data)
- Target: `~/.hermes/profiles/star-alliance-<member>/` (9 profiles)

**The 9 members** (from the repo):
1. the-butler (routing, plain English, Guild Master interface)
2. the-architect (system design, domain modeling)
3. the-developer (code execution)
4. the-designer (UI/UX design)
5. the-strategist (planning, campaigns)
6. the-translator (legal translation)
7. the-herald (marketing, comms)
8. the-merchant (trading — stub/reserved)
9. the-quartermaster (release, verification)

**Steps per member:**

1. Read the member source file (e.g., `star-alliance-members/the-architect.md`).
2. Read the corresponding `.claude/agents/the-architect.md` (generated, stripped of source-of-truth metadata).
3. Create a Hermes profile:
   ```bash
   hermes profile create star-alliance-architect --clone-from default
   ```

4. Configure the profile:
   ```bash
   # Set the member's model (from the member file's `model:` field)
   hermes config set model.default sonnet --profile star-alliance-architect
   
   # Set the member's personality (from the member description)
   hermes personality set "You are the Architect, a senior systems architect..." --profile star-alliance-architect
   ```

5. Create the profile's `AGENTS.md` (loaded when running in the project dir):
   ```bash
   # ~/.hermes/profiles/star-alliance-architect/AGENTS.md
   # Contains the member's full persona, skill drills, and conduct rules
   ```

6. Enable only the member's skills (from the member file's `skills:` list):
   ```bash
   hermes skills config --profile star-alliance-architect
   # Enable only: transactions-domain-model, legal-rule-modeling, etc.
   ```

7. Set the member's toolsets (from the member file's `tools:` list — mapped from Claude names to Hermes toolsets):
   | Claude Tool | Hermes Toolset |
   |-------------|----------------|
   | Read, Edit, Write | `file` |
   | Bash | `terminal` |
   | Task | `delegation` |
   | (add for all) | `web`, `search`, `browser`, `skills`, `memory`, `todo` |

8. Verify the profile:
   ```bash
   hermes --profile star-alliance-architect doctor
   hermes --profile star-alliance-architect config
   ```

**Commit:** `feat: create 9 Hermes profiles for Star Alliance members`

---

### Task A3: Create the Butler routing profile

**Objective:** The Butler is the main interface — it routes requests to other members. This needs special setup.

**Files:**
- Source: `star-alliance-members/the-butler.md` (if it exists — may be defined in CLAUDE.md instead)
- Source: `.claude/hooks/guild-routing-gate.sh` (current routing logic)
- Target: `~/.hermes/profiles/star-alliance-butler/`

**Steps:**

1. Read the guild routing gate to understand current routing logic:
   ```bash
   cat .claude/hooks/guild-routing-gate.sh
   ```

2. Create the Butler profile:
   ```bash
   hermes profile create star-alliance-butler --clone-from default
   ```

3. Configure the Butler as the default profile for Star Alliance work:
   ```bash
   hermes config set model.default sonnet --profile star-alliance-butler
   ```

4. Create the Butler's `AGENTS.md` with:
   - The plain-English communication rules from CLAUDE.md
   - The routing logic (which member to dispatch for which task)
   - The Butler's persona
   - Instruction to use `delegate_task` to dispatch to other members

5. The Butler's routing table (derived from `members-formation` skill + `guild-routing-gate.sh`):

   | Request type | Dispatch to |
   |--------------|-------------|
   | System design, DB, schema | Architect |
   | Code, bugs, implementation | Developer |
   | UI, design, visuals | Designer |
   | Planning, campaigns | Strategist |
   | Legal translation | Translator |
   | Marketing, comms | Herald |
   | Trading, markets | Merchant |
   | Release, verification | Quartermaster |

6. Set up the Butler to run from the project directory:
   ```bash
   hermes profile use star-alliance-butler
   # Or alias: hermes profile alias sa-butler
   ```

**Commit:** `feat: create Butler routing profile with member dispatch table`

---

### Task A4: Update `build.py` and `guild/install_agents.py`

**Objective:** The build system currently generates `.claude/agents/*.md`. Update it to generate profile config files for Hermes instead.

**Files:**
- Modify: `guild/install_agents.py` (agent installer)
- Modify: `build.py` (dashboard data generator — minimal changes)

**Steps for `install_agents.py`:**

1. Read `guild/install_agents.py` fully.
2. Replace the output target:
   - **Old:** writes to `.claude/agents/<member>.md`
   - **New:** writes to `~/.hermes/profiles/star-alliance-<member>/AGENTS.md`
3. Keep the input source the same (`star-alliance-members/*.md`).
4. Add logic to also write `config.yaml` per profile:
   ```yaml
   # ~/.hermes/profiles/star-alliance-architect/config.yaml
   model:
     default: sonnet
     provider: anthropic
   personality: "You are the Architect..."
   ```
5. Test: `python3 guild/install_agents.py` — verify it creates profile dirs.
6. Run conformity check: `python3 tools/conformity_check.py` — should still pass (it checks agents==members; update it to check profiles==members instead).

**Steps for `conformity_check.py`:**

1. Read `tools/conformity_check.py`.
2. Update the `AG` (agents) check:
   - **Old:** `.claude/agents/*.md` == `star-alliance-members/*.md`
   - **New:** `~/.hermes/profiles/star-alliance-*/AGENTS.md` == `star-alliance-members/*.md`
3. Keep all other checks the same (VER, P, RG, FB).

**Commit:** `feat: update install_agents.py to generate Hermes profiles`

---

### Task A5: Verify Track A

**Objective:** Confirm the basic migration works end-to-end.

**Steps:**

1. Run the build:
   ```bash
   cd ~/Documents/Claude/Projects/star-alliance
   python3 build.py
   python3 tools/conformity_check.py
   ```

2. Start the Butler profile:
   ```bash
   hermes --profile star-alliance-butler
   # Or: hermes -p star-alliance-butler
   ```

3. Send a test message that should route to the Architect:
   > "Design a database schema for a user management system"

4. Verify:
   - The Butler receives the message
   - The Butler dispatches to `star-alliance-architect` via `delegate_task`
   - The Architect profile loads with correct skills
   - The Architect responds with a schema design
   - The Butler translates the response to plain English

5. Test the dashboard still works:
   ```bash
   open desktop/dist/index.html
   # Or: python3 -m http.server 8000 && open http://localhost:8000
   ```

**Commit:** `test: verify Track A migration (profiles + routing + dashboard)`

---

## Track B: Advanced Migration

### Task B1: Create the Star Alliance MCP Server

**Objective:** Replace Claude Code's hook system (20+ Python scripts) with a single Hermes MCP server that exposes the gate logic as tools.

**Files:**
- Create: `server/star_alliance_mcp.py` (MCP server)
- Source: `.claude/hooks/*.py` (20+ hook scripts)

**Hook → MCP Tool mapping:**

| Claude Code Hook | When | Hermes MCP Tool |
|-----------------|------|-----------------|
| `guild-routing-gate.sh` | UserPromptSubmit | `sa_route_request` — returns which member to dispatch to |
| `turn-start.py` | UserPromptSubmit | `sa_turn_start` — logs turn start, sets context |
| `sa-pretool.py` | PreToolUse:* | `sa_pre_check` — runs before any tool call (safety, weapon gate) |
| `executor-enforce.py` | PreToolUse:* | `sa_executor_check` — enforces Butler can't write files directly |
| `build-mark.py` | PostToolUse:Edit\|Write | `sa_build_mark` — marks build as stale after edits |
| `precompact-snapshot.py` | PreCompact | `sa_snapshot` — saves context before compression |
| `turn-cost.py` | Stop | `sa_turn_cost` — logs turn cost |
| `verify-gate.py` | Stop | `sa_verify` — runs independent critic on the diff |
| `delegation-gate.py` | Stop | `sa_delegation_check` — enforces doer was used for bulk work |
| `thinker-attest.py` | Stop | `sa_thinker_attest` — logs which model thought |
| `turn-finalize.sh` | Stop | `sa_turn_finalize` — commits if all gates pass |
| `workflow-banner-enforcer.py` | Stop | `sa_workflow_banner` — enforces workflow banner |
| `plain-english-nudge.py` | Stop | `sa_plain_english` — nudges if response is too technical |
| `destructive-gate.py` | PreToolUse:Bash | `sa_destructive_check` — blocks destructive git ops |
| `thinker-gate.py` | PreToolUse:Task\|Agent | `sa_thinker_check` — blocks model override |
| `weapon-gate.py` | (within summon.py) | `sa_weapon_gate` — validates model choice |

**Important:** Hermes doesn't have a `PreToolUse`/`PostToolUse` hook system like Claude Code. The MCP server exposes these as **tools the agent calls explicitly** — or better, as a **cron job** that runs after each turn. Some gates (destructive, executor) need to be preventive — those can't be directly ported without a hook system.

**Realistic approach:**
- **Preventive gates** (executor-enforce, destructive-gate, thinker-gate): These BLOCK actions before they happen. Hermes has `approvals.mode` (manual/smart/off) but no custom hook injection. Options:
  - (a) Wrap these into a custom Hermes tool that members must call before editing — unreliable (agent might skip it).
  - (b) Use Hermes's `tirith_enabled` (security scanner) for destructive commands — partial coverage.
  - (c) Accept that preventive gates are lost in migration. The Butler's AGENTS.md instructs it to use delegate_task for file edits instead of doing them directly. The verify-gate (post-turn critic) catches violations.
  - **Recommendation: (c) for now, with (a) as a manual safety net.**

- **Post-turn gates** (verify-gate, delegation-gate, turn-cost, thinker-attest, turn-finalize, workflow-banner, plain-english): These run after the turn. Hermes cron can't trigger mid-conversation. Options:
  - (a) Expose as MCP tools the Butler calls at the end of each turn — works but relies on the agent remembering to call them.
  - (b) Use Hermes's `checkpoints` feature — saves state before/after turns, can rollback.
  - (c) Run as a post-turn script via a wrapper.
  - **Recommendation: (a) — expose as MCP tools, instruct the Butler to call `sa_verify` before finishing.**

**Steps:**

1. Create `server/star_alliance_mcp.py`:
   ```python
   #!/usr/bin/env python3
   """Star Alliance MCP Server — exposes guild gates as MCP tools."""
   
   # Tools to expose:
   # - sa_route_request(prompt: str) -> {member: str, reason: str}
   # - sa_verify(diff: str) -> {verdict: pass|block, findings: str}
   # - sa_delegation_check(turn_log: str) -> {verdict: pass|block}
   # - sa_turn_cost(model: str, tokens: int) -> {logged: bool}
   # - sa_turn_finalize(gates_passed: list) -> {committed: bool}
   # - sa_snapshot(summary: str) -> {path: str}
   # - sa_plain_english_check(response: str) -> {nudge: str|none}
   # - sa_build_mark() -> {stale: bool}
   ```

2. Register the MCP server with Hermes:
   ```bash
   hermes mcp add star-alliance --command "python3 $STAR_ALLIANCE_ROOT/server/star_alliance_mcp.py"
   hermes mcp test star-alliance
   ```

3. Test each tool individually via `hermes mcp test star-alliance`.

**Commit:** `feat: create Star Alliance MCP server with guild gate tools`

---

### Task B2: Port the verify-gate (independent critic)

**Objective:** The most important gate — an independent model (GLM-5.2) reviews every turn's diff before it ships. This is the core quality mechanism.

**Files:**
- Source: `.claude/hooks/verify-gate.py`
- Source: `evolution/verdict.py`
- Target: `server/star_alliance_mcp.py` (add `sa_verify` tool)

**Steps:**

1. Read `verify-gate.py` and `evolution/verdict.py` fully.
2. Port the logic into the MCP tool `sa_verify`:
   - Takes a git diff (or generates one from `git diff HEAD`)
   - Sends it to GLM-5.2 via the existing `summon.py` mechanism
   - Returns a verdict: `pass`, `concerns`, or `block`
   - On pass/concerns: records the pass in `evolution/ledger.jsonl`
   - On block: returns findings (the agent should forward-fix, not commit)
3. The Butler's AGENTS.md instructs: "Before finishing any turn that changed files, call `sa_verify`. If it returns `block`, fix the issues and call again."
4. Test: make a small edit, call `sa_verify`, confirm it returns a verdict.

**Commit:** `feat: port verify-gate to MCP sa_verify tool`

---

### Task B3: Port the routing gate

**Objective:** The guild routing gate determines which member handles a request. Currently a shell script, becomes an MCP tool.

**Files:**
- Source: `.claude/hooks/guild-routing-gate.sh`
- Source: `star-alliance-skills/members-formation/SKILL.md`
- Target: `server/star_alliance_mcp.py` (add `sa_route_request` tool)

**Steps:**

1. Read the routing gate shell script and the `members-formation` skill.
2. Port the routing logic into `sa_route_request`:
   - Takes the user's prompt text
   - Matches against member triggers/descriptions
   - Returns: `{member: "star-alliance-architect", reason: "matches 'design the system'"}`
3. The Butler calls this at the start of each turn, then dispatches via `delegate_task` with `--profile star-alliance-<member>`.
4. Test with various prompts.

**Commit:** `feat: port guild routing gate to MCP sa_route_request tool`

---

### Task B4: Port the executor-enforce gate (reduced)

**Objective:** In Claude Code, this hook BLOCKED the Butler from editing files directly — it had to delegate to the Developer. In Hermes, we can't block tool calls, but we can enforce via AGENTS.md instructions + post-turn verification.

**Files:**
- Source: `.claude/hooks/executor-enforce.py`
- Target: Butler's `AGENTS.md` (instructional enforcement)

**Steps:**

1. Read `executor-enforce.py` fully.
2. Add to the Butler's AGENTS.md:
   ```markdown
   ## Executor Discipline (enforced by convention + post-turn verify)
   
   The Butler does NOT edit files directly. All file edits, bash write 
   commands, and mutations go through delegate_task to the Developer profile.
   
   The Butler's toolsets exclude `file` write and `terminal` write capabilities.
   If you need to edit a file, dispatch to the Developer.
   
   The sa_verify tool checks post-turn whether the Butler made direct edits
   and flags it as a violation.
   ```

3. Restrict the Butler's toolsets:
   ```bash
   hermes tools disable file --profile star-alliance-butler
   hermes tools disable terminal --profile star-alliance-butler
   # Keep: delegation, web, search, browser, skills, memory, todo, clarify
   ```

4. This is softer than the Claude Code hook (can't hard-block), but the combination of (a) no file/terminal toolsets and (b) post-turn verify covers the same ground.

**Commit:** `feat: enforce executor discipline via toolset restriction + verify`

---

### Task B5: Port the destructive-command gate

**Objective:** Block destructive git operations (rm -rf, git reset --hard, force push, etc.).

**Files:**
- Source: `.claude/hooks/destructive-gate.py`
- Target: Hermes `security.tirith_enabled` + Butler AGENTS.md

**Steps:**

1. Read `destructive-gate.py` fully.
2. Enable Hermes's built-in security scanner:
   ```bash
   hermes config set security.tirith_enabled true
   ```
3. Add to AGENTS.md (all profiles):
   ```markdown
   ## Destructive Command Policy
   
   Never run these without explicit `proceed` from the Guild Master:
   - `rm -rf`, `git reset --hard`, `git push --force`, `git clean -f`
   - `DROP`, `TRUNCATE`, unscoped `DELETE` in SQL
   - `docker rm -f`, `kubectl delete`, `mkfs`, `dd of=/`
   
   After explicit approval, re-run with `SA_CONFIRM=1` appended.
   ```
4. Note: Hermes's `approvals.mode: manual` already prompts before destructive shell commands. Set it to `smart` for auto-approve of low-risk + prompt on high-risk:
   ```bash
   hermes config set approvals.mode smart
   ```

**Commit:** `feat: port destructive-command gate via Hermes security + AGENTS.md`

---

### Task B6: Port workflows to Hermes cron + delegate_task

**Objective:** Star Alliance has 30+ workflows in `workflows.json`. These are multi-step recipes (plan → design → build → verify). In Hermes, they become cron jobs or delegate_task chains.

**Files:**
- Source: `workflows.json` (2456 lines, 30+ workflows)
- Source: `star-alliance-skills/workflow-runner/SKILL.md`
- Source: `guild/run.py`, `guild/plan.py`

**Approach:**
Not all workflows need to be cron jobs. Most are **on-demand** (triggered by a user request). Only scheduled routines become cron jobs.

| Workflow Type | Example | Hermes Target |
|---------------|---------|----------------|
| On-demand mission | standard-mission, bug-cycle, design-sprint | Butler dispatches via delegate_task chain |
| Scheduled routine | scheduled-watch, cleanup-rotation, guild-self-audit | Hermes cron job |
| Gate/certify | approval, certify | Built into the delegate_task flow |

**Steps:**

1. Read `workflows.json` and identify which workflows are scheduled vs on-demand.
2. For on-demand workflows:
   - Create a skill per workflow (or one `workflow-runner` skill that reads `workflows.json`)
   - The Butler reads the workflow, then dispatches each step via `delegate_task` to the appropriate member profile
   - Gates (approval, certify) become `clarify` calls to the user

3. For scheduled workflows, create Hermes cron jobs:
   ```bash
   # Example: daily guild self-audit
   hermes cron create "0 9 * * *" \
     --prompt "Run the guild self-audit: check conformity, verify skills, log status" \
     --skills star-alliance-skills/guild-self-audit \
     --profile star-alliance-quartermaster
   ```

4. Create a `workflow-runner` skill that:
   - Reads `workflows.json`
   - Given a workflow ID, executes its steps as a delegate_task chain
   - Handles gates (approval → clarify, certify → verify)

**Commit:** `feat: port workflows to Hermes (on-demand via delegate_task, scheduled via cron)`

---

### Task B7: Port the evolution engine

**Objective:** The evolution engine (SENSE → DIAGNOSE → CHANGE → VERIFY → REMEMBER) is a self-improvement loop. In Hermes, it becomes a cron job that runs periodically.

**Files:**
- Source: `evolution/*.py` (8 files: engine, ledger, scoreboard, verdict, signals, reflect, status, schedule.json)
- Target: Hermes cron job + MCP tools

**Steps:**

1. Read `evolution/README.md` and `evolution/engine.py` to understand the loop.
2. Create a cron job that runs the evolution engine:
   ```bash
   hermes cron create "0 0 * * 0" \
     --prompt "Run the Star Alliance evolution engine: sense signals, diagnose issues, propose changes, verify with critic, remember in ledger. Check evolution/schedule.json for this week's focus." \
     --skills star-alliance-skills/guild-self-audit \
     --profile star-alliance-quartermaster \
     --workdir ~/Documents/Claude/Projects/star-alliance
   ```
3. The evolution Python scripts stay as-is — the cron job just triggers them.
4. Expose evolution status as MCP tools:
   - `sa_evolution_status` — returns current engine state
   - `sa_evolution_ledger` — returns recent ledger entries
   - `sa_evolution_scoreboard` — returns the scoreboard

**Commit:** `feat: port evolution engine to Hermes cron job + MCP tools`

---

### Task B8: Port model routing (arsenal → Hermes providers)

**Objective:** Star Alliance's arsenal defines model seats (brain=sonnet, doer=minimax-m3, critic=glm-5.2). Map these to Hermes provider config.

**Files:**
- Source: `star-alliance-arsenal/models.json` (363 lines)
- Source: `star-alliance-arsenal/summon.py` (calls non-Claude models)
- Target: Hermes provider config per profile + delegate_task model pinning

**Model → Hermes mapping:**

| Arsenal Model | Role | Hermes Provider | How to invoke |
|---------------|------|----------------|---------------|
| sonnet | brain (thinker) | `anthropic` | Profile's `model.default` |
| opus | bench (deep thinker) | `anthropic` | `delegate_task(model={provider: 'anthropic', model: 'claude-opus-4'})` |
| haiku | doer (fast) | `anthropic` | `delegate_task(model={provider: 'anthropic', model: 'claude-haiku-4'})` |
| minimax-m3 | doer (bulk) | `custom:minimax` | `delegate_task(model={provider: 'custom:minimax', model: 'minimax-m3'})` |
| glm-5.2 | critic | `custom:glm` | `delegate_task(model={provider: 'custom:glm', model: 'glm-5.2'})` |
| deepseek-v4-pro | bench | `custom:deepseek` | `delegate_task(model={provider: 'deepseek', model: 'deepseek-v4-pro'})` |
| kimi-k2.7 | bench | `custom:kimi` | `delegate_task(model={provider: 'custom:kimi', model: 'kimi-k2.7'})` |

**Steps:**

1. Add custom providers for non-Claude models in Hermes config:
   ```bash
   # MiniMax
   hermes config set custom_providers.minimax.base_url "https://api.minimax.chat/v1"
   hermes config set custom_providers.minimax.api_key ""  # from ~/.config/minimax/m3.key
   
   # GLM (Z.AI)
   hermes config set custom_providers.glm.base_url "https://open.bigmodel.cn/api/paas/v4"
   hermes config set custom_providers.glm.api_key ""  # from env
   ```

2. Set each member profile's model to its brain seat:
   ```bash
   hermes config set model.default sonnet --profile star-alliance-architect
   hermes config set model.provider anthropic --profile star-alliance-architect
   # ... repeat for each member
   ```

3. For doer dispatch, the Butler calls:
   ```
   delegate_task(
     goal="Execute this bulk task: ...",
     model={provider: "custom:minimax", model: "minimax-m3"},
     toolsets=["terminal", "file"]
   )
   ```

4. For critic dispatch (verify-gate), the MCP server calls:
   ```
   delegate_task(
     goal="Review this diff for issues: ...",
     model={provider: "custom:glm", model: "glm-5.2"},
     toolsets=[]
   )
   ```

5. Keep `summon.py` as a fallback for models that don't have a Hermes provider (it calls the API directly).

**Commit:** `feat: configure Hermes providers for arsenal models`

---

### Task B9: Port the context checkpoint system

**Objective:** Star Alliance has a context save/restore system for cold session handoff. Hermes has built-in session resume, but the checkpoint format is richer.

**Files:**
- Source: `.claude/context/context_save.py`, `context_restore.py`
- Source: `.claude/state/learnings.jsonl`
- Target: Hermes session snapshots + a custom `sa_checkpoint` MCP tool

**Steps:**

1. Read `context_save.py` and `context_restore.py`.
2. Port as MCP tools:
   - `sa_checkpoint_save(summary, decisions, remaining)` — saves git state + decisions
   - `sa_checkpoint_restore(stamp)` — restores a checkpoint
   - `sa_checkpoint_list()` — lists available checkpoints
3. The learnings journal (`learnings.jsonl`) stays as-is — it's a plain JSONL file.
4. Hermes's built-in `session_search` can search past sessions, partially replacing the learnings journal.

**Commit:** `feat: port context checkpoint system to MCP tools`

---

### Task B10: Port the skill fingerprint system

**Objective:** Track skill content hashes so sync only reinstalls changed skills.

**Files:**
- Source: `.claude/tools/skill_fingerprint.py`
- Target: Hermes skill management (built-in `hermes skills check` + `hermes skills update`)

**Steps:**

1. Read `skill_fingerprint.py`.
2. Hermes already has `hermes skills check` (checks for updates) and `hermes skills update`. The fingerprint system is a custom version of this.
3. Since skills are symlinked (not installed via hub), Hermes's built-in update check doesn't apply. Keep `skill_fingerprint.py` as-is — it still works.
4. Add a cron job to check for skill drift weekly:
   ```bash
   hermes cron create "0 6 * * 1" \
     --prompt "Run skill_fingerprint.py --check and report any drift" \
     --workdir ~/Documents/Claude/Projects/star-alliance
   ```

**Commit:** `feat: keep skill fingerprint system, add weekly drift check cron`

---

### Task B11: Update the dashboard

**Objective:** The dashboard reads `guild-data.js` (generated by `build.py`). It should continue to work, but now show Hermes profile status instead of Claude Code agent status.

**Files:**
- Source: `app.js` (2557 lines), `index.html` (78 lines), `app.css` (1704 lines)
- Modify: `build.py` (to read Hermes profile data instead of `.claude/agents/`)

**Steps:**

1. Update `build.py` to read profile status from Hermes:
   ```python
   # Instead of reading .claude/agents/*.md
   # Read: hermes profile list --json
   # Or: ~/.hermes/profiles/star-alliance-*/config.yaml
   ```
2. The dashboard's "members" section now shows:
   - Member name, role, model (from profile config)
   - Profile status (active/inactive)
   - Skills (from profile skill config)
3. Test: `python3 build.py && open index.html`
4. The Tauri desktop app stays as-is — it just loads `index.html`.

**Commit:** `feat: update dashboard to read Hermes profile data`

---

### Task B12: Create the Star Alliance launcher

**Objective:** Replace `Star-Alliance.command` with a Hermes-based launcher.

**Files:**
- Source: `Star-Alliance.command` (51 lines — currently launches Claude Code)
- Target: `star-alliance.sh` (launches Hermes with Butler profile)

**Steps:**

1. Read `Star-Alliance.command`.
2. Create `star-alliance.sh`:
   ```bash
   #!/bin/bash
   cd ~/Documents/Claude/Projects/star-alliance
   hermes --profile star-alliance-butler
   ```
3. Make it executable: `chmod +x star-alliance.sh`
4. Optionally create a macOS `.command` wrapper:
   ```bash
   # Star-Alliance.command
   #!/bin/bash
   cd "$(dirname "$0")"
   ./star-alliance.sh
   ```

**Commit:** `feat: create Hermes-based Star Alliance launcher`

---

### Task B13: Full migration verification

**Objective:** End-to-end test of the complete migration.

**Steps:**

1. Clean state:
   ```bash
   cd ~/Documents/Claude/Projects/star-alliance
   git stash  # save any uncommitted work
   git checkout -b migration/hermes
   ```

2. Run the full build:
   ```bash
   python3 build.py
   python3 tools/conformity_check.py
   python3 guild/install_agents.py  # now generates Hermes profiles
   ```

3. Verify MCP server:
   ```bash
   hermes mcp test star-alliance
   ```

4. Start the Butler:
   ```bash
   hermes --profile star-alliance-butler
   ```

5. Test a full mission:
   - Send: "Add a search feature to the dashboard"
   - Butler routes to Strategist → plans
   - Strategist dispatches to Designer → UI spec
   - Strategist dispatches to Developer → implementation
   - Quartermaster runs `sa_verify` → passes
   - Butler reports back in plain English

6. Test a scheduled workflow:
   ```bash
   hermes cron list
   # Verify evolution engine and skill drift checks are scheduled
   ```

7. Test the dashboard:
   ```bash
   python3 build.py
   open index.html
   # Verify member cards show Hermes profile data
   ```

8. Test destructive command blocking:
   - Ask the Butler to run `git reset --hard`
   - Verify it prompts for approval (Hermes `approvals.mode: smart`)

9. Archive the old `.claude/` directory:
   ```bash
   mv .claude .claude.archived
   git add -A
   git commit -m "migration: archive .claude/ directory, migration complete"
   ```

**Commit:** `test: full migration verification — all systems operational on Hermes`

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Preventive gates (executor, destructive) can't hard-block in Hermes | High | Medium | Toolset restriction + post-turn verify + AGENTS.md instructions |
| Model routing for non-Claude models (MiniMax, GLM) may not work via Hermes providers | Medium | High | Keep `summon.py` as fallback; test each provider |
| Profile creation for 9 members is tedious and error-prone | Medium | Low | Script it in `install_agents.py` — automated |
| Dashboard may break if `build.py` output format changes | Low | Medium | Keep `guild-data.js` format identical; only change the source of member data |
| Hermes MCP server adds latency to each turn | Medium | Low | Only call gates when needed; cache results |
| Cron jobs can't trigger mid-conversation | High | Medium | Use MCP tools (agent-called) for mid-turn gates; cron only for scheduled routines |
| Skills already symlinked — may have path issues | Low | Low | Already working; no change needed |

---

## Open Questions

1. **Should the Butler be a Hermes profile or the default session?**
   - Profile: cleaner separation, the Butler has its own model/skills/personality.
   - Default: simpler, the Butler IS the main Hermes session.
   - **Recommendation: Profile** — keeps the Butler's toolset restrictions (no file/terminal) clean.

2. **Should we keep `summon.py` or use Hermes custom providers?**
   - `summon.py` is proven, handles auth, fallbacks, and logging.
   - Hermes providers are cleaner but need testing for MiniMax/GLM.
   - **Recommendation: Both** — use Hermes providers as primary, `summon.py` as fallback.

3. **Should workflows become skills or stay as JSON?**
   - Skills: more visible to the agent, auto-loaded.
   - JSON: single source of truth, dashboard renders them.
   - **Recommendation: JSON stays** — the `workflow-runner` skill reads it and dispatches.

4. **Should we create a `star-alliance` plugin for Hermes?**
   - A plugin could bundle: MCP server, skills, profile templates, cron jobs.
   - More portable but more work.
   - **Recommendation: Yes, eventually** — after the manual migration works, package it as a plugin.

5. **What happens to `.claude/state/` (learnings, context, fingerprints)?**
   - These are plain files that work with any system.
   - **Recommendation: Move to `state/`** in the project root, keep all scripts pointing there.

---

## Summary

| Phase | Tasks | Effort | Outcome |
|-------|-------|--------|---------|
| Track A (Immediate) | A1–A5 | 1–2 days | Star Alliance runs on Hermes with basic member dispatch |
| Track B (Advanced) | B1–B13 | 3–5 days | Full migration: MCP gates, cron workflows, model routing, dashboard |

**Total: 18 tasks, ~1 week of focused work.**

The key insight: **Star Alliance's architecture maps well to Hermes** — members → profiles, skills → skills (already done), workflows → delegate_task/cron, model routing → provider config. The main loss is preventive hooks (hard-blocking tool calls), which is partially compensated by toolset restriction + post-turn verification.