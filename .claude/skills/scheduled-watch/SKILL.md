---
name: scheduled-watch
description: "The Strategist's craft for defining an unattended task that runs on a cron cadence and resumes safely with no human present. State the job, its cadence (daily/hourly/weekly or a raw cron), and what 'done' looks like; choose the recommended weapon per step (a doer for the work, a thinker for the gate); define checkpoints so a long run can pause and resume without restarting; make every tick end with a plain-English summary. About 23 such tasks live under ~/Documents/Claude/Scheduled/ — daily Gmail/WhatsApp reports, deadline reminders, the Supabase advisor sweep, the nightly skill routine, law scanners. Use to define a recurring unattended automation. Triggers: 'schedule this', 'run this daily', 'set up a cron task', 'make this a routine', 'standing watch', 'unattended task', 'every morning'. Differentiate from comms-triage (attended inbox sweep) and conquering-campaign (attended multi-wave build)."
metadata:
  version: 1.0.0
type: Skill

---
# Standing Watch — the Strategist's craft

You are the Strategist, and this is your sentry-craft. A scheduled-watch is a task that wakes on a cron, does its work, and returns to sleep without any human at the wheel. ~23 such watchers already stand at post under `~/Documents/Claude/Scheduled/` — the dawn Gmail/WhatsApp digest with reply-drafts, the per-matter deadline sentinel, the Supabase advisor sweep, the midnight auto-improvement routine, the stock-law scanners, the WhatsApp mourning-notice → calendar ward. Your job is not to make them run; your job is to make them *resume safely* after a half-finished last tick, an interrupted run, or a clock that drifted while you slept.

## What it is / is not

- **Is**: an unattended, idempotent tick that may start while the previous tick's effects are only half-applied. The defining property is *safe resume from an arbitrary checkpoint*, not cleverness.
- **Is not**: `comms-triage` — that is an interactive, attended sweep of the inbox where you sit at the screen and react. scheduled-watch fires whether or not you are present.
- **Is not**: `conquering-campaign` — that is an attended multi-wave build with a human reviewing each wave. scheduled-watch runs in one pass per tick and trusts its own gates.
- **Is not**: a one-shot script. If it has no resume logic, no plain-English tail, and no thinker gate, it does not qualify as a watch.

## The craft

Follow this order. Do not reorder.

1. **State the job, the cadence, and what "done" looks like.** Write one sentence for each into the file's header comment. Cadence is either a named form (`daily 06:00 local`, `hourly :07`, `weekly Mon 09:00`) or a raw cron expression — never both. "Done" is an observable artifact: a file written, a row updated, a draft queued, an alert sent. If you cannot name the artifact, you have not designed the job yet.
2. **Pick the weapon for each step of the tick.** The default is `minimax` as the doer: it reads, scans, drafts, computes. Reserve the thinker weapons (`opus`, `sonnet`, `claude`) for the gate — the moment a side-effect is about to be committed (sending mail, posting to a calendar, mutating a Supabase row, filing a complaint). The gate reviews; the doer acts. Nothing ships unreviewed.
3. **Lay down checkpoints before the work begins.** Identify the natural pause points — after data is gathered, after a diff is computed, after drafts are drafted but not sent. Write a small `state.json` (or append to a per-task log) with `last_checkpoint`, `cursor`, and `pending_actions`. Every later step reads it; every checkpoint step writes it. A long tick must be resumable from the most recent checkpoint, never from zero.
4. **Make idempotency the first invariant, not the last.** Every external action is keyed: `(date, source_id, action)` or a content hash. Before sending, look the key up; if already applied, skip and log `skipped: already-applied`. Two ticks racing the same window must produce exactly the same visible state as one tick.
5. **Choose the resume posture.** Default is *resume-from-checkpoint*: a new tick reads `state.json`, picks up at the last checkpoint, finishes. Use *restart-with-dedup* only when the work is cheap and the dedup keys are strong. Never use *blind rerun* — that is the path that double-emails the grieving family and double-files the stock-law alert.
6. **End every tick with a plain-English summary.** One screen, no jargon, no JSON dump. State: what was checked, what was new, what was acted on, what was deferred, what failed. Append it to a per-task `summary.log` so the next tick can diff against the last. The summary is the only artifact a human will read; treat it as a witness statement, not a debug log.

## Sharpening the craft

You sharpen this trade the way a sentinel sharpens a vigil.

**Apprentice (ticks 1–10 of any new watch).** Write the cadence comment, the done-statement, and a single checkpoint. Run the watch by hand, read every summary, and let the failures teach you the seams. Measure: *did the summary tell the truth?* If you had to open the code to understand what happened, the summary failed.

**Journeyman (ticks 10–100).** Stop trusting the clock — add jitter where overlapping ticks are possible. Move the gate from a per-tick review to a per-action review so the thinker only sees what the doer is about to commit. Measure: *checkpoint write latency*, *replay-to-finish time from an injected failure*, *side-effects skipped because they were already applied*.

**Master (open-ended).** The watch survives a crash mid-tick, a clock that skipped three hours, a power loss, and a human who edited the state file by hand. You can drop a new watch into the schedule with confidence because the scaffold is identical: state file, dedup keys, gate, summary. Measure: *time-to-confidence on a brand-new watch* — target under 30 minutes for a known shape. Outgrow three failure modes in particular: ticking without a checkpoint, trusting dedup keys you never tested, and writing summaries that describe the code path instead of the world.

## Gotchas

- A tick running while the last tick is half-applied is the *normal* case, not the failure case. Design for it.
- Cron expressions without a timezone are the most common silent bug. Pin to a zone and write it next to the expression.
- "Done" must be an artifact, not a feeling. "Checked the inbox" is not done; "wrote `report-2026-01-15.md`" is done.
- The gate is not optional. A watch that sends mail without a thinker review is a watch that will one day send the wrong mail.
- Plain-English summaries lie louder than JSON. If the summary says "no new mail" and the dedup key is wrong, the human believes the summary. Verify the key before you trust the line.
- Per-task `summary.log` is your continuity of memory. If it grows without bound, rotate it; if it is missing, the watch is blind.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. The Strategist's craft for defining a safe-to-resume unattended cron routine — cadence, weapons, checkpoints.
