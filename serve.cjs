// Star Alliance Dashboard — static server
// Usage: node serve.cjs  →  http://localhost:4178/dashboard.html
const http = require('http')
const fs = require('fs')
const path = require('path')
const os = require('os')
const crypto = require('crypto')
const { execFile } = require('child_process')

const PORT = 4178
const ROOT = __dirname

const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon'
}

const MODELS_FILE = path.join(ROOT, 'star-alliance-arsenal', 'models.json')

// ---------------------------------------------------------------------------
// Security: per-process CSRF/session token, minted once at startup.
// The dashboard reads it from GET /api/status and must echo it back in the
// X-SA-Token header on every POST control endpoint.
// ---------------------------------------------------------------------------
const SA_TOKEN = crypto.randomBytes(32).toString('hex')

function isLocalOrigin(req) {
  // Require the Origin (or failing that, Host) to be localhost/127.0.0.1.
  const origin = req.headers['origin']
  const host = req.headers['host'] || ''
  if (origin) {
    try {
      const u = new URL(origin)
      return u.hostname === 'localhost' || u.hostname === '127.0.0.1'
    } catch {
      return false
    }
  }
  // No Origin header (e.g. curl, same-origin fetches in some browsers) — fall
  // back to Host, which for a loopback-only server will always be localhost.
  return /^(localhost|127\.0\.0\.1)(:\d+)?$/.test(host)
}

function checkToken(req) {
  const provided = req.headers['x-sa-token']
  return typeof provided === 'string' && provided === SA_TOKEN
}

function requireGuards(req, res) {
  // Returns true if the request passed both guards; otherwise writes a 403
  // and returns false. Call this first thing in every POST control handler.
  if (!isLocalOrigin(req)) {
    res.writeHead(403, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ ok: false, error: 'forbidden: non-local origin' }))
    return false
  }
  if (!checkToken(req)) {
    res.writeHead(403, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ ok: false, error: 'forbidden: missing or invalid X-SA-Token' }))
    return false
  }
  return true
}

// ---------------------------------------------------------------------------
// Security: server-side id allowlist. An id is controllable ONLY if it is:
//   - a launchd label starting with "com.attax." (as "launchd:com.attax.X"), OR
//   - a known ~/.claude/scheduled-tasks dir name (as "native:<dirName>"), OR
//   - a hermes cron job id present in `hermes cron list --all` (as "hermes:<id>")
// Foreign plists (whatsapp/ollama/google/steam/openclaw) can NEVER be mutated,
// and native jobs are never controllable in Wave 1 (schedule_scan.js reports
// them with controllable:false — enforced again here as defense in depth).
// ---------------------------------------------------------------------------

function execFileP(cmd, args, opts) {
  return new Promise((resolve, reject) => {
    execFile(cmd, args, { maxBuffer: 10 * 1024 * 1024, ...opts }, (err, stdout, stderr) => {
      if (err) { err.stdout = stdout; err.stderr = stderr; reject(err); return }
      resolve({ stdout, stderr })
    })
  })
}

async function getKnownNativeDirs() {
  try {
    const baseDir = path.join(os.homedir(), '.claude', 'scheduled-tasks')
    return fs.readdirSync(baseDir, { withFileTypes: true })
      .filter(d => d.isDirectory())
      .map(d => d.name)
  } catch {
    return []
  }
}

async function getKnownHermesIds() {
  try {
    const { stdout } = await execFileP('hermes', ['cron', 'list', '--all'])
    let parsed
    try { parsed = JSON.parse(stdout) } catch { return [] }
    const list = Array.isArray(parsed) ? parsed : (parsed.jobs || [])
    return list.map(item => item.id || item.name).filter(Boolean)
  } catch {
    return []
  }
}

