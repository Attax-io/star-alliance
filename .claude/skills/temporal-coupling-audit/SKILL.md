---
name: temporal-coupling-audit
description: >-
  Detect hidden dependencies between modules by analyzing which files co-change in commits.
  Files that always change together are coupled — even if the architecture diagram shows them
  as separate. Use when someone asks "are our module boundaries holding?", "where are the
  hidden dependencies?", "why does changing X always break Y?", "check for architectural decay",
  "audit our layering", "find cross-boundary coupling", or as a follow-up to a hotspot-radar
  sweep. Produces a coupling map ranked by co-change strength, with expected vs. surprising
  coupling clearly labeled. Based on Adam Tornhill's temporal coupling method.
metadata:
  version: 1.0.0
type: Skill

---
# Temporal Coupling Audit

**The detective's insight:** two modules that always change together at the same time are
coupled — regardless of what the import graph, dependency diagram, or documentation says.
Temporal coupling (co-change) reveals the *real* architecture, not the *intended* one.

> "Temporal coupling is a way to reduce bias and see how your code changes instead of how
> you think it changes." — Tornhill

When the intended architecture and the temporal coupling diverge, that divergence is
**architectural decay** — and it grows silently until it becomes a crisis.

## When to run it

After a `hotspot-radar` sweep (to understand *why* the hotspots are hot), or any time a
change "shouldn't" have broken something else — that surprise coupling is exactly what this
audit surfaces. Also useful before a major refactor: understand the real coupling before
you try to cut the seams.

## The Audit (4 steps)

---

### Step 1 — Generate the co-change log

```bash
# Extract file pairs that co-changed in the same commits
git log --pretty=format:'[%H] %s' --name-only --after="YYYY-MM-DD" > evo.log
```

Parse the log to find, for each commit, which files changed together. Group by commit SHA.
Every pair (A, B) within the same commit is a co-change event.

**Shell approach (pair extraction):**
```bash
# For each commit, print all file pairs that co-changed
git log --name-only --pretty=format:'COMMIT' --after="YYYY-MM-DD" \
  | awk '/^COMMIT/{if(files) {n=split(files,a," "); for(i=1;i<=n;i++) for(j=i+1;j<=n;j++) print a[i]"|"a[j]}; files=""} !/^COMMIT/{files=files" "$0}' \
  | sort | uniq -c | sort -rn | head -50
```

Output: `<co-change-count>  <file_A>|<file_B>`

---

### Step 2 — Calculate coupling strength

For each pair (A, B):

```
coupling_degree = co_changes(A,B) / min(total_changes(A), total_changes(B))
```

A degree of 1.0 means every time the less-changed file changed, the other changed too.
Degrees above 0.30 (30%) are worth examining. Degrees above 0.50 in a *surprising* pair are
a strong signal of architectural decay.

**Coupling strength table:**
| Degree | Interpretation |
|---|---|
| 0.70–1.0 | Very tight coupling — almost always move together |
| 0.40–0.69 | Strong coupling — frequent co-change |
| 0.20–0.39 | Moderate coupling — common enough to investigate |
| < 0.20 | Weak — probably incidental |

---

### Step 3 — Classify: expected vs. surprising

This is the forensic judgment step. Not all coupling is a crime.

**Expected coupling (not a problem):**
- Model + its migration + its unit tests → co-change is by design
- A controller + its view template → expected in MVC
- An interface + its primary implementation → design pattern
- A shared utility + its tests → healthy

**Surprising coupling (investigate):**
- Auth module ↔ payment module (should be separate concerns)
- Database layer ↔ UI component (layer boundary violation)
- Module A ↔ Module B ↔ Module C (all three always change together → god object, shared state, or implicit protocol)
- Test A ↔ Test B (tests that always fail and fix together share hidden state)

**Decision heuristic:** if you'd have to explain why these two modules co-change to a new developer,
and the explanation is longer than one sentence, it's surprising coupling.

---

### Step 4 — Produce the coupling map

Report format:

```
TEMPORAL COUPLING AUDIT — <system> — <date window>
────────────────────────────────────────────────────
SURPRISING COUPLINGS (investigate)

  src/auth/session.js ↔ src/payment/checkout.js
  Degree: 0.58 (29 of 50 commits co-changed)
  Verdict: ★★★ HIGH — these should be independent; shared state suspected
  Suggested probe: grep for shared globals, event bus, or implicit auth-in-payment calls

  src/api/users.js ↔ src/ui/admin-panel.jsx
  Degree: 0.44 (22 of 50 commits)
  Verdict: ★★ MEDIUM — API and UI shouldn't be tightly coupled; check for direct imports

EXPECTED COUPLINGS (healthy — no action)

  src/models/user.js ↔ tests/models/user.test.js
  Degree: 0.82 — unit test pair, expected

ARCHITECTURAL DECAY SCORE: 2 surprising couplings found
  Recommended action: refactor auth/payment boundary before next feature addition
```

---

## Reading the map over time

A single coupling audit is a snapshot. The real power comes from running it periodically and
watching coupling *trends*:

- A new surprising coupling appears → a recent refactor introduced hidden dependency
- An existing surprising coupling grows stronger → architectural decay accelerating
- A coupling disappears → successful decoupling (validate with a re-audit 30 days later)

Track the count of surprising couplings per time period as a health metric. A rising count is
a lagging indicator of architectural decay.

## Notes

- **Aggregate boundaries for large repos.** Map individual files to modules/packages first
  (e.g., all `src/auth/*` → `auth-module`), then run the coupling analysis on module pairs.
  File-level coupling in a 500-file repo produces too many pairs to read.
- **Exclude auto-generated pairs.** If a code generator always touches file A when file B
  changes, that's mechanical coupling — not architectural.
- **Combine with hotspot-radar.** A hotspot that is also highly coupled to surprising partners
  is your highest-priority refactoring target — it's both painful to change and entangled.

## Versioning

Bump `metadata.version` on any change. Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write` after a bump.

## Changelog

- **1.0.0** — Initial release. Temporal coupling audit method from Adam Tornhill,
  *Your Code as a Crime Scene* (Pragmatic Bookshelf, 2015).