#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — CONTEXT SAVE  (adopted from gstack context-save, 2026-06 audit)
#
# A mid-session resumption checkpoint: captures git state + the decisions made +
# the work remaining, so a FUTURE cold session (or a different member) can pick up
# exactly where this one left off. Distinct from memory files (curated, durable
# facts) — this is a transient "where am I" snapshot for handoff/resume.
#
# Usage:
#   python3 .claude/context/context_save.py "<one-line summary>" \
#       [--decisions "a; b; c"] [--remaining "x; y"]
#   (summary may also be piped on stdin)
#
# Writes:  .claude/state/context/<UTC-stamp>.md   and   .../latest.md
# Restore with context_restore.py.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import subprocess
import argparse
from datetime import datetime, timezone


def git(args, root):
    return subprocess.run(["git", "-C", root] + args,
                          capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("summary", nargs="?", default="")
    ap.add_argument("--decisions", default="")
    ap.add_argument("--remaining", default="")
    a = ap.parse_args()

    summary = a.summary or (sys.stdin.read().strip() if not sys.stdin.isatty() else "")
    if not summary:
        sys.stderr.write("context_save: provide a one-line summary (arg or stdin)\n")
        sys.exit(1)

    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    root = git(["rev-parse", "--show-toplevel"], proj) or proj
    out_dir = os.path.join(proj, ".claude", "state", "context")
    os.makedirs(out_dir, exist_ok=True)

    branch = git(["branch", "--show-current"], root)
    head = git(["rev-parse", "--short", "HEAD"], root)
    status = git(["status", "--porcelain"], root)
    recent = git(["log", "--oneline", "-8"], root)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")

    def bullets(s):
        items = [x.strip() for x in s.replace("\n", ";").split(";") if x.strip()]
        return "\n".join(f"- {x}" for x in items) or "- (none recorded)"

    body = f"""# Context checkpoint — {stamp}

**Summary:** {summary}

**Branch:** `{branch or "?"}`  ·  **HEAD:** `{head or "?"}`

## Decisions made
{bullets(a.decisions)}

## Work remaining
{bullets(a.remaining)}

## Working tree at save
```
{status or "(clean)"}
```

## Recent commits
```
{recent}
```
"""
    path = os.path.join(out_dir, f"{stamp}.md")
    with open(path, "w") as f:
        f.write(body)
    with open(os.path.join(out_dir, "latest.md"), "w") as f:
        f.write(body)
    print(f"context saved → {os.path.relpath(path, proj)}")


if __name__ == "__main__":
    main()
