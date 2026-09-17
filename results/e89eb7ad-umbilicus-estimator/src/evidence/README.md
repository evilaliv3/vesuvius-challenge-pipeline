# Evidence files

Every number the article prints expands a macro computed from a file in this directory, or a
macro the frozen run of September wrote from the same kind of files. Nothing in the article is
typed by hand, and nothing here is either: each of these files is the output of a tool in
`../tools/`, and the article is delivered as `../../article.pdf`. Which files regenerate here, which
need the cut grid slices, and the command for each, are in `../README.md`, section 2.

## Frozen files of the September run

Unchanged bytes of that run: `fifteen.csv`, `synthetic-sections.csv`, `twentythree.csv`,
`cpp-runs.csv`, `search-noise.csv`, `field-stops.csv`,
`function-coverage.csv`, `reference-uncertainty.csv` and `frozen-verdicts.json`, the verdicts of
the two blocks as that run declared them. `cpp-runs.csv`, `search-noise.csv`, `field-stops.csv`
and `function-coverage.csv` come from the stand-in C++ build in `../inputs/real/`;
`reference-uncertainty.csv` from the two umbilici of PHerc1218, the hand annotation and the
one derived from sheet instance labels, which `second-reference.csv` shows to be a per slice
centroid of the papyrus mask and not a second hand;
`synthetic-sections.csv` is the battery of seven families as the September run measured it and
`twentythree.csv` the 24 scrolls of the generalisation run as it measured them, both kept because
`rev1_recompute.py` is read against them and prints what moved.

**`fifteen.csv` is superseded by `fifteen-k20.csv`** for Tables III and IV: one seed per slice
against twenty. It stays here because the k = 0 rows of the new file are checked against it, and
because the density table reads its no-division column.

## Files of the revision, with the tool that writes each

