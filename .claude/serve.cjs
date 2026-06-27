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

// Estimated 0..1 consumption per model — drafted by MiniMax M3. Pure: recomputes
// on every call from the live Claude window-activity signal (orchestrator burn ⇒
// the doers are working), weighted per model. Claude families get a REAL fill.
function estimateUsage(claude, caps) {
  const WEIGHT = { 'minimax-m3': 1.0, 'glm-5.2': 0.7, 'kimi-k2.7': 0.5, 'deepseek-v4-pro': 0.5, 'nemotron-3-ultra': 0.4, 'qwen3.5': 0.4, 'gemma4': 0.3, 'gpt-5.5': 0.2 };
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
  if (field !== 'skills' && field !== 'weapons') return cb(new Error('bad field'));
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

// build.py requires members-meta.json weaponsDesc keys to match the .md weapons
// EXACTLY (both directions). So a weapons edit must re-sync weaponsDesc or the
// rebuild aborts. descMap (from the dashboard's MODELS) supplies text for new models.
function syncWeaponsMeta(member, values, descMap, cb) {
  if (!/^[a-z0-9-]+$/.test(member)) return cb(new Error('bad member'));
  const file = path.join(ROOT, 'members-meta.json');
  fs.readFile(file, 'utf8', (err, raw) => {
    if (err) return cb(err);
    let doc; try { doc = JSON.parse(raw); } catch (e) { return cb(e); }
    const mem = doc.members && doc.members[member];
    if (!mem) return cb(new Error('member not in members-meta.json'));
    const prev = mem.weaponsDesc || {};
    const next = {};
    values.forEach((mdl) => {
      let d = (descMap && typeof descMap[mdl] === 'string') ? descMap[mdl] : (prev[mdl] || '');
      next[mdl] = String(d).slice(0, 500);
    });
    mem.weaponsDesc = next;
    try { fs.writeFileSync(file + '.bak', raw); fs.writeFileSync(file, JSON.stringify(doc, null, 2) + '\n'); }
    catch (e) { return cb(e); }
    cb(null);
  });
}

function regenGuildData(cb) {
  execFile('python3', [path.join(ROOT, 'build.py')], { cwd: ROOT, timeout: 20000 }, (err) => cb(err));
}

// ── Phase-2 control-panel writers (MiniMax-authored). Each .bak's before write.
const MEMBERS_DIR = path.join(ROOT, 'star-alliance-members');
const META = path.join(ROOT, 'members-meta.json');
const SKILLS_META = path.join(ROOT, 'skills-meta.json');

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
    'weapons: [' + weapons.join(', ') + ']', '---'].join('\n');
  const content = frontmatter + '\n\nYou are ' + name + ', a member of the Star Alliance.\n\n';
  try { fs.writeFileSync(file, content); } catch (e) { return cb(e); }
  const descMap = opts.descMap || {};
  const weaponsDesc = {}; for (const w of weapons) weaponsDesc[w] = String(descMap[w] || '').slice(0, 500);
  const entry = { name: name, role: opts.role || '', color: opts.color || '#888888', summary: '', deploy: '', triggers: '', weaponsDesc: weaponsDesc, does: [], doesnt: [] };
  let raw, meta;
  try { raw = fs.readFileSync(META); meta = JSON.parse(raw); } catch (e) { return cb(e); }
  if (!meta.members) meta.members = {};
  meta.members[member] = entry;
  try { fs.writeFileSync(META + '.bak', raw); fs.writeFileSync(META, JSON.stringify(meta, null, 2) + '\n'); } catch (e) { return cb(e); }
  cb(null);
}

// Dispatch a parsed save body to the right writer; returns true if handled.
function dispatchSave(body, done) {
  switch (body.kind) {
    case 'member-field':
      return setMemberField(body.member, body.field, body.values, (e, info) => {
        if (e) return done(e);
        if (body.field === 'weapons') return syncWeaponsMeta(body.member, body.values, body.desc, done);
        done(null);
      });
    case 'skill-flag':       return setSkillFlag(body.skill, body.disabled, done);
    case 'member-meta':      return setMemberMeta(body.member, body.fields, done);
    case 'member-description':return setMemberDescription(body.member, body.text, done);
    case 'member-body':      return setMemberBody(body.member, body.text, done);
    case 'member-create':    return createMember(body.member, body.opts, done);
    case 'member-delete':    return deleteMember(body.member, done);
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
