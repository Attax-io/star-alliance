---
type: Document
title: Order templates — the order shape per subordinate type
timestamp: 2026-06-28T00:00:00Z
---

# Order templates — right-sized by who executes

The same skeleton (Order · Intent · Context · Constraints · Output contract), tuned to the
subordinate (axiom 7). Pick the template, fill it, then run the seven axioms over the draft.

## One-shot worker (a Claude subagent given a text-only task — no follow-up, no shared memory)

Put the **entire** spec in the order; a one-shot worker cannot ask back mid-task. Be
maximally explicit about the output contract. In execution this is a Claude subagent spawned via
the Task tool with the whole spec in its prompt — cheaper model (Haiku/Sonnet) for bulk drafting.

> **Order:** Extract every function signature from the attached file into a markdown table.
> **Intent:** Build an API index; completeness matters more than prose.
> **Context:** (the file's contents are pasted into the prompt)
> **Constraints:** Table only, no prose. Skip private helpers (leading underscore). Do not
> invent signatures not in the file.
> **Output contract:** A markdown table with columns `name | params | returns | line`. One
> row per public function. End with a count line `Total: N`.

Spawn it as a Claude subagent via the Task tool (`model=haiku` or `sonnet`), putting the whole
order and the file contents in the prompt.

## Subagent (an isolated Claude agent — has tools, but NO shared memory of this chat)

(The one-shot worker above is a subagent too — the difference is that this register hands it
tools and expects it to act; the worker above only returns text.)

Include every fact, path, and prior decision it needs; state exactly which files it may
touch and the exact return shape. It is one-shot and stateless — anything you assume it
"already knows" it does not.

> **Order:** Add a `created_at` timestamp column to the `notes` feature, end to end.
> **Intent:** Notes must be sortable by age; ship it working, not half-wired.
> **Context:** Schema in `db/migrations/`, the read path is `app/notes/list.ts`, the type is
> `app/notes/types.ts`. We use Supabase; RLS is already on `notes`. Prior decision: timestamps
> are `timestamptz default now()`.
> **Constraints:** Touch only those three areas. No new dependencies. Additive migration only.
> **Output contract:** Reply with the files changed, the migration SQL, and confirmation that
> `npm run typecheck` passes. Do not commit.

## Member (a peer with their own craft)

Command by **intent**, not micro-steps (mission command). Give the end-state, the why, and
the bounds; trust the member to choose the method. Wide latitude inside clear constraints.

> **Order:** Make the dashboard load feel instant.
> **Intent:** Users think it's slow; perceived speed is the goal, not a specific metric.
> **Context:** Recent complaints centre on the first paint after login.
> **Constraints:** No backend schema changes this pass; keep the visual design unchanged.
> **Output contract:** A short plan of what you'll do + the before/after you'll measure.

## Human — the Guild Master (a non-programmer)

Bottom line first, **plain English**, no jargon. Where the call is theirs, give 2-3 options
with a recommendation — not a wall of detail.

> **Order:** I can ship the fix today or do it properly over two days — your call.
> **Intent:** The quick fix hides the symptom; the proper one removes the cause.
> **Context:** The slow page is slow because we ask the database the same thing many times.
> **Constraints:** The quick fix is safe to undo; the proper one changes more.
> **Output contract:** Options — (A) quick patch today, low risk; (B) proper fix in two days,
> recommended. Which do you want?

## The fill-then-cut rhythm

Fill every section first so nothing is missing (axiom 4), then **cut** every word that is
not load-bearing (axioms 1-2). A finished order reads shorter than the draft and leaves no
question open.
