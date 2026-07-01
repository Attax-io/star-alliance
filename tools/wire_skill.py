#!/usr/bin/env python3
"""wire_skill.py — auto-wire a new skill into every derived surface.

A skill is "created" the moment its dir + SKILL.md exist, but it is not DONE until the
four hand-edited dashboard surfaces agree (skills-meta.json, domains.json home pool,
every skill-count claim, and a themed art tile). Skill authors routinely skip these,
leaving the conformity sweep red. This script mechanizes the deterministic parts and
prints the parts that need human judgment (member assignment + drill row + art subject).

Idempotent: run it on an already-wired skill and it's a no-op.

    python3 tools/wire_skill.py <skill-name> [--render] [--all]

  <skill-name>   wire one skill dir under star-alliance-skills/<name>/
  --all          wire EVERY skill dir that's missing from skills-meta.json
  --render       also run gen-skill-art.cjs (renders only missing tiles)

After it runs: assign the skill to a member (+ Skill Drills row), refine the art prompt,
then `python3 build.py` and `python3 tools/conformity_check.py`.
"""
import json
import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "star-alliance-skills"
META = ROOT / "data" / "skills-meta.json"
DOMAINS = ROOT / "data" / "domains.json"
README = ROOT / "README.md"
ART = ROOT / "tools" / "generators" / "gen-skill-art.cjs"
STYLE_REF = "${STYLE}"


def skill_dirs():
    return sorted(p.name for p in SKILLS_DIR.iterdir()
                  if p.is_dir() and (p / "SKILL.md").exists())


def read_frontmatter(name):
    txt = (SKILLS_DIR / name / "SKILL.md").read_text()
    desc = ""
    m = re.search(r'^description:\s*"(.*?)"\s*$', txt, re.S | re.M)
    if m:
        desc = m.group(1)
    return desc


def derive_triggers(desc):
    # Pull the "Triggers:" / "Use for:" clause out of the description, else blank.
    m = re.search(r"(?:Triggers|Use for|Use when)[:]\s*(.*?)(?:\.\s+Differentiate|\.\s+Distinct|$)",
                  desc, re.S)
    if not m:
        return ""
    seg = m.group(1).strip().rstrip(".")
    # keep only the quoted phrases if present
    quoted = re.findall(r"'[^']+'", seg)
    return ", ".join(quoted) if quoted else seg[:240]


def derive_blurb(desc):
    # First sentence, stripped of the "The X's craft for " preamble, capped.
    first = re.split(r"(?<=[.])\s", desc.strip())[0]
    first = re.sub(r"^The [\w-]+'s (read-only )?(craft|discipline|engine) for ", "", first)
    first = first[:1].upper() + first[1:]
    return first[:95].rstrip(" ,;")


def load_json(path):
    return json.loads(path.read_text())


def dump_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def wire_meta(name, desc):
    meta = load_json(META)
    if name in meta:
        return False
    meta[name] = {
        "icon": "🧩",
        "blurb": derive_blurb(desc),
        "level": "Advanced",
        "tabler": "ti-puzzle",
        "triggers": derive_triggers(desc),
        "modes": "",
    }
    # keep keys sorted for a stable file (the home pool order is independent)
    meta = {k: meta[k] for k in sorted(meta)}
    dump_json(META, meta)
    return True


def wire_domains_and_counts():
    """Add any missing skill to the home pool, then reconcile EVERY count surface
    to the real skill-dir total. Returns (added_to_pool[list], new_count)."""
    dirs = skill_dirs()
    total = len(dirs)
    dom = load_json(DOMAINS)
    home = next(d for d in dom["domains"] if d["id"] == "star-alliance")
    added = [s for s in dirs if s not in home["skills"]]
    for s in added:
        home["skills"].append(s)
    # notes count
    home["notes"] = re.sub(r"\b\d+ skills\b", f"{total} skills", home["notes"])
    dump_json(DOMAINS, dom)
    # README — every "(N skills" / "N skills)" mention
    txt = README.read_text()
    txt = re.sub(r"\b\d+ skills\b", f"{total} skills", txt)
    README.write_text(txt)
    return added, total


def wire_art_stub(name, blurb):
    txt = ART.read_text()
    if f'id: "{name}"' in txt:
        return False
    entry = (
        f'  {{\n'
        f'    id: "{name}",\n'
        f'    prompt: `{STYLE_REF}. [REFINE — Designer handoff] A Fallen-Sword emblem for '
        f'"{blurb}", no text, no watermarks`,\n'
        f'  }},\n'
    )
    txt = txt.replace("const SKILLS = [\n", "const SKILLS = [\n" + entry, 1)
    ART.write_text(txt)
    return True



