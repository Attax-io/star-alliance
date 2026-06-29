#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# Star Alliance — DISPATCH ENFORCEMENT unit tests
#
# Exercises dispatch-enforce.py's `check()` gate. The production dispatcher
# (sa-pretool.py) loads the hook module via importlib.util and calls check();
# we mirror that pattern here so the tests run against the real code path.
#
# Cases:
#   1. test_path_with_gt_in_arg_is_allowed   — false-positive regression test
#   2. test_real_redirect_in_child_session_is_blocked
#   3. test_main_session_always_allowed       — is_child guard still works
#   4. test_dispatch_marker_is_allowed        — dispatch.py piggyback allow
#   5. test_sed_in_place_blocked               — unrelated pattern still works
# ─────────────────────────────────────────────────────────────────────────────
import importlib.util
import os
import unittest


HOOK_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "dispatch-enforce.py"
)


def _load_hook():
    """Load dispatch-enforce.py fresh (mirrors sa-pretool.py's loader)."""
    spec = importlib.util.spec_from_file_location("dispatch_enforce", HOOK_PATH)
    assert spec is not None and spec.loader is not None  # always true at runtime
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DispatchEnforceTests(unittest.TestCase):
    def setUp(self):
        # Snapshot env so we can mutate CLAUDE_CODE_CHILD_SESSION per test
        # without leaking state between cases.
        self._saved_env = os.environ.get("CLAUDE_CODE_CHILD_SESSION")
        self.hook = _load_hook()

    def tearDown(self):
        if self._saved_env is None:
            os.environ.pop("CLAUDE_CODE_CHILD_SESSION", None)
        else:
            os.environ["CLAUDE_CODE_CHILD_SESSION"] = self._saved_env

    def _check(self, command, child=True):
        if child:
            os.environ["CLAUDE_CODE_CHILD_SESSION"] = "1"
        else:
            os.environ.pop("CLAUDE_CODE_CHILD_SESSION", None)
        return self.hook.check({
            "tool_name": "Bash",
            "tool_input": {"command": command},
        })

    # ── Regression: false-positive on `>` in filesystem path ──────────────
    def test_path_with_gt_in_arg_is_allowed(self):
        """Bug report: a read-only find|head|echo with `/Users/.../Claude/...`
        in its argument was being matched by the bare `>` redirect pattern."""
        cmd = (
            'f=$(find /Users/attaselim/Documents/Claude/Projects/star-alliance/'
            'star-alliance-skills -iname "SKILL.md" -path "*high-alert*" '
            '2>/dev/null | head -1); echo "$f"; echo "---"; head -60 "$f"'
        )
        result = self._check(cmd, child=True)
        self.assertEqual(
            result["exit"], 0,
            f"Path containing `>` must not trigger redirect block, got: {result}",
        )

    # ── Positive control: real redirect is still blocked ────────────────
    def test_real_redirect_in_child_session_is_blocked(self):
        result = self._check('echo "x" > /tmp/foo', child=True)
        self.assertEqual(result["exit"], 2)
        self.assertIn("DISPATCH ENFORCE", result.get("stderr", ""))

    # ── is_child guard: main session never blocked ──────────────────────
    def test_main_session_always_allowed(self):
        result = self._check('echo "x" > /tmp/foo', child=False)
        self.assertEqual(result["exit"], 0)

    # ── dispatch.py piggyback is allowed for the dispatch sub-command ───
    def test_dispatch_marker_is_allowed(self):
        cmd = 'python3 tools/dispatch.py the-architect "design the schema"'
        result = self._check(cmd, child=True)
        self.assertEqual(result["exit"], 0)

    # ── Unrelated pattern (sed -i) still fires ──────────────────────────
    def test_sed_in_place_blocked(self):
        result = self._check("sed -i 's/a/b/' file.txt", child=True)
        self.assertEqual(result["exit"], 2)
        self.assertIn("DISPATCH ENFORCE", result.get("stderr", ""))


if __name__ == "__main__":
    unittest.main()