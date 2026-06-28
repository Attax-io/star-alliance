---
type: Document
title: Hook Enforcement
description: Machine-enforced quality gates — TeammateIdle and TaskCompleted hooks that exit code 2 to BLOCK a teammate going idle or a task completing until acceptance criteria are met. The team-level mirror of the guild verify-gate.
timestamp: 2026-06-28T00:00:00Z
---

# Hook Enforcement

Doctrine tells an agent it *should* not skip a gate. A **hook** makes it *cannot*. This is the difference between a discipline and an invariant: the QAS independence gate, the "done means done" rule, the evidence requirement — all become real only when something mechanical refuses to let the line advance past them. The harness wires two team-lifecycle hooks for exactly this, and they are the team-level analogue of the Star Alliance verify-gate (`.claude/hooks/verify-gate.py`): never let an over-eager agent grade its own work or declare done what is not done.

The principle is one move: **a gate you only trust is a gate that gets skipped under pressure; a gate a hook enforces is a gate.** Convert each load-bearing gate in `gating-and-release.md` into a hook wherever the coordination substrate exposes a lifecycle event.

## The two enforcement points

| Hook | Fires when | Blocks | exit 2 means |
| --- | --- | --- | --- |
| **TeammateIdle** | A teammate is about to go idle (no more queued work) | The teammate going idle | "Your assigned work is not actually complete — keep working" |
| **TaskCompleted** | A task is about to be marked done | The task completing | "Acceptance criteria are not met — this is not done" |

`TeammateIdle` guards the *agent* lifecycle (an agent must not park itself with work unfinished). `TaskCompleted` guards the *work-item* lifecycle (a task must not flip to done before its ACs verify). Together they make the agent loop's terminal states — "idle" and "done" — gated rather than self-declared.

## Exit-code contract

These are PreToolUse/lifecycle hooks with the standard Claude Code hook contract:

- **exit 0** — gate passes; the teammate goes idle / the task completes normally.
- **exit 2** — gate **BLOCKS**. The action is prevented and the hook's stderr is fed back to the teammate as the reason. The teammate stays working (TeammateIdle) or the task stays open (TaskCompleted), then re-attempts — so the hook must print *what is missing*, not just "blocked".
- **any other non-zero** — treated as a hook error (fails open by default — log it loudly; a silently broken gate is worse than no gate).

The feedback loop is the whole point: exit 2 + a precise stderr message ("AC-3 has no evidence attached"; "lint did not run") turns the block into a corrective instruction, not a dead end.

## Wiring

Agent Teams are experimental — enable them first, then register the hooks in `.claude/settings.json` (or `settings.local.json`):

```json
{
  "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" },
  "hooks": {
    "TeammateIdle": [{
      "command": "bash -c './gates/teammate-idle-check.sh'",
      "description": "Block idle until assigned work is verifiably complete"
    }],
    "TaskCompleted": [{
      "command": "bash -c './gates/task-complete-check.sh'",
      "description": "Block completion until acceptance criteria are met"
    }]
  }
}
```

Keep the *check* in a script the hook calls, not inline in the command string (inline gate logic is unauditable and easy to weaken accidentally). The script reads the task/teammate context the harness passes on stdin, runs the real check (e.g. the spec's success-validation command from `gating-and-release.md`, or a grep for attached evidence), and exits 0 or 2.

## What a check should actually verify

A hook is only as good as its check. Anchor each one to the artifacts the pipeline already requires:

- **TaskCompleted** → re-run the spec's **success-validation command** (the runnable "done" proof from the spec contract); confirm every acceptance criterion has **attached evidence**; confirm CI is green. No green command → exit 2.
- **TeammateIdle** → confirm none of the teammate's assigned tasks are still open or un-evidenced; confirm any task it owns that is a QAS/Sec independence gate was actually run, not skipped. Unfinished or unverified → exit 2.

A check that always exits 0 is theatre — it must be able to fail, and it must fail on the real anti-patterns ("trust me, it works", a self-graded QAS, a done flag with no validation command output).

## Relationship to the other gates

This file is the **mechanism**; `gating-and-release.md` is the **doctrine** those mechanisms enforce, and `coordination-patterns.md` covers the human-discipline side (escalation, evidence, the agent loop). The mapping:

| Gate (doctrine) | Enforcing hook (mechanism) |
| --- | --- |
| QAS independence gate — "implementer never grades its own work" | `TaskCompleted` rejects a done-flag whose QAS task is unrun or self-owned |
| Evidence-based delivery — "no 'trust me, it works'" | `TaskCompleted` rejects completion with no attached evidence / no validation output |
| "Done means done" / agent-loop terminal states | `TeammateIdle` rejects parking with assigned work unverified |

Hooks do not replace the human merge gate (HITL) — they make sure the work that *reaches* the human has already cleared every machine-checkable gate, so the human reviews substance, not bookkeeping. The guild's own `verify-gate.py` (Stop·blocking, auto-runs an independent critic on a turn's diff, exit-blocks on findings) is the single-session version of the same pattern; these two hooks extend it from one session to a coordinated team.

## Limits

- **Experimental surface** — `TeammateIdle`/`TaskCompleted` exist only with Agent Teams enabled; on subagent/background coordination there is no idle/completed lifecycle event to hook, so enforce those gates via task **dependencies** (`blockedBy`) instead (see `coordination-patterns.md`).
- **Fail-open by default** — if the check script errors, the action proceeds. That is deliberate (a broken gate must not wedge the whole team) but means a crashing check silently disarms the gate. Log errors loudly and alert; never swallow them.
- **Permissions inherit** — teammates run under the lead's permission mode, so a hook script must not assume elevated access it was not granted.
