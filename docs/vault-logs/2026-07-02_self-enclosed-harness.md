---
description: Self-enclosed harness campaign — portability root resolver, fail-closed config guard, skill provenance refusal, agent allowlist + thinker fail-closed on missing member file, telemetry honesty (workflow sentinel dir + agent-spawn log), and Tier-3 landing kit (full roster + root re-point).
type: Document

---
## Plain-English Summary
The guild can now travel. Seven fixes make it install cleanly into a new project and lock itself down once it lands. It no longer trusts a hard-coded folder path (which was already wrong on this machine) — every gate now finds the repo from its own location. A half-installed guild refuses to run half-open instead of quietly allowing everything. The guild now refuses to run a skill that isn't its own, and refuses to run an unknown helper agent on a high-stakes turn. Its usage logs stopped under-counting. And the installer now lands the whole team, not just one member, and points the new copy at itself. The one step left is running the installer against the Lex folder, which must be done where that folder lives.

## Files Changed
- [[_saroot.py]] — NEW shared primitive. `resolve_root()` (code-location-first, env-hint validated), `guild_managed()`, `missing_config()`. Basis of P0 + P2.
- [[executor-enforce.py]] — root via _saroot (P0); NEW `_p2_half_installed()` fail-CLOSED guard: a guild-managed repo missing `star-alliance-arsenal/models.json` blocks write-class tools instead of falling back silently (P2). Silent in the home repo (config present).
- [[routing-enforce.py]] — root via _saroot (P0); final blanket-allow replaced with an allowlist (KNOWN_BUILTINS ∪ guild roster) — unknown/foreign agents refused on FULL-tier turns, Explore/Plan/general-purpose still pass (P4).
- [[thinker-gate.py]] — root via _saroot (P0); NEW `_is_known_member()` — a known member with a MISSING agent file now fails CLOSED (the Lex empty-agents case) while genuine non-members still pass (P4).
- [[butler-skill-gate.py]] — root via _saroot (P0); NEW `_is_foreign_bare_skill()` provenance refusal: a bare skill absent from `star-alliance-skills/` is blocked; plugin-namespaced skills + the Butler floor exempt; fail-open when not guild-managed (P3).
- [[okf-gate.py]] — root via _saroot (P0).
- [[signals.py]] — `once_per_turn()` sentinel dir moved from `<root>/state` to `<root>/.claude/state` (aligns with turn-start) + CLAUDE_PROJECT_DIR resolution — fixes the once-per-name-for-life workflow undercount (P5).
- [[turn-start.py]] — now clears the dynamic `xp-workflow-*` sentinels each turn so once_per_turn re-arms (P5).
- [[spawn-log.py]] — NEW PostToolUse hook on Task|Agent → dispatch-log.jsonl; closes the Claude-subagent-spawn telemetry hole (P5). Registered in settings.json.
- [[settings.json]] — registered spawn-log on a new Task|Agent PostToolUse matcher.
- [[install.sh]] — Tier 3 now copies the FULL `agents/` roster into the target `.claude/agents/` (fixes the "Lex agents EMPTY → routing deadlock" blocker) and re-points STAR_ALLIANCE_ROOT to the self-contained target (P1).
- [[absorb.py]] — NEW `scan_workflows` / `propose_workflows` + `--workflows`/`--only-workflows` CLI: workflow-adopt branch mirroring the skill branch; proposal-only, never copies (P6).

## Why
Corrected intent audit (docs/audit-self-enclosed-guild-2026-07-02.md, revised this session): the guild was self-equipped but not self-enclosed. Two audit verdicts were misreads — the gates ARE armed (via sa-pretool router) and install.sh already exists — so the real work was portability (one hard-coded path), isolation-enforcement (P3/P4), telemetry honesty (P2/P5), fail-closed posture (P2), and the Tier-3 roster/root gaps (P1). Guild Master directed: keep Star Alliance branding, carry Hermes on every landing, land Lex first.

## Verification
Every touched .py compiles (py_compile). settings.json + workflows.json valid JSON. install.sh passes `bash -n`. Behavioral tests: provenance refuses a foreign bare skill / allows a real repo skill + plugin + floor; routing allowlist passes Explore + roster, would block unknown; thinker `_is_known_member` True for the-developer, False for Explore; P2 guard silent in home repo (models.json present); scan_workflows(self)=0 candidates. conformity_check.py shows ONLY environmental HS (home ~/.claude/skills store) + PD (~/.hermes/profiles) failures — zero AG/VER/RG/FB/P drift, i.e. no code-side regression. Gate check() smoke test: all patched gates exit 0 on a benign Read; executor-enforce main() exit 0 on Read.

## P13 Self-Audit (Supabase MCP)
No Supabase MCP tools were called this session. No SQL, DDL, migrations, or advisors run.

## Follow-ups (not done this session)
- Run the installer against the Lex folder (needs the Lex path; not mounted here): `bash star-alliance-arsenal/install.sh the-strategist /path/to/lex --tier 3` then verify `.claude/agents/` populated + one full high-stakes turn.
- P6 skill_sync `--apply` auto-copy for detected ADD-TO-REPO skills — deferred (lowest value; workflow-adopt was the structurally-absent gap and is done).
- P5(b) skill-activation-at-prompt-time logging — deferred (seam change, low ROI; agent-spawn + workflow honesty done).
- Optional doctrine line in CLAUDE.md naming the provenance rule (mechanism shipped; doctrine not hand-edited to avoid touching the sacred file blindly).
- Two stray 8-byte probe files (`.claude/hooks/_saroot_probe.tmp`, `build-campaigns/_probe.tmp2`) — sandbox blocked `rm`; remove with `git clean -f` or Finder.

## Addendum — leveling made live (same session)
- [[server.py]] — MCP `invoke_skill` now appends a `{"type":"skill","name":…,"via":"mcp"}` row to `.claude/state/xp-log.jsonl` on each successful pull, so a skill earns XP when the guild actually uses it through the MCP — not only via the Skill tool (closes the skill-telemetry gap the audit flagged).
- [[turn-start.py]] — once-per-day, launches `python3 build.py` DETACHED (dated sentinel `level-refresh-<date>`, fail-silent) so usage-based levels for skills/members/workflows recompute on their own without a manual build. build.py only regenerates generated files, so this is the sanctioned refresh path.
- [[install-star-alliance.command]] — detect-and-rebuild a broken/synced venv (two-device fix) + accept python3 fallback.
Verification: server.py + turn-start.py compile; xp.py resolves a skill level from the log (guild-sync → xp 1/level 1); build.py runs exit 0 and regenerated guild-data.* (levels refreshed now); installer passes bash -n.

## Addendum 2 — workflow leveling key-mismatch fix
- [[build.py]] — `stamp_xp` resolved workflows by `id` but workflow XP is logged by display `name` (workflow-gate.py writes `{"type":"workflow","name":…}`), so every workflow fell back to level 1 and the dashboard's level-desc sort had nothing to order. Now resolves workflows by `name`. Verified: after rebuild, Compliance Audit + Strategic Audit show level 2 and sort to the top, rest level-1 A→Z. Skills were already keyed by id (correct) — no change needed; the dashboard sort (level desc, then name asc) was already correct in dashboard.js.
