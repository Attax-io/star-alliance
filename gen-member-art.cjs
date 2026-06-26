#!/usr/bin/env node
// Generates legendary Greek/Zeus-like portrait art for each guild member via MiniMax image API.
// Also regenerates kimi-k2.7 as a proper warhammer.
// Usage: node gen-member-art.cjs

const fs = require("fs");
const path = require("path");
const https = require("https");

const KEY_PATH = path.join(process.env.HOME, ".config/minimax/m3.key");
const API_KEY = fs.readFileSync(KEY_PATH, "utf8").trim();

const MEMBER_DIR = path.join(__dirname, "member-art");
const WEAPON_DIR = path.join(__dirname, "weapon-art");
fs.mkdirSync(MEMBER_DIR, { recursive: true });

const MEMBERS = [
  {
    id: "the-butler",
    color: "#b89530",
    prompt: "Legendary divine portrait, a refined well-dressed servant man in a pristine dark tailored butler coat with white gloves, bowing slightly with a silver serving tray, humble deferential posture, soft warm candlelight, subtle divine glow, aristocratic manor backdrop, ultra detailed epic fantasy art, no religious symbols",
  },
  {
    id: "the-architect",
    color: "#3b7dd8",
    prompt: "Legendary divine portrait, a tall dark-skinned man with natural hair crowned in sapphire light, deep blue architectural robes, holding glowing holographic blueprints, radiant blue divine energy, intense focused eyes, marble temple backdrop, ultra detailed epic fantasy art, no religious symbols",
  },
  {
    id: "the-developer",
    color: "#3da155",
    prompt: "Legendary divine portrait, a young South Asian man with short dark hair, emerald green tech-mage robes, green lightning and code sparks crackling from his fingertips, forge fire behind him, determined gaze, ultra detailed epic fantasy art, dark background, no religious symbols",
  },
  {
    id: "the-designer",
    color: "#d54d7a",
    prompt: "Legendary divine portrait, a broad-shouldered Northern European woman with long braided blonde hair, golden armored robes adorned with runic symbols, surrounded by floating glowing design schematics and art tools, radiant golden divine energy, fierce creative gaze, dark dramatic background, ultra detailed epic fantasy art, no religious symbols",
  },
  {
    id: "the-strategist",
    color: "#7c5dc8",
    prompt: "Legendary divine portrait, a regal older Asian man with silver hair, deep violet war-commander robes trimmed in dark gold, calculating cold gaze, glowing purple strategy maps floating around him, purple divine energy crackling at his fingertips, dark epic throne room background, ultra detailed epic fantasy art, no religious symbols",
  },
  {
    id: "the-translator",
    color: "#b89530",
    prompt: "Legendary divine portrait, an older Middle Eastern man with a long silver-streaked beard, golden scholar robes, surrounded by swirling ancient scripts and language runes of many civilizations, golden divine light, wise serene expression, ultra detailed epic fantasy art, no religious symbols",
  },
  {
    id: "the-herald",
    color: "#e0883c",
    prompt: "Legendary divine portrait, a charismatic herald with a great golden horn raised to the sky, amber-gold and bronze robes, radiant sound waves and unfurling banners behind, confident outward gaze, warm divine light, ultra detailed epic fantasy art, dark background, no religious symbols",
  },
  {
    id: "the-merchant",
    color: "#3da155",
    prompt: "Legendary divine portrait, a sharp-featured Indian man with sleek dark hair and a trimmed beard, emerald-gold merchant robes, one hand balancing glowing golden scales, other hand holding rising market charts, confident powerful smile, divine green light, ultra detailed epic fantasy art, no religious symbols",
  },
  {
    id: "the-quartermaster",
    color: "#b89530",
    prompt: "Legendary divine portrait, a broad-shouldered Northern European man with short blonde hair and a strong jaw, golden armored robes, surrounded by floating glowing inventory scrolls and ledgers, keeper-of-all-knowledge aura, golden divine energy, dark dramatic background, ultra detailed epic fantasy art, no religious symbols",
  },
];

const KIMI_FIX = {
  id: "kimi-k2.7",
  color: "#ff6b8a",
  prompt: "A legendary rose-red warhammer, massive brutal rectangular hammerhead covered in glowing pink runes, thick reinforced handle wrapped in crimson leather, pink-crimson elemental energy flames erupting from the head, dark fantasy weapon art, ultra detailed, isolated on dark background, 200x200",
};

function postJSON(url, headers, body) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const data = JSON.stringify(body);
    const req = https.request(
      {
        hostname: u.hostname,
        path: u.pathname + u.search,
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json", "Content-Length": Buffer.byteLength(data) },
      },
      (res) => {
        let buf = "";
        res.on("data", (d) => (buf += d));
        res.on("end", () => {
          if (res.statusCode >= 400) return reject(new Error(`HTTP ${res.statusCode}: ${buf}`));
          try { resolve(JSON.parse(buf)); }
          catch (e) { reject(new Error("Bad JSON: " + buf.slice(0, 200))); }
        });
      }
    );
    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

function downloadBinary(url, dest) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith("https") ? https : require("http");
    const file = fs.createWriteStream(dest);
    mod.get(url, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        file.close();
        return downloadBinary(res.headers.location, dest).then(resolve).catch(reject);
      }
      res.pipe(file);
      file.on("finish", () => file.close(resolve));
    }).on("error", (e) => { fs.unlink(dest, () => {}); reject(e); });
  });
}

async function generate(prompt, outPath, label) {
  if (fs.existsSync(outPath)) {
    console.log(`✓ ${label} — already exists, skipping`);
    return;
  }
  console.log(`⚡ Generating ${label}…`);
  const resp = await postJSON(
    "https://api.minimax.io/v1/image_generation",
    { Authorization: `Bearer ${API_KEY}` },
    { model: "image-01", prompt, aspect_ratio: "1:1", response_format: "url", n: 1 }
  );
  const imageUrl = resp?.data?.image_urls?.[0];
  if (!imageUrl) throw new Error(`No URL: ${JSON.stringify(resp).slice(0, 200)}`);
  await downloadBinary(imageUrl, outPath);
  console.log(`✓ ${label} → ${path.relative(__dirname, outPath)}`);
}

(async () => {
  // Fix kimi warhammer first
  await generate(KIMI_FIX.prompt, path.join(WEAPON_DIR, `${KIMI_FIX.id}.png`), `weapon:${KIMI_FIX.id} (REGEN)`).catch(e => console.error(`✗ kimi: ${e.message}`));

  // Member portraits
  for (const m of MEMBERS) {
    await generate(m.prompt, path.join(MEMBER_DIR, `${m.id}.png`), `member:${m.id}`).catch(e => console.error(`✗ ${m.id}: ${e.message}`));
  }
  console.log("Done.");
})();
