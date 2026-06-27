#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — PRECOMPACT SNAPSHOT  (PreCompact, non-blocking)
#
# Why this exists: when Claude's context is compressed, all in-flight state
# (current workflow, branch, recently-touched files, last tier) is lost. The
# next turn restarts cold — members re-read the same files, re-derive context,
# waste ~30min equivalent of tokens. This hook captures a lightweight snapshot
# BEFORE compression fires, so the next session can rehydrate fast.
#
# Writes: .claude/state/snapshots/<epoch>.json  (kept, never deleted here)
# Also writes: .claude/state/latest-snapshot.json  (always the most recent)
#
# Contents: ts, branch, tier, recent_files (last 10 from git), last workflow
# (scanned from .claude/state/last-workflow if the workflow-gate writes it).
#
# Fails OPEN — a broken snapshot must never block compression.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, time, pathlib, subprocess

def main():
    try:
        proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        state = pathlib.Path(proj) / ".claude" / "state"
        state.mkdir(parents=True, exist_ok=True)
        snaps = state / "snapshots"
        snaps.mkdir(exist_ok=True)

        def git(cmd):
            try:
                return subprocess.check_output(
                    ["git", "-C", proj] + cmd.split(),
                    stderr=subprocess.DEVNULL, text=True
                ).strip()
            except Exception:
                return ""

        branch = git("rev-parse --abbrev-ref HEAD")
        recent_files = [f for f in git("diff --name-only HEAD~1").splitlines() if f][:10]

        tier_file = state / "last-tier"
        tier = tier_file.read_text().strip() if tier_file.exists() else "unknown"

        workflow_file = state / "last-workflow"
        workflow = workflow_file.read_text().strip() if workflow_file.exists() else "unknown"

        snap = {
            "ts": time.time(),
            "branch": branch,
            "tier": tier,
            "workflow": workflow,
            "recent_files": recent_files,
        }
        blob = json.dumps(snap, indent=2)
        ts_key = str(int(time.time()))
        (snaps / f"{ts_key}.json").write_text(blob)
        (state / "latest-snapshot.json").write_text(blob)
    except Exception:
        pass
    sys.exit(0)

if __name__ == "__main__":
    main()
