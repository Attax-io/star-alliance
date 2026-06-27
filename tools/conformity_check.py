#!/usr/bin/env python3
"""Conformity check — audit the whole Star Alliance repo for internal conformity
and conformity with every decision on record (guild-log type:decision).

Read-only. Prints a PASS/FAIL map and exits 1 on any contradiction. The Quartermaster
runs this as the spine of the `compliance-audit` star-map workflow.

Checks (each maps to a source-of-truth invariant or a logged decision):
  P  parity        guild-data.js  ==  guild-data.json
  D23 report-gate  every workflow ENDS with a Butler 'report' gate   (decision #23)
  C  qm-close      every workflow's last member step before report is the-quartermaster
  A  arsenal-order per member: doers → thinkers/duals → sonnet last   (session decision)
  BR brain       each member's session model (model:) is a carried, thinking weapon (brain = personality)
  PD prime-doer  the prime doer (minimax-m3) leads the arsenal (the member's hands)
  R  refs          workflow actors ∈ members∪{you}; gates valid; member skills exist
  S  source==gen   member .md frontmatter weapons order == generated guild-data
  W  weaponsDesc   members-meta weaponsDesc set == member weapons set
  SD skill-drills  every member-carried skill has a `## Skill Drills` table row
  N  counts        guild-data meta.counts == real lengths
  WART weapon-art  every registry weapon has a weapon-art/<id>.png tile
  MU usage-sidecar models-usage.json keys ⊆ registry ids
  FB fallback-sync fail-safe ROLE/CLOUD_TAG dicts == models.json (anti-drift)
  RG routing-gate  guild-routing-gate.sh member→model prose == guild-data
"""
import json, re, sys, pathlib

ROOT = next((p for p in pathlib.Path(__file__).resolve().parents
             if (p / "VERSIONS.md").exists() and (p / ".git").exists()),
            pathlib.Path(__file__).resolve().parent)

# role per model id — DERIVED from the canonical registry
# (star-alliance-arsenal/models.json). The literal below is a FAIL-SAFE only.
# Media weapons are normalized to "doer" for arsenal ordering; sonnet "both" forced last.
_FALLBACK_ROLE = {
    "opus": "thinker", "deepseek-v4-pro": "thinker",
    "glm-5.2": "thinker", "kimi-k2.7": "thinker", "nemotron-3-ultra": "thinker",
    "qwen3.5": "thinker", "qwen-3.5": "thinker", "gemma4": "thinker",
    "sonnet": "both",
    "haiku": "doer", "minimax-m3": "doer",
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

CLAUDE_NATIVE = {"opus", "sonnet", "haiku"}
MEDIA_WEAPONS = {"image-01", "minimax-video", "minimax-speech", "minimax-music"}


def expected_order(weapons):
    """Canonical arsenal order:
       prime doer (minimax-m3, cheapest) first → other doers → prime thinker (opus,
       best) first → other thinkers → sonnet last (universal Claude-tool fallback).
       Relative order within the 'other doers' / 'other thinkers' groups is preserved."""
    doers = [w for w in weapons if ROLE.get(w) == "doer"]
    if "minimax-m3" in doers:  # prime doer always leads
        doers = ["minimax-m3"] + [w for w in doers if w != "minimax-m3"]
    thinkers = [w for w in weapons if ROLE.get(w) in ("thinker", "both") and w != "sonnet"]
    if "opus" in thinkers:     # prime thinker always leads the thinker block
        thinkers = ["opus"] + [w for w in thinkers if w != "opus"]
    tail = ["sonnet"] if "sonnet" in weapons else []
    return doers + thinkers + tail


def frontmatter_list(text, key):
    m = re.search(rf'^{key}:\s*\[([^\]]*)\]', text, re.M)
    if not m:
        return None
    return [x.strip() for x in m.group(1).split(",") if x.strip()]


def _parse_weapons_table(text):
    """Return [(model, desc), …] from the `## Your Weapons` table, or None if absent.
    Columns are: | Priority | Weapon | When to Draw It |."""
    lines = text.split("\n")
    try:
        start = next(i for i, l in enumerate(lines) if l.strip() == "## Your Weapons")
    except StopIteration:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    rows = []
    for l in lines[start + 1:end]:
        if not l.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cells) != 3:
            continue
        if cells[0] == "Priority" or set(cells[1]) <= set("-: "):
            continue  # header row / separator
        rows.append((cells[1], cells[2]))
    return rows or None


