#!/usr/bin/env python3
"""Auto-derive guild-log.json entries from git history.

Two passes:
  1. For each commit, scan the changed files and synthesise log entries
     (skill-upgrade when metadata.version changed, member-upgrade when an
     agent .md changed, etc.).
  2. Skip commits that already have a matching hand-edited entry (matched
     by commit hash) so we never double-log.

The script is idempotent — running it twice produces the same output.
It writes guild-log.json. Hand-edited entries with no commit link are kept.

Usage:
    python3 build_guild_log.py            # rebuild guild-log.json
    python3 build_guild_log.py --dry-run  # print what would be added
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def default_repo() -> Path:
    env = os.environ.get("STAR_ALLIANCE_ROOT") or os.environ.get("STAR_ALLIANCE_REPO")
    if env:
        return Path(env).expanduser()
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / "VERSIONS.md").exists() and (anc / ".git").exists():
            return anc
    return here.parent


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True, stderr=subprocess.STDOUT,
    )


def parse_porcelain(repo: Path, ref: str) -> tuple[str, list[str]]:
    """Return (subject, [filenames]) for a commit."""
    files = git(repo, "show", "--name-only", "--pretty=format:%s", ref).strip()
    parts = files.split("\n", 1)
    subject = parts[0].strip()
    fnames = [f.strip() for f in parts[1].strip().splitlines() if f.strip()] if len(parts) > 1 else []
    return subject, fnames


def is_skill_md(path: str) -> str | None:
    """Return the skill name if path is a SKILL.md inside a skill directory.

    Recognises both layouts:
      star-alliance-skills/<name>/SKILL.md  (current)
      <name>/SKILL.md                       (legacy flat layout)
    """
    m = re.match(r"^(?:star-alliance-skills/)?([^/]+)/SKILL\.md$", path)
    if not m:
        return None
    name = m.group(1)
    # Skip non-skill directories that happen to contain a SKILL.md
    if name in {"node_modules", ".git"}:
        return None
    return name


def is_member_md(path: str) -> str | None:
    """Return the member name if path is an agent .md file.

    Recognises both layouts:
      star-alliance-members/<name>.md  (current)
      members/<name>.md               (legacy)
    """
    m = re.match(r"^(?:star-alliance-members/|members/)([^/]+)\.md$", path)
    if not m:
        return None
    name = m.group(1)
    if name.lower() == "readme":
        return None  # skip the directory's own README
    return name


def is_dashboard_file(path: str) -> bool:
    """Return True if path is part of the dashboard surface."""
    return path in {
        "index.html", "app.css", "app.js",
        "build.py", "data/skills-meta.json", "data/members-meta.json",
        "data/domains.json", "guild-data.js", "guild-data.json",
    }


def extract_version_at(repo: Path, ref: str, skill_name: str) -> str | None:
    """Read metadata.version of a skill at a specific commit.

    Tries both layouts so we can read historical commits.
    """
    for rel in (f"star-alliance-skills/{skill_name}/SKILL.md", f"{skill_name}/SKILL.md"):
        try:
            text = git(repo, "show", f"{ref}:{rel}")
        except subprocess.CalledProcessError:
            continue
        m = re.search(r"(?m)^[ \t]+version:\s*(\S+)", text)
        return m.group(1) if m else None
    return None


def classify(repo: Path, ref: str, subject: str, files: list[str]) -> list[dict]:
    """Build derived log entries from a commit."""
    derived: list[dict] = []
    date = git(repo, "show", "-s", "--format=%cs", ref).strip()  # YYYY-MM-DD

    skills_changed: set[str] = set()
    members_changed: set[str] = set()
    structural = False
    dashboard = False

    for f in files:
        if (s := is_skill_md(f)):
            skills_changed.add(s)
        elif (m := is_member_md(f)):
            members_changed.add(m)
        elif is_dashboard_file(f):
            dashboard = True
        elif f in {"README.md", "VERSIONS.md"}:
            # Repo-meta changes; only log as structural if no skills/members changed
            pass
        elif f in {"members", "star-alliance-skills", "star-alliance-members",
                   "log_event.py", "build_guild_log.py", "data/guild-log.json"}:
            structural = True

    # Skill version bumps → skill-upgrade
    for s in sorted(skills_changed):
        new_v = extract_version_at(repo, ref, s)
        if not new_v:
            continue
        # Find previous version: walk parent commits until we see this skill
        prev_v: str | None = None
        try:
            parent_log = git(repo, "log", "--pretty=format:%H", "-n", "20", ref).strip().splitlines()
        except subprocess.CalledProcessError:
            parent_log = []
        for prev_ref in parent_log[1:]:
            prev_v = extract_version_at(repo, prev_ref.strip(), s)
            if prev_v and prev_v != new_v:
                break
            if prev_v == new_v:
                # Skill existed at same version → it was an edit, not a bump
                prev_v = None
                break
        if prev_v == new_v:
            continue  # no actual version change
        title = f"Upgrade {s} to {new_v}"
        if prev_v:
            title = f"Upgrade {s}: {prev_v} → {new_v}"
        derived.append({
            "date": date,
            "type": "skill-upgrade",
            "title": title,
            "who": _infer_who(subject),
            "ref": [s],
            "from": prev_v or "",
            "to": new_v,
            "commit": ref[:8],
            "_derived": True,
        })

    # New skill file (no parent version anywhere) → skill-create
    for s in sorted(skills_changed):
        # Walk parents — if NO parent had this skill at all, it's a create
        try:
            parent_log = git(repo, "log", "--pretty=format:%H", "-n", "50", ref).strip().splitlines()
        except subprocess.CalledProcessError:
            continue
        existed_before = False
        for prev_ref in parent_log[1:]:
            if extract_version_at(repo, prev_ref.strip(), s):
                existed_before = True
                break
        if not existed_before:
            derived.append({
                "date": date,
                "type": "skill-create",
                "title": f"Add skill: {s}",
                "who": _infer_who(subject),
                "ref": [s],
                "commit": ref[:8],
                "_derived": True,
            })

    # Member file changes
    for m in sorted(members_changed):
        # Detect create vs upgrade by checking parent (both layouts)
        existed_before = False
        try:
            parent_log = git(repo, "log", "--pretty=format:%H", "-n", "50", ref).strip().splitlines()
        except subprocess.CalledProcessError:
            parent_log = []
        for prev_ref in parent_log[1:]:
            for rel in (f"star-alliance-members/{m}.md", f"members/{m}.md"):
                try:
                    git(repo, "show", f"{prev_ref.strip()}:{rel}")
                    existed_before = True
                    break
                except subprocess.CalledProcessError:
                    continue
            if existed_before:
                break
        ttype = "member-upgrade" if existed_before else "member-create"
        title = f"Update member: {m}" if existed_before else f"Add member: {m}"
        derived.append({
            "date": date,
            "type": ttype,
            "title": title,
            "who": _infer_who(subject),
            "ref": [m],
            "commit": ref[:8],
            "_derived": True,
        })

    if dashboard:
        derived.append({
            "date": date,
            "type": "dashboard",
            "title": _strip_prefix(subject),
            "who": _infer_who(subject),
            "commit": ref[:8],
            "_derived": True,
        })

    if structural and not skills_changed and not members_changed and not dashboard:
        derived.append({
            "date": date,
            "type": "structure",
            "title": _strip_prefix(subject),
            "who": _infer_who(subject),
            "commit": ref[:8],
            "_derived": True,
        })

    return derived


def _strip_prefix(subject: str) -> str:
    """Drop the conventional-commit prefix for cleaner titles."""
    return re.sub(r"^(feat|fix|chore|refactor|style|docs|test)(\([^)]+\))?:\s*", "", subject).strip()


def _infer_who(subject: str) -> str:
    """Skillsmith routine commits start with 'skillsmith routine' → credit the skill."""
    if subject.lower().startswith("skillsmith routine"):
        return "skillsmith"
    return "Atta"


def load_log(repo: Path) -> dict:
    p = repo / "data/guild-log.json"
    if p.exists():
        return json.loads(p.read_text())
    return {"version": 1, "entries": []}


def save_log(repo: Path, log: dict) -> None:
    p = repo / "data/guild-log.json"
    p.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n")


def dedupe(entries: list[dict]) -> list[dict]:
    """Collapse noisy duplicates from squashed history.

    Rule: for the same (type, ref[0]) pair, keep only the earliest date.
    This is mainly for `skill-create` events that re-fire on every edit to an
    existing skill whose parent tree doesn't expose it at the right path.
    """
    seen: dict[tuple, dict] = {}
    for e in entries:
        ref = (e.get("ref") or [""])[0]
        key = (e["type"], ref)
        if key not in seen or e["date"] < seen[key]["date"]:
            seen[key] = e
    return list(seen.values())


def collapse_bulk(entries: list[dict], threshold: int = 5) -> list[dict]:
    """Collapse same-commit bulk events (e.g. a release that bumps 21 skills at once).

    If a single commit produces ≥ `threshold` entries of the same type, replace
    them with one summary entry. The summary preserves all ref names and the
    version transitions so the dashboard can show the full scope.
    """
    by_commit: dict[tuple, list[dict]] = {}
    passthrough: list[dict] = []
    for e in entries:
        c = e.get("commit", "")
        if not c or e["type"] in {"dashboard", "structure", "chore"}:
            passthrough.append(e)
            continue
        by_commit.setdefault((c, e["type"]), []).append(e)

    out: list[dict] = list(passthrough)
    for (commit, etype), group in by_commit.items():
        if len(group) < threshold:
            out.extend(group)
            continue
        # Bulk release: collapse to one summary entry
        names = sorted({(e.get("ref") or [""])[0] for e in group if e.get("ref")})
        title = f"Bulk {etype}: {len(group)} items updated"
        if etype == "skill-upgrade":
            title = f"Bulk skill upgrades: {len(group)} skills"
        elif etype == "skill-create":
            title = f"Bulk skill additions: {len(group)} skills"
        elif etype == "member-upgrade":
            title = f"Bulk member updates: {len(group)} members"
        elif etype == "member-create":
            title = f"Bulk member additions: {len(group)} members"
        summary = {
            "date": group[0]["date"],
            "type": etype,
            "title": title,
            "who": group[0].get("who", "Atta"),
            "ref": names,
            "commit": commit,
            "bulk": True,
            "_derived": True,
        }
        out.append(summary)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-derive guild-log.json from git history")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=80, help="Max commits to scan")
    ap.add_argument("--max-entries", type=int, default=60,
                    help="Cap on derived entries kept (most recent).")
    ap.add_argument("--repo", type=Path, default=default_repo())
    args = ap.parse_args()

    repo = args.repo.expanduser().resolve()
    log = load_log(repo)

    # Existing commits already logged (hand + derived)
    seen_commits = {e.get("commit") for e in log["entries"] if e.get("commit")}

    # Scan recent commits, oldest first so derived events land in chronological order
    log_out = git(repo, "log", "--pretty=format:%H", f"-n{args.limit}").strip().splitlines()
    log_out.reverse()

    new_entries: list[dict] = []
    for ref in log_out:
        ref = ref.strip()
        if ref[:8] in seen_commits:
            continue
        try:
            subject, files = parse_porcelain(repo, ref)
        except subprocess.CalledProcessError:
            continue
        if not files:
            continue
        derived = classify(repo, ref, subject, files)
        new_entries.extend(derived)

    if args.dry_run:
        collapsed = collapse_bulk(new_entries)
        deduped = dedupe(collapsed)
        deduped.sort(key=lambda e: e["date"], reverse=True)
        if len(deduped) > args.max_entries:
            deduped = deduped[: args.max_entries]
        print(f"Would add {len(new_entries)} raw → "
              f"{len(collapse_bulk(new_entries))} after bulk-collapse → "
              f"{len(deduped)} after dedupe:")
        for e in deduped:
            print(f"  [{e['date']}] {e['type']:14} {e['title']} ({e.get('commit','')})")
        return 0

    if new_entries:
        hand = [e for e in log["entries"] if not e.get("_derived")]
        all_derived = [e for e in log["entries"] if e.get("_derived")] + new_entries
        all_derived = dedupe(collapse_bulk(all_derived))
        all_derived.sort(key=lambda e: (e["date"], e.get("commit", "")), reverse=True)
        if len(all_derived) > args.max_entries:
            all_derived = all_derived[: args.max_entries]
        log["entries"] = hand + all_derived
        save_log(repo, log)
        print(f"Wrote {len(new_entries)} new raw → "
              f"{len(all_derived)} derived kept after collapse + dedupe. "
              f"Total: {len(log['entries'])} ({len(hand)} hand + {len(all_derived)} derived).")
    else:
        print(f"No new derived entries. Total stays at {len(log['entries'])}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
