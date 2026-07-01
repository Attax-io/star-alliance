#!/usr/bin/env python3
"""xp.py — resolve a real, USAGE-BASED numeric level for every member, skill,
and workflow in the guild, from append-only invocation logs (single source of
truth), mirroring the shape of tools/domain_version.py.

LEVEL CURVE (confirmed, see CLAUDE.md / the XP campaign brief):
  Start level 1, 0 XP. XP = invocation count.
  step cost(1->2) = 10
  step cost(n->n+1) = floor(cost(n-1->n) * 1.1 + 1)   -> 10, 12, 14, 16, ...
  cumulative to reach a level = sum of step costs below it:
    L1 = 0
    L2 = 10
    L3 = 22
    L4 = 36
    L5 = 52
    ...
  Level(xp) = highest level whose cumulative cost <= xp.

SOURCES (namespaced by type so a member and a same-named skill never collide):
  members    <- .claude/state/dispatch-log.jsonl  (keyed on `agent`)
  skills     <- .claude/state/xp-log.jsonl         ({"type":"skill", "name":...})
  workflows  <- .claude/state/xp-log.jsonl         ({"type":"workflow", "name":...})

Fail-soft throughout: a missing/unreadable log resolves every id in that
namespace to level 1, 0 XP — this module must NEVER crash the build or a caller.
"""

from __future__ import annotations

import json
from pathlib import Path

# ── The level curve ─────────────────────────────────────────────────────────

_FIRST_STEP_COST = 10
_STEP_GROWTH = 1.1
_MAX_LEVEL_CAP = 500  # sanity ceiling — no real XP count will ever reach this


def _cumulative_costs(max_level: int = _MAX_LEVEL_CAP) -> list[int]:
    """cumulative[i] = total XP needed to REACH level i+2 (0-indexed on step,
    i.e. cumulative[0] is the XP needed for level 2, cumulative[1] for level 3,
    etc). Level 1 always costs 0 (the floor)."""
    costs = []
    step = _FIRST_STEP_COST
    total = 0
    for _ in range(max_level):
        total += step
        costs.append(total)
        step = int(step * _STEP_GROWTH + 1)
    return costs


_CUMULATIVE = _cumulative_costs()


def level_from_xp(xp: int) -> dict:
    """Resolve {level, xp, xpIntoLevel, xpForNextLevel} from a raw XP count.
    Never raises: a negative/garbage xp is clamped to 0."""
    try:
        xp = max(0, int(xp))
    except (TypeError, ValueError):
        xp = 0

    level = 1
    prev_cum = 0
    for i, cum in enumerate(_CUMULATIVE):
        if xp >= cum:
            level = i + 2  # _CUMULATIVE[0] is the threshold for level 2
            prev_cum = cum
        else:
            break

    # XP required to go from `level` to `level+1`.
    next_cum = _CUMULATIVE[level - 1] if level - 1 < len(_CUMULATIVE) else None
    xp_for_next = (next_cum - prev_cum) if next_cum is not None else None
    xp_into_level = xp - prev_cum

    return {
        "xp": xp,
        "level": level,
        "xpIntoLevel": xp_into_level,
        "xpForNextLevel": xp_for_next,  # None => at/near the sanity cap
    }


# ── Log readers (fail-soft) ──────────────────────────────────────────────────

def _project_dir() -> Path:
    import os
    root = os.environ.get("STAR_ALLIANCE_ROOT") or os.environ.get("CLAUDE_PROJECT_DIR")
    if root:
        return Path(root)
    return Path(__file__).resolve().parent.parent


