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


def _sense(signal, **kw):
    """Fail-soft capability-signal emit; never breaks the gate (logging, not control)."""
    try:
        sys.path.insert(0, os.path.join(project_dir(), "evolution"))
        import signals  # noqa: E402
        signals.emit(signal, **kw)
    except Exception:
        pass


def _first_reminder_this_turn():
    """True only on the FIRST valid summon of a turn. turn-start.py clears the
    sentinel on every new UserPromptSubmit, so the ~130-token weapon-doctrine
    reminder fires once per turn instead of on every single draw (it used to
    re-inject on each summon — pure repeated tax on multi-summon turns)."""
    state = os.path.join(project_dir(), ".claude", "state")
    sentinel = os.path.join(state, "weapon-reminded")
    if os.path.exists(sentinel):
        return False
    try:
        os.makedirs(state, exist_ok=True)
        open(sentinel, "w").close()
    except OSError:
        pass
    return True


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
    "the plan. Several thinkers at once only under ultra-brainstorming. "
    "SIZE THRESHOLD: a MiniMax/Ollama summon costs ~80–100s wall-time — only offload "
    "doer-grade BULK (≳1.5k tokens of output, or many repetitive transforms). For a "
    "small job (a few lines, one quick edit), the thinker does it inline; offloading "
    "it is net-negative. (weapon-utility)"
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


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str, "systemMessage":str}."""
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}
    try:
        models, retired = extract_models(tool, ti)
    except Exception as e:
        return {"exit": 0, "stderr": f"[weapon-gate] parse error, failing open: {e}\n"}

    if not models and not retired:
        return {"exit": 0}  # not a summon — nothing to govern

    if retired:
        return {"exit": 2, "stderr": (
            "⛔ WEAPON GATE — that summons MiniMax via the RETIRED Ollama route. "
            "MiniMax M3 is drawn through its DIRECT sub now: `python3 minimax.py \"…\"` "
            "or `summon.py minimax-m3`. Re-draw the prime doer directly.\n"
        )}

    valid = known_weapons()
    if valid:
        unknown = [m for m in models if m not in valid]
        if unknown:
            return {"exit": 2, "stderr": (
                f"⛔ WEAPON GATE — no such weapon in the guild arsenal: {sorted(set(unknown))}. "
                f"Draw a real weapon (one of: {', '.join(sorted(valid))}). "
                "A member can only wield weapons in its loadout — see weapon-utility.\n"
            )}

    # Capability telemetry: a valid doer draw — recorded per-occurrence (each offload
    # is a distinct datapoint for the engine's doer-discipline signal), fail-soft.
    _sense("doer-summon", surface="arsenal",
           detail=f"doer summoned: {', '.join(models)}", meta={"models": models})

    # Valid summon → non-blocking doctrine reminder (+ doer size-threshold),
    # emitted ONCE per turn (not on every draw).
    if _first_reminder_this_turn():
        return {"exit": 0, "systemMessage": REMINDER}
    return {"exit": 0}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[weapon-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)
    r = check(data)
    if r.get("systemMessage"):
        print(json.dumps({"systemMessage": r["systemMessage"]}))
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    main()
