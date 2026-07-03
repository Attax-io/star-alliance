---
name: new-member-onboarding
description: "The exact checklist to run whenever a new guild member is recruited. Profiles must be created, installed, art-forged, and committed — in that order. Use when: 'onboard new member', 'recruit a member', 'add a new profile', 'new the-slug-style-name (such as the-architect)', 'create profiles for a new member'. Pairs with skillsmith, workflow-forge, dual-model-review."
metadata:
  version: 1.0.1
type: Skill
---

# New member onboarding — the Quartermaster's checklist

When a new guild member is recruited, six steps must run in order. Skip a step
and the member exists in `star-alliance-members/` but is missing from the
runtime: no Claude agent card, no art tile, no conformity pass, no commit. This
skill is the source of truth for the sequence.

Every member is a Claude model. Substitute `<slug>` with the member's short slug
throughout (e.g. `steward`, `strategist`). The full member id is `the-<slug>`.

## 1. Member file

Create `star-alliance-members/the-<slug>.md`.

Use an existing member file (e.g. `star-alliance-members/the-steward.md`) as
the template. Required frontmatter fields:

- `name: the-<slug>`
- `description:` — one-line plain-English summary of when to deploy this member
- `model:` — the member's Claude model, one of the three in
  `star-alliance-arsenal/models.json` (`opus`, `sonnet`, or `haiku`). The
  Architect is `opus`, the Quartermaster is `haiku`, every other member is
  `sonnet`.
- `tools: [Read, Edit, Write, Bash]`
- `skills:` — list of skill slugs the member invokes
- `type: Member`

Body: first-person soul ("You are **the <Slug>**, …"), expertise bullets, the
Arsenal section, Skill Drills table, How you work, What you don't do.

## 2. Claude-side agent file

Generate the Claude Code subagent card — the runtime form a member takes when it
is spawned as a subagent:

```
python3 guild/install_agents.py
```

This writes `.claude/agents/the-<slug>.md` from the member file (the Butler is a
Persona and gets no agent card). NEVER hand-edit `.claude/agents/` — it is
generated. If the generator only enumerates the original roster, add `<slug>` to
its source list first, then rerun.

## 3. Art tile

Forge a member portrait and thumb via the arsenal image generator, then save
to the two art directories:

```
python3 star-alliance-arsenal/imagegen.py
```

Save outputs to:

- `art/member-art/the-<slug>.png`
- `art/member-art-thumb/the-<slug>.png`

Match the dimensions and style of the existing tiles in those directories.

## 4. Rebuild guild data

```
python3 build.py
```

This regenerates the dashboard data, member registry, and any other
derived artifacts that depend on the member catalog. Without this step the
new member is invisible to the dashboard.

## 5. Conformity check

```
python3 tools/conformity_check.py
```

Confirm zero drift. Pay attention to the `REG`/`BR` tags — they verify the
member's `model:` is one of the three Claude models in
`star-alliance-arsenal/models.json` (`opus`/`sonnet`/`haiku`) and that the
generated `.claude/agents/the-<slug>.md` matches the source member file. If a
tag fails on the new member, the agent card is stale — rerun step 2
(`python3 guild/install_agents.py`).

## 6. Commit

Stage every file the onboarding produced — the member file, the generated Claude
agent card, the two art tiles, and any regenerated guild-data files. One commit,
one message naming the new member.

```
git add star-alliance-members/the-<slug>.md \
        .claude/agents/the-<slug>.md \
        art/member-art/the-<slug>.png \
        art/member-art-thumb/the-<slug>.png \
        guild-data.json guild-data.js dashboard.css
git commit -m "Onboard the-<slug>: member + agent card + art"
```

If `guild/install_agents.py` was edited to add the slug to its roster list,
include that diff in the same commit.

## Pitfalls

- **Never hand-edit `.claude/agents/`.** It is generated from
  `star-alliance-members/` by `guild/install_agents.py`. Edit the member file,
  then regenerate — a hand-edit is silently overwritten by the next build.
- **`model:` must be a Claude model.** Only `opus`, `sonnet`, or `haiku` (the
  three in `models.json`). Conformity fails the build if a member names anything
  else. Architect = opus, Quartermaster = haiku, everyone else = sonnet.
- **Step 4 must precede step 5.** `conformity_check.py` reads the rebuilt
  `guild-data.json`. Running conformity against a stale build will report
  phantom drift on the new member.
- **Stage only what onboarding produced.** Do not scoop in unrelated
  experiments from the working tree. The diff is the diff the onboarding
  earned.
- **The Butler gets no agent card.** He is a Persona (the live session), never a
  spawnable subagent — `install_agents.py` correctly skips him.

## Verification

When onboarding is complete, three questions have clean answers:

1. Does `.claude/agents/the-<slug>.md` exist and match the member file?
2. Does `python3 tools/conformity_check.py` exit 0?
3. Does `git log -1 --name-only` show every file the onboarding produced?

If any answer is no, return to the first failing step and rerun from there.