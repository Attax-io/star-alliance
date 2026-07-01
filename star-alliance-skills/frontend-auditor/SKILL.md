---
name: frontend-auditor
description: "Diffs the Lex Council Next.js codebase (pages, mutations, hooks, stores) against FRONTEND-INVENTORY.json using fixed globs and greps from the project root, then returns a [NEW]/[REMOVED] delta per category. Use after refactors or whenever FRONTEND.md feels out of sync with the live app. Triggers: 'audit the frontend', 'is FRONTEND.md current', 'frontend drift', 'pages/mutations/hooks drift'."
metadata:
  version: 1.0.0
type: Skill
---

# Frontend Auditor

**Runtime:** this skill invokes the Lex Council Supabase MCP connector, so it must be run by a Claude-native runtime that has that connector mounted — not a Hermes doer.

The frontend-auditor skill reconciles the live Next.js codebase under `lex_council/apps/web/` against the canonical inventory in `lex_council/docs/architecture/frontend/FRONTEND-INVENTORY.json`. It runs a fixed set of globs and greps from the project root, builds sorted lists per category, diffs them against the baseline JSON, and returns the delta.

## Categories

- **Pages** — glob `lex_council/apps/web/app/**/page.tsx`. Normalize paths relative to `lex_council/`.
- **Mutations** — glob `lex_council/apps/web/lib/mutations/*.ts`. Relative to `lex_council/`.
- **Hooks** — grep `^export function use` across `lex_council/apps/web/` (`*.ts`, `*.tsx`). Extract hook names. Dedupe, sort.
- **Stores** — grep `^export\s+const\s+\w+\s*=\s*create[<(]` across `lex_council/apps/web/` (`*.ts`, `*.tsx`) filtered to files whose path contains `store` (case-insensitive). Extract exported names. Dedupe, sort.

## Output

Return `[NEW]` / `[REMOVED]` items per category. No raw dumps — diffs only. Keep the response under 300 words. Do not edit any files — return-only.