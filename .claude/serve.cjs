// Minimal static file server for previewing the dashboard (dev only).
// /api/arsenal feeds the Arsenal page REAL data on refresh:
//   • which :cloud models are actually pulled (`ollama list`)
//   • Claude spend per family, parsed live from ~/.claude/projects/**/*.jsonl
//     (5-hour rolling window — the same source `ccusage` reads)
//   • hand-edited caps + non-Claude spend from models-usage.json at repo root
// The /api/arsenal endpoint + the claudeUsage() parser were drafted by
// MiniMax M3 (direct cloud sub) and integrated here.
const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');
const { execFile } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
// This project's Claude transcript dir (cwd path with /and. → -, the Claude Code
// convention). Used to scope the delegation rate to THIS project's Opus output.
const PROJECT_TRANSCRIPT_DIR = path.join(
  os.homedir(), '.claude', 'projects', ROOT.replace(/[/.]/g, '-')
);
const PORT = process.env.PORT || 4178;
const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.svg': 'image/svg+xml', '.ico': 'image/x-icon',
};

// Real pulled cloud models, via `ollama list`. Never throws — degrades to empty.
function fetchOllama(cb) {
  execFile('ollama', ['list'], { timeout: 4000 }, (err, stdout) => {
    if (err) return cb({ pulled: [], ollamaUp: false });
    const lines = String(stdout).split(/\r?\n/);
    const pulled = [];
    for (let i = 1; i < lines.length; i++) {       // skip header row
      const line = lines[i].trim();
      if (!line) continue;
      const tag = line.split(/\s+/)[0];
      if (tag && tag.indexOf(':cloud') !== -1) pulled.push(tag);
    }
    cb({ pulled, ollamaUp: true });
  });
}

// Real Claude consumption — drafted by MiniMax M3. Scans the last 6h of
// transcript .jsonl files, buckets usage.{input,output}_tokens by model family,
// and tracks a 5-hour rolling window (win_out = output tokens this window).
// scopeDir (optional): restrict the walk to one project's transcript dir, so the
// delegation rate compares THIS project's doer output against THIS project's Opus
// output — not Opus across every project on the machine.
function claudeUsage(cb, scopeDir) {
  const WINDOW_MS = 5 * 60 * 60 * 1000;
  const SIX_HOURS_MS = 6 * 60 * 60 * 1000;
  const root = scopeDir || path.join(os.homedir(), '.claude', 'projects');
  const result = {
    opus:   { in: 0, out: 0, total: 0, win_out: 0, win_total: 0 },
    sonnet: { in: 0, out: 0, total: 0, win_out: 0, win_total: 0 },
    haiku:  { in: 0, out: 0, total: 0, win_out: 0, win_total: 0 },
  };
  const now = Date.now();
  let rootStat;
  try { rootStat = fs.statSync(root); if (!rootStat.isDirectory()) return cb(result); }
  catch (e) { return cb(result); }
  const cutoff = now - SIX_HOURS_MS;
  const windowStart = now - WINDOW_MS;

  const files = [];
  function walk(dir) {
    let entries;
    try { entries = fs.readdirSync(dir, { withFileTypes: true }); } catch (e) { return; }
    for (const ent of entries) {
      const full = path.join(dir, ent.name);
      try {
        if (ent.isDirectory()) walk(full);
        else if (ent.isFile() && ent.name.endsWith('.jsonl')) {
          const st = fs.statSync(full);
          if (st.mtimeMs >= cutoff) files.push(full);
        }
      } catch (e) { /* skip */ }
    }
  }
  try { walk(root); } catch (e) { return cb(result); }

  let idx = 0;
  function next() {
    if (idx >= files.length) return cb(result);
    const file = files[idx++];
    let stream, rl;
    try { stream = fs.createReadStream(file); rl = readline.createInterface({ input: stream, crlfDelay: Infinity }); }
    catch (e) { return next(); }
    let done = false;
    const finish = () => { if (done) return; done = true; try { rl.close(); } catch (e) {} try { stream.destroy(); } catch (e) {} next(); };
    rl.on('line', (line) => {
      let row; try { row = JSON.parse(line); } catch (e) { return; }
      const msg = row && row.message;
      if (!msg || typeof msg !== 'object') return;
      const model = msg.model, usage = msg.usage;
      if (typeof model !== 'string' || !usage || typeof usage !== 'object') return;
      let fam = null;
      if (model.indexOf('opus') !== -1) fam = 'opus';
      else if (model.indexOf('sonnet') !== -1) fam = 'sonnet';
      else if (model.indexOf('haiku') !== -1) fam = 'haiku';
      if (!fam) return;
      const tsMs = typeof row.timestamp === 'string' ? Date.parse(row.timestamp) : NaN;
      const inWin = !isNaN(tsMs) && tsMs >= windowStart;
      const input = Number(usage.input_tokens) || 0, output = Number(usage.output_tokens) || 0;
      const f = result[fam];
      f.in += input; f.out += output; f.total += input + output;
      if (inWin) { f.win_out += output; f.win_total += input + output; }
    });
    rl.on('close', finish); rl.on('error', finish); stream.on('error', finish);
  }
  next();
}

