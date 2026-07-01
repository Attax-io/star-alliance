// Star Alliance Dashboard — static server
// Usage: node serve.cjs  →  http://localhost:4178/dashboard.html
const http = require('http')
const fs = require('fs')
const path = require('path')

const PORT = 4178
const ROOT = __dirname

const MIME = {
  '.html': 'text/html', '.css': 'text/css', '.js': 'application/javascript',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.ico': 'image/x-icon'
}

const MODELS_FILE = path.join(ROOT, 'star-alliance-arsenal', 'models.json')

function readModels() {
  const raw = fs.readFileSync(MODELS_FILE, 'utf8')
  const obj = JSON.parse(raw)
  if (!obj.memberOverrides || typeof obj.memberOverrides !== 'object' || Array.isArray(obj.memberOverrides)) {
    obj.memberOverrides = {}
  }
  return obj
}

// Derive brains/doers from the registry — single source of truth.
//   brains = every model id whose backend === 'claude'
//   doers  = every model id whose role   === 'doer'
// role: 'media' models are intentionally excluded (neither brain nor doer).
// Also surface the seat defaults so the dashboard can show "effective doer" on
// a card even when the member has no explicit override.
// Re-reads models.json on each call so the lists stay in lockstep with the registry.
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

http.createServer(async (req, res) => {
  const url = req.url.split('?')[0]

  if (url === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ ok: true }))
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

  const filePath = path.join(ROOT, req.url === '/' ? '/dashboard.html' : req.url)
  fs.readFile(filePath, (err, data) => {
    if (err) { res.writeHead(404); res.end('Not found'); return }
    const ext = path.extname(filePath)
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'text/plain', 'Cache-Control': 'no-store' })
    res.end(data)
  })
}).listen(PORT, () => console.log(`★ Star Alliance → http://localhost:${PORT}/dashboard.html`))