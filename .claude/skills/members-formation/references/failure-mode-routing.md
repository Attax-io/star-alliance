---
type: Document
title: Failure-mode routing — every stuck has a named owner
timestamp: 2026-06-28T00:00:00Z
---

# Failure-mode routing — every stuck has a named owner

The Butler routes the START of work by matching the request to a workflow. This table
routes the FAILURES that surface mid-work: when an agent (or a member) gets stuck, the
stuck itself has a deterministic owner. "Agent is blocked" is not a dead end — it is a
routing signal. Read the failure, name the owner, hand off.

| Failure surfaced mid-work | What it really is | Route to |
|---|---|---|
| A bug appears while doing something else | an unplanned defect | **the-developer** — `bug-fix-workflow` (file it, don't inline-derail) |
| The spec / acceptance criteria are missing or contradictory | undefined WHAT | **the-architect** — `spec-driven-development` (write the spec, gate it) |
| The task is too big / spans many waves / keeps growing | scope overflow | **the-strategist** — `conquering-campaign` (decompose into waves) |
| A visual or UX decision is needed to proceed | undecided design | **the-designer** — `design-taste` / `ux-research` |
| A security risk is spotted | unverified safety | **the-developer** — Security Sweep / `code-review-craft` |
| The repo has drifted / conformity fails | broken invariant | **the-quartermaster** — Compliance Audit |
| The request is vague, first-contact, low-stakes | undiscovered intent | **the-butler** — `butler-onboarding` (discover, offer starter prompts) |
| High-stakes ambiguity — destructive scope, wrong architecture, missing context | dangerous unknown | **HALT** — the Confusion Protocol: name it, present 2-3 options, ask |
| A doer returned malformed / truncated / off-spec output | doer miss, not a dead end | the member's **thinker** — re-prompt the doer against the plan (`weapon-utility`); never hand-fix silently |
| No workflow fits the work at all | uncharted path | **Workflow Forge** — forge the workflow first, then proceed |
| A specialist needs a craft no member carries | capability gap | **Skill Forge** — forge the skill; if a whole role is missing → **Guild Recruitment** |

## The rule

A blocked agent must DECLARE the failure mode, not silently retry or guess. The owner is
derivable from the table — so "I'm stuck" becomes "this is a missing-spec stuck → the-architect."
Retrying the same blind action (the read-the-same-file loop, the re-run-the-same-doer loop) is
the anti-pattern; re-routing by failure mode is the craft.
