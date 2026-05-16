# Templates

Canonical shapes for every artefact a campaign produces. Copy and adapt — don't reinvent these formats per run, the consistency is what makes campaigns auditable.

## Campaign plan

Path: `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/00-campaign-plan.md`

```markdown
---
description: <one-sentence description of the campaign and what it's reconciling>
date: <YYYY-MM-DD>
trigger: <why this campaign — graphify run, version bump, drift suspected, etc.>
---

# Campaign: <Topic> (<YYYY-MM-DD>)

## Goal

Reconcile [[BACKEND]] / [[FRONTEND]] / [[INTEGRATION]] / [[GUIDELINES]] (or whatever the project's docs are) with actual app reality (code in <path> + DB via <mechanism>). Produce an honest source-of-truth and update doc-generation instructions so future runs stay accurate.

## What we already know going in

- <findings from any pre-campaign tool runs — graphify, lint, etc.>
- <hypotheses to verify or disprove>

## Wave structure

| Wave | Tasks | Run mode |
|---|---|---|
| **W1 — Foundation reality** | <task list> | parallel |
| **W2 — Deep structural** | <task list> | parallel |
| **W3 — Domain depth** | <task list> | parallel |
| **W4 — Synthesis** | synthesis → staged rewrites → promotion → vault-log | sequential |

## Tasks

### W1.1 — <Task Name>
- **Subagent:** <type>
- **Model:** <opus|sonnet|haiku>
- **Scope:** <one-line scope>
- **Output:** `01-<task>.md`

### W1.2 — ...

(Each task gets a 4-line entry.)

## Logging convention

Each subagent writes findings as a single markdown file at:
`docs/audit-campaigns/<YYYY-MM-DD>_<topic>/NN-<name>.md`

With this header:

\`\`\`yaml
---
task: WX.Y - Task Name
agent: subagent-type
model: opus|sonnet|haiku
date: YYYY-MM-DD
status: complete|partial|blocked
---
\`\`\`

Then sections: **Method · Findings · Drift table · Recommendations · Open questions**.

## Success criteria

1. Every entity-of-interest has been verified or explicitly marked unverifiable.
2. Every doc rule has been spot-checked.
3. Updated docs cite the audit-campaign findings as evidence.
4. Future re-audit can be triggered with one prompt.
```

---

## Findings file

Path: `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/NN-<name>.md`

```markdown
---
task: W<wave>.<num> - <Task Name>
agent: <subagent-type>
model: opus|sonnet|haiku
date: <YYYY-MM-DD>
status: complete|partial|blocked
---

# <Task Title>

## 1. Method

- Files read
- Greps / queries used (with the exact commands when feasible)
- Sample sizes
- Any fallbacks (e.g., "DB pooler down — used migration files instead")

## 2. Findings

<Task-specific sections — typically:>
- Inventory tables (live vs documented)
- Pattern compliance scores
- Per-module breakdown
- Cross-cutting observations

## 3. Drift table

| Entity | In code/DB | In doc | Status (match / drift / undocumented / orphan) |
|---|---|---|---|
| ... | ... | ... | ... |

## 4. Critical findings

<Anything security-relevant or that could surprise the user.>

## 5. Recommendations

<Concrete edits the synthesis should make to the relevant doc, section by section.>

## 6. Open questions

<Things the synthesis agent should ask the user before finalising.>
```

---

## Synthesis (`99-synthesis.md`)

This is the big one. Write it yourself, not via a subagent.

