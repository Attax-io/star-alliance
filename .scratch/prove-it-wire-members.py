#!/usr/bin/env python3
"""Apply the three prove-it edits to all 10 member files. Idempotent."""
import re
import sys
from pathlib import Path

ROOT = Path("/Users/attaselim/Documents/Claude/Projects/star-alliance")
MEMBERS_DIR = ROOT / "star-alliance-members"

MEMBER_FILES = [
    "the-butler.md",
    "the-strategist.md",
    "the-architect.md",
    "the-designer.md",
    "the-interpreter.md",
    "the-herald.md",
    "the-steward.md",
    "the-developer.md",
    "the-quartermaster.md",
    "the-merchant.md",
]

PROVEIT_ROW = "| `prove-it` | before any message declaring a task done, fixed, shipped, complete, or ready - cross-check the original request line by line against the actual diff/tool-call evidence | it does not replace running tests/builds, and it does not replace `verify-gate.py` (that one checks code quality, not fulfillment) | `verify-gate.py`, `requesting-code-review`, `dual-model-review` |\n"

PROVEIT_BULLET_TEXT = "Before declaring any task done, run the `prove-it` cross-check - re-read the original request line by line against the actual diff or evidence; the Stop hook backs this up, but it is never the only check."

IDEMPOTENCY_MARKER = "<!-- PROVE-IT-WIRED -->"


def edit_skills_line(content: str) -> tuple[str, bool]:
    pat = re.compile(r"^(skills:\s*\[)([^\]]*)(\])", re.MULTILINE)
    m = pat.search(content)
    if not m:
        return content, False
    skills_inner = m.group(2)
    if "prove-it" in skills_inner:
        return content, False
    new_inner = skills_inner.rstrip() + ", prove-it"
    new_line = m.group(1) + new_inner + m.group(3)
    return content[: m.start()] + new_line + content[m.end():], True


def edit_universal_row(content: str) -> tuple[str, bool]:
    lines = content.split("\n")
    out_lines = []
    inserted = False
    for i, line in enumerate(lines):
        out_lines.append(line)
        if not inserted and line.startswith("| `weapon-utility`"):
            window = "\n".join(lines[max(0, i - 30): i + 1])
            if "Universal skills" in window or "Universal doctrine" in window:
                if PROVEIT_ROW.rstrip("\n") not in content:
                    out_lines.append(PROVEIT_ROW.rstrip("\n"))
                inserted = True
    if not inserted:
        return content, False
    return "\n".join(out_lines), True


def edit_how_you_work(content: str, filename: str) -> tuple[str, bool]:
    if IDEMPOTENCY_MARKER in content:
        return content, False

    if filename == "the-butler.md":
        anchor = "## What you don't do\n\n"
        if anchor not in content:
            return content, False
        bullet = f"- {PROVEIT_BULLET_TEXT} {IDEMPOTENCY_MARKER}\n"
        return content.replace(anchor, anchor + bullet, 1), True

    marker = "## How you work\n\n"
    idx = content.find(marker)
    if idx < 0:
        return content, False
    after = idx + len(marker)
    rest = content[after:]
    m = re.search(r"^1\.\s", rest, re.MULTILINE)
    if not m:
        return content, False
    insert_at = after + m.start()
    bullet = f"- {PROVEIT_BULLET_TEXT} {IDEMPOTENCY_MARKER}\n"
    return content[:insert_at] + bullet + content[insert_at:], True


def main():
    print("=== prove-it member wiring ===\n")
    results = []
    for fn in MEMBER_FILES:
        path = MEMBERS_DIR / fn
        orig = path.read_text()
        content = orig

        content, ok_a = edit_skills_line(content)
        content, ok_b = edit_universal_row(content)
        content, ok_c = edit_how_you_work(content, fn)

        if content != orig:
            path.write_text(content)
            results.append((fn, ok_a, ok_b, ok_c))
            status = "OK" if (ok_a and ok_b and ok_c) else "PARTIAL"
            print(f"  {fn}: skills={ok_a} row={ok_b} bullet={ok_c} -> {status}")
        else:
            results.append((fn, False, False, False))
            print(f"  {fn}: NO CHANGE")

    fail = [r for r in results if not all(r[1:])]
    if fail:
        print(f"\nFAILED on: {[f[0] for f in fail]}")
        return 1
    print("\nAll 10 member files wired successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())