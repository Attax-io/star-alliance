---
name: hotspot-radar
description: >-
  Mine a git repository's change history to produce a ranked hotspot list — files ranked by
  the combined signal of change frequency and complexity. Use when someone says "find the worst
  parts of this codebase", "what should we refactor first", "which files have the most churn",
  "prioritize our refactoring backlog", "find the maintenance bottlenecks", or before any
  refactoring sprint that needs an objective starting point. Outputs a scored table of hotspots
  with complexity and frequency evidence. Based on Adam Tornhill's forensic code analysis method.
metadata:
  version: 1.0.0
type: Skill

---
# Hotspot Radar

A fast, git-native technique to objectively rank files by maintenance risk: **change frequency
× complexity**. No special tools required beyond git and a terminal.

The radar answers one question: *where should we spend our limited refactoring budget?* Not
where the architecture diagram says we should, not where the senior developer's intuition says —
where the *data* says.

## When to run it

Before any refactoring sprint, after receiving a "where are the worst parts?" question, or as the
*evidence-gathering phase* of a `code-crime-scene` investigation. This skill is the data-collection
step; `code-crime-scene` is the interpretation step.

## The Radar Sweep (5 steps)

---

### Step 1 — Extract the evolution log

```bash
# Bounded window (recommended: last 6–12 months)
git log --numstat --pretty=format:'[%H]' --after="YYYY-MM-DD" > evo.log

# Or full history
git log --numstat --pretty=format:'[%H]' > evo.log
```

The `--numstat` flag adds lines-added / lines-deleted per file per commit. The
`--pretty=format:'[%H]'` wraps each commit SHA in brackets — this is the format Code Maat
and similar parsers expect. If using a raw parser, adjust accordingly.

**Tip:** for very large repos, bound to 1 year maximum. Older history reflects past
architectural decisions, not current pain.

---

### Step 2 — Count change frequency

Parse the log and count how many commits touched each file.

**Shell one-liner:**
```bash
git log --name-only --pretty=format: --after="YYYY-MM-DD" \
  | grep -v '^$' \
  | sort \
  | uniq -c \
  | sort -rn \
  | head -40
```

This produces: `<commit_count>  <file_path>` sorted descending.

**Filter out false positives before ranking:**
```bash
# Exclude mechanical changes
grep -v -E "package-lock\.json|yarn\.lock|\.min\.(js|css)|generated|migrations/[0-9]|CHANGELOG|VERSION" \
  freq.txt > freq_filtered.txt
```

---

### Step 3 — Measure complexity

For each high-frequency file, measure complexity. Two reliable proxies:

**A) Lines of code (LOC):** `wc -l <file>` — fast, language-agnostic. A 2000-line file is
almost always more complex than a 100-line file, regardless of language.

**B) Indentation depth (better):** average or max indentation is a reliable proxy for cyclomatic
complexity. Deep nesting = many conditional branches = complexity.

```bash
# Average indentation depth for a file (tab or 2-space indented)
awk '{match($0, /^[ \t]*/); print RLENGTH/2}' <file> | awk '{s+=$1; c++} END {print s/c}'
```

For a quick relative ranking, LOC is sufficient. Use indentation depth when LOC produces
surprising results (e.g., a 1000-line file that's all one flat list vs. a 300-line file with 6
levels of nesting).

---

### Step 4 — Score and rank

Combine the two dimensions into a hotspot score:

```
hotspot_score = change_frequency × log(complexity)
```

Using `log(complexity)` prevents a 10,000-line file from drowning out all others. The
logarithm scales complexity so a file 10× as long scores roughly 2× higher, not 10×.

Alternatively: simply sort by frequency first, then manually note complexity for the top 20 —
the frequency ranking is usually the dominant signal.

**Produce a table:**
| Rank | File | Change Freq | LOC | Score | Priority |
|---|---|---|---|---|---|
| 1 | src/auth/session.js | 47 | 812 | 313 | ★★★ |
| 2 | ... | ... | ... | ... | ... |

---

### Step 5 — Distinguish hotspots from false positives

Before handing the list to anyone, check each top-10 entry:

| Signal | Likely false positive? | Action |
|---|---|---|
| Auto-generated or minified file | Yes | Remove from list |
| Sequential migration files (001, 002...) | Usually yes | Remove |
| Configuration file (env, settings) | Maybe | Check if it's complex or just frequently touched for config value changes |
| Single-purpose utility (e.g., a constants file) | Maybe | Check if it's actually read by many other modules |
| Legitimate feature module | No — this is your hotspot | Keep and investigate |

A hotspot that survives the false-positive filter is a real suspect.

---

## Using the output

- **Top 3 hotspots** → candidates for immediate refactoring attention
- **Top 10** → input to a `temporal-coupling-audit` to find hidden coupling
- **Trend over time** → run the radar monthly; a rising file is accelerating into a hotspot

Hand the scored table to the `code-crime-scene` skill for interpretation, or directly to the
Developer/Architect as a prioritized refactoring backlog.

## Notes

- No special tools needed — git + shell is sufficient for any repo.
- Code Maat (github.com/adamtornhill/code-maat) automates many of these steps if available.
- The radar is **language-agnostic**: works equally on JavaScript, Python, Java, Go, SQL, etc.
- Complexity metrics from static analyzers (SonarQube, ESLint complexity rules) can substitute
  for LOC/indentation when available — they're more precise but not necessary for the ranking.

## Versioning

Bump `metadata.version` on any change. Regenerate `VERSIONS.md` with
`python3 skillsmith/scripts/skill_registry.py write` after a bump.

## Changelog

- **1.0.0** — Initial release. Git-native hotspot scoring technique from Adam Tornhill,
  *Your Code as a Crime Scene* (Pragmatic Bookshelf, 2015).