#!/usr/bin/env python3
"""Conformity check — Claude-only Star Alliance harness.

Read-only. Prints a PASS/FAIL map and exits 1 on any contradiction.

This is the LEAN sweep for the Claude-only harness (Hermes/MiniMax doer layer
removed 2026-07-03). It verifies the source-of-truth → generated contract and the
core invariants; the old brain/doer two-seat, profile-distribution, dispatch-bridge,
and cloud-tag checks are gone with the doer layer.

Checks:
  P   parity        guild-data.js  ==  guild-data.json
  MCP mcp-register  guild MCP server registered in repo .mcp.json
  N   counts        guild-data meta.counts == real lengths
  K   skills        skill dirs == skills-meta keys == guild-data skill ids
  VER versions      every skill's SKILL.md version == its VERSIONS.md row
  BR  brain         every member's model: is a Claude model (opus|sonnet|haiku) in the registry
  R   refs          workflow actors ∈ members∪{you}; gates valid; member skills exist
  D23 report-gate   every workflow ENDS with a Butler 'report' gate
  C   qm-close      every mutating workflow's last member step is the-quartermaster
  SD  skill-drills  every member-carried skill has a `## Skill Drills` table row
  AG  agents        .claude/agents/the-*.md match star-alliance-members/ (install_agents --check)
  REG registry      models.json is Claude-only (backend==claude, brain seat only)
"""
import json, re, sys, pathlib, subprocess

ROOT = next((p for p in pathlib.Path(__file__).resolve().parents
             if (p / "VERSIONS.md").exists() and (p / ".git").exists()),
            pathlib.Path(__file__).resolve().parent)

CLAUDE_MODELS = {"opus", "sonnet", "haiku"}


def frontmatter_list(text, key):
    m = re.search(rf'^{key}:\s*\[([^\]]*)\]', text, re.M)
    if not m:
        return None
    return [x.strip() for x in m.group(1).split(",") if x.strip()]


