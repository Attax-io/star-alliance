// tools/schedule_scan.js
// Read-only job scanner for the Mission Control Scheduler panel (Wave 1).
// CommonJS module. Exports scanAll() -> { jobs: [...] }.
//
// Composes four scanners: launchd, native (~/.claude/scheduled-tasks), hermes cron,
// and heartbeat join. Every external call goes through child_process.execFile with
// an argv array — never shell string-concat. Each scanner fails soft (catches its
// own errors, logs, and returns []) so one broken scanner never crashes the others.

'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFile } = require('child_process');

const HOME = os.homedir();
const REPO_ROOT = path.join(__dirname, '..');

function execFileP(cmd, args, opts) {
  return new Promise((resolve, reject) => {
    execFile(cmd, args, { maxBuffer: 10 * 1024 * 1024, ...opts }, (err, stdout, stderr) => {
      if (err) {
        err.stdout = stdout;
        err.stderr = stderr;
        reject(err);
        return;
      }
      resolve({ stdout, stderr });
    });
  });
}

function safeReadJson(filePath) {
  try {
    const raw = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(raw);
  } catch (err) {
    return null;
  }
}

function logScanError(scannerName, err) {
  // Fail soft: log to stderr, never throw out of a scanner.
  try {
    // eslint-disable-next-line no-console
    console.error(`[schedule_scan] ${scannerName} failed: ${err && err.message ? err.message : err}`);
  } catch (_) {
    // even logging must not throw
  }
}

// ---------------------------------------------------------------------------
// Scanner 1: launchd (~/Library/LaunchAgents/*.plist)
// ---------------------------------------------------------------------------

async function getLoadedLaunchdLabels() {
  // `launchctl list` — no args needed, prints a table of all loaded jobs for the user.
  // Format (tab-separated): PID  LastExitStatus  Label
  const loaded = new Set();
  try {
    const { stdout } = await execFileP('launchctl', ['list']);
    const lines = stdout.split('\n');
    for (const line of lines) {
      const parts = line.split('\t');
      if (parts.length >= 3) {
        const label = parts[2].trim();
        if (label) loaded.add(label);
      }
    }
  } catch (err) {
    logScanError('scanLaunchd:launchctl-list', err);
  }
  return loaded;
}

function calendarIntervalToDisplay(sci) {
  if (!sci) return null;
  // StartCalendarInterval can be a single object or an array of objects.
  const entries = Array.isArray(sci) ? sci : [sci];
  const parts = entries.map((e) => {
    const h = typeof e.Hour === 'number' ? String(e.Hour).padStart(2, '0') : '*';
    const m = typeof e.Minute === 'number' ? String(e.Minute).padStart(2, '0') : '00';
    let prefix = '';
    if (typeof e.Weekday === 'number') prefix = `weekday ${e.Weekday} `;
    if (typeof e.Day === 'number') prefix = `day ${e.Day} `;
    if (typeof e.Month === 'number') prefix += `month ${e.Month} `;
    return `${prefix}${h}:${m}`;
  });
  return parts.join(', ');
}

async function scanLaunchd() {
  const jobs = [];
  let plistDir;
  try {
    plistDir = path.join(HOME, 'Library', 'LaunchAgents');
    if (!fs.existsSync(plistDir)) return jobs;
  } catch (err) {
    logScanError('scanLaunchd:init', err);
    return jobs;
  }

  let files = [];
  try {
    files = fs.readdirSync(plistDir).filter((f) => f.endsWith('.plist'));
  } catch (err) {
    logScanError('scanLaunchd:readdir', err);
    return jobs;
  }

  const loadedLabels = await getLoadedLaunchdLabels();

  for (const file of files) {
    const fullPath = path.join(plistDir, file);
    try {
      // plutil -convert json -o - <path>  — execFile with argv array, no shell concat.
      const { stdout } = await execFileP('plutil', ['-convert', 'json', '-o', '-', fullPath]);
      let parsed;
      try {
        parsed = JSON.parse(stdout);
      } catch (parseErr) {
        logScanError(`scanLaunchd:parse:${file}`, parseErr);
        continue;
      }

      const label = parsed.Label || path.basename(file, '.plist');
      const isAttax = label.startsWith('com.attax.');
      const enabled = loadedLabels.has(label);

      const scheduleDisplay = calendarIntervalToDisplay(parsed.StartCalendarInterval);
      const programArgs = Array.isArray(parsed.ProgramArguments) ? parsed.ProgramArguments : [];

      jobs.push({
        id: `launchd:${label}`,
        kind: 'launchd',
        name: label,
        description: programArgs.length ? programArgs.join(' ') : null,
        enabled,
        schedule: {
          display: scheduleDisplay || (parsed.StartInterval ? `every ${parsed.StartInterval}s` : 'unknown'),
          cron: null,
          calendar: parsed.StartCalendarInterval || null,
        },
        lastRun: { status: 'never', at: null, summary: null },
        controllable: isAttax
          ? { toggle: true, retime: true, runNow: true }
          : { toggle: false, retime: false, runNow: false },
        source: {
          plistPath: fullPath,
          note: isAttax ? null : 'system, view-only',
        },
      });
    } catch (err) {
      logScanError(`scanLaunchd:${file}`, err);
      // skip this plist, keep going
    }
  }

  return jobs;
}

