#!/usr/bin/env python3
"""skillsmith — reconcile the star-alliance repo with the on-device copies.

Three locations hold skills:
  repo     ~/Documents/Claude/Projects/star-alliance        (distribution source, git)
  global   ~/.claude/skills                                 (what /<skill> actually loads)
  project  <cwd>/.claude/skills                              (per-project overrides)

This script reads the top-level frontmatter `version:` in each copy, compares them,
and tells you which way to sync. It NEVER edits frontmatter; `apply` only mirrors whole
skill directories with rsync for the clean "one side is a strictly newer version" case.

Subcommands:
  status                    per-skill version across all three locations (read-only)
  plan                      actionable recommendation per skill (read-only)
  apply --skill NAME        mirror the newer-versioned copy for ONE skill (repo<->global)
        [--direction install|push]   install = repo→global, push = global→repo
        [--dry]                       print the rsync command, don't run it

Direction is inferred from the versions unless --direction is given. Forks and externals
(see EXCEPTIONS) are never auto-applied — they print a manual note instead.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Skills whose repo copy intentionally DIVERGES from the device copy — never blind-sync.
# (See references/sync-playbook.md.)
EXCEPTIONS = {
    "cleanup": "repo is a slim Cowork stub; device is the full monolith — sync guts only",
    "conquering-campaign": "repo is the Cowork-packaged edition (lean desc); device keeps the rich canonical",
    "impeccable": "external — refresh via `npx impeccable`, never blind-overwrite",
}

RSYNC_EXCLUDES = ["--exclude", ".git", "--exclude", "__pycache__", "--exclude", "*.pyc"]

# member_slug → installed profile folder name. Mirrors tools/publish_profiles.py so the
# profile name on disk matches the profile the member runs under. Keep in sync if slugs change.
PROFILE_MAP = {
    "the-architect":     "architect",
    "the-developer":     "developer",
    "the-designer":      "designer",
    "the-interpreter":   "interpreter",
    "the-herald":        "herald",
    "the-merchant":      "merchant",
    "the-quartermaster": "quartermaster",
}


def default_repo() -> Path:
    """Resolve the star-alliance repo regardless of cwd / install location (the global
    copy's parents[2] is ~/.claude/skills, which would make --repo == --global)."""
    env = os.environ.get("STAR_ALLIANCE_REPO")
    if env:
        return Path(env).expanduser()
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / "VERSIONS.md").exists() and (anc / ".git").exists():
            return anc
    known = Path.home() / "Documents" / "Claude" / "Projects" / "star-alliance"
    if (known / "VERSIONS.md").exists():
        return known
    return here.parents[2]


def discover_skills_root(anchor: Path) -> Path:
    """Layout-aware skills-root discovery. The repo restructure (2026-06) moved skill dirs from
    the repo TOP LEVEL into `star-alliance-skills/`. The "repo" side of the sync is a skills base
    (`repo/<name>/SKILL.md`), so it must point at wherever the skills actually live — probe known
    layouts and return the first dir holding >=1 `*/SKILL.md`; fall back to `anchor`."""
    for c in (anchor, anchor / "star-alliance-skills", anchor / "claude-skills"):
        if c.is_dir() and any(
            d.is_dir() and not d.name.startswith(".") and (d / "SKILL.md").exists()
            for d in c.iterdir()
        ):
            return c
    return anchor


def ver_of(skill_md: Path) -> str | None:
    """Canonical version = metadata.version (spec-clean); top-level version: is the
    fallback for un-migrated externals (e.g. impeccable)."""
    if not skill_md.exists():
        return None
    parts = skill_md.read_text().split("---", 2)
    if len(parts) < 3:
        return None
    fm = parts[1]
    m = re.search(r"(?m)^metadata:\s*$", fm)
    if m:
        tail = fm[m.end():]
        block = re.match(r"((?:\n[ \t]+.*|\n[ \t]*)*)", tail)
        seg = block.group(0) if block else tail
        vm = re.search(r"(?m)^[ \t]+version:\s*(.+)$", seg)
        if vm:
            return vm.group(1).strip().strip('"').strip("'")
    tm = re.search(r"(?m)^version:\s*(.+)$", fm)
    return tm.group(1).strip().strip('"').strip("'") if tm else None


def vkey(v: str | None):
    """SemVer-ish sort key; non-numeric segments fall back to (−1,) so they sort low."""
    if not v:
        return (-1,)
    parts = []
    for seg in v.split("."):
        m = re.match(r"(\d+)", seg)
        parts.append(int(m.group(1)) if m else -1)
    return tuple(parts)


