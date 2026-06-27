"""wire.py — Arsenal / Skill / Workflow Forge: read a spec JSON, update the right
registry, optionally propagate to member loadouts, then rebuild guild-data.

Registries by --kind:
    weapon    -> star-alliance-arsenal/models-usage.json  (arsenal usage entry)
    skill     -> skills-meta.json                          (per-skill presentation)
    workflow  -> workflows.json                            (a workflow definition)

CLI:
    python3 guild/wire.py --kind weapon|skill|workflow --spec <spec.json>
                          [--propagate loadouts] [--dry-run]

The spec JSON shape:
    weapon:    {"id": "...", "entry": {...}}        # entry merged under models-usage[id]
    skill:     {"id": "...", "entry": {...}}        # entry merged under skills-meta[id]
    workflow:  {"id": "...", "workflow": {...}}     # upserted into workflows.json.workflows[]

--dry-run prints the planned mutations and exits WITHOUT writing or rebuilding.
A missing/invalid spec exits non-zero with a clear message (no traceback).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD = REPO_ROOT / "build.py"

REGISTRY = {
    "weapon": REPO_ROOT / "star-alliance-arsenal" / "models-usage.json",
    "skill": REPO_ROOT / "skills-meta.json",
    "workflow": REPO_ROOT / "workflows.json",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_spec(spec_path: Path) -> dict:
    if not spec_path.exists():
        raise SystemExit(f"spec file not found: {spec_path}")
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"spec is not valid JSON ({spec_path}): {exc}")
    if not isinstance(spec, dict):
        raise SystemExit(f"spec must be a JSON object, got {type(spec).__name__}")
    if not spec.get("id"):
        raise SystemExit("spec is missing a top-level \"id\"")
    return spec


def plan_mutations(kind: str, spec: dict) -> list[str]:
    """Compute (but do not apply) the mutations; return a human-readable plan."""
    reg_path = REGISTRY[kind]
    if not reg_path.exists():
        raise SystemExit(f"registry for {kind} not found: {reg_path}")
    reg = _load_json(reg_path)
    sid = spec["id"]
    plan: list[str] = []

    if kind == "workflow":
        wf = spec.get("workflow")
        if not isinstance(wf, dict):
            raise SystemExit("workflow spec needs a \"workflow\" object")
        existing = {w.get("id") for w in reg.get("workflows", [])}
        verb = "update" if sid in existing else "add"
        plan.append(f"{verb} workflow {sid!r} in workflows.json")
    else:
        entry = spec.get("entry")
        if not isinstance(entry, dict):
            raise SystemExit(f"{kind} spec needs an \"entry\" object")
        verb = "update" if sid in reg else "add"
        plan.append(f"{verb} {kind} {sid!r} in {reg_path.name}")
    return plan


def apply_mutations(kind: str, spec: dict) -> None:
    reg_path = REGISTRY[kind]
    reg = _load_json(reg_path)
    sid = spec["id"]

    if kind == "workflow":
        wf = spec["workflow"]
        wf.setdefault("id", sid)
        wfs = reg.setdefault("workflows", [])
        for i, w in enumerate(wfs):
            if w.get("id") == sid:
                wfs[i] = wf
                break
        else:
            wfs.append(wf)
    else:
        entry = dict(reg.get(sid) or {})
        entry.update(spec["entry"])
        reg[sid] = entry

    reg_path.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def propagate_loadouts(kind: str, spec: dict, dry_run: bool) -> list[str]:
    """Add a skill/weapon to the member loadouts named in spec['propagate_to'].

    Only applies to kind weapon|skill. Member source of truth is guild-data.json;
    the actual loadout edit belongs in each member's .md frontmatter, so here we
    only REPORT the intended propagation and leave the .md edit to build inputs —
    keeping wire.py from silently rewriting member prompts.
    """
    targets = spec.get("propagate_to") or []
    notes: list[str] = []
    if kind == "workflow":
        notes.append("propagate: n/a for workflow kind (skipped)")
        return notes
    if not targets:
        notes.append("propagate: spec has no \"propagate_to\" list — nothing to do")
        return notes
    for mid in targets:
        notes.append(f"propagate: would add {kind} {spec['id']!r} to member {mid!r} loadout"
                     + ("" if dry_run else " (edit member .md, then rebuild)"))
    return notes


def run_build() -> int:
    if not BUILD.exists():
        print(f"ERROR: build.py not found at {BUILD}", file=sys.stderr)
        return 1
    proc = subprocess.run(["python3", str(BUILD)], cwd=str(REPO_ROOT))
    return proc.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="Forge — wire a weapon/skill/workflow into its registry")
    ap.add_argument("--kind", required=True, choices=("weapon", "skill", "workflow"))
    # --in is the workflow-runner's file-rail alias for --spec
    # (resolve_io_args supplies --in from the step's first `inputs` entry).
    ap.add_argument("--spec", "--in", dest="spec", required=True, help="Path to the spec JSON")
    ap.add_argument("--propagate", choices=("loadouts",), default=None,
                    help="Propagate a skill/weapon into member loadouts")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print planned mutations; write nothing and skip the rebuild")
    # Tolerate the runner's --out rail (this step writes its own registry target).
    ap.add_argument("--out", dest="_out", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.is_absolute():
        spec_path = (REPO_ROOT / spec_path).resolve()

    try:
        spec = load_spec(spec_path)
        plan = plan_mutations(args.kind, spec)
    except SystemExit as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"wire: kind={args.kind} spec={spec_path}")
    for line in plan:
        print(f"  plan: {line}")

    if args.propagate == "loadouts":
        for note in propagate_loadouts(args.kind, spec, args.dry_run):
            print(f"  {note}")

    if args.dry_run:
        print("dry-run: nothing written, no rebuild. Re-run without --dry-run to apply.")
        return 0

    try:
        apply_mutations(args.kind, spec)
    except SystemExit as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR applying mutations: {exc}", file=sys.stderr)
        return 1
    print("  applied registry mutation.")

    code = run_build()
    if code != 0:
        print(f"ERROR: build.py exited {code} after wiring", file=sys.stderr)
        return code
    print("wire: done — registry updated and guild-data rebuilt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
