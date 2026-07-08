#!/usr/bin/env python3
"""
docs_cleanup.py — deterministic docs-hygiene detector for the /cleanup skill.

Detect-only: this tool NEVER modifies a docs file. DB/count probes are NOT its
job — those run via MCP by Claude. The script does the file-side checks only.

Subcommands:
  frontmatter     Parse YAML frontmatter of the 8 planet hubs. Flag stale
                  audit/sync dates (>14d), app_version drift on Vault Core vs
                  app.config.ts, and any counts: keys (→ needs_mcp_probe).
                  Output: /tmp/docs_frontmatter.json
  wikilinks       Find every [[X]] across DOCS; classify each target as
                  broken / code-link / archived-pointer / resolved. `code-link`
                  = a [[file.ts]] / [[apps/.../x.tsx]] cross-ref into the app
                  source tree (not doc-rot); `broken` is now only genuine
                  missing-.md doc links. Output (broken + code-link + archived):
                  /tmp/docs_wikilinks.json
  orphans         vault-log files not referenced in vault-logs/INDEX.md.
                  Output: /tmp/docs_orphans.json
  retired-names   Grep DOCS for a registry of retired v2-schema names + retired
                  primitives (word-boundary). Human triage only — never fixed.
                  Output: /tmp/docs_retired_names.json
  artifacts       Grep DOCS for botched global-replace artifacts
                  (`x` (was `x`) / `x` (v2; was `x`)). Output:
                  /tmp/docs_artifacts.json
  campaign-drift  build-campaigns/*/00-campaign-plan.md marked in-progress that
                  already have a matching vault-log. Output:
                  /tmp/docs_campaign_drift.json
  all             Run every check, write combined human findings →
                  /tmp/docs_cleanup_findings.md, print a summary table.
"""

import json
import sys
import os
import subprocess
import re
import datetime
from collections import defaultdict

# ── constants ──────────────────────────────────────────────────────────────

_FALLBACK_LEX_ROOT = os.path.expanduser(
    "~/Documents/Claude/Projects/Lex Council App/lex_council"
)


def default_root():
    """Walk up from this file / cwd looking for the lex_council dir that holds
    apps/web/config/app.config.ts. Falls back to the hardcoded path so the
    script still runs from the original machine layout."""
    starts = []
    try:
        starts.append(os.path.dirname(os.path.abspath(__file__)))
    except NameError:
        pass
    starts.append(os.getcwd())
    for start in starts:
        cur = start
        while True:
            for cand in (cur, os.path.join(cur, "lex_council")):
                marker = os.path.join(cand, "apps", "web", "config",
                                      "app.config.ts")
                if os.path.isfile(marker):
                    return cand
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
    return _FALLBACK_LEX_ROOT


LEX_ROOT = default_root()
DOCS = os.path.join(LEX_ROOT, "docs")
APP_CONFIG = os.path.join(LEX_ROOT, "apps", "web", "config", "app.config.ts")

FRONTMATTER_FILE = "/tmp/docs_frontmatter.json"
WIKILINKS_FILE   = "/tmp/docs_wikilinks.json"
ORPHANS_FILE     = "/tmp/docs_orphans.json"
RETIRED_FILE     = "/tmp/docs_retired_names.json"
ARTIFACTS_FILE   = "/tmp/docs_artifacts.json"
DRIFT_FILE       = "/tmp/docs_campaign_drift.json"
FINDINGS_FILE    = "/tmp/docs_cleanup_findings.md"

STALE_DAYS = 14

# Planet hubs (paths relative to DOCS).
PLANET_HUBS = [
    "Vault Core.md",
    "primary_instructions.md",
    "GENERAL-GUIDELINES.md",
    "BACKEND.md",
    "FRONTEND.md",
    "INTEGRATION.md",
    "DESIGN-CANON.md",
    "V2-CONVENTIONS.md",
]

# Frontmatter date fields whose staleness we care about.
DATE_FIELDS = ["last_full_audit", "counts_updated", "last_synced",
               "last_housekeeper_pass"]

# Retired-name registry — historical names that should usually NOT appear in
# current prose. Surfaced for human triage; some occurrences are legit context.
RETIRED_NAMES = {
    "v2-schema": [
        "fd", "fd_access", "council_members", "ppl", "cm_hr", "admin_perms",
        "whbd_responses", "evi", "evo", "is_verified",
        # NOTE: cm_ap_js is deliberately NOT here — it is the LIVE view backing
        # `cmAp` (FRONTEND.md, CLAUDE.md S1b), not a retired v2-schema name.
        # A prior version of this list mis-flagged it; see
        # docs/audits/2026-07-06_docs-drift-reconcile/99-synthesis.md.
    ],
    "retired-primitives": [
        "KpiStrip", "PageHeaderStrip", "AdminPageShell", "AdminFilterBar",
        "AdminDataTable", "STAT_CARDS",
    ],
}

