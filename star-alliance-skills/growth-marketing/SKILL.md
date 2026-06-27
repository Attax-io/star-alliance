---
name: growth-marketing
description: "The Herald's marketing craft — turn a business's invisibility into a repeatable demand engine across four modes. content-seo: ICP + pain keywords, topic clusters, local SEO, on-page, publish via article-creator. brand-positioning: positioning statement, ICP, value prop, voice, proof bank, hand off to brandkit. email-nurture: lead magnets, capture, a 4-6 email sequence, re-engagement, bar-compliance. social-paid: channel mix, organic cadence, a paid-ads starter, retargeting, tracking. Tuned for legal-services and other trust-led professional businesses; composes with storm-investigation for audience and market research. Triggers: 'plan our marketing', 'we need leads', 'fix our positioning', 'content plan', 'SEO plan', 'build an email sequence', 'social plan', 'ad plan', 'go to market', 'growth marketing', 'demand gen'."
metadata:
  version: 1.0.0
type: Skill

---
# Growth Marketing — the Herald's craft
Turns a legal-services business's invisibility into a repeatable demand engine. Composes with **article-creator** (publish long-form), **brandkit** (visuals and identity), and **storm-investigation** (ICP, market, competitor research). One skill, four modes — pick one, ship the artifact, measure.

## When to run which mode

| Mode | Trigger | Produces |
|---|---|---|
| `content-seo` | "We need organic leads" / new practice area / low site traffic | Topic cluster + briefs + on-page checklist + 90-day publish plan |
| `brand-positioning` | "Our messaging is fuzzy" / launching a new firm / rebrand | Positioning statement, ICP profile, voice guide, proof bank, brandkit handoff |
| `email-nurture` | "We get leads but they don't convert" / new lead magnet / slow pipeline | Lead magnet brief + capture plan + 4–6 email sequence + compliance checklist |
| `social-paid` | "We need distribution now" / stalled organic / new market | Organic cadence + repurposing system + paid-ads starter (search + social) + tracking plan |

## Mode 1 — content-seo
Inbound engine for legal services. A potential client Googles "do I have a wrongful termination case in [county]" — you want to be the answer.

1. **Lock the ICP and jurisdiction.** Use `storm-investigation` to pull: practice areas with real demand, the client type (individual vs. SMB vs. GC), and the geographic reach (city, county, state, multi-state bar). A solo family-law attorney in Travis County is not the same ICP as a B2B IP firm in NYC. Write it down: *"We serve [persona] in [place] facing [problem] who want [outcome]."*
2. **Mine pain keywords, not vanity keywords.** Skip "lawyer" and "attorney" head terms (CPC $50–$500, dominated by aggregators). Target long-tail pain: *"can my employer do X," "how long does divorce take in [state]," "do I need an estate plan if I'm single."* Use Google's "People Also Ask," Avvo question data, Reddit r/legaladvice, and bar-association consumer guides. Group into 3–5 topic clusters per practice area.
3. **Build the cluster map.** For each practice area: 1 pillar page (e.g., "Employment Law for Texas Employees") + 8–12 supporting articles answering specific questions. Every supporting post links back to the pillar and to the relevant practice-area page with a clear CTA (consultation booking, phone, form).
4. **Lock the on-page basics.** One H1 with the primary query, meta description under 155 chars with action verb, schema markup (`LegalService` + `FAQPage` + `Attorney`), internal links, and a consultation CTA above the fold on every practice-area page. Local signals: embed a Google Map, list service areas by city, add bar admission and jurisdiction in the footer.
5. **Own local SEO.** Claim and complete Google Business Profile for every office location: categories (e.g., "Divorce Lawyer," "Estate Planning Attorney"), service areas, hours, photos, weekly Google Posts. Build citations on Avvo, Justia, FindLaw, Martindale-Hubbell, Yelp, and the local bar directory. NAP (name, address, phone) must match exactly across every listing.
6. **Hand off to `article-creator` and ship.** Each cluster article becomes a brief → draft → publish cycle. One article per week minimum; two if the firm has bandwidth. Republish older posts quarterly with fresh dates and updated info.
7. **Measure what matters.** Track: organic sessions per practice-area page, keyword rankings for the 10–20 money terms, consultation form submissions attributed to organic, cost-per-lead by cluster. Ignore vanity traffic. If a cluster produces zero consultation requests in 90 days, kill it and pick a new angle.
8. **Respect the bar rules.** No guarantees ("we'll win your case"), no misleading claims, no client testimonials where state rules prohibit them, "Attorney Advertising" disclaimer where required, and clear attorney-vs.-firm identification on every page.

