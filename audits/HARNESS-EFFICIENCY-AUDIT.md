---
type: Document
title: Harness Efficiency Audit
description: Does the Star Alliance harness achieve its stated goal — save tokens, save time, run efficiently? Verdict + ranked upgrade routes.
timestamp: 2026-06-27T14:00:00Z
---

# Star Alliance — Harness Efficiency Audit

**Question asked:** the repo was built as a harness to *save tokens, save time, and be efficient*. Does it achieve that? Where are the upgrade routes?

**Short verdict:** It achieves the **token-cost** goal convincingly and the **time/efficiency** goal only partially. The core saving engine — offloading generation to cheap models — is real and measurable. But the harness has accreted a **fixed per-turn ceremony tax** and a large **self-maintenance surface** that quietly spend back much of what the engine saves, especially on small tasks. It is efficient at the *batch / campaign* scale it was designed around, and inefficient at the *quick-task* scale it is also used for.

---

## What the harness is (one paragraph)

Three real mechanisms sit under a guild theme:

1. **Arsenal** — stdlib CLIs (`summon.py` → `minimax.py` / `ollama_cloud.py`) that push text generation off Opus onto MiniMax M3 and Ollama-cloud models, with a `usage-log.jsonl` ledger.
2. **Skills + Members** — 51 progressive-disclosure skills and 9 sub-agent definitions, installed into a project's `.claude/` by `install.py`, so context loads on demand and specialist work runs in isolated sub-agent windows.
3. **Hook ring** — `UserPromptSubmit` / `PreToolUse` / `PostToolUse` / `Stop` hooks that inject routing doctrine and mechanically enforce the workflow/banner protocol.

Around those sits a **buildless dashboard** (`build.py` → 423 KB `guild-data.js` → `index.html`/`app.js`/`app.css`) and a `guild/` orchestration layer (`run.py`, `delegate.py`, workflows).

---

## Does it save tokens? **Yes — and it's proven, not asserted.**

`usage-log.jsonl` is the strongest thing in the repo. 549 logged offload calls:

| Model | Calls | Tokens in | Tokens out |
|---|---|---|---|
| minimax-m3 | 545 | 12,608,603 | 1,295,427 |
| kimi-k2.7 | 1 | 1,030 | 8,000 |
| nemotron-3-ultra | 1 | 23 | 175 |
| gemma4 | 2 | 38 | 4 |

~12.6M input tokens of work were processed by MiniMax instead of Opus. Even discounting heavily, that is a large, genuine displacement of premium tokens onto a cheap backend. The architecture that makes this cheap — a one-line `delegate()` wrapper, a single `summon.py` router, telemetry that's best-effort and never breaks the call — is clean and correct. **This is the part of the harness that does its job.**

Two honest caveats:
- The ledger proves *offload volume*, not *net savings*. There's no record of the Opus tokens spent **orchestrating** each offload (the plan→prompt→review loop the doctrine mandates). The harness measures the numerator and not the denominator.
- Offload is concentrated almost entirely on **one** weapon (minimax-m3 = 99% of calls). The other six bench weapons are essentially unused (4 calls total). The "8-weapon arsenal" is, in practice, a 1-weapon arsenal with a large catalogue.

## Does it save time / run efficiently? **Partially — and it taxes itself.**

The cost side is structural and runs on **every turn**, including trivial ones:

1. **Per-prompt doctrine injection.** `guild-routing-gate.sh` prepends ~1,400 words (≈1,850 tokens) of binding routing rules to **every** `UserPromptSubmit`. The hook's own comment calls this "a few hundred tokens" — it is closer to ~1.9k. On a one-line question, the harness pays a near-2k-token premium *before the model reads the question*. Over hundreds of turns this is the largest fixed cost in the system, and it lands on the premium model, not the cheap one.

2. **Mandatory ceremony with no fast path.** `workflow-gate.py` blocks **every tool call** until the turn emits a `🗺 Starmap Workflow Started` banner; `workflow-banner-enforcer.py` blocks **turn-end** if the banner/member roster is missing. There is no "small task" exemption. A two-character typo fix must declare a workflow, emit banners, and clear the gate. This is ceremony optimized for campaigns, applied uniformly to quick fixes — the exact tasks where overhead dominates useful work.

