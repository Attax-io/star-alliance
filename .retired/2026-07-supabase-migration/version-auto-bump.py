#!/usr/bin/env python3
"""version-auto-bump.py — Stop hook (runs before turn-finalize.sh)

On every turn that changes substantive files, appends one entry to
data/guild-log.json so build.py derives a bumped version on the next rebuild.

Type mapping (checked in priority order):
  skill-create  → a new star-alliance-skills/*/SKILL.md was added  (MINOR bump)
  member-create → a new star-alliance-members/*.md was added        (MINOR bump)
  workflow      → workflows.json was modified                        (MINOR bump)
  upgrade       → any other substantive change                       (PATCH bump)

Skip conditions:
  - Only generated / state / tracking files changed (see SKIP list)
  - evolution/DISARMED present (engine kill-switch)
  - .claude/state/version-bumped present (already ran this turn)
  - data/guild-log.json does not exist
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent  # hooks → .claude → repo root

# Basenames that never trigger a bump
SKIP_NAMES = {
    "guild-data.json", "guild-data.js", "skill-md.js", "workflow-md.js",
    "VERSIONS.md", "guild-log.json",
}
# Path prefixes that never trigger a bump
SKIP_PREFIXES = (
    ".claude/state/",
    "evolution/ledger.jsonl",
    "evolution/scoreboard",
    "data/turn-cost.jsonl",
    "data/usage-log.jsonl",
    "data/domains.json",
)


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args], capture_output=True, text=True
    ).stdout


def changed_files() -> list[tuple[bool, str]]:
    """Return (is_new, path) for every working-tree change."""
    result = []
    for line in git("status", "--porcelain", "-uall").splitlines():
        if len(line) < 4:
            continue
        xy, path = line[:2], line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ")[-1].strip()
        path = path.strip('"')
        is_new = xy.strip() == "??" or "A" in xy
        result.append((is_new, path))
    return result


def is_substantive(path: str) -> bool:
    if os.path.basename(path) in SKIP_NAMES:
        return False
    for prefix in SKIP_PREFIXES:
        if path == prefix or path.startswith(prefix):
            return False
    return True


def determine_type(changes: list[tuple[bool, str]]) -> str:
    for is_new, path in changes:
        if is_new and re.match(r"star-alliance-skills/[^/]+/SKILL\.md$", path):
            return "skill-create"
    for is_new, path in changes:
        if is_new and re.match(r"star-alliance-members/[^/]+\.md$", path):
            return "member-create"
    for _, path in changes:
        if path == "workflows.json":
            return "workflow"
    return "upgrade"


def brief_summary(changes: list[tuple[bool, str]]) -> str:
    paths = [p for _, p in changes[:3]]
    rest = len(changes) - 3
    s = ", ".join(paths)
    if rest > 0:
        s += f" (+{rest} more)"
    return s


def main() -> int:
    state = REPO / ".claude" / "state"

    # Kill switches
    if (REPO / "evolution" / "DISARMED").exists():
        return 0
    if (state / "version-bumped").exists():
        return 0

    guild_log = REPO / "data" / "guild-log.json"
    if not guild_log.exists():
        return 0

    # Last workflow name for richer entry titles
    last_wf = ""
    try:
        last_wf = (state / "last-workflow").read_text().strip()
    except Exception:
        pass

    all_changes = changed_files()
    substantive = [(n, p) for n, p in all_changes if is_substantive(p)]
    if not substantive:
        return 0

    entry_type = determine_type(substantive)
    summary = brief_summary(substantive)
    title = f"{last_wf}: {summary}" if last_wf else f"auto-upgrade: {summary}"

    try:
        data = json.loads(guild_log.read_text(encoding="utf-8"))
        data.setdefault("entries", []).append({
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "type": entry_type,
            "title": title,
            "who": "quartermaster-auto",
            "commit": "",
        })
        guild_log.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        # Signal turn-finalize.sh to rebuild so the version is reflected immediately
        state.mkdir(parents=True, exist_ok=True)
        (state / "build-pending").write_text("1")
        # Sentinel: don't run twice in one turn
        (state / "version-bumped").write_text("1")

        print(f"[version-auto-bump] {entry_type!r} entry appended → version bumps on rebuild")
    except Exception as exc:
        sys.stderr.write(f"[version-auto-bump] ERROR: {exc}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
