#!/usr/bin/env python3
"""skillsmith — reconcile the claude-skills repo with the on-device copies.

Three locations hold skills:
  repo     ~/Documents/Claude/Projects/claude-skills        (distribution source, git)
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


def default_repo() -> Path:
    """Resolve the claude-skills repo regardless of cwd / install location (the global
    copy's parents[2] is ~/.claude/skills, which would make --repo == --global)."""
    env = os.environ.get("CLAUDE_SKILLS_REPO")
    if env:
        return Path(env).expanduser()
    here = Path(__file__).resolve()
    for anc in here.parents:
        if (anc / "VERSIONS.md").exists() and (anc / ".git").exists():
            return anc
    known = Path.home() / "Documents" / "Claude" / "Projects" / "claude-skills"
    if (known / "VERSIONS.md").exists():
        return known
    return here.parents[2]


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


def recommend(n, repo, glob, repo_p, glob_p):
    """repo/glob = versions (may be None); repo_p/glob_p = directory present?"""
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
        )
        buckets.setdefault(tag, []).append((n, msg))
    order = ["INSTALL", "STAMP", "PUSH", "ADD-TO-REPO", "FORK", "OK"]
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


def main():
    ap = argparse.ArgumentParser(description="skillsmith repo↔device sync")
    ap.add_argument("cmd", choices=["status", "plan", "apply"])
    ap.add_argument("--repo", type=Path, default=default_repo())
    ap.add_argument("--global", dest="glob", type=Path, default=Path.home() / ".claude" / "skills")
    ap.add_argument("--project", type=Path, default=Path.cwd() / ".claude" / "skills")
    ap.add_argument("--skill", help="skill name (required for apply)")
    ap.add_argument("--direction", choices=["install", "push"])
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    repo, glob = a.repo.expanduser().resolve(), a.glob.expanduser().resolve()
    locs = locations(repo, glob, a.project.expanduser())
    if a.cmd == "status":
        cmd_status(locs)
        return 0
    if a.cmd == "plan":
        cmd_plan(locs)
        return 0
    if a.cmd == "apply":
        if not a.skill:
            print("apply requires --skill NAME", file=sys.stderr)
            return 2
        return cmd_apply(repo, glob, a.skill, a.direction, a.dry)


if __name__ == "__main__":
    sys.exit(main())
