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
    id: "check-point-resched",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "watch-where-you-step",
    prompt: `${STYLE}. A single armored boot hovering one inch above a cracked obsidian floor veined with glowing gold cascading cracks that radiate outward toward a distant precipice; the boot is mid-step, suspended, the cracks unfurling beneath like a frozen ripple, a faint parchment scroll with FK-relationship runes pinned at the boot's ankle, dramatic shaft of light from above illuminating the cracks but not the dark abyss ahead, tension between advance and warning, no text, no watermarks`,
  },
  {
    id: "prove-it",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "butler-onboarding",
    prompt: `${STYLE}. A half-open ornate gate flanked by two warm lantern flames, three gilded parchment scroll-cards fanned on a velvet cushion at the threshold inviting a traveler in, soft golden light spilling through the gap, no text, no watermarks`,
  },
  {
    id: "pattern-detector",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "Reads the seven most recent Lex Council housekeeping run logs plus the current OPEN-ITEMS.md an", no text, no watermarks`,
  },
  {
    id: "heat-map-analyst",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "Ranks Lex Council docs under lex_council/docs/ by claude_hits delta over the last 30 days a", no text, no watermarks`,
  },
  {
    id: "health-checker",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "Runs three read-only Supabase health queries (missing FK indexes, public tables without RLS, hi", no text, no watermarks`,
  },
  {
    id: "frontend-auditor",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "Diffs the Lex Council Next.js codebase (pages, mutations, hooks, stores) against FRONTEND-INVEN", no text, no watermarks`,
  },
  {
    id: "cold-doc-rotator",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "Picks the N Lex Council docs with the oldest last_housekeeper_pass frontmatter field (treatin", no text, no watermarks`,
  },
  {
    id: "backend-auditor",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "Audits the Lex Council Supabase schema (tables, views, triggers, RPC functions, cron jobs, RLS", no text, no watermarks`,
  },
  {
    id: "head-of-department",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "The thin authority-and-limits layer that sits between a worker and a sub-tree.", no text, no watermarks`,
  },
  {
    id: "temporal-coupling-audit",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "new-member-onboarding",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "The exact checklist to run whenever a new guild member is recruited.", no text, no watermarks`,
  },
  {
    id: "hotspot-radar",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "daily-stock-analysis",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "AI-powered daily stock analysis for A-share HK US JP KR markets generating a structured Decisio", no text, no watermarks`,
  },
  {
    id: "cognitive-bias-guard",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "code-unity",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "The Developer's and Architect's code-unity guardian — enforce ONE source of truth for every typ", no text, no watermarks`,
  },
  {
    id: "code-crime-scene",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "bug-fix-closer",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "Mark one or more Lex Council bug_reports rows as Fixed (br_status=4) in the DB.", no text, no watermarks`,
  },
  {
    id: "view-registry",
    prompt: `${STYLE}. A heavy leather-bound codex with a golden eye clasp, glowing typed registry page listing three view names, a magnifying glass hovering over a Supabase scroll, no text, no watermarks`,
  },
  {
    id: "bundled-rls",
    prompt: `${STYLE}. A medieval tower shield with an interlocking padlock and three glowing rune-stones set into its face, each stone a different named bundle, a faint blue initplan sigil glowing at the shield's core, no text, no watermarks`,
  },
  {
    id: "vault-log-writer",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "stitch-design-taste",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "redesign-existing-projects",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "phased-db-refactor",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "obedience",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "minimalist-ui",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "lex-system-audit",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "industrial-brutalist-ui",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "high-end-visual-design",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "gpt-taste",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "file-access-model",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "dual-model-review",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "The dual-review flow that backs the cross-system bridge.", no text, no watermarks`,
  },
  {
    id: "design-taste-frontend",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "admin-page-fixer",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "admin-page-builder",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "add-new-view",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "End-to-end procedure for creating or revising a view in the Lex Council Supabase backend.", no text, no watermarks`,
  },
  {
    id: "add-new-trigger",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "End-to-end procedure for creating or modifying a database trigger and its backing function in t", no text, no watermarks`,
  },
  {
    id: "add-admin-permission",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "", no text, no watermarks`,
  },
  {
    id: "decompose-and-swarm",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "The Butler's swarm craft — judge whether a task is worth parallelising, scout the codebase surf", no text, no watermarks`,
  },
  {
    id: "design-tokens",
    prompt: `${STYLE}. A master architect's emblem on dark aged leather: a three-tiered ziggurat of glowing enchanted gemstones — a broad base row of raw uncut crystals (the primitive palette), a middle row of cut and named gems linked by fine gold filigree threads (the semantic layer), and a small crowning row set into tiny carved component-sockets — one vertical seam splits the whole structure into a sunlit light-theme half and a moonlit dark-theme half, the same gem positions glowing in mirrored tones, a faint OKLCH color-wheel halo behind it and gold rune-brackets framing the tiers, the craft of one ordered source of color powering every surface, no text, no watermarks`,
  },
  {
    id: "a11y-craft",
    prompt: `${STYLE}. A guardian's emblem on dark aged leather: a radiant all-seeing eye set within a circular gold rune-ring, its iris split clean down the middle into a high-contrast black half and a luminous white half, beams of golden light passing through an ornate gate beneath it that only well-formed sigils may cross, a small carved figure with arms outstretched (the universal-access mark) glowing at the gate's center, faint keyboard-key runes and a focus-ring of gold light orbiting the eye, the craft of proving every surface is usable by all before it ships, no text, no watermarks`,
  },
  {
    id: "price-action",
    prompt: `${STYLE}. A master tape-reader's parchment on dark aged leather: a single luminous golden price-line flowing across it in clear market structure — a strong rising impulse leg, a shallow pullback, then another impulse, resolving into a balanced sideways trading range bounded by two glowing horizontal rails, with a breakout arrow piercing one rail at the right edge — beneath the line two opposing currents of tiny gold and shadow arrows (buyers vs sellers) showing the order-flow imbalance, a brass spyglass and a balance-scale weighing the two sides, faint runic glyphs framing the regimes — the read-only craft of reading the shifting balance written in the bars, no text, no watermarks`,
  },
  {
    id: "voices-check",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "A skill for integrating an agent's competing internal sub-voices into one coherent response ins", no text, no watermarks`,
  },
  {
    id: "chart-patterns",
    prompt: `${STYLE}. A master chartist's parchment on dark aged leather: a single glowing golden price-line carving the unmistakable silhouettes of classic chart patterns across it — a head-and-shoulders crest, a double-top twin-peak, a coiling symmetrical triangle, and a breakout flag on its pole — a brass drafting compass and straight-edge measuring a pattern's height to project a dotted golden measure-rule target arrow, faint red-and-green candlestick bars and a small volume histogram along the base, arcane geometry glyphs framing the formations — the read-only craft of naming the shapes the crowd's hope and fear carve into price, no text, no watermarks`,
  },
  {
    id: "metamorphosis-check",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "A guardrail skill that catches the single most dangerous agent failure: confidently running the", no text, no watermarks`,
  },
  {
    id: "letting-go",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "A universal guardrail skill that kills retry-storms, perfectionism paralysis, and over-delibera", no text, no watermarks`,
  },
  {
    id: "guild-reflection",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "The Quartermaster's self-improvement engine — turn finished work into durable guild upgrades th", no text, no watermarks`,
  },
  {
    id: "probability-statistics",
    prompt: `${STYLE}. A merchant-sage's table of chance on dark parchment: a pair of glowing golden dice mid-roll, a luminous bell-curve (normal distribution) arcing in gold light above a row of histogram bars, a brass scale weighing a frequentist coin against a Bayesian prior-scroll, scattered data-points resolving into a fitted trend-line, arcane probability glyphs (Σ, integral signs, a P-value seal) orbiting the scene — the read-only craft of reasoning rigorously about uncertainty, never a trade in sight`,
  },
  {
    id: "invariant-inference",
    prompt: `${STYLE}. A master diviner's rule-forging ritual on dark parchment: two sorted heaps of glowing gemstones — emerald-green "good" examples on the left, ember-red "bad" examples on the right — and a single luminous golden boundary-line being conjured between them that perfectly separates the two, an oracle's all-seeing eye floating above casting a probing beam that finds one stray counterexample (a red gem on the wrong side) which a feedback-arc loops back to redraw the line tighter, arcane logic-glyphs and a brass set-square framing the law being learned — the craft of inferring the rule that must always hold`,
  },
  {
    id: "spec-driven-development",
    prompt: `${STYLE}. A master architect's grand glowing blueprint-scroll unfurled on dark parchment, the scroll itself transforming left-to-right into a built stone fortress as the eye travels along it (a sealed spec-scroll → a drafting compass and plan → a checklist of stacked task-tablets → a finished citadel tower), four ornate golden gate-arches spaced along the path each sealed with a runic checkmark seal that the work must pass through, a quill and a brass set-square crossed at the base over a foundation stone — the discipline of building from the spec, never from the gut`,
  },
  {
    id: "python-master",
    prompt: `${STYLE}. A great emerald-and-gold serpent (python) coiled protectively around a master smith's anvil on dark parchment, its scales etched with glowing runic code-glyphs, a forge-hammer and an open blueprint-scroll of interlocking modular gears resting on the anvil, fourteen tiny golden craft-sigils orbiting the coil like a constellation (a flask for tests, a quill for docs, a shield for security, a gear for tooling), a sealed package crate stamped with gold wax at the base — the master craft of forging flawless Python`,
  },
  {
    id: "volume-price-analysis",
    prompt: `${STYLE}. A towering set of glowing golden volume bars rising beneath a row of carved red-and-green candlestick bars on dark parchment, a great brass balance-scale at center weighing "effort" (a heavy volume bar) against "result" (a price candle) with one pan tipping to reveal a hidden cloaked insider figure pulling strings below the chart, a horizontal volume-at-price histogram glowing along the right edge — the art of reading what the smart money cannot hide`,
  },
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
    id: "design-unity",
    prompt: `${STYLE}. A single luminous master seal-stone at the center radiating golden threads of light to many smaller surface-panels arranged in a perfect grid around it, every panel snapping into alignment and glowing the same hue as the central seal, one canonical rune-tablet beneath casting its law upward — the art of one source of truth holding every surface in one language`,
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
    id: "imagegen-frontend",
    prompt: `${STYLE}. A grand arcane viewing portal framed in carved stone beside a glowing rectangular arcane tablet and a gilded heraldic identity shield, all three conjuring vivid fantasy interface artwork and a brand crest from swirling violet and teal summoning energy, web of glowing threads radiating outward — a triune device for web portals, handheld screens, and brand identity`,
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
    id: "invariant-inference",
    prompt: `${STYLE}. A master diviner's table where two sorted heaps of glowing rune-stones — emerald "good" stones on the left, crimson "bad" stones on the right — are separated by a single luminous golden boundary-line conjured mid-air, an arcane lens forging a brand-new predicate-rune to split a stubborn pair the existing runes could not, a loop of counterexample-lightning arcing back from a judging scrying-eye to refine the line, the proven rule sealed in a hovering crystal — the art of learning a hidden law from examples and proving it true`,
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
  {
    id: "safe-agentic-orchestration",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden conductor's baton crossed over a layered org-chart of glowing sword-nodes, each rank tethered by gold command-lines into one disciplined formation, a spec-scroll gate and a sealed QAS checkmark guarding the flow into a final human-merge rune — the craft of marshalling many agents into one verifiable team, no text, no watermarks`,
  },
  {
    id: "agent-web-reach",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden globe pierced by a sword whose blade unspools into a dozen reaching tendrils — each tipped with a tiny platform sigil (play-button, bird, alien, feed-waves) drawing glowing content back through a brass cookie-key past a shattered 403 wall — the craft of giving an agent reach across the whole web, no text, no watermarks`,
  },
  {
    id: "agentic-video-production",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden film clapperboard whose strip becomes a flowing timeline of glowing keyframes — research scroll, script page, asset shards, edit blade, and a final rendered frame — gated by small brass checkpoints between each stage, reels of retrieved b-roll stacked beside it — the craft of producing finished video agentically from a plain brief, no text, no watermarks`,
  },
  {
    id: "timeseries-forecasting",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a glowing golden time-series line marching across parchment then extending into the future as a forecast, flanked by a softly-shaded quantile prediction-band fanning outward, a brass sundial-compass marking the context window and the horizon, faint covariate threads feeding in from the side — the read-only craft of projecting one series forward with calibrated uncertainty, no text, no watermarks`,
  },
  {
    id: "multimodal-model-wrappers",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a single golden sword-hilt socket into which many different model-blades (text, eye, sound-wave, film-frame, vector-lattice) all plug through one shared collar, normalized into one luminous output stream — the craft of one stable call-surface over many providers and modalities, no text, no watermarks`,
  },
  {
    id: "system-prompt-design-patterns",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a master's prompt-scroll unfurled, its sections carved as glowing golden bands — identity crest, capability ledger, tool-use rune, a refusal shield-wall, a persona mask — a sword laid across it warding off a tangle of red jailbreak-serpents at the margin — the meta-craft of designing a strong system prompt, no text, no watermarks`,
  },
  {
    id: "cn-market-strategy-pack",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden Eastern dragon coiling around a candlestick chart, its body tracing a trend then a reversal, four strategy-seals (trend, reversal, theme, chan-wave) glowing at the corners, a brass abacus and a fanned deck of strategy-scrolls below — the Merchant's read-only pack of fifteen market strategies, never a trade in sight, no text, no watermarks`,
  },
  {
    id: "pattern-library-discovery",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden card-catalog cabinet of glowing pattern-tablets sorted into seven labelled drawers (api, ci, config, database, security, testing, ui), a sword-shaped index-key drawing one proven tablet out into the light while a faint ghost of reinvention dissolves — the craft of capturing and reusing battle-tested patterns, no text, no watermarks`,
  },
  {
    id: "dev-ops-command-pack",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden circular lifecycle-gear of stations — start, pre-PR shield, deploy rocket, health pulse, rollback hook, retro lens — a sword as the gate-lever that can halt the ring at any checkpoint, twin dev/remote rails mirrored beneath — the craft of a disciplined, reversible dev-ops loop, no text, no watermarks`,
  },
  {
    id: "codebase-memory-mcp",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a vast glowing golden knowledge-graph of a codebase — function-nodes and class-nodes wired by call-chain edges and HTTP-route threads — a sword-shaped query-probe lighting one path through the lattice while greyed-out dead-code nodes crumble at the edge, a small brass index-engine humming at the root — the craft of querying a repo as one fast structural graph, no text, no watermarks`,
  },
  {
    id: "penpot-design-platform",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: an open design-platform canvas of glowing golden boards and component-symbols built from clean open-SVG vector paths, native design-token swatches ranged along the side, a sword-stylus driving an MCP-thread that inspects and generates a board, a small plugin-puzzle sigil docked at the frame — the craft of driving the open-source Penpot platform and its MCP, no text, no watermarks`,
  },
  {
    id: "automated-testing",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden testing pyramid of glowing glass vials — broad unit base, component middle, a single E2E capstone — a sword-probe striking each tier green while a red flaky-test crack is sealed shut, a brass coverage-gauge at the base — the craft of proving code works before it ships, no text, no watermarks`,
  },
  {
    id: "frontend-react-engineering",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a glowing golden atom whose electron-orbits are nested component-boundaries, a server-shard and client-shard split by a luminous seam, hooks threaded as orbital rings, a sword forging a clean component from the design handoff — the craft of production React engineering, no text, no watermarks`,
  },
  {
    id: "code-review-craft",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden magnifier-lens crossed with a sword passing over a scroll of code-diff lines, each flagged finding tagged by a small severity-rune (red/amber/grey) and pinned to its exact line, nitpick-noise swept off the margin — the craft of the deliberate evidenced code review, no text, no watermarks`,
  },
  {
    id: "observability-incident-response",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden heartbeat-trace pulsing across a dark ops-board of log/metric/trace dials, an alert-klaxon flaring as a sword steadies a faltering pulse back to green, a runbook-scroll and a calm post-mortem lens beside it — the craft of run-time visibility and live-failure response, no text, no watermarks`,
  },
  {
    id: "api-integration-design",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: two golden systems joined by a glowing sword-shaped connector, a versioned contract-scroll between them, webhook-bolts arcing across with signature-seals, a circuit-breaker rune and a backoff-spring guarding the seam — the craft of the API and integration boundary, no text, no watermarks`,
  },
  {
    id: "contract-review",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden contract-scroll under a sword-stylus drawing red redline strokes through one-sided clauses, a brass risk-scale weighing indemnity against liability, a flagged missing-clause gap glowing at the margin, a certify-seal left unsigned for a human hand — the advisory craft of inbound contract review, no text, no watermarks`,
  },
  {
    id: "financial-data-reach",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden data-aqueduct carrying glowing streams of price-candles, filing-scrolls, and macro-series into a clean reservoir, a brass as-of dial guarding against look-ahead leakage, a sword filtering noise from signal — the read-only craft of acquiring and cleaning market data, never a trade in sight, no text, no watermarks`,
  },
  {
    id: "data-analysis-viz",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden dataset resolving from a raw scattered grid into clean histogram bars, a trend-line, and a comparison chart, a sword-rule enforcing honest axis-zero, chart-junk swept away, a narrative-scroll summarizing the finding — the craft of exploratory data analysis and honest visualization, no text, no watermarks`,
  },
  {
    id: "ux-research",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden microscope over a cluster of user-figures, sticky-note findings rising into an affinity-map and a journey-map ribbon, a persona-mask and a severity-dial beside it, a sword separating real evidence from guesswork — the Designer's craft of learning from real users, no text, no watermarks`,
  },
  {
    id: "ux-copywriting",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden quill inscribing crisp words onto UI chips — a button label, an error toast, an empty-state line — a sword trimming a bloated sentence to its sharp core, a small screen-reader rune blessing the copy as accessible — the craft of the smallest unit of product writing, no text, no watermarks`,
  },
  {
    id: "butler-onboarding",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden open door framed by a sword, beyond it the guild's roster and workflow-banners arrayed as a welcoming hall, three glowing starter-prompt scrolls offered on a tray to a hesitant newcomer — the Butler's craft of the open door, no text, no watermarks`,
  },
  {
    id: "negotiation-deal-strategy",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: two golden hands clasping over a deal-table, a sword laid flat as the agreed line, a BATNA-anchor and a ZOPA-band glowing beneath, a concession-ladder and a sealed deal-memo to the side — the Herald's advisory craft of the negotiated deal, never a signature given, no text, no watermarks`,
  },
  {
    id: "workflow-runner",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden control-console with a glowing play-lever, a star-map workflow-scroll feeding through it step by step — script-cogs, prose-quills, and a halting approval-gate rune — a run-summary scroll spooling out the bottom, a sword as the master lever — the Quartermaster craft of running the guild own machinery, no text, no watermarks`,
  },
  {
    id: "leaders-command",
    prompt: `${STYLE}. A Fallen-Sword emblem on dark aged leather: a golden commander baton crossed over a crisp single-line order-scroll sealed with a wax sigil, the Guild Master spoken words above resolving into one sharp arrow of intent passed down to a waiting blade, terse runes marking order-intent-context-constraints-contract, every excess word burned away — the Butler craft of the clear precise command, no text, no watermarks`,
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
