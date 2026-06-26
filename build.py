#!/usr/bin/env python3
"""Build the Star Alliance dashboard data — single unified generator.

Reads every source of truth and emits ONE data file the dashboard loads:

  guild-data.js    →  const GUILD = { meta, members, skills, domains, log }
  guild-data.json  →  the same object as pure JSON (non-browser consumers)

Sources
  star-alliance-skills/<id>/SKILL.md   skill frontmatter (version) + body (intro/sections)
  skills-meta.json                     per-skill presentation: icon, blurb, level, tabler, triggers, modes
  star-alliance-members/<id>.md         member structure: model, weapons[], skills[], description
  members-meta.json                    per-member presentation: name, role, color, avatar, summary, …
  domains.json                         project domains (hand-edited)
  guild-log.json                       change log (owned by build_guild_log.py + log_event.py)

The build VALIDATES cross-references (member→skill, domain→skill, domain→member,
weapon→desc) and computes reverse indices (skill.members). It is idempotent: only
meta.generated changes between identical runs, and --check ignores that field.

Usage
  python3 build.py            write guild-data.js + guild-data.json
  python3 build.py --check    exit 1 if content (ignoring timestamp) would change
  python3 build.py --report   per-skill / per-member summary table
  python3 build.py --strict   treat warnings as errors
  python3 build.py --repo P   point at a different repo root
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

SKILLS_DIR = "star-alliance-skills"
AGENTS_DIR = "star-alliance-members"
SCHEMA_VERSION = 3

# meta fields that vary run-to-run — excluded from --check diffing (see _normalize).
# Add any future non-deterministic meta field here or --check will report spurious changes.
IDEMPOTENT_META_BLANKS = ("generated",)

VENDORED = {
    "performance": "vendored",
    "supabase": "vendored",
    "supabase-postgres-best-practices": "vendored",
    "impeccable": "external",
}

LEVEL_RAMP = {
    "Foundational": "gray",
    "Intermediate": "blue",
    "Advanced": "teal",
    "Elite": "amber",
    "Master": "purple",
}


def default_repo() -> Path:
    """Find the star-alliance repo regardless of cwd."""
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
    return here.parent


# ── Frontmatter parsing (ported from the original dashboard build helpers)─────────────────────

def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def fm_field(fm: str, key: str) -> str:
    m = re.search(rf"(?im)^{key}:\s*(.+)$", fm)
    return m.group(1).strip().strip('"').strip("'") if m else ""


def read_version(fm: str) -> str:
    """Canonical version = metadata.version. Falls back to top-level version:."""
    m = re.search(r"(?m)^metadata:\s*$", fm)
    if m:
        tail = fm[m.end():]
        block = re.match(r"((?:\n[ \t]+.*|\n[ \t]*)*)", tail)
        seg = block.group(0) if block else tail
        vm = re.search(r"(?m)^[ \t]+version:\s*(.+)$", seg)
        if vm:
            return vm.group(1).strip().strip('"').strip("'")
    tm = re.search(r"(?m)^version:\s*(.+)$", fm)
    return tm.group(1).strip().strip('"').strip("'") if tm else ""


def get_description(fm: str) -> str:
    """Handle inline, quoted, and block-scalar (>, |) description forms."""
    lines = fm.splitlines()
    i, n, out = 0, len(lines), []
    while i < n:
        m = re.match(r"(?i)^description:\s*(.*)$", lines[i])
        if m:
            head = m.group(1).strip()
            if head in (">", "|", ">-", "|-", ">+", "|+", ""):
                i += 1
                while i < n and (re.match(r"^\s+\S", lines[i]) or lines[i].strip() == ""):
                    if lines[i].strip():
                        out.append(lines[i].strip())
                    i += 1
                return " ".join(out)
            return head.strip('"').strip("'").replace('\\"', '"')
        i += 1
    return ""


def parse_list_field(fm: str, key: str) -> list[str]:
    """Parse a `key: [a, b, c]  # trailing comment` frontmatter list.

    The brackets bound the capture, so trailing `# comments` are excluded.
    """
    m = re.search(rf"(?im)^{key}:\s*\[(.*?)\]", fm, re.DOTALL)
    if not m:
        return []
    return [s.strip().strip('"').strip("'") for s in m.group(1).split(",") if s.strip()]


# ── Body parsing (ported from the original dashboard build helpers)────────────────────────────

def extract_intro(body: str) -> str:
    """First meaningful paragraph after the H1 heading."""
    lines = body.split("\n")
    first_para: list[str] = []
    started = False
    in_html_comment = False
    for line in lines:
        stripped = line.strip()
        if "<!--" in stripped:
            if "-->" not in stripped:
                in_html_comment = True
            continue
        if in_html_comment:
            if "-->" in stripped:
                in_html_comment = False
            continue
        if stripped.startswith("# ") and not started:
            started = True
            continue
        if not started:
            continue
        if stripped == "":
            if first_para:
                break
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("|") and stripped.count("|") >= 3:
            continue
        if stripped.startswith(">"):
            continue
        if stripped.startswith("<!--"):
            continue
        if re.match(r"^[-*]\s", stripped):
            continue
        clean = re.sub(r'`([^`]+)`', r'\1', stripped)
        clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean)
        clean = re.sub(r'\*([^*]+)\*', r'\1', clean)
        first_para.append(clean)
    return " ".join(first_para)[:300]


def extract_sections(body: str) -> list[str]:
    """Extract H2 headings (## ...), stripping markdown formatting."""
    headings = re.findall(r'^##\s+(.+)$', body, re.MULTILINE)
    return [re.sub(r'[*_`]', '', h.strip()) for h in headings]


def list_files(skill_dir: Path, subdir: str) -> list[str]:
    d = skill_dir / subdir
    if not d.is_dir():
        return []
    return sorted(
        f.name for f in d.iterdir()
        if f.name != "__pycache__" and not f.name.startswith(".")
    )


def slugify(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


# ── Skills ───────────────────────────────────────────────────────────────────

def iter_skills(repo: Path):
    """Walk star-alliance-skills/ — each subdir with a SKILL.md is one skill."""
    root = repo / SKILLS_DIR
    if not root.is_dir():
        root = repo  # backward compat: flat layout
    for d in sorted(root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        f = d / "SKILL.md"
        if f.exists():
            yield d.name, d, f


def build_skill(name: str, skill_dir: Path, skill_md: Path, meta: dict, repo: Path = None) -> dict:
    text = skill_md.read_text()
    fm, body = split_frontmatter(text)
    desc = get_description(fm)
    version = read_version(fm) or "—"
    m = meta.get(name, {})
    level = m.get("level", "Foundational")
    blurb = m.get("blurb") or (desc.split(". ")[0][:90] + ("…" if len(desc) > 90 else ""))
    return {
        "id": name,
        "name": fm_field(fm, "name") or name,
        "version": version,
        "icon": m.get("icon", "📦"),
        "art": m.get("art", ""),  # optional inline-SVG sigil; falls back to icon
        "artPng": bool(repo and (repo / "skill-art" / f"{name}.png").exists()),
        "blurb": blurb,
        "level": level,
        "ramp": LEVEL_RAMP.get(level, "gray"),
        "tabler": m.get("tabler", ""),
        "src": VENDORED.get(name, "own"),
        "desc": desc,
        "intro": extract_intro(body),
        "sections": extract_sections(body),
        "triggers": m.get("triggers", ""),
        "modes": m.get("modes", ""),
        "disabled": bool(m.get("disabled", False)),
        "refs": list_files(skill_dir, "references"),
        "scripts": list_files(skill_dir, "scripts"),
        "stats": {"lines": body.count("\n"), "words": len(body.split())},
        "members": [],  # reverse index — filled by compute_reverse_indices()
    }


def build_skills(repo: Path, skills_meta: dict, warnings: list[str]) -> list[dict]:
    skills = []
    for name, skill_dir, skill_md in iter_skills(repo):
        if name not in skills_meta:
            warnings.append(f"skill '{name}' has no skills-meta.json entry — using defaults")
        skills.append(build_skill(name, skill_dir, skill_md, skills_meta, repo))
    return skills


# ── Members ──────────────────────────────────────────────────────────────────

def parse_agent(md_path: Path) -> dict:
    """Extract member structure from an agent .md frontmatter."""
    fm, body = split_frontmatter(md_path.read_text())
    return {
        "id": md_path.stem,
        "model": fm_field(fm, "model"),
        "weapons": parse_list_field(fm, "weapons"),
        "skills": parse_list_field(fm, "skills"),
        "description": get_description(fm),
        "prompt": body.strip(),
    }


def iter_agents(repo: Path):
    d = repo / AGENTS_DIR
    if not d.is_dir():
        return
    for md in sorted(d.glob("*.md")):
        if md.stem.lower() == "readme":
            continue
        yield md


def build_member(agent: dict, meta: dict, errors: list[str]) -> dict:
    mid = agent["id"]
    wdesc = meta.get("weaponsDesc", {})
    weapons = []
    for w in agent["weapons"]:
        if w not in wdesc:
            errors.append(f"member '{mid}': weapon '{w}' has no weaponsDesc entry")
        weapons.append({"model": w, "desc": wdesc.get(w, "")})
    for w in wdesc:
        if w not in agent["weapons"]:
            errors.append(f"member '{mid}': weaponsDesc '{w}' matches no weapon in the agent .md")
    return {
        "id": mid,
        "name": meta.get("name", mid),
        "role": meta.get("role", ""),
        "model": agent["model"],
        "color": meta.get("color", "#888888"),
        "avatar": meta.get("avatar", ""),
        "summary": meta.get("summary", ""),
        "deploy": meta.get("deploy", ""),
        "triggers": meta.get("triggers", ""),
        "description": agent["description"],
        "prompt": agent.get("prompt", ""),
        "weapons": weapons,
        "does": meta.get("does", []),
        "doesnt": meta.get("doesnt", []),
        "skills": agent["skills"],
    }


def build_members(repo: Path, members_meta: dict, errors: list[str]) -> list[dict]:
    agents = {md.stem: parse_agent(md) for md in iter_agents(repo)}
    # Every agent must have a presentation half, and vice-versa.
    for aid in agents:
        if aid not in members_meta:
            errors.append(f"agent '{aid}.md' has no members-meta.json entry")
    for mid in members_meta:
        if mid not in agents:
            errors.append(f"members-meta.json key '{mid}' has no agent .md")
    # Roster order = members-meta.json key order (intentional: Butler leads),
    # with any agent missing from meta appended alphabetically for safety.
    ordered = [aid for aid in members_meta if aid in agents]
    ordered += [aid for aid in agents if aid not in members_meta]
    members = []
    for aid in ordered:
        members.append(build_member(agents[aid], members_meta.get(aid, {}), errors))
    return members


# ── Domains & Log ────────────────────────────────────────────────────────────

def load_domains(repo: Path) -> list[dict]:
    p = repo / "domains.json"
    if not p.exists():
        return []
    return json.loads(p.read_text()).get("domains", [])


def load_workflows(repo: Path) -> list[dict]:
    p = repo / "workflows.json"
    if not p.exists():
        return []
    return json.loads(p.read_text()).get("workflows", [])


def load_log(repo: Path) -> dict:
    p = repo / "guild-log.json"
    if not p.exists():
        return {"entries": [], "count": 0}
    entries = json.loads(p.read_text()).get("entries", [])
    seen = set()
    for e in entries:
        if "id" not in e:
            commit = e.get("commit", "")
            stub = slugify(e.get("title", "entry"))[:40]
            base = f"g-{commit}-{stub}" if commit else f"h-{stub}"
            eid, k = base, 2
            while eid in seen:  # two entries slugify identically → suffix to keep ids unique
                eid, k = f"{base}-{k}", k + 1
            e["id"] = eid
        seen.add(e["id"])
    return {"entries": entries, "count": len(entries)}


# ── Indices, validation, meta ────────────────────────────────────────────────

def compute_reverse_indices(members: list[dict], skills: list[dict]) -> None:
    by_id = {s["id"]: s for s in skills}
    for s in skills:
        s["members"] = []
    for m in members:
        for sid in m["skills"]:
            if sid in by_id:
                by_id[sid]["members"].append(m["id"])
    for s in skills:
        s["members"].sort()


def validate(members: list[dict], skills: list[dict], domains: list[dict],
             workflows: list[dict],
             errors: list[str], warnings: list[str]) -> None:
    skill_ids = {s["id"] for s in skills}
    member_ids = {m["id"] for m in members}

    # Hard: workflow steps must have a known kind and resolve to known entities.
    for wf in workflows:
        wf_id = wf["id"]
        for step in wf.get("steps", []):
            kind = step.get("kind")
            if kind not in {"member", "gate"}:
                errors.append(f"workflow '{wf_id}' step has unknown kind '{kind}'")
                continue
            if kind == "member":
                actor = step.get("actor")
                if actor != "you" and actor not in member_ids:
                    errors.append(f"workflow '{wf_id}' step references unknown member '{actor}'")
            elif kind == "gate":
                gate = step.get("gate")
                if gate not in {"approval", "certify", "report"}:
                    errors.append(f"workflow '{wf_id}' step has unknown gate '{gate}'")

    # Hard: every member skill must resolve to an installed skill.
    for m in members:
        for sid in m["skills"]:
            if sid not in skill_ids:
                errors.append(f"member '{m['id']}' references unknown skill '{sid}'")

    # Warn: domain refs may legitimately point at other repos.
    for d in domains:
        for sid in d.get("skills", []):
            if sid not in skill_ids:
                warnings.append(f"domain '{d['id']}' references skill '{sid}' not in the guild pool")
        for mid in d.get("members", []):
            if mid not in member_ids:
                warnings.append(f"domain '{d['id']}' references member '{mid}' not in the guild (external)")


def build_meta(members, skills, domains, workflows, log) -> dict:
    return {
        "name": "Star Alliance",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "schemaVersion": SCHEMA_VERSION,
        "counts": {
            "members": len(members),
            "skills": len(skills),
            "domains": len(domains),
            "workflows": len(workflows),
            "log": log["count"],
        },
    }


def assemble(repo: Path) -> tuple[dict, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    skills_meta = json.loads((repo / "skills-meta.json").read_text()) if (repo / "skills-meta.json").exists() else {}
    members_meta_file = json.loads((repo / "members-meta.json").read_text()) if (repo / "members-meta.json").exists() else {"members": {}}
    members_meta = members_meta_file.get("members", {})

    skills = build_skills(repo, skills_meta, warnings)
    members = build_members(repo, members_meta, errors)
    domains = load_domains(repo)
    workflows = load_workflows(repo)
    log = load_log(repo)

    compute_reverse_indices(members, skills)
    validate(members, skills, domains, workflows, errors, warnings)

    guild = {
        "meta": build_meta(members, skills, domains, workflows, log),
        "members": members,
        "skills": skills,
        "domains": domains,
        "workflows": workflows,
        "log": log,
    }
    return guild, errors, warnings


# ── Output ───────────────────────────────────────────────────────────────────

def _normalize(guild: dict) -> str:
    """Serialize with run-to-run meta fields blanked — for idempotent --check diffing."""
    import copy
    g = copy.deepcopy(guild)
    for k in IDEMPOTENT_META_BLANKS:
        g["meta"][k] = ""
    return json.dumps(g, ensure_ascii=False, indent=2, sort_keys=True)


def write_outputs(repo: Path, guild: dict, check: bool) -> bool:
    """Returns True if content changed (or would change under --check)."""
    body = json.dumps(guild, ensure_ascii=False, indent=2)
    js = (
        "// Auto-generated by build.py — do not edit by hand.\n"
        "// Re-run: python3 build.py\n"
        f"const GUILD = {body};\n"
    )
    js_path = repo / "guild-data.js"
    json_path = repo / "guild-data.json"

    changed = True
    if json_path.exists():
        try:
            prev = json.loads(json_path.read_text())
            changed = _normalize(prev) != _normalize(guild)
        except (json.JSONDecodeError, KeyError):
            changed = True

    if check:
        if changed:
            print("Would update guild-data.js + guild-data.json (content changed).")
        else:
            print("Up to date (only the timestamp would differ).")
        return changed

    js_path.write_text(js)
    json_path.write_text(body + "\n")
    print(f"Wrote guild-data.js ({len(js):,} bytes) + guild-data.json")
    return changed


def report(guild: dict) -> None:
    print(f"\n{guild['meta']['name']} — schema v{guild['meta']['schemaVersion']} — "
          f"generated {guild['meta']['generated']}")
    print("counts:", guild["meta"]["counts"])
    print(f"\n{'SKILL':34} {'ver':>8} {'level':13} {'src':>9} {'lines':>6} {'words':>6} {'carriers':>8}  icon")
    print("-" * 100)
    for s in guild["skills"]:
        print(f"{s['id']:34} {s['version']:>8} {s['level']:13} {s['src']:>9} "
              f"{s['stats']['lines']:>6} {s['stats']['words']:>6} {len(s['members']):>8}  {s['icon']}")
    print(f"\n{'MEMBER':20} {'model':>8} {'skills':>7} {'weapons':>8}  role")
    print("-" * 100)
    for m in guild["members"]:
        print(f"{m['id']:20} {m['model']:>8} {len(m['skills']):>7} {len(m['weapons']):>8}  {m['role']}")


def emit_findings(errors: list[str], warnings: list[str]) -> None:
    if warnings:
        print(f"\nBUILD WARNINGS ({len(warnings)}):", file=sys.stderr)
        for w in warnings:
            print(f"  ⚠ {w}", file=sys.stderr)
    if errors:
        print(f"\nBUILD ERRORS ({len(errors)}):", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the Star Alliance dashboard data.")
    ap.add_argument("--check", action="store_true", help="Show whether content would change, don't write")
    ap.add_argument("--report", action="store_true", help="Print a per-skill/member summary table")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    ap.add_argument("--repo", type=Path, default=default_repo())
    a = ap.parse_args()

    repo = a.repo.expanduser().resolve()
    if not repo.exists():
        print(f"repo not found: {repo}", file=sys.stderr)
        return 2

    guild, errors, warnings = assemble(repo)
    emit_findings(errors, warnings)

    if errors or (a.strict and warnings):
        print("\nBuild aborted — fix the errors above.", file=sys.stderr)
        return 1

    if a.report:
        report(guild)
        return 0

    changed = write_outputs(repo, guild, a.check)
    if a.check:
        return 1 if changed else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
