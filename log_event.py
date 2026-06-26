#!/usr/bin/env python3
"""Append a single event to guild-log.json.

Manual entry point for log items that can't be auto-derived from git
(skill/member creation, dashboard redesigns, structural reorganisations,
anything that isn't a version bump).

Usage:
    python3 log_event.py --type skill-upgrade --title "..." --detail "..."
    python3 log_event.py --type member-upgrade --title "..." --who the-architect

Types:
    skill-upgrade    a skill's metadata.version was bumped
    skill-create     a new skill was added to star-alliance-skills/
    skill-remove     a skill was removed
    member-upgrade   a member's prompt or skills list was updated
    member-create    a new agent file was added to star-alliance-members/
    member-remove    an agent file was removed
    dashboard        visual / structural change to the dashboard
    structure        repo reorganisation (folder moves, renames)
    chore            anything else worth logging
    decision         a choice made + WHY — kept as a record for future runs,
                     not a change to the project (does not bump the version)

The script auto-stamps `date` to today (YYYY-MM-DD), assigns the next `id`,
and preserves all existing entries — never overwrites.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path


VALID_TYPES = {
    "skill-upgrade", "skill-create", "skill-remove",
    "member-upgrade", "member-create", "member-remove",
    "dashboard", "structure", "chore", "decision",
}


def default_repo() -> Path:
    env = os.environ.get("STAR_ALLIANCE_REPO")
    if env:
        return Path(env).expanduser()
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / "VERSIONS.md").exists() and (anc / ".git").exists():
            return anc
    return here.parent


def load_log(repo: Path) -> dict:
    p = repo / "guild-log.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"version": 1, "entries": []}


def save_log(repo: Path, log: dict) -> None:
    p = repo / "guild-log.json"
    p.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")


def next_id(entries: list[dict]) -> int:
    return (max((e["id"] for e in entries if "id" in e), default=0)) + 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Append an event to guild-log.json")
    ap.add_argument("--type", required=True, choices=sorted(VALID_TYPES),
                    help="Event type")
    ap.add_argument("--title", required=True, help="One-line headline")
    ap.add_argument("--detail", default="", help="Optional longer description")
    ap.add_argument("--who", default="Atta",
                    help="Who did it (member name or 'Atta'). Default: Atta")
    ap.add_argument("--ref", action="append", default=[],
                    help="Related entity name (skill or member). Repeatable.")
    ap.add_argument("--from-ver", default="", help="For upgrades: old version")
    ap.add_argument("--to-ver", default="", help="For upgrades: new version")
    ap.add_argument("--commit", default="", help="Git commit hash if known")
    ap.add_argument("--repo", type=Path, default=default_repo())
    args = ap.parse_args()

    repo = args.repo.expanduser().resolve()
    log = load_log(repo)

    entry = {
        "id": next_id(log["entries"]),
        "date": date.today().isoformat(),
        "type": args.type,
        "title": args.title.strip(),
        "who": args.who.strip(),
    }
    if args.detail:
        entry["detail"] = args.detail.strip()
    if args.ref:
        entry["ref"] = args.ref
    if args.from_ver:
        entry["from"] = args.from_ver
    if args.to_ver:
        entry["to"] = args.to_ver
    if args.commit:
        entry["commit"] = args.commit

    log["entries"].insert(0, entry)  # newest first
    save_log(repo, log)

    print(f"Logged #{entry['id']} [{entry['type']}] {entry['title']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
