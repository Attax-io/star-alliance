---
type: Document
title: "Mode: deploy-member"
description: Deploy a guild member + its skills into another project, tiered.
---

# Mode: deploy-member — install a member (+ skills) into a target project

Goal: take a working `star-alliance` member and stand it up inside **another project** so that
project gets the member agent, its skills, and (optionally) the guild's env + hooks + lite workflows.
This is the "Star Alliance is nearly finished — how do we *use* it elsewhere?" path (the recurring
2026-06-27 ask). The mechanical work is one script; this playbook is when/how to drive it and what
each tier actually lands.

## The one command

```sh
bash "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/install.sh" <member> <target-project-path> --tier 1|2|3
```

`install.sh` resolves `SA_ROOT` from its own location, reads the member file from
`star-alliance-members/<member>.md`, and copies into the **target** project's `.claude/`. It refuses
an unknown member (prints the roster) or a missing target dir.

## The three tiers (each is a superset of the one below)

| Tier | Lands in the target | Use when |
|---|---|---|
| **1 — skills only** (default) | rsyncs **this member's skills** into `<target>/.claude/skills/` | the target just needs the member's *craft* (the skills), driven by whatever agent is already there. |
| **2 — + member + env** | Tier 1 **+** the member agent file → `<target>/.claude/agents/<member>.md` **+** `STAR_ALLIANCE_ROOT` merged into `<target>/.claude/settings.json` | the target should be able to *summon the member as an agent* and reach the arsenal CLIs (`summon.py`, `minimax.py`). |
| **3 — + hooks + workflows** | Tier 2 **+** every `.claude/hooks/*.py|*.sh` copied **+** hook wiring merged into the target `settings.json` **+** `workflows-lite.json` → `<target>/workflows.json` | the target should run the **full guild conduct** — routing gate, workflow-gate, high-alert banners, the lite star-map. |

**Which member's skills?** Tier 1/2 ships exactly the skills in that member's `skills:` frontmatter
loadout — *not* the whole library. Deploy `the-developer` and you get its craft skills; deploy
`the-quartermaster` and you get skillsmith + okf + the housekeeping kit. To seed a project with more
than one member's craft, run `install.sh` once per member into the same target (tiers compose; later
runs merge, they don't clobber prior members).

## Manual steps the script can't do (it prints these)

- **Tier 2:** add to the target's `CLAUDE.md`:
  `Arsenal tools path: $STAR_ALLIANCE_ROOT/star-alliance-arsenal/`.
- **Tier 3:** copy the relevant `CLAUDE.md` sections (reading discipline, guild conduct) into the
  target `CLAUDE.md`. If `workflows-lite.json` is absent the script says so — copy the repo
  `workflows.json` by hand.

## Relationship to `project-start`

`deploy-member` is the **producer** side (push a member out of this repo); the `project-start` skill is
the **consumer** side (a fresh project bootstrapping itself). When the user says *"set up star alliance
in project X"* and X is empty, run `deploy-member` at the tier they need; when X already has its own
conventions, prefer `project-start` so the guild folds into the existing project rather than stamping
over it.

## The deploy ledger (data source for member-leveling Wave 6)

Every `install.sh` run appends one line to
`star-alliance-skills/skillsmith/references/deploy-ledger.md`
(`<date> · <member> · tier <n> · <target>`). This is the durable record of **where each member is
actually deployed** — the usage/deployment-frequency axis that member-leveling Wave 6 consumes (levels
meter *capability*; the deploy ledger meters *reach*). Don't hand-prune it; it is append-only history.

## Conformity-close

`deploy-member` writes into a **foreign** project, not the `star-alliance` repo, so it does **not**
trigger the repo conformity sweep (nothing in the guild repo changed except the appended deploy-ledger
line). If a deploy surfaces a member/skill defect *in the source repo*, fix that under
`upgrade`/`sync` and close per Invariant #8 there. Commit the deploy-ledger append with a
`deploy: <member> → <target> (tier N)` message; no push needed for a local-only deploy.