def _iter_jsonl(path: Path):
    if not path.exists():
        return
    try:
        with open(path, "r", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        return


def count_dispatch_log(repo: Path | None = None) -> dict[str, int]:
    """member_id -> invocation count, from .claude/state/dispatch-log.jsonl,
    keyed on the `agent` field. Fail-soft: unreadable/missing -> {}."""
    repo = repo or _project_dir()
    path = repo / ".claude" / "state" / "dispatch-log.jsonl"
    counts: dict[str, int] = {}
    for row in _iter_jsonl(path):
        agent = row.get("agent")
        if not agent:
            continue
        counts[agent] = counts.get(agent, 0) + 1
    return counts


def count_xp_log(repo: Path | None = None) -> dict[str, dict[str, int]]:
    """{"skill": {name: count}, "workflow": {name: count}} from
    .claude/state/xp-log.jsonl. Fail-soft: unreadable/missing -> empty dicts."""
    repo = repo or _project_dir()
    path = repo / ".claude" / "state" / "xp-log.jsonl"
    out: dict[str, dict[str, int]] = {"skill": {}, "workflow": {}}
    for row in _iter_jsonl(path):
        t = row.get("type")
        name = row.get("name")
        if not name or t not in out:
            continue
        out[t][name] = out[t].get(name, 0) + 1
    return out


# ── Public API ────────────────────────────────────────────────────────────

def resolve_xp(kind: str, name: str, *, repo: Path | None = None,
                _cache: dict | None = None) -> dict:
    """Resolve {xp, level, xpIntoLevel, xpForNextLevel} for one (kind, name)
    pair. kind in {"member", "skill", "workflow"}. Fail-soft: any error ->
    level 1, 0 xp. `_cache` lets a bulk caller pass in pre-read counts to
    avoid re-reading the logs per item (see resolve_all)."""
    try:
        repo = repo or _project_dir()
        if _cache is None:
            _cache = _read_all_counts(repo)
        if kind == "member":
            xp = _cache["member"].get(name, 0)
        elif kind in ("skill", "workflow"):
            xp = _cache[kind].get(name, 0)
        else:
            xp = 0
        return level_from_xp(xp)
    except Exception:  # noqa: BLE001 — resolve_xp must never crash a caller
        return level_from_xp(0)


def _read_all_counts(repo: Path) -> dict[str, dict[str, int]]:
    try:
        member_counts = count_dispatch_log(repo)
    except Exception:  # noqa: BLE001
        member_counts = {}
    try:
        xp_counts = count_xp_log(repo)
    except Exception:  # noqa: BLE001
        xp_counts = {"skill": {}, "workflow": {}}
    return {
        "member": member_counts,
        "skill": xp_counts.get("skill", {}),
        "workflow": xp_counts.get("workflow", {}),
    }


def resolve_all(members: list[str], skills: list[str], workflows: list[str],
                 repo: Path | None = None) -> dict[str, dict[str, dict]]:
    """Bulk resolver for build.py: given id lists for each kind, return
    {"member": {id: xpinfo}, "skill": {id: xpinfo}, "workflow": {id: xpinfo}}.
    Reads each log exactly once. Never raises."""
    repo = repo or _project_dir()
    try:
        cache = _read_all_counts(repo)
    except Exception:  # noqa: BLE001
        cache = {"member": {}, "skill": {}, "workflow": {}}

    out: dict[str, dict[str, dict]] = {"member": {}, "skill": {}, "workflow": {}}
    for mid in members:
        out["member"][mid] = resolve_xp("member", mid, repo=repo, _cache=cache)
    for sid in skills:
        out["skill"][sid] = resolve_xp("skill", sid, repo=repo, _cache=cache)
    for wid in workflows:
        out["workflow"][wid] = resolve_xp("workflow", wid, repo=repo, _cache=cache)
    return out


if __name__ == "__main__":
    import sys
    _repo = _project_dir()
    if len(sys.argv) >= 3:
        print(json.dumps(resolve_xp(sys.argv[1], sys.argv[2], repo=_repo), indent=2))
    else:
        cache = _read_all_counts(_repo)
        print(json.dumps({
            "member_counts": cache["member"],
            "skill_counts": cache["skill"],
            "workflow_counts": cache["workflow"],
            "sample_curve": [level_from_xp(x) for x in (0, 5, 10, 21, 22, 35, 51, 100)],
        }, indent=2))