def main():
    fails, notes = [], []

    g = json.loads((ROOT / "guild-data.json").read_text())
    members_list = g.get("members") or g.get("agents") or []
    members = {m["id"]: m for m in members_list}

    skills_meta = json.loads((ROOT / "data/skills-meta.json").read_text())
    skill_ids = set(skills_meta.keys())

    # ── REG: models.json must be Claude-only ──
    try:
        _regm = json.loads((ROOT / "star-alliance-arsenal" / "models.json").read_text())
    except Exception as e:
        _regm = {"models": {}, "seats": {}}
        fails.append(f"REG could not read models.json: {e}")
    reg_models = _regm.get("models", {})
    for mid, md in reg_models.items():
        if md.get("backend") != "claude":
            fails.append(f"REG model '{mid}' has backend '{md.get('backend')}' — the registry "
                         f"is Claude-only (opus/sonnet/haiku)")
    seats = _regm.get("seats", {})
    if "doer" in seats or "bench" in seats:
        fails.append("REG models.json seats still declares a 'doer'/'bench' seat — the "
                     "Claude-only harness has a brain seat only")
    _brain = seats.get("brain") or {}
    for mid in [_brain.get("default")] + list(_brain.get("fallback") or []):
        if mid and mid not in reg_models:
            fails.append(f"REG brain seat references '{mid}' which is not a registry model")

    # ── P: guild-data.js == guild-data.json ──
    js_path = ROOT / "guild-data.js"
    if js_path.exists():
        mo = re.search(r'\{.*\}', js_path.read_text(), re.S)
        if not mo or json.loads(mo.group(0)) != g:
            fails.append("P  parity: guild-data.js does NOT match guild-data.json (rerun build.py)")

    # ── MCP: guild server registered in repo .mcp.json ──
    repo_mcp = ROOT / ".mcp.json"
    ok = False
    if repo_mcp.exists():
        try:
            ok = "star-alliance" in json.loads(repo_mcp.read_text()).get("mcpServers", {})
        except Exception:
            ok = False
    if not ok:
        fails.append("MCP guild MCP server 'star-alliance' not registered in repo .mcp.json")

    # ── workflow-level checks ──
    for wf in g["workflows"]:
        wid = wf["id"]
        steps = wf["steps"]
        last = steps[-1] if steps else {}
        if last.get("kind") != "gate" or last.get("gate") != "report":
            fails.append(f"D23 {wid}: does not END with a 'report' gate")
        for s in steps:
            if s.get("kind") in ("member", "agent"):
                a = s.get("actor")
                if a != "you" and a not in members:
                    fails.append(f"R  {wid}: unknown actor '{a}'")
            elif s.get("kind") == "gate":
                if s.get("gate") not in {"approval", "certify", "report"}:
                    fails.append(f"R  {wid}: unknown gate '{s.get('gate')}'")
            else:
                fails.append(f"R  {wid}: unknown step kind '{s.get('kind')}'")
        wf_class = wf.get("class", "mutating")
        member_steps = [s for s in steps if s.get("kind") in ("member", "agent")]
        if wf_class != "read-only" and member_steps and member_steps[-1].get("actor") != "the-quartermaster":
            fails.append(f"C  {wid}: mutating workflow closes with "
                         f"'{member_steps[-1].get('actor')}', not the-quartermaster")

    # ── per-member checks ──
    for mid, m in members.items():
        brain = m.get("model")
        if not brain:
            fails.append(f"BR {mid}: no session model (model:) declared")
        elif brain not in CLAUDE_MODELS:
            fails.append(f"BR {mid}: model '{brain}' is not a Claude model (opus|sonnet|haiku)")
        elif brain not in reg_models:
            fails.append(f"BR {mid}: model '{brain}' is not in the models.json registry")
        for sk in m.get("skills", []):
            if sk not in skill_ids:
                fails.append(f"R  {mid}: skill '{sk}' not in skills-meta")

    # ── SD: skill-drill coverage (members are the SoT) ──
    members_dir = ROOT / "star-alliance-members"
    if members_dir.is_dir():
        for md in sorted(members_dir.glob("the-*.md")):
            text = md.read_text()
            skills = frontmatter_list(text, "skills")
            if skills is None:
                continue
            body = text.split("---", 2)[2] if text.count("---") >= 2 else text
            for sk in skills:
                if re.search(r'\|\s*`?' + re.escape(sk) + r'`?\s*\|', body) is None:
                    fails.append(f"SD {md.stem}: skill '{sk}' carried but has no Skill Drills row")

    # ── K: skill dirs == skills-meta == guild-data ids (ignore _-prefixed) ──
    skill_dirs = {d.name for d in (ROOT / "star-alliance-skills").iterdir()
                  if d.is_dir() and (d / "SKILL.md").exists() and not d.name.startswith("_")}
    meta_keys = {s for s in skills_meta if not s.startswith("_")}
    data_ids = {s["id"] for s in g["skills"] if not s["id"].startswith("_")}
    if skill_dirs != meta_keys:
        fails.append(f"K  skill dirs vs skills-meta differ: only-dir={sorted(skill_dirs - meta_keys)} "
                     f"only-meta={sorted(meta_keys - skill_dirs)}")
    if skill_dirs != data_ids:
        fails.append(f"K  skill dirs vs guild-data differ: only-dir={sorted(skill_dirs - data_ids)} "
                     f"only-data={sorted(data_ids - skill_dirs)}")

    # ── VER: SKILL.md version == VERSIONS.md row ──
    versions_path = ROOT / "VERSIONS.md"
    if versions_path.exists():
        ver_rows = dict(re.findall(
            r'\|\s*\[`([^`]+)`\][^|]*\|\s*([0-9]+\.[0-9]+\.[0-9]+)\s*\|', versions_path.read_text()))
        for s in sorted(skill_dirs):
            smd = (ROOT / "star-alliance-skills" / s / "SKILL.md").read_text()
            vm = re.search(r'^\s*version:\s*([0-9]+\.[0-9]+\.[0-9]+)', smd, re.M)
            skill_ver = vm.group(1) if vm else None
            if s not in ver_rows:
                notes.append(f"VER {s}: no row in VERSIONS.md (regen skill registry)")
            elif skill_ver and ver_rows[s] != skill_ver:
                fails.append(f"VER {s}: VERSIONS.md says {ver_rows[s]} but SKILL.md is {skill_ver}")

    # ── N: counts ──
    counts = g.get("meta", {}).get("counts", {})
    members_key = "members" if "members" in g else "agents"
    real = {members_key: len(members_list), "skills": len(g["skills"]), "workflows": len(g["workflows"])}
    for k, v in real.items():
        if counts.get(k) != v:
            fails.append(f"N  counts.{k}={counts.get(k)} != real {v}")

    # ── AG: .claude/agents match star-alliance-members (install_agents --check) ──
    ia = ROOT / "guild" / "install_agents.py"
    if ia.exists():
        try:
            r = subprocess.run(["python3", str(ia), "--check"],
                               capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                for ln in (r.stdout + r.stderr).splitlines():
                    if "DRIFT" in ln:
                        fails.append(f"AG {ln.strip()} — run: python3 guild/install_agents.py")
        except Exception as e:
            notes.append(f"AG install_agents --check skipped: {e}")

    # ── report ──
    print("═" * 60)
    print(" CONFORMITY SWEEP — Star Alliance (Claude-only harness)")
    print("═" * 60)
    print(f" members={real[members_key]}  skills={real['skills']}  workflows={real['workflows']}  "
          f"models={sorted(reg_models)}")
    print("─" * 60)
    if notes:
        print(" NOTES (non-blocking):")
        for n in notes:
            print(f"   • {n}")
        print("─" * 60)
    if fails:
        print(f" ✗ {len(fails)} CONTRADICTION(S):")
        for f in fails:
            print(f"   ✗ {f}")
        print("═" * 60)
        return 1
    print(" ✓ FULL CONFORMITY — Claude-only harness holds.")
    print("═" * 60)
    return 0


def check_member(name):
    """Fast-path: audit ONE member's skill↔drill coupling after a loadout edit."""
    slug = name if name.startswith("the-") else f"the-{name}"
    md = ROOT / "star-alliance-members" / f"{slug}.md"
    if not md.exists():
        print(f"✗ no such member: {slug}.md")
        return 1
    text = md.read_text()
    skills = frontmatter_list(text, "skills") or []
    body = text.split("---", 2)[2] if text.count("---") >= 2 else text
    try:
        meta_keys = set(json.loads((ROOT / "data" / "skills-meta.json").read_text()).keys())
    except Exception:
        meta_keys = set()
    fails = []
    for sk in skills:
        if re.search(r'\|\s*`?' + re.escape(sk) + r'`?\s*\|', body) is None:
            fails.append(f"SD {slug}: skill '{sk}' carried but has no Skill Drills row")
        if meta_keys and sk not in meta_keys:
            fails.append(f"R  {slug}: skill '{sk}' not in skills-meta.json")
    for row_sk in re.findall(r'^\|\s*`([a-z0-9][a-z0-9-]+)`\s*\|', body, re.M):
        if row_sk in meta_keys and row_sk not in skills:
            fails.append(f"SD {slug}: stale drill row for '{row_sk}' — not in the loadout")
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
