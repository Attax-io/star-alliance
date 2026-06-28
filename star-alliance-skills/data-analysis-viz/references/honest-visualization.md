---
title: Honest Visualization
type: reference
skill: data-analysis-viz
---
# Honest visualization

A chart is an argument made of ink. It must not claim more than the data supports. The rules below are not stylistic preferences — they are the difference between informing and misleading. The default posture is *the chart says exactly what the data says, and no more*.

## Axis integrity

- **Bar charts start the value axis at zero.** A bar's length encodes magnitude; truncating the axis multiplies a small difference into a visual chasm. A 4%-vs-5% gap on an axis zoomed to 3.9-5.1 is a lie of scale. If a zero baseline genuinely flattens a meaningful difference, switch the encoding — a dot/lollipop plot honestly shows *position* without implying a length-from-zero.
- **Line and scatter axes may be truncated, but label the truncation.** Position-based encodings don't require zero, but a reader must be able to see the range. Mark a broken axis; never silently start at an arbitrary value to manufacture drama or calm.
- **One y-axis per chart by default.** Dual axes let you slide two scales until unrelated series appear to track — a classic deception. If you must compare two differently-scaled series, index both to 100 at a common base, or stack two panels sharing the x-axis.
- **Consistent scales across small multiples.** Faceted panels meant for comparison must share axes; independent per-panel scales make a small series look as big as a large one.
- **Linear unless log is justified and labeled.** A log axis is honest for multiplicative/wide-range data but must be announced — readers assume linear.

## Remove chart-junk

Chart-junk is any ink that adds no information. Strip it:
- No 3-D on anything — perspective distorts every length, area, and angle.
- No decorative gradients, drop shadows, textures, or heavy gridlines.
- No redundant encoding (color *and* legend *and* label *and* pattern all saying the one thing).
- No more decimal places than the data earns; round to the precision the measurement supports.
- Light or absent gridlines; let the data, not the frame, carry the visual weight.
- Direct-label series where you can instead of forcing a legend lookup.

The test (Tufte's data-ink ratio): if erasing a mark loses no information, erase it.

## Color with intent and accessibility

- **Match the scale to the variable.** *Sequential* (light→dark of one hue) for ordered magnitudes; *categorical* (distinct hues) for nominal groups; *diverging* (two hues around a neutral midpoint) only when there's a meaningful center (zero, a target, a baseline).
- **Encode one variable with color.** Don't let color carry meaning in one chart and pure decoration in the next.
- **Colorblind-safe by default.** ~8% of men can't separate red from green; use colorblind-safe palettes and never rely on red-vs-green alone to carry the message — add shape, label, or position.
- **Enough contrast, not more colors than needed.** Past ~6-7 categorical colors, hues stop being distinguishable; bucket, facet, or highlight-one-gray-the-rest instead.

## Labeling and annotation

- **Title states the takeaway, not the variables.** "Conversion fell 30% after the April redesign" beats "Conversion by month." The title is where the finding lives.
- **Axis labels with units**, always. A number without units is not a finding.
- **Show the n.** Every chart carries the sample it's drawn from; a striking pattern over 9 points is a different claim than over 9,000.
- **Annotate the point that matters** — the outlier, the inflection, the threshold — directly on the chart, so the reader's eye lands where the argument is.
- **Source and as-of date** when the data is external or time-sensitive.

## The misleading-chart catalogue — refuse these

- **Truncated bar axis** — exaggerates differences (see axis integrity).
- **Dual-axis correlation** — two scales tuned to fake a relationship.
- **Cherry-picked range** — a window chosen to show the trend you want; show enough context to be honest about it.
- **Cumulative/area used to hide a downturn** — a rising cumulative line can mask falling period-over-period values; plot the rate, not just the running total, when the rate is the question.
- **Aggregation that hides the split** — one bar averaging over groups that disagree; segment it (Simpson's paradox).
- **Area encoding radius instead of value** — in bubbles, doubling the radius quadruples the apparent size; scale by area.
- **Overplotting passed off as density** — 50k opaque overlapping points; use transparency, binning (hexbin), or sampling, and say which.
- **Pie with too many slices / 3-D pie** — angle comparison fails; use a sorted bar.
- **Spurious precision** — "47.3829%" from 12 samples implies certainty the data can't carry.

When a requested chart would mislead, propose the honest alternative and say why — the job is the truthful read, not the flattering one.
