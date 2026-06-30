---
title: Choosing the Chart
type: reference
skill: data-analysis-viz
---
# Let the question pick the chart

The chart is the answer to a question, not decoration on a number. There are only a handful of question shapes; each has a fitting chart family. Name the shape, then choose the encoding. Picking a chart you like and forcing the data into it is the root of most bad visuals.

## The map: question shape → chart family

### Distribution — "what does this single variable look like?"
*How is it spread? Where's the center? Are there outliers, gaps, multiple modes?*
- **Histogram** — continuous, one variable; bin width matters, try a few.
- **Box plot / violin** — compare a distribution across a few categories; box shows median + IQR + outliers, violin adds shape.
- **ECDF (cumulative)** — when percentiles/thresholds matter ("what share is under 5 min"); bin-free, honest about the whole distribution.
- **Avoid:** a single bar of the mean — it throws away the entire distribution.

### Comparison — "how do these categories rank against each other?"
*Which is biggest? How do groups differ on one measure?*
- **Bar chart, horizontal, sorted by value** — the default for nominal categories, especially with long labels or many bars. Sorting *is* the insight.
- **Grouped bar** — one extra dimension (metric × category), kept to 2-3 series before it clutters.
- **Dot / lollipop plot** — many categories or when a zero-baseline bar wastes space but you still want honest position.
- **Avoid:** vertical bars with rotated unreadable labels; rainbow color when the bars already encode the category by position.

### Trend — "how does this change over time?"
*Rising, falling, seasonal, a step change?*
- **Line chart** — the default for a continuous series over time; multiple lines for a few series.
- **Small multiples (faceted lines)** — when comparing the *shape* of several series; one panel each beats a tangle of overlaid lines.
- **Area chart** — only for a single cumulative/volume series, or stacked area for composition-over-time (and only with few, ordered bands).
- **Avoid:** a line chart on a *categorical* x-axis (line implies continuity between points that have no order); a bar chart for a long dense time series.

### Relationship — "how do two variables move together?"
*Correlated? Clustered? Is there an outlier driving it?*
- **Scatter plot** — two numeric variables; add a fit/trend line **only when a relationship is genuinely present**, never reflexively.
- **Bubble** — a third numeric variable as size, used sparingly (area, not radius, encodes value).
- **Heatmap** — two categorical (or binned) dimensions with a value; good for crosstabs and correlation matrices.
- **Avoid:** connecting scatter points with a line; reading causation from a fitted slope.

### Composition — "what are the parts of the whole?"
*Share of total, and how the mix shifts.*
- **Stacked bar** — parts of a whole across a few categories or time buckets.
- **100%-stacked bar** — when the *share* matters more than the absolute total.
- **Treemap** — many parts in a hierarchy where rough relative size is the point.
- **Pie** — acceptable only for **2-3 slices** of a true part-of-whole; beyond that, humans can't compare the angles — use a sorted bar.
- **Avoid:** pie charts with 6+ slices, nested donuts, any 3-D pie.

## Quick-decision table

| You want to show… | Reach for | Not |
|---|---|---|
| spread of one variable | histogram / ECDF / box | single mean bar |
| ranking of categories | sorted horizontal bar | pie |
| change over time | line / small multiples | bar soup, categorical-x line |
| two variables relating | scatter (+ fit if real) | connected scatter |
| part-of-whole | stacked / 100%-stacked bar | many-slice pie |
| where the aggregate hides a split | small multiples / grouped bar | one aggregate number |

## Common mismatches to catch

- **Pie abuse** — more than three slices; switch to a sorted bar so the eye can compare lengths, not angles.
- **Line on categorical x** — implies a trend through unordered categories; use bars.
- **Dual y-axes** — two series on two differently-scaled axes can be made to "correlate" by choosing the scales; almost always a trap. Prefer two stacked panels sharing the x-axis, or index both series to 100 at a base point.
- **Too many overlaid lines** — past ~4-5 series a single line chart is a hairball; facet into small multiples.
- **Chart for a single number** — if the answer is one figure, a big labeled number with its denominator beats any chart.

When the shape is clear, hand the *honesty* of the chosen chart to `honest-visualization.md` before you render it.
