#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — THINKER ATTESTATION  (Stop hook, NON-blocking)
#
# THE DOCTRINE: a deployment brief's "planning model" line must reflect the model
# that ACTUALLY thought — never a template (transparency rule, 2026-06-28). The
# critic (GLM) is mechanically real because a hook causes it to run and ledgers the
# verdict. The thinker can't be "caused to run" by a hook — its model is fixed when
# the session launches — but the transcript already RECORDS which model thought each
# turn (`message.model`, e.g. claude-opus-4-8). This hook reads that and writes it
# to the ledger as PROOF, once per turn. That is the thinker's analog of GLM's
# ledger line: if a brief ever claims a planning model the session didn't run as,
# the ledger won't back it up.
#
# It NEVER blocks: the main-session/persona model is the Guild Master's own choice
# (Opus now), not bound to any member's declared model. Enforcement of a *deployed
# member* running as its declared model lives in thinker-gate.py (PreToolUse, the
# pre-spawn override block) — the one point where a mismatch is both detectable and
# preventable. Here we only surface truth.
#
# Fails OPEN (exit 0) on everything — a broken attestation must never trap a turn.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
from datetime import datetime, timezone


def _proj():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _ledger(repo, **kw):
    try:
        sys.path.insert(0, os.path.join(repo, "evolution"))
        import ledger  # noqa: E402
        ledger.append(**kw)
    except Exception:
        pass


def _epoch(iso):
    if not iso:
        return None
    try:
        s = str(iso).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return None


def _last_real_user_index(lines):
    idx = -1
    for i, o in enumerate(lines):
        if o.get("type") != "user":
            continue
        c = (o.get("message", {}) or {}).get("content")
        is_tool_result = isinstance(c, list) and any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in c
        )
        if not is_tool_result:
            idx = i
    return idx


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    repo = _proj()
    state = os.path.join(repo, ".claude", "state")
    transcript = data.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        sys.exit(0)
    try:
        lines = [json.loads(l) for l in open(transcript) if l.strip()]
    except Exception:
        sys.exit(0)
    if not lines:
        sys.exit(0)

    ui = _last_real_user_index(lines)
    window = lines[ui:] if ui >= 0 else lines
    start_epoch = _epoch(lines[ui].get("timestamp")) if ui >= 0 else None

    # Collect the distinct model(s) that produced this turn's assistant messages.
    models = []
    for o in window:
        if o.get("type") != "assistant":
            continue
        m = (o.get("message", {}) or {}).get("model")
        if m and m not in models:
            models.append(m)
    if not models:
        sys.exit(0)

    # Once-per-turn dedup keyed on the window anchor (turn-cost.py already deleted
    # the shared turn-start sentinel by the time we run, so we anchor on the user
    # message timestamp — stable across a blocking Stop's re-fires).
    key = str(int(start_epoch)) if start_epoch is not None else str(len(lines))
    sentinel = os.path.join(state, "thinker-attested")
    try:
        if open(sentinel).read().strip() == key:
            sys.exit(0)
    except OSError:
        pass

    _ledger(repo, kind="thinker", author=models[0], surface="arsenal",
            detail=f"thinker ran as {', '.join(models)}",
            meta={"role": "thinker", "models": models, "scope": "main-session"})
    try:
        os.makedirs(state, exist_ok=True)
        with open(sentinel, "w") as fh:
            fh.write(key)
    except OSError:
        pass
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[thinker-attest] {e}, failing open\n")
        sys.exit(0)
