#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — CONTEXT RESTORE  (pair of context_save.py)
#
# Prints the most recent context checkpoint so a cold session can resume. Pass a
# stamp to restore a specific one, or --list to see all saved checkpoints.
#
# Usage:
#   python3 .claude/context/context_restore.py            # latest
#   python3 .claude/context/context_restore.py --list     # list all
#   python3 .claude/context/context_restore.py <stamp>    # a specific one
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys


def main():
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    d = os.path.join(proj, ".claude", "state", "context")
    if not os.path.isdir(d):
        sys.stderr.write("context_restore: no checkpoints saved yet.\n")
        sys.exit(1)

    args = sys.argv[1:]
    if args and args[0] == "--list":
        stamps = sorted(f[:-3] for f in os.listdir(d)
                        if f.endswith(".md") and f != "latest.md")
        if not stamps:
            print("(no checkpoints)")
            return
        for s in stamps:
            print(s)
        return

    if args:
        target = os.path.join(d, args[0] + ".md")
        if not os.path.exists(target):
            sys.stderr.write(f"context_restore: no checkpoint '{args[0]}'\n")
            sys.exit(1)
    else:
        target = os.path.join(d, "latest.md")
        if not os.path.exists(target):
            sys.stderr.write("context_restore: no 'latest' checkpoint.\n")
            sys.exit(1)

    with open(target) as f:
        sys.stdout.write(f.read())


if __name__ == "__main__":
    main()
