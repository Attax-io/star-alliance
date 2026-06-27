#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — VERIFY HASH  (shared helper for the independent-verification gate)
#
# Prints a stable 16-char fingerprint of the SOURCE changes currently in the
# working tree vs HEAD (tracked-modified + untracked source files, content-hashed
# and pinned to the current HEAD commit). Both verify-gate.py (the Stop gate) and
# the "mark verified" command use THIS one definition so they always agree.
#
# Output:
#   CLEAN   — no source files changed (gate stands aside)
#   NOREPO  — not in a git repo (gate stands aside)
#   <hash>  — 16-hex fingerprint of the current source diff
#
# "Source" = code that warrants an independent review. Docs/data/memory/state are
# excluded on purpose: a memory note or a JSON data edit is not an implementation.
# ─────────────────────────────────────────────────────────────────────────────
import subprocess
import hashlib
import os
import sys

SRC_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".sh",
           ".sql", ".go", ".rs", ".rb", ".php", ".vue", ".svelte", ".css"}


def is_source(path):
    if path.startswith(".claude/state/"):
        return False
    _, ext = os.path.splitext(path)
    return ext in SRC_EXT


def run(args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def main():
    root = run(["git", "rev-parse", "--show-toplevel"]).strip()
    if not root:
        print("NOREPO")
        return
    os.chdir(root)

    files = []
    # -uall expands untracked files individually; plain --porcelain collapses a
    # brand-new directory into one entry with no extension, hiding its source files.
    for line in run(["git", "status", "--porcelain", "-uall"]).splitlines():
        path = line[3:].strip()
        if " -> " in path:                      # renamed: take the destination
            path = path.split(" -> ")[-1].strip()
        path = path.strip('"')
        if is_source(path):
            files.append(path)
    files = sorted(set(files))

    if not files:
        print("CLEAN")
        return

    h = hashlib.sha256()
    h.update(run(["git", "rev-parse", "HEAD"]).strip().encode())
    for f in files:
        h.update(b"\0" + f.encode())
        try:
            with open(f, "rb") as fh:
                h.update(fh.read())
        except OSError:
            pass
    print(h.hexdigest()[:16])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:                       # fail safe: never crash a caller
        sys.stderr.write(f"[verify_hash] {e}\n")
        print("NOREPO")
