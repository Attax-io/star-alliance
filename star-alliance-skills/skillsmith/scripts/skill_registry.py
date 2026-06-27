#!/usr/bin/env python3
"""skillsmith — registry + Cowork-compliance for the star-alliance repo.

Single source of truth for "what version is each skill and is it Cowork-installable".
Measures the two limits that matter (description chars, SKILL.md body words/lines),
classifies a status, and (re)writes VERSIONS.md.

Subcommands:
  report            print the per-skill table to stdout (no writes)
  write             regenerate <repo>/VERSIONS.md from live frontmatter
  check [name]      Cowork-compliance check; exit 1 if any HARD violation
                    (description > 1024 chars). `name` limits to one skill.

Paths default to the repo this script lives in (…/skillsmith/../..). Override with
  --repo /path/to/star-alliance

Limits (see references/cowork-limits.md):
  description  <= 1024 chars      HARD  (frontmatter validation reject)
  SKILL.md     <  500 lines       soft  (authoring ideal)
  SKILL.md     << ~10k words      soft  (Cowork installer ceiling; references/ don't count)
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

DESC_HARD = 1024
BODY_WORD_CEILING = 10000
BODY_WORD_LARGE = 5000
BODY_LINE_IDEAL = 500

# Skills sourced from upstream (carry metadata.version provenance). Edit when vendoring more.
VENDORED = {
    "performance": "vendored",
    "supabase": "vendored",
    "supabase-postgres-best-practices": "vendored",
    "impeccable": "external",  # self-updates via `npx impeccable`
}


def default_repo() -> Path:
    """Resolve the star-alliance repo regardless of where this runs from — the repo
    checkout OR the ~/.claude/skills global install (where parents[2] would wrongly be
    ~/.claude/skills). Order: $STAR_ALLIANCE_REPO → marker-detect → known path → parents[2]."""
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
    """Layout-aware skills-root discovery, decoupled from the git/VERSIONS.md anchor.

    The repo was restructured (2026-06): skill dirs moved from the repo TOP LEVEL into a
    `star-alliance-skills/` subdir. `anchor` is the stable git root (where VERSIONS.md lives);
    the skills may sit at `anchor` OR `anchor/<subdir>`. Probe known layouts and return the
    first dir holding >=1 `*/SKILL.md`; fall back to `anchor` for unknown layouts."""
    for c in (anchor, anchor / "star-alliance-skills", anchor / "claude-skills"):
        if c.is_dir() and any(
            d.is_dir() and not d.name.startswith(".") and (d / "SKILL.md").exists()
            for d in c.iterdir()
        ):
            return c
    return anchor


def split_frontmatter(text: str):
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
    """Canonical version = metadata.version (spec-clean). Falls back to a top-level
    version: for externals not yet migrated (e.g. impeccable)."""
    m = re.search(r"(?m)^metadata:\s*$", fm)
    if m:
        tail = fm[m.end():]
        # stop at the first non-indented (dedented) line — stays inside the metadata block
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


def short_desc(fm: str) -> str:
    raw = re.sub(r"\s+", " ", get_description(fm))
    first = raw.split(". ")[0]
    return (first[:90] + "…") if len(first) > 92 else first


def measure(skill_md: Path) -> dict:
    text = skill_md.read_text()
    fm, body = split_frontmatter(text)
    desc = get_description(fm)
    bw = len(body.split())
    bl = body.count("\n") + 1
    dc = len(desc)
    angle = ("<" in desc) or (">" in desc)
    if dc > DESC_HARD:
        status = "✗ desc>1024"
    elif angle:
        status = "✗ desc<>"
    elif bw > BODY_WORD_CEILING:
        status = "⚠ body>10k"
    elif bw > BODY_WORD_LARGE or bl > BODY_LINE_IDEAL:
        status = "○ large"
    else:
        status = "✓ lean"
    return {
        "version": read_version(fm) or "—",
        "desc_words": len(desc.split()),
        "desc_chars": dc,
        "body_words": bw,
        "body_lines": bl,
        "status": status,
        "short": short_desc(fm),
        "src": VENDORED.get(skill_md.parent.name, "own"),
    }


def iter_skills(repo: Path):
    for d in sorted(repo.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        f = d / "SKILL.md"
        if f.exists():
            yield d.name, f


def cmd_report(repo: Path):
    skills_root = discover_skills_root(repo)
    print(f"{'SKILL':32} {'ver':>8} {'src':>9} {'descC':>6} {'bodyW':>7} {'bodyL':>6}  status")
    print("-" * 80)
    for name, f in iter_skills(skills_root):
        m = measure(f)
        print(f"{name:32} {m['version']:>8} {m['src']:>9} {m['desc_chars']:>6} "
              f"{m['body_words']:>7} {m['body_lines']:>6}  {m['status']}")


def cmd_check(repo: Path, only: str | None):
    skills_root = discover_skills_root(repo)
    bad = 0
    for name, f in iter_skills(skills_root):
        if only and name != only:
            continue
        m = measure(f)
        if m["status"] == "✗ desc>1024":
            print(f"HARD  {name}: description {m['desc_chars']} chars > {DESC_HARD}")
            bad += 1
        elif m["status"] == "✗ desc<>":
            print(f"HARD  {name}: description contains '<' or '>' (frontmatter validator rejects angle brackets)")
            bad += 1
        elif m["status"].startswith("⚠"):
            print(f"WARN  {name}: body {m['body_words']} words (> ~{BODY_WORD_CEILING} Cowork ceiling) — lean-pass candidate")
        elif m["status"].startswith("○"):
            print(f"note  {name}: body {m['body_words']}w / {m['body_lines']}L — over the <500-line ideal, still installable")
    if bad:
        print(f"\n{bad} HARD violation(s). Trim the description(s) to <= {DESC_HARD} chars.")
        return 1
    print("\nNo hard violations — all skills are Cowork-installable.")
    return 0


def cmd_write(repo: Path):
    skills_root = discover_skills_root(repo)
    # Link paths in VERSIONS.md are relative to the repo root (where the file lives), so prefix
    # each `{name}/SKILL.md` with the skills_root's path under the anchor (empty if skills sit at
    # the top level — preserves the pre-restructure link format).
    rel = skills_root.relative_to(repo).as_posix() if skills_root != repo else ""
    prefix = f"{rel}/" if rel else ""
    rows = [(name, measure(f)) for name, f in iter_skills(skills_root)]
    out = []
    out.append("# Skill Version Registry\n")
    out.append("Canonical version + Cowork-compliance status of every skill. **Source of truth is\n"
               "`metadata.version`** in each skill's `SKILL.md` frontmatter (a top-level `version:` is rejected by\n"
               "the Agent Skills frontmatter validator — only `name, description, license, allowed-tools, metadata,\n"
               "compatibility` are allowed). This table mirrors it. Regenerate with\n"
               "`python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write`.\n")
    out.append("## Cowork limits\n")
    out.append("| Limit | Rule | Source |")
    out.append("|---|---|---|")
    out.append("| **description** | **≤ 1024 characters** (hard — frontmatter validation reject above it) | Anthropic Agent Skills frontmatter spec |")
    out.append("| **SKILL.md body** | **< 500 lines ideal** (soft — add hierarchy + `references/` pointers as you approach it) | `skill-creator` authoring guidance |")
    out.append("| **SKILL.md body** | **keep well under ~10k words** for the Cowork installer (a 15,342-word file is known to fail; references/ bundled files do NOT count) | empirical (`cleanup` §1.9.0) |\n")
    out.append("**Status:** `✓ lean` = within all · `○ large` = installable but over the 500-line ideal or 5k+ words "
               "(trim candidate) · `⚠ body>10k` = near/over the empirical Cowork word ceiling — lean-pass candidate · "
               "`✗ desc>1024` / `✗ desc<>` = hard violations (too long / contains angle brackets), will reject.\n")
    out.append("**On any change:** bump the skill's `version:`, regenerate this file, keep the description ≤1024 chars, "
               "and prefer pushing detail into `references/` over growing SKILL.md. See [`README.md`](README.md).\n")
    out.append("> Every skill records its version under `metadata.version`. Vendored/external skills came with one\n"
               "> upstream; our own skills set it explicitly. `impeccable` is external (npx-managed) and still ships a\n"
               "> top-level `version:` — the reader falls back to it; don't hand-edit it to satisfy the validator.\n")
    out.append("| Skill | Ver | Src | Desc (words / chars) | Body (words / lines) | Cowork | What it does |")
    out.append("|---|---|---|---|---|---|---|---|")
    for name, m in rows:
        out.append(f"| [`{name}`]({prefix}{name}/SKILL.md) | {m['version']} | {m['src']} | "
                   f"{m['desc_words']} / {m['desc_chars']} | {m['body_words']} / {m['body_lines']} | "
                   f"{m['status']} | {m['short']} |")
    lean = sum(1 for _, m in rows if m["status"].startswith("✓"))
    large = sum(1 for _, m in rows if m["status"].startswith("○"))
    over = sum(1 for _, m in rows if m["status"].startswith("⚠"))
    hard = sum(1 for _, m in rows if m["status"].startswith("✗"))
    out.append(f"\n_{len(rows)} skills — {lean} lean · {large} large (installable, over the 500-line ideal) · "
               f"{over} near the word ceiling · {hard} hard violations._")
    (repo / "VERSIONS.md").write_text("\n".join(out) + "\n")
    print(f"wrote {repo / 'VERSIONS.md'} ({len(rows)} skills, {hard} hard violations)")
    return 1 if hard else 0


def main():
    ap = argparse.ArgumentParser(description="skillsmith registry + Cowork-compliance")
    ap.add_argument("cmd", choices=["report", "write", "check"])
    ap.add_argument("name", nargs="?", help="limit `check` to one skill")
    ap.add_argument("--repo", type=Path, default=default_repo())
    a = ap.parse_args()
    repo = a.repo.expanduser().resolve()
    if not repo.exists():
        print(f"repo not found: {repo}", file=sys.stderr)
        return 2
    if a.cmd == "report":
        cmd_report(repo)
        return 0
    if a.cmd == "check":
        return cmd_check(repo, a.name)
    if a.cmd == "write":
        return cmd_write(repo)


if __name__ == "__main__":
    sys.exit(main())
