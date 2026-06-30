---
type: Document
title: Capturing Patterns
description: The fixed pattern shape, quality bar, and extract-from-proven capture protocol.
timestamp: 2026-06-28T00:00:00Z
---

# Capturing Patterns

How a proven implementation becomes a library pattern. Capture is **filling a
fixed shape from real code**, not free-writing — the shape is the contract that
lets a consumer trust the result without re-vetting it.

## The fixed pattern shape

Every pattern file is one `.md` carrying the same sections, in this order:

```markdown
# {Pattern Name}

## What It Does
[One paragraph: the purpose and the problem it solves. Concrete, not aspirational.]

## When to Use
- Use case 1
- Use case 2
- (the recognizable situations a consumer matches against)

## Code Pattern
[A COMPLETE, copy-paste-ready code block. Not a sketch — it compiles/runs as-is
once placeholders are filled. Inline comments mark the load-bearing steps
(auth check, RLS context, validation, error handling).]

## Customization Guide
1. Replace `{placeholder}` with your value (e.g. `{resource}`, `{table_name}`)
2. Update type definitions
3. Adjust business logic

## Security Checklist
- [ ] RLS context enforced (if database operations)
- [ ] Auth required (if protected)
- [ ] Input validated (Zod / schema)
- [ ] Error handling comprehensive

## Validation
[Exact commands that prove a correct application, e.g.
`lint && type-check`, integration tests for API, e2e for UI.]
```

A file missing the runnable Code Pattern, the Customization Guide's marked
placeholders, the Security Checklist, or the Validation commands is a **draft**,
not a pattern. Do not index a draft.

## Why each field exists

- **What It Does / When to Use** — discovery surface. These are what the index
  table and a consumer's "does this match my task?" scan read against.
- **Code Pattern** — the deliverable. Complete and copy-paste-ready so reuse is
  literally copy → customize, not re-derive. Comments call out the steps that
  must not be dropped.
- **Customization Guide** — makes the pattern a template. Placeholders are
  explicit (`{...}`) so nothing load-bearing is left ambiguous.
- **Security Checklist** — the trust gate. A pattern asserts its security
  properties (RLS, auth, validation, error handling) up front; the consumer
  inherits them by following the pattern.
- **Validation** — closes the loop. The commands that prove the applied pattern
  actually works in the consumer's codebase.

## Capture protocol (extract-from-proven)

1. **Find the trigger.** A shape is being implemented *repeatedly*. Frequency,
   not novelty, is the signal to extract — capture once so it is never
   re-derived.
2. **Locate the proven source.** Identify a real, production, working
   implementation of the shape. Patterns are mined from code that already passed
   lint, types, security, and tests in situ — never invented speculatively.
3. **Extract into the shape.** Generalize the real code: strip
   instance-specifics, mark them as `{placeholders}`, write the Customization
   Guide around them. Keep the load-bearing structure intact.
4. **Fill the trust fields.** Write the Security Checklist (assert what the
   pattern enforces) and the Validation commands (prove a correct application).
5. **Validate with the owner.** An architect role confirms the extraction before
   admission (see ownership, below).
6. **Index it.** Add the use-case → file row to the category README in the same
   commit. Un-indexed = invisible = dead.

## Quality bar

Before admission, a pattern should clear:

- [ ] Clear, concrete use-case description
- [ ] Complete, working code example (not a sketch)
- [ ] Customization instructions with explicit placeholders
- [ ] Security validation checklist
- [ ] Success/validation commands
- [ ] Security properties enforced where applicable (RLS, auth, input
      validation, comprehensive error handling, strict types)

## Ownership: who captures

- **Architect role** (the pattern owner) discovers gaps, extracts patterns from
  proven implementations, validates, and admits them to the index.
- **Execution agents** consume patterns and **report missing ones** — they do
  not silently admit their own. The gap report is how the library grows: repeated
  requests for a missing shape are the extraction signal.

This split is what keeps the library *trustworthy* — every entry passed one
owner's bar, so a consumer never has to second-guess a pattern's pedigree.
