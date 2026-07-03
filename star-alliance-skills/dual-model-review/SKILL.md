---
name: dual-model-review
description: "The two-Claude review flow — the guild's quality gate. A member drafts a piece of work (as a Sonnet subagent, say), then a SECOND, independent Claude subagent reviews it before the work is reported done. The reviewer is a DIFFERENT Claude — a different model (an Opus subagent reviewing a Sonnet draft) or at minimum a fresh instance with no memory of the drafting — so it brings genuinely independent eyes. One drafter + one or two independent Claude reviewers, fired in PARALLEL via the Task/Agent tool; each must PASS before the work ships. Triggers: 'dual review', 'two reviewers', 'have another model check this', 'review in parallel', 'draft then review', 'second pair of eyes', or any time a member is about to declare production work done. Pairs with weapon-utility (spawn-a-subagent doctrine), decompose-and-swarm (when many slices each need dual review), and safe-agentic-orchestration (the independence gate — a verifier must never be the implementer)."
metadata:
  version: 1.0.0
type: Skill
---

# Dual-Model Review

The dual-review flow is the guild's quality gate. A member drafts the work
(the drafting Claude — often a Sonnet member subagent), then a **second,
independent Claude subagent** reviews it before the member reports the work
done. The reviewer is a **different Claude** — a different model (an Opus
subagent reviewing a Sonnet draft), or at minimum a fresh instance that never
saw the drafting turn — so it brings genuinely independent eyes. For
higher-stakes work, fire **two** independent Claude reviewers in **parallel**.
Both must independently PASS before the work ships.

This skill is the **runtime contract** that makes every member agree on what
"done" means: nothing production-grade ships unreviewed by a second Claude.

## What it is / is not

**It is:**
- The standard review shape used by every member for production work:
  **1 drafter + 1–2 independent Claude reviewers**, the reviewers running in
  parallel.
- A doctrine of independent verdict, not a fixed script — the reviewer prompts
  are tuned per member (the Designer reviews visual output; the Merchant
  reviews numerical analysis), but the **shape is universal**.

**It is not:**
- A replacement for the drafter's own judgment. The drafter still plans,
  integrates, and reports. The reviewers are the independent second pair of
  eyes — the member remains responsible for the final decision.
- A licence to let the drafter grade its own work. The reviewer must be a
  DIFFERENT Claude subagent — a different model, or a fresh instance with no
  memory of the draft. A drafter reviewing itself is theatre. This is the same
  independence gate `safe-agentic-orchestration` enforces.
- An always-on review. For trivial work (rename one symbol, copy a file),
  dual review is overkill. See §When to dual-review.

---

## The three roles

The dual-review flow holds **three roles at once**. Knowing which Claude plays
which role — and never confusing them — is the load-bearing rule.

```
                       ┌──────────────────────────┐
                       │  The member (integrator) │
                       │  plans + integrates      │
                       └──────────┬───────────────┘
                                  │ spawns
              ┌───────────────────┴─────────────────────┐
              │                                         │
              ▼                                         ▼
   ┌────────────────────┐                  ┌────────────────────────┐
   │  Drafter           │                  │  Reviewers             │
   │  a Claude subagent │                  │  independent Claude    │
   │  (e.g. Sonnet)     │                  │  subagents (e.g. Opus) │
   │  generates the     │                  │  fire IN PARALLEL      │
   │  artifact          │                  │  via the Task tool     │
   └────────────────────┘                  └────────────────────────┘
```

- **Drafter** — the hands. A Claude subagent (often the member's own model,
  e.g. Sonnet) that generates the artifact (code, prose, data, markup) and
  returns it. Spawn it via the Task/Agent tool.
- **Reviewers** — one or two **independent Claude subagents**. Each CAN run
  grep/build/read inside its own subagent shell to verify the artifact. They
  fire **simultaneously** — two `Task` calls in one message, not one after the
  other.
- **The member (integrator)** — reads both reviewer verdicts, reconciles
  disagreement, and returns a single PASS / CONCERNS / BLOCK.

**Independence rule.** The reviewer is deliberately a *different* Claude than
the drafter — a different model (Opus reviewing Sonnet), or a fresh instance
with no memory of the draft. A reviewer that IS the drafter shares its blind
spots. Different model / fresh instance = diverse blind spots = the point, not
a coincidence. (This is the same `critic != implementer` invariant
`safe-agentic-orchestration` enforces.)