def run_make_thumbs():
    """Run make_thumbs.py in incremental mode so any newly-rendered skill art tile
    immediately gets its dashboard thumbnail (art/skill-art-thumb/<id>.png).
    Never hard-fails skill wiring — Pillow may be missing; if so, try the repo's
    scratchpad-venv convention once, and if that also fails, print a clear warning
    and return so wiring still completes."""
    thumbs = ROOT / "tools" / "make_thumbs.py"
    try:
        r = subprocess.run([sys.executable, str(thumbs)], cwd=ROOT,
                            capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            print("• thumbnails: ok (incremental \u2014 only missing/stale thumbs rendered)")
            return
        if "No module named 'PIL'" in (r.stderr or "") or "No module named 'PIL'" in (r.stdout or ""):
            print("  \u26a0 Pillow not installed \u2014 building a one-off scratchpad venv to render thumbnails")
            venv_dir = ROOT / ".scratch-thumbs-venv"
            try:
                subprocess.run([sys.executable, "-m", "venv", str(venv_dir)],
                                check=True, capture_output=True, timeout=120)
                pip = venv_dir / "bin" / "pip"
                py = venv_dir / "bin" / "python3"
                subprocess.run([str(pip), "install", "-q", "pillow"],
                                check=True, capture_output=True, timeout=180)
                r2 = subprocess.run([str(py), str(thumbs)], cwd=ROOT,
                                     capture_output=True, text=True, timeout=120)
                if r2.returncode == 0:
                    print("• thumbnails: ok (via scratchpad venv \u2014 Pillow installed on the fly)")
                else:
                    print(f"  \u26a0 thumbnail generation still failed via scratchpad venv:\n{r2.stderr[-800:]}")
                    print("  \u26a0 SKIPPING thumbnail generation \u2014 wiring will still complete.")
                    print("  \u26a0 Fix manually: python3 -m venv .scratch-thumbs-venv && "
                          ".scratch-thumbs-venv/bin/pip install pillow && "
                          ".scratch-thumbs-venv/bin/python3 tools/make_thumbs.py")
            except Exception as e:
                print(f"  \u26a0 could not build scratchpad venv ({e}) \u2014 SKIPPING thumbnail generation.")
                print("  \u26a0 Install Pillow manually and re-run: python3 tools/make_thumbs.py")
        else:
            print("  \u26a0 thumbnail generation failed (non-Pillow error) \u2014 SKIPPING, wiring still completes.")
            print(f"  \u26a0 {(r.stderr or r.stdout)[-800:]}")
    except Exception as e:
        print(f"  \u26a0 could not run make_thumbs.py ({e}) \u2014 SKIPPING thumbnail generation, wiring still completes.")


def main():
    args = sys.argv[1:]
    render = "--render" in args
    do_all = "--all" in args
    names = [a for a in args if not a.startswith("--")]

    if do_all:
        meta = load_json(META)
        names = [s for s in skill_dirs() if s not in meta]
        if not names:
            print("✓ every skill dir already has a skills-meta entry")
    elif not names:
        print(__doc__)
        sys.exit(1)

    for name in names:
        if not (SKILLS_DIR / name / "SKILL.md").exists():
            print(f"✗ {name}: no star-alliance-skills/{name}/SKILL.md")
            continue
        desc = read_frontmatter(name)
        blurb = derive_blurb(desc)
        m = wire_meta(name, desc)
        a = wire_art_stub(name, blurb)
        print(f"• {name}: meta {'added' if m else 'ok'} · art-stub {'added' if a else 'ok'}")
        if len(desc) > 1024:
            print(f"  ⚠ description is {len(desc)} chars (>1024 hard cap) — TRIM before build")

    added, total = wire_domains_and_counts()
    print(f"• home pool: {('added ' + ', '.join(added)) if added else 'ok'} · counts → {total}")

    if render:
        print("• rendering missing art tiles…")
        subprocess.run(["node", str(ART)], cwd=ROOT)
        print("• generating dashboard thumbnails for any newly-rendered tiles…")
        run_make_thumbs()

    print("\nMANUAL (judgment) — not automated:")
    print("  1. Assign each skill to a member: add to `skills:` frontmatter in")
    print("     star-alliance-members/<member>.md AND add a `## Skill Drills` row.")
    print("  2. Refine the art prompt subject in gen-skill-art.cjs (Designer handoff),")
    print("     then re-render that tile: node tools/generators/gen-skill-art.cjs --regen <name>")
    print("  3. python3 build.py && python3 tools/conformity_check.py")


if __name__ == "__main__":
    main()
