---
name: dashboard-parity
description: "The Quartermaster's craft for proving a change actually reaches the rendered dashboard at index.html — not just the source files, but the generated guild-data.js the browser loads and the live DOM it paints. The dashboard is buildless: index.html loads guild-data.js (const GUILD), regenerated from source by build.py, so a change is done only when it survives that chain. This craft rebuilds, asserts the new value is in guild-data.js and the old value is gone, renders index.html on the local server, and confirms it shows in the live DOM via screenshot. Use after any edit that should appear on the dashboard — members, skills, workflows, domains, the guild log, the version, or any art. Triggers: 'is it on the dashboard', 'did it reflect on index.html', 'verify the dashboard', 'check the dashboard renders', 'dashboard parity', 'did the build land', 'did my change show up'. Differentiate from guild-conformity (source files agree with each other and the generated data) and cleanup (app/i18n hygiene)."
metadata:
  version: 1.1.0
type: Skill

---
# Dashboard Parity — the Quartermaster's craft

You are the keeper of the looking-glass. A change is not done when the source file is saved, nor when the build script exits zero — it is done when the Guild Master opens the dashboard and *sees it*. The dashboard is buildless: `index.html` loads `guild-data.js` (a top-level `const GUILD`), which `build.py` regenerates from the source files. Between a saved edit and a painted pixel sit four places a change can silently die. Your craft is to walk that whole chain and prove, with a rebuild, a file assertion, a DOM assertion, and a screenshot, that the looking-glass shows the truth.

## What it is / is not

- It IS: rebuild from source, assert the delta landed in `guild-data.js` (the file the browser actually loads), render `index.html` on the local server, and confirm the new value is in the live DOM and the old value is gone — closing with a screenshot.
- It is NOT: `guild-conformity` — that proves the *source files agree with each other* and that `guild-data.js == guild-data.json` (file-vs-file). This craft proves the *rendered page* agrees with the source (file-vs-DOM). Conformity is the precondition; parity is the last mile to the browser.
- It is NOT: `cleanup` — that is Lex Council app/i18n hygiene, a different codebase entirely.
- It is NOT: a build step or a generator. You orchestrate `build.py`; you never hand-edit `guild-data.js` / `guild-data.json`.

## The craft