| file | tool | what |
|---|---|---|
| `consistency.csv` | `rev1_consistency.py`, which is not in this folder | every count the captions state, recounted from the CSVs |
| `villa-lines.csv` | the same tool | the cited lines of normalgridtools.cpp at commit 23adee047, with the token each holds |
| `upstream-check.csv` | `upstream_check.py` | whether the defect is still at the tip of upstream, asked of a fetched clone |
| `mechanism-curve.csv` | `synthetic_density.py` | Fig. 1 recomputed: score against distance, sum and mean, two sections |
| `synthetic-density.csv` | `synthetic_density.py` | maximum of each objective and the estimate on sections with a known centre, density 1:1 to 1:10 (Table VI) |
| `synthetic-sections-refit.csv` | `rev1_recompute.py synthetic` | the seven families of sections with a known centre, 20 seeds, both variants |
| `far-field-eigenvalue.csv` | `far_field_eigenvalue.py` | the far field limit of the weighted mean as the largest eigenvalue of the normals' covariance, on the PHerc0826 slice of Fig. 3 and on two synthetic sections, with the mean at the true centre beside it; reads the one cut slice of Fig. 3, the PHerc0826 reference and `../inputs/synthetic_sections.py` |
| `far-field-slices.csv` | `far_field_eigenvalue.py --slices` | the same quantity on each of the 360 slices of the fifteen scrolls, with two scores to compare it against and the outside flags read from `cpp-k20-estimates.csv`, the shipped walk's, since the declaration of 13:03 UTC on 2026-09-18 (`k20-estimates.csv`, the transcription's, is the fallback when the compiled file is absent): the weighted mean at the reference control point (`mean_at_reference`, `predicts_runaway`), which needs a reference the code does not have, and the weighted mean at the point the published search returns on that slice at the seed of the frozen table (`estimate_k0_x`, `estimate_k0_y`, `mean_at_refined`, `predicts_runaway_refined`), which is the comparison a warning inside the function could make; reads `../inputs/grid15/`, the references and `k20-estimates.csv` |
| `far-field-prediction.csv` | `far_field_eigenvalue.py --slices` | that condition against the runs as a two by two table, pooled over the 360 slices, with Fisher's exact test. Three rows, the `predictor` column saying which comparison each is: the reference one on the majority of the 20 seeds and on the seed of the frozen table, and the refined score one, the diagnostic the code could implement, per run on the seed of the frozen table. The third is the one that goes against the idea: it fires on 14 slices with 3 false alarms and misses 124 of the 135 runs that left the grid, sensitivity 0.08, which is why Section IX does not offer the warning. **The pooled Fisher test in this file is no longer read by any macro**: two model reviews of 2026-09-18 made the same point, that 24 slices from each of 15 scrolls are not 360 independent observations, and the file is kept as a record of what was computed |
| `exponent-ablation-*.csv` (the 8 of the ablation itself) | `exponent_ablation.py`, and `figure_exponent.py --numbers` for the last two | the exponent of the weight at 0.5, 1, 1.5 and 2, which both model reviews of 2026-09-18 asked for: the fifteen scrolls at 20 seeds (`-k20-estimates.csv`, `-fifteen-k20.csv`, `-seed-spread.csv`), the cancellation of a pure power in the far field of the weighted mean and its rate out to a distance of 1e9 on three sections and five exponents (`-cancellation.csv`, `-cancellation-rate.csv`), the density bias on the synthetic sections (`-synthetic-density.csv`), and the two the figure tool writes, the mechanism curve of Figure 2 and the score field at each exponent (`-mechanism-curve.csv`, `-score-field.csv`). At exponent 1 the run reproduces the published estimates with zero differences over 7,200, which is what lets the exponent be an argument of `rev1_lib.py` with no number moving. The ablation was declared before it ran, in a document of the working tree that is not in this folder |
| `exponent-ablation-aggregate.csv` | `exponent_intervals.py` | an interval on the aggregate row of the exponent table and the paired count against p = 1, after a referee asked on 2026-09-18 what supports p = 1 over its neighbours. No estimate is recomputed: it reads the run already on disk, so it regenerates from this folder alone. The bootstrap resamples the **scroll** and not the control point, because the quantity is a median over scrolls; the resamples and the seed are those of every other interval, and the caption of the table says which unit it is |
| `far-field-per-scroll.csv`, `far-field-permutation.csv` | `far_field_scrolls.py` | Table I and the p value of Section II, replacing the pooled test: the same condition with the scroll as the unit (per scroll, the slices the condition flags, the runs that left the grid, and how many of those it missed: zero on 14 of 15, one miss on PHerc0257 z 8479 where the bound is 0.909 of the score on the axis and the shipped walk leaves the grid on the majority of seeds), and a permutation test that shuffles the predictor within each scroll, holding every scroll's own counts fixed, with the exact tail computed by convolution of the per scroll hypergeometric counts, p = 5.29e-29, and a 200,000 round simulation beside it. The earlier form of the exact p was a product that is right only when the observation is the largest the shuffling can reach, which it was on the transcription's outcomes and is not on the shipped walk's; the convolution reproduces 1.37e-30 on the transcription's file, which is its known reference. Reads only `far-field-slices.csv`, so it recomputes nothing from the grids and cannot disagree with it |
| `far-field-slices-transcription.csv`, `far-field-prediction-transcription.csv`, `far-field-per-scroll-transcription.csv`, `far-field-permutation-transcription.csv` | the same two tools, as they ran on the transcription's outcomes this morning | the four far field files as they stood before the outcomes were read from the shipped walk: same eigenvalues, the transcription's inside flags. Kept beside the current four because the article prints the slices that change side between the two, and because the permutation tool's exact p is checked against this file (`far_field_scrolls.py --input far-field-slices-transcription.csv` prints 1.37e-30 and writes nothing) |
| `density-asymmetry.csv`, `density-asymmetry-slices.csv` | `density_asymmetry.py`, as it was on 16 September | one-sidedness of the segments around the reference on the slices of Table III, five primary scrolls; kept as written, the tool here no longer rewrites them |
| `density-asymmetry-fifteen.csv`, `-slices.csv`, `-summary.csv` | `density_asymmetry.py` | the same on all fifteen scrolls, with the distances and margins of Tables III and IV beside each scroll, and the Spearman correlations between the sector ratio and those distances and margins on the fifteen, the primary five and the confirmation ten; reads `../inputs/grid15/`, the references and `fifteen-k20.csv` |
| `k20-estimates.csv` | `fifteen_k20.py` | every estimate: 15 scrolls, 24 slices, 20 seeds, 2 variants |
| `fifteen-k20.csv`, `fifteen-k20-verdicts.json` | `fifteen_k20.py` | Tables III and IV with intervals, verdicts applied as written |
| `k20-search-noise.csv` | `fifteen_k20.py --reference-check` | twenty seeds of the transcription on the four saved C++ slices, against `search-noise.csv` |
| `ablation-estimates.csv`, `ablation-search.csv` | `ablation_search.py` | the four cells of Table VII, same seeds, computed by a second tool |
| `twentythree-refit.csv`, `positions-24-refit.csv` | `rev1_recompute.py twentythree` | the generalisation run on the 24 scrolls of the competition set, 3 seeds, both variants |
| `inference-refit.json`, `bland-altman-refit.csv` | `rev1_inference.py` | the Friedman, Holm and Nemenyi tests of Section III on the twenty-seed medians, and the Bland-Altman rows |
| `prereg-timeline.csv` | `prereg_timeline.py` | which primary scrolls had been measured, in `../inputs/result-d-one-division.md`, before the pre-registration of the fifteen was written, the date each of three pre-registration documents states in its first lines, and the seeds per slice each fixed; reads that report, `../prereg/preregistration-fifteen-references.md`, `../inputs/preregistration-twenty-four-scrolls.md`, `../inputs/note-twenty-seeds.md` and `fifteen-k20.csv` |
| `regression-test-run.csv` | `regression_test_result.py` | the regression test of the patch as built and run on 2026-09-17 and redone against the rebased commit on 2026-09-18: pass count, distance and tolerance of each new case, timings, compiler, OpenCV, and whether the second run printed the same estimates; read from `regression-test/`, plus the fork named by `VILLA_FORK` for the commit at its tip (`patch_commit`), its tree (`tree`) and the check that the tree is the one the sources were archived from (`same_tree`) |
| `baselines-k20.csv` | `baselines_k20.py` | two more rules on the slices, the heights and the control points of Tables III and IV: the plateau point nearest the centroid and the maximum of the distance transform of the filled section, both taken from the umbilicus bench, with a percentile bootstrap over the control points and the centroid and the repaired estimator of the same slices beside each row. **Post hoc** with respect to every pre-registration of the article, declared so in the caption of Table V and in the text beside it; `tuned_on_this_scroll` marks the three scrolls whose data set the plateau rule's threshold. Reads `../inputs/grid15/`, the references and `fifteen-k20.csv`, and takes the two rules from the bench archived at `../umbilicus-bench/` |
| `second-reference.csv` | `second_reference.py` | what the second umbilicus of PHerc1218 actually is, and the same comparison on all fifteen scrolls: the counts of who annotated what, read from `../inputs/fifteen-config.json`, and the distribution of the distance between a hand umbilicus and a per slice centroid of the papyrus mask, read from `../inputs/second-reference/hand-vs-mask-centroid.csv`. Written on 2026-09-19, when the article stopped calling that distance the distance between two independent annotations. The derivation of the mask centroids is not rebuilt here and its provenance is beside the input |
| `bench-rules.csv` | `bench_rules.py` | the same question asked once more inside the umbilicus bench, on the bench's own sample: seven rules on 46 heights per scroll at level 3 of the published surface predictions, four scrolls, from the run of 2026-09-18 named by `UMBILICUS_BASELINE_RUN`, with the bench's own six rows re-checked cell for cell against `../umbilicus-bench/results/bench.json` before anything is written. **A different sample from every table above, and never pooled with one**: the same centroid code reads 3.12 mm there and 3.51 mm on the slices of Table V for PHerc0826. **Post hoc** as well, under the same declaration |

