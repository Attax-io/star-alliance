---
type: Document
title: Second Mac Setup
description: Day-1 card for bringing a new Mac into the Star Alliance guild.
---

# Second Mac Setup — Day 1

Plain-English card for getting a new Mac talking to the guild. Total time: about
five minutes. Everything the guild knows lives in a shared online database
(Supabase); this Mac just needs the repo, one secret, and a pull.

## 1. Get the repo

```sh
git clone <your star-alliance remote> ~/Documents/Claude/Projects/star-alliance
cd ~/Documents/Claude/Projects/star-alliance
# (already cloned? just: git pull)
```

## 2. Connect this Mac to the guild database

```sh
python3 bin/sa init
```

It will ask you to paste the **Legacy JWT Secret**. Find it here:

Supabase dashboard → project **Lex Council Pro** → **Settings** → **JWT Keys** →
the **"Legacy JWT Secret"** tab → copy the secret.

Paste it once. `sa init` uses it to mint this Mac's own guild credential, stores
that credential in **this Mac's Keychain** (service `star-alliance-guild`), and
**discards the secret** — it is never written to disk. You won't need it again on
this machine.

## 3. Pull the guild onto this Mac

```sh
python3 bin/sa pull
```

This materializes the skills into `~/.claude/skills` (and the repo dirs) and the
member cards into `.claude/agents/` — the files Claude Code actually loads.

## 4. Check the connection

```sh
python3 bin/sa doctor
```

All green = done. This Mac is now a registered guild device.

## Troubleshooting

| Symptom | What it means | Fix |
|---|---|---|
| **401 Unauthorized** | The publishable key is missing or wrong | Check `~/.config/star-alliance/config.json` holds the project's publishable key (Supabase dashboard → Settings → API Keys). Re-run `sa doctor`. |
| **Amber warning about `consumers.json`** | Harmless — this Mac just hasn't registered consumer repos yet | Ignore it, or run `sa pull` inside a consumer repo (e.g. Lex Council) to register it. |
| **Keychain prompt / "item not found"** | The guild credential isn't in this Mac's Keychain yet | Re-run `python3 bin/sa init` and paste the Legacy JWT Secret again. |
| **Offline / can't reach the database** | Files keep working — the repo and `~/.claude/skills` are the read cache | Work normally; telemetry queues in `.claude/state/outbox.jsonl` and ships on the next session start. |

## What NOT to do

- Don't hand-edit `.claude/agents/*.md` — those files are materialized by `sa pull`
  and the next pull overwrites them. Edit `star-alliance-members/*.md`, then `sa push`.
- Don't store the Legacy JWT Secret anywhere. Paste it into `sa init`, then forget it.
