#!/usr/bin/env bash
# Smoke-test executor-enforce.py against synthetic PreToolUse payloads.
# Each case asserts: stdout+stderr combined, exit code.
#
# Two env contexts:
#   • BUTLER    — CLAUDE_CODE_CHILD_SESSION unset (default; main session)
#   • SUBAGENT  — CLAUDE_CODE_CHILD_SESSION=1  (spawned worker)
set -uo pipefail
cd "$(dirname "$0")"
HOOK="$PWD/executor-enforce.py"
REPO_ROOT="$PWD/.."
PASS=0
FAIL=0

run_case () {
    # Args: env-context, name, payload, expected-exit, expect-block-message
    local ctx="$1" name="$2" payload="$3" expect_exit="$4" expect_block="${5:-no}"
    local out ec
    out=$(CLAUDE_PROJECT_DIR="$REPO_ROOT" CLAUDE_CODE_CHILD_SESSION="$ctx" \
          python3 "$HOOK" <<<"$payload" 2>&1)
    ec=$?
    local label="[$ctx] $name"
    if [[ "$ec" == "$expect_exit" ]]; then
        if [[ "$expect_block" == "yes" && "$out" != *"EXECUTOR ENFORCE"* ]]; then
            printf "  ✗ %-58s exit=%d but stderr missing 'EXECUTOR ENFORCE'\n     out=%s\n" "$label" "$ec" "$out"
            FAIL=$((FAIL+1))
        elif [[ "$expect_block" == "no" && "$out" == *"EXECUTOR ENFORCE"* ]]; then
            printf "  ✗ %-58s unexpected block message\n     out=%s\n" "$label" "$out"
            FAIL=$((FAIL+1))
        else
            printf "  ✓ %-58s exit=%d\n" "$label" "$ec"
            PASS=$((PASS+1))
        fi
    else
        printf "  ✗ %-58s expected exit=%d, got %d\n     out=%s\n" "$label" "$expect_exit" "$ec" "$out"
        FAIL=$((FAIL+1))
    fi
}

# ─── BUTLER (main session) — executor lock fully enforced ────────────────

echo "== BUTLER: Bash summons =="
run_case "" "summon.py minimax-m3 (happy path)" \
    '{"tool_name":"Bash","tool_input":{"command":"python3 arsenal/summon.py minimax-m3 \"refactor X\""}}' \
    0 no
run_case "" "minimax.py direct (happy path)" \
    '{"tool_name":"Bash","tool_input":{"command":"python3 arsenal/minimax.py \"summarize Y\""}}' \
    0 no
run_case "" "summon.py haiku (wrong executor, block)" \
    '{"tool_name":"Bash","tool_input":{"command":"python3 arsenal/summon.py haiku \"bulk\""}}' \
    2 yes
run_case "" "summon.py glm-5.2 (wrong executor, block)" \
    '{"tool_name":"Bash","tool_input":{"command":"summon.py glm-5.2 \"refactor\""}}' \
    2 yes
run_case "" "echo hello (read-only, allow)" \
    '{"tool_name":"Bash","tool_input":{"command":"echo hello"}}' \
    0 no
run_case "" "git status (read-only, allow)" \
    '{"tool_name":"Bash","tool_input":{"command":"git status"}}' \
    0 no
run_case "" "cat file (read-only, allow)" \
    '{"tool_name":"Bash","tool_input":{"command":"cat README.md"}}' \
    0 no
run_case "" "ls (read-only, allow)" \
    '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' \
    0 no
run_case "" "npm test (read-only, allow)" \
    '{"tool_name":"Bash","tool_input":{"command":"npm test"}}' \
    0 no

echo ""
echo "== BUTLER: Bash write commands (Option C — no shell escape) =="
run_case "" "sed -i (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"sed -i s/old/new/g foo.py"}}' \
    2 yes
run_case "" "cat > file (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"cat > foo.py <<EOF\nhello\nEOF"}}' \
    2 yes
run_case "" "echo > file (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"echo hello > foo.py"}}' \
    2 yes
