#!/usr/bin/env python3
"""
tests/test_sa_cli.py — local unit tests for bin/sa (Phase 3).

No network calls. Loads bin/sa as a module via importlib (it has no .py
extension) and exercises: hash manifest determinism, JWT minting+decoding,
outbox append/flush truncation logic (mocked server), and pull materialization
into a temp dir.

Run: python3 tests/test_sa_cli.py
"""
import sys
import os
import json
import shutil
import base64
import tempfile
import unittest
import importlib.util
import unittest.mock as mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SA_PATH = ROOT / "bin" / "sa"

import importlib.machinery
loader = importlib.machinery.SourceFileLoader("sa_cli", str(SA_PATH))
spec = importlib.util.spec_from_loader("sa_cli", loader)
sa = importlib.util.module_from_spec(spec)
loader.exec_module(sa)


class TestApiKeyHeaders(unittest.TestCase):
    def test_publishable_key_env_override(self):
        with mock.patch.dict(os.environ, {"SA_PUBLISHABLE_KEY": "sb_publishable_TEST"}):
            self.assertEqual(sa.publishable_key(), "sb_publishable_TEST")

    def test_publishable_key_default(self):
        env = dict(os.environ)
        env.pop("SA_PUBLISHABLE_KEY", None)
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(sa, "CLI_CONFIG", Path("/nonexistent/config.json")):
                self.assertEqual(sa.publishable_key(), sa.DEFAULT_PUBLISHABLE_KEY)

    def test_headers_apikey_is_publishable_not_jwt(self):
        fake_jwt = "header.payload.sig"
        h = sa._headers(fake_jwt)
        self.assertEqual(h["Authorization"], f"Bearer {fake_jwt}")
        self.assertNotEqual(h["apikey"], fake_jwt)
        self.assertEqual(h["apikey"], sa.publishable_key())


class TestHashManifest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_deterministic_regardless_of_write_order(self):
        d1 = self.tmp / "a"
        d1.mkdir()
        (d1 / "one.txt").write_text("hello")
        (d1 / "two.txt").write_text("world")
        h1 = sa.hash_manifest(d1)

        d2 = self.tmp / "b"
        d2.mkdir()
        (d2 / "two.txt").write_text("world")
        (d2 / "one.txt").write_text("hello")
        h2 = sa.hash_manifest(d2)

        self.assertEqual(h1, h2)

    def test_changes_on_content_change(self):
        d = self.tmp / "c"
        d.mkdir()
        (d / "f.txt").write_text("v1")
        h1 = sa.hash_manifest(d)
        (d / "f.txt").write_text("v2")
        h2 = sa.hash_manifest(d)
        self.assertNotEqual(h1, h2)

    def test_ignores_pycache(self):
        d = self.tmp / "d"
        d.mkdir()
        (d / "f.txt").write_text("v1")
        h1 = sa.hash_manifest(d)
        pc = d / "__pycache__"
        pc.mkdir()
        (pc / "f.cpython-311.pyc").write_bytes(b"\x00\x01")
        h2 = sa.hash_manifest(d)
        self.assertEqual(h1, h2)