1. **Name the delta first.** Before you build, write down exactly what should change on the dashboard and the literal string you'll recognise it by — `"name": "Brand Audit"` present / `"Marketing Recon"` gone; the Quartermaster's tile shows skill X; the brand mark reads vY. A parity check with no expected value is theatre.
2. **Rebuild from source.** `python3 build.py`. This regenerates both `guild-data.js` and `guild-data.json`. Never hand-edit either — the browser reads the generated `.js`; a hand-edit lies until the next build erases it. If you changed a source file and skipped this step, the dashboard is still showing the old data no matter how clean the diff looks.
3. **Assert in the file the browser loads.** `grep -c` the **new** value in `guild-data.js` (must be ≥1) and the **old** value (must be 0). Check `guild-data.js`, not only `guild-data.json` — `index.html` loads the `.js`; the `.json` is for non-browser consumers. They must match (that is conformity's parity check), but the `.js` is the one that ships.
4. **Render and assert in the DOM.** Start the dashboard server (`preview_start "dashboard"` — `autoPort` handles a port already taken by another session; never kill another chat's server). Reload the page after the rebuild — the buildless dashboard has no HMR, so a stale tab verifies the old bundle. `GUILD` is a module-scoped `const`, **not** a global, so do not read `window.GUILD` — read the rendered DOM: navigate to the view, then assert the new text is present and the old text absent via `preview_eval` / `preview_snapshot`.
5. **Prove it visually.** Resize to a real desktop width first (`1440×900`) — the headless viewport defaults to a ~20px sliver and screenshots come out as a thin black bar. Take one screenshot of the changed surface. For a tile or portrait, confirm the *image* loaded (the id-keyed PNG exists), not merely the label.
6. **Sweep the propagation failure modes** (see Gotchas) — the ways a change reaches the file but not the screen.
7. **Log and hand off.** Record what you verified — the delta, that it is in `guild-data.js`, that the DOM shows it, and the screenshot — so the Butler's report can claim *"reflected on the dashboard"* with proof, not hope.

## Headless render smoke-harness (crash-sweep before the browser)

The DOM check in step 4 proves *one* surface paints. But a data change can crash a *different*
renderer you didn't open — a member with a new field, a skill the card-builder chokes on. Before
spending a browser, run every renderer against all the data headlessly and catch the crash in
milliseconds. The harness is buildless, like the dashboard:

1. **Load the real code in a `vm`, with a DOM stub.** In a node script, build a minimal `document`
   stub (`createElement`/`querySelector`/`appendChild` returning chainable no-op nodes, an
   `innerHTML` setter), then `vm.runInNewContext` over `guild-data.js` + `app.js` so the *actual*
   renderers run, not a reimplementation. The point is to exercise shipped code.
2. **Inject the test inside the IIFE.** `app.js` wraps its renderers in an IIFE, so they aren't on
   the global object. Append your driver to the source *before* running it in the vm — call each
   renderer (`renderMembers`, `renderSkills`, `renderDomains`, …) over every member / skill / domain
   in `GUILD`, inside the same closure. Reaching them from outside is the part that doesn't work; the
   inject-inside trick is what makes it work.
3. **Assert no throw, per record.** Wrap each renderer call per-item so one bad record names itself
   (`renderSkill("schema-evolution") threw: …`) instead of aborting the sweep. Green = every renderer
   survived every record. This is the cheap gate you run *before* `preview_start`.

It does not replace the DOM-and-screenshot proof (step 4–5) — a renderer can run clean and still paint
wrong. It's the fast pre-filter that turns "open the browser and discover a crash" into "the harness
named the broken record in 200ms." Run it after `build.py`, before the visual pass.

## Sharpening the craft

You improve along four rungs, and your measure is the count of changes confirmed on-screen versus the ones you declared done that the Guild Master then could not see.

- **Apprentice — file-grepper.** You rebuild and grep `guild-data.js` for the new value. You stop at the file. You miss that "in the JSON" is not "on the screen", and you sometimes check `.json` while the browser loads `.js`. Measure: rebuild-before-claim rate. Outgrow: declaring done at the file.
- **Journeyman — DOM-prover.** You render `index.html` and assert against the live DOM, new-present and old-absent, with a desktop-sized screenshot. You reload after every build and you read the DOM, never `window.GUILD`. Measure: DOM-confirmed rate, stale-tab catches. Outgrow: trusting a screenshot you took at 20px wide.
- **Artisan — chain-warden.** You know every place a change dies between save and paint — skipped build, `.js`/`.json` split, id-keyed art going blank on a rename, browser cache. You add an assertion the moment a new failure mode bites once. Measure: propagation bugs caught pre-handoff, checks added. Outgrow: re-discovering the same failure twice.
- **Master — render-oracle.** You predict what will not propagate before you build it — "this renames the id, so the art tile goes blank until regenerated" — and you fix it in the same pass. The screenshot only ever confirms what you already knew. Measure: predicted-vs-surprised ratio, blank tiles shipped (must be zero). Outgrow: confidence without the shot.

Track, always: rebuild-before-claim rate, DOM-confirmed rate, blank/stale tiles shipped (must be zero), propagation failure modes caught before handoff.

## Gotchas

- **Edited the source, forgot `build.py`.** The single most common miss. `guild-data.js` is still old; the dashboard shows stale data while the source diff looks finished. Rebuild is always step one.
- **Verified `guild-data.json`, not `guild-data.js`.** The browser loads the `.js`. Assert against the file that ships.
- **`window.GUILD` is undefined.** `GUILD` is a top-level `const`, not a global. Assert against the rendered DOM, not the variable.
- **Sliver screenshots.** The headless viewport defaults to ~20px wide. Resize to `1440×900` before shooting or the image is a black bar.
- **Port 4178 already in use** by another session. Use `autoPort`; do not stop a server you did not start.
- **No HMR.** The buildless dashboard does not hot-reload. Reload the tab after a rebuild, or you verify the previous bundle.
- **Art is id-keyed** (`skill-art/<id>.png`, `workflow-art/<id>.png`, `member-art/<id>.png`). A *display-name* rename that keeps the id keeps the art; changing the *id* blanks the tile until art is regenerated. Verify the image, not just the label, on any rename.
- **New skill / member lags the data.** A `SKILL.md` or agent `.md` only appears after `build.py` rebuilds `guild-data`; a green file diff is not a green dashboard, and conformity's `K`/`N` checks will flag the gap until you rebuild.
- **"It's in the file" is not "it's on the screen."** The craft ends at the DOM and a screenshot, never at the source diff.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.1.0** — Added **§Headless render smoke-harness** — a buildless node+`vm` crash-sweep that loads the real `guild-data.js` + `app.js` over a DOM stub and runs every renderer against all members/skills/domains, catching a crash in any surface (not just the one you opened) in milliseconds before spending a browser. Documents the inject-the-driver-inside-the-IIFE trick (the renderers aren't global) and per-record assertion so a bad record names itself. The fast pre-filter ahead of the DOM-and-screenshot proof. New section → MINOR.
- **1.0.0** — Initial release. The Quartermaster's last-mile check: prove every change reaches the rendered dashboard at index.html — rebuild, assert in guild-data.js, confirm in the live DOM, screenshot.
