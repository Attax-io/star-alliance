---
name: claude-code-hooks
description: "The Developer's craft for authoring Claude Code hooks — the shell scripts the harness fires on tool and session events to enforce guild standards. Covers the event contract (PreToolUse / PostToolUse / UserPromptSubmit / Stop / SessionStart), reading the tool call as JSON on stdin, exit-code semantics (0 allow, 2 block with stderr fed back to the model), JSON output for non-blocking systemMessage banners and additionalContext, matcher scoping in settings.json, and the cardinal rule: fail open so a broken hook never bricks a session. Use when writing, debugging, or hardening a hook, or wiring an automated 'whenever X happens, do Y' behavior the harness must run. Triggers: 'write a hook', 'add a PreToolUse hook', 'gate this tool', 'block this command', 'fire a banner on', 'why is my hook blocking', 'fail-open hook', 'test my hook', 'claude code hooks'. Differentiate from update-config (settings.json keys/permissions) and skillsmith (skill versioning)."
metadata:
  version: 1.2.0
type: Skill

---
# Claude Code Hooks — the Developer's craft

You are the guild's hook-smith. A hook is a shell command the Claude Code harness runs at a fixed
point in the session loop — before a tool fires, after it returns, when the user submits a prompt,
when the agent tries to stop. It is how the whole guild enforces its standards without trusting the
model to remember them: the workflow-gate blocks every tool until a star-map banner is declared, the
okf-gate refuses a non-conformant `.md` write, high-alert stamps a banner the instant a skill fires.
Your craft is to write these correctly — to read the harness's JSON, decide, and either get out of
the way or block with a clear reason — and above all to **fail open**, so a bug in your hook degrades
to a no-op instead of bricking the session.

## What it is / is not

- It IS: author a hook script (read the event JSON on stdin → decide → exit code / JSON output), wire
  it into `settings.json` under the right event + matcher, and test it by piping a synthetic event in.
- It is NOT: `update-config` — that owns the *shape* of `settings.json` (permissions, env, which keys
  exist). You write the *script* a hook entry points at; lean on that skill for the settings plumbing.
- It is NOT: `skillsmith` — hooks are repo tooling, not versioned skills. A hook has no `metadata.version`.
- It is NOT: a place for slow or networked work. Hooks run synchronously in the session's critical
  path; a hook that hangs hangs the session.

## The event contract

| Event | Fires | Can block? | Typical use |
|---|---|---|---|
| **PreToolUse** | before a tool runs | **yes** — exit 2 denies the call | gate tools (workflow-gate, weapon-gate, okf-gate) |
| **PostToolUse** | after a tool returns | no (tool already ran) | auto-commit, lint, side-effect banners |
| **UserPromptSubmit** | user sends a message | yes — exit 2 drops the turn | inject routing context, enforce a pre-turn rule |
| **Stop** | agent attempts to end its turn | yes — exit 2 forces it to continue | banner-enforcer, "did you log it?" gates |
| **SessionStart** | session opens | no | print mode banners, load standing context |

Each hook is invoked with the **event payload as JSON on stdin**. PreToolUse/PostToolUse carry
`tool_name` and `tool_input` (the exact args the model passed); read those to decide. The harness also
passes context (cwd, session id) — parse what you need, ignore the rest.

## Two ways to respond

1. **Exit code (simplest).** `exit 0` = allow / silent. `exit 2` = **block**, and whatever the hook
   wrote to **stderr is fed back to the model** as the reason (PreToolUse, UserPromptSubmit, Stop).
   Any other non-zero is a hook error — surfaced to the user, non-blocking. This is enough for most gates.
2. **JSON on stdout (richer).** Print a JSON object to control the harness precisely:
   `{"decision": "block", "reason": "..."}` to deny; `{"systemMessage": "..."}` to surface a
   **non-blocking banner** without stopping anything; `{"hookSpecificOutput": {"additionalContext": "..."}}`
   (UserPromptSubmit/SessionStart) to inject text the model sees. Use JSON when you need a banner *and*
   an allow, or a structured decision; use the exit code when you just need yes/no.

## The craft

1. **Name the event + the decision.** Which of the five moments? What exactly are you gating or
   announcing? Write the one-line rule before any code — "block any Bash whose command matches `rm -rf /`",
   "banner the instant a Skill tool fires". A hook with a fuzzy rule blocks the wrong thing.
2. **Read stdin as JSON, defensively.** Parse `tool_name` / `tool_input`. **Never assume a field
   exists** — a missing key, a tool you don't recognise, malformed JSON → fall through to allow, not crash.
3. **Decide narrowly.** Match only what you mean to. A `PreToolUse` matcher of `Bash` already scopes
   you to Bash; inside, match the specific command, not a broad substring that catches innocents.
4. **Fail open — the cardinal rule.** Wrap the whole body so that *any* unexpected exception exits 0
   (allow). A hook exists to enforce a standard, not to become a single point of failure that bricks
   every tool call when it throws. A blocked-by-bug session is worse than the unenforced rule.