ARCHIVED_SEGMENT = os.path.join("architecture", "_archived")

DATE_RE = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")

# A [[link]] whose target points at a CODE/asset file (outside docs/) is not
# doc-rot — it's a cross-reference into the app source tree. These get their own
# `code-link` bucket so the `broken` count reflects only genuine missing-.md
# doc links. A target qualifies if its stem ends in one of these extensions OR
# the raw target path points into apps/ or packages/.
CODE_LINK_EXTS = (
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".py", ".sql", ".json", ".css", ".sh",
)
CODE_PATH_RE = re.compile(r"(^|/)(apps|packages)/")
VERSION_RE = re.compile(r"version:\s*'([^']+)'")
ARTIFACT_RES = [
    re.compile(r"`([a-z_]+)`\s*\(v2;\s*was\s*`\1`\)"),
    re.compile(r"`([a-z_]+)`\s*\(was\s*`\1`\)"),
]


# ── helpers ────────────────────────────────────────────────────────────────

def warn(msg):
    print(f"  [WARN] {msg}")


def today():
    return datetime.date.today()


def parse_frontmatter(path):
    """Return a dict of the simple `key: value` lines between the first two
    `---` fences. No yaml lib — line scan only. Nested keys (indented) are
    captured under a synthetic `<parent>.<child>` key so `counts:` blocks are
    detectable. Returns {} if no frontmatter."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return {}
    fm = {}
    parent = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indented = line[0] in (" ", "\t")
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not indented:
            parent = key
            fm[key] = val
        elif parent is not None:
            fm[f"{parent}.{key}"] = val
    return fm


def days_since(date_str):
    """Extract a leading YYYY-MM-DD from a frontmatter value (it may have
    trailing prose) and return age in days, or None if unparseable/null."""
    if not date_str or date_str.lower() in ("null", "none", "~", "tbd", "n/a"):
        return None
    m = DATE_RE.search(date_str)
    if not m:
        return None
    try:
        d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return None
    return (today() - d).days


def app_config_version():
    """Parse APP_CONFIG.version from app.config.ts via regex. None on miss."""
    try:
        with open(APP_CONFIG, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return None
    m = VERSION_RE.search(text)
    return m.group(1) if m else None


def grep_lines(pattern, extended=True):
    """grep -rn over DOCS for *.md. Returns list of (relpath, lineno, text).
    Falls back to empty list on any subprocess failure."""
    flags = "-rnE" if extended else "-rn"
    try:
        out = subprocess.run(
            ["grep", flags, pattern, DOCS, "--include=*.md"],
            capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        warn(f"grep failed ({pattern!r}): {e}")
        return []
    rows = []
    for line in out.stdout.splitlines():
        # format: <path>:<lineno>:<text>
        parts = line.split(":", 2)
        if len(parts) < 3:
            continue
        path, lineno, text = parts
        try:
            rel = os.path.relpath(path, DOCS)
        except ValueError:
            rel = path
        rows.append((rel, int(lineno) if lineno.isdigit() else 0, text))
    return rows


def walk_md_files():
    """All *.md paths under DOCS (recursive)."""
    found = []
    for root, _dirs, files in os.walk(DOCS):
        for name in files:
            if name.endswith(".md"):
                found.append(os.path.join(root, name))
    return found


# ── subcommands ────────────────────────────────────────────────────────────

def cmd_frontmatter():
    """Parse the planet-hub frontmatter; flag stale dates + version drift."""
    print("docs_cleanup.py frontmatter — scanning planet hubs...")
    result = {"hubs": [], "today": today().isoformat()}
    app_ver = app_config_version()
    print(f"  app.config.ts version: {app_ver or '???'}")

    for rel in PLANET_HUBS:
        path = os.path.join(DOCS, rel)
        fm = parse_frontmatter(path)
        entry = {"hub": rel, "stale": [], "version_drift": None,
                 "needs_mcp_probe": []}
        if fm is None:
            warn(f"missing hub file: {rel}")
            entry["error"] = "file_not_found"
            result["hubs"].append(entry)
            continue

        for field in DATE_FIELDS:
            if field not in fm:
                continue
            age = days_since(fm[field])
            if age is not None and age > STALE_DAYS:
                entry["stale"].append({"field": field, "value": fm[field],
                                       "age_days": age})

        # Vault Core only: app_version drift vs app.config.ts
        if rel == "Vault Core.md" and app_ver is not None:
            fm_ver = fm.get("app_version", "").strip().strip("'\"")
            if fm_ver and fm_ver != app_ver:
                entry["version_drift"] = {"frontmatter": fm_ver,
                                          "app_config": app_ver}

        # Any counts: keys → needs an MCP probe (don't compute here)
        for key in fm:
            if key == "counts" or key.startswith("counts."):
                entry["needs_mcp_probe"].append(key)

        stale_n = len(entry["stale"])
        mark = "🚩" if (stale_n or entry["version_drift"]) else "✓"
        extra = []
        if stale_n:
            extra.append(f"{stale_n} stale date(s)")
        if entry["version_drift"]:
            extra.append("VERSION DRIFT")
        if entry["needs_mcp_probe"]:
            extra.append(f"{len(entry['needs_mcp_probe'])} counts→probe")
        print(f"  {mark} {rel}" + (f"  ({', '.join(extra)})" if extra else ""))
        result["hubs"].append(entry)

    with open(FRONTMATTER_FILE, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Wrote → {FRONTMATTER_FILE}")
    return result


def cmd_wikilinks():
    """Classify every [[X]] target as broken / archived-pointer / resolved."""
    print("docs_cleanup.py wikilinks — collecting [[links]]...")
    rows = grep_lines(r"\[\[[^]]+\]\]")
    if not rows and not os.path.isdir(DOCS):
        warn(f"DOCS not found: {DOCS}")

    md_files = walk_md_files()
    # basename (no .md) → list of relpaths
    by_stem = defaultdict(list)
    # full relpath (no .md, forward slashes) → relpath — for path-aware links
    by_relpath = {}
    for path in md_files:
        relpath = os.path.relpath(path, DOCS)
        stem = os.path.splitext(os.path.basename(path))[0]
        by_stem[stem].append(relpath)
        relpath_noext = relpath[:-3] if relpath.endswith(".md") else relpath
        by_relpath[relpath_noext.replace(os.sep, "/")] = relpath

    broken, archived, code_links = [], [], []
    resolved_count = 0
    seen_targets = {}  # cache key → broken/archived-pointer/resolved

    for rel, lineno, text in rows:
        for raw in WIKILINK_RE.findall(text):
            # strip |alias and #heading; take last path segment as the file stem
            target = raw.split("|", 1)[0].split("#", 1)[0].strip()
            if not target:
                continue
            stem = target.rstrip("/").split("/")[-1]
            # A target pointing at a code/asset file (by extension) or into the
            # app source tree (apps/ | packages/ path segment) is a cross-ref,
            # not doc-rot — bucket it as code-link and skip .md resolution.
            # (.md targets fall through to broken/archived/resolved below.)
            stem_lc = stem.lower()
            is_code = (
                (stem_lc.endswith(CODE_LINK_EXTS)
                 and not stem_lc.endswith(".md"))
                or bool(CODE_PATH_RE.search(target))
            )
            if is_code:
                code_links.append({"target": target, "stem": stem,
                                   "file": rel, "line": lineno})
                continue
            # by_stem keys are extension-less; a target may be written [[X]] or
            # [[X.md]] — normalize a trailing .md so both forms resolve.
            if stem_lc.endswith(".md"):
                stem = stem[:-3]

            target_norm = target.rstrip("/")
            if target_norm.lower().endswith(".md"):
                target_norm = target_norm[:-3]
            has_dir = "/" in target_norm
            reason = None

            if has_dir:
                # Path-aware resolution: a target with a directory component
                # must match that exact relpath, not just share a basename
                # with some file elsewhere. Prevents a renamed directory
                # (e.g. audit-campaigns/ → audits/) from silently resolving
                # against a same-named file under the OLD path.
                cache_key = target_norm
                if cache_key in seen_targets:
                    cls, reason = seen_targets[cache_key]
                else:
                    exact = by_relpath.get(target_norm)
                    if exact:
                        cls = ("archived-pointer" if ARCHIVED_SEGMENT in exact
                               else "resolved")
                    else:
                        stem_matches = by_stem.get(stem, [])
                        if stem_matches:
                            cls, reason = "broken", "path_mismatch"
                        else:
                            cls, reason = "broken", "missing"
                    seen_targets[cache_key] = (cls, reason)
            else:
                cache_key = stem
                if cache_key in seen_targets:
                    cls, reason = seen_targets[cache_key]
                else:
                    matches = by_stem.get(stem, [])
                    if not matches:
                        cls, reason = "broken", "missing"
                    elif all(ARCHIVED_SEGMENT in m for m in matches):
                        cls = "archived-pointer"
                    else:
                        cls = "resolved"
                    seen_targets[cache_key] = (cls, reason)

            row = {"target": target, "stem": stem, "file": rel, "line": lineno}
            if reason:
                row["reason"] = reason
            if cls == "broken":
                broken.append(row)
            elif cls == "archived-pointer":
                archived.append(row)
            else:
                resolved_count += 1

    result = {
        "broken_count": len(broken),
        "code_link_count": len(code_links),
        "archived_pointer_count": len(archived),
        "resolved_count": resolved_count,
        "broken": broken,
        "code_links": code_links,
        "archived_pointers": archived,
    }
    with open(WIKILINKS_FILE, "w") as f:
        json.dump(result, f, indent=2)
    bm = "🚩" if broken else "✓"
    am = "?" if archived else "✓"
    print(f"  {bm} broken (missing .md): {len(broken)}")
    print(f"  · code-link (code/asset ref): {len(code_links)}")
    print(f"  {am} archived-pointer: {len(archived)}")
    print(f"  ✓ resolved: {resolved_count}")
    print(f"  Wrote → {WIKILINKS_FILE}")
    return result


def cmd_orphans():
    """vault-log files not referenced inside vault-logs/INDEX.md."""
    print("docs_cleanup.py orphans — diffing vault-logs vs INDEX...")
    vl_dir = os.path.join(DOCS, "vault-logs")
    index_path = os.path.join(vl_dir, "INDEX.md")
    date_prefix = re.compile(r"^\d{4}-\d{2}-\d{2}_")

    if not os.path.isdir(vl_dir):
        warn(f"vault-logs dir not found: {vl_dir}")
        result = {"orphan_count": 0, "orphans": [], "error": "no_vault_logs_dir"}
        with open(ORPHANS_FILE, "w") as f:
            json.dump(result, f, indent=2)
        return result

    files = set()
    for name in os.listdir(vl_dir):
        if name.endswith(".md") and date_prefix.match(name):
            files.add(name[:-3])  # strip .md → basename stem

    indexed = set()
    if os.path.exists(index_path):
        try:
            with open(index_path, encoding="utf-8") as f:
                idx_text = f.read()
        except OSError as e:
            warn(f"could not read INDEX.md: {e}")
            idx_text = ""
        for raw in WIKILINK_RE.findall(idx_text):
            target = raw.split("|", 1)[0].split("#", 1)[0].strip()
            stem = target.rstrip("/").split("/")[-1]
            indexed.add(stem)
    else:
        warn("vault-logs/INDEX.md not found — every log counts as orphan")

    orphans = sorted(files - indexed)
    result = {"total_logs": len(files), "indexed": len(files & indexed),
              "orphan_count": len(orphans), "orphans": orphans}
    with open(ORPHANS_FILE, "w") as f:
        json.dump(result, f, indent=2)
    mark = "🚩" if orphans else "✓"
    print(f"  {mark} {len(orphans)} orphan(s) of {len(files)} dated logs")
    if orphans:
        for o in orphans[:10]:
            print(f"    - {o}")
        if len(orphans) > 10:
            print(f"    … +{len(orphans) - 10} more")
    print(f"  Wrote → {ORPHANS_FILE}")
    return result


def cmd_retired_names():
    """Grep DOCS for each retired name (word-boundary). Human triage only."""
    print("docs_cleanup.py retired-names — scanning registry...")
    grouped = {}
    total = 0
    for category, names in RETIRED_NAMES.items():
        for name in names:
            rows = grep_lines(r"\b" + re.escape(name) + r"\b")
            hits = [{"file": rel, "line": ln, "text": txt.strip()[:160]}
                    for rel, ln, txt in rows]
            if hits:
                grouped[name] = {"category": category, "count": len(hits),
                                 "occurrences": hits}
                total += len(hits)

    result = {"total_occurrences": total, "names_hit": len(grouped),
              "by_name": grouped, "note": "human triage only — never auto-fixed"}
    with open(RETIRED_FILE, "w") as f:
        json.dump(result, f, indent=2)
    mark = "🚩" if grouped else "✓"
    print(f"  {mark} {len(grouped)} retired name(s) present, "
          f"{total} total occurrence(s)")
    for name, info in sorted(grouped.items(), key=lambda x: -x[1]["count"])[:12]:
        print(f"    [{info['category']}] {name} × {info['count']}")
    print(f"  Wrote → {RETIRED_FILE}")
    return result


def cmd_artifacts():
    """Grep DOCS for botched same-identifier global-replace artifacts."""
    print("docs_cleanup.py artifacts — scanning for replace artifacts...")
    hits = []
    for path in walk_md_files():
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            warn(f"could not read {path}: {e}")
            continue
        rel = os.path.relpath(path, DOCS)
        for i, line in enumerate(lines, start=1):
            for rx in ARTIFACT_RES:
                m = rx.search(line)
                if m:
                    hits.append({"file": rel, "line": i,
                                 "identifier": m.group(1),
                                 "text": line.strip()[:160]})
                    break

    result = {"artifact_count": len(hits), "artifacts": hits}
    with open(ARTIFACTS_FILE, "w") as f:
        json.dump(result, f, indent=2)
    mark = "🚩" if hits else "✓"
    print(f"  {mark} {len(hits)} replace-artifact(s)")
    for h in hits[:10]:
        print(f"    {h['file']}:{h['line']} — {h['identifier']}")
    print(f"  Wrote → {ARTIFACTS_FILE}")
    return result


def cmd_campaign_drift():
    """in-progress campaign plans that already have a matching vault-log."""
    print("docs_cleanup.py campaign-drift — scanning build-campaigns...")
    bc_dir = os.path.join(DOCS, "build-campaigns")
    vl_dir = os.path.join(DOCS, "vault-logs")
    drift = []

    if not os.path.isdir(bc_dir):
        warn(f"build-campaigns dir not found: {bc_dir}")
        result = {"drift_count": 0, "drift": [], "error": "no_build_campaigns"}
        with open(DRIFT_FILE, "w") as f:
            json.dump(result, f, indent=2)
        return result

    vl_names = []
    if os.path.isdir(vl_dir):
        vl_names = [n[:-3] for n in os.listdir(vl_dir) if n.endswith(".md")]

    checked = 0
    for entry in sorted(os.listdir(bc_dir)):
        camp_dir = os.path.join(bc_dir, entry)
        plan = os.path.join(camp_dir, "00-campaign-plan.md")
        if not os.path.isfile(plan):
            continue
        checked += 1
        fm = parse_frontmatter(plan)
        if fm is None:
            continue
        status = fm.get("status", "").strip().lower()
        if status != "in-progress":
            continue
        # Does a vault-log named <campaign-dir-basename>*.md exist?
        matches = [n for n in vl_names if n.startswith(entry)]
        if matches:
            drift.append({"campaign": entry, "status": status,
                          "vault_logs": sorted(matches)})

    result = {"campaigns_checked": checked, "drift_count": len(drift),
              "drift": drift}
    with open(DRIFT_FILE, "w") as f:
        json.dump(result, f, indent=2)
    mark = "🚩" if drift else "✓"
    print(f"  {mark} {len(drift)} drift row(s) of {checked} plan(s) checked")
    for d in drift[:10]:
        print(f"    {d['campaign']} → {len(d['vault_logs'])} log(s)")
    print(f"  Wrote → {DRIFT_FILE}")
    return result


def cmd_all():
    """Run every check; write combined human findings + print summary."""
    print("docs_cleanup.py all — running every check\n")
    fm = cmd_frontmatter(); print()
    wl = cmd_wikilinks(); print()
    orp = cmd_orphans(); print()
    ret = cmd_retired_names(); print()
    art = cmd_artifacts(); print()
    drift = cmd_campaign_drift(); print()

    lines = [
        "# Docs Cleanup Findings", "",
        f"_Generated {today().isoformat()} by docs_cleanup.py — "
        "detect-only, no files modified._", "",
    ]

    def section(title, summary, bullets):
        lines.extend([f"## {title}", ""])
        if summary:
            lines.append(summary)
        lines.extend("  " + b for b in bullets)
        lines.append("")

    # ── Frontmatter (per-hub one-liner) ──
    hub_bullets = []
    for h in fm["hubs"]:
        if h.get("error"):
            hub_bullets.append(f"- 🚩 **{h['hub']}** — {h['error']}")
            continue
        bits = [f"`{s['field']}` {s['age_days']}d old" for s in h["stale"]]
        if h["version_drift"]:
            vd = h["version_drift"]
            bits.append(f"VERSION DRIFT (fm {vd['frontmatter']} vs "
                        f"config {vd['app_config']})")
        if h["needs_mcp_probe"]:
            bits.append(f"{len(h['needs_mcp_probe'])} counts→needs_mcp_probe")
        hub_bullets.append(f"- 🚩 **{h['hub']}** — " + "; ".join(bits)
                           if bits else f"- ✓ **{h['hub']}** — clean")
    section("Frontmatter (planet hubs)", "", hub_bullets)

    # ── Wikilinks ──
    wl_b = [f"- 🚩 `[[{b['target']}]]` → {b['file']}:{b['line']}"
            for b in wl["broken"][:40]]
    if wl["broken_count"] > 40:
        wl_b.append(f"- … +{wl['broken_count'] - 40} more broken")
    wl_b += [f"- ? `[[{a['target']}]]` (archived) → {a['file']}:{a['line']}"
             for a in wl["archived_pointers"][:20]]
    section("Wikilinks",
            f"- broken (missing .md): **{wl['broken_count']}** · code-link "
            f"(code/asset ref): **{wl.get('code_link_count', 0)}** · "
            f"archived-pointer: **{wl['archived_pointer_count']}** · resolved: "
            f"{wl['resolved_count']}", wl_b)

    # ── Orphans ──
    orp_b = [f"- 🚩 {o}" for o in orp["orphans"][:60]]
    if orp["orphan_count"] > 60:
        orp_b.append(f"- … +{orp['orphan_count'] - 60} more")
    section("Orphan vault-logs (not in INDEX.md)",
            f"- orphans: **{orp['orphan_count']}** of "
            f"{orp.get('total_logs', '?')} dated logs", orp_b)

    # ── Retired names ──
    ret_b = [f"- [{i['category']}] **{n}** × {i['count']}"
             for n, i in sorted(ret["by_name"].items(),
                                 key=lambda x: -x[1]["count"])]
    section("Retired names (human triage only — never auto-fixed)",
            f"- names present: **{ret['names_hit']}**, total occurrences: "
            f"{ret['total_occurrences']}", ret_b)

    # ── Artifacts ──
    art_b = [f"- 🚩 {h['file']}:{h['line']} — `{h['identifier']}`"
             for h in art["artifacts"][:40]]
    section("Replace artifacts",
            f"- artifacts: **{art['artifact_count']}**", art_b)

    # ── Campaign drift ──
    drift_b = [f"- 🚩 {d['campaign']} → {', '.join(d['vault_logs'][:3])}"
               for d in drift["drift"]]
    section("Campaign drift (in-progress plan + existing vault-log)",
            f"- drift rows: **{drift['drift_count']}** of "
            f"{drift.get('campaigns_checked', '?')} plans checked", drift_b)

    with open(FINDINGS_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    # ── summary table ──
    print("=" * 60)
    print("DOCS CLEANUP SUMMARY")
    print("=" * 60)
    stale_hubs = sum(1 for h in fm["hubs"]
                     if h.get("stale") or h.get("version_drift")
                     or h.get("error"))
    rows = [
        ("frontmatter (hubs flagged)", stale_hubs),
        ("wikilinks broken (.md)",     wl["broken_count"]),
        ("wikilinks code-link",        wl.get("code_link_count", 0)),
        ("wikilinks archived-pointer", wl["archived_pointer_count"]),
        ("orphan vault-logs",          orp["orphan_count"]),
        ("retired names present",      ret["names_hit"]),
        ("replace artifacts",          art["artifact_count"]),
        ("campaign drift rows",        drift["drift_count"]),
    ]
    for label, n in rows:
        mark = "🚩" if n else "✓"
        print(f"  {mark} {label:<30} {n}")
    print("=" * 60)
    print(f"  Human findings → {FINDINGS_FILE}")


# ── main ───────────────────────────────────────────────────────────────────

COMMANDS = {
    "frontmatter": cmd_frontmatter,
    "wikilinks": cmd_wikilinks,
    "orphans": cmd_orphans,
    "retired-names": cmd_retired_names,
    "artifacts": cmd_artifacts,
    "campaign-drift": cmd_campaign_drift,
    "all": cmd_all,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python3 docs_cleanup.py <{'|'.join(COMMANDS)}>")
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
