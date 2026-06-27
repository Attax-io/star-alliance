#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — TURN COST  (Stop hook, non-blocking, Phase 0 measurement)
#
# Why this exists: the harness was richly instrumented for THEATER (klaxons, the
# dashboard, per-skill art) and blind to TRUTH — it could not tell you the one
# number that matters for an efficiency harness: premium (Opus) tokens spent per
# turn, and whether the proportional gate (Phase 1) actually made small turns
# cheaper. This Stop hook closes that loop. It records, once per assistant turn:
#   • the real Opus input/output (and cache) tokens for that turn, read from the
#     transcript's per-message usage blocks, and
#   • which routing tier fired — LITE (proportional) vs FULL (campaign-grade) —
#     detected from the SA-GATE:<TIER> marker the routing gate injects.
# Joined against the arsenal ledger by tools/efficiency_report.py, this turns the
# plan's MODELLED "~25–40% saved" into a number you read off your own data.
#
# Best-effort by contract — like every other hook here, it FAILS OPEN (exit 0) on
# any error: a broken measurement hook must never brick a turn or block Stop.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, time, re, pathlib

TIER_RE = re.compile(r"SA-GATE:(LITE|FULL)")


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def last_real_user_index(lines):
    """Index of the last genuine user turn (not a tool_result-only message)."""
    idx = -1
    for i, o in enumerate(lines):
        if o.get("type") != "user":
            continue
        c = o.get("message", {}).get("content")
        is_tool_result = isinstance(c, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in c
        )
        if not is_tool_result:
            idx = i
    return idx


def _text_of(o):
    """All text content of a transcript line (assistant text blocks or str)."""
    msg = o.get("message", {}) or {}
    c = msg.get("content")
    if isinstance(c, str):
        return c
    out = []
    if isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and b.get("type") == "text":
                out.append(b.get("text", ""))
    return "\n".join(out)


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    transcript = data.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        sys.exit(0)

    try:
        lines = [json.loads(l) for l in open(transcript) if l.strip()]
    except Exception:
        sys.exit(0)

    if not lines:
        sys.exit(0)

    ui = last_real_user_index(lines)
    window = lines[ui:] if ui >= 0 else lines

    # Sum Opus token usage across every assistant message in this turn.
    tin = tout = cache_read = cache_create = 0
    n_msgs = 0
    for o in window:
        if o.get("type") != "assistant":
            continue
        u = (o.get("message", {}) or {}).get("usage") or {}
        if not u:
            continue
        n_msgs += 1
        tin += int(u.get("input_tokens") or 0)
        tout += int(u.get("output_tokens") or 0)
        cache_read += int(u.get("cache_read_input_tokens") or 0)
        cache_create += int(u.get("cache_creation_input_tokens") or 0)

    # Detect which routing tier fired this turn (LITE vs FULL).
    # B1 fix: guild-routing-gate.sh writes the tier to a sidecar file
    # (.claude/state/last-tier) because the SA-GATE marker lands in hook stdout
    # (system-reminder context), not in user-turn text — so the regex below never
    # matched and 90% of turns logged tier=unknown. Sidecar is consumed once.
    tier = "unknown"
    tier_file = pathlib.Path(project_dir()) / ".claude" / "state" / "last-tier"
    if tier_file.exists():
        try:
            tier = tier_file.read_text().strip().lower()
            tier_file.unlink()
        except Exception:
            pass
    if tier == "unknown":
        for o in window:
            m = TIER_RE.search(_text_of(o))
            if m:
                tier = m.group(1).lower()
                break

    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tier": tier,
        "assistant_msgs": n_msgs,
        "in": tin,
        "out": tout,
        "cache_read": cache_read,
        "cache_create": cache_create,
    }

    try:
        out_dir = os.path.join(project_dir(), "data")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "turn-cost.jsonl"), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
