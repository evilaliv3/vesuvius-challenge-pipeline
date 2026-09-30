# Output preserving acceleration of the bad patch finder in the scrollreading pipeline

Draft of the text, written 2026-09-22 from the outcomes of the studies listed in `src/prereg/`.
This file is the prose; it is not typeset here and no PDF is built from this folder.

## Abstract

Two changes inside one function of the scrollreading patch chain make its slowest stage finish
where it used to be abandoned, and change nothing it writes. On a quiet machine the `c` stage of
the two largest tangles goes from 7,094.8 s to 35.5 and from 7,930.6 s to 61.2, **about two
hundred times and about a hundred and thirty**; on a ribbon, where the enumeration was never the
cost, it is **1.05** and the work says so rather than averaging it away. Every file the five
delivery stages write is byte identical between the arms on **fifteen named growth trees,
fourteen of them distinct**, across two scrolls, and so is the stage's whole standard output. A
third, a guard, turns an abort into a result on a tree whose alignment file names 104 patches
that are not on disk, and costs time on a scroll of ribbons, which section 5 measures. An earlier performance patch of this series, re measured here because its own
study no longer exists, is worth **31.11** times on that ribbon: the order of magnitude belongs
to it, and what is new here is that the large trees finish at all. Read at the same commit, the author's remedy for patches that cannot sit together is half on in the chain as this laboratory automated it: the bad patch finder runs, while the annealing and the bridges, manual steps of his recipe, were never taken by our runner. Put back, they change the delivered sheets; the annealing draws from the hardware random device, so its result moves from run to run, and a seed for it is offered as a correction.

## What this work is about, in plain words

The scrolls from Herculaneum were burnt by a volcano. They cannot be unrolled by hand, so they
are scanned, and software has to find the sheets of papyrus inside the scan. Each sheet is then
flattened so the writing on it can be read.

This work is about one program in that chain, written by Will Stevens~\cite{stevens}. The
program first grows many small pieces of surface, called patches. A later step looks for patches
that cannot be joined to their neighbours consistently, and throws those away.

**That step did not finish on the largest scans.** We stopped it after two hours. Two changes
inside it make the same step finish in about a minute. Nothing it produces changes: every file
the chain writes afterwards is identical, byte for byte, to the file it wrote before.

A third change repairs a crash. On one scan the program stopped with an error because its own
bookkeeping named pieces that were not on disk. It now refuses those pieces and says how many it
refused, instead of stopping.

**What a reader can check.** Every number in this work names the file it was read from, and every
one of those files is in this folder. The claim that nothing changed is a comparison of every
file the chain writes, not of the finished pictures alone. Where a measurement was taken on a
busy machine, the text says so.

## 1. The chain and its stages, on two scrolls

The object is the patch based surface tracing chain of Will Stevens~\cite{stevens}, `pipeline9/simpaper10` of the
scrollreading repository at commit `62cbc21`, which is `refs/heads/main` of the clone on this disk
(`growth-bookkeeping/evidence/upstream-vs-ours.csv`). The copy of `simpaper10.cpp` the builds here
were laid from hashes to the same blob as `62cbc21:pipeline9/simpaper10.cpp`. A run is a growth,
`g 36000`, followed by five delivery stages: `c`, `l`, `vm 10`, `hm 10`, `fm 30 10`. The growth
writes patches and an alignment file, `rel.csv`, one line per alignment between two patch numbers.
The `c` stage, the bad patch finder, reads them both, enumerates chains of patches of length 2 to
5, scores them, and condemns the patches that cannot be placed consistently.

### The three changes this work proposes, and how they are named here

The series these patches belong to numbers them on disk, and those numbers mean nothing to a
reader. This work calls them **S1**, **S2** and **S3**, in the order the text meets them, and the
serial appears only in the last column.

| | what it is | what it does | measured effect | identity | on disk |
|---|---|---|---|---|---|
| **S1** | a dead prefix is not extended | when a chain dies the odometer advances at the position it died, instead of enumerating every suffix of a prefix already rejected | with S2, the `c` stage of the largest tangle goes from 7,094.8 s to 35.5, **199.9 times**, and of the second from 7,930.6 to 61.2 | every file the five stages write, byte for byte, on fifteen named trees | `corrections/00008` |
| **S2** | the cover's frequency table is a vector | the greedy cover rebuilt a `std::map` of counts on every pass; patch numbers are small integers, so one cleared vector holds the same counts | measured with S1 above; on a ribbon the pair is **1.05 times**, which the work states rather than averages away | the same | `corrections/00009` |
| **S3** | a chain through a patch with no geometry is refused | the alignment map has keys the patches map does not; the stage aborted on the first such chain, and the guard counts and refuses it at the point the chain is assembled | turns an abort into a run on the one tree where it happens, and **costs** 1.33, 1.29 and 1.07 times on three ribbons of the reference scroll | byte identical on the three trees with no such patch | `corrections/00007` |
| *the earlier performance patch* | the selection render state is cleared per touched cell and the normals are precomputed | it is **not one of the three** and is listed here because this work re measures it: its own study no longer exists | **31.11** times on the ribbon of 9,512 patches, median against median | the whole downstream on fresh copies of two growth trees, one of each scroll: **94,962 files compared, none differing**, and the only difference in anything either arm prints is one line, `points skipped as off-grid: 0`, which only the arm with the patch writes | `performance/00002` |

The prose below says S1, S2 and S3. The earlier performance patch is in the table because this
work re measures both of the things it claims, its factor and its identity, and neither could be
read back from anything on this disk when the work was begun; it is not one of the three and the
prose never counts it among them. Its identity was measured on 2026-09-22
(`a8-identity/evidence/identity-totals.csv`, columns `files_compared` and `files_differing`, row
`both trees`). The per file detail is in `identity.csv` and the printed output in
`stdout-identity.csv`.

**Where these are, upstream.** All three were opened on the author's repository on 22
September 2026. S1, S2 and S3 are one pull request, **WillStevens/scrollreading #4**, which
is stacked on **#3**: that one carries the earlier performance patch alone, because the
three do not apply to `main` without it. The defect of section 6, a growth started into a
folder that already holds one, is **issue #2** on the same repository. The numbers in this
work were measured before any of them was opened and none was changed afterwards.

Two scrolls are used and they are not interchangeable. PHerc. 1447 is a 2027 Grand Prize scroll,
removed from the First Letters list on 24 September because letters have been found on it (villa
PR 1887; `prize-eligibility/evidence/prize-eligibility.csv`), and its voxel is 8.640 um, its own value from
`pipeline/datasets/manifests/PHerc1447.json` through `pipeline/datasets/voxel.py`. PHerc. 0139 is
on neither prize list and its voxel is 9.362 um; it is used here only as a second body of growth trees on
which byte equality and stage times can be checked.

What the five stages cost, on the arm carrying the two changes of section 4, from
`c-stage-cost/evidence/runs.csv`, column `seconds`, four OpenMP threads, on a machine shared with
other studies (column `cores_busy_at_start`, 5.4 to 8.4 of 24 on these rows):

| stage | seed26, a ribbon, 9,512 patches | seed40, a tangle, 14,959 patches | machine |
|---|---|---|---|
| `c` | **48.3** | **35.5** | quiet, 0.05 to 0.12 cores busy of 24 |
| `l` | 2.5 | 5.3 | shared, 5.4 to 8.4 |
| `vm 10` | 2.5 | 5.4 | shared, 5.4 to 8.4 |
| `hm 10` | 0.1 | 0.1 | shared, 5.4 to 8.4 |
| `fm 30 10` | 13.8 | 6.2 | shared, 5.4 to 8.4 |

The `c` row is the median of three runs on a machine doing nothing else, 47.4, 48.3 and 48.6 on
the ribbon and 34.5, 35.5 and 35.6 on the tangle
(`quiet-bench/evidence/c-stage-runs.csv`, column `seconds`, tag `c2`). The spreads are 2.53 and
3.19 per cent of the smallest in `quiet-bench/evidence/c-stage-summary.csv`. The four rows below
it are single timings from the earlier harness on a shared machine and have not been repeated
quietly, so the column mixes two kinds of measurement and the table says which is which rather
than presenting five numbers of equal weight. The shared machine gave the same `c` stage 51.8 and
34.9 s: 7.2 per cent above the quiet figure on the ribbon and 1.7 per cent below it on the
tangle.

