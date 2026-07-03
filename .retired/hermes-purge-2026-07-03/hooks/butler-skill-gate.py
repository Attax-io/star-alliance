#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — BUTLER SKILL GATE  (PreToolUse, BLOCKING)
#
# THE HARD RULE: the Butler is the VOICE of the guild, not a craftsperson. He
# must not invoke any skill outside his allowlist. The gate enforces the
# helpless doctrine — the hardcoded fallback (`butler-voice`, `helpless`,
# `star-alliance-language`) is unioned into the allowlist so the Butler
# can never lock himself out of his own craft — even if guild-data.json
# is missing or the-butler is absent from it.
#
# Resolution order:
#   1. Non-Skill tools: allow.
#   2. Skill name not resolvable: allow (fail open — Skill tool with no name
#      would itself be malformed; don't brick the session on it).
#   3. Resolved name on the allowlist: allow.
#   4. A member is deployed this turn (deployment bullet OR non-intake workflow
#      banner): allow — the skill is that member's assigned tool.
#   5. Otherwise: block (exit 2) — the Butler is invoking craft he doesn't own;
#      hand the cleared order to the Strategist, who routes the member that
#      carries this skill. The Guild Master can override by explicitly assigning
#      the skill this turn (deploy the member).
#
# Fails OPEN on any internal error (unreadable transcript, missing keys,
# malformed payload): a broken skill gate must never brick every Skill tool
# in the session. Errors go to stderr.
# ─────────────────────────────────────────────────────────────────────────────
import sys, os, json, re

# Hardcoded Butler fallback floor (the helpless doctrine) — ALWAYS unioned
# into the resolved allowlist so the Butler can never lock himself out of his
# own craft regardless of whether guild-data.json is present, readable, or
# has a `the-butler` entry.
FALLBACK_ALLOW = {"butler-voice", "helpless", "star-alliance-language"}

# A deployment bullet looks like:
#   - The Developer ...
#   ▸ The Architect ...
#   * The Designer ...
# We recognize a bullet char (or dash), optional spaces, then the word `The`,
# a space, and an uppercase letter.
_DEPLOY_BULLET_RES = [
    re.compile(r"^[\s]*[•·▸*\-\u2022][\s]*The\s+[A-Z]"),
    re.compile(r"^[\s]*The\s+[A-Z]"),
]

# Reuse the workflow banner regexes — but only the names matter here; a
# banner whose name is Conversation or Routing means the Butler is still in
# intake (no member deployed yet).
BANNER_RES = [
    re.compile(r"Starmap Workflow Started:\s*(.+?)\s*!"),
    re.compile(r"▸\s*Workflow\s*[—–\-]\s*([^\n·|]+)"),
]


def find_banner(text):
    for rx in BANNER_RES:
        m = rx.search(text)
        if m:
            return m.group(1).strip()
    return None


def project_dir():
    # P0 (self-enclosed campaign): prefer code-location root over a possibly-stale
    # env var; fall back to the legacy default on any error so behaviour never regresses.
    try:
        import importlib.util as _ilu, os as _os
        _sp = _ilu.spec_from_file_location("_saroot",
            _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_saroot.py"))
        _sm = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_sm)
        return _sm.resolve_root()
    except Exception:
        return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _resolve_skill_name(data):
    """Extract the skill name from tool_input. Try `skill`, then `name`;
    lowercase; if plugin-namespaced (plugin:skill), take the part after the
    last colon. Return None if no name can be resolved."""
    ti = data.get("tool_input") or {}
    raw = ti.get("skill")
    if not raw:
        raw = ti.get("name")
    if not raw:
        return None
    name = str(raw).strip().lower()
    if ":" in name:
        name = name.rsplit(":", 1)[-1]
    return name or None


def _load_butler_allowlist():
    """Read guild-data.json, find the-butler, return its skills list lowercased.
    On any failure or missing member, return an empty list — the caller is
    responsible for unioning FALLBACK_ALLOW."""
    try:
        path = os.path.join(project_dir(), "guild-data.json")
        with open(path) as f:
            d = json.load(f)
    except Exception:
        return []
    members = d.get("members")
    if not isinstance(members, list):
        return []
    for m in members:
        if isinstance(m, dict) and m.get("id") == "the-butler":
            skills = m.get("skills") or []
            if isinstance(skills, list):
                return {str(s).strip().lower() for s in skills if str(s).strip()}
            return []
    return []


def _deployment_bullet(text):
    """True if any line in `text` looks like a deployment bullet naming a member
    ('- The Developer ...', '▸ The Architect ...', etc.)."""
    for line in (text or "").splitlines():
        for rx in _DEPLOY_BULLET_RES:
            if rx.search(line):
                return True
    return False


def last_user_index(lines):
    """Index of the last REAL user turn (not a tool_result-only message)."""
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


