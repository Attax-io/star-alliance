"""Shared usage logger for the Star Alliance arsenal.

Appends one JSON line per model call to ``usage-log.jsonl`` next to this file, so
the dashboard (``serve.cjs`` → ``/api/arsenal``) can compute REAL per-model spend
across the three Claude models the guild runs on (opus / sonnet / haiku).

Best-effort by contract: a telemetry failure must NEVER break a model call, so
every path here swallows its own errors.

Record shape (one per line):
    {"ts":"2026-06-27T10:15:00Z","model":"haiku","backend":"claude","in":20,"out":2,
     "phase":"work","wall_ms":812}

``model`` is the guild model id (opus / sonnet / haiku). ``backend`` is "claude".

``phase`` tags WHY the call ran (default "work"). ``wall_ms`` is the measured
round-trip of the model call, so the efficiency report can compute
time-per-token, not just token spend. Both are additive: old readers ignore the
extra keys, old callers omit them.
"""
import json
import os
import time

_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "usage-log.jsonl")


def log_usage(model, backend, tokens_in=0, tokens_out=0, phase="work", wall_ms=None):
    """Append one usage record. Never raises."""
    try:
        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model": str(model or "unknown"),
            "backend": str(backend or "unknown"),
            "in": int(tokens_in or 0),
            "out": int(tokens_out or 0),
            "phase": str(phase or "work"),
        }
        if wall_ms is not None:
            try:
                rec["wall_ms"] = int(wall_ms)
            except (TypeError, ValueError):
                pass
        with open(_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
    except Exception:
        pass  # telemetry is best-effort; a logging failure must not break the call
