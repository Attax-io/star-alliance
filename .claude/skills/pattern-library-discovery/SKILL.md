---
name: pattern-library-discovery
description: "Build and query a reusable code-pattern library so agents reuse a proven, security-validated pattern instead of reinventing one. Two crafts: CAPTURE (extract a battle-tested implementation into a fixed-shape .md — What It Does, When to Use, Code Pattern, Customization Guide, Security Checklist, Validation — filed under api/ci/config/database/security/testing/ui and indexed) and DISCOVERY (reuse-before-reinvent: library index, then category folder, then live-codebase grep, then apply/extract/escalate). Triggers: 'find a pattern for X', 'is there a reusable pattern', 'capture this as a pattern', 'search the pattern library', 'reuse before reinvent', 'how should I build X'. Differs from spec-driven-development (per-feature spec, not cross-feature reuse), safe-agentic-orchestration (the governing loop, not the lookup step), and arsenal-forge (mints model/tool weapons, not code patterns)."
metadata:
  version: 1.0.0
type: Skill
---

# Pattern Library Discovery

A reusable code-pattern library plus the discipline of querying it **before**
writing new code. The craft has two halves that feed each other: **capture** —
extracting a proven implementation into a copy-paste-ready, security-validated
pattern with a fixed shape; and **discovery** — searching that library (and the
live codebase) first, so an agent reuses a battle-tested solution instead of
reinventing one. Distilled from the Safe Agentic Workflow `patterns_library/`
(api · ci · config · database · security · testing · ui), its `pattern-discovery`
skill, and the `/search-pattern` command.

## What it is

- A **curated library of patterns**, each a self-contained `.md` with a fixed
  shape (What It Does · When to Use · Code Pattern · Customization Guide ·
  Security Checklist · Validation), filed under a small fixed taxonomy.
- A **discovery protocol**: library index → category folder → live codebase grep
  → reuse, extract, or escalate. Reuse-before-reinvent is the default, enforced
  at the start of any feature/route/component/migration/test.
- A **capture protocol** under ownership control: only an architect role extracts
  and admits new patterns; execution agents consume and report gaps.

## What it is not

- **Not spec-driven-development.** SDD turns a single requirement into a spec →
  plan → tasks for *this* feature. This skill is about *reuse across* features —
  the persistent library of proven shapes a spec's tasks draw from. SDD asks
  "what should we build?"; this asks "have we already solved this shape?"
- **Not safe-agentic-orchestration.** Orchestration governs the loop, roles, and
  gates that *run* the work. This is one craft those roles invoke — the lookup
  step before implementation, not the governance around it.
- **Not arsenal-forge.** Arsenal-forge mints model/tool *weapons* for a member.
  This curates *code patterns* (reusable implementations), not arsenal entries —
  a different artifact, owner, and store.
- Not a snippet dump or a generic codebase search. A pattern is admitted only
  when proven, shaped, security-checked, and indexed; a search returns matches,
  a pattern returns a vetted solution.

## Principles

### 1. Reuse before reinvent — always check the library first
Before writing a new API route, component, migration, or test, search the
library. The protocol is a fixed sequence: **index → category folder → codebase
grep → apply / extract / escalate.** Skipping the lookup is the failure the whole
craft exists to prevent. Example: tasked to "add a protected user-data endpoint,"
you open `api/user-context-api.md` and customize it rather than hand-rolling auth
+ RLS from scratch — the vetted version already enforces both.

### 2. A pattern has a fixed shape — capture is filling that shape, not free-writing
Every pattern carries the same sections so it is scannable and trustworthy:
**What It Does · When to Use · Code Pattern (complete, copy-paste-ready) ·
Customization Guide (placeholders marked, e.g. `{resource}`, `{table_name}`) ·
Security Checklist · Validation commands.** A "pattern" missing the checklist or
the runnable example is a draft, not a pattern. The shape *is* the contract: a
consumer trusts it because every field is present. See
[references/capturing-patterns.md](references/capturing-patterns.md).

### 3. Extract only from the proven — patterns are battle-tested, not aspirational
A pattern is mined from a real, working, production implementation — never
invented speculatively. Its value is precisely that it already passed lint,
types, security, and tests in situ. The trigger to capture is *frequency*: when a
shape gets implemented repeatedly, an architect extracts it once so it is never
re-derived. Aspirational "here's how we *should* do X" belongs in a spec, not the
library.

### 4. Organize by a small, stable taxonomy
Patterns file under a flat, fixed category set — **api · ci · config · database ·
security · testing · ui** — each a folder with a README index. A small taxonomy
keeps discovery fast (you know which folder before you search) and resists the
sprawl that makes a library un-queryable. Add a category only when a genuinely
new domain of patterns emerges, not per-pattern. See
[references/category-taxonomy.md](references/category-taxonomy.md).

### 5. The index is the front door — keep it authoritative
Discovery starts at the library README: a table mapping *use case → pattern file*
("Create authenticated API endpoint → `api/user-context-api.md`"). Every admitted
pattern is added to that index in the same commit; an un-indexed pattern is
invisible and therefore dead. The index, not folder-walking, is how a consumer
finds the right pattern fast.

### 6. Search the live codebase as the second lookup
If the index has no match, grep the real code before writing new — a proven
implementation may already exist un-extracted. Search with the right tool: filter
by file type for speed, use content mode + context lines to understand usage,
group findings by usage / context / variation / outlier. A codebase hit is both a
reuse opportunity *and* a candidate to extract into the library. See
[references/search-and-retrieval.md](references/search-and-retrieval.md).

### 7. Capture is owned; consumption is open — and gaps flow back
A clear ownership split keeps the library trustworthy: an **architect role**
discovers, extracts, validates, and admits patterns; **execution agents** consume
them and **report missing patterns** rather than silently admitting their own.
The gap report is the library's growth engine — repeated requests for a missing
shape are the signal to extract the next pattern. Reuse → report gap → extract →
index → reuse is the closing loop.

## References

- [references/capturing-patterns.md](references/capturing-patterns.md) — the
  fixed pattern shape (every field, with examples), quality bar, and the
  extract-from-proven capture protocol.
- [references/category-taxonomy.md](references/category-taxonomy.md) — the
  seven-category taxonomy, what files under each, the README-index contract, and
  when to add a category.
- [references/search-and-retrieval.md](references/search-and-retrieval.md) — the
  index → category → codebase discovery sequence, search-tool craft (type
  filters, context, multiline, grouping), and the apply / extract / escalate
  decision.