The four stages after `c` cost 17.0 seconds on the tangle and 18.9 on the ribbon, summed from
the same column. Before the changes the `c`
stage of that same tangle took 7,251 s (`c-stage-cost/evidence/c-stage-times.csv`, column
`reference_seconds`, read from the uncapped run's log), so it was not one stage among five: it was
the run. The growth that precedes them takes 2,400 to 10,075 s over the nine trees of section 2
(`seed-search-1447/evidence/per-seed.csv`, column `growth_wall_clock_seconds`), measured with two
or three growths running beside each other, which makes those wall clocks a cost record and not a
result.

The two kinds named in the table have a measured meaning and it is given in section 2.

### The words this work uses

Each is defined here once, in one sentence, and used in that sense throughout.

- **chain**: the sequence of programs that turns a scan into a flattened sheet.
- **growth**: the first step, which grows small pieces of surface out from a starting point.
- **patch**: one such small piece of surface.
- **alignment file**: the list of which patches sit next to which, one line per pair.
- **stage**: one program of the chain after the growth, named by its letter, `c`, `l`, `vm`, `hm`, `fm`.
- **the `c` stage**: the step this work changes, which finds and removes patches that cannot be joined consistently.
- **chain of patches**: a short run of patches joined end to end, which the `c` stage walks to test them.
- **odometer**: the counter the `c` stage uses to walk every such run in turn, like a milometer.
- **ribbon**: a growth that came out as one long strip, cheap for the `c` stage to check.
- **tangle**: a growth that came out folded on itself, expensive for the `c` stage to check.
- **fan out**: the average number of neighbours a patch has, which tells a ribbon from a tangle early.
- **byte identical**: two runs wrote exactly the same bytes in every file, not merely similar pictures.
- **the guard**: the third change, which refuses a run of patches whose geometry is missing.


## 2. Ten drawn seeds on PHerc. 1447

Ten seed points were drawn on PHerc. 1447 and grown
(`seed-search-1447/evidence/per-seed.csv`, one row per seed). Nine of the ten finished their
growth by themselves and were delivered and measured; seed11's growth returned 3 and is counted
apart in every column (`growth_return_code`, `in_the_distribution`), never folded into a median
with the others.

**The fan out of the alignment map splits the ten trees into two groups with nothing in
between.** `AugmentAlignmentMap` inserts the reverse of every alignment, so the map the chain walk
sees is symmetric and its mean fan out is twice the edge count over the number of keys
(`seed-search-1447/evidence/alignment-fanout.csv`, column `fan_out`, computed from each growth's
own `rel.csv`):

| kind | seeds | fan out |
|---|---|---|
| ribbon | seed26, seed01, seed15 | 4.51, 4.61, 4.64 |
| tangle | seed38, seed40, seed48, seed44, seed11, seed34, seed35 | 27.40, 30.82, 30.86, 32.97, 33.97, 35.88, 37.67 |

seed44's 32.97 was for some hours the one number that file did not carry: its row read
`not measurable` in every measured column, because the file was written before that growth
ended and nothing went back to fill it. It reads **468,938** edges over **28,444** keys now, and
the guard that let it through was our own: `tools/check_fanout_agrees.py` compared only the five
columns copied from elsewhere and never looked at the measured ones, so a row whose `fan_out`
was absent passed it. The same figure was already in two other files while that one was blank,
`early-tangle/evidence/prediction-seed44.csv`, column `answer_when_the_growth_ends`, and
`seed-search-1447/evidence/prediction-seed44-square.csv`, column `fan_out`. Its keys were taken as the count of patch files,
which is the same thing on every tree here but one, seed34, where the map has 104 keys the disk
does not have; that difference is section 5. Ten trees have a fan out and nine have a square:
seed11's growth returned 3, so it has a fan out and no square and is counted apart in every column
that would fold it into a median.

**A prediction written before the answer existed, and right.** The kind of a tree is readable from
the growth's own log long before the growth ends, and seed44 is the one seed where the rule was
applied in advance rather than fitted. At 532 seconds into a growth that then ran 9,097 s, with
the share of the first 100,000 log lines at 0.11963 against a ribbon band topping out at 0.04275,
the prediction recorded was **tangle**, with the note that it sat in the gap between the two bands
and 0.00039 below the nearest tangle rather than inside the tangle band
(`early-tangle/evidence/prediction-seed44.csv`, columns `predicted`, `elapsed_seconds_when_read`
and `share_of_first_100000`). The answer row appended when the growth ended reads tangle at fan
out 32.97. The rule also has a repeat control it did not have when it was written: the same seed
was grown twice, under different machine states and to logs of 4,010,300 and 3,348,977 lines, and
the two shares differ by 0.00005 against a gap of about 0.07 between the kinds
(`early-tangle/evidence/repeat-control-seed44.csv`).

The squares, over the three seeds on papyrus, from
`seed-search-1447/evidence/per-seed.csv`, column `largest_square_mm_min_step`, which is the side
of the exact largest axis aligned fully covered square of a delivered sheet at that scroll's own
voxel: maximum **12.7244 mm** (seed26), median **11.3635 mm** (seed15), minimum **10.3909 mm**
(seed01), the rows of `seed-search-1447/evidence/summary.csv`, column `value`. Of the thirty
delivered sheets those three seeds hand back, ten per seed, **zero reach 20 mm** (column
`sheets_reaching_20mm`, 0 on all three rows). The other seven, seed11, seed34, seed35, seed38,
seed40, seed44 and seed48, the seven tangles above, grew in air: the raw masked scan is absent at
each seed point, column `passes_rule` of `seeds-at-scale-1447/evidence/seed-rule.csv`.

**What the fan out predicts, and what it does not.** Over the nine seeds that have both a fan out
and a square, the three ribbons hold three of the four largest squares, 12.7244, 11.3635 and
10.3909, and five of the six tangles are at or below 9.2948
(`seed-search-1447/evidence/per-seed.csv`, column `largest_square_mm_min_step`, with the kind
from `alignment-fanout.csv`, column `fan_out`). The paragraph below cites the prediction file, and
these squares are not in it. The sixth is the counterexample and
it is the seed the rule was applied to in advance: seed44, a tangle at fan out 32.97, delivers
**11.1968 mm**, the third largest square of the nine: above one of the three ribbons, 10.3909, and
below the other two, 11.3635 and 12.7244. A bound pre registered before its downstream ran, that a
seed at or above fan out 27.40 gives a square at or below 9.2948 mm, said «likely, and it is the
sixth test of a bound that is five for five»
(`seed-search-1447/evidence/prediction-seed44-square.csv`, columns `claim` and `confidence`); the
delivered square is above it. The study recorded its own refutation in that file on
2026-09-22T02:23:46Z, as a second row appended beside the prediction rather than as an edit of
it, because a pre registration is not rewritten: the prediction row's `answer` column still reads
«not yet known, the downstream has not been run», which is what it said when it was written, and
the appended row's `answer` reads «WRONG on both», with 11.1968 mm against the bound of 9.2948 and
4,292.4 mm2 against the bound of 1,898.5. **The fan out orders the cost of the `c` stage
sharply, and that is section 3. It does not bound the square** (figure S3)**.**

## 3. Where the c stage's time goes

A profile was taken before anything was changed, with `perf record -F 299 -e cycles:u` over the
first **2,676.3 s** of the untouched stage on a fresh copy of seed40's tree, the run stopped by
a signal at that point (`c-stage-cost/evidence/runs.csv`, tag `baseline-profile`, columns `seconds` and
`return_code`). That return code reads -15, and the profile itself is
`c-stage-cost/evidence/profile-baseline.csv`, which carries the shares and not the duration. The binary carried `-g` and nothing else: its
`.text` section is byte for byte that of the same build without `-g`
(`c-stage-cost/evidence/text-section-identity.csv`), so the profile is of the code that ships.

| share | what | sort |
|---|---|---|
| 91.50 % | `BadPatchFinder::FindBadPatchesGeneral` | symbol |
| 50.98 % | `stl_tree.h:1437`, the right child step of a red black descent | source line |
| 8.14, 7.21, 4.76, 3.95 % | `stl_tree.h:2604, 2605, 2603, 2607`, the body of `_M_lower_bound` | source line |
| 5.41 % | `stl_tree.h:1425`, the left child step | source line |
| 3.20 % | `badpatchfinder.cpp:426`, the odometer's re walk of the chain | source line |

**About eighty per cent of the stage is the descent of a `std::map`**, and the line of the chain's
own source that drives it is the odometer's validity walk.

The enumeration is an odometer over `indices[0.length-1]`. The number of index tuples it visits
for a chain of length L is the number of walks of L minus 1 edges in the augmented alignment
multigraph. That count can be taken exactly from a tree's own `rel.csv` and `patches/` with no run
at all (`c-stage-cost/evidence/step-counts-model.csv`), and a counting build of the stage itself,
one increment per visit of the `while` body, agrees with it to the step: on seed26 both read
**10,761,063** over the four rounds (`c-stage-cost/evidence/totals.csv`, the two rows
`odometer steps, all four rounds, model` and `... measured, unpruned`). The count was taken this
way because the untouched binary, given the same tree at four threads, had not begun the round at
length 5 after 3,000 s (`c-stage-cost/evidence/runs.csv`, tag `plain-rounds123`, `return_code`
124).

| tree | length 2 | length 3 | length 4 | length 5 |
|---|---|---|---|---|
| seed26, fan out 4.51 | 42,868 | 243,529 | 1,443,677 | 9,030,989 |
| seed40, fan out 30.82 | 460,985 | 20,319,828 | 983,163,150 | 50,496,320,188 |

seed40 totals **51,500,264,151** steps and the round at length 5 is **98.05 per cent** of them
(`totals.csv`). The walk grows with the fourth power of the fan out at the longest length the stage runs, which is the model column `chain_cost_at_length_5` of `alignment-fanout.csv`, stated there as a cost model of the walk in the source and not as a measured time. The exact counts above are the measurement, and they are the two rows a reader should compare.

## 4. Two changes and their proof

Both are patch files of this project's series for that repository, after the orphan guard of
section 5. Neither changes a decision the stage makes; both change how much work it does to reach
the same decision.

- **S1, a dead prefix is not extended.** When the chain being built meets a repeated patch
  or a patch already condemned, the build loop breaks, but the odometer still advances its last
  index, so every suffix of a prefix that is already dead is enumerated one at a time and rejected
  again for the reason the prefix was rejected for. The change records the position at which the
  chain died and advances the odometer there, resetting the indices below it to zero, which is
  where the carry would have left them. A bad first patch is the same argument at depth zero.
- **S2, the frequency table of the cover is a vector.** The greedy cover at the end of the
  same function condemns one patch per pass and rebuilds a `std::map<int,int>` of counts from
  nothing on every pass. Patch numbers are small non negative integers, so one vector indexed by
  patch number, cleared at the top of each pass, holds the same counts with no allocation and no
  tree descent. The scan order and the comparison are untouched, so the patch chosen on each pass
  is the same patch.

A working copy laid down by the build script from the pinned upstream plus the series with both
patches is byte for byte the working copy laid with the guard alone and then edited by the two
change scripts (`c-stage-cost/evidence/patch-verification.csv`, column `B_equals_C`, `yes`, both
sides `db825fd1...`). The patch files, and not a hand edited tree, are what was built and measured.

**The steps.** With the first change the counting build reads, on seed40, 460,985, 73,846, 130,903
and 280,593 over the four rounds: **946,327 steps against 51,500,264,151, a factor of 54,421** (figure S2)
(`c-stage-cost/evidence/step-counts-measured.csv`, variants `pruned` and `unpruned`,
`totals.csv`). On seed26 the two variants print the same number of kept chains at every length,
21,432, 52,571, 191,087 and 682,561 (column `sequences`), which is the change's correctness read
off the instrument itself. Neither number depends on the machine.

**Where the time then went.** A diagnostic build timing the three phases of the function with
`omp_get_wtime`, on seed40's tree (`c-stage-cost/evidence/phases.csv`, summed by tool into
`totals.csv`):

