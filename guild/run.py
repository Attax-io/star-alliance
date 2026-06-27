"""run.py — execute a workflow by name from workflows.json.

CLI:
    python3 guild/run.py "<Workflow Name>" [--dry-run] [--state-dir runs/<id>]

Loads workflows.json from REPO_ROOT, finds the workflow by name (case-insensitive),
and resolves each step to a script, prose (delegate) call, or human handoff.
Writes per-step outputs plus a run_summary.md into the state directory.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Allow `from delegate import delegate` when this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from delegate import delegate  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_JSON = REPO_ROOT / "workflows.json"

# Step titles that mean "wait for a human" — never automated.
HUMAN_TITLES = {
    "place the order",
    "report the bug",
    "request the build",
    "ask the question",
}

DEFAULT_WEAPON = "minimax-m3"


def slugify(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").lower()
    return s or "step"


def find_workflow(name: str) -> dict:
    if not WORKFLOWS_JSON.exists():
        raise SystemExit(f"workflows.json not found at {WORKFLOWS_JSON}")
    try:
        data = json.loads(WORKFLOWS_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to parse workflows.json: {exc}")
    target = name.strip().lower()
    for wf in data.get("workflows", []):
        if (wf.get("name") or "").strip().lower() == target:
            return wf
    avail = ", ".join((w.get("name") or "?") for w in data.get("workflows", []))
    raise SystemExit(f"workflow not found: {name!r}. available: {avail}")


def resolve_step(step: dict) -> str:
    """Return 'script:<path>', 'prose:<actor>/<weapon>', or 'human'."""
    title = (step.get("title") or "").strip()
    title_lc = title.lower()
    actor = (step.get("actor") or "").strip().lower()
    # A gate is a human-approval checkpoint (Butler report-back / your-go).
    # It must NEVER route to a weapon — the runner halts and awaits a human.
    if step.get("kind") == "gate" or step.get("gate"):
        return "human"
    if actor in ("user", "you") or title_lc in HUMAN_TITLES:
        return "human"
    explicit = (step.get("script") or "").strip()
    if explicit:
        return f"script:{explicit}"
    weapon = (step.get("weapon") or DEFAULT_WEAPON).strip()
    return f"prose:{(actor or 'agent')}/{weapon}"


def args_to_flags(args: dict | None) -> list[str]:
    """Translate a step's `args` object into ['--key', 'value', ...] CLI flags.

    Backward-compatible: a step with no `args` yields an empty list, so its
    invocation is unchanged. Boolean True becomes a bare `--flag`; False/None
    are omitted. Everything else is stringified.
    """
    flags: list[str] = []
    for key, val in (args or {}).items():
        flag = f"--{key}"
        if val is True:
            flags.append(flag)
        elif val is False or val is None:
            continue
        else:
            flags += [flag, str(val)]
    return flags


def _artifact_path(name: str, state_dir: Path) -> Path:
    """Resolve a produces/inputs key to a concrete file path under state_dir.

    A bare key (e.g. "raw request") becomes a slugged .md file in state_dir; a
    path-like value is resolved repo-relative if not absolute.
    """
    if "/" in name or name.endswith((".md", ".txt", ".json")):
        p = Path(name)
        return p if p.is_absolute() else (REPO_ROOT / name).resolve()
    p = state_dir / f"{slugify(name)}.md"
    return p


def resolve_io_args(args: dict, step: dict, state_dir: Path) -> dict:
    """Fill in --in / --out for a script step from its inputs / produces.

    Only fills what the step's `args` did not set explicitly, so authors keep
    full control. Used for framing/planning steps where the file rails are
    boilerplate.
    """
    out = dict(args)
    if "in" not in out:
        inputs = step.get("inputs") or []
        if inputs:
            out["in"] = str(_artifact_path(str(inputs[0]), state_dir))
    if "out" not in out:
        produces = (step.get("produces") or "").strip()
        if produces:
            out["out"] = str(_artifact_path(produces, state_dir))
    return out


def run_script(path: str, args: dict | None = None) -> tuple[int, str, str]:
    """Run a script via python3 (with optional --key value flags from `args`).

    Returns (exit_code, stdout, stderr).
    """
    p = Path(path)
    if not p.is_absolute():
        p = (REPO_ROOT / path).resolve()
    if not p.exists():
        return 1, "", f"script not found: {p}"
    cmd = ["python3", str(p)] + args_to_flags(args)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=1800,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout running {p}"
    except Exception as exc:
        return 1, "", f"failed to run {p}: {exc}"


def render_prose_prompt(step: dict) -> str:
    """step['act'] concatenated with the contents of any step['inputs']."""
    prompt = step.get("act") or ""
    for inp in step.get("inputs") or []:
        ip = Path(inp)
        if not ip.is_absolute():
            ip = (REPO_ROOT / inp).resolve()
        if ip.exists() and ip.is_file():
            try:
                prompt += "\n\n" + ip.read_text(encoding="utf-8")
            except Exception as exc:
                prompt += f"\n\n[could not load {inp}: {exc}]"
        else:
            prompt += f"\n\n[input not found: {inp}]"
    return prompt


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a Star Alliance workflow by name")
    ap.add_argument("name", help="Workflow name (case-insensitive)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the resolution of each step without executing")
    ap.add_argument("--state-dir", default=None,
                    help="Where to write step outputs (default: runs/<workflow id>)")
    args = ap.parse_args()

    try:
        wf = find_workflow(args.name)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    wf_id = wf.get("id") or slugify(wf.get("name", "workflow"))
    state_dir = Path(args.state_dir) if args.state_dir else Path("runs") / wf_id
    if not state_dir.is_absolute():
        state_dir = (REPO_ROOT / state_dir).resolve()
    state_dir.mkdir(parents=True, exist_ok=True)

    steps = wf.get("steps") or []
    total = len(steps)
    summary: list[str] = [
        f"# Run Summary: {wf.get('name', wf_id)}",
        "",
        f"- Workflow id: {wf_id}",
        f"- State dir: {state_dir}",
        f"- Dry run: {args.dry_run}",
        "",
        "| # | Step | Resolution |",
        "|---|------|------------|",
    ]

    halted = False
    halt_reason = ""

    for i, step in enumerate(steps, 1):
        title = step.get("title") or f"step {i}"
        resolution = resolve_step(step)
        print(f"[{i}/{total}] {title}  ->  ({resolution})")
        summary.append(f"| {i} | {title} | {resolution} |")

        if resolution == "human":
            # A gate is a hard human-approval checkpoint: the runner MUST halt and
            # await a human "go" — it can never be skipped. A passive human step
            # (actor `you`, e.g. "Place the Order") just continues.
            if step.get("kind") == "gate" or step.get("gate"):
                halted = True
                halt_reason = (f"step {i} '{title}' — approval gate: "
                               f"{step.get('label') or 'awaiting human go'}")
                print(f"  ⏸ {halt_reason}")
                break
            continue

        try:
            if resolution.startswith("script:"):
                path = resolution.split(":", 1)[1]
                step_args = step.get("args") if isinstance(step.get("args"), dict) else None
                if step_args:
                    # Steps that carry `args` get their file rails wired: --in from
                    # the step's first input (resolved to a state_dir/repo path) and
                    # --out from `produces`, unless the args set them explicitly.
                    step_args = resolve_io_args(step_args, step, state_dir)
                flags = args_to_flags(step_args)
                if args.dry_run:
                    shown_cmd = f"python3 {path}" + (f" {' '.join(flags)}" if flags else "")
                    print(f"   (dry-run) would run: {shown_cmd}")
                    continue
                code, _out, err = run_script(path, step_args)
                if code != 0 and step.get("gate"):
                    halted = True
                    halt_reason = (f"step {i} '{title}' (gate) exited {code}: "
                                   f"{(err or _out).strip()[:300]}")
                    print(f"  ! {halt_reason}")
                    break
                if step.get("verify"):
                    vcode, _vout, verr = run_script(step["verify"])
                    if vcode != 0:
                        halted = True
                        halt_reason = (f"step {i} '{title}' verify exited {vcode}: "
                                       f"{(verr or _vout).strip()[:300]}")
                        print(f"  ! {halt_reason}")
                        break
                continue

            if resolution.startswith("prose:"):
                if args.dry_run:
                    print("   (dry-run) would invoke delegate")
                    continue
                weapon = (step.get("weapon") or DEFAULT_WEAPON).strip()
                prompt = render_prose_prompt(step)
                out = delegate(weapon, prompt)
                produces = (step.get("produces") or "").strip()
                if produces:
                    out_name = produces
                else:
                    out_name = f"{i}_{slugify(title)}.md"
                out_path = state_dir / out_name
                if not out_path.suffix:
                    out_path = out_path.with_suffix(".md")
                out_path.write_text(out, encoding="utf-8")
                try:
                    shown = out_path.relative_to(REPO_ROOT)
                except ValueError:
                    shown = out_path
                print(f"   wrote {shown}")
        except Exception as exc:
            print(f"  ! error: {exc}")
            if resolution.startswith("script:") and step.get("gate"):
                halted = True
                halt_reason = f"step {i} '{title}' raised {type(exc).__name__}: {exc}"
                break
            continue

    summary.append("")
    if halted:
        summary.append(f"**HALTED**: {halt_reason}")
    else:
        summary.append("**Completed** all steps.")

    try:
        (state_dir / "run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"ERROR writing run_summary.md: {exc}", file=sys.stderr)

    return 1 if halted else 0


if __name__ == "__main__":
    sys.exit(main())
