#!/usr/bin/env node
// Generates Fallen Sword-themed skill art PNGs via MiniMax image API.
// Output: skill-art/<id>.png
// Usage: node gen-skill-art.cjs [--regen <id>,<id>...]
// --regen flag forces regeneration of specific skills even if PNG exists.

const fs = require("fs");
const path = require("path");
const https = require("https");

const KEY_PATH = path.join(process.env.HOME, ".config/minimax/m3.key");
const API_KEY = fs.readFileSync(KEY_PATH, "utf8").trim();

const OUT_DIR = path.join(__dirname, "skill-art");
fs.mkdirSync(OUT_DIR, { recursive: true });

// Parse --regen flag
const regenArg = process.argv.indexOf("--regen");
const regenSet = new Set(regenArg !== -1 ? process.argv[regenArg + 1].split(",") : []);

const STYLE = "fantasy RPG skill icon, Fallen Sword MMORPG style, dark parchment background with aged leather texture, gold runic border, ornate medieval frame, dramatic lighting, rich saturated colors, detailed pixel-art-adjacent illustration, 48x48 icon style, pure black outer border";

const SKILLS = [
  {
    id: "article-creator",
    prompt: `${STYLE}. A glowing scroll unfurling with golden runic script, quill pen with ink dripping arcane light, parchment page covered in illuminated manuscript text, scribe's candlelight casting warm amber glow`,
  },
  {
    id: "brandkit",
    prompt: `${STYLE}. A gilded heraldic shield bearing a royal crown, flanked by two crossed banners with rampant lion emblems, embossed in gold leaf on deep crimson, wax seal with guild crest at bottom`,
  },
  {
    id: "bug-fix-workflow",
    prompt: `${STYLE}. Two crossed enchanted daggers striking a glowing red demonic rune, sparks and purple arcane energy exploding at the crossing point, the rune cracking and dissolving, dramatic combat lighting`,
  },
  {
    id: "cleanup",
    prompt: `${STYLE}. An enchanted broom trailing golden sparkle dust, sweeping away dark shadows and cobwebs from a stone floor, divine white light following in its wake, purification glow`,
  },
  {
    id: "codex-law-translate",
    prompt: `${STYLE}. An ancient leather-bound law codex open to a glowing page, balanced scales of justice floating above it with golden chains, runic text on both pages in two different ancient scripts`,
  },
  {
    id: "conquering-campaign",
    prompt: `${STYLE}. A war banner planted atop a conquered fortress tower, crimson flag with gold crest whipping in wind, broken enemy shields below, dawn light breaking through storm clouds, triumph`,
  },
  {
    id: "db-rename-sweep",
    prompt: `${STYLE}. A stone tablet with old runes being chiseled away and replaced with new gleaming golden inscriptions, mason's hammer and chisel glowing with arcane energy, dust of old names dissolving`,
  },
  {
    id: "design-taste-frontend",
    prompt: `${STYLE}. A painter's wooden palette with pools of vivid magical paint glowing in different arcane colors, fine paintbrush with gold-tipped bristles, floating runes forming elegant patterns`,
  },
  {
    id: "dev-server",
    prompt: `${STYLE}. A glowing arcane server tower built of stacked magical crystals, each crystal pulsing with different colored light, ethereal cables of light connecting them, a small green power gem at top`,
  },
  {
    id: "fallen-sword-design-language",
    prompt: `${STYLE}. The legendary Iluthar — Sword of Light — fallen diagonally across a dark stone altar, blade radiating blinding gold-white divine light, ancient Erildath runes glowing along the fuller, shadow realm darkness surrounding it`,
  },
  {
    id: "full-output-enforcement",
    prompt: `${STYLE}. A massive tower shield of impenetrable dark steel, embossed with three vertical roman numerals in gold, a large central boss radiating authority, shield wall aura of silver force energy`,
  },
  {
    id: "gpt-taste",
    prompt: `${STYLE}. A crystal tasting goblet filled with swirling violet arcane essence, a refined silver fork hovering beside it, magical sparkles of competing flavors dancing around, alchemist's comparison ritual`,
  },
  {
    id: "graphify",
    prompt: `${STYLE}. An arcane ley-line map with glowing teal nodes connected by pulsing energy threads, small crystals at each node junction, the web pattern forming a constellation on aged parchment`,
  },
  {
    id: "guild-log",
    prompt: `${STYLE}. A massive guild tome open flat, guild crest seal embossed in gold on the cover, crossed swords watermark visible on the pages, neat rows of quest records and member deeds written in glowing ink`,
  },
  {
    id: "high-end-visual-design",
    prompt: `${STYLE}. A flawless diamond gemstone catching light into rainbow prismatic rays, surrounded by floating gold filigree ornaments, resting on velvet cushion, masterwork jeweler's icon of perfection`,
  },
  {
    id: "image-to-code",
    prompt: `${STYLE}. Left side: a vivid fantasy landscape painting on canvas. Right side: the same image dissolving into glowing golden rune-script on parchment scrolls. A wizard's hand holds a transmutation orb at center where image becomes code, clear split transformation, dramatic arcane glow`,
  },
  {
    id: "imagegen-frontend-mobile",
    prompt: `${STYLE}. A glowing rectangular arcane tablet — like a magical smartphone — held upright, vivid fantasy artwork materializing on its crystal screen from summoning sparks, the tablet framed in ornate gold runes, clearly a handheld magical device generating images`,
  },
  {
    id: "imagegen-frontend-web",
    prompt: `${STYLE}. A grand arcane viewing portal framed in carved stone, magical image conjuring itself within from swirling violet and teal energy, web of glowing threads radiating from the frame`,
  },
  {
    id: "impeccable",
    prompt: `${STYLE}. A radiant 8-pointed star of pure divine light, each point a different precious gemstone color, central white core of absolute perfection, gold filigree rays extending outward, flawless`,
  },
  {
    id: "industrial-brutalist-ui",
    prompt: `${STYLE}. A brutal iron fortress gate with exposed bolts and rivets, raw dark steel aesthetic, minimal harsh geometric angles, heavy chains, no decoration — pure function and power, grim determination`,
  },
  {
    id: "minimalist-ui",
    prompt: `${STYLE}. A single perfect enso circle brushed in silver on dark stone, one glowing dot at center, four minimal accent marks at cardinal points, zen balance and negative space, elegant restraint`,
  },
  {
    id: "obsidian-markdown",
    prompt: `${STYLE}. A razor-sharp obsidian crystal shard, black volcanic glass with purple arcane veins glowing within, a glowing hash rune carved into its face, floating above a dark altar`,
  },
  {
    id: "performance",
    prompt: `${STYLE}. A golden lightning bolt crackling with pure electric speed energy, motion blur streaks behind it, small thunderclouds parting, the bolt etched with acceleration runes, pure kinetic power`,
  },
  {
    id: "redesign-existing-projects",
    prompt: `${STYLE}. A phoenix rising from the ashes of an old crumbling structure, vivid orange and gold flames of rebirth, new gleaming architecture emerging from the fire, transformation and renewal`,
  },
  {
    id: "skillsmith",
    prompt: `${STYLE}. A dwarven anvil with a glowing skill rune being hammered into a weapon, forge sparks of orange arcane fire flying, the hammer embossed with a gear symbol, craftsmanship and creation`,
  },
  {
    id: "stitch-design-taste",
    prompt: `${STYLE}. An enchanted needle trailing a thread of liquid gold light, stitching together two pieces of magical fabric with glowing patterns, the thread forming elegant runes as it weaves`,
  },
  {
    id: "strategies-review",
    prompt: `${STYLE}. A tactical war map spread on a wooden table, carved chess-piece king at center, glowing battle lines drawn in arcane light, strategic markers showing troop movements, commander's seal`,
  },
  {
    id: "supabase",
    prompt: `${STYLE}. A teal-green lightning bolt of pure database power striking downward into a crystal database tower, electric energy crackling, the bolt engraved with circuit-like runes, storage and speed combined`,
  },
  {
    id: "supabase-postgres-best-practices",
    prompt: `${STYLE}. A wise ancient war elephant rendered in deep blue steel armor, holding a glowing database crystal in its trunk, a golden checkmark seal embossed on its flank, Postgres guardian`,
  },
  {
    id: "transactions-domain-model",
    prompt: `${STYLE}. A golden merchant's scale perfectly balanced with glowing transaction coins, a ledger book with flowing arcane accounting runes, silk purse of gold coins, the economics of the realm`,
  },
  {
    id: "vault-log-compliance",
    prompt: `${STYLE}. A massive circular iron vault door, heavily riveted dark steel, four thick locking bolts at cardinal points, ornate combination wheel at center, red wax compliance seal stamped on the door, NO text or watermarks, pure fantasy RPG icon, no game logos`,
  },
  {
    id: "storm-investigation",
    prompt: `${STYLE}. A swirling tempest of dark arcane storm clouds encircling a central glowing crystal scrying orb set with an all-seeing eye, five ghostly spectral advisor faces emerging from the storm at the points of a pentagonal divination circle, threads of golden insight streaming from each spectre into the orb, forks of violet contradiction-lightning crackling between opposing spectres, glowing runic research sigils etched on the parchment beneath, a storm of knowledge made manifest`,
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

async function generateSkill(s) {
  const outPath = path.join(OUT_DIR, `${s.id}.png`);
  if (fs.existsSync(outPath) && !regenSet.has(s.id)) {
    console.log(`✓ ${s.id} — exists, skipping`);
    return;
  }
  console.log(`🎨 Generating ${s.id}…`);

  const resp = await postJSON(
    "https://api.minimax.io/v1/image_generation",
    { Authorization: `Bearer ${API_KEY}` },
    {
      model: "image-01",
      prompt: s.prompt,
      aspect_ratio: "1:1",
      response_format: "url",
      n: 1,
    }
  );

  const imageUrl = resp?.data?.image_urls?.[0] || resp?.data?.[0]?.url || resp?.images?.[0]?.url;
  if (!imageUrl) throw new Error(`No URL in response: ${JSON.stringify(resp).slice(0, 300)}`);

  await downloadBinary(imageUrl, outPath);
  console.log(`✓ ${s.id} → skill-art/${s.id}.png`);
}

(async () => {
  const failures = [];
  for (const s of SKILLS) {
    try {
      await generateSkill(s);
    } catch (e) {
      console.error(`✗ ${s.id}: ${e.message}`);
      failures.push(s.id);
    }
  }
  if (failures.length) {
    console.log(`\nFailed: ${failures.join(", ")}`);
    console.log(`Retry: node gen-skill-art.cjs --regen ${failures.join(",")}`);
  } else {
    console.log("\nAll done. Run: python3 build.py");
  }
})();
