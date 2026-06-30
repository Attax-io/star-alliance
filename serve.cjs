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

http.createServer((req, res) => {
  if (req.url === '/api/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({ ok: true }))
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