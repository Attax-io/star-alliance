#!/usr/bin/env node
// Generates role classification icons (thinker / doer / both) via MiniMax image API.
// Output: role-art/thinker.png, role-art/doer.png, role-art/both.png
// Usage: node gen-role-icons.cjs

const fs   = require("fs");
const path = require("path");
const https = require("https");

const KEY  = fs.readFileSync(path.join(process.env.HOME, ".config/minimax/m3.key"), "utf8").trim();
const OUT  = path.join(__dirname, "..", "..", "role-art");
fs.mkdirSync(OUT, { recursive: true });

const ICONS = [
  {
    id: "thinker",
    prompt: "Legendary dark fantasy emblem icon, a GLOWING ARCANE EYE OF OMNISCIENCE floating inside a radiant violet crystal prism, intense deep PURPLE and INDIGO energy swirling around it, ancient mystical runes orbiting the eye, all-seeing oracle power, VIVID oversaturated violet glow radiating outward, pure black background, fallen sword legendary game art style, ultra sharp ultra detailed, square composition",
  },
  {
    id: "doer",
    prompt: "Legendary dark fantasy emblem icon, a BLAZING DIVINE FORGE HAMMER crashing down on an anvil of pure fire, INTENSE AMBER and ORANGE flames erupting around the impact, molten metal sparks flying, runes of execution and power burning across the hammerhead, raw unstoppable force energy, VIVID oversaturated orange-gold radiance, pure black background, fallen sword legendary game art style, ultra sharp ultra detailed, square composition",
  },
  {
    id: "both",
    prompt: "Legendary dark fantasy emblem icon, TWO CROSSED LEGENDARY BLADES forming an X, one blade made of PURE ICE-BLUE lightning and one made of BLAZING GOLD divine fire, yin-yang of thinker and doer energies, INTENSE dual-element aura where they cross, arcane symbols glowing at the intersection, VIVID oversaturated blue and gold radiance, pure black background, fallen sword legendary game art style, ultra sharp ultra detailed, square composition",
  },
];

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

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith("https") ? https : require("http");
    const file = fs.createWriteStream(dest);
    mod.get(url, res => {
      if (res.statusCode === 301 || res.statusCode === 302)
        return download(res.headers.location, dest).then(resolve).catch(reject);
      res.pipe(file);
      file.on("finish", () => file.close(resolve));
    }).on("error", e => { fs.unlink(dest, () => {}); reject(e); });
  });
}

(async () => {
  for (const icon of ICONS) {
    const dest = path.join(OUT, `${icon.id}.png`);
    if (fs.existsSync(dest)) { console.log(`✓ ${icon.id} — exists, skipping`); continue; }
    console.log(`⚡ Generating ${icon.id}…`);
    const resp = await postJSON("https://api.minimax.io/v1/image_generation", {
      model: "image-01", prompt: icon.prompt, aspect_ratio: "1:1", response_format: "url", n: 1,
    });
    const url = resp?.data?.image_urls?.[0];
    if (!url) { console.error(`✗ ${icon.id}: no URL — ${JSON.stringify(resp).slice(0,200)}`); continue; }
    await download(url, dest);
    console.log(`✓ ${icon.id} → role-art/${icon.id}.png`);
  }
  console.log("Done.");
})();