// Hand-edited caps + non-Claude spend. { "<modelId>": { spent, quota, unit } }
function loadUsage() {
  try {
    const parsed = JSON.parse(fs.readFileSync(path.join(ROOT, 'star-alliance-arsenal', 'models-usage.json'), 'utf8'));
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) return parsed;
  } catch (e) {}
  return {};
}

// Merge live Claude window-spend over the hand-edited caps. Claude spend is
// REAL (k output tokens / 5h); the cap stays whatever models-usage.json sets.
function mergeUsage(claude) {
  const fileU = loadUsage();
  const out = Object.assign({}, fileU);
  const DEF = {
    opus:   { quota: 2000, unit: 'k tok/5h' },
    sonnet: { quota: 4000, unit: 'k tok/5h' },
    haiku:  { quota: 8000, unit: 'k tok/5h' },
  };
  ['opus', 'sonnet', 'haiku'].forEach((fam) => {
    const c = claude[fam] || {};
    const prev = (fileU[fam] && typeof fileU[fam] === 'object') ? fileU[fam] : {};
    out[fam] = {
      spent: Math.round((c.win_out || 0) / 1000),
      quota: Number(prev.quota) || DEF[fam].quota,
      unit: prev.unit || DEF[fam].unit,
    };
  });
  return out;
}

// Per-model usage weights — DERIVED from the canonical registry
// (star-alliance-arsenal/models.json). Literal fallback only if it can't be read.
function loadModelWeights() {
  const fallback = { 'minimax-m3': 1.0, 'glm-5.2': 0.7, 'kimi-k2.7': 0.5, 'deepseek-v4-pro': 0.5, 'nemotron-3-ultra': 0.4, 'qwen3.5': 0.4, 'gemma4': 0.3 };
  try {
    const reg = JSON.parse(fs.readFileSync(path.join(ROOT, 'star-alliance-arsenal', 'models.json'), 'utf8'));
    const w = {};
    for (const [id, d] of Object.entries(reg.models || {})) if (d && d.weight != null) w[id] = d.weight;
    return Object.keys(w).length ? w : fallback;
  } catch (e) { return fallback; }
}

// Estimated 0..1 consumption per model — drafted by MiniMax M3. Pure: recomputes
// on every call from the live Claude window-activity signal (orchestrator burn ⇒
// the doers are working), weighted per model. Claude families get a REAL fill.
function estimateUsage(claude, caps) {
  const WEIGHT = loadModelWeights();
  const CLAUDE_DEFAULT = { opus: 2000, sonnet: 4000, haiku: 8000 };
  const CLAUDE_FAMILY = ['opus', 'sonnet', 'haiku'];
  const clamp01 = (x) => Math.max(0, Math.min(1, x || 0));
  const ids = new Set([...Object.keys(WEIGHT), ...CLAUDE_FAMILY]);
  const c = claude || {};
  const activity = ((c.opus || {}).win_out || 0) + ((c.sonnet || {}).win_out || 0) + ((c.haiku || {}).win_out || 0);
  const base = clamp01(activity / 1500000);
  const result = {};
  for (const id of ids) {
    if (CLAUDE_FAMILY.indexOf(id) !== -1) {
      const capQ = (caps && caps[id] && caps[id].quota) ? caps[id].quota : CLAUDE_DEFAULT[id];
      result[id] = { fill: clamp01((c[id] || {}).win_out / (capQ * 1000)), basis: 'live' };
    } else {
      const w = WEIGHT[id];
      result[id] = { fill: w === undefined ? 0.03 : clamp01(0.03 + base * w), basis: 'estimate' };
    }
  }
  return result;
}

