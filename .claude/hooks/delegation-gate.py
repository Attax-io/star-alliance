#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — EXECUTOR (DELEGATION) GATE  (Stop hook, BLOCKING)
#
# THE DOCTRINE: "doer-grade bulk → MiniMax first." Until now this was nudged
# (weapon-gate's reminder) and tracked (usage-log.jsonl) but never ENFORCED —
# nothing made a turn actually delegate. This is the executor's analog of the
# verify-gate (GLM critic): a real, mechanical gate that BLOCKS a turn which
# produced doer-grade inline bulk WITHOUT ever calling a doer, and LEDGERS the
# truth either way. The ledger reflects what truly ran — including the override.
#
# WHAT IT MEASURES (and why this trigger):
#   MiniMax returns *text* that the thinker still applies with Edit/Write, so a
#   delegated bulk edit and a hand-typed one look identical in the diff — they
#   differ only by a logged doer call. So the gate's discriminator is the reliable
#   one ("was a doer call logged this turn?"); the trigger for "this *should* have
#   been delegated" is inherently a heuristic, so it is calibrated CONSERVATIVELY:
#   the summed bytes of doer-grade inline OUTPUT this turn (Write content +
#   Edit/MultiEdit new_string) must exceed BULK_BYTES. Planning / conversation
#   turns produce no edits and never trip it; a few small edits never trip it.
#
# DECISION:
#   • bulk < BULK_BYTES                         → allow (nothing doer-grade)
#   • bulk ≥ BULK_BYTES and a doer call logged  → PASS  (ledger delegation pass)
#   • bulk ≥ BULK_BYTES and NO doer logged      → BLOCK (exit 2; ledger block)
#
# RISK POSTURE (mirrors verify-gate.py): armed by default; fail OPEN on any infra
# error (a broken gate must never trap a session); kill switch evolution/DISARMED
# (or .claude/state/delegation-gate-disarmed); one-turn LOGGED override SA_SOLO=1
# (optionally SA_SOLO_REASON="…") — going solo stays visible in the ledger.
#
# Because a blocking Stop hook does NOT abort sibling Stop hooks (turn-finalize is
# a sibling and would commit mid-block), on BLOCK we drop a sentinel
# (.claude/state/delegation-block) that turn-finalize.sh honors to skip the commit
# — the same mirror pattern verify-gate uses. On pass/override we clear it.
# ─────────────────────────────────────────────────────────────────────────────
import os
import sys
import json
from datetime import datetime, timezone

# ~1.5k tokens of output ≈ 6 KB — the weapon-utility size threshold below which the
# thinker is told to work inline (offloading is net-negative). Tune from real data.
BULK_BYTES = 6000
DOER_BACKENDS = {"minimax", "ollama"}
EDIT_TOOLS = {"Write", "Edit", "MultiEdit"}


def _proj():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _ledger(repo, **kw):
    """Best-effort ledger append; observability must never break the gate."""
    try:
        sys.path.insert(0, os.path.join(repo, "evolution"))
        import ledger  # noqa: E402
        ledger.append(**kw)
    except Exception:
        pass


def _epoch(iso):
    """ISO-8601 (…Z) → epoch seconds, or None."""
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
    """Index of the last genuine user turn (not a tool_result-only message)."""
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


def _bulk_bytes(window):
    """Summed bytes of doer-grade inline output authored this turn."""
    total = 0
    for o in window:
        if o.get("type") != "assistant":
            continue
        for b in (o.get("message", {}) or {}).get("content", []) or []:
            if not (isinstance(b, dict) and b.get("type") == "tool_use"):
                continue
            if b.get("name") not in EDIT_TOOLS:
                continue
            inp = b.get("input", {}) or {}
            if "content" in inp:                       # Write
                total += len((inp.get("content") or "").encode("utf-8", "ignore"))
            if "new_string" in inp:                    # Edit
                total += len((inp.get("new_string") or "").encode("utf-8", "ignore"))
            for e in inp.get("edits", []) or []:       # MultiEdit
                if isinstance(e, dict):
                    total += len((e.get("new_string") or "").encode("utf-8", "ignore"))
    return total


