---
name: portability-audit
description: "Audit how portable a Claude Code project is — maps every layer (skills, members, hooks, env vars, hardcoded paths, arsenal tools) plus per-machine portability hazards, assigns tier gaps, and produces a ranked install plan. Also catches the runtime bricks: device-specific home paths, references to retired primitives (stale installer/hooks/settings pointing at folders that no longer exist), plaintext secrets, and doubled repo-root paths — before they strand a session. Run before deploying Star Alliance members to a new project, or when a project feels 'stuck here' or 'broken on this machine'. Triggers: 'audit portability', 'can I use this in another project', 'how do I deploy this elsewhere', 'portability audit', 'what needs to move', 'install plan for project X', 'why is this broken on this machine', 'check for hardcoded paths', 'scan for secrets', '/portability-audit'."
metadata:
  version: 1.1.0
type: Skill

---
# portability-audit — map what's portable, what's broken, what's missing

Answers: **can this project's AI setup move to another project, and what's the gap?**
And: **will it even survive on THIS machine, or does it hide a per-machine brick?**

Mined from the 2026-06-27 Star Alliance portability audit, extended after five sessions
where device-specific paths, retired-primitive references, and a leaked secret each
bricked the harness at runtime. Reusable on any Claude Code project — not just Star Alliance.

## The 7 portability layers

Audit each layer in order. Each one can independently block a deployment — or a session.

| # | Layer | What to check | Common break |
|---|---|---|---|
| 1 | **Skills** | Are skills in `~/.claude/skills` (global) or `.claude/skills` (project)? Are versions current vs source repo? | Stale version silently runs old code |
| 2 | **Members** | Are `.md` files in `.claude/agents/`? Do they reference any path that only exists here? | Member present but arsenal calls fail |
| 3 | **Arsenal tools** | Does any script reference a relative path that only resolves from one directory? | Silent path failure in target project |
| 4 | **Env vars** | Is `STAR_ALLIANCE_ROOT` (or equivalent) set in `.claude/settings.json`? | Repo-relative tool calls resolve to nothing |
| 5 | **Hooks** | Are `.claude/hooks/*.py` present? Are they wired in `settings.json`? Do the wired paths still exist? | Gate hooks silently absent, or point at a deleted folder and block every turn |
| 6 | **Workflows** | Is `workflows.json` present? Does it have the workflows the members reference? | Workflow-gate blocks every turn |
| 7 | **Portability hazards** | Any per-machine hardcoded path, retired-primitive reference, plaintext secret, or doubled repo-root? | Bricks the harness at runtime on a different machine, or leaks a credential |

Layer 7 is the difference between "portable to another project" and "survives being
opened by another person or on another laptop." A single `/Users/<someone-else>` in
`settings.json` can block an entire project on first launch.

## Procedure

### Step 1 — Identify what's installed

```sh
ls .claude/agents/
ls .claude/skills/
ls ~/.claude/skills/
ls .claude/hooks/
cat .claude/settings.json
ls workflows.json 2>/dev/null && echo "present" || echo "MISSING"
```

### Step 2 — Check arsenal path resolution

```sh
grep -n "python3\|STAR_ALLIANCE_ROOT\|arsenal" .claude/agents/*.md
```

Fails = any bare `python3 star-alliance-arsenal/…` or repo-relative tool path without `$STAR_ALLIANCE_ROOT`.

### Step 2.5 — Scan for portability hazards (Layer 7)

Run each scan across config, hooks, agents, and settings. Use `LC_ALL=C grep` (macOS
grep silently misses matches on multibyte files) or `rg`.

**(a) Per-machine hardcoded home paths** — any absolute path baked to one user's home:

```sh
LC_ALL=C grep -rnE '/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|/private/tmp/[A-Za-z0-9._-]+' \
  .claude/ *.json 2>/dev/null | grep -v '\$HOME\|~/'
```

Any hit that names a specific user (e.g. `/Users/attaselim`) instead of `$HOME`/`~` is a
brick on any other machine. Fix: replace with `$HOME`, `~`, or `$STAR_ALLIANCE_ROOT`.

**(b) Retired-primitive references** — settings/hooks/agents pointing at a script or folder
that no longer exists (stale installer, retired build pipeline, dead MCP server, old hook):

```sh
# List every path settings.json wires as a hook command, then verify each exists.
LC_ALL=C grep -oE '"[^"]*\.(sh|py|json)"' .claude/settings.json | tr -d '"' | while read -r p; do
  resolved="${p/\$STAR_ALLIANCE_ROOT/$STAR_ALLIANCE_ROOT}"; resolved="${resolved/#\~/$HOME}"
  [ -e "$resolved" ] || echo "RETIRED/MISSING: $p"
done
# Flag references to known-retired primitives (installer, build pipeline, local MCP server).
LC_ALL=C grep -rnE 'install\.sh|build\.py|mcp/server\.py|evolution/|turn-finalize\.sh' \
  .claude/ *.json 2>/dev/null
```

