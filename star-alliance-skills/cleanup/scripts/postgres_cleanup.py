#!/usr/bin/env python3
"""
postgres_cleanup.py — Supabase / pg health sweep for the /cleanup skill.

Subcommands:
  detect    Read MCP output files (written by Claude before calling this script)
            and produce a unified /tmp/pg_issues.json list.
  classify  Read /tmp/pg_issues.json, classify each as:
              advisory-auto-fix   safe additive migration (missing FK index, etc.)
              advisory-surface    perf/security advisory that Claude should surface
              schema-campaign     needs a full campaign (column drop, RLS rewrite, etc.)
              noise               known benign pattern
            Output: /tmp/pg_issues_classified.json
  apply     Read /tmp/pg_issues_classified.json, generate SQL for advisory-auto-fix
            items and write /tmp/pg_apply.sql for Claude to pass to apply_migration.
  verify    Re-read MCP output files after fixes; report delta vs /tmp/pg_issues.json.

Expected MCP output files (Claude writes these before calling detect):
  /tmp/pg_advisors.json   — output of get_advisors MCP call (list of advisor objects)
  /tmp/pg_health.json     — output of execute_sql health queries (list of result objects)
"""

import json
import sys
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# ── constants ──────────────────────────────────────────────────────────────

ADVISORS_FILE = "/tmp/pg_advisors.json"
HEALTH_FILE   = "/tmp/pg_health.json"
ISSUES_FILE   = "/tmp/pg_issues.json"
CLASSIFIED_FILE = "/tmp/pg_issues_classified.json"
APPLY_SQL_FILE  = "/tmp/pg_apply.sql"


def default_root() -> Path:
    """Locate the lex_council repo root resiliently.

    Tries the canonical install path first, then walks up from this file and
    from cwd looking for a dir containing apps/web/config/app.config.ts.
    Mirrors the default_root() helper in scripts/i18n_cleanup.py.
    """
    env = os.environ.get("LEX_ROOT")
    if env:
        return Path(env).resolve()
    canonical = Path(
        os.path.expanduser("~/Documents/Claude/Projects/Lex Council App/lex_council")
    )
    if (canonical / "apps" / "web" / "config" / "app.config.ts").is_file():
        return canonical
    # walk up from __file__ and from cwd looking for the config marker
    starts = [Path(__file__).resolve(), Path.cwd().resolve()]
    for start in starts:
        for parent in [start, *start.parents]:
            if (parent / "apps" / "web" / "config" / "app.config.ts").is_file():
                return parent
            cand = parent / "lex_council"
            if (cand / "apps" / "web" / "config" / "app.config.ts").is_file():
                return cand
    raise SystemExit(
        "Could not locate lex_council root. Pass LEX_ROOT env var."
    )


# ── L9 / L10 / L15 / L17 mandatory health queries ────────────────────────────
# These are PRINTED by the detect phase so Claude runs them via the MCP
# execute_sql tool and appends each result to /tmp/pg_health.json as an object
# {"query_type": "<key>", "rows": [...]}. The classify phase tiers them via
# HEALTH_RESULT_PATTERNS below. SQL lifted verbatim from SKILL.md lessons.

# L9 — views missing security_invoker=true (silent definer-mode RLS bypass)
SQL_L9_SECURITY_INVOKER = """\
-- L9: public views missing security_invoker=true (silent RLS bypass)
-- Save result to /tmp/pg_health.json as {"query_type": "views_missing_security_invoker", "rows": [...]}
SELECT c.relname, c.reloptions
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'v'
AND (c.reloptions IS NULL OR NOT 'security_invoker=true' = ANY(c.reloptions));
-- Expect 0 rows. Any row = silent regression → schema-campaign."""

