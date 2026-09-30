# c-stage-cost: make the chain's `c` stage linear, on seed40's tree

Opened 2026-09-21T15:20:23Z (`date -u`), PLAN 47 step two, on the director's direction of
2026-09-21T14:30:36Z:

> step two the cost of `FindBadPatchesGeneral` profiled with symbols on seed40's tree (7,251 s
> today), one change at a time, same bar, target under ten minutes on that tree.

Written before any number of this study exists. Machine at the moment of writing, first line of
`/data/scrollagent/tools/machine.sh`:
`load 7.18 / 18   cores busy 6.9 / 24   MemAvailable 78.6 GB / floor 20   our disk 260 GB / 492`.
The machine is shared: four growths and `c` stages of other studies run under other process
groups. Nothing of this study is started while cores busy is over 22, and nothing of it touches a
process group it did not create.

## 1. What is already measured elsewhere and is not re measured here

Read from the CSVs and logs named, not from memory:

- `runs/rev1/seed-search-1447/log/uncapped-seed40.txt`: the `c` stage of `PHerc1447-seed40`
  returned 0 in 7,251 s on 2026-09-21T13:33:20Z, then `l` 6 s, `vm 10` 5 s, `hm 10` 0 s,
  `fm 30 10` 7 s, ten sheets.
- `runs/rev1/seed-search-1447/evidence/alignment-fanout.csv`, columns `edges`, `keys`, `fan_out`,
  `chain_cost_at_length_5`: seed40 has 230,513 relation rows over 14,959 keys, mean fan out 30.82,
  and the cost model of the walk at length 5 is 9.02e+05 per start. The three cheap seeds are at
  fan out 4.51 to 4.64 and 413 to 465.
- `runs/rev1/orphan-guard/OUTCOME.md`: the guard `tools/00007-no-chain-through-a-patch-without-geometry.patch`
  is in place and is the source this study starts from.

## 2. The profile I will take, before changing anything

1. A working copy of the guarded source, built by the route of
   `seed-search-1447/tools/build_binaries.py` (`build.sh corrected`, seed40's SEED_X/Y/Z, the
   PHerc1447 volume shape from its manifest, `parse_parameters.py`, `make simpaper10`), with
   `-g -fno-omit-frame-pointer` added and the optimisation level otherwise untouched, so the
   symbols are there and the code is the code that runs.
2. `perf record` with call graph on the `c` stage of a **fresh copy** of
   `runs/rev1/seed-search-1447/out/PHerc1447-seed40/growth`. The tree on disk is never run in
   place. If a full 7,251 s sample is too large, the record is taken over a bounded window of the
   run and that is said in the outcome.
3. A **compiled counter** beside the sampler, because a share is not a count: a build that counts,
   per chain length, the number of odometer steps, the number of alignment map lookups, the number
   of chains built, the number rejected for a repeat, the number rejected for a bad patch, and the
   number pushed. Those counters are written to a CSV. The counting build is used for counts only
   and never for a time.

## 3. The candidate changes I expect to find, named before I look

Each is to be confirmed or refuted from the profile and the counters, not assumed. The owner's
words for this line: it repeats the same thing a thousand times, it keeps no cache, it uses O(N)
where it could use O(1).

- **C1, the dead prefix.** The odometer in `FindBadPatchesGeneral` re walks the whole chain from
  `indices[0]` on every increment, and when the chain being built hits a repeat or a bad patch it
  `break`s out of the build but the odometer still enumerates every suffix of that dead prefix.
  A depth first walk in the same order, pruning a prefix that already carries a repeat or a bad
  patch, emits the same sequences in the same order, because every extension of such a prefix
  carries the same defect and is rejected anyway.
- **C2, the repeated lookup.** `am[currentPatch]` is a `std::map<int,std::vector<alignment> >`
  lookup and it appears twice on the same key in the same `if`/body, once for `.size()` and once
  for `[indices[i]]`, in both the build loop and the increment loop.
- **C3, O(N) where O(1) is possible.** `am` is keyed by a patch id. If the ids are dense enough,
  a vector of pointers indexed by id replaces the red black tree lookup; the profile's «over map
  and set nodes» says where the time is.
- **C4, the per iteration allocation.** `std::vector<int> currentSequence` and
  `std::set<int> currentSequencePatches` are constructed and destroyed on every odometer step,
  for a chain of at most five elements. A fixed array of `length` with a linear scan does the
  same work with no allocation.
- **C5, the set membership test.** `badPatches.count()` is a `std::set<int>` probe in the hot
  path, run once per element of every chain built.
- **C6, work recomputed per patch.** `PrecomputeNormals(patches)` and the index build run once per
  call and are not in the walk; they are checked in the profile and left alone unless they show.

The order in which they are applied is decided from the profile, largest expected saving first, so
that the runs after the first are cheap. The order is recorded in the outcome with the reason.

## 4. The bar, which is the director's

- **Byte identical delivered sheets on seeds 01, 15, 26, 38, 40 and 48, all six**: a fresh copy of
  each growth tree, the whole downstream `c l vm 10 hm 10 fm 30 10` at
  `SIMPAPER_PATCH_LIMIT=40000`, and the sha256 of every `patch_<n>.bin` and of every other file the
  downstream writes compared with what is on disk today. The route and the scripts are
  `runs/rev1/orphan-guard/tools/` reused, not rewritten.
- **Time measured on seed40's tree**, 230,513 relations, against 7,251 s today.
- **Target, written before the work: the `c` stage of seed40's tree under ten minutes, 600 s.**
- **One change at a time**, each with its own timing on seed40 and its own identity check, each a
  patch file in the laboratory's series numbered from `00008` after the orphan guard's `00007`,
  each verified by laying a fresh working copy from the patch files alone and getting byte for byte
  the source that was built.

## 5. What would make each fail honestly

- A delivered sheet, or any other file the downstream writes, differing by one byte on any of the
  six seeds: the change is wrong and is withdrawn, whatever its time.
- A change whose measured time on seed40 is not better than the step before it by more than the run
  to run spread: it is reported as no effect and kept out of the series.
- The pruning of C1 emitting a different number of sequences, or the same number in a different
  order: the printed `badpatchscores.csv` and `patchorders.csv` would move, which the identity
  check catches; it is a refutation of C1, not a licence to soften the bar.
- The profile showing the time somewhere else entirely, for instance in `PlacePatchInto` or in the
  output, in which case C1 to C5 are refuted and the outcome says so with the shares.
- **The ten minute target not reached.** Then the outcome says so plainly and gives the best time
  measured, read back from its CSV. A target is not moved after the fact.

## 6. Caps

- Threads: every run of this study is given a bounded `OMP_NUM_THREADS`, declared beside each
  measurement in `evidence/runs.csv`. The enumeration this study attacks is single threaded, so
  the thread count does not change it; the `PlacePatchInto` loop after it is parallel and the same
  count is used for the baseline and for every change.
- Nothing is started while cores busy is above 22 or `MemAvailable` below 20 GB, read from
  `tools/machine.sh` before each start and recorded.
- Disk: each fresh copy of seed40's tree is about 2.1 GB and is removed when its run is measured;
  the study declares a ceiling of 40 GB for itself under the 492 GB budget.
- `TMPDIR=/data/tmp`. Nothing here needs the network and nothing costs money.
- Nothing is written under `/data/repositories/scrollreading` or under
  `runs/rev1/seed-search-1447/`; this study writes inside its own folder only.
