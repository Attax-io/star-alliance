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
# Repo root (walk up to the pinned VERSIONS.md + .git), so this works from tools/.
_HERE = next((p for p in Path(__file__).resolve().parents
              if (p / "VERSIONS.md").exists() and (p / ".git").exists()),
             Path(__file__).resolve().parent)
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

# --- the portable GATED HARNESS (--with-harness) -------------------------------
# The curated set that makes the Butler really route + spawn gated helpers in a
# TARGET project, speaking plain English. Deliberately EXCLUDES this repo's self
# machinery (build.py, the self-critic verify-gate, auto-commit turn-finalize,
# cost telemetry) — a target project owns its own build/commit/review flow.
HARNESS_HOOKS = [
    "sa-pretool.py", "workflow-gate.py", "high-alert.py", "okf-gate.py",
    "stop-line-gate.py", "weapon-gate.py", "destructive-gate.py", "turn-start.py",
    "plain-english-nudge.py", "workflow-banner-enforcer.py", "verify_hash.py",
    "guild-routing-gate.sh",
]
HARNESS_EVOLUTION = ["signals.py", "ledger.py"]   # high-alert/gates emit signals here
# data the gates read at runtime, copied to the target ROOT (paths the hooks expect)
HARNESS_ROOT_FILES = ["workflows.json", "guild-data.json"]


def harness_hooks_block() -> dict:
    """The curated settings.json hooks wiring for a target project. References
    $CLAUDE_PROJECT_DIR so it resolves against the TARGET, not this repo."""
    def cmd(rel):
        ext = "sh" if rel.endswith(".sh") else "py"
        runner = "sh" if ext == "sh" else "python3"
        return {"type": "command",
                "command": f'{runner} "$CLAUDE_PROJECT_DIR/.claude/hooks/{rel}"'}
    return {
        "UserPromptSubmit": [{"hooks": [cmd("guild-routing-gate.sh"), cmd("turn-start.py")]}],
        "PreToolUse": [{"matcher": "*", "hooks": [cmd("sa-pretool.py")]}],
        "Stop": [{"hooks": [cmd("plain-english-nudge.py"), cmd("workflow-banner-enforcer.py")]}],
    }


def install_harness(repo: Path, to: Path, dry: bool) -> dict:
    """Copy the gated-harness files into the target and wire (or print) settings.
    Returns a manifest dict for the stamp. Additive + idempotent."""
    claude = to / ".claude"
    landed = {"hooks": [], "evolution": [], "root_files": [], "arsenal": [],
              "settings_hooks": "skipped", "state_dir": False}
    if dry:
        print(f"   + harness hooks → {claude/'hooks'}  ({len(HARNESS_HOOKS)} files)")
        print(f"   + workflows.json + guild-data.json → {to}")
        print(f"   + star-alliance-arsenal/models.json → {to/'star-alliance-arsenal'}")
        print(f"   + evolution/ (signals.py, ledger.py, ledger.jsonl) → {to/'evolution'}")
        print(f"   + settings.json hooks wiring (UserPromptSubmit/PreToolUse/Stop) "
              f"+ STAR_ALLIANCE_ROOT, IF target has no hooks (else printed)")
        return landed

    # 1. hooks
    (claude / "hooks").mkdir(parents=True, exist_ok=True)
    for h in HARNESS_HOOKS:
        src = repo / ".claude" / "hooks" / h
        if src.exists():
            shutil.copy2(src, claude / "hooks" / h)
            landed["hooks"].append(h)
    # 2. evolution signal writer + a writable ledger
    (to / "evolution").mkdir(parents=True, exist_ok=True)
    for e in HARNESS_EVOLUTION:
        src = repo / "evolution" / e
        if src.exists():
            shutil.copy2(src, to / "evolution" / e)
            landed["evolution"].append(e)
    led = to / "evolution" / "ledger.jsonl"
    if not led.exists():
        led.write_text("")
    # 3. root data files the gates read
    for f in HARNESS_ROOT_FILES:
        src = repo / f
        if src.exists():
            shutil.copy2(src, to / f)
            landed["root_files"].append(f)
    # 4. models.json where weapon-gate looks: <root>/star-alliance-arsenal/models.json
    (to / "star-alliance-arsenal").mkdir(parents=True, exist_ok=True)
    msrc = repo / "star-alliance-arsenal" / "models.json"
    if msrc.exists():
        shutil.copy2(msrc, to / "star-alliance-arsenal" / "models.json")
        landed["arsenal"].append("models.json")
    # 5. state dir for per-turn sentinels
    (claude / "state").mkdir(parents=True, exist_ok=True)
    landed["state_dir"] = True
    # 6. settings.json hooks wiring — safe: only auto-wire if target has NO hooks
    sp = claude / "settings.json"
    cur = json.loads(sp.read_text()) if sp.exists() else {}
    block = harness_hooks_block()
    if not cur.get("hooks"):
        if sp.exists():
            shutil.copy2(sp, claude / "settings.json.bak")
        cur["hooks"] = block
        cur.setdefault("env", {})["STAR_ALLIANCE_ROOT"] = str(to)
        sp.write_text(json.dumps(cur, indent=2, ensure_ascii=False) + "\n")
        landed["settings_hooks"] = "wired"
    else:
        print("   ! target settings.json already has a 'hooks' block — NOT merged "
              "(would risk double-firing). Add these manually:")
        print(json.dumps({"hooks": block,
                          "env": {"STAR_ALLIANCE_ROOT": str(to)}}, indent=2))
        landed["settings_hooks"] = "manual"
    return landed
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
    return json.loads((repo / "data/domains.json").read_text()).get("domains", [])


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
        return json.loads((repo / "data/harness.json").read_text()).get("harness_version", "0.0.0")
    except Exception:
        return "0.0.0"