# L15 — stale function bodies referencing pre-v2 names (rename drift)
SQL_L15_STALE_PROSRC = """\
-- L15: function bodies (public + private) still referencing pre-v2 names
-- Save result to /tmp/pg_health.json as {"query_type": "stale_function_bodies", "rows": [...]}
SELECT p.proname AS fn_name,
       n.nspname AS schema,
       LEFT(p.prosrc, 300) AS body_preview
FROM pg_proc p
JOIN pg_namespace n ON n.oid = p.pronamespace
WHERE n.nspname IN ('public', 'private')
AND (
    p.prosrc ILIKE '%council_members%'
    OR p.prosrc ILIKE '%ppl%'
    OR p.prosrc ILIKE '%fd_access%'
    OR p.prosrc ILIKE '%cm_hr%'
    OR p.prosrc ILIKE '%admin_perms%'
    OR p.prosrc ILIKE '%whbd_%'
    OR p.prosrc ILIKE '%atnd_%'
    OR p.prosrc ILIKE '%n_kinds%'
)
ORDER BY p.proname;
-- Expect 0 rows. Each row = stale body needing a campaign fix → schema-campaign."""

# L10 — unconditionally-permissive RLS policies (qual='true') — advisor misses these
SQL_L10_PERMISSIVE_POLICIES = """\
-- L10: unconditionally-permissive RLS policies (qual='true' or NULL)
-- Save result to /tmp/pg_health.json as {"query_type": "permissive_rls_policies", "rows": [...]}
SELECT schemaname, tablename, policyname, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
AND (qual = 'true' OR qual IS NULL)
ORDER BY tablename, policyname;
-- Any qual='true' row = schema-campaign (not safe to auto-fix without intent)."""

# L17 — dead service_role policies + RLS-enabled-no-policy (advisor partial)
SQL_L17_DEAD_SERVICE_ROLE = """\
-- L17: dead auth.role()='service_role' policies (service_role bypasses RLS — never evaluated)
-- Save result to /tmp/pg_health.json as {"query_type": "dead_service_role_policies", "rows": [...]}
SELECT schemaname, tablename, policyname, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
AND (qual ILIKE '%auth.role()%service_role%' OR qual ILIKE '%''service_role''%')
ORDER BY tablename, policyname;
-- Each row = dead policy → schema-campaign (batch DROP in dedicated migration)."""

SQL_L17_RLS_NO_POLICY = """\
-- L17: tables with RLS enabled but zero policies (stale backup/archive tables)
-- Save result to /tmp/pg_health.json as {"query_type": "rls_enabled_no_policy", "rows": [...]}
SELECT c.relname AS table_name
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relrowsecurity = true
AND NOT EXISTS (
    SELECT 1 FROM pg_policies p
    WHERE p.schemaname = 'public' AND p.tablename = c.relname
)
ORDER BY c.relname;
-- Each row = RLS enabled, no policy → schema-campaign (DROP or add blanket policy)."""

# Ordered list of the mandatory health queries the detect phase prints.
MANDATORY_HEALTH_QUERIES = [
    ("L9  security_invoker",        SQL_L9_SECURITY_INVOKER),
    ("L15 stale prosrc",           SQL_L15_STALE_PROSRC),
    ("L10 permissive RLS",         SQL_L10_PERMISSIVE_POLICIES),
    ("L17 dead service_role",      SQL_L17_DEAD_SERVICE_ROLE),
    ("L17 rls_enabled_no_policy",  SQL_L17_RLS_NO_POLICY),
]

# Advisor names that are safe to auto-fix (additive only, no destructive DDL)
SAFE_AUTO_FIX_ADVISORS = {
    "no_primary_key",          # add PK — only if table is empty or small
    "fk_no_index",             # add index on FK column — always safe
    "missing_index_on_fk",     # same as above, different advisor name
    "unindexed_foreign_key",   # same pattern
    "index_types",             # suggest BRIN/HASH when btree used — surface only
}

# Advisor names that always need a campaign (destructive or complex)
CAMPAIGN_REQUIRED_ADVISORS = {
    "unused_index",            # DROP INDEX — destructive, needs validation
    "rls_disabled",            # enable RLS — needs policy audit
    "no_rls",                  # same
    "security_definer_view",   # views using SECURITY DEFINER — architecture change
    "function_search_path_mutable",  # fix search_path — mass update
    "auth_leaked_password",    # auth config change
    "multiple_permissive_policies",  # RLS rewrite — architecture
}