import hashlib as _hashlib

def fingerprint_dir(d):
    """Content hash of a skill directory: sha256 over path+bytes of every non-dotfile,
    non-.pyc file, sorted. Identical algorithm to .claude/tools/skill_fingerprint.py so
    hashes match that manifest; kept as a local helper (not imported) to avoid a
    cross-tree import dependency from skillsmith/scripts/ into .claude/tools/."""
    if not d.exists():
        return None
    h = _hashlib.sha256()
    for root, _dirs, files in __import__("os").walk(d):
        for fn in sorted(files):
            if fn.startswith(".") or fn.endswith((".pyc",)):
                continue
            fp = __import__("os").path.join(root, fn)
            rel = __import__("os").path.relpath(fp, d)
            h.update(b"\0" + rel.encode())
            try:
                with open(fp, "rb") as fh:
                    h.update(fh.read())
            except OSError:
                pass
    return h.hexdigest()[:16]


def locations(repo: Path, glob: Path, proj: Path | None):
    locs = [("repo", repo), ("global", glob)]
    if proj and proj.exists():
        locs.append(("project", proj))
    return locs


def all_names(locs):
    names = set()
    for _, base in locs:
        if base.exists():
            for d in base.iterdir():
                if d.is_dir() and not d.name.startswith(".") and (d / "SKILL.md").exists():
                    names.add(d.name)
    return sorted(names)


def cmd_status(locs):
    cols = [t for t, _ in locs]
    print(f"{'SKILL':32} " + " ".join(f"{c:>9}" for c in cols))
    print("-" * (33 + 10 * len(cols)))
    for n in all_names(locs):
        vers = [ver_of(base / n / "SKILL.md") or "—" for _, base in locs]
        print(f"{n:32} " + " ".join(f"{v:>9}" for v in vers))


def present(base: Path, n: str) -> bool:
    return (base / n / "SKILL.md").exists()


def recommend(n, repo, glob, repo_p, glob_p, repo_dir=None, glob_dir=None):
    """repo/glob = versions (may be None); repo_p/glob_p = directory present?;
    repo_dir/glob_dir = Path to the skill directory on each side, used ONLY for the
    equal-version content-hash check below (exceptions are never hash-checked)."""
    if n in EXCEPTIONS:
        return ("FORK", EXCEPTIONS[n])
    if repo_p and not glob_p:
        return ("INSTALL", f"in repo ({repo or 'unversioned'}) but absent on device → install repo→global")
    if glob_p and not repo_p:
        return ("ADD-TO-REPO", f"on device ({glob or 'unversioned'}) but absent in repo → add it to the repo")
    # present in both
    if repo and not glob:
        return ("STAMP", f"device copy is unversioned; repo is {repo} → install repo→global to carry the version stamp")
    if glob and not repo:
        return ("ADD-TO-REPO", f"repo copy is unversioned; device is {glob} → version the repo copy")
    rk, gk = vkey(repo), vkey(glob)
    if rk > gk:
        return ("INSTALL", f"repo {repo} > global {glob} → install repo→global")
    if gk > rk:
        return ("PUSH", f"global {glob} > repo {repo} → review + push global→repo (upgrade flow)")
    # equal version — check content hash before declaring OK
    if repo_dir is not None and glob_dir is not None:
        rh, gh = fingerprint_dir(repo_dir), fingerprint_dir(glob_dir)
        if rh is not None and gh is not None and rh != gh:
            return ("DRIFT", f"same version {repo or 'unversioned'} but bytes differ (repo={rh} global={gh}) → content drift, review + resync")
    return ("OK", f"in sync at {repo or 'unversioned'}")


def cmd_plan(locs):
    names = all_names(locs)
    repo_base = dict(locs).get("repo")
    glob_base = dict(locs).get("global")
    buckets = {}
    for n in names:
        tag, msg = recommend(
            n,
            ver_of(repo_base / n / "SKILL.md") if repo_base else None,
            ver_of(glob_base / n / "SKILL.md") if glob_base else None,
            present(repo_base, n) if repo_base else False,
            present(glob_base, n) if glob_base else False,
            repo_dir=(repo_base / n) if repo_base else None,
            glob_dir=(glob_base / n) if glob_base else None,
        )
        buckets.setdefault(tag, []).append((n, msg))
    order = ["INSTALL", "STAMP", "PUSH", "DRIFT", "ADD-TO-REPO", "FORK", "OK"]
    for tag in order:
        if tag not in buckets:
            continue
        print(f"\n## {tag} ({len(buckets[tag])})")
        for n, msg in buckets[tag]:
            print(f"  {n:32} {msg}")


