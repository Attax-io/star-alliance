"""delegate.py — RETIRED external-doer shim.

Star Alliance is now a Claude-only harness. The external "doer" layer (the
Hermes/MiniMax subprocess path that summon.py / minimax.py drove) has been
removed. There is no non-Claude model to delegate bulk work to anymore.

The specialist work those doers used to do is now done by Claude subagents,
spawned by the live session with its own Task/Agent tool
(subagent_type=<agent>). Nothing in this repo shells out to a doer.

This module is kept only so older imports and CLI invocations fail LOUDLY and
CLEARLY instead of crashing with an ImportError on a deleted file. Both
delegate() and delegate_many() raise a RuntimeError explaining the removal; the
CLI prints the same message and exits non-zero. Importing the module never
crashes.
"""
from __future__ import annotations

import argparse
import sys

_REMOVED_MSG = (
    "The external doer layer has been removed — Star Alliance is now a "
    "Claude-only harness. Spawn a Claude subagent from the live session "
    "(Task/Agent tool, subagent_type=<agent>) instead of delegating to an "
    "external model."
)


def delegate(model: str, prompt: str, system: str | None = None,
             file: str | None = None, timeout: int = 300) -> str:
    """RETIRED. Always raises RuntimeError — there is no external doer to call."""
    raise RuntimeError(_REMOVED_MSG)


def delegate_many(prompts, model: str = "claude", system: str | None = None,
                  timeout: int = 600) -> list:
    """RETIRED. Always raises RuntimeError — there is no external doer to call."""
    raise RuntimeError(_REMOVED_MSG)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="RETIRED — the external doer layer has been removed."
    )
    ap.add_argument("model", nargs="?", help="(ignored — retired)")
    ap.add_argument("prompt", nargs="?", help="(ignored — retired)")
    ap.add_argument("-s", "--system", default=None, help="(ignored — retired)")
    ap.add_argument("-f", "--file", default=None, help="(ignored — retired)")
    ap.parse_args()
    print(f"ERROR: {_REMOVED_MSG}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
