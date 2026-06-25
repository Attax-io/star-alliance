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
const PORT = 4178;
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
function claudeUsage(cb) {
  const WINDOW_MS = 5 * 60 * 60 * 1000;
  const SIX_HOURS_MS = 6 * 60 * 60 * 1000;
  const root = path.join(os.homedir(), '.claude', 'projects');
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
    const parsed = JSON.parse(fs.readFileSync(path.join(ROOT, 'models-usage.json'), 'utf8'));
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

http.createServer((req, res) => {
  if (req.method === 'GET' && (req.url === '/api/arsenal' || req.url.startsWith('/api/arsenal?'))) {
    fetchOllama((o) => {
      claudeUsage((claude) => {
        const body = JSON.stringify({
          pulled: o.pulled,
          ollamaUp: o.ollamaUp,
          usage: mergeUsage(claude),
          estimate: estimateUsage(claude, loadUsage()),
          claudeRaw: claude,
          ts: Date.now(),
        });
        res.writeHead(200, {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'no-store',
        });
        res.end(body);
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
