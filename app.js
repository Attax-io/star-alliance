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
  "opus":             { label: "Opus",            color: "#e8c93a", tier: "Master",  host: "Anthropic · native",  desc: "Claude Opus 4.8 — the master brain. Orchestrates the guild, reasons deepest, reviews everything. This IS the run.",
    call: "You ARE Opus — the orchestrator. Delegate sub-work via the Task tool: subagent_type + model:'opus' for heavy sub-reasoning.",
    meter: { kind: "sub", note: "Claude subscription · unmetered" } },
  "sonnet":           { label: "Sonnet",          color: "#3df0ff", tier: "Thinker", host: "Anthropic · native",  desc: "Claude Sonnet 4.6 — the reliable longsword. Fast, balanced daily dispatch.",
    call: "Task tool subagent, model:'sonnet'. Or switch the main loop with /model sonnet.",
    meter: { kind: "sub", note: "Claude subscription · unmetered" } },
  "haiku":            { label: "Haiku",           color: "#4ec985", tier: "Light",   host: "Anthropic · native",  desc: "Claude Haiku 4.5 — the dagger. Fastest and cheapest, for simple strikes.",
    call: "Task tool subagent, model:'haiku' — cheap mechanical strikes.",
    meter: { kind: "sub", note: "Claude subscription · unmetered" } },
  "gpt-5.5":          { label: "GPT-5.5",         color: "#9d7bff", tier: "Premium", host: "OpenAI · direct",     desc: "OpenAI GPT-5.5 — a US-hosted frontier second opinion. Premium-priced.",
    call: "OpenAI direct (provision pending). POST https://api.openai.com/v1/chat/completions, Bearer $OPENAI_API_KEY, model:'gpt-5.5'.",
    meter: { kind: "off", note: "Not provisioned — no key on device yet" } },
  "minimax-m3":       { label: "MiniMax M3",      color: "#4ec9a0", tier: "Doer",    host: "MiniMax · DIRECT",    desc: "MiniMax M3 — the primary doer. Cheap, 1M context, for bulk delegated work. Use the DIRECT cloud sub — the old Ollama minimax-m3 route is RETIRED.",
    call: "DIRECT cloud sub — NOT Ollama.\nPOST https://api.minimax.io/v1/text/chatcompletion_v2\nAuthorization: Bearer $(cat ~/.config/minimax/m3.key)\nbody: { model:'MiniMax-M3', messages:[…] }",
    meter: { kind: "used", spent: 0, quota: 100, unit: "M tok", est: true, note: "est · set your real plan cap" } },
  "glm-5.2":          { label: "GLM-5.2",         color: "#d4a05a", tier: "Bench",   host: "Ollama Cloud",        desc: "GLM-5.2 — the staff. Coding-first, strong multilingual analysis. Pulled & ready.",
    call: "Ollama Cloud sub:  ollama run glm-5.2:cloud \"…\"\nor POST localhost:11434/api/generate { model:'glm-5.2:cloud', prompt:'…' }   ✓ pulled",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · shares the Ollama Cloud pool" } },
  "kimi-k2.7":        { label: "Kimi K2.7",       color: "#ff6b8a", tier: "Bench",   host: "Ollama Cloud",        desc: "Kimi K2.7 — the warhammer. Long-horizon coding and agentic work.",
    call: "Ollama Cloud sub:  ollama pull kimi-k2:cloud  then  ollama run kimi-k2:cloud \"…\"  (verify exact cloud tag).",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · not yet pulled · shares Ollama Cloud pool" } },
  "deepseek-v4-pro":  { label: "DeepSeek V4 Pro", color: "#5b8cff", tier: "Bench",   host: "Ollama Cloud",        desc: "DeepSeek V4 Pro — the greatsword. Frontier MoE reasoning.",
    call: "Ollama Cloud sub:  ollama pull deepseek-v3.1:cloud  then  ollama run deepseek-v3.1:cloud \"…\"  (verify exact cloud tag).",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · not yet pulled · shares Ollama Cloud pool" } },
  "nemotron-3-ultra": { label: "Nemotron-3 Ultra",color: "#7fd4ff", tier: "Bench",   host: "Ollama Cloud",        desc: "Nemotron-3 Ultra — the lance. High-throughput reasoning, long agent runs.",
    call: "Ollama Cloud sub:  ollama pull <nemotron-cloud-tag>  then  ollama run <tag> \"…\"  (verify the exact cloud tag first).",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · not yet pulled · shares Ollama Cloud pool" } },
  "qwen3.5":          { label: "Qwen 3.5",        color: "#c47fff", tier: "Bench",   host: "Ollama Cloud",        desc: "Qwen 3.5 — the shortsword. Versatile general-purpose workhorse.",
    call: "Ollama Cloud sub:  ollama pull qwen3-coder:cloud  then  ollama run qwen3-coder:cloud \"…\"  (verify exact cloud tag).",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · not yet pulled · shares Ollama Cloud pool" } },
  "gemma4":           { label: "Gemma 4",         color: "#ffb04e", tier: "Bench",   host: "Ollama Cloud",        desc: "Gemma 4 — the throwing knife. Small and light, for quick cheap passes.",
    call: "Ollama Cloud sub:  ollama pull gemma3:cloud  then  ollama run gemma3:cloud \"…\"  (verify exact cloud tag).",
    meter: { kind: "used", spent: 0, quota: 100, unit: "req", est: true, pool: "Ollama Cloud", note: "est · not yet pulled · shares Ollama Cloud pool" } },
};
const modelMeta = (m) => MODELS[m] || { label: m || "—", color: "#8a93ad" };
const modelGlyph = (m) => (modelMeta(m).label).replace(/[^A-Za-z0-9]/g, "").slice(0, 2).toUpperCase();
// The armory display order for the Arsenal page.
const ARSENAL = ["opus", "sonnet", "haiku", "gpt-5.5", "minimax-m3", "glm-5.2", "kimi-k2.7", "deepseek-v4-pro", "nemotron-3-ultra", "qwen3.5", "gemma4"];
// Lower rank = closer to the core (heavier model). Drives star-map ring assignment.
const TIER_RANK = { "opus": 0, "gpt-5.5": 1, "sonnet": 2, "glm-5.2": 3, "kimi-k2.7": 3, "minimax-m3": 3, "deepseek-v4-pro": 3, "nemotron-3-ultra": 3, "qwen3.5": 3, "gemma4": 4, "haiku": 4 };
// model id → the ollama `:cloud` tag we expect, so /api/arsenal can mark it pulled.
const CLOUD_TAG = {
  "minimax-m3": "minimax-m3:cloud", "glm-5.2": "glm-5.2:cloud", "kimi-k2.7": "kimi-k2:cloud",
  "deepseek-v4-pro": "deepseek-v3.1:cloud", "nemotron-3-ultra": "nemotron:cloud",
  "qwen3.5": "qwen3-coder:cloud", "gemma4": "gemma3:cloud",
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
const N = GUILD.members.length;
const byMember = new Map(GUILD.members.map((m) => [m.id, m]));
const bySkill  = new Map(GUILD.skills.map((s) => [s.id, s]));
const byDomain = new Map(GUILD.domains.map((d) => [d.id, d]));
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
  cleanOv(mid); saveOverrides();
}
function assign(mid, sid) {
  const o = ensureOv(mid), base = byMember.get(mid).skills;
  pull(o.block, sid);                                  // (re)assigning clears any stale block
  if (base.includes(sid)) pull(o.remove, sid);         // re-assign a previously removed base skill
  else if (!o.add.includes(sid)) o.add.push(sid);
  cleanOv(mid); saveOverrides();
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
const saveDisabled = () => { try { localStorage.setItem("sa-disabled", JSON.stringify(disabled)); } catch (_) {} };
const isDisabled = (sid) => disabled.includes(sid);
const toggleDisabled = (sid) => { isDisabled(sid) ? pull(disabled, sid) : disabled.push(sid); saveDisabled(); };

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
  cleanWov(mid); saveWeapons();
}
function revokeModel(mid, model) {
  const o = ensureWov(mid), m = byMember.get(mid);
  pull(o.add, model);
  if (baseWeapons(m).includes(model) && !o.remove.includes(model)) o.remove.push(model);
  cleanWov(mid); saveWeapons();
}
const toggleWield = (mid, model) => { const m = byMember.get(mid); wields(m, model) ? revokeModel(mid, model) : grantModel(mid, model); };
const resetAllWeapons = () => { weaponOv = {}; saveWeapons(); };
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
// s.art is a build-time-vetted inline SVG sigil (sanitized in gen, sourced from skills-meta.json) —
// injected raw like avatars; falls back to the emoji icon when absent.
const skillArt = (s) => (s && s.art) ? s.art : `<span class="ico-emoji">${esc(s ? s.icon : "📦")}</span>`;

function skillChip(id, mid) {
  const s = bySkill.get(id);
  const name = s ? s.name : id;
  const blocked = mid && isBlocked(mid, id);
  const cls = "tag" + (isShared(id) ? " shared" : "") + (blocked ? " blocked" : "");
  return `<a class="${cls}" href="#/skills/${esc(id)}">${s ? esc(s.icon) + " " : ""}${esc(name)}</a>`;
}

function memberCard(m) {
  const assigned = assignedSkills(m);
  const shown = assigned.slice(0, 5).map((s) => skillChip(s, m.id)).join("");
  const extra = assigned.length > 5 ? `<span class="tag">+${assigned.length - 5}</span>` : "";
  const active = effectiveSkills(m).length;
  const blocked = assigned.length - active;
  // role=link (not <a>): skill chips inside are real anchors, and nesting <a> in <a> is invalid HTML.
  return `<div class="member-card glass" role="link" tabindex="0" data-href="#/members/${esc(m.id)}"
       aria-label="${esc(m.name)} — ${esc(m.role)}" style="--mc:${esc(m.color)}" data-id="${esc(m.id)}">
    <div class="mc-top">
      <div class="avatar">${m.avatar || ""}</div>
      <div><div class="mc-name">${esc(m.name)}</div><div class="mc-role">${esc(m.role)}</div></div>
    </div>
    <div class="mc-skills">${shown}${extra}</div>
    <div class="mc-foot">
      <span class="tag">${esc(modelMeta(m.model).label)}</span>
      <span class="sep"></span><span>${pluralize(active, "skill")}${blocked ? ` <span class="blk-note">· ${blocked} blocked</span>` : ""}</span>
      <span class="sep"></span><span>${pluralize(m.weapons.length, "weapon")}</span>
    </div>
  </div>`;
}

/* ── 6. Views ─────────────────────────────────────────────────────────────── */

// Star Map ------------------------------------------------------------------
function renderStarMap() {
  const c = GUILD.meta.counts;
  return `${viewHead("Constellation", "Star Map",
      `${c.members} members linked by shared specializations across ${c.skills} skills.`)}
    <div class="starmap-wrap glass" style="padding:24px">
      ${buildStarMapSVG()}
      <div class="map-legend">
        <span class="lg"><span class="dot" style="background:#e8c93a"></span>Opus core</span>
        <span class="lg"><span class="dot" style="background:#3df0ff"></span>Sonnet ring</span>
        <span class="lg"><span class="ln"></span>shared specialization (brighter = rarer)</span>
      </div>
    </div>
    <div class="starmap-list grid roster-grid" style="margin-top:24px">
      ${GUILD.members.map(memberCard).join("")}
    </div>`;
}

function buildStarMapSVG() {
  const members = GUILD.members;
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

  // Rarity-weighted edges over each member's EFFECTIVE skill set (override-aware).
  const eff = new Map(members.map((m) => [m.id, new Set(effectiveSkills(m))]));
  const freq = {}; GUILD.skills.forEach((s) => { freq[s.id] = liveFreq(s.id); });
  const edges = [];
  let maxW = 0;
  for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
    const A = members[i], B = members[j], sa = eff.get(A.id), sb = eff.get(B.id);
    const shared = [...sa].filter((s) => sb.has(s) && freq[s] > 0 && freq[s] < N);  // skip skills on everyone
    if (!shared.length) continue;
    const w = shared.reduce((t, s) => t + Math.log(N / freq[s]), 0);
    if (w <= 0) continue;
    edges.push({ a: A.id, b: B.id, w, shared });
    maxW = Math.max(maxW, w);
  }

  const orbits = radii.map((R, i) =>
    `<circle class="orbit${i === radii.length - 1 ? " dashed" : ""}" cx="${cx}" cy="${cy}" r="${R.toFixed(1)}"/>`).join("");

  const links = edges.map((e) => {
    const A = pos[e.a], B = pos[e.b];
    const s = (e.w / maxW).toFixed(3);
    const title = e.shared.map((x) => bySkill.get(x)?.name || x).join(", ");
    return `<line class="link" data-a="${esc(e.a)}" data-b="${esc(e.b)}" style="--s:${s}"
      x1="${A.x.toFixed(1)}" y1="${A.y.toFixed(1)}" x2="${B.x.toFixed(1)}" y2="${B.y.toFixed(1)}"><title>${esc(title)}</title></line>`;
  }).join("");

  const nodes = members.map((m) => {
    const p = pos[m.id];
    const carriers = effectiveSkills(m).length;
    return `<a href="#/members/${esc(m.id)}" class="node" data-id="${esc(m.id)}" style="--c:${esc(m.color)}"
        aria-label="${esc(m.name)} — ${esc(m.role)}, ${pluralize(carriers, "skill")}">
      <g transform="translate(${p.x.toFixed(1)},${p.y.toFixed(1)})">
        <circle class="halo" r="20"/><circle class="ring2" r="14"/><circle class="core" r="9"/>
      </g>
      <text class="node-label" x="${p.x.toFixed(1)}" y="${(p.y + 32).toFixed(1)}">${esc(m.name)}</text>
      <text class="node-sub" x="${p.x.toFixed(1)}" y="${(p.y + 46).toFixed(1)}">${esc(modelMeta(m.model).label)}</text>
    </a>`;
  }).join("");

  return `<svg class="starmap" viewBox="0 0 800 800" role="group" aria-label="Guild constellation — members linked by shared skills">
    <g class="orbits" aria-hidden="true">${orbits}</g>
    <g class="links" aria-hidden="true">${links}</g>
    <g class="map-core" aria-hidden="true">
      <circle cx="${cx}" cy="${cy}" r="3" fill="#e8c93a"/>
      <text x="${cx}" y="${cy + 5}" text-anchor="middle" font-size="15" fill="#e8c93a" opacity=".8">✦</text>
    </g>
    <g class="nodes">${nodes}</g>
  </svg>`;
}

// Members -------------------------------------------------------------------
function renderMembers() {
  return `${viewHead("Roster", "Guild Members",
      `${GUILD.members.length} specialists, each carrying a curated skill set.`)}
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
    return `<div class="weapon-card${w.added ? " added" : ""}" draggable="true" data-model="${esc(w.model)}" data-member="${esc(m.id)}" style="--wc:${esc(mm.color)}">
      <div class="weapon-rank">${["PRIMARY", "SECONDARY", "TERTIARY"][i] || "RESERVE"}${w.added ? ` · <span class="wc-added">granted</span>` : ""}</div>
      <div class="weapon-name"><span class="weapon-glyph" style="--wc:${esc(mm.color)}">${esc(modelGlyph(w.model))}</span>${esc(mm.label)}
        <button class="wc-revoke" type="button" data-member="${esc(m.id)}" data-model="${esc(w.model)}"
          title="Revoke from this agent" aria-label="Revoke ${esc(mm.label)} from this agent">✕</button>
      </div>
      <div class="weapon-desc">${esc(w.desc || mm.desc || "")}</div>
    </div>`;
  }).join("");

  const skills = assigned.map((sid) => {
    const s = bySkill.get(sid);
    const off = isDisabled(sid);
    const blk = isBlocked(m.id, sid);
    const isAdded = !m.skills.includes(sid);
    return `<div class="skill-line${blk || off ? " blocked" : ""}" data-skill="${esc(sid)}">
      <button class="si-toggle" type="button" data-member="${esc(m.id)}" data-skill="${esc(sid)}"
        aria-pressed="${blk}" aria-label="${blk ? "Allow" : "Block"} ${esc(s ? s.name : sid)} for this agent"
        title="${blk ? "Blocked — click to allow" : "Click to block for this agent"}">
        <span class="si-ico">${s ? esc(s.icon) : "📦"}</span></button>
      <a class="sn" href="#/skills/${esc(sid)}">${esc(s ? s.name : sid)}</a>
      ${isAdded ? `<span class="tag added">added</span>` : ""}
      ${off ? `<a class="tag off" href="#/skills/${esc(sid)}" title="Deactivated guild-wide">deactivated</a>`
            : (blk ? `<span class="tag blocked">blocked</span>`
                   : (isShared(sid) ? `<span class="tag shared">shared</span>` : ""))}
      <span class="sb">${esc(s ? s.blurb : "")}</span>
      <button class="unassign-btn" type="button" data-member="${esc(m.id)}" data-skill="${esc(sid)}"
        title="Unassign from this agent" aria-label="Unassign ${esc(s ? s.name : sid)} from this agent">✕</button>
    </div>`;
  }).join("");

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
        <div class="avatar lg">${m.avatar || ""}</div>
        <div class="dh-meta">
          <h1 class="dh-name">${esc(m.name)}</h1>
          <div class="dh-role">${esc(m.role)}</div>
          <div class="dh-tags">
            <span class="tag gold">${esc(modelMeta(m.model).label)}</span>
            <span class="tag">${pluralize(active.length, "skill")}</span>
            ${blocked ? `<span class="tag rose">${blocked} blocked</span>` : ""}
            ${added ? `<span class="tag green">${added} added</span>` : ""}
            <span class="tag cyan">${sharedN} shared</span>
          </div>
          <p class="dh-summary">${esc(m.summary)}</p>
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
      <div class="section glass">
        <div class="section-title sk-head">
          <span>Skills carried · ${active.length}${blocked ? ` <span class="blk-note">· ${blocked} blocked</span>` : ""}${added ? ` <span class="add-note">· ${added} added</span>` : ""}</span>
          ${memberHasOverrides(m.id) ? `<button class="reset-btn" id="reset-member" data-member="${esc(m.id)}">Reset agent</button>` : ""}
        </div>
        <p class="skill-hint">Tap a skill's <strong>icon</strong> to block it · <strong>✕</strong> to unassign · or assign a new one below. Edits ripple through the Star Map, carrier counts, and roster, and persist in this browser.</p>
        ${skills}
        ${assignPanel}
      </div>
      <div class="panel-grid">
        <div class="section glass">
          <div class="section-title">Deployment</div>
          <div class="kv">
            <div><div class="k">Deploy when</div><div class="v">${esc(m.deploy)}</div></div>
            <div><div class="k">Triggers</div><div class="v">${esc(m.triggers)}</div></div>
            ${m.description ? `<div><div class="k">Mandate</div><div class="v">${esc(m.description)}</div></div>` : ""}
          </div>
        </div>
        <div class="section glass">
          <div class="section-title">Role boundaries</div>
          <div class="duo">
            <ul class="bullets yes">${m.does.map((d) => `<li>${esc(d)}</li>`).join("")}</ul>
            <ul class="bullets no">${m.doesnt.map((d) => `<li>${esc(d)}</li>`).join("")}</ul>
          </div>
        </div>
      </div>
    </div>`;
}

// Arsenal / Armory ----------------------------------------------------------
function renderArsenal() {
  const anyOv = Object.keys(weaponOv).length;
  const cards = ARSENAL.map((id) => {
    const mm = modelMeta(id);
    const wielders = GUILD.members.filter((m) => wields(m, id)).length;
    const chips = GUILD.members.map((m) => {
      const on = wields(m, id);
      return `<button class="wield-chip${on ? " on" : ""}" type="button" data-member="${esc(m.id)}" data-model="${esc(id)}"
        aria-pressed="${on}" title="${on ? "Revoke from" : "Assign to"} ${esc(m.name)}">
        <span class="wc-dot" aria-hidden="true">${on ? "✓" : "＋"}</span>${esc(m.name)}</button>`;
    }).join("");
    return `<div class="model-card" style="--wc:${esc(mm.color)}">
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
      <p class="model-desc">${esc(mm.desc || "")}</p>
      ${mm.call ? `<div class="model-call">
        <div class="mc-head"><span class="mc-label">⚔ How to summon</span></div>
        <pre class="mc-recipe">${esc(mm.call)}</pre>
      </div>` : ""}
      <div class="wield-row">${chips}</div>
    </div>`;
  }).join("");

  let liveTag;
  if (arsenalFetching && !arsenalLive) liveTag = `<span class="tag">⟳ syncing…</span>`;
  else if (arsenalLive && !arsenalLive.offline) liveTag = `<span class="tag green">● live — ${esc(String((arsenalLive.pulled || []).length))} cloud models pulled</span>`;
  else if (arsenalLive && arsenalLive.offline) liveTag = `<span class="tag">○ static estimates (start serve.cjs for live data)</span>`;
  else liveTag = "";

  return `${viewHead("Armory", "Arsenal",
      "Every model in the guild's armory — with its <strong>summon recipe</strong>. Claude = native master brain; MiniMax = <strong>direct</strong> cloud sub (not Ollama); the bench = Ollama Cloud. On the dev server each card shows whether its cloud model is actually pulled. Tap an agent under a model to grant/revoke.")}
    <div class="arsenal-toolbar">
      ${liveTag}
      <button class="reset-btn" id="refresh-arsenal" type="button">⟳ Refresh</button>
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
  return `<a class="skill-card glass${off ? " deactivated" : ""}" href="#/skills/${esc(s.id)}" data-id="${esc(s.id)}">
    <div class="sc-top">
      <div class="sc-icon${s.art ? " art" : ""}">${skillArt(s)}</div>
      <div><div class="sc-name">${esc(s.name)}</div><div class="sc-ver">v${esc(s.version)}</div></div>
    </div>
    <div class="sc-blurb">${esc(s.blurb)}</div>
    <div class="sc-foot">
      ${off ? `<span class="tag off">deactivated</span>` : ""}
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

  return `${crumb("#/skills", "All skills")}
    <div class="skill-panel">
      <div class="sp-hero glass${off ? " deactivated" : ""}">
        <div class="sp-icon${s.art ? " art" : ""}">${skillArt(s)}</div>
        <div class="sp-meta">
          <h1 class="sp-title">${esc(s.name)}</h1>
          <div class="sp-tags">
            <span class="tag">v${esc(s.version)}</span>
            <span class="tag ${rampClass(s)}">${esc(s.level)}</span>
            <span class="tag src-${esc(s.src)}">${esc(s.src)}</span>
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
  // Pull real Arsenal data (pulled-status) once per page visit; skipped on in-place re-renders.
  if (key === "arsenal" && !arsenalApplied) refreshArsenalData();
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
function activateNode(id) {
  const svg = app.querySelector(".starmap"); if (!svg) return;
  svg.classList.add("dim");
  svg.querySelectorAll(".node").forEach((n) => n.classList.toggle("active", n.dataset.id === id));
  svg.querySelectorAll(".link").forEach((l) => l.classList.toggle("active", l.dataset.a === id || l.dataset.b === id));
}
function clearNodes() {
  const svg = app.querySelector(".starmap"); if (!svg) return;
  svg.classList.remove("dim");
  svg.querySelectorAll(".active").forEach((x) => x.classList.remove("active"));
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
app.addEventListener("click", (e) => {
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
  // Arsenal page: force a live data re-pull.
  const ra = e.target.closest("#refresh-arsenal");
  if (ra) { e.preventDefault(); arsenalApplied = false; refreshArsenalData(); return; }
  // Arsenal page: grant/revoke a model for an agent (re-render in place, restore focus to the chip).
  const wc = e.target.closest(".wield-chip");
  if (wc) {
    e.preventDefault();
    toggleWield(wc.dataset.member, wc.dataset.model);
    refreshView();
    app.querySelector(`.wield-chip[data-member="${cssEsc(wc.dataset.member)}"][data-model="${cssEsc(wc.dataset.model)}"]`)?.focus();
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
app.addEventListener("mouseover", (e) => { const n = e.target.closest(".node"); if (n) activateNode(n.dataset.id); });
app.addEventListener("mouseout", (e) => { if (e.target.closest(".node")) clearNodes(); });
app.addEventListener("focusin", (e) => { const n = e.target.closest(".node"); if (n) activateNode(n.dataset.id); });
app.addEventListener("focusout", (e) => { if (e.target.closest(".node")) clearNodes(); });

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
  byId("footer-meta").innerHTML =
    `${esc(GUILD.meta.name)} · ${c.members} members · ${c.skills} skills · ${c.domains} sectors · ` +
    `schema v${GUILD.meta.schemaVersion} · generated ${esc(GUILD.meta.generated)}` +
    (oc ? ` · <button id="reset-overrides" class="footer-btn">${oc} unsaved edit${oc > 1 ? "s" : ""} · reset all</button>` : "");
}

byId("footer").addEventListener("click", (e) => {
  if (e.target.closest("#reset-overrides")) { resetAll(); refreshView(); }
});

window.addEventListener("hashchange", onRoute);
if (!location.hash) location.replace("#/map");
onRoute();
setFooter();

})();