3. **Approval-gate round-trips.** STEP 0 forces a restate-and-halt before any write/build/git op. Correct and valuable for high-stakes work; pure latency tax on the obvious ones. The doctrine says "don't ask permission just to continue," but the hook enforces the halt mechanically — the rule and the enforcement disagree.

4. **Self-maintenance surface.** The harness spends premium tokens maintaining *itself*: `member-table-sync.py` regenerates member tables on every edit, `okf-gate.py` enforces frontmatter, `autocommit.sh` commits on every edit (git log shows long runs of `auto: Edit app.css` / `app.js` noise), and `build.py` (40 KB) regenerates a 423 KB data blob feeding a cosmetic dashboard. None of this touches the user's actual work product. It's a meta-layer with a real, recurring upkeep cost.

**Net:** for a large multi-wave campaign, the fixed ~2k/turn + ceremony is trivial against the offload savings — the harness wins clearly. For a quick question or one-file edit, the ceremony can **exceed** the work, and the harness loses against just asking the model directly. The design implicitly assumes every task is campaign-sized. Most aren't.

---

## Upgrade routes (ranked by impact-to-effort)

### Tier 1 — make it efficient at small scale (highest impact)

1. **Add a task-size fast lane.** Triage in the routing gate: if the prompt is a quick-fix / question / single-file edit, skip the full doctrine injection, the workflow-banner requirement, and the approval halt. Inject the heavy gate **only** for build/campaign/multi-member work. This directly fixes the system's biggest structural inefficiency and helps every small turn.

2. **Shrink the per-turn injection.** The 1,400-word gate repeats stable doctrine that could live in `CLAUDE.md` / member files (loaded once) instead of re-injected every prompt. Cut the `UserPromptSubmit` payload to a ~150-token routing reminder + a pointer. Estimated saving: ~1.7k premium tokens × every turn.

3. **Close the measurement loop.** Log the **orchestration** cost next to offload volume — Opus tokens spent routing/reviewing per delegated call — so the ledger reports *net* savings, not gross offload. Right now the harness can't actually prove its headline claim end-to-end; this makes the claim testable. A `arsenal_usage.py` companion record + a dashboard "net saved" tile.

### Tier 2 — make the saving engine broader and safer

4. **Right-size the arsenal to reality.** Either activate the 6 idle bench weapons (pull the Ollama tags, add one real routing rule that picks them by task shape) or demote them from "loadout" to "catalogue" so members stop carrying weapons they never draw. A 1-weapon arsenal dressed as 8 is honest debt.

5. **Batch the offload calls.** 545 separate `subprocess` MiniMax calls each pay process-spawn + HTTP setup latency. For loops (the campaigns this is built for), a batched/persistent client would cut wall-clock time materially. `delegate()` is the right place to add a batch mode.

6. **Reconcile rule vs. enforcement on the approval gate.** The prose ("proceed without re-asking") and the hook (mechanical halt) contradict. Pick one: either a standing-authorization token the user can grant per session, or drop the prose. Ambiguity here costs a round-trip every time.

### Tier 3 — trim the self-maintenance tax

7. **Quiet autocommit.** Coalesce the `auto: Edit X` commit storm (debounce, or commit per logical change, not per file write). The git history is currently unreadable as a record of intent.

8. **Decouple the dashboard from the work loop.** Regenerate `guild-data.js` on demand / on release, not implicitly via edit hooks. The cosmetic layer shouldn't sit in the critical path of doing real work.

9. **Lean-pass the 6 oversized skills** (`conquering-campaign` is at the ~10k-word Cowork ceiling; `graphify`, `image-to-code`, `imagegen-*`, `brandkit` are over the 500-line ideal). Push detail into `references/` so the skill body — the part that loads into context — stays cheap. The registry already flags these; act on it.

---

## Bottom line

The harness's **thesis is sound and its engine works**: offloading to cheap models is real, measured, and substantial. The failure mode is that it wraps that engine in a **fixed, campaign-grade ceremony** applied to every task regardless of size, and pays a steady **self-upkeep tax** in premium tokens. It is, today, a tool that saves a lot on big jobs and can lose money on small ones.

The single highest-leverage change is **#1 (a task-size fast lane)**: it would let the proven savings engine run without the campaign tax on the 80% of turns that don't need it — turning "efficient at batch scale" into "efficient at every scale," which is what the harness set out to be.