// ── Delegation ledger — REAL per-weapon spend from the backends' usage log.
// Each arsenal backend (summon.py → minimax.py / ollama_cloud.py) appends one
// JSON line per call to star-alliance-arsenal/usage-log.jsonl. We aggregate it
// per guild model id, with lifetime + 7d (week) + 5h (session) windows. This is
// the figure that proves the harness is offloading work to the cheap bench
// instead of burning Opus. Never throws — missing/garbage log → empty ledger.
function benchUsage() {
  const file = path.join(ROOT, 'star-alliance-arsenal', 'usage-log.jsonl');
  // Direct callers (no SA_MODEL_ID) may log a tag-derived id; normalize the two
  // that don't strip cleanly to their guild id.
  const NORM = { 'kimi-k2.7-code': 'kimi-k2.7', 'nemotron-3-super': 'nemotron-3-ultra' };
  const WEEK_MS = 7 * 24 * 60 * 60 * 1000;
  const SESSION_MS = 5 * 60 * 60 * 1000;
  const now = Date.now();
  const byModel = {};
  let raw;
  try { raw = fs.readFileSync(file, 'utf8'); } catch (e) { return byModel; }
  raw.split(/\r?\n/).forEach((line) => {
    line = line.trim();
    if (!line) return;
    let r; try { r = JSON.parse(line); } catch (e) { return; }
    let id = String(r.model || ''); id = NORM[id] || id;
    if (!id || id === 'unknown') return;
    const tin = Number(r.in) || 0, tout = Number(r.out) || 0;
    const ts = typeof r.ts === 'string' ? Date.parse(r.ts) : NaN;
    const m = byModel[id] || (byModel[id] = {
      calls: 0, in: 0, out: 0,
      wCalls: 0, wIn: 0, wOut: 0,
      sCalls: 0, sIn: 0, sOut: 0,
    });
    m.calls++; m.in += tin; m.out += tout;
    if (!isNaN(ts)) {
      if (now - ts <= WEEK_MS) { m.wCalls++; m.wIn += tin; m.wOut += tout; }
      if (now - ts <= SESSION_MS) { m.sCalls++; m.sIn += tin; m.sOut += tout; }
    }
  });
  return byModel;
}

// Combine bench spend with the live Claude window to produce the headline the
// dashboard shows: how much work the doers absorbed, and a directional
// delegation rate (doer output vs Opus output over the same 5h session window).
function buildLedger(claude, bench) {
  const sum = (sel) => Object.keys(bench).reduce((a, k) => a + (bench[k][sel] || 0), 0);
  const weekDoerOut = sum('wOut'), weekDoerCalls = sum('wCalls'), weekDoerIn = sum('wIn');
  const sessDoerOut = sum('sOut'), sessDoerCalls = sum('sCalls');
  const opusWinOut = ((claude.opus || {}).win_out) || 0;
  const denom = sessDoerOut + opusWinOut;
  return {
    week: {
      doerCalls: weekDoerCalls,
      doerOut: weekDoerOut,
      doerIn: weekDoerIn,
    },
    session: {
      doerCalls: sessDoerCalls,
      doerOut: sessDoerOut,
      opusOut: opusWinOut,
      rate: denom > 0 ? sessDoerOut / denom : 0,  // directional: doer share of recent output
    },
    byModel: bench,
  };
}

// ── Control-panel write-through (MiniMax-authored). Safely set an inline array
//    field (skills / weapons) in a member's .md frontmatter, with a .bak backup
//    and a round-trip verify, then regenerate guild-data so the edit sticks.
function setMemberField(member, field, values, cb) {
  if (!/^[a-z0-9-]+$/.test(member)) return cb(new Error('bad member'));
  if (field !== 'skills') return cb(new Error('field not editable — the arsenal is universal (models.json seats); only skills are per-member'));
  if (!Array.isArray(values) || !values.every((v) => /^[A-Za-z0-9._-]+$/.test(String(v)))) return cb(new Error('bad values'));
  const file = path.join(ROOT, 'star-alliance-members', member + '.md');
  const newBracket = '[' + values.join(', ') + ']';
  const re = new RegExp('^(\\s*' + field + ':\\s*)\\[[^\\]]*\\](.*)$', 'm');
  fs.readFile(file, 'utf8', (err, original) => {
    if (err) return cb(err);
    const m = re.exec(original);
    if (!m) return cb(new Error('field line not found'));
    const updated = original.replace(re, (full, g1, g2) => g1 + newBracket + g2);
    try { fs.writeFileSync(file + '.bak', original); } catch (e) { return cb(e); }
    fs.writeFile(file, updated, (werr) => {
      if (werr) return cb(werr);
      fs.readFile(file, 'utf8', (rerr, content) => {
        if (rerr) { try { fs.writeFileSync(file, original); } catch (_) {} return cb(rerr); }
        if (content.indexOf(m[1] + newBracket) === -1) {
          try { fs.writeFileSync(file, original); } catch (_) {}
          return cb(new Error('verify failed, restored'));
        }
        cb(null, { file: file });
      });
    });
  });
}


function regenGuildData(cb) {
  execFile('python3', [path.join(ROOT, 'build.py')], { cwd: ROOT, timeout: 20000 }, (err) => cb(err));
}

