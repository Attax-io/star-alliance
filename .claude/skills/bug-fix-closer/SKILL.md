---
name: bug-fix-closer
description: "Mark one or more Lex Council bug_reports rows as Fixed (br_status=4) in the DB. Use when the user says 'close bug #NNN', 'mark bug fixed', 'mark bugs NNN and MMM fixed', 'close these bugs in DB', or any phrasing about manually closing bugs in the database — after a fix landed but the Stop hook didn't auto-close them (title didn't match), or for batch closes of multiple bugs at once."
metadata:
  version: 1.0.0
  member: the-quartermaster
type: Skill

---
# Bug-Fix Closer

The Quartermaster's manual override for marking Lex Council bugs as Fixed in the
database. A Stop hook (`tools/bug-fix-closer.py`) already auto-closes bugs when a
session whose title contains `#NNN` ends — this skill is the manual fallback for
when the hook didn't fire, or when a batch of bugs needs closing in one shot.

## What it does

Runs a direct SQL `UPDATE` on the `bug_reports` table via `supabase.py`, setting
`br_status = 4` and `br_status_name = 'Fixed'`. The `RETURNING` clause confirms
which rows were actually changed.

## When to use

- A fix landed but the Stop hook didn't auto-close the bug (the session title
  didn't contain `#NNN`, or the session is still open).
- A batch of bugs needs marking Fixed in one operation.
- You need to verify a bug is already Fixed before claiming it closed.

## How to invoke manually

```bash
python3 $STAR_ALLIANCE_ROOT/star-alliance-arsenal/supabase.py \
  "UPDATE bug_reports SET br_status=4, br_status_name='Fixed' WHERE br_id IN (<comma-sep ids>) AND br_status != 4 RETURNING br_id, br_title"
```

### Single bug

```bash
python3 $STAR_ALLIANCE_ROOT/star-alliance-arsenal/supabase.py \
  "UPDATE bug_reports SET br_status=4, br_status_name='Fixed' WHERE br_id IN (42) AND br_status != 4 RETURNING br_id, br_title"
```

### Batch (multiple bugs)

```bash
python3 $STAR_ALLIANCE_ROOT/star-alliance-arsenal/supabase.py \
  "UPDATE bug_reports SET br_status=4, br_status_name='Fixed' WHERE br_id IN (42, 57, 89) AND br_status != 4 RETURNING br_id, br_title"
```

## Notes

### br_status values

| Value | Name | Meaning |
|---|---|---|
| 1 | Submitted | Newly filed, not yet looked at |
| 2 | Investigated & Pending | Under investigation or awaiting action |
| 3 | Rejected | Will not fix |
| 4 | Fixed | Fix is live |

### Rules

- **Never downgrade a Fixed bug.** The `AND br_status != 4` guard prevents
  re-processing an already-Fixed row. Always include it.
- **Always use `RETURNING`.** The returned `br_id` and `br_title` confirm which
  rows were actually updated. If the query returns zero rows, either the bug
  was already Fixed or the `br_id` doesn't exist — investigate before claiming
  success.
- **Verify after closing.** Read the `RETURNING` output and report which bugs
  were closed. If fewer rows return than you expected, say so.

## See also

- `bug-fix-workflow` — the full end-to-end bug lifecycle (pull, triage,
  investigate, fix, close, push new bugs).
- `supabase` — the underlying Supabase interaction layer.