#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — DESTRUCTIVE-COMMAND GATE  (PreToolUse: Bash, BLOCKING)
#
# THE RULE: CLAUDE.md already says "confirm destructive git ops before executing"
# and "cancel = immediate revert" — but that was prose. Prose reminds; it never
# bites. This hook bites: it intercepts the Bash tool BEFORE an irreversible
# command runs and blocks it until the Guild Master has explicitly confirmed.
#
# Adopted from the gstack `careful`/`guard` pattern during the 2026-06 Skills
# Pool strategic audit (the cheapest, highest-confidence harvest item: 9/10).
#
# What it guards (data loss / history rewrite / prod impact):
#   rm -rf / rm -r            DROP TABLE / DROP DATABASE / TRUNCATE
#   git push --force / -f     git reset --hard      git clean -fd
#   git checkout . / restore .  kubectl delete       docker rm -f / system prune
#   mkfs                      dd of=…               truncate -s 0
#   > /dev/sd*  (raw disk)    chmod -R 777
#
# OVERRIDE (honors an explicit "proceed"): once the Guild Master confirms, append
# the token  # sa-confirm  (or set env SA_CONFIRM=1) to the command and re-run.
# This mirrors gstack `careful`'s per-warning override and Star Alliance's
# "honor an explicit proceed — don't re-insert your own breakpoints" rule.
#
# Mechanics: PreToolUse hooks get the tool call as JSON on stdin.
#   • destructive pattern + no confirm token → exit 2 (block, name the risk)
#   • confirm token present                  → exit 0 (allow — operator owns it)
#   • no destructive pattern                 → exit 0 (allow)
# Fails OPEN on any internal error: a broken safety hook must never brick the
# session. Errors go to stderr.
# ─────────────────────────────────────────────────────────────────────────────
import sys
import os
import re
import json

# (label, compiled pattern, why-it's-dangerous) — order = first match wins for the message.
PATTERNS = [
    ("rm -rf",            re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-r\s+-f|-f\s+-r|--recursive)\b"), "recursive delete — unrecoverable"),
    ("rm -r",             re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*|--recursive)\b"), "recursive delete"),
    ("git push --force",  re.compile(r"\bgit\s+push\b.*(--force\b|--force-with-lease\b|\s-f\b)"), "rewrites remote history"),
    ("git reset --hard",  re.compile(r"\bgit\s+reset\s+--hard\b"), "discards uncommitted work"),
    ("git clean -f",      re.compile(r"\bgit\s+clean\b.*\s-[a-zA-Z]*f"), "deletes untracked files"),
    ("git checkout .",    re.compile(r"\bgit\s+checkout\s+\.(\s|$)"), "discards uncommitted changes"),
    ("git restore .",     re.compile(r"\bgit\s+restore\s+(\.|--\s+\.)(\s|$)"), "discards uncommitted changes"),
    ("DROP TABLE/DB",     re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE), "permanent schema/data loss"),
    ("TRUNCATE",          re.compile(r"\bTRUNCATE\s+(TABLE\s+)?\w", re.IGNORECASE), "permanent data loss"),
    ("DELETE FROM (no WHERE)", re.compile(r"\bDELETE\s+FROM\s+\w+\s*(;|$)", re.IGNORECASE), "unscoped delete — wipes the table"),
    ("kubectl delete",    re.compile(r"\bkubectl\s+delete\b"), "production resource removal"),
    ("docker rm -f",      re.compile(r"\bdocker\s+(rm|rmi)\b.*\s-[a-zA-Z]*f"), "force-removes containers/images"),
    ("docker prune",      re.compile(r"\bdocker\s+(system\s+|image\s+|volume\s+)?prune\b"), "bulk image/volume loss"),
    ("mkfs",              re.compile(r"\bmkfs(\.\w+)?\b"), "formats a filesystem"),
    ("dd of=",            re.compile(r"\bdd\b.*\bof=/"), "raw block write — can destroy a disk"),
    ("truncate -s 0",     re.compile(r"\btruncate\s+-s\s*0\b"), "zeroes a file"),
    ("> /dev/ raw disk",  re.compile(r">\s*/dev/(sd|disk|nvme|hd)\w"), "raw device overwrite"),
    ("chmod -R 777",      re.compile(r"\bchmod\s+-R\s+0?777\b"), "world-writable recursive"),
]

CONFIRM_TOKEN = re.compile(r"#\s*sa-confirm\b|(^|\s)SA_CONFIRM=1(\s|$)")


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str}."""
    if data.get("tool_name") != "Bash":
        return {"exit": 0}

    cmd = (data.get("tool_input") or {}).get("command", "") or ""
    if not cmd.strip():
        return {"exit": 0}

    # Explicit operator confirmation → stand aside (the Guild Master owns the risk).
    if CONFIRM_TOKEN.search(cmd) or os.environ.get("SA_CONFIRM") == "1":
        return {"exit": 0}

    for label, pat, why in PATTERNS:
        if pat.search(cmd):
            return {"exit": 2, "stderr": (
                "⛔ DESTRUCTIVE-COMMAND GATE — this command is irreversible.\n"
                f"   Matched: {label}  ({why})\n"
                f"   Command: {cmd.strip()[:300]}\n"
                "   This is a hard-to-reverse action. Per the guild's approval rule, do NOT\n"
                "   run it until the Guild Master has explicitly confirmed. Restate the risk,\n"
                "   get an explicit 'proceed', then re-run with  # sa-confirm  appended\n"
                "   (or SA_CONFIRM=1) to pass this gate.\n"
            )}

    return {"exit": 0}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[destructive-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)
    r = check(data)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    main()
