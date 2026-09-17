# Rule of the two runs that remain, written before any number of theirs

Written on **2026-09-18 at 10:52 UTC** (the machine's clock, `date -u`), before running a single
estimate of the twenty-four scroll run and a single estimate of the exponent ablation.

**It is post hoc with respect to every pre-registration of this line of work.** When this rule is
written the following are known: all the numbers of the transcription for both runs
(`evidence/positions-24-refit.csv`, `evidence/exponent-ablation-*.csv`), the four pre-registered
verdicts, the result of the first C++ run of this morning (28 rows out of 30 in agreement, no
verdict moved) and the fact that the C++ without a cap always stops by itself. It is not a
pre-registration and must not be read as one: it is a rule fixed before running so that it cannot
be adjusted afterwards.

It continues and does not replace `declaration-cpp-comparison.md` of 2026-09-18 09:23 UTC, whose
criterion of agreement, rule of stopping, guard and refusal to pair the seeds hold unchanged.

## 1. Run A: the twenty-four scrolls

**Design, which does not change.** The slices are those in the cache of `grid23/<scroll>/`, the same
rule as `rev1_lib.grid23_slices`, that is every non empty `.grid` with at least 100 segments: 24
scrolls, 24 slices each. **One seed only per slice and per variant**, `20260915 + z`, as the
pre-registration of that run fixes it, and not twenty: the figure "576 out of 576" is a count over
576 **slices** at one seed, not over 11,520 slice and seed pairs, and the C++ run does not change
that design because changing it would change the claim instead of checking it. The spread between
seeds stays measured on the three seeds `(20260915, 7, 123456)` of the weighted sum alone, as
before.

**What changes.** Only who produces x and y: `align_and_extract_umbilicus` compiled, called from
`vc_gen_umbilicus`, **without any cap**.

**Size.** 576 slices x 2 variants = 1,152 estimates, plus 2 more seeds on the weighted sum for the
spread = 1,152, **2,304 estimates in all**, about 8 minutes at 6 processes.

**The 576 out of 576.** If the C++ gives a different count, that number changes in the paper and the
difference is published: it is not reconciled, the more convenient of the two is not chosen, no seed
is added to make it come out right.

## 2. Run B: the exponent of the weight

**What is compiled.** The shipped function has no exponent: the weight at
`normalgridtools.cpp:112` is written `1.0f / std::max(100.0f, dist)`. To vary it, that line is
modified. Three new binaries, p = 0.5, p = 1.5 and p = 2, produced by `build.sh` with a substitution
anchored on the exact line of the branch; **if the anchor does not match exactly once, the build
fails**, because a binary born of a slipped anchor is a binary nobody can characterise. Checked
before running: the assert fires on an already substituted source and passes on the source of the
branch.

**The other two rows of the table are not recompiled because they already exist in C++**: p = 1 is
the weighted sum of this morning's run, written `1.0f / std::max(...)` and not `pow(..., 1.0f)`,
that is the shipped expression; the control is the weighted mean of the same run.

**What these binaries do NOT buy.** No authority: a binary with p = 1.5 is our code, not shipped
code, and on those three rows the C++ says nothing the transcription did not say. They buy one
thing only, which is worth more than a label: the control and the row p = 1 stop being a different
instrument from the tables that sit on the same page. The caption will say it in these words: three
of the five rows are compiled variants of an objective that does not exist upstream.

**Design, which does not change.** 15 scrolls, 24 slices, 20 seeds, seeds `20260915 + z + 1000 k`,
the same `F.seed_of` of the existing ablation.

**Size.** 3 exponents x 7,200 = **21,600 estimates**, about 75 minutes at 6 processes.

## 3. What stays transcription, and why it is not a limitation of ours

**The ablation of the search will never move.** Columns (c) and (d) replace the search, and the
shipped function has no replaceable search: an ablation is measured on the instrument that knows how
to ablate the thing. It is a property of their code, not a limitation of ours, and the paper will
say so in those terms.

**The audits of the transcription stay on the transcription**: the cap and the sampling are audits
*of the transcription* and cannot be measured on anything else.

**The comparison of the spread between seeds is not repointed.** `k20-search-noise.csv` deliberately
puts the transcription against the compiled binary: if both sides became the same thing the
comparison would say nothing any more. In this round nobody touches it.

## 4. The guard, unchanged

A wall clock guard of **600 seconds per estimate**, applied **identically** to all the variants,
weighted mean and weighted sum and the three exponents. An estimate that touches the guard is
recorded with `guard=1`, its position enters no number, it is not thrown away in silence, and rows
that contain even a single one are not declared reproduced: they are reported as incomplete, per
scroll, per variant and per slice. The guarded estimates are rerun once only with a guard of 3,600 s
only to report whether they stop by themselves; that number is descriptive.

## 5. The seeds are not paired

Unchanged: `std::mt19937` against PCG64. The same seed number is not the same sample. The
comparisons are between distributions and never per single estimate, and for run A, which has one
seed only per slice, the comparison is on the aggregate count and on the median, never slice by
slice.

## 6. When one stops

As in the first declaration: if any one of the four pre-registered verdicts moves, one stops and
says so at once, without deciding alone. For run A it holds in addition that a change of the count
inside the grid is **not** a reason to stop: it is a result to publish as a difference.

## 7. Coverage, and what is done if it is not enough

Target: both runs in full. If one does not finish, exactly which scrolls and which slices are
covered and which are not is said, and the subset is never presented as the whole. Order fixed now:
run A first, which is short, then run B in the order p = 0.5, p = 1.5, p = 2.

## 8. Addition of 2026-09-18T13:03:33Z: the far field criterion, validated on the shipped walk

Written before rerunning `far_field_eigenvalue.py --slices` and `far_field_scrolls.py`, and
**post hoc with respect to every pre-registration**: it is known that this morning the criterion
predicted every runaway with no false negatives on all 360 slices, with the permutation within
scroll, and all the C++ estimates of `cpp-k20-estimates.csv` are known.

What changes: only the outcome per slice, that is whether the run of the weighted mean left the
grid, read from the estimates of the shipped function instead of from those of the transcription.
The eigenvalues come from the grids and do not change. Slices, seeds, the rule of the majority over
20 seeds and the seed k = 0 stay as before; the permutation within scroll keeps its seed.

Rule: if the criterion holds as it did this morning, Table I and the abstract say so with the
shipped walk. If even a single slice changes side, that is a result and goes in the paper as a
difference, with the name of the slice, and it is not reconciled. The transcription's versions stay
beside as `far-field-*-transcription.csv` and the difference is printed from those.
