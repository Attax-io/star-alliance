#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — ABSORB INWARD  (the SENSE step for cross-project learning)
#
# The Evolution Engine's inward loop watched only the guild's OWN turns. It had
# NO way to learn from a project the guild worked on and carry a good idea home.
# This is the missing half of the mandate: "learn from a new project, but save
# improvements back INTO star-alliance — never as a global skill."
#
# absorb.py is the SENSE step of that inward loop. It SCANS a deployed target
# project's .claude/skills, DIFFS each skill against the box (star-alliance-skills),
# and for every skill the box LACKS (kind=new) or that MATERIALLY differs
# (kind=improved) it emits a `proposal` event through the existing ledger. It
# COPIES NOTHING. It is read-only w.r.t. the target and write-only to the ledger.
#
# The applier (evolution/absorb_apply.py) is the CHANGE step — critic-gated and
# human-gated. This file never writes a skill; it only proposes. Same safety
# envelope as engine.py: propose first, a human + critic decide what sticks.
#
#   python3 evolution/absorb.py <target-project-path> [--json] [--no-emit]
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BOX_SKILLS = REPO / "star-alliance-skills"          # the guild's source-of-truth skills
SKILL_FILE = "SKILL.md"

sys.path.insert(0, str(HERE))
import ledger        # noqa: E402


def _read(p: Path) -> str:
    try:
        return Path(p).read_text(encoding="utf-8")
    except Exception:
        return ""


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _frontmatter_version(text: str) -> str:
    m = re.search(r'(?m)^\s*version:\s*["\']?([0-9][0-9A-Za-z.\-]*)', text or "")
    return m.group(1) if m else ""


def _target_skills_dir(target: str | Path) -> Path:
    return Path(target) / ".claude" / "skills"


def scan(target: str | Path) -> list[dict]:
    """Read-only scan of <target>/.claude/skills. Return a list of candidates.

    A candidate is a skill the box LACKS (kind=new) or one whose content hash
    MATERIALLY differs from the box copy (kind=improved). An identical skill is
    skipped. This function copies nothing and never touches the target."""
    tdir = _target_skills_dir(target)
    candidates: list[dict] = []
    if not tdir.is_dir():
        return candidates
    for sub in sorted(tdir.iterdir()):
        if not sub.is_dir():
            continue
        sfile = sub / SKILL_FILE
        if not sfile.is_file():
            continue
        ttext = _read(sfile)
        if not ttext.strip():
            continue
        sid = sub.name
        thash = _hash(ttext)
        tver = _frontmatter_version(ttext)
        box = BOX_SKILLS / sid / SKILL_FILE
        if not box.is_file():
            candidates.append({
                "skill_id": sid, "kind": "new", "source": str(sfile),
                "target_hash": thash, "target_version": tver, "box_version": "",
                "detail": f"skill '{sid}' present in target, absent from the box",
            })
            continue
        btext = _read(box)
        if _hash(btext) == thash:
            continue                                  # identical — nothing to absorb
        bver = _frontmatter_version(btext)
        candidates.append({
            "skill_id": sid, "kind": "improved", "source": str(sfile),
            "target_hash": thash, "target_version": tver, "box_version": bver,
            "detail": (f"skill '{sid}' differs from the box "
                       f"(target v{tver or '?'} vs box v{bver or '?'})"),
        })
    return candidates


def propose(target: str | Path, emit: bool = True) -> list[dict]:
    """Scan + emit one `proposal` ledger event per candidate. Returns candidates.
    emit=False makes it a pure dry read (no ledger writes)."""
    cands = scan(target)
    for c in cands:
        if not emit:
            continue
        ledger.append(
            "proposal", author="evolution-absorb", surface="skills", tier="A",
            diff_hash=c["target_hash"], detail="absorb: " + c["detail"],
            meta={
                "absorb": True, "skill_id": c["skill_id"], "kind": c["kind"],
                "source": c["source"], "target": str(target),
                "target_version": c["target_version"], "box_version": c["box_version"],
                "action": (f"critic-gate then human go: "
                           f"python3 evolution/absorb_apply.py {target} {c['skill_id']} --go"),
            },
        )
    return cands


def _cli():
    import argparse
    ap = argparse.ArgumentParser(
        prog="absorb",
        description="SENSE inward: scan a target project's skills, propose absorbing "
                    "novel/improved ones into the box (copies nothing).")
    ap.add_argument("target", help="path to a deployed target project (scans <target>/.claude/skills)")
    ap.add_argument("--json", action="store_true", help="emit candidates as JSON")
    ap.add_argument("--no-emit", action="store_true", help="dry read — do NOT write ledger proposals")
    a = ap.parse_args()
    cands = propose(a.target, emit=not a.no_emit)
    if a.json:
        print(json.dumps(cands, ensure_ascii=False, indent=2))
        return
    if not cands:
        print(f"[absorb] no novel/improved skills in {a.target} — box is up to date.")
        return
    verb = "would propose" if a.no_emit else "proposed"
    print(f"[absorb] {verb} {len(cands)} candidate(s) from {a.target}:")
    for c in cands:
        print(f"   · [{c['kind']:8}] {c['skill_id']:28} {c['detail']}")
    if not a.no_emit:
        print("[absorb] ledger proposals written. Nothing copied. "
              "Absorb one with: python3 evolution/absorb_apply.py <target> <skill_id> --go")


if __name__ == "__main__":
    _cli()