5. **Block with a usable reason.** On `exit 2`, write to stderr exactly what the model must do to
   proceed — "declare a star-map workflow banner first", not "denied". The reason is the model's only
   guidance; a vague one causes a retry loop.
6. **Wire it in `settings.json`.** Add under `hooks.<Event>` an entry with a `matcher` (tool-name
   regex, or `"*"`) and a `command` (absolute path or `$CLAUDE_PROJECT_DIR`-relative). Keep the script
   executable. Let `update-config` own this edit if you're unsure of the schema.
7. **Test by piping a synthetic event.** Before trusting it live, feed it the JSON the harness would:
   `echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python3 .claude/hooks/your-gate.py;
   echo "exit=$?"`. Prove it blocks the bad case (exit 2 + reason on stderr) AND allows the good case
   (exit 0, silent). An untested hook is a guess.

## Enforcement-gate pitfalls (the false-block failure modes)

An enforcement gate that over-blocks is worse than no gate: it stalls real work and trains everyone to
disarm it. Every rule below is a "gate fired on an innocent call" bug seen in the field — a stall, not
a caught violation. Design against them up front.

- **Anchor the command regex; carve out read-only.** A write-detector like `grep -E 'write|>'` with no
  `^` anchor or word boundary fires on read-only compounds it never meant to catch — `python3 -c '...'`,
  heredocs (`<<'EOF'`), a redirect into the scratchpad, a `git log` whose text merely contains "write".
  Match the actual command *verb* at a boundary, and add an explicit allow-list carve-out: recognised
  read-only tools and any write under the scratchpad / tmp dir pass untouched. (An unanchored gate
  false-blocked ~37% of one agent's read-only calls before it was anchored.)
- **A disarm authorizes the whole operation — never auto-re-arm per tool-call.** A gate that re-arms the
  instant its condition clears will re-block the *next* step of a multi-step repair, deadlocking the very
  fix meant to satisfy it. A disarm or confirmation persists for the entire operation it authorizes;
  model it as an explicit, manual, persistent kill switch (`touch …/disarmed` → `rm` to re-arm), not a
  flag the gate resets after every call.
- **Confirmation classifiers accept the affirmation family, not one exact phrase.** If the gate only
  clears on one canonical string, ordinary approvals — `go`, `yes`, `proceed`, `try again` — get rejected
  and the session stalls at the gate. Match a set of short affirmations, case-insensitive and trimmed.
  Balance the other way too: match genuine affirmations, don't loosen so far you read `no` / `don't` as
  consent.
- **Resolve the repo root dynamically; never hardcode a home path.** A hook with `/Users/<name>/…` baked
  in hard-fails on any other machine, a renamed directory, or a fresh clone. Derive the root from
  `$CLAUDE_PROJECT_DIR`, `git rev-parse --show-toplevel`, or the script's own `__file__` — and if every
  resolution fails, exit 0 (allow), never crash. Portability failures are just fail-open failures wearing
  a different hat.

## Sharpening the craft

You improve along four rungs; your measure is sessions enforced cleanly versus sessions a hook of
yours has wrongly blocked or crashed.

- **Apprentice — exit-coder.** You read stdin, you `exit 2` on a match. You sometimes crash on a field
  that isn't there, and your block reason is too terse to act on. Measure: false-block rate. Outgrow:
  assuming the payload shape; blocking without a usable reason.
- **Journeyman — fail-open hand.** You wrap every hook so an exception allows, you scope the matcher
  tightly, and you write reasons the model can act on. You test both branches before shipping. Measure:
  crash-to-no-op rate (must be 100%), tested-both-branches rate. Outgrow: broad substring matches.
- **Artisan — banner-and-gate.** You reach for JSON output when a hook must both allow and announce,
  you inject `additionalContext` to steer a turn, and you keep hooks off the critical path's slow lane.
  Measure: hooks that hang (must be zero), correct decision shape. Outgrow: doing networked/slow work in a hook.
- **Master — session-warden.** You design the gate before the failure it prevents — you can name the
  exact unenforced behavior each hook closes, and you can predict the innocent call a naive matcher
  would catch. Your hooks never need a hotfix because you tested the edge first. Measure: post-ship
  hook fixes (must trend to zero). Outgrow: confidence without the piped-event proof.

Track, always: false-block rate, crash-to-allow rate (must be 100% — a thrown hook must never block),
hooks that block the wrong tool, hooks that hang the session (must be zero).

## Gotchas

- **A crashing hook blocks the tool.** A non-zero exit from an unhandled exception reads to the harness
  as a hook decision. Always `try/except → exit 0`. Fail open, every time.
- **`exit 2` vs other non-zero.** Only exit 2 is the *block* signal on PreToolUse/UserPromptSubmit/Stop.
  Other non-zero codes surface as a hook *error* and do not block. Don't `sys.exit(1)` meaning to deny.
- **Block reason goes to stderr, not stdout.** On exit 2 the model reads stderr. Print your reason
  there; stdout with a non-zero exit is ignored as the decision channel.
- **The matcher is the first filter.** Scope at the `settings.json` matcher (`"Bash"`, `"Write|Edit"`,
  `"*"`) so the script only runs for relevant tools — cheaper and safer than re-checking inside.
- **PostToolUse can't undo.** The tool already ran. Use it for reactions (commit, lint, banner), never
  to "block" — there's nothing left to block.
- **Stdin is consumed once.** Read it into a variable at the top; you can't re-read the stream.
- **Hooks run synchronously in the loop.** No network calls, no long sleeps, no waiting on a server —
  you're holding up every tool call. Defer slow work to a background job the hook merely triggers.
- **Relative paths resolve against the harness, not your cwd.** Use an absolute path or
  `$CLAUDE_PROJECT_DIR` in the `command`, and make the script `chmod +x`. Inside the script, resolve the
  repo root dynamically (never a hardcoded home path) and fail open if resolution fails.
- **Test the allow branch too.** It's easy to prove a hook blocks; the dangerous bug is one that
  blocks the *good* case. Pipe both a should-block and a should-allow event and check each exit code.

## Proven patterns (Star Alliance harness)

Three patterns mined from the harness-efficiency build — reach for them when the obvious wiring is wasteful or blind:

- **Per-turn coalescing — move bookkeeping off the per-edit path.** Cosmetic/bookkeeping work (regen a view, commit, sync a table) wired on `PostToolUse: Edit|Write` fires **once per file write** — its cost scales with edit count (the `auto: Edit X` commit storm). If the work is a *view* (a dashboard, a table, a commit), move it to a single **`Stop`** hook that runs **once per turn**: regen only if a relevant source changed (`git status --porcelain | grep …`), then coalesce all the turn's changes into ONE commit (`git add -A` + one `commit`). The view lags the repo by at most one turn — acceptable; the critical path stops paying per edit.
- **Marker-injection for measurement.** To record something a hook decided (which branch fired, which tier) for a *later* hook to read: have the deciding hook **inject a unique marker string** into its output (a `UserPromptSubmit` hook prints `SA-GATE:LITE` / `SA-GATE:FULL` into context), then a `Stop` hook **greps the turn's transcript** for that marker and logs it alongside the turn's token usage. The transcript is the shared channel between hooks of different events — no extra state file needed.
- **Proportional injection — tier the output by stakes/size.** A `UserPromptSubmit` hook that injects the SAME heavy doctrine every turn taxes every turn. Classify the prompt against a **policy config** (keyword lists in a JSON file, not buried in shell) on two axes — **stakes** (reversibility/blast-radius) and **size** — and inject a short reminder for clearly-small-and-low-stakes turns, the full doctrine otherwise. **Stakes always beats size; unknown/empty/garbled → heavy (fail-safe).** Gate the whole thing behind an env override (`SA_GATE=full`) so the old uniform behavior is one flag away, and keep the classifier fail-to-heavy: a broken classifier must never *weaken* the gate.

## Bundled

- `scripts/hook_template.py` — a fail-open PreToolUse skeleton: reads stdin JSON, decides, blocks via
  exit 2 + stderr reason, and swallows every exception to exit 0. Copy and fill the decision.
- `scripts/test_hook.sh` — pipes a should-block and a should-allow synthetic event into a hook and
  prints each exit code, so you prove both branches before wiring it live.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new section/template · MAJOR: contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.2.0** — **Enforcement-gate pitfalls section** added, mined from 8 sessions where PreToolUse gates false-positived and stalled real work: (1) anchor the command regex and carve out read-only tools + scratchpad writes — an unanchored write-detector misread `python3 -c`, heredocs, and redirects as writes (~37% false-block rate); (2) a disarm authorizes the whole operation — never auto-re-arm per tool-call, or a mid-repair gate deadlocks the next fix; (3) confirmation classifiers accept the affirmation family (`go`/`yes`/`proceed`/`try again`), not one exact phrase, without loosening onto `no`/`don't`; (4) resolve the repo root dynamically (`$CLAUDE_PROJECT_DIR` / `git rev-parse` / `__file__`) and fail open — a hardcoded home path hard-fails on any other machine. New section → MINOR.
- **1.1.0** — **Proven patterns section** added, mined from the harness-efficiency build: (1) per-turn coalescing — move view/bookkeeping work off `PostToolUse: Edit|Write` (per-edit) onto a single `Stop` hook (per-turn, one coalesced commit), killing the `auto: Edit` storm; (2) marker-injection — a deciding hook prints a unique marker into context, a later `Stop` hook greps the transcript for it (the transcript is the cross-event channel); (3) proportional injection — tier a `UserPromptSubmit` hook's output by a stakes/size policy config, stakes-beats-size, unknown→heavy, env override + fail-to-heavy classifier. New section → MINOR.
- **1.0.0** — Initial release. The Developer's craft for authoring Claude Code hooks: the five-event contract, stdin-JSON parsing, exit-code vs JSON-output decisions, matcher scoping, fail-open discipline, and the pipe-a-synthetic-event test loop — with a fail-open template and a two-branch test harness.