---
type: Document
title: Search and Retrieval
description: The index-then-category-then-codebase discovery sequence, search-tool craft, and the apply/extract/escalate decision.
timestamp: 2026-06-28T00:00:00Z
---

# Search and Retrieval

Discovery is the half of the craft that runs *before* you write code. Its goal:
land on a vetted pattern (or a proven codebase implementation) instead of
re-deriving a solution. The discipline is a fixed lookup sequence plus the
search-tool craft to execute the codebase step well.

## The discovery sequence

Run this **before** any new API route, component, migration, or test:

```
1. Library index   →  open the master README; match use-case → pattern file.
2. Category folder  →  if unsure, browse the right folder (api/ ui/ database/ …).
3. Codebase grep    →  no library match? search the live code for a proven
                       implementation of the same shape.
4. Decide           →  apply / extract / escalate (below).
```

The sequence is ordered cheapest-and-most-trusted first: the index is one read
and returns a vetted answer; the codebase grep is the fallback when the library
is silent.

## Step 1–2: querying the library

- Start at the README's **use-case → pattern** table and the "if you need to…"
  matrix. Match your task's shape, not its surface wording ("protected endpoint
  reading user-owned rows" → user-context API).
- If the index match is ambiguous, open the category folder and skim the
  `## What It Does` / `## When to Use` headers — they exist precisely for this
  scan.

## Step 3: searching the live codebase

When the library has no match, a proven implementation may still exist
un-extracted. Grep for it before writing new. Search-tool craft:

- **Filter by file type** for speed on large trees: search `type: ts` /
  `tsx` / `md` rather than everything. Use `files_with_matches` to see *which*
  files, `content` to see the matching lines.
- **Add context** to understand usage, not just locate it: `-C 3` (or `-B`/`-A`)
  with content mode shows the surrounding call site, imports, and signature.
- **Multiline** for cross-line shapes (a function body, an import-to-return
  span): enable multiline matching with a `[\s\S]*?` style pattern.
- **Use precise regex** to find structure, not noise:
  `\bfunction\s+(\w+)` (definitions), `import.*from\s+['"](.*)['"]` (sources),
  `export.*(GET|POST|PUT|DELETE)` (routes).

### Group the findings

Don't dump matches — categorize them so the result is actionable:

- **Usage patterns** — how the shape is used.
- **Contexts** — where it appears.
- **Variations** — different takes on the same shape.
- **Outliers** — unusual / suspect usage.

This grouping turns a raw grep into either a reuse target or a clean extraction
candidate.

### Common codebase queries

| Goal                         | Search                                    |
| ---------------------------- | ----------------------------------------- |
| Find the security helper     | `withUserContext\|withAdminContext`       |
| Find direct DB access to fix | `prisma\.(user\|payment)` (ts)            |
| Find all endpoints           | `export.*(GET\|POST\|PUT\|DELETE)` (ts)   |
| Find env-var usage           | `process\.env\.`                          |
| Find tech-debt markers       | `TODO:\|FIXME:\|HACK:`                     |
| Pre-refactor: all usage      | `oldFunctionName`  (build the change list)|

## Step 4: apply / extract / escalate

The lookup ends in one of three moves:

- **Apply** — a library pattern matches. Read it, copy the Code Pattern, follow
  the Customization Guide (fill every `{placeholder}`), run the Validation
  commands. Reuse, done.
- **Extract** — no library pattern, but the codebase has a proven implementation
  *and* the shape recurs. Flag it to the architect role as an extraction
  candidate (see [capturing-patterns.md](capturing-patterns.md)); reuse the
  existing code now.
- **Escalate / report gap** — neither library nor codebase has it. Implement
  following existing conventions, and **report the missing pattern** to the
  owner. Repeated gap reports are the signal to capture the next pattern — the
  loop that grows the library. Execution agents report gaps; they do not silently
  admit their own patterns.

The cardinal rule across all four steps: **reuse before reinvent.** Writing new
code without running this sequence is the single failure the craft exists to
prevent.