run_case "" "rm file (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"rm foo.py"}}' \
    2 yes
run_case "" "rm -rf (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"rm -rf build/"}}' \
    2 yes
run_case "" "tee file (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"tee foo.py"}}' \
    2 yes
run_case "" "cp src dst (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"cp a.py b.py"}}' \
    2 yes
run_case "" "mv src dst (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"mv a.py b.py"}}' \
    2 yes
run_case "" "touch (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"touch foo.py"}}' \
    2 yes
run_case "" "dd (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"dd if=/dev/zero of=disk.img bs=1M count=10"}}' \
    2 yes

echo ""
echo "== BUTLER: Task/Agent spawns =="
run_case "" "Task: model=minimax-m3 (happy)" \
    '{"tool_name":"Task","tool_input":{"model":"minimax-m3","prompt":"refactor X"}}' \
    0 no
run_case "" "Task: model=sonnet (brain-tier, allow)" \
    '{"tool_name":"Task","tool_input":{"model":"sonnet","prompt":"plan the work"}}' \
    0 no
run_case "" "Task: model=opus (brain-tier, allow)" \
    '{"tool_name":"Task","tool_input":{"model":"opus","prompt":"design the schema"}}' \
    0 no
run_case "" "Task: model=haiku (wrong executor, block)" \
    '{"tool_name":"Task","tool_input":{"model":"haiku","prompt":"refactor X"}}' \
    2 yes
run_case "" "Task: model=glm-5.2 (wrong executor, block)" \
    '{"tool_name":"Task","tool_input":{"model":"glm-5.2","prompt":"summarize"}}' \
    2 yes
run_case "" "Task: no model + small prompt (allow)" \
    '{"tool_name":"Task","tool_input":{"model":"","prompt":"check the lint output"}}' \
    0 no
run_case "" "Task: no model + bulk keyword (block)" \
    '{"tool_name":"Task","tool_input":{"model":"","prompt":"refactor the entire module to async"}}' \
    2 yes

echo ""
echo "== BUTLER: Direct write tools (the new lock) =="
run_case "" "Edit on .py (block)" \
    '{"tool_name":"Edit","tool_input":{"file_path":"a.py","old_string":"x","new_string":"y"}}' \
    2 yes
run_case "" "Write on .py (block)" \
    '{"tool_name":"Write","tool_input":{"file_path":"a.py","content":"hello"}}' \
    2 yes
run_case "" "MultiEdit (block)" \
    '{"tool_name":"MultiEdit","tool_input":{"file_path":"a.py","edits":[]}}' \
    2 yes
run_case "" "NotebookEdit (block)" \
    '{"tool_name":"NotebookEdit","tool_input":{"notebook_path":"a.ipynb"}}' \
    2 yes

echo ""
echo "== BUTLER: Read-only tools (always allowed) =="
run_case "" "Read (allow)" \
    '{"tool_name":"Read","tool_input":{"file_path":"a.py"}}' \
    0 no
run_case "" "Glob (allow)" \
    '{"tool_name":"Glob","tool_input":{"pattern":"**/*.py"}}' \
    0 no
run_case "" "Grep (allow)" \
    '{"tool_name":"Grep","tool_input":{"pattern":"TODO","path":"."}}' \
    0 no
run_case "" "WebFetch (allow)" \
    '{"tool_name":"WebFetch","tool_input":{"url":"https://example.com"}}' \
    0 no
run_case "" "WebSearch (allow)" \
    '{"tool_name":"WebSearch","tool_input":{"query":"python asyncio"}}' \
    0 no
run_case "" "LS (allow)" \
    '{"tool_name":"LS","tool_input":{"path":"."}}' \
    0 no
run_case "" "TodoWrite (allow)" \
    '{"tool_name":"TodoWrite","tool_input":{"todos":[]}}' \
    0 no

echo ""
echo "== BUTLER: MCP tools (write-verb heuristic) =="
run_case "" "mcp__github__create_issue (block)" \
    '{"tool_name":"mcp__github__create_issue","tool_input":{"title":"bug"}}' \
    2 yes
