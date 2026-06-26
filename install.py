#!/usr/bin/env python3
"""install.py — install the WHOLE Star Alliance harness into a project's .claude/.

The harness = skills + members (agents) + arsenal (model-offload CLIs), driven by
`domains.json`. skillsmith syncs SKILLS only; this installs the whole guild as one
unit and can be re-run to update.

Usage:
  # Install the domain matching a project path (auto-detected), copy mode:
  python3 install.py --to "/path/to/project"

  # Install a specific domain by id:
  python3 install.py --to "/path/to/project" --domain lex-council-app

  # Install EVERYTHING (all members + all skills):
  python3 install.py --to "/path/to/project" --all

  # Live-dev on THIS machine — symlink instead of copy so repo edits are instant:
  python3 install.py --to "/path/to/project" --dev --all

  # Also mirror the installed skills into ~/.claude/skills (global load path):
  python3 install.py --to "/path/to/project" --all --global

  # Inspect / remove:
  python3 install.py status     --to "/path/to/project"
  python3 install.py uninstall  --to "/path/to/project"   [--dry-run]

Modes:
  --release (default)  copy + version stamp. Portable to other machines.
  --dev                symlink skills/members/arsenal back to the repo (live edits);
                       silently falls back to copy if a symlink can't be made.

Lands in <project>/.claude/:
  agents/<member>.md            the domain's guild members (Claude Code agents)
  skills/<skill>/...            union of those members' skills + the domain's skills
  arsenal/{summon,minimax,ollama_cloud}.py + models-usage.json
  settings.json                 MERGED — adds arsenal run-permissions, never clobbers
  .harness-version.json         stamp + manifest of everything installed

Stdlib only. Honors skillsmith's EXCEPTIONS (fork/external skills copied without
--delete so a project's diverged fork is never blown away).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# --- reuse skillsmith's battle-tested bits (single source of truth) -------------
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE / "star-alliance-skills" / "skillsmith" / "scripts"))
try:
    import skill_sync  # type: ignore
    EXCEPTIONS = skill_sync.EXCEPTIONS
    RSYNC_EXCLUDES = skill_sync.RSYNC_EXCLUDES
    ver_of = skill_sync.ver_of
except Exception:  # keep install.py usable even if skillsmith moves
    EXCEPTIONS = {}
    RSYNC_EXCLUDES = ["--exclude", ".git", "--exclude", "__pycache__", "--exclude", "*.pyc"]
    def ver_of(_p):  # type: ignore
        return None

ARSENAL_FILES = ["summon.py", "minimax.py", "ollama_cloud.py", "models-usage.json"]
ARSENAL_PERMS = [
    "Bash(python3 .claude/arsenal/summon.py:*)",
    "Bash(python3 .claude/arsenal/minimax.py:*)",
    "Bash(python3 .claude/arsenal/ollama_cloud.py:*)",
]


# --- small fs helpers -----------------------------------------------------------
def rm_path(p: Path) -> None:
    if p.is_symlink() or p.is_file():
        p.unlink()
    elif p.is_dir():
        shutil.rmtree(p)


def link_or_copy(src: Path, dst: Path, dev: bool, is_dir: bool) -> str:
    """Return 'symlink' or 'copy' depending on mode + success. Falls back to copy."""
    rm_path(dst)
    if dev:
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.symlink_to(src, target_is_directory=is_dir)
            return "symlink"
        except OSError:
            pass  # fall through to copy
    if is_dir:
        # rsync gives us EXCEPTIONS-aware --delete control; mkdir first.
        dst.mkdir(parents=True, exist_ok=True)
        delete = [] if dst.name in EXCEPTIONS else ["--delete"]
        subprocess.run(["rsync", "-a", *delete, *RSYNC_EXCLUDES, f"{src}/", f"{dst}/"], check=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return "copy"


# --- domains.json + the install set --------------------------------------------
def load_domains(repo: Path) -> list:
    return json.loads((repo / "domains.json").read_text()).get("domains", [])


def norm(p) -> Path:
    return Path(str(p)).expanduser().resolve()


def pick_domain(domains: list, domain_id: str | None, to_path: Path):
    if domain_id:
        for d in domains:
            if d["id"] == domain_id:
                return d
        ids = ", ".join(d["id"] for d in domains)
        sys.exit(f"install: unknown --domain '{domain_id}'. Known: {ids}")
    t = norm(to_path)
    for d in domains:
        if d.get("path") and norm(d["path"]) == t:
            return d
    return None


def parse_member_skills(md: Path) -> list:
    """Pull the informational skills:[...] list from a member's frontmatter."""
    if not md.exists():
        return []
    parts = md.read_text().split("---", 2)
    fm = parts[1] if len(parts) >= 3 else ""
    m = re.search(r"(?m)^skills:\s*\[(.*?)\]", fm, re.DOTALL)
    if not m:
        return []
    return [s.strip().strip('"').strip("'") for s in m.group(1).split(",") if s.strip()]


