---
title: EDA Workflow
type: reference
skill: data-analysis-viz
---
# The exploratory-data-analysis pass

The arc from raw table to written finding. Run it in order; each stage feeds the next, and skipping the early ones is how a beautiful chart ends up lying.

## 1. Frame before you load

Name the decision the analysis serves and the question shape (distribution · comparison · trend · relationship · composition · open "what's here"). The frame decides which columns matter, which cuts to try, and which chart family you are heading toward. An analysis without a question produces a gallery, not an answer.

## 2. Profile — the mechanical first pass

Before any aggregation, profile every column. This is the single most-skipped, most-valuable step.

- **Shape:** row count, column count. Is this the n you expected?
- **Real type per column:** not the declared type. Numbers arriving as `"1,200"` or `"$4.50"`, dates as text, booleans as `Y/N/1/0/yes`. Coerce explicitly later; here, just *record the truth*.
- **Null rate per column:** count and percent. A 60%-null column is a different object than a clean one — it may be unusable or may itself be the signal.
- **Cardinality:** distinct count. Distinguishes a continuous measure from a low-cardinality category from a near-unique key. A "category" with 40k distinct values is probably an ID.
- **Range / extremes:** min, max, a few smallest and largest values. Surfaces impossible values (negative age, year 1900, $1e9 order) immediately.
- **Sample rows:** print 5-10 actual rows. Eyes catch encoding, delimiter, and header problems no summary will.

Output of this stage is a small profile table — one row per column — that the rest of the analysis is built on.

## 3. Validate — name the data-quality issues

From the profile, list concrete problems before deciding anything:

- **Missingness:** which columns, what rate, is it random or structured (one source/date range always null)?
- **Duplicates:** full-row dupes, and key-level dupes (two rows for the same supposed-unique id).
- **Impossible / out-of-range values:** negatives where impossible, future dates, percentages over 100, mismatched units (cm vs m, USD vs cents).
- **Inconsistent categories:** `"US" / "USA" / "United States"`, casing, whitespace, typos that fragment a real category.
- **Referential gaps:** foreign keys with no match, totals that don't reconcile to a known control figure.

## 4. Clean — on the record, reversibly

Resolve each validated issue with a *named decision* and an *affected-row count*, and keep the cleaned set distinguishable from the original.

- **Drop** rows only when the issue makes them unusable for the question, and report the share dropped.
- **Impute** only with a stated method (median, forward-fill, "Unknown" category) and flag imputed rows so they never masquerade as observed.
- **Coerce** types explicitly (strip `$`/commas → numeric, parse → date) and re-check the null rate after — a parse that silently fails inflates nulls.
- **Canonicalize** categories with an explicit mapping, not a fuzzy guess.

The cleaning log is part of the deliverable. "1,043/50,210 rows (2.1%) excluded for null region; kept in global totals" is the kind of line that lets a reader trust — or correctly distrust — every downstream chart.

## 5. Explore — find the shape

- **Univariate:** distribution of each key variable. Histogram/ECDF for continuous, value-counts/bar for categorical. Note skew, modality, outliers, and zero-inflation. This decides which summary statistic is honest (see the skill's principle 5).
- **Bivariate:** relationships between pairs. Scatter for numeric-numeric (correlation, but resist drawing a fit line until a relationship is real), grouped box/bar for numeric-categorical, crosstab/heatmap for categorical-categorical.
- **Multivariate / segmentation:** cut the headline metric by the meaningful dimension(s) — cohort, region, channel, time bucket. This is where most insight lives. Watch for **Simpson's paradox**: an aggregate trend that reverses once you condition on a group. The segmented view is frequently the finding; the aggregate hid it.
- **Time:** if there's a date, look at the series — trend, seasonality, level shifts, gaps. Aggregate to a sensible grain (don't plot 50k daily points when weekly tells the story).

## 6. Summarize honestly

For each reported number, pick the statistic the distribution earns and pair it with spread and denominator. Median + IQR for skewed/outlier-heavy; mean + SD for roughly symmetric; counts always with their rate and base. When the question is genuinely inferential — *is this difference real, what's the interval, does this fit a distribution* — hand to `probability-statistics` rather than eyeballing it.

## 7. Write the findings — the deliverable

A short narrative, not a chart dump:

1. **Takeaway** in one or two sentences — what the data shows, in plain language.
2. **The 2-4 charts that prove it**, each honest (see `honest-visualization.md`) and each carrying its takeaway in the title.
3. **Caveats** — small n, selection/survivorship bias, missing periods, correlation-not-causation, cleaning decisions that could swing the result.
4. **The decision number** — the single figure the choice turns on.
5. **Confidence** — Low / Med / High, with the one thing that would change it.

A **dashboard** is this same discipline made standing and refreshable: the same honest charts and summary stats, wired to re-run on new data, with the narrative compressed into titles and a short header. Build one only when the analysis genuinely recurs.