# Health query result keys that map to issue types
HEALTH_RESULT_PATTERNS = {
    "missing_fk_indexes": "advisory-auto-fix",
    "tables_without_rls": "schema-campaign",
    "high_dead_tuple_tables": "advisory-surface",
    "bloated_tables": "advisory-surface",
    "long_running_queries": "noise",
    # ── L9 / L10 / L15 / L17 mandatory health-query result keys ──
    # Any non-empty result here is a silent-failure class → full campaign.
    "views_missing_security_invoker": "schema-campaign",  # L9  — silent RLS bypass
    "stale_function_bodies":          "schema-campaign",  # L15 — pre-v2 rename drift
    "permissive_rls_policies":        "schema-campaign",  # L10 — qual='true' open policies
    "dead_service_role_policies":     "schema-campaign",  # L17 — dead service_role policies
    "rls_enabled_no_policy":          "schema-campaign",  # L17 — RLS on, zero policies
}


# ── helpers ────────────────────────────────────────────────────────────────

def load_json_file(path, default=None):
    if not os.path.exists(path):
        return default or []
    try:
        return json.load(open(path))
    except json.JSONDecodeError as e:
        print(f"  [WARN] Could not parse {path}: {e}", file=sys.stderr)
        return default or []


def save_json_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ── subcommands ────────────────────────────────────────────────────────────

def print_mandatory_health_queries():
    """Print the L9/L10/L15/L17 health queries for Claude to run via MCP execute_sql.

    The script has no DB access. Claude runs each query, then appends the result
    to /tmp/pg_health.json as {"query_type": "<key>", "rows": [...]} so the
    classify phase can tier it (all → schema-campaign on any non-empty result).
    """
    print("\n" + "=" * 72)
    print("MANDATORY HEALTH QUERIES — run each via MCP execute_sql, append results")
    print(f"to {HEALTH_FILE} as a list of {{\"query_type\": ..., \"rows\": [...]}} objects.")
    print("Advisor checks MISS every one of these (silent-failure classes).")
    print("=" * 72)
    for label, sql in MANDATORY_HEALTH_QUERIES:
        print(f"\n--- [{label}] ---")
        print(sql)
    print("\n" + "=" * 72 + "\n")


def cmd_detect():
    """Combine advisor + health results into a single issues list."""
    print("postgres_cleanup.py detect — reading MCP output files...")

    # Always emit the mandatory health queries so Claude runs them via MCP.
    # (Baked in from SKILL.md L9/L10/L15/L17 — no longer prose-only.)
    print_mandatory_health_queries()

    issues = []

    # ── advisors ──
    advisors = load_json_file(ADVISORS_FILE)
    if not advisors:
        print(f"  [INFO] {ADVISORS_FILE} not found or empty. "
              "Run get_advisors MCP call and save output there first.")
    else:
        print(f"  Found {len(advisors)} advisor entries")
        for adv in advisors:
            # Supabase advisor objects have: name, title, description, remediation, metadata
            name = adv.get("name") or adv.get("type") or "unknown"
            title = adv.get("title") or name
            desc = adv.get("description") or ""
            remediation = adv.get("remediation") or ""
            metadata = adv.get("metadata") or {}

            issue = {
                "id": f"adv_{name}_{len(issues)}",
                "source": "advisor",
                "advisor_name": name,
                "title": title,
                "description": desc,
                "remediation": remediation,
                "metadata": metadata,
                "raw": adv,
            }
            issues.append(issue)

    # ── health query results ──
    health = load_json_file(HEALTH_FILE)
    if not health:
        print(f"  [INFO] {HEALTH_FILE} not found or empty. "
              "Run execute_sql health queries and save output there first.")
    else:
        print(f"  Found {len(health)} health result entries")
        for item in health:
            # Health results are freeform SQL rows; key pattern = what was queried
            qtype = item.get("query_type") or item.get("type") or "unknown"
            rows = item.get("rows") or item.get("results") or []
            if not rows:
                continue
            issue = {
                "id": f"health_{qtype}_{len(issues)}",
                "source": "health",
                "query_type": qtype,
                "row_count": len(rows),
                "sample_rows": rows[:5],
                "raw": item,
            }
            issues.append(issue)

    save_json_file(ISSUES_FILE, issues)
    print(f"  Wrote {len(issues)} issues → {ISSUES_FILE}")
    return issues