def resolve_set(repo: Path, domain, want_all: bool):
    skills_src = repo / "star-alliance-skills"
    members_src = repo / "star-alliance-members"
    all_skills = {d.name for d in skills_src.iterdir() if (d / "SKILL.md").exists()} if skills_src.exists() else set()
    all_members = {f.stem for f in members_src.glob("*.md") if f.stem != "README"} if members_src.exists() else set()

    if want_all or domain is None:
        return sorted(all_members), sorted(all_skills), [], []

    wanted_m = domain.get("members", [])
    members = sorted(m for m in wanted_m if m in all_members)
    missing_members = [m for m in wanted_m if m not in all_members]

    skills = set(domain.get("skills", []))
    for m in members:
        skills |= set(parse_member_skills(members_src / f"{m}.md"))
    declared = set(domain.get("skills", []))
    missing_skills = sorted(declared - all_skills)
    skills = sorted(s for s in skills if s in all_skills)
    return members, skills, missing_members, missing_skills


# --- settings.json merge (additive, never clobber) ------------------------------
def merge_settings(claude_dir: Path, dry: bool) -> list:
    sp = claude_dir / "settings.json"
    cur = json.loads(sp.read_text()) if sp.exists() else {}
    allow = cur.setdefault("permissions", {}).setdefault("allow", [])
    added = [p for p in ARSENAL_PERMS if p not in allow]
    if not added:
        return []
    allow.extend(added)
    allow.sort()
    if not dry:
        if sp.exists():
            shutil.copy2(sp, claude_dir / "settings.json.bak")
        sp.write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n")
    return added


# --- stamp ----------------------------------------------------------------------
def git_sha(repo: Path) -> str | None:
    try:
        r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True)
        return r.stdout.strip() or None
    except Exception:
        return None


def harness_version(repo: Path) -> str:
    try:
        return json.loads((repo / "harness.json").read_text()).get("harness_version", "0.0.0")
    except Exception:
        return "0.0.0"


# --- commands -------------------------------------------------------------------
def do_install(repo: Path, to: Path, domain, want_all, dev, do_global, dry, no_settings):
    members, skills, miss_m, miss_s = resolve_set(repo, domain, want_all)
    skills_src = repo / "star-alliance-skills"
    members_src = repo / "star-alliance-members"
    arsenal_src = repo / "star-alliance-arsenal"
    claude = to / ".claude"
    mode = "dev" if dev else "release"
    did_symlink = did_copy = False
    label = "WOULD INSTALL (dry-run)" if dry else "INSTALLING"
    dom_id = domain["id"] if domain else ("all" if want_all else "all (no domain match)")
    print(f"== {label} — Star Alliance {harness_version(repo)} [{mode}] → {to}")
    print(f"   domain: {dom_id}   members: {len(members)}   skills: {len(skills)}")
    if miss_m:
        print(f"   ! members in domain but not in roster (skipped): {', '.join(miss_m)}")
    if miss_s:
        print(f"   ! skills in domain but not in repo (skipped): {', '.join(miss_s)}")

    if dry:
        print(f"   agents → {claude/'agents'}")
        print(f"   skills → {claude/'skills'}  ({', '.join(skills)})")
        print(f"   arsenal → {claude/'arsenal'}")
        if not no_settings:
            print(f"   settings.json += {len(ARSENAL_PERMS)} arsenal perms (union, backed up)")
        return 0

    # members → agents/
    for m in members:
        how = link_or_copy(members_src / f"{m}.md", claude / "agents" / f"{m}.md", dev, is_dir=False)
        did_symlink |= how == "symlink"; did_copy |= how == "copy"
    # skills → skills/
    for s in skills:
        how = link_or_copy(skills_src / s, claude / "skills" / s, dev, is_dir=True)
        did_symlink |= how == "symlink"; did_copy |= how == "copy"
        if s in EXCEPTIONS and how == "copy":
            print(f"   ~ {s}: fork/external — copied without --delete ({EXCEPTIONS[s]})")
    # arsenal → arsenal/
    if dev:
        how = link_or_copy(arsenal_src, claude / "arsenal", dev=True, is_dir=True)
        did_symlink |= how == "symlink"; did_copy |= how == "copy"
        arsenal_installed = ARSENAL_FILES if how == "copy" else ["(symlinked dir)"]
    else:
        (claude / "arsenal").mkdir(parents=True, exist_ok=True)
        arsenal_installed = []
        for f in ARSENAL_FILES:
            if (arsenal_src / f).exists():
                shutil.copy2(arsenal_src / f, claude / "arsenal" / f)
                arsenal_installed.append(f)
        did_copy = True

    added = [] if no_settings else merge_settings(claude, dry=False)

    if do_global:
        gskills = Path.home() / ".claude" / "skills"
        for s in skills:
            delete = [] if s in EXCEPTIONS else ["--delete"]
            (gskills / s).mkdir(parents=True, exist_ok=True)
            subprocess.run(["rsync", "-a", *delete, *RSYNC_EXCLUDES,
                            f"{skills_src / s}/", f"{gskills / s}/"], check=True)
        print(f"   ✓ also mirrored {len(skills)} skills → {gskills}")

    stamp = {
        "harness_version": harness_version(repo),
        "source_sha": git_sha(repo),
        "source_repo": str(repo),
        "mode": mode,
        "domain": dom_id,
        "installed": {
            "agents": [f"{m}.md" for m in members],
            "skills": skills,
            "arsenal": arsenal_installed,
        },
        "settings_added": added,
    }
    (claude / ".harness-version.json").write_text(json.dumps(stamp, indent=2, ensure_ascii=False) + "\n")

    print(f"   ✓ agents: {len(members)}   skills: {len(skills)} ({'symlinked' if dev and did_symlink else 'copied'})"
          f"   arsenal: {len(arsenal_installed)} item(s)")
    if dev and did_copy and did_symlink:
        print("   ! some items fell back to copy (symlink not permitted on this target)")
    if added:
        print(f"   ✓ settings.json: +{len(added)} arsenal perm(s) (backup: settings.json.bak)")
    print(f"   ✓ stamp: {claude/'.harness-version.json'}")
    return 0