| arm | setup | odometer | sequences | cover | stage |
|---|---|---|---|---|---|
| S3 and S1 | 1.49 | 0.46 | 15.41 | 252.96 | 277.0 s |
| S3, S1 and S2 | 1.69 | 0.49 | 15.42 | 15.58 | 40.1 s |

After the first change the enumeration this work set out to fix costs 0.46 s and the greedy cover
costs 252.96 s, which is why there is a second change and why it is the one it is.

**The times of this table were taken on a shared machine, which is the weaker kind of
measurement, and the quiet bench has since re taken two of these seeds with nothing else
running; where a figure of this table is quoted elsewhere in this work it is the quiet one.**
`c-stage-cost/evidence/c-stage-times.csv`, columns `reference_seconds`, `arm_seconds` and
`speedup`, four threads for the arms, on a shared machine:

| seed | `rel.csv` lines | before | S1 | S1 and S2 | note |
|---|---|---|---|---|---|
| seed01 | 25,505 | 30 s | 57.9 | 55.1 | before taken at 24 threads, not comparable |
| seed15 | 26,476 | 32 s | 85.7 | 78.3 | before taken at 24 threads, not comparable |
| seed26 | 21,436 | 22 s | 52.5 | 51.8 | before taken at 24 threads, not comparable |
| seed38 | 304,256 | 7,808 s | 605.5 | 63.0 | both arms on a shared machine |
| seed40 | 230,513 | 7,251 s | 289.1 | 34.9 | both arms on a shared machine |
| seed48 | 284,922 | 8,300 s | 472.7 | 54.4 | both arms on a shared machine |

Two of those rows have since been taken again on a machine that was doing nothing else, and the
pair that matters most is one of them.

| tree | arm | runs | seconds | spread |
|---|---|---:|---|---|
| seed26, 9,512 patches | untouched | 2 | 51.8 and 49.4 | 2.4 s, 4.86 per cent of the smallest |
| seed26 | with both changes | 3 | 47.4, 48.6, 48.3 | 1.2 s, 2.53 per cent |
| seed40, 14,959 patches | untouched | 1 | 7,094.8 | not measurable, one run |
| seed40 | with both changes | 3 | 35.6, 35.5, 34.5 | 1.1 s, 3.19 per cent |

Four threads, one run at a time, 0.05 to 0.14 cores busy of 24 before each
(`quiet-bench/evidence/c-stage-summary.csv`, columns `every_second_that_finished`,
`spread_seconds`, `spread_pct` and `cores_busy_min`). **On seed40 the quiet pair is 7,094.8
seconds against 35.5, about two hundred times** (figure S1): 199.9 taking the median of each arm, which is
the shape every other factor in this work uses, and 205.65 taking the smallest of each
(`quiet-bench/evidence/c2-factor.csv`, column `factor`). That replaces the 207.8 this section used
to quote, which was a ratio of two timings taken on a shared machine at different hours; the old
figure and the new one agree to four per cent, which is the most that should ever have been
claimed for it. The ratios still quoted from the shared machine, 207.8, 152.6 on seed48 and
123.9 on seed38, are in `c-stage-cost/evidence/c-stage-times.csv`, column `speedup`, and not in
the quiet bench's files; they remain ratios of that kind and section 10 says what that is worth. The quiet pair on seed38 is the bench's last arm and is not in this
draft.

One caveat, from `quiet-bench/evidence/throttle-overlap.csv`: of those four quiet rows, three had
nothing else on the machine and the untouched run on seed40 had a single 24 second burst of one
core inside it, left by a watcher of another study, which is 0.003 of its wall clock against four
working threads. It is named here rather than left for a reader to find, and it cannot move a
factor of two hundred.

On a seventh tree, seed11 of 26,947 patches and 457,647 relation rows
(`seed-search-1447/evidence/alignment-fanout.csv`, columns `patch_files` and `edges`), the
untouched stage took
**22,699 s, 6 hours 18 minutes**, and returned zero
(`seed-search-1447/evidence/untouched-seed11-downstream.csv`, columns `seconds` and
`return_code`, row `c`). The five stages together are 22,775 s. The changed stage took **128.0 s**
on a copy of the same tree (`c-stage-cost/evidence/runs.csv`, tag `c2-11-35`, stage `c`), which is
the quotient of those two columns, **177.3**. That tree is the one where both binaries finished
and nothing had to be inferred from a stopped run. Both timings were taken on a shared machine.

**The reference scroll, where every tree is a ribbon.** The same pair of arms was run four times
per arm on each of seven distinct growth trees of PHerc. 0139, whose fan out is 4.7074 to 4.9490
(`c-stage-on-0139/evidence/trees.csv`, column `fan_out`), so
the enumeration the first change attacks is cheap on all of them and there is nothing for it to
save (`c-stage-on-0139/evidence/c-stage-times.csv`, columns `median_seconds`, `min_seconds`,
`max_seconds` and `cores_busy_min`/`cores_busy_max`, 0.0 to 12.1 of 24). The verdicts are
`c-stage-on-0139/evidence/c-stage-diff.csv`, column `verdict`, which calls a difference nothing
when the two arms' observed ranges intersect.:

| tree | untouched, median | with both changes, median | per cent | verdict |
|---|---|---|---|---|
| A, 392 patches | 3.0 | 2.9 | -1.7 | not separable from the spread |
| repeat, 7,854 | 51.8 | 52.3 | +1.2 | not separable from the spread |
| S, 14,583 | 90.3 | 90.5 | +0.3 | not separable from the spread |
| D450, 15,117 | 110.5 | 109.4 | -1.0 | not separable from the spread |
| C, 15,231 | 72.2 | 68.7 | -4.8 | c2 is faster |
| D150, 15,183 | 108.1 | 83.8 | -22.4 | c2 is faster |
| P2, 15,338 | 115.2 | 102.4 | -11.1 | c2 is faster |

