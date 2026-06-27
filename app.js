/* ============================================================================
   Star Alliance — Cosmic Command Center
   app.js — vanilla, buildless. Loads one global: GUILD = {meta,members,skills,domains,log}
   ========================================================================== */
(() => {
"use strict";

/* ── 1. Boot guard ────────────────────────────────────────────────────────── */
const app = document.getElementById("app");
function bootFailed() {
  app.innerHTML = `<div class="state state-error" role="alert">
    <div class="glyph">📡</div>
    <h2>Uplink lost</h2>
    <p>The guild data failed to load. <code>guild-data.js</code> must sit beside
       <code>index.html</code> and define <code>const GUILD</code>. Re-run
       <code>python3 build.py</code>, then reload.</p>
    <button class="btn" onclick="location.reload()">Retry uplink</button>
  </div>`;
}
if (typeof GUILD === "undefined" || !GUILD || !Array.isArray(GUILD.members)) {
  document.addEventListener("DOMContentLoaded", bootFailed);
  return;
}

/* ── 2. Utilities ─────────────────────────────────────────────────────────── */
const esc = (s) => String(s ?? "").replace(/[&<>"']/g,
  (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// NOTE: member.avatar holds trusted, build-time-authored inline SVG (from members-meta.json) and is
// intentionally injected raw (never esc()'d). Avatars must never come from user input — keep them build-only.
const debounce = (fn, ms = 150) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
const byId = (id) => document.getElementById(id);
const pluralize = (n, w) => `${n} ${w}${n === 1 ? "" : "s"}`;

// ════════════════════════════════════════════════════════════════════════
// THE ARMORY — single hand-edited source of truth for every model.
//   call  — how a future run SUMMONS this model. Copy-pasteable. The whole
//           point: stop calling MiniMax-via-Ollama when the DIRECT sub exists.
//   meter — consumption estimate for the Arsenal progress bar. Hand-edited.
//           kind 'sub'  → subscription, no hard cap (striped bar).
//           kind 'off'  → not provisioned (empty bar).
//           kind 'used' → metered: { spent, quota, unit }. est: true labels it.
//   ⚠ NEVER paste a raw API key here — recipes reference the keyFILE on disk.
// ════════════════════════════════════════════════════════════════════════
const MODELS = {
  "opus":             { label: "Opus",            color: "#e8c93a", tier: "Master",  host: "Anthropic · native",  role: "thinker", desc: "Claude Opus 4.8 — the master brain. Orchestrates the guild, reasons deepest, reviews everything. This IS the run.",
    ollama_desc: "Claude Opus 4.8 · Anthropic's most powerful model. Best for complex reasoning, deep analysis, agentic orchestration, and long-horizon planning. Top-tier on MMLU, HumanEval, MATH. Use for hard problems that need the best answer, not the fastest.",
    call: "Native — no script. You ARE Opus, the orchestrator. Delegate sub-work via the Task tool: subagent_type + model:'opus'.\n(python3 star-alliance-arsenal/summon.py opus just echoes this reminder.)",
    meter: { kind: "sub", note: "Claude subscription · unmetered" } },
  "sonnet":           { label: "Sonnet",          color: "#3df0ff", tier: "Thinker", host: "Anthropic · native",  role: "both", desc: "Claude Sonnet 4.6 — the reliable longsword. Fast, balanced daily dispatch.",
    ollama_desc: "Claude Sonnet 4.6 · Balanced speed and intelligence. Near-Opus quality at a fraction of the latency. Excels at coding, writing, analysis, and tool use. The go-to for reliable daily dispatch — fast enough for interactive use, smart enough for hard tasks.",
    call: "Native — no script. Task tool subagent, model:'sonnet'. Or switch the main loop with /model sonnet.",
    meter: { kind: "sub", note: "Claude subscription · unmetered" } },
  "haiku":            { label: "Haiku",           color: "#4ec985", tier: "Light",   host: "Anthropic · native",  role: "doer", desc: "Claude Haiku 4.5 — the stiletto. Fastest and cheapest, for precise quick strikes.",
    ollama_desc: "Claude Haiku 4.5 · Fastest and cheapest Claude. Sub-second responses, ideal for bulk classification, routing, summarization, and mechanical transforms. Use when you need high volume at low cost — not when you need deep reasoning.",
    call: "Native — no script. Task tool subagent, model:'haiku' — cheap mechanical strikes.",
    meter: { kind: "sub", note: "Claude subscription · unmetered" } },
  "gpt-5.5":          { label: "GPT-5.5",         color: "#9d7bff", tier: "Premium", host: "OpenAI · direct",     role: "thinker", desc: "OpenAI GPT-5.5 — a US-hosted frontier second opinion. Premium-priced.",
    ollama_desc: "OpenAI GPT-5.5 · OpenAI's flagship frontier model. Multimodal reasoning, world-class coding, and strong creative generation. Best used as a second opinion on hard problems, cross-validation, or tasks that benefit from a different model family's perspective.",
    call: "python3 star-alliance-arsenal/summon.py gpt-5.5  → reports NOT provisioned (no key on device).\nWhen provisioned: OpenAI direct, POST api.openai.com/v1/chat/completions, Bearer $OPENAI_API_KEY, model:'gpt-5.5'.",
    meter: { kind: "off", note: "Not provisioned — no key on device yet" } },
  "minimax-m3":       { label: "MiniMax M3",      color: "#4ec9a0", tier: "Doer",    host: "MiniMax · DIRECT",    role: "doer", desc: "MiniMax M3 — the crossbow. Cheap, 1M context, fires bulk delegated work at range. Use the DIRECT cloud sub — the old Ollama minimax-m3 route is RETIRED.",
    ollama_desc: "MiniMax M3 · 1M context window, very cheap per token. Strong at long-document analysis, bulk text extraction, and summarization. The guild's primary sub-agent for delegated work. Use for anything where you need to process large inputs at low cost.",
    call: "DIRECT cloud sub — NOT Ollama.\nEasiest:  python3 star-alliance-arsenal/minimax.py \"<prompt>\"\n  flags: -s <system>  --json  -f <file>  (reads stdin if no arg)\nRaw:  POST https://api.minimax.io/v1/text/chatcompletion_v2\n  Authorization: Bearer $(cat ~/.config/minimax/m3.key)\n  body { model:'MiniMax-M3', messages:[…], max_tokens:16000 }",
    meter: { kind: "used", spent: 0, quota: 100, unit: "M tok", est: true, note: "est · set your real plan cap" } },
  "image-01":         { label: "MiniMax Image",   color: "#45c98f", tier: "Forge",   host: "MiniMax · DIRECT",    role: "doer", desc: "MiniMax image-01 — the enchanter's brush. Paints 1024² skill-sigils and battle-standards from a spell-phrase. Forged every art tile in the armory.",
    ollama_desc: "MiniMax image-01 · Text-to-image diffusion. 1024×1024, prompt-driven, strong on stylized/illustrative art. The guild's art forge — skill-art, weapon cards, member portraits. Use for any raster icon or illustration; M3 (text) cannot make pixels.",
    call: "DIRECT cloud · Bearer $(cat ~/.config/minimax/m3.key).\nEasiest:  node gen-skill-art.cjs            (renders skill-art/<id>.png; skips existing, --regen <id> to force)\nRaw:  POST https://api.minimax.io/v1/image_generation\n  body { model:'image-01', prompt:'…', aspect_ratio:'1:1', response_format:'url', n:1 }",
    meter: { kind: "used", spent: 0, quota: 1000, unit: "img", est: true, note: "est · set your real plan cap" } },
  "minimax-video":    { label: "MiniMax Hailuo",  color: "#38c9c0", tier: "Forge",   host: "MiniMax · DIRECT",    role: "doer", desc: "MiniMax Hailuo — the scrying-loom. Weaves short moving visions (text/image → video) for banners and intro stings.",
    ollama_desc: "MiniMax Hailuo video (MiniMax-Hailuo-02 / video-01) · Text-to-video and image-to-video, ~6s 720p clips. Async API: submit → poll task → retrieve file. Use for short motion — animated banners, weapon GIFs, intros.",
    call: "DIRECT cloud · Bearer $(cat ~/.config/minimax/m3.key).  No helper script yet.\nRaw (async):  POST https://api.minimax.io/v1/video_generation  body { model:'MiniMax-Hailuo-02', prompt:'…' } → task_id\n  Poll:  GET /v1/query/video_generation?task_id=…  → file_id\n  Fetch:  GET /v1/files/retrieve?file_id=…   (verify current model tag)",
    meter: { kind: "used", spent: 0, quota: 100, unit: "clip", est: true, note: "est · async video gen · set real cap" } },
  "minimax-speech":   { label: "MiniMax Speech",  color: "#6cc98a", tier: "Forge",   host: "MiniMax · DIRECT",    role: "doer", desc: "MiniMax Speech — the herald's horn. Gives any text a spoken voice (TTS), in many tongues and timbres.",
    ollama_desc: "MiniMax Speech (speech-02-hd / -turbo, T2A v2) · Text-to-speech. Multilingual, many voices, adjustable speed/pitch/emotion. Use for narration, voiced briefings, audio versions of reports.",
    call: "DIRECT cloud · Bearer $(cat ~/.config/minimax/m3.key).  No helper script yet.\nRaw:  POST https://api.minimax.io/v1/t2a_v2  body { model:'speech-02-hd', text:'…', voice_setting:{ voice_id:'…', speed:1 } } → audio\n  (verify current voice ids + model tag)",
    meter: { kind: "used", spent: 0, quota: 1000, unit: "k char", est: true, note: "est · T2A billed per char · set real cap" } },
  "minimax-music":    { label: "MiniMax Music",   color: "#8fc94e", tier: "Forge",   host: "MiniMax · DIRECT",    role: "doer", desc: "MiniMax Music — the bard's lute. Composes scored music from a brief: a mood, a verse, a length.",
    ollama_desc: "MiniMax Music (music-1.5) · Generates instrumental or vocal music from a text brief + optional lyrics. Use for theme music, ambient loops, short scores.",
    call: "DIRECT cloud · Bearer $(cat ~/.config/minimax/m3.key).  No helper script yet.\nRaw:  POST https://api.minimax.io/v1/music_generation  body { model:'music-1.5', prompt:'…', lyrics:'…' }\n  (verify current model tag)",
    meter: { kind: "used", spent: 0, quota: 100, unit: "track", est: true, note: "est · set real cap" } },
  "glm-5.2":          { label: "GLM-5.2",         color: "#d4a05a", tier: "Bench",   host: "Ollama Cloud",        role: "thinker", desc: "GLM-5.2 — the longbow. Coding-first, strong multilingual analysis. Long reach, pulled & ready.",
    ollama_desc: "GLM-5.2 · Zhipu AI's flagship. Coding-first with top LiveCodeBench performance. Strong multilingual capabilities — especially Chinese, Arabic, and European languages. Best for code review, multi-language tasks, and structured analytical work.",
    call: "Easiest:  python3 star-alliance-arsenal/summon.py glm-5.2 \"<prompt>\"\nDirect:  python3 star-alliance-arsenal/ollama_cloud.py glm-5.2:cloud \"<prompt>\"  (-s, --json, -f, stdin)\nOllama Cloud sub · tag glm-5.2:cloud  ✓ pulled",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · shares the Ollama Cloud pool" } },
  "kimi-k2.7":        { label: "Kimi K2.7",       color: "#ff6b8a", tier: "Bench",   host: "Ollama Cloud",        role: "thinker", desc: "Kimi K2.7 — the hammer. Long-horizon coding and agentic work, blunt force done right.",
    ollama_desc: "Kimi K2.7 · Moonshot AI's agentic powerhouse. Designed for long-horizon tool use, autonomous coding, and multi-step debugging. Strong at planning, self-correction, and sustained agentic loops. Best when a task requires many tool calls across a long session.",
    call: "Easiest:  python3 star-alliance-arsenal/summon.py kimi-k2.7 \"<prompt>\"\nDirect:  python3 star-alliance-arsenal/ollama_cloud.py kimi-k2.7-code:cloud \"<prompt>\"\nPull first:  ollama pull kimi-k2.7-code:cloud  ✓ pulled",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · not yet pulled · shares Ollama Cloud pool" } },
  "deepseek-v4-pro":  { label: "DeepSeek V4 Pro", color: "#5b8cff", tier: "Bench",   host: "Ollama Cloud",        role: "thinker", desc: "DeepSeek V4 Pro — the scythe. Wide-sweeping frontier MoE reasoning.",
    ollama_desc: "DeepSeek V4 Pro · Mixture-of-Experts frontier reasoning at low cost. Exceptional at STEM, mathematics, and logical inference. Near GPT-4 quality for a fraction of the price. Best for hard analytical problems, algorithm design, and scientific reasoning.",
    call: "Easiest:  python3 star-alliance-arsenal/summon.py deepseek-v4-pro \"<prompt>\"\nDirect:  python3 star-alliance-arsenal/ollama_cloud.py deepseek-v4-pro:cloud \"<prompt>\"\nPull first:  ollama pull deepseek-v4-pro:cloud  ✓ pulled",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · not yet pulled · shares Ollama Cloud pool" } },
  "nemotron-3-ultra": { label: "Nemotron-3 Ultra",color: "#7fd4ff", tier: "Bench",   host: "Ollama Cloud",        role: "thinker", desc: "Nemotron-3 Ultra — the lance. High-throughput reasoning, long agent runs.",
    ollama_desc: "Nemotron-3 Ultra · NVIDIA's high-throughput reasoning model. Strong at structured data extraction, long-form document analysis, and sustained multi-turn agentic work. Optimized for inference efficiency — best when you need frontier reasoning at scale.",
    call: "Easiest:  python3 star-alliance-arsenal/summon.py nemotron-3-ultra \"<prompt>\"\nDirect:  python3 star-alliance-arsenal/ollama_cloud.py nemotron-3-super:cloud \"<prompt>\"\nPull first:  ollama pull nemotron-3-super:cloud  (NOT pulled yet — pull before use)",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · not yet pulled · shares Ollama Cloud pool" } },
  "qwen3.5":          { label: "Qwen 3.5",        color: "#c47fff", tier: "Bench",   host: "Ollama Cloud",        role: "thinker", desc: "Qwen 3.5 — the shortsword. Versatile general-purpose workhorse.",
    ollama_desc: "Qwen 3.5 · Alibaba's versatile coder. Supports 29 languages, strong structured output, function calling, and API integration. Well-rounded across coding, writing, and analysis. Best for multilingual tasks and general-purpose work where flexibility matters.",
    call: "Easiest:  python3 star-alliance-arsenal/summon.py qwen3.5 \"<prompt>\"\nDirect:  python3 star-alliance-arsenal/ollama_cloud.py qwen3.5:cloud \"<prompt>\"\nPull first:  ollama pull qwen3.5:cloud  ✓ pulled",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · not yet pulled · shares Ollama Cloud pool" } },
  "gemma4":           { label: "Gemma 4",         color: "#ffb04e", tier: "Bench",   host: "Ollama Cloud",        role: "doer", desc: "Gemma 4 — the ninja star. Small, fast, deadly accurate for quick cheap passes.",
    ollama_desc: "Gemma 4 · Google's lightweight open model. Fast, compact, deployable anywhere. Strong instruction following, basic reasoning, and summarization at minimal cost. Best for high-volume quick passes, preprocessing, and tasks where speed and cost trump depth.",
    call: "Easiest:  python3 star-alliance-arsenal/summon.py gemma4 \"<prompt>\"\nDirect:  python3 star-alliance-arsenal/ollama_cloud.py gemma4:cloud \"<prompt>\"\nPull first:  ollama pull gemma4:cloud  ✓ pulled",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · not yet pulled · shares Ollama Cloud pool" } },
};
const modelMeta = (m) => MODELS[m] || { label: m || "—", color: "#8a93ad" };
const modelGlyph = (m) => (modelMeta(m).label).replace(/[^A-Za-z0-9]/g, "").slice(0, 2).toUpperCase();
const ROLE_META = {
  thinker: { label: "Thinker", icon: "role-art/thinker.png", color: "#9d7bff", rule: "Only reasons, plans, analyzes, and orchestrates. Never executes bulk work or fires sub-tasks directly." },
  doer:    { label: "Doer",    icon: "role-art/doer.png",    color: "#ffb04e", rule: "Only executes, produces, writes, and transforms. Never orchestrates other agents or makes high-level decisions." },
  both:    { label: "Both",    icon: "role-art/both.png",    color: "#3df0ff", rule: "Can think and execute. Assign explicitly — don't use as a catch-all." },
};
// The armory display order for the Arsenal page.
const ARSENAL = ["opus", "sonnet", "haiku", "gpt-5.5", "minimax-m3", "image-01", "minimax-video", "minimax-speech", "minimax-music", "glm-5.2", "kimi-k2.7", "deepseek-v4-pro", "nemotron-3-ultra", "qwen3.5", "gemma4"];
// model id → the ollama `:cloud` tag we expect, so /api/arsenal can mark it pulled.
// MUST match summon.py's CLOUD_TAG (the routing source of truth) and what
// `ollama list` actually shows — otherwise the pulled badge lies.
const CLOUD_TAG = {
  "minimax-m3": "minimax-m3:cloud", "glm-5.2": "glm-5.2:cloud", "kimi-k2.7": "kimi-k2.7-code:cloud",
  "deepseek-v4-pro": "deepseek-v4-pro:cloud", "nemotron-3-ultra": "nemotron-3-super:cloud",
  "qwen3.5": "qwen3.5:cloud", "gemma4": "gemma4:cloud",
};

// ── Live Arsenal data (real pulled-status + real spend) from the dev server's
//    /api/arsenal route. Degrades silently to the hand-edited estimates when the
//    page is opened over file:// (no server) — the dashboard stays buildless.
let arsenalLive = null;          // last server payload, or null until first success
let arsenalApplied = false;      // guards against the refreshView() → afterRender() refetch loop
let arsenalFetching = false;

async function refreshArsenalData() {
  if (arsenalFetching) return;
  arsenalFetching = true;
  try {
    const r = await fetch("/api/arsenal", { cache: "no-store" });
    if (!r.ok) throw new Error("bad status " + r.status);
    const data = await r.json();
    arsenalLive = data;
    const pulled = new Set(data.pulled || []);
    // Merge into MODELS: real pulled flag + real spend overwrites the estimate.
    ARSENAL.forEach((id) => {
      const mm = MODELS[id]; if (!mm) return;
      const tag = CLOUD_TAG[id];
      mm._pulled = tag ? pulled.has(tag) : undefined;     // undefined = N/A (native/direct API)
    });
  } catch (_) {
    arsenalLive = arsenalLive || { offline: true };       // mark "no server" once
  } finally {
    arsenalFetching = false;
    arsenalApplied = true;
    if ((location.hash.split("?")[0] || "").includes("arsenal")) refreshView();
  }
}

/* ── 3. Data indices (built once) ─────────────────────────────────────────── */
const byMember = new Map(GUILD.members.map((m) => [m.id, m]));
const bySkill  = new Map(GUILD.skills.map((s) => [s.id, s]));
const byDomain = new Map(GUILD.domains.map((d) => [d.id, d]));
// Sectors (project domains) whose config lists this skill. The home domain lists
// the whole pool, so membership alone can't say global vs sector-specific — the
// skill's own `global` flag (installed at ~/.claude/skills) is the real signal.
const skillSectors = (id) => GUILD.domains.filter((d) => (d.skills || []).includes(id));
const skillScopeTip = (s) => s.global
  ? "Global skill — installed at ~/.claude/skills, available in every sector"
  : `Sector-specific — ${skillSectors(s.id).map((d) => d.name).join(", ") || "not deployed to any sector yet"}`;
const logEntries = (GUILD.log && GUILD.log.entries) || [];
// ── Per-agent overrides — "what-if" edits, persisted per browser in localStorage.
// overrides = { "<memberId>": { add:[skillId…], remove:[skillId…], block:[skillId…] } }
//   add     — skills assigned beyond the agent's base set
//   remove  — base skills unassigned from the agent
//   block   — assigned skills disabled (kept in the list, but inert)
// ASSIGNED = base − remove + add.   EFFECTIVE = assigned − block.
// EFFECTIVE drives every derived view: star map links, carrier counts, roster chips.
let overrides = {};
try { overrides = JSON.parse(localStorage.getItem("sa-overrides") || "null") || {}; } catch (_) { overrides = {}; }
if (!Object.keys(overrides).length) {
  // one-time migration from the older blocks-only store
  try {
    const old = JSON.parse(localStorage.getItem("sa-blocks") || "null");
    if (old) { for (const mid in old) overrides[mid] = { add: [], remove: [], block: (old[mid] || []).slice() }; }
  } catch (_) {}
  try { localStorage.removeItem("sa-blocks"); } catch (_) {}
}
function saveOverrides() { try { localStorage.setItem("sa-overrides", JSON.stringify(overrides)); } catch (_) {} }
const getOv = (mid) => overrides[mid] || { add: [], remove: [], block: [] };
const ensureOv = (mid) => (overrides[mid] || (overrides[mid] = { add: [], remove: [], block: [] }));
function cleanOv(mid) { const o = overrides[mid]; if (o && !o.add.length && !o.remove.length && !o.block.length) delete overrides[mid]; }
const pull = (arr, v) => { const i = arr.indexOf(v); if (i >= 0) arr.splice(i, 1); };

function toggleBlock(mid, sid) { const o = ensureOv(mid); o.block.includes(sid) ? pull(o.block, sid) : o.block.push(sid); cleanOv(mid); saveOverrides(); }
function unassign(mid, sid) {
  const o = ensureOv(mid), base = byMember.get(mid).skills;
  pull(o.block, sid);                                  // an unassigned skill can't stay blocked
  if (base.includes(sid)) { if (!o.remove.includes(sid)) o.remove.push(sid); } else pull(o.add, sid);
  cleanOv(mid); saveOverrides(); saveMemberField(mid, "skills");
}
function assign(mid, sid) {
  const o = ensureOv(mid), base = byMember.get(mid).skills;
  pull(o.block, sid);                                  // (re)assigning clears any stale block
  if (base.includes(sid)) pull(o.remove, sid);         // re-assign a previously removed base skill
  else if (!o.add.includes(sid)) o.add.push(sid);
  cleanOv(mid); saveOverrides(); saveMemberField(mid, "skills");
}
const resetMember = (mid) => { delete overrides[mid]; saveOverrides(); };
const resetAll = () => { overrides = {}; disabled = []; saveOverrides(); saveDisabled(); };
const memberHasOverrides = (mid) => { const o = overrides[mid]; return !!o && (o.add.length || o.remove.length || o.block.length); };
const totalOverrides = () => Object.values(overrides).reduce((n, o) => n + o.add.length + o.remove.length + o.block.length, 0) + disabled.length;

// Skill-set views (override-aware) + the live carrier helpers that replace the build-time reverse index.
const isBlocked = (mid, sid) => getOv(mid).block.includes(sid);
function assignedSkills(m) {
  const o = getOv(m.id);
  const base = m.skills.filter((s) => !o.remove.includes(s));
  const added = o.add.filter((s) => bySkill.has(s) && !m.skills.includes(s));
  return base.concat(added);
}
// Guild-wide kill switch — a deactivated skill is inert for EVERY agent at once.
let disabled = [];
try { disabled = JSON.parse(localStorage.getItem("sa-disabled") || "[]") || []; } catch (_) { disabled = []; }
GUILD.skills.forEach((s) => { if (s.disabled && !disabled.includes(s.id)) disabled.push(s.id); });  // seed from source
const saveDisabled = () => { try { localStorage.setItem("sa-disabled", JSON.stringify(disabled)); } catch (_) {} };
const isDisabled = (sid) => disabled.includes(sid);
const toggleDisabled = (sid) => { isDisabled(sid) ? pull(disabled, sid) : disabled.push(sid); saveDisabled(); postSave({ kind: "skill-flag", skill: sid, disabled: isDisabled(sid) }); };

// ── Generic source write-through (control panel). True on server-confirmed save. Offline → false (overlay keeps it).
async function postSave(payload) {
  try {
    const r = await fetch("/api/save", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const d = await r.json();
    return !!(d && d.ok);
  } catch (_) { return false; }
}
async function saveMemberEdit(el) {
  const field = el.dataset.medit, mid = el.dataset.member; if (!field || !mid) return;
  const text = (el.innerText || el.textContent || "").trim();
  const m = byMember.get(mid) || {};
  const cur = field === "prompt" ? (m.prompt || "") : (m[field] || "");
  if (cur === text) return;                                   // no change → no write/rebuild
  let payload;
  if (field === "description") payload = { kind: "member-description", member: mid, text };
  else if (field === "prompt") payload = { kind: "member-body", member: mid, text };
  else payload = { kind: "member-meta", member: mid, fields: { [field]: text } };
  const ok = await postSave(payload);
  el.classList.toggle("edit-unsaved", !ok);
  if (ok) { if (field === "prompt") m.prompt = text; else m[field] = text; }
}
async function deleteMemberUI(mid) {
  if (!confirm("Delete member \u201c" + mid + "\u201d? Removes its .md file and roster entry.")) return;
  if (await postSave({ kind: "member-delete", member: mid })) { location.hash = "#/members"; location.reload(); }
  else alert("Delete failed \u2014 is the dev server running?");
}
async function createMemberUI() {
  const id = (prompt("New member id (kebab-case, e.g. the-scribe):") || "").trim(); if (!id) return;
  if (!/^[a-z0-9-]+$/.test(id)) { alert("id must be kebab-case [a-z0-9-]"); return; }
  const name = (prompt("Display name:", id) || id).trim();
  const role = (prompt("Role / one-line description:", "") || "").trim();
  if (await postSave({ kind: "member-create", member: id, opts: { name, role, model: "sonnet", skills: [], weapons: [] } })) { location.hash = "#/members/" + id; location.reload(); }
  else alert("Create failed \u2014 member may exist, or the dev server is off.");
}

// Guild-wide weapon kill switch — a deactivated weapon is hidden from all agent loadouts.
let disabledWeapons = [];
try { disabledWeapons = JSON.parse(localStorage.getItem("sa-disabled-weapons") || "[]") || []; } catch (_) { disabledWeapons = []; }
// Seed deactivations from source — members-meta.json weaponStatus marks weapons dark/deactivated at the guild level.
for (const wid of Object.keys((GUILD.meta && GUILD.meta.weaponStatus) || {})) { if (!disabledWeapons.includes(wid)) disabledWeapons.push(wid); }
const saveDisabledWeapons = () => { try { localStorage.setItem("sa-disabled-weapons", JSON.stringify(disabledWeapons)); } catch (_) {} };
const isWeaponDisabled = (mid) => disabledWeapons.includes(mid);
const toggleWeaponDisabled = (mid) => { isWeaponDisabled(mid) ? pull(disabledWeapons, mid) : disabledWeapons.push(mid); saveDisabledWeapons(); };

const effectiveSkills = (m) => assignedSkills(m).filter((s) => !isBlocked(m.id, s) && !isDisabled(s));
const liveCarriers = (sid) => GUILD.members.filter((m) => effectiveSkills(m).includes(sid)).map((m) => m.id);
const liveFreq = (sid) => liveCarriers(sid).length;
const isShared = (id) => liveFreq(id) > 1;

// ── Per-agent WEAPON (model) overrides — assign/revoke models per agent, persisted per browser.
// weaponOv = { "<memberId>": { add:[modelId…], remove:[modelId…] } }
//   add    — models granted beyond the agent's base loadout
//   remove — base models revoked from the agent
// EFFECTIVE loadout = base − remove + add.
let weaponOv = {};
try { weaponOv = JSON.parse(localStorage.getItem("sa-weapons") || "null") || {}; } catch (_) { weaponOv = {}; }
function saveWeapons() { try { localStorage.setItem("sa-weapons", JSON.stringify(weaponOv)); } catch (_) {} }
const getWov = (mid) => weaponOv[mid] || { add: [], remove: [] };
const ensureWov = (mid) => (weaponOv[mid] || (weaponOv[mid] = { add: [], remove: [] }));
function cleanWov(mid) { const o = weaponOv[mid]; if (o && !o.add.length && !o.remove.length && !(o.order && o.order.length)) delete weaponOv[mid]; }
const baseWeapons = (m) => m.weapons.map((w) => w.model);
// Does this agent currently wield this model?
function wields(m, model) {
  const o = getWov(m.id);
  if (o.remove.includes(model)) return false;
  if (o.add.includes(model)) return true;
  return baseWeapons(m).includes(model);
}
// Ordered effective loadout as {model, desc, added} — base order first, then granted extras.
function effectiveWeapons(m) {
  const o = getWov(m.id), out = [];
  for (const w of m.weapons) { if (!o.remove.includes(w.model)) out.push({ model: w.model, desc: w.desc, added: false }); }
  for (const model of o.add) { if (!baseWeapons(m).includes(model)) out.push({ model, desc: modelMeta(model).desc || "", added: true }); }
  if (o.order && o.order.length) {
    const byModel = new Map(out.map(w => [w.model, w]));
    const ordered = [];
    for (const model of o.order) { if (byModel.has(model)) { ordered.push(byModel.get(model)); byModel.delete(model); } }
    for (const w of byModel.values()) ordered.push(w);
    return ordered;
  }
  return out;
}
function grantModel(mid, model) {
  const o = ensureWov(mid), m = byMember.get(mid);
  pull(o.remove, model);
  if (!baseWeapons(m).includes(model) && !o.add.includes(model)) o.add.push(model);
  cleanWov(mid); saveWeapons(); saveMemberField(mid, "weapons");
}
function revokeModel(mid, model) {
  const o = ensureWov(mid), m = byMember.get(mid);
  pull(o.add, model);
  if (baseWeapons(m).includes(model) && !o.remove.includes(model)) o.remove.push(model);
  cleanWov(mid); saveWeapons(); saveMemberField(mid, "weapons");
}
const toggleWield = (mid, model) => { const m = byMember.get(mid); wields(m, model) ? revokeModel(mid, model) : grantModel(mid, model); };
const resetAllWeapons = () => { weaponOv = {}; saveWeapons(); };

// ── Control-panel write-through: persist a member's loadout to its source .md
//    via the dev server, then fold the change into the in-memory base so the
//    overlay == source. No server (file://) → keep the localStorage overlay (fallback).
async function saveMemberField(mid, field) {
  const m = byMember.get(mid); if (!m) return;
  const values = field === 'skills' ? assignedSkills(m) : effectiveWeapons(m).map((w) => w.model);
  const payload = { kind: 'member-field', member: mid, field, values };
  if (field === 'weapons') { payload.desc = {}; values.forEach((mdl) => { payload.desc[mdl] = (MODELS[mdl] && MODELS[mdl].desc) || ''; }); }
  let d;
  try {
    const r = await fetch('/api/save', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload) });
    d = await r.json();
  } catch (_) { return; }                 // offline → overlay is the fallback
  if (!d || !d.ok) return;                // server rejected → keep overlay
  if (field === 'skills') {
    m.skills = values.slice();
    const o = overrides[mid]; if (o) { o.add = []; o.remove = []; } cleanOv(mid); saveOverrides();
  } else {
    m.weapons = effectiveWeapons(m).map((w) => ({ model: w.model, desc: w.desc }));
    delete weaponOv[mid]; saveWeapons();
  }
  refreshView();
}
function reorderWeapons(mid, orderedModels) { ensureWov(mid).order = orderedModels.slice(); cleanWov(mid); saveWeapons(); }
function resetWeaponOrder(mid) { const o = weaponOv[mid]; if (o) delete o.order; cleanWov(mid); saveWeapons(); }

// Assign-panel UI state (preserved across in-place refreshes, reset on real navigation).
let assignOpenFor = null, assignQuery = "";

const searchIndex = [
  ...GUILD.members.map((m) => ({ kind: "member", id: m.id, label: m.name, sub: m.role, icon: "◆", hash: `#/members/${m.id}`, hay: `${m.name} ${m.role} ${m.summary}`.toLowerCase() })),
  ...GUILD.skills.map((s) => ({ kind: "skill", id: s.id, label: s.name, sub: s.blurb, icon: s.icon, hash: `#/skills/${s.id}`, hay: `${s.id} ${s.name} ${s.blurb} ${s.level}`.toLowerCase() })),
  ...GUILD.domains.map((d) => ({ kind: "sector", id: d.id, label: d.name, sub: d.tagline, icon: d.icon, hash: `#/domains/${d.id}`, hay: `${d.name} ${d.tagline}`.toLowerCase() })),
];

/* ── 4. Hash router ───────────────────────────────────────────────────────── */
function parseHash() {
  const raw = location.hash.replace(/^#\/?/, "");
  const [pathPart, queryPart = ""] = raw.split("?");
  const segments = pathPart.split("/").filter(Boolean);
  return { segments, query: new URLSearchParams(queryPart) };
}

const ROUTES = {
  map:     { list: renderStarMap,      navKey: "map" },
  members: { list: renderMembers,      detail: renderMemberDossier, navKey: "members" },
  arsenal: { list: renderArsenal,      navKey: "arsenal" },
  skills:  { list: renderSkills,       detail: renderSkillPanel,    navKey: "skills" },
  domains: { list: renderDomains,      detail: renderSectorDetail,  navKey: "domains" },
  log:     { list: renderLog,          navKey: "log" },
};

function onRoute() {
  assignOpenFor = null; assignQuery = "";  // close any assign panel when navigating
  arsenalApplied = false;                  // a real navigation re-arms the Arsenal live-fetch
  const { segments, query } = parseHash();
  const key = segments[0] || "map";
  const route = ROUTES[key];
  if (!route) { mount(renderNotFound(), null); return; }  // null → no nav link highlighted on a 404

  let html;
  if (segments[1] && route.detail) html = route.detail(segments[1], query);
  else html = route.list(query);

  mount(html, route.navKey);
  afterRender(key, segments, query);
}

function mount(html, navKey) {
  app.innerHTML = `<div class="view-enter">${html}</div>`;
  setActiveNav(navKey);
  app.focus({ preventScroll: true });
  const h1 = app.querySelector("h1, [data-focus]");
  if (h1) { h1.setAttribute("tabindex", "-1"); h1.focus({ preventScroll: true }); }
  window.scrollTo({ top: 0, behavior: "instant" in document.documentElement.style ? "instant" : "auto" });
}

// Re-render the current view in place after a block toggle. Preserves scroll position and
// skips the entrance animation + heading-focus that mount() does on real navigation.
function refreshView() {
  const y = window.scrollY;
  const { segments, query } = parseHash();
  const route = ROUTES[segments[0] || "map"];
  if (!route) return;
  app.innerHTML = (segments[1] && route.detail) ? route.detail(segments[1], query) : route.list(query);
  setActiveNav(route.navKey);
  afterRender(segments[0] || "map", segments, query);
  setFooter();
  window.scrollTo({ top: y });
}

function setActiveNav(navKey) {
  document.querySelectorAll("#nav a").forEach((a) => {
    if (a.dataset.nav === navKey) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  byId("nav").classList.remove("open");
  byId("nav-toggle").setAttribute("aria-expanded", "false");
}

/* ── 5. Shared partials ───────────────────────────────────────────────────── */
const viewHead = (eyebrow, title, sub) => `
  <header class="view-head">
    <div class="view-eyebrow">${esc(eyebrow)}</div>
    <h1 class="view-title">${esc(title)}</h1>
    ${sub ? `<p class="view-sub">${sub}</p>` : ""}
  </header>`;

const crumb = (href, label) => `<a class="crumb" href="${href}">← ${esc(label)}</a>`;
const rampClass = (s) => `ramp ramp-${esc(s.ramp || "gray")}`;

// Member craft-level (Wave 2 build.py emits m.conferred + m.levelInfo). A level is a
// craft-depth meter, decoupled from standing — see STRATEGIST-MEMBER-LEVELING.md.
const memberRamp = (m) => `ramp ramp-${esc((m.levelInfo && m.levelInfo.rampConferred) || "gray")}`;
function memberLevelBadge(m) {
  const li = m.levelInfo || {};
  const due = li.dueForPromotion;
  const tip = due ? ` title="Earned ${esc(li.earned)} — promotion due"`
                  : (li.overConferred ? ` title="Arsenal regressed below ${esc(m.conferred)} — review"` : "");
  return `<span class="tag ${memberRamp(m)} mc-level"${tip}>${esc(m.conferred || "Foundational")}${due ? " ↑" : (li.overConferred ? " ↓" : "")}</span>`;
}
function memberLevelSection(m) {
  const li = m.levelInfo;
  if (!li) return "";
  const prog = li.progress || [];
  const met = prog.filter((r) => r.ok).length;
  const total = prog.length;
  const pct = total ? Math.round((100 * met) / total) : 100;
  const reqRows = prog.map((r) => {
    const val = "have" in r ? `${r.have}/${r.need}` : (r.ok ? "✓" : "—");
    return `<div class="lvl-req ${r.ok ? "ok" : "todo"}"><span class="lvl-box">${r.ok ? "✓" : "○"}</span><span class="lvl-rlabel">${esc(r.label)}</span><span class="lvl-rval">${esc(val)}</span></div>`;
  }).join("");
  const statusChip = li.dueForPromotion
    ? `<span class="tag amber">earned ${esc(li.earned)} — promotion due</span>`
    : (li.overConferred ? `<span class="tag rose">over-conferred — review</span>` : `<span class="lvl-settled">✓ settled</span>`);
  const nextBlock = li.nextTier
    ? `<div class="lvl-next">Next tier <strong>${esc(li.nextTier)}</strong> — ${met}/${total} prerequisites met
         <div class="lvl-bar"><span style="width:${pct}%"></span></div>
         <div class="lvl-reqs">${reqRows}</div></div>`
    : `<div class="lvl-next lvl-ceiling">At the ceiling — ${esc(m.conferred)} is the top tier.</div>`;
  return `<div class="section glass">
      <div class="section-title">Craft level</div>
      <div class="lvl-head">
        <span class="tag ${memberRamp(m)} lvl-current">${esc(m.conferred || "Foundational")}</span>
        <span class="lvl-ad">Arsenal Depth ${li.ad}</span>
        ${statusChip}
      </div>
      ${nextBlock}
      <p class="skill-hint">Level meters craft depth (arsenal + specialty), <strong>not</strong> standing. The Quartermaster confers it when the checklist is met (<code>member_level.py</code>).</p>
    </div>`;
}
// skill art: PNG from skill-art/<id>.png takes priority, then inline SVG, then emoji fallback.
const skillArt = (s) => {
  if (!s) return `<span class="ico-emoji">📦</span>`;
  if (s.artPng) return `<img class="skill-art-img" src="skill-art/${esc(s.id)}.png" alt="${esc(s.name)}" loading="lazy">`;
  if (s.art) return s.art;
  return `<span class="ico-emoji">${esc(s.icon || "📦")}</span>`;
};

function skillChip(id, mid) {
  const s = bySkill.get(id);
  const name = s ? s.name : id;
  const blocked = mid && isBlocked(mid, id);
  const cls = "tag" + (isShared(id) ? " shared" : "") + (blocked ? " blocked" : "");
  return `<a class="${cls}" href="#/skills/${esc(id)}">${s ? esc(s.icon) + " " : ""}${esc(name)}</a>`;
}

function skillIconTile(sid, mid) {
  const s = bySkill.get(sid);
  if (!s) return "";
  const blocked = mid && isBlocked(mid, sid);
  const img = s.artPng
    ? `<img class="sit-img" src="skill-art/${esc(s.id)}.png" alt="${esc(s.name)}" loading="lazy">`
    : s.art
      ? `<span class="sit-svg">${s.art}</span>`
      : `<span class="sit-emoji">${esc(s.icon || "📦")}</span>`;
  const lvl = esc(s.level || "");
  const blurb = esc(s.blurb || "");
  return `<a class="sit${blocked ? " sit-blocked" : ""}" href="#/skills/${esc(sid)}"
      data-tip-name="${esc(s.name)}" data-tip-level="${lvl}" data-tip-blurb="${blurb}"
      aria-label="${esc(s.name)}${blocked ? " (blocked)" : ""}">${img}</a>`;
}

function memberCard(m) {
  const assigned = assignedSkills(m);
  const MAX = 8;
  const shown = assigned.slice(0, MAX).map((s) => skillIconTile(s, m.id)).join("");
  const extra = assigned.length > MAX ? `<span class="sit-extra">+${assigned.length - MAX}</span>` : "";
  const active = effectiveSkills(m).length;
  const blocked = assigned.length - active;
  // role=link (not <a>): skill icon tiles inside are real anchors — no nesting <a> in <a>.
  return `<div class="member-card glass" role="link" tabindex="0" data-href="#/members/${esc(m.id)}"
       aria-label="${esc(m.name)} — ${esc(m.role)}" style="--mc:${esc(m.color)}" data-id="${esc(m.id)}">
    <div class="mc-portrait-wrap">
      <img class="mc-portrait" src="member-art/${esc(m.id)}.png" alt="${esc(m.name)} portrait" loading="lazy">
    </div>
    <div class="mc-top">
      <div class="avatar">${m.avatar || ""}</div>
      <div><div class="mc-name">${esc(m.name)}</div><div class="mc-role">${esc(m.role)}</div></div>
    </div>
    <div class="mc-skills">${shown}${extra}</div>
    <div class="mc-foot">
      <span>${pluralize(active, "skill")}${blocked ? ` <span class="blk-note">· ${blocked} blocked</span>` : ""}</span>
      <span class="sep"></span><span>${pluralize(m.weapons.length, "weapon")}</span>
      <span class="mc-foot-spacer"></span>${memberLevelBadge(m)}
    </div>
  </div>`;
}

/* ── 6. Views ─────────────────────────────────────────────────────────────── */

// Star Map ------------------------------------------------------------------
function renderStarMap(query) {
  const reqId = query && query.get ? query.get("flow") : null;
  const wf = GUILD.workflows.find(w => w.id === reqId) || GUILD.workflows[0];
  const unknown = reqId && !GUILD.workflows.some(w => w.id === reqId);
  if (unknown) console.warn(`[map] unknown workflow id "${reqId}" — falling back to default`);
  const accent = ACCENT[wf.accent] || "var(--cyan)";
  return `${viewHead("Operations", "Star Map",
      `A workflow is just a set of repeated steps the Star Alliance follow to get a job done. Hover a star to read ${esc(wf.name)}'s role — the power core traces the active workflow.`)}
    ${flowChips(wf.id)}
    ${unknown ? `<div class="flow-note">Unknown flow — showing the default.</div>` : ""}
    <div class="flow-meta glass" style="--accent:${accent}">
      <div class="fm-icon" aria-hidden="true">${esc(wf.icon || "")}</div>
      <div class="fm-body">
        <div class="fm-tagline">${esc(wf.tagline || "")}</div>
        <div class="fm-when"><span class="fm-when-label">When</span> ${esc(wf.when || "")}</div>
      </div>
    </div>
    <div class="starmap-wrap glass" style="--accent:${accent}">
      ${buildConstellation(wf)}
      <div class="starmap-tip" id="starmap-tip" hidden></div>
    </div>`;
}

// Accent name → CSS color. There is no --blue token, so map it to a literal.
const ACCENT = { cyan: "var(--cyan)", gold: "var(--gold)", violet: "var(--violet)", green: "var(--green)", rose: "var(--rose)", blue: "#5e9ef5" };

// Star Map workflow gallery — each workflow is a 100x100 Fallen Sword art tile
// (workflow-art/<id>.png, mirrors skill art) with its name below.
function flowChips(activeId) {
  return `<nav class="flow-gallery" aria-label="Workflows">` + GUILD.workflows.map(w => {
    const accent = ACCENT[w.accent] || 'var(--cyan)';
    const pic = w.artPng
      ? `<img class="ft-img" src="workflow-art/${esc(w.id)}.png" alt="${esc(w.name)}" loading="lazy">`
      : `<span class="ft-emoji" aria-hidden="true">${esc(w.icon || '⚔')}</span>`;
    return `<a class="flow-tile" href="#/map?flow=${esc(w.id)}" style="--accent:${accent}"${w.id === activeId ? ' aria-current="page"' : ''} title="${esc(w.tagline || w.name)}">
      <span class="ft-pic">${pic}</span>
      <span class="ft-name">${esc(w.name)}</span>
    </a>`;
  }).join("") + `</nav>`;
}

const TIER_RANK = { "opus": 0, "gpt-5.5": 1, "sonnet": 2, "glm-5.2": 3, "kimi-k2.7": 3, "minimax-m3": 3, "deepseek-v4-pro": 3, "nemotron-3-ultra": 3, "qwen3.5": 3, "gemma4": 4, "haiku": 4, "image-01": 5, "minimax-video": 5, "minimax-speech": 5, "minimax-music": 5 };

function buildConstellation(wf) {
  const members = GUILD.members;
  const N = members.length;
  const models = [...new Set(members.map((m) => m.model))].sort((a, b) => (TIER_RANK[a] ?? 9) - (TIER_RANK[b] ?? 9));
  const T = models.length;
  const cx = 400, cy = 400, innerR = 150;
  const gap = T > 1 ? Math.min(120, (300 - innerR) / (T - 1)) : 0;
  const pos = {};
  const radii = [];
  models.forEach((model, ti) => {
    const ring = members.filter((m) => m.model === model);
    const R = innerR + ti * gap;
    radii.push(R);
    const start = -90 + ti * 22;
    ring.forEach((m, i) => {
      const a = (start + i * (360 / ring.length)) * Math.PI / 180;
      pos[m.id] = { x: cx + R * Math.cos(a), y: cy + R * Math.sin(a) };
    });
  });
  const eff = new Map(members.map((m) => [m.id, new Set(effectiveSkills(m))]));
  const freq = {}; GUILD.skills.forEach((s) => { freq[s.id] = liveFreq(s.id); });
  const edges = []; let maxW = 0;
  for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
    const A = members[i], B = members[j], sa = eff.get(A.id), sb = eff.get(B.id);
    const shared = [...sa].filter((s) => sb.has(s) && freq[s] > 0 && freq[s] < N);
    if (!shared.length) continue;
    const w = shared.reduce((t, s) => t + Math.log(N / freq[s]), 0);
    if (w <= 0) continue;
    edges.push({ a: A.id, b: B.id, w, shared }); maxW = Math.max(maxW, w);
  }
  const orbits = radii.map((R, i) => `<circle class="orbit${i === radii.length - 1 ? " dashed" : ""}" cx="${cx}" cy="${cy}" r="${R.toFixed(1)}"/>`).join("");
  const links = edges.map((e) => { const A = pos[e.a], B = pos[e.b]; const s = maxW > 0 ? (e.w / maxW).toFixed(3) : "0";
    return `<line class="link" data-a="${esc(e.a)}" data-b="${esc(e.b)}" style="--s:${s}" x1="${A.x.toFixed(1)}" y1="${A.y.toFixed(1)}" x2="${B.x.toFixed(1)}" y2="${B.y.toFixed(1)}"></line>`; }).join("");

  // Members participating in this workflow (actors only)
  const flowMemberIds = new Set();
  wf.steps.forEach((s) => { if (s.kind === "member" && s.actor !== "you") flowMemberIds.add(s.actor); });

  // Per-member tooltip lines (keyed by member id)
  const memberTipLines = new Map();
  wf.steps.forEach((s, i) => {
    if (s.kind !== "member" || s.actor === "you") return;
    const seg = s.produces ? ` (produces ${esc(s.produces)})` : "";
    const line = `Step ${i + 1} · ${esc(s.title || "")} — ${esc(s.act || "")}${seg}`;
    if (!memberTipLines.has(s.actor)) memberTipLines.set(s.actor, []);
    memberTipLines.get(s.actor).push(line);
  });

  const nodes = members.map((m) => {
    const p = pos[m.id];
    const inFlow = flowMemberIds.has(m.id);
    const tipBody = inFlow
      ? (memberTipLines.get(m.id) || []).join(" | ")
      : `Not part of ${esc(wf.name)}.`;
    return `<a href="#/members/${esc(m.id)}" class="node ${inFlow ? "in-flow" : "off-flow"}" data-id="${esc(m.id)}" data-name="${esc(m.name)}" data-tip="${tipBody}" style="--c:${esc(m.color)}"><g transform="translate(${p.x.toFixed(1)},${p.y.toFixed(1)})"><circle class="halo" r="20"/><circle class="ring2" r="14"/><circle class="core" r="9"/></g><text class="node-label" x="${p.x.toFixed(1)}" y="${(p.y + 32).toFixed(1)}">${esc(m.name)}</text></a>`;
  }).join("");

  // Build the actor waypoint sequence (kind === "member"); "you" maps to center
  const waypoints = [];
  wf.steps.forEach((s) => {
    if (s.kind !== "member") return;
    if (s.actor === "you") waypoints.push({ x: cx, y: cy, isYou: true });
    else waypoints.push({ x: pos[s.actor].x, y: pos[s.actor].y, isYou: false });
  });
  if (waypoints.length === 0 || !waypoints[waypoints.length - 1].isYou) {
    waypoints.push({ x: cx, y: cy, isYou: true });
  }
  const pathD = waypoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");

  // Gate markers at midpoints between the previous and next actor waypoint
  const gateMarkers = [];
  let actorIdx = -1;
  for (let i = 0; i < wf.steps.length; i++) {
    const s = wf.steps[i];
    if (s.kind === "gate") {
      const prev = actorIdx >= 0 ? waypoints[actorIdx] : { x: cx, y: cy };
      let next = null;
      for (let j = i + 1; j < wf.steps.length; j++) {
        if (wf.steps[j].kind === "member") {
          let k = 0;
          for (let m2 = 0; m2 <= j; m2++) if (wf.steps[m2].kind === "member") k++;
          next = waypoints[k - 1];
          break;
        }
      }
      if (!next) next = { x: cx, y: cy };
      const mx = (prev.x + next.x) / 2;
      const my = (prev.y + next.y) / 2;
      const gname = { approval: "Approval Gate", certify: "Certification Gate", report: "Report to You" }[s.gate] || "Gate";
      gateMarkers.push(`<g class="cgate cgate-${esc(s.gate)}" transform="translate(${mx.toFixed(1)},${my.toFixed(1)})" tabindex="0" role="img" aria-label="${esc(gname)}" data-name="${esc(gname)}" data-tip="${esc(s.label || s.gate)}"><circle class="cgate-hit" r="16" fill="transparent"/><rect class="cgate-shape" x="-9" y="-9" width="18" height="18" transform="rotate(45)"/><title>${esc(s.label || s.gate)}</title></g>`);
    } else if (s.kind === "member") {
      actorIdx++;
    }
  }

  const dur = (waypoints.length * 1.1).toFixed(1);
  const youCore = `<g class="you-core" transform="translate(${cx},${cy})" tabindex="0" role="img" aria-label="You · Guild Master" data-name="You · Guild Master" data-tip="The Guild Master and prompter. Every mission begins with your order — the Butler turns it into a clear brief for your approval — and ends when the guild reports the finished work back to you."><circle class="halo" r="22"/><circle class="core" r="10"/><text class="you-glyph" text-anchor="middle" dominant-baseline="central">✦</text><title>You — where every mission begins and ends</title></g>`;

  return `<svg class="starmap" viewBox="0 0 800 800" data-core-dur="${dur}" role="group" aria-label="${esc(wf.name)} workflow over the guild constellation">
    <g class="orbits" aria-hidden="true">${orbits}</g>
    <g class="links" aria-hidden="true">${links}</g>
    <path id="flow-path" class="flow-path" d="${pathD}" fill="none"/>
    <g class="cgates">${gateMarkers.join("")}</g>
    <g class="nodes">${nodes}</g>
    <g class="hookring">${renderHookRing(cx, cy)}</g>
    <g class="you-core-wrap">${youCore}</g>
    <g class="comet-tail">${(() => { const N = 16; let s = ""; for (let k = 0; k < N; k++) { const t = k/(N-1); const r = (5.5*(1-t)+0.8).toFixed(2); const op = (0.6*(1-t)*(1-t)).toFixed(3); const fill = `color-mix(in srgb, var(--accent) ${Math.round(40+t*55)}%, #ffffff)`; s += `<circle class="spark" r="${r}" cx="${cx}" cy="${cy}" style="fill:${fill};opacity:${op}"/>`; } return s; })()}</g>
    <circle class="power-core" r="6" cx="${cx}" cy="${cy}"/>
  </svg>`;
}

// Hook ring — the harness lifecycle hooks (GUILD.hooks) plotted as an arc of
// markers along the outer orbit. The same ring shows on every workflow's map
// (hooks fire on all turns). Hover a marker → tooltip lists every hook on that
// event in plain English. Data source: hooks.json → build.py → GUILD.hooks.
function renderHookRing(cx, cy) {
  const events = (typeof GUILD !== "undefined" && GUILD.hooks) || [];
  if (!events.length) return "";
  const R = 362;
  const span = 120, start = -150;                       // top arc, left→right (chronological)
  const step = events.length > 1 ? span / (events.length - 1) : 0;
  const pt = (deg) => { const a = deg * Math.PI / 180; return { x: cx + R * Math.cos(a), y: cy + R * Math.sin(a) }; };

  // Faint dashed arc behind the markers, so they read as one ring.
  const a0 = pt(start), a1 = pt(start + step * (events.length - 1));
  const arc = events.length > 1
    ? `<path class="hookring-arc" d="M ${a0.x.toFixed(1)} ${a0.y.toFixed(1)} A ${R} ${R} 0 0 1 ${a1.x.toFixed(1)} ${a1.y.toFixed(1)}" fill="none"/>`
    : "";

  const markers = events.map((ev, i) => {
    const p = pt(start + i * step);
    const name = ev.label || ev.event || "Hook";
    const scripts = ev.scripts || [];
    const head = `Fires: ${esc(ev.fires || "")}`;
    const body = scripts.map((s) => `<b>${esc(s.name)}</b> — ${esc(s.plain)}`).join("<br><br>");
    const tip = `${head}<br><br>${body}`;
    const count = scripts.length > 1 ? `<text class="hooknode-badge" x="11" y="-9">${scripts.length}</text>` : "";
    return `<g class="hooknode" tabindex="0" role="img" aria-label="${esc(name)}: ${esc(String(scripts.length))} hook(s)" data-name="${esc(name)}" data-tip="${tip}" transform="translate(${p.x.toFixed(1)},${p.y.toFixed(1)})">
      <circle class="hooknode-hit" r="24" fill="transparent"/>
      <circle class="hooknode-halo" r="15"/>
      <circle class="hooknode-core" r="11"/>
      <text class="hooknode-glyph" text-anchor="middle" dominant-baseline="central">${esc(ev.glyph || "⛓")}</text>
      ${count}
      <text class="hooknode-label" text-anchor="middle" y="-26">${esc(name)}</text>
      <title>${esc(name)} — ${esc(String(scripts.length))} hook(s)</title>
    </g>`;
  }).join("");

  return `${arc}${markers}`;
}

// Members -------------------------------------------------------------------
function renderMembers() {
  return `${viewHead("Roster", "Guild Members",
      `${GUILD.members.length} specialists, each carrying a curated skill set.`)}
    <div class="arsenal-toolbar"><button class="reset-btn" id="member-new" type="button">\uff0b Recruit a member</button></div>
    <div class="grid roster-grid">${GUILD.members.map(memberCard).join("")}</div>`;
}

function renderMemberDossier(id) {
  const m = byMember.get(id);
  if (!m) return renderNotFound(`No member “${esc(id)}” in the roster.`);
  const assigned = assignedSkills(m);
  const active = effectiveSkills(m);
  const blocked = assigned.length - active.length;
  const added = assigned.filter((s) => !m.skills.includes(s)).length;
  const sharedN = active.filter(isShared).length;

  const eff = effectiveWeapons(m);
  const weapons = eff.map((w, i) => {
    const mm = modelMeta(w.model);
    const role = mm.role ? ROLE_META[mm.role] : null;
    return `<div class="weapon-card${w.added ? " added" : ""}" draggable="true" data-model="${esc(w.model)}" data-member="${esc(m.id)}" style="--wc:${esc(mm.color)}">
      <div class="weapon-thumb-wrap">
        <img class="weapon-thumb" src="weapon-art/${esc(w.model)}.png" alt="${esc(mm.label)}" loading="lazy">
        ${role ? `<img class="weapon-role-pip" src="${esc(role.icon)}" alt="${esc(role.label)}" title="${esc(role.label)}: ${esc(role.rule)}" style="--rc:${esc(role.color)}">` : ""}
        <div class="weapon-thumb-tip">
          <div class="wtt-header">
            <div class="wtt-name">${esc(mm.label)}</div>
            ${role ? `<div class="wtt-role">${esc(role.label)}</div>` : ""}
          </div>
          <div class="wtt-body">${esc(mm.ollama_desc || mm.desc || "")}</div>
        </div>
      </div>
      <div class="weapon-name"><span class="weapon-glyph" style="--wc:${esc(mm.color)}">${esc(modelGlyph(w.model))}</span>${esc(mm.label)}
        <button class="wc-revoke" type="button" data-member="${esc(m.id)}" data-model="${esc(w.model)}"
          title="Revoke from this agent" aria-label="Revoke ${esc(mm.label)} from this agent">✕</button>
      </div>
    </div>`;
  }).join("");

  const skillLine = (sid) => {
    const s = bySkill.get(sid);
    const off = isDisabled(sid);
    const blk = isBlocked(m.id, sid);
    const isAdded = !m.skills.includes(sid);
    const siArt = s
      ? (s.artPng
          ? `<img class="sit-img" src="skill-art/${esc(s.id)}.png" alt="${esc(s.name)}" loading="lazy">`
          : s.art
            ? `<span class="sit-svg">${s.art}</span>`
            : `<span class="sit-emoji">${esc(s.icon || "📦")}</span>`)
      : `<span class="sit-emoji">📦</span>`;
    return `<div class="skill-line${blk || off ? " blocked" : ""}" data-skill="${esc(sid)}">
      <button class="si-toggle sit si-sit" type="button" data-member="${esc(m.id)}" data-skill="${esc(sid)}"
        data-tip-name="${esc(s ? s.name : sid)}" data-tip-level="${esc(s ? s.level || "" : "")}" data-tip-blurb="${esc(s ? s.blurb || "" : "")}"
        aria-pressed="${blk}" aria-label="${blk ? "Allow" : "Block"} ${esc(s ? s.name : sid)} for this agent"
        title="${blk ? "Blocked — click to allow" : "Click to block for this agent"}">${siArt}</button>
      <a class="sn" href="#/skills/${esc(sid)}">${esc(s ? s.name : sid)}</a>
      ${isAdded ? `<span class="tag added">added</span>` : ""}
      ${off ? `<a class="tag off" href="#/skills/${esc(sid)}" title="Deactivated guild-wide">deactivated</a>`
            : (blk ? `<span class="tag blocked">blocked</span>`
                   : (isShared(sid) ? `<span class="tag shared">shared</span>` : ""))}
      <button class="unassign-btn" type="button" data-member="${esc(m.id)}" data-skill="${esc(sid)}"
        title="Unassign from this agent" aria-label="Unassign ${esc(s ? s.name : sid)} from this agent">✕</button>
    </div>`;
  };

  // Split carried skills into General + one group per sector that lists the skill.
  // Grouping is by SECTOR MEMBERSHIP (a non-home domain's skills[]), NOT the `global`
  // flag — `global` only means "installed at ~/.claude/skills" (a deploy fact), so a
  // globally-installed skill can still be sector-specific (e.g. transactions-domain-model
  // lives in the global path but belongs to Lex Council App). Home domain (the whole-pool
  // listing) is excluded as a sector. General = carried skills in no non-home sector.
  const homeDomain = GUILD.domains.reduce(
    (a, b) => ((b.skills || []).length > (a.skills || []).length ? b : a),
    GUILD.domains[0] || {});
  const placedInSector = new Set();
  const sectorGroups = GUILD.domains
    .filter((d) => d.id !== (homeDomain && homeDomain.id))
    .map((d) => {
      const ids = assigned.filter((sid) => (d.skills || []).includes(sid));
      ids.forEach((id) => placedInSector.add(id));
      return { name: d.name, id: d.id, icon: d.icon, color: d.color, ids };
    })
    .filter((g) => g.ids.length);
  const generalIds = assigned.filter((sid) => !placedInSector.has(sid));

  const open = assignOpenFor === m.id;
  const pool = open ? GUILD.skills.filter((s) => !assigned.includes(s.id)) : [];
  const assignPanel = `
    <div class="assign-row">
      <button class="assign-toggle" id="assign-toggle" type="button" data-member="${esc(m.id)}" aria-expanded="${open}">
        ${open ? "✕ Close" : "＋ Assign a skill"}
      </button>
    </div>
    ${open ? `<div class="assign-panel">
      ${pool.length ? `<label class="assign-search"><span aria-hidden="true">⌕</span>
          <input id="assign-q" type="search" placeholder="Find a skill to assign…" value="${esc(assignQuery)}" aria-label="Find a skill to assign"></label>
        <div class="assign-chips" id="assign-chips">${pool.map((s) =>
          `<button class="assign-chip" type="button" data-member="${esc(m.id)}" data-skill="${esc(s.id)}"
             data-hay="${esc((s.id + " " + s.name + " " + s.blurb).toLowerCase())}">
             <span>${esc(s.icon)}</span> ${esc(s.name)} <span class="ac-plus">＋</span></button>`).join("")}</div>`
        : `<p class="empty">This agent already carries every skill in the pool.</p>`}
    </div>` : ""}`;

  return `${crumb("#/members", "All members")}
    <div class="dossier" style="--mc:${esc(m.color)}">
      <div class="dossier-hero glass">
        <div class="dh-portrait-wrap">
          <img class="dh-portrait" src="member-art/${esc(m.id)}.png" alt="${esc(m.name)} portrait" loading="lazy">
        </div>
        <div class="dh-meta">
          <div class="dh-name-row">
            <div class="avatar lg">${m.avatar || ""}</div>
            <div class="dh-name-group">
              <h1 class="dh-name">${esc(m.name)}</h1>
              <div class="dh-role editable" contenteditable="true" spellcheck="false" data-medit="role" data-member="${esc(m.id)}">${esc(m.role)}</div>
            </div>
          </div>
          <div class="dh-tags">
            ${memberLevelBadge(m)}
            <span class="tag">${pluralize(active.length, "skill")}</span>
            ${blocked ? `<span class="tag rose">${blocked} blocked</span>` : ""}
            ${added ? `<span class="tag green">${added} added</span>` : ""}
            <span class="tag cyan">${sharedN} shared</span>
          </div>
          <p class="dh-summary editable" contenteditable="true" spellcheck="false" data-medit="summary" data-member="${esc(m.id)}">${esc(m.summary)}</p>
        </div>
      </div>
      <div class="panel-grid">
        <div class="section glass" style="grid-column:1/-1">
          <div class="section-title sk-head">
            <span>Arsenal · ${pluralize(eff.length, "weapon")}</span>
            <a class="reset-btn" href="#/arsenal">Manage in Arsenal →</a>
          </div>
          <p class="skill-hint">The models this agent can wield. Tap <strong>✕</strong> to revoke one · grant more from the <a href="#/arsenal">Arsenal</a> · <strong>drag a card</strong> to reorder priority. Edits persist in this browser.</p>
          <div class="arsenal-grid">${weapons}</div>
        </div>
      </div>
      <div class="panel-grid">
        <div class="section glass">
          <div class="section-title sk-head">
            <span>General Skills · ${generalIds.length}${blocked ? ` <span class="blk-note">· ${blocked} blocked</span>` : ""}${added ? ` <span class="add-note">· ${added} added</span>` : ""}</span>
            ${memberHasOverrides(m.id) ? `<button class="reset-btn" id="reset-member" data-member="${esc(m.id)}">Reset agent</button>` : ""}
          </div>
          <p class="skill-hint">Cross-cutting skills — not tied to any one sector. Tap a skill's <strong>icon</strong> to block it · <strong>✕</strong> to unassign. Hover for details.</p>
          <div class="skill-lines">${generalIds.length ? generalIds.map(skillLine).join("") : `<p class="empty">No general skills carried.</p>`}</div>
          ${assignPanel}
        </div>
        ${sectorGroups.map((g) => `
        <div class="section glass" style="--mc:${esc(g.color || "#888")}">
          <div class="section-title sk-head">
            <span>${esc(g.icon || "⬡")} ${esc(g.name)} · ${g.ids.length}</span>
            <a class="reset-btn" href="#/domains/${esc(g.id)}">View sector →</a>
          </div>
          <p class="skill-hint">Sector-specific skills deployed to <strong>${esc(g.name)}</strong>.</p>
          <div class="skill-lines">${g.ids.map(skillLine).join("")}</div>
        </div>`).join("")}
        <div class="section glass">
          <div class="section-title">Deployment</div>
          <div class="kv">
            <div><div class="k">Deploy when</div><div class="v editable" contenteditable="true" spellcheck="false" data-medit="deploy" data-member="${esc(m.id)}">${esc(m.deploy)}</div></div>
            <div><div class="k">Triggers</div><div class="v editable" contenteditable="true" spellcheck="false" data-medit="triggers" data-member="${esc(m.id)}">${esc(m.triggers)}</div></div>
            <div><div class="k">Mandate</div><div class="v editable" contenteditable="true" spellcheck="false" data-medit="description" data-member="${esc(m.id)}">${esc(m.description || "")}</div></div>
          </div>
        </div>
        <div class="section glass">
          <div class="section-title">Role boundaries</div>
          <div class="duo">
            <ul class="bullets yes">${m.does.map((d) => `<li>${esc(d)}</li>`).join("")}</ul>
            <ul class="bullets no">${m.doesnt.map((d) => `<li>${esc(d)}</li>`).join("")}</ul>
          </div>
        </div>
        ${memberLevelSection(m)}
        ${renderStarmapWorkflow(m)}
        <div class="section glass" style="grid-column:1/-1">
          <div class="section-title">Workflow / system prompt</div>
          <p class="skill-hint">The agent's mandate body. Click to edit \u2014 saves to the member <code>.md</code> when the dev server runs.</p>
          <pre class="prompt-edit editable" contenteditable="true" spellcheck="false" data-medit="prompt" data-member="${esc(m.id)}">${esc(m.prompt || "")}</pre>
        </div>
        <div class="section glass" style="grid-column:1/-1">
          <div class="section-title">Danger zone</div>
          <button class="reset-btn danger" id="member-delete" data-member="${esc(m.id)}">Delete this member</button>
        </div>
      </div>
    </div>`;
}

function renderStarmapWorkflow(m) {
  const flows = [];

  for (const wf of GUILD.workflows) {
    const occurrences = [];
    wf.steps.forEach((step, i) => {
      if (step.kind === "member" && step.actor === m.id) {
        const labelFor = (s) => {
          if (!s) return null;
          if (s.kind === "member") {
            if (s.actor === "you") return "You";
            return byMember.get(s.actor)?.name || "a teammate";
          }
          if (s.kind === "gate") {
            if (s.gate === "approval") return "your approval";
            if (s.gate === "certify") return "the Quartermaster's certification";
            if (s.gate === "report") return "the final report";
            return "a gate";
          }
          return null;
        };
        const prevLabel = i > 0 ? labelFor(wf.steps[i - 1]) : null;
        const nextLabel = i < wf.steps.length - 1 ? labelFor(wf.steps[i + 1]) : null;
        occurrences.push({ i, step, prevLabel, nextLabel });
      }
    });
    if (occurrences.length > 0) flows.push({ wf, occurrences });
  }

  if (flows.length === 0) {
    return `
      <div class="section glass starmap-wf" style="grid-column:1/-1">
        <div class="section-title">Starmap Workflow</div>
        <div class="skill-hint">${esc(m.name)} is not yet part of any charted workflow.</div>
      </div>`;
  }

  let html = `
    <div class="section glass starmap-wf" style="grid-column:1/-1">
      <div class="section-title">Starmap Workflow</div>
      <div class="skill-hint">How ${esc(m.name)} is summoned across the guild's ${flows.length} ${flows.length === 1 ? "workflow" : "workflows"}.</div>`;

  if (m.triggers) {
    html += `
      <div class="swf-prompts">
        <div class="k">Prompts that summon ${esc(m.name)}</div>
        <div class="v">${esc(m.triggers)}</div>
      </div>`;
  }

  html += `<div class="swf-grid">`;

  for (const { wf, occurrences } of flows) {
    const accent = ACCENT[wf.accent] || "var(--cyan)";
    html += `
      <div class="swf-card" style="--accent:${accent}">
        <div class="swf-card-head">
          <span class="swf-icon" aria-hidden="true">${esc(wf.icon || "✦")}</span>
          <a href="#/map?flow=${esc(wf.id)}">${esc(wf.name)}</a>
          <a class="swf-view" href="#/map?flow=${esc(wf.id)}">view relay →</a>
        </div>`;
    for (const { i, step, prevLabel, nextLabel } of occurrences) {
      html += `
        <div class="swf-step">
          <div class="swf-stepnum">Step ${i + 1}</div>
          <div class="swf-title">${esc(step.title)}</div>
          <div class="swf-act">${esc(step.act)}</div>
          ${stepLoadout(step)}
          ${step.produces ? `<div class="swf-produces">produces → ${esc(step.produces)}</div>` : ""}
          <div class="swf-ctx">${prevLabel ? `After ${esc(prevLabel)} · ` : ""}${nextLabel ? `hands to ${esc(nextLabel)}` : "final step"}</div>
        </div>`;
    }
    html += `</div>`;
  }

  html += `</div></div>`;
  return html;
}

// Weapon loadout for a workflow step (optional structured fields: thinker / doers / ultra).
// Renders nothing when a step declares no weapons — fully backward compatible.
function modelLabel(id) {
  return (typeof MODELS !== "undefined" && MODELS[id] && MODELS[id].label) || id;
}
function stepLoadout(step) {
  if (!step || (!step.thinker && !(step.doers && step.doers.length) && !step.ultra)) return "";
  const parts = [];
  if (step.ultra) {
    const prime = step.thinker ? ` → prime ${esc(modelLabel(step.thinker))}` : "";
    parts.push(`<span class="lo-tag lo-ultra" title="ultra-brainstorming — all of the member's thinker models fire at once; the prime thinker reviews and synthesizes one plan">✦ ultra · all thinkers${prime}</span>`);
  } else if (step.thinker) {
    parts.push(`<span class="lo-tag lo-thinker" title="prime thinker — plans the work and reviews the result">🧠 ${esc(modelLabel(step.thinker))}</span>`);
  }
  if (Array.isArray(step.doers) && step.doers.length) {
    const ds = step.doers.map((d) => {
      const m = (typeof d === "object" && d) ? d.model : d;
      const c = (typeof d === "object" && d && d.count > 1) ? `<span class="lo-x">×${d.count}</span>` : "";
      return `${esc(modelLabel(m))}${c}`;
    }).join(" · ");
    const parallel = step.doers.length > 1 || step.doers.some((d) => typeof d === "object" && d && d.count > 1);
    parts.push(`<span class="lo-tag lo-doers" title="doer(s) — execute the thinker's plan${parallel ? "; these run in parallel" : ""}">⚔ ${ds}${parallel ? " · parallel" : ""}</span>`);
  }
  return `<div class="swf-loadout">${parts.join("")}</div>`;
}

// Arsenal / Armory ----------------------------------------------------------
const fmtK = (n) => (n >= 1000 ? (n / 1000).toFixed(n >= 10000 ? 0 : 1) + "k" : String(n || 0));
function ledgerFor(id) {
  const bm = arsenalLive && arsenalLive.ledger && arsenalLive.ledger.byModel;
  return (bm && bm[id]) || null;
}
function renderArsenal() {
  const anyOv = Object.keys(weaponOv).length;
  const cards = ARSENAL.map((id) => {
    const mm = modelMeta(id);
    const off = isWeaponDisabled(id);
    const wielders = GUILD.members.filter((m) => wields(m, id)).length;
    const wieldCount = GUILD.members.filter((m) => wields(m, id)).length;
    const dropItems = GUILD.members.map((m) => {
      const on = wields(m, id);
      return `<label class="wield-drop-item${on ? " on" : ""}">
        <input type="checkbox" class="wield-chip" data-member="${esc(m.id)}" data-model="${esc(id)}"${on ? " checked" : ""}>
        <span class="wc-dot" aria-hidden="true">${on ? "✓" : "＋"}</span>${esc(m.name)}</label>`;
    }).join("");
    const chips = `<div class="wield-dropdown">
      <button class="wield-drop-btn" type="button" data-weapon="${esc(id)}">
        ${wieldCount > 0 ? `${wieldCount} agent${wieldCount > 1 ? "s" : ""}` : "Assign agents"} <span class="wield-drop-arrow">▾</span>
      </button>
      <div class="wield-drop-list">${dropItems}</div>
    </div>`;
    const role = mm.role ? ROLE_META[mm.role] : null;
    return `<div class="model-card${off ? " deactivated" : ""}" style="--wc:${esc(mm.color)}">
      <div class="weapon-art-wrap" data-weapon-color="${esc(mm.color)}" data-weapon-off="${off}">
        <img class="weapon-art${off ? " dimmed" : ""}" src="weapon-gif/${esc(id)}.gif" onerror="this.src='weapon-art/${esc(id)}.png'" alt="${esc(mm.label)} weapon art" loading="lazy">
        <canvas class="weapon-aura-canvas" aria-hidden="true"></canvas>
        <button class="weapon-power-btn${off ? " off" : ""}" type="button" data-weapon="${esc(id)}"
          title="${off ? "Reactivate weapon" : "Deactivate weapon"}">⏻</button>
      </div>
      ${role ? `<div class="weapon-role" style="--rc:${esc(role.color)}">
        <img class="role-icon" src="${esc(role.icon)}" alt="${esc(role.label)}">
        <div class="role-info">
          <span class="role-label">${esc(role.label)}</span>
          <span class="role-rule">${esc(role.rule)}</span>
        </div>
      </div>` : ""}
      <div class="model-head">
        <span class="weapon-glyph" style="--wc:${esc(mm.color)}">${esc(modelGlyph(id))}</span>
        <div class="model-id">
          <div class="model-label">${esc(mm.label)}</div>
          <div class="model-badges"><span class="mb tier">${esc(mm.tier || "Model")}</span>${mm.host ? `<span class="mb host">${esc(mm.host)}</span>` : ""}${
            mm._pulled === true ? `<span class="mb pulled">● pulled</span>` :
            mm._pulled === false ? `<span class="mb unpulled">○ not pulled</span>` : ""}</div>
        </div>
        <span class="model-count" title="Agents wielding this model">${wielders}/${GUILD.members.length}</span>
      </div>
      ${(() => {
        const L = ledgerFor(id);
        if (!L || !L.wCalls) return "";
        return `<div class="model-usage" title="Real spend logged by the arsenal backends this week (7d rolling)">
          <span class="mu-dot">●</span> ${L.wCalls} call${L.wCalls > 1 ? "s" : ""} · ${fmtK(L.wOut)} out · ${fmtK(L.wIn)} in <span class="mu-win">7d</span></div>`;
      })()}
      <p class="model-desc">${esc(mm.desc || "")}</p>
      ${mm.call ? `<div class="model-call">
        <div class="mc-head"><span class="mc-label">⚔ How to summon</span></div>
        <pre class="mc-recipe">${esc(mm.call)}</pre>
      </div>` : ""}
      <div class="wield-row">${chips}</div>
      <p class="model-ollama-desc">${esc(mm.ollama_desc || mm.desc || "")}</p>
    </div>`;
  }).join("");

  let liveTag;
  if (arsenalFetching && !arsenalLive) liveTag = `<span class="tag">⟳ syncing…</span>`;
  else if (arsenalLive && !arsenalLive.offline) liveTag = `<span class="tag green">● live — ${esc(String((arsenalLive.pulled || []).length))} cloud models pulled</span>`;
  else liveTag = "";

  // Delegation ledger headline — REAL doer work logged by the backends. The
  // figure that proves the harness is offloading work to the cheap bench.
  let ledgerBanner = "";
  const lg = arsenalLive && arsenalLive.ledger;
  if (lg && lg.week && lg.week.doerCalls > 0) {
    const rate = Math.round((lg.session && lg.session.rate || 0) * 100);
    const showRate = lg.session && (lg.session.opusOut > 0 || lg.session.doerOut > 0);
    ledgerBanner = `<div class="ledger-banner glass" title="Real token spend logged by summon.py → minimax.py / ollama_cloud.py">
      <span class="lb-icon">⚔</span>
      <div class="lb-stats">
        <div class="lb-headline"><b>${lg.week.doerCalls}</b> doer call${lg.week.doerCalls > 1 ? "s" : ""} · <b>${fmtK(lg.week.doerOut)}</b> tokens offloaded to the bench <span class="lb-win">7d</span></div>
        <div class="lb-sub">~${fmtK(lg.week.doerOut)} Opus output tokens the doers absorbed${showRate ? ` · <b>${rate}%</b> of recent output delegated <span class="lb-win">5h</span>` : ""}</div>
      </div>
    </div>`;
  } else if (lg) {
    ledgerBanner = `<div class="ledger-banner glass empty" title="No doer calls logged yet — fire one via summon.py">
      <span class="lb-icon">⚔</span>
      <div class="lb-stats"><div class="lb-headline">No delegated work logged yet</div>
      <div class="lb-sub">Doer calls via <code>summon.py</code> will appear here — proof the bench is carrying load.</div></div>
    </div>`;
  }

  return `${viewHead("Armory", "Arsenal",
      "Every model in the guild's armory — with its <strong>summon recipe</strong>. Claude = native master brain; MiniMax = <strong>direct</strong> cloud sub (not Ollama); the bench = Ollama Cloud. On the dev server each card shows whether its cloud model is actually pulled. Tap an agent under a model to grant/revoke.")}
    ${ledgerBanner}
    <div class="arsenal-toolbar">
      ${liveTag}
      ${anyOv ? `<span class="tag green">Custom loadouts active</span><button class="reset-btn" id="reset-weapons">Reset all assignments</button>` : ""}
    </div>
    <div class="model-grid">${cards}</div>`;
}

// Skills / Skill Pool -------------------------------------------------------
function renderSkills(query) {
  const levels = [...new Set(GUILD.skills.map((s) => s.level))];
  const srcs = [...new Set(GUILD.skills.map((s) => s.src))];
  const q = query.get("q") || "", level = query.get("level") || "", src = query.get("src") || "", sort = query.get("sort") || "name";

  const levelOpts = `<option value="">All levels</option>` +
    levels.map((l) => `<option value="${esc(l)}"${l === level ? " selected" : ""}>${esc(l)}</option>`).join("");
  const sortOpts = [["name", "Name"], ["level", "Level"], ["version", "Version"], ["carriers", "Carriers"]]
    .map(([v, t]) => `<option value="${v}"${v === sort ? " selected" : ""}>Sort: ${t}</option>`).join("");
  const srcSeg = `<button data-src="" aria-pressed="${src === "" }">All</button>` +
    srcs.map((s) => `<button data-src="${esc(s)}" aria-pressed="${s === src}">${esc(s[0].toUpperCase() + s.slice(1))}</button>`).join("");

  const cards = GUILD.skills.map(skillCard).join("");

  return `${viewHead("Inventory", "Skill Pool", `${GUILD.skills.length} skills shared across the guild.`)}
    <div class="filter-bar glass">
      <label class="search-field"><span class="si" aria-hidden="true">⌕</span>
        <input id="f-q" type="search" placeholder="Search skills…" aria-label="Search skills" value="${esc(q)}"></label>
      <div class="seg" id="f-src" role="group" aria-label="Filter by source">${srcSeg}</div>
      <select id="f-level" aria-label="Filter by level">${levelOpts}</select>
      <select id="f-sort" aria-label="Sort skills">${sortOpts}</select>
      <span class="filter-meta"><span id="filter-count" class="count"></span></span>
    </div>
    <div class="grid skill-grid" id="skill-results">${cards}</div>
    <div class="empty is-hidden" id="skill-empty">No skills match those filters.</div>`;
}

function skillCard(s) {
  const off = isDisabled(s.id);
  return `<a class="skill-card glass${off ? " deactivated" : ""}" href="#/skills/${esc(s.id)}" data-id="${esc(s.id)}" title="${esc(skillScopeTip(s))}">
    <div class="sc-top">
      <div class="sc-icon${(s.art || s.artPng) ? " art" : ""}">${skillArt(s)}</div>
      <div><div class="sc-name">${esc(s.name)}</div><div class="sc-ver">v${esc(s.version)}</div></div>
    </div>
    <div class="sc-blurb">${esc(s.blurb)}</div>
    <div class="sc-foot">
      ${off ? `<span class="tag off">deactivated</span>` : ""}
      <span class="tag ${s.global ? "scope-global" : "scope-sector"}" title="${esc(skillScopeTip(s))}">${s.global ? "🌐 Global" : "⬡ Sector"}</span>
      <span class="tag ${rampClass(s)}">${esc(s.level)}</span>
      <span class="tag src-${esc(s.src)}">${esc(s.src)}</span>
      <span class="sc-carriers">${pluralize(liveFreq(s.id), "carrier")}</span>
    </div>
  </a>`;
}

function renderSkillPanel(id) {
  const s = bySkill.get(id);
  if (!s) return renderNotFound(`No skill “${esc(id)}” in the skill pool.`);
  const off = isDisabled(s.id);
  const carrierIds = liveCarriers(s.id);
  const carriers = carrierIds.map((mid) => {
    const m = byMember.get(mid);
    return `<a class="ref-pill" href="#/members/${esc(mid)}" style="--mc:${esc(m?.color || "#888")}">
      <span class="avatar" style="width:26px;height:26px;border-radius:7px">${m?.avatar || ""}</span>${esc(m ? m.name : mid)}</a>`;
  }).join("") || `<span class="empty">${off ? "Deactivated guild-wide — no agent can use it." : (s.members.length ? "No guild member carries this skill (all blocked)." : "No guild member carries this skill yet.")}</span>`;

  const sections = s.sections.length
    ? `<div class="section glass"><div class="section-title">Inside the skill · ${s.sections.length} sections</div>
       <ul class="sectionlist">${s.sections.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : "";
  const files = (s.refs.length || s.scripts.length)
    ? `<div class="section glass"><div class="section-title">Bundled files</div>
       <div class="chips">${[...s.scripts, ...s.refs].map((f) => `<span class="tag">${esc(f)}</span>`).join("")}</div></div>` : "";

  const secs = skillSectors(s.id);
  const sectorChip = (d) => `<a class="ref-pill" href="#/domains/${esc(d.id)}" style="--mc:${esc(d.color || "#888")}">
      <span class="avatar" style="width:26px;height:26px;border-radius:7px;display:grid;place-items:center;font-size:14px">${esc(d.icon || "")}</span>${esc(d.name)}</a>`;
  const sectorsBlock = `<div class="section glass">
      <div class="section-title">${s.global ? "Availability" : "Sector"}</div>
      <p class="scope-note">${s.global
        ? `<span class="scope-flag is-global">🌐 Global</span> Installed at <code>~/.claude/skills</code> — every sector can load it. Listed in:`
        : `<span class="scope-flag is-sector">⬡ Sector-specific</span> Lives only in a project's <code>.claude/skills</code>, not on the global load path. Found in:`}</p>
      ${secs.length ? `<div class="ref-grid">${secs.map(sectorChip).join("")}</div>`
                    : `<span class="empty">Not listed in any sector yet.</span>`}</div>`;

  return `${crumb("#/skills", "All skills")}
    <div class="skill-panel">
      <div class="sp-hero glass${off ? " deactivated" : ""}">
        <div class="sp-icon${(s.art || s.artPng) ? " art" : ""}">${skillArt(s)}</div>
        <div class="sp-meta">
          <h1 class="sp-title">${esc(s.name)}</h1>
          <div class="sp-tags">
            <span class="tag">v${esc(s.version)}</span>
            <span class="tag ${rampClass(s)}">${esc(s.level)}</span>
            <span class="tag src-${esc(s.src)}">${esc(s.src)}</span>
            <span class="tag ${s.global ? "scope-global" : "scope-sector"}" title="${esc(skillScopeTip(s))}">${s.global ? "🌐 Global" : "⬡ Sector-specific"}</span>
            ${off ? `<span class="tag off">deactivated guild-wide</span>` : ""}
          </div>
          <p class="sp-blurb">${esc(s.desc || s.blurb)}</p>
        </div>
        <button class="deactivate-toggle${off ? " on" : ""}" id="deactivate-toggle" type="button" data-skill="${esc(s.id)}"
          aria-pressed="${off}" title="${off ? "Reactivate this skill for the whole guild" : "Deactivate this skill for every agent"}">
          ⏻ ${off ? "Reactivate skill" : "Deactivate skill"}
        </button>
      </div>
      ${off ? `<div class="off-banner glass">⏻ Deactivated guild-wide — every agent's copy is inert, it counts as 0 carriers everywhere, and it's dropped from the Star Map. Reactivate to restore.</div>` : ""}
      <div class="telemetry glass">
        <div class="stat"><b class="count">${carrierIds.length}</b><span>Carriers</span></div>
        <div class="stat"><b class="count">${s.stats.lines}</b><span>Lines</span></div>
        <div class="stat"><b class="count">${s.stats.words}</b><span>Words</span></div>
        <div class="stat"><b class="count">${s.sections.length}</b><span>Sections</span></div>
        <div class="stat"><b class="count">${s.scripts.length + s.refs.length}</b><span>Files</span></div>
      </div>
      ${s.intro ? `<div class="section glass"><div class="section-title">Overview</div><p style="color:var(--muted);line-height:1.7">${esc(s.intro)}</p></div>` : ""}
      ${sectorsBlock}
      <div class="section glass"><div class="section-title">Carried by · ${carrierIds.length}</div><div class="ref-grid">${carriers}</div></div>
      ${sections}
      ${files}
    </div>`;
}

// Domains / Sectors ---------------------------------------------------------
function renderDomains() {
  return `${viewHead("Sectors", "Project Domains", `${GUILD.domains.length} domains drawing from the shared skill pool.`)}
    <div class="grid sector-grid">${GUILD.domains.map(sectorCard).join("")}</div>`;
}

function sectorCard(d) {
  return `<a class="sector-card glass" href="#/domains/${esc(d.id)}" style="--sc:${esc(d.color)}">
    <div class="sector-icon">${esc(d.icon)}</div>
    <div><div class="sector-name">${esc(d.name)}</div></div>
    <div class="sector-tagline">${esc(d.tagline)}</div>
    <div class="sector-stats">
      <div class="st"><b class="count">${d.skills.length}</b><span>skills</span></div>
      <div class="st"><b class="count">${d.members.length}</b><span>members</span></div>
    </div>
  </a>`;
}

function renderSectorDetail(id) {
  const d = byDomain.get(id);
  if (!d) return renderNotFound(`No sector “${esc(id)}”.`);

  const skills = d.skills.map((sid) => {
    const s = bySkill.get(sid);
    if (!s) return `<span class="ref-pill ext" title="not installed in the guild pool"><span class="ri">⚠</span>${esc(sid)}</span>`;
    return `<a class="ref-pill" href="#/skills/${esc(sid)}"><span class="ri">${esc(s.icon)}</span>${esc(s.name)}</a>`;
  }).join("");

  const members = d.members.map((mid) => {
    const m = byMember.get(mid);
    if (!m) return `<span class="ref-pill ext" title="external agent, not a guild member"><span class="ri">◇</span>${esc(mid)} <span class="tag">external</span></span>`;
    return `<a class="ref-pill" href="#/members/${esc(mid)}" style="--mc:${esc(m.color)}"><span class="avatar" style="width:24px;height:24px;border-radius:6px">${m.avatar || ""}</span>${esc(m.name)}</a>`;
  }).join("");

  return `${crumb("#/domains", "All sectors")}
    <div class="dossier" style="--mc:${esc(d.color)}">
      <div class="dossier-hero glass">
        <div class="sector-icon" style="font-size:40px;width:76px;height:76px">${esc(d.icon)}</div>
        <div class="dh-meta">
          <h1 class="dh-name">${esc(d.name)}</h1>
          <div class="dh-role">${esc(d.tagline)}</div>
          <div class="dh-tags">
            <span class="tag cyan">${pluralize(d.skills.length, "skill")}</span>
            <span class="tag">${pluralize(d.members.length, "member")}</span>
          </div>
          ${d.notes ? `<p class="dh-summary">${esc(d.notes)}</p>` : ""}
          ${d.path ? `<p class="path">${esc(d.path)}</p>` : ""}
        </div>
      </div>
      <div class="section glass"><div class="section-title">Linked skills · ${d.skills.length}</div><div class="ref-grid">${skills}</div></div>
      <div class="section glass"><div class="section-title">Members in sector · ${d.members.length}</div><div class="ref-grid">${members}</div></div>
    </div>`;
}

// Guild Log -----------------------------------------------------------------
function renderLog(query) {
  const types = [...new Set(logEntries.map((e) => e.type))];
  const active = query.get("type") || "";
  const seg = `<button data-logtype="" aria-pressed="${active === ""}">All</button>` +
    types.map((t) => `<button data-logtype="${esc(t)}" aria-pressed="${t === active}">${esc(t)}</button>`).join("");
  const entries = logEntries.map(logEntry).join("");

  return `${viewHead("Activity", "Guild Log", `${logEntries.length} recorded changes to the guild.`)}
    <div class="filter-bar glass">
      <div class="seg" id="f-logtype" role="group" aria-label="Filter by type">${seg}</div>
      <span class="filter-meta"><span id="log-count" class="count"></span></span>
    </div>
    <div class="timeline" id="log-results">${entries}</div>
    <div class="empty is-hidden" id="log-empty">No entries of that type.</div>`;
}

function logEntry(e) {
  const refs = (e.ref || []).map((r) => {
    const mem = byMember.get(r);
    if (mem) return `<a class="tag" href="#/members/${esc(r)}">${esc(mem.name)}</a>`;
    if (bySkill.get(r)) return `<a class="tag" href="#/skills/${esc(r)}">${esc(r)}</a>`;
    return `<span class="tag">${esc(r)}</span>`;
  }).join("");
  const ver = e.from && e.to ? `<span class="tag">${esc(e.from)} → ${esc(e.to)}</span>` : (e.to ? `<span class="tag">${esc(e.to)}</span>` : "");
  return `<div class="log-entry t-${esc(e.type)}" data-type="${esc(e.type)}">
    <div class="le-head">
      <span class="type-chip t-${esc(e.type)}">${esc(e.type)}</span>
      <span class="le-date">${esc(e.date)}</span>
      ${e.bulk ? `<span class="tag">bulk</span>` : ""}
    </div>
    <div class="le-title">${esc(e.title)}</div>
    ${e.detail ? `<div class="le-detail">${esc(e.detail)}</div>` : ""}
    <div class="le-foot">${ver}${refs}
      ${e.who ? `<span class="le-commit">by ${esc(e.who)}</span>` : ""}
      ${e.commit ? `<span class="le-commit">· ${esc(e.commit)}</span>` : ""}
    </div>
  </div>`;
}

// Not found -----------------------------------------------------------------
function renderNotFound(msg) {
  return `<div class="state" role="alert">
    <div class="glyph">🛰️</div><h1 data-focus>Sector uncharted</h1>
    <p>${msg ? esc(msg) : "That route doesn’t map to anything in the guild."}</p>
    <a class="btn" href="#/map">Return to Star Map</a>
  </div>`;
}

/* ── 7. After-render hooks (filters) ──────────────────────────────────────── */
function afterRender(key, segments) {
  if (key === "skills" && !segments[1]) filterSkills();
  if (key === "log" && !segments[1]) filterLog();
  if (key === "arsenal" && !arsenalApplied) refreshArsenalData();
  if (key === "arsenal") initWeaponAuras();
  if (key === "map") initPowerCore();
}

function initWeaponAuras() {
  // Cancel any existing loops
  if (window._auraRafs) window._auraRafs.forEach(id => cancelAnimationFrame(id));
  window._auraRafs = [];

  document.querySelectorAll(".weapon-art-wrap[data-weapon-color]").forEach(wrap => {
    const canvas = wrap.querySelector(".weapon-aura-canvas");
    if (!canvas) return;
    const color = wrap.dataset.weaponColor || "#ffffff";
    const off   = wrap.dataset.weaponOff === "true";
    if (off) { canvas.style.opacity = "0"; return; }
    canvas.style.opacity = "1";

    // parse hex to rgb
    const r = parseInt(color.slice(1,3),16);
    const g = parseInt(color.slice(3,5),16);
    const b = parseInt(color.slice(5,7),16);

    const W = wrap.offsetWidth  || 300;
    const H = wrap.offsetHeight || 200;
    canvas.width  = W;
    canvas.height = H;
    const ctx = canvas.getContext("2d");

    // Particle pool
    const MAX = 55;
    const particles = [];

    function spawnParticle() {
      // spawn from edges or bottom, drift upward with elemental variation
      const edge = Math.random();
      let x, y, vx, vy, size, life, maxLife, type;
      if (edge < 0.5) {
        // sides
        x  = edge < 0.25 ? Math.random() * W * 0.3 : W - Math.random() * W * 0.3;
        y  = Math.random() * H;
        vx = (x < W/2 ? 1 : -1) * (0.2 + Math.random() * 0.5);
        vy = -(0.4 + Math.random() * 1.2);
      } else {
        // bottom spread
        x  = W * 0.2 + Math.random() * W * 0.6;
        y  = H - Math.random() * H * 0.15;
        vx = (Math.random() - 0.5) * 1.2;
        vy = -(0.6 + Math.random() * 1.4);
      }
      size    = 1.5 + Math.random() * 3.5;
      maxLife = 60 + Math.random() * 80;
      life    = maxLife;
      type    = Math.random() < 0.3 ? "spark" : "orb";
      particles.push({ x, y, vx, vy, size, life, maxLife, type });
    }

    for (let i = 0; i < MAX * 0.6; i++) spawnParticle();

    function frame() {
      ctx.clearRect(0, 0, W, H);

      // ambient edge glow sweep
      const t = Date.now() / 1000;
      const glow = ctx.createRadialGradient(W/2, H/2, H*0.1, W/2, H/2, H*0.85);
      const pulse = 0.04 + 0.03 * Math.sin(t * 1.4);
      glow.addColorStop(0,   `rgba(${r},${g},${b},0)`);
      glow.addColorStop(0.7, `rgba(${r},${g},${b},0)`);
      glow.addColorStop(1,   `rgba(${r},${g},${b},${pulse})`);
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, W, H);

      if (particles.length < MAX && Math.random() < 0.55) spawnParticle();

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.x  += p.vx + Math.sin(t * 2 + i) * 0.3;
        p.y  += p.vy;
        p.vy -= 0.012; // slight acceleration upward
        p.life--;
        if (p.life <= 0) { particles.splice(i, 1); continue; }

        const alpha = (p.life / p.maxLife) * 0.85;
        const s     = p.size * (p.life / p.maxLife);

        if (p.type === "spark") {
          // elongated spark line
          ctx.save();
          ctx.strokeStyle = `rgba(${r},${g},${b},${alpha})`;
          ctx.lineWidth   = s * 0.5;
          ctx.shadowColor = `rgba(${r},${g},${b},${alpha * 0.8})`;
          ctx.shadowBlur  = 6;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x - p.vx * 4, p.y - p.vy * 4);
          ctx.stroke();
          ctx.restore();
        } else {
          // glowing orb
          const grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, s * 2.5);
          grad.addColorStop(0,   `rgba(255,255,255,${alpha * 0.9})`);
          grad.addColorStop(0.3, `rgba(${r},${g},${b},${alpha * 0.8})`);
          grad.addColorStop(1,   `rgba(${r},${g},${b},0)`);
          ctx.beginPath();
          ctx.arc(p.x, p.y, s * 2.5, 0, Math.PI * 2);
          ctx.fillStyle = grad;
          ctx.fill();
        }
      }

      window._auraRafs.push(requestAnimationFrame(frame));
    }
    window._auraRafs.push(requestAnimationFrame(frame));
  });
}

function syncQuery(params) {
  const base = location.hash.split("?")[0] || "#/skills";
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v) usp.set(k, v); });
  const qs = usp.toString();
  history.replaceState(null, "", base + (qs ? "?" + qs : ""));
}

function filterSkills() {
  const root = byId("skill-results"); if (!root) return;
  const q = (byId("f-q")?.value || "").trim().toLowerCase();
  const level = byId("f-level")?.value || "";
  const src = byId("f-src")?.querySelector('[aria-pressed="true"]')?.dataset.src || "";
  const sort = byId("f-sort")?.value || "name";
  syncQuery({ q, level, src, sort });

  const cards = [...root.children];
  let shown = 0;
  cards.forEach((c) => {
    const s = bySkill.get(c.dataset.id); if (!s) return;
    const hay = `${s.id} ${s.name} ${s.blurb} ${s.desc} ${s.level} ${s.src}`.toLowerCase();
    const ok = (!q || hay.includes(q)) && (!level || s.level === level) && (!src || s.src === src);
    c.classList.toggle("is-hidden", !ok); if (ok) shown++;
  });

  const rank = { Foundational: 0, Intermediate: 1, Advanced: 2, Elite: 3, Master: 4 };
  const cmp = {
    name: (a, b) => a.name.localeCompare(b.name),
    level: (a, b) => (rank[b.level] ?? 0) - (rank[a.level] ?? 0) || a.name.localeCompare(b.name),
    version: (a, b) => String(b.version).localeCompare(String(a.version), undefined, { numeric: true }),
    carriers: (a, b) => liveFreq(b.id) - liveFreq(a.id) || a.name.localeCompare(b.name),
  }[sort] || ((a, b) => a.name.localeCompare(b.name));
  const SK0 = { name: "", level: "", version: "", members: [] };  // defensive fallback for the comparator
  cards.sort((x, y) => cmp(bySkill.get(x.dataset.id) || SK0, bySkill.get(y.dataset.id) || SK0)).forEach((c) => root.appendChild(c));

  byId("filter-count").textContent = `${shown} of ${GUILD.skills.length}`;
  byId("skill-empty")?.classList.toggle("is-hidden", shown !== 0);
}

function filterLog() {
  const root = byId("log-results"); if (!root) return;
  const type = byId("f-logtype")?.querySelector('[aria-pressed="true"]')?.dataset.logtype || "";
  syncQuery({ type });
  let shown = 0;
  [...root.children].forEach((e) => {
    const ok = !type || e.dataset.type === type;
    e.classList.toggle("is-hidden", !ok); if (ok) shown++;
  });
  byId("log-count").textContent = pluralize(shown, "entry").replace("entrys", "entries");
  byId("log-empty")?.classList.toggle("is-hidden", shown !== 0);
}

function pressSeg(group, el) {
  group.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b === el)));
}

// In-place filter of the assign panel's skill chips (no re-render — preserves input focus).
function filterAssign() {
  const box = byId("assign-chips"); if (!box) return;
  assignQuery = (byId("assign-q")?.value || "").trim().toLowerCase();
  [...box.children].forEach((c) => c.classList.toggle("is-hidden", !!assignQuery && !c.dataset.hay.includes(assignQuery)));
}

/* ── 8. Star-map hover/focus highlight ────────────────────────────────────── */
function showStarTip(node, evt) {
  const tip = document.getElementById("starmap-tip");
  const svg = app.querySelector(".starmap");
  const wrap = app.querySelector(".starmap-wrap");
  if (!tip || !svg || !wrap) return;
  svg.classList.add("dim");
  app.querySelectorAll(".starmap .node").forEach((n) => n.classList.toggle("active", n === node));
  tip.innerHTML = `<div class="tip-name">${node.dataset.name || ""}</div><div class="tip-body">${node.dataset.tip || ""}</div>`;
  tip.hidden = false;
  const wr = wrap.getBoundingClientRect();
  let x = evt.clientX - wr.left + 14;
  let y = evt.clientY - wr.top + 14;
  const tw = tip.offsetWidth, th = tip.offsetHeight;
  if (x + tw > wr.width) x = wr.width - tw - 8;
  if (y + th > wr.height) y = wr.height - th - 8;
  if (x < 8) x = 8;
  if (y < 8) y = 8;
  tip.style.left = x + "px";
  tip.style.top = y + "px";
}
function hideStarTip() {
  const tip = document.getElementById("starmap-tip");
  const svg = app.querySelector(".starmap");
  if (svg) svg.classList.remove("dim");
  app.querySelectorAll(".starmap .node.active").forEach((n) => n.classList.remove("active"));
  if (tip) tip.hidden = true;
}

// Drive the power core(s) along the active-workflow path. SMIL animateMotion
// injected via innerHTML doesn't start reliably, so we animate with rAF +
// getPointAtLength. Cancels itself on re-render / navigation and honours
// prefers-reduced-motion.
function initPowerCore() {
  if (window._coreRaf) cancelAnimationFrame(window._coreRaf);
  const svg = app.querySelector(".starmap");
  const path = svg && svg.querySelector("#flow-path");
  const core = svg && svg.querySelector(".power-core");
  const sparks = svg ? Array.from(svg.querySelectorAll(".spark")) : [];
  if (!svg || !path || !core) return;
  const L = path.getTotalLength();
  if (!L) return;
  const place = (el, frac) => { const p = path.getPointAtLength(((frac % 1) + 1) % 1 * L); el.setAttribute("cx", p.x); el.setAttribute("cy", p.y); };
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    place(core, 0); return;
  }
  const durMs = Math.max(9000, (L / 70) * 1000);
  const TAIL_PX = 110;
  const gap = (TAIL_PX / Math.max(1, sparks.length)) / L;
  let start = null;
  const tick = (ts) => {
    if (!document.body.contains(core)) return;  // navigated away → stop
    if (start === null) start = ts;
    const frac = ((ts - start) % durMs) / durMs;
    place(core, frac);
    sparks.forEach((sp, k) => place(sp, frac - (k + 1) * gap));
    window._coreRaf = requestAnimationFrame(tick);
  };
  window._coreRaf = requestAnimationFrame(tick);
}

/* ── 9. Command palette ───────────────────────────────────────────────────── */
const palette = byId("palette");
let paletteResults = [], paletteSel = 0, lastFocus = null;

function openPalette() {
  lastFocus = document.activeElement;
  palette.hidden = false;
  palette.innerHTML = `<div class="palette-box">
    <div class="palette-input"><span aria-hidden="true">⌕</span>
      <input id="pal-input" type="text" placeholder="Jump to a member, skill, or sector…" aria-label="Search" autocomplete="off"></div>
    <div class="palette-results" id="pal-results" role="listbox"></div>
    <div class="palette-hint"><span><kbd>↑</kbd><kbd>↓</kbd> navigate</span><span><kbd>↵</kbd> open</span><span><kbd>esc</kbd> close</span></div>
  </div>`;
  paletteQuery("");
  const input = byId("pal-input");
  input.focus();
  input.addEventListener("input", () => paletteQuery(input.value));
}
function closePalette() {
  palette.hidden = true; palette.innerHTML = "";
  if (lastFocus && lastFocus.focus) lastFocus.focus();
}
function paletteQuery(q) {
  const s = q.trim().toLowerCase();
  paletteResults = (!s ? searchIndex : searchIndex.filter((r) => r.hay.includes(s))).slice(0, 9);
  paletteSel = 0;
  renderPaletteResults();
}
function renderPaletteResults() {
  const box = byId("pal-results"); if (!box) return;
  if (!paletteResults.length) { box.innerHTML = `<div class="palette-empty">No matches in the guild.</div>`; return; }
  box.innerHTML = paletteResults.map((r, i) => `<div class="palette-result" role="option"
      aria-selected="${i === paletteSel}" data-hash="${esc(r.hash)}">
      <span class="pr-icon">${esc(r.icon)}</span>
      <div><div class="pr-label">${esc(r.label)}</div><div class="pr-sub">${esc((r.sub || "").slice(0, 70))}</div></div>
      <span class="pr-kind">${esc(r.kind)}</span></div>`).join("");
  const sel = box.querySelector('[aria-selected="true"]');
  if (sel) sel.scrollIntoView({ block: "nearest" });
}
function paletteGo(i) {
  const r = paletteResults[i]; if (!r) return;
  closePalette(); location.hash = r.hash;
}

/* ── 10. Delegated listeners + init ───────────────────────────────────────── */
app.addEventListener("focusout", (e) => {
  const el = e.target && e.target.closest && e.target.closest("[data-medit]");
  if (el) saveMemberEdit(el);
});
app.addEventListener("click", (e) => {
  const mdel = e.target.closest("#member-delete"); if (mdel) { e.preventDefault(); deleteMemberUI(mdel.dataset.member); return; }
  const mnew = e.target.closest("#member-new"); if (mnew) { e.preventDefault(); createMemberUI(); return; }
  const srcBtn = e.target.closest("#f-src button");
  if (srcBtn) { pressSeg(byId("f-src"), srcBtn); filterSkills(); return; }
  const logBtn = e.target.closest("#f-logtype button");
  if (logBtn) { pressSeg(byId("f-logtype"), logBtn); filterLog(); return; }
  const cssEsc = (v) => (window.CSS && CSS.escape) ? CSS.escape(v) : v;
  // Block/allow a skill, then re-render in place and restore focus to the toggle.
  const tog = e.target.closest(".si-toggle");
  if (tog) {
    e.preventDefault();
    toggleBlock(tog.dataset.member, tog.dataset.skill);
    refreshView();
    app.querySelector(`.si-toggle[data-skill="${cssEsc(tog.dataset.skill)}"]`)?.focus();
    return;
  }
  // Unassign a skill from the agent (remove it from the list entirely).
  const un = e.target.closest(".unassign-btn");
  if (un) { e.preventDefault(); unassign(un.dataset.member, un.dataset.skill); refreshView(); app.querySelector(".sk-head")?.scrollIntoView({ block: "nearest" }); return; }
  // Open / close the assign panel.
  const at = e.target.closest("#assign-toggle");
  if (at) { e.preventDefault(); assignOpenFor = (assignOpenFor === at.dataset.member) ? null : at.dataset.member; refreshView(); byId("assign-q")?.focus(); return; }
  // Assign a skill to the agent (panel stays open + filter preserved).
  const ac = e.target.closest(".assign-chip");
  if (ac) { e.preventDefault(); assign(ac.dataset.member, ac.dataset.skill); refreshView(); filterAssign(); byId("assign-q")?.focus(); return; }
  // Arsenal page: toggle the wield dropdown open/closed.
  const db = e.target.closest(".wield-drop-btn");
  if (db) {
    e.preventDefault();
    const dropdown = db.closest(".wield-dropdown");
    const isOpen = dropdown.classList.contains("open");
    document.querySelectorAll(".wield-dropdown.open").forEach(d => d.classList.remove("open"));
    if (!isOpen) dropdown.classList.add("open");
    return;
  }
  // Arsenal page: grant/revoke a model for an agent via checkbox.
  const wc = e.target.closest(".wield-chip");
  if (wc) {
    e.preventDefault();
    toggleWield(wc.dataset.member, wc.dataset.model);
    refreshView();
    return;
  }
  // Dossier: revoke a model from this agent.
  const wr = e.target.closest(".wc-revoke");
  if (wr) { e.preventDefault(); revokeModel(wr.dataset.member, wr.dataset.model); refreshView(); return; }
  // Arsenal page: reset every model assignment.
  const rw = e.target.closest("#reset-weapons");
  if (rw) { e.preventDefault(); resetAllWeapons(); refreshView(); return; }
  // Deactivate / reactivate a skill for the whole guild.
  const dt = e.target.closest("#deactivate-toggle");
  if (dt) { e.preventDefault(); toggleDisabled(dt.dataset.skill); refreshView(); byId("deactivate-toggle")?.focus(); return; }
  // Deactivate / reactivate a weapon (model) guild-wide from Arsenal page.
  const dw = e.target.closest("[data-weapon]");
  const pw = e.target.closest(".weapon-power-btn");
  if (pw) {
    e.preventDefault();
    const mid = pw.dataset.weapon;
    const wasOff = isWeaponDisabled(mid);
    toggleWeaponDisabled(mid);
    if (!wasOff) {
      // Deactivating — force-remove from every member
      GUILD.members.forEach((m) => {
        if (baseWeapons(m).includes(mid)) {
          ensureWov(m.id).remove.push(mid);
          const addIdx = weaponOv[m.id]?.add?.indexOf(mid);
          if (addIdx > -1) weaponOv[m.id].add.splice(addIdx, 1);
          cleanWov(m.id);
        } else {
          const o = getWov(m.id);
          if (o.add.includes(mid)) {
            ensureWov(m.id).add.splice(ensureWov(m.id).add.indexOf(mid), 1);
            cleanWov(m.id);
          }
        }
      });
      saveWeapons();
    }
    refreshView();
    return;
  }
  if (dw && dw.classList.contains("deactivate-toggle")) { e.preventDefault(); toggleWeaponDisabled(dw.dataset.weapon); refreshView(); return; }
  // Reset every override on this agent.
  const rm = e.target.closest("#reset-member");
  if (rm) { resetMember(rm.dataset.member); refreshView(); return; }
  // Whole-card navigation — but let inner links (skill chips) handle their own clicks.
  const card = e.target.closest(".member-card");
  if (card && !e.target.closest("a")) { location.hash = card.dataset.href; }
});
app.addEventListener("dragstart", e => {
  const card = e.target.closest(".weapon-card");
  if (!card) return;
  e.dataTransfer.effectAllowed = "move";
  e.dataTransfer.setData("text/plain", card.dataset.model);
  card.classList.add("dragging");
  app.dataset.dragModel = card.dataset.model;
  app.dataset.dragMember = card.dataset.member;
});
app.addEventListener("dragover", e => {
  const card = e.target.closest(".weapon-card");
  if (!card) return;
  if (app.dataset.dragMember && app.dataset.dragMember !== card.dataset.member) return;
  e.preventDefault();
  e.dataTransfer.dropEffect = "move";
  card.classList.add("drag-over");
});
app.addEventListener("drop", e => {
  const card = e.target.closest(".weapon-card");
  if (!card) return;
  e.preventDefault();
  const srcMember = app.dataset.dragMember;
  const srcModel = app.dataset.dragModel;
  const tgtMember = card.dataset.member;
  const tgtModel = card.dataset.model;
  if (!srcMember || !srcModel || srcMember !== tgtMember) return;
  const m = byMember.get(srcMember);
  if (!m) return;
  const current = effectiveWeapons(m).map(w => w.model);
  const srcIdx = current.indexOf(srcModel);
  const tgtIdx = current.indexOf(tgtModel);
  if (srcIdx === -1 || tgtIdx === -1 || srcIdx === tgtIdx) return;
  current.splice(srcIdx, 1);
  current.splice(tgtIdx, 0, srcModel);
  reorderWeapons(srcMember, current);
  refreshView();
});
app.addEventListener("dragend", () => {
  app.querySelectorAll(".weapon-card.dragging").forEach(el => el.classList.remove("dragging"));
  app.querySelectorAll(".weapon-card.drag-over").forEach(el => el.classList.remove("drag-over"));
  delete app.dataset.dragModel;
  delete app.dataset.dragMember;
});
// dragleave cleanup
app.addEventListener("dragleave", e => { const c = e.target.closest && e.target.closest(".weapon-card"); if (c) c.classList.remove("drag-over"); });
app.addEventListener("keydown", (e) => {
  if (e.key !== "Enter" && e.key !== " ") return;
  const card = e.target.closest(".member-card");
  // Only when the card itself is focused — its skill-chip <a> children handle their own Enter natively.
  if (card && e.target === card) { e.preventDefault(); location.hash = card.dataset.href; }
});
app.addEventListener("input", debounce((e) => {
  if (e.target.id === "f-q") filterSkills();
  else if (e.target.id === "assign-q") filterAssign();
}, 140));
app.addEventListener("change", (e) => { if (e.target.id === "f-level" || e.target.id === "f-sort") filterSkills(); });

// star-map highlight via delegation (mouse + keyboard)
app.addEventListener("mouseover", (e) => { const n = e.target.closest(".starmap .node, .starmap .you-core, .starmap .cgate"); if (n) showStarTip(n, e); });
app.addEventListener("mousemove", (e) => { const n = e.target.closest(".starmap .node, .starmap .you-core, .starmap .cgate"); if (n) showStarTip(n, e); });
app.addEventListener("mouseout", (e) => { const n = e.target.closest(".starmap .node, .starmap .you-core, .starmap .cgate"); if (n && !e.relatedTarget?.closest?.(".starmap .node, .starmap .you-core, .starmap .cgate")) hideStarTip(); });
app.addEventListener("focusin", (e) => { const n = e.target.closest(".starmap .node, .starmap .you-core, .starmap .cgate"); if (n) { const r = n.getBoundingClientRect(); showStarTip(n, { clientX: r.left + r.width / 2, clientY: r.top + r.height / 2 }); } });
app.addEventListener("focusout", (e) => { if (e.target.closest(".starmap .node, .starmap .you-core, .starmap .cgate")) hideStarTip(); });

byId("topbar").addEventListener("click", (e) => {
  if (e.target.closest("#nav-toggle")) {
    const nav = byId("nav"), t = byId("nav-toggle");
    const open = nav.classList.toggle("open");
    t.setAttribute("aria-expanded", String(open));
  }
  if (e.target.closest("#palette-trigger")) openPalette();
});

palette.addEventListener("click", (e) => {
  if (e.target === palette) { closePalette(); return; }
  const r = e.target.closest(".palette-result");
  if (r) paletteGo(paletteResults.findIndex((x) => x.hash === r.dataset.hash));
});

document.addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); palette.hidden ? openPalette() : closePalette(); return; }
  if (palette.hidden) return;
  if (e.key === "Escape") { e.preventDefault(); closePalette(); }
  else if (e.key === "ArrowDown") { e.preventDefault(); paletteSel = Math.min(paletteSel + 1, paletteResults.length - 1); renderPaletteResults(); }
  else if (e.key === "ArrowUp") { e.preventDefault(); paletteSel = Math.max(paletteSel - 1, 0); renderPaletteResults(); }
  else if (e.key === "Enter") { e.preventDefault(); paletteGo(paletteSel); }
});

function setFooter() {
  const c = GUILD.meta.counts;
  const oc = totalOverrides();
  const ver = GUILD.meta.version || "0.0.0";
  const brandVer = byId("brand-ver");
  if (brandVer) brandVer.textContent = `v${ver}`;
  byId("footer-meta").innerHTML =
    `${esc(GUILD.meta.name)} · ${c.members} members · ${c.skills} skills · ${c.domains} sectors · ` +
    `release v${esc(ver)} · schema v${GUILD.meta.schemaVersion} · generated ${esc(GUILD.meta.generated)}` +
    (oc ? ` · <button id="reset-overrides" class="footer-btn">${oc} unsaved edit${oc > 1 ? "s" : ""} · reset all</button>` : "");
}

byId("footer").addEventListener("click", (e) => {
  if (e.target.closest("#reset-overrides")) { resetAll(); refreshView(); }
});

window.addEventListener("hashchange", onRoute);
if (!location.hash) location.replace("#/map");
onRoute();
setFooter();

// ── Fallen Sword skill tooltip ──────────────────────────────────────────────
const fsTip = document.createElement("div");
fsTip.id = "fs-tip";
fsTip.setAttribute("role", "tooltip");
fsTip.setAttribute("aria-hidden", "true");
document.body.appendChild(fsTip);

let tipTarget = null;
const MARGIN = 12;

function showTip(el, x, y) {
  const name  = el.dataset.tipName  || "";
  const level = el.dataset.tipLevel || "";
  const blurb = el.dataset.tipBlurb || "";
  fsTip.innerHTML = `
    <div class="fst-header">
      <div class="fst-name">${esc(name)}</div>
      ${level ? `<div class="fst-level">${esc(level)}</div>` : ""}
    </div>
    <div class="fst-body"><div class="fst-blurb">${esc(blurb)}</div></div>`;
  positionTip(x, y);
  fsTip.classList.add("visible");
}

function positionTip(x, y) {
  const tw = fsTip.offsetWidth || 210;
  const th = fsTip.offsetHeight || 80;
  const vw = window.innerWidth, vh = window.innerHeight;
  let left = x + MARGIN;
  let top  = y + MARGIN;
  if (left + tw > vw - 8) left = x - tw - MARGIN;
  if (top  + th > vh - 8) top  = y - th - MARGIN;
  fsTip.style.left = `${Math.max(8, left)}px`;
  fsTip.style.top  = `${Math.max(8, top)}px`;
}

function hideTip() {
  fsTip.classList.remove("visible");
  tipTarget = null;
}

document.addEventListener("mousemove", (e) => {
  const sit = e.target.closest(".sit[data-tip-name]");
  if (sit) {
    if (tipTarget !== sit) { tipTarget = sit; showTip(sit, e.clientX, e.clientY); }
    else positionTip(e.clientX, e.clientY);
  } else if (tipTarget) {
    hideTip();
  }
});

document.addEventListener("mouseleave", hideTip);
document.addEventListener("scroll", hideTip, true);

// Close wield dropdowns when clicking outside.
document.addEventListener("click", (e) => {
  if (!e.target.closest(".wield-dropdown")) {
    document.querySelectorAll(".wield-dropdown.open").forEach(d => d.classList.remove("open"));
  }
});

})();
