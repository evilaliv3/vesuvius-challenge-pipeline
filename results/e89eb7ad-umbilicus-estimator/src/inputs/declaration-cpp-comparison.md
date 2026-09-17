# Rule of the comparison of C++ against the transcription, written before any number of the comparison

Written on **2026-09-18 at 09:23 UTC** (the machine's clock, `date -u`), before running a single
estimate of the comparison and before looking at any row produced by the C++ on the fifteen tables.

**It is post hoc with respect to every pre-registration of this line of work**: when this rule is
written, already known are all the numbers of the Python transcription
(`evidence/fifteen-k20.csv`, `k20-estimates.csv`, `fifteen-k20-verdicts.json`), the four
pre-registered verdicts, the spread between runs (`evidence/search-noise.csv`), the behaviour of the
cap (`evidence/search-cap.csv`) and the twenty runs of the compiled binary on the four saved slices
(`evidence/cpp-runs.csv`). It is not a pre-registration and must not be read as one: it is a rule
fixed before running, so that it cannot be adjusted after the result has been seen.

It answers point 2 of the "maintainer's decision" list of PR 1823: reproduce the accuracy tables by
calling `align_and_extract_umbilicus` for real, instead of its transcription in Python.

## 0. One number has already been produced, and it is not one of the comparison

Before this rule I built the instrument (`vc_gen_umbilicus`) and checked it against a known
reference, `evidence/cpp-runs.csv`, on the only one of the four saved slices that also exists as a
`.grid` in the cache: PHerc0125 z 2140, 20 repetitions without a seed, the two variants.
Median of the instrument (5066.4, 2951.6) against (5079.8, 2961.1) of the existing bench for the
published version, and (5140.2, 3076.0) against (5126.8, 3074.4) for the weighted sum: 16.5 and 13.5
grid units, that is 0.15 and 0.13 mm at 9.362 um, inside the spread of the generator, which on this
slice is declared to be up to 4.52 mm. **This is a check on the instrument and not a number of the
comparison**, and it is written here because it was produced before this rule and not after.

## 1. What does not change

Nothing of the chain of measurement, except the arm that produces the coordinates.

* The slices: the 24 heights per scroll the frozen files were measured on, unchanged.
* The seeds, as numbers: `20260915 + z + 1000 k`, k from 0 to 19. See point 3 however.
* The two variants: the function as it stands at the commit (weighted mean, "as-is") and the same
  with the division alone removed (weighted sum, "no-division").
* The metric, the baselines, the threshold of 0.30 mm, the four criteria, the bootstrap interval and
  its seeds: **the same code is used**, `tools/fifteen_k20.score` and `tools/fifteen_k20.verdict`,
  without copying it and without rewriting it. Only the file of estimates it is fed changes.

## 2. What changes

Only this: the `x`, `y` coordinates of every estimate come from `align_and_extract_umbilicus`
compiled from the sources of the branch, called from
`volume-cartographer/apps/src/vc_gen_umbilicus.cpp`, instead of from `villa_estimator.estimate`.

## 3. The seeds cannot be paired, and the comparison does not pretend it can

The C++ draws from `std::mt19937` with `uniform_int_distribution` and `uniform_real_distribution`;
the transcription draws from `numpy.random.default_rng`, that is PCG64. **The same seed number of
the two generators does not produce the same sample**, nor the same thousand candidates. Giving the
C++ the seeds `20260915 + z + 1000 k` serves to make the C++ run repeatable, not to pair it with the
Python one.

Consequence, declared now: **the comparison is between two distributions, not between two numbers**.
For every row, the median over the twenty medians per seed and its interval are compared, not the
single estimate. No comparison per slice and per seed will be presented as paired, and in particular
the column `median_k0_mm` (k = 0, which in the frozen file is the seed of the original tables) is
**not** a paired comparison and will be reported only as descriptive.

## 4. What counts as agreement

Three outcomes, distinct and decided now.

**A. Agreement.** A row of Tables II and III is reproduced when all three hold:

1. the median of the C++ falls inside the 95 % bootstrap interval of the frozen row
   (`ci_lo_mm` .. `ci_hi_mm` of `fifteen-k20.csv`);
2. the frozen median falls inside the 95 % bootstrap interval of the C++ row, computed by the same
   code on the C++ estimates (the criterion is symmetric on purpose: a more dispersed arm must not
   be able to "swallow" the other and declare agreement);
3. none of the four flags of the row changes: `margin_ci_includes_zero`,
   `margin_ci_below_threshold`, and the two counting quantities `inside` / `inside_of` in the sense
   of point C below.

If all thirty rows are in agreement: the transcription was faithful and the paper holds as written.

**B. A difference that does not move a verdict.** Some row is not in agreement by A, but the four
pre-registered verdicts (P1, P2, C1, C2) computed by `fifteen_k20.verdict` on the C++ estimates are
identical to those of the frozen file, and no margin flag changes sign or crosses the threshold.
Then the paper prints the numbers of the C++ and says that the transcription was used for the
ablations.

**C. A difference that moves a verdict: everything stops.** Any one of these is enough to stop and
report at once, without going on to write numbers:

* any one of the four verdicts changes;
* `margin_vs_centroid_mm` changes sign on a row, or crosses the threshold of 0.30 mm;
* `margin_ci_includes_zero` goes from 0 to 1 on a row the paper counts as won;
* the `inside` count of the "no-division" variant falls below the total on any scroll, that is the
  claim "inside on every slice" falls.

## 5. The two divergences already known

**Float64 against float32.** The C++ carries the candidate in `cv::Vec2f` and the distance in
`float`, the transcription carries both in `float64`. It is not corrected and not compensated, in
neither of the two directions: here the C++ **is** the reference by definition, because it is what
the PR ships, and the difference is one of the things the comparison has to measure. Where it shows,
in the far field of the slices that run away, it will be reported as such.

**The cap of the search.** `MAX_SWEEPS = 2000` belongs to the transcription and not to the C++,
which has no iteration limit at all. The C++ arm therefore runs **without a cap**. Rule for a slice
that does not stop, written now:

* a wall clock guard of **600 seconds per estimate**, against 1.2 s measured on a slice that
  converges and 2.4 s on the worst known runaway slice (PHerc0125 z 6891); it is 250 times the worst
  measured, so it is not a cap in disguise;
* the guard applies **identically to the two variants**, and not only to the published one;
* an estimate that touches the guard is recorded with a flag `guard=1` and its position **enters no
  number**. The position reached is not used, because using it is exactly the cap the maintainer
  objects to and because stopping early brings the estimate closer to the reference, that is it
  favours the published version; and the slice is not thrown away in silence, because throwing it
  away also favours the published version, by taking its worst case away from it;
* rows that contain even a single estimate with `guard=1` **are not declared reproduced**: they are
  reported as incomplete, with the number of missing estimates, per scroll and per variant;
* the estimates with `guard=1` are rerun once only with a guard of 3,600 s, only to report whether
  they stop by themselves and at what distance; that number is descriptive and does not enter the
  tables.

## 6. Coverage, and what is done if the machine is not enough

Target: **15 scrolls x 24 slices x 20 seeds x 2 variants = 14,400 estimates**, that is the whole of
Table II and the whole of Table III, the same 7,200 estimates per variant of the frozen file.

Expected cost, from measurement and not from an estimate by eye: from 1.2 to 2.5 s per estimate on
this CPU, so between 4.8 and 10 hours of CPU, and between 50 minutes and 1 hour 40 of wall clock
with 6 threads. No GPU, no spending.

If the run does not finish, **exactly** which scrolls and which slices are covered and which are not
is reported, and the subset is never presented as the whole. The order of execution is fixed now, so
that a subset cannot be chosen afterwards: the five scrolls of the primary block first, in the order
of `fifteen-config.json`, then the ten of the confirmation block in the same order.

## 7. What is not touched

The text of the papers is not touched in this run, neither in `paper/` nor elsewhere: the numbers
are produced and that is all. `runs/spiral/normalgrid/` stays read only, as for the whole of this
line of work.
