# Declaration: the two `c` stage changes, checked on the reference scroll PHerc0139

Written at 2026-09-21T20:50:06Z (`date -u`), before any number of this study existed. Nothing
below is retouched: additions are dated and appended under «Additions».

## Why this study exists

House rule, `coordinator.md` section 2: «Ogni misura si accoppia a un riferimento noto e si rifa'
quando l'algoritmo cambia» (`tools/check_references.sh`). The algorithm changed today.
`runs/rev1/c-stage-cost/` added two changes to `FindBadPatchesGeneral` of `pipeline9/badpatchfinder.cpp`,
on top of the orphan guard `corrections/00007`:

- `corrections/00008-a-dead-prefix-is-not-extended.patch`
- `corrections/00009-frequency-table-of-the-cover-is-a-vector.patch`

Every check it ran is on PHerc1447 (seven seeds). PHerc0139 is this home's reference scroll and
the scroll every published result of ours was measured on, and nothing has been checked on it.

## Question

On the PHerc0139 growth trees already on disk, does the whole downstream
`c l vm 10 hm 10 fm 30 10` write byte for byte the same files with the two changes in place as
without them, and what do the changes cost or save on the `c` stage of those trees?

## What is fixed before anything runs

- **No growth is run.** Every tree is one already on disk, and it is never run in place: each run
  works on a fresh `cp -a` copy inside this study's `scratch/`, and the copy is hashed and then
  removed. Nothing is written under another study's folder, under `/data/scrollagent/pipeline`
  or under `/data/repositories`.
- **Trees, all PHerc0139**, each with a `rel.csv` beside it, listed with the tree id this study
  gives them:

  | id | path |
  |---|---|
  | `repeat` | `runs/rev1/growth-repeat/out/growth` |
  | `b40` | `runs/rev1/reference-b40/out/growth` |
  | `D150` | `runs/rev1/seed-distance-ladder/out/growth-D150` |
  | `D450` | `runs/rev1/seed-distance-ladder/out/growth-D450` |
  | `P2` | `runs/rev1/why-the-growth-stops/out/growth-P2` |
  | `C` | `runs/rev1/why-the-growth-stops/out/growth-C` |
  | `S` | `runs/rev1/why-the-growth-stops/out/growth-S` |
  | `A` | `runs/rev1/held-patch/out/growth-A` |

  `repeat` and `b40` are stated by the coordinator to hold the same content: they are this home's
  determinism check and are **one data point, not two**. This study checks that statement with a
  fingerprint of both trees and says what it found; whatever the answer, the two are reported as
  one tree for the purpose of the bar.
  `runs/rev1/ceiling-24000/out/growth` is named in the task; whether it exists is checked and
  written down. `runs/rev1/why-the-growth-stops/out/growth-P` is not in the list.
- **Arms.** Three binaries, all built now by this study from the pinned upstream plus the patch
  series, by the route of `c-stage-cost/tools/build_one.py`, differing only in which patches of
  the `corrections` group are present:

  | arm | series content | what it is |
  |---|---|---|
  | `plain` | `corrected` without `00007`, `00008`, `00009` | the untouched binary, the control |
  | `guarded` | `corrected` without `00008`, `00009` | the orphan guard alone |
  | `c2` | the whole `corrected` group, `00009` last | the two changes under test |

  The pair the bar is read on is **`plain` against `c2`**. `guarded` is there so that a difference,
  if there is one, can be attributed to the guard or to the two changes rather than guessed at.
- **Parameters.** `parameters.json` is the one on disk at `/data/scrollagent/pipeline/build/efficient/parameters.json`,
  the file that configured the binary which grew these trees (`reference-b40/DECLARATION.md`:
  sha256 `28cd6f45...`, seed 4052, 2763, 10487, `RANDOM_SEED` 124, volume 6621 x 6621 x 20974).
  The same file is used for all three arms, so no constant differs between arms. The volume shape
  is cross checked against `pipeline/datasets/manifests/PHerc0139.json`, which is the published
  metadata, and a mismatch stops the study.
- **Run.** `c l vm 10 hm 10 fm 30 10`, `SIMPAPER_PATCH_LIMIT=40000` for every arm and every tree,
  `SIMPAPER_SURFACE_ZARR=/data/scrollagent/data/datasets/PHerc0139/0`,
  `ZARR_CHUNK_MANIFEST` the published chunk listing, `OMP_NUM_THREADS=4`, `TMPDIR=/data/tmp`.
- **Tools.** `tools/run_arm.py`, `tools/build_one.py` and `tools/compare_outputs.py` of
  `c-stage-cost`, and the comparison of `orphan-guard/tools/`, are copied into this study's
  `tools/` and adapted only in their paths, their scroll and the tree list. Every adaptation is
  named in the outcome.

## The bar

1. **Byte identical delivered output on every 0139 tree run**: for each tree, the sha256 of
   **every file** the downstream leaves under the output folder, not the sheets alone, equal
   between `plain` and `c2`. `missing-*.txt`, written by the zarr reader, is excluded and the
   exclusion is stated. **If one file differs, that is the headline**: it would mean the two
   changes are not output preserving on a scroll, and the upstream text and the whole claim have
   to be withdrawn. A difference is reported first, named file by file, and nothing is rounded
   into a pass.
2. **The `c` stage time per tree, in both arms, with its spread**, not one number: repeated runs,
   each on a fresh copy, arms interleaved so that machine drift falls on both, with the cores busy
   and `MemAvailable` from `/data/scrollagent/tools/machine.sh` read immediately before each run
   and written into the row. One run of each is not a time.

## What is expected, so that it is not reported as a surprise

On PHerc1447 the two changes made a **small ribbon tree about 18 per cent slower**
(`c-stage-cost/evidence/small-tree-cost.csv`, seed26: 39.4 s median to 46.6, same machine and
hour; the cause was not identified). Every PHerc0139 tree here is a ribbon, fan out stated by the
coordinator as 4.71 to 4.95, so a slowdown of that order is the expected outcome on time. It is
measured and reported as such, not as a finding. A speed up would be the surprise.

## What would make this study fail honestly

- Any file differing between `plain` and `c2` on any tree: bar 1 fails, and that is the result.
- A tree that cannot be run (absent, empty, no `rel.csv`, a stage returning non zero): it is named
  as not run, with the reason, and never silently dropped.
- A time whose spread within an arm covers the difference between the arms: the difference is then
  written as «not separable from the spread», never as a number.
- A build that does not reproduce: `plain` and `c2` must be laid down from the patch files, and
  the working copy of `c2` must be the working copy of `plain` plus the three patches; the sha256
  of each binary is recorded.

## Caps

- No growth, no network, no spend, no GPU.
- Cores busy never above 22 of 24 (`tools/machine.sh`, `/proc/stat` ticks), `MemAvailable` never
  below 20 GB. A run refuses to start outside those. The machine is shared: another downstream of
  the coordinator runs under its own process group and is never touched. Nothing is killed that
  this study did not start, and then only by PID or process group.
- Disk: each tree copy is 54 MB to 1.9 GB and is removed after it has been hashed; the study's
  own footprint is kept under 60 GB and `df` is re read, never assumed.
- Wall clock: 6 hours. Beyond it the study stops and reports what it has, tree by tree.

## Additions

Dated and declared post hoc, appended below this line; nothing above is retouched.