def cmd_classify():
    """Classify each issue into a fix tier."""
    issues = load_json_file(ISSUES_FILE)
    if not issues:
        print(f"  [ERROR] {ISSUES_FILE} empty. Run detect first.")
        sys.exit(1)

    classified = []
    counts = {"advisory-auto-fix": 0, "advisory-surface": 0,
              "schema-campaign": 0, "noise": 0}

    for issue in issues:
        tier = "advisory-surface"  # default

        if issue["source"] == "advisor":
            name = issue.get("advisor_name", "").lower()
            if any(p in name for p in ("fk_no_index", "unindexed_fk", "missing_index",
                                        "fk_index", "foreign_key_index")):
                tier = "advisory-auto-fix"
            elif name in CAMPAIGN_REQUIRED_ADVISORS:
                tier = "schema-campaign"
            elif name in {"index_types", "bloat", "dead_tuples", "cache_hit"}:
                tier = "advisory-surface"
            elif "password" in name or "leaked" in name or "auth" in name:
                tier = "schema-campaign"
            elif name in {"no_primary_key"}:
                # Only auto-fix if metadata says table is empty
                row_count = issue.get("metadata", {}).get("row_count", 999)
                tier = "advisory-auto-fix" if row_count == 0 else "schema-campaign"
            else:
                tier = "advisory-surface"

        elif issue["source"] == "health":
            qtype = issue.get("query_type", "")
            tier = HEALTH_RESULT_PATTERNS.get(qtype, "advisory-surface")

        issue["tier"] = tier
        classified.append(issue)
        counts[tier] = counts.get(tier, 0) + 1

    save_json_file(CLASSIFIED_FILE, classified)

    print("\nClassification summary:")
    print(f"  advisory-auto-fix  : {counts['advisory-auto-fix']}  (will generate SQL)")
    print(f"  advisory-surface   : {counts['advisory-surface']}   (surfaced to user)")
    print(f"  schema-campaign    : {counts['schema-campaign']}     (flag for campaign)")
    print(f"  noise              : {counts['noise']}               (suppressed)")
    print(f"\nWrote → {CLASSIFIED_FILE}")
    return classified


def cmd_apply():
    """Generate migration SQL for advisory-auto-fix items."""
    classified = load_json_file(CLASSIFIED_FILE)
    if not classified:
        print(f"  [ERROR] {CLASSIFIED_FILE} empty. Run classify first.")
        sys.exit(1)

    auto_fix = [i for i in classified if i["tier"] == "advisory-auto-fix"]
    if not auto_fix:
        print("  No advisory-auto-fix items found. Nothing to apply.")
        return []

    sql_blocks = [
        "-- postgres_cleanup.py apply — generated auto-fix SQL",
        f"-- Generated: {datetime.now(timezone.utc).isoformat()}",
        "-- Apply via: apply_migration MCP tool with project_id bqgrpnsvplvicnmzxwkm",
        "-- REVIEW before applying: verify each CREATE INDEX is appropriate",
        "",
    ]

    applied = []
    for issue in auto_fix:
        name = issue.get("advisor_name", "")
        meta = issue.get("metadata", {})

        if any(p in name.lower() for p in ("fk_no_index", "unindexed", "missing_index", "fk_index")):
            # Standard FK index fix
            table = meta.get("table") or meta.get("table_name") or "UNKNOWN_TABLE"
            col = meta.get("column") or meta.get("column_name") or "UNKNOWN_COLUMN"
            schema = meta.get("schema") or "public"
            idx_name = f"{table}_{col}_idx"

            sql = (
                f"-- Fix: missing FK index on {schema}.{table}.{col}\n"
                f"CREATE INDEX IF NOT EXISTS {idx_name}\n"
                f"    ON {schema}.{table} ({col});\n"
            )
            sql_blocks.append(sql)
            issue["applied_sql"] = sql
            applied.append(issue)

        elif name == "no_primary_key":
            table = meta.get("table") or "UNKNOWN_TABLE"
            sql = (
                f"-- Fix: add PK to {table} — REVIEW CAREFULLY\n"
                f"-- ALTER TABLE public.{table} ADD COLUMN id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY;\n"
                f"-- (Commented out — verify table schema before applying)\n"
            )
            sql_blocks.append(sql)
            issue["applied_sql"] = sql
            applied.append(issue)

    full_sql = "\n".join(sql_blocks)
    with open(APPLY_SQL_FILE, "w") as f:
        f.write(full_sql)

    print(f"  Generated SQL for {len(applied)} auto-fix items → {APPLY_SQL_FILE}")
    print("  Pass this SQL to: apply_migration MCP with project_id bqgrpnsvplvicnmzxwkm")
    print("  Then run: postgres_cleanup.py verify")

    # Update classified file with applied_sql
    save_json_file(CLASSIFIED_FILE, classified)
    return applied


