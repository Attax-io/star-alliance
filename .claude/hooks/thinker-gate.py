#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — THINKER CONFORMITY GATE  (PreToolUse: Task|Agent, BLOCKING)
#
# THE DOCTRINE: each member declares its thinker `model:` and the harness must run
# it. A deployed member can only diverge from its declared model ONE way — an
# explicit `model` override on the Task/Agent call — and that override is in the
# tool input BEFORE the subagent spawns. So this is the single point where a
# member/model mismatch is both DETECTABLE and PREVENTABLE: we block the spawn.
# (Post-hoc proof of a subagent's actual model isn't available in this setup — no
# sidechain transcript — so the pre-spawn block is the real, mechanical teeth.)
#
# DECISION (only for spawns whose subagent_type is a real guild member):
#   • no `model` override            → allow (member runs its declared model by construction)
#   • override == declared model     → allow + ledger the attested pairing
#   • override != declared model     → BLOCK (exit 2) + ledger — the Guild Master chose
#                                      "record + hard block" on a mismatch
# Non-member agent types (Explore, general-purpose, …) have no declared thinker, so
# overriding them is fine — the missing agent file naturally scopes enforcement to
# guild members (fail-open-on-missing).
#
# LOGGED override: SA_ALLOW_MODEL_OVERRIDE=1 lets a deliberate cross-model launch
# through, on the record. Fails OPEN on any error — a broken gate never bricks the
# tool layer. Designed as a pure check(data) for the sa-pretool.py dispatcher.
# ─────────────────────────────────────────────────────────────────────────────
import sys
import os
import re
import json


def _proj():
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


def _ledger(repo, **kw):
    try:
        sys.path.insert(0, os.path.join(repo, "evolution"))
        import ledger  # noqa: E402
        ledger.append(**kw)
    except Exception:
        pass


def _declared_model(repo, sub):
    """The `model:` frontmatter of a generated agent file, or None if unreadable
    (which scopes enforcement to real guild members)."""
    path = os.path.join(repo, ".claude", "agents", f"{sub}.md")
    try:
        with open(path, encoding="utf-8") as fh:
            head = fh.read(4000)
    except OSError:
        return None
    m = re.search(r"(?mi)^\s*model:\s*([A-Za-z0-9._-]+)\s*$", head)
    return m.group(1).strip() if m else None


def _is_known_member(repo, sub):
    """True iff `sub` is a declared guild member (per star-alliance-members/ or
    guild-data.json), independent of whether its generated agent file exists.
    Only meaningful in a guild-managed repo; empty knowledge => False (fail open)."""
    import os as _os, json as _json
    mem_dir = _os.path.join(repo, "star-alliance-members")
    try:
        if _os.path.isfile(_os.path.join(mem_dir, f"{sub}.md")):
            return True
    except OSError:
        pass
    try:
        d = _json.load(open(_os.path.join(repo, "guild-data.json"), encoding="utf-8"))
        return sub in {m.get("id") for m in (d.get("members") or []) if isinstance(m, dict)}
    except Exception:
        return False


def _norm(s):
    return (s or "").strip().lower()


def check(data):
    """Pure decision. Returns {"exit":0|2, "stderr":str, "systemMessage":str}."""
    tool = data.get("tool_name", "")
    if tool not in ("Task", "Agent"):
        return {"exit": 0}

    ti = data.get("tool_input", {})
    if not isinstance(ti, dict):
        return {"exit": 0}
    sub = ti.get("subagent_type") or ti.get("subagentType") or ""
    override = ti.get("model")
    if not sub or not override:
        return {"exit": 0}                              # no override → declared model runs

    repo = _proj()
    declared = _declared_model(repo, sub)
    if declared is None:
        # P4 (self-enclosed campaign): distinguish "genuinely not a guild member"
        # (allow — Explore/Plan/etc. have no declared thinker) from "a KNOWN guild
        # member whose agent file is missing" (a half-installed guild, e.g. the Lex
        # empty .claude/agents/ case). In the latter we cannot validate the override,
        # so in a guild-managed repo we fail CLOSED and point at the installer.
        if _is_known_member(repo, sub):
            return {"exit": 2, "stderr": (
                f"\u26d4 THINKER GATE — '{sub}' is a guild member but its agent file "
                f"(.claude/agents/{sub}.md) is missing, so its declared thinker model "
                f"cannot be verified. This repo is a half-installed guild. Run the "
                f"installer to populate agents:\n"
                f"     python3 guild/install_agents.py\n"
                f"   (Override for a deliberate cross-model launch: SA_ALLOW_MODEL_OVERRIDE=1.)\n"
            )}
        return {"exit": 0}                              # genuinely not a guild member

    friendly = "The " + sub.replace("the-", "").replace("-", " ").title()

    if os.environ.get("SA_ALLOW_MODEL_OVERRIDE") == "1":
        _ledger(repo, kind="thinker", author=override, surface="arsenal",
                verdict="override",
                detail=f"thinker override (allowed): {sub} declared {declared}, ran {override}",
                meta={"role": "thinker", "member": sub,
                      "declared": declared, "override": override})
        return {"exit": 0,
                "systemMessage": f"▸ Thinker override (logged) — {friendly}: "
                                 f"{declared} → {override}"}

    if _norm(override) == _norm(declared):
        _ledger(repo, kind="thinker", author=override, surface="arsenal", verdict="pass",
                detail=f"thinker conformity: {sub} ran as declared {declared}",
                meta={"role": "thinker", "member": sub, "declared": declared})
        return {"exit": 0,
                "systemMessage": f"▸ Thinker verified — {friendly} ({declared})"}

    _ledger(repo, kind="thinker", author=override, surface="arsenal", verdict="block",
            detail=f"thinker mismatch: {sub} declares {declared}, launched as {override}",
            meta={"role": "thinker", "member": sub,
                  "declared": declared, "override": override})
    return {"exit": 2, "stderr": (
        f"⛔ THINKER GATE — you are launching {friendly} ({sub}) as '{override}', but it "
        f"declares its thinker model as '{declared}'. A member must run its declared "
        f"thinker. Drop the `model` override (it will run '{declared}'), or — if the "
        f"cross-model launch is deliberate — put it ON THE RECORD: "
        f"SA_ALLOW_MODEL_OVERRIDE=1 and re-dispatch.\n"
    )}


def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        sys.stderr.write(f"[thinker-gate] malformed payload, failing open: {e}\n")
        sys.exit(0)
    r = check(data)
    if r.get("stderr"):
        sys.stderr.write(r["stderr"])
    sys.exit(r.get("exit", 0))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Parity with the sibling gates: a broken gate must never brick the tool
        # layer (in production sa-pretool.py also wraps check() → fail open).
        sys.stderr.write(f"[thinker-gate] {e}, failing open\n")
        sys.exit(0)