// ---------------------------------------------------------------------------
// Scanner 2: native (~/.claude/scheduled-tasks/*/SKILL.md)
// ---------------------------------------------------------------------------

function parseFrontmatter(content) {
  // Minimal YAML frontmatter parser for the two fields we need: name, description.
  // Frontmatter is delimited by --- ... --- at the top of the file.
  const match = content.match(/^---\s*\n([\s\S]*?)\n---/);
  if (!match) return {};
  const body = match[1];
  const result = {};
  const nameMatch = body.match(/^name:\s*(.+)$/m);
  const descMatch = body.match(/^description:\s*(.+)$/m);
  if (nameMatch) result.name = nameMatch[1].trim();
  if (descMatch) result.description = descMatch[1].trim();
  return result;
}

async function scanNative(launchdJobs) {
  const jobs = [];
  let baseDir;
  try {
    baseDir = path.join(HOME, '.claude', 'scheduled-tasks');
    if (!fs.existsSync(baseDir)) return jobs;
  } catch (err) {
    logScanError('scanNative:init', err);
    return jobs;
  }

  // Build a set of launchd base names (com.attax.<name>) for dedupe.
  const attaxBaseNames = new Set();
  for (const j of launchdJobs || []) {
    if (j.kind === 'launchd' && j.name.startsWith('com.attax.')) {
      attaxBaseNames.add(j.name.replace('com.attax.', ''));
    }
  }

  let dirs = [];
  try {
    dirs = fs.readdirSync(baseDir, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => d.name);
  } catch (err) {
    logScanError('scanNative:readdir', err);
    return jobs;
  }

  for (const dirName of dirs) {
    try {
      const skillPath = path.join(baseDir, dirName, 'SKILL.md');
      if (!fs.existsSync(skillPath)) continue;
      const content = fs.readFileSync(skillPath, 'utf8');
      const fm = parseFrontmatter(content);
      const name = fm.name || dirName;

      // Dedupe: if a native task's base name matches a com.attax.<name> launchd
      // plist (e.g. skillsmith-routine), prefer the launchd entry and drop this one.
      if (attaxBaseNames.has(name) || attaxBaseNames.has(dirName)) {
        continue;
      }

      jobs.push({
        id: `native:${dirName}`,
        kind: 'native',
        name,
        description: fm.description || null,
        enabled: true,
        schedule: {
          display: 'app-managed',
          cron: null,
          calendar: null,
        },
        lastRun: { status: 'never', at: null, summary: null },
        controllable: { toggle: false, retime: false, runNow: false },
        source: {
          skillPath,
        },
      });
    } catch (err) {
      logScanError(`scanNative:${dirName}`, err);
    }
  }

  return jobs;
}

// ---------------------------------------------------------------------------
// Scanner 3: hermes cron
// ---------------------------------------------------------------------------

async function scanHermes() {
  const jobs = [];
  try {
    const { stdout } = await execFileP('hermes', ['cron', 'list', '--all']);
    const trimmed = (stdout || '').trim();
    if (!trimmed) return jobs;

    let parsed = null;
    try {
      parsed = JSON.parse(trimmed);
    } catch (parseErr) {
      // Non-JSON output (e.g. "No scheduled jobs.") — treat as zero jobs, not an error.
      return jobs;
    }

    const list = Array.isArray(parsed) ? parsed : (Array.isArray(parsed.jobs) ? parsed.jobs : []);
    for (const item of list) {
      if (!item || typeof item !== 'object') continue;
      const id = item.id || item.name || `hermes-job-${jobs.length}`;
      jobs.push({
        id: `hermes:${id}`,
        kind: 'hermes',
        name: item.name || String(id),
        description: item.description || item.prompt || null,
        enabled: item.enabled !== false,
        schedule: {
          display: item.schedule_display || item.cron || 'unknown',
          cron: item.cron || null,
          calendar: null,
        },
        lastRun: { status: 'never', at: null, summary: null },
        controllable: { toggle: true, retime: true, runNow: true },
        source: { raw: item },
      });
    }
  } catch (err) {
    // hermes CLI missing, unreachable, or errored — fail soft, zero jobs.
    logScanError('scanHermes', err);
  }
  return jobs;
}

