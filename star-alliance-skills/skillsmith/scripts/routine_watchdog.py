#!/usr/bin/env python3
"""Watchdog for the daily skillsmith routine.

Watches ``data/routine-heartbeat.json`` and alerts (exit 1, log append, stdout
block) when the routine has missed its expected run. Exits 0 quietly when the
heartbeat shows a healthy or not-yet-scheduled state.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Path layout:
#   <repo>/star-alliance-skills/skillsmith/scripts/routine_watchdog.py
#   <repo>                                  <-- parents[3]
SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[3]

HEARTBEAT_PATH = REPO_ROOT / "data" / "routine-heartbeat.json"
LOG_PATH = (
    REPO_ROOT
    / "star-alliance-skills"
    / "skillsmith"
    / "routine-logs"
    / "watchdog.log"
)

# A running-status that hasn't progressed after this many hours past
# next_expected_by is itself considered a stuck-run alert.
RUNNING_GRACE_HOURS = 3


def _parse_iso(value):
    """Parse an ISO8601 string as timezone-aware UTC. Returns None on null/empty."""
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        return None
    # datetime.fromisoformat in Python 3.11+ accepts a trailing 'Z', but be
    # defensive for older interpreters.
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _emit_alert(reason, heartbeat):
    """Print the stdout alert block, append a single log line, return exit 1."""
    now = datetime.now(timezone.utc)
    timestamp_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    print("=" * 60)
    print("WATCHDOG ALERT")
    print(f"timestamp:    {timestamp_iso}")
    print(f"reason:       {reason}")
    print("heartbeat:")
    for key in (
        "last_run_start",
        "last_run_end",
        "last_run_status",
        "last_run_summary",
        "budget_spent",
        "next_expected_by",
    ):
        print(f"  {key}: {heartbeat.get(key)!r}")
    print("=" * 60)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"{timestamp_iso} {reason}\n")
    return 1


def _emit_missing_heartbeat_alert(reason):
    """Alert variant for the missing/unreadable heartbeat file path."""
    now = datetime.now(timezone.utc)
    timestamp_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"routine_watchdog: ALERT - {reason}")
    print(f"  expected at: {HEARTBEAT_PATH}")
    print(f"  timestamp:   {timestamp_iso}")
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"{timestamp_iso} {reason}\n")
    return 1


def main():
    if not HEARTBEAT_PATH.exists():
        return _emit_missing_heartbeat_alert(
            "heartbeat file missing (routine has never recorded a run "
            "or file was deleted)"
        )

    try:
        with HEARTBEAT_PATH.open("r", encoding="utf-8") as fh:
            heartbeat = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        return _emit_missing_heartbeat_alert(
            f"heartbeat file unreadable: {exc}"
        )

    status = heartbeat.get("last_run_status")
    next_expected_by = _parse_iso(heartbeat.get("next_expected_by"))

    # 5a. Explicit failure always alerts.
    if status == "failed":
        return _emit_alert(
            "last_run_status == 'failed' (most recent run reported failure)",
            heartbeat,
        )

    # 5c. No schedule set yet, and not failed: quiet informational exit.
    if next_expected_by is None:
        print(
            f"routine_watchdog: OK - no schedule set yet "
            f"(status={status!r}, next_expected_by=null)"
        )
        return 0

    # 5b. Schedule exists. Compare against current UTC time.
    now = datetime.now(timezone.utc)
    if now <= next_expected_by:
        # Not yet due.
        print(
            f"routine_watchdog: OK - last status={status!r}, "
            f"next expected by {next_expected_by.isoformat()}"
        )
        return 0

    # Past next_expected_by. Decide based on status.
    if status == "running":
        # Allow a grace window for in-progress runs.
        seconds_overdue = (now - next_expected_by).total_seconds()
        if seconds_overdue <= RUNNING_GRACE_HOURS * 3600:
            print(
                f"routine_watchdog: OK - run in progress "
                f"(status='running', within {RUNNING_GRACE_HOURS}h grace)"
            )
            return 0
        return _emit_alert(
            f"status 'running' but stuck {seconds_overdue / 3600:.2f}h past "
            f"next_expected_by (grace {RUNNING_GRACE_HOURS}h exceeded)",
            heartbeat,
        )

    # Any other status ('never', 'success') past next_expected_by -> missed run.
    seconds_overdue = (now - next_expected_by).total_seconds()
    return _emit_alert(
        f"missed run: status={status!r}, "
        f"{seconds_overdue / 3600:.2f}h past next_expected_by "
        f"({next_expected_by.isoformat()})",
        heartbeat,
    )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        # Last-resort safety net: log the crash and exit non-zero so cron
        # surfaces the failure instead of silently passing.
        timestamp_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        reason = f"watchdog crashed: {type(exc).__name__}: {exc}"
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as fh:
            fh.write(f"{timestamp_iso} {reason}\n")
        print(f"routine_watchdog: ALERT - {reason}")
        sys.exit(1)