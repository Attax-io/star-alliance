# Mode: create — author a new skill, then make it upgradeable

Goal: a brand-new skill, authored with the **official `skill-creator`** workflow, that lands in the
repo already wired into the repo's conventions (`metadata.version`, registry, Cowork limits) and
optionally installed to the device.

## Step C1 — Author via skill-creator (don't reinvent)

Use the official **`skill-creator`** skill. Invoke it (`Skill` tool → `skill-creator`, or the plugin
form `anthropic-skills:skill-creator`), or follow its `SKILL.md` directly. Its location on disk:

```
~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator/
```

Its workflow (don't skip the interview — a good description is the whole triggering mechanism):

1. **Capture intent** — what should the skill enable? when should it trigger (user phrases/contexts)? expected output? test cases worth it?
2. **Interview + research** — fill gaps; look at similar skills.
3. **Write `SKILL.md`** — name (kebab-case ≤64), a **pushy, trigger-rich description**, lean body, bundled `scripts/`/`references/` as needed.
4. **(Optional) eval** — for objectively-verifiable skills, set up test cases per skill-creator's eval loop.

Validate with skill-creator's own checker:

```sh
SC=~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator
python3 "$SC/scripts/quick_validate.py" <path-to-new-skill>     # name + description + allowed props
```

## Step C2 — Make it upgradeable (the skillsmith wrapping)

Before it lands in the repo, ensure:

- **`metadata.version: 1.0.0`** in the frontmatter (the canonical field; a *top-level* `version:` is rejected by the validator).
- **Description ≤ 1024 chars and no `<`/`>`** (skill-creator's validator enforces both; `skill_registry.py check` re-confirms the length).
- **Body < 500 lines / well under ~10k words** — extract verbose detail to `references/` from the start (see `cowork-limits.md`). Don't let a new skill ship already over the ideal.
- A short **§Versioning** note (the bump contract) — copy the shape used by the other own-skills. Optional **§Changelog** with the `1.0.0` row.

## Step C3 — Place it in the repo

```sh
mv <new-skill> ~/Documents/Claude/Projects/claude-skills/<name>     # one dir per skill at repo root
python3 skillsmith/scripts/skill_registry.py check <name>           # 0 hard violations
python3 skillsmith/scripts/skill_registry.py write                  # add it to VERSIONS.md
```

## Step C4 — Install to the device (optional) + commit

If the skill should be usable across projects right away:

```sh
python3 skillsmith/scripts/skill_sync.py apply --skill <name> --direction install   # repo→global
```

Then commit + push the repo:

```sh
git -C <repo> add -A && git -C <repo> commit && git -C <repo> push origin main
```

## Notes

- **Vendoring an upstream skill** (not authoring fresh): drop it in; it usually already carries
  `metadata.version` (keep it). Add it to `VENDORED` in `skill_registry.py` + `skill_sync.py` if it's an
  external/self-updating one, and register it. Don't hand-edit a self-updating external (`impeccable`) — if
  it ships a top-level `version:`, leave it (the reader falls back to it).
- **Where does the skill live?** Repo root = the distribution copy. The device copy is what runs — Step
  C4 installs it. A project-specific skill can instead go straight into a project's `.claude/skills/`.