So on a scroll that produces no tangle the change costs nothing and sometimes gains: four of the
seven trees are not separable from the spread and three are faster, and no tree is slower than
its own spread allows. Those seven pairs were measured within one run of one harness but on a
machine that was not quiet throughout, and they are not in the quiet bench's order.

**The third arm says something the pair above hides, and the work would be dishonest without it.**
The harness ran a third binary on every one of those trees: the untouched one plus the orphan
guard of section 5 and nothing else (`c-stage-on-0139/evidence/binaries.csv`, column `corrections_present`), which is the column
that makes the arms differ. The guard adds a check the untouched
binary does not make, and on this scroll it **costs** time:

| tree | untouched over the guard alone | ranges overlap | the guard over both changes | overlap |
|---|---:|---|---:|---|
| A, 392 patches | 0.750 | no | 1.379 | no |
| repeat, 7,854 | 1.034 | yes | 0.958 | yes |
| S, 14,583 | 0.895 | yes | 1.115 | yes |
| D450, 15,117 | 0.978 | yes | 1.033 | yes |
| C, 15,231 | 0.778 | no | 1.351 | no |
| D150, 15,183 | 0.935 | no | 1.379 | no |
| P2, 15,338 | 1.003 | yes | 1.122 | no |

(`c-stage-on-0139/evidence/c-stage-ratios.csv`, columns `ratio_median_over_median` and
`ranges_overlap`). Above one means the second arm of the pair is the faster. On three of the
seven trees the guard alone is slower than the untouched binary by more than either arm's spread:
1.33 times on the smallest tree, 1.29 on C, 1.07 on D150. Measured against the guard rather than
against the untouched binary, the two changes of section 4 pay that cost back and more, 1.379,
1.351, 1.379 and 1.122 on A, C, D150 and P2 with no overlap on any of the four.

That is the shape a reader should take away for a scroll of ribbons: the guard is a price, the
two changes cover it, and the three together are between free and a gain. The price is worth
naming because the guard is the piece that turns an abort into a result, and section 5 is where
that trade is argued.

**The output does not move, and that is what the two changes were accepted on.** Not the delivered
sheets alone, but everything the five stages write, on a fresh copy of each tree, against sha256
taken before this work compiled anything.

| body of evidence | comparisons | differing | file |
|---|---|---|---|
| six growth trees of PHerc. 1447, both arms, everything written | **585** | 0 | `c-stage-cost/evidence/identity.csv`, column `byte_identical` |
| a seventh tree of PHerc. 1447, seed11 | **40** | 0 | `c-stage-cost/evidence/identity-seed11-untouched.csv` |
| eight named growth trees of PHerc. 0139, **seven distinct**, three arm pairings, files the downstream wrote | **936** | 0 | `c-stage-on-0139/evidence/identity-by-tree.csv`, columns `written_by_downstream` and `written_differing` |

Those are the numbers and the work claims no more than them. The same file on the reference
scroll, `c-stage-on-0139/evidence/identity-by-tree.csv`, carries a second sum: its column
`carried_input` adds to **1,473,675**, as its column `written_by_downstream` adds to 936. That
second sum **is not identity evidence**: it counts the carried growth
tree, hard linked between the arms and therefore identical by construction, whose real check is
the pristine fingerprint of each tree taken before any stage ran
(`c-stage-on-0139/evidence/pristine-check.csv`, column `unchanged`, eight rows, all `yes`).

**Eight named trees, seven distinct.** Two of the eight, the growth of `growth-repeat` and the
growth of `reference-b40`, are the same tree: their `rel.csv` has the same sha256 and the same
19,123 lines over 7,854 patches, because one study grew it and the other repeated that growth and
got it back byte for byte. They are counted twice above because the comparison was run twice, and
the honest population is **seven distinct growths**. This
project quoted the larger number once and withdrew it; it is named here so that nobody quotes it
again.

Stronger than the files, because it would catch a difference the files hide: the whole standard
output of the `c` stage, line for line, is identical to the run that wrote the sheets, on all six
PHerc. 1447 trees in both arms (`c-stage-cost/evidence/stdout-identity.csv`, column `identical`,
twelve rows, all `yes`). The longest is **2,914,773** lines on seed15, the maximum of column
`reference_lines` over those twelve rows. and on all eight named PHerc. 0139 trees, seven distinct, in both pairings
(`c-stage-on-0139/evidence/stdout-identity.csv`, sixteen rows, all `yes`). That output names every
chain kept, in the order it is kept, with its score, and every patch condemned in the order it is
condemned. The only lines removed before the comparison are the two per chain length that the
guard of section 5 prints and an unguarded binary cannot, counted in each row.

**What the baseline already carries, and the number this project had wrong.** The arm called
untouched here is not stock upstream: it carries this project's earlier performance series,
including the per thread render state, the parallel loops over pairs and over chains, the
precomputed normals and the sparse clear. A prepared text claimed a factor of seventeen for that
group on the strength of a study that no longer exists. It was re measured on a quiet machine on
the night of 21 September, on seed26, by building an arm with that patch removed
(`quiet-bench/evidence/a8-factor-medians.csv`, column `factor`), with both ranges beside it,
because with two and three runs a median is a weak statistic:

| ratio | over | median against median | factor | the two ranges |
|---|---|---|---|---|
| the earlier performance patch | the series without it over the series with it | 1,574.0 over 50.6 | **31.11** | 1,548.2 to 1,675.7 over 3 runs, 49.4 to 51.8 over 2 |
| the two changes of section 4 | the series with the patch over that plus both changes | 50.6 over 48.3 | **1.05** | 49.4 to 51.8 over 2, 47.4 to 48.6 over 3 |
| all six changes together | without the patch over with everything | 1,574.0 over 48.3 | **32.59** | as above |

Two files in that study carry this factor and they are not the same statistic, so both are named
wherever either is used. `a8-factor-medians.csv`, quoted above, is a median against a median and
gives **31.11**; `a8-factor.csv`, written by `tools/summarise_c.py`, is the smallest run of each
arm against the other and gives **31.34** on the same rows (1,548.2 over 49.4). The two differ by
less than one per cent and neither is corrected by the other: a median and a minimum are different
questions about the same five runs.

Every run was four threads on a fresh copy of the tree, one at a time, with the machine between
0.05 and 0.12 cores busy of 24 before each. **This is one tree of 9,512 patches**, a ribbon, and
the file says so in its own header; the two runs that would have given the same factor on the
large trees were removed, because at this factor they came to 61.6 and 66.4 hours for a number
already in the file. The seventeen is withdrawn: it cannot be read back from anything on this
disk.

**The ribbon, and a measurement that did not reproduce.** A first measurement on a loaded machine
showed the changed binary 18 per cent slower on one ribbon; the quiet re measurement does not
reproduce it. Both sets, with the cores busy each was taken at:

| when | machine, cores busy of 24 | untouched | with both changes | file |
|---|---|---|---|---|
| afternoon of 21 September | 6.1 to 8.3 | 39.0, 39.3, 39.5, 39.8 | 45.9, 46.6, 47.2 | `c-stage-cost/evidence/small-tree-cost.csv` |
| night of 21 September, quiet | 0.05 to 0.12 | 51.8, 49.4 | 47.4, 48.6, 48.3 | `quiet-bench/evidence/c-stage-runs.csv` |

On the quiet machine the changed binary is about 4 per cent faster on that tree. What moved
between the two sets is the untouched arm, not the changed one: the night's changed runs sit where
the afternoon's changed runs sat. Section 10 says what can and cannot be concluded from that.
The marker that stood here asked for the untouched arm on seed26 to be repeated so the baseline
would have a spread of its own. The quiet bench delivered two runs of it, **51.8 and 49.4 s**, a
spread of **2.4 s, 4.86 per cent of the smallest** (`quiet-bench/evidence/c-stage-summary.csv`,
columns `every_second_that_finished`, `spread_seconds` and `spread_pct`). Two runs is a spread
and not a distribution, and it is stated as two throughout; whether a third is wanted is the
direction's, and nothing in this section rests on the difference between two and three.

## 5. The crash and the guard

On the tree of seed34 the untouched stage aborts. Return code 134 after 39 s at four threads,
`terminate called after throwing an instance of 'std::out_of_range', what(): map::at`
(`orphan-guard/evidence/runs.csv`, `log/chain-plain-PHerc1447-seed34-c.txt`). At twenty four
threads the abort came at 21 s, so it is the binary's and not the thread count's.

