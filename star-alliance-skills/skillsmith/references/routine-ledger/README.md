# routine ledger

The durable, committed memory of the `routine` mode (see `../routine-playbook.md`). One file per
run: **`YYYY-MM-DD.md`**. The routine writes it **incrementally as it works** (Stage C) so the run is
watchable, then drops a Run Summary at the top in Stage E. The next run reads recent entries to know
what was proposed-but-deferred and whether past upgrades actually helped — so it converges instead of
re-proposing the same thing.

Logs (`../../routine-logs/*.log`) are the raw CLI transcript and are gitignored. **This ledger is
committed** — it's the memory, not the noise.

## Entry format

```markdown
# routine YYYY-MM-DD

## Run Summary
- Applied: <skill> <verb> → vX.Y.Z [conf N/10] (commit <sha>); …
- Created: <new-skill> [conf N/10] (commit <sha>)
- Deferred: <skill/idea> [conf N/10] — <why not yet>
- Cost: $X.XX · skills STORMed: K · roots: R
- Next-best proposal: <one line>

## Harvest
active: … · frictionful: … · dormant: … · new-skill hints: …

## Per-skill dossiers
### <skill>  (v X.Y.Z, status, mentions N, days-since D)
- STORM scan: <2-line distillation of the 5 persona verdicts>
- Contradiction map: agreed=<high-confidence route> · blind-spot=<gap>
- Synthesis: <ranked upgrade routes>
- Peer review: conf N/10 — <weakest link / bias / missing angle>
- Decision: APPLIED | DEFERRED | NO-OP — <why>

### <new-skill candidate>
- Gap signal: <recurring topic with no skill>
- STORM verdict: worth it? conf N/10 — <reason>
- Decision: CREATED | DEFERRED — <why>
```

Keep dossiers terse — they're a decision trail, not an essay. The detail that matters is the
**confidence score** (it gates execution) and the **decision + why**.
