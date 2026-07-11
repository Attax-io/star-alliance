# evolution/ — kill-switch directory only

The evolution engine (engine.py, verdict.py, signals.py, reflect.py,
scoreboard.py, stale_scan.py, absorb.py, …) was retired 2026-07-12 in the
Supabase migration (Phase 4). The modules live in
`.retired/2026-07-supabase-migration/evolution/`; its ledger.jsonl is
archived at `data/archive/2026-07-pre-supabase/evolution-ledger.jsonl`.

This directory is KEPT because `.claude/hooks/butler-boundary-gate.py`
uses `evolution/DISARMED` as its engine-wide kill-switch path:

    touch evolution/DISARMED   # disarm the butler-boundary gate
    rm evolution/DISARMED      # re-arm

Reflection is now the manual-trigger `guild-reflection` skill v2, which
reads the guild.* views in Supabase and writes guild.findings rows.
