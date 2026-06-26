---
title: Star Alliance — Strategist's Workflow Catalogue
author: The Strategist (mined archived sessions; MiniMax doer, Strategist gate)
date: 2026-06-26
project_version_at_scan: 6.30.29
method: full-text mine of 546 archived session transcripts → cluster → gate
scope: 24 star-alliance sessions (S1–S24) + 522 Lex Council sessions (492 App + 30 lex_council)
---

# Star Alliance — The Strategist's Workflow Catalogue

> The Guild Master asked: *"check all former archived sessions and note down all possible
> workflows … there is a huge load concerning Lex Council workflows."* The Strategist swept
> **546 archived transcripts** — the full star-alliance history (24, labelled `S#`) **plus the
> entire Lex Council trove (522 sessions)** — extracted every human-intent turn, and clustered
> them into the repeatable patterns below.
>
> - **§1–§4** = the star-alliance guild workflows (the SA pass).
> - **§5–§7** = the Lex Council workflows (the operational trove — the bulk of the real work).
>
> SA pass drafted by the **MiniMax** doer-weapon and gated by the Strategist; the Lex pass was
> synthesized directly by the Strategist from a 522-session signature histogram + intent digest.

**Legend:** weapons — `minimax` = doer (makes the artefact), `claude`/`sonnet`/`opus` = gate/thinker.
Members — Butler (router), Strategist (planner), Designer (visuals), Quartermaster (skills/logs/conformity),
Architect, Developer, Translator, Merchant.

---

## Verdict at a glance

