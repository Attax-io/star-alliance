#!/usr/bin/env python3
"""sync.py — regenerate ALL generated files from the sources of truth
(members, skills, models, workflows). Run after editing any
star-alliance-members/*.md, star-alliance-skills/*, models.json,
workflows.json, or data/*.json. Never hand-edit generated files.

Sources of truth  →  Generated files
-------------------------
star-alliance-members/*.md        →  guild/AGENTS.md   (Hermes profile manifests)
star-alliance-skills/SKILL.md      →  skill-md.js
star-alliance-arsenal/models.json →  guild-data.json
workflows.json                    →  workflow-md.js
data/*.json                       →  guild-data.json
art/skill-art/, art/workflow-art/  →  artPng flags in guild-data.json
art/*-art/                         →  art/*-thumb/   (Pillow thumbs for dashboard)

Output:
  - guild/AGENTS.md
  - guild-data.json, guild-data.js
  - skill-md.js, workflow-md.js
  - VERSIONS.md
  - art/skill-art-thumb/, art/workflow-art-thumb/, art/member-art-thumb/

Requires: Pillow (PIL) for the thumb step. If missing, install with:
  python3 -m pip install pillow

Usage:
  python3 sync.py
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
PY = sys.executable


def banner(step: str) -> None:
    print()
    print("=" * 60)
    print(f"  {step}")
    print("=" * 60)


def run(label: str, args: list[str]) -> None:
    print(f"\n→ {label}")
    print(f"  $ {' '.join(args)}")
    result = subprocess.run(args, cwd=REPO)
    if result.returncode != 0:
        print(f"\n✘ {label} failed with exit code {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"✔ {label} OK")


def main() -> int:
    print(f"Star Alliance — sync.py")
    print(f"  repo: {REPO}")
    print(f"  python: {PY}")

    # Step 1: regenerate Hermes profile AGENTS.md from star-alliance-members/
    banner("Step 1/3 · Regenerate guild profile AGENTS.md")
    run(
        "install_agents.py",
        [PY, str(REPO / "guild" / "install_agents.py")],
    )

    # Step 2: regenerate dashboard thumbnails from art/*.  Idempotent — skips
    #         thumbs that already exist and are newer than their source, so
    #         untouched art is a near no-op.
    banner("Step 2/3 · Generate dashboard thumbnails")
    run("make_thumbs.py", [PY, str(REPO / "tools" / "make_thumbs.py")])

    # Step 3: regenerate guild-data.json, guild-data.js, skill-md.js,
    #         workflow-md.js, VERSIONS.md from sources of truth.
    banner("Step 3/3 · Rebuild dashboard data bundles")
    run("build.py", [PY, str(REPO / "build.py")])

    # Final summary
    banner("Summary")
    data_path = REPO / "guild-data.json"
    if not data_path.exists():
        print("✘ guild-data.json not found after build", file=sys.stderr)
        return 1
    data = json.loads(data_path.read_text())
    counts = data.get("meta", {}).get("counts", {}) or {}
    members = counts.get("members", "?")
    skills = counts.get("skills", "?")
    workflows = counts.get("workflows", "?")
    art_png_skills = sum(1 for s in data.get("skills", []) if s.get("artPng"))
    art_png_workflows = sum(1 for w in data.get("workflows", []) if w.get("artPng"))
    print(f"  members   : {members}")
    print(f"  skills    : {skills}   ({art_png_skills} with art tile)")
    print(f"  workflows : {workflows}   ({art_png_workflows} with art tile)")
    print(f"  version   : {data.get('meta', {}).get('version', '?')}")
    print(f"  generated : {data.get('meta', {}).get('generated', '?')}")
    print()
    print("✔ sync complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())