def do_status(to: Path):
    claude = to / ".claude"
    sp = claude / ".harness-version.json"
    if not sp.exists():
        print(f"no harness installed at {to} (no .claude/.harness-version.json)")
        return 1
    st = json.loads(sp.read_text())
    print(f"Star Alliance {st.get('harness_version')} [{st.get('mode')}] sha={st.get('source_sha')}")
    print(f"  domain: {st.get('domain')}")
    inst = st.get("installed", {})
    print(f"  agents:  {len(inst.get('agents', []))}")
    print(f"  skills:  {len(inst.get('skills', []))}")
    print(f"  arsenal: {len(inst.get('arsenal', []))}")
    for d in ("agents", "skills", "arsenal"):
        live = claude / d
        n = len(list(live.iterdir())) if live.exists() else 0
        print(f"  on disk {d}/: {n}")
    return 0


def do_uninstall(to: Path, dry: bool):
    claude = to / ".claude"
    sp = claude / ".harness-version.json"
    if not sp.exists():
        print(f"nothing to uninstall at {to}")
        return 1
    st = json.loads(sp.read_text())
    inst = st.get("installed", {})
    tag = "WOULD REMOVE (dry-run)" if dry else "REMOVING"
    print(f"== {tag} harness from {to}")
    for a in inst.get("agents", []):
        p = claude / "agents" / a
        print(f"   - agents/{a}")
        if not dry:
            rm_path(p)
    for s in inst.get("skills", []):
        p = claude / "skills" / s
        print(f"   - skills/{s}")
        if not dry:
            rm_path(p)
    print("   - arsenal/")
    if not dry:
        rm_path(claude / "arsenal")
    # un-merge only the perms we added
    added = st.get("settings_added", [])
    if added and (claude / "settings.json").exists():
        cur = json.loads((claude / "settings.json").read_text())
        allow = cur.get("permissions", {}).get("allow", [])
        kept = [p for p in allow if p not in added]
        print(f"   - settings.json: −{len(allow) - len(kept)} arsenal perm(s)")
        if not dry:
            cur["permissions"]["allow"] = kept
            (claude / "settings.json").write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n")
    if not dry:
        for d in ("agents", "skills", "arsenal"):
            dd = claude / d
            if dd.is_dir() and not any(dd.iterdir()):
                dd.rmdir()
        rm_path(sp)
    print("   ✓ done (your own files untouched)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Install the Star Alliance harness into a project.")
    ap.add_argument("cmd", nargs="?", default="install", choices=["install", "status", "uninstall"])
    ap.add_argument("--to", required=True, type=Path, help="target project directory")
    ap.add_argument("--domain", help="domain id from domains.json (else auto-detect by --to path)")
    ap.add_argument("--all", action="store_true", help="install every member + skill (ignore domain)")
    ap.add_argument("--dev", action="store_true", help="symlink instead of copy (live edits)")
    ap.add_argument("--release", action="store_true", help="copy + stamp (default)")
    ap.add_argument("--global", dest="do_global", action="store_true",
                    help="also mirror installed skills into ~/.claude/skills")
    ap.add_argument("--no-settings", action="store_true", help="don't touch settings.json")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.dev and a.release:
        sys.exit("install: choose one of --dev / --release")
    repo = _HERE
    to = a.to.expanduser().resolve()

    if a.cmd == "status":
        return do_status(to)
    if a.cmd == "uninstall":
        return do_uninstall(to, a.dry_run)

    if not to.exists():
        sys.exit(f"install: target does not exist: {to}")
    domains = load_domains(repo)
    domain = None if a.all else pick_domain(domains, a.domain, to)
    if domain is None and not a.all and not a.domain:
        print("install: no domain matched --to path; installing EVERYTHING. "
              "Use --domain <id> to scope, or --all to silence this.")
    return do_install(repo, to, domain, a.all, a.dev, a.do_global, a.dry_run, a.no_settings)


if __name__ == "__main__":
    sys.exit(main())
