#!/usr/bin/env python3
"""critique.py — COLD critique: hand a diff/plan as TEXT to the Critic seat (default
glm-5.2) and get back a refutation-focused review.

The Critic is deliberately a DIFFERENT model family than the Brain (opus) — a critic
that shares the author's lineage shares its blind spots. This is the cheap, fast,
tool-free review mode.

TEXT-ONLY by nature: the Critic is a non-Claude weapon, so it CANNOT inspect the repo
(no grep/build/git/file reads). It judges only what you paste in. When the check must
RUN something — grep for a regression, run the build, read a file the diff didn't
include — use GROUNDED mode instead: Task a Claude review agent. Cold critique alone
misses *absence* bugs (a stale id left in a file nobody pasted), so grounded verify is
the backstop on real source changes. See weapon-utility §The Critic seat.

Usage:
    git diff HEAD | python3 star-alliance-arsenal/critique.py
    python3 star-alliance-arsenal/critique.py -f plan.md
    python3 star-alliance-arsenal/critique.py -m deepseek-v4-pro "<text>"

The critic model + its fallback chain live in models.json -> seats.critic. This
helper defaults to that seat's default; pass -m to draw a fallback.

Exit: 0 ok · 2 empty input · the backend's own code on failure (caller falls back).
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _critic_default():
    """seats.critic.default from the registry, or glm-5.2 if unreadable."""
    try:
        with open(os.path.join(HERE, "models.json"), encoding="utf-8") as fh:
            return json.load(fh).get("seats", {}).get("critic", {}).get("default") or "glm-5.2"
    except Exception:
        return "glm-5.2"


SYSTEM = (
    "You are the Critic — an adversarial reviewer from a DIFFERENT model family than "
    "the author. REFUTE, do not praise. Hunt correctness bugs, missed cases, false "
    "assumptions, and anything the author rationalized past. You are reading TEXT only; "
    "you cannot run the code or inspect the repo — explicitly flag any claim that needs "
    "grounded verification. Output: a short list of concrete findings (severity · what · "
    "why · where), then a final line  VERDICT: pass | concerns | block. No filler."
)


def main():
    ap = argparse.ArgumentParser(prog="critique", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?", default=None,
                    help="Text to critique. Omit or '-' to read stdin.")
    ap.add_argument("-f", "--file", default=None, help="Read the text from a file path.")
    ap.add_argument("-m", "--model", default=None,
                    help="Critic model (default: seats.critic.default, i.e. glm-5.2).")
    ap.add_argument("-s", "--system", default=SYSTEM, help="Override the critic system prompt.")
    ap.add_argument("--timeout", type=int, default=180, help="HTTP timeout seconds (default 180).")
    a = ap.parse_args()

    if a.file:
        try:
            text = open(a.file, encoding="utf-8").read()
        except OSError as e:
            print(f"critique: cannot read {a.file}: {e}", file=sys.stderr)
            sys.exit(2)
    elif a.text in (None, "-"):
        text = sys.stdin.read()
    else:
        text = a.text
    if not text.strip():
        print("critique: empty input — nothing to review", file=sys.stderr)
        sys.exit(2)

    model = a.model or _critic_default()
    cmd = [sys.executable, os.path.join(HERE, "summon.py"), model,
           text, "-s", a.system, "--timeout", str(a.timeout)]
    env = dict(os.environ, SA_MODEL_ID=model)
    sys.exit(subprocess.run(cmd, env=env).returncode)


if __name__ == "__main__":
    main()
