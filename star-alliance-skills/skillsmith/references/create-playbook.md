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
SA=~/Documents/Claude/Projects/star-alliance
mv <new-skill> "$SA/star-alliance-skills/<name>"                                      # one dir per skill UNDER star-alliance-skills/ (NOT repo root — skills migrated 2026-06-24)
python3 "$SA/star-alliance-skills/skillsmith/scripts/skill_registry.py" check <name>  # 0 hard violations
python3 "$SA/star-alliance-skills/skillsmith/scripts/skill_registry.py" write         # add it to VERSIONS.md
```

## Step C4 — Wire it into the guild dashboard (REQUIRED — don't skip)

`skill_registry.py write` only touches `VERSIONS.md`. The dashboard (`guild-data.*` + the web app)
reads **four other hand-edited sources**. A new skill is **not done** until all four are updated and
`build.py` is re-run — skip any and the skill ships broken: no card, **no themed art** (falls back to
the bare emoji — this is exactly the `storm-investigation` v1.0.0 miss), or no owner.

1. **`skills-meta.json`** — add the presentation entry: `icon` (emoji), `blurb`, `level`
   (Foundational/Intermediate/Advanced/Master), `tabler` (a `ti-*` class), `triggers`, `modes`.
2. **`domains.json`** — add the skill `id` to the `star-alliance` home pool (+ any project domain that borrows it); bump the count in that domain's `notes`.
3. **Assign to member(s)** — add the skill to the adequate guild member's `skills:` frontmatter in
   `star-alliance-members/<member>.md`, **and** mention it in that member's body (§How you work) so the
   deployed agent actually invokes it.
4. **Themed art (Fallen Sword)** — every skill has a `skill-art/<id>.png`. Add a `{ id, prompt }` entry
   to **`gen-skill-art.cjs`** using the shared `STYLE` prefix (dark parchment, gold runic border,
   fantasy RPG icon) + a subject that depicts the skill; end the prompt with `no text, no watermarks`.
   Then render it — MiniMax's image API is the doer:

   ```sh
   node "$SA/gen-skill-art.cjs"          # renders ONLY the missing PNG; existing art is skipped
   ```

Then regenerate the dashboard data (sets each skill's `artPng` flag + folds in meta/members/domains):

```sh
python3 "$SA/build.py"                   # writes guild-data.js + guild-data.json
```

## Step C5 — Install to the device (optional) + commit

If the skill should be usable across projects right away:

```sh
python3 "$SA/star-alliance-skills/skillsmith/scripts/skill_sync.py" apply --skill <name> --direction install   # repo→global
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