A hook wired to a deleted folder hard-blocks the whole project on every turn. Fix:
unwire it, or repoint it at the live primitive. (Retired in this repo: the installer,
`build.py`, the local MCP server, the evolution engine — see CLAUDE.md.)

**(c) Plaintext secrets** — any credential committed in cleartext:

```sh
LC_ALL=C grep -rnE 'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|eyJ[A-Za-z0-9_-]{20,}' \
  .claude/ *.json 2>/dev/null
```

Any hit (e.g. a GitHub PAT in `settings.json`) is a leaked credential. **Do not print the
secret value in the audit output** — report only the file and line. Fix: rotate the
credential immediately, move it to the Keychain or an untracked env file, and scrub history.

**(d) Doubled repo-root paths** — a path that repeats the repo root or an arsenal segment:

```sh
LC_ALL=C grep -rnE 'star-alliance/star-alliance|star-alliance-arsenal/[^ "]*star-alliance-arsenal|\$STAR_ALLIANCE_ROOT/[^ "]*\$STAR_ALLIANCE_ROOT' \
  .claude/ *.json 2>/dev/null
```

Doubled roots resolve to a folder that never exists. Fix: collapse to a single root segment.

### Step 3 — Check skill versions

```sh
for d in .claude/skills/*/; do
  skill=$(basename "$d")
  local_ver=$(grep 'version:' "$d/SKILL.md" | head -1 | awk '{print $2}')
  repo_ver=$(grep 'version:' "$STAR_ALLIANCE_ROOT/star-alliance-skills/$skill/SKILL.md" 2>/dev/null | head -1 | awk '{print $2}')
  [[ "$local_ver" != "$repo_ver" ]] && echo "STALE: $skill local=$local_ver repo=$repo_ver"
done
```

### Step 4 — Assign tiers + gaps

| Finding | Tier gap | Fix |
|---|---|---|
| Skills stale or missing | Tier 1 | `install.sh <member> . --tier 1` |
| Member .md absent | Tier 2 | `install.sh <member> . --tier 2` |
| `STAR_ALLIANCE_ROOT` missing | Tier 2 | Add env block to `.claude/settings.json` |
| Arsenal paths hardcoded | Tier 2 | Replace with `$STAR_ALLIANCE_ROOT/star-alliance-arsenal/` |
| Hooks absent | Tier 3 | `install.sh <member> . --tier 3` |
| `workflows.json` missing | Tier 3 | Copy `workflows-lite.json` from arsenal |
| Per-machine home path baked in | **CRITICAL** | Replace `/Users/<name>` with `$HOME`/`~`/`$STAR_ALLIANCE_ROOT` |
| Hook/setting wired to retired or missing path | **CRITICAL** | Unwire it or repoint at the live primitive |
| Plaintext secret committed | **CRITICAL** | Rotate now, move to Keychain/untracked env, scrub history |
| Doubled repo-root path | HIGH | Collapse to a single root segment |

Layer-7 findings are CRITICAL by default because they brick or leak at runtime — fix them
before any tier install, since installing on top of a broken settings.json just spreads it.

### Step 5 — Produce the install plan

Output format:

```
PORTABILITY AUDIT — <project-name>
Date: <today>

LAYER STATUS:
  Skills      : <N current> / <N total> — <N stale>
  Members     : <present|missing>
  Arsenal     : <STAR_ALLIANCE_ROOT set|MISSING>
  Hooks       : <N hooks present|MISSING> — <N wired-but-missing>
  Workflows   : <present|MISSING>
  Hazards     : <N per-machine paths> · <N retired refs> · <N secrets> · <N doubled roots>

GAPS (ranked by impact):
  1. [CRITICAL] ...
  2. [HIGH] ...
  3. [LOW] ...

INSTALL PLAN:
  bash "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/install.sh" <member> . --tier <N>
```

Never print a discovered secret's value in the report — cite file and line only.

## Tier definitions (quick ref)

| Tier | What you get | Command |
|---|---|---|
| 1 | Skills only | `install.sh <member> <project> --tier 1` |
| 2 | + member agent + `STAR_ALLIANCE_ROOT` env | `install.sh <member> <project> --tier 2` |
| 3 | + hooks + routing gate + `workflows-lite.json` | `install.sh <member> <project> --tier 3` |

## After the audit

Run `/project-start` in the target project to verify the install resolved all gaps.
Re-run Step 2.5 after any install — a tier install can copy a settings.json that
re-introduces a per-machine path or a wired-but-missing hook.

## Versioning

Bump `metadata.version` on any change — PATCH for wording, MINOR for a new layer, step,
or hazard check.