// ── Phase-2 control-panel writers (MiniMax-authored). Each .bak's before write.
const MEMBERS_DIR = path.join(ROOT, 'star-alliance-members');
const META = path.join(ROOT, 'data/members-meta.json');
const SKILLS_META = path.join(ROOT, 'data/skills-meta.json');

function setSkillFlag(skill, disabled, cb) {
  if (!/^[a-z0-9-]+$/.test(skill)) return cb(new Error('invalid skill id'));
  let raw, obj;
  try { raw = fs.readFileSync(SKILLS_META); obj = JSON.parse(raw); } catch (e) { return cb(e); }
  if (!obj[skill]) return cb(new Error('unknown skill'));
  if (disabled) obj[skill].disabled = true; else delete obj[skill].disabled;
  try { fs.writeFileSync(SKILLS_META + '.bak', raw); fs.writeFileSync(SKILLS_META, JSON.stringify(obj, null, 2) + '\n'); } catch (e) { return cb(e); }
  cb(null);
}

function setMemberMeta(member, fields, cb) {
  if (!/^[a-z0-9-]+$/.test(member)) return cb(new Error('invalid member id'));
  const allowed = ['role', 'summary', 'deploy', 'triggers'];
  let raw, meta;
  try { raw = fs.readFileSync(META); meta = JSON.parse(raw); } catch (e) { return cb(e); }
  if (!meta.members || !meta.members[member]) return cb(new Error('unknown member'));
  fields = fields || {};
  for (const k of allowed) {
    if (Object.prototype.hasOwnProperty.call(fields, k)) {
      let v = fields[k]; if (typeof v !== 'string') v = String(v); if (v.length > 800) v = v.slice(0, 800);
      meta.members[member][k] = v;
    }
  }
  try { fs.writeFileSync(META + '.bak', raw); fs.writeFileSync(META, JSON.stringify(meta, null, 2) + '\n'); } catch (e) { return cb(e); }
  cb(null);
}

function setMemberDescription(member, text, cb) {
  if (!/^[a-z0-9-]+$/.test(member)) return cb(new Error('invalid member id'));
  if (typeof text !== 'string') text = String(text); if (text.length > 1000) text = text.slice(0, 1000);
  const file = path.join(MEMBERS_DIR, member + '.md');
  let content; try { content = fs.readFileSync(file, 'utf8'); } catch (e) { return cb(e); }
  if (!/^description:.*$/m.test(content)) return cb(new Error('no description line'));
  const updated = content.replace(/^description:.*$/m, 'description: ' + JSON.stringify(text));
  try { fs.writeFileSync(file + '.bak', content); fs.writeFileSync(file, updated); } catch (e) { return cb(e); }
  cb(null);
}

function setMemberBody(member, text, cb) {
  if (!/^[a-z0-9-]+$/.test(member)) return cb(new Error('invalid member id'));
  const file = path.join(MEMBERS_DIR, member + '.md');
  let content; try { content = fs.readFileSync(file, 'utf8'); } catch (e) { return cb(e); }
  const lines = content.split('\n');
  if (lines[0] !== '---') return cb(new Error('no frontmatter'));
  let secondDelim = -1;
  for (let i = 1; i < lines.length; i++) { if (lines[i] === '---') { secondDelim = i; break; } }
  if (secondDelim === -1) return cb(new Error('no frontmatter'));
  const frontmatter = lines.slice(0, secondDelim + 1).join('\n') + '\n';
  const cleanText = String(text == null ? '' : text).replace(/^\n+|\n+$/g, '');
  const updated = frontmatter + '\n' + cleanText + '\n';
  try { fs.writeFileSync(file + '.bak', content); fs.writeFileSync(file, updated); } catch (e) { return cb(e); }
  cb(null);
}

function deleteMember(member, cb) {
  if (!/^[a-z0-9-]+$/.test(member)) return cb(new Error('invalid member id'));
  const file = path.join(MEMBERS_DIR, member + '.md');
  if (!fs.existsSync(file)) return cb(new Error('no such member'));
  try { fs.writeFileSync(file + '.bak', fs.readFileSync(file)); fs.unlinkSync(file); } catch (e) { return cb(e); }
  let raw, meta;
  try { raw = fs.readFileSync(META); meta = JSON.parse(raw); } catch (e) { return cb(e); }
  if (meta.members && meta.members[member]) {
    delete meta.members[member];
    try { fs.writeFileSync(META + '.bak', raw); fs.writeFileSync(META, JSON.stringify(meta, null, 2) + '\n'); } catch (e) { return cb(e); }
  }
  cb(null);
}

