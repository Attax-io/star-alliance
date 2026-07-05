#!/usr/bin/env python3
"""activity_coverage.py — activity-monitor instrumentation coverage audit.

Keeps the user-activity monitor's coverage in lock-step with the app's
mutation + UI surface. Since 2026-07-06 every write funnels through
callServerRpc in apps/web/lib/mutations/_shared.ts, which auto-emits a
`record.*` event via a verb→event map (VERB_EVENT) minus a denylist
(WRITE_ACTIVITY_DENY). This detector verifies that invariant still holds and
flags four drift classes so a new page/action never goes silently untracked:

  1. unknown_literals  (HIGH)  event_type strings emitted in code but ABSENT
                                from the DB allow-list → the log_user_activity
                                RPC rejects them silently (0 rows). Needs a DB
                                seed row (migration) — surfaced, not auto-fixed.
  2. dead_types        (LOW)   allow-list types neither emitted as a literal,
                                produced by the mutation boundary, nor an
                                automatic nav event → defined but unreachable.
  3. uncovered_verbs   (MED)   write-looking RPC verb prefixes (create/update/
                                delete/set/…) used by a mutation but missing
                                from VERB_EVENT and not denied → their writes
                                are untracked. MECHANICAL auto-fix: add the
                                verb→event mapping to _shared.ts.
  4. boundary_bypass   (MED)   create/update/delete RPCs invoked via callRpc
                                or a raw .rpc() call (not callServerRpc) → they
                                skip the auto-emit boundary. Fix = migrate the
                                module to callServerRpc.

Subcommands:
  detect    Scan code + DB allow-list → /tmp/activity_coverage.json
  classify  Re-read detect output, rank by severity → /tmp/activity_coverage_classified.json + summary

Read-only. No app files are modified; auto-wiring (class 3) is applied by the
skill body per references/mode-activity-coverage.md, not by this script.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ── project root (shared pattern with the other cleanup scripts) ──
def default_root() -> str:
    starts = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    seen = set()
    for start in starts:
        for parent in [start, *start.parents]:
            if parent in seen:
                continue
            seen.add(parent)
            if (parent / 'apps' / 'web' / 'config' / 'app.config.ts').is_file():
                return str(parent)
            cand = parent / 'lex_council'
            if (cand / 'apps' / 'web' / 'config' / 'app.config.ts').is_file():
                return str(cand)
    return os.path.expanduser("~/Documents/Claude/Projects/Lex Council App/lex_council")


LEX_ROOT = default_root()
WEB = os.path.join(LEX_ROOT, "apps", "web")
SHARED_TS = os.path.join(WEB, "lib", "mutations", "_shared.ts")
MUTATIONS_DIR = os.path.join(WEB, "lib", "mutations")
DETECT_OUT = Path("/tmp/activity_coverage.json")
CLASSIFY_OUT = Path("/tmp/activity_coverage_classified.json")

# Events fired automatically by components/portal/ActivityTracker.tsx — always
# reachable regardless of literal call sites.
AUTO_NAV_EVENTS = {"session.start", "session.end", "session.heartbeat", "route.view"}

# Events the mutation boundary can produce (the VERB_EVENT values) — reachable
# whenever at least one non-denied write RPC maps to them.
BOUNDARY_EVENTS = {
    "record.create", "record.update", "record.delete",
    "record.status_change", "record.assign",
}

# Verb prefixes that denote a write (used to spot uncovered_verbs). Read-only /
# housekeeping verbs are intentionally excluded.
WRITE_VERBS = {
    "create", "insert", "add", "upsert", "grant", "update", "set", "rename",
    "link", "unlink", "save", "merge", "decide", "approve", "delete", "remove",
    "soft", "restore", "reactivate", "suspend", "snooze", "archive", "publish",
    "unpublish", "schedule", "unschedule", "submit", "cancel", "reject", "void",
    "assign", "transfer", "promote", "demote", "move", "certify", "agree",
    "initiate", "confirm", "broadcast", "subscribe", "unsubscribe",
}

# Fallback allow-list if the DB is unreachable in this (often headless) context.
# Mirrors public.user_activity_event_types as of 2026-07-06.
ALLOWLIST_FALLBACK = {
    "chat.message_send", "comment.create", "file.closure_cancel",
    "file.closure_request", "file.demote", "file.download", "file.preview",
    "file.promote", "file.transfer", "file.upload", "route.view", "session.end",
    "session.heartbeat", "session.start", "movement.confirm", "movement.initiate",
    "movement.reject", "record.assign", "record.create", "record.delete",
    "record.open", "record.status_change", "record.update", "task.complete",
    "task.whbd_review", "task.whbd_submit", "transaction.agree",
    "transaction.certify", "wages.month_close", "filter.apply", "search.submit",
}


def _sh(cmd: list) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
    except Exception:
        return ""


def load_allowlist() -> tuple:
    """Return (set_of_event_types, source_str). Prefer the live DB; fall back
    to the committed constant so run_all / the rotation never break offline."""
    env_path = os.path.join(WEB, ".env.local")
    url = None
    if os.path.isfile(env_path):
        m = re.search(r'^DATABASE_URL=(\S+)', open(env_path).read(), re.M)
        if m:
            url = m.group(1).strip().strip('"').strip("'")
    if url:
        try:
            import psycopg2  # type: ignore
            c = psycopg2.connect(url)
            cur = c.cursor()
            cur.execute("SELECT event_type FROM public.user_activity_event_types")
            types = {r[0] for r in cur.fetchall()}
            cur.close()
            c.close()
            if types:
                return types, "db"
        except Exception:
            pass
    return set(ALLOWLIST_FALLBACK), "fallback-constant"


def emitted_literals() -> set:
    """Every event_type string passed as the FIRST arg to a track call, across
    the app, EXCLUDING _shared.ts (whose VERB_EVENT map is the boundary source,
    counted separately) and tests."""
    out = _sh([
        "grep", "-rhoE", "--include=*.ts", "--include=*.tsx",
        r"track(Activity|ActivityEvent)\(\s*'[a-z][a-z._]+'", WEB,
    ])
    lits = set(re.findall(r"'([a-z][a-z._]+)'", out))
    return lits


def parse_shared_maps() -> tuple:
    """Parse VERB_EVENT (verb→event) and WRITE_ACTIVITY_DENY from _shared.ts so
    the detector reflects the real, current boundary config."""
    verb_event, deny = {}, set()
    if not os.path.isfile(SHARED_TS):
        return verb_event, deny
    src = open(SHARED_TS).read()
    m = re.search(r"const VERB_EVENT[^{]*\{(.*?)\n\}", src, re.S)
    if m:
        for vk, ev in re.findall(r"(\w+):\s*'([a-z][a-z._]+)'", m.group(1)):
            verb_event[vk] = ev
    m = re.search(r"WRITE_ACTIVITY_DENY\s*=\s*new Set<string>\(\[(.*?)\]\)", src, re.S)
    if m:
        deny = set(re.findall(r"'([a-z_]+)'", m.group(1)))
    return verb_event, deny


def mutation_rpcs() -> list:
    """[(rpc_name, transport)] for every RPC invoked from lib/mutations.
    Skips the transport lib (_shared.ts) and the allow-list registry, whose
    RPC-name occurrences are documentation, not call sites, and any line that
    is a comment (leading //, *, or an inline ` * ` doc-comment body)."""
    rows = []
    out = _sh([
        "grep", "-rnoE", "--include=*.ts",
        r"call(Server)?Rpc<?[^(]*\(\s*'[a-z_]+'|\.rpc\(\s*'[a-z_]+'", MUTATIONS_DIR,
    ])
    for line in out.splitlines():
        # line format: <path>:<lineno>:<match>
        path = line.split(":", 1)[0]
        base = os.path.basename(path)
        if base in ("_shared.ts", "server-rpc-allowlist.ts"):
            continue
        payload = line.split(":", 2)[-1].lstrip()
        if payload.startswith("//") or payload.startswith("*"):
            continue
        name_m = re.search(r"'([a-z_]+)'", line)
        if not name_m:
            continue
        name = name_m.group(1)
        if "callServerRpc" in line:
            transport = "server"
        elif "callRpc" in line:
            transport = "callRpc"
        else:
            transport = "raw-rpc"
        rows.append((name, transport))
    return rows


def verb_of(rpc: str) -> str:
    if rpc.startswith("soft_delete"):
        return "delete"
    return rpc.split("_")[0]


def cmd_detect(_args) -> None:
    allowlist, allow_source = load_allowlist()
    lits = emitted_literals()
    verb_event, deny = parse_shared_maps()
    rpcs = mutation_rpcs()

    # Which boundary events are actually producible (≥1 non-denied write RPC maps to them)
    producible_boundary = set()
    for rpc, _t in rpcs:
        if rpc in deny:
            continue
        ev = verb_event.get(verb_of(rpc))
        if ev:
            producible_boundary.add(ev)

    reachable = set(lits) | AUTO_NAV_EVENTS | (BOUNDARY_EVENTS & producible_boundary)

    # 1. literals emitted but not in the allow-list → RPC rejects silently
    unknown_literals = sorted(l for l in lits if l not in allowlist)

    # 2. allow-list types with no path to being emitted
    dead_types = sorted(t for t in allowlist if t not in reachable)

    # 3. write RPCs whose verb is neither mapped nor denied → untracked write
    uncovered = {}
    for rpc, _t in rpcs:
        if rpc in deny:
            continue
        v = verb_of(rpc)
        if v in WRITE_VERBS and v not in verb_event:
            uncovered.setdefault(v, []).append(rpc)
    uncovered_verbs = [{"verb": v, "rpcs": sorted(set(rs))} for v, rs in sorted(uncovered.items())]

    # 4. create/update/delete RPCs that bypass the auto-emit boundary
    bypass = []
    for rpc, t in rpcs:
        if t == "server" or rpc in deny:
            continue
        if verb_of(rpc) in ("create", "update", "delete", "insert", "add"):
            bypass.append({"rpc": rpc, "transport": t})
    # dedupe
    seen = set()
    boundary_bypass = []
    for b in bypass:
        k = (b["rpc"], b["transport"])
        if k not in seen:
            seen.add(k)
            boundary_bypass.append(b)

    result = {
        "lex_root": LEX_ROOT,
        "allowlist_source": allow_source,
        "allowlist_count": len(allowlist),
        "emitted_literal_count": len(lits),
        "mutation_rpc_count": len(rpcs),
        "verb_event_map": verb_event,
        "unknown_literals": unknown_literals,
        "dead_types": dead_types,
        "uncovered_verbs": uncovered_verbs,
        "boundary_bypass": sorted(boundary_bypass, key=lambda b: b["rpc"]),
    }
    DETECT_OUT.write_text(json.dumps(result, indent=2))
    print(f"[activity-coverage] allow-list={len(allowlist)} ({allow_source}) "
          f"literals={len(lits)} rpcs={len(rpcs)}")
    print(f"  unknown_literals={len(unknown_literals)} dead_types={len(dead_types)} "
          f"uncovered_verbs={len(uncovered_verbs)} boundary_bypass={len(boundary_bypass)}")
    print(f"  → {DETECT_OUT}")


SEV = {
    "unknown_literals": "HIGH",
    "boundary_bypass": "MED",
    "uncovered_verbs": "MED",
    "dead_types": "LOW",
}


def cmd_classify(_args) -> None:
    if not DETECT_OUT.is_file():
        print("[activity-coverage] run `detect` first", file=sys.stderr)
        sys.exit(1)
    d = json.loads(DETECT_OUT.read_text())
    findings = []
    for lit in d["unknown_literals"]:
        findings.append({"sev": "HIGH", "class": "unknown_literal", "item": lit,
                         "fix": "Add a row to public.user_activity_event_types (migration) — "
                                "the RPC rejects unknown types, so this event logs 0 rows."})
    for b in d["boundary_bypass"]:
        findings.append({"sev": "MED", "class": "boundary_bypass", "item": b["rpc"],
                         "fix": f"Invoked via {b['transport']}; migrate to callServerRpc so the "
                                "auto-emit boundary tracks it."})
    for u in d["uncovered_verbs"]:
        findings.append({"sev": "MED", "class": "uncovered_verb", "item": u["verb"],
                         "rpcs": u["rpcs"],
                         "fix": "MECHANICAL: add a `%s:` entry to VERB_EVENT in _shared.ts "
                                "(map to the right record.* event)." % u["verb"]})
    for t in d["dead_types"]:
        findings.append({"sev": "LOW", "class": "dead_type", "item": t,
                         "fix": "Allow-list type with no emitter — wire a call site or retire the row."})
    order = {"HIGH": 0, "MED": 1, "LOW": 2}
    findings.sort(key=lambda f: order[f["sev"]])
    summary = {
        "high": sum(1 for f in findings if f["sev"] == "HIGH"),
        "med": sum(1 for f in findings if f["sev"] == "MED"),
        "low": sum(1 for f in findings if f["sev"] == "LOW"),
        "findings": findings,
    }
    CLASSIFY_OUT.write_text(json.dumps(summary, indent=2))
    print(f"[activity-coverage] HIGH={summary['high']} MED={summary['med']} LOW={summary['low']}")
    for f in findings:
        extra = f" ({', '.join(f['rpcs'])})" if f.get("rpcs") else ""
        print(f"  [{f['sev']}] {f['class']}: {f['item']}{extra}")
    print(f"  → {CLASSIFY_OUT}")


def main() -> None:
    p = argparse.ArgumentParser(description="Activity-monitor coverage audit.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("detect", help="scan code + DB allow-list → /tmp/activity_coverage.json")
    sub.add_parser("classify", help="rank drift by severity → /tmp/activity_coverage_classified.json")
    args = p.parse_args()
    {"detect": cmd_detect, "classify": cmd_classify}[args.cmd](args)


if __name__ == "__main__":
    main()
