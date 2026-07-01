"""command.py — the Butler's down-command composer (Leader's Command, as a runnable primitive).

Where frame_brief.py frames the Guild Master's request UP into a brief, command.py
issues the order DOWN: it takes an intent (the Guild Master's words, or a brief) and a
target subordinate type, and drafts a single concise, precise, complete order in the
seven-axiom shape so the subordinate executes correctly first-time — no clarification
round-trips, minimal tokens.

The order shape (adapts the military BLUF / SMEAC order):
    ORDER (BLUF) · INTENT (end-state + why) · CONTEXT (facts it can't see) ·
    CONSTRAINTS (scope + anti-goals) · OUTPUT CONTRACT (return shape + acceptance)

Right-sizing (axiom 7) is chosen by --target:
    doer     — full spec in the prompt; stateless; no autonomy assumed (maps to summon -s/-f)
    subagent — full spec + output contract; one-shot, isolated, no shared memory
    agent    — intent + latitude (mission command); trust the craft, don't micro-spec
    human    — plain English, BLUF, options + a recommendation; minimal jargon

Importable API:
    compose_command(target, intent, weapon="minimax-sub") -> str

CLI:
    python3 guild/command.py --target doer|subagent|agent|human \
        --in <intent_file_or_text> --out <order.md> [--weapon <model>]

Default weapon is minimax-sub (cheap, unattended-friendly). Reuses guild/delegate.py's
delegate(), so token spend auto-logs to the arsenal ledger. Exit 0 on success.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from delegate import delegate  # noqa: E402

DEFAULT_WEAPON = "minimax-sub"

# Per-target right-sizing directive (axiom 7: match the order to who executes it).
TARGETS: dict[str, str] = {
    "doer": (
        "The subordinate is a DOER weapon (a model that returns text, has no tools, no "
        "memory, and one shot). Put the ENTIRE spec in the order — it cannot look anything "
        "up or ask back. Be maximally explicit about the output contract. (In execution the "
        "ORDER/INTENT/CONSTRAINTS/OUTPUT-CONTRACT become the -s system prompt and the CONTEXT "
        "material becomes the -f file.)"
    ),
    "subagent": (
        "The subordinate is a SUBAGENT (an isolated Claude agent with tools but NO shared "
        "memory of this conversation). Include every fact, path, and prior decision it needs; "
        "state exactly what files it may touch and the exact shape of the result it must return."
    ),
    "agent": (
        "The subordinate is a peer MEMBER with their own craft. Command by INTENT, not "
        "micro-steps (mission command): give the end-state, the why, and the bounds, then "
        "trust the agent to choose the method. Keep latitude wide inside clear constraints."
    ),
    "human": (
        "The subordinate is the GUILD MASTER (a human, NOT a programmer). Write in plain "
        "English with the bottom line first, no jargon. Where a decision is theirs, present "
        "2-3 options with a clear recommendation rather than a wall of detail."
    ),
}

_SYSTEM_TEMPLATE = """You are the Butler of the Star Alliance guild — the commander who takes the Guild Master's words and re-issues them DOWN to a subordinate as a single clear, precise, complete order. A good order transfers exactly enough intent and spec for correct one-shot execution and not one word more: too little and the subordinate guesses wrong or asks back (a costly round-trip); too much and the signal buries. Compose the minimal sufficient order.

Target subordinate: {target_directive}

Apply the seven axioms: (1) intent first; (2) bottom line up front; (3) one reading — kill every ambiguity, name the exact file/function/number/format; (4) complete the brief — assume no shared memory, include every fact it cannot look up; (5) bound the field — scope and explicit anti-goals; (6) contract the return — exact output shape plus acceptance criteria; (7) right-size to the subordinate above.

Emit ONLY the order as Markdown, in exactly this shape (no preamble, no closing remarks):

# Order

**Order:** <one line — the deliverable, bottom line up front>

**Intent:** <the end-state and why, one or two lines>

## Context — what the subordinate cannot see
- <every fact, path, prior decision, or example it needs; "none needed" if truly self-contained>

## Constraints
- <scope, limits, and explicit anti-goals — what NOT to do or touch>

## Output contract
- <the exact shape of the result + concrete acceptance criteria that mean it is done correctly>

Keep it tight and unambiguous. Do not invent requirements the intent does not support. If the intent is too thin to command responsibly, say so under Order and list what is missing under Output contract."""


def _resolve_request(raw: str) -> str:
    """If `raw` is an existing file path, return its contents; else the literal text."""
    candidate = Path(raw)
    try:
        if candidate.exists() and candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    except OSError:
        pass
    return raw


def compose_command(target: str, intent: str, weapon: str = DEFAULT_WEAPON) -> str:
    """Compose a precise order to `target` from `intent` via the commanding weapon.

    `intent` may be a file path or literal text. Raises ValueError on an unknown
    target or empty intent; propagates RuntimeError from delegate() on failure.
    """
    key = (target or "").strip().lower()
    if key not in TARGETS:
        raise ValueError(
            f"unknown target {target!r}; choose one of {', '.join(sorted(TARGETS))}"
        )
    text = _resolve_request(intent).strip()
    if not text:
        raise ValueError("empty intent — nothing to command")
    system = _SYSTEM_TEMPLATE.format(target_directive=TARGETS[key])
    prompt = "Guild Master's intent to issue as an order:\n\n" + text
    return delegate(weapon, prompt, system=system).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="Compose a precise down-command to a subordinate")
    ap.add_argument("--target", required=True, choices=sorted(TARGETS),
                    help="Who executes the order (right-sizes the command)")
    ap.add_argument("--in", dest="inp", required=True,
                    help="Intent: a file path OR literal text")
    ap.add_argument("--out", required=True, help="Path to write the order markdown")
    ap.add_argument("--weapon", default=DEFAULT_WEAPON,
                    help=f"Commanding weapon (default: {DEFAULT_WEAPON})")
    args = ap.parse_args()

    try:
        order = compose_command(args.target, args.inp, weapon=args.weapon)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(order + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"ERROR writing {out_path}: {exc}", file=sys.stderr)
        return 1

    print(f"commanded ({args.target}) -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