function createMember(member, opts, cb) {
  if (!/^[a-z0-9-]+$/.test(member)) return cb(new Error('invalid member id'));
  opts = opts || {};
  const file = path.join(MEMBERS_DIR, member + '.md');
  if (fs.existsSync(file)) return cb(new Error('member exists'));
  const name = opts.name || member;
  const model = opts.model || 'sonnet';
  const skills = Array.isArray(opts.skills) ? opts.skills : [];
  const weapons = Array.isArray(opts.weapons) ? opts.weapons : [];
  const idRe = /^[A-Za-z0-9._-]+$/;
  for (const s of skills) if (!idRe.test(s)) return cb(new Error('invalid skill id: ' + s));
  for (const w of weapons) if (!idRe.test(w)) return cb(new Error('invalid weapon id: ' + w));
  const frontmatter = ['---', 'name: ' + member, 'description: ' + JSON.stringify(opts.role || name),
    'model: ' + model, 'tools: [Read, Edit, Write, Bash]', 'skills: [' + skills.join(', ') + ']',
    '---'].join('\n');  // no per-member weapons: the arsenal is universal (models.json seats)
  const content = frontmatter + '\n\nYou are ' + name + ', a member of the Star Alliance.\n\n';
  try { fs.writeFileSync(file, content); } catch (e) { return cb(e); }
  const entry = { name: name, role: opts.role || '', color: opts.color || '#888888', summary: '', deploy: '', triggers: '', does: [], doesnt: [] };
  let raw, meta;
  try { raw = fs.readFileSync(META); meta = JSON.parse(raw); } catch (e) { return cb(e); }
  if (!meta.members) meta.members = {};
  meta.members[member] = entry;
  try { fs.writeFileSync(META + '.bak', raw); fs.writeFileSync(META, JSON.stringify(meta, null, 2) + '\n'); } catch (e) { return cb(e); }
  cb(null);
}

// ── Phase-3 control-panel writers: skills, domains, models, workflows, log.
//    Every entity is now editable from the dashboard. Generic JSON-file editor
//    keeps each writer tiny; all .bak before write, all followed by regen.
const SKILLS_DIR = path.join(ROOT, 'star-alliance-skills');
const DOMAINS_JSON = path.join(ROOT, 'data/domains.json');
const MODELS_JSON = path.join(ROOT, 'star-alliance-arsenal/models.json');
const WORKFLOWS_JSON = path.join(ROOT, 'workflows.json');
const LOG_EVENT_PY = path.join(ROOT, 'tools/log_event.py');
const ID_RE = /^[a-z0-9-]+$/;          // skills, domains, workflows
const MODEL_ID_RE = /^[A-Za-z0-9._-]+$/;  // model ids carry dots (glm-5.2)

// Read JSON, .bak the raw text, hand the parsed doc to mutate(doc) → doc|Error,
// write it back pretty-printed. Synchronous: these files are all small. Preserves
// the file's existing indent unit (domains.json is 1-space, the rest 2-space) and
// literal-unicode style (emoji kept literal), so an edit's diff stays scoped to
// the one entity that actually changed.
function editJsonFile(file, mutate, cb) {
  let raw, doc;
  try { raw = fs.readFileSync(file, 'utf8'); doc = JSON.parse(raw); } catch (e) { return cb(e); }
  let next;
  try { next = mutate(doc); } catch (e) { return cb(e); }
  if (next instanceof Error) return cb(next);
  const im = raw.match(/\n([ ]+)\S/);
  const indent = im ? im[1].length : 2;
  const eol = raw.endsWith('\n') ? '\n' : '';   // preserve the file's EOF style
  try {
    fs.writeFileSync(file + '.bak', raw);
    fs.writeFileSync(file, JSON.stringify(next || doc, null, indent) + eol);
  } catch (e) { return cb(e); }
  cb(null);
}

// skills-meta.json: patch the presentation fields for one skill.
function setSkillMeta(skill, fields, cb) {
  if (!ID_RE.test(skill)) return cb(new Error('invalid skill id'));
  const allowed = ['icon', 'blurb', 'level', 'tabler', 'triggers', 'modes'];
  editJsonFile(SKILLS_META, (obj) => {
    if (!obj[skill]) obj[skill] = {};
    fields = fields || {};
    for (const k of allowed) if (Object.prototype.hasOwnProperty.call(fields, k)) {
      let v = fields[k]; if (typeof v !== 'string') v = String(v);
      obj[skill][k] = v.slice(0, 1200);
    }
    return obj;
  }, cb);
}

