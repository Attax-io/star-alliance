#!/usr/bin/env node
// Generates Fallen Sword-themed workflow art PNGs via MiniMax image API.
// Mirrors gen-skill-art.cjs — same style/forge, themed per Star Map workflow.
// Output: workflow-art/<id>.png   (1024² source, displayed 100x100 in the Star Map)
// Usage: node gen-workflow-art.cjs [--regen <id>,<id>...]

const fs = require("fs");
const path = require("path");
const https = require("https");

const KEY_PATH = path.join(process.env.HOME, ".config/minimax/m3.key");
const API_KEY = fs.readFileSync(KEY_PATH, "utf8").trim();

const OUT_DIR = path.join(__dirname, "..", "..", "workflow-art");
fs.mkdirSync(OUT_DIR, { recursive: true });

// Parse --regen flag
const regenArg = process.argv.indexOf("--regen");
const regenSet = new Set(regenArg !== -1 ? process.argv[regenArg + 1].split(",") : []);

// Same Fallen Sword aesthetic as the skill tiles, so workflows sit beside them.
const STYLE = "fantasy RPG skill icon, Fallen Sword MMORPG style, dark parchment background with aged leather texture, gold runic border, ornate medieval frame, dramatic lighting, rich saturated colors, detailed pixel-art-adjacent illustration, 48x48 icon style, pure black outer border";

