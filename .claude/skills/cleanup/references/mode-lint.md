---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Mode: lint — full recipe

Run ESLint + TypeScript health sweep; auto-fix safe rules; surface architectural violations
as campaign candidates. Script: `scripts/lint_cleanup.py`.

**Scoped vs full-project lint.** The project enforces `--max-warnings 0`. A full project-wide
lint run often surfaces pre-existing warnings in files the current campaign never touched. This
mode supports BOTH: (a) full-project sweep (to build a debt baseline), and (b) scoped sweep
(to prove a campaign's changes are clean). See Step L3 for scoping options.

**No preview server required.** This mode does not need Claude to open a browser session.
All verification is tsc + ESLint only.

#### Step L0 — Pre-flight

```bash
# Confirm we're in lex_council/
ls lex_council/package.json   # must exist
# Check that npm run lint exists
grep '"lint"' lex_council/package.json
```

If not in the right directory or lint script missing, surface and abort.

#### Step L1 — Detect

```bash
python3 ~/.claude/skills/cleanup/scripts/lint_cleanup.py detect
```

The script runs `npx eslint --format json --ext .ts,.tsx apps/web packages` from `lex_council/`,
parses the JSON output, dedupes by `(file, rule)`, and writes `/tmp/lint_issues.json`.

Show the user: total unique issues (N errors, M warnings), top 5 rules by occurrence.
Ask whether to proceed with classification.

**Turbo cache trap.** Stale Turbo cache causes lint to report errors in unmodified files. If
unexpected errors appear in files clearly not related to recent work, run:

```bash
cd lex_council && npx turbo run check-types --force --filter=web
```

before investigating — the force flag bypasses stale cache.

#### Step L2 — Classify

```bash
python3 ~/.claude/skills/cleanup/scripts/lint_cleanup.py classify
```

Tier mapping:

| Tier | Signal | Action |
|---|---|---|
| **auto-fixable** | ESLint `fixable: true` in JSON output, or rule in safe-fixable list (prefer-const, no-var, import/order, etc.) | Run `eslint --fix`, then tsc |
| **architectural** | `react-hooks/exhaustive-deps`, `react-hooks/rules-of-hooks`, `import/no-cycle`, `no-unused-expressions`, `no-restricted-imports`, syntax/parse errors | Surface as campaign candidate |
| **wip-noise** | `no-unused-vars` / `@typescript-eslint/no-unused-vars` in files not touched this session | Suppress — tsc handles this better |
| **unknown** | No match | Surface with raw error text |

**`no-unused-expressions` is always architectural.** The most common trigger is a ternary used
as a statement (`cond ? a.foo() : a.bar()`), which fails `no-unused-expressions`. The fix is
always `if/else` — never `eslint-disable`. Auto-fix is blocked for this rule.

#### Step L3 — Scoping (optional)

For proving a campaign's changes are clean independent of pre-existing project-wide warnings:

```bash
# Get files touched in the current campaign/session
git status --short | awk '$1 ~ /^M/ || $1 == "M" {print $2}' > /tmp/touched.txt

# Run eslint scoped to those files only
cd apps/web
npx eslint --max-warnings 0 $(cat /tmp/touched.txt | grep "^apps/web/" | sed 's|^apps/web/||')
echo "EXIT=$?"
```

`EXIT=0` proves the campaign-touched surface is clean. Report both the full-project result
(with provenance note for pre-existing failures) AND the scoped result.

#### Step L4 — Apply

```bash
python3 ~/.claude/skills/cleanup/scripts/lint_cleanup.py apply
```

The script runs `eslint --fix` on files with auto-fixable issues, then runs tsc to verify.
If tsc fails after --fix, surface the failures — do NOT mark the phase complete until tsc passes.

**Safe-fixable rules**: prefer-const, no-var, import/order, import/no-duplicates,
@typescript-eslint/no-extra-semi, react/jsx-boolean-value, react/self-closing-comp, eol-last,
no-trailing-spaces. Full list in `scripts/lint_cleanup.py:SAFE_FIXABLE_RULES`.

**Auto-fix batch limit**: apply at most 50 files per run. Larger batches risk a single
unfixable file blocking the whole batch. Run verify between batches if > 50 files.

#### Step L5 — Verify

```bash
python3 ~/.claude/skills/cleanup/scripts/lint_cleanup.py verify
```

Re-runs full ESLint, reports delta vs the pre-fix baseline. Then:

```bash
cd lex_council && npx turbo run check-types --force --filter=web
```

Expected: auto-fixable count drops to 0. tsc passes. Architectural count unchanged
(those require campaigns, not auto-fix).

#### Step L6 — Surface architectural violations

```bash
python3 ~/.claude/skills/cleanup/scripts/lint_cleanup.py surface
```

Print the triage list. For each architectural violation cluster (same rule across N files),
suggest the conquering-campaign trigger (e.g., "sweep no-unused-expressions ternary violations
across 12 files").

**Off-token hex grep bonus scan.** ESLint does not catch raw hex color literals in CSSProperties.
Run after the standard lint sweep:

```bash
grep -rn '#[0-9a-fA-F]\{3,6\}' \
  lex_council/apps/web/components \
  lex_council/apps/web/app \
  --include="*.tsx" --include="*.ts" | grep -v "//.*#" | wc -l
```

A count > 10 is a flag for a token-sweep campaign. Surface to the user as an advisory.

#### Step L7 — Vault log

Delegate to **vault-log-compliance** *only if code changed* (auto-fix was applied). For
triage-only runs, no vault log needed.

The entry should document: files fixed, rules resolved, tsc result, architectural violations
surfaced as campaign candidates, and the off-token hex count if > 0.

**Key traps for lint mode:**

- **Pre-existing parse errors block the whole app typecheck.** A single unterminated string
  literal stops tsc from analyzing any other file. Run `tsc --noEmit` first to confirm the
  baseline is clean before attributing new errors to the current session's changes.
- **`'use client'` + `generateMetadata` in same file** is a hard Next.js build error (not a
  lint or tsc error — only surfaces at `next build`). Classify as `architectural`.
- **Module-level `const` style objects** have dead-code that ESLint's `no-unused-vars` does not
  catch because the object itself is exported. This requires a manual `grep` for usage or a
  `knip`/`ts-prune` run — out of scope for auto-fix, surface as advisory.
- **`useTranslations` cleanup** requires removing BOTH the import AND the `const t = ...` line.
  ESLint `--fix` removes unused-import but leaves the `const` declaration, causing a follow-up
  `no-unused-vars` error on the next run. Fix both in one pass.