**OUTPUT artifact:** `content-seo-plan.md` — ICP + jurisdiction, pain keyword list grouped by cluster, cluster map (pillar + 8–12 supports per practice area), on-page checklist, local SEO task list, 90-day publishing calendar with handoff notes to `article-creator`.

## Mode 2 — brand-positioning
Make the firm unmistakable. Two attorneys can both do "estate planning in Austin" — positioning is why the phone rings for *you*.

1. **Pull the research.** Use `storm-investigation` for: top 5 local competitors' positioning lines, review sites for language clients actually use, the firm's own case history (without client names) for repeatable wins, partner credentials and niches. Also pull the founder's story — why this firm exists.
2. **Write the positioning statement.** One sentence, four slots: *"For [ICP] in [jurisdiction/industry] who [pain], [firm name] is the [category] that [key benefit] because [proof]."* Example: *"For tech startups in Texas raising their Series A, Lex Council is the corporate counsel that ships closing docs in 72 hours because we've closed 140+ founder-friendly rounds."* Reject vague lines like "trusted advisors" and "client-focused."
3. **Define the ICP profile in detail.** Demographics, psychographics, the moment they search for a lawyer, the prior solution they tried, the fear they carry, the outcome they measure. Build 2–3 personas max; one is enough for a solo firm.
4. **Articulate the value prop in three layers.** Headline (one line), sub-headline (one sentence expanding the benefit), proof points (3–5 bullets: case results, bar admissions, peer ratings, publications, years of practice). Strip legalese.
5. **Lock the voice.** Pick 3–4 voice attributes (e.g., "plainspoken, calm, direct, never snide") and 3 anti-attributes (e.g., "no Latin unless defined, no chest-thumping, no 'warrior' metaphors"). Write 5 example do/don't pairs covering website copy, social, and email.
6. **Build the proof bank.** A single document listing: case results (anonymized where required), settlements and verdicts, bar admissions and certifications, peer ratings (Avvo, Martindale, Super Lawyers), speaking engagements, media mentions, pro bono work, attorney bios with credentials. This is the raw material every mode downstream will draw from.
7. **Hand off to `brandkit`.** Positioning statement + voice guide + proof bank becomes the input for visual identity: logo, palette, typography, photography direction, templates for proposals, decks, email signatures, and social cards. The brandkit skill produces these; the Herald defines what they must say.
8. **Audit the existing surface.** Website, Google Business Profile, LinkedIn, Avvo, directory listings, email signature, letterhead. Rewrite every bio, headline, and "About" section to match the new positioning. Consistency compounds.

**OUTPUT artifact:** `brand-positioning-kit.md` — positioning statement, ICP profiles, value prop (3 layers), voice guide with do/don't examples, proof bank, handoff brief for `brandkit`, and an audit checklist of every surface to update.

## Mode 3 — email-nurture
Convert leads without being pushy. Legal buyers move slowly — they're scared, comparing, and shopping trust as much as competence.

