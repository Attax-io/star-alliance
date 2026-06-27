"""sync_act.py — keep each scripted step's `act` prose in sync with its script.

For every workflows.json step that carries a `script`, the script's module
docstring (first line) is the single source of truth. This tool derives a
normalized one-liner — "Runs `<script>` — <docstring first line>." — and either
reports drift (--check, exits non-zero on any mismatch) or rewrites the step's
`act` to match (--write). Keeps workflows.json valid JSON.

CLI:
    python3 guild/sync_act.py --check  [--workflow <name>]
    python3 guild/sync_act.py --write  [--workflow <name>]
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_JSON = REPO_ROOT / "workflows.json"


def script_docstring_first_line(script: str) -> str | None:
    """First line of the target script's module docstring, with any leading
    "<basename> — " / "<basename>: " / "<basename> - " prefix stripped.

    Returns None if the script or its docstring is missing.
    """
    p = Path(script)
    if not p.is_absolute():
        p = (REPO_ROOT / script).resolve()
    if not p.exists():
        return None
    try:
        doc = ast.get_docstring(ast.parse(p.read_text(encoding="utf-8")))
    except Exception:
        return None
    if not doc:
        return None
    first = doc.strip().splitlines()[0].strip()
    base = re.escape(p.name)
    first = re.sub(rf"^{base}\s*(?:—|–|-|:)\s*", "", first).strip()
    # Drop a trailing comma left over from a wrapped docstring sentence.
    first = first.rstrip(",").strip()
    return first or None


def expected_act(script: str, desc: str) -> str:
    desc = desc.rstrip(".").strip()
    return f"Runs `{script}` — {desc}."


def iter_scripted_steps(data: dict, only_workflow: str | None):
    """Yield (workflow, step) for every step carrying a `script`."""
    target = only_workflow.strip().lower() if only_workflow else None
    for wf in data.get("workflows", []):
        if target and (wf.get("name") or "").strip().lower() != target:
            continue
        for step in wf.get("steps", []):
            if (step.get("script") or "").strip():
                yield wf, step


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Sync scripted steps' act prose with the script docstring (SSOT)."
    )
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="Report mismatches; exit non-zero if any drift.")
    mode.add_argument("--write", action="store_true",
                      help="Overwrite each scripted step's `act` to match its script.")
    ap.add_argument("--workflow", default=None,
                    help="Limit to one workflow (by name, case-insensitive).")
    args = ap.parse_args()

    if not WORKFLOWS_JSON.exists():
        print(f"workflows.json not found at {WORKFLOWS_JSON}", file=sys.stderr)
        return 2
    try:
        data = json.loads(WORKFLOWS_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"failed to parse workflows.json: {exc}", file=sys.stderr)
        return 2

    mismatches: list[str] = []
    missing: list[str] = []
    changed = 0
    checked = 0

    for wf, step in iter_scripted_steps(data, args.workflow):
        script = (step.get("script") or "").strip()
        desc = script_docstring_first_line(script)
        if desc is None:
            missing.append(f"{wf.get('name')} :: {step.get('title')} -> {script} "
                           f"(no script or no module docstring)")
            continue
        checked += 1
        want = expected_act(script, desc)
        have = step.get("act") or ""
        if have == want:
            continue
        if args.write:
            step["act"] = want
            changed += 1
        else:
            mismatches.append(
                f"{wf.get('name')} :: {step.get('title')}\n"
                f"    have: {have}\n"
                f"    want: {want}"
            )

    if missing:
        for m in missing:
            print(f"  ! {m}", file=sys.stderr)

    if args.write:
        if changed:
            WORKFLOWS_JSON.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        print(f"sync_act --write: normalized {changed} of {checked} scripted step(s).")
        return 1 if missing else 0

    # --check
    if mismatches:
        print(f"sync_act --check: {len(mismatches)} drift(s) of {checked} scripted step(s):")
        for m in mismatches:
            print(m)
        return 1
    if missing:
        print(f"sync_act --check: {checked} scripted step(s) in sync, "
              f"but {len(missing)} script(s) missing/undocumented.")
        return 1
    print(f"sync_act --check: all {checked} scripted step(s) in sync.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