class TestParseSkillFrontmatter(unittest.TestCase):
    """Regression coverage for the YAML block-scalar description bug (fixed
    2026-07-12): parse_skill_frontmatter previously captured only the
    block-scalar indicator token (e.g. literally ">") instead of the
    indented body lines that follow it."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_skill(self, name, frontmatter_body):
        d = self.tmp / name
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\n" + frontmatter_body + "\n---\n\n# Body\n\nSkill body text.\n"
        )
        return d

    def test_folded_block_scalar_description(self):
        d = self._write_skill(
            "folded-skill",
            'name: folded-skill\n'
            'description: >-\n'
            '  This is a folded description that spans\n'
            '  multiple indented lines and should be\n'
            '  joined into one string.\n'
            'metadata:\n'
            '  version: "1.2.3"',
        )
        meta = sa.parse_skill_frontmatter(d)
        self.assertEqual(meta["name"], "folded-skill")
        self.assertEqual(meta["version"], "1.2.3")
        self.assertNotIn(">", meta["description"])
        self.assertIn("folded description", meta["description"])
        self.assertIn("joined into one string", meta["description"])

    def test_literal_block_scalar_description(self):
        d = self._write_skill(
            "literal-skill",
            'name: literal-skill\n'
            'description: |\n'
            '  Line one of the literal description.\n'
            '  Line two of the literal description.\n'
            'metadata:\n'
            '  version: "2.0.0"',
        )
        meta = sa.parse_skill_frontmatter(d)
        self.assertEqual(meta["name"], "literal-skill")
        self.assertEqual(meta["version"], "2.0.0")
        self.assertNotEqual(meta["description"].strip(), "|")
        self.assertIn("Line one of the literal description.", meta["description"])
        self.assertIn("Line two of the literal description.", meta["description"])

    def test_single_line_description_still_works(self):
        d = self._write_skill(
            "simple-skill",
            'name: simple-skill\n'
            'description: "A plain one-line description."\n'
            'metadata:\n'
            '  version: "0.1.0"',
        )
        meta = sa.parse_skill_frontmatter(d)
        self.assertEqual(meta["name"], "simple-skill")
        self.assertEqual(meta["version"], "0.1.0")
        self.assertEqual(meta["description"], "A plain one-line description.")


class TestJWT(unittest.TestCase):
    def test_mint_and_decode(self):
        secret = "test-secret-value"
        token = sa.mint_jwt(secret, role="guild_agent", iss="star-alliance")
        payload = sa.decode_jwt_unverified(token)
        self.assertEqual(payload["role"], "guild_agent")
        self.assertEqual(payload["iss"], "star-alliance")
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)
        # ~10 years out
        self.assertGreater(payload["exp"] - payload["iat"], 9 * 365 * 24 * 3600)

    def test_signature_verifies_with_correct_secret(self):
        secret = "another-secret"
        token = sa.mint_jwt(secret)
        self.assertTrue(sa.verify_jwt(token, secret))

    def test_signature_rejects_wrong_secret(self):
        token = sa.mint_jwt("secret-a")
        self.assertFalse(sa.verify_jwt(token, "secret-b"))

    def test_no_padding_urlsafe(self):
        token = sa.mint_jwt("s")
        for part in token.split(".")[:2]:
            self.assertNotIn("=", part)
            self.assertNotIn("+", part)
            self.assertNotIn("/", part)


class TestOutbox(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._orig_state = sa.STATE_DIR
        self._orig_outbox = sa.OUTBOX_PATH
        sa.STATE_DIR = self.tmp
        sa.OUTBOX_PATH = self.tmp / "outbox.jsonl"

    def tearDown(self):
        sa.STATE_DIR = self._orig_state
        sa.OUTBOX_PATH = self._orig_outbox
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_append_then_read(self):
        sa.outbox_append("turns", {"a": 1})
        sa.outbox_append("events", {"b": 2})
        lines = sa.outbox_read_lines()
        self.assertEqual(len(lines), 2)

    def test_flush_truncates_on_full_success(self):
        sa.outbox_append("turns", {"a": 1})
        sa.outbox_append("turns", {"a": 2})
        with mock.patch.object(sa, "pg_request_safe", return_value=(True, None)):
            summary = sa.outbox_flush(jwt="fake-jwt")
        self.assertEqual(summary["flushed"], 2)
        self.assertEqual(summary["kept"], 0)
        self.assertEqual(sa.outbox_read_lines(), [])

    def test_flush_keeps_rows_on_failure(self):
        sa.outbox_append("turns", {"a": 1})
        with mock.patch.object(sa, "pg_request_safe", return_value=(False, "network error")):
            summary = sa.outbox_flush(jwt="fake-jwt")
        self.assertEqual(summary["flushed"], 0)
        self.assertEqual(summary["kept"], 1)
        self.assertEqual(len(sa.outbox_read_lines()), 1)

    def test_flush_exits_gracefully_with_no_jwt(self):
        sa.outbox_append("turns", {"a": 1})
        summary = sa.outbox_flush(jwt=None)
        # no JWT and no env fallback -> summary should note it, never raise
        self.assertIn("errors", summary)

    def test_flush_partial_failure_keeps_only_failed_table(self):
        sa.outbox_append("turns", {"a": 1})
        sa.outbox_append("events", {"b": 2})

        def fake_pg_request_safe(method, path, jwt, **kw):
            if path == "turns":
                return True, None
            return False, "boom"

        with mock.patch.object(sa, "pg_request_safe", side_effect=fake_pg_request_safe):
            summary = sa.outbox_flush(jwt="fake-jwt")
        self.assertEqual(summary["flushed"], 1)
        self.assertEqual(summary["kept"], 1)
        remaining = sa.outbox_read_lines()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(json.loads(remaining[0])["table"], "events")


class TestPullMaterialize(unittest.TestCase):
    def test_materializes_members_and_skills_into_temp_dir(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            member_dir = tmp / "agents"
            skill_dir = tmp / "skills"

            fake_members = [{"id": "the-tester", "content": "# The Tester\n"}]
            fake_skills = [{"id": "test-skill"}]
            # guild.skill_files rows from PostgREST carry `relpath`, not `path`
            # (2026-07-12 alignment; also exercise the content_b64 branch).
            fake_files = [
                {"relpath": "SKILL.md", "content": "# Test Skill\n"},
                {"relpath": "assets/icon.bin", "content_b64": base64.b64encode(b"\x89PNG\r\n").decode("ascii")},
            ]

            def fake_pg_request_safe(method, path, jwt, **kw):
                if path == "members":
                    return True, fake_members
                if path == "skills":
                    return True, fake_skills
                if path == "skill_files":
                    return True, fake_files
                return False, "unexpected path"

            with mock.patch.object(sa, "pg_request_safe", side_effect=fake_pg_request_safe):
                result = sa.pull_materialize(
                    "fake-jwt",
                    member_target_dirs=[member_dir],
                    skill_target_dirs=[skill_dir],
                )

            self.assertTrue(result["ok"])
            self.assertEqual(result["members"], 1)
            self.assertEqual(result["skills"], 1)
            self.assertTrue((member_dir / "the-tester.md").exists())
            self.assertEqual((member_dir / "the-tester.md").read_text(), "# The Tester\n")
            self.assertTrue((skill_dir / "test-skill" / "SKILL.md").exists())
            self.assertEqual((skill_dir / "test-skill" / "SKILL.md").read_text(), "# Test Skill\n")
            self.assertEqual((skill_dir / "test-skill" / "assets" / "icon.bin").read_bytes(), b"\x89PNG\r\n")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_fails_open_on_network_error(self):
        with mock.patch.object(sa, "pg_request_safe", return_value=(False, "connection refused")):
            result = sa.pull_materialize("fake-jwt")
        self.assertFalse(result["ok"])
        self.assertIn("connection refused", result["reason"])


class TestSchemaContract(unittest.TestCase):
    """Guards the authoritative outbox payload field names against the live
    guild.turns / guild.events / guild.log columns (2026-07-12 alignment)."""

    TURNS_COLS = {
        "client_uuid", "ts", "device_id", "project", "tier",
        "assistant_msgs", "tokens_in", "tokens_out", "cache_read",
        "cache_create", "wall_ms",
    }
    EVENTS_COLS = {
        "client_uuid", "ts", "device_id", "project", "kind", "subject", "detail",
    }
    LOG_COLS = {
        "client_uuid", "entry_date", "type", "title", "who", "detail", "device_id",
    }
    EVENTS_KINDS = {"skill_fire", "spawn", "workflow", "command", "note"}
    # guild.devices: id (PK, text slug), hostname, os_user, repo_root,
    # cli_version, last_seen_at, registered_at (2026-07-12 alignment)
    DEVICES_COLS = {"id", "hostname", "os_user", "repo_root", "cli_version"}
    # guild.members: id, name, description, content, version, status,
    # updated_at, updated_by — NOTE: no content_hash column (that's skills-only)
    MEMBERS_COLS = {"id", "name", "description", "content", "status", "updated_by"}
    # guild.sync_state: PK (device_id, kind); kind in {skills, members}
    SYNC_STATE_COLS = {"device_id", "kind"}
    SYNC_STATE_KINDS = {"skills", "members"}

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._orig_state = sa.STATE_DIR
        self._orig_outbox = sa.OUTBOX_PATH
        sa.STATE_DIR = self.tmp
        sa.OUTBOX_PATH = self.tmp / "outbox.jsonl"

    def tearDown(self):
        sa.STATE_DIR = self._orig_state
        sa.OUTBOX_PATH = self._orig_outbox
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _row_keys(self, row):
        """A flushed row's real column set = payload keys + client_uuid
        (outbox_flush merges client_uuid into payload at flush time)."""
        return set(row["payload"].keys()) | {"client_uuid"}

    def test_cmd_log_payload_matches_guild_log_columns(self):
        args = type("A", (), {"title": "test entry", "type": "note"})()
        sa.cmd_log.__wrapped__ = None  # no-op guard if ever wrapped
        with mock.patch.object(sa, "outbox_flush", return_value={}):
            sa.cmd_log(args)
        lines = sa.outbox_read_lines()
        self.assertEqual(len(lines), 1)
        row = json.loads(lines[0])
        self.assertEqual(row["table"], "log")
        self.assertEqual(self._row_keys(row), self.LOG_COLS)
        # no legacy field names survive
        self.assertNotIn("kind", row["payload"])
        self.assertNotIn("at", row["payload"])

    def test_cmd_log_no_extra_or_missing_columns(self):
        args = type("A", (), {"title": "x", "type": "xp-opening-balance"})()
        with mock.patch.object(sa, "outbox_flush", return_value={}):
            sa.cmd_log(args)
        row = json.loads(sa.outbox_read_lines()[0])
        self.assertEqual(row["payload"]["type"], "xp-opening-balance")
        self.assertRegex(row["payload"]["entry_date"], r"^\d{4}-\d{2}-\d{2}$")

    def test_post_init_device_row_matches_guild_devices_columns(self):
        """Regression guard: devices.id is the PK (a text slug), never
        devices.device_id — that column does not exist."""
        captured = {}

        def fake_pg_request_safe(method, path, jwt, **kw):
            if path == "devices":
                captured["devices_body"] = kw.get("body")
            elif path == "sync_state":
                captured.setdefault("sync_state_bodies", []).append(kw.get("body"))
            return True, "ok"

        with mock.patch.object(sa, "pg_request_safe", side_effect=fake_pg_request_safe):
            with mock.patch.object(sa, "pull_materialize", return_value={"ok": True, "members": 0, "skills": 0}):
                sa._post_init("fake-jwt")

        self.assertIn("devices_body", captured)
        body = captured["devices_body"]
        self.assertEqual(set(body.keys()), self.DEVICES_COLS)
        self.assertNotIn("device_id", body)
        self.assertEqual(body["id"], sa.device_id_slug())

        self.assertIn("sync_state_bodies", captured)
        kinds_seen = {b["kind"] for b in captured["sync_state_bodies"]}
        self.assertEqual(kinds_seen, self.SYNC_STATE_KINDS)
        for b in captured["sync_state_bodies"]:
            self.assertEqual(set(b.keys()), self.SYNC_STATE_COLS)
            self.assertEqual(b["device_id"], sa.device_id_slug())

    def test_push_members_payload_matches_guild_members_columns(self):
        """Regression guard: guild.members has no content_hash column — that
        is a guild.skills-only field. Pushing a member must never send it."""
        tmp_members = self.tmp / "members"
        tmp_members.mkdir()
        (tmp_members / "the-developer.md").write_text("# The Developer\n")
        orig_members_dir = sa.MEMBERS_DIR
        sa.MEMBERS_DIR = tmp_members
        captured = []
        try:
            def fake_pg_request_safe(method, path, jwt, **kw):
                if path == "members":
                    captured.append(kw.get("body"))
                return True, "ok"
            with mock.patch.object(sa, "pg_request_safe", side_effect=fake_pg_request_safe):
                sa._push_members("fake-jwt")
        finally:
            sa.MEMBERS_DIR = orig_members_dir

        self.assertEqual(len(captured), 1)
        body = captured[0]
        self.assertTrue(set(body.keys()).issubset(self.MEMBERS_COLS))
        self.assertNotIn("content_hash", body)
        self.assertEqual(body["id"], "the-developer")

    def test_cmd_doctor_probes_devices_by_id_not_device_id(self):
        """Regression guard: cmd_doctor's reachability probe must select the
        real PK column `id`, never the nonexistent `device_id`."""
        captured = {}

        def fake_pg_request_safe(method, path, jwt, **kw):
            if path == "devices":
                captured["params"] = kw.get("params")
                return True, [{"id": "mac-atta"}]
            return True, []

        with mock.patch.object(sa, "pg_request_safe", side_effect=fake_pg_request_safe):
            with mock.patch.object(sa, "keychain_read_jwt", return_value="fake-jwt"):
                sa.cmd_doctor(type("A", (), {})())

        self.assertEqual(captured["params"].get("select"), "id")

    def test_build_files_payload_is_object_not_array(self):
        """Regression guard for the live 2026-07-12 push_skill failure: the
        RPC does jsonb_each(p_files) on the TOP-LEVEL argument, so p_files
        MUST be a flat {relpath: content} object — an array of
        {path, content, hash} descriptors raises 22023 'cannot call
        jsonb_each on a non-object'."""
        skill_dir = self.tmp / "a-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# hi\n")
        binbytes = b"\x89PNG\r\n"
        (skill_dir / "assets").mkdir()
        (skill_dir / "assets" / "icon.bin").write_bytes(binbytes)

        payload = sa.build_files_payload(skill_dir)
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["SKILL.md"], "# hi\n")
        self.assertIsInstance(payload["assets/icon.bin"], dict)
        self.assertEqual(
            base64.b64decode(payload["assets/icon.bin"]["content_b64"]), binbytes
        )
        # no per-file hash / path keys — those never existed on skill_files
        self.assertNotIn("hash", payload)
        self.assertNotIn("path", payload)


