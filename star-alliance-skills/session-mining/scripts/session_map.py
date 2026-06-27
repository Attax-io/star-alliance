#!/usr/bin/env python3
"""session_map.py — locate session transcripts and map them to titles.

The real conversation bodies are the Claude Code project transcripts:
    ~/.claude/projects/<slug>/<cliSessionId>.jsonl     (slug = cwd with '/'->'-')
Cowork (local-agent-mode) wraps each in a metadata file that holds the human
TITLE + cwd, keyed by cliSessionId:
    ~/Library/Application Support/Claude/claude-code-sessions/**/local_*.json

This script joins the two: filter by cwd substring, resolve each wrapper's
cliSessionId to its .jsonl, and emit a TSV sorted by transcript size:
    <bytes>\t<title>\t<cliSessionId>\t<jsonl-path>

Usage:
    python3 session_map.py --match star-alliance --out map.tsv
    python3 session_map.py --match "Lex Council"            # prints to stdout
"""
import argparse, json, os, sys

HOME = os.path.expanduser("~")
PROJECTS = os.path.join(HOME, ".claude", "projects")
COWORK = os.path.join(HOME, "Library", "Application Support", "Claude", "claude-code-sessions")


def jsonl_for(cli_id):
    """Find <cliSessionId>.jsonl anywhere under ~/.claude/projects/."""
    if not os.path.isdir(PROJECTS):
        return None
    for slug in os.listdir(PROJECTS):
        p = os.path.join(PROJECTS, slug, cli_id + ".jsonl")
        if os.path.exists(p):
            return p
    return None


def iter_wrappers():
    """Yield (title, cwd, cliSessionId) for every Cowork wrapper metadata file."""
    if not os.path.isdir(COWORK):
        return
    for root, _, files in os.walk(COWORK):
        for f in files:
            if not (f.startswith("local_") and f.endswith(".json")):
                continue
            try:
                d = json.load(open(os.path.join(root, f)))
            except Exception:
                continue
            cli = d.get("cliSessionId")
            if not cli:
                continue
            yield (d.get("title") or "?", d.get("cwd") or "", cli)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", default="", help="cwd substring filter (default: all)")
    ap.add_argument("--out", default="", help="write TSV here (default: stdout)")
    a = ap.parse_args()

    rows, seen = [], set()
    for title, cwd, cli in iter_wrappers():
        if a.match and a.match not in cwd:
            continue
        if cli in seen:
            continue
        seen.add(cli)
        j = jsonl_for(cli)
        sz = os.path.getsize(j) if j else 0
        rows.append((sz, title.replace("\t", " "), cli, j or ""))
    rows.sort(reverse=True)

    out = open(a.out, "w") if a.out else sys.stdout
    for sz, title, cli, j in rows:
        out.write(f"{sz}\t{title}\t{cli}\t{j}\n")
    if a.out:
        out.close()
        with_t = sum(1 for r in rows if r[0])
        print(f"sessions: {len(rows)} | with transcript: {with_t} | bytes: {sum(r[0] for r in rows)}")


if __name__ == "__main__":
    main()
