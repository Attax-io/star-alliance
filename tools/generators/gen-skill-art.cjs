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

const OUT_DIR = path.join(__dirname, "..", "..", "skill-art");
fs.mkdirSync(OUT_DIR, { recursive: true });

// Parse --regen flag
const regenArg = process.argv.indexOf("--regen");
const regenSet = new Set(regenArg !== -1 ? process.argv[regenArg + 1].split(",") : []);

const STYLE = "fantasy RPG skill icon, Fallen Sword MMORPG style, dark parchment background with aged leather texture, gold runic border, ornate medieval frame, dramatic lighting, rich saturated colors, detailed pixel-art-adjacent illustration, 48x48 icon style, pure black outer border";

const SKILLS = [
  {
    id: "algorithmic-trading-chan",
    prompt: `${STYLE}. An ancient quant's grimoire open on dark parchment, a glowing golden pendulum swinging back toward a marked equilibrium line on the left page (mean reversion) while a soaring golden arrow trends upward across the right page (momentum), a row of carved candlestick bars etched in gold along the bottom, arcane equations and a balanced brass scale weighing risk in the margin — the master trader's tome of why strategies win`,
  },
  {
    id: "harness-efficiency",
    prompt: `${STYLE}. An ornate brass measuring gauge mounted on dark parchment, its needle swinging toward a glowing golden surplus, twin scales weighing a heavy stack of spent gold coins against a far larger hoard saved, a ledger scroll of glowing sigils beside it tallying what was spent versus what was conserved — the instrument that proves the treasury grows`,
  },
  {
    id: "claude-code-hooks",
    prompt: `${STYLE}. A glowing arcane gate-rune carved into a stone archway, an enchanted iron hook hanging from a chain across the threshold, a stream of magical sigils flowing toward the gate where the hook catches and judges each one — some passing through in green light, one halted in red — the warden-rune that inspects all who pass`,
  },
  {
    id: "schema-evolution",
    prompt: `${STYLE}. An ancient blueprint scroll of a citadel growing a new wing, golden architectural lines extending the existing structure without disturbing the old stone, a glowing branching crystal lattice adding a new facet while every existing facet stays intact, the art of growing a foundation without cracking it`,
  },
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
    id: "dev-server",
    prompt: `${STYLE}. A glowing arcane server tower built of stacked magical crystals, each crystal pulsing with different colored light, ethereal cables of light connecting them, a small green power gem at top`,
  },
  {
    id: "design-language",
    prompt: `${STYLE}. Three ancient open tomes arranged in a fan, each inscribed in a different glowing script — dark-fantasy Erildath runes, the guild's star-forged glyphs, and a council's formal seal-script — a single luminous quill weaving a thread of light between all three, the art of giving each world its own tongue`,
  },
  {
    id: "motion-design",
    prompt: `${STYLE}. An enchanted pendulum of polished brass swinging in a long arcing trail of golden light, its motion-curve traced as a glowing ease-out spline across dark parchment, sand-timer grains streaming in measured cadence beside it, faint after-images marking the rhythm of perfect timing — the art of giving movement its exact curve and beat`,
  },
  {
    id: "full-output-enforcement",
    prompt: `${STYLE}. A massive tower shield of impenetrable dark steel, embossed with three vertical roman numerals in gold, a large central boss radiating authority, shield wall aura of silver force energy`,
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
    id: "obsidian-markdown",
    prompt: `${STYLE}. A razor-sharp obsidian crystal shard, black volcanic glass with purple arcane veins glowing within, a glowing hash rune carved into its face, floating above a dark altar`,
  },
  {
    id: "performance",
    prompt: `${STYLE}. A golden lightning bolt crackling with pure electric speed energy, motion blur streaks behind it, small thunderclouds parting, the bolt etched with acceleration runes, pure kinetic power`,
  },
  {
    id: "skillsmith",
    prompt: `${STYLE}. A dwarven anvil with a glowing skill rune being hammered into a weapon, forge sparks of orange arcane fire flying, the hammer embossed with a gear symbol, craftsmanship and creation`,
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
  {
    id: "weapon-utility",
    prompt: `${STYLE}. An ornate weapon rack mounted on dark stone, a row of distinct enchanted blades arranged by priority from left to right, the leftmost blades glowing AMBER-GOLD as the chosen doers, a tall glowing VIOLET runed staff at the right as the thinker directing them, a thread of light running from the staff to the drawn blade as the mind commanding the hand, a small balanced selection-rune hovering before the rack, disciplined armory order`,
  },
  {
    id: "members-formation",
    prompt: `${STYLE}. A grand commander's war table seen from above, an aged parchment battle map with a glowing golden compass rose at its center, carved chess-like guild pieces arranged in a deliberate formation, branching routes of light splitting into two parallel columns on one side and a single-file relay column on the other, ornate runic gate-arches marking checkpoints along the routes, a gloved hand poised to set a piece into place, command and disciplined order made manifest`,
  },
  {
    id: "ultra-brainstorming",
    prompt: `${STYLE}. Five glowing orbs of arcane thought arranged in a council circle, each a different burning color holding its own mind, brilliant threads of insight streaming from all five and weaving together into one radiant master-plan scroll at the center, scattered contradiction-sparks resolving into harmony where the threads converge, a constellation of merging ideas hovering above an open strategist's planning table, many minds fused into a single design`,
  },
  {
    id: "design-taste",
    prompt: `${STYLE}. A master engraver's palette with seven glowing wells of arcane paint each a distinct archetype hue, a gold-tipped brush selecting one, a ward of white light burning away cheap generic patterns, elegant runic layout-grids forming behind it, premium anti-slop taste engine`,
  },
  {
    id: "guild-conformity",
    prompt: `${STYLE}. A great golden scale of justice each pan bearing a glowing guild seal, a crystal magnifying lens hovering over an open parchment ledger, threads of light cross-checking matching runes between two tomes, a blazing green checkmark sigil where all aligns, audit made harmony`,
  },
  {
    id: "guild-sync",
    prompt: `${STYLE}. Two facing enchanted mirrors on dark parchment — a master tome of glowing golden runes on the left, its living reflection on the right — bound by a ring of circular arrows of light flowing between them keeping both in perfect step, a few stray runes on the reflection flaring red where they have fallen out of sync and a golden thread reaching out to draw them back into alignment, the art of keeping the copy true to the source`,
  },
  {
    id: "market-recon",
    prompt: `${STYLE}. A brass-and-crystal merchant's spyglass over an arcane market chart, glowing green and crimson candlestick bars rising across aged parchment, floating risk-runes and a balanced coin-scale, eyes-only reconnaissance of fortunes, observation not execution`,
  },
  {
    id: "japanese-candlesticks",
    prompt: `${STYLE}. A row of tall glowing green and crimson candlestick bars rendered as actual lit wax candles with flickering flames, casting amber light over an aged Japanese rice-merchant's chart scroll, a brushed sumi-e hammer and doji rune in the corner, an Edo-era folding fan and ink-brush beside coins, the ancient Far-Eastern art of reading price`,
  },
  {
    id: "legal-drafting",
    prompt: `${STYLE}. An ornate golden quill writing flowing bilingual script across twin parchment columns, right-to-left arcane Arabic runes on one side and Latin legal script on the other, a red wax seal and ribbon at the foot, ink glowing with the firm's authority, the scribe's craft of the law`,
  },
  {
    id: "relationship-intel",
    prompt: `${STYLE}. Two clasped gauntleted hands sealing a pact over a glowing web of letter-scrolls, threads of golden light linking portrait-lockets of contacts in a constellation, a scrying eye reading sentiment from each thread, intelligence woven from correspondence`,
  },
  {
    id: "release-train",
    prompt: `${STYLE}. An armored war-train of riveted dark steel forging down glowing rails into a unified citadel gate, many branch-tracks merging into one main line, a golden version-seal stamped on the lead car, banner of a shipped release whipping in the wind, the closing march`,
  },
  {
    id: "workflow-forge",
    prompt: `${STYLE}. A glowing star-map constellation on aged parchment with nodes of light linked into a named route, a cartographer's compass beside a smith's stamp pressing a finished pattern into the map, a single mythic workflow-sigil crystallizing from a remembered run`,
  },
  {
    id: "arsenal-forge",
    prompt: `${STYLE}. A dwarven forge-anvil arraying enchanted weapons by priority, amber-gold crossbow and blades as doers on the left and a tall violet runed staff as the thinker on the right, a new blade quenched in glowing rune-fire with a role-sigil branded on its pommel, the weaponsmith's recruitment`,
  },
  {
    id: "scheduled-watch",
    prompt: `${STYLE}. A sentinel's hourglass fused with a clockwork gear-tower standing watch on a dark rampart, glowing cron-runes orbiting the dial, a checkpoint-rune marking a safe resume point, a small lantern that relights itself each tick, the unattended vigil`,
  },
  {
    id: "law-harvest",
    prompt: `${STYLE}. A great shelf of ancient law-scrolls being gathered, a sickle of golden light reaping verbatim text from a glowing codex into a clean indexed tome, Arabic runes preserved intact on the canonical page, a verified seal stamped on the harvest, the gathering of statutes`,
  },
  {
    id: "comms-triage",
    prompt: `${STYLE}. A butler's silver salver bearing sorted glowing envelopes beneath a calendar-rune and a chat-glyph, three sorting portals labelled task event and draft drawing each message into its place, a held wax seal awaiting the master's approval, the orderly triage of the desk`,
  },
  {
    id: "legal-rule-modeling",
    prompt: `${STYLE}. An arcane abacus beside a chiseled stone tablet of law transmuting into a glowing deterministic formula, brackets rates and caps etched as runic gates, a calculator-crystal computing inputs into outputs, an article-citation sigil beside each rule, the law made arithmetic`,
  },
  {
    id: "high-alert",
    prompt: `${STYLE}. A blazing signal-beacon flaming atop a dark stone watchtower, golden-red alarm fire leaping skyward, a bronze war-horn and a swinging warning bell beside it, concentric red-gold alert rings radiating outward across the night, a herald's banner snapping in the wind, the whole guild roused to attention, urgent klaxon glow`,
  },
  {
    id: "okf",
    prompt: `${STYLE}. A GOLD enchanted broom-and-quill setting a scriptorium of leather-bound tomes into flawless order, each tome stamped with a glowing rune-label of its kind on the spine, threads of gold light cross-linking one tome to the next, a single concept inscribed per page, loose stray scrolls being swept into their proper shelf-slots, the Open Knowledge crest seal above, methodical scholarly hygiene and clean frontmatter`,
  },
  {
    id: "star-alliance-language",
    prompt: `${STYLE}. A hooded guild-reader at a lectern unrolling a luminous concept-map of an ordered library, glowing rune-labels and gold cross-link threads charting where each knowledge lives, only three tomes pulled open and softly lit while the rest rest shelved and dim, an eye-of-orientation sigil above guiding the gaze, swift cheap reliable reading with no blind full-read, the quiet reader's-protocol counterpart to the gold tidying crest`,
  },
  {
    id: "session-mining",
    prompt: `${STYLE}. A dwarven runesmith's pickaxe of glowing gold striking a deep vein of crystal memory-shards in a dark cavern wall, each struck shard floating up as a luminous scroll-fragment of a past chronicle, a set of scales beside the vein weighing the true shards against false ones — the dull already-known shards crumbling to dust while the rare new ones rise glowing, an arcane ledger open below catching the verified findings in gold ink, the craft of mining old chronicles for lessons and proving which still matter`,
  },
  {
    id: "portability-audit",
    prompt: `${STYLE}. A weathered cartographer's map unfurling across a stone table, six glowing rune-layers stacked above it like translucent strata — skills, members, arsenal tools, env vars, hooks, workflows — each layer either blazing gold-green where intact or cracked red where broken, a quill annotating gap markers in crimson ink beside a sealed travel chest ready for deployment, the craft of mapping what moves and what breaks before a guild deploys to new territory, no text, no watermarks`,
  },
  {
    id: "project-start",
    prompt: `${STYLE}. A guild sentinel standing at the gate of a new fortress at dawn, lantern raised to check a glowing checklist etched into the stonework — three runes lighting up green as the check passes: a shield rune for the root path, a sword-rack rune for skill versions, a banner rune for member presence — a sunrise breaking over the parapets behind, the craft of a fast dawn-check before the day's work begins, no text, no watermarks`,
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
