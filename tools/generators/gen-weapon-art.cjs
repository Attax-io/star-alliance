#!/usr/bin/env node
// Generates legendary weapon art for each arsenal model via MiniMax image API.
// Output: weapon-art/<model-id>.png (200x200)
// Usage: node gen-weapon-art.cjs

const fs = require("fs");
const path = require("path");
const https = require("https");

const KEY_PATH = path.join(process.env.HOME, ".config/minimax/m3.key");
const API_KEY = fs.readFileSync(KEY_PATH, "utf8").trim();

const OUT_DIR = path.join(__dirname, "..", "..", "weapon-art");
fs.mkdirSync(OUT_DIR, { recursive: true });

const WEAPONS = [
  {
    id: "opus",
    prompt: "VIBRANT GLOWING fantasy weapon art. A divine scepter-trident, PURE MOLTEN GOLD, three prongs shooting blinding solar flares, ancient pharaoh runes blazing with white-gold light, massive god-scale size, INTENSE oversaturated gold and white radiance, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "sonnet",
    prompt: "VIBRANT GLOWING fantasy weapon art. An elegant longsword, blade made of PURE ELECTRIC CYAN lightning, intensely saturated aqua-blue glow, crackling lightning arcs all along the edge, wings cross-guard, BRILLIANT neon cyan aura radiating outward, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "haiku",
    prompt: "VIBRANT GLOWING fantasy weapon art. A slender stiletto blade, impossibly thin and needle-sharp, BLAZING NEON GREEN, vivid emerald energy crackling along the edge like static electricity, ornate finger-ring guard, INTENSE saturated green radiance on black, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "gpt-5.5",
    prompt: "VIBRANT GLOWING fantasy weapon art. A wizard staff topped with a MASSIVE pulsing violet crystal orb, DEEP SATURATED PURPLE with cosmic nebula swirling inside, bright arcane glyphs orbiting it, INTENSE purple-magenta radiance exploding outward, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "minimax-m3",
    prompt: "VIBRANT GLOWING fantasy weapon art. A heavy siege crossbow, wide powerful limbs made of dark metal and bone, a glowing TEAL-GREEN bolt loaded on the track, intricate circuit rune engravings across the stock, mechanical cocking mechanism visible, VIVID neon teal string and bolt tip radiating energy, INTENSE saturated teal glow, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "image-01",
    prompt: "VIBRANT GLOWING fantasy weapon art. An enchanter's magic paintbrush wielded like a wand, long ornate handle, bristles of pure liquid JADE-EMERALD light dripping glowing paint, a ring of luminous color-swatches and arcane sigils orbiting the tip, INTENSE saturated emerald-green radiance, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "minimax-video",
    prompt: "VIBRANT GLOWING fantasy weapon art. A mystical scrying-loom, an ornate circular frame strung with shimmering threads of pure TEAL-CYAN light, a glowing woven tapestry of a moving vision rippling in the center, a luminous shuttle trailing streams of light, INTENSE saturated teal-cyan radiance, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "minimax-speech",
    prompt: "VIBRANT GLOWING fantasy weapon art. A herald's great war horn, a long curved brass-and-bone horn with ornate engraved bands, GLOWING SPRING-GREEN sound waves blasting outward from its bell, luminous runes along the curve, INTENSE saturated green radiance rippling outward, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "minimax-music",
    prompt: "VIBRANT GLOWING fantasy weapon art. A bard's enchanted lute, elegant rounded body with ornate inlay along the neck, strings of pure LIME-CHARTREUSE light, glowing musical notes and sound-glyphs drifting off the strings, INTENSE saturated lime-green radiance, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "glm-5.2",
    prompt: "VIBRANT GLOWING fantasy weapon art. A tall elegant LONGBOW shown full length, BLAZING AMBER-ORANGE wood, ancient multilingual inscriptions glowing gold along the limbs, bowstring made of pure golden light, and THREE glowing arrows standing point-down in the ground beside the bow, their amber arrowheads and fletching radiating light, clearly a bow-and-arrow weapon, INTENSE warm orange-gold radiance, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "kimi-k2.7",
    prompt: "VIBRANT GLOWING fantasy weapon art. A massive square-headed hammer, enormous flat striking face covered in BLAZING HOT MAGENTA-PINK runes, thick reinforced handle, VIVID electric-pink plasma erupting from the hammerhead like an explosion, raw blunt force energy, INTENSE magenta radiance, no red tones, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "deepseek-v4-pro",
    prompt: "VIBRANT GLOWING fantasy weapon art. A death scythe with a long curved blade, BRILLIANT SAPPHIRE BLUE glowing blade edge, long dark staff, VIVID electric-blue energy crackling along the full arc of the blade, sweeping powerful silhouette, INTENSE cobalt-blue radiance blooming outward, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "nemotron-3-ultra",
    prompt: "VIBRANT GLOWING fantasy weapon art. A long jousting lance, GLOWING ICY SILVER-WHITE, crystalline tip radiating frozen starlight, VIVID ice-blue and white aura, ice shards exploding from the tip, BRILLIANT celestial radiance, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "qwen3.5",
    prompt: "VIBRANT GLOWING fantasy weapon art. A curved katana, blade made of PURE VIOLET ARCANE ENERGY, BLAZING lavender-purple glow, magical particles and petals dissolving off the edge, INTENSE saturated violet radiance, pure black background, ultra sharp ultra detailed",
  },
  {
    id: "gemma4",
    prompt: "VIBRANT GLOWING fantasy weapon art. A ninja shuriken throwing star, eight razor-sharp points perfectly symmetrical, BLAZING AMBER-ORANGE like a spinning miniature sun, spinning motion blur, VIVID orange-gold fire trails from each point, INTENSE warm radiance exploding outward, pure black background, ultra sharp ultra detailed",
  },
];

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
    const u = new URL(url);
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

async function generateWeapon(w) {
  const outPath = path.join(OUT_DIR, `${w.id}.png`);
  if (fs.existsSync(outPath)) {
    console.log(`✓ ${w.id} — already exists, skipping`);
    return;
  }
  console.log(`⚔ Generating ${w.id}…`);

  // MiniMax image generation endpoint
  const resp = await postJSON(
    "https://api.minimax.io/v1/image_generation",
    { Authorization: `Bearer ${API_KEY}` },
    {
      model: "image-01",
      prompt: w.prompt,
      aspect_ratio: "1:1",
      response_format: "url",
      n: 1,
    }
  );

  const imageUrl = resp?.data?.image_urls?.[0] || resp?.data?.[0]?.url || resp?.images?.[0]?.url;
  if (!imageUrl) throw new Error(`No URL in response: ${JSON.stringify(resp).slice(0, 300)}`);

  await downloadBinary(imageUrl, outPath);
  console.log(`✓ ${w.id} → weapon-art/${w.id}.png`);
}

(async () => {
  for (const w of WEAPONS) {
    try {
      await generateWeapon(w);
    } catch (e) {
      console.error(`✗ ${w.id}: ${e.message}`);
    }
  }
  console.log("Done.");
})();
