---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Environment Hazards

Quick index of runtime and tooling hazards; each entry names the failure mode # and cure location.

---

**PostToolUse hooks** rewrite/strip mid-flight — prefer `Write` over chained Edits when the intermediate is lint-dirty (#28); re-Read after >30s waits (#41).

**JSX structural pivot** via chained Edits → single `Write` (#51).

**Mass-edit/codemod footguns** — multiline-aware, `\b`≠decimal-safe, last-import insertion, `\uXXXX` double-escape, exclude canon files (#73, references/fe-i18n-playbook.md).

**Runtime caches that don't HMR** — newly-added JSON keys + SWC stale parses → **restart the dev server first when the runtime contradicts the file on disk** (#48).

**SSR/client hydration mismatch** with module-level state (#20, references/fe-i18n-playbook.md).

**Pre-commit hooks that auto-commit** (husky/lefthook) — probe before committing, let the chain finish, document it (#63).

**Docs housekeeper daemon races the Edit tool** on `lex_council/docs/*` (bumps frontmatter between Read and Edit → endless "modified since read") — edit via an atomic read-replace-write (one shell call), never retry Edit against a daemon-watched path (#87).

**Git under a concurrent actor** — when another actor holds uncommitted changes in the MAIN working copy, NEVER `git checkout -b` (it moves HEAD in their tree and can hijack/co-mingle their commits), branch via `git worktree add .claude/worktrees/<name> -b <branch>` (clean tree from HEAD, only your files), commit scoped, push, PR (#95). A fresh worktree has no `node_modules` → symlink them from the primary checkout to run `tsc`/`lint`/preview; the symlink resolves `@repo/*` to primary packages → confirm `git status packages/` is clean there first. Campaigns A+B+E all shipped this way.

**`gh` may be absent** — don't fail the handoff; push the branch + hand the user the `…/pull/new/<branch>` URL (#99).
