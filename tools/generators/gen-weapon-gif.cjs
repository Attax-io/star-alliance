#!/usr/bin/env node
// Animates each arsenal weapon PNG → GIF via MiniMax video-01 (image-to-video).
// Pipeline: weapon-art/<id>.png → MiniMax video → MP4 → GIF (via ffmpeg)
// Usage: node gen-weapon-gif.cjs [id]   (no arg = all)

const fs   = require("fs");
const path = require("path");
const https = require("https");
const http  = require("http");
const { execSync } = require("child_process");

const KEY   = fs.readFileSync(path.join(process.env.HOME, ".config/minimax/m3.key"), "utf8").trim();
const SRC   = path.join(__dirname, "..", "..", "weapon-art");
const GIF   = path.join(__dirname, "..", "..", "weapon-gif");
const TMP   = path.join(__dirname, "..", "..", "weapon-tmp");
[GIF, TMP].forEach(d => fs.mkdirSync(d, { recursive: true }));

const WEAPONS = [
  { id: "opus",             color: "#e8c93a", aura: "golden solar divine light pulsing, gold energy waves rippling outward" },
  { id: "sonnet",           color: "#3df0ff", aura: "cyan electric lightning arcs crackling, ice-blue energy pulses along the blade" },
  { id: "haiku",            color: "#4ec985", aura: "neon green spirit fireflies swirling, emerald energy shimmering" },
  { id: "minimax-m3",       color: "#4ec9a0", aura: "teal circuit energy sparking, mechanical crossbow limbs vibrating with teal pulses" },
  { id: "glm-5.2",          color: "#d4a05a", aura: "amber-gold fire and embers drifting upward, warm orange bow glow pulsing" },
  { id: "kimi-k2.7",        color: "#ff6b8a", aura: "hot magenta plasma erupting from the hammerhead, pink energy shockwaves radiating" },
  { id: "deepseek-v4-pro",  color: "#5b8cff", aura: "sapphire blue energy arcs sweeping along the scythe blade, cobalt waves pulsing" },
  { id: "nemotron-3-ultra", color: "#7fd4ff", aura: "icy silver-white crystalline shards drifting, celestial blue-white light pulsing" },
  { id: "qwen3.5",          color: "#c47fff", aura: "violet arcane energy flowing, lavender petals dissolving into magical particles" },
  { id: "gemma4",           color: "#ffb04e", aura: "amber-orange comet fire trails spinning, blazing star radiance pulsing outward" },
];

const TARGET = process.argv[2];
const QUEUE  = TARGET ? WEAPONS.filter(w => w.id === TARGET) : WEAPONS;

function postJSON(url, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const u = new URL(url);
    const req = https.request({
      hostname: u.hostname, path: u.pathname, method: "POST",
      headers: { Authorization: `Bearer ${KEY}`, "Content-Type": "application/json", "Content-Length": Buffer.byteLength(data) },
    }, res => {
      let buf = ""; res.on("data", d => buf += d);
      res.on("end", () => { try { resolve(JSON.parse(buf)); } catch(e) { reject(new Error(buf.slice(0,300))); } });
    });
    req.on("error", reject); req.write(data); req.end();
  });
}

function getJSON(url) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    https.get({ hostname: u.hostname, path: u.pathname + u.search,
      headers: { Authorization: `Bearer ${KEY}` } }, res => {
      let buf = ""; res.on("data", d => buf += d);
      res.on("end", () => { try { resolve(JSON.parse(buf)); } catch(e) { reject(new Error(buf.slice(0,300))); } });
    }).on("error", reject);
  });
}

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith("https") ? https : http;
    const file = fs.createWriteStream(dest);
    mod.get(url, res => {
      if (res.statusCode === 301 || res.statusCode === 302)
        return download(res.headers.location, dest).then(resolve).catch(reject);
      res.pipe(file);
      file.on("finish", () => file.close(resolve));
    }).on("error", e => { fs.unlink(dest, () => {}); reject(e); });
  });
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function poll(taskId, label) {
  for (let i = 0; i < 60; i++) {
    await sleep(8000);
    const r = await getJSON(`https://api.minimax.io/v1/query/video_generation?task_id=${taskId}`);
    const status = r.status;
    process.stdout.write(`\r  [${label}] ${status}… (${(i+1)*8}s)`);
    if (status === "Success") { console.log(); return r.file_id; }
    if (status === "Fail") throw new Error(`Task failed: ${JSON.stringify(r)}`);
  }
  throw new Error("Timed out after 8 min");
}

async function processWeapon(w) {
  const gifPath = path.join(GIF, `${w.id}.gif`);
  if (fs.existsSync(gifPath)) { console.log(`✓ ${w.id} — gif exists, skipping`); return; }

  const srcPng = path.join(SRC, `${w.id}.png`);
  if (!fs.existsSync(srcPng)) { console.error(`✗ ${w.id} — source PNG missing`); return; }

  console.log(`🎬 ${w.id} — submitting to MiniMax video-01…`);

  const imgB64 = "data:image/png;base64," + fs.readFileSync(srcPng).toString("base64");
  const prompt = `The weapon comes alive with ${w.aura}. Subtle slow motion, loopable animation, dark background, cinematic fantasy, no camera movement.`;

  const sub = await postJSON("https://api.minimax.io/v1/video_generation", {
    model: "video-01",
    prompt,
    first_frame_image: imgB64,
  });

  if (!sub.task_id) throw new Error(`No task_id: ${JSON.stringify(sub).slice(0,200)}`);
  console.log(`  task_id: ${sub.task_id}`);

  const fileId = await poll(sub.task_id, w.id);

  // retrieve download URL
  const meta = await getJSON(`https://api.minimax.io/v1/files/retrieve?file_id=${fileId}`);
  const videoUrl = meta.file?.download_url;
  if (!videoUrl) throw new Error(`No download_url: ${JSON.stringify(meta).slice(0,200)}`);

  const mp4 = path.join(TMP, `${w.id}.mp4`);
  console.log(`  downloading MP4…`);
  await download(videoUrl, mp4);

  // MP4 → GIF via ffmpeg (palette-optimized, elemental color tinted, 480px wide, 15fps)
  console.log(`  converting to GIF…`);
  const palette = path.join(TMP, `${w.id}-palette.png`);
  execSync(`ffmpeg -y -i "${mp4}" -vf "fps=12,scale=480:-1:flags=lanczos,palettegen=stats_mode=diff" "${palette}" 2>/dev/null`);
  execSync(`ffmpeg -y -i "${mp4}" -i "${palette}" -lavfi "fps=12,scale=480:-1:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" "${gifPath}" 2>/dev/null`);

  console.log(`✓ ${w.id} → weapon-gif/${w.id}.gif`);
}

(async () => {
  for (const w of QUEUE) {
    try { await processWeapon(w); }
    catch(e) { console.error(`\n✗ ${w.id}: ${e.message}`); }
  }
  console.log("Done.");
})();
