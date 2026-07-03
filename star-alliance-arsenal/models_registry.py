"""Single loader for the canonical arsenal registry (models.json).

Every Python consumer imports from here instead of hand-copying model facts, so
roles/tags/status/weights can never drift. Resolves models.json next to this file.

Claude-only registry: the three models are opus / sonnet / haiku, all with
backend "claude". There is no non-Claude doer layer.

Fails LOUD only at the call site that needs data — load() raises if the file is
unreadable, but the convenience maps accept a `fallback` so enforcement hooks can
degrade safely (a broken registry must never brick a gate).
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(_HERE, "models.json")


def load(path=None):
    """Return the {id: {fields}} model map. Raises on read/parse error."""
    with open(path or _PATH, encoding="utf-8") as fh:
        return json.load(fh)["models"]


def _safe(path=None):
    try:
        return load(path)
    except Exception:
        return {}


def role_map(fallback=None, path=None):
    """{id: role}. fallback returned if the registry can't be read."""
    m = _safe(path)
    if not m:
        return dict(fallback or {})
    return {mid: d.get("role", "") for mid, d in m.items()}


def claude_ids(path=None):
    """Set of Claude-native ids (opus/sonnet/haiku). Every model qualifies now."""
    return {mid for mid, d in _safe(path).items() if d.get("backend") == "claude"}


def known_ids(path=None):
    """Set of every registered model id."""
    return set(_safe(path).keys())


def status_map(path=None):
    return {mid: d.get("status", "") for mid, d in _safe(path).items()}


def seats(path=None):
    """The role seats block (Brain) from models.json.
    {} if absent or unreadable — callers degrade to per-agent defaults."""
    try:
        with open(path or _PATH, encoding="utf-8") as fh:
            return json.load(fh).get("seats", {})
    except Exception:
        return {}
