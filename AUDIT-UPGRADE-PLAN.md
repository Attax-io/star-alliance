---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Star Alliance — Guild Retrospective: Upgrade Plan

_Campaign output. 3 stores · full history (Mar 15–Jun 27) · 8,695 signal windows → 1,806 raw candidates → 112 distinct lessons → the upgrades below._
**Apply-gate is OFF — every item is a proposal. No skill/workflow/member file was modified.** Approve per-tier to apply.

Verify legend: ❌ real gap (not in target) · ◐ partial (related text exists, lesson sharper) · ✅ already captured (no action) · 🆕 new skill/workflow idea.

---

## P1 — High-impact, verified real gaps (do these first)

### P1.1 · File-reading discipline → **every member + CLAUDE.md**  ❌  evidence **x46** (largest signal in entire history)
- **Lesson:** Read files that may exceed token caps with `offset`/`limit` or `grep`; switch the instant the first full-read fails — never retry the full read. In scheduled/autonomous runs, loop files one at a time.
- **Target:** new shared "Reading discipline" clause. Cleanest home: `CLAUDE.md` (global, all members inherit) + a one-liner in `scheduled-watch` for the loop-one-at-a-time case.
- **Why:** 46 separate sessions hit token-cap read failures and re-tried blindly. Nothing in any member `.md` or `CLAUDE.md` mentions offset/limit. Single highest-frequency lesson mined.

### P1.2 · dev-server: check project memory before generic defaults  ◐  x4
- **Lesson:** Before applying a generic skill default, check the project's own memory/CLAUDE for per-project overrides (ports, serve command, "never kill :8000").
- **Target:** `star-alliance-skills/dev-server/SKILL.md`.
- **Why:** Matches the standing memory [[star-alliance-dashboard-serving]] (serve.cjs :4178, :8000 is WhatsApp MCP — never kill). Skill should point at project memory, not hardcode.

### P1.3 · conquering-campaign: declare trim-mode in frontmatter, never silently skip stages  ◐  x3
- **Lesson:** When trimming waves, declare the trim mode explicitly with all required fields; never silently drop a stage.
- **Target:** `conquering-campaign/SKILL.md` (frontmatter spec / wave-playbook).
- **Why:** Recurring: campaign skipped stages without declaring it, audits couldn't tell trim from omission.

### P1.4 · supabase: three RLS/Realtime hard rules  ◐ partial  x8 combined
- **Lessons:** (a) After `ENABLE RLS`, add explicit INSERT/UPDATE/DELETE policies for `authenticated` — no policy = default-deny on writes (x2). (b) On view column changes, DROP+CREATE then **re-apply `security_invoker=true`** (x3). (c) Set `REPLICA IDENTITY FULL`/USING INDEX before Realtime on non-PK filters (x3).
- **Target:** `star-alliance-skills/supabase/` + `supabase-postgres-best-practices`.
- **Why:** Each cost a real debugging cycle. Verify which already live in the best-practices skill; add the missing ones.

---

## P2 — Member-conduct & routing hardening (medium)

### P2.1 · Member-conduct clause block → members README / each `.md`  x12 cluster
Bundle these recurring corrections into a shared conduct block:
- Don't make unrequested changes; wait for explicit permission before modifying code/visuals.
- Before creating components, check for and reuse existing ones; reuse design-token constants, never hardcode hex.
- Treat **'cancel' as immediate revert** of the prior change-set; honor explicit **'proceed'** — don't re-insert your own verification breakpoints.
- Read vault/memory logs before continuing work started in a prior session.
- Save user **confirmations and wins** as feedback memories, not only corrections. _(directly extends [[butler-commit-standing-auth]] habit)_
- Log errors loudly; never silently swallow.

### P2.2 · Routing hardening → the-butler / routing gate  x9 cluster
- Confirm destructive git ops (`reset --hard`, force push) before executing. _(reinforces existing push-needs-ask in [[butler-commit-standing-auth]])_
- Handle MCP unavailability without fabricating writes — reconnect or fall back to non-write ops; when WhatsApp dispatch disabled, log intent verbatim, never call the tool.
- Long-running subagents must emit periodic status heartbeats, not only wake-on-completion. _(this campaign felt that — monitors only fired at the end)_
- Re-read skill/workflow docs when the user re-invokes them mid-session; reset state.
- Treat same-session re-invocation minutes after close as a **pivot/extension**, not a new campaign.

### P2.3 · skillsmith routine sharpening  x10 cluster
- Verify all numbers/claims/gaps against source before publishing a verdict (x2).
- Distinguish 'skill prescribed' vs 'skill failed' in the friction harvester; absence-of-friction is a soft signal, not proof.
- Log sub-threshold dissents in multi-persona synthesis (anti-groupthink proof).
- Never hand-edit vendored upstream skills — clobbered on next sync. _(reinforces [[star-alliance-member-skill-principle]] fork/external exceptions)_
- Add a mechanical PreToolUse hook for trigger-phrase gates beyond in-skill prose.

---

## P3 — Already captured — NO ACTION (verify pass caught these)

- ✅ Verify-via-SELECT / `apply_migration` success is partial signal → already in conquering-campaign SKILL.md, failure-modes, db-playbook.
- ✅ Rename sweeps ~14 surfaces → already enumerated in db-rename-sweep SKILL.md.
- ✅ Plan-approval gate (restate scope, wait for "go") → already enforced by the harness routing-gate hook + [[butler-approval-gate]] memory. (Not in member `.md` bodies, but mechanically enforced — low value to duplicate.)
- ✅ Vault-log P13 self-audit on Supabase-MCP sessions → already the vault-log-compliance skill's mandate.

---

## P4 — Class B: Lex-app craft (different repo — out of guild scope)

These are real lessons but belong in the **Lex Council App** `CLAUDE.md`, not guild machinery:
react-hooks/memoization, fd-defracture access model, i18n-extract, admin-page-builder, frontend guard-mirroring, MATERIALIZED CTE hints, RTL slide-over transforms. ~120 raw candidates. **Recommend a sibling mini-campaign rooted in the Lex repo** if you want these landed.

---

## 🆕 New skill / workflow candidates (from NEW-* targets, unbuilt)

- **DB-Migration workflow** (~80 raw refs: migration/schema/ddl/rls/trigger). Partly covered by conquering-campaign db-playbook — decide: promote to a standalone `workflows.json` entry or leave inside the campaign skill.
- **Verification workflow** (~23 refs): "observational evidence, not tooling success" as a reusable gate. Could formalize the existing `verify` skill into the star-map.
- **Heartbeat pattern for long subagents** (cross-cutting): not a skill, an arsenal/weapon-utility addition.

---

## Recommended apply order
1. **P1.1** (file-reading) — biggest signal, one clean edit, helps every future session.
2. **P1.2–P1.4** — skill-local, low blast radius.
3. **P2** — conduct/routing; review wording before applying (touches member identity).
4. **P4** — separate Lex-repo campaign, your call.
5. **🆕** — Workflow Forge session if you want the new workflows.
