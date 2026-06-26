#!/usr/bin/env python3
"""Conformity Sweep — audit the whole Star Alliance repo for internal conformity
and conformity with every decision on record (guild-log type:decision).

Read-only. Prints a PASS/FAIL map and exits 1 on any contradiction. The Quartermaster
runs this as the spine of the `conformity-sweep` star-map workflow.

Checks (each maps to a source-of-truth invariant or a logged decision):
  P  parity        guild-data.js  ==  guild-data.json
  D23 report-gate  every workflow ENDS with a Butler 'report' gate   (decision #23)
  C  qm-close      every workflow's last member step before report is the-quartermaster
  A  arsenal-order per member: doers → thinkers/duals → sonnet last   (session decision)
  R  refs          workflow actors ∈ members∪{you}; gates valid; member skills exist
  S  source==gen   member .md frontmatter weapons order == generated guild-data
  W  weaponsDesc   members-meta weaponsDesc set == member weapons set
  N  counts        guild-data meta.counts == real lengths
"""
import json, re, sys, pathlib

ROOT = pathlib.Path(__file__).parent

# role per model id, mirrored from MODELS in app.js. sonnet is "both" but forced last.
ROLE = {
    "opus": "thinker", "gpt-5.5": "thinker", "deepseek-v4-pro": "thinker",
    "glm-5.2": "both", "qwen3.5": "both", "sonnet": "both",
    "haiku": "doer", "minimax-m3": "doer", "kimi-k2.7": "doer",
    "nemotron-3-ultra": "doer", "gemma4": "doer",
    "image-01": "doer", "minimax-video": "doer", "minimax-speech": "doer", "minimax-music": "doer",
}

CLAUDE_NATIVE = {"opus", "sonnet", "haiku"}
MEDIA_WEAPONS = {"image-01", "minimax-video", "minimax-speech", "minimax-music"}


def expected_order(weapons):
    """doers (best-first) + thinkers&duals minus sonnet (best-first) + sonnet."""
    doers = [w for w in weapons if ROLE.get(w) == "doer"]
    thinkers = [w for w in weapons if ROLE.get(w) in ("thinker", "both") and w != "sonnet"]
    tail = ["sonnet"] if "sonnet" in weapons else []
    return doers + thinkers + tail


def frontmatter_list(text, key):
    m = re.search(rf'^{key}:\s*\[([^\]]*)\]', text, re.M)
    if not m:
        return None
    return [x.strip() for x in m.group(1).split(",") if x.strip()]


def main():
    fails = []
    notes = []

    g = json.loads((ROOT / "guild-data.json").read_text())
    members = {m["id"]: m for m in g["members"]}
    skills_meta = json.loads((ROOT / "skills-meta.json").read_text())
    skill_ids = set(skills_meta.keys())
    meta = json.loads((ROOT / "members-meta.json").read_text())["members"]
    log = json.loads((ROOT / "guild-log.json").read_text())["entries"]
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
            elif s.get("kind") == "gate":
                if s.get("gate") not in {"approval", "certify", "report"}:
                    fails.append(f"R  {wid}: unknown gate '{s.get('gate')}'")
            else:
                fails.append(f"R  {wid}: unknown step kind '{s.get('kind')}'")
        # C — last member step before the final report gate is the-quartermaster
        member_steps = [s for s in steps if s.get("kind") == "member"]
        if member_steps and member_steps[-1].get("actor") != "the-quartermaster":
            fails.append(f"C  {wid}: closes with '{member_steps[-1].get('actor')}', "
                         f"not the-quartermaster (conformance-close convention)")

    # per-member checks
    for mid, m in members.items():
        weapons = [w["model"] for w in m["weapons"]]
        # A — arsenal order rule
        exp = expected_order(weapons)
        if weapons != exp:
            fails.append(f"A  {mid}: arsenal order {weapons} != expected {exp}")
        # unknown roles
        for w in weapons:
            if w not in ROLE:
                fails.append(f"A  {mid}: weapon '{w}' has no role mapping")
        # W — members-meta weaponsDesc set == weapons set
        wd = set(meta.get(mid, {}).get("weaponsDesc", {}).keys())
        if wd != set(weapons):
            fails.append(f"W  {mid}: weaponsDesc {sorted(wd)} != weapons {sorted(weapons)}")
        # R — member skills exist in skills-meta
        for sk in m.get("skills", []):
            if sk not in skill_ids:
                fails.append(f"R  {mid}: skill '{sk}' not in skills-meta")
        # S — source .md weapons order == generated
        md = ROOT / "star-alliance-members" / f"{mid}.md"
        if md.exists():
            src = frontmatter_list(md.read_text(), "weapons")
            if src is not None and src != weapons:
                fails.append(f"S  {mid}: .md weapons {src} != generated {weapons}")

    # U — weapon-utility is foundational: every member must carry it (session decision)
    if "weapon-utility" in skill_ids:
        for mid, m in members.items():
            if "weapon-utility" not in m.get("skills", []):
                fails.append(f"U  {mid}: missing foundational skill 'weapon-utility' (every member must carry it)")

    # T — every type build.py explicitly classifies must be loggable via log_event.py
    def _set(text, name):
        mo = re.search(rf'{name}\s*=\s*\{{([^}}]*)\}}', text)
        return set(re.findall(r'"([^"]+)"', mo.group(1))) if mo else set()
    bp = (ROOT / "build.py").read_text()
    le = (ROOT / "log_event.py").read_text()
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
        fails.append(f"K  skill dirs vs skills-meta differ: only-dir={sorted(skill_dirs - meta_keys)} "
                     f"only-meta={sorted(meta_keys - skill_dirs)}")
    if skill_dirs != data_ids:
        fails.append(f"K  skill dirs vs guild-data differ: only-dir={sorted(skill_dirs - data_ids)} "
                     f"only-data={sorted(data_ids - skill_dirs)}")

    # G — gen-workflow-art.cjs has a prompt entry for every workflow (art can be forged)
    gen = (ROOT / "gen-workflow-art.cjs")
    if gen.exists():
        gen_ids = set(re.findall(r'id:\s*"([^"]+)"', gen.read_text()))
        uncovered = {w["id"] for w in g["workflows"]} - gen_ids
        if uncovered:
            fails.append(f"G  gen-workflow-art.cjs missing art prompt for {sorted(uncovered)}")

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
    doms = json.loads((ROOT / "domains.json").read_text())["domains"]
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

    # === V — every skill SKILL.md carries a parseable version — audit #1 ===
    for name in sorted(skill_dirs):
        txt = (ROOT / "star-alliance-skills" / name / "SKILL.md").read_text()
        if not re.search(r'(?m)^[ \t]*version:\s*\S+', txt):
            fails.append(f"V  skill '{name}' has no version in SKILL.md (metadata.version required)")

    # === L — weapon routability (hard) + liveness (NOTE) — audit #1/#2 ===
    smt = (ROOT / "star-alliance-arsenal" / "summon.py").read_text()
    cloud_map = dict(re.findall(r"'([^']+)':\s*'([^']+:cloud)'", smt))
    routable = set(CLAUDE_NATIVE) | set(cloud_map) | MEDIA_WEAPONS | {"minimax-m3"}
    if "gpt-5.5" in smt:
        routable.add("gpt-5.5")
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
    # QM's queue, not the build gate. See STRATEGIST-MEMBER-LEVELING.md §3.
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


if __name__ == "__main__":
    sys.exit(main())