const WORKFLOWS = [
  {
    id: "app-packaging",
    prompt: `${STYLE}. A master artificer's workbench on dark parchment: a finished glowing AMBER application-crystal being sealed inside an ornate runed reliquary-crate, a smaller sidecar casket latched alongside it, an enchanted anvil and gilded toolchain laid out, a wax guild-seal stamping the lid, the craft of scaffolding and packing a built app into one distributable shell`,
  },
  {
    id: "standard-mission",
    prompt: `${STYLE}. A grand celestial war-map carved on dark parchment, a glowing CYAN mission route winding through a constellation of stars, the guild banner planted at the center, runic waypoint markers at each stage, a coordinated multi-wave campaign mapped across the heavens`,
  },
  {
    id: "quick-fix",
    prompt: `${STYLE}. A single swift EMERALD-GREEN lightning bolt striking a small glowing crack in a stone rune and sealing it instantly, clean and precise, minimal sparks, speed and economy, one decisive strike`,
  },
  {
    id: "design-sprint",
    prompt: `${STYLE}. An artisan's enchanted paintbrush sweeping a glowing ROSE-PINK arc across a blank crystal canvas, a polished interface panel materializing within an ornate gilded frame, swatches of vivid magical color floating nearby, swift creative momentum`,
  },
  {
    id: "architecture-build",
    prompt: `${STYLE}. A glowing SAPPHIRE-BLUE architectural blueprint of a grand citadel etched on dark vellum, marble pillars and foundation stones rising from the plan, a mason's set-square and compass crossed over it, structural ley-lines pulsing with blue light, solid and exact`,
  },
  {
    id: "legal-codex",
    prompt: `${STYLE}. Golden scales of justice balanced above an open leather-bound codex, its two glowing pages inscribed in several different ancient scripts side by side, a gold wax seal of law stamped at the base, warm authoritative amber-gold light`,
  },
  {
    id: "market-recon",
    prompt: `${STYLE}. An enchanted brass spyglass trained on a glowing EMERALD-GREEN ascending market line charted among the stars, a scrying-orb reflecting risk runes, a merchant's ledger and stacked coins below, watchful intelligence, pure observation and no combat`,
  },
  {
    id: "skill-forge",
    prompt: `${STYLE}. A dwarven forge-anvil glowing with VIOLET arcane fire, a hammer striking a skill-rune into a gleaming blade, sparks of purple magic flying, a rack of sharpened enchanted tools behind it, craftsmanship keeping the arsenal current`,
  },
  {
    id: "guild-log-sync",
    prompt: `${STYLE}. A long unfurled GOLDEN guild scroll-ledger, an enchanted quill auto-writing rows of glowing entries to backfill blank lines, the guild crest seal at the top, missing records filling in with warm gold light, meticulous record-keeping`,
  },
  {
    id: "compliance-audit",
    prompt: `${STYLE}. Golden scales of perfect balance above a master guild-ledger, every glowing entry aligned in flawless rows, a polished mirror reflecting the guild crest in perfect symmetry, radiant GOLD rune-checkmarks of verification floating around the frame, the warm authoritative light of order and agreement, nothing out of place`,
  },
  {
    id: "bug-cycle",
    prompt: `${STYLE}. A glowing EMERALD-GREEN rune-beetle pinned and dispelled by a precise dagger of light, a corrupted crack in the stone sealing shut behind it, a small ledger of marks beside it, the hunt-and-close of a tracked corruption`,
  },
  {
    id: "security-sweep",
    prompt: `${STYLE}. A SAPPHIRE-BLUE warded shield wall over a vault door, glowing ward-runes scanning for cracks, a few breaches sealing with blue light, a vigilant defensive sweep across a fortress gate`,
  },
  {
    id: "okf-tidy",
    prompt: `${STYLE}. A GOLD enchanted broom-and-quill sweeping an aged repository of leather-bound tomes into perfect order, each tome stamped with a glowing rune-label of its kind on the spine, cross-link threads of gold light connecting them, the Open Knowledge crest seal above, methodical scholarly tidiness and clean frontmatter`,
  },
  {
    id: "cleanup-rotation",
    prompt: `${STYLE}. A VIOLET enchanted broom of light sweeping glowing debris and tangled threads off an aged parchment ledger, runes snapping into clean alignment, methodical housekeeping across many small modes`,
  },
  {
    id: "sync-rotation",
    prompt: `${STYLE}. Two facing arcane tomes on dark parchment bound by a glowing ring of VIOLET circular arrows flowing between them, a master ledger and its living mirror-copy held in perfect step, a few stray runes on the copy flaring red and a thread of violet light drawing them back into alignment, the closing rite that keeps the device true to the repo`,
  },
  {
    id: "release-train",
    prompt: `${STYLE}. A CYAN celestial locomotive of light hauling merged banner-branches into one bright main line, a version sigil stamped on its side, departing a station gate, a clean coordinated shipment`,
  },
  {
    id: "tool-forge",
    prompt: `${STYLE}. A GOLD ornate abacus-and-scales instrument forged on dark parchment, glowing numerals and legal glyphs orbiting it, a precise calculation device built from the letter of the law`,
  },
  {
    id: "legal-draft",
    prompt: `${STYLE}. A GOLD enchanted quill writing a bilingual legal instrument on aged vellum, twin columns of Arabic and Latin script glowing, a wax seal at the foot, formal correspondence in the firm's register`,
  },
  {
    id: "comms-triage",
    prompt: `${STYLE}. A CYAN constellation of glowing envelopes, calendar runes, and message orbs being sorted by a guiding hand into ordered task-cards, an inbox swept into clean order`,
  },
  {
    id: "scheduled-routine",
    prompt: `${STYLE}. A VIOLET astrolabe-clock of light ticking on dark parchment, a standing sentinel running an unattended watch on a cron orbit, checkpoint runes marking each safe tick`,
  },
  {
    id: "marketing-audit",
    prompt: `${STYLE}. A ROSE-PINK looking-glass sweeping over a glowing storefront banner and public square, beacon and megaphone runes, an audit of reputation, reach, and message truth`,
  },
  {
    id: "art-forge",
    prompt: `${STYLE}. A ROSE-PINK artisan's forge-anvil where a glowing portrait sigil is being struck into a gilded frame, sparks of vivid magical color, heraldic art being forged and reviewed`,
  },
  {
    id: "arsenal-forge",
    prompt: `${STYLE}. A SAPPHIRE-BLUE weapon-smith's anvil forging a glowing elemental weapon, a thinker/doer role-rune branded onto its hilt, the blade slotted into a rack of guild arms`,
  },
  {
    id: "strategic-audit",
    prompt: `${STYLE}. A VIOLET scrying orb ringed by five glowing council-flames converging into a single graded verdict-scroll, a multi-mind panel weighed and ranked into one judgement`,
  },
  {
    id: "swarm-panel",
    prompt: `${STYLE}. A swirling AMBER swarm of seven worker figures fanning out in radial spokes from a central glowing panel / round-table at the heart of the scene, each worker bearing a small task-scroll and a distinct subtle color sigil marking their own disjoint subtask, seam-contract ribbons of light binding the slices back to the central table, a coordinating Developer's hand at the hub guiding the fan-out, parallel motion and ordered convergence, no combat`,
  },
  {
    id: "harness-calibration",
    prompt: `${STYLE}. An AMBER guild instrument-bench with hook-levers, dial gauges, and a glowing measurement scroll, a technician's hand tuning a precision gear while efficiency-runes light up green one by one`,
  },
  {
    id: "workflow-forge",
    prompt: `${STYLE}. A CYAN celestial cartographer's table where a finished mission-route is being engraved as a new constellation onto the star map, a fresh workflow sigil set among the stars`,
  },
  {
    id: "relationship-intel",
    prompt: `${STYLE}. A GOLD web of glowing relationship-threads linking portrait medallions of contacts across dark parchment, a quill annotating character notes, a guardian eye watching for fraying bonds, commercial intelligence woven from correspondence`,
  },
  {
    id: "law-harvest",
    prompt: `${STYLE}. A GOLD harvest of scroll-laws gathered from a field of stacked tomes into an ordered library shelf, a sickle of light separating named from unnamed scrolls, verbatim glyphs extracted onto clean pages`,
  },
  {
    id: "web-oracle",
    prompt: `${STYLE}. A CYAN scrying-orb on a brass far-seer's stand piercing a glowing web of ley-lines that stretch beyond the known map, distant lights of far realms reflected in the glass, an open ledger beneath citing each vision with a runic source-mark, far-sight and verified knowledge drawn from the wider world`,
  },
  {
    id: "inquiry-recon",
    prompt: `${STYLE}. A TEAL enchanted magnifying lens held over the guild's own unrolled archive-map, a glowing teal pin marking one exact found location among rows of indexed runes, a hooded scout's gloved hand tracing a line of text, an open reference tome beneath with a single line lit and a source-mark beside it, quiet read-only reconnaissance of the guild's own records, no weapon drawn`,
  },
  {
    id: "conversation",
    prompt: `${STYLE}. A calm SLATE-GREY hearth-side parley scene, two empty carved chairs facing each other across a low rune-lit table, a single softly glowing speech-glyph hovering between them, the guild banner furled and at rest against the wall, no weapons present, quiet plain counsel and exchange of words`,
  },
  {
    id: "local-session",
    prompt: `${STYLE}. An INDIGO summoning-circle on dark parchment from which a spectral scout-hawk of glowing indigo light is dispatched toward the edge of the map and returns clutching a small sealed findings-scroll, a conjurer's rune-marked hand open beneath, a faint mirrored twin of the guild crest showing the session runs apart in isolation, quiet remote reconnaissance by a summoned familiar, no weapon drawn`,
  },
  {
    id: "reflective-cycle",
    prompt: `${STYLE}. An EMERALD-GREEN ouroboros ring of glowing runes circling an open guild-journal, a finished quest-scroll feeding into the loop and emerging as a single bright engraved doctrine-rune stamped onto a skill-tome, an enchanted quill writing the lesson down, the closing of a learning loop, no combat`,
  },
  {
    id: "guild-self-audit",
    prompt: `${STYLE}. An EMERALD-GREEN polished scrying-mirror reflecting the guild's own rack of skill-blades, a few dull rusted blades flagged with red runes for weeding while bright ones gleam, golden scales weighing member-crests for balance, an open ledger of retired-idea glyphs crossed out, calm self-examination and pruning, no enemy present`,
  },
  {
    id: "guild-recruitment",
    prompt: `${STYLE}. A Fallen-Sword guild-banner emblem on dark aged leather: a golden empty seat at a round war-table being filled by a new armored figure rising into the light, a recruitment-scroll listing three skill-runes and a single weapon-sigil beside a conformity-checkmark seal, a sword raised in oath — the rite of scaffolding a new guild member behind the gate, no text, no watermarks`,
  },
  {
    id: "routing",
    prompt: `${STYLE}. An INDIGO signpost-beacon on dark parchment at a crossroads, multiple glowing direction-arrows pointing to different colored workflow sigils (cyan for missions, rose for design, green for fixes, gold for legal), a robed Strategist-figure with a compass deciding which path to take, the guild banner planted at the center marking the start-point, a clear awaiting-choice scene — the intake gateway where work begins, no specialist yet engaged`,
  },
  {
    id: "star-alliance-deploy",
    prompt: `${STYLE}. A GOLDEN sealed manifest scroll bearing the Star Alliance crest being loaded onto a radiant merchant-vessel, glowing cargo crates of weaponized skills and lore being stacked on deck, a deployment-rune burnished into the hull, anchors lifting and the ship's sails catching celestial wind toward a distant harbor, the moment of grand release when the arsenal ships to the wider world`,
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

async function generateWorkflow(w) {
  const outPath = path.join(OUT_DIR, `${w.id}.png`);
  if (fs.existsSync(outPath) && !regenSet.has(w.id)) {
    console.log(`✓ ${w.id} — exists, skipping`);
    return;
  }
  console.log(`🎨 Generating ${w.id}…`);

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
  console.log(`✓ ${w.id} → workflow-art/${w.id}.png`);
}

(async () => {
  const failures = [];
  for (const w of WORKFLOWS) {
    try {
      await generateWorkflow(w);
    } catch (e) {
      console.error(`✗ ${w.id}: ${e.message}`);
      failures.push(w.id);
    }
  }
  if (failures.length) {
    console.log(`\nFailed: ${failures.join(", ")}`);
    console.log(`Retry: node gen-workflow-art.cjs --regen ${failures.join(",")}`);
  } else {
    console.log("\nAll done. Run: python3 build.py");
  }
})();