1. **Build a lead magnet worth downloading.** Legal lead magnets that convert: state-specific checklists ("Texas divorce: 14 documents to gather before you file"), calculators ("How much will my Chapter 7 cost in [state]?"), recorded 20-minute webinars on a hot topic, downloadable guides ("The founder's pre-Series A legal checklist"), and free case evaluations. Skip generic "10 tips" PDFs — they don't build trust.
2. **Capture cleanly.** One form, one offer per page. Fields: name, email, and only the question you actually need (e.g., "What type of case?"). Use a CRM that supports tagging by practice area (HubSpot free tier, MailerLite, ConvertKit, or a legal-specific CRM like Clio Grow). Confirm the opt-in with a single, well-formatted welcome email that delivers the magnet and sets expectations.
3. **Draft the welcome/nurture sequence (4–6 emails over 14–21 days).**
   - **Email 1 (immediate):** Deliver the lead magnet, restate what the firm does in 2 lines, set the cadence ("I'll send 4 short emails over the next 2 weeks").
   - **Email 2 (Day 3):** One real story or anonymized case result illustrating the firm's approach. No names if confidentiality requires; "[Client case #47]" is fine.
   - **Email 3 (Day 6):** Bust the top 3 myths in the practice area (e.g., "Myth: my spouse will get half everything in a Texas divorce").
   - **Email 4 (Day 10):** The firm's process, in plain language. What happens after the first call, what it costs, how long it takes. Kill the unknown.
   - **Email 5 (Day 14):** Proof roundup — bar admissions, peer ratings, a press mention, a recent verdict. No client testimonials if your state bars them.
   - **Email 6 (Day 18–21):** The soft CTA: book a 15-minute consultation, with two specific time slots, a plain-language description of what the call covers, and an honest note that there's no obligation.
4. **Set the long-game cadence.** After the welcome sequence: 1 email every 2–3 weeks — practice-area updates, plain-English explainers, firm news, and the occasional seasonal CTA (tax season, open enrollment, year-end estate planning). Cap at 2 per month; legal audiences unsubscribe fast.
5. **Build a re-engagement branch.** If a lead opens nothing in 60 days, send a single "Still the right time?" email with a clear unsubscribe path. Suppress non-openers after 90 days of inactivity. Cold leads are not the same as warm ones.
6. **Mind the compliance.** CAN-SPAM basics: real physical address, working unsubscribe, honest subject lines. State bar rules: no guarantees, no fee-splitting language, identify attorneys and jurisdictions. Confidentiality: never reference a real case in marketing email without consent. Add "Attorney Advertising" where required. Store consent records in the CRM.
7. **Measure.** Open rate (target 35%+ on welcome sequence), click rate, consultation bookings attributed to email (UTM tags), and unsubscribe rate (cap at 0.5% per send). One sequence can run for years — refresh the proof and the CTAs quarterly.

**OUTPUT artifact:** `email-nurture-plan.md` — lead magnet brief, capture page copy, 4–6 email sequence with subject lines and full body, long-game cadence, re-engagement branch, compliance checklist, and measurement plan.

## Mode 4 — social-paid
Get the firm's name in front of the right people this week, not this quarter.