// Validates an id against the allowlist and returns a descriptor:
//   { ok: true, kind: 'launchd', label } | { ok: true, kind: 'hermes', hermesId } | { ok: false }
async function resolveControllableId(id) {
  if (typeof id !== 'string' || !id) return { ok: false }

  if (id.startsWith('launchd:')) {
    const label = id.slice('launchd:'.length)
    if (label.startsWith('com.attax.')) {
      return { ok: true, kind: 'launchd', label }
    }
    return { ok: false }
  }

  if (id.startsWith('native:')) {
    const dirName = id.slice('native:'.length)
    const known = await getKnownNativeDirs()
    if (known.includes(dirName)) {
      // Native tasks are read-only in Wave 1/2 (no launchd/hermes backing to
      // mutate) — allowlisted for identification, but callers must still
      // reject actual mutation attempts on this kind.
      return { ok: true, kind: 'native', dirName }
    }
    return { ok: false }
  }

  if (id.startsWith('hermes:')) {
    const hermesId = id.slice('hermes:'.length)
    const known = await getKnownHermesIds()
    if (known.includes(hermesId)) {
      return { ok: true, kind: 'hermes', hermesId }
    }
    return { ok: false }
  }

  return { ok: false }
}

function findPlistPathForLabel(label) {
  // Mirrors schedule_scan.js's launchd scanner: plists live in ~/Library/LaunchAgents.
  const dir = path.join(os.homedir(), 'Library', 'LaunchAgents')
  const candidate = path.join(dir, `${label}.plist`)
  if (fs.existsSync(candidate)) return candidate
  return null
}

async function refreshSingleJob(id) {
  // Re-scan and return just the one job matching `id`, for the response payload.
  try {
    const { scanAll } = require(path.join(ROOT, 'tools', 'schedule_scan.js'))
    const result = await scanAll()
    return (result.jobs || []).find(j => j.id === id) || null
  } catch {
    return null
  }
}

// Derive brains/doers from the registry — single source of truth.
function readModels() {
  const raw = fs.readFileSync(MODELS_FILE, 'utf8')
  const obj = JSON.parse(raw)
  if (!obj.memberOverrides || typeof obj.memberOverrides !== 'object' || Array.isArray(obj.memberOverrides)) {
    obj.memberOverrides = {}
  }
  return obj
}

function deriveModelLists() {
  const obj = readModels()
  const models = obj.models || {}
  const brains = []
  const doers = []
  for (const [id, m] of Object.entries(models)) {
    if (!m || typeof m !== 'object') continue
    if (m.backend === 'claude') brains.push(id)
    if (m.role === 'doer') doers.push(id)
  }
  const seats = obj.seats || {}
  const defaults = {
    brain: seats.brain && seats.brain.default ? seats.brain.default : null,
    doer:  seats.doer  && seats.doer.default  ? seats.doer.default  : null
  }
  return { brains, doers, defaults }
}

function writeModels(obj) {
  fs.writeFileSync(MODELS_FILE, JSON.stringify(obj, null, 2) + '\n', 'utf8')
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = ''
    req.on('data', chunk => { data += chunk; if (data.length > 1e6) { reject(new Error('body too large')); req.destroy() } })
    req.on('end', () => resolve(data))
    req.on('error', reject)
  })
}

function parseJsonBody(raw) {
  try { return { body: JSON.parse(raw) } } catch { return { error: 'invalid JSON' } }
}

