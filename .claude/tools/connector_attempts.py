#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — CONNECTOR ATTEMPTS LEDGER  (small CLI for the seven-try gate)
#
# A tiny JSON-Lines log of the real attempts a stuck specialist has already
# made on a task before escalating to The Connector. The Connector gate reads
# this file to decide whether the seven-try rule has been satisfied.
#
# Storage: <repo>/.claude/state/connector-attempts.jsonl  (one JSON object per
# line: task_id, member, note, ts). Missing file → count is 0.
#
# Subcommands:
#   log <task-id> <member> <note...>   append a line, print the new count
#   count <task-id>                    print the integer count
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
import time


def _proj():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _state_path():
    return os.path.join(_proj(), ".claude", "state", "connector-attempts.jsonl")


def _ensure_state():
    path = _state_path()
    parent = os.path.dirname(path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    return path


def _count(task_id):
    path = _state_path()
    if not os.path.isfile(path):
        return 0
    n = 0
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("task_id") == task_id:
                    n += 1
    except OSError:
        return 0
    return n


def _log(task_id, member, note):
    path = _ensure_state()
    obj = {
        "task_id": task_id,
        "member": member,
        "note": note,
        "ts": time.time(),
    }
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
    return _count(task_id)


def _usage():
    sys.stderr.write(
        "usage: connector_attempts.py <command> [args...]\n"
        "  log <task-id> <member> <note...>   append an attempt, print new count\n"
        "  count <task-id>                    print the count for <task-id>\n"
    )


def main(argv):
    if len(argv) < 2:
        _usage()
        return 2
    cmd = argv[1]
    if cmd == "log":
        # log <task-id> <member> <note...>
        if len(argv) < 5:
            _usage()
            return 2
        task_id = argv[2]
        member = argv[3]
        note = " ".join(argv[4:])
        n = _log(task_id, member, note)
        print(f"attempts for {task_id}: {n}")
        return 0
    if cmd == "count":
        if len(argv) != 3:
            _usage()
            return 2
        task_id = argv[2]
        n = _count(task_id)
        print(n)
        return 0
    _usage()
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        sys.stderr.write(f"[connector_attempts] {e}\n")
        sys.exit(1)
