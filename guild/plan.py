"""plan.py — the Strategist's planning step as a runnable primitive.

Takes a framed brief and routes it to a thinker weapon with a per-template
system prompt, producing a plan: waves/roles/checkpoints (campaign), tickets
(sprint), a scope document (scope), a spec (spec), an audit lens (lens), or
panel seating (panel).

Importable API:
    plan(template, brief, weapon="minimax-m3") -> str

CLI:
    python3 guild/plan.py --template campaign|sprint|scope|spec|lens|panel \
        --in <brief> --out <plan.md> [--weapon <model>]

Default weapon is minimax-m3 (cheap, unattended-friendly). It reuses
guild/delegate.py's delegate(), so token spend auto-logs to the arsenal ledger.

Exit 0 on success, non-zero on failure.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `from delegate import delegate` when run directly or imported.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from delegate import delegate  # noqa: E402

DEFAULT_WEAPON = "minimax-m3"

# Per-template planning directives. Each shapes the same brief into a
# different deliverable the downstream agents can act on.
TEMPLATES: dict[str, str] = {
    "campaign": (
        "Produce a CAMPAIGN PLAN: break the work into ordered waves. For each "
        "wave give its goal, the agent roles it engages, and a checkpoint that "
        "decides whether to proceed. End with the overall success condition."
    ),
    "sprint": (
        "Produce a SPRINT PLAN as a list of tickets. Each ticket: a title, the "
        "owning agent, a one-line acceptance criterion, and its dependencies. "
        "Order them so dependencies come first."
    ),
    "scope": (
        "Produce a SCOPE DOCUMENT: what is in scope, what is explicitly out of "
        "scope, the surfaces/files touched, known risks, and the assumptions the "
        "work rests on."
    ),
    "spec": (
        "Produce a SPEC: the precise behaviour to build, inputs and outputs, edge "
        "cases, and the verification that proves it correct. Be concrete enough to "
        "implement against without further questions."
    ),
    "lens": (
        "Produce an AUDIT LENS: the dimensions to evaluate against, what 'good' "
        "looks like on each, and the evidence to gather. This is the rubric a "
        "reviewer will apply, not the audit itself."
    ),
    "panel": (
        "Produce PANEL SEATING: name the distinct expert perspectives to convene, "
        "the question each one owns, and how their verdicts will be converged and "
        "graded into a single answer."
    ),
}

_SYSTEM_TEMPLATE = """You are the Strategist of the Star Alliance guild — the planner who turns a framed brief into an actionable plan before the guild executes.

{template_directive}

Emit ONLY the plan as Markdown. Start with a single-sentence objective, then the structured plan. No preamble, no closing remarks. Ground every item in the brief — do not invent scope the brief does not support. If the brief is too thin to plan responsibly, say so and list what is missing."""


def _resolve_brief(raw: str) -> str:
    """If `raw` is an existing file path, return its contents; else the literal text."""
    candidate = Path(raw)
    try:
        if candidate.exists() and candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    except OSError:
        pass
    return raw


def plan(template: str, brief: str, weapon: str = DEFAULT_WEAPON) -> str:
    """Turn `brief` into a plan via the thinker weapon.

    `brief` may be a file path or literal text. Raises ValueError on an unknown
    template and propagates RuntimeError from delegate() on failure.
    """
    key = (template or "").strip().lower()
    if key not in TEMPLATES:
        raise ValueError(
            f"unknown template {template!r}; choose one of {', '.join(sorted(TEMPLATES))}"
        )
    text = _resolve_brief(brief).strip()
    if not text:
        raise ValueError("empty brief — nothing to plan")
    system = _SYSTEM_TEMPLATE.format(template_directive=TEMPLATES[key])
    prompt = "Brief to plan from:\n\n" + text
    return delegate(weapon, prompt, system=system).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Turn a brief into a plan")
    ap.add_argument("--template", required=True, choices=sorted(TEMPLATES),
                    help="Plan template")
    ap.add_argument("--in", dest="inp", required=True,
                    help="Brief: a file path OR literal text")
    ap.add_argument("--out", required=True, help="Path to write the plan markdown")
    ap.add_argument("--weapon", default=DEFAULT_WEAPON,
                    help=f"Thinker weapon (default: {DEFAULT_WEAPON})")
    args = ap.parse_args()

    try:
        out_text = plan(args.template, args.inp, weapon=args.weapon)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_text + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"ERROR writing {out_path}: {exc}", file=sys.stderr)
        return 1

    print(f"planned ({args.template}) -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
