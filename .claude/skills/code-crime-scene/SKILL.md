---
name: code-crime-scene
description: >-
  Forensic investigation style for any codebase, system, or process — treat it as a crime
  scene. Gather historical evidence first (never just the current snapshot), cross-reference
  multiple signals, and find where those signals converge (the "hotspot"). Use when someone
  says "investigate this codebase", "audit the system health", "where are the real problems
  in this code", "find the bottlenecks", "where should we focus refactoring", "why does this
  area keep breaking", or any open-ended investigation of a system's health, quality, or
  organizational dynamics. Based on Adam Tornhill's forensic psychology method from
  *Your Code as a Crime Scene* (Pragmatic Bookshelf, 2015).
metadata:
  version: 1.0.0
type: Skill

---
# Crime Scene Investigation (Code)

**The core principle:** the current snapshot of a codebase tells you *what* exists. The history
of commits tells you *where the real problems are*. Static code analysis sees the body; forensic
analysis finds the killer.

Borrowed from geographical offender profiling in criminal psychology: criminals move through
physical space in patterns; developers move through a codebase in patterns. Both leave traces.
Both traces reveal the offender.

> "Code that has changed in the past is likely to change again. Code changes for a reason." — Tornhill

## When to run this skill

Any time the investigation is open-ended — you don't yet know what the problem is, only that
something is wrong. If you already know the module to fix, go straight to `hotspot-radar` or
`temporal-coupling-audit`. Run this skill when you need to *find* the crime scene first.

## The Six-Phase Investigation

Work the phases in order. Each one narrows the suspect list. Stop when the top suspects are
clear enough to act on — don't force all six if three is enough.

---

### Phase 1 — Gather the scene (never trust the snapshot)
Collect raw evidence from the version-control system. The code you see right now is the crime
scene *after* it's been disturbed. The git log is the forensic record no one cleaned up.

**Evidence to gather:**
- `git log --numstat --pretty=format:'[%H]' [--after="YYYY-MM-DD"]` → change frequency per file
- `git log --format='%an' -- <file>` → author fingerprints per module
- `git log --all-match --grep="fix\|bug\|hotfix" --name-only` → defect-linked changes

**Principle:** use a bounded time window — the last 6–12 months of activity reflects current
reality; older history is archaeology, not forensics. If the repo is young, use all history.

---

### Phase 2 — Profile the offender (change frequency)
Count how many commits touched each file. Files that change most often are where the team
*actually spends its time* — not what the architecture diagram says they should spend time on.

**High change frequency = high developer effort = likely pain area.**

This is not yet a hotspot — a config file or seed data file might change often for benign reasons.
Change frequency narrows the suspect list; it doesn't convict.

**False positive filters:** exclude `package-lock.json`, generated files, migration files with
sequential changes, build artifacts, and changelog/version files — they change mechanically.

---

### Phase 3 — Assess the neighborhood (complexity dimension)
Measure the complexity of the high-frequency files. Lines of code (LOC) is a sufficient proxy.
Indentation depth is an even better proxy for cyclomatic complexity (deeply nested code = many
conditional paths).

**The hotspot formula:** `hotspot score ≈ change_frequency × complexity`

A complex file that *rarely changes* is a latent bomb, not an active crime scene. A simple file
that changes constantly is probably a config or router — low cost. The **overlap of high complexity
and high change frequency is your hotspot** — that's where the effort goes and the bugs live.

Research backing: Nagappan & Ball (2005) found change frequency is a stronger defect predictor
than any static metric. Multiple studies confirm change frequency + LOC outperforms more
elaborate measures.

---

### Phase 4 — Map the connections (temporal coupling)
Which files always change together? Co-changing files reveal hidden dependencies the module
structure doesn't show. This is your "who was with the victim at the time?"

**Expected coupling** (not a crime): model + migration + test change together — fine.
**Surprising coupling** (a crime): auth module co-changes with payment module co-changes with
search module → hidden global state, god object, or architectural decay.

Coupling score = `(co-changes) / min(changes_A, changes_B)`. A score above ~30% is worth
investigating. A score above ~50% in an unexpected pair is architectural decay.

See the `temporal-coupling-audit` skill for the full coupling workflow.

---

### Phase 5 — Build the knowledge map (ownership and silos)
For each top suspect, who has touched it? Run `git shortlog -s -n -- <file>` per hotspot.

**Signals:**
- **Single dominant author (>60% of commits)**: knowledge silo — if they leave, the module is
  orphaned. Also: no peer review = silent accumulation of tribal patterns.
- **Many authors with low individual counts**: high coordination overhead, ownership diffusion,
  and Conway's Law effects — more authors per module correlates directly with more post-release
  defects (research: Nagappan et al., 2008).
- **Author turnover** (contributors disappear over time): knowledge loss in progress.

The knowledge map tells you both the *technical* and *organizational* risk in each hotspot.

---

### Phase 6 — Verify intuitions with data
Form a hypothesis after phases 1–5. Then challenge it.

> "Human intuition is wonderful for making quick decisions. The quality of those decisions,
> however, is not always wonderful." — Tornhill

- Does the suspected hotspot appear at the top of *all* three dimensions (frequency, complexity,
  coupling)? Triple convergence = high confidence.
- Is there a simpler explanation? (A module might score high because a mechanical rename swept
  through it — check the commit messages.)
- Is the complexity score inflated by auto-generated boilerplate? (Strip it and re-score.)

**Never act on a single signal.** Wait for convergence across at least two dimensions before
declaring a hotspot confirmed.

---

## Output contract

Deliver a **ranked suspect list** with evidence, not an opinion:

```
HOTSPOT REPORT — <system name> — <date window>
───────────────────────────────────────────────
Rank 1: src/auth/session.js
  Change freq:   47 commits (top 2%)
  Complexity:    812 LOC, avg indent 4.1
  Coupling:      co-changes with payment.js (52%), user.js (44%)
  Authors:       3 active, 1 dominant (68% of commits — Marco)
  Verdict:       ★★★ CONFIRMED HOTSPOT — refactor priority
  Next step:     temporal-coupling-audit on auth/ + payment/ boundary

Rank 2: ...
```

Include: rank, file path, the three evidence scores, coupling pairs, authorship note, verdict
confidence (★ = one signal, ★★★ = triple convergence), and a concrete next step.

---

## Principles (distilled from Tornhill)

1. **Evidence before opinions.** Mine the history; don't ask the team to self-report problems.
   Self-reports have hindsight bias and political filters. The log has neither.
2. **Complexity alone is not a crime.** A complex module no one touches is a latent risk, not an
   active hotspot. Target complexity that also has high developer activity.
3. **Behavioral data beats structural data.** What *actually changed* beats what *should* change
   according to the architecture diagram.
4. **Three-signal convergence is your conviction.** One signal = look closer. Two = likely.
   Three (frequency + complexity + coupling) = act.
5. **Time-window is a tool.** Shrink it to see current pain; expand it to see structural trends.
   A hotspot that appeared only in the last 90 days is a fresh wound — a different story than one
   that has been there for three years.
6. **False positives are real.** Generated files, migration sequences, and changelog commits
   inflate scores. Filter mechanically before ranking.

## Versioning

Bump `metadata.version` on any change. Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write` after a bump.

## Changelog

- **1.0.0** — Initial release. Six-phase forensic investigation method derived from Adam Tornhill,
  *Your Code as a Crime Scene* (Pragmatic Bookshelf, 2015).