def _doer_calls_since(repo, start_epoch):
    """Count real doer invocations logged on/after the turn window start."""
    n = 0
    # 1) usage-log.jsonl — the record of ACTUAL doer API calls (authoritative).
    path = os.path.join(repo, "star-alliance-arsenal", "usage-log.jsonl")
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if str(r.get("backend", "")).lower() not in DOER_BACKENDS:
                    continue
                ts = _epoch(r.get("ts"))
                # A line whose time can't be established must NOT count as this-turn:
                # usage-log.jsonl is append-only across ALL sessions, so a single
                # malformed-ts doer entry anywhere in history would permanently satisfy
                # the gate and silently defeat enforcement. Unknown ts → ignore.
                if ts is not None and ts >= start_epoch - 1:   # 1s slack for clock skew
                    n += 1
    except Exception:
        pass
    # 2) doer-summon signals in the evolution ledger (corroboration / fallback).
    if n == 0:
        try:
            sys.path.insert(0, os.path.join(repo, "evolution"))
            import ledger  # noqa: E402
            for ev in ledger.read(kind="metric"):
                if (ev.get("meta") or {}).get("signal") != "doer-summon":
                    continue
                ts = _epoch(ev.get("ts"))
                if ts is not None and ts >= start_epoch - 1:   # unknown ts → ignore
                    n += 1
        except Exception:
            pass
    return n


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    repo = _proj()
    state = os.path.join(repo, ".claude", "state")
    block_sentinel = os.path.join(state, "delegation-block")
    ledgered_sentinel = os.path.join(state, "delegation-ledgered")

    def _clear_block():
        try:
            os.remove(block_sentinel)
        except OSError:
            pass

    # Kill switch — one file stands the gate down (shared with the whole engine).
    if (os.path.exists(os.path.join(repo, "evolution", "DISARMED")) or
            os.path.exists(os.path.join(state, "delegation-gate-disarmed"))):
        _clear_block()
        sys.exit(0)

    transcript = data.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        sys.exit(0)                                    # can't measure → fail open
    try:
        lines = [json.loads(l) for l in open(transcript) if l.strip()]
    except Exception:
        sys.exit(0)
    if not lines:
        sys.exit(0)

    ui = _last_real_user_index(lines)
    window = lines[ui:] if ui >= 0 else lines
    start_epoch = _epoch(lines[ui].get("timestamp")) if ui >= 0 else None
    if start_epoch is None:
        sys.exit(0)                                    # no window anchor → fail open

    bulk = _bulk_bytes(window)

    # Once-per-turn ledger dedup keyed on (window, decision): a blocking Stop
    # re-fires Stop, and we must not spam the ledger with the same verdict. The
    # block DECISION is recomputed every pass (idempotent); only the LEDGER write
    # is deduped. A genuine decision change (block→pass after the user delegates)
    # has a different key, so it ledgers again — exactly what we want.
    def _ledger_once(decision, **kw):
        key = f"{int(start_epoch)}:{decision}"
        try:
            prev = open(ledgered_sentinel).read().strip()
        except OSError:
            prev = ""
        if prev == key:
            return
        _ledger(repo, **kw)
        try:
            with open(ledgered_sentinel, "w") as fh:
                fh.write(key)
        except OSError:
            pass

    # One-turn LOGGED override — going solo is allowed but stays on the record.
    # Two channels, both honored: SA_SOLO=1 env (for a human re-ending the turn from a
    # shell) and a .claude/state/solo-once file whose contents are the reason (for the
    # AGENT itself, which cannot set session env for a Stop hook mid-turn — without this
    # the gate is unclearable by the very actor it gates except by killing it). The file
    # is NOT consumed here: a blocking Stop re-fires Stop, so consume-on-read would
    # re-block on the next pass; turn-start.py clears it at the next real user turn.
    once = os.path.join(state, "solo-once")
    if os.environ.get("SA_SOLO") == "1" or os.path.exists(once):
        reason = os.environ.get("SA_SOLO_REASON", "").strip()
        if not reason and os.path.exists(once):
            try:
                reason = open(once).read().strip()
            except OSError:
                reason = ""
        reason = reason or "no reason given"
        if bulk >= BULK_BYTES:
            _ledger_once("solo-override", kind="delegation", author="thinker",
                         surface="arsenal", verdict="solo-override",
                         detail=f"solo override: {bulk}B inline, no doer — {reason}",
                         meta={"role": "executor", "bulk_bytes": bulk, "reason": reason})
        _clear_block()
        sys.exit(0)

    # Below the doer-grade threshold → nothing to enforce.
    if bulk < BULK_BYTES:
        _clear_block()
        sys.exit(0)

    doer = _doer_calls_since(repo, start_epoch)
    if doer >= 1:
        _ledger_once("pass", kind="delegation", author="thinker", surface="arsenal",
                     verdict="pass",
                     detail=f"delegation OK: {bulk}B inline + {doer} doer call(s)",
                     meta={"role": "executor", "bulk_bytes": bulk, "doer_calls": doer})
        _clear_block()
        sys.exit(0)

    # bulk crossed + zero doer calls → BLOCK.
    _ledger_once("block", kind="delegation", author="thinker", surface="arsenal",
                 verdict="block",
                 detail=f"delegation gate: {bulk}B doer-grade inline, no doer call",
                 meta={"role": "executor", "bulk_bytes": bulk})
    try:
        with open(block_sentinel, "w") as fh:
            fh.write(str(int(start_epoch)))
    except OSError:
        pass
    sys.stderr.write(
        "⛔ DELEGATION GATE — this turn produced "
        f"{bulk:,} bytes of doer-grade inline output (Write/Edit) but logged NO doer "
        "call. Doer-grade bulk goes to MiniMax first (weapon-utility):\n"
        "     python3 star-alliance-arsenal/summon.py minimax-m3 \"<prompt>\"\n"
        "   Delegate the bulk and re-end the turn — the gate clears once a doer call is\n"
        "   on record. Nothing is committed while this blocks (forward-fix only).\n"
        "   If this work is genuinely non-offloadable (tool-orchestration, deep\n"
        "   reasoning), go solo ON THE RECORD — either:\n"
        "     • human:  SA_SOLO=1 SA_SOLO_REASON=\"why\"  then re-end, or\n"
        "     • agent:  echo \"why\" > .claude/state/solo-once  then re-end\n"
        "   Kill switch: touch evolution/DISARMED\n")
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"[delegation-gate] {e}, failing open\n")
        sys.exit(0)
