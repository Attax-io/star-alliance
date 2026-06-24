#!/usr/bin/env python3
"""Build the guild dashboard data file.

Reads every SKILL.md in the repo + dashboard-meta.json, merges them,
and writes skills-data.js (loaded by guild-dashboard.html via <script src>).

Auto-extracted from SKILL.md:
  name, version, desc, body_lines, words, intro, sections, refs, scripts, src, ramp

From dashboard-meta.json (hand-edited or AI-assigned):
  icon, blurb, level, tabler, triggers, modes

Usage:
  python3 build_dashboard.py              # write skills-data.js
  python3 build_dashboard.py --check      # print what would change, don't write
  python3 build_dashboard.py --report     # print per-skill summary table
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────────────

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


# ── Frontmatter parsing ──────────────────────────────────────────────────────

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


# ── Body parsing ─────────────────────────────────────────────────────────────

def extract_intro(body: str) -> str:
    """First meaningful paragraph after the H1 heading.
    Skips HTML comments, blockquotes, tables, config blocks, and list items."""
    lines = body.split("\n")
    first_para = []
    started = False
    in_html_comment = False
    for line in lines:
        stripped = line.strip()
        # Track multi-line HTML comments
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
    """List entries in a subdirectory (files and dirs), sorted, excluding junk."""
    d = skill_dir / subdir
    if not d.is_dir():
        return []
    return sorted(
        f.name for f in d.iterdir()
        if f.name != "__pycache__" and not f.name.startswith(".")
    )


# ── Main extraction ──────────────────────────────────────────────────────────

def iter_skills(repo: Path):
    for d in sorted(repo.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name == "skillsmith":
            # skillsmith is a sub-skill / tool, not shown in the gallery
            # Actually it IS shown — let's include it
            pass
        if not d.is_dir() or d.name.startswith("."):
            continue
        f = d / "SKILL.md"
        if f.exists():
            yield d.name, d, f


def extract_skill(name: str, skill_dir: Path, skill_md: Path, meta: dict) -> dict:
    text = skill_md.read_text()
    fm, body = split_frontmatter(text)
    desc = get_description(fm)
    version = read_version(fm) or "—"
    body_stripped = body.strip()
    body_lines = body.count("\n")  # match original dashboard counting
    words = len(body_stripped.split())

    m = meta.get(name, {})

    level = m.get("level", "Foundational")
    ramp = LEVEL_RAMP.get(level, "gray")

    return {
        "name": name,
        "version": version,
        "icon": m.get("icon", "📦"),
        "blurb": m.get("blurb", desc.split(". ")[0][:90] + ("…" if len(desc) > 90 else "")),
        "level": level,
        "body_lines": body_lines,
        "words": words,
        "desc": desc,
        "intro": extract_intro(body),
        "sections": extract_sections(body),
        "triggers": m.get("triggers", ""),
        "modes": m.get("modes", ""),
        "refs": list_files(skill_dir, "references"),
        "scripts": list_files(skill_dir, "scripts"),
        "tabler": m.get("tabler", ""),
        "src": VENDORED.get(name, "own"),
        "ramp": ramp,
    }


def build_skills(repo: Path) -> list[dict]:
    meta_path = repo / "dashboard-meta.json"
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())

    skills = []
    for name, skill_dir, skill_md in iter_skills(repo):
        skills.append(extract_skill(name, skill_dir, skill_md, meta))

    return skills


def write_data_js(repo: Path, skills: list[dict]) -> str:
    """Write skills-data.js — a simple JS file that sets window.SKILLS."""
    json_str = json.dumps(skills, ensure_ascii=False, indent=2)
    content = (
        "// Auto-generated by build_dashboard.py — do not edit by hand.\n"
        "// Re-run: python3 build_dashboard.py\n"
        f"const SKILLS = {json_str};\n"
    )
    return content


# ── CLI ──────────────────────────────────────────────────────────────────────

def cmd_build(repo: Path, check: bool) -> int:
    skills = build_skills(repo)
    content = write_data_js(repo, skills)
    out_path = repo / "skills-data.js"

    if check:
        if out_path.exists():
            old = out_path.read_text()
            if old == content:
                print(f"No changes — skills-data.js is up to date ({len(skills)} skills).")
                return 0
            else:
                print(f"Would update {out_path} ({len(skills)} skills).")
                # Show what changed
                import difflib
                old_lines = old.splitlines()
                new_lines = content.splitlines()
                diff = list(difflib.unified_diff(old_lines, new_lines, n=1, lineterm=""))
                for line in diff[:40]:
                    print(line)
                if len(diff) > 40:
                    print(f"... ({len(diff) - 40} more lines)")
                return 1
        else:
            print(f"Would create {out_path} ({len(skills)} skills).")
            return 1

    out_path.write_text(content)
    print(f"Wrote {out_path} ({len(skills)} skills, {len(content):,} bytes)")
    return 0


def cmd_report(repo: Path) -> int:
    skills = build_skills(repo)
    print(f"{'SKILL':36} {'ver':>8} {'level':14} {'src':>9} {'lines':>6} {'words':>6}  icon")
    print("-" * 100)
    for s in skills:
        print(f"{s['name']:36} {s['version']:>8} {s['level']:14} {s['src']:>9} "
              f"{s['body_lines']:>6} {s['words']:>6}  {s['icon']}")
    print(f"\n{len(skills)} skills total.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Build the skills dashboard data file.")
    ap.add_argument("--check", action="store_true", help="Show what would change, don't write")
    ap.add_argument("--report", action="store_true", help="Print per-skill summary table")
    ap.add_argument("--repo", type=Path, default=default_repo())
    a = ap.parse_args()

    repo = a.repo.expanduser().resolve()
    if not repo.exists():
        print(f"repo not found: {repo}", file=sys.stderr)
        return 2

    if a.report:
        return cmd_report(repo)
    return cmd_build(repo, a.check)


if __name__ == "__main__":
    sys.exit(main())