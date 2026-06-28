#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — SAFE-READ GUARD  (PreToolUse: Read)   *** DISARMED BY DEFAULT ***
#
# Kills the single most-repeated correction in guild history (the blind-full-read
# of a large/unknown-size file → token-cap failure → retry-the-same-read loop;
# ~44 occurrences across the audit register, "46 sessions" in CLAUDE.md). Doctrine
# alone never stopped it; this is the mechanical guard.
#
# *** NOT WIRED LIVE YET. *** This file ships standalone for review. It is NOT in
# the sa-pretool.py dispatcher and NOT in settings.json, so it changes nothing until
# you arm it. To arm: add ("safe-read-gate.py", {"Read"}) to the GATES list in
# .claude/hooks/sa-pretool.py. Behaviour is controlled by env SA_SAFE_READ:
#   • unset / "warn"  → WARN-only (non-blocking systemMessage nudging offset/limit)
#   • "block"         → block a blind full Read of a file over the line threshold
#   • "off"           → no-op
# Fails OPEN on any error — a read must never be bricked by this guard.
#
# Heuristic (cheap, no model): a Read call is "risky" when it targets an existing
# file, passes NO offset and NO limit, and the file exceeds SAFE_READ_LINES lines
# (default 1500 — below the harness 2000-line default cap, so the nudge fires before
# truncation bites). Directories, missing files, and small files are always allowed.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json

SAFE_READ_LINES = int(os.environ.get("SA_SAFE_READ_LINES", "1500"))


def _count_lines(path: str, cap: int) -> int:
    """Count lines up to cap+1 (stops early on huge files). Returns -1 on error."""
    try:
        n = 0
        with open(path, "rb") as f:
            for _ in f:
                n += 1
                if n > cap:
                    break
        return n
    except Exception:
        return -1


def check(data: dict) -> dict:
    """Pure decision. Returns {"exit":0|2, "stderr":str, "systemMessage":str}.
    Mirrors the workflow-gate contract so it can drop into sa-pretool.py unchanged."""
    mode = os.environ.get("SA_SAFE_READ", "warn").lower()
    if mode == "off":
        return {"exit": 0}
    if data.get("tool_name") != "Read":
        return {"exit": 0}

    inp = data.get("tool_input") or data.get("input") or {}
    path = inp.get("file_path") or inp.get("path")
    if not path or inp.get("offset") is not None or inp.get("limit") is not None:
        return {"exit": 0}  # paginated reads are exactly what we want — allow
    if not os.path.isfile(path):
        return {"exit": 0}  # dirs / missing / images handled by the Read tool itself

    n = _count_lines(path, SAFE_READ_LINES)
    if n <= SAFE_READ_LINES:
        return {"exit": 0}  # small/unknown → allow

    msg = (
        f"⚠ safe-read: '{os.path.basename(path)}' is large (>{SAFE_READ_LINES} lines). "
        f"Prefer offset/limit or grep over a blind full read — the #1 repeated correction "
        f"in guild history is the token-cap full-read loop."
    )
    if mode == "block":
        return {"exit": 2, "stderr": "⛔ " + msg + " Re-issue the Read with offset/limit.\n"}
    return {"exit": 0, "systemMessage": msg}  # warn-only (default): nudge, don't block


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[safe-read-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)
    try:
        r = check(data)
    except Exception as e:
        sys.stderr.write(f"[safe-read-gate] errored, failing open: {e}\n")
        sys.exit(0)
    if r.get("systemMessage"):
        print(json.dumps({"systemMessage": r["systemMessage"]}))
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    main()
