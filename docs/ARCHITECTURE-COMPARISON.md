# Architecture Comparison: Three Ways to Run the Guild

**For:** Guild Master
**From:** The Architect
**Date:** June 2026

---

## Summary

The guild can run three ways. Today we use a **hybrid**: a premium AI (Claude) acts as the brain — it plans, judges quality, holds the safety gates, and writes the plain-English reports — while a cheaper AI (Hermes profiles) acts as the muscle, doing the bulk editing, generation, and mechanical grunt work. The alternative is to let one side do everything. Going **Claude-only** means top-quality judgment on every task but at a much higher cost, because we'd be paying premium rates for work that doesn't need premium judgment. Going **Hermes-only** saves money but loses quality on the subtle, high-stakes decisions where the premium brain earns its keep. My recommendation: **keep the hybrid**. It matches each job to the right worker automatically — cheap muscle for grunt work, premium judgment only where it matters — and the safety gates we already built are designed around that split.

---

## Option 1 — TODAY (Hybrid): Claude thinks, Hermes does

The premium AI (Claude) is the orchestrator and judge. It receives orders, plans the work, reviews everything the workers produce, and signs off before anything ships. The Hermes profiles are the workers — they take the plan and execute the bulk: large edits, file generation, mechanical transforms. Both sides share the same skills, the same member roster, and the same safety gates, which are built around this brain/muscle split.

**Pros**
- Each job goes to the right worker: cheap muscle for grunt work, premium judgment only where it matters.
- Cost stays low — the expensive brain is only paid for the thinking, not the typing.
- Safety gates already match this split, so quality control is built in, not bolted on.
- The same skills and roster work on both sides, so there's one source of truth for how the guild operates.

**Cons**
- Two layers to maintain: the Claude side and the Hermes side, plus the bridge between them.
- More moving parts means more places something can silently break.
- The team needs to understand two systems, not one.

---

## Option 2 — CLAUDE-ONLY: one AI does everything

One guild where Claude agents handle all of it — the planning, the judgment, the safety gates, and all the bulk grunt work — using the same skills and roster we have today.

**Pros**
- Simplest to reason about: one system, one set of tools, no bridge to maintain.
- Highest consistent quality — even grunt work gets premium judgment, which means fewer rough edges.
- Fewer moving parts and fewer integration points that can break.

**Cons**
- Significantly more expensive — we'd pay premium rates for mechanical work that doesn't need a premium brain.
- Slower on large bulk tasks, because the premium brain is not optimized for sheer volume of output.
- Overkill: most grunt work doesn't benefit from top-tier judgment, so the extra quality is wasted cost.

---

## Option 3 — HERMES-ONLY: the guild runs itself, no Claude

One guild where Hermes profiles do everything on their own — planning, judgment, bulk work, safety gates — with no Claude in the loop at all.

**Pros**
- Lowest cost — the entire guild runs on the cheaper models.
- One system to maintain, no bridge layer.
- Self-contained: the guild doesn't depend on an external premium service.

**Cons**
- Lower quality on subtle, high-stakes judgment — the kind where a missed nuance or a bad architectural call costs real money downstream.
- Weaker safety review: the gates lose the independent premium-brain check that catches the things a cheaper model misses.
- Riskier for decisions that need depth: architecture, legal-rule modeling, cross-system contracts — exactly the work where being wrong is expensive.

---

## Comparison at a Glance

| | **Cost** | **Quality of Judgment** | **Speed on Bulk Work** | **Simplicity** | **Safety / Reliability** |
|---|---|---|---|---|---|
| **Hybrid (today)** | Low — cheap muscle, premium only for thinking | High — premium brain on the calls that matter | Fast — bulk goes to workers built for volume | Medium — two layers to maintain | Strong — gates built around the brain/muscle split |
| **Claude-only** | High — premium rates on everything, including grunt work | Highest — premium judgment everywhere | Slower — premium brain is not built for sheer volume | High — one system, no bridge | Strong — but the extra quality on grunt work is wasted cost |
| **Hermes-only** | Lowest — everything on cheaper models | Lower — cheaper brain on subtle calls | Fast — same workers, no overhead | High — one self-contained system | Weaker — loses the independent premium-brain check |

---

## Recommendation

**Keep the hybrid.** It matches each job to the right worker automatically — cheap muscle for grunt work, premium judgment only where it matters — which means we get the quality we need on the decisions that count without paying premium rates for the typing. Claude-only buys quality we don't need at a cost we shouldn't pay; Hermes-only saves money but loses quality on exactly the work where being wrong is most expensive.

---

## When You Might Revisit This

- If the Hermes models rise in quality enough to rival Claude on subtle judgment, the case for Hermes-only gets stronger — the quality gap that justifies the hybrid today would narrow.
- If the guild budget tightens significantly, Hermes-only becomes worth a serious look as a cost measure, accepting some quality trade-off.
- If the bridge between the two layers proves consistently fragile or costly to maintain, the simplicity argument for a single-system approach grows.