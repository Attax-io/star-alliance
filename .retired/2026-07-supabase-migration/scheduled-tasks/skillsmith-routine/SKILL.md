---
name: skillsmith-routine
description: Daily autonomous skillsmith routine — STORM-mine the Star Alliance skills, apply ≥8/10 upgrades, commit + push.
---

Run the Star Alliance skillsmith `routine` mode now, fully autonomously, end to end.

Repo (canonical, resolve via $HOME — do NOT hardcode a username):
  REPO="$HOME/Documents/Claude/Projects/star-alliance"
First verify it exists and is the right remote:
  [ -d "$REPO/.git" ] || gh repo clone Attax-io/star-alliance "$REPO"
  git -C "$REPO" remote get-url origin   # expect .../Attax-io/star-alliance.git
Then cd into it. All skill/script paths live under `star-alliance-skills/` after the 2026-06 restructure — e.g. the harvester is `star-alliance-skills/skillsmith/scripts/routine_scan.py`, playbooks are `star-alliance-skills/skillsmith/references/`.

Invoke the skillsmith skill and follow `star-alliance-skills/skillsmith/references/routine-playbook.md` exactly:
- Stage A — harvest: `python3 star-alliance-skills/skillsmith/scripts/routine_scan.py --days 14 --out star-alliance-skills/skillsmith/routine-logs/scan-$(date +%F).json` (read-only).
- Stage B — STORM research per active/frictionful skill (`references/storm-method.md`); skip the converged set if the SKILL.md corpus is unchanged since the last run (check `git log`), per the convergence lesson. Default doer for sub-work is MiniMax (`python3 ~/.config/minimax/mm.py`, key at ~/.config/minimax/m3.key) per the repo CLAUDE.md.
- Stage C — write today's ledger entry `star-alliance-skills/skillsmith/references/routine-ledger/$(date +%F).md` incrementally as you go.
- Stage D — execute every finding with peer-review confidence ≥ 8/10 that clears the §R4 guards (upgrade existing skills, create genuinely new ones, fix bugs — skillsmith itself last per §R6; respect the 3-day cooldown; forks/externals edited fork-aware, never blind).
- Stage E — CONFORMITY-CLOSE (Invariant #8): only run `python3 build.py` if a skill actually changed this run (it rebuilds guild-data; running it on a no-op only churns the dashboard and risks sweeping in a concurrent actor's in-flight work). Always run `python3 conformity_check.py` read-only — it must report FULL CONFORMITY before any commit. Commit each applied change separately with message `skillsmith routine <date>: <verb> <skill> — <one-line> [conf N/10]`, stage only the files you changed by explicit path (never `git add -A`), then `git push origin main`. Write the Run Summary at the top of today's ledger entry.

You are unattended. Do not ask questions; apply the autonomy contract as written (fully autonomous, ≥8/10 gate, everything a revertible commit on main — never force-push or rebase). Respect the per-run budget §R5 (top ~3 actions, ~8 skills STORMed). If you cannot finish a stage, write what you learned to the ledger and stop cleanly. This runs once daily — do not re-run yourself.