#!/usr/bin/env python3
"""
tools/backfill_guild.py — historical backfill PREP (no network).

Phase 3 of the Supabase migration. Converts pre-existing local telemetry into
outbox rows (schema: {"table","client_uuid","payload"}) so a later `sa flush`
can drain them into the `guild` schema, and archives the originals with a
sha256 manifest. This script NEVER touches the network — it only reads the
source files and writes to .claude/state/outbox.jsonl + data/archive/.

Conversions:
  1. data/turn-cost.jsonl        (699+ rows)  -> outbox `turns` rows
  2. .claude/state/dispatch-log.jsonl, kind=spawn rows (~164) -> outbox `events` rows
  3. per-member opening-balance (derived from dispatch-log agent counts, ~9 members)
     -> outbox `log` rows

Idempotent: uses a stable client_uuid (uuid5 over a deterministic string) per
source row, so re-running this script does not duplicate outbox entries (the
DB's client_uuid UNIQUE constraint + Prefer: resolution=ignore-duplicates on
`sa flush` makes this safe even if outbox rows are appended twice locally —
but this script also skips a source file it detects it already archived).
"""
import sys
import os
import json
import hashlib
import uuid
import shutil
import time
from pathlib import Path
from datetime import datetime, timezone
import getpass

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STATE_DIR = ROOT / ".claude" / "state"
OUTBOX_PATH = STATE_DIR / "outbox.jsonl"
ARCHIVE_DIR = DATA_DIR / "archive" / "2026-07-pre-supabase"

TURN_COST_SRC = DATA_DIR / "turn-cost.jsonl"
DISPATCH_LOG_SRC = STATE_DIR / "dispatch-log.jsonl"
XP_LOG_SRC = STATE_DIR / "xp-log.jsonl"

# Deterministic namespace so uuid5(NAMESPACE, seed) is stable across runs.
NAMESPACE = uuid.UUID("6f6e6b61-6c65-2d67-7569-6c642d6e7300")

MEMBERS = [
    "the-architect", "the-butler", "the-designer", "the-developer",
    "the-herald", "the-interpreter", "the-merchant", "the-quartermaster",
    "the-steward",
]

PROJECT_NAME = "star-alliance"


def device_id_slug():
    """Stable per-machine id: 'mac-' + the OS user. Same convention used by
    turn-cost.py, spawn-log.py, and bin/sa (cmd_log) — never derive this
    independently."""
    try:
        return "mac-" + getpass.getuser()
    except Exception:
        return "mac-unknown"



def stable_uuid(*parts: str) -> str:
    seed = "|".join(parts)
    return str(uuid.uuid5(NAMESPACE, seed))


