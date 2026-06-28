---
type: Reference
title: Severity and Scope
skill: code-review-craft
---

# Severity, scope, and finding volume

Two failure modes kill a review: **missing the one bug that mattered**, and **burying
it under noise**. Severity tagging and scope discipline are the defenses.

## The severity scale

Tag every finding so the author can triage at a glance. Order the report by severity —
Critical and High first, always.

- **Critical** — data loss/corruption, a security hole (injection, auth bypass,
  cross-tenant read, leaked secret), or a crash on a common path. Must be fixed before
  merge. Prefer to reproduce it.
- **High** — wrong result in a real, reachable case; an unhandled error that escapes; a
  contract break that silently misleads callers. Should be fixed before merge.
- **Medium** — works today but fragile, duplicated, or hard to maintain; an edge case
  unlikely but possible. Fix soon; not a merge blocker on its own.
- **Low / Nit** — minor and optional; a small reuse win, a clearer name *that affects
  meaning*. Cosmetic-only nits that do not change behavior should usually be **dropped**,
  not filed.

When unsure between two levels, pick the higher and say why in one clause — under-tagging
a real data-loss bug is the costly error.

## Scope boundaries

Review **what changed**, plus exactly the surrounding code the change depends on or
breaks. Everything else is out of scope.

- **Pre-existing debt outside the diff** — note it **once**, in a single "out of scope"
  line, and move on. Do not rewrite the file, do not file ten findings against legacy
  code the author did not touch.
- **The change's dependencies** — in scope. If the diff calls a function whose contract
  it now violates, that function is fair game even if unchanged.
- **Adjacent files the change breaks** — in scope. A renamed export breaks its importers;
  review them.
- **Speculative future needs** — out of scope. Review the code in front of you, not the
  feature it might grow into.

> Example out-of-scope line: "Out of scope: this module predates the lint config and has
> unrelated formatting debt — not reviewed."

## Calibrating finding volume to effort

Match the depth of the review to what was asked. This mirrors the `engineering:code-review`
effort levels.

- **"Is this safe?" / quick look (low–medium effort)** — return only the **few
  high-confidence** findings, Critical and High. Silence on the rest is correct: if there
  is nothing real to say, say "no blocking findings" and stop. Do not manufacture nits to
  look thorough.
- **"Review this PR" / standard (medium effort)** — the high-confidence findings plus
  Medium items worth fixing. Still scoped, still no cosmetic noise.
- **"Audit this thoroughly" / high effort** — broader coverage; you may surface
  **uncertain** findings, each clearly flagged as uncertain and tagged "needs a run to
  confirm" (see `grounding-findings.md`).

The test of a good review is not how many findings it returns but whether the author can
**immediately find the ones that matter**. Five findings, two Critical at the top, beats
thirty with the data-loss bug at position 19. A review is finished when its findings are
true, located, severity-ordered, scoped to the change, and free of noise.