---

## When to dual-review — and when not to

Dual-review is **standard for production work**, but it is not free. Each extra
Claude reviewer costs a subagent turn and adds wall-clock parallel latency. So
the rule is:

**Dual-review IS the default when:**
- The work touches source files that will be committed (`git diff` after the
  work is non-trivial).
- The deliverable is a public artifact — an article, a legal instrument, a
  campaign, a published analysis.
- The brief says "important" / "production" / "user-facing" / "ship" — i.e.
  anything that won't be caught by the developer's local test loop.
- The work is irreversible or expensive to redo (migrations, deploys,
  schema changes, large file deletes).

**Dual-review is OVERKILL when:**
- The change is mechanical and verifiable by a tool (rename one symbol,
  format a file, copy a directory).
- The work is throwaway — a spike, a one-off probe, an exploration.
- A reviewer cannot meaningfully add information (e.g. reviewing a single
  one-line typo).
- The brief is "quick check" / "draft only" / "I'll review myself."

When skipping, **say so explicitly in the report** —
*"skipped dual review: mechanical rename, verified by tool"*. The report should
be honest about what ran, not silent about what didn't.

---

## The five-step flow

Every dual-reviewed piece of work runs these five steps in this order. Skipping
a step is a violation.

### Step 1 — Plan and prompt

