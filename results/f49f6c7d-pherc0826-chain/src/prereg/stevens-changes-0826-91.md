<!-- Shipped copy of stevens-changes-0826-91/DECLARATION.md, 2026-09-30, as the study wrote it. Where it says PRIVATE, private or never public it describes how the study kept its own outputs on the day it was written, before the owner's decision of 2026-09-30 to publish this article with no position on the scroll. -->
# stevens-changes-0826-91: every change we made to Stevens' pipeline, compared on the same PHerc0826 seeds

Declared 2026-09-28T05:50:47Z (`date -u`) by a coordinator agent, before any number of this study exists. Order: PLAN.md
item 91 (owner's word, 2026-09-28T05:43:22Z; ledger rows `item91-ablation-opened`, `item-91-launched`). What exists when
this is written: nothing of this study; read before it, not measured: the trees and patch files named below, and a
`git apply --check` of the PR diff on the series tree (it applies, simpaper10.cpp with an offset of 326 lines) and of
patch 21 on top of it (it applies). No build of this study has run.

## The arms, and what each tree is

All trees are laid down from `/data/repositories/scrollreading` by `git archive` (never a commit, never a working tree):

- **A, upstream as is**: `62cbc21` (WillStevens/scrollreading main). His `parameters.json` keys and values
  (`seeds-at-scale-1447/scratch/parameters-stock.json`, which is his file) with only the run configuration set: PHerc0826's
  shape, the seed point, `OUTPUT_DIR` the run folder, `SURFACE_ZARR` the local 0826 level 0 (the published zstd copy). His
  makefile, his compiled `PATCH_LIMIT 10000`, his folders made as his readme step 7 says (`surface.bp/surface`,
  `boundary.bp/surface`, `patches`). **If 62cbc21 does not compile with this machine's g++ 15**, A carries the smallest
  fix that makes it compile, in this order and no further: (1) `build/00001` (the `<cstdint>` include, four lines); (2)
  the makefile's library paths (`-L/data/opt/blosc2/lib -I/data/opt/blosc2/include`, libtiff likewise, rpath) passed on
  the make line, not written into the tree. Which of these was needed is a row of `evidence/builds.csv`; nothing else of
  the house series enters A.
- **B = A + scrollreading PR #3 and PR #4, which carry the phase c commits of work S (aeb2e975)**: `1c67ae2`, the tip of
  `badpatchfinder-linear-enumeration` (PR #4, stacked on PR #3), whose merge base with `62cbc21` is `62cbc21`. Its four
  commits: `ed39e8a` (PR #3: render state and precomputed normals of the bad patch finder), `12d89d7` (the guard: refuse
  a chain through a patch with alignments and no geometry), `88b12a5` (advance the enumeration past a dead prefix),
  `1c67ae2` (the cover's frequency table as a vector); the last three are work S's two changes and its guard. The same
  build fix as A if A needed one.
- **C = B + the identical acceleration**: the tree of step 20 of `stevens-pr-acceleration/evidence/series.csv`
  (`ca54f8a8...`: build/00001-00002, the house performance group minus performance/00002, which is PR #3, then the flat
  hash, AVX-512, the LTO/PGO build variables, the LZ4HC recode tool), plus the diff `62cbc21..1c67ae2` applied with
  `git apply` (the same four commits as B). Built with `ARCHFLAGS=-march=native LTO=1 PGO=use`, the training profile being
  stevens-pr-acceleration's B19 profile (`scratch/arms/B19/pipeline9/*.gcda`, grown on commit 19 of the same series,
  sha256 listed in `evidence/builds.csv`), with `-Wno-error=coverage-mismatch` because C's simpaper10.cpp and
  badpatchfinder.cpp differ from the profiled tree. Gate: 0 FMA instructions (objdump vfmadd, vfmsub, vfnmadd, vfnmsub)
  in every binary of every arm, else the binary is removed. Run with the chain's growth settings:
  `SIMPAPER_SHARED_CHUNKS=512 SIMPAPER_FORCE_THREADS=1 OMP_WAIT_POLICY=passive OMP_NUM_THREADS=3`, the growth reading the
  LZ4HC copy `hot-lines-88/scratch/l/0`, `ZARR_CHUNK_MANIFEST` and `ZARR_MISSING_LIST` as `chain-0826/tools/run_seed.sh`,
  and **`SIMPAPER_PATCH_LIMIT=10000`** in every stage, so that the limit equals A's compiled one and C against B isolates
  code, not a setting (the chain uses 40000; this only matters on a tree above 10000 patches, written per run as a column).
- **D = C + the SetSeed velocity reset**: patch 21 of the series
  (`0021-start-the-five-seed-cells-of-a-patch-at-rest.patch`, sha256 `8606e679...` in series.csv) applied on C's tree;
  same flags, same profile, same settings.
- **X, the chain as delivered (informational, no CPU)**: the delivered trees of chain-0826 for the same seeds
  (`chain-0826/out/<seed>/growth` and `C40`), read from disk. **C cannot reuse them, and this is declared now**: the
  delivered tree is `build + performance + corrections-inert + corrections + acceleration + flathash + avx512 (+ lto pgo
  native)`, i.e. C plus the six output changing corrections and three inert ones, and stevens-pr-acceleration measured
  the series tree against the delivered one on PHerc1447-seed1111: `growth_tree differs 5433 of 5433` (branch-identity.csv,
  row B16 against delivered, «the delivered tree carries the corrections»). So C is grown; C against X is written per
  seed (growth tree and sheets by `growth-memory-1447/tools/tree_identity.py`, measures side by side) and is expected to
  differ; X minus C is then the effect of the corrections, a column, not an arm of the order.
- **E, the seed selection, a separate row with no growth**: from chain-0826's own CSVs, per wave (batch-1-400-0826 under
  rule v1, batch-401-2400-0826 and batch-2401-6400-0826 under rule v2, batch-6401-6712-0826 the wave 4 proximity draw):
  draws (seed-rule.csv rows of the group), seed rule passers (passes_rule), v1 passers among them (seed-rule-v2-tests.csv
  passes_rule_v1, v2 waves only), ladder rows and cap survivors (ladder.csv outcome «still growing at the cap»),
  delivered seeds (per-seed-queue.csv delivering_binary starting «delivered»), survivors per draw, survivors per passer,
  delivered seeds with a best square of 10 mm or more, median best square per delivered seed. Tool `tools/e_row.py`,
  `evidence/e-yield.csv`.

Arms A to D differ only in code (and C, D in the growth copy of the prediction, which is part of the acceleration). The
identity claims are measured, never assumed: C against B and B against A on the growth tree (A, B and C share the growth
code up to output preserving changes), and on the sheets for C against B; D against C is expected to differ.

## The seeds: rule declared before the draw

`tools/select_seeds.py`, `numpy.random.default_rng(20260928)`:
1. Population: rows of `chain-0826/evidence/per-seed-queue.csv` with `delivered_downstream_return_code` 0,
   `largest_square_mm_min_step` a number, `growth_patches` at most 10000 (so upstream's compiled limit rarely binds), and
   the delivered growth tree on disk (`chain-0826/out/<seed>/growth/rel.csv` present: needed for X and the estimate).
2. Excluded: the 12 seeds of item 90 road 1b (`area-0826-90/evidence/road1b-seeds.csv`) and the SetSeed seeds of item 90
   road 2 (seed2019, seed5630, seed6365).
3. Strata: the population split at its median `pred_chunk_share_255` into a low and a high half (ties to low); within
   each half, four bins by `largest_square_mm_min_step` at that half's quartiles (25, 50, 75 per cent, numpy linear). One
   seed drawn uniformly in each of the 8 cells, cells in the order (low, bin 1..4), (high, bin 1..4), one
   `rng.integers(0, n)` per cell. An empty cell takes the next seed of the nearest non empty cell of the same half by
   square (written). Output `evidence/seeds.csv` with the cell, the draw index and the population size.

## Measures per seed and arm (one row per run, `evidence/runs-<arm>.csv` via `tools/run91.sh`)

CPU seconds (user plus system of every stage, from bash `times` of a subshell per stage, children included) and wall
seconds, per stage and total; growth return code, patches, rel.csv lines, peak VmHWM (sampled every 10 s); downstream
stages `c, l, vm 10, hm 10, fm 30 10` (his multi component recipe: his 363.8629 cm2 is ten components) each with rc,
CPU, wall; sheets; then `tools/measure91.py` (area-0826-90/tools/collection.py's measure, unchanged code, pointed at this
study's folders; its known reference, Stevens' formula on seed6365's delivered squares = 101.3992, must pass first) on
square.py's CSV (called exactly as chain-0826/tools/measure_seed.sh calls it, voxel 9.362 from the manifest): Stevens'
formula area (cm2, points x step_i_mm x step_j_mm summed over sheets, the line that gives his 363.8629), best square
(`square_mm_min_step`, max over sheets), a2 share (flagged over measurable stride points, T* and S carried), v2 cells
(against the other sheets of the same run), clean area. **Deaths**: a run that is stopped by the ceiling (below) is
«stopped at the ceiling», an outcome with its stage and time, not an error; a stage that exits non zero is «crashed», its
rc written. Neither is dropped from the table.

**Aggregate** (`tools/aggregate91.py`, `evidence/aggregate.csv`): per arm the median over seeds of every measure and the
count of seeds measured, deaths counted; and the paired differences B-A, C-B, D-C (and X-C) per seed and their median,
only over seeds where both arms produced the measure. An arm pair whose trees are byte identical is written «identical»
for the output measures, never «better»; its time difference is still written.

## Ceilings, priority and load

- **Deadline 2026-09-30T12:00Z** for A and B. Before any A or B run starts, `tools/estimate.py` writes
  `evidence/estimate.csv` from existing timings only (no new run): the seed's chain growth wall and stage c seconds
  (`chain-0826/evidence/runs/<seed>.csv`); the growth factor upstream over C = (upstream over session-start, g 600 row of
  `pipeline/releases/2026-09/evidence/round-two-timings.csv`) divided by the product of the five cpu ratios of
  `stevens-pr-acceleration/evidence/pr-table.csv` (flat hash, AVX-512, cap 512, LTO+PGO on 0826, LZ4HC); stage c of A =
  the seed's odometer steps counted on its delivered rel.csv by `c-stage-cost/tools/walk_counts.py`'s method at limit
  10000, times the seconds per step of PHerc1447-seed40 without work S (7251 s for 51,500,264,151 steps, c-stage-times.csv
  and totals.csv), plus the seed's chain stage c times the upstream over session-start c ratio of round-two-timings.csv
  (the selection cost PR #3 removes); stage c of B = the chain's stage c. Labelled a sizing, not a result. A or B starts
  only if now plus 1.25 times its estimate is before the deadline; else its row is «not run: would not finish», written.
  Any A or B process alive at the deadline is stopped by its process group, the run «stopped at the ceiling».
- **Order**: C for the 8 seeds, then D, then per seed in ascending estimated A time B then A. Two runs at a time, each
  `OMP_NUM_THREADS=3`, so at most 6 cores, `nice 10`. A start waits while any `runs/rev1/*/scratch/CLOCK.lock` exists,
  while the cores busy over 10 s exceed 16 (so chain-0826 and road 1b keep their cores), while MemAvailable minus the
  run's memory bound (12 GB for C and D, 32 GB for A and B: his readme's «larger scrolls probably need 32Gb») is under 20
  GB, and while /data is under **50 GB free plus the run's size row**. A running step is never killed for disk; the
  runner stops before the next start.
- **Disk**: before each run a size row (`evidence/sizes.csv`: the seed's delivered growth plus C40 du from chain-0826/out
  as the estimate, then the measured du after). Each run grows into `scratch/coll/<arm>-<seed>/C40` and runs its
  downstream in place (no copy); the growth tree's per file sha256 manifest is written right after the growth
  (`evidence/manifests/<arm>-<seed>-growth.csv`), the sheets' after fm; after its rows and measures are read back, the
  folder is listed (`log/listing-<arm>-<seed>.txt`) and removed except the sheets and the stage CSV files. Identity between
  arms is computed from the manifests, so no two trees need to coexist.
- **If nothing can start now** (/data under 50 GB free at the time of this declaration's check): the builds, the seed
  list, the estimate and the E row are made, the runner is written and checked with `SA_CHECK_ONLY=1`, and nothing is
  grown; the runner is launched only by the director's or coordinator's word once /data has room.

## What would change these rules

Nothing after the first growth. A change before it is an addition below, dated, with its reason.

## Addition of 2026-09-28T05:52:56Z: the delivered test of the seed rule, corrected before any seed was drawn

The first run of tools/select_seeds.py stopped with an empty population and wrote nothing: per-seed-queue.csv's column
`delivered_downstream_return_code` reads «not measurable» on all 207 rows (per_seed.py never fills it). The delivered test
is therefore `delivering_binary` starting with «delivered» (per_seed.py: «the series and the sha256 head of the binary
whose downstream returned 0»), the test E already uses. Nothing else of the rule changes. The growth trees of the chain
have `growth/rel.csv` but no `growth/patches` (removed by item 90's dedup, the sha identical `C40/patches` kept), so X and
the estimate read patches from `C40/patches`.

## Addition of 2026-09-28T05:56:38Z: PR #3 as opened does not compile on its base; B's second build fix, declared before any growth

Seen by the builds (evidence/builds.csv, log/build-B-*.txt), no growth run: A at 62cbc21 needed build/00001 (the
cstdint include; g++ 15 stops at common_types.h:118 `uint32_t`), as declared. B (1c67ae2) stops after that fix at
simpaper10.cpp:787 and :794, `'outPath' was not declared in this scope`: commit ed39e8a (PR #3) replaces upstream's
`OUTPUT_DIR "/badpatches.csv"` and `OUTPUT_DIR "/badpatchscores.csv"` with `outPath(...)`, a function of the house
performance/00001 that upstream does not have. The GitHub API read at this time gives PR #3 head ed39e8a and PR #4 head
1c67ae2, both open, base main 62cbc21: **the two pull requests as opened do not compile on their base**, on any compiler.
B therefore carries, after build/00001, a second fix and nothing else: those two `outPath("/x.csv")` calls written back
as upstream's `OUTPUT_DIR "/x.csv"` (the same path at run time, since B's OUTPUT_DIR is compiled). Checked on a scratch copy
of B's tree: it then compiles. The fix is a column of builds.csv; for C and D it is not needed (outPath exists there).
This is a defect of our open pull requests, to be reported to the director as such.

## Addition of 2026-09-28T06:02:53Z: floor 40 GB and 9 cores (director 2026-09-28T06:01:51Z), declared before any growth

chain-0826 is in a soft pause (deliver.stop written, its running growths finish); for item 91 only, the floor for a new
start is **40 GB free on /data** plus the run's size row (not 50; the 98 per cent brake is at 19.7 GB). Road 1b of item 90
(about 37.6 GB RAM, 3 threads) runs beside this study. So: at most **3 runs at a time** (3 OpenMP threads each, at most 9
cores), nice 10, a start only while the cores busy over 10 s are at most 18 (so ours plus road 1b plus the chain's last
growths stay under the machine), the memory and CLOCK.lock gates unchanged, each tree removed after its rows are listed.
Estimate (evidence/estimate.csv, a sizing): every A and B run fits before 2026-09-30T12:00Z if the runner starts by about
2026-09-29T19:00Z; the runner re checks each A and B at its start. Arm X (the chain as delivered, no growth) was measured
before this addition by tools/x_all.sh (square.py and measure91.py on the chain's sheets, one thread).

## Addition of 2026-09-28T06:04:44Z: runner stopped by its group and restarted with one91b.sh (the wall of a stage)

The first launch (PGID 1915401, 06:03:03Z) ran C on seed1700 and seed5702 for about a minute. Its per stage wall was taken
around the 10 s sampling loop, so every stage read up to 10 s too long (stage l read 10.0 s wall for 0.0 s CPU). The
runner group was killed (kill -- -1915401) and the two partial C rows moved to evidence/runs/superseded/; nothing of them is
used. tools/one91b.sh is one91.sh with the wall taken inside the stage's subshell (date before and after the binary),
sampling every 5 s, and the check only exit before any file is written; run91.sh now calls it (one91.sh stays as written,
x_all.sh's arm X uses it and has no stage timing). Seen in the aborted run, not a result: C on seed1700 grew 178 patches
where the chain's delivered tree has 2162 (X = C plus the corrections), which the declared X column will measure.