def cmd_apply(repo, glob, name, direction, dry):
    if name in EXCEPTIONS:
        print(f"SKIP {name}: {EXCEPTIONS[name]} (manual — see references/sync-playbook.md)")
        return 1
    rv, gv = ver_of(repo / name / "SKILL.md"), ver_of(glob / name / "SKILL.md")
    if not direction:
        if vkey(rv) > vkey(gv):
            direction = "install"
        elif vkey(gv) > vkey(rv):
            direction = "push"
        else:
            print(f"{name}: same version ({rv}) in repo and global — nothing to apply (use --direction to force)")
            return 0
    if direction == "install":
        src, dst, why = repo / name, glob / name, f"repo {rv} → global"
    else:
        src, dst, why = glob / name, repo / name, f"global {gv} → repo"
    if not src.exists():
        print(f"source missing: {src}", file=sys.stderr)
        return 2
    cmd = ["rsync", "-a", "--delete", *RSYNC_EXCLUDES, f"{src}/", f"{dst}/"]
    print(f"{name}: {why}\n  {' '.join(cmd)}")
    if dry:
        print("  (dry-run — not executed)")
        return 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(cmd)
    if r.returncode == 0:
        print(f"  ✓ applied. New {('global' if direction=='install' else 'repo')} version: "
              f"{ver_of(dst / 'SKILL.md')}")
    return r.returncode


