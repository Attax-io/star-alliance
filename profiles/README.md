# Star Alliance — Specialist Profiles

Each profile directory under `profiles/<agent>/` is a **Hermes profile
distribution** — a self-contained, upgradable profile package that Hermes
installs via `hermes profile install` and updates via `hermes profile update`.

## Structure

```
profiles/<agent>/
  distribution.yaml   # Hermes distribution manifest (name, version, source)
  SOUL.md              # System prompt (loaded by Hermes as the agent's identity)
  config.yaml          # Model and provider settings
  skills.yaml          # Skills manifest (documentation — which skills belong to this profile)
```

## Install (first time)

```bash
# Install all 7 specialist profiles:
python3 tools/publish_profiles.py

# Or install one:
hermes profile install profiles/architect --name the-architect -y
```

This creates `~/.hermes/profiles/<slug>/` with SOUL.md, config.yaml, and
distribution.yaml. Memories, sessions, and auth are created empty on first
install.

## Update (after git pull)

```bash
# Update all 7 profiles from the repo:
python3 tools/publish_profiles.py --update

# Or update one:
hermes profile update the-architect -y
```

Update overwrites distribution-owned files (SOUL.md, config.yaml,
distribution.yaml) from the repo. User data — memories, sessions, auth.json,
.env, skills/ — is **never touched**.

## The 7 specialists

Butler and Strategist stay as project-scoped orchestrators — see `AGENTS.md`
and `agents/` in the repo root. They are not distributions.

| Profile | Slug | Role |
|---|---|---|
| Architect | `the-architect` | Systems design, domain modeling, database architecture |
| Developer | `the-developer` | Writing code, fixing bugs, implementation |
| Designer | `the-designer` | UI/UX design, visual quality, brand kits |
| Interpreter | `the-interpreter` | Legal codex, law translation, multi-locale content |
| Herald | `the-herald` | Marketing, growth, demand generation, content/SEO |
| Merchant | `the-merchant` | Investment analysis, trading strategies, market research |
| Quartermaster | `the-quartermaster` | Skill management, syncing, upgrading, conformance |

Total: 7 specialist distributions + 2 orchestrators (Butler + Strategist) = 9.