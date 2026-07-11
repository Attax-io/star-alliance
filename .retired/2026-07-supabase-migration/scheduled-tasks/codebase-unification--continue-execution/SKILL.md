---
name: codebase-unification--continue-execution
description: Unify the code base.
---

Read docs/INDEX.md first.

**Codebase Unification — Core Rules & Status**

**Objective:** Reduce code, eliminate duplication, improve performance. Zero changes to functionality, UI, or design.

**Work — Priority Order**

1. **Token Sweep** — Continue replacing inline `borderRadius: 6/8` and `fontSize: 12/13/14` with `@repo/md` tokens. Skip 9/10/11/15/16px — no token match.
2. **ModalShell** — Migrate complex remaining modals only if `customHeader` prop handles non-standard headers without visual changes.
3. **Dead imports** — Remove unused `createClient` imports in files already migrated to `useReferenceDataStore`.
4. **New files** — Any new modal → `ModalShell`. Any new page → `usePaginatedQuery` + query-configs. Any new store → `createListStore`.

---

**Non-Negotiable Rules**

- Run `npx tsc --noEmit` after every batch — must pass with zero errors
- Never change functionality, UI, or design
- Always read a file before editing it
- Use `replace_all: true` for token replacements
- Don't touch `docs/archived/` without explicit permission