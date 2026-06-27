#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — MEMBER TABLE SYNC  (PostToolUse, non-blocking)
#
# THE INVARIANT: a member's "## Your Weapons" prose table is GENERATED from its
# frontmatter `weapons:` loadout + members-meta.json `weaponsDesc`. It is never
# hand-authoritative. When a loadout source is edited, the table must regenerate
# or it drifts (8 of 9 members had drifted before this existed).
#
# This hook fires after any Edit/Write/MultiEdit. If the touched file is a member
# .md or members-meta.json, it runs build.py — which self-heals every table (and
# guild-data) — so the fix lands in the SAME autocommit that follows. build.py's
# writes are subprocess writes, not Claude tool calls, so they do not re-trigger
# PostToolUse: no loop.
#
# Fails OPEN on anything: a broken sync must never brick the session. exit 0 always.
# Must run BEFORE autocommit.sh in the PostToolUse chain so the table is committed.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, subprocess


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = data.get("tool_input", {}) or {}
    path = (ti.get("file_path") or ti.get("filePath") or "").replace("\\", "/")
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    is_member_md = "/star-alliance-members/" in path and path.endswith(".md")
    is_meta = path.endswith("data/members-meta.json")
    if not (is_member_md or is_meta):
        sys.exit(0)

    try:
        subprocess.run(
            [sys.executable, os.path.join(proj, "build.py")],
            cwd=proj, capture_output=True, text=True, timeout=60,
        )
    except Exception as e:
        sys.stderr.write(f"[member-table-sync] build.py failed, leaving file as-is: {e}\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
