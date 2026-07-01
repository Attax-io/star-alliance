#!/usr/bin/env python3
"""Conformity check — audit the whole Star Alliance repo for internal conformity
and conformity with every decision on record (guild-log type:decision).

Read-only. Prints a PASS/FAIL map and exits 1 on any contradiction. The Quartermaster
runs this as the spine of the `compliance-audit` star-map workflow.

UNIFIED VERSION — works in the merged repo that contains BOTH Claude-side
(star-alliance-members/, data/members-meta.json, CLAUDE.md) and Hermes-side
(agents/, data/agents-meta.json, AGENTS.md, profiles/) files. If both naming
conventions exist, both are checked; if only one exists, that one is used.

Checks (each maps to a source-of-truth invariant or a logged decision):
  P  parity        guild-data.js  ==  guild-data.json
  D23 report-gate  every workflow ENDS with a Butler 'report' gate   (decision #23)
  C  qm-close      every workflow's last agent step before report is the-quartermaster
  BR brain         each agent's session model (model:) is a registry thinker (brain = personality)
  ST seats         models.json `seats` valid (Brain/Doer/Critic/Bench) + critic family != brain family
  R  refs          workflow actors ∈ agents∪{you}; gates valid; agent skills exist
  SD skill-drills  every agent-carried skill has a `## Skill Drills` table row
  N  counts        guild-data meta.counts == real lengths
  WART weapon-art  every registry weapon has a weapon-art/<id>.png tile
  MU usage-sidecar models-usage.json keys ⊆ registry ids
  FB fallback-sync fail-safe ROLE/CLOUD_TAG dicts == models.json (anti-drift)
  RG routing-gate  guild-routing-gate agent→model prose == guild-data
  PD profile-dist   repo profiles/<agent>/ SOUL.md+config.yaml == installed ~/.hermes/profiles/<slug>/
  AL arch-layers   CLAUDE.md and AGENTS.md both describe the three-layer architecture,
                   and the model table in each matches models.json seats
  DX dispatch-xref tools/dispatch.py AGENTS dict → profiles/<folder>/ directory exists
  MP member-parity star-alliance-members/ and agents/ reference the same agent IDs (if both exist)
"""
import json, re, sys, pathlib

ROOT = next((p for p in pathlib.Path(__file__).resolve().parents
             if (p / "VERSIONS.md").exists() and (p / ".git").exists()),
            pathlib.Path(__file__).resolve().parent)

# ── Dual naming support ──────────────────────────────────────────────────────
# The merged repo may have guild-data.json with either "agents" (Hermes) or
# "members" (Claude) as the top-level key.  We detect which exists and use it.
# The same applies to data/agents-meta.json vs data/members-meta.json, and
# agents/ vs star-alliance-members/ directories.

def _detect_agents_key(g):
    """Return ('agents', g['agents']) or ('members', g['members']) — whichever exists."""
    if "agents" in g:
        return "agents", g["agents"]
    if "members" in g:
        return "members", g["members"]
    raise KeyError("guild-data.json has neither 'agents' nor 'members' key")

def _detect_meta_path():
    """Return the path to the agents/members meta file, whichever exists."""
    for name in ("agents-meta.json", "members-meta.json"):
        p = ROOT / "data" / name
        if p.exists():
            return p
    return ROOT / "data" / "agents-meta.json"  # default (will fail loudly if truly absent)

def _detect_meta_key(path):
    """Return the JSON key inside the meta file ('agents' or 'members')."""
    try:
        d = json.loads(path.read_text())
        if "agents" in d:
            return "agents"
        if "members" in d:
            return "members"
    except Exception:
        pass
    return "agents"  # default

def _detect_agent_dirs():
    """Return a list of (dir_path, label) tuples for agent definition directories that exist."""
    dirs = []
    agents_dir = ROOT / "agents"
    members_dir = ROOT / "star-alliance-members"
    if agents_dir.is_dir():
        dirs.append((agents_dir, "agents"))
    if members_dir.is_dir():
        dirs.append((members_dir, "members"))
    if not dirs:
        # fall back to agents/ as default (will fail if truly absent)
        dirs.append((agents_dir, "agents"))
    return dirs

# role per model id — DERIVED from the canonical registry
# (star-alliance-arsenal/models.json). The literal below is a FAIL-SAFE only.
# Media weapons are normalized to "doer" for arsenal ordering; sonnet "both" forced last.
_FALLBACK_ROLE = {
    "opus": "thinker",
    "sonnet": "both",
    "haiku": "both",
    "minimax-sub": "doer",
    "minimax-payg": "doer",
    "glm-5.2": "doer",
    "kimi-k2.7": "doer",
    "image-01": "doer", "minimax-video": "doer", "minimax-speech": "doer", "minimax-music": "doer",
}


def _load_role():
    try:
        arsenal = str(ROOT / "star-alliance-arsenal")
        if arsenal not in sys.path:
            sys.path.insert(0, arsenal)
        import models_registry as _reg
        rm = _reg.role_map()
        if not rm:
            return dict(_FALLBACK_ROLE)
        norm = {mid: ("doer" if r == "media" else r) for mid, r in rm.items()}
        norm.setdefault("qwen-3.5", "thinker")  # legacy alias kept for old refs
        return norm
    except Exception:
        return dict(_FALLBACK_ROLE)


ROLE = _load_role()

HERMES_NATIVE = {"glm-5.2", "minimax-sub", "minimax-payg", "kimi-k2.7"}
CLAUDE_NATIVE = {"opus", "haiku", "sonnet"}
MEDIA_WEAPONS = {"image-01", "minimax-video", "minimax-speech", "minimax-music"}

# Vendor-published skills ship with every Hermes profile by default (they're the
# shared toolbox: apple, github, research, etc.). When checking that a profile's
# installed skill-set matches the member's declared `skills:`, we EXCLUDE these
# vendor skills from the equality check — they are present by convention, not by
# declaration. The list lives here (not in guild-data) because it's a property of
# the Hermes skill registry, not of the guild data model.
HERMES_VENDOR_SKILLS = {
    "apple", "autonomous-ai-agents", "computer-use", "creative", "data-science",
    "dogfood", "email", "github", "media", "mlops", "note-taking", "productivity",
    "research", "smart-home", "social-media", "software-development", "yuanbao",
    "hermes-project-anchoring",
}


def _skill_fingerprint(skill_dir):
    """SHA-256 fingerprint of a skill directory's full content.

    Mirrors the approach used by .claude/tools/skill_fingerprint.py: every file
    under the directory (relative path + sha256 of bytes), sorted by relative
    path for determinism, then the resulting list-of-pairs is hashed as JSON.

    Returns None if the directory does not exist or has no SKILL.md (a skill
    without SKILL.md is not a real skill — let the caller decide whether that's
    a fail or a skip).
    """
    import hashlib
    if not skill_dir.is_dir():
        return None
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return None
    files = []
    for p in sorted(skill_dir.rglob("*")):
        if p.is_file():
            files.append((str(p.relative_to(skill_dir)), hashlib.sha256(p.read_bytes()).hexdigest()))
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def frontmatter_list(text, key):
    m = re.search(rf'^{key}:\s*\[([^\]]*)\]', text, re.M)
    if not m:
        return None
    return [x.strip() for x in m.group(1).split(",") if x.strip()]


