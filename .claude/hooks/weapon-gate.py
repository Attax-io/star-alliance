#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — WEAPON GATE  (PreToolUse, mostly-advisory)
#
# Governs HOW members draw and wield weapons (AI models), the mechanical partner
# to the weapon-utility skill. weapon-utility carries the doctrine; this hook is
# the bit that bites — the same move the workflow-gate made for workflows.
#
# It fires only when a tool is actually SUMMONING a model:
#   • Bash running summon.py <model>   (the arsenal dispatcher)
#   • Bash running minimax.py          (the prime doer, minimax-m3)
#   • Task / Agent with a model:'…'    (a Claude sub-agent weapon)
#
# Two behaviours:
#   1. BLOCK (exit 2) the one unambiguous violation — summoning a weapon that is
#      NOT in the guild arsenal at all (a hallucinated / mistyped / RETIRED model
#      name, e.g. the old Ollama minimax route). Safe to block: a non-existent
#      weapon can never be the right answer.
#   2. REMIND (non-blocking systemMessage, exit 0) on a VALID summon — restate the
#      thinker→(parallel)doers→review loop so the member wields it correctly.
#
# It does NOT block on "wrong member's arsenal" or "thinker used as doer": in
# single-context mode the acting member is a persona with no reliable tool
# footprint, so those can't be observed without false klaxons. Doctrine for them
# lives in weapon-utility; this hook enforces only what it can see for certain.
#
# Fails OPEN on any error — a broken hook must never brick the session.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, re

SUMMON_RE  = re.compile(r"summon\.py\s+([A-Za-z0-9.\-]+)")
MINIMAX_RE = re.compile(r"\bminimax\.py\b")
# old retired route: minimax reached via ollama instead of the DIRECT sub
RETIRED_RE = re.compile(r"ollama[^\n]*minimax|minimax[^\n]*ollama", re.I)


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def known_weapons():
    """Every valid weapon id: the canonical registry (star-alliance-arsenal/
    models.json) UNION every member's loadout (guild-data.json). The registry
    covers RESERVE weapons that sit in no loadout (e.g. nemotron-3-ultra,
    qwen3.5) so they stay summonable. Empty set on any error → check skipped
    (fail open)."""
    ids = set()
    root = project_dir()
    # 1. canonical registry — the source of truth for what weapons EXIST.
    try:
        reg = json.load(open(os.path.join(
            root, "star-alliance-arsenal", "models.json")))
        ids |= set(reg.get("models", {}).keys())
    except Exception:
        pass
    # 2. union member loadouts (covers anything not yet in the registry).
    try:
        g = json.load(open(os.path.join(root, "guild-data.json")))
        for m in g.get("members", []):
            for w in m.get("weapons", []) or []:
                wid = w.get("model") if isinstance(w, dict) else w
                if wid:
                    ids.add(wid)
    except Exception:
        pass
    return ids


REMINDER = (
    "⚔ Weapon doctrine — one thinker plans & reviews; it may run ONE OR SEVERAL "
    "doers in parallel (many of one model, or a mix), reviewing each return against "
    "the plan. Several thinkers at once only under ultra-brainstorming. (weapon-utility)"
)


def extract_models(tool, ti):
    """Return (models, used_retired_route) seen in this tool call."""
    models, retired = [], False
    if tool == "Bash":
        cmd = ti.get("command", "") or ""
        models += SUMMON_RE.findall(cmd)
        if MINIMAX_RE.search(cmd):
            models.append("minimax-m3")
        if RETIRED_RE.search(cmd):
            retired = True
    elif tool in ("Task", "Agent"):
        mdl = ti.get("model") or ti.get("model_name") or ""
        if mdl:
            models.append(mdl)
    return models, retired


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[weapon-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)

    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    try:
        models, retired = extract_models(tool, ti)
    except Exception as e:
        sys.stderr.write(f"[weapon-gate] parse error, failing open: {e}\n")
        sys.exit(0)

    if not models and not retired:
        sys.exit(0)  # not a summon — nothing to govern

    if retired:
        sys.stderr.write(
            "⛔ WEAPON GATE — that summons MiniMax via the RETIRED Ollama route. "
            "MiniMax M3 is drawn through its DIRECT sub now: `python3 minimax.py \"…\"` "
            "or `summon.py minimax-m3`. Re-draw the prime doer directly.\n"
        )
        sys.exit(2)

    valid = known_weapons()
    if valid:
        unknown = [m for m in models if m not in valid]
        if unknown:
            sys.stderr.write(
                f"⛔ WEAPON GATE — no such weapon in the guild arsenal: {sorted(set(unknown))}. "
                f"Draw a real weapon (one of: {', '.join(sorted(valid))}). "
                "A member can only wield weapons in its loadout — see weapon-utility.\n"
            )
            sys.exit(2)

    # Valid summon → non-blocking doctrine reminder.
    print(json.dumps({"systemMessage": REMINDER}))
    sys.exit(0)


if __name__ == "__main__":
    main()
