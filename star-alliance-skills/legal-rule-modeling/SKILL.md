---
name: legal-rule-modeling
description: "The Architect's craft for modelling a governing law into the exact calculation rules and inputs a public legal calculator must honour — the 'Model the Law' step of tool-forge. Read the law (e.g. Egyptian wage tax, social insurance, severance, inheritance/mawarith, feddan/kirat land, customs); extract the computation — brackets, rates, caps, floors, rounding, edge cases, exemptions — into a deterministic inputs → computation → output model the Developer can implement without re-reading the statute; cite the article behind each rule; flag every ambiguity for the team-review disclaimer. Use before building any legal calculator or corporate tool. Triggers: 'model the law for this calculator', 'extract the calculation rules', 'what are the brackets for X', 'rule model for the tool'. Differentiate from transactions-domain-model (the app's money model) and codex-law-translate (translating the law's text, not its arithmetic)."
metadata:
  version: 1.0.0
type: Skill

---
# Legal Rule Modeling — the Architect's craft

A legal calculator is only as honest as its rule model. Your craft turns a statute — its brackets, rates, caps, floors, and dusty edge cases — into a deterministic spec the Developer can transcribe into code without ever re-reading the original Arabic text. You are the cartographer of arithmetic. Miss a boundary and the public trusts a number that betrays them; misread a rate and a worker loses a month's wages. The model is the spine of the tool. Break it and the whole tool-forge collapses downstream.

## What it is / is not

- **It IS:** a pure-function specification of a statute as `inputs → computation → output`, with every constant, bracket edge, exemption, and rounding rule cited to an article number and flagged for review.
- **It IS NOT:** `codex-law-translate` — the Translator renders the law's prose into 6 locales (AR/EN/FR/ES/RU/ZH); you model its arithmetic. The two are siblings, never the same.
- **It IS NOT:** `transactions-domain-model` — the Merchant's domain is money movement, ledger entries, and reconciliation inside the Lex Council app. Yours is external public law expressed as deterministic computation.
- **It IS NOT:** legal advice, opinion, or interpretation beyond what the statute's plain text and authoritative commentaries support. When a discretionary call exists, you flag it — you do not resolve it.

## The craft

Follow this order, in this order. Do not skip ahead.

1. **Identify the statute and the calculator's surface.** Confirm the governing law (Egyptian Labour Law 12/2003, Income Tax Law 91/2005, Social Insurance Law 148/2019, Personal Status Law 462/1955, Customs Law 66/1970, etc.), its effective date, and which version applies. A wage-tax calculator for 2024 cannot silently inherit 2020 brackets. Note the version in the model header.

2. **Read the law end-to-end before you write a line.** The Translator may have produced a structured glossary at `lex-council/codex/<locale>/<statute>/glossary.json`. Use it as a vocabulary anchor; do not let it pre-decide your arithmetic. Read the canonical Arabic source yourself. Skim, then re-read the chapters that govern computation.

3. **Enumerate every input.** For an Egyptian wage-tax model: gross monthly wage, tax-exempt allowances (Art. 6 schedule), social insurance employee share (9% per Law 148/2019), personal exemption (Art. 13), and any variable deductions. For mawarith: heirs list with their categories (Art. 3 of Law 462/1955 and amendments) and the residue. For feddan/kirat land area: input unit, precision, governorate (the qirat denominator varies). Write each input as a typed field with units, source article, and a `nullable` flag.

4. **Extract the computation into named stages.** Bracket tables become ordered `stages`: compute `taxable_base = gross - exempt - employee_insurance`, then look up the bracket in the schedule, then apply the marginal rate, then add the cumulative tax of all lower brackets. Each stage names a function, its inputs, and its output type. No stage may read a constant that is not in the constants table.

5. **Pin every constant with its article.** `0.09` is not 9% — it is "employee social insurance contribution, 9%, Art. 2 of Law 148/2019, as amended by Law 25/2020." If a constant has no article, it has no place in the model. Every constant lives in `constants[]` with `value`, `article`, `source_url`, `effective_from`.

6. **Enumerate every boundary.** Bracket floors and ceilings, the minimum wage floor (currently EGP 3,500 under the 2023 National Wages Council resolution), the personal-exemption cap, the maximum insurable wage (Art. 5 of Law 148/2019, reset periodically by ministerial decree). For each, state: inclusive or exclusive, and the test value. A calculator that mishandles `bracket_floor ≤ x < bracket_ceiling` is worse than no calculator.

7. **Specify rounding and currency.** EGP to two decimal places, half-up — but the statute may mandate truncation for certain levies. Cite the rounding rule or note its absence. The model owns this; the UI may not impose its own.

