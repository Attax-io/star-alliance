#!/usr/bin/env python3
"""Append prove-it entry to each profile skills.yaml that exists. Idempotent."""
import sys
from pathlib import Path

ROOT = Path("/Users/attaselim/Documents/Claude/Projects/star-alliance")
PROFILES_DIR = ROOT / "profiles"

PROFILES = [
    "butler",   # may not exist
    "strategist",
    "architect",
    "designer",
    "interpreter",
    "herald",
    "steward",
    "developer",
    "quartermaster",
    "merchant",
]

PROVEIT_BLOCK = """- name: prove-it
  reason: Universal request-fulfillment check - before declaring a task done, cross-check the original request against the actual diff/tool-call evidence; backed by the prove-it.py Stop hook critic gate.
"""


def main():
    results = {}
    for profile in PROFILES:
        path = PROFILES_DIR / profile / "skills.yaml"
        if not path.exists():
            results[profile] = ("MISSING", None)
            continue
        content = path.read_text()
        if "name: prove-it" in content:
            results[profile] = ("ALREADY_PRESENT", None)
            continue
        # Ensure exactly one trailing newline before appending
        if not content.endswith("\n"):
            content += "\n"
        if not content.endswith("\n\n"):
            content += "\n"
        content += PROVEIT_BLOCK
        path.write_text(content)
        results[profile] = ("APPENDED", None)

    print("=== prove-it profile wiring ===\n")
    for p, (status, _) in results.items():
        print(f"  profiles/{p}/skills.yaml: {status}")

    skipped = [p for p, (s, _) in results.items() if s == "MISSING"]
    if skipped:
        print(f"\nSkipped (no profile dir): {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())