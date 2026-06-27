---
type: Document
timestamp: 2026-06-27T10:27:03Z
---

# Mode: consolidate-code — full recipe

> **Script:** `python3 ~/.claude/skills/cleanup/scripts/consolidate_code.py <scan|classify|surface|extract>` — `extract` is dry-run by default and refuses to auto-merge (byte-compare + a conquering-campaign required for any real consolidation, per §L4).

The code-side sibling of `consolidate` (which is i18n-only). Surfaces — then extracts the
mechanical tier of — duplicate/copy-pasted CODE. The registry `CONSOLIDATION-CANDIDATES.md`
ships pre-seeded with 41 open candidates mined from 146 sessions (2026-05-29); this mode
refreshes it and acts on the safe tier.

**Why a separate mode from `consolidate`.** `consolidate` touches i18n JSON + TSX callsites
via AST resolution. `consolidate-code` touches arbitrary code shapes (components, DB views,
RLS predicates, constants) with different detection + different risk. Conflating them would
overload one script.

#### Step CC1 — Refresh the registry

Re-run the detection greps for each candidate class against the live codebase. The
highest-signal verified-live detections:

```bash
cd lex_council
# Magic-literal duplication (canonical const exists, local copies proliferate)
grep -rln "const PANEL_WIDTH = 332" apps/web --include="*.tsx" --include="*.ts" | wc -l   # C1: was 44
# Config defined in N places
grep -rn "PAGE_SIZE_OPTIONS\s*=" apps/web --include="*.tsx" --include="*.ts"               # C2: 2 files
# Copy-pasted function bodies — SHA-1 the body, flag N>=2 identical
# (the 1d944474 session built a mutation duplicate-detector that escalated
#  name-equality -> SHA-1 body-hash and caught 2 missed exports)
# Off-token hex (pairs with lint mode L13)
grep -rn '#[0-9a-fA-F]\{3,6\}' apps/web/components apps/web/app --include="*.tsx" | grep -c "Token gap"
```

For DB-side candidates, the canonical source is the persisted
`docs/audit-campaigns/2026-05-22_db-wide-consolidation-audit/99-synthesis.md` (74 findings) —
read it; don't re-derive.

#### Step CC2 — Classify each candidate (3 tiers)

| Tier | Criteria | Action |
|---|---|---|
| **T1 extract-now** | Mechanical, ≤ codemod or a few files, zero behavior-parity risk (magic-literal dedup, orphan `git rm`, identical-helper extraction) | Do under autonomous cadence |
| **T2 needs-campaign** | Cross-cutting, >15 sites, OR behavior-parity risk (DB view merge, RLS predicate extraction, button-role standardization) | Surface; open a conquering-campaign |
| **T3 resolved** | Already consolidated | Record so re-mining doesn't re-flag |

#### Step CC3 — Byte-compare before any merge (HARD RULE)

§L2 + §L4 (look-alike-but-different). Before merging N near-duplicate literals/views/predicates
into one helper, **byte-compare them**. If any pair differs, either keep them separate or make
the helper's API preserve every difference (per-arm CASE, parameter, etc.). The RLS-bucket-matrix
trap (4 arrays looked identical, encoded distinct access tiers) is why this is non-negotiable.

The i18n `consolidate` mode already encodes this (only merge when translation matches in every
locale). `consolidate-code` must encode it for code: only merge when all N are byte-identical
OR the difference is captured in the merged API.

#### Step CC4 — Extract T1, surface T2

For T1: extract the shared primitive/const FIRST, then replace each consumer (per the
conquering-campaign extraction-first phase ordering). Run tsc + lint after each extraction.

For T2: write/refresh the registry entry, recommend the conquering-campaign trigger phrase.

#### Step CC5 — Vault log

Delegate to **vault-log-compliance** if code changed. The entry documents: which T1 candidates
were extracted (before/after consumer counts), which T2 were surfaced, registry delta.

**Priority order (from the seeded registry):** C35 ghost-views (CRITICAL, fix now not campaign)
→ C1 PANEL_WIDTH ×44 (codemod) → C38 294 i18n dup groups → C28/C29 legacy `_js` views →
C7/C8/C11 V9-container primitives → C23–C27 DB view/RLS merge → C30 admin_perms god-table (XL).