# --- commands -------------------------------------------------------------------
def do_install(repo: Path, to: Path, domain, want_all, dev, do_global, dry, no_settings,
               with_harness=False):
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
        if with_harness:
            install_harness(repo, to, dry=True)
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

    harness = install_harness(repo, to, dry=False) if with_harness else None

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
        "harness": harness,
    }
    (claude / ".harness-version.json").write_text(json.dumps(stamp, indent=2, ensure_ascii=False) + "\n")

    print(f"   ✓ agents: {len(members)}   skills: {len(skills)} ({'symlinked' if dev and did_symlink else 'copied'})"
          f"   arsenal: {len(arsenal_installed)} item(s)")
    if harness:
        print(f"   ✓ harness: {len(harness['hooks'])} hooks, evolution+ledger, "
              f"workflows.json+guild-data.json+models.json, settings={harness['settings_hooks']}")
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
    # harness files (only what we recorded installing)
    harness = st.get("harness")
    if harness:
        print("   - harness (hooks/evolution/root data files)")
        if not dry:
            for h in harness.get("hooks", []):
                rm_path(claude / "hooks" / h)
            for e in harness.get("evolution", []):
                rm_path(to / "evolution" / e)
            for f in harness.get("root_files", []):
                rm_path(to / f)
            for a in harness.get("arsenal", []):
                rm_path(to / "star-alliance-arsenal" / a)
            # tidy now-empty dirs we may have created
            for d in (claude / "hooks", to / "evolution", to / "star-alliance-arsenal"):
                if d.is_dir() and not any(d.iterdir()):
                    d.rmdir()
            # if WE wired the settings hooks block, remove it (we wrote it, we own it)
            if harness.get("settings_hooks") == "wired" and (claude / "settings.json").exists():
                s = json.loads((claude / "settings.json").read_text())
                s.pop("hooks", None)
                env = s.get("env", {})
                if env.get("STAR_ALLIANCE_ROOT") == str(to):
                    env.pop("STAR_ALLIANCE_ROOT", None)
                    if not env:
                        s.pop("env", None)
                (claude / "settings.json").write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")
                print("   - settings.json: removed wired hooks block + STAR_ALLIANCE_ROOT")
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
    ap.add_argument("--with-harness", action="store_true",
                    help="also install the gated harness (hooks + workflows + signals + "
                         "settings wiring) so the Butler routes/spawns gated helpers there")
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
    return do_install(repo, to, domain, a.all, a.dev, a.do_global, a.dry_run, a.no_settings,
                      with_harness=a.with_harness)


if __name__ == "__main__":
    sys.exit(main())