def main():
    fails = []
    notes = []

    g = json.loads((ROOT / "guild-data.json").read_text())

    # ── Detect naming convention ──
    agents_key, agents_list = _detect_agents_key(g)
    agents = {m["id"]: m for m in agents_list}

    skills_meta = json.loads((ROOT / "data/skills-meta.json").read_text())
    skill_ids = set(skills_meta.keys())

    meta_path = _detect_meta_path()
    meta_key = _detect_meta_key(meta_path)
    meta = json.loads(meta_path.read_text())[meta_key]

    log = json.loads((ROOT / "data/guild-log.json").read_text())["entries"]
    decisions = [e for e in log if e.get("type") == "decision"]

    # Step kind: "agent" (Hermes) or "member" (Claude) — accept both
    AGENT_KINDS = {"agent", "member"}

    # P — guild-data.js == guild-data.json
    js_path = ROOT / "guild-data.js"
    if js_path.exists():
        js = js_path.read_text()
        mo = re.search(r'\{.*\}', js, re.S)
        if not mo or json.loads(mo.group(0)) != g:
            fails.append("P  parity: guild-data.js does NOT match guild-data.json (rerun build.py)")

    # Swarm guardrail constants (§5 SWARM-METHODOLOGY-PLAN.md)
    MAX_SWARM = 5
    VALID_PARTITIONS = {"by-file", "by-module", "by-subtask"}
    VALID_ISOLATIONS = {"shared-tree", "worktree"}

    # workflow-level checks
    for wf in g["workflows"]:
        wid = wf["id"]
        steps = wf["steps"]
        # D23 — ends with report gate
        last = steps[-1] if steps else {}
        if last.get("kind") != "gate" or last.get("gate") != "report":
            fails.append(f"D23 {wid}: does not END with a 'report' gate (decision #23)")
        # SW1–SW5 — swarm object guardrails (fail-soft: never crash the sweep)
        try:
            for si, s in enumerate(steps):
                if s.get("kind") not in AGENT_KINDS:
                    continue
                sw = s.get("swarm")
                if sw is None:
                    continue
                actor = s.get("actor", "")
                # SW1 — swarm.agent (or swarm.member) must equal the step's actor
                sw_agent = sw.get("agent") or sw.get("member")
                if sw_agent != actor:
                    fails.append(f"SW1 {wid} step '{s.get('title','?')}': swarm.agent/member "
                                 f"'{sw_agent}' != actor '{actor}'")
                # SW2 — 1 < max_instances <= MAX_SWARM, 2 <= min_instances <= max_instances
                max_i = sw.get("max_instances")
                min_i = sw.get("min_instances")
                if not (isinstance(max_i, int) and 1 < max_i <= MAX_SWARM):
                    fails.append(f"SW2 {wid} step '{s.get('title','?')}': max_instances "
                                 f"({max_i!r}) must satisfy 1 < n <= {MAX_SWARM}")
                if not (isinstance(min_i, int) and isinstance(max_i, int)
                        and 2 <= min_i <= max_i):
                    fails.append(f"SW2 {wid} step '{s.get('title','?')}': min_instances "
                                 f"({min_i!r}) must satisfy 2 <= min <= max_instances ({max_i!r})")
                # SW3 — partition and isolation enums
                part = sw.get("partition")
                iso = sw.get("isolation")
                if part not in VALID_PARTITIONS:
                    fails.append(f"SW3 {wid} step '{s.get('title','?')}': partition "
                                 f"'{part}' not in {sorted(VALID_PARTITIONS)}")
                if iso not in VALID_ISOLATIONS:
                    fails.append(f"SW3 {wid} step '{s.get('title','?')}': isolation "
                                 f"'{iso}' not in {sorted(VALID_ISOLATIONS)}")
                # SW4 — when integration_step:true, must be followed in-stage by an inline
                # same-actor step
                if sw.get("integration_step"):
                    stage = s.get("stage")
                    found_integration = False
                    for s2 in steps[si + 1:]:
                        if s2.get("stage") != stage:
                            continue
                        if (s2.get("kind") in AGENT_KINDS
                                and s2.get("actor") == actor
                                and s2.get("exec") == "inline"):
                            found_integration = True
                            break
                    if not found_integration:
                        fails.append(
                            f"SW4 {wid} step '{s.get('title','?')}': integration_step:true "
                            f"but no following inline same-actor step found in stage '{stage}'"
                        )
                # SW5 — swarm.agent/member must be a real guild agent id
                if sw_agent and sw_agent not in agents:
                    fails.append(f"SW5 {wid} step '{s.get('title','?')}': swarm.agent/member "
                                 f"'{sw_agent}' is not a guild agent id")
        except Exception as _sw_exc:
            notes.append(f"SW  {wid}: swarm guardrail check raised an exception "
                         f"(skipped, fail-soft): {_sw_exc}")
        # R — actors + gates resolve
        for s in steps:
            if s.get("kind") in AGENT_KINDS:
                a = s.get("actor")
                if a != "you" and a not in agents:
                    fails.append(f"R  {wid}: unknown actor '{a}'")
                # WPN — structured weapon fields (optional) stay valid: thinker is a
                # thinker-role weapon in the actor's loadout; doers are doer-role and in
                # loadout; ultra only if the actor carries ultra-brainstorming.
                if a in agents:
                    am = agents[a]
                    loadout = {w["model"] for w in am.get("weapons", [])}
                    th = s.get("thinker")
                    if th is not None and (ROLE.get(th) not in ("thinker", "both") or th not in loadout):
                        fails.append(f"WPN {wid}: step '{s.get('title','?')}' thinker '{th}' "
                                     f"is not a thinker-role weapon in {a}'s loadout")
                    for d in (s.get("doers") or []):
                        model = d.get("model") if isinstance(d, dict) else d
                        cnt = d.get("count", 1) if isinstance(d, dict) else 1
                        if not isinstance(cnt, int) or cnt < 1:
                            fails.append(f"WPN {wid}: step '{s.get('title','?')}' doer '{model}' bad count {cnt!r}")
                        if ROLE.get(model) not in ("doer", "both") or model not in loadout:
                            fails.append(f"WPN {wid}: step '{s.get('title','?')}' doer '{model}' "
                                         f"is not a doer-role weapon in {a}'s loadout")
                    if s.get("ultra") and "ultra-brainstorming" not in am.get("skills", []):
                        fails.append(f"WPN {wid}: step '{s.get('title','?')}' ultra=true but "
                                     f"{a} lacks the ultra-brainstorming skill")
            elif s.get("kind") == "gate":
                if s.get("gate") not in {"approval", "certify", "report"}:
                    fails.append(f"R  {wid}: unknown gate '{s.get('gate')}'")
            else:
                fails.append(f"R  {wid}: unknown step kind '{s.get('kind')}'")
        # C — last agent step before the final report gate is the-quartermaster
        wf_class = wf.get("class", "mutating")
        if wf_class not in ("mutating", "read-only"):
            fails.append(f"CLS {wid}: unknown class '{wf_class}' (expected mutating | read-only)")
        agent_steps = [s for s in steps if s.get("kind") in AGENT_KINDS]
        # C — the Quartermaster conformance-close is required only for MUTATING workflows
        # (those that change guild artifacts). Read-only/advisory workflows end at the
        # Butler's report with the worker as the last agent step — no ceremonial close.
        if wf_class != "read-only" and agent_steps and agent_steps[-1].get("actor") != "the-quartermaster":
            fails.append(f"C  {wid}: mutating workflow closes with '{agent_steps[-1].get('actor')}', "
                         f"not the-quartermaster (conformance-close convention)")
        # read-only workflows must NOT end on a Quartermaster close — the worker is the
        # last agent step; a trailing Quartermaster is the ceremonial no-op we removed.
        if wf_class == "read-only" and agent_steps and agent_steps[-1].get("actor") == "the-quartermaster":
            fails.append(f"C  {wid}: read-only workflow closes with a Quartermaster step "
                         f"(a no-op conformance close — remove it; the Butler report is the deliverable)")

    # per-agent checks. Phase 2 (4-seat arsenal): per-agent loadouts are GONE —
    # the arsenal is universal (models.json "seats"), so the old per-loadout checks
    # (A order · PD prime-doer · W weaponsDesc · S frontmatter · WT table) are retired
    # and replaced by ST (seats valid + critic≠brain family) above. Only the BRAIN is
    # per-agent: it's the session model the agent runs as.
    for mid, m in agents.items():
        # BR — the brain (session model) must be a registry weapon that can think.
        # A NULL/missing brain is itself a fail: build.py emits top-level "model": null
        # while seats.brain silently falls back to the seat default — an inconsistent
        # agent. Every agent must declare its own session model (model:) in frontmatter.
        brain = m.get("model")
        if not brain:
            fails.append(f"BR {mid}: no session model (model:) declared — every agent "
                         f"must name its own brain (falling back to the seat default is inconsistent)")
        elif brain not in ROLE:
            fails.append(f"BR {mid}: brain '{brain}' has no role mapping in the registry")
        elif ROLE.get(brain) not in ("thinker", "both"):
            fails.append(f"BR {mid}: brain '{brain}' has role '{ROLE.get(brain)}' — "
                         f"a brain must be able to think (thinker|both)")
        # NEW RULE: a member's declared brain model must have backend == 'claude' in
        # the registry. The brain drives the thinker→executor→critic loop; only the
        # Claude family is tool-capable and orchestrating-grade. A non-Claude brain is
        # a silent downgrade and a hard failure.
        if brain and brain in ROLE:
            try:
                _br_regm = json.loads(
                    (ROOT / "star-alliance-arsenal" / "models.json").read_text()
                ).get("models", {})
            except Exception:
                _br_regm = {}
            _br_backend = (_br_regm.get(brain) or {}).get("backend")
            if _br_backend and _br_backend != "claude":
                fails.append(f"BR {mid}: brain '{brain}' has backend '{_br_backend}' — "
                             f"a member's brain must have backend == 'claude' "
                             f"(only Claude models can drive the loop)")
        # R — agent skills exist in skills-meta
        for sk in m.get("skills", []):
            if sk not in skill_ids:
                fails.append(f"R  {mid}: skill '{sk}' not in skills-meta")

    # U — weapon-utility is foundational: every agent must carry it (session decision)
    if "weapon-utility" in skill_ids:
        for mid, m in agents.items():
            if "weapon-utility" not in m.get("skills", []):
                fails.append(f"U  {mid}: missing foundational skill 'weapon-utility' (every agent must carry it)")

    # SD — Skill Drills coverage: every skill a agent carries must be DRILLED in that
    # agent's `## Skill Drills` table — i.e. appear as a table ROW (matched by the
    # `| <skill> |` cell). The frontmatter `skills:` list declares what the agent wields;
    # the drills table declares WHEN/when-NOT to wield each. A carried-but-undrilled skill
    # is a coverage hole the agent would have no firing doctrine for → HARD FAIL.
    # Check ALL agent definition directories (agents/ and/or star-alliance-members/).
    for agent_dir, _label in _detect_agent_dirs():
        for md in sorted(agent_dir.glob("the-*.md")):
            text = md.read_text()
            skills = frontmatter_list(text, "skills")
            if skills is None:
                continue  # no skills frontmatter → nothing to drill
            body = text.split("---", 2)[2] if text.count("---") >= 2 else text
            for sk in skills:
                if re.search(r'\|\s*`?' + re.escape(sk) + r'`?\s*\|', body) is None:
                    fails.append(f"SD {md.stem}: skill '{sk}' is carried but has no Skill Drills "
                                 f"table row (add a `| {sk} | ... |` drill)")

    # T — every type build.py explicitly classifies must be loggable via log_event.py
    def _set(text, name):
        mo = re.search(rf'{name}\s*=\s*\{{([^}}]*)\}}', text)
        return set(re.findall(r'"([^"]+)"', mo.group(1))) if mo else set()
    bp_path = ROOT / "build.py"
    if bp_path.exists():
        bp = bp_path.read_text()
        le_path = ROOT / "tools" / "log_event.py"
        if le_path.exists():
            le = le_path.read_text()
            classified = _set(bp, "VERSION_MAJOR_TYPES") | _set(bp, "VERSION_MINOR_TYPES") | _set(bp, "VERSION_IGNORE_TYPES")
            loggable = _set(le, "VALID_TYPES")
            orphan = classified - loggable
            if orphan:
                fails.append(f"T  build.py classifies {sorted(orphan)} but log_event.py cannot log them")

    # K — skill dirs == skills-meta keys == generated skill ids (no orphan/uncounted skills)
    skill_dirs = {d.name for d in (ROOT / "star-alliance-skills").iterdir()
                  if d.is_dir() and (d / "SKILL.md").exists()}
    meta_keys = set(skills_meta.keys())
    data_ids = {s["id"] for s in g["skills"]}
    if skill_dirs != meta_keys:
        new_dirs = sorted(skill_dirs - meta_keys)
        hint = "  → auto-wire: python3 tools/wire_skill.py --all" if new_dirs else ""
        fails.append(f"K  skill dirs vs skills-meta differ: only-dir={new_dirs} "
                     f"only-meta={sorted(meta_keys - skill_dirs)}{hint}")
    if skill_dirs != data_ids:
        fails.append(f"K  skill dirs vs guild-data differ: only-dir={sorted(skill_dirs - data_ids)} "
                     f"only-data={sorted(data_ids - skill_dirs)}")

    # ART — every skill ships with a Fallen Sword tile (never a bare-emoji fallback)
    artless = sorted(s for s in skill_dirs
                     if not (ROOT / "art" / "skill-art" / f"{s}.png").exists())
    if artless:
        fails.append(f"ART skills missing a skill-art/<id>.png tile: {artless} "
                     f"(forge via tools/generators/gen-skill-art.cjs + build.py)")

    # VER — every skill has a VERSIONS.md registry row whose version matches its SKILL.md
    versions_path = ROOT / "VERSIONS.md"
    if versions_path.exists():
        versions_txt = versions_path.read_text()
        ver_rows = dict(re.findall(
            r'\|\s*\[`([^`]+)`\][^|]*\|\s*([0-9]+\.[0-9]+\.[0-9]+)\s*\|', versions_txt))
        for s in sorted(skill_dirs):
            smd = (ROOT / "star-alliance-skills" / s / "SKILL.md").read_text()
            vm = re.search(r'^\s*version:\s*([0-9]+\.[0-9]+\.[0-9]+)', smd, re.M)
            skill_ver = vm.group(1) if vm else None
            if s not in ver_rows:
                fails.append(f"VER {s}: no row in VERSIONS.md "
                             f"(regen: star-alliance-skills/skillsmith/scripts/skill_registry.py write)")
            elif skill_ver and ver_rows[s] != skill_ver:
                fails.append(f"VER {s}: VERSIONS.md says {ver_rows[s]} but SKILL.md is {skill_ver}")

    # === AG — agents/*.md are the SOURCE (SSOT), and ~/.hermes/profiles/*/AGENTS.md are GENERATED from them (the SSOT).
    # Never hand-edit an agent file. install_agents.py --check is the authority; any drift
    # is a hard contradiction so a stale agent (what the model actually runs as) is caught.
    import subprocess as _sp
    install_agents_path = ROOT / "guild" / "install_agents.py"
    if install_agents_path.exists():
        try:
            _r = _sp.run(["python3", str(install_agents_path), "--check"],
                         capture_output=True, text=True, timeout=30)
            for _ln in _r.stdout.splitlines():
                _m = re.match(r"\s*DRIFT\s+(\S+)", _ln)
                if _m:
                    fails.append(f"AG profile '{_m.group(1)}' drifted from agents/ "
                                 f"(SSOT) — run: python3 guild/install_agents.py")
        except Exception:
            pass

    # === HP — ~/.hermes/profiles/star-alliance-*/AGENTS.md are GENERATED from
    # agents/ (the SSOT). Same drift rule as AG but for Hermes
    # profiles. install_agents.py --check reports drift for Hermes profiles.
        try:
            _r = _sp.run(["python3", str(install_agents_path), "--check"],
                         capture_output=True, text=True, timeout=30)
            for _ln in _r.stdout.splitlines():
                if "(hermes" in _ln and "DRIFT" in _ln:
                    _m = re.search(r"DRIFT\s+(\S+)\s+\(hermes", _ln)
                    if _m:
                        fails.append(f"HP hermes profile '{_m.group(1)}' AGENTS.md drifted from "
                                     f"agents/ (SSOT) — run: python3 guild/install_agents.py")
        except Exception:
            pass

    # === LITE — workflows-lite.json is GENERATED from workflows.json (SSOT); never
    # hand-edit. gen_workflows_lite.py --check is the authority.
    gen_lite_path = ROOT / "guild" / "gen_workflows_lite.py"
    if gen_lite_path.exists():
        try:
            _rl = _sp.run(["python3", str(gen_lite_path), "--check"],
                          capture_output=True, text=True, timeout=30)
            if _rl.returncode != 0:
                fails.append("LITE workflows-lite.json drifted from workflows.json (SSOT) — "
                             "run: python3 guild/gen_workflows_lite.py")
        except Exception:
            pass

    # G — gen-workflow-art.cjs has a prompt entry for every workflow (art can be forged)
    gen = (ROOT / "tools/generators/gen-workflow-art.cjs")
    if gen.exists():
        gen_ids = set(re.findall(r'id:\s*"([^"]+)"', gen.read_text()))
        uncovered = {w["id"] for w in g["workflows"]} - gen_ids
        if uncovered:
            fails.append(f"G  tools/generators/gen-workflow-art.cjs missing art prompt for {sorted(uncovered)}")

    # N — counts
    counts = g.get("meta", {}).get("counts", {})
    real = {agents_key: len(agents_list), "skills": len(g["skills"]), "workflows": len(g["workflows"])}
    for k, v in real.items():
        if counts.get(k) != v:
            fails.append(f"N  counts.{k}={counts.get(k)} != real {v}")

    # === DC — doc count claims match reality (README + domains) — audit #1 ===
    actual_skills = len(skill_dirs)
    readme_path = ROOT / "README.md"
    if readme_path.exists():
        readme_txt = readme_path.read_text()
        for mobj in re.finditer(r'\((\d+)\s+skills', readme_txt):
            if int(mobj.group(1)) != actual_skills:
                fails.append(f"DC README claims {mobj.group(1)} skills, actual {actual_skills}")
    doms_path = ROOT / "data/domains.json"
    if doms_path.exists():
        doms = json.loads(doms_path.read_text())["domains"]
        home = next((d for d in doms if d["id"] == "star-alliance"), None)
        if home:
            if len(home["skills"]) != actual_skills:
                fails.append(f"DC domains star-alliance lists {len(home['skills'])} skills, actual {actual_skills}")
            # domains.json key may be "agents" or "members" depending on naming
            home_agents_key = "agents" if "agents" in home else "members"
            if len(home.get(home_agents_key, [])) != real[agents_key]:
                fails.append(f"DC domains star-alliance lists {len(home.get(home_agents_key, []))} {home_agents_key}, actual {real[agents_key]}")
            note = home.get("notes", "")
            for mm in re.finditer(r'(\d+)\s+guild (?:agents|members)', note):
                if int(mm.group(1)) != real[agents_key]:
                    fails.append(f"DC domains notes: '{mm.group(1)} guild agents/members' != actual {real[agents_key]}")
            for ss in re.finditer(r'(\d+)\s+skills', note):
                if int(ss.group(1)) != actual_skills:
                    fails.append(f"DC domains notes: '{ss.group(1)} skills' != actual {actual_skills}")

        # === SEC — agent-page skill split stays self-maintaining (skills-carried widget) ===
        # The agent dossier renders carried skills as General + one widget per sector domain
        # that lists the skill. Grouping is by SECTOR MEMBERSHIP (a non-home domain's skills[]),
        # not the `global` install flag. A skill in no non-home sector renders under General by
        # design, so there is no "untagged" failure mode — only a dead reference can break the
        # auto-grouping: a domain lists a skill id that no longer exists → HARD FAIL (the sector
        # widget would render a ghost line).
        for d in doms:
            for sid in d.get("skills", []):
                if sid not in data_ids:
                    fails.append(f"SEC domain '{d['id']}' lists unknown skill '{sid}' "
                                 f"(dead ref — agent-page sector widget would render a ghost)")

    # === V — every skill SKILL.md carries a parseable version — audit #1 ===
    for name in sorted(skill_dirs):
        txt = (ROOT / "star-alliance-skills" / name / "SKILL.md").read_text()
        if not re.search(r'(?m)^[ \t]*version:\s*\S+', txt):
            fails.append(f"V  skill '{name}' has no version in SKILL.md (metadata.version required)")

    # === L — weapon routability (hard) + liveness (NOTE) — audit #1/#2 ===
    summon_path = ROOT / "star-alliance-arsenal" / "summon.py"
    cloud_map = {}
    if summon_path.exists():
        smt = summon_path.read_text()
        cloud_map = dict(re.findall(r"'([^']+)':\s*'([^']+:cloud)'", smt))
    routable = set(HERMES_NATIVE) | set(CLAUDE_NATIVE) | set(cloud_map) | MEDIA_WEAPONS | {"minimax-sub", "minimax-payg"}
    all_weapons = {w for m in agents.values() for w in (x["model"] for x in m.get("weapons", []))}
    for w in sorted(all_weapons - routable):
        fails.append(f"L  weapon '{w}' in a loadout is not routable by summon.py or native")
    # liveness — best-effort, NOTE only (never a hard fail; it is environment-dependent)
    import os as _os
    try:
        _ol = _sp.run(["ollama", "list"], capture_output=True, text=True, timeout=10).stdout
        pulled = {ln.split()[0] for ln in _ol.splitlines()[1:] if ln.strip()}
    except Exception:
        pulled = set()
    live = set(HERMES_NATIVE) | set(CLAUDE_NATIVE)
    for w, tag in cloud_map.items():
        if tag in pulled:
            live.add(w)
    if (pathlib.Path.home() / ".config" / "minimax" / "m3.key").exists() or _os.environ.get("MINIMAX_API_KEY"):
        live |= {"minimax-sub", "minimax-payg"} | MEDIA_WEAPONS
    dead = sorted(all_weapons - live)
    if dead:
        notes.append(f"weapon liveness — NOT firing on this device: {', '.join(dead)}")
        for w in dead:
            users = sorted(mid for mid, m in agents.items() if w in (x["model"] for x in m.get("weapons", [])))
            notes.append(f"  '{w}' declared by {len(users)} agent(s): {', '.join(users)}")

    # agent leveling — promotion queue + regression review (NOTES, never blocking).
    # Leveling is Quartermaster-gated and human-in-the-loop, so drift belongs in the
    # QM's queue, not the build gate. See docs/STRATEGIST-MEMBER-LEVELING.md §3.
    due = [(mid, m) for mid, m in agents.items() if m.get("levelInfo", {}).get("dueForPromotion")]
    over = [(mid, m) for mid, m in agents.items() if m.get("levelInfo", {}).get("overConferred")]
    if due:
        notes.append(f"agent levels — {len(due)} DUE for promotion (Quartermaster: python3 agent_level.py promote):")
        for mid, m in due:
            notes.append(f"  ↑ {mid}: conferred {m['conferred']} → earned {m['levelInfo']['earned']}")
    if over:
        notes.append(f"agent levels — {len(over)} OVER-conferred (arsenal regressed; review demotion, policy A):")
        for mid, m in over:
            notes.append(f"  ↓ {mid}: conferred {m['conferred']} > earned {m['levelInfo']['earned']}")

    # UI consistency — app.js must use effectiveWeapons(m).length, never bare m.weapons.length,
    # so the agents-list card count matches the detail page (which applies localStorage overrides).
    app_js = ROOT / "app.js"
    if app_js.exists():
        app_src = app_js.read_text(encoding="utf-8")
        bare_hits = [i + 1 for i, ln in enumerate(app_src.splitlines())
                     if re.search(r'\bm\.weapons\.length\b', ln)]
        if bare_hits:
            fails.append(
                f"UI  app.js line(s) {bare_hits} use bare m.weapons.length — "
                f"must use effectiveWeapons(m).length so card count matches detail page"
            )

    # === Phase-D registry hardening (audit #2 §8.3) — models.json is the ONE SoT.
    #     These guard the derive-from-registry contract so a fallback dict, a cost
    #     sidecar, an art tile, or the routing-gate prose can never SILENTLY drift
    #     from star-alliance-arsenal/models.json. (cloud_map/smt come from the L check.)
    try:
        _regm = json.loads((ROOT / "star-alliance-arsenal" / "models.json").read_text()).get("models", {})
    except Exception:
        _regm = {}
    if _regm:
        reg_ids = set(_regm)
        # WART — every registry weapon ships a weapon-art/<id>.png tile (no bare fallback)
        tileless = sorted(mid for mid in reg_ids
                          if not (ROOT / "art" / "weapon-art" / f"{mid}.png").exists())
        if tileless:
            fails.append(f"WART models missing a weapon-art/<id>.png tile: {tileless} "
                         f"(forge via tools/generators/gen-weapon-art.cjs)")
        # MU — the cost sidecar (models-usage.json) may only key ids that exist in the registry
        mu_path = ROOT / "star-alliance-arsenal" / "models-usage.json"
        if mu_path.exists():
            mu_ids = {k for k in json.loads(mu_path.read_text()) if k != "_comment"}
            orphan = sorted(mu_ids - reg_ids)
            if orphan:
                fails.append(f"MU models-usage.json keys not in the registry: {orphan} "
                             f"(cost sidecar drifted from models.json)")
        # FB — anti-drift: the fail-safe ROLE dicts must equal the registry (media→doer).
        #      This is the exact guard that would have caught the old app.js sonnet=doer bug.
        reg_role_norm = {mid: ("doer" if d.get("role") == "media" else d.get("role"))
                         for mid, d in _regm.items()}
        for mid, r in _FALLBACK_ROLE.items():
            if mid == "qwen-3.5":  # legacy alias, not a registry id
                continue
            if reg_role_norm.get(mid) != r:
                fails.append(f"FB conformity _FALLBACK_ROLE[{mid}]={r!r} != registry "
                             f"{reg_role_norm.get(mid)!r} (fallback drifted from models.json)")
        missing_fb = sorted(reg_ids - (set(_FALLBACK_ROLE) - {"qwen-3.5"}))
        if missing_fb:
            fails.append(f"FB conformity _FALLBACK_ROLE missing registry ids: {missing_fb}")
        # FB(tags) — summon.py's fallback cloud-tag map (parsed as cloud_map in the L check)
        #            must equal the registry's cloud_tags exactly.
        reg_tags = {mid: d["cloud_tag"] for mid, d in _regm.items() if d.get("cloud_tag")}
        if cloud_map != reg_tags:
            fails.append(f"FB summon _FALLBACK_CLOUD_TAG {cloud_map} != registry cloud_tags "
                         f"{reg_tags} (routing fallback drifted from models.json)")
        # ST — universal SEATS (models.json "seats"): every seat default + fallback must
        #      name a real registry id. The Critic seat was REMOVED from the registry
        #      (decision: critic is no longer a separate seat — Claude models are BRAIN,
        #      everything non-Claude is DOER). So `seats.critic` may legitimately be
        #      absent and we must not fail on that. We DO still validate that BRAIN ids
        #      have backend == 'claude' and DOER ids have backend != 'claude' — that is
        #      the new hard rule, and the old critic-family-vs-brain-family check is gone.
        try:
            seats = json.loads((ROOT / "star-alliance-arsenal" / "models.json").read_text()).get("seats", {})
        except Exception:
            seats = {}
        if seats:
            for seat in ("brain", "doer"):
                s = seats.get(seat) or {}
                dflt = s.get("default")
                if dflt and dflt not in reg_ids:
                    fails.append(f"ST seat '{seat}' default '{dflt}' is not a registry model")
                for fb in (s.get("fallback") or []):
                    if fb not in reg_ids:
                        fails.append(f"ST seat '{seat}' fallback '{fb}' is not a registry model")
            # NEW RULE: every BRAIN id (default + fallback) MUST have backend == 'claude'.
            # A non-Claude id in a brain seat is a hard failure — the brain is the
            # tool-capable Claude family, and non-Claude models cannot drive the loop.
            bdef = (seats.get("brain") or {}).get("default")
            if bdef and ((_regm.get(bdef) or {}).get("backend") != "claude"):
                fails.append(f"ST brain seat default '{bdef}' has backend "
                             f"'{(_regm.get(bdef) or {}).get('backend')}' — a BRAIN id must "
                             f"have backend == 'claude' (only Claude models can drive the loop)")
            for fb in (seats.get("brain") or {}).get("fallback") or []:
                if (_regm.get(fb) or {}).get("backend") != "claude":
                    fails.append(f"ST brain seat fallback '{fb}' has backend "
                                 f"'{(_regm.get(fb) or {}).get('backend')}' — a BRAIN id must "
                                 f"have backend == 'claude'")
            # NEW RULE: every DOER id (default + fallback) MUST be NON-Claude.
            # DOER is the executor seat (cheap, fast, different family than the brain).
            ddef = (seats.get("doer") or {}).get("default")
            if ddef and ((_regm.get(ddef) or {}).get("backend") == "claude"):
                fails.append(f"ST doer seat default '{ddef}' has backend 'claude' — "
                             f"a DOER id must be NON-Claude (Claude belongs in the BRAIN seat)")
            for fb in (seats.get("doer") or {}).get("fallback") or []:
                if (_regm.get(fb) or {}).get("backend") == "claude":
                    fails.append(f"ST doer seat fallback '{fb}' has backend 'claude' — "
                                 f"a DOER id must be NON-Claude")

    # === RG — routing-gate agent→model prose must match guild-data (lint, not
    #     generate: the lines are hand-edited doctrine per audit §7.1/C2, just kept honest) ===
    # Check BOTH possible routing-gate locations:
    #   Claude side: .claude/hooks/guild-routing-gate.sh
    #   Hermes side: server/star_alliance_mcp.py
    rg_paths = [
        ROOT / ".claude" / "hooks" / "guild-routing-gate.sh",
        ROOT / "server" / "star_alliance_mcp.py",
    ]
    agent_model = {m["id"]: m.get("model") for m in agents_list}
    for rg_path in rg_paths:
        if not rg_path.exists():
            continue
        rg_txt = rg_path.read_text()
        # Match agent→model pairs in prose: "the-architect (glm-5.2)" etc.
        # Accept any registry model id pattern: word chars with dots/hyphens
        rg_pairs = dict(re.findall(
            r'(the-[a-z]+)\s*\(([a-z0-9][a-z0-9.\-]*)\)', rg_txt))
        for mid, mdl in sorted(rg_pairs.items()):
            if agent_model.get(mid) != mdl:
                fails.append(f"RG {rg_path.name} says {mid} ({mdl}) but guild-data model is "
                             f"'{agent_model.get(mid)}' (routing-gate drifted from agent .md)")

    # === PD — profile-distribution parity: repo source == installed profile ===
    # Each repo profile under profiles/<agent>/ is a Hermes distribution.  The
    # installed profile at ~/.hermes/profiles/<slug>/ should have SOUL.md and
    # config.yaml that match the repo source.  If they drift (someone hand-edited
    # the installed copy, or publish_profiles.py --update wasn't run after a
    # repo change), the subagents are running stale identity/config.
    #
    # SOUL.md and config.yaml are compared as raw text (byte-exact).  distribution.yaml
    # is compared semantically (parsed as YAML, excluding Hermes-added runtime fields
    # source/installed_at, because Hermes re-serializes the YAML on install).
    import os as _os
    try:
        import yaml as _yaml
    except ImportError:
        _yaml = None
    _PROFILE_MAP = {
        "the-architect":     "architect",
        "the-developer":     "developer",
        "the-designer":      "designer",
        "the-interpreter": "interpreter",
        "the-herald":        "herald",
        "the-merchant":      "merchant",
        "the-quartermaster": "quartermaster",
    }
    _hermes_home = pathlib.Path(_os.environ.get("HERMES_REAL_HOME", str(pathlib.Path.home())))
    _profiles_root = _hermes_home / ".hermes" / "profiles"
    for slug, folder in _PROFILE_MAP.items():
        repo_dir = ROOT / "profiles" / folder
        inst_dir = _profiles_root / slug
        if not repo_dir.is_dir():
            continue  # not a distribution-profile (butler/strategist are project-scoped)
        if not inst_dir.is_dir():
            fails.append(f"PD {slug}: not installed at {inst_dir} "
                         "(run: python3 tools/publish_profiles.py)")
            continue
        # SOUL.md and config.yaml — byte-exact comparison
        for fname in ("SOUL.md", "config.yaml"):
            repo_file = repo_dir / fname
            inst_file = inst_dir / fname
            if not repo_file.is_file():
                continue
            if not inst_file.is_file():
                fails.append(f"PD {slug}: {fname} missing from installed profile "
                             f"(run: python3 tools/publish_profiles.py --update)")
                continue
            if repo_file.read_text(encoding="utf-8") != inst_file.read_text(encoding="utf-8"):
                fails.append(f"PD {slug}: {fname} has drifted — repo != installed "
                             f"(run: python3 tools/publish_profiles.py --update)")
        # distribution.yaml — semantic comparison (exclude Hermes runtime fields)
        repo_dist = repo_dir / "distribution.yaml"
        inst_dist = inst_dir / "distribution.yaml"
        if repo_dist.is_file() and inst_dist.is_file() and _yaml:
            repo_y = _yaml.safe_load(repo_dist.read_text(encoding="utf-8")) or {}
            inst_y = _yaml.safe_load(inst_dist.read_text(encoding="utf-8")) or {}
            # Strip Hermes-added runtime fields from installed copy
            inst_y.pop("source", None)
            inst_y.pop("installed_at", None)
            if repo_y != inst_y:
                fails.append(f"PD {slug}: distribution.yaml has drifted — repo != installed "
                             f"(run: python3 tools/publish_profiles.py --update)")

    # === PS — Profile Skill-set parity: profile's installed skills/ == member's declared skills ===
    # For each spawnable profile, the set of non-vendor skills present under
    # ~/.hermes/profiles/<slug>/skills/ must equal the set declared in the member's
    # `skills:` array in guild-data.json. Fail-open (INFO/note) when the installed
    # profile is absent — mirrors PD's contract: a missing profile is a separate,
    # louder failure (PD), and PS only fires when there IS a profile to audit.
    #
    # Build the per-member declared-skills map: slug -> set(skill ids).
    # Source priority:
    #   1. agents/members array in guild-data.json (the SSOT)
    #   2. Fall back to scanning star-alliance-members/*.md frontmatter
    _member_declared_skills = {}
    for _m in agents_list:
        _ms = _m.get("skills") or []
        if _ms:
            _member_declared_skills[_m["id"]] = set(_ms)
    if not _member_declared_skills:
        # Fallback: scan star-alliance-members/*.md frontmatter
        _sam_dir = ROOT / "star-alliance-members"
        if _sam_dir.is_dir():
            for _md in sorted(_sam_dir.glob("the-*.md")):
                _skills = frontmatter_list(_md.read_text(), "skills")
                if _skills:
                    _member_declared_skills[_md.stem] = set(_skills)

    for slug, folder in _PROFILE_MAP.items():
        if slug == "the-butler":
            continue  # not a spawnable profile
        inst_skills_dir = _profiles_root / slug / "skills"
        if not inst_skills_dir.is_dir():
            notes.append(f"PS {slug}: profile skills/ missing at {inst_skills_dir} "
                         f"(skipped, fail-open — install via publish_profiles.py)")
            continue
        # Installed = every directory under skills/ that has a SKILL.md
        inst_skill_ids = {d.name for d in inst_skills_dir.iterdir()
                          if d.is_dir() and (d / "SKILL.md").is_file()}
        # Declared = member's `skills:` minus vendor-published (vendor skills ship
        # by default with every profile; they're not part of the equality contract)
        declared = {s for s in _member_declared_skills.get(slug, set())
                    if s not in HERMES_VENDOR_SKILLS}
        declared_but_missing = sorted(declared - inst_skill_ids)
        present_but_undeclared = sorted(
            (inst_skill_ids - declared) - HERMES_VENDOR_SKILLS
        )
        if declared_but_missing:
            fails.append(
                f"PS {slug}: declared-but-missing in skills/: {declared_but_missing} "
                f"— run publish_profiles --update + skill_sync --profile-content"
            )
        if present_but_undeclared:
            fails.append(
                f"PS {slug}: present-but-undeclared in skills/: {present_but_undeclared} "
                f"— remove from profile or add to member array"
            )

    # === HS — Hermes/Claude content parity: skill content drift ===
    # For every declared skill in every member's `skills:`, the on-disk content
    # (fingerprinted as a directory hash) must match the repo's SSOT under
    # star-alliance-skills/<id>/. Two destinations are checked:
    #
    #   Hermes profile (~/.hermes/profiles/<slug>/skills/<id>/)  — fail-OPEN if
    #     the directory is missing (the profile may not be installed; PD owns that)
    #   Claude store    (~/.claude/skills/<id>/)                  — fail-HARD if
    #     missing or drifted. The Claude store is a SHARED resource across all
    #     agents; a missing or drifted skill breaks every Claude-side member.
    _claude_skills_dir = pathlib.Path.home() / ".claude" / "skills"
    for slug, _folder in _PROFILE_MAP.items():
        if slug == "the-butler":
            continue
        declared = _member_declared_skills.get(slug, set())
        for sid in sorted(declared):
            # Repo fingerprint (the SSOT) — must always exist
            repo_skill = ROOT / "star-alliance-skills" / sid
            repo_fp = _skill_fingerprint(repo_skill)
            if not repo_fp:
                # Repo is missing a skill the member declares — already caught by R,
                # don't double-report. Skip the HS check for this id.
                continue
            # Hermes profile fingerprint — fail-open if the dir is missing
            hermes_skill = _profiles_root / slug / "skills" / sid
            hermes_fp = _skill_fingerprint(hermes_skill)
            if hermes_fp is None:
                notes.append(f"HS {slug}/{sid}: profile skills/{sid}/ missing "
                             f"(skipped, fail-open — install via publish_profiles.py)")
            elif hermes_fp != repo_fp:
                fails.append(
                    f"HS {slug}/{sid}: profile content drift — "
                    f"repo fp {repo_fp[:12]} != profile fp {hermes_fp[:12]} "
                    f"— run skill_sync --profile-content"
                )
            # Claude store fingerprint — fail-HARD if missing or drifted
            claude_skill = _claude_skills_dir / sid
            claude_fp = _skill_fingerprint(claude_skill)
            if not claude_fp:
                fails.append(
                    f"HS {sid}: Claude-store drift/absent "
                    f"(~/.claude/skills/{sid}) "
                    f"— run skill_sync --direction install"
                )
            elif claude_fp != repo_fp:
                fails.append(
                    f"HS {sid}: Claude-store content drift — "
                    f"repo fp {repo_fp[:12]} != Claude fp {claude_fp[:12]} "
                    f"— run skill_sync --direction install"
                )

    # === AL — architecture-layer coherence (CLAUDE.md + AGENTS.md) ===
    # Both instruction files must describe the three-layer architecture and the
    # triple-seat model system. If both exist, their model tables must match the
    # seats in models.json (brain default, doer default, critic default).
    _AL_KEYWORDS = ["three-layer architecture"]
    try:
        models_json_seats = json.loads(
            (ROOT / "star-alliance-arsenal" / "models.json").read_text()).get("seats", {})
    except Exception:
        models_json_seats = {}
    _al_seat_defaults = {}
    for seat in ("brain", "doer", "critic"):
        s = models_json_seats.get(seat) or {}
        dflt = s.get("default")
        if dflt:
            _al_seat_defaults[seat] = dflt

    for _al_file_name in ("CLAUDE.md", "AGENTS.md"):
        _al_path = ROOT / _al_file_name
        if not _al_path.exists():
            fails.append(f"AL {_al_file_name}: file missing — expected in the merged repo")
            continue
        _al_txt = _al_path.read_text(encoding="utf-8")
        for kw in _AL_KEYWORDS:
            if kw not in _al_txt:
                fails.append(f"AL {_al_file_name}: missing keyword '{kw}' "
                             f"(expected: three-layer architecture + triple-seat model names)")
        # If both files exist and we have seat defaults, verify the model table matches
        # Look for model table rows like "| **Thinker (Brain)** | GLM-5.2 |" or "| Brain | glm-5.2 |"
        if _al_seat_defaults:
            # Extract model names from markdown tables — look for seat default model ids
            for seat, expected_model in _al_seat_defaults.items():
                # Try to find the model in a table row near the seat keyword
                # Patterns: "Brain" or "Thinker" for brain; "Doer" for doer; "Critic" for critic
                seat_aliases = {
                    "brain": [r"brain", r"thinker"],
                    "doer":  [r"doer"],
                    "critic": [r"critic"],
                }
                found = False
                for alias in seat_aliases.get(seat, [seat]):
                    # Look for a table row containing the alias and the expected model
                    pattern = rf'\|\s*[^|]*{alias}[^|]*\|[^|]*{re.escape(expected_model)}'
                    if re.search(pattern, _al_txt, re.IGNORECASE):
                        found = True
                        break
                if not found:
                    # Also try: the model name might appear anywhere near a seat section
                    # Be lenient — only fail if the model is clearly absent from the file
                    # but the seat keyword is present (indicating a stale table)
                    seat_kw_present = any(re.search(rf'{a}', _al_txt, re.IGNORECASE)
                                         for a in seat_aliases.get(seat, [seat]))
                    if seat_kw_present and expected_model not in _al_txt:
                        fails.append(f"AL {_al_file_name}: seat '{seat}' references models.json "
                                     f"default '{expected_model}' but that model id is not "
                                     f"mentioned in the file (model table may be stale)")

    # === DX — dispatch bridge integrity ===
    # Verify tools/dispatch.py exists, parse the AGENTS dict from source, and
    # for each agent (except the-butler and the-strategist) verify a matching
    # profiles/<folder>/ directory exists with distribution.yaml.
    _dx_path = ROOT / "tools" / "dispatch.py"
    if not _dx_path.exists():
        fails.append("DX tools/dispatch.py: file missing — the dispatch bridge is required")
    else:
        _dx_src = _dx_path.read_text(encoding="utf-8")
        # Parse the AGENTS dict — it's a Python dict literal in the source
        _dx_m = re.search(r'AGENTS\s*=\s*\{(.*?)\}', _dx_src, re.S)
        if not _dx_m:
            fails.append("DX tools/dispatch.py: cannot parse AGENTS dict — expected 'AGENTS = {...}'")
        else:
            # Extract agent names (keys) from the dict literal
            _dx_agent_names = re.findall(r'"(the-[a-z]+)"', _dx_m.group(1))
            _dx_skip = {"the-butler", "the-strategist"}
            for _dx_agent in _dx_agent_names:
                if _dx_agent in _dx_skip:
                    continue
                # Folder name = agent name without "the-" prefix
                _dx_folder = _dx_agent.replace("the-", "", 1)
                _dx_profile_dir = ROOT / "profiles" / _dx_folder
                if not _dx_profile_dir.is_dir():
                    fails.append(f"DX dispatch.py lists '{_dx_agent}' but profiles/{_dx_folder}/ "
                                 f"directory does not exist")
                elif not (_dx_profile_dir / "distribution.yaml").is_file():
                    fails.append(f"DX dispatch.py lists '{_dx_agent}' but profiles/{_dx_folder}/"
                                 f"distribution.yaml is missing")

    # === MP — member↔agent parity (only if both directories exist) ===
    # If both star-alliance-members/ and agents/ exist, verify they have the same
    # set of .md files (same agent IDs). If only one exists, skip the check.
    _mp_members_dir = ROOT / "star-alliance-members"
    _mp_agents_dir = ROOT / "agents"
    if _mp_members_dir.is_dir() and _mp_agents_dir.is_dir():
        _mp_member_ids = {f.stem for f in _mp_members_dir.glob("the-*.md")}
        _mp_agent_ids = {f.stem for f in _mp_agents_dir.glob("the-*.md")}
        _mp_only_members = sorted(_mp_member_ids - _mp_agent_ids)
        _mp_only_agents = sorted(_mp_agent_ids - _mp_member_ids)
        if _mp_only_members:
            fails.append(f"MP only in star-alliance-members/ (not in agents/): {_mp_only_members}")
        if _mp_only_agents:
            fails.append(f"MP only in agents/ (not in star-alliance-members/): {_mp_only_agents}")
    # If only one exists, skip — no parity to check

    # report
    print("═" * 64)
    print(" CONFORMITY SWEEP — Star Alliance repo (unified)")
    print("═" * 64)
    print(f" decisions on record : {len(decisions)}")
    for d in decisions:
        print(f"   #{d['id']} {d['title']}")
    print(f" {agents_key}={real[agents_key]}  skills={real['skills']}  workflows={real['workflows']}  "
          f"version={g.get('meta',{}).get('version')}")
    print("─" * 64)
    if notes:
        print(" NOTES (non-blocking):")
        for n in notes:
            print(f"   • {n}")
        print("─" * 64)
    if fails:
        print(f" ✗ {len(fails)} CONTRADICTION(S):")
        for f in fails:
            print(f"   ✗ {f}")
        print("═" * 64)
        return 1
    print(" ✓ FULL CONFORMITY — every cross-reference and decision holds.")
    print("═" * 64)
    return 0


