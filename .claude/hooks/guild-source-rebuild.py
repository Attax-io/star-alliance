#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — GUILD SOURCE REBUILD  (PostToolUse, non-blocking)
#
# THE INVARIANT: guild-data.json / guild-data.js are GENERATED outputs.
# When any source that feeds build.py is edited, the outputs must regenerate
# immediately — in the SAME autocommit — or they drift from source truth.
#
# Covered sources (members/.md + members-meta.json handled by member-table-sync):
#   • workflows.json
#   • star-alliance-skills/**  (any skill file)
#   • data/guild-log.json      (version is derived from log entries)
#
# build.py is idempotent: double-runs with member-table-sync are harmless.
# Fails OPEN: a broken rebuild must never brick the session. exit 0 always.
# Must run BEFORE autocommit.sh so the regenerated outputs land in that commit.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, subprocess

TRIGGERS = [
    "workflows.json",
    "/star-alliance-skills/",
    "data/guild-log.json",
]


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = data.get("tool_input", {}) or {}
    path = (ti.get("file_path") or ti.get("filePath") or "").replace("\\", "/")
    if not path:
        sys.exit(0)

    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    if not any(t in path for t in TRIGGERS):
        sys.exit(0)

    try:
        result = subprocess.run(
            [sys.executable, os.path.join(proj, "build.py")],
            cwd=proj, capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            sys.stderr.write(
                f"[guild-source-rebuild] build.py exited {result.returncode}: "
                f"{result.stderr[:300]}\n"
            )
        else:
            sys.stderr.write("[guild-source-rebuild] build.py OK\n")
    except Exception as e:
        sys.stderr.write(f"[guild-source-rebuild] build.py failed: {e}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