The throwing call was identified without lowering the optimisation level: `-g` was appended to the
same `-O3` flags and the plain rebuild is byte for byte the binary that crashed
(`badpatch-crash/evidence/binary-gate.csv`). The stack, taken with an `LD_PRELOAD` interposer on
`__cxa_throw` because no debugger is installed here, puts the throw inside the OpenMP body of
`FindBadPatchesGeneral` at chain length 2. The line attribution of `addr2line` is wrong and the
work says so: the body has three `.at` calls and one throw site, the cold paths are tail merged,
and the DWARF line names only one of them. An instrumented copy, built to report and never to run
the chain, settles it: **202** failing chains, all at length 2, the alignment map has the key in
202 of 202, the patches map does not in 202 of 202, the failing element is the second of the
chain in 202 of 202, and the first element is in both maps in 202 of 202. The call is
`patches->at(p)`, **line 436** of `badpatchfinder.cpp`, whose text was read from the file and is
`PlacePatchInto(st,patches->at(p),p,aftx,false);`
(`badpatch-crash/evidence/crash-diagnosis.csv`, columns `value`, `out_of` and `the_check`,
written by that study's `tools/crash_diagnosis.py` from the instrumented run's log). The 73
distinct patches it counts are the same 73 rows as `key-containers.csv` and their
`times_reported_missing` sums to 202, so no chain is counted twice and none is missing.

The key is a patch number that `rel.csv` names as the target of an alignment and that has no
`patch_<n>.bin` on disk. The loader keys the patches map by the files on disk and keys the
alignment map by `rel.csv`, and `AugmentAlignmentMap` then makes every id ever named as a target a
key of the alignment map, with no check that the target was loaded. On seed34's tree `rel.csv`
names **104** such ids out of 28,054 patch files and 505,213 relation rows, and exactly **73** of
them can be the second element of a kept chain of length 2, because the enumeration keeps a chain
only when its first patch is lower than its last and is itself loaded
(`badpatch-crash/evidence/orphans-per-tree.csv`, columns `ids_in_rel_with_no_patch_file` and
`of_those_reachable_as_second_of_a_kept_length_2_chain`). The same columns read 0 and 0 on the
three trees whose stage finishes.

**The guard, and the prediction it was checked against.** The change is thirty five lines inside `FindBadPatchesGeneral`: a third flag beside the repeat and bad patch flags, set when an element of the chain being assembled is not a key of the patches map. A chain that would have been kept and carries such an id is counted instead of being pushed; every other chain is treated exactly as before; and the stage prints, once per chain length, the count of chains refused, the count of distinct ids and the ids themselves. The guard is at the assembly and not at the throwing line,
which is one of three calls in the same OpenMP body that would throw on the same key.

The 73 was fixed from `rel.csv` and the `patches/` listing **before the guard existed**, and the
202 from the instrumented diagnostic build of the same study, also before it existed. What the
guard then reported on the same tree (`orphan-guard/evidence/refused-chains.csv`, columns
`chains_refused`, `patches_involved`, `predicted_patches`, `matches_prediction`):

| chain length | chains refused | distinct ids with no geometry |
|---|---|---|
| 2 | **202** | **73**, and the prediction column reads `yes` |
| 3 | 178 | 58 |
| 4 | 83 | 32 |

The two sets of ids at length 2 are equal, with no id on either side alone
(`orphan-guard/evidence/cross-check.csv`). The stage that used to abort after 21 s instead ran the
length 2 round, its vertex cover, its bad patch selection and two further rounds, and was stopped
by its own 14,400 s cap inside the round at length 5, not by memory
(`orphan-guard/evidence/runs.csv`, `log/memory-watchdog.txt`). That the work does not fit in four
hours on that tree is the cost of section 3 and not of this change.

**The guard fires nowhere else, and it does not change what is written.** On the three trees with
no orphan it reports `chains=0 patches=0` at each of the four lengths, twelve lines in all
(`orphan-guard/evidence/skipped-chains.csv`), and the sixty delivered sheets and all 234 files the
downstream writes are byte identical between the guarded and the untouched arm on each of those
three (`orphan-guard/evidence/sheets-identity.csv`,
`orphan-guard/evidence/all-outputs-identity.csv`).

**It does cost time, and an earlier draft of this work said it did not.** That claim rested on one
tree: repeated runs on seed26 within one hour gave 39.3 to 40.7 s guarded against 39.0 to 39.8
untouched, inside the spread (`c-stage-cost/evidence/small-tree-cost.csv`). Measured on seven
trees of the reference scroll rather than one, the guard alone is slower than the untouched binary
on three of them by more than either arm's spread, and section 3 gives the three ratios, the
ranges behind them and the machine they were taken on. The reason is in the change itself: the
guard adds a `count()` to the hot loop, and on a scroll where the enumeration is cheap that loop
is most of the stage. The two changes of section 4 more than cover it, which is also in section 3,
and the trade this section argues is a crash turned into a result, not a free check.

## 6. Behind the crash, a growth that reopens a folder

The question the guard does not answer is why that tree's `rel.csv` names 104 patches that are not
on disk. It was read out of the source and the filesystem, with no run
(`growth-bookkeeping/`).

**What happened.** The growth that produced seed34's tree did not start on an empty folder. The
surface file `growth/surface.bp` was created at 2026-09-20T20:32:34Z by a growth that was stopped
about 111 s later, and this chain writes its patch files only at the very end, so that run left a
populated surface and an empty `patches` folder. The growth that produced the tree started into
the same folder at 2026-09-21T01:10:11Z. The growth opens the surface where it finds it and takes
its starting patch number from the in memory map, which the growth mode has just allocated empty,
so the new run numbered its patches from 0 again while the surface still carried the stopped run's
ids on its points. Every alignment the new growth computed against those points was written into
`rel.csv` with the old id in the second column. The ids the new numbering did not happen to
re create as a surviving patch are the 104 with no file.

**The evidence, three independent readings that agree.**

- The logs. A tool reads a growth log once and counts the alignment targets the aligner names whose id is above every id that run can have created by that point, the ceiling being the round header plus the patches in flight minus one. The test is conservative, and a stale id below the ceiling is not counted. seed34 names **413** distinct impossible ids in 2,192 mentions; the other nine logs name **zero** (`growth-bookkeeping/evidence/log-compare.csv`). The 413 run from
  12 to 603 and are first named in rounds 1 to 320. In the second round of seed34's growth, when only patches 0 to 4 could exist, the aligner names eighteen ids between 224 and 602. In the same round of seed01 it names 0, 1 and 2. - The filesystem. seed34 is the only tree of the nine measurable with chunk files older than the growth that wrote it, **124** of 52,716 (`growth-bookkeeping/evidence/tree-freshness.csv`), spanning 2026-09-20T20:32:37Z to 20:34:28Z (`stale-chunks-seed34.csv`). Those 124 are a lower
  bound: the writer appends, so every chunk the new run touched again carries both runs' points
  under one mtime.
- The relation file. Of the 505,213 rows, **33,493** name one of the 413 and **5,133** name one of
  the 104 (`growth-bookkeeping/evidence/orphan-rows.csv`, column `rows`). Their first column runs
  from 1 to 35,996 with a median of 10,012 for the 104, against a median of 20,817 over all rows:
  the stale points are not consumed early, they stay in the surface and are aligned against for
  the whole growth.

**The part that is worse than the crash.** Of the 413 ids the log says cannot be that run's, 86
have no patch file and **327 do**, because the new numbering created the same number again
(`growth-bookkeeping/evidence/id-inventory-seed34.csv`). The rows that name those 327 point at
geometry that is not the geometry the alignment was computed against. The crash is the loud case
and it is now refused; the 327 are the silent case (figure S4), and this work measures their count and not
their effect. The 104 and the 413 do not coincide, and the gap is the test's rather than the
data's: 86 of the 104 are in the 413 and the other 18 have numbers at or below the ceiling at the
moment they were named, so the test cannot classify them.

**Whose fault it is.** Upstream's. Every line of the path is in the author's source: the
allocation of the id before growth, the stamping of it on every point written into the surface,
the single write of geometry after the whole growth, the reopening of the surface as found, and
the starting patch number taken from the empty in memory map
(`growth-bookkeeping/evidence/id-allocation.csv`, with the built and the upstream line number side
by side, and `upstream-vs-ours.csv` site by site). Two changes of this project sit near the path
and neither creates it; they change which alignments are found, so the exact set of orphan rows
would differ under stock upstream, not whether orphan rows can exist. The one change of this
project that touches the folder makes the failure **less** likely, not more: it gives each run its
own output folder, where upstream compiles the folder in, so upstream every growth writes into the
same place and a growth interrupted before its final write, followed by another, is the ordinary
case rather than an accident of a runner.

