#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — ABSORB APPLIER  (the CHANGE step: critic-gated + human-gated)
#
# The second half of the inward loop. Given ONE proposal (a target project + a
# skill id from absorb.py), it:
#   1. re-derives the candidate via absorb.scan  (single source of the diff logic)
#   2. runs the INDEPENDENT critic (verdict.run_cold) on the proposed skill
#   3. STOPS on a critic block; FAILS CLOSED if the critic is unreachable
#   4. writes the skill into the box ONLY on a critic pass/concerns AND an explicit
#      human "go" (--go or SA_ABSORB_GO=1), then regenerates via build.py
#
# THE BOX IS THE ONLY SINK. _sink_guard resolves every write target and REFUSES
# anything not strictly inside star-alliance-skills/. It can never write under
# ~/.claude or a project's own .claude/skills — that guarantee is what makes an
# absorbed skill a GUILD skill, never a global one. The AB conformity check
# exercises this guard so the rule is enforced mechanically, not by promise.
#
#   python3 evolution/absorb_apply.py <target-project-path> <skill_id> [--go]
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BOX_SKILLS = (REPO / "star-alliance-skills").resolve()      # the ONE sink
DISARMED = HERE / "DISARMED"

sys.path.insert(0, str(HERE))
import ledger        # noqa: E402
import verdict       # noqa: E402
import absorb        # noqa: E402


def _sink_guard(dest: Path) -> Path:
    """Resolve <dest> and REFUSE anything not strictly inside star-alliance-skills/.

    This is the mechanical guarantee that an absorbed skill can only ever land in
    the box — never under ~/.claude, never a project's own .claude/skills. Every
    write in this module funnels through here. Raises SystemExit on a bad target."""
    rp = dest.resolve()
    if rp != BOX_SKILLS and BOX_SKILLS not in rp.parents:
        raise SystemExit(f"[absorb] REFUSED — write target {rp} is outside the box {BOX_SKILLS}")
    low = str(rp).lower()
    if f"{os.sep}.claude{os.sep}" in low or low.endswith(f"{os.sep}.claude"):
        raise SystemExit(f"[absorb] REFUSED — {rp} is a .claude/ path; the box is the only sink")
    return rp


def _build() -> None:
    bp = REPO / "build.py"
    if bp.is_file():
        subprocess.run(["python3", str(bp)], cwd=str(REPO), check=False)


def apply(target: str, skill_id: str, go: bool = False, timeout: int = 180) -> dict:
    if DISARMED.exists():
        raise SystemExit("[absorb] DISARMED — engine kill switch is set; refusing.")

    # 1. re-derive the candidate (reuse absorb.scan — one source of diff logic)
    cands = {c["skill_id"]: c for c in absorb.scan(target)}
    c = cands.get(skill_id)
    if not c:
        raise SystemExit(
            f"[absorb] no candidate '{skill_id}' in {target} "
            f"(already absorbed, identical, or not present?)")
    src = Path(c["source"])
    new_text = src.read_text(encoding="utf-8")

    # 2. INDEPENDENT critic on the proposed skill
    box_file = BOX_SKILLS / skill_id / "SKILL.md"
    if c["kind"] == "improved" and box_file.is_file():
        review = (f"# ABSORB — improve skill '{skill_id}' (box <- target {target})\n\n"
                  f"## proposed replacement\n{new_text}\n")
    else:
        review = f"# ABSORB — NEW skill '{skill_id}' proposed for the box\n\n{new_text}\n"
    v = verdict.run_cold(review, timeout=timeout)
    ledger.append("verdict", author=v.model or "critic", surface="skills", tier="A",
                  diff_hash=c["target_hash"], verdict=v.decision,
                  detail=f"absorb critic verdict for '{skill_id}': {v.decision}",
                  meta={"absorb": True, "skill_id": skill_id})

    if v.is_block:
        ledger.append("block", author="evolution-absorb", surface="skills", tier="A",
                      diff_hash=c["target_hash"], verdict="block",
                      detail=f"absorb BLOCKED for '{skill_id}' by critic")
        raise SystemExit(f"[absorb] BLOCKED by critic — nothing written.\n{v.raw}")
    if not v.reached:
        # critic unreachable → FAIL CLOSED. Leave the proposal queued.
        raise SystemExit(f"[absorb] critic unreachable ({v.decision}) — FAIL CLOSED, "
                         f"left queued. Retry when the critic is reachable.")

    # 3. HUMAN GATE — a critic pass is necessary, not sufficient.
    go = go or os.environ.get("SA_ABSORB_GO") == "1"
    if not go:
        print(f"[absorb] critic {v.decision.upper()} for '{skill_id}'. Ready to absorb. "
              f"Re-run with --go (or SA_ABSORB_GO=1) to write it into the box.")
        return {"written": False, "verdict": v.decision, "skill_id": skill_id}

    # 4. WRITE — the ONLY sink, guarded per file. Copies the whole skill folder.
    dest_dir = _sink_guard(BOX_SKILLS / skill_id)
    src_dir = src.parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    for root, _dirs, files in os.walk(src_dir):
        rel = Path(root).relative_to(src_dir)
        for fn in files:
            out = _sink_guard(dest_dir / rel / fn)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(root) / fn, out)

    ledger.append("change", author="evolution-absorb", surface="skills", tier="A",
                  diff_hash=c["target_hash"], verdict=v.decision,
                  detail=f"absorbed skill '{skill_id}' into the box ({c['kind']})",
                  meta={"absorb": True, "skill_id": skill_id, "source": str(src)})
    _build()
    print(f"[absorb] WROTE '{skill_id}' into {dest_dir} and regenerated (build.py).")
    return {"written": True, "verdict": v.decision, "skill_id": skill_id}


def _cli():
    import argparse
    ap = argparse.ArgumentParser(
        prog="absorb_apply",
        description="CHANGE inward: critic-gate + human-gate one proposed skill, then "
                    "write it into star-alliance-skills/ (the ONLY sink).")
    ap.add_argument("target", help="path to the deployed target project")
    ap.add_argument("skill_id", help="the skill id to absorb (from absorb.py output)")
    ap.add_argument("--go", action="store_true", help="explicit human go — write on a critic pass")
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()
    r = apply(a.target, a.skill_id, go=a.go, timeout=a.timeout)
    print(f"[absorb] result: {r}")


if __name__ == "__main__":
    _cli()