The member reads the order. Writes:
- a one-line label for itself (e.g. "You are the Developer — task: implement
  the foo middleware").
- the drafter prompt — a self-contained brief with file paths, contracts,
  acceptance test. Keep it tight.
- the one or two reviewer prompts — each a self-contained brief that names the
  artifact under review, the dimension to review (correctness, security,
  style, completeness — vary it), and the verdict format
  (PASS / CONCERNS / BLOCK with one-line reason).

When two reviewers run, the reviewer prompts SHOULD disagree on **dimension**
(one reviews for correctness, the other for security or completeness) — that is
how two independent Claude subagents add unique signal instead of duplicating
each other.

### Step 2 — Spawn the drafter

Spawn the drafter as a Claude subagent via the Task/Agent tool
(`subagent_type="the-<member>"`), passing the drafter prompt. For a big
generation, size the brief and let the subagent work; the member **reviews the
returned artifact inline against the plan**, re-prompting the drafter on
non-conforming output before moving on.

### Step 3 — Fire the reviewer(s) IN PARALLEL as Claude subagents

This is the load-bearing step. When two reviewers run, both run
**simultaneously** in a single assistant turn — two `Task` calls in one
message, not in sequence. Each reviewer is an independent Claude subagent (a
different model, or a fresh instance).

Each reviewer subagent:
1. Loads the artifact (passed in the brief, or read from disk if the brief
   includes the path).
2. Runs its review dimension — correctness, security, completeness, etc.
3. Returns a structured verdict:

   ```
   VERDICT: PASS | CONCERNS | BLOCK
   DIMENSION: <what was reviewed>
   EVIDENCE: <one-line reason, with file/line/snippet if applicable>
   SUGGESTED FIX: <optional, one line>
   ```

**Why parallel, not sequential.** Sequential review doubles the wall-clock
budget; parallel review uses the same time as one review. Only the live top
session can fan out parallel sibling subagents, so the Butler orchestrates the
parallel spawn.

### Step 4 — Integrate the verdicts

The member reads the verdict(s) and decides. With two reviewers:

| Verdict A | Verdict B | Integrated result |
|---|---|---|
| PASS | PASS | **Ship.** Both reviewers agree. Return result. |
| PASS | CONCERNS | **Ship with notes.** Apply the CONCERNS as a follow-up if cheap, or document them in the report. |
| PASS | BLOCK | **Block.** A single BLOCK stops the ship. Re-spawn the drafter with the BLOCK's reason. |
| CONCERNS | CONCERNS | **Block — two concerns compound.** Treat as BLOCK unless both are cosmetic. |
| CONCERNS | BLOCK | **Block.** |
| BLOCK | BLOCK | **Block.** |

A disagreement between two reviewers (one PASS, one BLOCK) is **the canonical
signal that the review is working** — diverse blind spots caught something one
reviewer missed. Don't average; respect the BLOCK. With a single reviewer, its
verdict stands: PASS ships, CONCERNS ships-with-notes, BLOCK re-drafts.

### Step 5 — Report

Return a single structured report to the caller. It MUST include:
- WHAT was done (the artifact, file paths, hashes if material).
- The reviewer verdict(s) (verbatim).
- The integrated result.
- Anything skipped (with reason) — see §When not to dual-review.

If a reviewer subagent timed out or errored, **say so** in the report —
*"Reviewer A (Opus) timed out; Reviewer B PASSED; partial dual review"*. The
caller cannot recalibrate if it doesn't know what actually ran.

---

## Invocation — the right way

Spawn every drafter and reviewer as a **Claude subagent** via the Task/Agent
tool. Fire the reviewers in parallel by issuing their Task calls in a single
assistant message.

```
# Draft — spawn the member as a Claude subagent:
Task(subagent_type="the-developer", prompt="<drafter-prompt>")

# Review — fire one or two INDEPENDENT Claude reviewers in ONE message so they
# run in parallel. Use a different model where you can (an Opus subagent
# reviewing a Sonnet draft), or at minimum a fresh instance:
Task(subagent_type="the-architect", prompt="<reviewer-prompt: correctness>")
Task(subagent_type="the-architect", prompt="<reviewer-prompt: security>")
```

**Why a different Claude for the reviewer.** The reviewer's value is
independence. A fresh subagent never saw the drafting reasoning, so it cannot
inherit the drafter's blind spots; a different model (Opus vs Sonnet) brings a
different lineage of judgment on top. The bigger the gap between drafter and
reviewer, the more the review catches.

---

## Pitfalls

These are the failure modes that bite dual-review runs. Load them before you
start.

### 1. Reviewing with the same Claude that drafted

The single most common failure: letting the drafter grade its own work (or
re-using the same subagent for both). The reviewer MUST be a different Claude —
a different model, or a fresh instance with no memory of the draft. A drafter
that reviews itself confirms its own blind spots.

### 2. Sequential instead of parallel reviewers

When two reviewers run, they must fire in ONE assistant message so they run
simultaneously. Two separate turns doubles the wall-clock cost for no gain.
Only the live top session can spawn parallel siblings, so the Butler
orchestrates the fan-out.

### 3. Under-sizing the reviewer brief

A reviewer handed only "review this" with no artifact and no dimension returns
noise. Give it the artifact (or a path), a single review dimension, and the
verdict format. A precise brief is what makes the second Claude's turn worth
spending.

### 4. Duplicated review dimensions

If both reviewers review for the same dimension (e.g. both check correctness),
they produce near-identical verdicts — the second reviewer adds zero unique
signal. Assign **different dimensions** (correctness + security, completeness +
style, etc.) so the two independent Claudes actually compound.

### 5. Forgetting to report what ran

The caller needs to know which reviewers actually returned. A reviewer that
timed out and was retried should be logged in the report —
*"Reviewer A timed out once, retried, PASS on retry; Reviewer B PASSED first
try"*. The caller cannot recalibrate if the report is silent about partial
runs.

### 6. Reporting the artifact, not the verdict

The member integrates the verdicts — that's its job. The report should present
**the integrated decision**, not just dump the raw verdicts and make the caller
integrate. Two PASS verdicts become "shipped"; one PASS + one CONCERNS becomes
"shipped with notes: …". A raw verdict dump is a hand-off failure.

---

## Cross-links

- [[weapon-utility]] — the spawn-a-subagent doctrine. Dual-review spawns a
  drafter subagent for generation and one or two independent Claude subagents
  for review. Never let the reviewer be the drafter.
- [[decompose-and-swarm]] — when many slices each need dual review, fan out the
  slices AND fan out reviewers per slice. Same parallel pattern, one level
  deeper.
- [[safe-agentic-orchestration]] — the independence-gate doctrine: a verifier
  must never be the implementer. Dual-review is that gate at the single-piece
  level.
- [[star-alliance-language]] — the report is plain English, jargon-free, names
  the verdicts and the integrated result. No stack traces, no model code-names
  the reader has to decode.

## Changelog

- **1.0.0** — Initial release. Three roles (a Claude drafter + one or two
  independent Claude reviewers in parallel), five-step flow (plan / draft /
  parallel review / integrate / report), explicit invocation rules (spawn every
  role as a Claude subagent via the Task tool; the reviewer is always a
  different Claude — different model or fresh instance), pitfalls (reviewing
  with the same Claude, sequential reviewers, under-sized briefs, duplicated
  dimensions, missing-report, raw-verdict hand-off).