Three things this section does not answer, and they are named rather than left implicit. Whether the 327 re created ids carry a wrong alignment into a delivered sheet. What removed the tree of the earlier, 6,454 s run of that seed, since no file older than 20:32:34Z survives under it and no runner script removes a growth tree; and which stale ids are actually inside the 124 chunk files, which are compressed and were not decoded here.

## 7. What a seed now costs and what the search can afford

`seed-search-1447/evidence/cost-per-ribbon.csv` sums the growth and the `c` stage, and only those
two, over the six seeds that have both a measured fan out and a `c` stage time in both arms. The
other four stages are seconds and are not in these sums, which are stated as growth plus `c`.

| | three ribbons | three tangles | six together | per ribbon |
|---|---|---|---|---|
| before | 2,952.0, 3,039.0, 2,450.6 | 15,217.6, 13,230.8, 15,975.0 | **52,865.0 s** | **4.89 h** |
| after | 2,977.1, 3,085.3, 2,448.3 | 7,348.2, 6,171.5, 7,729.4 | **29,759.8 s** | **2.76 h** |
| after, with tangles stopped at 100,000 log lines | 2,977.1, 3,085.3, 2,448.3 | 532, 532, 532 | **10,106.7 s** | **0.94 h** |

Every cell is from `seed-search-1447/evidence/cost-per-ribbon-quiet.csv`, which
`tools/cost_per_ribbon.py` writes beside the older file rather than over it. The growth seconds
are unchanged and were measured with two or three growths in parallel, so they are a cost record
and not a result. **The `c` seconds of three of the six seeds are the quiet bench's**, medians of the runs that finished, and the file says so per row in its own column. The other three are the shared machine's, as they were. «Per ribbon» is the whole six seed cost over the three ribbons those six seeds delivered, which is what one delivered ribbon costs when three of the six draws are tangles.

One cell moved more than the arithmetic: seed26's «before» was 22 seconds and is now 50.6. The
22 was measured at twenty four threads against an «after» at four, so it was not a pair; with
both arms at four threads on a quiet machine the ribbon's `c` stage is 50.6 against 48.3, which
is the 1.05 of section 4 and not a speedup at all.

The third row is an arithmetic projection and not a measurement: **no growth has ever been stopped
by that rule**, and the CSV says so in its own header. What the rule rests on is
`early-tangle/`. The share of a growth log's first 100,000 lines that match the aligner's
`Patch <n> has <m> matches` separates the two kinds: over both scrolls and all sixteen growths
measured, every one of the ten ribbons is at or below **0.04977** and every one of the six tangles
at or above **0.12002**, and the interval between is empty
(`early-tangle/evidence/early-rate.csv`, `other-scroll.csv`). On seed44 that share was read at
**532 seconds** into a growth whose cap was 54,000, and the prediction was recorded as tangle
before the growth could answer (`early-tangle/evidence/prediction-seed44.csv`).

Three things about that rule are in the record and are not softened. The first declared quantity,
the running mean of the number of matches announced per patch, **does not separate at any K of the
ladder** and is closed negative (`early-tangle/evidence/early-mean.csv`). The band fitted on three
PHerc. 1447 ribbons **failed** on four of the seven PHerc. 0139 ribbons, which is most of them, and
what survives is a single threshold rather than a band, arrived at after seeing the failures and
written as such. And the cross scroll test could not be run as designed, because PHerc. 0139
produced no tangle at all in seven growth trees from five studies (fan out 4.71 to 4.95): that is
«the test could not be run», not «the rule held».

What the numbers do support is the shape of a search. Before, a tangle cost about four hours of
`c` stage after two hours of growth and gave a square under 9.3 mm. After, the `c` stage of a
tangle is a minute, so a tangle costs its growth and nothing else, and the arithmetic of the third
row says what a rule that stopped tangles early would add on top. Nothing here authorises stopping
a growth: that needs more than three ribbons and it is not opened by this work.

**The growth is next, by the same method.** A cap on the chunk store the growth's readers share (patch `00006` of this laboratory's performance series) holds the peak memory of a growth of seed1111 to 0.300 of the unchanged growth's at a cap of 128 chunks, with all 2,493 files of the growth tree and all 10 sheets byte identical, while its clocks, taken in a quiet window, are not measurable under the rule declared for them, so no speed is claimed for it here [prov 66].

## 8. What this does not change

Nothing in this work moves a square, and the reason is section 4: every output is byte for byte
what it was, so every property of the delivered surface is what it was, and **every defect the
stage had, it still has**. What changed is how long the chain takes to produce the same answer,
and on one tree, whether it produces one at all.

The distance to a 20 mm square is unchanged and it is the honest frame for the whole work.

- The largest square this chain delivers on PHerc. 1447, over the nine seeds whose growth
  finished, is **12.7244 mm** (figure S5 draws it on the material) (`seed-search-1447/evidence/per-seed.csv`, column
  `largest_square_mm_min_step`, maximum over the nine rows with `in_the_distribution` yes). The
  median of those nine is 9.2948 mm.
- The best published segment of that same scroll is **13.5262 mm** (figure S6)
  (`published-segments-eligible/evidence/segments-eligible.csv`, column `square_mm_min_step`,
  maximum over the fifteen PHerc. 1447 rows, segment `20251105093211-z_dbg_gen_00320`, at that
  scroll's own 8.640 um voxel). The chain is **0.8018 mm below it**, and that gap is inside this
  project's own repeat spread of **2.6213 mm**; both figures are in
  `seed-search-1447/evidence/summary.csv` and neither is in the two files cited above, which
  carry the squares they are computed from. So the gap decides nothing either way.
- The First Letters prize asks for ten letters in 4 cm2, which is a contiguous **400 mm2**, a
  20 mm square; PHerc. 1447 is no longer on its list, and the 20 mm side is kept here as the size the
  squares are read against. **Zero** of the ninety sheets these nine seeds deliver reaches 20 mm
  (`per-seed.csv`, column `sheets_reaching_20mm`), and **zero** of the twenty one published
  segments of PHerc. 1447 and PHerc. 0800 measured here, both 2027 Grand Prize scrolls, reaches it either
  (`segments-eligible.csv`, column `reaches_20mm`, `no` on every row).

**Coverage, beside the square, and coverage is not reading.** The delivered sheets of 29 further seeds
of PHerc. 1447, delivered by this chain after the ten of section 2 and on papyrus by the same seed
rule, cover **2,227 cm2 deduplicated at one cell** of the chain's grid, 4 voxels on a side (2,010 at
two cells), unstitched (`coverage-union-1447/evidence/union-renamed-v3.csv`, row `cell_set` `all`,
columns `union_cm2`, `union_bin_side_8_voxels_cm2` and `seeds_counted`, rounded to whole cm2).
Stevens' number, "around 365 cm² of coverage on PHerc. 1667" (scrollprize.org/winners, column
`stevens_quote` of the same row), is his, on another scroll and on joined flattened components;
the ten components he published, measured by this laboratory's tool, sum to 363.8629 cm2 with every
overlap counted (`field-0826-0800/evidence/field-sums-renamed-v3.csv`, row `scroll` `PHerc1667`,
column `delivered_area_cm2_sum`, the count from column `surfaces`).
Coverage is not reading: of this area, two sheets have been run through an ink detector and
section 10 says what it shows, and nothing in this work says how much of it carries letters.

So the acceleration buys search, not surface. It makes it cheap to ask the question on many seeds
and it makes one class of tree deliverable at all; it does not bring the answer nearer to 20 mm by
a millimetre, and nothing in this work should be read as saying it does.

## 9. The author's remedy, half on as this laboratory automated it

The prize page describes Stevens' award as a chain that detects overlapping patches whose 2D alignments imply incompatible 3D locations, drops them, and joins the rest into flattened components [winners]. His report names three methods for the dropping: chains of 2 to 5 patches whose placements disagree, bridges, and simulated annealing [stevensreport12]. The bad patch finder this work accelerates is the first of the three. At `62cbc21`, reading the source alone, we asked which of the three reach the sheets of the chain as this laboratory runs it, the five stages of section 1 [prov 63].

- **Method 1 runs.** Stage `c` checks the chains at lines 820 to 840 of `simpaper10.cpp`, and stage `vm` drops the patches it condemns at line 1014.
- **Method 2 is detected and not consumed.** Stage `vm` finds the bridges at line 1073 and writes them to `badbridgess_out.csv` under the comment "remember to copy this to badbridges.csv" at line 1061; none of the five stages reads that file. His report uses the bridges as weight inside method 3, not as a drop of their own.
- **Method 3 is not run.** The annealing is the mode `nm` at line 1510. Its exclusions reach the sheets only through `manualBadPatch.csv`, read at line 586, and no delivered tree of ours holds that file.

