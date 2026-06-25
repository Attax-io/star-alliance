/**
 * Shared config + env loader for the codex-law-translate pipeline.
 * Every script does `const cfg = require('./_config')`.
 *
 * Requires env var CODEX_CONFIG = absolute path to a config.json (see config.example.json).
 * Reads the Supabase service-role creds from <projectRoot>/apps/web/.env.local.
 */
const fs = require('fs')
const path = require('path')

const cfgPath = process.env.CODEX_CONFIG
if (!cfgPath) {
  console.error('Set CODEX_CONFIG=/abs/path/config.json before running.')
  process.exit(1)
}
const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'))

for (const req of ['code', 'sourcePath', 'projectRoot']) {
  if (!cfg[req]) { console.error(`config.json missing required field: ${req}`); process.exit(1) }
}

const envFile = path.join(cfg.projectRoot, 'apps/web/.env.local')
const env = Object.fromEntries(
  fs.readFileSync(envFile, 'utf8').split('\n')
    .filter((l) => l && !l.startsWith('#') && l.includes('='))
    .map((l) => { const [k, ...v] = l.split('='); return [k.trim(), v.join('=').trim()] })
)
cfg.SUPABASE_URL = env.NEXT_PUBLIC_SUPABASE_URL
cfg.SERVICE_KEY = env.SUPABASE_SERVICE_ROLE_KEY
if (!cfg.SUPABASE_URL || !cfg.SERVICE_KEY) {
  console.error(`Missing Supabase creds in ${envFile}`); process.exit(1)
}

cfg.locales = cfg.locales || ['en', 'fr', 'es', 'ru', 'zh']
cfg.tags = cfg.tags || []
if (!cfg.tmp) cfg.tmp = '/tmp/codex_' + cfg.code.replace(/\W+/g, '_')
cfg.batchesDir = path.join(cfg.tmp, 'batches')
fs.mkdirSync(cfg.batchesDir, { recursive: true })

cfg.restHeaders = (extra = {}) => ({
  apikey: cfg.SERVICE_KEY,
  Authorization: `Bearer ${cfg.SERVICE_KEY}`,
  'Content-Type': 'application/json',
  ...extra,
})

module.exports = cfg
