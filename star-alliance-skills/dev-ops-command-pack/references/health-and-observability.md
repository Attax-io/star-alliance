---
type: Document
title: Health, observability, and dev-vs-remote symmetry
description: The health dashboard, log triage, smoke tests, Stop-the-Line conditions, and the canonical local/remote naming.
timestamp: 2026-06-28T00:00:00Z
---

# Health, observability, and dev-vs-remote symmetry

Source: SAW `.claude/commands/` — remote-health, remote-logs, remote-status, deploy-dev,
dev-health, dev-logs, rollback-dev, check-docker-status; `.claude/skills/deployment-sop`.

## remote-health — the proof gate, as a dashboard

Health is the evidence a deploy or rollback succeeded. SAW's health command is a structured
sweep, not a single curl:

1. **Container state** — `docker ps` + `docker inspect … State.Health.Status` for every service.
2. **Resources** — `docker stats` (CPU/mem), `df -h`, `docker system df` (disk is a silent
   killer of deploys — a full disk fails the pull, not the app).
3. **App health endpoint** — `curl -w` capturing HTTP status **and response time**; expects a
   structured `{status, timestamp, uptime, environment}` body.
4. **Dependency liveness** — `pg_isready`, `redis-cli ping → PONG`. The app is only as healthy
   as the datastores it can reach.
5. **Recent errors** — `docker logs --since 5m | grep -i 'error|fatal|exception'`.
6. **Running version** — the revision label, so "healthy" is tied to a known commit.

It then computes a **health score (0–100)** from weighted criteria (containers up +30, health
checks +20, resources <80% +15, no recent errors +15, response <500ms +10, DB/Redis +10) and
classifies **Critical / Warning** alert conditions (any container down, endpoint dead, DB
unreachable, disk >90% = Critical).

The principle: **health is multi-signal and scored, not binary.** "It returns 200" is one of
six signals; a green endpoint over a 92%-full disk is a deploy about to fail.

## smoke tests — the post-deploy contract (deployment-sop)

`deployment-sop` adds the human-flow layer on top of the machine health check. After any
deploy: health endpoint responds, DB connection verified via the health body, **auth flow
works (sign-in/sign-up)**, critical user flows functional, no new errors in logs. Capture the
result as **deployment evidence** (environment, branch, commit, pre/post checkboxes, the raw
`curl` health output) attached to the ticket.

The hard rule: **the health check MUST pass within 5 minutes**, production deploys MUST have
staging validation first, and a rollback plan MUST be documented *before* a production deploy.
The principle: **a deploy without recorded evidence didn't happen** — evidence is what lets a
future rollback know what "good" looked like.

## remote-logs — triage, not just tail

logs is observability with built-in analysis: choose mode (`--follow` to stream a live deploy,
`--tail N` for history), then **classify lines** into errors (`ERROR|FATAL|Exception`,
stack traces), warnings (`WARN|deprecated`), and success markers (`started|listening|ready|
connected`). It emits a per-container summary (status, error count, warning count, last line)
and offers targeted search (`grep -i` for `database`, `Redis`, `POST /api`, …).

The principle: **logs are read through a triage lens** — counts and classifications first,
raw scroll only when needed. "Warnings are expected for dev" is encoded; signal is separated
from noise before a human reads it.

## Dev-vs-remote symmetry — one verb, two targets, collapsed to canonical

SAW originally had parallel `dev-*` and `remote-*` families and **deliberately collapsed them**
(ticket-driven): the `dev-*` set (`deploy-dev`, `dev-health`, `dev-logs`, `rollback-dev`,
`check-docker-status`) became thin **deprecated aliases** pointing at the canonical
`/remote-*` commands. The naming contract:

- `/remote-*` = operations on the remote dev/staging machine (staging-first, then dev)
- `/local-*` = operations on the local machine

Within `remote-status`, the same symmetry shows as **deployment modes**: a `dev` container
(standard ports, hot-reload, source-mounted) and a `staging` container (production-like,
self-contained, stable, won't break on `git pull`) — **staging is the recommended target**
precisely because it is the stable one.

The principle: **collapse parallel verb families to one canonical name with a documented
alias, and keep one consistent local↔remote vocabulary.** Two names for one operation is
drift waiting to happen; the alias preserves muscle memory while the canonical command is the
single source of behavior. (See `lex-theme-flat` discipline elsewhere: intentional aliases are
fine when annotated; accidental duplicates are the defect.)

## Stop-the-Line — the shared safety doctrine

Both skills encode **FORBIDDEN / REQUIRED** pairs that the whole pack inherits:

- **FORBIDDEN**: deploying with failing CI; skipping smoke tests on production; deploying
  untested DB migrations; force-deploying over an active incident; PRs without a ticket
  reference; pushing without rebasing.
- **REQUIRED**: health passes within 5 min; staging validation precedes production; a
  documented rollback plan before production; ticket-referenced commits; independent review
  (a QAS/critic pass) before merge.

The principle, which is the spine of the entire pack: **anyone may stop the line.** A gate
that blocks a bad deploy is doing its job, not getting in the way — the cost of stopping is
always less than the cost of a rollback plus a postmortem.