http.createServer(async (req, res) => {
  const url = req.url.split('?')[0]

  if (url === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ ok: true, token: SA_TOKEN }))
    return
  }

  if (url === '/api/model-lists') {
    try {
      const lists = deriveModelLists()
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify(lists))
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: String(err) }))
    }
    return
  }

  if (url === '/api/model-override' && req.method === 'GET') {
    try {
      const obj = readModels()
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify(obj.memberOverrides))
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: String(err) }))
    }
    return
  }

  if (url === '/api/model-override' && req.method === 'POST') {
    try {
      const raw = await readBody(req)
      let body
      try { body = JSON.parse(raw) } catch { res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'invalid JSON' })); return }
      const { memberId, brain, doer } = body || {}
      if (!memberId || typeof memberId !== 'string') {
        res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'memberId required' })); return
      }
      const { brains: validBrains, doers: validDoers } = deriveModelLists()
      if (!validBrains.includes(brain)) {
        res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'brain must be one of: ' + validBrains.join(', ') })); return
      }
      if (!validDoers.includes(doer)) {
        res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'doer must be one of: ' + validDoers.join(', ') })); return
      }
      const obj = readModels()
      obj.memberOverrides[memberId] = { brain, doer }
      writeModels(obj)
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: true }))
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: String(err) }))
    }
    return
  }

  if (url === '/api/schedules') {
    try {
      const { scanAll } = require(path.join(ROOT, 'tools', 'schedule_scan.js'))
      const result = await scanAll()
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify(result))
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: String(err) }))
    }
    return
  }

  // -------------------------------------------------------------------
  // POST /api/schedule/toggle  { id, enabled }
  // -------------------------------------------------------------------
  if (url === '/api/schedule/toggle' && req.method === 'POST') {
    if (!requireGuards(req, res)) return
    try {
      const raw = await readBody(req)
      const { body, error } = parseJsonBody(raw)
      if (error) { res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error })); return }
      const { id, enabled } = body || {}
      if (typeof enabled !== 'boolean') {
        res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'enabled must be boolean' })); return
      }
      const resolved = await resolveControllableId(id)
      if (!resolved.ok) {
        res.writeHead(403, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'id not controllable' })); return
      }

      if (resolved.kind === 'launchd') {
        const plistPath = findPlistPathForLabel(resolved.label)
        if (!plistPath) {
          res.writeHead(404, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'plist not found for ' + resolved.label })); return
        }
        const uid = String(process.getuid())
        let lastErr = null
        try {
          if (enabled) {
            await execFileP('launchctl', ['bootstrap', `gui/${uid}`, plistPath])
          } else {
            await execFileP('launchctl', ['bootout', `gui/${uid}/${resolved.label}`])
          }
        } catch (err) {
          lastErr = err
          // Fallback to load/unload -w
          try {
            if (enabled) {
              await execFileP('launchctl', ['load', '-w', plistPath])
            } else {
              await execFileP('launchctl', ['unload', '-w', plistPath])
            }
            lastErr = null
          } catch (err2) {
            lastErr = err2
          }
        }
        if (lastErr) {
          res.writeHead(500, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ ok: false, error: (lastErr.stderr || lastErr.message || String(lastErr)) }))
          return
        }
        const job = await refreshSingleJob(id)
        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ ok: true, job }))
        return
      }

      if (resolved.kind === 'hermes') {
        try {
          await execFileP('hermes', ['cron', enabled ? 'resume' : 'pause', resolved.hermesId])
        } catch (err) {
          res.writeHead(500, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ ok: false, error: (err.stderr || err.message || String(err)) }))
          return
        }
        const job = await refreshSingleJob(id)
        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ ok: true, job }))
        return
      }

      // native jobs: not controllable for toggle
      res.writeHead(403, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: 'this job kind cannot be toggled' }))
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: String(err) }))
    }
    return
  }

  // -------------------------------------------------------------------
  // POST /api/schedule/retime  { id, calendar: { Hour, Minute } }
  // -------------------------------------------------------------------
  if (url === '/api/schedule/retime' && req.method === 'POST') {
    if (!requireGuards(req, res)) return
    try {
      const raw = await readBody(req)
      const { body, error } = parseJsonBody(raw)
      if (error) { res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error })); return }
      const { id, calendar } = body || {}
      const hour = calendar && calendar.Hour
      const minute = calendar && calendar.Minute
      if (!Number.isInteger(hour) || hour < 0 || hour > 23) {
        res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'Hour must be an integer 0-23' })); return
      }
      if (!Number.isInteger(minute) || minute < 0 || minute > 59) {
        res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'Minute must be an integer 0-59' })); return
      }
      const resolved = await resolveControllableId(id)
      if (!resolved.ok) {
        res.writeHead(403, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'id not controllable' })); return
      }

      if (resolved.kind === 'launchd') {
        const plistPath = findPlistPathForLabel(resolved.label)
        if (!plistPath) {
          res.writeHead(404, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'plist not found for ' + resolved.label })); return
        }
        const backupPath = plistPath + '.bak'
        try {
          // 1. Back up the original.
          fs.copyFileSync(plistPath, backupPath)

          // 2. Read plist as JSON via plutil.
          const { stdout: jsonStdout } = await execFileP('plutil', ['-convert', 'json', '-o', '-', plistPath])
          const plist = JSON.parse(jsonStdout)

          // 3. Set StartCalendarInterval.
          plist.StartCalendarInterval = { Hour: hour, Minute: minute }

          // 4. Write back as xml1.
          const tmpJsonPath = plistPath + '.new.json'
          fs.writeFileSync(tmpJsonPath, JSON.stringify(plist))
          await execFileP('plutil', ['-convert', 'xml1', tmpJsonPath, '-o', plistPath])
          fs.unlinkSync(tmpJsonPath)

          // 5. Lint the result.
          await execFileP('plutil', ['-lint', plistPath])

          // 6. Unload + load to apply.
          const uid = String(process.getuid())
          try {
            await execFileP('launchctl', ['bootout', `gui/${uid}/${resolved.label}`])
          } catch { /* may already be unloaded */ }
          try {
            await execFileP('launchctl', ['bootstrap', `gui/${uid}`, plistPath])
          } catch (bootErr) {
            await execFileP('launchctl', ['load', '-w', plistPath])
          }
        } catch (err) {
          // Restore from backup on any failure.
          try { fs.copyFileSync(backupPath, plistPath) } catch { /* best effort */ }
          res.writeHead(500, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ ok: false, error: (err.stderr || err.message || String(err)) }))
          return
        }
        const job = await refreshSingleJob(id)
        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ ok: true, job }))
        return
      }

      if (resolved.kind === 'hermes') {
        const cronExpr = `${minute} ${hour} * * *`
        try {
          await execFileP('hermes', ['cron', 'edit', resolved.hermesId, '--schedule', cronExpr])
        } catch (err) {
          res.writeHead(500, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ ok: false, error: (err.stderr || err.message || String(err)) }))
          return
        }
        const job = await refreshSingleJob(id)
        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ ok: true, job }))
        return
      }

      res.writeHead(403, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: 'this job kind cannot be retimed' }))
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: String(err) }))
    }
    return
  }

  // -------------------------------------------------------------------
  // POST /api/schedule/run  { id }
  // -------------------------------------------------------------------
  if (url === '/api/schedule/run' && req.method === 'POST') {
    if (!requireGuards(req, res)) return
    try {
      const raw = await readBody(req)
      const { body, error } = parseJsonBody(raw)
      if (error) { res.writeHead(400, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error })); return }
      const { id } = body || {}
      const resolved = await resolveControllableId(id)
      if (!resolved.ok) {
        res.writeHead(403, { 'Content-Type': 'application/json' }); res.end(JSON.stringify({ ok: false, error: 'id not controllable' })); return
      }

      if (resolved.kind === 'launchd') {
        const uid = String(process.getuid())
        try {
          await execFileP('launchctl', ['kickstart', '-k', `gui/${uid}/${resolved.label}`])
        } catch (err) {
          res.writeHead(500, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ ok: false, error: (err.stderr || err.message || String(err)) }))
          return
        }
        const job = await refreshSingleJob(id)
        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ ok: true, job }))
        return
      }

      if (resolved.kind === 'hermes') {
        try {
          await execFileP('hermes', ['cron', 'run', resolved.hermesId])
        } catch (err) {
          res.writeHead(500, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ ok: false, error: (err.stderr || err.message || String(err)) }))
          return
        }
        const job = await refreshSingleJob(id)
        res.writeHead(200, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ ok: true, job }))
        return
      }

      res.writeHead(403, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: 'this job kind cannot be run' }))
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ ok: false, error: String(err) }))
    }
    return
  }

  const filePath = path.join(ROOT, req.url === '/' ? '/dashboard.html' : req.url)
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return }
    const ext = path.extname(filePath)
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'text/plain', 'Cache-Control': 'no-store' })
    res.end(data)
  })
}).listen(PORT, '127.0.0.1', () => console.log(`★ Star Alliance → http://localhost:${PORT}/dashboard.html (loopback-only)`))
