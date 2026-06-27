# Deprecated hooks — archived, NOT wired

These three PostToolUse hooks were superseded by the **build-once-per-turn** chain and
removed from `.claude/settings.json`. They are kept here (not deleted) so old doc/log
references resolve to an explanation rather than a dangling name. **Nothing loads them.**

| Archived hook | Did | Replaced by |
|---|---|---|
| `autocommit.sh` | git commit on **every** edit (`auto: session turn` noise) | `turn-finalize.sh` (Stop) — ONE coalesced, workflow-named commit per turn |
| `member-table-sync.py` | ran `build.py` on every member `.md` / `members-meta.json` edit | `build-mark.py` (PostToolUse, flags `build-pending`) → `turn-finalize.sh` (Stop, builds once) |
| `guild-source-rebuild.py` | ran `build.py` on every workflow / skill / guild-log edit | same build-mark → turn-finalize path |

**Why:** the old chain made harness upkeep cost scale with *edit count* — a 20-edit campaign
fired ~40 redundant `build.py` runs and 20+ commits. The current chain caps it at **one build
and one commit per turn** (`build-mark.py` sets a flag, `turn-finalize.sh` consumes it at Stop).

Do not re-wire these. To restore the per-edit behavior you would have to add them back to
`settings.json` PostToolUse — which reintroduces the O(edits) cost the new chain fixed.

_Archived during the Strategic Audit harness-fix campaign, 2026-06-28._
