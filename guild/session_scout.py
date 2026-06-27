"""session_scout.py — Guild Log Sync: scout sessions, log the missing entries,
rebuild guild-data in ONE call.

A thin wrapper that chains the three existing tools:
    build_guild_log.py   derive log entries from git history (idempotent)
    log_event.py         append any manual entries that git can't derive
    build.py             regenerate guild-data.js / guild-data.json

CLI:
    python3 guild/session_scout.py --window today,yesterday [--dry-run|--apply]

--dry-run (default) reports what it WOULD log/rebuild and writes nothing.
--apply actually runs the chain.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_GUILD_LOG = REPO_ROOT / "build_guild_log.py"
BUILD = REPO_ROOT / "build.py"


def _run(cmd: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=600
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"timeout running {' '.join(cmd)}"
    except Exception as exc:  # pragma: no cover - defensive
        return 1, "", f"failed to run {' '.join(cmd)}: {exc}"


def scout(window: str, apply: bool) -> int:
    """Run (or dry-run) the guild-log sync chain. Returns an exit code."""
    if not BUILD_GUILD_LOG.exists():
        print(f"ERROR: build_guild_log.py not found at {BUILD_GUILD_LOG}", file=sys.stderr)
        return 1
    if not BUILD.exists():
        print(f"ERROR: build.py not found at {BUILD}", file=sys.stderr)
        return 1

    print(f"session_scout: window={window!r} mode={'apply' if apply else 'dry-run'}")

    # Pass 1 — derive log entries from git history. build_guild_log.py has its
    # own --dry-run that prints what it WOULD add; we lean on it for the report.
    bgl_cmd = ["python3", str(BUILD_GUILD_LOG)]
    if not apply:
        bgl_cmd.append("--dry-run")
    code, out, err = _run(bgl_cmd)
    label = "would log (git-derived)" if not apply else "logged (git-derived)"
    print(f"[1/2] build_guild_log.py — {label}")
    if out.strip():
        print(out.rstrip())
    if code != 0:
        print(f"ERROR: build_guild_log.py exited {code}: {err.strip()}", file=sys.stderr)
        return code

    # NOTE: log_event.py is for *manual* entries git cannot derive (skill/member
    # creation, dashboard redesigns). It needs a human-authored --type/--title and
    # is therefore not auto-invoked here; the scout surfaces git-derivable entries
    # and rebuilds. Manual events stay an explicit `python3 log_event.py ...` call.
    print("[note] log_event.py is for manual (non-git-derivable) entries — not auto-run.")

    # Pass 2 — rebuild guild-data. In dry-run, use build.py --check (writes nothing,
    # exit 1 means content WOULD change).
    if not apply:
        code, out, err = _run(["python3", str(BUILD), "--check"])
        if code == 0:
            print("[2/2] build.py --check — guild-data already current (no rebuild needed).")
        else:
            print("[2/2] build.py --check — guild-data WOULD change on rebuild.")
        if out.strip():
            print(out.rstrip())
        print("dry-run: nothing written. Re-run with --apply to commit the sync.")
        return 0

    code, out, err = _run(["python3", str(BUILD)])
    print("[2/2] build.py — rebuilt guild-data.js + guild-data.json")
    if out.strip():
        print(out.rstrip())
    if code != 0:
        print(f"ERROR: build.py exited {code}: {err.strip()}", file=sys.stderr)
        return code

    print("session_scout: guild-log sync complete.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Guild Log Sync — scout, log, rebuild")
    ap.add_argument(
        "--window",
        default="today",
        help="Comma list of session windows to scout (e.g. today,yesterday)",
    )
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true",
                      help="Report what would be logged/rebuilt; write nothing (default)")
    mode.add_argument("--apply", action="store_true",
                      help="Actually run the log + rebuild chain")
    # Tolerate the workflow-runner's file rails (this step uses neither).
    ap.add_argument("--in", dest="_in", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--out", dest="_out", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    # Default is dry-run unless --apply is given.
    apply = bool(args.apply)
    return scout(args.window, apply)


if __name__ == "__main__":
    sys.exit(main())
