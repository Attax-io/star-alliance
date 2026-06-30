---
name: new-member-onboarding
description: "The exact checklist to run whenever a new guild member is recruited. Profiles must be created, installed, art-forged, and committed — in that order. Use when: 'onboard new member', 'recruit a member', 'add a new profile', 'new the-<slug>', 'create profiles/<slug>/'. Pairs with skillsmith, workflow-forge, dual-model-review."
metadata:
  version: 1.0.0
type: Skill
---

# New member onboarding — the Quartermaster's checklist

When a new guild member is recruited, eight steps must run in order. Skip a step
and the member exists in `star-alliance-members/` but is missing from the
runtime: no Hermes profile, no art tile, no conformity pass, no commit. This
skill is the source of truth for the sequence.

Substitute `<slug>` with the member's short slug throughout (e.g. `steward`,
`strategist`). The full member id is `the-<slug>`.

## 1. Member file

Create `star-alliance-members/the-<slug>.md`.

Use an existing member file (e.g. `star-alliance-members/the-steward.md`) as
the template. Required frontmatter fields:

- `name: the-<slug>`
- `description:` — one-line plain-English summary of when to deploy this member
- `model:` — the member's brain (e.g. `glm-5.2`, `opus`)
- `tools: [Read, Edit, Write, Bash]`
- `skills:` — list of skill slugs the member invokes
- `type: Member`

Body: first-person soul ("You are **the <Slug>**, …"), expertise bullets, the
two-layer Arsenal section, Skill Drills table, How you work, What you don't
do.

## 2. Claude-side agent file

Generate the Claude Code subagent mirror:

```
python3 guild/install_agents.py
```

This writes `.claude/agents/the-<slug>.md` from the member file. If the
generator only enumerates the original roster, add `<slug>` to its source list
first (mirrors what we did for `PROFILE_MAP` in `tools/publish_profiles.py`).

## 3. Hermes profile folder

Create `profiles/<slug>/` with four files. Copy from `profiles/architect/` and
adapt:

- **SOUL.md** — first-person soul. Frontmatter:
  - `name: the-<slug>`
  - `profile: <slug>`
  - `source: agents/the-<slug>.md`
  - Body sections: Who I am, What I do, What I never do, How I work, How I
    collaborate, My plain-English rule, What I leave at the door, On being
    dispatched, On tools, What good looks like. Model the structure on
    `profiles/architect/SOUL.md`; do not pirate its content.

- **config.yaml** — copy `profiles/architect/config.yaml`. Adjust only the
  `model.default:` line to match the member's brain. Keep the `providers`
  block and `_config_version: 31`.

- **distribution.yaml** — copy `profiles/architect/distribution.yaml`. Change
  `name:`, `version: 1.0.0`, and `description:` (one-line plain-English
  matching the member's purpose).

- **skills.yaml** — one entry per skill from the member's `skills:` list,
  each with `name:` and `reason:`. Quote any `reason:` value that contains a
  colon (`:`) inside the prose — YAML parses it as a mapping otherwise.

## 4. Install the profile

```
python3 tools/publish_profiles.py --only the-<slug>
```

If `publish_profiles.py` errors with an unknown-slug message, it has a
hardcoded `PROFILE_MAP`. Add `"the-<slug>": "<slug>"` to that map and rerun.
Verify the profile landed:

```
ls ~/.hermes/profiles/<slug>/
```

Expect: `SOUL.md config.yaml cron distribution.yaml home logs memories plans
sessions skills skills.yaml skins workspace`.

## 5. Art tile

Forge a member portrait and thumb via the arsenal image generator, then save
to the two art directories:

```
python3 star-alliance-arsenal/imagegen.py
```

Save outputs to:

- `art/member-art/the-<slug>.png`
- `art/member-art-thumb/the-<slug>.png`

Match the dimensions and style of the existing tiles in those directories.

## 6. Rebuild guild data

```
python3 build.py
```

This regenerates the dashboard data, member registry, and any other
derived artifacts that depend on the member catalog. Without this step the
new profile is invisible to the dashboard.

## 7. Conformity check

```
python3 tools/conformity_check.py
```

Confirm zero drift. Pay attention to the `PD` tag — it verifies repo
`profiles/<slug>/` matches installed `~/.hermes/profiles/<slug>/`. If `PD`
fails on the new member, the install step did not actually overwrite the
distribution-owned files; rerun step 4 with `--force`.

## 8. Commit

Stage every file the onboarding produced — the member file, the Claude agent
mirror, the four profile files, the two art tiles, and any regenerated
guild-data files. One commit, one message naming the new member.

```
git add star-alliance-members/the-<slug>.md \
        .claude/agents/the-<slug>.md \
        profiles/<slug>/ \
        art/member-art/the-<slug>.png \
        art/member-art-thumb/the-<slug>.png \
        guild-data.json guild-data.js dashboard.css \
        tools/publish_profiles.py
git commit -m "Onboard the-<slug>: member + profile + art"
```

If `publish_profiles.py` was edited to add the slug to `PROFILE_MAP`, include
that diff in the same commit.

## Pitfalls

- **YAML colon in reason strings.** Any `reason:` value containing a `:`
  inside the prose must be wrapped in quotes. YAML will not raise a runtime
  error — it will silently misparse, and `hermes profile install` will
  produce a skills.yaml with a missing entry.
- **`publish_profiles.py` is hardcoded.** It does not auto-discover
  `profiles/*` subdirectories. Forgetting step 4's map edit makes
  `--only the-<slug>` exit with "ERROR: unknown slug(s)" before any install.
- **Step 6 must precede step 7.** `conformity_check.py` reads the rebuilt
  `guild-data.json`. Running conformity against a stale build will report
  phantom drift on the new member.
- **Stage only what onboarding produced.** Do not scoop in unrelated
  experiments from the working tree. The diff is the diff the onboarding
  earned.
- **The `--only` flag is comma-separated, not space-separated.**
  `python3 tools/publish_profiles.py --only the-steward the-strategist` will
  only install `the-steward` and pass `the-strategist` as a stray arg.

## Verification

When onboarding is complete, three questions have clean answers:

1. Does `~/.hermes/profiles/<slug>/distribution.yaml` exist?
2. Does `python3 tools/conformity_check.py` exit 0?
3. Does `git log -1 --name-only` show every file the onboarding produced?

If any answer is no, return to the first failing step and rerun from there.