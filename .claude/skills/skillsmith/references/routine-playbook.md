---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Mode: routine — the daily STORM-driven skill-evolution loop

Goal: **once a day, autonomously make the skill library better.** Each run mines your code, projects,
and session transcripts; researches every candidate change with the STORM method
(`storm-method.md`); writes its findings to a durable ledger; applies the high-confidence ones
(upgrades, new skills, bug fixes — skillsmith itself included); and commits + pushes, leaving a
human-readable trail you can watch and revert.

This mode reuses `upgrade-playbook.md` and `create-playbook.md` as its execution primitives. It does
not invent a second way to bump/register/sync — it drives the existing ones, gated by STORM.

> **Autonomy (Atta's choice, 2026-06-20): FULLY AUTONOMOUS.** The run applies upgrades, creates
> skills, and commits+pushes without asking — but ONLY for findings whose STORM peer-review
> confidence is **≥ 8/10** and that clear the guards in §R4. Everything it does is logged to the
> ledger and lands as a labeled, revertible git commit. Lower-confidence findings are written to the
> ledger as proposals, not applied.

> **Visibility (Atta's requirement): the run must be watchable.** It narrates every stage to a live
> markdown ledger entry as it goes (not just at the end), and the runner tees CLI output to a dated
> log. You can `tail -f` either, open them in an editor, or read the git commits. To watch it happen
> live, invoke `routine` yourself in an interactive session (see §R7).

---

## The five stages

```
A. HARVEST   gather the corpus           (scripts/routine_scan.py — read-only)
B. RESEARCH  STORM per skill + gaps       (storm-method.md — model / Workflow fan-out)
C. NOTEBOOK  write the dated ledger entry (references/routine-ledger/YYYY-MM-DD.md)
D. EXECUTE   apply ≥8/10 findings         (upgrade-playbook + create-playbook, guarded)
E. REPORT    commit, push, summarize      (one labeled commit per applied change)
```

### Stage A — Harvest (read-only)

**Pre-flight — resolve the repo before anything else (added Run 28, 2026-06-24).** The canonical repo
is **`Attax-io/star-alliance`**, checked out at **`~/Documents/Claude/Projects/star-alliance`**
(renamed from `claude-skills` on 2026-06-24 — GitHub auto-redirects the old name). The scheduler hands
you a path; before you scan, **make sure it actually exists and is the canonical checkout** — the repo
lives under iCloud `~/Documents` and a rename / eviction / fresh machine can leave the handed path
dead. A run that can't find the repo dies at Stage A, so self-heal instead of aborting:

```sh
REPO="$HOME/Documents/Claude/Projects/star-alliance"
[ -d "$REPO/.git" ] || gh repo clone Attax-io/star-alliance "$REPO"   # re-clone if missing
git -C "$REPO" remote get-url origin                                   # expect …/Attax-io/star-alliance.git
```

- If you were handed a **stale `…/claude-skills` path**, redirect to `…/star-alliance` — do **not**
  `gh repo clone` into the old name (gh follows the GitHub redirect and creates a confusing
  *redirect-duplicate*; clone to the explicit `star-alliance` target instead). If a duplicate already
  exists, confirm it has no unique commits/working changes, then delete it and operate the canonical
  checkout only.
- Because a fresh checkout makes every file's mtime "now", **take cooldowns (§R4.5) from `git log`
  dates, not file mtime**, on any run where the repo was just (re)materialised.

```sh
python3 skillsmith/scripts/routine_scan.py --days 14 --out skillsmith/routine-logs/scan-YYYY-MM-DD.json
```

The scan (see the script's header) gathers, **read-only**:
- every skill's name, `metadata.version`, Cowork status, mtime, and days-since-last-change;
- every mention of each skill across the configured roots (default: the `star-alliance` repo, every
  project under `~/Documents/Claude/Projects`, and your session transcripts in
  `~/.claude/projects/**/*.jsonl`, last `--days`);
- friction snippets — lines near a skill mention containing error/fail/bug/confus/wrong/should/instead/
  "didn't work" — these are the upgrade signal;
- recurring session topics with **no** matching skill — the new-skill signal.

Open the JSON (or let Stage B read it). Nothing is written outside `routine-logs/` here.

### Stage B — Research (STORM)

For each skill that the harvest flags as **active or frictionful** (skip dormant, zero-mention skills
this run), run the four STORM steps from `storm-method.md`: five-persona scan → contradiction map →
synthesis dossier → peer review with confidence scores. Also run one STORM pass on the **gap list**
(recurring topics with no skill) to decide which, if any, are worth creating.

**Run it as a Workflow when the active set is large.** One subagent per persona per skill is the
clean fan-out; a synthesis agent and a peer-review agent close each skill. Pattern:

```
pipeline(activeSkills,
  s => parallel(PERSONAS.map(p => () => agent(personaPrompt(p, s, corpus[s]), {schema: VERDICT}))),
  verdicts => agent(synthesisPrompt(verdicts), {schema: DOSSIER}),
  dossier  => agent(peerReviewPrompt(dossier), {schema: GRADED}))
```

Budget the fan-out; don't STORM all 28 skills every day (see §R5).

**Dossier build guard.** When assembling a per-skill dossier for the doer (SKILL.md body + scan signals), pass the SKILL.md body whole — most fit the 16000-token budget. Never hard-truncate mid-sentence to fit a cap; that makes STORM report a phantom "file truncated" top bug, wasting the slot and poisoning the dossier (observed 2026-06-29 on supabase, skillsmith, conquering-campaign, each SKILL.md > 9000 chars). If a body truly overflows, summarize it and tell STORM it was summarized, or split across calls — but never raw-cut.

**Re-aim the lens — convergence on one question ≠ no work left (the Run-12 lesson, codified).** Runs
1–11 graded only the *friction snippets* (is this mention noise?) and converged to a no-op for ten
straight runs — yet Run 12 found a real, never-adjudicated defect the instant it changed the
**question** instead of the corpus. So every run that the friction lens reports converged MUST rotate
to a second lens before declaring no-op:

1. **Body-vs-reality STORM** on the highest-mention skill that has **never been body-STORMed** — diff
   the skill's prose against what the project *memories* and *session transcripts* say actually
   happens (this is how `dev-server`, `bug-fix-workflow`, and `codex-law-translate` upgrades were all
   found: zero friction snippets, large body-vs-reality gaps).
2. **Repo↔device drift** — a skill hand-upgraded on one side but not the other (the R13 class).
3. **Cross-skill contradiction** — a skill mandating what another skill / a project memory bans.

A converged friction lens is a signal to *re-aim*, not to stop. Record which lens produced the no-op so
the next run rotates to a fresh one rather than re-grading the same snippets.

**Standing attended-only class — do NOT keep autonomously re-deferring it.** The `cleanup` docs-mode
INDEX.md gap (~540 orphan vault-logs + ~1299 broken wikilinks in the **Lex Council** repo) has been
re-deferred 5+ times. It is **out of autonomous routine scope** and must stop consuming STORM budget
each run: it lives in a *foreign* repo (not `star-alliance`), targets a *fork* skill (`cleanup`,
edit-with-care per §R4.2), and is gated on a human reading the INDEX.md curated-vs-generated contract
first. Treat it as a one-line ledger carry ("attended-only, see prior defers") — do not re-STORM it
unless a new, in-scope signal appears.

### Stage C — Notebook (the durable memory)

Append a dated entry to **`references/routine-ledger/YYYY-MM-DD.md`** (format in
`routine-ledger/README.md`). It records, per skill: the dossier, the ranked upgrade routes, the
confidence scores, the new-skill candidates, and the bugs found. **Write this incrementally as Stage
B completes each skill** — this file is how you (and the user watching) see what the run is thinking
before it acts. The ledger is committed; it is the routine's cross-run memory, so the next run can
see what was proposed-but-deferred and whether a past upgrade actually helped.

### Stage D — Execute (autonomous, guarded)

Walk the graded findings high-confidence-first. For each finding with **peer-review confidence ≥ 8**
that clears §R4:

- **Upgrade an existing skill** → run `upgrade-playbook.md` (edit → bump SemVer → changelog →
  `skill_registry.py check NAME` → `skill_registry.py write` → re-sync device). One commit.
- **Create a new skill** → run `create-playbook.md` (skill-creator → make upgradeable → place in repo
  → register → optional install). One commit.
- **Fix a bug** in a skill → treat as a PATCH upgrade.

Respect the per-run budget (§R5). Everything below 8/10 stays in the ledger as a proposal for a human
or a future run.

### Stage E — Report

- **Conformity-close first (Invariant #8) — the Quartermaster's final gate.** Before committing, rebuild the guild data and run the Compliance Audit: `python3 build.py && python3 tools/conformity_check.py`. It must report **FULL CONFORMITY** (exit 0) — guild-data↔json parity, `meta.counts`, workflow gates/actors, member arsenal order, decision-conformity, and the **K-invariant** (skill dirs == `skills-meta.json` == generated skill ids) all hold. If it FAILS, fix the contradiction **before** the commit — a created / removed skill not yet in `skills-meta.json` + `build.py` output, a stale count, a broken ref — never ship a contradiction. Stage the regenerated `guild-data.*` (+ `skills-meta.json`/`domains.json` on a create/remove) in the **same** commit as the skill change.
- **Critic gate (Invariant #10) — independent verification before each commit.** After conformity-close, run the Evolution Engine's VERIFY organ on the staged diff and **fail closed**: `git diff HEAD | python3 evolution/verdict.py --fail-closed`. Exit 0 (pass/concerns) → proceed to commit. Non-zero (BLOCK, or the critic is unreachable on this unattended run) → **DO NOT commit this finding**; write the critic's verdict to today's ledger and move to the next finding. This is the gate that stops `routine` from self-grading its mid-run commits — the implementer never grades its own work (HARNESS-BOOKS 9.9).
- Commit each applied change separately, message:
  `skillsmith routine YYYY-MM-DD: <verb> <skill> — <one-line> [conf N/10]`.
- `git push origin main`.
- Write a **Run Summary** at the top of the ledger entry: what was applied, what was deferred, total
  cost, and the single highest-value proposal for next time.
- If a push notification channel is configured, emit the one-line summary.

---

## §R4 — Guards (every autonomous action passes ALL of these)

1. **Confidence ≥ 8/10** from STORM peer review. No exceptions for auto-apply.
2. **Forks + externals: edit them, but with their handling — never blind.** (Atta opted these IN,
   2026-06-20.) `cleanup` and `conquering-campaign` are forks (repo = lean Cowork edition, device =
   full canonical/monolith); the routine MAY upgrade them, but per their fork rules
   (`sync-playbook.md` §S3 — edit the correct edition, re-apply the lean packaging, NEVER rsync the
   monolith over the stub). The sync scripts deliberately `SKIP` forks on `apply`, so do that device
   sync by hand. `impeccable` is an external, npx-managed package (~37 MB): the only valid "edit" is
   `npx impeccable` to refresh — hand-edits to its source get clobbered, so a finding against it
   becomes a *refresh* action, not a source edit. Apply the same ≥8/10 gate to all three.
3. **Cowork-clean after the edit.** `skill_registry.py check NAME` must report 0 hard violations, or
   the edit is reverted and logged. Description stays ≤1024 chars with no `<`/`>`.
4. **No duplicate skills.** Before `create`, confirm the idea isn't already covered (grep the registry
   + descriptions). A near-duplicate becomes an *upgrade* of the existing skill instead.
5. **Cooldown.** Don't re-touch a skill upgraded by the routine in the last **3 days** unless the
   finding is a real bug (correctness), not a polish.
6. **Self-upgrade is special** — see §R6.
7. **Reversible.** Every change is its own commit on `main`. The routine never force-pushes, never
   rebases, never `git push origin <branch>:main`. A bad day is `git revert`.

---

## §R5 — Per-run budget (so it converges, not churns)

- **Top-N actions per run: default 3** (highest combined synthesis+peer-review score first). The point
  is steady daily improvement, not rewriting everything at once.
- **STORM at most ~8 skills per run** (the active/frictionful set, ranked by mention count + friction).
  Dormant skills are skipped until a session actually exercises them.
- **`--max-budget-usd` cap** on the headless invocation (default $10/run, set in `run_routine.sh`) is
  the hard ceiling; if STORM is mid-skill when it trips, finish the current skill, write the ledger,
  and stop cleanly.
- Tune N / the cap / the day-count at the top of `run_routine.sh` and in the `routine_scan.py` flags.

---

## §R6 — Self-upgrade safety (skillsmith improving skillsmith)

The routine is allowed to upgrade **skillsmith itself** — that's the point of "improve my skills
including skillsmith." But a self-edit must never break the run that makes it:

1. **Do skillsmith's own changes LAST**, after every other skill is done and the registry is written.
2. The running process already loaded the *old* skillsmith into context, so a self-edit only takes
   effect **next** run — never hot-swap mid-run.
3. After a self-edit: **`skill_registry.py check skillsmith` must pass** — this is the hard gate (no
   deps). Also run the skill-creator `quick_validate.py` **when `pyyaml` is importable** (best-effort:
   it needs `import yaml`, which is absent on the stock homebrew python3 — do NOT
   `--break-system-packages` to get it; the registry check is the gate that matters). If the gate
   fails, **`git checkout` the self-edit** (revert it) and log the failure as a proposal. A broken
   skillsmith must not be committed.
4. Bump skillsmith's own `metadata.version` + changelog like any other upgrade.

---

## §R7 — The scheduler (how "each day" fires) + watching it

The routine runs **locally** (it needs your files + session transcripts; cloud routines can't see
them). Primary mechanism = a **native Claude Code routine** (it shows in the app's *Routines* panel,
next to your other routines). The macOS LaunchAgent is an optional fallback.

### Primary: native Claude Code routine — in the *Routines* panel (set up 2026-06-20)
Registered via the scheduled-tasks system as task **`skillsmith-routine`**
(`~/.claude/scheduled-tasks/skillsmith-routine/SKILL.md`), cron `0 6 * * *` (daily ~06:00 local,
small jitter). Enable / disable / retime / **Run now** from the Routines panel, or via
`mcp__scheduled-tasks__update_scheduled_task`.

- **Runs while the Claude Code app is open** (if it's closed when due, it runs on next launch).
- **Permissions:** the first run pre-approves the tools it needs (Bash git/python, Edit/Write, Skill,
  Workflow, `git -C <repo> push`); approvals are stored on the task and auto-applied to later runs.
  **Click "Run now" once** to pre-approve so the 06:00 runs never stall on a prompt.
- **No hard `$` cap** here (that was a LaunchAgent-only flag) — the per-run budget is the soft §R5
  limit (top ~3 actions, ~8 skills STORMed), enforced by the task prompt.

### Optional fallback: macOS LaunchAgent — runs even when the app is closed, hard `$` cap
`scripts/run_routine.sh` (headless `claude -p` with `--permission-mode bypassPermissions` +
`--max-budget-usd` cap, tees to `routine-logs/`) fired by `assets/com.attax.skillsmith-routine.plist`.
Use only if you want app-closed running or the hard dollar cap — and if you install it, **disable the
native routine first** so it doesn't double-run.
```sh
cp assets/com.attax.skillsmith-routine.plist ~/Library/LaunchAgents/ \
  && launchctl load -w ~/Library/LaunchAgents/com.attax.skillsmith-routine.plist   # on
launchctl unload ~/Library/LaunchAgents/com.attax.skillsmith-routine.plist          # off
```

### Watch a run
- Live, on demand: run **`/skillsmith routine`** in an interactive session and watch it happen.
- A scheduled run: it notifies on completion; or open today's ledger entry
  `references/routine-ledger/<date>.md`, or read the commits
  (`git -C ~/Documents/Claude/Projects/star-alliance log --oneline --since=today`).

---

## Quick recipes

- **"run the routine now"** → `routine` mode, Stages A→E, fully autonomous per §R4.
- **"what would the routine do? don't apply"** → run Stages A→C only (harvest + STORM + ledger), then
  stop. Everything is a proposal; nothing is executed.
- **"turn the daily run on/off"** → the `launchctl load`/`unload` pair in §R7.
- **"why did it change skill X yesterday?"** → read `routine-ledger/<date>.md` (the dossier +
  confidence) and `git show` the commit.

---

## Routine integrity (mined from full session history)

These guard the routine's own verdicts against false confidence:

- **Verify every number, claim, and gap against source before publishing a verdict.** A metric without
  a source read is a guess, not a finding.
- **Distinguish "skill prescribed" from "skill failed"** in the friction harvester. Absence-of-friction
  is a *soft* signal, never proof of correctness — a quiet run can mean the skill worked OR was never reached.
- **Isolate a single skill's contribution** before attributing any directory-wide metric to it; add
  semantic verification to keyword-proximity checkers (distrust a checker that only ever flags false positives).
- **Log sub-threshold dissents explicitly** in multi-persona synthesis — prove convergence isn't groupthink.
- **Never hand-edit vendored upstream skills** (`author:`/`organization:` in frontmatter, e.g. the two
  `supabase*` skills). Local edits get clobbered on the next sync — route the lesson to a guild-owned
  skill or a local overlay instead.
- **NO-OP immediately when the target identity is undefined** — skip the redundant on-disk search.