def main():
    fails = []
    notes = []

    g = json.loads((ROOT / "guild-data.json").read_text())
    members = {m["id"]: m for m in g["members"]}
    skills_meta = json.loads((ROOT / "data/skills-meta.json").read_text())
    skill_ids = set(skills_meta.keys())
    meta = json.loads((ROOT / "data/members-meta.json").read_text())["members"]
    log = json.loads((ROOT / "data/guild-log.json").read_text())["entries"]
    decisions = [e for e in log if e.get("type") == "decision"]

    # P — guild-data.js == guild-data.json
    js = (ROOT / "guild-data.js").read_text()
    mo = re.search(r'\{.*\}', js, re.S)
    if not mo or json.loads(mo.group(0)) != g:
        fails.append("P  parity: guild-data.js does NOT match guild-data.json (rerun build.py)")

    # workflow-level checks
    for wf in g["workflows"]:
        wid = wf["id"]
        steps = wf["steps"]
        # D23 — ends with report gate
        last = steps[-1] if steps else {}
        if last.get("kind") != "gate" or last.get("gate") != "report":
            fails.append(f"D23 {wid}: does not END with a 'report' gate (decision #23)")
        # R — actors + gates resolve
        for s in steps:
            if s.get("kind") == "member":
                a = s.get("actor")
                if a != "you" and a not in members:
                    fails.append(f"R  {wid}: unknown actor '{a}'")
                # WPN — structured weapon fields (optional) stay valid: thinker is a
                # thinker-role weapon in the actor's loadout; doers are doer-role and in
                # loadout; ultra only if the actor carries ultra-brainstorming.
                if a in members:
                    am = members[a]
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
        # C — last member step before the final report gate is the-quartermaster
        wf_class = wf.get("class", "mutating")
        if wf_class not in ("mutating", "read-only"):
            fails.append(f"CLS {wid}: unknown class '{wf_class}' (expected mutating | read-only)")
        member_steps = [s for s in steps if s.get("kind") == "member"]
        # C — the Quartermaster conformance-close is required only for MUTATING workflows
        # (those that change guild artifacts). Read-only/advisory workflows end at the
        # Butler's report with the worker as the last member step — no ceremonial close.
        if wf_class != "read-only" and member_steps and member_steps[-1].get("actor") != "the-quartermaster":
            fails.append(f"C  {wid}: mutating workflow closes with '{member_steps[-1].get('actor')}', "
                         f"not the-quartermaster (conformance-close convention)")
        # read-only workflows must NOT end on a Quartermaster close — the worker is the
        # last member step; a trailing Quartermaster is the ceremonial no-op we removed.
        if wf_class == "read-only" and member_steps and member_steps[-1].get("actor") == "the-quartermaster":
            fails.append(f"C  {wid}: read-only workflow closes with a Quartermaster step "
                         f"(a no-op conformance close — remove it; the Butler report is the deliverable)")

    # per-member checks. Phase 2 (4-seat arsenal): per-member loadouts are GONE —
    # the arsenal is universal (models.json "seats"), so the old per-loadout checks
    # (A order · PD prime-doer · W weaponsDesc · S frontmatter · WT table) are retired
    # and replaced by ST (seats valid + critic≠brain family) above. Only the BRAIN is
    # per-member: it's the session model the member runs as.
    for mid, m in members.items():
        # BR — the brain (session model) must be a registry weapon that can think.
        # A NULL/missing brain is itself a fail: build.py emits top-level "model": null
        # while seats.brain silently falls back to the seat default — an inconsistent
        # member. Every member must declare its own session model (model:) in frontmatter.
        brain = m.get("model")
        if not brain:
            fails.append(f"BR {mid}: no session model (model:) declared — every member "
                         f"must name its own brain (falling back to the seat default is inconsistent)")
        elif brain not in ROLE:
            fails.append(f"BR {mid}: brain '{brain}' has no role mapping in the registry")
        elif ROLE.get(brain) not in ("thinker", "both"):
            fails.append(f"BR {mid}: brain '{brain}' has role '{ROLE.get(brain)}' — "
                         f"a brain must be able to think (thinker|both)")
        # R — member skills exist in skills-meta
        for sk in m.get("skills", []):
            if sk not in skill_ids:
                fails.append(f"R  {mid}: skill '{sk}' not in skills-meta")

    # U — weapon-utility is foundational: every member must carry it (session decision)
    if "weapon-utility" in skill_ids:
        for mid, m in members.items():
            if "weapon-utility" not in m.get("skills", []):
                fails.append(f"U  {mid}: missing foundational skill 'weapon-utility' (every member must carry it)")

    # SD — Skill Drills coverage: every skill a member carries must be DRILLED in that
    # member's `## Skill Drills` table — i.e. appear as a table ROW (matched by the
    # `| <skill> |` cell). The frontmatter `skills:` list declares what the member wields;
    # the drills table declares WHEN/when-NOT to wield each. A carried-but-undrilled skill
    # is a coverage hole the member would have no firing doctrine for → HARD FAIL.
    for md in sorted((ROOT / "star-alliance-members").glob("the-*.md")):
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
    bp = (ROOT / "build.py").read_text()
    le = (ROOT / "tools" / "log_event.py").read_text()
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
                     if not (ROOT / "skill-art" / f"{s}.png").exists())
    if artless:
        fails.append(f"ART skills missing a skill-art/<id>.png tile: {artless} "
                     f"(forge via tools/generators/gen-skill-art.cjs + build.py)")

    # VER — every skill has a VERSIONS.md registry row whose version matches its SKILL.md
    versions_txt = (ROOT / "VERSIONS.md").read_text()
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

    # G — gen-workflow-art.cjs has a prompt entry for every workflow (art can be forged)
    gen = (ROOT / "tools/generators/gen-workflow-art.cjs")
    if gen.exists():
        gen_ids = set(re.findall(r'id:\s*"([^"]+)"', gen.read_text()))
        uncovered = {w["id"] for w in g["workflows"]} - gen_ids
        if uncovered:
            fails.append(f"G  tools/generators/gen-workflow-art.cjs missing art prompt for {sorted(uncovered)}")

    # N — counts
    counts = g.get("meta", {}).get("counts", {})
    real = {"members": len(g["members"]), "skills": len(g["skills"]), "workflows": len(g["workflows"])}
    for k, v in real.items():
        if counts.get(k) != v:
            fails.append(f"N  counts.{k}={counts.get(k)} != real {v}")

    # === DC — doc count claims match reality (README + domains) — audit #1 ===
    actual_skills = len(skill_dirs)
    readme_txt = (ROOT / "README.md").read_text()
    for mobj in re.finditer(r'\((\d+)\s+skills', readme_txt):
        if int(mobj.group(1)) != actual_skills:
            fails.append(f"DC README claims {mobj.group(1)} skills, actual {actual_skills}")
    doms = json.loads((ROOT / "data/domains.json").read_text())["domains"]
    home = next((d for d in doms if d["id"] == "star-alliance"), None)
    if home:
        if len(home["skills"]) != actual_skills:
            fails.append(f"DC domains star-alliance lists {len(home['skills'])} skills, actual {actual_skills}")
        if len(home["members"]) != real["members"]:
            fails.append(f"DC domains star-alliance lists {len(home['members'])} members, actual {real['members']}")
        note = home.get("notes", "")
        for mm in re.finditer(r'(\d+)\s+guild members', note):
            if int(mm.group(1)) != real["members"]:
                fails.append(f"DC domains notes: '{mm.group(1)} guild members' != actual {real['members']}")
        for ss in re.finditer(r'(\d+)\s+skills', note):
            if int(ss.group(1)) != actual_skills:
                fails.append(f"DC domains notes: '{ss.group(1)} skills' != actual {actual_skills}")

    # === SEC — member-page skill split stays self-maintaining (skills-carried widget) ===
    # The member dossier renders carried skills as General + one widget per sector domain
    # that lists the skill. Grouping is by SECTOR MEMBERSHIP (a non-home domain's skills[]),
    # not the `global` install flag. A skill in no non-home sector renders under General by
    # design, so there is no "untagged" failure mode — only a dead reference can break the
    # auto-grouping: a domain lists a skill id that no longer exists → HARD FAIL (the sector
    # widget would render a ghost line).
    for d in doms:
        for sid in d.get("skills", []):
            if sid not in data_ids:
                fails.append(f"SEC domain '{d['id']}' lists unknown skill '{sid}' "
                             f"(dead ref — member-page sector widget would render a ghost)")

    # === V — every skill SKILL.md carries a parseable version — audit #1 ===
    for name in sorted(skill_dirs):
        txt = (ROOT / "star-alliance-skills" / name / "SKILL.md").read_text()
        if not re.search(r'(?m)^[ \t]*version:\s*\S+', txt):
            fails.append(f"V  skill '{name}' has no version in SKILL.md (metadata.version required)")

    # === L — weapon routability (hard) + liveness (NOTE) — audit #1/#2 ===
    smt = (ROOT / "star-alliance-arsenal" / "summon.py").read_text()
    cloud_map = dict(re.findall(r"'([^']+)':\s*'([^']+:cloud)'", smt))
    routable = set(CLAUDE_NATIVE) | set(cloud_map) | MEDIA_WEAPONS | {"minimax-m3"}
    all_weapons = {w for m in members.values() for w in (x["model"] for x in m["weapons"])}
    for w in sorted(all_weapons - routable):
        fails.append(f"L  weapon '{w}' in a loadout is not routable by summon.py or Claude-native")
    # liveness — best-effort, NOTE only (never a hard fail; it is environment-dependent)
    import os as _os
    import subprocess as _sp
    try:
        _ol = _sp.run(["ollama", "list"], capture_output=True, text=True, timeout=10).stdout
        pulled = {ln.split()[0] for ln in _ol.splitlines()[1:] if ln.strip()}
    except Exception:
        pulled = set()
    live = set(CLAUDE_NATIVE)
    for w, tag in cloud_map.items():
        if tag in pulled:
            live.add(w)
    if (pathlib.Path.home() / ".config" / "minimax" / "m3.key").exists() or _os.environ.get("MINIMAX_API_KEY"):
        live |= {"minimax-m3"} | MEDIA_WEAPONS
    dead = sorted(all_weapons - live)
    if dead:
        notes.append(f"weapon liveness — NOT firing on this device: {', '.join(dead)}")
        for w in dead:
            users = sorted(mid for mid, m in members.items() if w in (x["model"] for x in m["weapons"]))
            notes.append(f"  '{w}' declared by {len(users)} member(s): {', '.join(users)}")

    # member leveling — promotion queue + regression review (NOTES, never blocking).
    # Leveling is Quartermaster-gated and human-in-the-loop, so drift belongs in the
    # QM's queue, not the build gate. See docs/STRATEGIST-MEMBER-LEVELING.md §3.
    due = [(mid, m) for mid, m in members.items() if m.get("levelInfo", {}).get("dueForPromotion")]
    over = [(mid, m) for mid, m in members.items() if m.get("levelInfo", {}).get("overConferred")]
    if due:
        notes.append(f"member levels — {len(due)} DUE for promotion (Quartermaster: python3 member_level.py promote):")
        for mid, m in due:
            notes.append(f"  ↑ {mid}: conferred {m['conferred']} → earned {m['levelInfo']['earned']}")
    if over:
        notes.append(f"member levels — {len(over)} OVER-conferred (arsenal regressed; review demotion, policy A):")
        for mid, m in over:
            notes.append(f"  ↓ {mid}: conferred {m['conferred']} > earned {m['levelInfo']['earned']}")

    # UI consistency — app.js must use effectiveWeapons(m).length, never bare m.weapons.length,
    # so the members-list card count matches the detail page (which applies localStorage overrides).
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
                          if not (ROOT / "weapon-art" / f"{mid}.png").exists())
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
        #      name a real registry id, and the Critic must be a DIFFERENT backend family
        #      than the Brain (diverse blind spots is the whole point of an adversary).
        try:
            seats = json.loads((ROOT / "star-alliance-arsenal" / "models.json").read_text()).get("seats", {})
        except Exception:
            seats = {}
        if seats:
            for seat in ("brain", "doer", "critic"):
                s = seats.get(seat) or {}
                dflt = s.get("default")
                if dflt and dflt not in reg_ids:
                    fails.append(f"ST seat '{seat}' default '{dflt}' is not a registry model")
                for fb in (s.get("fallback") or []):
                    if fb not in reg_ids:
                        fails.append(f"ST seat '{seat}' fallback '{fb}' is not a registry model")
            bdef = (seats.get("brain") or {}).get("default")
            cdef = (seats.get("critic") or {}).get("default")
            bfam = (_regm.get(bdef) or {}).get("backend")
            cfam = (_regm.get(cdef) or {}).get("backend")
            if bdef and cdef and bfam and cfam and bfam == cfam:
                fails.append(f"ST critic '{cdef}' shares the brain's backend family '{bfam}' "
                             f"— critic must differ from brain for diverse review")

    # === RG — guild-routing-gate.sh member→model prose must match guild-data (lint, not
    #     generate: the lines are hand-edited doctrine per audit §7.1/C2, just kept honest) ===
    rg_path = ROOT / ".claude" / "hooks" / "guild-routing-gate.sh"
    if rg_path.exists():
        rg_pairs = dict(re.findall(r'(the-[a-z]+)\s*\((opus|sonnet|haiku)\)', rg_path.read_text()))
        member_model = {m["id"]: m.get("model") for m in g["members"]}
        for mid, mdl in sorted(rg_pairs.items()):
            if member_model.get(mid) != mdl:
                fails.append(f"RG guild-routing-gate.sh says {mid} ({mdl}) but guild-data model is "
                             f"'{member_model.get(mid)}' (routing-gate drifted from member .md)")

    # report
    print("═" * 64)
    print(" CONFORMITY SWEEP — Star Alliance repo")
    print("═" * 64)
    print(f" decisions on record : {len(decisions)}")
    for d in decisions:
        print(f"   #{d['id']} {d['title']}")
    print(f" members={real['members']}  skills={real['skills']}  workflows={real['workflows']}  "
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
    """Fast-path: audit ONE member's skill↔drill coupling right after a loadout edit.

    The cheap guard the Quartermaster runs the instant a member's `skills:` frontmatter
    changes — long before the full sweep — so the SD drift (skill carried, no drill row,
    or a stale row for a dropped skill) is caught at EDIT time, not sweep time. Checks,
    for `the-<name>.md`: every carried skill has a `## Skill Drills` row (SD), every
    carried skill exists in skills-meta (R), and no drill row names a skill the member no
    longer carries (the reverse — a stale row left after removal). Exit 0 clean, 1 on drift.
    """
    slug = name if name.startswith("the-") else f"the-{name}"
    md = ROOT / "star-alliance-members" / f"{slug}.md"
    if not md.exists():
        print(f"✗ no such member: {md.name}")
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
    if len(sys.argv) >= 3 and sys.argv[1] == "--member":
        sys.exit(check_member(sys.argv[2]))
    sys.exit(main())
