"""Shared root-resolution + config-presence primitives for Star Alliance gates.

Campaign 2026-07-02_self-enclosed-harness, P0 (portability) + P2 (fail-closed).

P0 — every gate used `os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()` and some
tools trusted a HARD-CODED STAR_ALLIANCE_ROOT from settings.json. On a second device
(atta/attaselim home-path mismatch) or a fresh landing that env points at a missing
folder and path-resolving tools silently no-op. resolve_root() prefers the ACTUAL
location of the running code (walk up to the repo markers) and treats env vars as
hints that are VALIDATED before use.

P2 — gates used to fail OPEN when config (models.json / workflows.json / roster) was
missing. Correct at home, wrong in a half-installed landing. guild_managed() lets a
gate tell "this IS a guild repo but config is missing" (fail CLOSED) from "not a
guild repo at all" (no-op, never brick an unrelated session).

Usage from a sibling hook:  from _saroot import resolve_root, guild_managed, missing_config
"""
import os

_ROOT_MARKERS = ("workflows.json", "CLAUDE.md")


def _looks_like_root(path):
    try:
        return all(os.path.isfile(os.path.join(path, m)) for m in _ROOT_MARKERS)
    except OSError:
        return False


def _walk_up_from(start):
    d = os.path.abspath(start)
    last = None
    while d != last:
        if _looks_like_root(d):
            return d
        last, d = d, os.path.dirname(d)
    return None


def resolve_root():
    """Portable Star Alliance repo root. Order: code location -> validated
    CLAUDE_PROJECT_DIR -> validated STAR_ALLIANCE_ROOT -> cwd walk-up -> legacy
    env/cwd default (never regresses below the old behaviour)."""
    here = _walk_up_from(os.path.dirname(os.path.abspath(__file__)))
    if here:
        return here
    for env in ("CLAUDE_PROJECT_DIR", "STAR_ALLIANCE_ROOT"):
        val = os.environ.get(env)
        if val and _looks_like_root(val):
            return val
    cwd_root = _walk_up_from(os.getcwd())
    if cwd_root:
        return cwd_root
    return (os.environ.get("CLAUDE_PROJECT_DIR")
            or os.environ.get("STAR_ALLIANCE_ROOT")
            or os.getcwd())


def guild_managed(root=None):
    """True iff root carries the guild markers. A gate no-ops (exit 0) when False."""
    return _looks_like_root(root or resolve_root())


def missing_config(required, root=None):
    """Subset of `required` (paths relative to root) that is absent. Empty => all
    present. Non-empty in a guild-managed repo => caller should fail CLOSED."""
    root = root or resolve_root()
    return [rel for rel in required if not os.path.exists(os.path.join(root, rel))]
