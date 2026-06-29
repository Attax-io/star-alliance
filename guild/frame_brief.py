"""frame_brief.py — the Butler's framing step as a runnable primitive.

Collapses the near-identical prose framing steps that open most workflows
("Restate the Order" / "Clarify the Ask" / "Shape the Brief" / "Classify" /
"Reframe") into one templated call to a framing weapon. Reads a raw request
(a file path or literal text), asks the weapon to emit a structured brief
(one-line summary, scope / what-will-be-touched, acceptance criteria),
and writes it to --out.

Importable API:
    frame_brief(style, request, weapon="minimax-m3") -> str

CLI:
    python3 guild/frame_brief.py --style restate|clarify|shape|classify|reframe \
        --in <request_file_or_text> --out <brief.md> [--weapon <model>]

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

# Per-style framing instructions. Each emits the same structured brief shape
# (summary / scope / acceptance) but with a style-appropriate emphasis.
STYLES: dict[str, str] = {
    "restate": (
        "Restate the order plainly. Strip ceremony and ambiguity; capture the "
        "true intent of the request exactly as given, adding nothing new."
    ),
    "clarify": (
        "Clarify the ask into a single, unambiguous ticket. Resolve vagueness "
        "into concrete, testable requirements; call out any assumptions you make."
    ),
    "shape": (
        "Shape the brief for the work ahead. Frame the request as a crisp brief "
        "the rest of the guild can act on without re-asking the requester."
    ),
    "classify": (
        "Classify the request. Identify its type, the workflow it belongs to, and "
        "the agents/skills it should route to, then frame it accordingly."
    ),
    "reframe": (
        "Reframe the request from the guild's vantage. Sharpen the underlying "
        "question and surface what is really being asked beneath the surface ask."
    ),
}

_SYSTEM_TEMPLATE = """You are the Butler of the Star Alliance guild — the framing voice that turns a raw request into a clear, actionable brief before any work begins.

{style_directive}

Emit ONLY the brief as Markdown, in exactly this shape (no preamble, no closing remarks):

# Brief

**Summary:** <one sentence capturing the request>

## Scope — what will be touched
- <bullets naming the files / surfaces / areas in play; "unknown — needs discovery" if genuinely unclear>

## Acceptance criteria
- <concrete, checkable conditions that mean the work is done>

Keep it tight. Do not invent requirements the request does not support. If the request is too thin to frame responsibly, say so under Summary and list what is missing under Acceptance criteria."""


def _resolve_request(raw: str) -> str:
    """If `raw` is an existing file path, return its contents; else the literal text."""
    candidate = Path(raw)
    try:
        if candidate.exists() and candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    except OSError:
        pass
    return raw


def frame_brief(style: str, request: str, weapon: str = DEFAULT_WEAPON) -> str:
    """Frame `request` into a structured brief via the framing weapon.

    `request` may be a file path or literal text. Raises ValueError on an
    unknown style and propagates RuntimeError from delegate() on failure.
    """
    key = (style or "").strip().lower()
    if key not in STYLES:
        raise ValueError(
            f"unknown style {style!r}; choose one of {', '.join(sorted(STYLES))}"
        )
    text = _resolve_request(request).strip()
    if not text:
        raise ValueError("empty request — nothing to frame")
    system = _SYSTEM_TEMPLATE.format(style_directive=STYLES[key])
    prompt = "Raw request to frame:\n\n" + text
    return delegate(weapon, prompt, system=system).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Frame a raw request into a structured brief")
    ap.add_argument("--style", required=True, choices=sorted(STYLES),
                    help="Framing style")
    ap.add_argument("--in", dest="inp", required=True,
                    help="Request: a file path OR literal text")
    ap.add_argument("--out", required=True, help="Path to write the brief markdown")
    ap.add_argument("--weapon", default=DEFAULT_WEAPON,
                    help=f"Framing weapon (default: {DEFAULT_WEAPON})")
    args = ap.parse_args()

    try:
        brief = frame_brief(args.style, args.inp, weapon=args.weapon)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(brief + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"ERROR writing {out_path}: {exc}", file=sys.stderr)
        return 1

    print(f"framed ({args.style}) -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