1. **Pick the channel mix by ICP.** For B2B legal (corporate, IP, employment for employers, regulatory): LinkedIn-led, X/Twitter secondary, no Facebook. For consumer legal (family, PI, estate, criminal defense): Google Business Profile + Facebook + Instagram Reels + YouTube Shorts. For local service legal: Google Business Profile + Nextdoor + Facebook community groups. Start with one; add a second only when the first is steady.
2. **Build the organic cadence (3–5 posts/week).** Mix: 40% educational (plain-English explainers, "what to do if X"), 30% proof (case results, awards, bar admissions — framed as the firm's standard, not chest-thumping), 20% behind-the-scenes (the team, the office, the process, "this week in court"), 10% soft CTA (consultation slots, lead magnet, event). Repurpose one `content-seo` article into 4–6 social posts. Use `brandkit` templates for every card.
3. **The LinkedIn formula for lawyers.** One founder or rainmaker posts 3x/week: a 150-word personal take on a legal development (new case law, regulatory change, common client mistake), with a single-line CTA. Comments on other lawyers' and journalists' posts daily, in voice. This is the highest-ROI channel for B2B legal and beats paid ads for trust-building.
4. **The paid-ads starter.** Start with Google Search ads on 5–10 high-intent terms per practice area (e.g., "divorce attorney [city]," "DUI lawyer near me," "wrongful termination lawyer [county]"). Use exact and phrase match; tight negative keyword list. Budget tiers: $500/mo = test, $1,500/mo = real signal, $5,000+/mo = scale. Layer Meta ads (Facebook/Instagram) only for consumer practice areas with strong visual proof — $300–$1,000/mo to retarget site visitors and video viewers. Skip LinkedIn ads until the firm has a defined B2B ICP and a $1,500+/mo budget.
5. **Build the retargeting loop.** Every landing page has Meta Pixel + Google Tag + LinkedIn Insight Tag. Retarget three audiences: (a) visited practice-area page but no consultation, (b) downloaded lead magnet but no booking, (c) watched 50%+ of a video. One ad creative per audience, refreshed every 6 weeks to fight fatigue.
6. **Creative from `brandkit`.** Every ad uses the firm's templates: same color, same typography, same photography style. Test 3 hooks per audience: a question, a stat, a short story. Rotate winners monthly.
7. **Track to revenue.** UTM every link. Connect CRM consultation data to ad platform conversions. Report weekly: cost per consultation booked, cost per signed engagement, and the practice area that produced each. Pause any keyword or creative that produces consultations that don't sign within 60 days.
8. **Stay compliant on every channel.** Ad disclaimers where state bars require, no guarantees of outcomes, no client-identifying info, "Attorney Advertising" labels on LinkedIn ads in required states. Keep records of every ad creative for the bar's recordkeeping window.

**OUTPUT artifact:** `social-paid-plan.md` — channel mix by ICP, 30-day organic calendar, paid-ads starter (keyword set, ad copy for 3 hooks, budget tier recommendation), retargeting audience definitions, measurement plan, compliance checklist.

## Principles
- **Trust beats reach.** A law firm's brand is built one credible answer at a time. 500 right-fit leads beat 50,000 strangers.
- **The bar rules apply to every channel.** Every word in every mode is subject to state bar advertising rules. When in doubt, check the jurisdiction's professional conduct rules and keep the file.
- **Local + niche beats generic.** "Estate planning attorney for tech founders in Austin" is a strategy. "Attorney" is a label.
- **Measure CAC and LTV by practice area.** Some legal work is high-value (corporate, PI, employment defense) and absorbs high acquisition cost. Some (uncontested divorce, simple wills) is low-margin and needs volume and automation. Spend accordingly.
- **One channel mastered beats five half-run.** Pick the channel where the ICP actually spends time, post weekly for 90 days, then add the second.
- **Content compounds.** A 2024 article still ranking in 2026 is paying for itself. Paid stops the moment the budget does; organic keeps paying.
- **Confidentiality is a marketing constraint and a marketing asset.** Tell anonymized stories well, and the firm's discretion becomes a selling point.

## How the Herald works
1. **Research first.** Run `storm-investigation` to pull ICP, competitor positioning, market demand, and proof material. No mode runs blind.
2. **Pick the mode.** Match the firm's current bottleneck: no traffic → `content-seo`; fuzzy messaging → `brand-positioning`; leads that don't convert → `email-nurture`; needs distribution now → `social-paid`. Run one mode per sprint.
3. **Produce the artifact.** Each mode outputs a single markdown artifact (named in the OUTPUT line) that the firm can execute against. No vague strategy decks.
4. **Hand off the work that isn't this skill's job.** Long-form publishing → `article-creator` with the content-seo brief. Visuals, templates, identity → `brandkit` with the brand-positioning handoff. Audience research → `storm-investigation` upfront.
5. **Ship the artifact, then ship the work it prescribes.** A positioning statement that never reaches the website is theater. A content plan that never publishes is a wish.
6. **Measure and iterate.** After 30, 60, and 90 days: review the metrics in each artifact's measurement section, kill what isn't working, double down on what is, and rerun the relevant mode. The Herald is a loop, not a deliverable.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. The Herald's four-mode marketing hub (content-seo, brand-positioning, email-nurture, social-paid), tuned for legal-services and trust-led professional businesses; composes with article-creator, brandkit, and storm-investigation.