// ---------------------------------------------------------------------------
// Scanner 4: heartbeats — join lastRun info onto jobs by id/name
// ---------------------------------------------------------------------------

function loadHeartbeats() {
  const heartbeats = [];

  try {
    const singleFile = path.join(REPO_ROOT, 'data', 'routine-heartbeat.json');
    const single = safeReadJson(singleFile);
    if (single) {
      heartbeats.push({ source: singleFile, data: single });
    }
  } catch (err) {
    logScanError('readHeartbeats:single', err);
  }

  try {
    const heartbeatsDir = path.join(REPO_ROOT, 'data', 'heartbeats');
    if (fs.existsSync(heartbeatsDir)) {
      const files = fs.readdirSync(heartbeatsDir).filter((f) => f.endsWith('.json'));
      for (const f of files) {
        const full = path.join(heartbeatsDir, f);
        const parsed = safeReadJson(full);
        if (parsed) {
          heartbeats.push({ source: full, id: path.basename(f, '.json'), data: parsed });
        }
      }
    }
  } catch (err) {
    logScanError('readHeartbeats:dir', err);
  }

  return heartbeats;
}

function statusFromHeartbeat(hb) {
  if (!hb || typeof hb !== 'object') return { status: 'never', at: null, summary: null };
  const status = hb.last_run_status || 'never';
  const at = hb.last_run_end || hb.last_run_start || null;
  const summary = hb.last_run_summary || null;
  // Never fake "ok" — only report ok if the heartbeat actually says so.
  if (status !== 'ok' && status !== 'warn' && status !== 'error') {
    return { status: 'never', at, summary };
  }
  return { status, at, summary };
}

function readHeartbeats(jobs) {
  let heartbeats;
  try {
    heartbeats = loadHeartbeats();
  } catch (err) {
    logScanError('readHeartbeats', err);
    return jobs;
  }

  if (!heartbeats.length) return jobs;

  // The single routine-heartbeat.json file is (today) a global heartbeat with no
  // job id of its own. Best-effort: join it onto the skillsmith-routine job by name,
  // since that's the routine it tracks. Per-file heartbeats (data/heartbeats/<id>.json)
  // join by matching <id> against the job's name or native dirName.
  for (const hb of heartbeats) {
    try {
      if (hb.id) {
        // Named heartbeat file — try to match by id against job name/id suffix.
        const match = jobs.find((j) => j.id.endsWith(`:${hb.id}`) || j.name === hb.id);
        if (match) {
          match.lastRun = statusFromHeartbeat(hb.data);
        }
      } else {
        // The single global routine-heartbeat.json — best-effort join to the
        // skillsmith-routine job (the routine this file currently tracks).
        const match = jobs.find((j) => j.name === 'com.attax.skillsmith-routine' || j.name === 'skillsmith-routine');
        if (match) {
          match.lastRun = statusFromHeartbeat(hb.data);
        }
      }
    } catch (err) {
      logScanError('readHeartbeats:join', err);
    }
  }

  return jobs;
}

// ---------------------------------------------------------------------------
// Composition
// ---------------------------------------------------------------------------

async function scanAll() {
  let launchdJobs = [];
  try {
    launchdJobs = await scanLaunchd();
  } catch (err) {
    logScanError('scanAll:scanLaunchd', err);
    launchdJobs = [];
  }

  let nativeJobs = [];
  try {
    nativeJobs = await scanNative(launchdJobs);
  } catch (err) {
    logScanError('scanAll:scanNative', err);
    nativeJobs = [];
  }

  let hermesJobs = [];
  try {
    hermesJobs = await scanHermes();
  } catch (err) {
    logScanError('scanAll:scanHermes', err);
    hermesJobs = [];
  }

  let jobs = [...launchdJobs, ...nativeJobs, ...hermesJobs];

  try {
    jobs = readHeartbeats(jobs);
  } catch (err) {
    logScanError('scanAll:readHeartbeats', err);
  }

  return { jobs };
}

module.exports = {
  scanAll,
  // exported for testing / introspection
  scanLaunchd,
  scanNative,
  scanHermes,
  readHeartbeats,
};