**The half that is missing is two manual steps of the author's recipe, and our automation of the chain omitted them.** In his own script for it the annealing is run apart, its output is copied by hand to `manualBadPatch.csv`, and the stages `v`, `h` and `f` are run again (`pipeline9/examine_anneal.sh`); the bridges reach the annealing only when a person copies them to `badbridges.csv`, as the comment above asks. The runner this laboratory wrote runs the five stages and takes none of those copies. Nothing is switched off in his code: the second half of his remedy is a step for a person, and our runner never took it. The two changes and the guard of this work sit inside method 1 and change none of this; the source the house's delivered binaries were built from carries every line quoted above.

**His recipe, run in full.** On 10 delivered seeds of PHerc. 1447 drawn by a fixed generator, the downstream was run again with the annealing and the bridges put back as he runs them (`nm 10 1000` after the first `vm 10`, the two copies, then `vm 10`, `hm 10` and `fm 30 10`, each seed's delivered binary). With the annealing left out, the same runner writes the delivered sheets again, 10 of 10 byte for byte on the first seed; with it, the delivered sheets change on 10 of 10 seeds [prov 64]. So the half that was left out matters to what the chain delivers. In which direction is not said here, and the next paragraph is why.

**The annealing does not repeat itself.** Its random stream is `std::mt19937 rng(std::random_device{}());` at line 675 of `anneal.cpp`: it is seeded from the hardware random device and from no seed the chain accepts, so two runs on one tree are two draws, not a repeat. Three further draws on three of those seeds, each the same run on the same inputs, give Table I [prov 65]. From draw to draw the best square of a seed's sheets moves by 0.7466, 4.3489 and 1.1762 mm, the largest of the three on seed262, and the patches the three new draws exclude overlap pair by pair with a mean Jaccard index of 0.0257 to 0.0304: each draw drops mostly other patches. Against the cells where a steep crossing detector of this laboratory flags a surface cutting across the laminae, the class the overlap was declared to fall in changes from draw to draw on all three seeds, so the same sheets read as the annealing removing part of the crossings on one draw and as exclusions that fall on the flags no more often than anywhere else on another. The detector is the subject of a separate work and is used here only as a common reference for the draws.

Table I. **The annealing, drawn four times on three seeds.** Per seed, the largest square over its sheets, in mm, as delivered (method 3 not run) and after each draw of his full recipe; d0 is the run of the arm on 10 seeds and d1 to d3 are three more of the same run. Under it, the class of each draw's overlap with the steep crossing flags and its enrichment E, the share of the excluded patches' points that are flagged over the share of all points that are flagged. Classes as declared before any draw: P when E is at least 2 and the exclusions take under 0.5 of the flags, I when E lies between 1.5 and 2, H when E is at most 1.5; a fourth class, R, occurred on no draw.

| seed | | delivered | d0 | d1 | d2 | d3 | spread |
|---|---|---|---|---|---|---|---|
| seed355 | square | 15.2840 | 12.2848 | 12.1736 | 12.2952 | 11.5486 | 0.7466 |
| | class, E | | P, 3.4108 | P, 3.4897 | P, 2.3960 | H, 1.2756 | |
| seed262 | square | 11.6981 | 8.1453 | 7.7266 | 7.6238 | 11.9727 | 4.3489 |
| | class, E | | I, 1.6431 | I, 1.9106 | H, 1.3015 | H, 0.7078 | |
| seed664 | square | 10.0413 | 10.2511 | 10.2169 | 9.0764 | 10.2526 | 1.1762 |
| | class, E | | P, 3.4649 | P, 2.5973 | H, 0.2183 | P, 4.5193 | |

**What this work offers him.** A seed for the annealing: a variable read from the environment when it is set, the hardware device only when it is not, which is the form the surface tracer of the villa repository already takes for its own random stream [villa]. With it, the rows of Table I become draws under named seeds that anyone can repeat, and the chain with and without method 3 becomes a comparison instead of a draw. It is offered as a correction of reproducibility and of nothing else. This work does not say that the annealing makes the sheets better or worse, and the table cannot say it: the best square falls on some draws and rises on others, and a square does not know whether a hole was cut in a good sheet or a crossing was cut out of a bad one.

## 10. Limits, and the one that bears on every time in this work

**Every factor quoted here is a ratio of two timings, and a 30 per cent swing between two honest
timings on this machine can have a cause this project has no instrument for.** The bench that
exists to catch exactly this caught it on its first row: the same binary on the same tree at the
same four threads read 39.0 to 39.8 s over four runs in the afternoon at 6.1 to 8.3 cores busy of
24, and 51.8 s at night at 0.07 cores busy. The quiet machine was the slower one, which is the
wrong direction.

Four causes were considered and two of them cannot be tested from inside this guest:

| candidate | testable here | state |
|---|---|---|
| page cache: the tree and the zarr were hot after a dozen runs and are cold now | yes | the repeats on the same tree discriminate it |
| a warm up effect in the binary itself | yes, the same test | open |
| CPU frequency | **no**: no governor is exposed, every core reports a flat 2800 MHz, there is no pstate node, and this is a guest | not testable |
| contention on the host from another tenant | **no**: invisible to this guest's `/proc/stat` by construction | not testable |

The evidence already narrows it. The swing is in the untouched binary alone: the changed binary's
night runs, 47.4, 48.6 and 48.3 s, sit where its afternoon runs sat, 45.9 to 47.2. A cause that
slows one binary and not the other on the same tree at the same hour is not the host's frequency.
Whatever it is, it is why the afternoon's «18 per cent slower on the ribbon» does not reproduce.

The mitigation is the one the bench has, and it is stated rather than assumed: **the two arms of a
ratio are measured back to back, on the same machine in the same state**, so a common cause
cancels. What does not cancel is comparing a number taken on one day with a number taken on
another, and no ratio in this work is allowed to mix the two. The bench that settles this closed
on 2026-09-22 at 06:07Z, so the times in this work are its times and no longer await it; where a
figure from the earlier shared machine is still given, the table it sits in says so on its own
line.

Four further limits, none of them about time.

- **Three ribbons.** The kinds of section 2 are nine growth trees of one scroll from one binary
  route, three of them ribbons. Every threshold, band and ordering that rests on the ribbon group rests on three points.
- **Nine seeds, not the distribution.** The seed search was stopped by the owner with three of ten measured and the remaining seeds were grown afterwards under different conditions. The maximum of nine is not the maximum of the draw, and six of the nine were never intended as a distribution.
- **The guard repairs the consumer, not the producer.** Section 6 says the fault is in the growth's bookkeeping. Whether the producer should be repaired instead is a decision with its own
  declaration and this work does not take it.
- **Identity is not correctness.** Every output of the changed arm is byte for byte the output of
  the unchanged one. That is the whole of the claim. Whether the stage's answer is right is a
  different question and is not touched here.

**Ink, on two of our sheets.** The organisers' 9 um detector, run on our \InkOursSheetsWord{} largest sheets of PHerc. 1447 as on the labelled segments of PHerc. 0139, shows a coherent response between that of the labelled no ink regions and that of the labelled ink, and \InkOursComponentsMinWord{} to \InkOursComponentsMaxWord{} candidate components above the threshold and floor of first-light-pherc0826~\cite{firstlight2026} against \InkLabelledComponentsMin{} to \InkLabelledComponentsMax{} on the labelled ink; no ink is evident, and the render's alignment to the lamina (the interlaminar band swinging across layers) is a stated limit. The coherent share of a region is \InkOursShareMin{} to \InkOursShareMax{} on the two sheets, \InkNoInkShareMin{} to \InkNoInkShareMax{} on the labelled no ink regions and \InkLabelledShareMin{} to \InkLabelledShareMax{} on the labelled ink, over the checkpoints seed42 and seed43, and the threshold and floor are a grey level of \InkExtThreshold{} and \InkExtFloorMm{} mm (`ink-detector-0139/evidence/descriptive-row.csv`, rows `FILL-SEED376-S0-pitchband` and `FILL-SEED316-S1-pitchband` against the rows `labelled ink` and `labelled no ink` of PHerc. 0139, columns `c_sheet`, `ext_floor_components_sheet`, `ext_threshold_u8` and `ext_floor_mm`). The two sheets are the two largest by the area accepted by the uncalibrated certificate, in both of its modes (`coverage-union-1447/evidence/union-per-sheet-renamed-v3.csv`, columns `accepted_uncalibrated_cm2_pitchband` and `accepted_uncalibrated_cm2_asis`).

**A precedent on the same scroll.** TAUIL Abd Elilah~\cite{tauil2026} ran the organisers' 9 um model on \TauilSegmentsWord{} published segments of PHerc. 1447, about \TauilAreaCm{} cm2, and reports "\TauilHeadlineQuote{}": their best window scores \TauilBestWindow{} against a control median of \TauilControlMedian{}. Their correction, headed "\TauilCorrectionDates{}", measured those surfaces oblique to the laminae, "\TauilObliqueQuote{}" from the local sheet normal, and describes them as "\TauilHalfOffQuote{}"; it reads: "\TauilCorrectionQuote{}" (`ink-detector-0139/evidence/tauil-quotes.csv`, column `value`, each quotation checked verbatim against `inputs/github-api/tauil-pherc1447-ink-survey/README.md`).

**One proposal of this project's own is refuted here.** On 23 September 2026 at 00:51Z the direction of this project proposed that a delivered cell count only where the surface prediction the seeds were grown from holds surface within a declared tolerance, so that this chain's sheets and another tool's rectangles would be measured by one occupancy and the square on those cells would be the bar. At one voxel it keeps \CoverShareAllSeeds{} of this work's delivered cells over every seed and \CoverShareBarSeed{} on the sheet that carries the bar. Forty unlabelled cutouts of the raw scan around cells of that sheet, twenty the rule keeps and twenty it drops, were judged by the owner at a crosshair: \CutoutCoveredSheet{} kept cells against \CutoutUncoveredSheet{} dropped ones read as sheet, a share of \CutoutSheetRateCovered{} against \CutoutSheetRateUncovered{}, Fisher one sided p = \CutoutFisherP{}, no separation (`src/evidence/studies/tracer-against-the-chain/cutout-score-seed26-patch2.csv`, with the shares in `coverage-selftest-chain.csv` beside it). The rule speaks about the marked prediction and not about the papyrus, so the bar keeps its name, **as delivered**, and the covered share is a column beside it and never a judge. Eighteen answered cells against seventeen cannot see a small effect, and the judge is not a papyrologist.

## Figures

Each figure is drawn by the script named in it, from the CSV of plotted numbers beside it; no
number in a figure is typed by hand. The six are referred to in the text where they belong.

**F1, drawn as S1. The `c` stage, untouched against changed, on the quiet bench.** One pair of
bars per seed on a logarithmic axis, the factor written over each pair
(`evidence/figures/s-f1-c-stage-before-after.csv`, columns `quiet_plain_seconds`,
`quiet_c2_seconds` and `quiet_factor_label`). The right panel is the reference scroll, drawn as
medians with the observed range from `c-stage-on-0139/evidence/c-stage-times.csv`.
*Caption:* On PHerc. 1447 the change is the difference between a stage that finishes and
one that is abandoned. The untouched binary takes **7,094.8 s** on one tangle and **7,930.6** on
the other; the changed one takes **35.5** and **61.2**, about two hundred times and a hundred and
thirty. On the ribbon, where the enumeration was never the cost, the same pair is **1.05** and
the panel shows it at that size rather than hiding it in an average. The three seeds with no
quiet pair are marked and left off this panel: their shared machine before was taken at twenty
four threads and their after at four, so the two are not a pair at all.

**F2, drawn as S2. The odometer's steps, modelled against counted.** Bars on a logarithmic axis,
one seed each (`evidence/figures/s-f2-odometer-steps.csv`, columns `modelled_steps` and
`counted_pruned_steps`).
*Caption:* What the change does is not run faster, it is do less. On the largest tangle the
enumeration as written takes **51,500,264,151** steps and the changed one **946,327**, a factor
of **54,421**, and that is a count of work and not a clock. The three ribbons sit four orders of
magnitude below the tangle before anything is changed, which is why the same change is worth two
hundred times on one and five per cent on the other.

**F3, drawn as S3. The square against the fan out, over ten drawn seeds.** One point per seed,
the kind by colour (`evidence/figures/s-f3-square-against-fanout.csv`, columns `fan_out`,
`square_mm` and `kind`).
*Caption:* The fan out of a growth's alignment map separates the two kinds of tree cleanly and
**does not bound the square**. Nine of the ten seeds have a square. The three ribbons deliver
10.3909, 11.3635 and **12.7244 mm**, and seed44, at a fan out of **32.97**, delivers
**11.1968**, above one of the three ribbons. A bound registered before that seed's downstream
ran said it would be at or below 9.2948 and it was not: the figure is the picture of a rule this
work withdrew.

**F4, drawn as S4. Two runs mixed in one folder.** Patch ids on the x axis, the stale ones
marked (`evidence/figures/s-f4-seed34-two-runs-mixed.csv`, columns `stale_patch_id`,
`comp_label` and `comp_count`).
*Caption:* A growth restarted into a folder that already held points does not start again, it
adds. Of the **28,054** patch files this run wrote, **413** carry ids the aligner's own log says
cannot be this run's; **104** ids appear in `rel.csv` with no patch file at all and **86** are
both. The number that matters is the third: **327** of the stale ids were **created again** by
the second run, so nine tenths of the damage is invisible in the file listing and shows only in
the log. The crash of section 5 is the tenth that is visible.

**F5, drawn as S5. Papyrus, with the delivered sheet on it.** Three panels of equal height, each
captioned inside the figure (`evidence/figures/s-f5-papyrus-with-the-sheet.csv`), whose rows also carry the display window
of each grayscale panel.
*Caption:* The material, with the square the chain gets out of it. Panel a is one z slice of the reference scroll's own grayscale, assembled from the cube stacks of the twelve cube window, with **606** cells of a delivered sheet lying on it. Panel b is that sheet's coverage mask and the largest fully covered square in it, **324** cells on a lattice of 3,054 by 3,389, which is **12.123 mm** at 9.362 um a voxel and is the largest over **610** measured sheets of twelve arms; panel c is PHerc. 1447, whose grayscale is not on this disk, so the sheet is drawn on the published prediction field instead and the caption inside the figure says which of the two renderings each panel is. Its square is **12.7244 mm** at 8.640 um a voxel. The two panels
of papyrus are different renderings of different scrolls and are not to be compared pixel for
pixel; what they share is the scale bar and the square.

**F6, drawn as S6. Our coverage mask beside a published segment's, at the same scale.** Two
panels (`evidence/figures/s-f6-coverage-beside-a-published-segment.csv`).
*Caption:* Our best sheet of PHerc. 1447 reaches **12.7244 mm**, recomputed over **100**
measured sheets, and the best published segment of the same scroll reaches **13.5262**: the gap
is 0.8018 mm and this work claims nothing from it. **The square is not drawn on the right
panel**, and the figure's own table says why in a row of its own: the segment's CSV measured a
grid of **682 by 411** cells and the segment's tifxyz is **212 by 200**, because the CSV read a
different rendering of the same segment. A square placed on a grid it was not measured on would
look like a measurement.

## About the author

Giovanni Pellerano is a computer engineer and whistleblowing hacktivist.
Co-author and Project Lead of the free and open-source software, GlobaLeaks, he
is responsible for software development and for the support of the community that has grown
around it worldwide. He is a digital rights advocate currently learning more about mainstream
generative AI development and how to resist against their various and profound harms.

He had not heard of the Vesuvius Challenge before Saturday 5 September 2026. Everything reported
in this series was done after that date, which is stated because it bounds what the work can be
assumed to rest on: no prior familiarity with the data, the tools, the community or the
literature, just a curious and hyperfocused mind joining this new journey.

## Declaration of generative AI in the research and writing process

During the preparation of this work the author used Claude Opus 5 (Anthropic) in order to carry
out the full research and to write the article: the model read the data, wrote and ran the tools,
performed the measurements, and drafted the text. The author set the direction, supplied the
domain judgement, challenged the conclusions, reviewed and edited the content, decided what was
published, and takes full responsibility for the content of the publication.

The failure this arrangement is prone to is asserting a conclusion that no measurement supports.
It happened repeatedly in this work. Several conclusions were retracted after being measured, and
the retractions are kept in the text rather than removed, so a reader can see both what was
claimed and what the measurement did to it.

What keeps the arrangement checkable is in the folder and not in this paragraph. The criterion of
a study is registered before the run, with the day and the hour it was written, and is not revised
once the results are in: the pre-registrations this article rests on are in `src/prereg/`, with
their digests. Every number printed here expands a macro computed from a file in `src/evidence/`,
and each of those files is written by a tool in `src/tools/`: none is typed by hand, by the author
or by the model. A reader who doubts a number is not asked to trust the arrangement: the file, the
tool and the command that produced it are in the same folder.