def _member_skills_from_json(repo: Path, member_id: str) -> list[str] | None:
    """Pull a member's `skills:` list out of guild-data.json (members[].skills). Returns
    None if the JSON isn't reachable or the member isn't present — caller falls back."""
    gd = repo / "guild-data.json"
    if not gd.exists():
        return None
    try:
        data = json.loads(gd.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    for m in data.get("members", []) or []:
        if m.get("id") == member_id:
            return [str(s) for s in (m.get("skills") or [])]
    return None


def _member_skills_from_md(md_path: Path) -> list[str]:
    """Pull a member's `skills:` array out of star-alliance-members/<id>.md YAML frontmatter.
    Skills are listed inline: `skills: [a, b, c]`."""
    if not md_path.exists():
        return []
    text = md_path.read_text()
    parts = text.split("---", 2)
    if len(parts) < 3:
        return []
    fm = parts[1]
    m = re.search(r"(?m)^skills:\s*\[(.*)\]\s*$", fm)
    if not m:
        # Could be multi-line YAML list — handle `skills:\n  - foo\n  - bar` too.
        out: list[str] = []
        if re.search(r"(?m)^skills:\s*$", fm):
            for line in fm.splitlines()[1:]:
                mm = re.match(r"\s*-\s*(.+?)\s*$", line)
                if not mm:
                    break
                out.append(mm.group(1).strip().strip('"').strip("'"))
        return out
    raw = m.group(1)
    return [s.strip().strip('"').strip("'") for s in raw.split(",") if s.strip()]


def cmd_profile_content(repo: Path, members_dir: Path | None, dry: bool) -> int:
    """For each member in PROFILE_MAP, mirror that member's skills from
    <repo>/star-alliance-skills/<id>/ into ~/.hermes/profiles/<slug>/skills/<id>/ using
    rsync -a --delete (byte-faithful — never re-encodes; PNGs containing JPEG bytes survive).

    Skill roster is read from guild-data.json:members[].skills; if that's missing or the
    member isn't there, falls back to star-alliance-members/<id>.md YAML frontmatter.

    Idempotent: rsync -a --delete makes a second run a no-op for matching content. The
    output of `rsync --stats` is captured so the log shows what changed (works on both
    modern rsync 3.1+ and the older 2.6.x that ships with macOS)."""
    skills_base = repo / "star-alliance-skills"
    if not skills_base.is_dir():
        print(f"ERROR: skills base not found at {skills_base}", file=sys.stderr)
        return 2

    # member_id → [skill_id, ...]
    rosters: dict[str, list[str]] = {}
    for member_id in PROFILE_MAP:
        from_json = _member_skills_from_json(repo, member_id)
        if from_json is not None:
            rosters[member_id] = from_json
            continue
        md_path = (members_dir / f"{member_id}.md") if members_dir else None
        if md_path is None:
            # Last resort: probe the canonical repo location.
            md_path = repo / "star-alliance-members" / f"{member_id}.md"
        rosters[member_id] = _member_skills_from_md(md_path)

    any_fail = False
    total_copied = 0
    total_skipped = 0
    for member_id, profile_slug in PROFILE_MAP.items():
        skills = rosters.get(member_id, [])
        if not skills:
            print(f"  - {member_id:20s} no skills found (json+md both empty) — skipped")
            total_skipped += 1
            continue
        dest_root = Path.home() / ".hermes" / "profiles" / member_id / "skills"
        for sid in skills:
            src = skills_base / sid
            dst = dest_root / sid
            if not src.is_dir():
                print(f"  ✗ {member_id} → {sid:32s} source missing: {src}", file=sys.stderr)
                any_fail = True
                continue
            if not (src / "SKILL.md").exists():
                print(f"  ✗ {member_id} → {sid:32s} no SKILL.md at {src} (not a skill?)", file=sys.stderr)
                any_fail = True
                continue
            cmd = [
                "rsync", "-a", "--delete", "--stats",
                *RSYNC_EXCLUDES,
                f"{src}/", f"{dst}/",
            ]
            ver = ver_of(src / "SKILL.md") or "—"
            if dry:
                print(f"  ~ {member_id} → {profile_slug}/{sid:30s} ({ver}) (dry-run)")
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            r = subprocess.run(cmd, capture_output=True, text=True)
            # rsync --stats prints "Number of files transferred: N" (and on 3.1+ also
            # "Number of regular files transferred: N"). On macOS-bundled rsync 2.6.x the
            # stats land on stdout; on 3.1+ they land on stderr. Scan both.
            transferred = "—"
            for stream in (r.stdout, r.stderr):
                for line in (stream or "").splitlines():
                    m = re.search(r"Number of (?:regular )?files transferred:\s*([\d,]+)", line)
                    if m:
                        transferred = m.group(1).replace(",", "")
                        break
                if transferred != "—":
                    break
            status = "✓" if r.returncode == 0 else "✗"
            print(f"  {status} {member_id} → {profile_slug}/{sid:30s} ({ver}) "
                  f"files_transferred={transferred}")
            if r.returncode != 0:
                any_fail = True
            else:
                total_copied += 1
    print()
    print(f"profile-content summary: copied={total_copied}, skipped={total_skipped}, "
          f"errors={1 if any_fail else 0}")
    return 1 if any_fail else 0


def main():
    ap = argparse.ArgumentParser(description="skillsmith repo↔device sync")
    ap.add_argument("cmd", choices=["status", "plan", "apply"])
    ap.add_argument("--repo", type=Path, default=default_repo())
    ap.add_argument("--global", dest="glob", type=Path, default=Path.home() / ".claude" / "skills")
    ap.add_argument("--project", type=Path, default=Path.cwd() / ".claude" / "skills")
    ap.add_argument("--skill", help="skill name (required for apply)")
    ap.add_argument("--direction", choices=["install", "push"])
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--profile-content", action="store_true",
                    help="mirror each member's skills from star-alliance-skills/ into the "
                         "matching ~/.hermes/profiles/<slug>/skills/. Pairs with apply.")
    ap.add_argument("--members-dir", type=Path,
                    help="override location of star-alliance-members/*.md "
                         "(fallback roster when guild-data.json is unavailable)")
    a = ap.parse_args()
    repo, glob = a.repo.expanduser().resolve(), a.glob.expanduser().resolve()
    repo = discover_skills_root(repo)   # repo side is a skills base; point it at where skills live
    # For --profile-content the `repo` we want is the *project* root (guild-data.json lives there,
    # not inside star-alliance-skills/). Recompute from the original argument.
    project_root = a.repo.expanduser().resolve()
    locs = locations(repo, glob, a.project.expanduser())
    if a.cmd == "status":
        cmd_status(locs)
        return 0
    if a.cmd == "plan":
        cmd_plan(locs)
        return 0
    if a.cmd == "apply":
        if not a.profile_content and not a.skill:
            print("apply requires --skill NAME (or --profile-content to sync member skill rosters)",
                  file=sys.stderr)
            return 2
        if a.profile_content:
            return cmd_profile_content(project_root, a.members_dir, a.dry)
        return cmd_apply(repo, glob, a.skill, a.direction, a.dry)


if __name__ == "__main__":
    sys.exit(main())