run_case "" "mcp__github__update_issue (block)" \
    '{"tool_name":"mcp__github__update_issue","tool_input":{"number":1}}' \
    2 yes
run_case "" "mcp__postgres__delete_row (block)" \
    '{"tool_name":"mcp__postgres__delete_row","tool_input":{"id":1}}' \
    2 yes
run_case "" "mcp__fs__write_file (block)" \
    '{"tool_name":"mcp__fs__write_file","tool_input":{"path":"a.txt","content":"x"}}' \
    2 yes
run_case "" "mcp__github__get_issue (read verb, allow)" \
    '{"tool_name":"mcp__github__get_issue","tool_input":{"number":1}}' \
    0 no
run_case "" "mcp__postgres__query (read verb, allow)" \
    '{"tool_name":"mcp__postgres__query","tool_input":{"sql":"SELECT 1"}}' \
    0 no
run_case "" "mcp__postgres__list_tables (read verb, allow)" \
    '{"tool_name":"mcp__postgres__list_tables","tool_input":{}}' \
    0 no
run_case "" "mcp__fs__read_file (read verb, allow)" \
    '{"tool_name":"mcp__fs__read_file","tool_input":{"path":"a.txt"}}' \
    0 no
run_case "" "mcp__something__unknown_tool (unknown, allow)" \
    '{"tool_name":"mcp__something__unknown_tool","tool_input":{}}' \
    0 no

echo ""
echo "== BUTLER: Override contract (reason required) =="
run_case "" "Bash: bare SA_ALLOW_EXECUTOR no reason (block)" \
    '{"tool_name":"Bash","tool_input":{"command":"sed -i s/old/new/g foo.py # SA_ALLOW_EXECUTOR"}}' \
    2 yes
run_case "" "Bash: SA_ALLOW_EXECUTOR: <short reason> (block — too short)" \
    '{"tool_name":"Bash","tool_input":{"command":"sed -i s/o/n/ f.py # SA_ALLOW_EXECUTOR: tiny"}}' \
    2 yes
run_case "" "Bash: SA_ALLOW_EXECUTOR: <real reason> (allow + log)" \
    '{"tool_name":"Bash","tool_input":{"command":"sed -i s/old/new/g foo.py # SA_ALLOW_EXECUTOR: one-line typo fix on single file"}}' \
    0 no
run_case "" "Task: bare SA_ALLOW_EXECUTOR no reason (block)" \
    '{"tool_name":"Task","tool_input":{"model":"haiku","prompt":"refactor # SA_ALLOW_EXECUTOR"}}' \
    2 yes
run_case "" "Task: SA_ALLOW_EXECUTOR: <real reason> (allow + log)" \
    '{"tool_name":"Task","tool_input":{"model":"sonnet","prompt":"planning # SA_ALLOW_EXECUTOR: needs Claude judgment for architecture decision"}}' \
    0 no
run_case "" "Task: SA_ALLOW_EXECUTOR with colon separator (allow)" \
    '{"tool_name":"Task","tool_input":{"model":"sonnet","prompt":"design # SA_ALLOW_EXECUTOR: this is a high-stakes architecture decision"}}' \
    0 no
run_case "" "Bash: SA_ALLOW_EXECUTOR mid-string not at end (still allow)" \
    '{"tool_name":"Bash","tool_input":{"command":"echo hello # SA_ALLOW_EXECUTOR: this is informational only, no mutation"}}' \
    0 no

# Confirm the override sentinel was written and contains the reason
echo ""
echo "== Override sentinel =="
(
    cd "$REPO_ROOT"
    rm -f ".claude/state/executor-override-last"
    CLAUDE_PROJECT_DIR="$REPO_ROOT" python3 "$HOOK" <<< '{"tool_name":"Task","tool_input":{"model":"sonnet","prompt":"work # SA_ALLOW_EXECUTOR: this is the test reason that is long enough"}}' >/dev/null 2>&1
    if [[ -f ".claude/state/executor-override-last" ]]; then
        reason=$(cat ".claude/state/executor-override-last")
        if [[ "$reason" == *"test reason that is long enough"* ]]; then
            printf "  ✓ %-58s written\n" "override sentinel contains reason"
            PASS=$((PASS+1))
        else
            printf "  ✗ %-58s wrong content: %s\n" "override sentinel" "$reason"
            FAIL=$((FAIL+1))
        fi
        rm -f ".claude/state/executor-override-last"
    else
        printf "  ✗ %-58s file missing\n" "override sentinel written"
        FAIL=$((FAIL+1))
    fi
)

