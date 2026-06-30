#!/usr/bin/env python3
"""bug-fix-closer — Stop hook: mark bug_reports Fixed when a session resolves one.

Reads the transcript's aiTitle (line 0), extracts a ``#NNN`` bug id, and closes
that bug in the Lex Council Supabase DB if it is not already Fixed (br_status 4).

Fail-open by design: any error exits 0 silently. A broken closer must never
block the Stop hook chain.
"""
import json
import os
import re
import subprocess
import sys

STAR_ALLIANCE_ROOT = os.environ.get(
    "STAR_ALLIANCE_ROOT", "/Users/atta/Documents/Claude/Projects/star-alliance"
)
SUPABASE_PY = os.path.join(STAR_ALLIANCE_ROOT, "star-alliance-arsenal", "supabase.py")
BUG_ID_RE = re.compile(r"#(\d+)")


def read_ai_title(transcript_path):
    """Return the ``aiTitle`` string from line 0 of the transcript JSONL."""
    with open(transcript_path, "r", encoding="utf-8") as fh:
        first = fh.readline()
    first = first.strip()
    if not first:
        return ""
    try:
        obj = json.loads(first)
    except json.JSONDecodeError:
        return ""
    return obj.get("aiTitle") or ""


def close_bug(bug_id):
    """UPDATE bug_reports SET Fixed WHERE br_id=:bug_id AND br_status != 4.

    Returns the number of rows actually updated (0 if already fixed / missing).
    """
    sql = (
        "UPDATE bug_reports "
        "SET br_status = 4, br_status_name = 'Fixed' "
        "WHERE br_id = {0} AND br_status != 4 "
        "RETURNING br_id, br_title, br_status_name"
    ).format(bug_id)
    proc = subprocess.run(
        ["python3", SUPABASE_PY, sql, "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        return 0
    out = proc.stdout.strip()
    if not out:
        return 0
    try:
        rows = json.loads(out)
    except json.JSONDecodeError:
        return 0
    if isinstance(rows, list):
        return len(rows)
    return 1 if rows else 0


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    transcript_path = payload.get("transcript_path")
    if not transcript_path or not os.path.isfile(transcript_path):
        return 0
    try:
        ai_title = read_ai_title(transcript_path)
    except OSError:
        return 0
    if not ai_title:
        return 0
    match = BUG_ID_RE.search(ai_title)
    if not match:
        return 0
    bug_id = match.group(1)
    try:
        updated = close_bug(bug_id)
    except (subprocess.SubprocessError, OSError):
        return 0
    if updated and updated >= 1:
        sys.stderr.write(
            "[bug-fix-closer] Bug #{0} marked Fixed in DB\n".format(bug_id)
        )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)