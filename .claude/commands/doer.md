# /doer — Route bulk work to the executor (minimax-m3)

When you need to do bulk work (≥1.5k tokens of output, or many repetitive
transforms) and you want the executor seat — minimax-m3 — to handle it instead
of doing the work yourself, use this slash command.

Usage:
  /doer <prompt>
  /doer -s <system> <prompt>
  /doer -f <file>          # read prompt from a file

Examples:
  /doer Refactor the auth module to use JWT tokens
  /doer -s "You are a code formatter" -f messy.py
  /doer Summarize the contents of the last 10 sessions

What it does:
  1. Takes your prompt and routes it through `star-alliance-arsenal/summon.py minimax-m3`
  2. Returns the executor's output as text
  3. Logs the doer-summon to the ledger (`doer-summon` signal)

Why use it:
  - It's the ONE-COMMAND path to the executor seat. You don't need to remember
    `Task(model="minimax-m3", prompt="...")` syntax.
  - The executor-enforce hook sees this as a properly-routed doer call, so you
    won't get blocked by the Butler lock.
  - The executor (minimax-m3) is fast and cheap — ~80–100s wall-time for a
    typical bulk job, vs the brain (Sonnet/Opus) which is slower and more
    expensive.

When NOT to use it:
  - Small edits (a few lines, single file): the brain does it inline, offloading
    is net-negative.
  - Tool orchestration (file edits via Edit/Write/Bash): minimax-m3 is text-only
    and can't hold tools; the brain or a spawned agent must do this.
  - High-stakes judgment (architecture decisions, schema design, security review):
    the brain's reasoning quality matters here.

After receiving the output:
  - Review it against your original request (this is the critic step — you are
    the critic for the brain's planner role)
  - Apply the result via Edit/Write or pass it to a downstream tool
  - If the output doesn't match what you asked, run /doer again with a sharper
    prompt — don't try to "fix" the output, get a fresh one from the doer.

Implementation: this command runs
`python3 "$STAR_ALLIANCE_ROOT/star-alliance-arsenal/summon.py" minimax-m3 <args>`
where `$STAR_ALLIANCE_ROOT` is set in `.claude/settings.json` env block.