#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — SKILL FINGERPRINT  (Codex doctrine, 2026-06 audit)
#
# HARNESS-BOOKS: Codex installs skills as FINGERPRINTED versioned assets and only
# reinstalls when the fingerprint mismatches — deterministic, churn-free sync.
# Star Alliance already has guild-sync + skillsmith for drift; this is the cheap
# hardening that makes "did this skill actually change?" a content question, not a
# version-bump guess. guild-sync / skillsmith can diff against this manifest to
# reinstall ONLY the skills whose content fingerprint moved.
#
# Usage:
#   python3 .claude/tools/skill_fingerprint.py            # write the manifest
#   python3 .claude/tools/skill_fingerprint.py --check    # exit 1 if drifted, no write
#
# Manifest: .claude/state/skill-fingerprints.json  { skill_name: {version, sha} }
# sha = sha256 over every file under the skill dir (path + bytes), sorted.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import re
import hashlib

SKILLS_SUBDIR = "star-alliance-skills"


def proj():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def read_version(skill_md):
    try:
        txt = open(skill_md, encoding="utf-8", errors="replace").read()
    except OSError:
        return "?"
    m = re.search(r"version:\s*['\"]?([0-9]+\.[0-9]+\.[0-9]+)", txt)
    return m.group(1) if m else "?"


def fingerprint_dir(d):
    h = hashlib.sha256()
    for root, _dirs, files in os.walk(d):
        for fn in sorted(files):
            if fn.startswith(".") or fn.endswith((".pyc",)):
                continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, d)
            h.update(b"\0" + rel.encode())
            try:
                with open(fp, "rb") as fh:
                    h.update(fh.read())
            except OSError:
                pass
    return h.hexdigest()[:16]


def build_manifest():
    base = os.path.join(proj(), SKILLS_SUBDIR)
    out = {}
    if not os.path.isdir(base):
        return out
    for name in sorted(os.listdir(base)):
        d = os.path.join(base, name)
        smd = os.path.join(d, "SKILL.md")
        if os.path.isdir(d) and os.path.exists(smd):
            out[name] = {"version": read_version(smd), "sha": fingerprint_dir(d)}
    return out


def main():
    manifest_path = os.path.join(proj(), ".claude", "state", "skill-fingerprints.json")
    current = build_manifest()

    if "--check" in sys.argv:
        prev = {}
        if os.path.exists(manifest_path):
            try:
                prev = json.load(open(manifest_path))
            except (OSError, json.JSONDecodeError):
                prev = {}
        drifted = [n for n in current
                   if current[n]["sha"] != prev.get(n, {}).get("sha")]
        removed = [n for n in prev if n not in current]
        if drifted or removed:
            for n in drifted:
                print(f"DRIFT  {n}  {current[n]['version']}  {current[n]['sha']}")
            for n in removed:
                print(f"GONE   {n}")
            sys.exit(1)
        print(f"OK — {len(current)} skills, no fingerprint drift")
        return

    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    json.dump(current, open(manifest_path, "w"), indent=2, sort_keys=True)
    print(f"wrote {len(current)} skill fingerprints → "
          f"{os.path.relpath(manifest_path, proj())}")


if __name__ == "__main__":
    main()