class TestProducerSchemas(unittest.TestCase):
    """Loads turn-cost.py, spawn-log.py, and backfill_guild.py as modules and
    asserts their outbox payloads carry exactly the authoritative columns."""

    TURNS_COLS = TestSchemaContract.TURNS_COLS
    EVENTS_COLS = TestSchemaContract.EVENTS_COLS
    LOG_COLS = TestSchemaContract.LOG_COLS

    @staticmethod
    def _load(name, path):
        loader = importlib.machinery.SourceFileLoader(name, str(path))
        spec = importlib.util.spec_from_loader(name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_turn_cost_outbox_row_matches_guild_turns_columns(self):
        tc = self._load("turn_cost_test", ROOT / ".claude" / "hooks" / "turn-cost.py")
        transcript = self.tmp / "t.jsonl"
        rec = {
            "type": "user", "message": {"content": "hi"},
        }
        asst = {
            "type": "assistant",
            "message": {"usage": {
                "input_tokens": 10, "output_tokens": 20,
                "cache_read_input_tokens": 1, "cache_creation_input_tokens": 2,
            }},
        }
        transcript.write_text(json.dumps(rec) + "\n" + json.dumps(asst) + "\n")

        state_dir = self.tmp / ".claude" / "state"
        state_dir.mkdir(parents=True)
        (state_dir / "turn-start").write_text(str(__import__("time").time()))

        with mock.patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(self.tmp)}):
            with mock.patch.object(sys, "stdin"):
                with mock.patch("json.load", return_value={"transcript_path": str(transcript)}):
                    with self.assertRaises(SystemExit):
                        tc.main()

        outbox = state_dir / "outbox.jsonl"
        self.assertTrue(outbox.exists())
        row = json.loads(outbox.read_text().strip().splitlines()[0])
        self.assertEqual(row["table"], "turns")
        keys = set(row["payload"].keys()) | {"client_uuid"}
        self.assertEqual(keys, self.TURNS_COLS)
        self.assertNotIn("in", row["payload"])
        self.assertNotIn("out", row["payload"])

    def test_backfill_turns_payload_matches_guild_turns_columns(self):
        bf = self._load("backfill_test", ROOT / "tools" / "backfill_guild.py")
        src = self.tmp / "turn-cost.jsonl"
        src.write_text(json.dumps({
            "ts": "2026-07-01T00:00:00Z", "tier": "full", "assistant_msgs": 1,
            "in": 5, "out": 7, "cache_read": 0, "cache_create": 0, "wall_ms": 100,
        }) + "\n")
        bf.TURN_COST_SRC = src
        bf.OUTBOX_PATH = self.tmp / "outbox.jsonl"
        bf.backfill_turns()
        row = json.loads(bf.OUTBOX_PATH.read_text().strip().splitlines()[0])
        self.assertEqual(row["table"], "turns")
        keys = set(row["payload"].keys()) | {"client_uuid"}
        self.assertEqual(keys, self.TURNS_COLS)
        self.assertEqual(row["payload"]["tokens_in"], 5)
        self.assertEqual(row["payload"]["tokens_out"], 7)

    def test_backfill_spawn_events_payload_matches_guild_events_columns(self):
        bf = self._load("backfill_test2", ROOT / "tools" / "backfill_guild.py")
        src = self.tmp / "dispatch-log.jsonl"
        src.write_text(json.dumps({
            "timestamp": "2026-07-01T00:00:00Z", "kind": "spawn",
            "agent": "the-developer", "description": "test",
        }) + "\n")
        bf.DISPATCH_LOG_SRC = src
        bf.OUTBOX_PATH = self.tmp / "outbox.jsonl"
        bf.backfill_spawn_events()
        row = json.loads(bf.OUTBOX_PATH.read_text().strip().splitlines()[0])
        self.assertEqual(row["table"], "events")
        keys = set(row["payload"].keys()) | {"client_uuid"}
        self.assertEqual(keys, self.EVENTS_COLS)
        self.assertEqual(row["payload"]["subject"], "the-developer")
        self.assertEqual(row["payload"]["kind"], "spawn")

    def test_backfill_opening_balance_payload_matches_guild_log_columns(self):
        bf = self._load("backfill_test3", ROOT / "tools" / "backfill_guild.py")
        bf.DISPATCH_LOG_SRC = self.tmp / "nonexistent.jsonl"
        bf.OUTBOX_PATH = self.tmp / "outbox.jsonl"
        bf.MEMBERS = ["the-developer"]
        bf.backfill_member_opening_balances()
        row = json.loads(bf.OUTBOX_PATH.read_text().strip().splitlines()[0])
        self.assertEqual(row["table"], "log")
        keys = set(row["payload"].keys()) | {"client_uuid"}
        self.assertEqual(keys, self.LOG_COLS)
        self.assertEqual(row["payload"]["type"], "xp-opening-balance")

    def test_spawn_log_outbox_row_matches_guild_events_columns_and_no_dual_write(self):
        sl = self._load("spawn_log_test", ROOT / ".claude" / "hooks" / "spawn-log.py")
        outbox = self.tmp / "outbox.jsonl"
        sl.OUTBOX_PATH = outbox
        legacy_mirror = self.tmp / "dispatch-log.jsonl"  # must NOT be written

        stdin_payload = json.dumps({
            "tool_name": "Task",
            "tool_input": {"subagent_type": "the-developer", "description": "x"},
        })
        with mock.patch("sys.stdin") as mock_stdin:
            mock_stdin.read = None
            with mock.patch("json.load", return_value=json.loads(stdin_payload)):
                with self.assertRaises(SystemExit):
                    sl.main()

        self.assertTrue(outbox.exists())
        row = json.loads(outbox.read_text().strip().splitlines()[0])
        self.assertEqual(row["table"], "events")
        keys = set(row["payload"].keys()) | {"client_uuid"}
        self.assertEqual(keys, self.EVENTS_COLS)
        self.assertEqual(row["payload"]["subject"], "the-developer")
        self.assertFalse(legacy_mirror.exists(), "spawn-log.py must no longer dual-write dispatch-log.jsonl")


if __name__ == "__main__":
    unittest.main(verbosity=2)