| Question | Answer |
|---|---|
| Workflows already formalized in `workflows.json` | **9** |
| …of those, **proven in the archived sessions** | **6** (quick-fix, design-sprint, architecture-build, skill-forge, guild-log-sync, conformity-sweep) |
| …formalized but **never exercised** in these sessions | **3** (standard-mission, legal-codex, market-recon) |
| **New candidate workflows discovered** (recur, not yet formalized) | **6** |
| Cross-cutting invariants the Guild Master keeps enforcing | **9** |
| **Lex Council sessions scanned** | **522** (492 App + 30 lex_council) |
| **Lex automated/scheduled routines** | **7** (skillsmith ×40, cleanup ×29, bug-triage ×21, audits, post-campaign cleanup, release, lessons-mine) |
| **Lex interactive workflow families** | **14** |
| **Cowork sessions scanned** (separate store) | **562** (back to 2026-03-15 — a whole pre-May era the Claude Code store didn't hold) |
| **Biggest gap (at audit time)** | Marketing/public-panel work recurred ~10× with no owning member — **now RESOLVED:** `the-herald` was recruited (decision #39) and `marketing-audit` routes to it |
| **Outcome** | `workflows.json` rebuilt **9 → 24**; conformity ✓; version → 6.37.35 (see §10) |

---

## 1. Proven formalized workflows

These nine already live in `workflows.json`. Six show up clearly in the archived work; three do not.

| Workflow | Proven? | Sessions | Evidence |
|---|---|---|---|
| **quick-fix** | ✓ | S4, S11 | S4 = single "add a deactivate button"; S11 = small icon-reposition tweak. Single-target, no full pipeline. |
| **design-sprint** | ✓ | S5, S6, S7, S10, S11, S15, S19, S20 | The dominant visual-iteration loop: portraits (S5,S7), weapon art (S6,S15,S20), skill icons+tooltips (S10), member-card layout (S11), skill-card art (S19). |
| **architecture-build** | ✓ | S8, S14, S21, S23 | S8 = starmap + agent-interaction model; S14 = STORM skill wired in; S21 = `weapon-utility` skill + thinker/doer/both schema; S23 = members-formation restructures member prompts. |
| **skill-forge** | ✓ | S3, S9, S12, S14, S17, S18, S22, S23 | S3 reusable script; S9 weapon-API upgrade; S12 merge analysis; S14 STORM create+wire; S17 designer-only scoping; S18 skill-creation audit; S22 bulk sync; S23 members-formation. |
| **guild-log-sync** | ✓ | S2, S13, S16 | S13 is its **birthplace** ("loop sessions → check log → Quartermaster fills gaps"); S2 "did you add that to the guild log?"; S16 log-what-we-decided. |
| **conformity-sweep** | ✓ | S16, S21, S22 | S21 is its **birthplace** ("create a conformity workflow run … ensure the whole repo conforms"); S22 folds it into cleanup; S16 "nothing contradicting". |
| standard-mission | ✗ | — | No archived session runs the explicit multi-wave full-guild pipeline. S8 is the closest but reads as design-sprint + architecture-build. |
| legal-codex | ✗ | — | No session loads real laws or builds a multilingual codex. (Lex-domain workflow; not exercised here.) |
| market-recon | ✗ | — | No read-only market/trading research in these sessions. (Reserved for the Merchant / incoming trading project.) |

> **Correction over the draft:** the Strategist's repo **audits** (S12, S24) are *not* market-recon
> and *not* plain conformity-sweep — they are their own pattern. See candidate #3 below.

---

## 2. Candidate workflows — recurring, NOT yet in `workflows.json`

Ranked by how often they recur.

### #1 — Art Forge  ·  `art-forge`  ·  **8 sessions** ✦ most common pattern
- **Trigger:** any new visual asset — member portrait, weapon art, skill sigil, workflow sigil, page hero, GIF.
- **Observed steps:**
  1. Strategist/Designer drafts the brief — size, theme, colour constraints, what to avoid (S6: "200×200, elemental colour, avoid reds"; S10: "FallenSword-themed 48×48"; S15: "vibrant, a distinct weapon per model").
  2. Designer + `minimax` (doer) generate the image batch.
  3. Claude (gate) reviews, rejects, sends deltas back to `minimax`.
  4. Iterate 2…N rounds (S6: six redraws; S15 t19–t20: longbow redrawn twice).
  5. Designer drops finals into the repo path; resize/zoom for fit (S6 t11, S10 t11).
  6. Quartermaster wires the art into the arsenal/skill/member pages so it renders (S15 t21,t25), rebuilds the dashboard.
- **Sessions:** S5, S6, S7, S10, S14, S15, S19, S20
- **Formalize?** **YES** — 8/24 sessions, the single most common pattern, stable shape, cross-cuts every other workflow (everything eventually needs a sigil).

### #2 — Arsenal Forge  ·  `arsenal-forge`  ·  **5 sessions**
- **Trigger:** a new weapon (AI model) joins the guild, or an existing one needs re-skinning / re-roleing.
- **Observed steps:**
  1. Strategist sets weapon identity — name, element/colour, visual metaphor (S15 t13: minimax=crossbow, glm=longbow, kimi=hammer, deepseek=scythe).
  2. Designer + `minimax` produce weapon art (→ runs Art Forge).
  3. Strategist assigns role — thinker / doer / both — and priority order (S21 t1: "doers first, then thinkers, sonnet last").
  4. Designer wires the FallenSword role-icon onto the weapon card (S15 t22).
  5. Quartermaster syncs each member page to show the right weapons + role icons (S15 t21,t25).
  6. Optional: route the weapon to a direct API (S9: "all routines use minimax direct API as the doer").
- **Sessions:** S4, S6, S9, S15, S20, S21
- **Formalize?** **YES** — the thinker/doer/both axis (S15) is a permanent schema; every new model re-invents these steps and skips the role-icon wiring (S15 had to be told twice).

### #3 — Strategic Audit  ·  `strategic-audit`  ·  **3 sessions** ✦ the Strategist's signature
- **Trigger:** "audit the repo / review across N angles / can these merge? / what should we keep?" — any multi-model judgement that ships an MD, not code.
- **Observed steps:**
  1. Guild Master poses the question (S24: "does it achieve its goals, is each member unique, is it conformant, upgrade paths?"; S12: "which skills can merge?").
  2. Strategist loads `ultra-brainstorming` / `storm-investigation` and assembles a multi-model panel (glm + kimi + minimax + claude — S12 t1).
  3. Panel fires; Strategist converges takes, resolves contradictions, grades (Phase 3–5).
  4. Strategist writes the ranked MD deliverable (`STRATEGIST-AUDIT.md`; **this file**).
  5. Guild Master rules on open calls; Strategist wires the accepted ones (S24 t3: "fold Engineer into Developer").
- **Sessions:** S12, S24, **S25 (this task)**
- **Formalize?** **YES** — it already produced two repo artefacts and is self-evidently recurring (you are reading the third run). The flagship "ultra" capability deserves a named workflow. *Caveat from the audit: the named 5-model panel currently fires at 2/5 — see `STRATEGIST-AUDIT.md` Finding #1/#2.*

### #4 — Workflow Forge  ·  `workflow-forge`  ·  **6 sessions** ✦ the meta-loop
- **Trigger:** after a non-trivial session a reusable pattern emerges and must be captured as a starmap workflow.
- **Observed steps:**
  1. Butler flags "this can be saved as a starmap workflow" (S16 t2 makes this a standing order).
  2. Strategist drafts it — name, trigger, members, weapons, steps (S13 t2; naming debate S17 t1–t4).
  3. Designer gives the workflow a 100×100 FallenSword sigil + nameplate (S20 t2) → runs Art Forge.
  4. Quartermaster writes it into `workflows.json` and pumps the project version (S16 t1).
  5. Designer weaves it into the starmap page (S8, S20).
- **Sessions:** S13, S16, S17, S18, S20, (S25)
- **Formalize?** **YES** — this is the loop the Guild Master keeps triggering by hand. S25 ("go catalogue the workflows") *is* the absence of this workflow. Formalizing closes the loop.

### #5 — Member Reforge  ·  `member-reforge`  ·  **4 sessions**
- **Trigger:** a member's identity, gender, role, skills, or weapon loadout must change.
- **Observed steps:**
  1. Guild Master states the correction (S23 t3: "Strategist is male — don't repeat this"; S24 t3: "fold Engineer into Developer").
  2. Strategist updates the member's **system-prompt/persona file first** (truth lives in the prompt, not the art).
  3. Designer swaps portrait + icons (→ Art Forge).
  4. Strategist reorders the member's skills/weapons to match the new role (S23 t5).
  5. Quartermaster runs a mini conformity-sweep to confirm files ↔ dashboard agree (S23 t6,t8).
- **Sessions:** S7, S17, S23, S24
- **Formalize?** Maybe — distinct from skill-forge (manages members, not skills); promote after the top four are stable.

### #6 — Starmap Weave  ·  `starmap-weave`  ·  **2 sessions**
- **Trigger:** a workflow/member changes, or the constellation visual itself needs an upgrade.
- **Observed steps:** Strategist defines edges/nodes → Designer rebuilds the starmap page → adds motion (power-core → comet with tail, S8 t11–t12) → adds hover tooltips on members/gates (S8 t13–t14) → Quartermaster syncs to current workflows.
- **Sessions:** S8, S20
- **Formalize?** **NO (yet)** — only 2 sessions, heavy overlap with design-sprint + architecture-build. Re-evaluate after the next two starmap changes.

---

## 3. Cross-cutting invariants

The standards the Guild Master enforced *across* workflows — not workflows themselves, but the rules every workflow must obey.

- **MiniMax-doer / Claude-gate.** Claude never ships the final artefact; `minimax` does, Claude reviews. The Guild Master interrogates this in nearly every session: "did you or minimax do this?" — S4 t2, S6 t2/t4/t9, S8 t6/t7, S9 t1, S10 t3–t6, S14 t5, S19 t1, S21 t6.
- **Butler reports back in simple English.** Restate the order before starting; summarize on done. Called out as a *failure* when skipped — S8 t3/t5, S13 t3, S16 t2, S23 t2/t4.
- **Quartermaster cleans up + logs at the end of every workflow.** S2 t3, S13 t1, S16 t1, S21 t6/t9/t12, S22 t3, S24 t1.
- **Quartermaster pumps the project version on any structural change.** S16 t1: "give the project a version … pump it whenever we upgrade."
- **Guild-log discipline.** Every meaningful action logged; missing entries back-filled. S2 t3, S13 t1, S16 t2.
- **Capture-as-you-go.** Butler must flag when something reusable just happened so it can become a workflow. S13 t2, S16 t2, S17, S18 t1, S20, S25.
- **"Continue from where you left off."** Long sessions pause/resume without restarting. S15 t23, S21 t10, S23 t7.
- **Cleanup carries conformity.** `cleanup` was upgraded so any routine sweep also runs the conformity check. S21 t6, S22 t5.
- **Identity lives in the system prompt, not the art.** When art is wrong, fix the persona file first so the next round is right. S23 t3/t5; S7 t4 is the counter-example that forced the rule.

---

## 4. Recommendation (star-alliance pass)

Add these to `workflows.json`, in order:

1. **`art-forge`** — recurs 8/24, the most common pattern, cross-cuts everything. Highest leverage.
2. **`arsenal-forge`** — 6 sessions; the thinker/doer/both axis is a permanent schema that every new model touches.
3. **`strategic-audit`** — the flagship "ultra" capability; already shipped two MD artefacts and is running a third right now (this file). Name it so it stops being a heroic one-off.
4. **`workflow-forge`** — the meta-loop that *produced this very task*; formalizing it closes the manual loop the Guild Master keeps re-opening.

`member-reforge` is a strong #5 once the top four settle; `starmap-weave` needs more evidence.

> **Tie-back to the audit:** `art-forge`, `arsenal-forge`, and `strategic-audit` all lean on `minimax`
> as doer and the thinker panel as gate. `STRATEGIST-AUDIT.md` Finding #2 warns the panel fires at
> **2/5** (kimi/deepseek not pulled, gpt-5.5 keyless). Formalizing these workflows is worth most
> *after* the phantom weapons are provisioned — otherwise the new workflows inherit the same silent gap.

---

# Lex Council — the operational trove (§5–§7)

> 522 Lex sessions, May 29 → Jun 26. Unlike the star-alliance pass (mostly one-off guild-building),
> Lex is where the guild's workflows were **actually forged and run at scale** — many fully
> automated on cron. This is the battle-tested half. Evidence cited as dates / bug numbers.

## 5. Lex automated & scheduled routines

These run **unattended** (cron / scheduled-task), often dozens of times. They are the real engine.

| Routine | Runs | What it does | Skill / driver |
|---|---|---|---|
| **Skillsmith routine** | ~40 | Nightly skill self-evolution — STORM-mine code/sessions → find upgrade routes & new-skill ideas → apply high-confidence ones (incl. itself). | `skillsmith` (routine mode) |
| **Cleanup rotation** | ~29 | Multi-mode hygiene sweep — i18n language/hardcoded/leaks, dev-error sweep, lint, postgres advisors, docs, followups. Now DB-native (`app_translations`). | `cleanup` (run_all) |
| **Daily / nightly bug triage** | ~21 | Pull open rows from `bug_reports`, spin a **local session per bug**, fix via conquering-campaign, flip status to Fixed, file new bugs found. | `bug-fix-workflow` |
| **Per-bug scheduled task** | ~10 | One cron task per bug (`bug-239…bug-248…`) running autonomously with no user present. | scheduled-task + bug-fix |
| **Post-campaign cleanup** | ~15 | After every build campaign: `/cleanup followups` → locate `99-risk-sweep.md` open items → targeted lint/i18n/postgres sweeps for what the campaign touched. | `cleanup followups` |
| **Release train** | ~8 | "clean up, **merge all branches + PRs into main**, bump version, push" — the version-and-merge closeout. | `update-app-version` + cleanup |
| **Lessons / skill-upgrade mining** | ~3 | "pull data from last + archived sessions, note down lessons and the skill's upgrade route" (e.g. cleanup, conquering-campaign). **This very task is that routine, for workflows.** | `skillsmith` / `storm-investigation` |
| **Implementation / simple-English audit** | ~6 | Post-build plain-English audit of what shipped + what's pending. | guidance-only audit |

**Finding:** the **bug-triage → conquering-campaign → post-campaign cleanup → release train** loop is
the most exercised, most automated, most proven workflow in the entire system — and it barely appears
in `workflows.json` (only thin `quick-fix` + `conformity-sweep`). The SA guild advertises workflows it
has rarely run; Lex runs workflows the guild never wrote down.

## 6. Lex interactive workflow families

Ranked by volume across the 522 sessions.

1. **Bug Cycle** (`bug-cycle`) — **dominant** (#239 → #306, dozens). Pull bug from `bug_reports` → read `primary_instructions.md` → reproduce → fix via `/conquering-campaign` → flip status → vault-log. Reporter variants (Atta / محمد عاطف / dalia), screenshot-attached bugs. → *the lived form of `quick-fix`+`bug-fix-workflow`.*
2. **Conquering-Campaign BUILD** — multi-wave features touching ≥3 surfaces, multi-phase (Campaign A/B/C; phases 0 / BE-K1 / BE-K2). Plan → waves → cleanup → close. → *the lived `standard-mission`/`architecture-build`.* (May 29–Jun 21, very frequent.)
3. **Conquering-Campaign AUDIT** — app-wide consolidation (FE/BE component merge), RLS-bundle audits, dark-mode/color audits, pending-work audits → `audit-campaigns/…/99-synthesis.md`. (Jun 2, Jun 20.)
4. **Security Sweep** (`security-sweep`) — RLS policies, SECURITY DEFINER RPCs, anon-leak hunts, advisor pulls; often **read-only / propose-don't-apply** with explicit sign-off gate. (Jun 2, Jun 15, Jun 18 wages-leak, Jun 20 mobile-prep.) → distinct from `conformity-sweep` (security ≠ self-consistency).
5. **i18n / Hardcoded-Text Extraction** — app-wide: find raw text → keys → translate 6 locales → consolidate → DB-source-of-truth (Bug #303, `app_translations`). (Jun 3, Jun 6, Jun 21.)
6. **Legal Codex Load+Translate+Publish** — `codex-law-translate`: AR canonical → translate 5 locales → adversarial QA → publish; loop through `source_laws` (Commercial Code Y1999 L17, labour law). → *the lived `legal-codex`.* (Jun 5, Jun 20, Jun 21.)
7. **Marketing / Public-Panel Audit** ⚠ **no owning member** — "audit from a marketing-firm perspective", SEO/Google catchability, Cloudflare-style footer/header, team page from live roster, truth-in-advertising removals, the `marketing-overview.md` doc, "what infrastructure for a paid campaign". (Jun 2 ×3, Jun 17, Jun 20 ×2, Jun 23.) **~10 sessions, zero owner.**
8. **Corporate-Tools / Calculator Build** (`tool-forge`) — Egyptian-law public calculators: wage-tax, social-insurance, severance, inheritance, feddan/kirat land, customs. A repeatable legal-tool pattern (audit law → build calculator UI → disclaimer → resources page). (Jun 2–Jun 23.)
9. **Mobile-Prep / DB-Source-of-Truth** — make portals responsive (#302), move i18n (#303) + permission catalog (#304) out of web-only TS into DB so a future mobile client shares one source. (Jun 19–21.)
10. **Finance-Critical Data Migration** — relocate historical financial files into branch-stock GFNs, backfill, QR seed; **plan + dry-run BEGIN/ROLLBACK + reconcile** safety protocol. (Jun 19–20.) → distinct from normal `architecture-build`.
11. **Feature / Permission Request** — implement `feature_requests` (#276 notarization offices), grant `permission_requests` (#277 access) via the file-access model. (Jun 6.)
12. **Error-Paste → Fix-All-Similar** — user pastes a console/build/Postgres error → fix it **and all of the same class** app-wide. (recurring across the whole span.)
13. **Performance Fix** — query timeouts, materialize views, perf follow-ups (transactions-timeout, Jun 2). → the lived `performance` skill.
14. **Cross-Repo Skill Sync** — reconcile `claude-skills` repo ↔ Lex on-device skills by version ("merge higher version both ways"). (Jun 16, Jun 19.) + Dev-server-detached ops, AI-to-Supabase research, blog/content-surface build (minor.)

## 7. Cross-project findings & consolidated recommendation

**A. The marketing gap is real and recurring.** Marketing/public-panel work is a *top-5* Lex family
(~10 sessions) yet the guild has **no Marketing member and no marketing workflow**. S24 flagged it
("we have no marketing agent … one of our worst nightmares"); the Lex data proves the demand. **Recruit
a Marketing member** (owns SEO/public-panel/campaign-audit skills) — the single highest-value roster move.

**B. The guild documents the wrong workflows.** `workflows.json` over-represents rare guild-building
(art, starmap) and under-represents the loop that actually runs daily (bug → campaign → cleanup →
release). Bring the catalogue in line with reality.

**C. Two safety-grade workflows are unwritten.** `security-sweep` (propose-don't-apply gate) and
`finance-critical-migration` (dry-run/rollback/reconcile) both carry explicit safety protocols the
Guild Master enforces by hand every time. Formalize them so the protocol is structural, not memory.

**Consolidated "formalize next", whole system:**

| # | Add | Why | Lens |
|---|---|---|---|
| 1 | **Recruit a Marketing member** | ~10 owner-less sessions; declared #1 nightmare | roster |
| 2 | `bug-cycle` | the single most-run workflow; only thinly in `workflows.json` | Lex |
| 3 | `cleanup-rotation` + `release-train` | run daily/automated, never formalized | Lex |
| 4 | `security-sweep`, `finance-critical-migration` | encode the safety gates structurally | Lex |
| 5 | `tool-forge` | repeatable legal-calculator pattern, growing | Lex |
| 6 | SA: `art-forge`, `arsenal-forge`, `strategic-audit` | top SA candidates (§4) | SA |

---

*Generated by the Strategist — SA pass mined by the MiniMax doer + Strategist gate; Lex pass (522 sessions) synthesized directly by the Strategist from a signature histogram + intent digest.*

---

# Cowork trove (§8–§10) — the missed store

> **The Guild Master was right:** much of the work lived in **Claude Cowork**, a *separate* session
> store (`~/Library/Application Support/Claude/local-agent-mode-sessions/`) the first two passes never
> touched. **562 unique Cowork sessions, back to 2026-03-15** — an entire era before the Claude Code
> store begins (2026-05-29). Mined from session metadata (title + initial intent), since Cowork keeps
> config/state locally and the transcript proper in the VM.

## 8. What only Cowork revealed

**A. Scheduled cron automations** (real skills under `~/Documents/Claude/Scheduled/`) — none were in `workflows.json`:
- `whatsapp-mourning-to-calendar` — scans WhatsApp for mourning/condolence (عزاء) notices → calendar events + 1h-before alert.
- `daily-whatsapp-summary` · `housekeeping-daily` / `-hourly` / `-weekly` · `auto-improvement` (the ancestor of the skillsmith routine).
- `stock-laws-scanner` · `pdf-to-markdown-extractor` · `stock-and-extract` — law-PDF ingestion loops.
- `lex-relationship-intel` / `-weekly` — client/contact relationship intelligence; ends with a plain-English summary + checkpoints; later upgraded to use per-model agents.
→ **captured as `scheduled-routine` (Standing Watch).**

**B. A comms layer** (Gmail + Calendar + WhatsApp MCP) — email/calendar/WhatsApp triage, inbox→tasks→calendar, meeting prep, daily digests, contacts→broadcast-groups / VCF. → **captured as `comms-triage`.**

**C. The lawyer's actual desk** — drafting client correspondence and bilingual (AR/FR/EN) legal instruments: contracts, declarations, resignation letters, legal-memo→article, bilingual civil-code HTML. → **captured as `legal-draft`.**

**D. The Flutter → Next.js migration era** (all of March) — page-by-page rebuilds (Files/Tasks/POAs/IDs/Documents/Transactions/Cases/Chat) matching the old Flutter app. A one-time campaign → folds under `standard-mission` / `architecture-build`.

**E. The single most common Cowork debug** — *"column/relation … does not exist"*: the front end expects a column a SQL view/RLS doesn't have (~30+ sessions). A mechanical fix-the-view loop → folds under `quick-fix` / `bug-cycle`.

**F. Deploys** — Vercel, then **Cloudflare Pages/Workers**, DNS migration, remote tunnels, bundle-size walls. → folds under `release-train`.

**G. Marketing/BD, a THIRD time** — capabilities sheet, PDF partnership proposals for law firms, pricing pages, "target law firms" strategy. Three independent eras all demanded marketing → vindicates the recruitment of **`the-herald`**.

### 8b. Deep dive — the nested sandboxes (second Cowork pass)

The first Cowork pass read only session **metadata** (`local_<uuid>.json`). Each session is actually a full
**sandbox**: `2,856 .jsonl` transcripts + per-session `audit.jsonl`, `outputs/` deliverable folders, and copies of
scheduled-task definitions. The deliverables confirm the new workflows are real — shipped
`Contrat_…_SWAT_AR-FR.pdf` and `Notification_non-renouvellement_FR-AR.docx` (→ `legal-draft`),
`Lex_Council_Translation_Report.pdf` (→ `legal-codex`), `Y1959 L57.md` / `harvest-digest-*.md` (→ `law-harvest`).

**The 23 cron automations** (`~/Documents/Claude/Scheduled/` + 3 in `~/.claude/scheduled-tasks/`) — the first pass saw 8. Each maps to a workflow:

| Cron family | Tasks | Maps to |
|---|---|---|
| Housekeeping | `housekeeping-daily/-hourly/-weekly`, `lex-council-app-housekeeping`, `lex-cleanup-rotation` | `cleanup-rotation` |
| Bug / skills | `lex-daily-bug-triage`, `skillsmith-routine`, `auto-improvement` | `bug-cycle` / `skill-forge` |
| Email & WhatsApp | `gmail-report`, `daily-whatsapp-summary`, `whatsapp-summary`, `whatsapp-daily-draft-agent`, `send-email-responses-reminder` | `comms-triage` |
| Deadlines & nudges | `deadline-*` (×6 matters), `contact-colleagues-progress-check`, `jeddah-hmco-thank-you` | `scheduled-routine` |
| Relationship/BD | `lex-relationship-intel` | **`relationship-intel`** (new) |
| Law library | `stock-and-extract`, `stock-laws-scanner`, `pdf-to-markdown-extractor` | **`law-harvest`** (new) |
| DB health | `supabase-advisor` | `security-sweep` |
| Strategy | `auto_strategizing`, `strategies-review` | `strategic-audit` / `skill-forge` |

These crons are sophisticated multi-agent pipelines (relationship-intel runs Harvester=haiku → Profiler=sonnet → Strategist=opus, resumable via `_state.md` checkpoints) — the MiniMax-doer/Claude-gate shape, generalized and scheduled.

## 9. The rebuilt star map — 24 workflows

| Workflow | Category | Lead | Status |
|---|---|---|---|
| standard-mission | Build & Fix | Strategist→Developer | kept (improved) |
| quick-fix | Build & Fix | Developer | kept (improved) |
| **bug-cycle** | Build & Fix | Strategist→Developer | **new** |
| architecture-build | Build & Fix | Architect | kept (improved) |
| **security-sweep** | Build & Fix | Architect | **new** |
| design-sprint | Design | Designer | kept |
| **art-forge** | Design | Designer | **new** |
| legal-codex | Legal | Translator | kept (improved) |
| **tool-forge** | Legal | Architect→Developer | **new** |
| **legal-draft** | Legal | Translator | **new** |
| **law-harvest** | Legal | Architect→Translator | **new** |
| **comms-triage** | Comms & Automation | Butler | **new** |
| **scheduled-routine** | Comms & Automation | Strategist→QM | **new** |
| cleanup-rotation *(was implicit)* | Hygiene & Release | Quartermaster | **new** |
| **release-train** | Hygiene & Release | Quartermaster | **new** |
| conformity-sweep | Hygiene & Release | Quartermaster | kept |
| guild-log-sync | Hygiene & Release | Butler→QM | kept |
| market-recon | Research & Intel | Merchant | kept (scoped to trading) |
| **marketing-audit** | Research & Intel | **Herald** | **new** |
| **relationship-intel** | Research & Intel | Herald→Strategist | **new** |
| **strategic-audit** | Guild Self | Strategist | **new** |
| skill-forge | Guild Self | Quartermaster | kept (improved) |
| **arsenal-forge** | Guild Self | Strategist→QM | **new** |
| **workflow-forge** | Guild Self | Strategist→QM | **new** |

Merged-not-split (folded into a broader workflow rather than given their own entry): schema-drift fixes → `quick-fix`/`bug-cycle`; performance + finance-critical migration → `architecture-build`; i18n/hardcoded extraction → `cleanup-rotation`; deploys → `release-train`; Flutter→Next migration → `standard-mission`.

## 10. Action taken (2026-06-26)

- **`workflows.json` rebuilt 9 → 24** — 15 added (13 first pass + `relationship-intel`, `law-harvest` from the deep dive), 6 improved, all categorized (new `category` field). Every workflow keeps the QM-conformance close + Butler plain-English report gate.
- **`gen-workflow-art.cjs`** — added a Fallen Sword art prompt for each of the 15 new ids; all 24 sigils forged via MiniMax into `workflow-art/` (artPng ✓ ×24).
- **`marketing-audit` wired to `the-herald`** (the marketing member recruited in decision #39) — the audit's "biggest gap" is closed in the live repo.
- **`scheduled-routine` documents all 23 cron automations**; `relationship-intel` and `law-harvest` capture the two cron families distinct in kind.
- **Logged** as guild-log decisions **#40 and #41** (type: workflow); `build.py` regenerated `guild-data.*`; **version 6.30.29 → 6.37.35**.
- **`conformity_check.py` → ✓ FULL CONFORMITY** (members=9, skills=36, workflows=24).

> Note (weapon liveness, carried from `STRATEGIST-AUDIT.md`): the new workflows lean on `minimax` (doer, live) and the thinker panel (gate). `conformity_check.py` still flags `gpt-5.5`, `kimi-k2.7`, `nemotron-3-ultra` as **not firing on this device** — `art-forge`, `arsenal-forge`, `strategic-audit` are only as strong as those weapons once provisioned.

---

*Cowork addendum by the Strategist — 562 Cowork sessions + their nested sandboxes (2,856 transcripts, outputs, 23 cron skills) mined from the local-agent-mode store; star map rebuilt 9 → 24, wired, logged, and conformity-verified.*
