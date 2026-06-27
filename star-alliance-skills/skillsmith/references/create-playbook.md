---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

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
   **Reconcile EVERY derived skill-count surface in the same pass — not just the registry.** Adding or removing a skill changes the repo's skill total, which is claimed in **four** hand-maintained places that must all agree: `domains.json` `star-alliance.skills[]` length **and** its `notes` ("… + N skills …"), and **`README.md`** (every `(N skills` mention — there are two: the tree comment and the VERSIONS pointer). `skill_registry.py write` only fixes `VERSIONS.md`'s header line; it does **not** touch README or domains. The conformity-close `DC` check (audit #1) enforces all of these against the real skill-dir count, so a missed README/domains count FAILS the sweep — fix every count when the total moves, or the next sweep is red.
3. **Assign to member(s)** — add the skill to the adequate guild member's `skills:` frontmatter in
   `star-alliance-members/<member>.md`, **and** mention it in that member's body (§How you work) so the
   deployed agent actually invokes it, **and add a matching `## Skill Drills` table row** (see the
   skill↔member invariant below). All three move together — frontmatter without a drill row FAILS the
   `SD` conformity check (`'<skill>' is carried but has no Skill Drills table row`).

   > **Skill ↔ member invariant (the `SD` check, both directions).** A member's `skills:` frontmatter
   > and its `## Skill Drills` table are ONE fact in two places — `build.py` regenerates the *weapons*
   > table but NEVER the *drills* table (it is hand-authored), so the two can silently diverge. Whenever
   > you **ADD** a skill to a member's loadout, add a drill row in the SAME edit:
   > `| `<skill>` | invoke WHEN … | do NOT invoke for … | pairs with `<skill>` |` (put a craft skill in
   > the main table, a cross-cutting one in the "Universal skills" table). Whenever you **REMOVE** a
   > skill from the loadout, delete its drill row in the same edit. The `SD` audit in
   > `conformity_check.py` enforces exactly this; conformity-close (Invariant #8) is the backstop, not
   > the primary guard — get it right at edit time, every time.
4. **Themed art (Fallen Sword) — the Designer's MANDATORY handoff.** Every skill has a
   `skill-art/<id>.png`; a new skill with none falls back to a bare emoji (the `storm-investigation`
   v1.0.0 miss). In the **Skill Forge** star-map workflow this is an explicit step owned by
   **the-designer** ("Forge the Sigil", `kind: member`, MANDATORY) — so when `create` runs under that
   workflow, the Quartermaster *hands the art to the Designer*, who adds the `{ id, prompt }` entry to
   **`gen-skill-art.cjs`** using the shared `STYLE` prefix (dark parchment, gold runic border, fantasy
   RPG icon) + a subject that depicts the skill, ending with `no text, no watermarks`, and renders it.
   Running `create` outside the workflow? The Quartermaster does this step himself — it is never
   optional, never deferred to "later". Then render — MiniMax's image API is the doer:

   ```sh
   node "$SA/gen-skill-art.cjs"          # renders ONLY the missing PNG; existing art is skipped
   ```

Then regenerate the dashboard data (sets each skill's `artPng` flag + folds in meta/members/domains):

```sh
python3 "$SA/build.py"                   # writes guild-data.js + guild-data.json
```

## Step C5 — Install to the device (optional) + conformity-close + commit

If the skill should be usable across projects right away:

```sh
python3 "$SA/star-alliance-skills/skillsmith/scripts/skill_sync.py" apply --skill <name> --direction install   # repo→global
```

**Conformity-close (Invariant #8) — the Quartermaster's final gate.** C4 already ran `build.py`; now prove the new skill is reflected everywhere:

```sh
python3 "$SA/conformity_check.py"     # FULL CONFORMITY (exit 0) — the K-invariant catches a skill dir not yet in skills-meta / guild-data
```

If it FAILS (e.g. K-check reports `only-dir=[<name>]`), the C4 wiring is incomplete — add the missing `skills-meta.json` / `domains.json` / member / art entry, re-run `build.py`, re-check. Then commit + push (scope to the new skill + its dashboard regen; avoid a blind `add -A` of a co-mingled tree, §L27):

```sh
git -C <repo> commit <scoped paths> && git -C <repo> push origin main
```

## Mode: create-from-source — distil a skill from a book / PDF / spec

When the skill's body is a *source document* (a book, a PDF, a long spec) rather than authored-from-scratch
craft, use this distillation loop. It is the doer/thinker shape: the doer (MiniMax) does ALL the reading and
writing of content, the thinker only slices, reviews, and files. Proven on `japanese-candlesticks` (Nison,
331pp → 11 reference files).

1. **Extract the text first — don't trust the harness page hint.** There is no system `pdftotext` on this
   device and `pip install` is blocked by PEP 668, so build a throwaway venv in the scratchpad:

   ```sh
   python3 -m venv "$SCRATCH/venv" && "$SCRATCH/venv/bin/pip" install -q pypdf
   "$SCRATCH/venv/bin/python" -c 'import pypdf,sys; r=pypdf.PdfReader(sys.argv[1]); \
     [open(f"p{i+1:02d}.txt","w").write(p.extract_text() or "") for i,p in enumerate(r.pages)]' "<pdf>"
   ```

   **Verify the REAL length from the extractor** — the harness file hint lies (a "60-page" PDF was 331). Print
   a per-page char-count density map so you can see chapter boundaries and skip blank/figure pages.

2. **Slice by chapter / section**, not by fixed page windows — one excerpt file per pattern-family / topic so
   each reference file has a coherent scope. Keep each excerpt under ~100k chars.

3. **Doer-draft each chunk, ONE at a time.** Drive a loop that calls the doer per excerpt and writes the raw
   Markdown to `references/<nn>-<slug>.md`, logging progress. Put the *instruction* in `-s` (system) and the
   *excerpt* in `-f` (the file is the user prompt). Big chunks need a bigger budget than the default — size
   them explicitly:

   ```sh
   python3 "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/summon.py" minimax-m3 -f "$SRC" -s "$SYS" --max-tokens 16000 --timeout 600 > "$DEST"
   ```

   (`summon.py` passes `--max-tokens`/`--timeout` through to the backend; drop to `minimax.py` direct only if
   a backend chokes.) Give the doer hard rules: start with an exact H1, one `##` per pattern with fixed
   bold-labelled fields (Type / Structure / Recognition / Psychology / Signal & confirmation / notes), use
   ONLY facts in the excerpt, invent no numbers, drop chart-image/exhibit references, Markdown only.

4. **Thinker reviews + files.** After each draft: check the H1 is right and the tail ends on a clean sentence
   (a draft ending mid-word = it hit the token cap → re-run that chunk with a higher `--max-tokens` or split
   it). Spot-check fidelity on 1–2 files. The references are the doer's; `SKILL.md` is the thinker's — a lean
   body that frames the craft and indexes the `references/`.

5. **Then the normal C2–C5 wiring** (version, registry, the four dashboard sources, art, build, conformity,
   sync). Write the **description LAST and keep it ≤ ~900 chars** — the 1024 hard cap bites on pattern-rich
   skills (this one took three trims). When a member gains the skill, fix any **count-drift** in that member's
   body prose ("all *three* crafts" → "all *four*") — easy to miss, and conformity won't catch wording.

## Notes

- **Vendoring an upstream skill** (not authoring fresh): drop it in; it usually already carries
  `metadata.version` (keep it). Add it to `VENDORED` in `skill_registry.py` + `skill_sync.py` if it's an
  external/self-updating one, and register it. Don't hand-edit a self-updating external (`impeccable`) — if
  it ships a top-level `version:`, leave it (the reader falls back to it).
- **Where does the skill live?** Repo root = the distribution copy. The device copy is what runs — Step
  C4 installs it. A project-specific skill can instead go straight into a project's `.claude/skills/`.