echo ""
echo "== BUTLER: Bypass token =="
run_case "" "Bash: sed -i with SA_ALLOW_EXECUTOR: <reason> (allow + log)" \
    '{"tool_name":"Bash","tool_input":{"command":"sed -i s/old/new/g foo.py # SA_ALLOW_EXECUTOR: one-line typo fix on a single file"}}' \
    0 no
run_case "" "Edit on .py — bypass only works on the prompt, not Edit args (still block)" \
    '{"tool_name":"Edit","tool_input":{"file_path":"a.py # SA_ALLOW_EXECUTOR: reason that is long enough","old_string":"x","new_string":"y"}}' \
    2 yes

# ─── SUBAGENT (CLAUDE_CODE_CHILD_SESSION=1) — executor seat, full freedom ───

echo ""
echo "== SUBAGENT: spawn-time rules still apply =="
run_case "1" "Task: model=haiku (still block wrong executor)" \
    '{"tool_name":"Task","tool_input":{"model":"haiku","prompt":"refactor X"}}' \
    2 yes
run_case "1" "Task: model=minimax-m3 (happy)" \
    '{"tool_name":"Task","tool_input":{"model":"minimax-m3","prompt":"refactor"}}' \
    0 no
run_case "1" "Bash: summon.py haiku (still block)" \
    '{"tool_name":"Bash","tool_input":{"command":"summon.py haiku \"bulk\""}}' \
    2 yes

echo ""
echo "== SUBAGENT: direct write tools now ALLOWED (it IS the executor) =="
run_case "1" "Edit on .py (allow — subagent is executor)" \
    '{"tool_name":"Edit","tool_input":{"file_path":"a.py","old_string":"x","new_string":"y"}}' \
    0 no
run_case "1" "Write on .py (allow)" \
    '{"tool_name":"Write","tool_input":{"file_path":"a.py","content":"hello"}}' \
    0 no
run_case "1" "MultiEdit (allow)" \
    '{"tool_name":"MultiEdit","tool_input":{"file_path":"a.py","edits":[]}}' \
    0 no
run_case "1" "Bash: sed -i (allow — subagent can do work)" \
    '{"tool_name":"Bash","tool_input":{"command":"sed -i s/old/new/g foo.py"}}' \
    0 no
run_case "1" "Bash: rm (allow)" \
    '{"tool_name":"Bash","tool_input":{"command":"rm build/temp"}}' \
    0 no
run_case "1" "mcp__github__create_issue (allow — subagent is executor)" \
    '{"tool_name":"mcp__github__create_issue","tool_input":{"title":"bug"}}' \
    0 no

# ─── KILL SWITCHES ───

echo ""
echo "== Kill switches =="
# (Skip DISARMED file check — evolution/ is mode 700 and the test can't write
#  it without sudo. The per-hook disarm below exercises the SAME _is_kill_switch
#  code path. Direct verification done out-of-band with chmod.)
mkdir -p "$REPO_ROOT/.claude/state"
touch "$REPO_ROOT/.claude/state/executor-enforce-disarmed"
run_case "" "[per-hook disarm] Butler Edit (allow)" \
    '{"tool_name":"Edit","tool_input":{"file_path":"a.py","old_string":"x","new_string":"y"}}' \
    0 no
rm -f "$REPO_ROOT/.claude/state/executor-enforce-disarmed"

echo ""
echo "== Malformed input (fail open) =="
run_case "" "garbage stdin (allow, fail open)" \
    'not json at all' \
    0 no

echo ""
echo "==== $PASS passed, $FAIL failed ===="
exit $FAIL