```markdown
---
task: W4 — Master Synthesis
agent: main
model: opus
date: <YYYY-MM-DD>
status: complete
inputs:
  - 00-campaign-plan.md
  - 01-<task>.md
  - 02-<task>.md
  - ...
  - NN-<task>.md
---

# <Topic> — Master Synthesis (<YYYY-MM-DD>)

This is the consolidated changelog from <N> parallel audits run on <YYYY-MM-DD>. Each finding cites the audit file that produced it.

## TL;DR (read this if nothing else)

**<One-sentence drift summary.>**

**<N> real bugs** worth fixing soon:
1. ...
2. ...
3. ...

**<N> real security findings:**
- ...

**Architecture facts the graph misled us on, now corrected:**
- ...

## 1. Critical findings (security & defence-in-depth)

### 1.1 <Finding>
- **Where:** ...
- **Doc state:** ...
- **Source:** `<findings-file>` §<section>
- **Action:** ...

(One subsection per critical finding.)

## 2. Real bugs (worth fixing)

### 2.1 <Bug>
(Description, severity, fix sketch, source citation.)

## 3. Doc ghosts (referenced but don't exist)

| Reference | In doc | Reality | Source |
|---|---|---|---|
| ... | ... | ... | ... |

## 4. Doc orphans (in doc but not in reality)

(List per doc.)

## 5. Undocumented reality (in code but not in doc)

(List per doc — the synthesis brief for the rewrites.)

## 6. Architecture patterns to document

| Pattern | Where to document | Source |
|---|---|---|
| ... | ... | ... |

## 7. Doc rewrite checklist (per-file)

The W4 step-2 agents will use this as their brief.

### 7.1 <DOC-1>.md — full rewrite (heaviest scope)

Concrete edits, in section order:
1. ...
2. ...

(Repeat per doc.)

## 8. Code cleanup checklist (separate from doc rewrite)

This section is for whoever takes the next code-cleanup PR.

### 8.1 Safe deletes (one PR)
- ...

### 8.2 Verify-then-delete
- ...

### 8.3 Decision needed
- ...

### 8.4 Bug fixes
- ...

### 8.5 Refactoring (lower priority)
- ...

## 9. Open questions for the user (must answer before promotion)

1. ...
2. ...

## 10. Re-audit cadence

(When to run the next campaign.)

## 11. Headline metrics

| Metric | Value | Source |
|---|---|---|
| Files in scope | ... | ... |
| Graph nodes | ... | ... |
| ... | ... | ... |

End of synthesis.
```

---

## Checkpoint registry (`CHECKPOINTS.md`)

Path: `docs/audit-campaigns/<YYYY-MM-DD>_<topic>/CHECKPOINTS.md`

Only created if external resources were unreachable during the audit. Full pattern in [checkpoint-pattern.md](checkpoint-pattern.md).

```markdown
---
description: Items that need re-validation when <blocker> clears. Run these queries and reconcile every staged doc against live state before promotion.
created: <YYYY-MM-DD>
status: pending-<blocker> | resolved-<YYYY-MM-DD>
---

# <Blocker> Re-validation Checkpoints

The <blocker> was unreachable during this campaign. When restored, run the queries below and reconcile each staged doc.

## How to use this file

1. When <blocker> clears, run all queries in §1.
2. For each row in §2, compare migration-derived (left) with live (right).
3. Update each staged doc — every block tagged `<!-- CHECKPOINT: CHK-<id> -->` references an item here.
4. After all checkpoints clear, promote staged docs and emit a follow-up vault-log.

## §1 Queries to run

\`\`\`sql
-- CHK-1: ...
SELECT ...;

-- CHK-2: ...
SELECT ...;
\`\`\`

## §2 Reconciliation table

| ID | Claim in staged docs | <Blocker>-derived value | Live value | Source query | Resolution |
|---|---|---|---|---|---|
| CHK-1a | ... | ... | _pending_ | CHK-1 | ... |
```

---

## Vault-log entry

Path: `docs/vault-logs/<YYYY-MM-DD>_<campaign>.md` (or whatever the project's logging path is).

```markdown
---
description: <one-sentence summary of what changed and why>
date: <YYYY-MM-DD>
campaign: <YYYY-MM-DD>_<topic>
tags: [audit, doc-sync, ...]
---

# <Topic> (<YYYY-MM-DD>)

## Files Changed

### Live docs promoted
- [[DOC-1]] — <short description of changes>
- [[DOC-2]] — ...

### Staged but NOT yet live (pending <blocker>, if any)
- ...

### Campaign artefacts (new)
- [[<campaign>/00-campaign-plan]]
- [[<campaign>/01-<task>]]
- ...
- [[<campaign>/99-synthesis]]

## Why

<Trigger and rationale for the campaign.>

## What was found (headline)

<3–8 bullet points of the most important findings.>

## What was changed

<List of doc/code changes in this entry.>

## What was NOT changed

<Things explicitly out of scope for this entry — usually code fixes, deletions held for a separate PR.>

## P13 Self-Audit

(Only if the project has a P13-style MCP-usage audit. Otherwise skip.)

| MCP call / tool | Result |
|---|---|
| ... | ... |

## Next steps

1. ...
2. ...
```