## The compiled function: the files the tables now rest on

On 2026-09-18 the accuracy tables, the twenty four scroll run and the exponent ablation were
recomputed by calling the shipped `align_and_extract_umbilicus` through `vc_gen_umbilicus`, the
driver under `../driver/`, instead of through the Python transcription. The rule for each run was
written before it ran, in `../inputs/declaration-cpp-comparison.md` (09:23 UTC) and
`../inputs/declaration-cpp-two-runs.md` (10:52 UTC); both are post hoc with respect to every
pre-registration and say so. The files below are what the article reads now. The transcription's
files of the same name without the `cpp-` prefix stay here: the article names four things that are
still the transcription's and the comparison in `cpp-vs-transcription.csv` is read against them.

| file | tool | what |
|---|---|---|
| `cpp-k20-estimates.csv` | `cpp_k20.py estimates` | every call: 15 scrolls, 24 slices, 20 seeds, 2 objectives, 14,400 rows, with the seed, whether the estimate is inside the grid, whether the wall clock guard was met (never) and the seconds the call took. Needs the two binaries of `../driver/build.sh` and `../inputs/grid15/` |
| `cpp-k20.csv`, `cpp-k20-verdicts.json` | `cpp_k20.py scores` | Tables III and IV and the pre-registered verdicts, from those estimates through the same `fifteen_k20.score` and `fifteen_k20.verdict` as the transcription's tables: the only thing that differs is who produced x and y. Reads the archived bench at `../umbilicus-bench/` for the centroid |
| `cpp-vs-transcription.csv` | `cpp_k20.py compare` | row by row, the compiled function against the transcription, by the criterion of the first declaration: a row agrees when each arm's median lies inside the other arm's interval and no mark on the row changes, and a `moves_a_verdict` column that is empty on every row |
| `cpp-k20-cost.csv` | written by hand from the log of the run, one quantity per row | what the 14,400 calls cost: wall minutes, workers, core hours, mean and worst seconds, the guard and how often it was met (never), and that no cap was imposed |
| `cpp-positions-24.csv` | `cpp_gen24.py gen24` | the twenty four scroll run, 576 slices by two objectives at the run's seed plus two more seeds of the weighted sum, 2,304 rows with a `role` column telling a position from a spread row. Needs `../inputs/grid23/`; Figure 4 is drawn from it |
| `cpp-twentyfour.csv` | `cpp_gen24_score.py` | the per scroll summary of that run, same schema as `twentythree-refit.csv`; two columns, `interior_max` and `interior_max_as_is`, are a probe of the objective's shape and stay the transcription's, as the tool and the article say |
| `cpp-exponent-estimates.csv` | `cpp_gen24.py exponent` | 21,600 calls at p = 0.5, 1.5 and 2, from three binaries with the weight raised to that exponent; p = 1 is not recompiled, it is the weighted sum rows of `cpp-k20-estimates.csv`. Needs the three exponent binaries and `../inputs/grid15/` |
| `cpp-exponent-fifteen-k20.csv`, `cpp-exponent-seed-spread.csv` | `cpp_exponent_score.py` | Table VIII scored through the same `exponent_ablation.score` and `spread` as before, with the check that the p = 1 rows equal the weighted sum rows of `cpp-k20.csv` to the digit |
| `cpp-exponent-aggregate.csv` | `exponent_intervals.py` | the interval and the paired count of the aggregate row, written from the two files above when they are present, which they are here |
| `search-cap.csv` | `search_cap.py` | the cap of the transcription's hill climb, 2,000 sweeps, which the C++ loop does not have: how many estimates of each run met it (only the published weighted mean ever did), how far that walk travels as the cap is raised on the one slice the compiled binary also ran on, and what the tables would say with the cap raised by that factor. Reads the transcription's raw files and `cpp-runs.csv`; needs `../inputs/grid15/` for the rescoring |

