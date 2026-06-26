"""Shared usage logger for the Star Alliance arsenal backends.

Appends one JSON line per model call to ``usage-log.jsonl`` next to this file, so
the dashboard (``serve.cjs`` → ``/api/arsenal``) can compute REAL per-weapon spend
and the delegation ledger — the figure that proves the harness is actually
offloading work to the cheap bench instead of burning Opus.

Best-effort by contract: a telemetry failure must NEVER break a model call, so
every path here swallows its own errors.

Record shape (one per line):
    {"ts":"2026-06-27T10:15:00Z","model":"gemma4","backend":"ollama","in":20,"out":2}

``model`` is the guild model id (gemma4, kimi-k2.7, minimax-m3, …). Backends pass it
explicitly (resolved from the SA_MODEL_ID env that summon.py sets); direct callers
fall back to a best-effort derivation.
"""
import json
import os
import time

_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage-log.jsonl")


def log_usage(model, backend, tokens_in=0, tokens_out=0):
    """Append one usage record. Never raises."""
    try:
        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": str(model or "unknown"),
            "backend": str(backend or "unknown"),
            "in": int(tokens_in or 0),
            "out": int(tokens_out or 0),
        }
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
    except Exception:
        pass  # telemetry is best-effort; a logging failure must not break the call
