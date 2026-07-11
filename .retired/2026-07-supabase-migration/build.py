#!/usr/bin/env python3
"""Build the Star Alliance dashboard data — single unified generator.

Reads every source of truth and emits ONE data file the dashboard loads:

  guild-data.js    →  const GUILD = { meta, members, skills, domains, log, models }
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

# NOTE: the old qualitative word-rank system (LEVEL_RAMP, MEMBER_TIER_ORDER,
# SKILL_LEVEL_WEIGHT, MEMBER_TIER_THRESHOLDS, the earned/conferred tier
# checklist) is RETIRED. Every member, skill, workflow, and domain card now
# carries a USAGE-BASED numeric level (XP = live invocation count), stamped by
# tools/xp.py — see stamp_xp() below. The old `level:` conferred field in
# member .md / members-meta.json stays INERT (not stripped) for deployability;
# it is simply no longer read into guild-data.

# ── Project version ───────────────────────────────────────────────────────────
# The Star Alliance project carries ONE version — owned by the Quartermaster and
# derived entirely from the guild log. Every logged change is an upgrade, so the
# version is just the log replayed as SemVer: each entry bumps exactly one tier
# by its `type`. It is cumulative and order-independent, so the same log always
# yields the same version (reproducible builds — no manual bump to forget).
#
#   MAJOR  ← structural eras   (repo-layout reorganizations — breaking changes)
#   MINOR  ← new capabilities  (a skill / member / workflow / dashboard view is born)
#   PATCH  ← refinements       (upgrades, chores, fixes — everything else)
#
# Unknown / future `type`s count as a refinement (PATCH) so no logged change is
# ever silently uncounted. To retune, move a type between these sets.
#
# `decision` (and any IGNORE type) is a RECORD kept for future runs — a choice
# and its rationale — not a change to the project, so it never bumps the version.
VERSION_MAJOR_TYPES = {"structure"}
VERSION_MINOR_TYPES = {"skill-create", "member-create", "dashboard", "workflow"}
VERSION_IGNORE_TYPES = {"decision"}


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
        "artPng": bool(repo and (repo / "art" / "skill-art" / f"{name}.png").exists()),
        "blurb": blurb,
        "craftLevel": level,  # qualitative craft-depth label (Foundational..Master) from
                               # skills-meta.json — DISTINCT from the numeric XP `level`
                               # stamped later by stamp_xp(). Kept for the skill report table.
        "tabler": m.get("tabler", ""),
        "src": VENDORED.get(name, "own"),
        "desc": desc,
        "intro": extract_intro(body),
        "sections": extract_sections(body),
        "_md": body,  # transient — popped into skill-md.js sidecar, never in guild-data
        "triggers": m.get("triggers", ""),
        "modes": m.get("modes", ""),
        "disabled": bool(m.get("disabled", False)),
        "refs": list_files(skill_dir, "references"),
        "scripts": list_files(skill_dir, "scripts"),
        "stats": {"lines": body.count("\n"), "words": len(body.split())},
        "global": False,  # set by mark_global_skills() — installed at the global load path?
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
        if md.stem.lower() in ("readme", "index", "log"):
            continue
        yield md


def derive_member_arsenal(brain_model, seats: dict, models: dict, errors: list[str] | None = None):
    """Project the CLAUDE-ONLY arsenal for one member from the seats SoT (models.json).
    Every member runs as exactly one Claude model — its session `model:` (opus/sonnet/
    haiku), an override of seats.brain.default. There is no non-Claude doer layer.
    Returns (seats_obj, weapons[{model,desc}]) — weapons[] holds the single Brain card
    the dashboard renders."""
    def dflt(seat):
        return (seats.get(seat) or {}).get("default")
    brain = brain_model or dflt("brain")
    # Build-time guard (conformity_check BR is the sweep backstop): a stale/typo'd model
    # silently yields an empty desc() body below — fail loud instead.
    if errors is not None and brain and brain not in models:
        src = "session model" if brain_model else "seat default"
        errors.append(f"member {src} '{brain}' is not a models.json key")
    seats_obj = {
        "brain": {"model": brain, "override": bool(brain_model) and brain_model != dflt("brain")},
    }

    def desc(mid):
        d = models.get(mid, {})
        body = d.get("summary") or d.get("desc") or ""
        return (f"Brain — {body}").strip(" —")
    weapons = [{"model": brain, "desc": desc(brain)}] if brain else []
    return seats_obj, weapons


def build_member(agent: dict, meta: dict, errors: list[str], seats: dict, models: dict) -> dict:
    mid = agent["id"]
    brain = agent.get("model")
    seats_obj, weapons = derive_member_arsenal(brain, seats, models, errors)
    return {
        "id": mid,
        "name": meta.get("name", mid),
        "role": meta.get("role", ""),
        "model": brain,
        "version": meta.get("version", "1.0.0"),  # every member ships as 1.0.0 by default
        "color": meta.get("color", "#888888"),
        "avatar": meta.get("avatar", ""),
        "summary": meta.get("summary", ""),
        "deploy": meta.get("deploy", ""),
        "triggers": meta.get("triggers", ""),
        "description": agent["description"],
        "prompt": agent.get("prompt", ""),
        "seats": seats_obj,
        "weapons": weapons,
        "does": meta.get("does", []),
        "doesnt": meta.get("doesnt", []),
        "skills": agent["skills"],
    }


# NOTE: the per-member "## Your Weapons" prose table is RETIRED (4-seat arsenal).
# The arsenal is universal (models.json seats), derived per member by
# derive_member_arsenal() — there is no per-member table to render or sync anymore.
# Each member .md carries a static "## Arsenal — universal seats" note instead.


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
    seats = load_seats(repo)
    models = load_models(repo)
    members = []
    for aid in ordered:
        members.append(build_member(agents[aid], members_meta.get(aid, {}), errors, seats, models))
    return members


# ── Domains & Log ────────────────────────────────────────────────────────────

def load_domains(repo: Path) -> list[dict]:
    p = repo / "data/domains.json"
    if not p.exists():
        return []
    domains = json.loads(p.read_text()).get("domains", [])
    # Merge in a real version + versionHistory per domain, from each domain's
    # own true source of truth (tools/domain_version.py). data/domains.json
    # itself stays the project list only — never hand-write versions there.
    try:
        import sys as _sys
        _sys.path.insert(0, str(repo / "tools"))
        import domain_version as _domain_version  # noqa: PLC0415

        resolved = _domain_version.resolve_all(domains, repo)
        for d in domains:
            info = resolved.get(d.get("id", ""), {})
            d["version"] = info.get("version")
            d["versionSource"] = info.get("versionSource", "unavailable")
            d["versionHistory"] = info.get("versionHistory", [])
    except Exception as exc:  # noqa: BLE001 — version enrichment must never fail the build
        print(f"[build] warning: domain version enrichment failed: {exc}")
        for d in domains:
            d.setdefault("version", None)
            d.setdefault("versionSource", "unavailable")
            d.setdefault("versionHistory", [])
    return domains


def load_workflows(repo: Path) -> list[dict]:
    p = repo / "workflows.json"
    if not p.exists():
        return []
    workflows = json.loads(p.read_text()).get("workflows", [])
    for wf in workflows:
        # Fallen Sword art tile for the Star Map, mirrors skill artPng → workflow-art/<id>.png
        wf["artPng"] = bool((repo / "art" / "workflow-art" / f"{wf.get('id', '')}.png").exists())
    return workflows


def _wf_token(x) -> str:
    """A list item in a workflow step may be a plain string or a dict like
    {"model": "minimax-sub", "count": 3}. Render either as readable text."""
    if isinstance(x, dict):
        name = x.get("model") or x.get("name") or x.get("actor") or "?"
        cnt = x.get("count")
        return f"{name}×{cnt}" if cnt else str(name)
    return str(x)


def workflow_to_md(wf: dict) -> str:
    """Serialize one workflow (from workflows.json) to a readable markdown doc —
    the source for the in-page workflow reader (mirrors a skill's SKILL.md)."""
    out = [f"# {wf.get('name', wf.get('id', 'Workflow'))}"]
    meta = []
    if wf.get("category"): meta.append(wf["category"])
    if wf.get("class"): meta.append(wf["class"])
    if meta:
        out.append("")
        out.append(" · ".join(f"**{m}**" for m in meta))
    if wf.get("tagline"):
        out.append("")
        out.append(f"> {wf['tagline']}")
    if wf.get("when"):
        out.append("")
        out.append("## When to use")
        out.append("")
        out.append(wf["when"])

    steps = wf.get("steps", [])
    if steps:
        out.append("")
        out.append("## The pipeline")
        n = 0
        for s in steps:
            kind = s.get("kind")
            if kind == "gate":
                out.append("")
                out.append(f"- **⛔ Gate — {s.get('gate', '')}.** {s.get('label', '')}")
                continue
            n += 1
            actor = s.get("actor", "")
            who = "You" if actor == "you" else actor
            out.append("")
            out.append(f"### {n}. {s.get('title', '')}")
            if who:
                out.append("")
                out.append(f"**Actor:** {who}")
            if s.get("act"):
                out.append("")
                out.append(s["act"])
            bullets = []
            if s.get("produces"): bullets.append(f"**Produces:** {s['produces']}")
            if s.get("inputs"): bullets.append(f"**Inputs:** {', '.join(_wf_token(x) for x in s['inputs'])}")
            if s.get("script"): bullets.append(f"**Script:** `{s['script']}`")
            if s.get("doers"): bullets.append(f"**Doers:** {', '.join(_wf_token(x) for x in s['doers'])}")
            if s.get("swarm"):
                sw = s["swarm"]
                sw_parts = []
                if sw.get("member"): sw_parts.append(str(sw["member"]))
                if sw.get("max_instances"): sw_parts.append(f"×{sw['max_instances']}")
                if sw.get("partition"): sw_parts.append(str(sw["partition"]))
                if sw.get("isolation"): sw_parts.append(str(sw["isolation"]))
                bullets.append(f"**Swarm:** {' · '.join(sw_parts)}")
            if s.get("parallel"): bullets.append("**Runs:** in parallel (fan-out)")
            if bullets:
                out.append("")
                for b in bullets:
                    out.append(f"- {b}")

    phrases = wf.get("trigger_phrases", [])
    if phrases:
        out.append("")
        out.append("## Trigger phrases")
        out.append("")
        for p in phrases:
            out.append(f"- {p}")

    return "\n".join(out) + "\n"


def load_hooks(repo: Path) -> list[dict]:
    """Harness lifecycle hooks surfaced on the Star Map ring (hooks.json).
    Hand-authored plain-English mirror of .claude/settings.json `hooks`."""
    p = repo / "data/hooks.json"
    if not p.exists():
        return []
    return json.loads(p.read_text()).get("hooks", [])


def load_log(repo: Path) -> dict:
    p = repo / "data/guild-log.json"
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


def stamp_xp(members: list[dict], skills: list[dict], workflows: list[dict],
             repo: Path) -> None:
    """Stamp a USAGE-BASED numeric {xp, level, xpIntoLevel, xpForNextLevel} onto
    every member, skill, and workflow object, from tools/xp.py (which counts
    real invocations in .claude/state/dispatch-log.jsonl + xp-log.jsonl — the
    single source of truth; see CLAUDE.md's XP campaign). Fail-soft: any error
    resolving XP must never crash the build — every item falls back to
    level 1 / 0 XP (tools/xp.py already fails soft internally; this is a
    second net around the import itself)."""
    try:
        import sys as _sys
        _sys.path.insert(0, str(repo / "tools"))
        import xp as _xp  # noqa: PLC0415

        member_ids = [m["id"] for m in members]
        skill_ids = [s["id"] for s in skills]
        # Workflow XP is logged by DISPLAY NAME (workflow-gate.py writes
        # {"type":"workflow","name":...}), so resolve workflows by name — not id —
        # or every workflow falls back to level 1 (self-enclosed campaign fix).
        workflow_ids = [w.get("name", "") for w in workflows]
        resolved = _xp.resolve_all(member_ids, skill_ids, workflow_ids, repo=repo)
    except Exception as exc:  # noqa: BLE001 — XP stamping must never fail the build
        print(f"[build] warning: XP resolution failed: {exc}")
        resolved = {"member": {}, "skill": {}, "workflow": {}}

    def _apply(obj: dict, kind: str, key: str) -> None:
        info = resolved.get(kind, {}).get(obj.get(key), None)
        if info is None:
            info = {"xp": 0, "level": 1, "xpIntoLevel": 0, "xpForNextLevel": 10}
        obj["xp"] = info["xp"]
        obj["level"] = info["level"]
        obj["xpIntoLevel"] = info["xpIntoLevel"]
        obj["xpForNextLevel"] = info["xpForNextLevel"]
        obj["neverInvoked"] = info["xp"] <= 0

    for m in members:
        _apply(m, "member", "id")
    for s in skills:
        _apply(s, "skill", "id")
    for w in workflows:
        _apply(w, "workflow", "name")  # match the name-keyed workflow XP log


def mark_global_skills(skills: list[dict], warnings: list[str]) -> None:
    """Flag each skill as global vs sector-specific.

    A skill is *global* when it's installed at Claude's global load path
    (~/.claude/skills) — every project/sector can use it. A skill that lives
    only inside a project's own .claude/skills is *sector-specific*. The home
    'star-alliance' domain lists the whole pool, so domain membership alone
    can't tell the two apart; the global load path is the real signal.
    """
    global_dir = Path.home() / ".claude" / "skills"
    if not global_dir.is_dir():
        warnings.append(
            f"global skills dir not found ({global_dir}) — every skill marked sector-specific"
        )
        return
    installed = {p.name for p in global_dir.iterdir() if p.is_dir()}
    for s in skills:
        s["global"] = s["id"] in installed


def validate(members: list[dict], skills: list[dict], domains: list[dict],
             workflows: list[dict],
             errors: list[str], warnings: list[str],
             model_roles: dict | None = None) -> None:
    skill_ids = {s["id"] for s in skills}
    member_ids = {m["id"] for m in members}

    # Hard: workflow steps must have a known kind and resolve to known entities.
    for wf in workflows:
        wf_id = wf["id"]
        wf_class = wf.get("class", "mutating")
        if wf_class not in ("mutating", "read-only"):
            errors.append(f"workflow '{wf_id}' has unknown class '{wf_class}' (expected mutating | read-only)")
        for step in wf.get("steps", []):
            kind = step.get("kind")
            if kind not in {"member", "gate"}:
                errors.append(f"workflow '{wf_id}' step has unknown kind '{kind}'")
                continue
            if kind == "member":
                actor = step.get("actor")
                if actor != "you" and actor not in member_ids:
                    errors.append(f"workflow '{wf_id}' step references unknown member '{actor}'")
                validate_step_weapons(wf_id, step,
                                      {m["id"]: m for m in members},
                                      model_roles or {}, errors)
            elif kind == "gate":
                gate = step.get("gate")
                if gate not in {"approval", "certify", "report"}:
                    errors.append(f"workflow '{wf_id}' step has unknown gate '{gate}'")
        # Hard standard: every workflow ENDS with the Butler's report-back gate —
        # a plain-English completion report to the Guild Master (which also flags
        # whether the run could be saved as a reusable star-map workflow).
        _steps = wf.get("steps", [])
        _last = _steps[-1] if _steps else {}
        if _last.get("kind") != "gate" or _last.get("gate") != "report":
            errors.append(f"workflow '{wf_id}' must END with a 'report' gate — the Butler "
                          f"reports back in plain English when the workflow is done (the guild standard)")

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


def derive_version(log: dict) -> tuple[str, dict]:
    """Replay the guild log into the project's SemVer string + tier breakdown."""
    major = minor = patch = 0
    for e in log.get("entries", []):
        t = e.get("type", "")
        if t in VERSION_IGNORE_TYPES:
            continue
        if t in VERSION_MAJOR_TYPES:
            major += 1
        elif t in VERSION_MINOR_TYPES:
            minor += 1
        else:
            patch += 1
    return f"{major}.{minor}.{patch}", {"major": major, "minor": minor, "patch": patch}


def load_weapon_status(members_meta_file=None) -> dict:
    """Weapon status map — DERIVED from the canonical registry
    (star-alliance-arsenal/models.json). Falls back to members-meta.json's
    legacy weaponStatus if the registry can't be read."""
    try:
        import pathlib
        reg = json.loads((pathlib.Path(__file__).resolve().parent
                          / "star-alliance-arsenal" / "models.json").read_text())
        status = {mid: d.get("status", "") for mid, d in reg.get("models", {}).items()
                  if d.get("status")}
        if status:
            return status
    except Exception:
        pass
    return (members_meta_file or {}).get("weaponStatus", {})


def build_meta(members, skills, domains, workflows, log, members_meta_file=None, hooks=None) -> dict:
    version, version_tiers = derive_version(log)
    return {
        "name": "Star Alliance",
        "version": version,
        "versionTiers": version_tiers,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "schemaVersion": SCHEMA_VERSION,
        "weaponStatus": load_weapon_status(members_meta_file),
        "counts": {
            "members": len(members),
            "skills": len(skills),
            "domains": len(domains),
            "workflows": len(workflows),
            "hooks": sum(len(h.get("scripts", [])) for h in (hooks or [])),
            "log": log["count"],
        },
    }


def load_models(repo: Path) -> dict:
    """The canonical model registry, id -> {role, backend, …, label, color, …}.
    Source of truth: star-alliance-arsenal/models.json. Emitted into guild-data as
    GUILD.models so app.js DERIVES its arsenal cards instead of hand-listing them."""
    try:
        return json.loads((repo / "star-alliance-arsenal" / "models.json").read_text()).get("models", {})
    except Exception:
        return {}


def load_seats(repo: Path) -> dict:
    """The universal role seats (Brain/Doer/Bench) from models.json.
    Emitted into guild-data as GUILD.seats so the dashboard renders the seat layer
    instead of per-member loadouts."""
    try:
        return json.loads((repo / "star-alliance-arsenal" / "models.json").read_text()).get("seats", {})
    except Exception:
        return {}


def load_model_roles(repo: Path) -> dict:
    """Model id -> role for workflow weapon-field validation. DERIVED from the
    canonical registry (star-alliance-arsenal/models.json), normalizing the media
    role to 'doer' for ordering — matching conformity_check._load_role. Empty dict
    on any error makes the validation skip (fail open), but the registry is the one
    source so this no longer scrapes app.js."""
    models = load_models(repo)
    return {mid: ("doer" if d.get("role") == "media" else d.get("role", ""))
            for mid, d in models.items() if d.get("role")}


def validate_step_weapons(wf_id: str, step: dict, members_by_id: dict,
                          model_roles: dict, errors: list[str]) -> None:
    """Enforce the structured weapon fields on a member step:
       thinker (thinker-role + in loadout), doers (doer-role + in loadout),
       ultra (actor must carry ultra-brainstorming). All fields are OPTIONAL —
       a step without them is valid (backward compatible). model_roles empty → skip."""
    actor = step.get("actor")
    if actor == "you" or actor not in members_by_id:
        return
    mem = members_by_id[actor]
    loadout = {w["model"] if isinstance(w, dict) else w for w in mem.get("weapons", [])}
    where = f"workflow '{wf_id}' step '{step.get('title', '?')}' (actor {actor})"

    th = step.get("thinker")
    if th is not None:
        if model_roles and model_roles.get(th) not in ("thinker", "both"):
            errors.append(f"{where}: thinker '{th}' is not a thinker-role weapon")
        if th not in loadout:
            errors.append(f"{where}: thinker '{th}' is not in {actor}'s loadout")

    doers = step.get("doers")
    if doers is not None:
        if not isinstance(doers, list) or not doers:
            errors.append(f"{where}: 'doers' must be a non-empty list")
        else:
            for d in doers:
                model = d.get("model") if isinstance(d, dict) else d
                cnt = d.get("count", 1) if isinstance(d, dict) else 1
                if not isinstance(cnt, int) or cnt < 1:
                    errors.append(f"{where}: doer '{model}' has invalid count {cnt!r}")
                if model_roles and model_roles.get(model) not in ("doer", "both"):
                    errors.append(f"{where}: doer '{model}' is not a doer-role weapon")
                if model not in loadout:
                    errors.append(f"{where}: doer '{model}' is not in {actor}'s loadout")

    if step.get("ultra"):
        if "ultra-brainstorming" not in mem.get("skills", []):
            errors.append(f"{where}: ultra=true but {actor} does not carry the "
                          f"ultra-brainstorming skill")


def assemble(repo: Path) -> tuple[dict, list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    skills_meta = json.loads((repo / "data/skills-meta.json").read_text()) if (repo / "data/skills-meta.json").exists() else {}
    members_meta_file = json.loads((repo / "data/members-meta.json").read_text()) if (repo / "data/members-meta.json").exists() else {"members": {}}
    members_meta = members_meta_file.get("members", {})

    skills = build_skills(repo, skills_meta, warnings)
    members = build_members(repo, members_meta, errors)
    domains = load_domains(repo)
    workflows = load_workflows(repo)
    hooks = load_hooks(repo)
    model_roles = load_model_roles(repo)
    log = load_log(repo)

    compute_reverse_indices(members, skills)
    mark_global_skills(skills, warnings)
    validate(members, skills, domains, workflows, errors, warnings, model_roles)
    stamp_xp(members, skills, workflows, repo)

    guild = {
        "meta": build_meta(members, skills, domains, workflows, log, members_meta_file, hooks),
        "members": members,
        "skills": skills,
        "domains": domains,
        "workflows": workflows,
        "hooks": hooks,
        "log": log,
        "models": load_models(repo),
        "seats": load_seats(repo),
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
    # Pull the full SKILL.md bodies out into a separate sidecar so guild-data
    # stays lean. The sidecar (loaded via <script>) powers the in-panel reader
    # even under file://, where the browser blocks fetch() of local files.
    md_map = {}
    for s in guild.get("skills", []):
        md = s.pop("_md", None)
        if md is not None:
            md_map[s["id"]] = md
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
    md_js = (
        "// Auto-generated by build.py — do not edit by hand.\n"
        "// Full SKILL.md bodies keyed by skill id. Powers the in-panel reader,\n"
        "// loaded via <script> so it works on file:// (where fetch() is blocked).\n"
        f"const SKILL_MD = {json.dumps(md_map, ensure_ascii=False, indent=0)};\n"
    )
    md_path = repo / "skill-md.js"
    md_path.write_text(md_js)
    # Workflow markdown sidecar — same pattern, for the in-page workflow reader.
    wf_map = {wf["id"]: workflow_to_md(wf) for wf in guild.get("workflows", [])}
    wf_js = (
        "// Auto-generated by build.py — do not edit by hand.\n"
        "// Markdown per workflow (serialized from workflows.json), keyed by id.\n"
        "// Loaded via <script> so the workflow reader works on file:// too.\n"
        f"const WORKFLOW_MD = {json.dumps(wf_map, ensure_ascii=False, indent=0)};\n"
    )
    (repo / "workflow-md.js").write_text(wf_js)
    print(f"Wrote guild-data.js ({len(js):,} bytes) + guild-data.json "
          f"+ skill-md.js ({len(md_js):,} bytes, {len(md_map)} skills) "
          f"+ workflow-md.js ({len(wf_js):,} bytes, {len(wf_map)} workflows)")
    # Keep the portable subset (workflows-lite.json) derived from workflows.json (SSOT).
    try:
        import subprocess
        subprocess.run(["python3", str(repo / "guild" / "gen_workflows_lite.py")],
                       check=False, capture_output=True, timeout=30)
    except Exception:
        pass
    return changed


def report(guild: dict) -> None:
    print(f"\n{guild['meta']['name']} v{guild['meta']['version']} — "
          f"schema v{guild['meta']['schemaVersion']} — "
          f"generated {guild['meta']['generated']}")
    print("counts:", guild["meta"]["counts"])
    print(f"\n{'SKILL':34} {'ver':>8} {'craft':13} {'xpLvl':>6} {'xp':>5} {'src':>9} {'lines':>6} {'words':>6} {'carriers':>8}  icon")
    print("-" * 100)
    for s in guild["skills"]:
        print(f"{s['id']:34} {s['version']:>8} {s.get('craftLevel', ''):13} "
              f"{s.get('level', 1):>6} {s.get('xp', 0):>5} {s['src']:>9} "
              f"{s['stats']['lines']:>6} {s['stats']['words']:>6} {len(s['members']):>8}  {s['icon']}")
    print(f"\n{'MEMBER':20} {'model':>8} {'ver':>8} {'skills':>7} {'xpLvl':>6} {'xp':>5}")
    print("-" * 100)
    for m in guild["members"]:
        print(f"{m['id']:20} {m['model']:>8} {m.get('version', ''):>8} {len(m['skills']):>7} "
              f"{m.get('level', 1):>6} {m.get('xp', 0):>5}")


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
