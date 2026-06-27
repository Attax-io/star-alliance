#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — BUILD MARK  (PostToolUse, non-blocking)
#
# Replaces the two per-edit build hooks (member-table-sync + guild-source-rebuild)
# that EACH ran the full 1k-line build.py (regenerating ~1.8 MB of guild-data.js /
# guild-data.json / skill-md.js / workflow-md.js) on EVERY single source edit. A
# campaign touching 20 skill files triggered ~20+ full rebuilds — pure redundant
# burn on the critical path.
#
# THE FIX: this hook does NOT build. It only drops a one-byte marker
#   .claude/state/build-pending
# whenever an edit touched a build-source file. turn-finalize.sh consumes the
# marker ONCE at Stop, rebuilds a single time, and that regenerated output lands
# in the same coalesced turn commit. Build cost is now O(1 per turn), not
# O(edits per turn).
#
# Build-source = anything build.py reads: member .md, members-meta.json, any
# skill file, workflows.json, guild-log.json, or any *-art tile.
#
# Fails OPEN (exit 0 always): a broken mark must never brick the session.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json

TRIGGERS = (
    "/star-alliance-members/",      # member .md (+ table regen)
    "data/members-meta.json",
    "data/skills-meta.json",
    "data/domains.json",
    "/star-alliance-skills/",       # any skill file
    "workflows.json",
    "data/guild-log.json",
    "/member-art/", "/skill-art/", "/role-art/", "/weapon-art/", "/workflow-art/",
)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    ti = data.get("tool_input", {}) or {}
    path = (ti.get("file_path") or ti.get("filePath") or "").replace("\\", "/")
    if not path or not any(t in path for t in TRIGGERS):
        sys.exit(0)

    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        state = os.path.join(proj, ".claude", "state")
        os.makedirs(state, exist_ok=True)
        open(os.path.join(state, "build-pending"), "w").write(path + "\n")
    except Exception as e:
        sys.stderr.write(f"[build-mark] could not set flag: {e}\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
