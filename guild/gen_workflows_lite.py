#!/usr/bin/env python3
"""gen_workflows_lite.py — generate star-alliance-arsenal/workflows-lite.json
from workflows.json (the SINGLE SOURCE OF TRUTH for all workflows).

workflows-lite.json is the universal subset shipped into NON-guild projects (the
portable install). It must never be hand-edited: it is a faithful copy of the LITE_IDS
entries from workflows.json, so it can never drift from the source.

Usage:
  python3 guild/gen_workflows_lite.py            # regenerate the file
  python3 guild/gen_workflows_lite.py --check    # exit 1 if the file is stale

The set of portable workflow ids lives HERE (one place) — add an id to LITE_IDS to
ship another workflow into portable installs.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

REPO = next((p for p in Path(__file__).resolve().parents
             if (p / "workflows.json").exists() and (p / ".git").exists()),
            Path(__file__).resolve().parent.parent)

SRC = REPO / "workflows.json"
DST = REPO / "star-alliance-arsenal" / "workflows-lite.json"

# The portable subset — universal workflows that make sense in any project.
LITE_IDS = [
    "standard-mission", "quick-fix", "design-sprint", "architecture-build",
    "bug-cycle", "security-sweep", "comms-triage", "inquiry-recon", "conversation",
]
NOTE = ("workflows-lite — universal subset for non-guild projects. GENERATED from "
        "workflows.json by guild/gen_workflows_lite.py — do not hand-edit.")


def build() -> dict:
    src = json.loads(SRC.read_text())
    wfs = src.get("workflows", src) if isinstance(src, dict) else src
    by_id = {w.get("id"): w for w in wfs}
    missing = [i for i in LITE_IDS if i not in by_id]
    if missing:
        sys.stderr.write(f"gen_workflows_lite: ids not in workflows.json: {missing}\n")
    chosen = [by_id[i] for i in LITE_IDS if i in by_id]   # verbatim copy, source order by LITE_IDS
    return {"version": src.get("version", 1) if isinstance(src, dict) else 1,
            "note": NOTE, "workflows": chosen}


def serialize(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    out = serialize(build())
    if "--check" in sys.argv:
        cur = DST.read_text() if DST.exists() else ""
        if cur != out:
            sys.stderr.write(f"STALE {DST.name} — run: python3 guild/gen_workflows_lite.py\n")
            return 1
        print(f"ok  {DST.name} matches workflows.json ({len(LITE_IDS)} workflows)")
        return 0
    DST.write_text(out)
    print(f"wrote {DST.relative_to(REPO)} ({len(build()['workflows'])} workflows from workflows.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