8. **List exemptions and edge cases explicitly.** Old-age exemption thresholds, foreign-resident carve-outs, the mawarith cases where the residue collapses to zero, the `awl` and `radd` redistributions, land-measurement conversions where the qirat denominator changes by governorate. Each gets a row in `edge_cases[]` with its own citation and an expected behaviour.

9. **Flag every ambiguity as `REVIEW_REQUIRED`.** "Reasonable," "as determined by the Minister," "subject to Council approval" — every discretionary phrase produces a `discretion_points[]` entry with the exact text and article. The Herald's disclaimer copy is generated from this list; the Developer may not hard-code a default.

10. **Shape the spec for implementation.** The final artefact is `lex-council/calculators/<calc_id>/model.md` plus a structured `model.json`: `inputs[]`, `stages[]`, `constants[]`, `boundaries[]`, `edge_cases[]`, `discretion_points[]`, `output` with its own citation. The Developer must be able to read `model.json` and write the function — without opening the statute. If they need to, the model has failed.

## Sharpening the craft

This trade deepens by confronting the difference between reading a law and computing it.

- **Apprentice move:** Produce a model for a single, clean bracket statute (the 2024 personal-income-tax schedule). You will miss a cap. The miss is the lesson — annotate the bug in the model's changelog so the next apprentice does not repeat it.
- **Journeyman move:** Model a statute with one genuine ambiguity — Law 148/2019 social insurance, where the maximum insurable wage is set by periodic ministerial decree rather than the statute itself. Learn to separate the static rule from the variable constant, and to wire the variable to a `decrees[]` table with an `effective_from` cursor. Stale constants are the most common production bug in the fleet; this is where you learn to prevent them at the model layer.
- **Master move:** Model inheritance (mawarith) under the 1955 Personal Status Law as amended. The arithmetic is the easy part; the `awl` and `radd` redistribution cases, the disappearing `asl`, and the category-mask logic are where the rule model reveals its shape. A master leaves behind not just a working spec but a test-fixture corpus: 64 cases covering every heirdom topology, each with a hand-computed expected output and the article chain that justifies it.

**Measure your growth** by three counters kept in the model header: `boundaries_covered`, `boundaries_total` (your own audit pass), `discretion_points_resolved`, `discretion_points_open`. A model with open discretions is not shippable; a model that quietly resolved them is dishonest. The counters force honesty and surface drift between versions.

**Failure modes to outgrow:** silently rounding away piasters; treating the personal-exemption cap as a flat subtraction instead of a tapered schedule; reading "exempt from tax" as "exempt from social insurance"; importing last year's bracket table because the new one was "similar"; letting the Translator's glossary pre-commit you to a reading before you read the article yourself.

## Gotchas

- **Amendments, not original statutes.** Most Egyptian labour and tax rules live in amendments, not the parent law. The article you cite must be the live one. Run a citation check against the latest Official Gazette entry; the Translator's glossary will lag.
- **Ministerial decrees.** Caps that move with the minimum wage or with an annual ministerial resolution must be modelled as a `variable` with `effective_from` and `source_decree_url`, never as a baked constant. A baked constant is a future outage.
- **Inclusive vs exclusive boundaries.** A bracket that ends at EGP 40,000 inclusive vs exclusive is the difference between a 14% and a 22% marginal rate on the boundary wage. State it. Test it. Never "off by one" a boundary.
- **Negative or zero outputs.** A mawarith model can produce a zero residue; a wage-tax model on a low-income input can floor at zero. Specify whether the output is `0` or a structured `{ value: 0, notes: [...] }` so the front-end can explain the result rather than display a confusing zero.
- **Double-counting exemptions.** The personal exemption (Art. 13) and the social-insurance deduction both subtract from gross. The bracket table assumes an order; reorder them and the result shifts. Lock the order in the spec; let the Developer only rearrange when the model is updated and re-reviewed.
- **Locale-shaped numbers.** Arabic locale input may use Eastern Arabic digits (٠١٢٣). The model is unit-agnostic about digits but unit-strict about currency and precision. Note it in the Developer handoff so the Designer can pair the input mask correctly.
- **The gate rule.** The Architect (a Claude model, opus/sonnet) reviews the model against the statute before a Claude subagent (spawned via the Task tool) drafts the calculator UI. Nothing ships unreviewed. A public calculator is a public claim; the claim is yours to underwrite.

## Versioning
Own skill. Bump `metadata.version` on any change (PATCH: wording/refs · MINOR: new mode/section · MAJOR: method contract change). Regenerate `VERSIONS.md` with `python3 star-alliance-skills/skillsmith/scripts/skill_registry.py write` after a bump, then `python3 build.py`.

## Changelog
- **1.0.0** — Initial release. The Architect's craft for modelling a law into deterministic calculator rules (brackets, caps, edge cases).