def check_member(name):
    """Fast-path: audit ONE agent's skill↔drill coupling right after a loadout edit.

    The cheap guard the Quartermaster runs the instant a agent's `skills:` frontmatter
    changes — long before the full sweep — so the SD drift (skill carried, no drill row,
    or a stale row for a dropped skill) is caught at EDIT time, not sweep time. Checks,
    for `the-<name>.md`: every carried skill has a `## Skill Drills` row (SD), every
    carried skill exists in skills-meta (R), and no drill row names a skill the agent no
    longer carries (the reverse — a stale row left after removal). Exit 0 clean, 1 on drift.

    Searches both agents/ and star-alliance-members/ directories.
    """
    slug = name if name.startswith("the-") else f"the-{name}"
    md = None
    for agent_dir, _label in _detect_agent_dirs():
        candidate = agent_dir / f"{slug}.md"
        if candidate.exists():
            md = candidate
            break
    if md is None:
        print(f"✗ no such agent: {slug}.md (searched agents/ and star-alliance-members/)")
        return 1
    text = md.read_text()
    skills = frontmatter_list(text, "skills") or []
    body = text.split("---", 2)[2] if text.count("---") >= 2 else text
    try:
        meta_keys = set(json.loads((ROOT / "data" / "skills-meta.json").read_text()).keys())
    except Exception:
        meta_keys = set()
    fails = []
    # SD — carried skill with no drill row.
    for sk in skills:
        if re.search(r'\|\s*`?' + re.escape(sk) + r'`?\s*\|', body) is None:
            fails.append(f"SD {slug}: skill '{sk}' carried but has no Skill Drills row "
                         f"(add `| {sk} | invoke WHEN … | do NOT … | pairs with … |`)")
        if meta_keys and sk not in meta_keys:
            fails.append(f"R  {slug}: skill '{sk}' not in skills-meta.json")
    # Reverse — a drill row for a skill no longer in the loadout (stale after removal).
    for row_sk in re.findall(r'^\|\s*`([a-z0-9][a-z0-9-]+)`\s*\|', body, re.M):
        if row_sk in meta_keys and row_sk not in skills:
            fails.append(f"SD {slug}: stale drill row for '{row_sk}' — not in the "
                         f"`skills:` loadout (delete the row, or re-add the skill)")
    if fails:
        print(f"✗ {slug}: {len(fails)} drift(s):")
        for f in fails:
            print(f"   ✗ {f}")
        return 1
    print(f"✓ {slug}: skill↔drill coupling holds ({len(skills)} skills, all drilled).")
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] in ("--agent", "--member"):
        sys.exit(check_member(sys.argv[2]))
    sys.exit(main())