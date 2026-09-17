# Design note, post hoc: Tables II and III with twenty seeds per slice and the ablation of the search

Written on 2026-09-16 at 10:59 UTC, **before** running `tools/fifteen_k20.py` and
`tools/ablation_search.py`. **It is post hoc with respect to the frozen paper**: already known were
all the numbers of `evidence/fifteen.csv` (one seed per slice), the median spread between runs of
1.31 mm on PHerc0125 z 6891 (`evidence/search-noise.csv`), the pre-registered verdicts (P1, P2, C1,
C2 won) and the referee's objection: with that spread the margins of 0.41 and 0.80 mm over the
centroid are inside the noise of the search. No number at twenty seeds had been computed.

## What does not change

The slices (the 24 heights per scroll of the frozen tables), the metric (`bench.errors`, median over the
control points inside the common coverage), the baseline (centroid of the filled mask, level 3,
the bench's own heights), the control (constant axis), the threshold of 0.30 mm and the four
criteria of `preregistration-fifteen-references.md`, which are applied as written.

## What changes

For every slice the estimate is made with **twenty seeds**: `20260915 + z + 1000·k`, k = 0..19, so
that k = 0 is exactly the seed of the frozen tables and the row at k = 0 must reproduce
`fifteen.csv` (known reference). For every seed k the polyline of the 24 estimates is built and
scored on the control points: out of it comes one median per seed, `m_k`. Per scroll and variant
the following are reported:

- **median** of the twenty `m_k` (it is the number that enters the verdicts);
- **IQR** of the twenty `m_k`;
- **95 % interval of the median**, percentile bootstrap with **1000 resamples**, seed of the
  generator **20260916** written in the CSV. One resample: for every slice one of the twenty
  estimates of that slice is drawn at random (with replacement), the polyline is built, the control
  points are drawn with replacement, the median is taken. This way the interval contains both the
  noise of the search and the sampling of the control points.
- **margin against the centroid** = median of the centroid minus the median of the estimator, with
  its interval (the centroid is deterministic and stays fixed in the resampling; its interval over
  the control points is reported separately), and the column that says whether the interval of the
  margin **includes zero** and whether it includes the threshold of 0.30 mm.

The verdicts are applied to the medians over the twenty seeds. If a verdict changes with respect to
the frozen one, the paper says that it changed and why; the pre-registration is not touched.

## The four cells of the ablation (Section III-C, today with no numbers)

Same slices, same twenty seeds, same score:
  (a) published: weighted mean and villa's search (cpp:78-142, seed from the unweighted sum, best
      updated inside the 3x3 loop, walk without bounds);
  (b) division alone removed: weighted sum and villa's search;
  (c) search rewritten with the mean (float64, search confined to the bounding box, eight probes
      from a fixed centre and the step halved if none improves, one objective only);
  (d) search rewritten with the sum: as (c) with the sum objective.
Column (b) of `ablation-search.csv` must coincide with `fifteen-k20.csv`: they are the same
computation done by two different instruments. If it does not coincide, one of the two is wrong.

## Prediction, written now

The intervals of the margins below 1 mm of the primary block (PHerc0125 0.80 and PHerc0332 0.41 in
`fifteen.csv`) **include zero**; the margin of PHerc0211 (1.37) and the defeat on PHerc0826 (minus
1.02) do not. The verdicts P1 and C1 stay won (they are counts of "better than the published one",
and the published one lies tens or hundreds of millimetres away). P2 and C2: **neither won nor
lost** is the outcome I expect for P2 if one of the three margins falls below 0.30; C2 stays won.
For the ablation: (c) and (d) are not better than (b) in the median on more than 8 scrolls out of
15, in line with the sentence of III-C.