// SKILL.md body rewrite (frontmatter preserved verbatim) — mirrors setMemberBody.
function setSkillBody(skill, text, cb) {
  if (!ID_RE.test(skill)) return cb(new Error('invalid skill id'));
  const file = path.join(SKILLS_DIR, skill, 'SKILL.md');
  let content; try { content = fs.readFileSync(file, 'utf8'); } catch (e) { return cb(e); }
  const lines = content.split('\n');
  if (lines[0] !== '---') return cb(new Error('no frontmatter'));
  let second = -1;
  for (let i = 1; i < lines.length; i++) if (lines[i] === '---') { second = i; break; }
  if (second === -1) return cb(new Error('no frontmatter'));
  const frontmatter = lines.slice(0, second + 1).join('\n') + '\n';
  const clean = String(text == null ? '' : text).replace(/^\n+|\n+$/g, '');
  try { fs.writeFileSync(file + '.bak', content); fs.writeFileSync(file, frontmatter + '\n' + clean + '\n'); }
  catch (e) { return cb(e); }
  cb(null);
}

function createSkill(skill, opts, cb) {
  if (!ID_RE.test(skill)) return cb(new Error('invalid skill id'));
  opts = opts || {};
  const dir = path.join(SKILLS_DIR, skill);
  if (fs.existsSync(dir)) return cb(new Error('skill exists'));
  const name = String(opts.name || skill);
  const desc = String(opts.description || name).replace(/"/g, '\\"');
  const fm = ['---', 'name: ' + skill, 'description: "' + desc + '"',
    'metadata:', '  version: 0.1.0', 'type: Skill', '---', '',
    '# ' + name, '', String(opts.body || 'Describe this skill.'), ''].join('\n');
  try { fs.mkdirSync(dir, { recursive: true }); fs.writeFileSync(path.join(dir, 'SKILL.md'), fm); }
  catch (e) { return cb(e); }
  editJsonFile(SKILLS_META, (obj) => {
    obj[skill] = { icon: opts.icon || '📦', blurb: String(opts.blurb || '').slice(0, 200),
      level: opts.level || 'Foundational', tabler: opts.tabler || '', triggers: opts.triggers || '', modes: '' };
    return obj;
  }, cb);
}

function deleteSkill(skill, cb) {
  if (!ID_RE.test(skill)) return cb(new Error('invalid skill id'));
  const dir = path.join(SKILLS_DIR, skill);
  if (!fs.existsSync(dir)) return cb(new Error('no such skill'));
  const md = path.join(dir, 'SKILL.md');
  try { if (fs.existsSync(md)) fs.writeFileSync(md + '.deleted.bak', fs.readFileSync(md)); } catch (_) {}
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch (e) { return cb(e); }
  editJsonFile(SKILLS_META, (obj) => { delete obj[skill]; return obj; }, cb);
}

// domains.json — upsert/delete one domain by id (array of {id,...}).
function upsertDomain(domain, cb) {
  if (!domain || !ID_RE.test(String(domain.id || ''))) return cb(new Error('invalid domain id'));
  editJsonFile(DOMAINS_JSON, (doc) => {
    if (!Array.isArray(doc.domains)) doc.domains = [];
    const i = doc.domains.findIndex((d) => d.id === domain.id);
    if (i === -1) doc.domains.push(domain); else doc.domains[i] = Object.assign({}, doc.domains[i], domain);
    return doc;
  }, cb);
}
function deleteDomain(id, cb) {
  if (!ID_RE.test(String(id || ''))) return cb(new Error('invalid domain id'));
  editJsonFile(DOMAINS_JSON, (doc) => {
    doc.domains = (doc.domains || []).filter((d) => d.id !== id); return doc;
  }, cb);
}

// models.json — upsert/delete one model by id (object map keyed by id).
function upsertModel(id, fields, cb) {
  if (!MODEL_ID_RE.test(String(id || ''))) return cb(new Error('invalid model id'));
  editJsonFile(MODELS_JSON, (doc) => {
    if (!doc.models) doc.models = {};
    doc.models[id] = Object.assign({}, doc.models[id] || {}, fields || {});
    return doc;
  }, cb);
}
function deleteModel(id, cb) {
  if (!MODEL_ID_RE.test(String(id || ''))) return cb(new Error('invalid model id'));
  editJsonFile(MODELS_JSON, (doc) => { if (doc.models) delete doc.models[id]; return doc; }, cb);
}

// workflows.json — upsert/delete one workflow by id (array of {id,...}).
function upsertWorkflow(wf, cb) {
  if (!wf || !ID_RE.test(String(wf.id || ''))) return cb(new Error('invalid workflow id'));
  editJsonFile(WORKFLOWS_JSON, (doc) => {
    if (!Array.isArray(doc.workflows)) doc.workflows = [];
    const i = doc.workflows.findIndex((w) => w.id === wf.id);
    if (i === -1) doc.workflows.push(wf); else doc.workflows[i] = Object.assign({}, doc.workflows[i], wf);
    return doc;
  }, cb);
}
function deleteWorkflow(id, cb) {
  if (!ID_RE.test(String(id || ''))) return cb(new Error('invalid workflow id'));
  editJsonFile(WORKFLOWS_JSON, (doc) => {
    doc.workflows = (doc.workflows || []).filter((w) => w.id !== id); return doc;
  }, cb);
}

// ── Evolution Engine control (Wave 5). The schedule lives in a repo file so the
//    dashboard edits it without touching the cron — reflect.py self-gates on it.
const EVOLUTION_DIR = path.join(ROOT, 'evolution');
const SCHEDULE_JSON = path.join(EVOLUTION_DIR, 'schedule.json');
const CADENCES = new Set(['off', 'hourly', 'daily', 'weekly']);

function setEvolutionSchedule(fields, cb) {
  fields = fields || {};
  editJsonFile(SCHEDULE_JSON, (doc) => {
    if (typeof fields.cadence === 'string') {
      if (!CADENCES.has(fields.cadence)) return new Error('bad cadence');
      doc.cadence = fields.cadence;
    }
    if (typeof fields.enabled === 'boolean') doc.enabled = fields.enabled;
    return doc;
  }, cb);
}

// guild log — append-only, via the canonical tools/log_event.py (auto-stamps
// date/id, never overwrites). Provenance stays intact; no direct JSON write.
const LOG_TYPES = new Set(['skill-upgrade','skill-create','skill-remove','member-upgrade',
  'member-create','member-remove','workflow','dashboard','structure','chore','decision']);
function appendLog(entry, cb) {
  entry = entry || {};
  if (!LOG_TYPES.has(entry.type)) return cb(new Error('invalid log type'));
  if (!entry.title || typeof entry.title !== 'string') return cb(new Error('title required'));
  const args = [LOG_EVENT_PY, '--type', entry.type, '--title', entry.title.slice(0, 200)];
  if (entry.detail) args.push('--detail', String(entry.detail).slice(0, 1000));
  if (entry.who) args.push('--who', String(entry.who).slice(0, 60));
  execFile('python3', args, { cwd: ROOT, timeout: 15000 }, (err) => cb(err || null));
}

// Dispatch a parsed save body to the right writer; returns true if handled.
function dispatchSave(body, done) {
  switch (body.kind) {
    case 'member-field':
      return setMemberField(body.member, body.field, body.values, (e) => done(e || null));
    case 'skill-flag':       return setSkillFlag(body.skill, body.disabled, done);
    case 'member-meta':      return setMemberMeta(body.member, body.fields, done);
    case 'member-description':return setMemberDescription(body.member, body.text, done);
    case 'member-body':      return setMemberBody(body.member, body.text, done);
    case 'member-create':    return createMember(body.member, body.opts, done);
    case 'member-delete':    return deleteMember(body.member, done);
    // Phase-3: skills / domains / models / workflows / log
    case 'skill-meta':       return setSkillMeta(body.skill, body.fields, done);
    case 'skill-body':       return setSkillBody(body.skill, body.text, done);
    case 'skill-create':     return createSkill(body.skill, body.opts, done);
    case 'skill-delete':     return deleteSkill(body.skill, done);
    case 'domain-upsert':    return upsertDomain(body.domain, done);
    case 'domain-delete':    return deleteDomain(body.id, done);
    case 'model-upsert':     return upsertModel(body.id, body.fields, done);
    case 'model-delete':     return deleteModel(body.id, done);
    case 'workflow-upsert':  return upsertWorkflow(body.workflow, done);
    case 'workflow-delete':  return deleteWorkflow(body.id, done);
    case 'log-append':       return appendLog(body.entry, done);
    default:                 return done(new Error('unknown kind'));
  }
}

http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/api/save') {
    let raw = '';
    req.on('data', (c) => { raw += c; if (raw.length > 1e6) req.destroy(); });
    req.on('end', () => {
      let body;
      try { body = JSON.parse(raw); } catch (e) { res.writeHead(400, {'Content-Type':'application/json'}); return res.end('{"ok":false,"error":"bad json"}'); }
      dispatchSave(body, (werr) => {
        if (werr) { res.writeHead(400, {'Content-Type':'application/json','Access-Control-Allow-Origin':'*'}); return res.end(JSON.stringify({ ok:false, error:String(werr.message||werr) })); }
        regenGuildData((rgerr) => {
          res.writeHead(rgerr ? 500 : 200, {'Content-Type':'application/json','Access-Control-Allow-Origin':'*'});
          res.end(JSON.stringify({ ok: !rgerr, error: rgerr ? String(rgerr.message||rgerr) : undefined, regen: rgerr ? 'failed' : 'ok' }));
        });
      });
    });
    return;
  }
  if (req.method === 'GET' && (req.url === '/api/arsenal' || req.url.startsWith('/api/arsenal?'))) {
    fetchOllama((o) => {
      claudeUsage((claude) => {
        // Project-scoped second pass: the ledger rate must weigh THIS project's
        // doer output against THIS project's Opus output, not all-projects Opus.
        claudeUsage((claudeScoped) => {
        const body = JSON.stringify({
          pulled: o.pulled,
          ollamaUp: o.ollamaUp,
          usage: mergeUsage(claude),
          estimate: estimateUsage(claude, loadUsage()),
          ledger: buildLedger(claudeScoped, benchUsage()),
          claudeRaw: claude,
          ts: Date.now(),
        });
        res.writeHead(200, {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'no-store',
        });
        res.end(body);
        }, PROJECT_TRANSCRIPT_DIR);
      });
    });
    return;
  }

  // Control-panel status: proves the server is live (so the UI knows it can
  // write to disk vs the file:// localStorage fallback), with last-build time
  // and the version baked into the current guild-data.js.
  if (req.method === 'GET' && req.url === '/api/status') {
    let lastBuild = null, version = null;
    try { lastBuild = fs.statSync(path.join(ROOT, 'guild-data.js')).mtime.toISOString(); } catch (_) {}
    try {
      const reg = JSON.parse(fs.readFileSync(path.join(ROOT, 'guild-data.json'), 'utf8'));
      version = reg && reg.meta && reg.meta.version || null;
    } catch (_) {}
    res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Cache-Control': 'no-store' });
    return res.end(JSON.stringify({ live: true, lastBuild, version, ts: Date.now() }));
  }
  // On-demand rebuild — run build.py without any source edit.
  if (req.method === 'POST' && req.url === '/api/rebuild') {
    regenGuildData((err) => {
      let lastBuild = null;
      try { lastBuild = fs.statSync(path.join(ROOT, 'guild-data.js')).mtime.toISOString(); } catch (_) {}
      res.writeHead(err ? 500 : 200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
      res.end(JSON.stringify({ ok: !err, error: err ? String(err.message || err) : undefined, lastBuild }));
    });
    return;
  }

  // ── Evolution Engine: live status (read), schedule control (write), run-now.
  if (req.method === 'GET' && req.url === '/api/evolution') {
    execFile('python3', [path.join(EVOLUTION_DIR, 'status.py')], { cwd: ROOT, timeout: 15000 }, (err, stdout) => {
      res.writeHead(200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'Cache-Control': 'no-store' });
      res.end(err ? JSON.stringify({ error: String(err.message || err) }) : (stdout || '{}'));
    });
    return;
  }
  if (req.method === 'POST' && req.url === '/api/evolution/schedule') {
    let raw = ''; req.on('data', (c) => { raw += c; if (raw.length > 1e5) req.destroy(); });
    req.on('end', () => {
      let body; try { body = JSON.parse(raw); } catch (e) { res.writeHead(400, {'Content-Type':'application/json'}); return res.end('{"ok":false,"error":"bad json"}'); }
      setEvolutionSchedule(body, (err) => {
        res.writeHead(err ? 400 : 200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
        res.end(JSON.stringify({ ok: !err, error: err ? String(err.message || err) : undefined }));
      });
    });
    return;
  }
  if (req.method === 'POST' && req.url === '/api/evolution/run') {
    execFile('python3', [path.join(EVOLUTION_DIR, 'reflect.py'), '--now'], { cwd: ROOT, timeout: 120000 }, (err, stdout, stderr) => {
      res.writeHead(err ? 500 : 200, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
      res.end(JSON.stringify({ ok: !err, output: (stdout || '') + (stderr || ''), error: err ? String(err.message || err) : undefined }));
    });
    return;
  }

  let urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
  if (urlPath === '/' || urlPath === '') urlPath = '/index.html';
  const filePath = path.join(ROOT, urlPath);
  const rel = path.relative(ROOT, filePath);
  if (rel.startsWith('..') || path.isAbsolute(rel)) {
    res.writeHead(403); res.end('Forbidden'); return;
  }
  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) { res.writeHead(404); res.end('Not found'); return; }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, { 'Content-Type': TYPES[ext] || 'application/octet-stream' });
    fs.createReadStream(filePath).pipe(res);
  });
}).listen(PORT, () => console.log(`dashboard on http://localhost:${PORT}`));