## `regression-test/`, the record `regression-test-run.csv` is read from

Written by the run of 2026-09-17 of the test target of the patch, built from the commit's own
sources without CMake or Qt, and kept here as it was left, with three small files added for the
reader: `build.sh` (the build, as run), `build.log` and `run.log` (compiler output, the test
binary's output and the `time` lines of each), `run2.log` (a second run in a fresh process),
`distances.cpp` and `distances.log` (a companion making the same four calls and printing the
distance from the known centre and the margin over the tolerance, which the test binary does not
print), `sources-commit.txt` (the commit the sources were archived from, `7a4129a1d`, the patch commit
after the rebase of 2026-09-18 onto upstream `b1ef996e3`; the audit was redone against it that day
and every distance, margin, tolerance and the pass count came out as on 2026-09-17, with
`distances.log` byte for byte, so what moved is the commit identity and one wall clock. Because the
sources were archived from the patch commit itself this time, the `same_tree` flag beside it is
trivially yes, where before it compared an archive of `dec288ff4` against the tip of the branch),
`opencv-version.hpp` (the version header of the OpenCV the build read, 4.10.0, third party under
the Apache 2 licence) and `compiler.log` (`g++ --version` of the same compiler on the same
machine). What is not here, and what `build.sh` needs to run again, is in `../README.md`,
section 2.

## `far-field-seedpoint-probe/`, a post hoc probe that no number depends on

`far-field-seedpoint-probe/` holds a script and its log and nothing else. It is a **post hoc
probe**, run on 2026-09-17 after the three rounds of review, on the same 360 slices the paper
already reports and with no criterion fixed beforehand: the far field bound compared with the
weighted mean at the point the search starts from, which Section IX of the paper names without
measuring. **No published number depends on it**, it writes no CSV here and feeds no macro. Its
result is quoted in the pull request text, where a maintainer asking the obvious question deserves
the best answer we have, and it is kept out of the paper, where a number measured after the fact
on the same slices would need its threshold and its criterion declared in advance to mean
anything. It is here so that the number quoted elsewhere can be reproduced, not to support a
claim.

`probe.log` is the output of the run the pull request quotes: on the 360 slices the test fires on
101, 13 of them on a run that stayed inside, and misses 47 of the 135 runs that left, sensitivity
0.65. The 135 counts runs at the single seed of the frozen table, which is what a warning inside
one run would see, and not the slices Table I counts by majority of the twenty seeds, 135 that
leave and 134 of them flagged on the shipped walk; the script says so in its own last lines.

Running it again is not free and not self contained. It reads `far-field-slices.csv` from this
directory for `lambda_max` and the per slice outcome, so it cannot disagree with Table I by
recomputing them, but it draws the samples and the thousand candidates from the grid slices
themselves, so it needs `../inputs/grid15/`, the 132 MB that `../README.md` says how to cut. With
the slices in place it takes about two minutes for the fifteen scrolls, or a few seconds for one
named on the command line:

```
python3 evidence/far-field-seedpoint-probe/seedpoint_probe.py [scroll ...]
```

Bootstrap: 1000 resamples, generator seed 20260916, written in each row.