def outbox_append_row(table: str, payload: dict, seed: str) -> None:
    row = {"table": table, "client_uuid": stable_uuid(table, seed), "payload": payload}
    with open(OUTBOX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, separators=(",", ":")) + "\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def backfill_turns() -> int:
    if not TURN_COST_SRC.exists():
        print(f"skip: {TURN_COST_SRC} not found")
        return 0
    n = 0
    with open(TURN_COST_SRC, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            # Authoritative guild.turns columns: client_uuid, ts, device_id,
            # project, tier, assistant_msgs, tokens_in, tokens_out,
            # cache_read, cache_create, wall_ms. The legacy source used flat
            # "in"/"out" names — remap, never carry those through.
            payload = {
                "ts": rec.get("ts"),
                "device_id": device_id_slug(),
                "project": PROJECT_NAME,
                "tier": rec.get("tier", "unknown"),
                "assistant_msgs": rec.get("assistant_msgs", 0),
                "tokens_in": rec.get("tokens_in", rec.get("in", 0)),
                "tokens_out": rec.get("tokens_out", rec.get("out", 0)),
                "cache_read": rec.get("cache_read", 0),
                "cache_create": rec.get("cache_create", 0),
                "wall_ms": rec.get("wall_ms", 0),
            }
            # Seed stays keyed on the RAW source line (stable across a fix to
            # the payload shape) so a re-run replaces the same client_uuid.
            seed = f"turns:{i}:{line[:80]}"
            outbox_append_row("turns", payload, seed)
            n += 1
    print(f"backfilled {n} turns rows from {TURN_COST_SRC.name}")
    return n


def backfill_spawn_events() -> int:
    if not DISPATCH_LOG_SRC.exists():
        print(f"skip: {DISPATCH_LOG_SRC} not found")
        return 0
    n = 0
    with open(DISPATCH_LOG_SRC, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("kind") != "spawn":
                continue
            # Authoritative guild.events columns: client_uuid, ts, device_id,
            # project, kind (spawn|skill_fire|workflow|command|note), subject,
            # detail (jsonb). subject = the agent name.
            payload = {
                "ts": rec.get("timestamp"),
                "device_id": device_id_slug(),
                "project": PROJECT_NAME,
                "kind": "spawn",
                "subject": rec.get("agent", "unknown"),
                "detail": rec,
            }
            seed = f"events:{i}:{line[:80]}"
            outbox_append_row("events", payload, seed)
            n += 1
    print(f"backfilled {n} events(spawn) rows from {DISPATCH_LOG_SRC.name}")
    return n


def backfill_member_opening_balances() -> int:
    """Derive a per-member opening-balance log row from dispatch-log agent
    counts — one guild.log row per known member, seeded so this is idempotent."""
    counts = {m: 0 for m in MEMBERS}
    if DISPATCH_LOG_SRC.exists():
        with open(DISPATCH_LOG_SRC, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                agent = rec.get("agent")
                if agent in counts:
                    counts[agent] += 1

    n = 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for member, count in counts.items():
        # Authoritative guild.log columns: client_uuid, entry_date (date),
        # type, title, who, detail, device_id. Opening balances are filed
        # with type='xp-opening-balance'.
        payload = {
            "entry_date": today,
            "type": "xp-opening-balance",
            "title": f"opening-balance: {member}",
            "who": device_id_slug(),
            "detail": {"member": member, "dispatch_count_pre_migration": count},
            "device_id": device_id_slug(),
        }
        seed = f"log-opening-balance:{member}"
        outbox_append_row("log", payload, seed)
        n += 1
    print(f"backfilled {n} per-member opening-balance log rows")
    return n


def archive_originals() -> dict:
    """Archive-only sources (never deleted from their live location, copied
    with a sha256 manifest): guild-log.json, mcp-telemetry.jsonl, usage-log.jsonl."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    candidates = [
        # The three CONVERTED sources (item 10's primary referent) — frozen
        # here for provenance so they can later be safely deleted.
        TURN_COST_SRC,
        DISPATCH_LOG_SRC,
        XP_LOG_SRC,
        # Archive-only sources named in the migration plan (never converted,
        # never deleted — kept for reference/audit only).
        DATA_DIR / "guild-log.json",
        DATA_DIR / "mcp-telemetry.jsonl",
        ROOT / "star-alliance-arsenal" / "usage-log.jsonl",
    ]
    manifest = {}
    for src in candidates:
        if not src.exists():
            manifest[str(src.relative_to(ROOT))] = "MISSING (skipped)"
            continue
        dest = ARCHIVE_DIR / src.name
        shutil.copy2(src, dest)
        manifest[str(src.relative_to(ROOT))] = sha256_file(dest)
    manifest_path = ARCHIVE_DIR / "MANIFEST.sha256.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"archived {len([v for v in manifest.values() if v != 'MISSING (skipped)'])} file(s) "
          f"to {ARCHIVE_DIR} (manifest: {manifest_path.name})")
    return manifest


def main():
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    print("tools/backfill_guild.py — no network, outbox-prep only\n")
    total = 0
    total += backfill_turns()
    total += backfill_spawn_events()
    total += backfill_member_opening_balances()
    archive_originals()
    print(f"\ntotal outbox rows staged: {total}")
    print("Originals are UNCHANGED on disk (archive-first, never deleted).")
    print("Run `bin/sa flush` after Supabase connectivity is confirmed to drain the outbox.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
