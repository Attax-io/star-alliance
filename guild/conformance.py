"""conformance.py — wraps conformity_check.py, writes a signoff markdown,
and propagates its exit code so it can gate a workflow.

CLI:
    python3 guild/conformance.py [--out runs/conformance_signoff.md]

Exit code: identical to conformity_check.py (0 = PASS, 1 = FAIL).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK = REPO_ROOT / "conformity_check.py"

_ISSUE_RE = re.compile(
    r"(\d+)\s+(?:issues?|contradictions?|failures?|errors?|problems?)",
    re.IGNORECASE,
)


def _count_issues(report: str) -> int:
    """Best-effort count of issues from a conformity report."""
    m = _ISSUE_RE.search(report or "")
    return int(m.group(1)) if m else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Run conformity check and write signoff")
    ap.add_argument(
        "--out",
        default="runs/conformance_signoff.md",
        help="Path for the signoff markdown (default: runs/conformance_signoff.md)",
    )
    args = ap.parse_args()

    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = (REPO_ROOT / out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    if not CHECK.exists():
        code = 1
        report = ""
        stderr = f"conformity_check.py not found at {CHECK}"
    else:
        try:
            proc = subprocess.run(
                ["python3", str(CHECK)],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                timeout=600,
            )
            code = proc.returncode
            report = proc.stdout or ""
            stderr = proc.stderr or ""
        except subprocess.TimeoutExpired:
            code, report, stderr = 1, "", "conformity_check.py timed out after 600s"
        except Exception as exc:
            code, report, stderr = 1, "", f"failed to invoke conformity_check.py: {exc}"

    status = "PASS" if code == 0 else "FAIL"
    n = _count_issues(report) if code != 0 else 0
    n_disp = n if n else (1 if code != 0 else 0)

    body = (
        "# Conformance Signoff\n\n"
        f"- Timestamp: {ts}\n"
        f"- Status: {status}\n"
        f"- Exit code: {code}\n"
    )
    if code != 0:
        body += f"- Issues: {n_disp}\n"
    body += "\n## Report\n\n```\n" + report.rstrip() + "\n```\n"
    if stderr.strip():
        body += "\n## Stderr\n\n```\n" + stderr.strip() + "\n```\n"

    try:
        out_path.write_text(body, encoding="utf-8")
    except Exception as exc:
        print(f"ERROR writing signoff: {exc}", file=sys.stderr)

    if code == 0:
        print("CONFORMANCE: PASS")
    else:
        print(f"CONFORMANCE: FAIL ({n_disp} issues)")
    return code


if __name__ == "__main__":
    sys.exit(main())
