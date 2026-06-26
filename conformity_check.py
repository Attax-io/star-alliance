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