def cmd_verify():
    """Re-read MCP output files after fixes and report delta."""
    before = load_json_file(ISSUES_FILE)
    before_count = len(before)

    if not os.path.exists(ADVISORS_FILE):
        print("  [WARN] No fresh advisor file found. "
              "Re-run get_advisors MCP and save output to /tmp/pg_advisors.json, "
              "then call detect again to get /tmp/pg_issues_after.json")
        return

    # Re-detect into a temp file
    import shutil
    tmp_issues = ISSUES_FILE.replace(".json", "_before.json")
    if os.path.exists(ISSUES_FILE):
        shutil.copy(ISSUES_FILE, tmp_issues)

    after = cmd_detect()
    after_count = len(after)

    delta = before_count - after_count
    print(f"\nVerification delta:")
    print(f"  Before : {before_count} issues")
    print(f"  After  : {after_count} issues")
    print(f"  Delta  : {'+' if delta >= 0 else ''}{delta} (negative = new issues found)")

    # Tier breakdown
    classified_before = load_json_file(CLASSIFIED_FILE)
    campaign_items = [i for i in classified_before if i.get("tier") == "schema-campaign"]
    if campaign_items:
        print(f"\n  {len(campaign_items)} schema-campaign items need a migration campaign:")
        for item in campaign_items[:10]:
            print(f"    - [{item.get('advisor_name','?')}] {item.get('title','')}")
        if len(campaign_items) > 10:
            print(f"    ... and {len(campaign_items)-10} more — see {CLASSIFIED_FILE}")


def cmd_surface():
    """Print a human-readable triage list for Claude to present to the user."""
    classified = load_json_file(CLASSIFIED_FILE)
    if not classified:
        print(f"  [ERROR] {CLASSIFIED_FILE} empty. Run classify first.")
        sys.exit(1)

    tiers = {
        "advisory-auto-fix": [],
        "advisory-surface": [],
        "schema-campaign": [],
        "noise": [],
    }
    for issue in classified:
        tier = issue.get("tier", "advisory-surface")
        tiers[tier].append(issue)

    print("\n" + "="*60)
    print("POSTGRES CLEANUP TRIAGE")
    print("="*60)

    if tiers["advisory-auto-fix"]:
        print(f"\n✓ AUTO-FIXABLE ({len(tiers['advisory-auto-fix'])} items):")
        for i in tiers["advisory-auto-fix"]:
            print(f"  [{i.get('advisor_name','?')}] {i.get('title','')}")

    if tiers["advisory-surface"]:
        print(f"\n⚠ SURFACE (perf/security advisories, {len(tiers['advisory-surface'])} items):")
        for i in tiers["advisory-surface"]:
            print(f"  [{i.get('advisor_name','?')}] {i.get('title','')}")

    if tiers["schema-campaign"]:
        print(f"\n🚩 NEEDS CAMPAIGN ({len(tiers['schema-campaign'])} items):")
        for i in tiers["schema-campaign"]:
            print(f"  [{i.get('advisor_name','?')}] {i.get('title','')}")
            rem = i.get("remediation","")
            if rem:
                print(f"      Remediation: {rem[:120]}")

    if tiers["noise"]:
        print(f"\n  noise: {len(tiers['noise'])} suppressed")

    print("="*60)


# ── main ───────────────────────────────────────────────────────────────────

COMMANDS = {
    "detect": cmd_detect,
    "classify": cmd_classify,
    "apply": cmd_apply,
    "verify": cmd_verify,
    "surface": cmd_surface,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python3 postgres_cleanup.py <{'|'.join(COMMANDS)}>")
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
