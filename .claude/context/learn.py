#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — LEARN  (adopted from gstack `learn`, 2026-06 audit)
#
# A durable, append-only store of cross-session "learnings" — the fast answer to
# "didn't we fix this before?". Complements (does NOT duplicate) the memory files:
#   • memory/  = hand-curated, indexed, durable FACTS (the library).
#   • learnings = append-only, searchable LOG of in-the-moment findings (the journal).
# Promote a recurring learning into a real memory file when it earns its place.
#
# Usage:
#   python3 .claude/context/learn.py add "<finding>" [--tags a,b]
#   python3 .claude/context/learn.py search "<term>"
#   python3 .claude/context/learn.py list [N]
#
# Store: .claude/state/learnings.jsonl  (one JSON object per line)
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import subprocess
from datetime import datetime, timezone


def store_path():
    proj = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return os.path.join(proj, ".claude", "state", "learnings.jsonl")


def load():
    p = store_path()
    if not os.path.exists(p):
        return []
    out = []
    for line in open(p):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def branch():
    return subprocess.run(["git", "branch", "--show-current"],
                          capture_output=True, text=True).stdout.strip()


def cmd_add(args):
    text = args[0] if args else (sys.stdin.read().strip() if not sys.stdin.isatty() else "")
    if not text:
        sys.stderr.write("learn add: provide a finding (arg or stdin)\n")
        sys.exit(1)
    tags = []
    if "--tags" in args:
        i = args.index("--tags")
        if i + 1 < len(args):
            tags = [t.strip() for t in args[i + 1].split(",") if t.strip()]
    rec = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "branch": branch(),
        "tags": tags,
        "text": text,
    }
    p = store_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"learned ({len(load())} total): {text[:80]}")


def fmt(r):
    tags = f" [{','.join(r['tags'])}]" if r.get("tags") else ""
    return f"{r.get('ts','?')}{tags}  {r.get('text','')}"


def cmd_search(args):
    if not args:
        sys.stderr.write("learn search: provide a term\n")
        sys.exit(1)
    term = args[0].lower()
    hits = [r for r in load()
            if term in r.get("text", "").lower()
            or term in ",".join(r.get("tags", [])).lower()]
    if not hits:
        print(f"(no learnings match '{args[0]}')")
        return
    for r in hits:
        print(fmt(r))


def cmd_list(args):
    n = int(args[0]) if args and args[0].isdigit() else 20
    recs = load()[-n:]
    if not recs:
        print("(no learnings yet)")
        return
    for r in recs:
        print(fmt(r))


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: learn.py add|search|list ...\n")
        sys.exit(1)
    sub, rest = sys.argv[1], sys.argv[2:]
    {"add": cmd_add, "search": cmd_search, "list": cmd_list}.get(
        sub, lambda _a: (sys.stderr.write(f"unknown subcommand '{sub}'\n"), sys.exit(1))
    )(rest)


if __name__ == "__main__":
    main()