def assistant_text_since(lines, start):
    out = []
    for o in lines[start + 1:]:
        if o.get("type") != "assistant":
            continue
        for b in o.get("message", {}).get("content", []):
            if isinstance(b, dict) and b.get("type") == "text":
                out.append(b.get("text", ""))
    return "\n".join(out)



def _raw_skill_ref(data):
    """Raw skill ref as typed (before namespace stripping) — needed to tell a
    plugin-namespaced skill (has ':') from a bare guild skill."""
    ti = data.get("tool_input") or {}
    return str(ti.get("skill") or ti.get("name") or "").strip()


def _is_foreign_bare_skill(name, raw):
    """P3 (self-enclosed campaign) — provenance refusal. Returns a reason string
    if `name` is foreign craft the guild must refuse, else None.

    Refuse only the clear case: a BARE skill (no plugin namespace) that is NOT the
    Butler's floor and does NOT exist under the repo's own star-alliance-skills/.
    That is exactly a global ~/.claude/skills skill shadowing / substituting for
    guild craft. EXEMPT: plugin-namespaced skills (explicitly installed
    integrations), the fallback floor, and any case where we cannot positively
    identify a guild repo (fail OPEN — never brick an unrelated session)."""
    if ":" in raw:
        return None  # plugin skill — explicitly installed, not shadow craft
    if name in FALLBACK_ALLOW:
        return None
    try:
        import importlib.util as _ilu, os as _os
        _sp = _ilu.spec_from_file_location("_saroot",
            _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_saroot.py"))
        _sm = _ilu.module_from_spec(_sp); _sp.loader.exec_module(_sm)
        root = _sm.resolve_root()
        if not _sm.guild_managed(root):
            return None  # not a guild repo — do not enforce
    except Exception:
        return None  # cannot resolve — fail open
    skills_dir = os.path.join(root, "star-alliance-skills")
    if not os.path.isdir(skills_dir):
        return None  # no SoT present — fail open
    if os.path.isdir(os.path.join(skills_dir, name)):
        return None  # it IS a repo skill — provenance OK
    return (f"skill '{name}' is not part of this guild "
            f"(no star-alliance-skills/{name}/). The guild runs its OWN craft, not "
            f"global ~/.claude skills. Add it to the repo (absorb) or invoke the "
            f"plugin-namespaced version if it is an installed integration.")


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str}."""
    tool = data.get("tool_name", "")
    if tool != "Skill":
        return {"exit": 0}

    skill_name = _resolve_skill_name(data)
    if not skill_name:
        # No resolvable name — fail open; a Skill call without a name is itself
        # malformed and the rest of the gate stack will handle it.
        return {"exit": 0}

    # P3 provenance refusal — reject foreign bare skills before any role logic.
    _foreign = _is_foreign_bare_skill(skill_name, _raw_skill_ref(data))
    if _foreign:
        return {"exit": 2, "stderr": (
            f"\u26d4 SKILL PROVENANCE GATE — refused: {_foreign}\n")}

    # Always-union the hardcoded fallback (helpless doctrine) so the Butler
    # can never lock himself out of his own craft, even if guild-data.json
    # is missing/broken.
    allowlist = set(_load_butler_allowlist()) | FALLBACK_ALLOW

    if skill_name in allowlist:
        return {"exit": 0}

    # Member-deployed override: if THIS turn the orchestrator already emitted
    # a deployment bullet naming a member, or a non-intake workflow banner,
    # the skill is that member's assigned tool — allow.
    transcript = data.get("transcript_path")
    text = ""
    if transcript and os.path.exists(transcript):
        try:
            lines = [json.loads(l) for l in open(transcript) if l.strip()]
            ui = last_user_index(lines)
            text = assistant_text_since(lines, ui)
        except Exception:
            text = ""

    # Race grace: at the FIRST tool of a turn the assistant text isn't flushed
    # yet — allow (mirrors workflow-gate's first-tool race grace).
    if not text.strip():
        return {"exit": 0}

    if _deployment_bullet(text):
        return {"exit": 0}

    banner = find_banner(text)
    if banner and banner.lower() not in ("conversation", "routing"):
        return {"exit": 0}

    # Pure Butler turn invoking a craft skill outside his allowlist.
    return {"exit": 2, "stderr": (
        f"⛔ BUTLER SKILL GATE — refused skill '{skill_name}'. "
        f"That is not your job. Dispatch the Strategist now: Task(subagent_type=\"the-strategist\", prompt=\"route: <the skill/task the Guild Master asked for>\") so it assigns the member that actually carries this skill. "
        f"(Enforces the helpless doctrine: the Butler is the voice, not a craftsperson.) "
        f"The Guild Master can override by explicitly assigning the skill this turn.\n"
    )}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[butler-skill-gate] malformed payload, failing open: {e!s}\n")
        sys.exit(0)
    try:
        r = check(data) or {"exit": 0}
    except Exception as e:
        # ANY internal error fails OPEN — a skill gate must never brick the session.
        sys.stderr.write(f"[butler-skill-gate] internal error, failing open: {e!s}\n")
        sys.exit(0)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    main()